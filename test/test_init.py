#
# This file is part of LiteDRAM.
#
# Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import filecmp
import unittest

from litex.build.tools import write_to_file

from litedram.init import get_sdram_phy_c_header, get_sdram_phy_py_header


def compare_with_reference(content, filename):
    write_to_file(filename, content)
    r = filecmp.cmp(filename, os.path.join("test", "reference", filename))
    os.remove(filename)
    return r


class TestInit(unittest.TestCase):
    def test_sdr(self):
        from litex.boards.targets.minispartan6 import BaseSoC
        soc       = BaseSoC()
        c_header  = get_sdram_phy_c_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        py_header = get_sdram_phy_py_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        self.assertEqual(compare_with_reference(c_header, "sdr_init.h"), True)
        self.assertEqual(compare_with_reference(py_header, "sdr_init.py"), True)

    def test_ddr3(self):
        from litex.boards.targets.kc705 import BaseSoC
        soc       = BaseSoC()
        c_header  = get_sdram_phy_c_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        py_header = get_sdram_phy_py_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        self.assertEqual(compare_with_reference(c_header, "ddr3_init.h"), True)
        self.assertEqual(compare_with_reference(py_header, "ddr3_init.py"), True)

    def test_ddr4(self):
        from litex.boards.targets.kcu105 import BaseSoC
        soc       = BaseSoC(max_sdram_size=0x4000000)
        c_header  = get_sdram_phy_c_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        py_header = get_sdram_phy_py_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        self.assertEqual(compare_with_reference(c_header, "ddr4_init.h"), True)
        self.assertEqual(compare_with_reference(py_header, "ddr4_init.py"), True)
