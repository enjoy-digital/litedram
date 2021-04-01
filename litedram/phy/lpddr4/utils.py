#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from functools import reduce
from operator import or_

from migen import *

from litex.soc.interconnect.csr import CSRStorage, AutoCSR

from litedram.common import TappedDelayLine


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
