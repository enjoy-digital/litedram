#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2021 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Stefan Schrijvers <ximin@ximinity.net>
# SPDX-License-Identifier: BSD-2-Clause

"""
LiteDRAM standalone core generator

LiteDRAM aims to be directly used as a python package when the SoC is created using LiteX. However,
for some use cases it could be interesting to generate a standalone verilog file of the core:
- integration of the core in a SoC using a more traditional flow.
- need to version/package the core.
- avoid Migen/LiteX dependencies.
- etc...

The standalone core is generated from a YAML configuration file that allows the user to generate
easily a custom configuration of the core.

Current version of the generator is limited to:
- SDR on all FPGAs.
- DDR3 on Lattice ECP5 FPGAs.
- DDR2/DDR3 on Xilinx 7-Series FPGAs.
- DDR4 on Xilinx Ultascale(+) FPGAs.
"""

import os
import sys
import math
import struct
import yaml
import argparse
import inspect

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.tools import replace_in_file
from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform
from litex.build.lattice import LatticePlatform
from litex.build.sim import SimPlatform

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.interconnect import wishbone
from litex.soc.interconnect import avalon
from litex.soc.cores.uart import *

from litedram import modules as litedram_modules
from litedram import phy as litedram_phys
from litedram.phy.ecp5ddrphy import ECP5DDRPHY
from litedram.phy.s7ddrphy import S7DDRPHY
from litedram.phy.model import SDRAMPHYModel

from litedram.core.controller import ControllerSettings

from litedram.frontend.axi import *
from litedram.frontend.wishbone import *
from litedram.frontend.avalon import *
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker
from litedram.frontend.fifo import LiteDRAMFIFO
from litedram.frontend.ecc import LiteDRAMNativePortECC

# IOs/Interfaces -----------------------------------------------------------------------------------

def get_common_ios():
    return [
        # Clk/Rst.
        ("clk", 0, Pins(1)),
        ("rst", 0, Pins(1)),

        # PLL status.
        ("pll_locked", 0, Pins(1)),

        # Init status.
        ("init_done",  0, Pins(1)),
        ("init_error", 0, Pins(1)),

        # IODELAY Clk/Rst.
        ("clk_iodelay", 0, Pins(1)),
        ("rst_iodelay", 0, Pins(1)),

        # USER Clk/Rst.
        ("user_clk", 0, Pins(1)),
        ("user_rst", 0, Pins(1))
    ]


def get_uart_std_ios():
    return [
        ("uart", 0,
            Subsignal("tx", Pins(1)),
            Subsignal("rx", Pins(1))
        ),
    ]

def get_uart_fifo_ios():
    return [
        ("uart_tx", 0,
            Subsignal("valid", Pins(1)),
            Subsignal("ready", Pins(1)),
            Subsignal("data",  Pins(8))
        ),
        ("uart_rx", 0,
            Subsignal("valid", Pins(1)),
            Subsignal("ready", Pins(1)),
            Subsignal("data",  Pins(8))
        ),
    ]

def get_dram_ios(core_config):
    assert core_config["memtype"] in ["SDR", "DDR2", "DDR3", "DDR4"]

    # SDR.
    if core_config["memtype"] in ["SDR"]:
        return [
            ("sdram", 0,
                Subsignal("a",       Pins(log2_int(core_config["sdram_module"].nrows))),
                Subsignal("ba",      Pins(log2_int(core_config["sdram_module"].nbanks))),
                Subsignal("ras_n",   Pins(1)),
                Subsignal("cas_n",   Pins(1)),
                Subsignal("we_n",    Pins(1)),
                Subsignal("cs_n",    Pins(1)),
                Subsignal("dm",      Pins(core_config["sdram_module_nb"])),
                Subsignal("dq",      Pins(8*core_config["sdram_module_nb"])),
                Subsignal("cke",     Pins(1))
            ),
        ]

    # DDR2 / DDR3.
    if core_config["memtype"] in ["DDR2", "DDR3"]:
        return [
            ("ddram", 0,
                Subsignal("a",       Pins(log2_int(core_config["sdram_module"].nrows))),
                Subsignal("ba",      Pins(log2_int(core_config["sdram_module"].nbanks))),
                Subsignal("ras_n",   Pins(1)),
                Subsignal("cas_n",   Pins(1)),
                Subsignal("we_n",    Pins(1)),
                Subsignal("cs_n",    Pins(core_config["sdram_rank_nb"])),
                Subsignal("dm",      Pins(core_config["sdram_module_nb"])),
                Subsignal("dq",      Pins(8*core_config["sdram_module_nb"])),
                Subsignal("dqs_p",   Pins(core_config["sdram_module_nb"])),
                Subsignal("dqs_n",   Pins(core_config["sdram_module_nb"])),
                Subsignal("clk_p",   Pins(core_config["sdram_rank_nb"])),
                Subsignal("clk_n",   Pins(core_config["sdram_rank_nb"])),
                Subsignal("cke",     Pins(core_config["sdram_rank_nb"])),
                Subsignal("odt",     Pins(core_config["sdram_rank_nb"])),
                Subsignal("reset_n", Pins(1))
            ),
        ]
    # DDR4.
    if core_config["memtype"] == "DDR4":
        # On DDR4, A14. A15 and A16 are shared with we_n/cas_n/ras_n
        a_width = min(log2_int(core_config["sdram_module"].nrows), 14)
        return [
            ("ddram", 0,
                Subsignal("a",       Pins(a_width)),
                Subsignal("ba",      Pins(log2_int(core_config["sdram_module"].ngroupbanks))),
                Subsignal("bg",      Pins(log2_int(core_config["sdram_module"].ngroups))),
                Subsignal("ras_n",   Pins(1)),
                Subsignal("cas_n",   Pins(1)),
                Subsignal("we_n",    Pins(1)),
                Subsignal("cs_n",    Pins(core_config["sdram_rank_nb"])),
                Subsignal("act_n",   Pins(1)),
                Subsignal("dm",      Pins(core_config["sdram_module_nb"])),
                Subsignal("dq",      Pins(8*core_config["sdram_module_nb"])),
                Subsignal("dqs_p",   Pins(core_config["sdram_module_nb"])),
                Subsignal("dqs_n",   Pins(core_config["sdram_module_nb"])),
                Subsignal("clk_p",   Pins(core_config["sdram_rank_nb"])),
                Subsignal("clk_n",   Pins(core_config["sdram_rank_nb"])),
                Subsignal("cke",     Pins(core_config["sdram_rank_nb"])),
                Subsignal("odt",     Pins(core_config["sdram_rank_nb"])),
                Subsignal("reset_n", Pins(1))
            ),
        ]

def get_native_user_port_ios(_id, aw, dw):
    return [
        ("user_port_{}".format(_id), 0,
            # cmd
            Subsignal("cmd_valid", Pins(1)),
            Subsignal("cmd_ready", Pins(1)),
            Subsignal("cmd_we",    Pins(1)),
            Subsignal("cmd_addr",  Pins(aw)),

            # wdata
            Subsignal("wdata_valid", Pins(1)),
            Subsignal("wdata_ready", Pins(1)),
            Subsignal("wdata_we",    Pins(dw//8)),
            Subsignal("wdata_data",  Pins(dw)),

            # rdata
            Subsignal("rdata_valid", Pins(1)),
            Subsignal("rdata_ready", Pins(1)),
            Subsignal("rdata_data",  Pins(dw))
        ),
    ]

def get_wishbone_user_port_ios(_id, aw, dw):
    return [
        ("user_port_{}".format(_id), 0,
            Subsignal("adr",   Pins(aw)),
            Subsignal("dat_w", Pins(dw)),
            Subsignal("dat_r", Pins(dw)),
            Subsignal("sel",   Pins(dw//8)),
            Subsignal("cyc",   Pins(1)),
            Subsignal("stb",   Pins(1)),
            Subsignal("ack",   Pins(1)),
            Subsignal("we",    Pins(1)),
            Subsignal("err",   Pins(1)),
        ),
    ]

def get_avalon_user_port_ios(_id, aw, dw):
    return [
        ("user_port_{}".format(_id), 0,
            Subsignal("address",          Pins(aw)),
            Subsignal("writedata",        Pins(dw)),
            Subsignal("readdata",         Pins(dw)),
            Subsignal("readdatavalid",    Pins(1)),
            Subsignal("byteenable",       Pins(dw//8)),
            Subsignal("read",             Pins(1)),
            Subsignal("write",            Pins(1)),
            Subsignal("waitrequest",      Pins(1)),
            Subsignal("burstcount",       Pins(8)),
        ),
    ]

def get_axi_user_port_ios(_id, aw, dw, iw):
    return [
        ("user_port_{}".format(_id), 0,
            # aw
            Subsignal("awvalid", Pins(1)),
            Subsignal("awready", Pins(1)),
            Subsignal("awaddr",  Pins(aw)),
            Subsignal("awburst", Pins(2)),
            Subsignal("awlen",   Pins(8)),
            Subsignal("awsize",  Pins(4)),
            Subsignal("awid",    Pins(iw)),

            # w
            Subsignal("wvalid", Pins(1)),
            Subsignal("wready", Pins(1)),
            Subsignal("wlast",  Pins(1)),
            Subsignal("wstrb",  Pins(dw//8)),
            Subsignal("wdata",  Pins(dw)),

            # b
            Subsignal("bvalid", Pins(1)),
            Subsignal("bready", Pins(1)),
            Subsignal("bresp",  Pins(2)),
            Subsignal("bid",    Pins(iw)),

            # ar
            Subsignal("arvalid", Pins(1)),
            Subsignal("arready", Pins(1)),
            Subsignal("araddr",  Pins(aw)),
            Subsignal("arburst", Pins(2)),
            Subsignal("arlen",   Pins(8)),
            Subsignal("arsize",  Pins(4)),
            Subsignal("arid",    Pins(iw)),

            # r
            Subsignal("rvalid", Pins(1)),
            Subsignal("rready", Pins(1)),
            Subsignal("rlast",  Pins(1)),
            Subsignal("rresp",  Pins(2)),
            Subsignal("rdata",  Pins(dw)),
            Subsignal("rid",    Pins(iw))
        ),
    ]

def get_fifo_user_port_ios(_id, dw):
    return [
        ("user_fifo_{}".format(_id), 0,
            # in
            Subsignal("in_valid", Pins(1)),
            Subsignal("in_ready", Pins(1)),
            Subsignal("in_data",  Pins(dw)),

            # out
            Subsignal("out_valid", Pins(1)),
            Subsignal("out_ready", Pins(1)),
            Subsignal("out_data",  Pins(dw)),
        ),
    ]

# CRG ----------------------------------------------------------------------------------------------

class LiteDRAMGENSDRPHYCRG(Module):
    def __init__(self, platform, core_config):
        assert core_config["memtype"] in ["SDR"]
        self.clock_domains.cd_sys  = ClockDomain()

        # # #

        # Clk / Rst.
        self.comb += self.cd_sys.clk.eq(platform.request("clk"))
        self.specials += AsyncResetSynchronizer(self.cd_sys, platform.request("rst"))


class LiteDRAMECP5DDRPHYCRG(Module):
    def __init__(self, platform, core_config):
        assert core_config["memtype"] in ["DDR3"]
        self.rst = Signal()
        self.clock_domains.cd_init    = ClockDomain()
        self.clock_domains.cd_por     = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys     = ClockDomain()
        self.clock_domains.cd_sys2x   = ClockDomain()
        self.clock_domains.cd_sys2x_i = ClockDomain(reset_less=True)

        # # #

        self.stop  = Signal()
        self.reset = Signal()

        # Clk / Rst.
        clk = platform.request("clk")
        rst = platform.request("rst")

        # Power On Reset.
        por_count = Signal(16, reset=2**16-1)
        por_done  = Signal()
        self.comb += self.cd_por.clk.eq(clk)
        self.comb += por_done.eq(por_count == 0)
        self.sync.por += If(~por_done, por_count.eq(por_count - 1))

        # PLL.
        sys2x_clk_ecsout = Signal()
        self.submodules.pll = pll = ECP5PLL()
        self.comb += pll.reset.eq(~por_done | rst | self.rst)
        pll.register_clkin(clk, core_config["input_clk_freq"])
        pll.create_clkout(self.cd_sys2x_i, 2*core_config["sys_clk_freq"])
        pll.create_clkout(self.cd_init, core_config["init_clk_freq"])
        self.specials += [
            Instance("ECLKBRIDGECS",
                i_CLK0   = self.cd_sys2x_i.clk,
                i_SEL    = 0,
                o_ECSOUT = sys2x_clk_ecsout),
            Instance("ECLKSYNCB",
                i_ECLKI = sys2x_clk_ecsout,
                i_STOP  = self.stop,
                o_ECLKO = self.cd_sys2x.clk),
            Instance("CLKDIVF",
                p_DIV     = "2.0",
                i_ALIGNWD = 0,
                i_CLKI    = self.cd_sys2x.clk,
                i_RST     = self.reset,
                o_CDIVX   = self.cd_sys.clk),
            AsyncResetSynchronizer(self.cd_sys,   ~pll.locked | self.reset),
            AsyncResetSynchronizer(self.cd_sys2x, ~pll.locked | self.reset),
        ]
        self.comb += platform.request("pll_locked").eq(pll.locked)

class LiteDRAMS7DDRPHYCRG(Module):
    def __init__(self, platform, core_config):
        assert core_config["memtype"] in ["DDR2", "DDR3"]
        self.rst = Signal()
        self.clock_domains.cd_sys = ClockDomain()
        if core_config["memtype"] == "DDR2":
            self.clock_domains.cd_sys2x     = ClockDomain(reset_less=True)
            self.clock_domains.cd_sys2x_dqs = ClockDomain(reset_less=True)
        elif core_config["memtype"] == "DDR3":
            self.clock_domains.cd_sys4x     = ClockDomain(reset_less=True)
            self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        else:
            raise NotImplementedError

        self.clock_domains.cd_iodelay = ClockDomain()

        # # #

        # Clk / Rst.
        clk = platform.request("clk")
        rst = platform.request("rst")

        # PLL.
        self.submodules.pll = pll = S7PLL(speedgrade=core_config["speedgrade"])
        self.comb += pll.reset.eq(rst | self.rst)
        pll.register_clkin(clk, core_config["input_clk_freq"])
        pll.create_clkout(self.cd_iodelay, core_config["iodelay_clk_freq"])
        pll.create_clkout(self.cd_sys, core_config["sys_clk_freq"])
        if core_config["memtype"] == "DDR2":
            pll.create_clkout(self.cd_sys2x,     2*core_config["sys_clk_freq"])
            pll.create_clkout(self.cd_sys2x_dqs, 2*core_config["sys_clk_freq"], phase=90)
        elif core_config["memtype"] == "DDR3":
            pll.create_clkout(self.cd_sys4x,     4*core_config["sys_clk_freq"])
            pll.create_clkout(self.cd_sys4x_dqs, 4*core_config["sys_clk_freq"], phase=90)
        else:
            raise NotImplementedError
        self.comb += platform.request("pll_locked").eq(pll.locked)

        # IODelay Ctrl.
        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_iodelay)

class LiteDRAMUSDDRPHYCRG(Module):
    def __init__(self, platform, core_config):
        assert core_config["memtype"] in ["DDR4"]
        self.rst = Signal()
        self.clock_domains.cd_por       = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys       = ClockDomain()
        self.clock_domains.cd_sys4x     = ClockDomain()
        self.clock_domains.cd_sys4x_pll = ClockDomain()
        self.clock_domains.cd_iodelay   = ClockDomain()

        # # #

        # Clk / Rst.
        clk = platform.request("clk")
        rst = platform.request("rst")

        # Power On Reset.
        por_count = Signal(32, reset=int(core_config["input_clk_freq"]*100/1e3)) # 100ms
        por_done  = Signal()
        self.comb += self.cd_por.clk.eq(clk)
        self.comb += por_done.eq(por_count == 0)
        self.sync.por += If(~por_done, por_count.eq(por_count - 1))

        # PLL.
        self.submodules.pll = pll = USMMCM(speedgrade=core_config["speedgrade"])
        self.comb += pll.reset.eq(rst | self.rst)
        pll.register_clkin(clk, core_config["input_clk_freq"])
        pll.create_clkout(self.cd_iodelay, core_config["iodelay_clk_freq"])
        pll.create_clkout(self.cd_sys4x_pll, 4*core_config["sys_clk_freq"], buf=None)
        self.comb += platform.request("pll_locked").eq(pll.locked)
        self.specials += [
            Instance("BUFGCE_DIV", name="main_bufgce_div",
                p_BUFGCE_DIVIDE=4,
                i_CE=por_done, i_I=self.cd_sys4x_pll.clk, o_O=self.cd_sys.clk),
            Instance("BUFGCE", name="main_bufgce",
                i_CE=por_done, i_I=self.cd_sys4x_pll.clk, o_O=self.cd_sys4x.clk),
        ]

        # IODelay Ctrl.
        self.submodules.idelayctrl = USIDELAYCTRL(self.cd_iodelay, cd_sys=self.cd_sys)

class LiteDRAMUSPDDRPHYCRG(Module):
    def __init__(self, platform, core_config):
        assert core_config["memtype"] in ["DDR4"]
        self.rst = Signal()
        self.clock_domains.cd_por       = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys       = ClockDomain()
        self.clock_domains.cd_sys4x     = ClockDomain()
        self.clock_domains.cd_sys4x_pll = ClockDomain()
        self.clock_domains.cd_iodelay   = ClockDomain()

        # # #

        # Clk / Rst.
        clk = platform.request("clk")
        rst = platform.request("rst")

        # Power On Reset.
        por_count = Signal(32, reset=int(core_config["input_clk_freq"]*100/1e3)) # 100ms
        por_done  = Signal()
        self.comb += self.cd_por.clk.eq(clk)
        self.comb += por_done.eq(por_count == 0)
        self.sync.por += If(~por_done, por_count.eq(por_count - 1))

        # PLL.
        self.submodules.pll = pll = USPMMCM(speedgrade=core_config["speedgrade"])
        self.comb += pll.reset.eq(rst | self.rst)
        pll.register_clkin(clk, core_config["input_clk_freq"])
        pll.create_clkout(self.cd_iodelay, core_config["iodelay_clk_freq"])
        pll.create_clkout(self.cd_sys4x_pll, 4*core_config["sys_clk_freq"], buf=None)
        self.comb += platform.request("pll_locked").eq(pll.locked)
        self.specials += [
            Instance("BUFGCE_DIV", name="main_bufgce_div",
                p_BUFGCE_DIVIDE=4,
                i_CE=por_done, i_I=self.cd_sys4x_pll.clk, o_O=self.cd_sys.clk),
            Instance("BUFGCE", name="main_bufgce",
                i_CE=por_done, i_I=self.cd_sys4x_pll.clk, o_O=self.cd_sys4x.clk),
        ]

        # IODelay Ctrl.
        self.submodules.idelayctrl = USPIDELAYCTRL(self.cd_iodelay, cd_sys=self.cd_sys)

# LiteDRAMCoreControl ------------------------------------------------------------------------------

class LiteDRAMCoreControl(Module, AutoCSR):
    def __init__(self):
        self.init_done  = CSRStorage()
        self.init_error = CSRStorage()

# LiteDRAMCore -------------------------------------------------------------------------------------

class LiteDRAMCore(SoCCore):
    def __init__(self, platform, core_config, **kwargs):
        platform.add_extension(get_common_ios())

        # Parameters -------------------------------------------------------------------------------
        sys_clk_freq   = core_config["sys_clk_freq"]
        cpu_type       = core_config["cpu"]
        cpu_variant    = core_config.get("cpu_variant", "standard")
        csr_data_width = core_config.get("csr_data_width", 32)
        uart_type      = core_config.get("uart", "rs232")
        if cpu_type is None:
            kwargs["integrated_rom_size"]  = 0
            kwargs["integrated_sram_size"] = 0
            kwargs["with_timer"]           = False
            kwargs["with_ctrl"]            = False

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq,
            cpu_type       = cpu_type,
            cpu_variant    = cpu_variant,
            csr_data_width = csr_data_width,
            with_uart      = False,
            **kwargs)

        # UART -------------------------------------------------------------------------------------
        if cpu_type is not None:
            assert uart_type in ["rs232", "fifo"]
            if uart_type == "fifo":
                platform.add_extension(get_uart_fifo_ios())
                uart_interface = RS232PHYInterface()
                self.submodules.uart = UART(uart_interface, tx_fifo_depth=1, rx_fifo_depth=1)
                self.uart.add_auto_tx_flush(sys_clk_freq=sys_clk_freq, timeout=1, interval=128)
                uart_tx_pads = platform.request("uart_tx")
                uart_rx_pads = platform.request("uart_rx")
                self.comb += [
                    # UART TX.
                uart_tx_pads.valid.eq(uart_interface.sink.valid),
                    uart_interface.sink.ready.eq(uart_tx_pads.ready),
                    uart_tx_pads.data.eq(uart_interface.sink.data),

                # UART RX.
                uart_interface.source.valid.eq(uart_rx_pads.valid),
                    uart_rx_pads.ready.eq(uart_interface.source.ready),
                    uart_interface.source.data.eq(uart_rx_pads.data)
                ]
            else:
                platform.add_extension(get_uart_std_ios())
                self.submodules.uart_phy = RS232PHY(platform.request("uart"), self.clk_freq, 115200)
                self.submodules.uart = UART(self.uart_phy)
            if self.irq.enabled:
                self.irq.add("uart", use_loc_if_exists=True)
            else:
                self.add_constant("UART_POLLING")

        # CRG / Rate -------------------------------------------------------------------------------
        if isinstance(platform, SimPlatform):
            crg  = CRG(platform.request("clk"))
            rate = {"SDR" : "1:1", "DDR2": "1:2", "DDR3": "1:4", "DDR4": "1:4"}[core_config["memtype"]]
        elif core_config["sdram_phy"] in [litedram_phys.GENSDRPHY]:
            crg  = LiteDRAMGENSDRPHYCRG(platform, core_config)
            rate = {"SDR" : "1:1"}[core_config["memtype"]]
        elif core_config["sdram_phy"] in [litedram_phys.ECP5DDRPHY]:
            crg  = LiteDRAMECP5DDRPHYCRG(platform, core_config)
            rate = {"DDR3": "1:2"}[core_config["memtype"]]
        elif core_config["sdram_phy"] in [litedram_phys.A7DDRPHY, litedram_phys.K7DDRPHY, litedram_phys.V7DDRPHY]:
            crg  = LiteDRAMS7DDRPHYCRG(platform, core_config)
            rate = {"DDR2": "1:2", "DDR3": "1:4"}[core_config["memtype"]]
        elif core_config["sdram_phy"] in [litedram_phys.USDDRPHY]:
            crg  = LiteDRAMUSDDRPHYCRG(platform, core_config)
            rate = {"DDR3": "1:4", "DDR4": "1:4"}[core_config["memtype"]]
        elif core_config["sdram_phy"] in [litedram_phys.USPDDRPHY]:
            crg  = LiteDRAMUSPDDRPHYCRG(platform, core_config)
            rate = {"DDR3": "1:4", "DDR4": "1:4"}[core_config["memtype"]]
        self.submodules.crg = crg

        # DRAM -------------------------------------------------------------------------------------
        platform.add_extension(get_dram_ios(core_config))
        sdram_module = core_config["sdram_module"](sys_clk_freq, rate=rate)

        # Collect Electrical Settings.
        electrical_settings_kwargs = {}
        for name in ["rtt_nom", "rtt_wr", "ron"]:
            if core_config.get(name, None) is not None:
                electrical_settings_kwargs[name] = core_config[name]

        # Sim.
        if isinstance(platform, SimPlatform):
            from litex.tools.litex_sim import get_sdram_phy_settings
            phy_settings   = get_sdram_phy_settings(
                memtype    = sdram_module.memtype,
                data_width = core_config["sdram_module_nb"]*8,
                clk_freq   = sys_clk_freq)
            self.submodules.ddrphy = sdram_phy = SDRAMPHYModel(
                module    = sdram_module,
                settings  = phy_settings,
                clk_freq  = sys_clk_freq)

        # GENSDRPHY.
        elif core_config["sdram_phy"] in [litedram_phys.GENSDRPHY]:
            assert core_config["memtype"] in ["SDR"]
            self.submodules.sdrphy = sdram_phy = core_config["sdram_phy"](
                pads         = platform.request("sdram"),
                sys_clk_freq = sys_clk_freq)

        # ECP5DDRPHY.
        elif core_config["sdram_phy"] in  [litedram_phys.ECP5DDRPHY]:
            assert core_config["memtype"] in ["DDR3"]
            kwargs = {}
            if core_config.get("dm_swap", False):
                kwargs['dm_remapping'] = {0:1, 1:0}

            self.submodules.ddrphy = sdram_phy = core_config["sdram_phy"](
                pads         = platform.request("ddram"),
                sys_clk_freq = sys_clk_freq,
                cmd_delay    = core_config.get("cmd_delay", 0),
                **kwargs)
            self.ddrphy.settings.add_electrical_settings(**electrical_settings_kwargs)
            self.comb += crg.stop.eq(self.ddrphy.init.stop)
            self.comb += crg.reset.eq(self.ddrphy.init.reset)

        # S7DDRPHY.
        elif core_config["sdram_phy"] in [litedram_phys.A7DDRPHY, litedram_phys.K7DDRPHY, litedram_phys.V7DDRPHY]:
            assert core_config["memtype"] in ["DDR2", "DDR3"]
            self.submodules.ddrphy = sdram_phy = core_config["sdram_phy"](
                pads             = platform.request("ddram"),
                memtype          = core_config["memtype"],
                nphases          = {"DDR2": 2, "DDR3": 4}[core_config["memtype"]],
                sys_clk_freq     = sys_clk_freq,
                iodelay_clk_freq = core_config["iodelay_clk_freq"],
                cmd_latency      = core_config["cmd_latency"])
            if core_config["memtype"] ==  "DDR3":
                self.ddrphy.settings.add_electrical_settings(**electrical_settings_kwargs)

        # USDDRPHY.
        elif core_config["sdram_phy"] in [litedram_phys.USDDRPHY, litedram_phys.USPDDRPHY]:
            self.submodules.ddrphy = sdram_phy = core_config["sdram_phy"](
                pads             = platform.request("ddram"),
                memtype          = core_config["memtype"],
                sys_clk_freq     = sys_clk_freq,
                iodelay_clk_freq = core_config["iodelay_clk_freq"],
                cmd_latency      = core_config["cmd_latency"])
            self.ddrphy.settings.add_electrical_settings(**electrical_settings_kwargs)
        else:
            raise NotImplementedError

        # Collect Controller Settings.
        controller_settings_kwargs = {}
        for name in inspect.getfullargspec(ControllerSettings. __init__).args:
            if core_config.get(name, None) is not None:
                controller_settings_kwargs[name] = core_config[name]
        controller_settings = controller_settings = ControllerSettings(**controller_settings_kwargs)

        # Add LiteDRAM Core to SoC.
        self.add_sdram("sdram",
            phy                     = sdram_phy,
            module                  = sdram_module,
            size                    = 0x01000000, # Only expose 16MB to the CPU, enough for Init/Calib.
            with_soc_interconnect   = cpu_type is not None,
            l2_cache_size           = 8,
            l2_cache_min_data_width = 0,
            controller_settings     = controller_settings,
        )

        # DRAM Control/Status ----------------------------------------------------------------------

        # Expose calibration status to user.
        self.submodules.ddrctrl = LiteDRAMCoreControl()
        self.comb += platform.request("init_done").eq(self.ddrctrl.init_done.storage)
        self.comb += platform.request("init_error").eq(self.ddrctrl.init_error.storage)

        # If no CPU, expose a bus control interface to user.
        if cpu_type is None:
            wb_bus = wishbone.Interface()
            self.bus.add_master(master=wb_bus)
            platform.add_extension(wb_bus.get_ios("wb_ctrl"))
            wb_pads = platform.request("wb_ctrl")
            self.comb += wb_bus.connect_to_pads(wb_pads, mode="slave")

        # User ports -------------------------------------------------------------------------------
        self.comb += platform.request("user_clk").eq(ClockSignal())
        self.comb += platform.request("user_rst").eq(ResetSignal())

        for name, port in core_config["user_ports"].items():

            # Common -------------------------------------------------------------------------------
            user_enable = Signal()
            # By default, block port until controller is ready.
            if port.get("block_until_ready", True):
                self.sync += user_enable.eq(self.ddrctrl.init_done.storage & ~self.ddrctrl.init_error.storage)
            # Else never block.
            else:
                self.comb += user_enable.eq(1)

            # Request user port on crossbar and add optional ECC.
            if port["type"] in ["native", "wishbone", "avalon", "axi"]:
                # With ECC.
                if port.get("ecc", False):
                    assert port.get("data_width", None) is not None
                    ecc_port  = self.sdram.crossbar.get_port()
                    user_port = LiteDRAMNativePort(
                        mode          = ecc_port.mode,
                        address_width = ecc_port.address_width,
                        data_width    = port.get("data_width")
                    )
                    ecc = LiteDRAMNativePortECC(user_port, ecc_port, with_error_injection=False)
                    setattr(self.submodules, f"ecc_{name}", ecc)
                # Without ECC.
                else:
                    user_port = self.sdram.crossbar.get_port(data_width=port.get("data_width", None))

            # Native -------------------------------------------------------------------------------
            if port["type"] == "native":
                platform.add_extension(get_native_user_port_ios(name,
                    user_port.address_width,
                    user_port.data_width))
                _user_port_io = platform.request("user_port_{}".format(name))
                self.comb += [
                    # Cmd Channel.
                    user_port.cmd.valid.eq(_user_port_io.cmd_valid & user_enable),
                    _user_port_io.cmd_ready.eq(user_port.cmd.ready & user_enable),
                    user_port.cmd.we.eq(_user_port_io.cmd_we),
                    user_port.cmd.addr.eq(_user_port_io.cmd_addr),

                    # WData Channel.
                    user_port.wdata.valid.eq(_user_port_io.wdata_valid & user_enable),
                    _user_port_io.wdata_ready.eq(user_port.wdata.ready & user_enable),
                    user_port.wdata.we.eq(_user_port_io.wdata_we),
                    user_port.wdata.data.eq(_user_port_io.wdata_data),

                    # RData Channel.
                    _user_port_io.rdata_valid.eq(user_port.rdata.valid & user_enable),
                    user_port.rdata.ready.eq(_user_port_io.rdata_ready & user_enable),
                    _user_port_io.rdata_data.eq(user_port.rdata.data),
                ]
            # Wishbone -----------------------------------------------------------------------------
            elif port["type"] == "wishbone":
                wb_port = wishbone.Interface(
                    user_port.data_width,
                    user_port.address_width)
                wishbone2native = LiteDRAMWishbone2Native(wb_port, user_port)
                self.submodules += wishbone2native
                platform.add_extension(get_wishbone_user_port_ios(name,
                        len(wb_port.adr),
                        len(wb_port.dat_w)))
                _wb_port_io = platform.request("user_port_{}".format(name))
                self.comb += [
                    wb_port.adr.eq(_wb_port_io.adr),
                    wb_port.dat_w.eq(_wb_port_io.dat_w),
                    _wb_port_io.dat_r.eq(wb_port.dat_r),
                    wb_port.sel.eq(_wb_port_io.sel),
                    wb_port.cyc.eq(_wb_port_io.cyc & user_enable),
                    wb_port.stb.eq(_wb_port_io.stb & user_enable),
                    _wb_port_io.ack.eq(wb_port.ack & user_enable),
                    wb_port.we.eq(_wb_port_io.we),
                    _wb_port_io.err.eq(wb_port.err),
                ]
            # Avalon -----------------------------------------------------------------------------
            elif port["type"] == "avalon":
                avalon_port = avalon.AvalonMMInterface(
                    user_port.data_width,
                    user_port.address_width)
                avalon2native = LiteDRAMAvalonMM2Native(avalon_port, user_port)
                self.submodules += avalon2native
                platform.add_extension(get_avalon_user_port_ios(name,
                        len(avalon_port.address),
                        len(avalon_port.writedata)))
                _avalon_port_io = platform.request("user_port_{}".format(name))
                self.comb += [
                    avalon_port.address.eq(_avalon_port_io.address),
                    avalon_port.writedata.eq(_avalon_port_io.writedata),
                    _avalon_port_io.readdata.eq(avalon_port.readdata),
                    _avalon_port_io.readdatavalid.eq(avalon_port.readdatavalid),
                    avalon_port.burstcount.eq(_avalon_port_io.burstcount),
                    avalon_port.byteenable.eq(_avalon_port_io.byteenable),
                    avalon_port.write.eq(_avalon_port_io.write & user_enable),
                    avalon_port.read.eq(_avalon_port_io.read & user_enable),
                    _avalon_port_io.waitrequest.eq(avalon_port.waitrequest | ~user_enable),
                ]
            # AXI ----------------------------------------------------------------------------------
            elif port["type"] == "axi":
                axi_port  = LiteDRAMAXIPort(
                    data_width    = user_port.data_width,
                    address_width = user_port.address_width + log2_int(user_port.data_width//8),
                    id_width      = port["id_width"])
                axi2native = LiteDRAMAXI2Native(
                    axi  = axi_port,
                    port = user_port,
                    with_read_modify_write = port.get("ecc", False)
                )
                self.submodules += axi2native
                platform.add_extension(get_axi_user_port_ios(name,
                        axi_port.address_width,
                        axi_port.data_width,
                        port["id_width"]))
                _axi_port_io = platform.request("user_port_{}".format(name))
                self.comb += [
                    # AW Channel.
                    axi_port.aw.valid.eq(_axi_port_io.awvalid & user_enable),
                    _axi_port_io.awready.eq(axi_port.aw.ready & user_enable),
                    axi_port.aw.addr.eq(_axi_port_io.awaddr),
                    axi_port.aw.burst.eq(_axi_port_io.awburst),
                    axi_port.aw.len.eq(_axi_port_io.awlen),
                    axi_port.aw.size.eq(_axi_port_io.awsize),
                    axi_port.aw.id.eq(_axi_port_io.awid),

                    # W Channel.
                    axi_port.w.valid.eq(_axi_port_io.wvalid),
                    _axi_port_io.wready.eq(axi_port.w.ready),
                    axi_port.w.last.eq(_axi_port_io.wlast),
                    axi_port.w.strb.eq(_axi_port_io.wstrb),
                    axi_port.w.data.eq(_axi_port_io.wdata),

                    # B Channel.
                    _axi_port_io.bvalid.eq(axi_port.b.valid),
                    axi_port.b.ready.eq(_axi_port_io.bready),
                    _axi_port_io.bresp.eq(axi_port.b.resp),
                    _axi_port_io.bid.eq(axi_port.b.id),

                    # AR Channel.
                    axi_port.ar.valid.eq(_axi_port_io.arvalid & user_enable),
                    _axi_port_io.arready.eq(axi_port.ar.ready & user_enable),
                    axi_port.ar.addr.eq(_axi_port_io.araddr),
                    axi_port.ar.burst.eq(_axi_port_io.arburst),
                    axi_port.ar.len.eq(_axi_port_io.arlen),
                    axi_port.ar.size.eq(_axi_port_io.arsize),
                    axi_port.ar.id.eq(_axi_port_io.arid),

                    # R Channel.
                    _axi_port_io.rvalid.eq(axi_port.r.valid),
                    axi_port.r.ready.eq(_axi_port_io.rready),
                    _axi_port_io.rlast.eq(axi_port.r.last),
                    _axi_port_io.rresp.eq(axi_port.r.resp),
                    _axi_port_io.rdata.eq(axi_port.r.data),
                    _axi_port_io.rid.eq(axi_port.r.id),
                ]
            # FIFO ---------------------------------------------------------------------------------
            elif port["type"] == "fifo":
                data_width = port.get("data_width", self.sdram.crossbar.controller.data_width)
                platform.add_extension(get_fifo_user_port_ios(name, data_width))
                _user_fifo_io = platform.request("user_fifo_{}".format(name))
                fifo = LiteDRAMFIFO(
                    data_width      = data_width,
                    base            = port["base"],
                    depth           = port["depth"],
                    write_port      = self.sdram.crossbar.get_port("write"),
                    read_port       = self.sdram.crossbar.get_port("read"),
                    with_bypass     = True,
                )
                self.submodules += fifo
                self.comb += [
                    # In.
                    fifo.sink.valid.eq(_user_fifo_io.in_valid & user_enable),
                    _user_fifo_io.in_ready.eq(fifo.sink.ready & user_enable),
                    fifo.sink.data.eq(_user_fifo_io.in_data),

                    # Out.
                    _user_fifo_io.out_valid.eq(fifo.source.valid & user_enable),
                    fifo.source.ready.eq(_user_fifo_io.out_ready & user_enable),
                    _user_fifo_io.out_data.eq(fifo.source.data),
                ]
            else:
                raise ValueError("Unsupported port type: {}".format(port["type"]))

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM standalone core generator")
    builder_args(parser)
    parser.set_defaults(output_dir="build")
    parser.add_argument("config", help="YAML config file")
    parser.add_argument("--sim",  action='store_true',     help="Integrate SDRAMPHYModel in core for simulation")
    parser.add_argument("--name", default="litedram_core", help="Standalone core/module name")
    args = parser.parse_args()
    core_config = yaml.load(open(args.config).read(), Loader=yaml.Loader)

    # Convert YAML elements to Python/LiteX --------------------------------------------------------
    for k, v in core_config.items():
        replaces = {"False": False, "True": True, "None": None}
        for r in replaces.keys():
            if v == r:
                core_config[k] = replaces[r]
        if "clk_freq" in k:
            core_config[k] = float(core_config[k])
        if k == "sdram_module":
            core_config[k] = getattr(litedram_modules, core_config[k])
        if k == "sdram_phy":
            core_config[k] = getattr(litedram_phys, core_config[k])

    # Generate core --------------------------------------------------------------------------------
    if args.sim:
        platform = SimPlatform("", io=[])
    elif core_config["sdram_phy"] in [litedram_phys.GENSDRPHY]:
        platform = LatticePlatform(core_config["device"], io=[], toolchain="trellis") # FIXME: Allow other Vendors.
    elif core_config["sdram_phy"] in [litedram_phys.ECP5DDRPHY]:
        platform = LatticePlatform(core_config["device"], io=[], toolchain="trellis")
    elif core_config["sdram_phy"] in [litedram_phys.A7DDRPHY, litedram_phys.K7DDRPHY, litedram_phys.V7DDRPHY]:
        platform = XilinxPlatform("", io=[], toolchain="vivado")
    elif core_config["sdram_phy"] in [litedram_phys.USDDRPHY, litedram_phys.USPDDRPHY]:
        platform = XilinxPlatform("", io=[], toolchain="vivado")
    else:
        raise ValueError("Unsupported SDRAM PHY: {}".format(core_config["sdram_phy"]))

    builder_arguments = builder_argdict(args)
    builder_arguments["compile_gateware"] = False

    soc     = LiteDRAMCore(platform, core_config, integrated_rom_size=0xC000)
    builder = Builder(soc, **builder_arguments)
    builder.build(build_name=args.name, regular_comb=False)

if __name__ == "__main__":
    main()
