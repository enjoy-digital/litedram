#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Paired-controller digital compatibility with real USPDDRPHY settings.

The behavioral PHY substitutes for physical serializers/delays; these tests
check the DFI scheduling contract, not analog calibration or FPGA timing.
"""

import unittest

from copy import copy

from migen import Module, Record, passive

from litedram.core.controller import ControllerSettings, LiteDRAMController
from litedram.core.crossbar import LiteDRAMCrossbar
from litedram.frontend.native_benchmark import NativeDMABenchmark
from litedram.frontend.paired import PairedPort
from litedram.init import get_ddr4_phy_init_sequence
from litedram.phy.model import SDRAMPHYModel
from litedram.phy.usddrphy import USPDDRPHY
from test.test_native_benchmark import simulate
from test.test_paired_controller import SmallMemory


class PairedUSPDDRPHYTest(unittest.TestCase):
    def run_profile(self, frequency, **latencies):
        # Single-rank x16 DDR4: A14/A15/A16 share WE/CAS/RAS pins.
        # Use local signal pads so this test does not depend on board packages.
        pads = Record([
            ("a", 14), ("ba", 2), ("bg", 1),
            ("ras_n", 1), ("cas_n", 1), ("we_n", 1),
            ("cs_n", 1), ("act_n", 1), ("cke", 1), ("odt", 1),
            ("reset_n", 1), ("clk_p", 1), ("clk_n", 1),
            ("dq", 16), ("dm", 2), ("dqs_p", 2), ("dqs_n", 2),
        ], name="ddram")
        actual = USPDDRPHY(pads, memtype="DDR4",
            sys_clk_freq=frequency, iodelay_clk_freq=500e6, **latencies)
        actual.settings.tccd = 8
        settings = copy(actual.settings)
        # Freeze only runtime phase CSRs at their actual hardware reset values.
        settings.rdphase = actual._rdphase.storage.reset.value
        settings.wrphase = actual._wrphase.storage.reset.value
        module = SmallMemory(frequency, "1:4", speedgrade="2400")
        module.geom_settings.addressbits = 17
        self.assertEqual(module.timing_settings.tCCD, 2)
        sequence, _ = get_ddr4_phy_init_sequence(settings, module.timing_settings)
        mr6 = next(address for label, address, _, _, _ in sequence
                   if label == "Load Mode Register 6")
        self.assertEqual(mr6, 4 << 10)
        top = Module()
        top.submodules.phy = phy = SDRAMPHYModel(module, settings=settings, clk_freq=frequency)
        top.submodules.controller = controller = LiteDRAMController(settings,
            module.geom_settings, module.timing_settings, frequency,
            controller_settings=ControllerSettings(
                with_bank_group_interleaving=True, with_refresh=False))
        top.comb += controller.dfi.connect(phy.dfi)
        top.submodules.crossbar = crossbar = LiteDRAMCrossbar(controller.interface)
        top.submodules.writer = writer = PairedPort(
            [crossbar.get_port("write") for _ in range(2)], "write", depth=8)
        top.submodules.reader = reader = PairedPort(
            [crossbar.get_port("read") for _ in range(2)], "read", depth=8)
        top.submodules.dma = dma = NativeDMABenchmark(writer.port, reader.port,
            capacity=32768, fifo_depth=8, drained=writer.drained, databits=16)
        events = []

        @passive
        def monitor():
            previous = {}
            cycle = 0
            while True:
                for phase in controller.dfi.phases:
                    if not (yield phase.cas_n) and (yield phase.ras_n):
                        group = (yield phase.bank) >> 2
                        self.assertGreaterEqual(cycle - previous.get(group, -10), 2)
                        previous[group] = cycle
                        events.append(cycle)
                cycle += 1
                yield

        def main():
            yield dma.allowed.eq(1)
            yield dma._base.storage.eq(32)
            yield dma._length.storage.eq(512)
            for random in (0, 1):
                yield dma._random.storage.eq(random)
                yield dma._start.re.eq(1)
                yield
                yield dma._start.re.eq(0)
                yield
                for _ in range(1500):
                    if (yield dma._done.status):
                        break
                    yield
                self.assertEqual((yield dma._done.status), 1)
                self.assertEqual((yield dma._fault.status), 0)
                self.assertEqual((yield dma._errors.status), 0)
                self.assertEqual((yield writer.error), 0)
                self.assertEqual((yield reader.error), 0)
                self.assertEqual((yield dma._read_beats.status), 16)
                self.assertEqual((yield writer.drained), 1)
            self.assertEqual(len(events), 128)

        simulate(top, [main(), monitor()])

    def test_1000_default_latency(self):
        self.run_profile(125e6)

    def test_2000_default_latency(self):
        self.run_profile(250e6)
