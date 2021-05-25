#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
import itertools

from migen import *

from litedram.phy.utils import Serializer, Deserializer, Latency, chunks, bit

from litex.gen.sim import run_simulation as _run_simulation


def run_simulation(dut, generators, clocks, debug_clocks=False, **kwargs):
    """Wrapper that can be used to easily debug clock configuration"""

    if debug_clocks:
        class DUT(Module):
            def __init__(self, dut):
                self.submodules.dut = dut
                for clk in clocks:
                    setattr(self.clock_domains, "cd_{}".format(clk), ClockDomain(clk))
                    cd = getattr(self, 'cd_{}'.format(clk))
                    self.comb += cd.rst.eq(0)

                    s = Signal(4, name='dbg_{}'.format(clk))
                    sd = getattr(self.sync, clk)
                    sd += s.eq(s + 1)
        dut = DUT(dut)

    _run_simulation(dut, generators, clocks, **kwargs)


class TestSimSerializers(unittest.TestCase):
    def run_simulation(self, dut, generators, **kwargs):
        clocks = {
            "sys":          (64, 31),
            "sys_11_25":    (64, 29),  # aligned to sys8x_90 (phase shift of 11.25)
            "sys2x":        (32, 15),
            "sys8x":        ( 8,  3),
            "sys8x_ddr":    ( 4,  1),
            "sys8x_90":     ( 8,  1),
            "sys8x_90_ddr": ( 4,  3),
        }
        run_simulation(dut, generators, clocks, **kwargs)

    @staticmethod
    def data_generator(i, datas):
        for data in datas:
            yield i.eq(data)
            yield
        yield i.eq(0)
        yield

    @staticmethod
    def data_checker(o, datas, n, latency, yield1=False):
        if yield1:
            yield
        for _ in range(latency):
            yield
        for _ in range(n):
            datas.append((yield o))
            yield
        yield

    def serializer_test(self, *, data_width, datas, clk, clkdiv, latency, clkgen=None, clkcheck=None, **kwargs):
        clkgen = clkgen if clkgen is not None else clkdiv
        clkcheck = clkcheck if clkcheck is not None else clk

        received = []
        dut = Serializer(clk=clk, clkdiv=clkdiv, i_dw=data_width, o_dw=1)
        generators = {
            clkgen: self.data_generator(dut.i, datas),
            clkcheck: self.data_checker(dut.o, received, n=len(datas) * data_width, latency=latency * data_width, yield1=True),
        }
        self.run_simulation(dut, generators, **kwargs)

        received = list(chunks(received, data_width))
        datas  = [[bit(i, d) for i in range(data_width)] for d in datas]
        self.assertEqual(received, datas)

    def deserializer_test(self, *, data_width, datas, clk, clkdiv, latency, clkgen=None, clkcheck=None, **kwargs):
        clkgen = clkgen if clkgen is not None else clk
        clkcheck = clkcheck if clkcheck is not None else clkdiv

        datas = [[bit(i, d) for i in range(data_width)] for d in datas]

        received = []
        dut = Deserializer(clk=clk, clkdiv=clkdiv, i_dw=1, o_dw=data_width)
        generators = {
            clkgen: self.data_generator(dut.i, itertools.chain(*datas)),
            clkcheck: self.data_checker(dut.o, received, n=len(datas), latency=latency),
        }

        self.run_simulation(dut, generators, **kwargs)

        received = [[bit(i, d) for i in range(data_width)] for d in received]
        self.assertEqual(received, datas)

    DATA_8 = [0b11001100, 0b11001100, 0b00110011, 0b00110011, 0b10101010]
    DATA_16 = [0b1100110011001100, 0b0011001100110011, 0b0101010101010101]

    ARGS_8 = dict(
        data_width = 8,
        datas = DATA_8,
        clkdiv = "sys",
        clk = "sys8x",
        latency = Serializer.LATENCY,
    )

    ARGS_16 = dict(
        data_width = 16,
        datas = DATA_16,
        clkdiv = "sys",
        clk = "sys8x_ddr",
        latency = Serializer.LATENCY,
    )

    def _s(default, **kwargs):
        def test(self):
            new = default.copy()
            new.update(kwargs)
            self.serializer_test(**new)
        return test

    def _d(default, **kwargs):
        def test(self):
            new = default.copy()
            new["latency"] = Deserializer.LATENCY
            new.update(kwargs)
            self.deserializer_test(**new)
        return test

    test_sim_serializer_8 = _s(ARGS_8)
    test_sim_serializer_8_phase90 = _s(ARGS_8, clkdiv="sys_11_25", clk="sys8x_90")
    # when clkgen and clkdiv are not phase aligned (clkdiv is delayed), there will be lower latency
    test_sim_serializer_8_phase90_gen0 = _s(ARGS_8, clkdiv="sys_11_25", clk="sys8x_90", clkgen="sys", latency=Serializer.LATENCY - 1)
    test_sim_serializer_8_phase90_check0 = _s(ARGS_8, clkdiv="sys_11_25", clk="sys8x_90", clkcheck="sys8x")

    test_sim_serializer_16 = _s(ARGS_16)
    test_sim_serializer_16_phase90 = _s(ARGS_16, clkdiv="sys_11_25", clk="sys8x_90_ddr")
    test_sim_serializer_16_phase90_gen0 = _s(ARGS_16, clkdiv="sys_11_25", clk="sys8x_90_ddr", clkgen="sys", latency=Serializer.LATENCY - 1)
    test_sim_serializer_16_phase90_check0 = _s(ARGS_16, clkdiv="sys_11_25", clk="sys8x_90_ddr", clkcheck="sys8x_ddr")

    # for phase aligned clocks the latency will be bigger (preferably avoid phase aligned reading?)
    test_sim_deserializer_8 = _d(ARGS_8, latency=Deserializer.LATENCY + 1)
    test_sim_deserializer_8_check90 = _d(ARGS_8, clkcheck="sys_11_25")
    test_sim_deserializer_8_gen90_check90 = _d(ARGS_8, clkcheck="sys_11_25", clkgen="sys8x_90")
    test_sim_deserializer_8_phase90 = _d(ARGS_8, clkdiv="sys_11_25", clk="sys8x_90", latency=Deserializer.LATENCY + 1)
    test_sim_deserializer_8_phase90_check0 = _d(ARGS_8, clkdiv="sys_11_25", clk="sys8x_90", clkcheck="sys", latency=Deserializer.LATENCY + 1)

    test_sim_deserializer_16 = _d(ARGS_16, latency=Deserializer.LATENCY + 1)
    test_sim_deserializer_16_check90 = _d(ARGS_16, clkcheck="sys_11_25")
    test_sim_deserializer_16_gen90_check90 = _d(ARGS_16, clkcheck="sys_11_25", clkgen="sys8x_90_ddr")
    test_sim_deserializer_16_phase90 = _d(ARGS_16, clkdiv="sys_11_25", clk="sys8x_90_ddr", latency=Deserializer.LATENCY + 1)
    test_sim_deserializer_16_phase90_check0 = _d(ARGS_16, clkdiv="sys_11_25", clk="sys8x_90_ddr", clkcheck="sys", latency=Deserializer.LATENCY + 1)


class LatencyTests(unittest.TestCase):
    def test_latency_default_zero(self):
        l = Latency()
        self.assertEqual((l._sys.numerator, l._sys.denominator), (0, 1))

    def test_latency_sys_init(self):
        for n in [0, 1, 2, 4, 9]:
            l = Latency(sys=n)
            self.assertEqual((l._sys.numerator, l._sys.denominator), (n, 1))

    def test_latency_get_sys(self):
        l = Latency()
        self.assertEqual(l.sys, 0)
        for n in [0, 1, 2, 4, 9]:
            l = Latency(sys=n)
            self.assertEqual(l.sys, n)

    def test_latency_get_sysNx(self):
        l = Latency()
        self.assertEqual(l.sys2x, 0)
        for n in [0, 1, 2, 4, 9]:
            l = Latency(sys=n)
            self.assertEqual(l.sys2x, 2*n)
            self.assertEqual(l.sys3x, 3*n)

    def test_latency_set_sysNx(self):
        for n in [3, 6, 9]:
            l = Latency(sys3x=n)
            self.assertEqual(l.sys, n // 3)

    def test_latency_add(self):
        l = Latency(sys=2) + Latency(sys2x=3)
        self.assertEqual(l.sys2x, 4+3)
        l = Latency(sys2x=2, sys4x=3) + Latency(sys4x=1)
        self.assertEqual(l.sys4x, 8)
        self.assertEqual(l.sys2x, 4)
        self.assertEqual(l.sys, 2)

    def test_latency_error_on_get_fraction(self):
        l = Latency(sys=1, sys2x=1)
        with self.assertRaises(ValueError):
            l.sys  # would have to be 1.5
        l = Latency(sys3x=1, sys2x=1)
        for attr in "sys sys2x sys3x sys4x sys5x".split():
            with self.assertRaises(ValueError):
                getattr(l, attr)
        l.sys6x # ok
