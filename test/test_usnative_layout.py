#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Logical lane indices and calibration addressing from validated physical maps."""

import re
import unittest

from dataclasses import replace

from migen.sim import run_simulation

from litedram.phy.usnative.auxiliary import parse_auxiliary_map
from litedram.phy.usnative.fifo import NativeFIFORead
from litedram.phy.usnative.layout import native_layout
from test.test_usnative_auxiliary import fixture


def layout_fixture(wide=False):
    pins, sites, text = fixture()
    auxiliary = parse_auxiliary_map(pins, sites, text, vivado_version='2026.1')
    if wide:
        for (name, index), site in list(sites.items()):
            sites[name, index + (16 if name == 'dq' else 2)] = replace(site,
                bank=65, native_site=site.native_site.replace('X0', 'X8'),
                control_site=site.control_site.replace('X0', 'X8'))
        for control, aux in list(auxiliary.items()):
            new = control.replace('X0', 'X8')
            auxiliary[new] = replace(aux, control=new,
                tristate=aux.tristate.replace('X2', 'X9'), riu=aux.riu.replace('X2', 'X9'))
    return sites, auxiliary


class TestUSNativeLayout(unittest.TestCase):
    def plan(self, wide=False):
        sites, auxiliary = layout_fixture(wide)
        return native_layout(sites, auxiliary, family='ULTRASCALE_PLUS')

    def test_widths_and_lane_ownership(self):
        for wide in (False, True):
            layout = self.plan(wide)
            self.assertEqual(layout.databits, 32 if wide else 16)
            self.assertEqual(layout.native_word_bits, 256 if wide else 128)
            self.assertEqual(len(layout.banks), 2 if wide else 1)
            owned = [bit for lane in layout.lanes for bit in lane.dq]
            self.assertEqual(len(set(owned)), layout.databits)
            for lane in layout.lanes:
                self.assertEqual([layout.slices[bit] for bit in lane.dq],
                                 [('dq', i) for i in range(8*lane.index, 8*lane.index+8)])
                self.assertEqual(layout.slices[lane.strobe], ('dqs_p', lane.index))

    def test_mapping_is_order_independent(self):
        sites, auxiliary = layout_fixture(True)
        self.assertEqual(self.plan(True), native_layout(dict(reversed(list(sites.items()))),
            dict(reversed(list(auxiliary.items()))), family='ULTRASCALE_PLUS'))

    def test_x64_upper_lane_stalls_whole_word(self):
        sites, auxiliary = layout_fixture(True)
        def relocate(site):
            return re.sub(r'X(\d+)', lambda m: 'X' + str(int(m[1]) + 20), site)
        for (name, index), site in list(sites.items()):
            sites[name, index + (32 if name == 'dq' else 4)] = replace(site,
                bank=site.bank + 2, native_site=relocate(site.native_site),
                control_site=relocate(site.control_site))
        for control, aux in list(auxiliary.items()):
            new = relocate(control)
            auxiliary[new] = replace(aux, control=new,
                tristate=relocate(aux.tristate), riu=relocate(aux.riu))
        layout = native_layout(sites, auxiliary, family='ULTRASCALE_PLUS')
        self.assertEqual(layout.native_word_bits, 512)
        self.assertEqual(len(layout.lanes), 8)
        dut = NativeFIFORead(layout)
        def check():
            yield dut.ready.eq(1)
            yield dut.independent.eq(1)
            for lane in layout.lanes:
                yield dut.empty.eq(1 << lane.dq[-1])
                yield dut.software_control.eq(0)
                yield
                yield
                self.assertEqual((yield dut.read_enable), 0)
                yield dut.software_control.eq(1)
                yield
                yield
                self.assertEqual((yield dut.lane_drain), 255 ^ (1 << lane.index))
            yield dut.empty.eq(0)
            yield dut.ready.eq(0)
            yield
            yield
            self.assertEqual((yield dut.read_enable), 0)
        run_simulation(dut, check())

    def test_sidebands_and_missing_masks_fail_closed(self):
        sites, auxiliary = layout_fixture()
        for name in ('par', 'parity', 'alert_n'):
            with self.assertRaisesRegex(ValueError, 'Parity/alert'):
                native_layout({**sites, (name, 0): sites['dm', 0]}, auxiliary,
                              family='ULTRASCALE_PLUS')
        del sites['dm', 1]
        with self.assertRaisesRegex(ValueError, 'mask'):
            native_layout(sites, auxiliary, family='ULTRASCALE_PLUS')

    def test_fifo_backpressure_and_software_ownership(self):
        for wide in (False, True):
            layout = self.plan(wide)
            dut = NativeFIFORead(layout)
            def check():
                yield dut.ready.eq(1)
                yield dut.empty.eq(0)
                yield
                yield
                self.assertEqual((yield dut.lane_drain), (1 << len(layout.lanes)) - 1)
                # One late bit must stall every lane during controller access.
                for lane in layout.lanes:
                    yield dut.empty.eq(1 << lane.dq[-1])
                    yield dut.independent.eq(1)
                    yield dut.software_control.eq(0)
                    yield
                    yield
                    self.assertEqual((yield dut.lane_drain), 0)
                    yield dut.software_control.eq(1)
                    yield
                    yield
                    self.assertEqual((yield dut.lane_drain),
                                     ((1 << len(layout.lanes)) - 1) ^ (1 << lane.index))
                    for bit in lane.dq:
                        self.assertEqual(((yield dut.read_enable) >> bit) & 1, 0)
                yield dut.ready.eq(0)
                yield dut.clear.eq(1)
                yield
                yield
                self.assertEqual((yield dut.read_enable), 0)
                for count in dut.read_counts:
                    self.assertEqual((yield count), 0)
            run_simulation(dut, check())
