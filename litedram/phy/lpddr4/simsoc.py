#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse

from migen import *

from litex.build.generic_platform import Pins, Subsignal
from litex.build.sim.config import SimConfig

from litex.soc.interconnect.csr import CSR
from litex.soc.integration.soc_core import SoCCore, soc_core_args, soc_core_argdict
from litex.soc.integration.builder import builder_args, builder_argdict, Builder
from litex.soc.cores.cpu import CPUS

from litedram.gen import LiteDRAMCoreControl
from litedram import modules as litedram_modules
from litedram.core.controller import ControllerSettings
from litedram.phy.model import DFITimingsChecker, _speedgrade_timings, _technology_timings

from litedram.phy.lpddr4.simphy import LPDDR4SimPHY, DoubleRateLPDDR4SimPHY
from litedram.phy.lpddr4.sim import LPDDR4Sim

from litedram.phy.sim_utils import Clocks, CRG, Platform

# Platform -----------------------------------------------------------------------------------------

_io = [
    # clocks added in main()
    ("lpddr4", 0,
        Subsignal("clk",   Pins(1)),
        # Subsignal("clk_n",   Pins(1)),
        Subsignal("cke",     Pins(1)),
        Subsignal("odt",     Pins(1)),
        Subsignal("reset_n", Pins(1)),
        Subsignal("cs",      Pins(1)),
        Subsignal("ca",      Pins(6)),
        Subsignal("dqs",     Pins(2)),
        # Subsignal("dqs_n",   Pins(2)),
        Subsignal("dmi",     Pins(2)),
        Subsignal("dq",      Pins(16)),
    ),
]

# Clocks -------------------------------------------------------------------------------------------

def get_clocks(sys_clk_freq):
    return Clocks({
        "sys":           dict(freq_hz=sys_clk_freq),
        "sys_11_25":     dict(freq_hz=sys_clk_freq, phase_deg=11.25),
        "sys2x":         dict(freq_hz=2*sys_clk_freq),
        "sys8x":         dict(freq_hz=8*sys_clk_freq),
        "sys8x_ddr":     dict(freq_hz=2*8*sys_clk_freq),
        "sys8x_90":      dict(freq_hz=8*sys_clk_freq, phase_deg=90),
        "sys8x_90_ddr":  dict(freq_hz=2*8*sys_clk_freq, phase_deg=2*90),
    })

# SoC ----------------------------------------------------------------------------------------------

class SimSoC(SoCCore):
    """Simulation of SoC with LPDDR4 DRAM

    This is a SoC used to run Verilator-based simulations of LiteDRAM with a simulated LPDDR4 chip.
    """
    def __init__(self, clocks, log_level,
            auto_precharge=False, with_refresh=True, trace_reset=0, disable_delay=False,
            masked_write=True, double_rate_phy=False, finish_after_memtest=False, **kwargs):
        platform     = Platform(_io, clocks)
        sys_clk_freq = clocks["sys"]["freq_hz"]

        # SoCCore ----------------------------------------------------------------------------------
        super().__init__(platform,
            clk_freq      = sys_clk_freq,
            ident         = "LiteX Simulation",
            cpu_variant   = "lite",
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform, clocks)

        # Debugging --------------------------------------------------------------------------------
        platform.add_debug(self, reset=trace_reset)

        # LPDDR4 -----------------------------------------------------------------------------------
        sdram_module = litedram_modules.MT53E256M16D1(sys_clk_freq, "1:8")
        pads = platform.request("lpddr4")
        sim_phy_cls = DoubleRateLPDDR4SimPHY if double_rate_phy else LPDDR4SimPHY
        self.submodules.ddrphy = sim_phy_cls(
            sys_clk_freq       = sys_clk_freq,
            aligned_reset_zero = True,
            masked_write       = masked_write,
        )

        for p in ["clk", "cke", "odt", "reset_n", "cs", "ca", "dq", "dqs", "dmi"]:
            self.comb += getattr(pads, p).eq(getattr(self.ddrphy.pads, p))

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

        # LPDDR4 Sim -------------------------------------------------------------------------------
        self.submodules.lpddr4sim = LPDDR4Sim(
            pads          = self.ddrphy.pads,
            cl            = self.sdram.controller.settings.phy.cl,
            cwl           = self.sdram.controller.settings.phy.cwl,
            sys_clk_freq  = sys_clk_freq,
            log_level     = log_level,
            disable_delay = disable_delay,
        )
        self.add_csr("lpddr4sim")

        self.add_constant("CONFIG_SIM_DISABLE_BIOS_PROMPT")
        if disable_delay:
            self.add_constant("CONFIG_DISABLE_DELAYS")
        if finish_after_memtest:
            self.submodules.ddrctrl = LiteDRAMCoreControl()
            self.add_csr("ddrctrl")
            self.sync += If(self.ddrctrl.init_done.storage, Finish())

        # Reuse DFITimingsChecker from phy/model.py
        nphases = self.sdram.controller.settings.phy.nphases
        timings = {"tCK": (1e9 / sys_clk_freq) / nphases}
        for name in _speedgrade_timings + _technology_timings:
            timings[name] = sdram_module.get(name)

        self.submodules.dfi_timings_checker = DFITimingsChecker(
            dfi          = self.ddrphy.dfi,
            nbanks       = 2**self.sdram.controller.settings.geom.bankbits,
            nphases      = nphases,
            timings      = timings,
            refresh_mode = sdram_module.timing_settings.fine_refresh_mode,
            memtype      = self.sdram.controller.settings.phy.memtype,
            verbose      = False,
        )

        # Debug info -------------------------------------------------------------------------------
        def dump(obj):
            print()
            print(" " + obj.__class__.__name__)
            print(" " + "-" * len(obj.__class__.__name__))
            d = obj if isinstance(obj, dict) else vars(obj)
            for var, val in d.items():
                if var == "self":
                    continue
                if isinstance(val, Signal):
                    val = "Signal(reset={})".format(val.reset.value)
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
    wrphase = soc.sdram.controller.settings.phy.wrphase.reset.value

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
            gtkw.regex_filter(["wrdata$", "p{}.*wrdata_en$".format(wrphase)]),
            gtkw.dfi_sorter(),
            gtkw.dfi_per_phase_colorer(),
        ])
        save.add(soc.ddrphy.dfi, group_name="dfi wrdata_mask", mappers=[
            gtkw.regex_filter(gtkw.suffixes2re(["wrdata_mask"])),
            gtkw.dfi_sorter(),
            gtkw.dfi_per_phase_colorer(),
        ])
        save.add(soc.ddrphy.dfi, group_name="dfi rddata", mappers=[
            gtkw.regex_filter(gtkw.suffixes2re(["rddata", "p0.*rddata_valid"])),
            gtkw.dfi_sorter(),
            gtkw.dfi_per_phase_colorer(),
        ])
        # serialization
        with save.gtkw.group("serialization", closed=True):
            if isinstance(soc.ddrphy, DoubleRateLPDDR4SimPHY):
                ser_groups = [("out 1x", soc.ddrphy._out), ("out 2x", soc.ddrphy.out)]
            else:
                ser_groups = [("out", soc.ddrphy.out)]
            for name, out in ser_groups:
                save.group([out.cs, out.dqs_o[0], out.dqs_oe, out.dmi_o[0], out.dmi_oe],
                    group_name = name,
                    mappers = [
                        gtkw.regex_colorer({
                            "yellow": gtkw.suffixes2re(["cs"]),
                            "orange": ["_o[^e]"],
                            "red": gtkw.suffixes2re(["oe"]),
                        })
                    ]
                )
        with save.gtkw.group("deserialization", closed=True):
            if isinstance(soc.ddrphy, DoubleRateLPDDR4SimPHY):
                ser_groups = [("in 1x", soc.ddrphy._out), ("in 2x", soc.ddrphy.out)]
            else:
                ser_groups = [("in", soc.ddrphy.out)]
            for name, out in ser_groups:
                save.group([out.dq_i[0], out.dq_oe, out.dqs_i[0], out.dqs_oe],
                    group_name = name,
                    mappers = [gtkw.regex_colorer({
                        "yellow": ["dqs"],
                        "orange": ["dq[^s]"],
                    })]
                )
        # dram pads
        save.group([s for s in vars(soc.ddrphy.pads).values() if isinstance(s, Signal)],
            group_name = "pads",
            mappers = [
                gtkw.regex_filter(["_[io]$"], negate=True),
                gtkw.regex_sorter(gtkw.suffixes2re(["cke", "odt", "reset_n", "clk", "cs", "ca", "dq", "dqs", "dmi", "oe"])),
                gtkw.regex_colorer({
                    "yellow": gtkw.suffixes2re(["cs", "ca"]),
                    "orange": gtkw.suffixes2re(["dq", "dqs", "dmi"]),
                    "red": gtkw.suffixes2re(["oe"]),
                }),
            ],
        )

def main():
    parser = argparse.ArgumentParser(description="Generic LiteX SoC Simulation")
    builder_args(parser.add_argument_group(title="Builder"))
    soc_core_args(parser.add_argument_group(title="SoC Core"))
    group = parser.add_argument_group(title="LPDDR4 simulation")
    group.add_argument("--sdram-verbosity",      default=0,               help="Set SDRAM checker verbosity")
    group.add_argument("--trace",                action="store_true",     help="Enable Tracing")
    group.add_argument("--trace-fst",            action="store_true",     help="Enable FST tracing (default=VCD)")
    group.add_argument("--trace-start",          default=0,               help="Cycle to start tracing")
    group.add_argument("--trace-end",            default=-1,              help="Cycle to end tracing")
    group.add_argument("--trace-reset",          default=0,               help="Initial traceing state")
    group.add_argument("--sys-clk-freq",         default="50e6",          help="Core clock frequency")
    group.add_argument("--auto-precharge",       action="store_true",     help="Use DRAM auto precharge")
    group.add_argument("--no-refresh",           action="store_true",     help="Disable DRAM refresher")
    group.add_argument("--log-level",            default="all=INFO",      help="Set simulation logging level")
    group.add_argument("--disable-delay",        action="store_true",     help="Disable CPU delays")
    group.add_argument("--gtkw-savefile",        action="store_true",     help="Generate GTKWave savefile")
    group.add_argument("--no-masked-write",      action="store_true",     help="Use LPDDR4 WRITE instead of MASKED-WRITE")
    group.add_argument("--no-run",               action="store_true",     help="Don't run the simulation, just generate files")
    group.add_argument("--double-rate-phy",      action="store_true",     help="Use sim PHY with 2-stage serialization")
    group.add_argument("--finish-after-memtest", action="store_true",     help="Stop simulation after DRAM memory test")
    args = parser.parse_args()

    soc_kwargs     = soc_core_argdict(args)
    builder_kwargs = builder_argdict(args)

    sim_config = SimConfig()
    sys_clk_freq = int(float(args.sys_clk_freq))
    clocks = get_clocks(sys_clk_freq)
    clocks.add_clockers(sim_config)

    # Configuration --------------------------------------------------------------------------------
    if soc_kwargs["uart_name"] == "serial":
        soc_kwargs["uart_name"] = "sim"
        sim_config.add_module("serial2console", "serial")
    args.with_sdram = True
    soc_kwargs["integrated_main_ram_size"] = 0x0
    soc_kwargs["sdram_verbosity"]          = int(args.sdram_verbosity)

    # SoC ------------------------------------------------------------------------------------------
    soc = SimSoC(
        clocks          = clocks,
        auto_precharge  = args.auto_precharge,
        with_refresh    = not args.no_refresh,
        trace_reset     = int(args.trace_reset),
        log_level       = args.log_level,
        disable_delay   = args.disable_delay,
        masked_write    = not args.no_masked_write,
        double_rate_phy = args.double_rate_phy,
        finish_after_memtest = args.finish_after_memtest,
        **soc_kwargs)

    # Build/Run ------------------------------------------------------------------------------------
    builder_kwargs["csr_csv"] = "csr.csv"
    builder = Builder(soc, **builder_kwargs)
    build_kwargs = dict(
        sim_config  = sim_config,
        trace       = args.trace,
        trace_fst   = args.trace_fst,
        trace_start = int(args.trace_start),
        trace_end   = int(args.trace_end)
    )
    vns = builder.build(run=False, **build_kwargs)

    if args.gtkw_savefile:
        generate_gtkw_savefile(builder, vns, trace_fst=args.trace_fst)

    if not args.no_run:
        builder.build(build=False, **build_kwargs)

if __name__ == "__main__":
    main()
