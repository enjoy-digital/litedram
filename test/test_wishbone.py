# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import unittest

from migen import *
from litex.gen.sim import run_simulation
from litex.soc.interconnect import wishbone

from litedram.frontend.wishbone import LiteDRAMWishbone2Native
from litedram.common import LiteDRAMNativePort

from test.common import DRAMMemory, seed_to_data


class TestWishbone(unittest.TestCase):
    def test_wishbone_data_width_not_smaller(self):
        with self.assertRaises(AssertionError):
            wb = wishbone.Interface(data_width=32)
            port = LiteDRAMNativePort("both", address_width=32, data_width=wb.data_width * 2)
            LiteDRAMWishbone2Native(wb, port)

    def wishbone_readback_test(self, pattern, wishbone, port, mem_depth=64, **kwargs):
        class DUT(Module):
            def __init__(self):
                self.port = port
                self.wb = wishbone
                self.submodules += LiteDRAMWishbone2Native(self.wb, self.port, **kwargs)
                self.mem = DRAMMemory(port.data_width, mem_depth)

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
        run_simulation(dut, generators)

        mem_expected = [0] * mem_depth
        for adr, data in pattern:
            mem_expected[adr] = data
        self.assertEqual(dut.mem.mem, mem_expected)

    def test_wishbone(self):
        pattern = [(adr, seed_to_data(adr, nbits=32)) for adr in range(16)]
        wb = wishbone.Interface(data_width=32, adr_width=30)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_readback_test(pattern, wb, port)
