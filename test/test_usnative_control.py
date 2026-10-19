#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Native control profiles, strobe ownership and emitted primitive parameters."""

import unittest

from dataclasses import replace

from litedram.phy.usnative.control import (
    ControlProfile, control_profiles, control_parameters, emit_control)
from litedram.phy.usnative.topology import parse_vivado_map
from test.test_usnative_topology import topology_fixture, encode


def sites(x4=False):
    pins, rows = topology_fixture(x4)
    return parse_vivado_map(pins, encode(pins, rows), vivado_version="2026.1")


class TestUSNativeControl(unittest.TestCase):
    def test_partner_strobe(self):
        profiles = control_profiles(sites())
        self.assertEqual(len(profiles), 4)
        for i in range(4):
            profile = profiles[f"BITSLICE_CONTROL_X0Y{i}"]
            self.assertTrue(profile.data)
            self.assertEqual(profile.other_nibble, i % 2 == 0)
            parameters = control_parameters(profile, family="ULTRASCALE_PLUS")
            self.assertEqual(parameters["RX_GATING"], '"ENABLE"')
            self.assertEqual(parameters["RX_CLK_PHASE_P"], '"SHIFT_90"')

    def test_x4_local_strobes(self):
        self.assertTrue(all(not p.other_nibble for p in control_profiles(sites(True)).values()))

    def test_command_profile(self):
        mapped = sites()
        mapped["a", 0] = replace(mapped["dq", 0], control_site="BITSLICE_CONTROL_X0Y8", byte=3)
        profile = control_profiles(mapped)["BITSLICE_CONTROL_X0Y8"]
        parameters = control_parameters(profile, family="ULTRASCALE")
        self.assertFalse(profile.data)
        self.assertEqual(parameters["RX_GATING"], '"DISABLE"')
        self.assertEqual(parameters["RX_CLK_PHASE_P"], '"SHIFT_0"')
        self.assertEqual(parameters["EN_OTHER_PCLK"], '"FALSE"')

    def test_unsupported_sharing(self):
        mapped = sites()
        mapped["a", 0] = mapped["dq", 0]
        self.assertTrue(control_profiles(mapped)[mapped["a", 0].control_site].data)
        mapped["alert_n", 0] = mapped["dq", 0]
        with self.assertRaisesRegex(ValueError, "Unsupported signal"):
            control_profiles(mapped)
        mapped = sites()
        mapped["dq", 0] = replace(mapped["dq", 0], byte=3)
        with self.assertRaisesRegex(ValueError, "same byte"):
            control_profiles(mapped)
        mapped = sites()
        del mapped["dqs_p", 1]
        with self.assertRaises(ValueError):
            control_profiles(mapped)

    def test_invalid_configuration(self):
        for p in [ControlProfile('bad"LOC', True, False),
                  ControlProfile('BITSLICE_CONTROL_X0Y0', False, True),
                  ControlProfile('BITSLICE_CONTROL_X0Y0', 1, False)]:
            with self.assertRaises(ValueError):
                control_parameters(p, family="ULTRASCALE_PLUS")
        p = ControlProfile('BITSLICE_CONTROL_X0Y0', True, False)
        with self.assertRaises(ValueError):
            control_parameters(p, family="7SERIES")
        with self.assertRaises(ValueError):
            emit_control("bad;endmodule", p, family="ULTRASCALE")

    def test_explicit_control_interface(self):
        text = emit_control("test_control", ControlProfile('BITSLICE_CONTROL_X0Y0', True, True),
                            family="ULTRASCALE_PLUS")
        for pin in ('RST', 'RIU_CLK', 'EN_VTC'):
            self.assertIn(f'input wire {pin}', text)
        self.assertIn('output wire DLY_RDY', text)
        self.assertIn('output wire VTC_RDY', text)
        self.assertIn('input wire [3:0] TBYTE_IN', text)
        self.assertIn('input wire [15:0] RIU_WR_DATA', text)
        self.assertIn('output wire [39:0] TX_BIT_CTRL_OUT_TRI', text)
