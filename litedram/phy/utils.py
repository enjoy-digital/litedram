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
from litex.soc.interconnect.csr import CSRStorage, AutoCSR

from litedram.common import TappedDelayLine, Settings, PhySettings
from litedram.phy.dfi import Interface as DFIInterface, phase_description


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
                setattr(self, o, Signal(pad.width, name=o))
                setattr(self, i, Signal(pad.width, name=i))
                setattr(self, oe, Signal(name=oe))
                self.comb += If(getattr(self, oe),
                    getattr(self, pad.name).eq(getattr(self, o))
                ).Else(
                    getattr(self, pad.name).eq(getattr(self, i))
                )
            else:
                setattr(self, pad.name, Signal(pad.width, name=pad.name))


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
    LATENCY = 1

    def __init__(self, clkdiv, clk, i_dw, o_dw, i=None, o=None, reset=None, reset_cnt=-1, name=None):
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


class SimSerDesMixin:
    """Helper class for easier (de-)serialization to simulation pads."""
    def ser(self, *, i, o, clkdiv, clk, name="", **kwargs):
        assert len(o) == 1
        kwargs = dict(i=i, i_dw=len(i), o=o, o_dw=1, clk=clk, clkdiv=clkdiv,
            name=f"ser_{name}".strip("_"), **kwargs)
        self.submodules += Serializer(**kwargs)

    def des(self, *, i, o, clkdiv, clk, name="", **kwargs):
        assert len(i) == 1
        kwargs = dict(i=i, i_dw=1, o=o, o_dw=len(o), clk=clk, clkdiv=clkdiv,
            name=f"des_{name}".strip("_"), **kwargs)
        self.submodules += Deserializer(**kwargs)


class DFIRateConverter(Module):
    # do the clock domain adjustment
    """Converts between DFI interfaces running at different clock frequencies

    This module allows to convert DFI interface `phy_dfi` running at higher clock frequency
    into a DFI interface running at `ratio` lower frequency. The new DFI has `ratio` more
    phases and the commands on the following phases of the new DFI will be serialized to
    following phases/clocks of `phy_dfi` (phases first, then clock cycles).

    Data must be serialized/deserialized in such a way that a whole burst on `phy_dfi` is
    sent in a single `clk` cycle. For this reason, the new DFI interface will have `ratio`
    less databits. For example, with phy_dfi(nphases=2, databits=32) and ratio=4 the new
    DFI will have nphases=8, databits=8. This results in 8*8=64 bits in `clkdiv` translating
    into 2*32=64 bits in `clk`. This means that only a single cycle of `clk` per `clkdiv`
    cycle carries the data (by default cycle 0). This can be modified by passing values
    different than 0 for `write_delay`/`read_delay` and may be needed to properly align
    write/read latency of the original PHY and the wrapper.
    """
    def __init__(self, phy_dfi, *, clkdiv, clk, ratio, serdes_reset_cnt=-1, write_delay=0, read_delay=0):
        assert len(phy_dfi.p0.wrdata) % ratio == 0
        assert 0 <= write_delay < ratio, f"Data can be delayed up to {ratio} clk cycles"
        assert 0 <= read_delay < ratio, f"Data can be delayed up to {ratio} clk cycles"

        phase_params = dict(
            addressbits = len(phy_dfi.p0.address),
            bankbits = len(phy_dfi.p0.bank),
            nranks = len(phy_dfi.p0.cs_n),
            databits = len(phy_dfi.p0.wrdata) // ratio,
        )
        self.dfi = DFIInterface(nphases=ratio * len(phy_dfi.phases), **phase_params)

        sd_clk = getattr(self.sync, clk)

        wr_delayed = ["wrdata", "wrdata_mask"]
        rd_delayed = ["rddata", "rddata_valid"]

        for name, width, dir in phase_description(**phase_params):
            # all signals except write/read
            if name in wr_delayed + rd_delayed:
                continue
            # on each clk phase
            for pi, phase_s in enumerate(phy_dfi.phases):
                sig_s = getattr(phase_s, name)
                assert len(sig_s) == width

                # data from each clkdiv phase
                sigs_m = []
                for j in range(ratio):
                    phase_m = self.dfi.phases[pi + len(phy_dfi.phases)*j]
                    sigs_m.append(getattr(phase_m, name))

                assert dir == DIR_M_TO_S
                ser = Serializer(
                    clkdiv     = clkdiv,
                    clk       = clk,
                    i_dw      = ratio*width,
                    o_dw      = width,
                    i         = Cat(sigs_m),
                    o         = sig_s,
                    reset_cnt = serdes_reset_cnt,
                    name      = name,
                )
                self.submodules += ser

        # TODO: it should be possible to get rid of Serializer/Deserializer for read/write

        # wrdata
        for name, width, dir in phase_description(**phase_params):
            if name not in wr_delayed:
                continue
            for pi, phase_s in enumerate(phy_dfi.phases):
                sig_s = getattr(phase_s, name)
                sig_m = Signal(len(sig_s) * ratio)

                sigs_m = []
                for j in range(ratio):
                    phase_m = self.dfi.phases[pi*ratio + j]
                    sigs_m.append(getattr(phase_m, name))

                width = len(Cat(sigs_m))
                self.comb += sig_m[write_delay*width:(write_delay+1)*width].eq(Cat(sigs_m))

                o = Signal.like(sig_s)
                ser = Serializer(
                    clkdiv     = clkdiv,
                    clk       = clk,
                    i_dw      = len(sig_m),
                    o_dw      = len(sig_s),
                    i         = sig_m,
                    o         = o,
                    reset_cnt = serdes_reset_cnt,
                    name      = name,
                )
                self.submodules += ser

                self.comb += sig_s.eq(o)

        # rddata
        for name, width, dir in phase_description(**phase_params):
            if name not in rd_delayed:
                continue
            for pi, phase_s in enumerate(phy_dfi.phases):
                sig_s = getattr(phase_s, name)

                sig_m = Signal(ratio * len(sig_s))
                sigs_m = []
                for j in range(ratio):
                    phase_m = self.dfi.phases[pi*ratio + j]
                    sigs_m.append(getattr(phase_m, name))

                des = Deserializer(
                    clkdiv    = clkdiv,
                    clk       = clk,
                    i_dw      = len(sig_s),
                    o_dw      = len(sig_m),
                    i         = sig_s,
                    o         = sig_m,
                    reset_cnt = serdes_reset_cnt,
                    name      = name,
                )
                self.submodules += des

                if name == "rddata_valid":
                    self.comb += Cat(sigs_m).eq(Replicate(sig_m[read_delay], ratio))
                else:
                    out_width = len(Cat(sigs_m))
                    sig_m_window = sig_m[read_delay*out_width:(read_delay + 1)*out_width]
                    self.comb += Cat(sigs_m).eq(sig_m_window)

    @staticmethod
    def wrap(phy, *, clkdiv, clk, ratio, cd_mapping=None, **kwargs):
        # we need to recalculate write/read latencies such that the controller sends/receives
        # data with correct latencies at `clkdiv`
        write_delay = phy.settings.write_latency % ratio
        read_delay = phy.settings.read_latency % ratio

        print(f"{write_delay=}")
        print(f"{read_delay=}")

        converter = DFIRateConverter(phy.dfi, clkdiv=clkdiv, clk=clk, ratio=ratio,
            write_delay=write_delay, read_delay=read_delay, **kwargs)

        if cd_mapping is None:
            cd_mapping = {"sys": clkdiv}
        else:
            cd_mapping["sys"] = clkdiv
        phy.submodules.dfi_converter = ClockDomainsRenamer(cd_mapping)(converter)

        # replace PHY attributes
        phy._dfi = phy.dfi
        phy.dfi = converter.dfi
        phy.nphases = len(converter.dfi.phases)

        phy._settings = phy.settings
        phy.settings = PhySettings(
            phytype       = phy._settings.phytype,
            memtype       = phy._settings.memtype,
            databits      = phy._settings.databits,
            dfi_databits  = len(phy.dfi.p0.wrdata),
            nranks        = phy._settings.nranks,
            nphases       = phy.nphases,
            rdphase       = phy._settings.rdphase,
            wrphase       = phy._settings.wrphase,
            cl            = phy._settings.cl,
            cwl           = phy._settings.cwl,
            read_latency  = phy._settings.read_latency//ratio + Serializer.LATENCY + Deserializer.LATENCY,
            write_latency = phy._settings.write_latency//ratio,
            cmd_latency   = phy._settings.cmd_latency,
            cmd_delay     = phy._settings.cmd_delay,
        )

        # def get_phase(phase_name):
        #     phase = getattr(clk_settings, phase_name)
        #     storage = getattr(phase, "storage", None)
        #     return storage.reset if storage is not None else phase
        # rdphase = get_phase("rdphase")
        # wrphase = get_phase("wrphase")



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
