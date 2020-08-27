#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse

from migen import *

from litex.boards.platforms import genesys2

from litex.soc.cores.clock import *
from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.phy import s7ddrphy
from litedram.modules import MT41J256M16

from liteeth.phy.s7rgmii import LiteEthPHYRGMII

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys_pll   = ClockDomain()
        self.clock_domains.cd_sys       = ClockDomain()
        self.clock_domains.cd_sys4x     = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200    = ClockDomain()

        # # #

        self.submodules.main_pll = main_pll = S7PLL(speedgrade=-2)
        self.comb += main_pll.reset.eq(~platform.request("cpu_reset_n"))
        main_pll.register_clkin(platform.request("clk200"), 200e6)
        main_pll.create_clkout(self.cd_sys_pll, sys_clk_freq)
        main_pll.create_clkout(self.cd_clk200,  200e6)
        main_pll.expose_drp()
        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_clk200)

        sys_clk_counter = Signal(32)
        self.sync += sys_clk_counter.eq(sys_clk_counter + 1)
        self.sys_clk_counter = CSRStatus(32)
        self.comb += self.sys_clk_counter.status.eq(sys_clk_counter)

        self.submodules.pll = pll = S7PLL(speedgrade=-2)
        self.comb += pll.reset.eq(~main_pll.locked)
        pll.register_clkin(self.cd_sys_pll.clk, sys_clk_freq)
        pll.create_clkout(self.cd_sys,    sys_clk_freq)
        pll.create_clkout(self.cd_sys4x,  4*sys_clk_freq)

# Bench SoC ----------------------------------------------------------------------------------------

class BenchSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(175e6)):
        platform = genesys2.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            integrated_rom_size = 0x8000,
            integrated_rom_mode = "rw",
            csr_data_width      = 32,
            uart_name           = "crossover")

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.add_csr("crg")

        # DDR3 SDRAM -------------------------------------------------------------------------------
        self.submodules.ddrphy = s7ddrphy.K7DDRPHY(platform.request("ddram"),
            memtype      = "DDR3",
            nphases      = 4,
            sys_clk_freq = sys_clk_freq,
            cmd_latency  = 1)
        self.add_csr("ddrphy")
        self.add_sdram("sdram",
            phy    = self.ddrphy,
            module = MT41J256M16(sys_clk_freq, "1:4"),
            origin = self.mem_map["main_ram"]
        )

        # Etherbone --------------------------------------------------------------------------------
        self.submodules.ethphy = LiteEthPHYRGMII(
            clock_pads         = self.platform.request("eth_clocks"),
            pads               = self.platform.request("eth"),
            with_hw_init_reset = False)
        self.add_csr("ethphy")
        self.add_etherbone(phy=self.ethphy)

        # Leds -------------------------------------------------------------------------------------
        from litex.soc.cores.led import LedChaser
        self.submodules.led = LedChaser(self.platform.request_all("user_led"), sys_clk_freq)
        self.add_csr("led")

# Bench Test ---------------------------------------------------------------------------------------

def bench_test(vco_freq):
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
                wb.write(wb.mems.rom.base + 4*i, data)

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

    class S7PLL:
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
    ctrl.load_rom("build/genesys2/software/bios/bios.bin")
    ctrl.reboot()

    s7pll = S7PLL()

    clkout0_clkreg1 = ClkReg1(s7pll.read(0x08))

    for clk_freq in range(int(60e6), int(180e6), int(10e6)):
        vco_div = int(vco_freq/clk_freq)
        print("Reconfig Main PLL to {}MHz...".format(vco_freq/vco_div/1e6))
        clkout0_clkreg1.high_time = vco_div//2 + vco_div%2
        clkout0_clkreg1.low_time  = vco_div//2
        s7pll.write(0x08, clkout0_clkreg1.pack())

        print("Measuring sys_clk...")
        duration = 5e-1
        start = wb.regs.crg_sys_clk_counter.read()
        time.sleep(duration)
        end = wb.regs.crg_sys_clk_counter.read()
        print("sys_clk: {:3.2f}MHz".format((end-start)/(1e6*duration)))

        print("Reboot SoC and get BIOS log...")
        ctrl.reboot()
        start = time.time()
        while (time.time() - start) < 5:
            if wb.regs.uart_xover_rxempty.read() == 0:
                print("{:c}".format(wb.regs.uart_xover_rxtx.read()), end="")

    # # #

    wb.close()

# Main ---------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM Bench on Genesys2")
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
        bench_test(vco_freq=soc.crg.main_pll.compute_config()["vco"])

if __name__ == "__main__":
    main()
