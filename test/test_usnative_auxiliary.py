#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Tristate/RIU mapping validation using synthetic Vivado query results."""

import unittest

from dataclasses import replace
from migen import Signal
from litedram.phy.usnative.auxiliary import parse_auxiliary_map, vivado_auxiliary_query
from litedram.phy.usnative.aux_primitives import RIU_PORTS, emit_tristate, riu_or, tristate_parameters
from litedram.phy.usnative.topology import parse_vivado_map
from test.test_usnative_topology import topology_fixture, encode


def fixture():
    pins, rows = topology_fixture()
    sites = parse_vivado_map(pins, encode(pins, rows), vivado_version="2026.1")
    # Deliberately unrelated coordinates: no inferred control-to-aux offsets.
    lines = [f'USNATIVE_AUX\t1\t{pins.fingerprint}\t{pins.part}\t2026.1',
             'control\ttristate\triu\triu_input']
    for i in range(4):
        lines.append(f'BITSLICE_CONTROL_X0Y{i}\tBITSLICE_TX_X2Y{i+20}\tRIU_OR_X2Y{i//2+8}\t' + ('LOW' if i % 2 == 0 else 'UPP'))
    lines.append('END\t4')
    return pins, sites, '\n'.join(lines)


class TestUSNativeAuxiliary(unittest.TestCase):
    def parse(self, text):
        pins, sites, _ = fixture()
        return parse_auxiliary_map(pins, sites, text, vivado_version="2026.1")

    def test_physical_associations(self):
        pins, sites, text = fixture()
        result = self.parse(text)
        self.assertEqual(len(result), 4)
        self.assertEqual(result['BITSLICE_CONTROL_X0Y1'].tristate, 'BITSLICE_TX_X2Y21')
        self.assertEqual(result['BITSLICE_CONTROL_X0Y1'].riu_input, 'UPP')
        query = vivado_auxiliary_query(pins, sites)
        self.assertIn('TRISTATE_ODELAY_OUT$bit', query)
        self.assertIn('RIU2CLB_RD_DATA$bit', query)

    def test_stale_or_partial_map(self):
        _, _, text = fixture()
        for bad in [text.replace('2026.1', '2025.2'), text.replace('END\t4', 'END\t3'),
                    text.rsplit('\n', 1)[0], text.replace('USNATIVE_AUX\t1', 'USNATIVE_AUX\t2')]:
            with self.assertRaises(ValueError):
                self.parse(bad)

    def test_auxiliary_collisions(self):
        _, _, text = fixture()
        for bad in [text.replace('BITSLICE_TX_X2Y21', 'BITSLICE_TX_X2Y20'),
                    text.replace('RIU_OR_X2Y9', 'RIU_OR_X2Y8'),
                    text.replace('\tUPP', '\tLOW'),
                    text.replace('BITSLICE_CONTROL_X0Y3', 'BITSLICE_CONTROL_X0Y2')]:
            with self.assertRaises(ValueError):
                self.parse(bad)

    def test_missing_or_split_byte(self):
        _, _, text = fixture()
        lines = text.splitlines()
        with self.assertRaises(ValueError):
            self.parse('\n'.join(lines[:3] + lines[4:]))
        lines[3] = lines[3].replace('RIU_OR_X2Y8', 'RIU_OR_X3Y9')
        with self.assertRaises(ValueError):
            self.parse('\n'.join(lines))

    def test_query_tokens(self):
        pins, sites, _ = fixture()
        with self.assertRaises(ValueError):
            vivado_auxiliary_query(replace(pins, part='bad;exit'), sites)
        with self.assertRaises(ValueError):
            vivado_auxiliary_query(replace(pins, family='7SERIES'), sites)

    def test_tristate_profile(self):
        p = tristate_parameters(family='ULTRASCALE_PLUS', refclk_mhz=2666.666667)
        self.assertEqual(p['DELAY_TYPE'], '"FIXED"')
        self.assertEqual(p['OUTPUT_PHASE_90'], '"TRUE"')
        text = emit_tristate('tri_test', 'BITSLICE_TX_X0Y2', family='ULTRASCALE_PLUS', refclk_mhz=2666.666667)
        for pin in ('RST', 'RST_DLY', 'EN_VTC'):
            self.assertIn('input wire '+pin, text)
        self.assertIn('output wire [39:0] BIT_CTRL_OUT', text)

    def test_invalid_tristate_configuration(self):
        for frequency in [0, -1, True, float('nan'), float('inf'), 1e-12, '2400']:
            with self.assertRaises(ValueError):
                tristate_parameters(family='ULTRASCALE', refclk_mhz=frequency)
        with self.assertRaises(ValueError):
            emit_tristate('bad;module', 'BITSLICE_TX_X0Y0', family='ULTRASCALE', refclk_mhz=2400)
        with self.assertRaises(ValueError):
            emit_tristate('good', 'bad"LOC', family='ULTRASCALE', refclk_mhz=2400)

    def test_riu_interface(self):
        ports = {name: Signal(width) for name, (_, width) in RIU_PORTS.items()}
        instance = riu_or('RIU_OR_X0Y2', family='ULTRASCALE_PLUS', **ports)
        self.assertEqual(instance.of, 'RIU_OR')
        self.assertIn(('LOC', 'RIU_OR_X0Y2'), instance.attr)
        self.assertEqual({item.name for item in instance.items if hasattr(item, 'expr')}, set(ports))
        for bad in [dict(ports, RIU_RD_DATA_LOW=Signal(15)),
                    {k: v for k, v in ports.items() if k != 'RIU_RD_VALID'},
                    dict(ports, UNKNOWN=Signal())]:
            with self.assertRaises(ValueError):
                riu_or('RIU_OR_X0Y2', family='ULTRASCALE_PLUS', **bad)
