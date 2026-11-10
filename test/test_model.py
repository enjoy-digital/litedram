#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *

from litedram import modules
from litedram.phy.model import SDRAMPHYModel
from litedram.phy.model import SDRAM_VERBOSE_OFF, SDRAM_VERBOSE_STD, SDRAM_VERBOSE_DBG


def count_displays(statements):
    count = 0
    for s in statements:
        if isinstance(s, Display):
            count += 1
        elif isinstance(s, If):
            count += count_displays(s.t) + count_displays(s.f)
        elif isinstance(s, Case):
            for v in s.cases.values():
                count += count_displays(v)
        elif isinstance(s, (list, tuple)):
            count += count_displays(s)
    return count


class TestSDRAMPHYModel(unittest.TestCase):
    def timing_checker_displays(self, verbosity):
        module = modules.MT41K128M16(100e6, "1:4")
        model  = SDRAMPHYModel(module, data_width=16, clk_freq=100e6, verbosity=verbosity)
        if not hasattr(model, "timing_checker"):
            return None
        return count_displays(model.timing_checker._fragment.sync["sys"])

    def test_verbosity_levels(self):
        # OFF: no timings checker, STD: violations reported, DBG: also prints the DFI commands.
        self.assertIsNone(self.timing_checker_displays(SDRAM_VERBOSE_OFF))
        std = self.timing_checker_displays(SDRAM_VERBOSE_STD)
        dbg = self.timing_checker_displays(SDRAM_VERBOSE_DBG)
        self.assertGreater(std, 0)
        self.assertGreater(dbg, std)
