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


class TestAvalon(MemoryTestDataMixin, unittest.TestCase):
    def avalon_readback_test(self, pattern, mem_expected, avalon, port, base_address=0):
        class DUT(Module):
            def __init__(self):
                self.port   = port
                self.avalon = avalon
                self.submodules += LiteDRAMAvalonMM2Native(
                    avalon       = self.avalon,
                    port         = self.port,
                    base_address = base_address)
                self.mem = DRAMMemory(port.data_width, len(mem_expected))

        def main_generator(dut):
            for adr, data in pattern:
                yield from dut.avalon.bus_write(adr, data)
                data_r = (yield from dut.avalon.bus_read(adr))
                self.assertEqual(data_r, data)

        dut = DUT()
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

    @unittest.skip
    def test_avalon_64bit_to_32bit(self):
        # Verify AvalonMM with 64-bit data width down-converted to 32-bit data width.
        data = self.pattern_test_data["64bit_to_32bit"]
        avl  = avalon.AvalonMMInterface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.avalon_readback_test(data["pattern"], data["expected"], avl, port)

    @unittest.skip
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

    @unittest.skip
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
