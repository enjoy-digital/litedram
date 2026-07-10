#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from litex.build.sim    import SimPlatform
from litex.build.xilinx import XilinxPlatform

from litedram import modules as litedram_modules
from litedram import phy     as litedram_phys
from litedram.gen import LiteDRAMCore


def core_config():
    return {
        "cpu"             : None,
        "memtype"         : "DDR3",
        "sdram_phy"       : litedram_phys.A7DDRPHY,
        "sdram_module"    : litedram_modules.MT41K128M16,
        "sdram_module_nb" : 2,
        "sdram_rank_nb"   : 1,
        "input_clk_freq"  : 100e6,
        "sys_clk_freq"    : 100e6,
        "iodelay_clk_freq": 200e6,
        "cmd_latency"     : 0,
        "speedgrade"      : -1,
        "user_ports"      : {
            "native_0": {
                "type": "native",
            },
        },
    }


def csr_locations(platform):
    soc = LiteDRAMCore(platform, core_config(), integrated_rom_size=0xc000)
    soc.finalize()

    csr_origin = soc.bus.regions["csr"].origin
    return {
        name: (region.origin - csr_origin)//soc.csr.paging
        for name, region in soc.csr.regions.items()
    }


class TestGen(unittest.TestCase):
    def test_sim_csr_map_matches_hardware(self):
        hw_locations  = csr_locations(XilinxPlatform("", io=[], toolchain="vivado"))
        sim_locations = csr_locations(SimPlatform("", io=[]))

        for name in ["ddrctrl", "ddrphy", "sdram"]:
            self.assertEqual(sim_locations[name], hw_locations[name])


if __name__ == "__main__":
    unittest.main()
