#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import time

# PLL Helpers --------------------------------------------------------------------------------------

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
    def __init__(self, value=0):
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
    def __init__(self, bus):
        self.bus = bus

    def reset(self):
        self.bus.regs.crg_main_pll_drp_reset.write(1)

    def read(self, adr):
        self.bus.regs.crg_main_pll_drp_adr.write(adr)
        self.bus.regs.crg_main_pll_drp_read.write(1)
        return self.bus.regs.crg_main_pll_drp_dat_r.read()

    def write(self, adr, value):
        self.bus.regs.crg_main_pll_drp_adr.write(adr)
        self.bus.regs.crg_main_pll_drp_dat_w.write(value)
        self.bus.regs.crg_main_pll_drp_write.write(1)


class USPLL(S7PLL): pass

# Bench Controller ---------------------------------------------------------------------------------

class BenchController:
    def __init__(self, bus):
        self.bus = bus

    def reboot(self):
       self.bus.regs.ctrl_reset.write(1)

    def load_rom(self, filename, delay=0):
        from litex.soc.integration.common import get_mem_data
        rom_data = get_mem_data(filename, "little")
        for i, data in enumerate(rom_data):
            self.bus.write(self.bus.mems.rom.base + 4*i, data)
            time.sleep(delay)

# Bench Test ---------------------------------------------------------------------------------------

def s7_bench_test(freq_min, freq_max, freq_step, vco_freq, bios_filename, bios_timeout=40):
    import time
    from litex import RemoteClient

    bus = RemoteClient()
    bus.open()

    # # #

    # Load BIOS and reboot SoC
    ctrl = BenchController(bus)
    ctrl.load_rom(bios_filename, delay=1e-4) # FIXME: delay needed @ 115200bauds.
    ctrl.reboot()

    # PLL/ClkReg
    s7pll           = S7PLL(bus)
    clkout0_clkreg1 = ClkReg1(s7pll.read(0x8))

    # Run calibration from freq_min to freq_max and log BIOS output.
    print("-"*80)
    print("Running calibration; sys_clk from {:3.3f}MHz to {:3.2f}MHz (step: {:3.2f}MHz)".format(
        freq_min/1e6, freq_max/1e6, freq_step/1e6))
    print("-"*80)
    print("")
    tested_vco_divs = []
    for clk_freq in range(int(freq_min), int(freq_max), int(freq_step)):
        # Compute VCO divider, skip if already tested.
        vco_div = int(vco_freq/clk_freq)
        if vco_div in tested_vco_divs:
            continue
        tested_vco_divs.append(vco_div)

        print("-"*40)
        print("sys_clk = {}MHz...".format(vco_freq/vco_div/1e6))
        print("-"*40)

        # Reconfigure PLL to change sys_clk
        clkout0_clkreg1.high_time = vco_div//2 + vco_div%2
        clkout0_clkreg1.low_time  = vco_div//2
        s7pll.write(0x08, clkout0_clkreg1.pack())

        # Measure/verify sys_clk
        duration = 5e-1
        start = bus.regs.crg_sys_clk_counter.read()
        time.sleep(duration)
        end = bus.regs.crg_sys_clk_counter.read()
        print("Measured sys_clk: {:3.2f}MHz.".format((end-start)/(1e6*duration)))

        # Reboot SoC and log BIOS output
        print("-"*40)
        print("Reboot SoC and get BIOS log...")
        print("-"*40)
        ctrl.reboot()
        start = time.time()
        while (time.time() - start) < bios_timeout:
            if bus.regs.uart_xover_rxfull.read():
                for c in bus.read(bus.regs.uart_xover_rxtx.addr, 16, burst="fixed"):
                    print("{:c}".format(c), end="")
        print("")

    # # #

    bus.close()

def s7_load_bios(bios_filename):
    from litex import RemoteClient

    bus = RemoteClient()
    bus.open()

    # # #

    # Load BIOS and reboot SoC.
    print("Loading BIOS...")
    ctrl = BenchController(bus)
    ctrl.load_rom(bios_filename, delay=1e-4) # FIXME: delay needed @ 115200bauds.
    ctrl.reboot()

    # # #

    bus.close()

def s7_set_sys_clk(clk_freq, vco_freq):
    import time
    from litex import RemoteClient


    bus = RemoteClient()
    bus.open()

    # # #

    # (Re)Configuring sys_clk.
    print("Configuring sys_clk to {:3.3f}...".format(clk_freq/1e6))
    s7pll           = S7PLL(bus)
    clkout0_clkreg1 = ClkReg1(s7pll.read(0x8))
    vco_div = int(vco_freq/clk_freq)
    clkout0_clkreg1.high_time = vco_div//2 + vco_div%2
    clkout0_clkreg1.low_time  = vco_div//2
    s7pll.write(0x08, clkout0_clkreg1.pack())
    # Measure/verify sys_clk
    duration = 1
    start = bus.regs.crg_sys_clk_counter.read()
    time.sleep(duration)
    end = bus.regs.crg_sys_clk_counter.read()
    print("Measured sys_clk: {:3.2f}MHz.".format((end-start)/(1e6*duration)))

    # # #

    bus.close()

# Bench Test ---------------------------------------------------------------------------------------

def us_bench_test(freq_min, freq_max, freq_step, vco_freq, bios_filename, bios_timeout=40):
    import time
    from litex import RemoteClient

    bus = RemoteClient()
    bus.open()

    # # #

    # Load BIOS and reboot SoC
    ctrl = BenchController(bus)
    ctrl.load_rom(bios_filename, delay=1e-4) # FIXME: delay needed @ 115200bauds.
    ctrl.reboot()

    # PLL/ClkReg
    uspll           = USPLL(bus)
    clkout0_clkreg1 = ClkReg1(uspll.read(0x8))

    # Run calibration from freq_min to freq_max and log BIOS output.
    print("-"*80)
    print("Running calibration; sys_clk from {:3.3f}MHz to {:3.2f}MHz (step: {:3.2f}MHz)".format(
        freq_min/1e6, freq_max/1e6, freq_step/1e6))
    print("-"*80)
    print("")
    tested_vco_divs = []
    for clk_freq in range(int(freq_min), int(freq_max), int(freq_step)):
        # Compute VCO divider, skip if already tested.
        vco_div = int(vco_freq/clk_freq)
        if vco_div in tested_vco_divs:
            continue
        tested_vco_divs.append(vco_div)

        print("-"*40)
        print("sys_clk = {}MHz...".format(vco_freq/vco_div/1e6))
        print("-"*40)

        # Reconfigure PLL to change sys_clk
        clkout0_clkreg1.high_time = vco_div//2 + vco_div%2
        clkout0_clkreg1.low_time  = vco_div//2
        uspll.write(0x08, clkout0_clkreg1.pack())

        # Measure/verify sys_clk
        duration = 5e-1
        start = bus.regs.crg_sys_clk_counter.read()
        time.sleep(duration)
        end = bus.regs.crg_sys_clk_counter.read()
        print("Measured sys_clk: {:3.2f}MHz.".format((end-start)/(1e6*duration)))

        # Reboot SoC and log BIOS output
        print("-"*40)
        print("Reboot SoC and get BIOS log...")
        print("-"*40)
        ctrl.reboot()
        start = time.time()
        while (time.time() - start) < bios_timeout:
            if bus.regs.uart_xover_rxempty.read() == 0:
                for c in bus.read(bus.regs.uart_xover_rxtx.addr, 1, burst="fixed"):
                    print("{:c}".format(c), end="")
        print("")
    # # #

    bus.close()
