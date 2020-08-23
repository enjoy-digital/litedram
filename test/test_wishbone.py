#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from litex.gen.sim import run_simulation
from litex.soc.interconnect import wishbone

from litedram.frontend.wishbone import LiteDRAMWishbone2Native
from litedram.common import LiteDRAMNativePort

from test.common import DRAMMemory, MemoryTestDataMixin


class TestWishbone(MemoryTestDataMixin, unittest.TestCase):
    def wishbone_readback_test(self, pattern, mem_expected, wishbone, port, base_address=0):
        class DUT(Module):
            def __init__(self):
                self.port = port
                self.wb   = wishbone
                self.submodules += LiteDRAMWishbone2Native(
                    wishbone     = self.wb,
                    port         = self.port,
                    base_address = base_address)
                self.mem = DRAMMemory(port.data_width, len(mem_expected))

        def main_generator(dut):
            for adr, data in pattern:
                yield from dut.wb.write(adr, data)
                data_r = (yield from dut.wb.read(adr))
                self.assertEqual(data_r, data)

        dut = DUT()
        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
        ]
        run_simulation(dut, generators, vcd_name='sim.vcd')
        self.assertEqual(dut.mem.mem, mem_expected)

    def test_wishbone_8bit(self):
        # Verify Wishbone with 8-bit data width.
        data = self.pattern_test_data["8bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=8)
        port = LiteDRAMNativePort("both", address_width=30, data_width=8)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit(self):
        # Verify Wishbone with 32-bit data width.
        data = self.pattern_test_data["32bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_64bit(self):
        # Verify Wishbone with 64-bit data width.
        data = self.pattern_test_data["64bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=64)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_64bit_to_32bit(self):
        # Verify Wishbone with 64-bit data width down-converted to 32-bit data width.
        data = self.pattern_test_data["64bit_to_32bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit_to_8bit(self):
        # Verify Wishbone with 32-bit data width down-converted to 8-bit data width.
        data = self.pattern_test_data["32bit_to_8bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=8)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_8bit_to_32bit(self):
        # Verify Wishbone with 8-bit data width up-converted to 32-bit data width.
        data = self.pattern_test_data["8bit_to_32bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=8)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit_to_64bit(self):
        # Verify Wishbone with 32-bit data width up-converted to 64-bit data width.
        data = self.pattern_test_data["32bit_to_64bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=64)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit_base_address(self):
        # Verify Wishbone with 32-bit data width and non-zero base address.
        data   = self.pattern_test_data["32bit"]
        wb     = wishbone.Interface(adr_width=30, data_width=32)
        port   = LiteDRAMNativePort("both", address_width=30, data_width=32)
        origin = 0x10000000
        # add offset (in data words)
        pattern = [(adr + origin//(32//8), data) for adr, data in data["pattern"]]
        self.wishbone_readback_test(pattern, data["expected"], wb, port, base_address=origin)

    def test_wishbone_64bit_to_32bit_base_address(self):
        # Verify Wishbone with 64-bit data width down-converted to 32-bit data width and non-zero base address.
        data    = self.pattern_test_data["64bit_to_32bit"]
        wb      = wishbone.Interface(adr_width=30, data_width=64)
        port    = LiteDRAMNativePort("both", address_width=30, data_width=32)
        origin  = 0x10000000
        pattern = [(adr + origin//(64//8), data) for adr, data in data["pattern"]]
        self.wishbone_readback_test(pattern, data["expected"], wb, port, base_address=origin)

    def test_wishbone_32bit_to_8bit_base_address(self):
        # Verify Wishbone with 32-bit data width down-converted to 8-bit data width and non-zero base address.
        data    = self.pattern_test_data["32bit_to_8bit"]
        wb      = wishbone.Interface(adr_width=30, data_width=32)
        port    = LiteDRAMNativePort("both", address_width=30, data_width=8)
        origin  = 0x10000000
        pattern = [(adr + origin//(32//8), data) for adr, data in data["pattern"]]
        self.wishbone_readback_test(pattern, data["expected"], wb, port, base_address=origin)
