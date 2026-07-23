#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
from types import SimpleNamespace

from migen import *

from litedram.common import get_default_cl
from litedram.init import get_ddr3_phy_init_sequence
from litedram.phy.s7ddrphy import A7DDRPHY, K7DDRPHY


class TestS7DDRPHYSettings(unittest.TestCase):
    sys_clk_freqs       = [50e6, 100e6, 125e6, 150e6, 175e6, 225e6]
    ddr3_cls            = range(5, 15)
    read_pipeline_cycles = 6

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

    @staticmethod
    def get_rdphase(phy):
        return phy.settings.rdphase.reset.value

    @staticmethod
    def get_mr0_cl(phy):
        init_sequence, _ = get_ddr3_phy_init_sequence(
            phy_settings    = phy.settings,
            timing_settings = SimpleNamespace(tWTR=2),
        )
        mr0 = next(address for comment, address, _, _, _ in init_sequence
            if comment.startswith("Load Mode Register 0"))
        mr0_to_cl = {
            0b0010 :  5,
            0b0100 :  6,
            0b0110 :  7,
            0b1000 :  8,
            0b1010 :  9,
            0b1100 : 10,
            0b1110 : 11,
            0b0001 : 12,
            0b0011 : 13,
            0b0101 : 14,
        }
        mr0_cl = ((mr0 >> 2) & 0b1) | (((mr0 >> 4) & 0b111) << 1)
        return mr0_to_cl[mr0_cl]

    def test_a7_default_cl_is_preserved(self):
        for sys_clk_freq in self.sys_clk_freqs:
            with self.subTest(sys_clk_freq=sys_clk_freq):
                phy         = A7DDRPHY(self.get_pads(), sys_clk_freq=sys_clk_freq)
                tck         = 1/(4*sys_clk_freq)
                expected_cl = get_default_cl("DDR3", tck)

                self.assertEqual(phy.settings.cl, expected_cl)
                self.assertEqual(self.get_mr0_cl(phy), expected_cl)

    def test_a7_read_alignment(self):
        for cl in self.ddr3_cls:
            for cmd_latency in range(3):
                with self.subTest(cl=cl, cmd_latency=cmd_latency):
                    phy = A7DDRPHY(self.get_pads(),
                        sys_clk_freq = 100e6,
                        cl           = cl,
                        cmd_latency  = cmd_latency,
                    )
                    rdphase          = self.get_rdphase(phy)
                    read_sys_latency = phy.settings.read_latency - self.read_pipeline_cycles

                    self.assertEqual(phy.settings.cl, cl)
                    self.assertEqual(self.get_mr0_cl(phy), cl)
                    self.assertEqual(
                        rdphase + cl + cmd_latency,
                        read_sys_latency*phy.settings.nphases + 1,
                    )

    def test_k7_read_alignment_is_unchanged(self):
        for cl in self.ddr3_cls:
            with self.subTest(cl=cl):
                phy              = K7DDRPHY(self.get_pads(), sys_clk_freq=100e6, cl=cl)
                rdphase          = self.get_rdphase(phy)
                read_sys_latency = phy.settings.read_latency - self.read_pipeline_cycles

                self.assertEqual(phy.settings.cl, cl)
                self.assertEqual(self.get_mr0_cl(phy), cl)
                self.assertEqual(
                    rdphase + cl,
                    read_sys_latency*phy.settings.nphases,
                )
