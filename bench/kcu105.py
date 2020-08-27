#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse

from migen import *

from litex.boards.platforms import kcu105

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser

from litedram.modules import EDY4016A
from litedram.phy import usddrphy

from liteeth.phy.ku_1000basex import KU_1000BASEX

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_sys4x  = ClockDomain(reset_less=True)
        self.clock_domains.cd_pll4x  = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()

        # # #

        self.submodules.pll = pll = USMMCM(speedgrade=-2)
        self.comb += pll.reset.eq(platform.request("cpu_reset"))
        pll.register_clkin(platform.request("clk125"), 125e6)
        pll.create_clkout(self.cd_pll4x, sys_clk_freq*4, buf=None, with_reset=False)
        pll.create_clkout(self.cd_clk200, 200e6, with_reset=False)
        pll.expose_drp()

        self.specials += [
            Instance("BUFGCE_DIV", name="main_bufgce_div",
                p_BUFGCE_DIVIDE=4,
                i_CE=1, i_I=self.cd_pll4x.clk, o_O=self.cd_sys.clk),
            Instance("BUFGCE", name="main_bufgce",
                i_CE=1, i_I=self.cd_pll4x.clk, o_O=self.cd_sys4x.clk),
            AsyncResetSynchronizer(self.cd_clk200, ~pll.locked),
        ]

        self.submodules.idelayctrl = USIDELAYCTRL(cd_ref=self.cd_clk200, cd_sys=self.cd_sys)

        sys_clk_counter = Signal(32)
        self.sync += sys_clk_counter.eq(sys_clk_counter + 1)
        self.sys_clk_counter = CSRStatus(32)
        self.comb += self.sys_clk_counter.status.eq(sys_clk_counter)

# Bench SoC ----------------------------------------------------------------------------------------

class BenchSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(125e6)):
        platform = kcu105.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq,
            integrated_rom_size = 0x8000,
            integrated_rom_mode = "rw",
            csr_data_width      = 32,
            uart_name           = "crossover")

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.add_csr("crg")

        # DDR4 SDRAM -------------------------------------------------------------------------------
        self.submodules.ddrphy = usddrphy.USDDRPHY(platform.request("ddram"),
            memtype          = "DDR4",
            sys_clk_freq     = sys_clk_freq,
            iodelay_clk_freq = 200e6,
            cmd_latency      = 1)
        self.add_csr("ddrphy")
        self.add_sdram("sdram",
            phy                     = self.ddrphy,
            module                  = EDY4016A(sys_clk_freq, "1:4"),
            origin                  = self.mem_map["main_ram"],
            size                    = 0x40000000,
        )

        # Etherbone --------------------------------------------------------------------------------
        self.submodules.ethphy = KU_1000BASEX(self.crg.cd_clk200.clk,
            data_pads    = self.platform.request("sfp", 0),
            sys_clk_freq = self.clk_freq)
        self.add_csr("ethphy")
        self.comb += self.platform.request("sfp_tx_disable_n", 0).eq(1)
        self.platform.add_platform_command("set_property SEVERITY {{Warning}} [get_drc_checks REQP-1753]")
        self.add_etherbone(phy=self.ethphy)

        # Leds -------------------------------------------------------------------------------------
        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)
        self.add_csr("leds")

# Main ---------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM Bench on KCU105")
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--load",  action="store_true", help="Load bitstream")
    parser.add_argument("--test",  action="store_true", help="Run Test")
    args = parser.parse_args()

    soc     = BenchSoC()
    builder = Builder(soc, csr_csv="csr.csv")
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

    if args.test:
        raise NotImplementedError

if __name__ == "__main__":
    main()
