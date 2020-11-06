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
from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import EDY4016A
from litedram.phy import usddrphy

from liteeth.phy.ku_1000basex import KU_1000BASEX

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys_pll = ClockDomain()
        self.clock_domains.cd_sys     = ClockDomain()
        self.clock_domains.cd_sys4x   = ClockDomain(reset_less=True)
        self.clock_domains.cd_pll4x   = ClockDomain(reset_less=True)
        self.clock_domains.cd_idelay  = ClockDomain()
        self.clock_domains.cd_uart    = ClockDomain()
        self.clock_domains.cd_eth     = ClockDomain()

        # # #

        self.submodules.main_pll = main_pll = USMMCM(speedgrade=-2)
        self.comb += main_pll.reset.eq(platform.request("cpu_reset"))
        main_pll.register_clkin(platform.request("clk125"), 125e6)
        main_pll.create_clkout(self.cd_sys_pll, sys_clk_freq)
        main_pll.create_clkout(self.cd_idelay, 200e6, with_reset=False)
        main_pll.create_clkout(self.cd_uart,   100e6)
        main_pll.create_clkout(self.cd_eth,    200e6)
        main_pll.expose_drp()

        self.submodules.pll = pll = USMMCM(speedgrade=-2)
        self.comb += pll.reset.eq(~main_pll.locked)
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
            AsyncResetSynchronizer(self.cd_idelay, ~pll.locked),
        ]

        self.submodules.idelayctrl = USIDELAYCTRL(cd_ref=self.cd_idelay, cd_sys=self.cd_sys)

        sys_clk_counter = Signal(32)
        self.sync += sys_clk_counter.eq(sys_clk_counter + 1)
        self.sys_clk_counter = CSRStatus(32)
        self.comb += self.sys_clk_counter.status.eq(sys_clk_counter)

# Bench SoC ----------------------------------------------------------------------------------------

class BenchSoC(SoCCore):
    def __init__(self, uart="crossover", sys_clk_freq=int(125e6), with_bist=False):
        platform = kcu105.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            integrated_rom_size = 0x10000,
            integrated_rom_mode = "rw",
            csr_data_width      = 32,
            uart_name           = uart)

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
            phy       = self.ddrphy,
            module    = EDY4016A(sys_clk_freq, "1:4"),
            origin    = self.mem_map["main_ram"],
            size      = 0x40000000,
            with_bist = with_bist,
        )

        # UARTBone ---------------------------------------------------------------------------------
        if uart != "serial":
            self.add_uartbone(name="serial", clk_freq=100e6, baudrate=115200, cd="uart")

        # Etherbone --------------------------------------------------------------------------------
        self.submodules.ethphy = KU_1000BASEX(self.crg.cd_eth.clk,
            data_pads    = self.platform.request("sfp", 0),
            sys_clk_freq = self.clk_freq)
        self.add_csr("ethphy")
        self.comb += self.platform.request("sfp_tx_disable_n", 0).eq(1)
        self.platform.add_platform_command("set_property SEVERITY {{Warning}} [get_drc_checks REQP-1753]")
        self.add_etherbone(phy=self.ethphy)

        # Leds -------------------------------------------------------------------------------------
        from litex.soc.cores.led import LedChaser
        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)
        self.add_csr("leds")

# Main ---------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM Bench on KCU105")
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
        s7_load_bios("build/kcu105/software/bios/bios.bin")

    if args.set_sys_clk is not None:
        from common import us_set_sys_clk
        us_set_sys_clk(clk_freq=float(args.config), vco_freq=soc.crg.main_pll.compute_config()["vco"])

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
