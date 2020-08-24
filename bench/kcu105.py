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

        # Ethebone ---------------------------------------------------------------------------------
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

# Bench Test ---------------------------------------------------------------------------------------

def bench_test():
    import time
    from litex import RemoteClient

    wb = RemoteClient()
    wb.open()

    # # #

    class SoCCtrl:
        @staticmethod
        def reboot():
            wb.regs.ctrl_reset.write(1)

        @staticmethod
        def load_rom(filename):
            from litex.soc.integration.common import get_mem_data
            rom_data = get_mem_data(filename, "little")
            for i, data in enumerate(rom_data):
                wb.write(wb.mems.rom.base + 4*i)

    class ClkReg1:
        def __init__(self, value=0):
            self.unpack(value)

        def unpack(self, value):
            self.low_time   = (value >>  0) & (2**6 - 1)
            self.high_time  = (value >>  6) & (2**6 - 1)
            self.reserved   = (value >> 12) & (2**1 - 1)
            self.phase_mux  = (value >> 13) & (2**3 - 1)

        def pack(self):
            value =  (self.low_time  << 0)
            value |= (self.high_time << 6)
            value |= (self.reserved  << 12)
            value |= (self.phase_mux << 13)
            return value

        def __repr__(self):
            s = "ClkReg1:\n"
            s += "  low_time:  {:d}\n".format(self.low_time)
            s += "  high_time: {:d}\n".format(self.high_time)
            s += "  reserved:  {:d}\n".format(self.reserved)
            s += "  phase_mux: {:d}".format(self.phase_mux)
            return s

    class ClkReg2:
        def __init__(self, value = 0):
            self.unpack(value)

        def unpack(self, value):
            self.delay_time = (value >>  0) & (2**6 - 1)
            self.no_count   = (value >>  6) & (2**1 - 1)
            self.edge       = (value >>  7) & (2**1 - 1)
            self.mx         = (value >>  8) & (2**2 - 1)
            self.frac_wf_r  = (value >> 10) & (2**1 - 1)
            self.frac_en    = (value >> 11) & (2**1 - 1)
            self.frac       = (value >> 12) & (2**3 - 1)
            self.reserved   = (value >> 15) & (2**1 - 1)

        def pack(self):
            value  = (self.delay_time  << 0)
            value |= (self.no_count    << 6)
            value |= (self.edge        << 7)
            value |= (self.mx          << 8)
            value |= (self.frac_wf_r   << 10)
            value |= (self.frac_en     << 11)
            value |= (self.frac        << 12)
            value |= (self.reserved    << 15)
            return value

        def __repr__(self):
            s = "ClkReg2:\n"
            s += "  delay_time: {:d}\n".format(self.delay_time)
            s += "  no_count:   {:d}\n".format(self.no_count)
            s += "  edge:       {:d}\n".format(self.edge)
            s += "  mx:         {:d}\n".format(self.mx)
            s += "  frac_wf_r:  {:d}\n".format(self.frac_wf_r)
            s += "  frac_en:    {:d}\n".format(self.frac_en)
            s += "  frac:       {:d}\n".format(self.frac)
            s += "  reserved:   {:d}".format(self.reserved)
            return s

    class USPLL:
        def reset(self):
            wb.regs.crg_main_pll_drp_reset.write(1)

        def read(self, adr):
            wb.regs.crg_main_pll_drp_adr.write(adr)
            wb.regs.crg_main_pll_drp_read.write(1)
            return wb.regs.crg_main_pll_drp_dat_r.read()

        def write(self, adr, value):
            wb.regs.crg_main_pll_drp_adr.write(adr)
            wb.regs.crg_main_pll_drp_dat_w.write(value)
            wb.regs.crg_main_pll_drp_write.write(1)

    # # #

    ctrl = SoCCtrl()
    ctrl.load_rom("build/kcu105/software/bios/bios.bin")
    ctrl.reset()

    vco_freq = 1e9

    uspll = USPLL()

    print("Dump Main PLL...")
    clkout0_clkreg1 = ClkReg1(uspll.read(0x08))
    print(clkout0_clkreg1)

    # TODO: add dynamic freq test.

    print("Reset SoC and get BIOS log...")
    ctrl.reset()
    start = time.time()
    while (time.time() - start) < 5:
        if wb.regs.uart_xover_rxempty.read() == 0:
            print("{:c}".format(wb.regs.uart_xover_rxtx.read()), end="")

    # # #

    wb.close()

# Main ---------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM Bench on KCU105")
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--load",  action="store_true", help="Load bitstream")
    parser.add_argument("--test",  action="store_true", help="Run Test")
    args = parser.parse_args()

    if args.build or args.load:
        soc     = BenchSoC()
        builder = Builder(soc, csr_csv="csr.csv")
        builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

    if args.test:
        bench_test()

if __name__ == "__main__":
    main()
