#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from litex.gen.sim import run_simulation
from litex.soc.interconnect import avalon

from litedram.frontend.avalon import LiteDRAMAvalonMM2Native
from litedram.common import LiteDRAMNativePort

from test.common import DRAMMemory, MemoryTestDataMixin

class DUT(Module):
    def __init__(self, port, avalon, base_address=0x0, mem_expected=[]):
        self.port   = port
        self.avalon = avalon
        self.submodules += LiteDRAMAvalonMM2Native(
            avalon       = self.avalon,
            port         = self.port,
            base_address = base_address)
        self.mem = DRAMMemory(port.data_width, len(mem_expected))

class TestAvalon(MemoryTestDataMixin, unittest.TestCase):
    def avalon_readback_test(self, pattern, mem_expected, avalon, port, base_address=0):
        def main_generator(dut):
            for adr, data in pattern:
                yield from dut.avalon.bus_write(adr, data)
                data_r = (yield from dut.avalon.bus_read(adr))
                self.assertEqual(data_r, data)

        dut = DUT(port, avalon, base_address, mem_expected)
        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
        ]
        run_simulation(dut, generators, vcd_name='sim.vcd')
        self.assertEqual(dut.mem.mem, mem_expected)

    def test_avalon_8bit(self):
        # Verify AvalonMM with 8-bit data width.
        data = self.pattern_test_data["8bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=8)
        port = LiteDRAMNativePort("both", address_width=30, data_width=8)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_32bit(self):
        # Verify AvalonMM with 32-bit data width.
        data = self.pattern_test_data["32bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_64bit(self):
        # Verify AvalonMM with 64-bit data width.
        data = self.pattern_test_data["64bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=64)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_64bit_to_32bit(self):
        # Verify AvalonMM with 64-bit data width down-converted to 32-bit data width.
        data = self.pattern_test_data["64bit_to_32bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_64bit_to_32bit_base_address(self):
        # Verify AvalonMM with 64-bit data width down-converted to 32-bit data width and non-zero base address.
        data    = self.pattern_test_data["64bit_to_32bit"]
        avl     = avalon.AvalonMMInterface(adr_width=30, data_width=64)
        port    = LiteDRAMNativePort("both", address_width=30, data_width=32)
        origin  = 0x10000000
        pattern = [(adr + origin//(64//8), data) for adr, data in data["pattern"]]
        self.avalon_readback_test(pattern, data["expected"], avl, port, base_address=origin)

    def test_avalon_32bit_to_8bit(self):
        # Verify AvalonMM with 32-bit data width down-converted to 8-bit data width.
        data = self.pattern_test_data["32bit_to_8bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=8)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_32bit_to_8bit_base_address(self):
        # Verify AvalonMM with 32-bit data width down-converted to 8-bit data width and non-zero base address.
        data    = self.pattern_test_data["32bit_to_8bit"]
        avl     = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port    = LiteDRAMNativePort("both", address_width=30, data_width=8)
        origin  = 0x10000000
        pattern = [(adr + origin//(32//8), data) for adr, data in data["pattern"]]
        self.avalon_readback_test(pattern, data["expected"], avl, port, base_address=origin)

    def test_avalon_8bit_to_32bit(self):
        # Verify AvalonMM with 8-bit data width up-converted to 32-bit data width.
        data = self.pattern_test_data["8bit_to_32bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=8)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_32bit_to_64bit(self):
        # Verify AvalonMM with 32-bit data width up-converted to 64-bit data width.
        data = self.pattern_test_data["32bit_to_64bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=64)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_32bit_to_128bit(self):
        # Verify AvalonMM with 32-bit data width up-converted to 128-bit data width.
        data = self.pattern_test_data["32bit_to_128bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=128)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_32bit_to_256bit(self):
        # Verify AvalonMM with 32-bit data width up-converted to 128-bit data width.
        data = self.pattern_test_data["32bit_to_256bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=256)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    def test_avalon_32bit_base_address(self):
        # Verify AvalonMM with 32-bit data width and non-zero base address.
        data   = self.pattern_test_data["32bit"]
        avl    = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port   = LiteDRAMNativePort("both", address_width=30, data_width=32)
        origin = 0x10000000
        # add offset (in data words)
        pattern = [(adr + origin//(32//8), data) for adr, data in data["pattern"]]
        self.avalon_readback_test(pattern, data["expected"], avl, port, base_address=origin)

    def test_avalon_burst(self):
        data = [0x01234567, 0x89abcdef, 0xdeadbeef, 0xc0ffee00, 0x76543210]

        def main_generator(dut):
            yield from dut.avalon.bus_write(0x0, data)
            yield
            self.assertEqual((yield from dut.avalon.bus_read(0x0000, burstcount=5)), 0x01234567)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0x89abcdef)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0xdeadbeef)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0xc0ffee00)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0x76543210)
            yield
            yield
            yield
            yield
            self.assertEqual((yield from dut.avalon.bus_read(0x0000)), 0x01234567)
            self.assertEqual((yield from dut.avalon.bus_read(0x0001)), 0x89abcdef)
            self.assertEqual((yield from dut.avalon.bus_read(0x0002)), 0xdeadbeef)
            self.assertEqual((yield from dut.avalon.bus_read(0x0003)), 0xc0ffee00)
            self.assertEqual((yield from dut.avalon.bus_read(0x0004)), 0x76543210)
            yield
            yield

        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        dut = DUT(port, avl, base_address=0x0, mem_expected=[0x4567, 0x0123, 0xcdef, 0x89ab, 0xbeef, 0xdead, 0xee00, 0xc0ff, 0x3210, 0x7654])
        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
        ]

        run_simulation(dut, generators, vcd_name='sim.vcd')
        self.assertEqual(dut.mem.mem, data + [0,0,0,0,0])

    def test_avalon_burst_downconvert(self):
        data = [0x01234567, 0x89abcdef, 0xdeadbeef, 0xc0ffee00, 0x76543210, 0xfedcba98]

        def main_generator(dut):
            yield from dut.avalon.bus_write(0x0, data)
            yield
            self.assertEqual((yield from dut.avalon.bus_read(0x0000, burstcount=6)), 0x01234567)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0x89abcdef)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0xdeadbeef)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0xc0ffee00)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0x76543210)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0xfedcba98)
            yield
            yield
            yield
            yield
            self.assertEqual((yield from dut.avalon.bus_read(0x0000)), 0x01234567)
            self.assertEqual((yield from dut.avalon.bus_read(0x0001)), 0x89abcdef)
            self.assertEqual((yield from dut.avalon.bus_read(0x0002)), 0xdeadbeef)
            self.assertEqual((yield from dut.avalon.bus_read(0x0003)), 0xc0ffee00)
            self.assertEqual((yield from dut.avalon.bus_read(0x0004)), 0x76543210)
            yield
            yield

        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=32, data_width=16)
        dut = DUT(port, avl, base_address=0x0, mem_expected=data + 6 * [0])
        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
        ]

        run_simulation(dut, generators, vcd_name="avalon_" + self._testMethodName + ".vcd")
        self.assertEqual(dut.mem.mem, [0x4567, 0x0123, 0xcdef, 0x89ab, 0xbeef, 0xdead, 0xee00, 0xc0ff, 0x3210, 0x7654, 0xba98, 0xfedc])

    def test_avalon_burst_upconvert(self):
        data = [0x01234567, 0x89abcdef, 0xdeadbeef, 0xc0ffee00, 0x76543210, 0xfedcba98]

        def main_generator(dut):
            yield from dut.avalon.bus_write(0x0, data)
            yield
            self.assertEqual((yield from dut.avalon.bus_read(0x0000, burstcount=6)), 0x01234567)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0x89abcdef)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0xdeadbeef)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0xc0ffee00)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0x76543210)
            self.assertEqual((yield dut.avalon.readdatavalid), 1)
            self.assertEqual((yield from dut.avalon.continue_read_burst()), 0xfedcba98)
            yield
            yield
            yield
            yield
            self.assertEqual((yield from dut.avalon.bus_read(0x0000)), 0x01234567)
            self.assertEqual((yield from dut.avalon.bus_read(0x0001)), 0x89abcdef)
            self.assertEqual((yield from dut.avalon.bus_read(0x0002)), 0xdeadbeef)
            self.assertEqual((yield from dut.avalon.bus_read(0x0003)), 0xc0ffee00)
            self.assertEqual((yield from dut.avalon.bus_read(0x0004)), 0x76543210)
            self.assertEqual((yield from dut.avalon.bus_read(0x0005)), 0xfedcba98)
            yield
            yield

        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=64)
        dut = DUT(port, avl, base_address=0x0, mem_expected=data)
        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
        ]

        run_simulation(dut, generators, vcd_name="avalon_" + self._testMethodName + ".vcd")
        self.assertEqual(dut.mem.mem, [0x89abcdef01234567, 0xc0ffee00deadbeef, 0xfedcba9876543210, 0, 0, 0])
