#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import re
from fractions import Fraction
from functools import reduce
from operator import or_
from collections import defaultdict

from migen import *

from litex.soc.interconnect.csr import CSRStorage, AutoCSR

from litedram.common import TappedDelayLine, Settings


def bit(n, val):
    return (val & (1 << n)) >> n

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def bitpattern(s):
    if len(s) > 8:
        return reduce(or_, [bitpattern(si) << (8*i) for i, si in enumerate(chunks(s, 8))])
    assert len(s) == 8
    s = s.translate(s.maketrans("_-", "01"))
    return int(s[::-1], 2)  # LSB first, so reverse the string

def delayed(mod, sig, cycles=1, **kwargs):
    delay = TappedDelayLine(signal=sig, ntaps=cycles, **kwargs)
    mod.submodules += delay
    return delay.output

def edge(mod, cond):
    """Get a signal that is high on a rising edge of `cond`"""
    cond_d = Signal()
    mod.sync += cond_d.eq(cond)
    return  ~cond_d & cond

class ConstBitSlip(Module):
    def __init__(self, dw, i=None, o=None, slp=None, cycles=1):
        self.i   = Signal(dw, name='i') if i is None else i
        self.o   = Signal(dw, name='o') if o is None else o
        assert cycles >= 1
        assert 0 <= slp <= cycles*dw-1
        slp = (cycles*dw-1) - slp

        # # #

        self.r = r = Signal((cycles+1)*dw, reset_less=True)
        self.sync += r.eq(Cat(r[dw:], self.i))
        self.comb += self.o.eq(r[slp+1:dw+slp+1])

# TODO: rewrite DQSPattern in litedram/common.py to support different data widths
class DQSPattern(Module):
    def __init__(self, preamble=None, postamble=None, wlevel_en=0, wlevel_strobe=0, register=False):
        self.preamble  = Signal() if preamble  is None else preamble
        self.postamble = Signal() if postamble is None else postamble
        self.o = Signal(16)

        # # #

        # DQS Pattern transmitted as LSB-first.

        self.comb += [
            self.o.eq(0b0101010101010101),
            If(self.preamble,
                self.o.eq(0b0101000001010101)  # 2tCK write preamble
            ),
            If(self.postamble,
                self.o.eq(0b0101010101010100)
            ),
            If(wlevel_en,
                self.o.eq(0b0000000000000000),
                If(wlevel_strobe,
                    # use 2 toggles as, according to datasheet, the first one may not be registered
                    self.o.eq(0b0000000000000101)
                )
            )
        ]
        if register:
            o = Signal.like(self.o)
            self.sync += o.eq(self.o)
            self.o = o


class Latency:
    """Helper for specifying latency in different clock domains"""

    PATTERN = re.compile(r"^sys(?:(\d+)x)?$")

    def __init__(self, **kwargs):
        self._sys = Fraction(0, 1)
        for name, cycles in kwargs.items():
            m = self.PATTERN.match(name)
            assert m, f"Wrong format: {name}"
            denom = m.group(1) or 1
            self._sys += Fraction(cycles, int(denom))

    def __getattr__(self, name):
        m = self.PATTERN.match(name)
        if m:
            denom = m.group(1) or 1
            cycles = self._sys * int(denom)
            if cycles.denominator != 1:
                raise ValueError("{}.{} results in a fraction: {}".format(self, name, cycles))
            return cycles.numerator
        raise AttributeError(name)

    def __add__(self, other):
        new = Latency()
        new._sys = self._sys + other._sys
        return new

    def __repr__(self):
        return "Latency({} sys clk)".format(self._sys)


class SimPad(Settings):
    def __init__(self, name, width, io=False):
        self.set_attributes(locals())

class SimulationPads(Module):
    """Pads for simulation purpose

    Tristate pads are simulated as separate input/output pins (name_i, name_o) and
    an output-enable pin (name_oe). Output pins are to be driven byt the PHY and
    input pins are to be driven by the DRAM simulator. An additional pin without
    a suffix is created and this module will include logic to set this pin to the
    actual value depending on the output-enable signal.
    """
    def layout(self, **kwargs):
        raise NotImplementedError("Simulation pads layout as a list of SimPad objects")

    def __init__(self, **kwargs):
        for pad  in self.layout(**kwargs):
            if pad.io:
                o, i, oe = (f"{pad.name}_{suffix}" for suffix in ["o", "i", "oe"])
                setattr(self, pad.name, Signal(pad.width))
                setattr(self, o, Signal(pad.width))
                setattr(self, i, Signal(pad.width))
                setattr(self, oe, Signal())
                self.comb += If(getattr(self, oe),
                    getattr(self, pad.name).eq(getattr(self, o))
                ).Else(
                    getattr(self, pad.name).eq(getattr(self, i))
                )
            else:
                setattr(self, pad.name, Signal(pad.width))


class CommandsPipeline(Module):
    """Commands pipeline logic for LPDDR4/LPDDR5

    Single DFI command may require more than one LPDDR4/LPDDR5 command, effectively
    spanning multiple DFI phases. This module given a list of DFI phase adapters
    will use them to translate DFI commands to data on the CS/CA lines and will
    handle any possible overlaps.

    Basic check will make sure that no command will be sent to DRAM if there was any command
    sent by the controller on DFI during previous phases. The extended version will instead
    make sure no command is sent to DRAM if there was any command _actually sent to DRAM_
    during the previous phasess. This is more expensive in terms of resources and generally
    not needed.

    Adapters have to provide the following fields: valid, cs, ca.
    """
    def __init__(self, adapters, *,
            cs_ser_width,  # n bits serialized in controller cycle (depends on CS being SDR/DDR)
            ca_ser_width,  # n bits serialized in controller cycle (depends on CA being SDR/DDR)
            ca_nbits,      # number of CA lines (LPDDR4/5 -> 6/7)
            cmd_nphases_span,  # at most how many phases can a command span
            extended_overlaps_check=False):
        nphases = len(adapters)
        self.cs = Signal(cs_ser_width)
        self.ca = [Signal(ca_ser_width) for _ in range(ca_nbits)]

        # # #

        # Number of phases (before the current one) we need to check for overlaps
        n_previous = cmd_nphases_span - 1

        # Create a history of valid adapters used for masking overlapping ones
        valids = ConstBitSlip(dw=nphases, cycles=1, slp=0)
        self.submodules += valids
        self.comb += valids.i.eq(Cat(a.valid for a in adapters))
        valids_hist = valids.r
        if extended_overlaps_check:
            valids_hist = Signal.like(valids.r)
            for i in range(len(valids_hist)):
                hist_before = valids_hist[max(0, i-n_previous):i]
                was_valid_before = reduce(or_, hist_before, 0)
                self.comb += valids_hist[i].eq(valids.r[i] & ~was_valid_before)

        cs_per_adapter = []
        ca_per_adapter = defaultdict(list)
        for phase, adapter in enumerate(adapters):
            # The signals from an adapter can be used if there were no commands on previous cycles
            allowed = ~reduce(or_, valids_hist[nphases+phase - n_previous:nphases+phase])

            # Use CS and CA of given adapter slipped by `phase` bits
            cs_bs = ConstBitSlip(dw=cs_ser_width, cycles=1, slp=phase)
            self.submodules += cs_bs
            self.comb += cs_bs.i.eq(Cat(adapter.cs)),
            cs_mask = Replicate(allowed, len(cs_bs.o))
            cs = cs_bs.o & cs_mask
            cs_per_adapter.append(cs)

            # For CA we need to do the same for each bit
            ca_bits = []
            for bit in range(ca_nbits):
                ca_bs = ConstBitSlip(dw=ca_ser_width, cycles=1, slp=phase)
                self.submodules += ca_bs
                ca_bit_hist = [adapter.ca[i][bit] for i in range(cmd_nphases_span)]
                self.comb += ca_bs.i.eq(Cat(*ca_bit_hist)),
                ca_mask = Replicate(allowed, len(ca_bs.o))
                ca = ca_bs.o & ca_mask
                ca_per_adapter[bit].append(ca)

        # OR all the masked signals
        self.comb += self.cs.eq(reduce(or_, cs_per_adapter))
        for bit in range(ca_nbits):
            self.comb += self.ca[bit].eq(reduce(or_, ca_per_adapter[bit]))


class Serializer(Module):
    """Serialize given input signal

    The parallel part uses `clkdiv` to latch the data. Output data counter `cnt` is incremented
    on rising edges of `clk` and it determines current slice of `i` that is presented on `o`.
    `LATENCY` is specified in `clkdiv` cycles.

    NOTE: both `clk` and `clkdiv` should be phase aligned.
    NOTE: `reset_cnt` is set to `ratio - 1` so that on the first clock edge after reset it is 0
    """
    LATENCY = 1

    def __init__(self, clkdiv, clk, i_dw, o_dw, i=None, o=None, reset=None, reset_cnt=-1, name=None):
        assert i_dw > o_dw
        assert i_dw % o_dw == 0
        ratio = i_dw // o_dw

        sd_clk = getattr(self.sync, clk)
        sd_clkdiv = getattr(self.sync, clkdiv)

        if i is None: i = Signal(i_dw)
        if o is None: o = Signal(o_dw)
        if reset is None: reset = Signal()

        self.i = i
        self.o = o
        self.reset = reset

        if reset_cnt < 0:
            reset_cnt = ratio + reset_cnt

        # Serial part
        cnt = Signal(max=ratio, reset=reset_cnt, name='{}_cnt'.format(name) if name is not None else None)
        sd_clk += If(reset | cnt == ratio - 1, cnt.eq(0)).Else(cnt.eq(cnt + 1))

        # Parallel part
        i_d = Signal.like(self.i)
        sd_clkdiv += i_d.eq(self.i)
        i_array = Array([i_d[n*o_dw:(n+1)*o_dw] for n in range(ratio)])
        self.comb += self.o.eq(i_array[cnt])


class Deserializer(Module):
    """Deserialize given input signal

    The serial part latches the input data on rising edges of `clk` and stores them in the `o_pre`
    buffer. The parallel part presents the data on `clkdiv` rising edges. `LATENCY` is expressed in
    `clkdiv` cycles. The additional latency cycle (compared to Serializer) is used to ensure that
    the last input bit is deserialized correctly.

    NOTE: both `clk` and `clkdiv` should be phase aligned.
    NOTE: `reset_cnt` is set to `ratio - 1` so that on the first clock edge after reset it is 0
    """
    LATENCY = 2

    def __init__(self, clkdiv, clk, i_dw, o_dw, i=None, o=None, reset=None, reset_cnt=-1, name=None):
        assert i_dw < o_dw
        assert o_dw % i_dw == 0
        ratio = o_dw // i_dw

        sd_clk = getattr(self.sync, clk)
        sd_clkdiv = getattr(self.sync, clkdiv)

        if i is None: i = Signal(i_dw)
        if o is None: o = Signal(o_dw)
        if reset is None: reset = Signal()

        self.i = i
        self.o = o
        self.reset = reset

        if reset_cnt < 0:
            reset_cnt = ratio + reset_cnt

        # Serial part
        cnt = Signal(max=ratio, reset=reset_cnt, name='{}_cnt'.format(name) if name is not None else None)
        sd_clk += If(reset, cnt.eq(0)).Else(cnt.eq(cnt + 1))

        def as_array(out):
            return Array([out[n*i_dw:(n+1)*i_dw] for n in range(ratio)])

        o_pre = Signal.like(self.o)
        sd_clk += as_array(o_pre)[cnt].eq(self.i)

        # Parallel part
        # we need to ensure that the last chunk will be correct if clocks are phase aligned
        o_pre_d = Signal.like(self.o)
        sd_clkdiv += o_pre_d.eq(o_pre)
        # would work as self.comb (at least in simulation)
        sd_clkdiv += self.o.eq(Cat(as_array(o_pre_d)[:-1], as_array(o_pre)[-1]))


class SimLogger(Module, AutoCSR):
    """Logger for use in simulation

    This module allows for easier message logging when running simulation designs.
    The logger can be used from `comb` context so it the methods can be directly
    used inside `FSM` code. It also provides logging levels that can be used to
    filter messages, either by specifying the default `log_level` or in runtime
    by driving to the `level` signal or using a corresponding CSR.
    """
    # Allows to use Display inside FSM and to filter log messages by level (statically or dynamically)
    DEBUG = 0
    INFO  = 1
    WARN  = 2
    ERROR = 3
    NONE  = 4

    def __init__(self, log_level=INFO, clk_freq=None):
        self.ops = []
        self.level = Signal(reset=log_level, max=self.NONE)
        self.time_ps = None
        if clk_freq is not None:
            self.time_ps = Signal(64)
            cnt = Signal(64)
            self.sync += cnt.eq(cnt + 1)
            self.comb += self.time_ps.eq(cnt * int(1e12/clk_freq))

    def debug(self, fmt, *args, **kwargs):
        return self.log("[DEBUG] " + fmt, *args, level=self.DEBUG, **kwargs)

    def info(self, fmt, *args, **kwargs):
        return self.log("[INFO] " + fmt, *args, level=self.INFO, **kwargs)

    def warn(self, fmt, *args, **kwargs):
        return self.log("[WARN] " + fmt, *args, level=self.WARN, **kwargs)

    def error(self, fmt, *args, **kwargs):
        return self.log("[ERROR] " + fmt, *args, level=self.ERROR, **kwargs)

    def log(self, fmt, *args, level=DEBUG, once=True):
        cond = Signal()
        if once:  # make the condition be triggered only on rising edge
            condition = edge(self, cond)
        else:
            condition = cond

        self.ops.append((level, condition, fmt, args))
        return cond.eq(1)

    def add_csrs(self):
        self._level = CSRStorage(len(self.level), reset=self.level.reset.value)
        self.comb += self.level.eq(self._level.storage)

    def do_finalize(self):
        for level, cond, fmt, args in self.ops:
            if self.time_ps is not None:
                fmt = f"[%16d ps] {fmt}"
                args = (self.time_ps, *args)
            self.sync += If((level >= self.level) & cond, Display(fmt, *args))
