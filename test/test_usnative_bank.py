#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Exact native control-bus endpoints, slot ownership and unused-input tie-offs."""

import unittest

from dataclasses import replace
from litedram.phy.usnative.auxiliary import parse_auxiliary_map
from litedram.phy.usnative.bank import control_wiring
from test.test_usnative_auxiliary import fixture


class TestUSNativeBank(unittest.TestCase):
    def setUp(self):
        pins, self.sites, text = fixture()
        self.aux = parse_auxiliary_map(pins, self.sites, text, vivado_version='2026.1')

    def plan(self, **kwargs):
        return control_wiring(kwargs.get('sites', self.sites), kwargs.get('aux', self.aux),
                              family=kwargs.get('family', 'ULTRASCALE_PLUS'))

    def test_complete_buses_and_unused_slots(self):
        plan = self.plan()
        self.assertEqual(len(plan.buses), 88)  # 20 RXTX * 4 + 4 TRI * 2.
        self.assertEqual(len(plan.unused_inputs), 16)
        self.assertEqual(len(plan.connections()), 192)
        for bus in plan.buses:
            self.assertEqual(bus.width, 40)
            self.assertEqual(plan.connections()[bus.source_site, bus.source_port], bus.name)
            self.assertEqual(plan.connections()[bus.sink_site, bus.sink_port], bus.name)
        self.assertEqual(len({b.name for b in plan.buses}), 88)

    def test_upper_nibble_slot_zero(self):
        dqs = self.sites['dqs_p', 0]
        plan = self.plan()
        bus = next(b for b in plan.buses if (b.sink_site, b.sink_port) == (dqs.native_site, 'RX_BIT_CTRL_IN'))
        self.assertEqual(bus.source_site, dqs.control_site)
        self.assertEqual(bus.source_port, 'RX_BIT_CTRL_OUT0')
        self.assertIn((self.sites['dq', 0].control_site, 'RX_BIT_CTRL_IN6'), plan.unused_inputs)
        mapped = dict(self.sites)
        mapped['dq', 7] = replace(mapped['dq', 7], position=12)
        plan = self.plan(sites=mapped)
        bus = next(b for b in plan.buses if (b.sink_site, b.sink_port) == (mapped['dq', 7].native_site, 'TX_BIT_CTRL_IN'))
        self.assertEqual(bus.source_port, 'TX_BIT_CTRL_OUT6')

    def test_tristate_association_without_coordinate_guess(self):
        control = 'BITSLICE_CONTROL_X0Y0'
        bus = next(b for b in self.plan().buses if (b.source_site, b.source_port) == (control, 'TX_BIT_CTRL_OUT_TRI'))
        self.assertEqual(bus.sink_site, 'BITSLICE_TX_X2Y20')
        self.assertEqual(bus.sink_port, 'BIT_CTRL_IN')

    def test_slot_and_site_collisions(self):
        for changed in [replace(self.sites['dq', 1], position=0),
                        replace(self.sites['dq', 1], native_site=self.sites['dq', 0].native_site),
                        replace(self.sites['dq', 1], position=6)]:
            with self.assertRaises(ValueError):
                self.plan(sites={**self.sites, ('dq', 1): changed})

    def test_missing_or_shared_tristate(self):
        with self.assertRaises(ValueError):
            self.plan(aux={})
        aux = dict(self.aux)
        aux['BITSLICE_CONTROL_X0Y1'] = replace(aux['BITSLICE_CONTROL_X0Y1'], tristate=aux['BITSLICE_CONTROL_X0Y0'].tristate)
        with self.assertRaises(ValueError):
            self.plan(aux=aux)

    def test_explicit_ports_and_family(self):
        plan = self.plan()
        self.assertEqual(plan.declarations().count('wire [39:0]'), 88)
        self.assertTrue(all(plan.connections()[key] == "40'd0" for key in plan.unused_inputs))
        with self.assertRaises(ValueError):
            self.plan(family='7SERIES')
