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

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys_pll = ClockDomain()
        self.clock_domains.cd_sys     = ClockDomain()
        self.clock_domains.cd_sys4x   = ClockDomain(reset_less=True)
        self.clock_domains.cd_pll4x   = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200  = ClockDomain()
        self.clock_domains.cd_uart    = ClockDomain()

        # # #

        self.submodules.main_pll = main_pll = USMMCM(speedgrade=-2)
        self.comb += main_pll.reset.eq(platform.request("cpu_reset"))
        main_pll.register_clkin(platform.request("clk125"), 125e6)
        main_pll.create_clkout(self.cd_sys_pll, sys_clk_freq)
        main_pll.create_clkout(self.cd_clk200, 200e6, with_reset=False)
        main_pll.create_clkout(self.cd_uart,   100e6)
        main_pll.expose_drp()

        self.submodules.pll = pll = USMMCM(speedgrade=-2)
        self.comb += pll.reset.eq(~main_pll.locked)
        pll.register_clkin(self.cd_sys_pll.clk, sys_clk_freq)
        pll.create_clkout(self.cd_pll4x,  sys_clk_freq*4, buf=None, with_reset=False)

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
    def __init__(self, sys_clk_freq=int(175e6)):
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
            iodelay_clk_freq = 200e6)
        self.add_csr("ddrphy")
        self.add_sdram("sdram",
            phy    = self.ddrphy,
            module = EDY4016A(sys_clk_freq, "1:4"),
            origin = self.mem_map["main_ram"],
            size   = 0x40000000,
        )

        # UARTBone ---------------------------------------------------------------------------------
        self.add_uartbone(name="serial", clk_freq=100e6, baudrate=115200, cd="uart")

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
        from common import us_bench_test
        us_bench_test(
            freq_min      = 80e6,
            freq_max      = 180e6,
            freq_step     = 1e6,
            vco_freq      = soc.crg.pll.compute_config()["vco"],
            bios_filename = "build/kcu105/software/bios/bios.bin")

if __name__ == "__main__":
    main()
