#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *

from litex.build.sim    import SimPlatform
from litex.build.xilinx import XilinxPlatform
from litex.gen.sim      import run_simulation

from litedram import modules as litedram_modules
from litedram import phy     as litedram_phys
from litedram.frontend.axi import LiteDRAMAXIPort
from litedram.gen import LiteDRAMCore, connect_axi_user_port


axi_user_port_layout = [
    ("awvalid", 1),
    ("awready", 1),
    ("awaddr",  32),
    ("awburst", 2),
    ("awlen",   8),
    ("awsize",  3),
    ("awid",    8),

    ("wvalid", 1),
    ("wready", 1),
    ("wlast",  1),
    ("wstrb",  4),
    ("wdata",  32),

    ("bvalid", 1),
    ("bready", 1),
    ("bresp",  2),
    ("bid",    8),

    ("arvalid", 1),
    ("arready", 1),
    ("araddr",  32),
    ("arburst", 2),
    ("arlen",   8),
    ("arsize",  3),
    ("arid",    8),

    ("rvalid", 1),
    ("rready", 1),
    ("rlast",  1),
    ("rresp",  2),
    ("rdata",  32),
    ("rid",    8),
]


class AXIUserPortDUT(Module):
    def __init__(self):
        self.user_enable = Signal()
        self.axi  = LiteDRAMAXIPort(data_width=32, address_width=32, id_width=8)
        self.pads = Record(axi_user_port_layout)

        self.comb += connect_axi_user_port(self.axi, self.pads, self.user_enable)


class TestGEN(unittest.TestCase):
    def test_axi_user_port_block_until_ready(self):
        dut = AXIUserPortDUT()

        def main_generator():
            yield dut.pads.awvalid.eq(1)
            yield dut.pads.wvalid.eq(1)
            yield dut.pads.bready.eq(1)
            yield dut.pads.arvalid.eq(1)
            yield dut.pads.rready.eq(1)

            yield dut.axi.aw.ready.eq(1)
            yield dut.axi.w.ready.eq(1)
            yield dut.axi.b.valid.eq(1)
            yield dut.axi.ar.ready.eq(1)
            yield dut.axi.r.valid.eq(1)
            yield

            self.assertEqual((yield dut.axi.aw.valid), 0)
            self.assertEqual((yield dut.pads.awready), 0)
            self.assertEqual((yield dut.axi.w.valid), 0)
            self.assertEqual((yield dut.pads.wready), 0)
            self.assertEqual((yield dut.pads.bvalid), 0)
            self.assertEqual((yield dut.axi.b.ready), 0)
            self.assertEqual((yield dut.axi.ar.valid), 0)
            self.assertEqual((yield dut.pads.arready), 0)
            self.assertEqual((yield dut.pads.rvalid), 0)
            self.assertEqual((yield dut.axi.r.ready), 0)

            yield dut.user_enable.eq(1)
            yield

            self.assertEqual((yield dut.axi.aw.valid), 1)
            self.assertEqual((yield dut.pads.awready), 1)
            self.assertEqual((yield dut.axi.w.valid), 1)
            self.assertEqual((yield dut.pads.wready), 1)
            self.assertEqual((yield dut.pads.bvalid), 1)
            self.assertEqual((yield dut.axi.b.ready), 1)
            self.assertEqual((yield dut.axi.ar.valid), 1)
            self.assertEqual((yield dut.pads.arready), 1)
            self.assertEqual((yield dut.pads.rvalid), 1)
            self.assertEqual((yield dut.axi.r.ready), 1)

        run_simulation(dut, main_generator())


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
