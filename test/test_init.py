#
# This file is part of LiteDRAM.
#
# Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import difflib
import unittest

from litedram.init import get_sdram_phy_c_header, get_sdram_phy_py_header


def compare_with_reference(test_case, content, filename):
    ref_filename = os.path.join("test", "reference", filename)
    with open(ref_filename, "r") as f:
        reference = f.read().split("\n")
    content = content.split("\n")
    diff = list(difflib.unified_diff(content, reference, fromfile=filename, tofile=ref_filename))
    msg = "Unified diff:\n" + "\n".join(diff)
    test_case.assertEqual(len(diff), 0, msg=msg)

def update_c_reference(content, filename):
    f = open(os.path.join("test", "reference", filename), "w")
    f.write(content)
    f.close()

class TestInit(unittest.TestCase):
    def test_sdr(self):
        from litex_boards.targets.scarabhardware_minispartan6 import BaseSoC
        soc       = BaseSoC()
        c_header  = get_sdram_phy_c_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        py_header = get_sdram_phy_py_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        #update_c_reference(c_header, "sdr_init.h")
        compare_with_reference(self, c_header, "sdr_init.h")
        compare_with_reference(self, py_header, "sdr_init.py")

    def test_ddr3(self):
        from litex_boards.targets.xilinx_kc705 import BaseSoC
        soc       = BaseSoC()
        c_header  = get_sdram_phy_c_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        py_header = get_sdram_phy_py_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        #update_c_reference(c_header, "ddr3_init.h")
        compare_with_reference(self, c_header, "ddr3_init.h")
        compare_with_reference(self, py_header, "ddr3_init.py")

    def test_ddr4(self):
        from litex_boards.targets.xilinx_kcu105 import BaseSoC
        soc       = BaseSoC(max_sdram_size=0x4000000)
        c_header  = get_sdram_phy_c_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        py_header = get_sdram_phy_py_header(soc.sdram.controller.settings.phy, soc.sdram.controller.settings.timing)
        #update_c_reference(c_header, "ddr4_init.h")
        compare_with_reference(self, c_header, "ddr4_init.h")
        compare_with_reference(self, py_header, "ddr4_init.py")
