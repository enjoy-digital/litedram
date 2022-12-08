#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020-2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import argparse

from migen import *

from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.integration.common import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.integration.soc import *
from litex.soc.cores.bitbang import *
from litex.soc.cores.cpu import CPUS

from litedram.gen import LiteDRAMCoreControl
from litedram.modules import EM6GA16L
from litedram.core.controller import ControllerSettings
from litedram.phy.rpc.simphy import SimulationPHY

# Platform -----------------------------------------------------------------------------------------

_io = [
    # clocks added later
    ("sys_rst", 0, Pins(1)),

    ("serial", 0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data",  Pins(8)),
        Subsignal("sink_valid",   Pins(1)),
        Subsignal("sink_ready",   Pins(1)),
        Subsignal("sink_data",    Pins(8)),
    ),

    # RPC pads
    ("rpcdram", 0,
        Subsignal("clk_p", Pins(1)),
        Subsignal("clk_n", Pins(1)),
        Subsignal("cs_n",  Pins(1)),
        Subsignal("dqs_p", Pins(1)),
        Subsignal("dqs_n", Pins(1)),
        Subsignal("stb",   Pins(1)),
        Subsignal("db",    Pins(16)),
    ),
]

class Platform(SimPlatform):
    def __init__(self):
        print('_io', end=' = '); __import__('pprint').pprint(_io)
        SimPlatform.__init__(self, "SIM", _io)

# DFI PHY model settings ---------------------------------------------------------------------------

sdram_module_nphases = {
    "SDR":   1,
    "DDR":   2,
    "LPDDR": 2,
    "DDR2":  2,
    "DDR3":  4,
    "RPC":   4,
    "DDR4":  4,
}

def get_sdram_phy_settings(memtype, data_width, clk_freq):
    nphases = sdram_module_nphases[memtype]
    assert memtype == "DDR3"

    # Settings from s7ddrphy
    tck                 = 2/(2*nphases*clk_freq)
    cmd_latency         = 0
    cl, cwl             = get_cl_cw(memtype, tck)
    cl_sys_latency      = get_sys_latency(nphases, cl)
    cwl                 = cwl + cmd_latency
    cwl_sys_latency     = get_sys_latency(nphases, cwl)
    rdcmdphase, rdphase = get_sys_phases(nphases, cl_sys_latency, cl)
    wrcmdphase, wrphase = get_sys_phases(nphases, cwl_sys_latency, cwl)
    read_latency        = 2 + cl_sys_latency + 2 + 3
    write_latency       = cwl_sys_latency

    sdram_phy_settings = {
        "nphases":       nphases,
        "rdphase":       rdphase,
        "wrphase":       wrphase,
        "rdcmdphase":    rdcmdphase,
        "wrcmdphase":    wrcmdphase,
        "cl":            cl,
        "cwl":           cwl,
        "read_latency":  read_latency,
        "write_latency": write_latency,
    }

    return PhySettings(
        phytype      = "SDRAMPHYModel",
        memtype      = memtype,
        databits     = data_width,
        dfi_databits = data_width if memtype == "SDR" else 2*data_width,
        **sdram_phy_settings,
    )

# Clocks -------------------------------------------------------------------------------------------

class Clocks(dict):
    # FORMAT: {name: {"freq_hz": _, "phase_deg": _}, ...}
    def names(self):
        return list(self.keys())

    def add_io(self, io):
        for name in self.names():
            print((name + "_clk", 0, Pins(1)))
            io.append((name + "_clk", 0, Pins(1)))

    def add_clockers(self, sim_config):
        for name, desc in self.items():
            sim_config.add_clocker(name + "_clk", **desc)

class _CRG(Module):
    def __init__(self, platform, domains=None):
        if domains is None:
            domains = ["sys"]
        # request() before clreating domains to avoid signal renaming problem
        domains = {name: platform.request(name + "_clk") for name in domains}

        self.clock_domains.cd_por = ClockDomain(reset_less=True)
        for name in domains.keys():
            setattr(self.clock_domains, "cd_" + name, ClockDomain(name=name))

        int_rst = Signal(reset=1)
        self.sync.por += int_rst.eq(0)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)

        for name, clk in domains.items():
            cd = getattr(self, "cd_" + name)
            self.comb += cd.clk.eq(clk)
            self.comb += cd.rst.eq(int_rst)

# Simulation SoC -----------------------------------------------------------------------------------

class SimSoC(SoCCore):
    def __init__(self, clocks, trace_reset=1, auto_precharge=False, with_refresh=True, **kwargs):
        platform     = Platform()
        sys_clk_freq = clocks["sys"]["freq_hz"]

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            ident       = "LiteX Simulation",
            cpu_variant = "lite",
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, clocks.names())

        # Debugging --------------------------------------------------------------------------------
        platform.add_debug(self, reset=trace_reset)

        # RPC DRAM ---------------------------------------------------------------------------------
        sdram_module = EM6GA16L(sys_clk_freq, "1:4")
        pads = platform.request("rpcdram")
        self.submodules.ddrphy = SimulationPHY(pads, sys_clk_freq=sys_clk_freq, generate_read_data=True)
        self.add_csr("ddrphy")

        controller_settings = ControllerSettings()
        controller_settings.auto_precharge = auto_precharge
        controller_settings.with_refresh = with_refresh

        self.add_sdram("sdram",
            phy                     = self.ddrphy,
            module                  = sdram_module,
            origin                  = self.mem_map["main_ram"],
            size                    = kwargs.get("max_sdram_size", 0x40000000),
            l2_cache_size           = kwargs.get("l2_size", 8192),
            l2_cache_min_data_width = kwargs.get("min_l2_data_width", 128),
            l2_cache_reverse        = False,
            controller_settings     = controller_settings
        )
        # Reduce memtest size for simulation speedup
        self.add_constant("MEMTEST_DATA_SIZE", 8*1024)
        self.add_constant("MEMTEST_ADDR_SIZE", 8*1024)

        self.add_constant("CONFIG_SIM_DISABLE_BIOS_PROMPT")
        # self.add_constant("CONFIG_DISABLE_DELAYS")

        self.submodules.ddrctrl = LiteDRAMCoreControl()
        self.add_csr("ddrctrl")
        self.sync += If(self.ddrctrl.init_done.storage, Finish())

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
        dump(clocks)
        dump(self.ddrphy.settings)
        dump(sdram_module.geom_settings)
        dump(sdram_module.timing_settings)
        print()
        print("=" * 80)

# Build --------------------------------------------------------------------------------------------

def generate_gtkw_savefile(builder, vns, trace_fst):
    from litex.build.sim import gtkwave as gtkw

    dumpfile = os.path.join(builder.gateware_dir, "sim.{}".format("fst" if trace_fst else "vcd"))
    savefile = os.path.join(builder.gateware_dir, "sim.gtkw")
    soc = builder.soc
    rdphase = soc.sdram.controller.settings.phy.rdphase
    wrphase = soc.sdram.controller.settings.phy.wrphase

    with gtkw.GTKWSave(vns, savefile=savefile, dumpfile=dumpfile) as save:
        save.clocks()
        save.add(soc.bus.slaves["main_ram"], mappers=[gtkw.wishbone_sorter(), gtkw.wishbone_colorer()])
        save.fsm_states(soc)
        # all dfi signals
        save.add(soc.ddrphy.dfi, mappers=[gtkw.dfi_sorter(), gtkw.dfi_in_phase_colorer()])
        # each phase in separate group
        with save.gtkw.group("dfi phaseX", closed=True):
            for i, phase in enumerate(soc.ddrphy.dfi.phases):
                save.add(phase, group_name="dfi p{}".format(i), mappers=[
                    gtkw.dfi_sorter(phases=False),
                    gtkw.dfi_in_phase_colorer(),
                ])
        # only dfi command signals
        save.add(soc.ddrphy.dfi, group_name="dfi commands", mappers=[
            gtkw.regex_filter(gtkw.suffixes2re(["cas_n", "ras_n", "we_n"])),
            gtkw.dfi_sorter(),
            gtkw.dfi_per_phase_colorer(),
        ])
        # only dfi data signals
        save.add(soc.ddrphy.dfi, group_name="dfi wrdata", mappers=[
            gtkw.regex_filter(["wrdata$", f"p{wrphase}.*wrdata_en$"]),
            gtkw.dfi_sorter(),
            gtkw.dfi_per_phase_colorer(),
        ])
        save.add(soc.ddrphy.dfi, group_name="dfi wrdata_mask", mappers=[
            gtkw.regex_filter(gtkw.suffixes2re(["wrdata_mask"])),
            gtkw.dfi_sorter(),
            gtkw.dfi_per_phase_colorer(),
        ])
        save.add(soc.ddrphy.dfi, group_name="dfi rddata", mappers=[
            gtkw.regex_filter(gtkw.suffixes2re(["rddata", f"p{rdphase}.*rddata_valid"])),
            gtkw.dfi_sorter(),
            gtkw.dfi_per_phase_colorer(),
        ])
        # dram pads
        save.group([s for s in vars(soc.ddrphy.pads).values() if isinstance(s, Signal)],
            group_name = "pads",
            mappers = [
                gtkw.regex_filter(gtkw.suffixes2re(["dqs_n", "clk_n"]), negate=True),
                gtkw.regex_sorter(["clk", "cs", "stb", "db", "dqs"]),
                gtkw.regex_colorer({
                    "yellow": gtkw.suffixes2re(["cs"]),
                    "orange": gtkw.suffixes2re(["db", "dqs"]),
                    "red": gtkw.suffixes2re(["stb"]),
                }),
            ],
        )


def main():
    parser = argparse.ArgumentParser(description="Generic LiteX SoC Simulation")
    builder_args(parser)
    soc_core_args(parser)
    parser.add_argument("--threads",         default=1,           help="Set number of threads (default=1)")
    parser.add_argument("--rom-init",        default=None,        help="rom_init file")
    parser.add_argument("--sdram-init",      default=None,        help="SDRAM init file")
    parser.add_argument("--sdram-verbosity", default=0,           help="Set SDRAM checker verbosity")
    parser.add_argument("--trace",           action="store_true", help="Enable Tracing")
    parser.add_argument("--trace-fst",       action="store_true", help="Enable FST tracing (default=VCD)")
    parser.add_argument("--trace-start",     default=0,           help="Cycle to start tracing")
    parser.add_argument("--trace-end",       default=-1,          help="Cycle to end tracing")
    parser.add_argument("--trace-reset",     default=1,           help="Tracing state at start")
    parser.add_argument("--opt-level",       default="O3",        help="Compilation optimization level")
    parser.add_argument("--sys-clk-freq",    default="100e6",     help="Core clock frequency")
    parser.add_argument("--auto-precharge",  action="store_true", help="Use DRAM auto precharge")
    parser.add_argument("--no-refresh",      action="store_true", help="Disable DRAM refresher")
    parser.add_argument("--gtkw-savefile",   action="store_true", help="Generate GTKWSave savefile")
    args = parser.parse_args()

    soc_kwargs     = soc_core_argdict(args)
    builder_kwargs = builder_argdict(args)

    sys_clk_freq = int(float(args.sys_clk_freq))
    clocks = Clocks({
        "sys":           dict(freq_hz=sys_clk_freq),
        "sys2x":         dict(freq_hz=2*sys_clk_freq),
        "sys4x":         dict(freq_hz=4*sys_clk_freq),
        "sys4x_90":      dict(freq_hz=4*sys_clk_freq, phase_deg=90),
        "sys4x_180":     dict(freq_hz=4*sys_clk_freq, phase_deg=180),
        "sys4x_90_ddr":  dict(freq_hz=2*4*sys_clk_freq, phase_deg=2*90),
        "sys4x_180_ddr": dict(freq_hz=2*4*sys_clk_freq, phase_deg=(2*180)%360),
    })

    clocks.add_io(_io)

    sim_config = SimConfig()
    clocks.add_clockers(sim_config)

    # Configuration --------------------------------------------------------------------------------

    cpu = CPUS[soc_kwargs.get("cpu_type", "vexriscv")]
    if soc_kwargs["uart_name"] == "serial":
        soc_kwargs["uart_name"] = "sim"
        sim_config.add_module("serial2console", "serial")
    if args.rom_init:
        soc_kwargs["integrated_rom_init"] = get_mem_data(args.rom_init, endianness=cpu.endianness)
    args.with_sdram = True
    soc_kwargs["integrated_main_ram_size"] = 0x0
    soc_kwargs["sdram_verbosity"]          = int(args.sdram_verbosity)

    # SoC ------------------------------------------------------------------------------------------
    soc = SimSoC(
        clocks         = clocks,
        trace_reset    = args.trace_reset,
        auto_precharge = args.auto_precharge,
        with_refresh   = not args.no_refresh,
        sdram_init     = [] if args.sdram_init is None else get_mem_data(args.sdram_init, endianness=cpu.endianness),
        l2_size        = args.l2_size,
        **soc_kwargs)

    # Build/Run ------------------------------------------------------------------------------------
    builder_kwargs["csr_csv"] = "csr.csv"
    builder = Builder(soc, **builder_kwargs)
    vns = builder.build(run=False, threads=args.threads, sim_config=sim_config,
        opt_level   = args.opt_level,
        trace       = args.trace,
        trace_fst   = args.trace_fst,
        trace_start = int(args.trace_start),
        trace_end   = int(args.trace_end))

    if args.gtkw_savefile:
        generate_gtkw_savefile(builder, vns, trace_fst=args.trace_fst)

    builder.build(build=False, threads=args.threads, sim_config=sim_config,
        opt_level   = args.opt_level,
        trace       = args.trace,
        trace_fst   = args.trace,
        trace_start = int(args.trace_start),
        trace_end   = int(args.trace_end)
    )

if __name__ == "__main__":
    main()
