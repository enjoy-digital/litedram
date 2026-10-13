#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""RXTX primitive profiles and explicit port generation for supported signal roles."""

import unittest

from dataclasses import replace

from litedram.phy.usnative.rxtx import emit_rxtx, rxtx_parameters
from litedram.phy.usnative.topology import NativePinSite


def site(position=6):
    return NativePinSite("AC26", 64, 0, "U", position, "IOB_X0Y6",
                         "BITSLICE_RX_TX_X0Y6", "BITSLICE_CONTROL_X0Y1",
                         "AD26", True, "IO_L4P_T0U_N6_DBC_AD7P_64")


class TestUSNativeRXTX(unittest.TestCase):
    def parameters(self, role, **kwargs):
        return rxtx_parameters(site(), role=role, family="ULTRASCALE_PLUS",
                               refclk_mhz=2666.666667, **kwargs)

    def test_data_and_strobe_controls(self):
        data, strobe = self.parameters("data"), self.parameters("strobe")
        self.assertEqual(data["TBYTE_CTL"], '"T"')
        self.assertEqual(strobe["TBYTE_CTL"], '"TBYTE_IN"')
        self.assertEqual(data["RX_DATA_TYPE"], '"DATA"')
        self.assertEqual(strobe["RX_DATA_TYPE"], '"DATA_AND_CLOCK"')
        self.assertNotEqual(data["TX_OUTPUT_PHASE_90"], strobe["TX_OUTPUT_PHASE_90"])

    def test_command_anchor(self):
        for position, expected in [(6, '"DATA_AND_CLOCK"'), (8, '"DATA"')]:
            parameters = rxtx_parameters(site(position), role="command",
                                        family="ULTRASCALE", refclk_mhz=2400)
            self.assertEqual(parameters["RX_DATA_TYPE"], expected)
            self.assertEqual(parameters["SIM_DEVICE"], '"ULTRASCALE"')

    def test_bad_strobe_and_polarity(self):
        for invalid in [site(8), replace(site(), master=False),
                        replace(site(), function="IO_L4P_T0U_N6_AD7P_64")]:
            with self.assertRaises(ValueError):
                rxtx_parameters(invalid, role="strobe", family="ULTRASCALE_PLUS", refclk_mhz=2400)

    def test_invalid_configuration(self):
        for frequency in [0, -1, float("nan"), float("inf"), True, "2400"]:
            with self.subTest(frequency=frequency):
                with self.assertRaises(ValueError):
                    rxtx_parameters(site(), role="data", family="ULTRASCALE_PLUS", refclk_mhz=frequency)
        for family, role in [("VERSAL", "data"), ("7SERIES", "data"), ("ULTRASCALE", "unknown")]:
            with self.assertRaises(ValueError):
                rxtx_parameters(site(), role=role, family=family, refclk_mhz=2400)

    def test_explicit_training_interface(self):
        text = emit_rxtx("native_test", site(), role="strobe",
                         family="ULTRASCALE_PLUS", refclk_mhz=2666.666667)
        for signal in ["RX_EN_VTC", "TX_EN_VTC", "RX_RST_DLY", "TX_RST_DLY", "FIFO_RD_EN"]:
            self.assertIn(f"input wire {signal}", text)
        for signal in ["RX_CNTVALUEOUT", "TX_CNTVALUEOUT"]:
            self.assertIn(f"output wire [8:0] {signal}", text)
        self.assertIn('.RX_REFCLK_FREQUENCY(2666.666667)', text)
        self.assertIn('.TX_REFCLK_FREQUENCY(2666.666667)', text)

    def test_identifiers_and_sites(self):
        for name, location in [("bad;endmodule", site()),
                               ("good", replace(site(), native_site='bad"LOC'))]:
            with self.assertRaises(ValueError):
                emit_rxtx(name, location, role="data", family="ULTRASCALE_PLUS", refclk_mhz=2400)
