#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import re
import math
from fractions import Fraction
from functools import reduce
from operator import or_
from collections import defaultdict

from migen import *

from litex.soc.interconnect import stream

from litedram.common import TappedDelayLine


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
    def __init__(self, dw, slp, cycles, i=None, o=None, register=True):
        self.i = Signal(dw, name='i') if i is None else i
        self.o = Signal(dw, name='o') if o is None else o

        assert cycles >= 1, cycles
        assert 0 <= slp <= cycles*dw-1, (slp, cycles, dw)
        slp = (cycles*dw-1) - slp

        # # #

        self.r = r = Signal((cycles+1)*dw, reset_less=True)
        if register:
            self.sync += r.eq(Cat(r[dw:], self.i))
        else:
            reg = Signal(cycles*dw, reset_less=True)
            # Cat with slice of len=0 generates incorrect Verilog
            if len(reg[dw:]) > 0:
                self.sync += reg.eq(Cat(reg[dw:], self.i))
            else:
                self.sync += reg.eq(self.i)
            self.comb += r.eq(Cat(reg, self.i))
        self.comb += self.o.eq(r[slp+1:dw+slp+1])

    @staticmethod
    def min_cycles(slp, dw):
        """Minimum number of cycles to be able to use given bitslip values"""
        return math.ceil((slp + 1) / dw)


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
        assert cmd_nphases_span <= nphases

        # # #

        # Number of phases (before the current one) we need to check for overlaps
        n_previous = cmd_nphases_span - 1
        # Number of bits to slip CA per phase (how many CA output bits are equivalent to 1 CS output bit)
        assert ca_ser_width % cs_ser_width == 0, f"Non-integer CA:CS output width ratio: {ca_ser_width % cs_ser_width}"
        ca_phase_slip = ca_ser_width // cs_ser_width

        # Create a history of valid adapters used for masking overlapping ones
        valids = ConstBitSlip(dw=nphases, slp=0, cycles=1, register=False)
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
            cs_bs = ConstBitSlip(dw=cs_ser_width, slp=phase, cycles=1)
            self.submodules += cs_bs
            cs_mask = Replicate(allowed, len(cs_bs.i))
            self.comb += cs_bs.i.eq(Cat(adapter.cs) & cs_mask),
            cs_per_adapter.append(cs_bs.o)

            # For CA we need to do the same for each bit
            ca_bits = []
            for bit in range(ca_nbits):
                ca_bs = ConstBitSlip(dw=ca_ser_width, slp=phase*ca_phase_slip, cycles=1)
                self.submodules += ca_bs
                ca_bit_hist = [ca[bit] for ca in adapter.ca]
                ca_mask = Replicate(allowed, len(ca_bs.o))
                self.comb += ca_bs.i.eq(Cat(*ca_bit_hist) & ca_mask),
                ca_per_adapter[bit].append(ca_bs.o)

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
    # TODO: make dynamic (0 for register=False)
    LATENCY = 1

    def __init__(self, clkdiv, clk, i_dw, o_dw, i=None, o=None, reset=None, register=True,
            reset_cnt=-1, name=None):
        assert i_dw > o_dw, (i_dw, o_dw)
        assert i_dw % o_dw == 0, (i_dw, o_dw)
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
        if register:
            i_d = Signal.like(self.i)
            sd_clkdiv += i_d.eq(self.i)
            i = i_d
        i_array = Array([i[n*o_dw:(n+1)*o_dw] for n in range(ratio)])
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
        assert i_dw < o_dw, (i_dw, o_dw)
        assert o_dw % i_dw == 0, (i_dw, o_dw)
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


class HoldValid(Module):
    """Hold input data until ready

    Acts more or less like PipeValid with 0 latency. Data on source becomes valid in the same
    cycle on which it is valid on sink. In the next cycle the data is latched to a buffer and
    the data from buffer is presented on source. After source.ready, it resets back to sink data.
    """
    def __init__(self, layout):
        self.sink = stream.Endpoint(layout)
        self.buf = stream.Endpoint(layout)
        self.source = stream.Endpoint(layout)

        self.sync += [
            If(self.buf.ready,
                self.buf.valid.eq(0),
            ).Elif(self.sink.valid,
                self.buf.valid.eq(1),
                self.buf.payload.eq(self.sink.payload),
                self.buf.param.eq(self.sink.param),
            ),
        ]

        self.comb += [
            If(self.buf.valid,
                self.buf.connect(self.source),
            ).Else(
                self.sink.connect(self.source),
            ),
        ]
