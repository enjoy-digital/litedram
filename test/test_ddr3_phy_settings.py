#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.fhdl.specials import Instance

from litedram.common import get_default_cwl, get_sys_latency
from litedram.phy.ecp5ddrphy import ECP5DDRPHY
from litedram.phy.gw2ddrphy import GW2DDRPHY
from litedram.phy.gw5ddrphy import GW5DDRPHY


class TestDDR3PHYSettings(unittest.TestCase):
    phys = [
        ("ecp5", ECP5DDRPHY, 0),
        ("gw2",  GW2DDRPHY, -1),
        ("gw5",  GW5DDRPHY, -1),
    ]
    sys_clk_freqs = [75e6, 100e6, 125e6, 166e6, 200e6, 250e6]

    @staticmethod
    def get_pads():
        return Record([
            ("a",       15),
            ("ba",       3),
            ("ras_n",    1),
            ("cas_n",    1),
            ("we_n",     1),
            ("clk_p",    1),
            ("clk_n",    1),
            ("dq",       8),
            ("dm",       1),
            ("dqs_p",    1),
            ("dqs_n",    1),
        ])

    def test_default_cwl_is_preserved(self):
        for name, phy_cls, _ in self.phys:
            for sys_clk_freq in self.sys_clk_freqs:
                with self.subTest(phy=name, sys_clk_freq=sys_clk_freq):
                    phy          = phy_cls(self.get_pads(), sys_clk_freq=sys_clk_freq)
                    tck          = 1/(2*sys_clk_freq)
                    expected_cwl = get_default_cwl("DDR3", tck)

                    self.assertEqual(phy.settings.cwl, expected_cwl)

    def test_gw5_dll_off(self):
        phy = GW5DDRPHY(self.get_pads(), sys_clk_freq=50e6, dll_off=True)
        self.assertTrue(phy.settings.dll_off)
        self.assertEqual((phy.settings.cl, phy.settings.cwl), (6, 6))
        self.assertEqual((phy.settings.rdphase, phy.settings.wrphase), (0, 0))
        with self.assertRaises(ValueError):
            GW5DDRPHY(self.get_pads(), sys_clk_freq=50e6, dll_off=True, cwl=5)

    def test_write_latency_matches_phy_pipeline(self):
        for name, phy_cls, write_latency_offset in self.phys:
            for sys_clk_freq in self.sys_clk_freqs:
                with self.subTest(phy=name, sys_clk_freq=sys_clk_freq):
                    phy             = phy_cls(self.get_pads(), sys_clk_freq=sys_clk_freq)
                    cwl             = phy.settings.cwl
                    cwl_sys_latency = get_sys_latency(phy.settings.nphases, cwl)

                    self.assertEqual(
                        phy.settings.write_latency,
                        cwl_sys_latency + write_latency_offset,
                    )

    def test_ecp5_without_dm(self):
        with_dm    = ECP5DDRPHY(self.get_pads())
        without_dm = ECP5DDRPHY(self.get_pads(), with_dm=False)

        def count_oddrx2dqa(phy):
            fragment = phy.get_fragment()
            return sum(
                isinstance(special, Instance) and special.of == "ODDRX2DQA"
                for special in fragment.specials
            )

        self.assertTrue(with_dm.settings.with_dm)
        self.assertFalse(without_dm.settings.with_dm)
        self.assertEqual(count_oddrx2dqa(with_dm) - count_oddrx2dqa(without_dm), 1)
