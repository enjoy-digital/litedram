#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Generated native core interfaces, complete wiring and invalid-layout rejection."""

import unittest

from dataclasses import replace
from migen import Instance, Record
from migen.sim import run_simulation

from litedram.phy.usnative.core import emit_core
from litedram.phy.usnative.sidebands import NativeSidebands, sideband_plan
from test.test_usnative_layout import layout_fixture


class TestUSNativeCore(unittest.TestCase):
    def test_width_bank_and_riu_coverage(self):
        for wide in (False, True):
            sites, auxiliary = layout_fixture(wide)
            core = emit_core('native_test', sites, auxiliary,
                             family='ULTRASCALE_PLUS', refclk_mhz=2400)
            self.assertEqual(core.ports['pll_clk'][1], 2 if wide else 1)
            self.assertEqual(core.ports['data_tristate'][1], 4 if wide else 2)
            self.assertEqual(core.verilog.count('RXTX_BITSLICE #('), len(core.layout.slices))
            self.assertEqual(core.verilog.count('BITSLICE_CONTROL #('), len(core.layout.controls))
            self.assertEqual(core.verilog.count('TX_BITSLICE_TRI #('), len(core.layout.controls))
            self.assertEqual(core.verilog.count('RIU_OR #('), len(core.layout.riu_bytes))
            for control in core.layout.controls:
                self.assertIn(f'LOC = "{control}"', core.verilog)
            self.assertNotIn('xem8320', core.verilog)

    def test_explicit_sideband_partition_and_mode_checks(self):
        sites, auxiliary = layout_fixture()
        sites.update({('par', 0): sites['dm', 0], ('alert_n', 0): sites['dm', 1]})
        plan = sideband_plan(sites, mr2=0x20, mr5=1 << 10)
        self.assertEqual(set(plan.native_sites) | set(plan.parity) | set(plan.alert), set(sites))
        self.assertEqual(plan.parity, (('par', 0),))
        self.assertEqual(plan.alert, (('alert_n', 0),))
        for mr2, mr5 in ((1 << 12, 0), (0, 1), (0, 7), (-1, 0), (0, True)):
            with self.assertRaises(ValueError):
                sideband_plan(sites, mr2=mr2, mr5=mr5)
        with self.assertRaises(ValueError):
            sideband_plan({**sites, ('parity', 0): sites['par', 0]}, mr2=0, mr5=0)

    def test_unknown_signal_cannot_disappear(self):
        sites, auxiliary = layout_fixture()
        sites['unknown', 0] = sites['dm', 0]
        with self.assertRaisesRegex(ValueError, 'Unsupported signal'):
            emit_core('native_test', sites, auxiliary, family='ULTRASCALE_PLUS', refclk_mhz=2400)

    def test_alert_is_masked_during_calibration(self):
        sites, _ = layout_fixture()
        sites['alert_n', 0] = replace(sites['dm', 0], position=6)
        plan = sideband_plan(sites, mr2=0, mr5=1024)
        self.assertTrue(plan.alert_unavailable_during_calibration)
        dut = NativeSidebands(Record([('alert_n', 1)]), plan)
        fragment = dut.get_fragment()
        fragment.specials = {s for s in fragment.specials if not isinstance(s, Instance)}
        def bench():
            # The physical pin is unavailable/low while BISC owns its site.
            yield dut._raw_alert_n.eq(0)
            for _ in range(5):
                yield
            self.assertEqual((yield dut.active), 0)
            self.assertEqual((yield dut.seen), 0)
            yield dut.enable.eq(1)
            for _ in range(3):
                yield
            self.assertEqual((yield dut.active), 1)
            self.assertEqual((yield dut.seen), 1)
            yield dut.clear.eq(1)
            for _ in range(2):
                yield
            self.assertEqual((yield dut.seen), 1)  # Active input wins over clear.
            yield dut.clear.eq(0)
            yield dut._raw_alert_n.eq(1)
            for _ in range(5):
                yield
            self.assertEqual((yield dut.active), 0)
            self.assertEqual((yield dut.seen), 1)
            yield dut.clear.eq(1)
            for _ in range(2):
                yield
            self.assertEqual((yield dut.seen), 0)
            yield dut.enable.eq(0)
            yield dut.clear.eq(0)
            yield dut._raw_alert_n.eq(0)
            for _ in range(5):
                yield
            self.assertEqual((yield dut.active), 0)
            self.assertEqual((yield dut.seen), 0)
        run_simulation(fragment, bench())
