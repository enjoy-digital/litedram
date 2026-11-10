#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Default CL/CWL (get_default_cl_cwl): each JEDEC bin applies up to its exact maximum rate."""

import unittest

from litedram.common import get_default_cl_cwl


class TestDefaultCLCWL(unittest.TestCase):
    # (memtype, maximum rate of the bin in MT/s, (CL, CWL) of the bin, (CL, CWL) of the next bin).
    bins = [
        ("DDR2",  400,       (3,  2), (4,  3)),
        ("DDR2", 1600/3,     (4,  3), (5,  4)),
        ("DDR2", 2000/3,     (5,  4), (6,  5)),
        ("DDR2",  800,       (6,  5), (7,  5)),
        ("DDR3",  800,       (6,  5), (7,  6)),
        ("DDR3", 3200/3,     (7,  6), (10, 7)),
        ("DDR3", 4000/3,     (10, 7), (11, 8)),
        ("DDR3", 1600,       (11, 8), (13, 9)),
        ("DDR4", 4000/3,     (9,  9), (11, 9)),
        ("DDR4", 1600,       (11, 9), (13, 10)),
        ("DDR4", 5600/3,     (13, 10), (15, 11)),
        ("DDR4", 6400/3,     (15, 11), (16, 12)),
        ("DDR4", 2400,       (16, 12), (18, 14)),
    ]

    def test_bins(self):
        for memtype, rate, cl_cwl, next_cl_cwl in self.bins:
            with self.subTest(memtype=memtype, rate=rate):
                tck = 2/(rate*1e6)
                self.assertEqual(get_default_cl_cwl(memtype, tck),         cl_cwl)      # At the bin's rate.
                self.assertEqual(get_default_cl_cwl(memtype, tck*1.01),    cl_cwl)      # Slower.
                self.assertEqual(get_default_cl_cwl(memtype, tck*0.999),   next_cl_cwl) # Faster: next bin.

    def test_sys_clk_frequencies(self):
        # tck from the sys_clk frequencies of the PHYs (1:4: DDR rate = 8 x sys_clk).
        for sys_clk_freq, cl_cwl in [(100e6, (6, 5)), (125e6, (7, 6)), (400e6/3, (7, 6)),
                                     (150e6, (10, 7)), (500e6/3, (10, 7)), (200e6, (11, 8))]:
            with self.subTest(sys_clk_freq=sys_clk_freq):
                self.assertEqual(get_default_cl_cwl("DDR3", 1/(4*sys_clk_freq)), cl_cwl)

    def test_too_fast(self):
        with self.assertRaises(ValueError):
            get_default_cl_cwl("DDR3", 2/(2000e6))
