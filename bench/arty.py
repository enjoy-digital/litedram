#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse

from migen import *

from litex_boards.platforms import arty

from litex.soc.cores.clock import *
from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.phy import s7ddrphy
from litedram.modules import MT41K128M16

from liteeth.phy.mii import LiteEthPHYMII

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys_pll   = ClockDomain()
        self.clock_domains.cd_sys       = ClockDomain()
        self.clock_domains.cd_sys4x     = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200    = ClockDomain()
        self.clock_domains.cd_uart      = ClockDomain()

        # # #

        self.submodules.main_pll = main_pll = S7PLL(speedgrade=-1)
        self.comb += main_pll.reset.eq(~platform.request("cpu_reset"))
        main_pll.register_clkin(platform.request("clk100"), 100e6)
        main_pll.create_clkout(self.cd_sys_pll, sys_clk_freq)
        main_pll.create_clkout(self.cd_clk200,  200e6)
        main_pll.create_clkout(self.cd_uart,    100e6)
        main_pll.expose_drp()
        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_clk200)

        self.submodules.pll = pll = S7PLL(speedgrade=-1)
        self.comb += pll.reset.eq(~main_pll.locked)
        pll.register_clkin(self.cd_sys_pll.clk, sys_clk_freq)
        pll.create_clkout(self.cd_sys,          sys_clk_freq)
        pll.create_clkout(self.cd_sys4x,        4*sys_clk_freq)
        pll.create_clkout(self.cd_sys4x_dqs,    4*sys_clk_freq, phase=90)

        sys_clk_counter = Signal(32)
        self.sync += sys_clk_counter.eq(sys_clk_counter + 1)
        self.sys_clk_counter = CSRStatus(32)
        self.comb += self.sys_clk_counter.status.eq(sys_clk_counter)

# Bench SoC ----------------------------------------------------------------------------------------

class BenchSoC(SoCCore):
    def __init__(self, uart="crossover", sys_clk_freq=int(125e6), with_bist=False):
        platform = arty.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            integrated_rom_size = 0x10000,
            integrated_rom_mode = "rw",
            csr_data_width      = 32,
            uart_name           = uart)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.add_csr("crg")

        # DDR3 SDRAM -------------------------------------------------------------------------------
        self.submodules.ddrphy = s7ddrphy.A7DDRPHY(platform.request("ddram"),
            memtype      = "DDR3",
            nphases      = 4,
            sys_clk_freq = sys_clk_freq)
        self.add_csr("ddrphy")
        self.add_sdram("sdram",
            phy       = self.ddrphy,
            module    = MT41K128M16(sys_clk_freq, "1:4"),
            origin    = self.mem_map["main_ram"],
            with_bist = with_bist,
        )

        # UARTBone ---------------------------------------------------------------------------------
        if uart != "serial":
            self.add_uartbone(name="serial", clk_freq=100e6, baudrate=115200, cd="uart")

        # Etherbone --------------------------------------------------------------------------------
        self.submodules.ethphy = LiteEthPHYMII(
            clock_pads = self.platform.request("eth_clocks"),
            pads       = self.platform.request("eth"),
            with_hw_init_reset = False)
        self.add_csr("ethphy")
        self.add_etherbone(phy=self.ethphy)

        # Leds -------------------------------------------------------------------------------------
        from litex.soc.cores.led import LedChaser
        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)
        self.add_csr("leds")

# Main ---------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM Bench on Arty A7")
    parser.add_argument("--uart",        default="crossover", help="Selected UART: crossover (default) or serial")
    parser.add_argument("--build",       action="store_true", help="Build bitstream")
    parser.add_argument("--with-bist",   action="store_true", help="Add BIST Generator/Checker")
    parser.add_argument("--load",        action="store_true", help="Load bitstream")
    parser.add_argument("--load-bios",   action="store_true", help="Load BIOS")
    parser.add_argument("--set-sys-clk", default=None,        help="Set sys_clk")
    parser.add_argument("--test",        action="store_true", help="Run Full Bench")
    args = parser.parse_args()

    soc     = BenchSoC(uart=args.uart, with_bist=args.with_bist)
    builder = Builder(soc, csr_csv="csr.csv")
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

    if args.load_bios:
        from common import s7_load_bios
        s7_load_bios("build/arty/software/bios/bios.bin")

    if args.set_sys_clk is not None:
        from common import s7_set_sys_clk
        s7_set_sys_clk(clk_freq=float(args.config), vco_freq=soc.crg.main_pll.compute_config()["vco"])

    if args.test:
        from common import s7_bench_test
        s7_bench_test(
            freq_min      = 60e6,
            freq_max      = 150e6,
            freq_step     = 1e6,
            vco_freq      = soc.crg.main_pll.compute_config()["vco"],
            bios_filename = "build/arty/software/bios/bios.bin")

if __name__ == "__main__":
    main()
