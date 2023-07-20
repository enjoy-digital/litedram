#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex_boards.platforms import sqrl_xcu1525

from litex.soc.cores.clock import *
from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litedram.common import PHYPadsReducer
from litedram.modules import MT40A512M8
from litedram.phy import usddrphy


# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq, channel):
        self.rst = Signal()
        self.clock_domains.cd_sys_pll = ClockDomain()
        self.clock_domains.cd_sys     = ClockDomain()
        self.clock_domains.cd_sys4x   = ClockDomain(reset_less=True)
        self.clock_domains.cd_pll4x   = ClockDomain(reset_less=True)
        self.clock_domains.cd_idelay  = ClockDomain()
        self.clock_domains.cd_uart    = ClockDomain()

        # # #

        # Main PLL.
        self.submodules.main_pll = main_pll = USPMMCM(speedgrade=-2)
        main_pll.register_clkin(platform.request("clk300", channel), 300e6)
        main_pll.create_clkout(self.cd_sys_pll, sys_clk_freq)
        main_pll.create_clkout(self.cd_idelay, 500e6)
        main_pll.create_clkout(self.cd_uart,   100e6)
        main_pll.expose_drp()

        # DRAM PLL.
        self.submodules.pll = pll = USPMMCM(speedgrade=-2)
        self.comb += pll.reset.eq(~main_pll.locked | self.rst)
        pll.register_clkin(self.cd_sys_pll.clk, sys_clk_freq)
        pll.create_clkout(self.cd_pll4x,  sys_clk_freq*4, buf=None, with_reset=False)
        self.specials += [
            Instance("BUFGCE_DIV",
                p_BUFGCE_DIVIDE = 4,
                i_CE = 1,
                i_I  = self.cd_pll4x.clk,
                o_O  = self.cd_sys.clk,
            ),
            Instance("BUFGCE",
                i_CE = 1,
                i_I  = self.cd_pll4x.clk,
                o_O  = self.cd_sys4x.clk,
            ),
        ]
        self.submodules.idelayctrl = USIDELAYCTRL(cd_ref=self.cd_idelay, cd_sys=self.cd_sys)

        # Sys Clk Counter.
        self.sys_clk_counter = CSRStatus(32)
        self.sync += self.sys_clk_counter.status.eq(self.sys_clk_counter.status + 1)

# Bench SoC ----------------------------------------------------------------------------------------

class BenchSoC(SoCCore):
    def __init__(self, uart="crossover", sys_clk_freq=int(125e6), channel=0, with_bist=False, with_analyzer=False):
        platform = sqrl_xcu1525.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            ident               = "LiteDRAM bench on XCU1525",
            integrated_rom_size = 0x10000,
            integrated_rom_mode = "rw",
            uart_name           = uart)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq, channel)

        # DDR4 SDRAM -------------------------------------------------------------------------------
        self.submodules.ddrphy = usddrphy.USPDDRPHY(
            pads             = PHYPadsReducer(platform.request("ddram", channel), [0, 1, 2, 3, 4, 5, 6, 7]),
            memtype          = "DDR4",
            sys_clk_freq     = sys_clk_freq,
            iodelay_clk_freq = 500e6)
        self.add_sdram("sdram",
            phy       = self.ddrphy,
            module    = MT40A512M8(sys_clk_freq, "1:4"),
            origin    = self.mem_map["main_ram"],
            size      = 0x40000000,
            with_bist = with_bist)
        # Workaround for Vivado 2018.2 DRC, can be ignored and probably fixed on newer Vivado versions.
        platform.add_platform_command("set_property SEVERITY {{Warning}} [get_drc_checks PDCN-2736]")

        # UARTBone ---------------------------------------------------------------------------------
        if uart != "serial":
            self.add_uartbone(clk_freq=100e6, baudrate=115200, cd="uart")

        # Analyzer ---------------------------------------------------------------------------------
        if with_analyzer:
            from litescope import LiteScopeAnalyzer
            analyzer_signals = [self.ddrphy.dfi]
            self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals,
                depth        = 256,
                clock_domain = "sys",
                csr_csv      = "analyzer.csv")

        # Leds -------------------------------------------------------------------------------------
        from litex.soc.cores.led import LedChaser
        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)

# Main ---------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM Bench on XCU1525")
    parser.add_argument("--uart",          default="crossover", help="Selected UART: crossover (default) or serial")
    parser.add_argument("--build",         action="store_true", help="Build bitstream")
    parser.add_argument("--channel",       default="0",         help="DDRAM channel 0 (default), 1, 2 or 3")
    parser.add_argument("--with-bist",     action="store_true", help="Add BIST Generator/Checker")
    parser.add_argument("--with-analyzer", action="store_true", help="Add Analyzer")
    parser.add_argument("--load",          action="store_true", help="Load bitstream")
    parser.add_argument("--load-bios",     action="store_true", help="Load BIOS")
    parser.add_argument("--sys-clk-freq",  default=None,        help="Set sys_clk_freq")
    parser.add_argument("--test",          action="store_true", help="Run Full Bench")
    args = parser.parse_args()

    soc     = BenchSoC(uart=args.uart, channel=int(args.channel, 0), with_bist=args.with_bist, with_analyzer=args.with_analyzer)
    builder = Builder(soc, output_dir=f"build/sqrl_xcu1525_ch{args.channel}", csr_csv="csr.csv")
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

    if args.load_bios:
        from common import load_bios
        load_bios(f"build/sqrl_xcu1525_ch{args.channel}/software/bios/bios.bin")

    if args.sys_clk_freq is not None:
        from common import us_set_sys_clk
        us_set_sys_clk(clk_freq=float(args.sys_clk_freq), vco_freq=soc.crg.main_pll.compute_config()["vco"])

    if args.test:
        from common import us_bench_test
        us_bench_test(
            freq_min      = 80e6,
            freq_max      = 180e6,
            freq_step     = 1e6,
            vco_freq      = soc.crg.pll.compute_config()["vco"],
            bios_filename = f"build/sqrl_xcu1525_ch{args.channel}/software/bios/bios.bin")

if __name__ == "__main__":
    main()
