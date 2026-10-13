#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Local and partner-nibble clock wiring, including missing-partner rejection."""

import unittest

from dataclasses import replace
from litedram.phy.usnative.clocks import nibble_clock_wiring
from test.test_usnative_auxiliary import fixture
from test.test_usnative_topology import topology_fixture, encode
from litedram.phy.usnative.topology import parse_vivado_map


class TestUSNativeClocks(unittest.TestCase):
    def setUp(self):
        _, self.sites, _ = fixture()

    def plan(self, sites=None, family='ULTRASCALE_PLUS'):
        return nibble_clock_wiring(self.sites if sites is None else sites, family=family)

    def test_partner_endpoints_and_enabled_paths(self):
        plan = self.plan()
        self.assertEqual(len(plan.clocks), 8)
        self.assertEqual(sum(c.enabled for c in plan.clocks), 4)
        self.assertEqual(len(plan.connections()), 16)
        self.assertEqual(plan.unused_inputs, ())
        for c in plan.clocks:
            source = next(s for s in self.sites.values() if s.control_site == c.source_site)
            sink = next(s for s in self.sites.values() if s.control_site == c.sink_site)
            self.assertEqual((source.bank, source.byte), (sink.bank, sink.byte))
            self.assertNotEqual(source.nibble, sink.nibble)
            self.assertEqual(c.source_port.replace('OUT', 'IN'), c.sink_port)
            self.assertEqual(c.enabled, sink.nibble == 'L')
        self.assertEqual(plan.declarations().count('wire '), 8)

    def test_independent_of_order_and_coordinates(self):
        changed = {key: replace(s, control_site=s.control_site.replace('X0Y', 'X8Y9'))
                   for key, s in reversed(list(self.sites.items()))}
        expected = [(c.source_site.replace('X0Y', 'X8Y9'), c.sink_site.replace('X0Y', 'X8Y9'))
                    for c in self.plan().clocks]
        self.assertEqual([(c.source_site, c.sink_site) for c in self.plan(changed).clocks], expected)

    def test_same_byte_number_in_different_banks(self):
        changed = {key: replace(s, bank=65, byte=0) if s.byte == 1 else s
                   for key, s in self.sites.items()}
        self.assertEqual(self.plan(changed), self.plan())

    def test_single_command_nibble_has_tied_inputs(self):
        sample = self.sites['dq', 0]
        changed = {**self.sites, ('a', 0): replace(sample, bank=65, byte=2,
            control_site='BITSLICE_CONTROL_X5Y99', native_site='BITSLICE_RX_TX_X5Y99')}
        plan = self.plan(changed)
        self.assertEqual(len(plan.unused_inputs), 2)
        self.assertTrue(all(plan.connections()[key] == "1'b0" for key in plan.unused_inputs))

    def test_lone_x4_strobe_needs_no_partner(self):
        pins, rows = topology_fixture(x4=True)
        sites = parse_vivado_map(pins, encode(pins, rows), vivado_version='2026.1')
        sites = {key: site for key, site in sites.items()
                 if (key[0] == 'dq' and key[1] < 4)
                 or (key[0] in ('dqs_p', 'dqs_n') and key[1] == 0)}
        plan = self.plan(sites)
        self.assertEqual(plan.clocks, ())
        self.assertEqual(plan.connections(), {
            ('BITSLICE_CONTROL_X0Y0', 'PCLK_NIBBLE_IN'): "1'b0",
            ('BITSLICE_CONTROL_X0Y0', 'NCLK_NIBBLE_IN'): "1'b0"})

    def test_invalid_physical_associations(self):
        sample = self.sites['dq', 0]
        for modified in (replace(sample, nibble='U'), replace(sample, nibble='bad'),
                         replace(sample, control_site='BITSLICE_CONTROL_X0Y99'),
                         replace(sample, control_site='invalid'), replace(sample, bank=65)):
            with self.subTest(site=modified), self.assertRaises(ValueError):
                self.plan({**self.sites, ('dq', 0): modified})

    def test_family_gate(self):
        self.assertEqual(self.plan(family='ULTRASCALE'), self.plan())
        with self.assertRaises(ValueError):
            self.plan(family='7SERIES')
