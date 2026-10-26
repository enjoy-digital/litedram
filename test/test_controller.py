#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from litedram.modules import MT41K128M16
from litedram.phy.model import get_sdram_phy_settings
from litedram.core.controller import LiteDRAMController, ControllerSettings


class TestController(unittest.TestCase):
    @staticmethod
    def get_controller(**kwargs):
        clk_freq = 100e6
        module   = MT41K128M16(clk_freq, "1:4")
        phy      = get_sdram_phy_settings("DDR3", 16, clk_freq)
        return LiteDRAMController(phy, module.geom_settings, module.timing_settings, clk_freq, **kwargs)

    def test_default_settings_are_per_instance(self):
        # The controller attaches phy/geom/timing to its settings: the default settings must not be
        # shared between instances.
        c0 = self.get_controller()
        c1 = self.get_controller()
        self.assertIsNot(c0.settings, c1.settings)
        self.assertFalse(hasattr(ControllerSettings(), "phy"))

    def test_settings_are_kept(self):
        settings = ControllerSettings(cmd_buffer_depth=4)
        c = self.get_controller(controller_settings=settings)
        self.assertIs(c.settings, settings)
        self.assertEqual(c.settings.cmd_buffer_depth, 4)
