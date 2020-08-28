#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# Bench Test ---------------------------------------------------------------------------------------

def s7_bench_test(freq_min, freq_max, freq_step, vco_freq, bios_filename, bios_timeout=5):
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
    ctrl.load_rom(bios_filename)
    ctrl.reboot()

    s7pll = S7PLL()

    clkout0_clkreg1 = ClkReg1(s7pll.read(0x08))

    tested_vco_divs = []
    for clk_freq in range(int(freq_min), int(freq_max), int(freq_step)):
        vco_div = int(vco_freq/clk_freq)
        if vco_div in tested_vco_divs:
            continue
        tested_vco_divs.append(vco_div)
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
        while (time.time() - start) < bios_timeout:
            if wb.regs.uart_xover_rxfull.read():
                for c in wb.read(wb.regs.uart_xover_rxtx.addr, 16, burst="fixed"):
                    print("{:c}".format(c), end="")

    # # #

    wb.close()
