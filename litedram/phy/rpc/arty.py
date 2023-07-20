#!/usr/bin/env python3

# This file is Copyright (c) 2015-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
# License: BSD

# Setup:
# https://user-images.githubusercontent.com/1450143/165936416-faebe814-e727-44e5-8392-72931f2abb68.JPG
# - Replace Arty's DDR3 with EM6GA16L.
# - Connect Arty's I2C to PMIC's I2C.

# Build/Use:
# ./arty.py --build --load
# litex_server --udp
# litex_term crossover

import os
import argparse

from migen import *

from litex_boards.platforms import digilent_arty
from litex.build.generic_platform import *
from litex.build.xilinx.vivado import vivado_build_args, vivado_build_argdict

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage

from litedram.init import get_sdram_phy_py_header
from litedram.core.controller import ControllerSettings
from litedram.phy.rpc.basephy import RPCPads
from litedram.phy.rpc.s7phy import A7RPCPHY
from litedram.modules import EM6GA16L

from liteeth.phy.mii import LiteEthPHYMII

from litescope import LiteScopeAnalyzer

# Pads ---------------------------------------------------------------------------------------------

class RPCPadsDDR3(RPCPads):
    def map(self, pads):
        self.clk_p  = pads.clk_p
        self.clk_n  = pads.clk_n
        self.cs_n   = pads.dm[1]
        self.dqs_p  = Array([pads.dqs_p[1], pads.dqs_p[0]])
        self.dqs_n  = Array([pads.dqs_n[1], pads.dqs_n[0]])
        self.stb    = pads.dm[0]
        self.db     = Array([
            pads.dq[10],
            pads.dq[14],
            pads.dq[8],
            pads.dq[12],
            pads.dq[15],
            pads.dq[9],
            pads.dq[13],
            pads.dq[11],
            pads.dq[2],
            pads.dq[6],
            pads.dq[0],
            pads.dq[4],
            pads.dq[7],
            pads.dq[1],
            pads.dq[5],
            pads.dq[3],
        ])


def ddram_dbg_pmod_io(pmod_db, pmod_others, len_db=1):
    unused = "V15 U16 P14 T11 R12 T14 T15 T16 N15 M16 V17 U18 R17 P17 U11 V16 M13 R10 R11 R13 R15 P15 R16".split(" ")
    pmod_db_pins = [f"{pmod_db}:{i}" for i in range(8)]
    return [
        ("ddram_dbg", 0,
            Subsignal("clk_p", Pins(f"{pmod_others}:0")),
            Subsignal("clk_n", Pins(f"{pmod_others}:4")),
            Subsignal("dqs_p", Pins(f"{pmod_others}:1 {pmod_others}:5")),
            Subsignal("dqs_n", Pins(f"{pmod_others}:6 {pmod_others}:7")),
            Subsignal("cs_n",  Pins(f"{pmod_others}:2")),
            Subsignal("stb",   Pins(f"{pmod_others}:3")),
            Subsignal("db",    Pins(*(pmod_db_pins[:len_db] + unused[:16 - len_db]))),
            IOStandard("LVCMOS33")
        ),
        ("dbg_pmod", 0, Pins(*pmod_db_pins[len_db:]), IOStandard("LVCMOS33")),
    ]

_ddram_dbg_io = ddram_dbg_pmod_io("pmoda", "pmodd")

def ddram_io():
    return [
        ("ddram_sstl15", 0,
            Subsignal("a", Pins(
                "R2 M6 N4 T1 N6 R7 V6 U7",
                "R8 V7 R6 U6 T6 T8"),
                IOStandard("SSTL15")),
            Subsignal("ba",    Pins("R1 P4 P2"), IOStandard("SSTL15")),
            Subsignal("ras_n", Pins("P3"), IOStandard("SSTL15")),
            Subsignal("cas_n", Pins("M4"), IOStandard("SSTL15")),
            Subsignal("we_n",  Pins("P5"), IOStandard("SSTL15")),
            Subsignal("cs_n",  Pins("U8"), IOStandard("SSTL15")),
            Subsignal("dm", Pins("L1 U1"), IOStandard("SSTL15")),
            Subsignal("dq", Pins(
                "K5 L3 K3 L6 M3 M1 L4 M2",
                "V4 T5 U4 V5 V1 T3 U3 R3"),
                IOStandard("SSTL15"),
                Misc("IN_TERM=UNTUNED_SPLIT_40")),
            Subsignal("dqs_p", Pins("N2 U2"),
                IOStandard("DIFF_SSTL15"),
                Misc("IN_TERM=UNTUNED_SPLIT_40")),
            Subsignal("dqs_n", Pins("N1 V2"),
                IOStandard("DIFF_SSTL15"),
                Misc("IN_TERM=UNTUNED_SPLIT_40")),
            Subsignal("clk_p", Pins("U9"), IOStandard("DIFF_SSTL15")),
            Subsignal("clk_n", Pins("V9"), IOStandard("DIFF_SSTL15")),
            Subsignal("cke",   Pins("N5"), IOStandard("SSTL15")),
            Subsignal("odt",   Pins("R5"), IOStandard("SSTL15")),
            Subsignal("reset_n", Pins("K6"), IOStandard("SSTL15")),
            Misc("SLEW=FAST"),
        )
    ]

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq, dynamic=False):
        self.clock_domains.cd_sys       = ClockDomain()
        self.clock_domains.cd_clk200    = ClockDomain()
        self.clock_domains.cd_sys4x_90  = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_180 = ClockDomain(reset_less=True)
        if dynamic:
            self.clock_domains.cd_sys_pll  = ClockDomain()
            self.clock_domains.cd_uart      = ClockDomain()
        else:
            self.clock_domains.cd_eth      = ClockDomain()

        # # #

        def add_sys_clocks(pll):
            pll.create_clkout(self.cd_sys,       sys_clk_freq)
            pll.create_clkout(self.cd_sys4x_90,  4*sys_clk_freq, phase=90)
            pll.create_clkout(self.cd_sys4x_180, 4*sys_clk_freq, phase=180)

        self.submodules.main_pll = main_pll = S7PLL(speedgrade=-1)
        self.comb += main_pll.reset.eq(~platform.request("cpu_reset"))
        main_pll.register_clkin(platform.request("clk100"), 100e6)
        if dynamic:
            main_pll.create_clkout(self.cd_sys_pll, sys_clk_freq)
            main_pll.create_clkout(self.cd_clk200, 200e6)
            main_pll.create_clkout(self.cd_uart,   100e6)
            main_pll.expose_drp()
        else:
            add_sys_clocks(main_pll)
            main_pll.create_clkout(self.cd_clk200, 200e6)
            main_pll.create_clkout(self.cd_eth,     25e6)

        if dynamic:
            self.submodules.sys_pll = sys_pll = S7PLL(speedgrade=-1)
            self.comb += sys_pll.reset.eq(~main_pll.locked)
            sys_pll.register_clkin(self.cd_sys_pll.clk, sys_clk_freq)
            add_sys_clocks(sys_pll)

            # a simple way to approximately check the actual frequency
            ref_clk_counter      = Signal(32)
            sys_clk_counter      = Signal(32)
            self.counters_run    = CSRStorage()
            self.ref_clk_counter = CSRStatus(32)
            self.sys_clk_counter = CSRStatus(32)
            self.sync.clk200 += If(self.counters_run.storage, ref_clk_counter.eq(ref_clk_counter + 1))
            self.sync.sys    += If(self.counters_run.storage, sys_clk_counter.eq(sys_clk_counter + 1))
            self.comb += [
                self.ref_clk_counter.status.eq(ref_clk_counter),
                self.sys_clk_counter.status.eq(sys_clk_counter),
            ]

        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_clk200)
        if not dynamic:
            self.comb += platform.request("eth_ref_clk").eq(self.cd_eth.clk)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(100e6), ip_address="192.168.1.50", debug_pmod=False,
                 no_sdram_init=False, dynamic_freq=False, with_analyzer=False, **kwargs):
        platform = digilent_arty.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        kwargs["integrated_rom_size"] = 0xa000
        kwargs["uart_name"]           = "crossover"
        SoCCore.__init__(self, platform, sys_clk_freq,
            ident               = "LiteX SoC on Arty A7",
            integrated_rom_mode = "rw", # to allow reloading BIOS
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq, dynamic=dynamic_freq)

        # DDR3 SDRAM -------------------------------------------------------------------------------
        platform.add_extension(ddram_io())
        platform.add_platform_command("set_property INTERNAL_VREF 0.750 [get_iobanks 34]")
        if debug_pmod:
            from pprint import pprint
            print()
            print("  PMOD placement:")
            print("  ---------------")
            pprint(_ddram_dbg_io)
            print()
            platform.add_extension(_ddram_dbg_io)
            ddram_pads = RPCPads(platform.request("ddram_dbg"))
            dbg_pmod = platform.request("dbg_pmod")
            self.comb += [
                dbg_pmod[0].eq(ClockSignal()),
                dbg_pmod[1].eq(ClockSignal("sys4x_90")),
                dbg_pmod[2].eq(ClockSignal("sys4x_180")),
            ]
        else:
            ddram_pads = RPCPadsDDR3(platform.request("ddram_sstl15"))

        self.submodules.ddrphy = A7RPCPHY(pads=ddram_pads,
                                          sys_clk_freq=100e6 if debug_pmod else sys_clk_freq,
                                          iodelay_clk_freq=200e6)
                                          # no_differential=debug_pmod)
        module = EM6GA16L(100e6 if debug_pmod else sys_clk_freq, "1:4")

        self.ddrphy.refresh_enable = CSRStorage()

        controller_settings = ControllerSettings()
        controller_settings.auto_precharge = False
        controller_settings.with_refresh = self.ddrphy.refresh_enable.storage

        self.add_sdram("sdram",
            phy                 = self.ddrphy,
            module              = module,
            controller_settings = controller_settings,
        )

        self.add_constant("SET_DDR_VCC_15")
        # self.add_constant("RPC_UTR_TEST")

        # make BIOS wait for manual initialization from RemoteClient
        # (waits for the given value in ctrl_scratch)
        # self.add_constant("SDRAM_WAIT_MANUAL_INIT_SEQUENCE", 0xc001c0de)

        if no_sdram_init:
            self.add_constant("SDRAM_INIT_DISABLE")

        # I2C --------------------------------------------------------------------------------------
        # Used to configure the power management chip (DA9062) on the board to use different DDRVCC.
        # We explicitly use tristate SCL, because the chip operates on 5V logic (pull ups are
        # through 100k resistors so shouldn't damage FPGA pins).
        self.submodules.i2c = I2CMaster(platform.request("i2c"))
        self.i2c.add_init(addr=0x58, init=[
            # Vbuck2A / 1.5V.
            (0xa3, 0x78),
            # Vbuck2B / 1.5V.
            (0xb4, 0x78),
        ])

        if dynamic_freq:
            # UartBone -----------------------------------------------------------------------------
            self.add_uartbone(clk_freq=100e6, baudrate=1e6, cd="uart")
        else:
            # Etherbone ----------------------------------------------------------------------------
            self.submodules.ethphy = LiteEthPHYMII(
                clock_pads = self.platform.request("eth_clocks"),
                pads       = self.platform.request("eth"))
            self.add_etherbone(phy=self.ethphy, ip_address=ip_address)

        # Leds -------------------------------------------------------------------------------------
        self.submodules.leds = LedChaser(
            pads         = Cat(*[platform.request("user_led", i) for i in range(4)]),
            sys_clk_freq = sys_clk_freq)

        # Analyzer ---------------------------------------------------------------------------------

        if with_analyzer:
            self.ddrphy.finalize()
            analyzer_signals = [
                *[self.ddrphy.dfi.phases[p].cas_n for p in range(self.ddrphy.nphases)],
                *[self.ddrphy.dfi.phases[p].ras_n for p in range(self.ddrphy.nphases)],
                *[self.ddrphy.dfi.phases[p].we_n  for p in range(self.ddrphy.nphases)],
                *[self.ddrphy.dfi.phases[p].reset_n  for p in range(self.ddrphy.nphases)],
                self.ddrphy.stb_1ck_in,
                # *self.ddrphy.db_1ck_out,
                # *self.ddrphy.db_1ck_in,
                self.ddrphy.stb_1ck_out,
                self.ddrphy.dqs_1ck_out,
                self.ddrphy.dqs_1ck_in,
                self.ddrphy.cs_n_1ck_out,
                self.ddrphy.clk_1ck_out,
                self.ddrphy.dq_data_en,
                self.ddrphy.dq_mask_en,
                self.ddrphy.dq_cmd_en,
                self.ddrphy.dq_read_stb,
                self.ddrphy.dq_in_cnt,
                self.ddrphy.db_cnt,
                self.ddrphy.dqs_cnt,
                self.ddrphy.rddata_en.sr,
                self.ddrphy.wrdata_en.sr,
                self.ddrphy.db_oe,
                self.ddrphy.dqs_oe,
                self.ddrphy.reset_fsm.state,
            ]
            self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals,
                depth        = 512,
                register     = True,
                clock_domain = "sys",
                csr_csv      = "analyzer.csv")

        self.add_constant("SDRAM_DEBUG")

        # Print info
        def dump(obj):
            print()
            print(" " + obj.__class__.__name__)
            print(" " + "-" * len(obj.__class__.__name__))
            d = obj if isinstance(obj, dict) else vars(obj)
            for var, val in d.items():
                if var == "self":
                    continue
                print("  {}: {}".format(var, val))
        print("=" * 80)
        dump(self.ddrphy.settings)
        dump(module.geom_settings)
        dump(module.timing_settings)
        print()
        print("=" * 80)
        print()
        print("  VCO freq = ", self.crg.main_pll.compute_config()["vco"])
        print()
        print("=" * 80)

    def generate_sdram_phy_py_header(self):
        f = open("sdram_init.py", "w")
        f.write(get_sdram_phy_py_header(
            self.sdram.controller.settings.phy,
            self.sdram.controller.settings.timing))
        f.close()

# Build --------------------------------------------------------------------------------------------

def reboot(wb):
    wb.regs.ctrl_reset.write(1)

def load_rom(wb, filename):
    from litex.soc.integration.common import get_mem_data
    rom_data = get_mem_data(filename, endianness="little")
    print(f"load bios from: {filename} starting at 0x{wb.mems.rom.base:08x}")
    for i, data in enumerate(rom_data):
        wb.write(wb.mems.rom.base + 4*i, data)

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Arty A7")
    parser.add_argument("--build",           action="store_true",    help="Build bitstream")
    parser.add_argument("--load",            action="store_true",    help="Load bitstream")
    parser.add_argument("--load-bios",       action="store_true",    help="Load BIOS over Etherbone and reboot SoC")
    builder_args(parser)
    soc_core_args(parser)
    vivado_build_args(parser)
    parser.add_argument("--ip-address",      default="192.168.1.50", help="Use given IP address")
    parser.add_argument("--with-spi-sdcard", action="store_true",    help="Enable SPI-mode SDCard support")
    parser.add_argument("--with-sdcard",     action="store_true",    help="Enable SDCard support")
    parser.add_argument("--debug-pmod",      action="store_true",    help="Send DRAM signals on PMODs (A and D)")
    parser.add_argument("--sys-clk-freq",    default="100e6",        help="Set frequency of the system clock (default 100 MHz)")
    parser.add_argument("--dynamic-freq",    action="store_true",    help="Dynamic system frequency")
    parser.add_argument("--no-sdram-init",   action="store_true",    help="Disable automatic DRAM initialization in BIOS")
    parser.add_argument("--no-analyzer",     action="store_true",    help="Do not add LiteScope analyzer")
    args = parser.parse_args()

    soc = BaseSoC(ip_address=args.ip_address, dynamic_freq=args.dynamic_freq,
                  debug_pmod=args.debug_pmod, sys_clk_freq=int(float(args.sys_clk_freq)),
                  no_sdram_init=args.no_sdram_init, with_analyzer=not args.no_analyzer,
                  **soc_core_argdict(args))
    assert not (args.with_spi_sdcard and args.with_sdcard)
    soc.platform.add_extension(digilent_arty._sdcard_pmod_io)
    if args.with_spi_sdcard:
        soc.add_spi_sdcard()
    if args.with_sdcard:
        soc.add_sdcard()
    builder_kwargs = builder_argdict(args)
    builder_kwargs["csr_csv"] = "csr.csv"
    builder = Builder(soc, **builder_kwargs)
    builder_kwargs = vivado_build_argdict(args)
    builder.build(**builder_kwargs, run=args.build)

    soc.generate_sdram_phy_py_header()

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

    if args.load_bios:
        from litex import RemoteClient
        from litex.soc.integration.common import get_mem_data

        def memwrite(wb, data, base=0x40000000, burst=0xff):
            for i in range(0, len(data), burst):
                wb.write(base + 4 * i, data[i:i + burst])

        wb = RemoteClient()
        wb.open()

        bios_bin = os.path.join(builder.software_dir, "bios", "bios.bin")
        rom_data = get_mem_data(bios_bin, "little")
        print(f"Loading BIOS from: {bios_bin} starting at 0x{wb.mems.rom.base:08x} ...")

        print('Stopping CPU')
        wb.regs.ctrl_reset.write(0b10)  # cpu_rst

        memwrite(wb, rom_data, base=wb.mems.rom.base, burst=1)
        wb.read(wb.mems.rom.base)

        print('Rebooting CPU')
        wb.regs.ctrl_reset.write(0)

        wb.close()

if __name__ == "__main__":
    main()
