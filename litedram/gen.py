#!/usr/bin/env python3

# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

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

Current version of the generator is limited to Xilinx 7-Series FPGA for DDR2/DDR3 memories.
"""

import os
import sys
import math
import struct
import yaml
import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from litex.soc.cores.clock import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.interconnect import csr_bus
from litex.soc.interconnect import wishbone
from litex.soc.cores.uart import *

from litedram import modules as litedram_modules
from litedram import phy as litedram_phys
from litedram.core.controller import ControllerSettings
from litedram.frontend.axi import *
from litedram.frontend.wishbone import *
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker

# IOs/Interfaces -----------------------------------------------------------------------------------

def get_common_ios():
    return [
        # clk / rst
        ("clk", 0, Pins(1)),
        ("rst", 0, Pins(1)),

        # serial
        ("serial", 0,
            Subsignal("tx", Pins(1)),
            Subsignal("rx", Pins(1))
        ),

        # crg status
        ("pll_locked", 0, Pins(1)),

        # init status
        ("init_done", 0, Pins(1)),
        ("init_error", 0, Pins(1)),

        # iodelay clk / rst
        ("clk_iodelay", 0, Pins(1)),
        ("rst_iodelay", 0, Pins(1)),

        # user clk / rst
        ("user_clk", 0, Pins(1)),
        ("user_rst", 0, Pins(1))
    ]

def get_dram_ios(core_config):
    sdram_module = core_config["sdram_module"]
    return [
        ("ddram", 0,
            Subsignal("a", Pins(log2_int(core_config["sdram_module"].nrows))),
            Subsignal("ba", Pins(log2_int(core_config["sdram_module"].nbanks))),
            Subsignal("ras_n", Pins(1)),
            Subsignal("cas_n", Pins(1)),
            Subsignal("we_n", Pins(1)),
            Subsignal("cs_n", Pins(core_config["sdram_rank_nb"])),
            Subsignal("dm", Pins(core_config["sdram_module_nb"])),
            Subsignal("dq", Pins(8*core_config["sdram_module_nb"])),
            Subsignal("dqs_p", Pins(core_config["sdram_module_nb"])),
            Subsignal("dqs_n", Pins(core_config["sdram_module_nb"])),
            Subsignal("clk_p", Pins(core_config["sdram_rank_nb"])),
            Subsignal("clk_n", Pins(core_config["sdram_rank_nb"])),
            Subsignal("cke", Pins(core_config["sdram_rank_nb"])),
            Subsignal("odt", Pins(core_config["sdram_rank_nb"])),
            Subsignal("reset_n", Pins(1))
        ),
    ]

def get_csr_ios(aw, dw):
    return [
        ("csr_port", 0,
            Subsignal("adr", Pins(aw)),
            Subsignal("we", Pins(1)),
            Subsignal("dat_w", Pins(dw)),
            Subsignal("dat_r", Pins(dw))
        ),
    ]

def get_native_user_port_ios(_id, aw, dw):
    return [
        ("user_port", _id,
            # cmd
            Subsignal("cmd_valid", Pins(1)),
            Subsignal("cmd_ready", Pins(1)),
            Subsignal("cmd_we",    Pins(1)),
            Subsignal("cmd_addr",  Pins(aw)),

            # wdata
            Subsignal("wdata_valid", Pins(1)),
            Subsignal("wdata_ready", Pins(1)),
            Subsignal("wdata_we", Pins(dw//8)),
            Subsignal("wdata_data", Pins(dw)),

            # rdata
            Subsignal("rdata_valid", Pins(1)),
            Subsignal("rdata_ready", Pins(1)),
            Subsignal("rdata_data", Pins(dw))
        ),
    ]

def get_wishbone_user_port_ios(_id, aw, dw):
    return [
        ("user_port", _id,
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

def get_axi_user_port_ios(_id, aw, dw, iw):
    return [
        ("user_port", _id,
            # aw
            Subsignal("aw_valid", Pins(1)),
            Subsignal("aw_ready", Pins(1)),
            Subsignal("aw_addr",  Pins(aw)),
            Subsignal("aw_burst", Pins(2)),
            Subsignal("aw_len", Pins(8)),
            Subsignal("aw_size", Pins(4)),
            Subsignal("aw_id",  Pins(iw)),

            # w
            Subsignal("w_valid", Pins(1)),
            Subsignal("w_ready", Pins(1)),
            Subsignal("w_last", Pins(1)),
            Subsignal("w_strb", Pins(dw//8)),
            Subsignal("w_data", Pins(dw)),

            # b
            Subsignal("b_valid", Pins(1)),
            Subsignal("b_ready", Pins(1)),
            Subsignal("b_resp", Pins(2)),
            Subsignal("b_id",  Pins(iw)),

            # ar
            Subsignal("ar_valid", Pins(1)),
            Subsignal("ar_ready", Pins(1)),
            Subsignal("ar_addr",  Pins(aw)),
            Subsignal("ar_burst", Pins(2)),
            Subsignal("ar_len", Pins(8)),
            Subsignal("ar_size", Pins(4)),
            Subsignal("ar_id",  Pins(iw)),

            # r
            Subsignal("r_valid", Pins(1)),
            Subsignal("r_ready", Pins(1)),
            Subsignal("r_last", Pins(1)),
            Subsignal("r_resp", Pins(2)),
            Subsignal("r_data", Pins(dw)),
            Subsignal("r_id", Pins(iw))
        ),
    ]


class Platform(XilinxPlatform):
    def __init__(self):
        XilinxPlatform.__init__(self, "", io=[], toolchain="vivado")

# CRG ----------------------------------------------------------------------------------------------

class LiteDRAMCRG(Module):
    def __init__(self, platform, core_config):
        self.clock_domains.cd_sys = ClockDomain()
        if core_config["memtype"] == "DDR3":
            self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
            self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        else:
            self.clock_domains.cd_sys2x = ClockDomain(reset_less=True)
            self.clock_domains.cd_sys2x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_iodelay = ClockDomain()

        # # #

        clk = platform.request("clk")
        rst = platform.request("rst")

        self.submodules.sys_pll = sys_pll = S7PLL(speedgrade=core_config["speedgrade"])
        self.comb += sys_pll.reset.eq(rst)
        sys_pll.register_clkin(clk, core_config["input_clk_freq"])
        sys_pll.create_clkout(self.cd_sys, core_config["sys_clk_freq"])
        if core_config["memtype"] == "DDR3":
            sys_pll.create_clkout(self.cd_sys4x, 4*core_config["sys_clk_freq"])
            sys_pll.create_clkout(self.cd_sys4x_dqs, 4*core_config["sys_clk_freq"], phase=90)
        else:
            sys_pll.create_clkout(self.cd_sys2x, 2*core_config["sys_clk_freq"])
            sys_pll.create_clkout(self.cd_sys2x_dqs, 2*core_config["sys_clk_freq"], phase=90)
        self.comb += platform.request("pll_locked").eq(sys_pll.locked)

        self.submodules.iodelay_pll = iodelay_pll = S7PLL()
        self.comb += iodelay_pll.reset.eq(rst)
        iodelay_pll.register_clkin(clk, core_config["input_clk_freq"])
        iodelay_pll.create_clkout(self.cd_iodelay, core_config["iodelay_clk_freq"])
        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_iodelay)

# Core ---------------------------------------------------------------------------------------------

class LiteDRAMCoreControl(Module, AutoCSR):
    def __init__(self):
        self.init_done = CSRStorage()
        self.init_error = CSRStorage()


class LiteDRAMCore(SoCSDRAM):
    csr_map = {
        "ddrctrl":   16,
        "ddrphy":    17
    }
    csr_map.update(SoCSDRAM.csr_map)
    def __init__(self, platform, core_config, **kwargs):
        platform.add_extension(get_common_ios())
        sys_clk_freq = core_config["sys_clk_freq"]
        cpu_type     = core_config["cpu"]
        csr_expose   = core_config.get("csr_expose", False)
        csr_align    = core_config.get("csr_align", 32)
        if cpu_type is None:
            kwargs["integrated_rom_size"]  = 0
            kwargs["integrated_sram_size"] = 0
            kwargs["l2_size"]              = 0
            kwargs["with_uart"]            = False
            kwargs["with_timer"]           = False
            kwargs["with_ctrl"]            = False
            kwargs["with_wishbone"]        = (cpu_type != None)
        else:
           kwargs["l2_size"] = 0
        SoCSDRAM.__init__(self, platform, sys_clk_freq,
            cpu_type=cpu_type,
            csr_alignment=csr_align,
            **kwargs)

        # crg
        self.submodules.crg = LiteDRAMCRG(platform, core_config)

        # sdram
        platform.add_extension(get_dram_ios(core_config))
        assert core_config["memtype"] in ["DDR2", "DDR3"]
        self.submodules.ddrphy = core_config["sdram_phy"](
            platform.request("ddram"),
            memtype=core_config["memtype"],
            nphases=4 if core_config["memtype"] == "DDR3" else 2,
            sys_clk_freq=sys_clk_freq,
            iodelay_clk_freq=core_config["iodelay_clk_freq"],
            cmd_latency=core_config["cmd_latency"])
        self.add_constant("CMD_DELAY", core_config["cmd_delay"])
        if core_config["memtype"] == "DDR3":
            self.ddrphy.settings.add_electrical_settings(
                rtt_nom=core_config["rtt_nom"],
                rtt_wr=core_config["rtt_wr"],
                ron=core_config["ron"])
        sdram_module = core_config["sdram_module"](sys_clk_freq,
            "1:4" if core_config["memtype"] == "DDR3" else "1:2")
        controller_settings = controller_settings=ControllerSettings(
            cmd_buffer_depth=core_config["cmd_buffer_depth"])
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings,
                            controller_settings=controller_settings)

        # sdram init
        self.submodules.ddrctrl = LiteDRAMCoreControl()
        self.comb += [
            platform.request("init_done").eq(self.ddrctrl.init_done.storage),
            platform.request("init_error").eq(self.ddrctrl.init_error.storage)
        ]

        # CSR port
        if csr_expose:
            csr_port = csr_bus.Interface(
                address_width=self.csr_address_width,
                data_width=self.csr_data_width)
            self.add_csr_master(csr_port)
            platform.add_extension(get_csr_ios(self.csr_address_width,
                                               self.csr_data_width))
            _csr_port_io = platform.request("csr_port", 0)
            self.comb += [
                csr_port.adr.eq(_csr_port_io.adr),
                csr_port.we.eq(_csr_port_io.we),
                csr_port.dat_w.eq(_csr_port_io.dat_w),
                _csr_port_io.dat_r.eq(csr_port.dat_r),
            ]
            if self.cpu_type == None:
                csr_base = core_config.get("csr_base", 0)
                self.shadow_base = csr_base;

        # user port
        self.comb += [
            platform.request("user_clk").eq(ClockSignal()),
            platform.request("user_rst").eq(ResetSignal())
        ]
        if core_config["user_ports_type"] == "native":
            for i in range(core_config["user_ports_nb"]):
                user_port = self.sdram.crossbar.get_port()
                platform.add_extension(get_native_user_port_ios(i,
                    user_port.address_width,
                    user_port.data_width))
                _user_port_io = platform.request("user_port", i)
                self.comb += [
                    # cmd
                    user_port.cmd.valid.eq(_user_port_io.cmd_valid),
                    _user_port_io.cmd_ready.eq(user_port.cmd.ready),
                    user_port.cmd.we.eq(_user_port_io.cmd_we),
                    user_port.cmd.addr.eq(_user_port_io.cmd_addr),

                    # wdata
                    user_port.wdata.valid.eq(_user_port_io.wdata_valid),
                    _user_port_io.wdata_ready.eq(user_port.wdata.ready),
                    user_port.wdata.we.eq(_user_port_io.wdata_we),
                    user_port.wdata.data.eq(_user_port_io.wdata_data),

                    # rdata
                    _user_port_io.rdata_valid.eq(user_port.rdata.valid),
                    user_port.rdata.ready.eq(_user_port_io.rdata_ready),
                    _user_port_io.rdata_data.eq(user_port.rdata.data),
                ]
        elif core_config["user_ports_type"] == "wishbone":
            for i in range(core_config["user_ports_nb"]):
                user_port = self.sdram.crossbar.get_port()
                wb_port = wishbone.Interface(
                    user_port.data_width,
                    user_port.address_width)
                wishbone2native = LiteDRAMWishbone2Native(wb_port, user_port)
                self.submodules += wishbone2native
                platform.add_extension(get_wishbone_user_port_ios(i,
                        len(wb_port.adr),
                        len(wb_port.dat_w)))
                _wb_port_io = platform.request("user_port", i)
                self.comb += [
                    wb_port.adr.eq(_wb_port_io.adr),
                    wb_port.dat_w.eq(_wb_port_io.dat_w),
                    _wb_port_io.dat_r.eq(wb_port.dat_r),
                    wb_port.sel.eq(_wb_port_io.sel),
                    wb_port.cyc.eq(_wb_port_io.cyc),
                    wb_port.stb.eq(_wb_port_io.stb),
                    _wb_port_io.ack.eq(wb_port.ack),
                    wb_port.we.eq(_wb_port_io.we),
                    _wb_port_io.err.eq(wb_port.err),
                ]
        elif core_config["user_ports_type"] == "axi":
            for i in range(core_config["user_ports_nb"]):
                user_port = self.sdram.crossbar.get_port()
                axi_port = LiteDRAMAXIPort(
                    user_port.data_width,
                    user_port.address_width + log2_int(user_port.data_width//8),
                    core_config["user_ports_id_width"])
                axi2native = LiteDRAMAXI2Native(axi_port, user_port)
                self.submodules += axi2native
                platform.add_extension(get_axi_user_port_ios(i,
                        axi_port.address_width,
                        axi_port.data_width,
                        core_config["user_ports_id_width"]))
                _axi_port_io = platform.request("user_port", i)
                self.comb += [
                    # aw
                    axi_port.aw.valid.eq(_axi_port_io.aw_valid),
                    _axi_port_io.aw_ready.eq(axi_port.aw.ready),
                    axi_port.aw.addr.eq(_axi_port_io.aw_addr),
                    axi_port.aw.burst.eq(_axi_port_io.aw_burst),
                    axi_port.aw.len.eq(_axi_port_io.aw_len),
                    axi_port.aw.size.eq(_axi_port_io.aw_size),
                    axi_port.aw.id.eq(_axi_port_io.aw_id),

                    # w
                    axi_port.w.valid.eq(_axi_port_io.w_valid),
                    _axi_port_io.w_ready.eq(axi_port.w.ready),
                    axi_port.w.last.eq(_axi_port_io.w_last),
                    axi_port.w.strb.eq(_axi_port_io.w_strb),
                    axi_port.w.data.eq(_axi_port_io.w_data),

                    # b
                    _axi_port_io.b_valid.eq(axi_port.b.valid),
                    axi_port.b.ready.eq(_axi_port_io.b_ready),
                    _axi_port_io.b_resp.eq(axi_port.b.resp),
                    _axi_port_io.b_id.eq(axi_port.b.id),

                    # ar
                    axi_port.ar.valid.eq(_axi_port_io.ar_valid),
                    _axi_port_io.ar_ready.eq(axi_port.ar.ready),
                    axi_port.ar.addr.eq(_axi_port_io.ar_addr),
                    axi_port.ar.burst.eq(_axi_port_io.ar_burst),
                    axi_port.ar.len.eq(_axi_port_io.ar_len),
                    axi_port.ar.size.eq(_axi_port_io.ar_size),
                    axi_port.ar.id.eq(_axi_port_io.ar_id),

                    # r
                    _axi_port_io.r_valid.eq(axi_port.r.valid),
                    axi_port.r.ready.eq(_axi_port_io.r_ready),
                    _axi_port_io.r_last.eq(axi_port.r.last),
                    _axi_port_io.r_resp.eq(axi_port.r.resp),
                    _axi_port_io.r_data.eq(axi_port.r.data),
                    _axi_port_io.r_id.eq(axi_port.r.id),
                ]
        else:
            raise ValueError("Unsupported port type: {}".format(core_config["user_ports_type"]))

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM standalone core generator")
    parser.add_argument("config", help="YAML config file")
    args = parser.parse_args()
    core_config = yaml.load(open(args.config).read(), Loader=yaml.Loader)

    # Convert YAML elements to Python/LiteX
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

    # Generate core
    platform = Platform()
    soc = LiteDRAMCore(platform, core_config, integrated_rom_size=0x6000)
    builder = Builder(soc, output_dir="build", compile_gateware=False)
    vns = builder.build(build_name="litedram_core", regular_comb=False)

    # Prepare core (could be improved)
    def replace_in_file(filename, _from, _to):
        # Read in the file
        with open(filename, "r") as file :
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace(_from, _to)

        # Write the file out again
        with open(filename, 'w') as file:
            file.write(filedata)

    if soc.cpu_type is not None:
        init_filename = "mem.init"
        os.system("mv build/gateware/{} build/gateware/litedram_core.init".format(init_filename))
        replace_in_file("build/gateware/litedram_core.v", init_filename, "litedram_core.init")

if __name__ == "__main__":
    main()
