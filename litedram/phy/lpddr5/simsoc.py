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
from litedram.modules import SDRAMModule, _TechnologyTimings, _SpeedgradeTimings
from litedram.core.controller import ControllerSettings
from litedram.phy.model import DFITimingsChecker, _speedgrade_timings, _technology_timings

from litedram.phy.sim_utils import Clocks, CRG, Platform
from litedram.phy.lpddr5.simphy import LPDDR5SimPHY
from litedram.phy.lpddr5.sim import LPDDR5Sim

# Platform -----------------------------------------------------------------------------------------

_io = [
    # clocks added in main
    ("lpddr5", 0,
        Subsignal("ck",      Pins(1)),  # ck_t/ck_c
        Subsignal("cs",      Pins(1)),
        Subsignal("ca",      Pins(7)),
        Subsignal("dq",      Pins(16)),
        Subsignal("wck",     Pins(2)),  # wck[1:0]_t/wck[1:0]_c
        Subsignal("rdqs",    Pins(2)),  # rdqs[1:0]_t/rdqs[1:0]_c
        Subsignal("dmi",     Pins(2)),
        Subsignal("reset_n", Pins(1)),
    ),
]

# Clocks -------------------------------------------------------------------------------------------

def get_clocks(sys_clk_freq, wck_ck_ratio):
    clocks = {
        "sys":           dict(freq_hz=sys_clk_freq),
        "sys2x":         dict(freq_hz=2*sys_clk_freq),
        "sys2x_180":     dict(freq_hz=2*sys_clk_freq, phase_deg=180),
    }
    clocks.update({
        2: {
            "sys4x":         dict(freq_hz=4*sys_clk_freq),
            "sys4x_180":     dict(freq_hz=4*sys_clk_freq, phase_deg=180),
        },
        4: {
            "sys8x":         dict(freq_hz=8*sys_clk_freq),
            "sys8x_180":     dict(freq_hz=8*sys_clk_freq, phase_deg=180),
        },
    }[wck_ck_ratio])
    return Clocks(clocks)

# SoC ----------------------------------------------------------------------------------------------

class LPDDR5ExampleModule(SDRAMModule):
    # 16B mode, 8Gb (32Mb x 16DQ x 16 banks)
    # x16, DVFSC disabled, Write Link ECC diabled
    # TODO: missing timings: tCCD, tZQCS
    memtype = "LPDDR5"

    nbanks      = 16
    nrows       = 32768
    ncols       = 1024

    # TODO: find a way to select if we need masked writes
    tccd = {"write": (8, None), "masked-write": (32, None)}

    technology_timings = _TechnologyTimings(tREFI=32e6/8192, tWTR=(4, 12), tCCD=tccd["masked-write"], tRRD=(2, 5), tZQCS=None)
    speedgrade_timings = {
        "default": _SpeedgradeTimings(tRP=(2, 21), tRCD=(2, 18), tWR=(3, 34), tRFC=210, tFAW=20, tRAS=(3, 42)),  # TODO: tRAS_max
    }

class SimSoC(SoCCore):
    """Simulation of SoC with LPDDR5 DRAM"""
    def __init__(self, clocks, log_level,
            auto_precharge=False, with_refresh=True, trace_reset=0, disable_delay=False,
            masked_write=True, finish_after_memtest=False, wck_ck_ratio=2, **kwargs):
        platform     = Platform(_io, clocks)
        sys_clk_freq = clocks["sys"]["freq_hz"]

        # SoCCore ----------------------------------------------------------------------------------
        super().__init__(platform,
            clk_freq      = sys_clk_freq,
            ident         = "LiteX Simulation",
            ident_version = True,
            cpu_variant   = "lite",
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform, clocks)

        # Debugging --------------------------------------------------------------------------------
        platform.add_debug(self, reset=trace_reset)

        # LPDDR5 -----------------------------------------------------------------------------------
        pads = platform.request("lpddr5")
        sdram_module = LPDDR5ExampleModule(sys_clk_freq, "1:1")
        sim_phy_cls = LPDDR5SimPHY
        self.submodules.ddrphy = sim_phy_cls(
            sys_clk_freq       = sys_clk_freq,
            aligned_reset_zero = True,
            masked_write       = masked_write,
            wck_ck_ratio       = wck_ck_ratio,
        )

        for p in ["ck", "cs", "ca", "dq", "wck", "rdqs", "dmi", "reset_n"]:
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

        # LPDDR5 Sim -------------------------------------------------------------------------------
        self.submodules.lpddr5sim = LPDDR5Sim(
            pads          = self.ddrphy.pads,
            ck_freq       = sys_clk_freq,
            log_level     = log_level,
        )

        self.add_constant("CONFIG_SIM_DISABLE_BIOS_PROMPT")
        if disable_delay:
            self.add_constant("CONFIG_DISABLE_DELAYS")
        if finish_after_memtest:
            self.submodules.ddrctrl = LiteDRAMCoreControl()
            self.sync += If(self.ddrctrl.init_done.storage, Finish())

        # # Reuse DFITimingsChecker from phy/model.py
        # nphases = self.sdram.controller.settings.phy.nphases
        # timings = {"tCK": (1e9 / sys_clk_freq) / nphases}
        # for name in _speedgrade_timings + _technology_timings:
        #     timings[name] = sdram_module.get(name)
        #
        # self.submodules.dfi_timings_checker = DFITimingsChecker(
        #     dfi          = self.ddrphy.dfi,
        #     nbanks       = 2**self.sdram.controller.settings.geom.bankbits,
        #     nphases      = nphases,
        #     timings      = timings,
        #     refresh_mode = sdram_module.timing_settings.fine_refresh_mode,
        #     memtype      = self.sdram.controller.settings.phy.memtype,
        #     verbose      = False,
        # )

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
            gtkw.regex_filter(["wrdata$", "p0.*wrdata_en$"]),
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
        # # serialization
        # with save.gtkw.group("serialization", closed=True):
        #     if isinstance(soc.ddrphy, DoubleRateLPDDR4SimPHY):
        #         ser_groups = [("out 1x", soc.ddrphy._out), ("out 2x", soc.ddrphy.out)]
        #     else:
        #         ser_groups = [("out", soc.ddrphy.out)]
        #     for name, out in ser_groups:
        #         save.group([out.cs, out.dqs_o[0], out.dqs_oe, out.dmi_o[0], out.dmi_oe],
        #             group_name = name,
        #             mappers = [
        #                 gtkw.regex_colorer({
        #                     "yellow": gtkw.suffixes2re(["cs"]),
        #                     "orange": ["_o[^e]"],
        #                     "red": gtkw.suffixes2re(["oe"]),
        #                 })
        #             ]
        #         )
        # with save.gtkw.group("deserialization", closed=True):
        #     if isinstance(soc.ddrphy, DoubleRateLPDDR4SimPHY):
        #         ser_groups = [("in 1x", soc.ddrphy._out), ("in 2x", soc.ddrphy.out)]
        #     else:
        #         ser_groups = [("in", soc.ddrphy.out)]
        #     for name, out in ser_groups:
        #         save.group([out.dq_i[0], out.dq_oe, out.dqs_i[0], out.dqs_oe],
        #             group_name = name,
        #             mappers = [gtkw.regex_colorer({
        #                 "yellow": ["dqs"],
        #                 "orange": ["dq[^s]"],
        #             })]
        #         )
        # dram pads
        save.group([s for s in vars(soc.ddrphy.pads).values() if isinstance(s, Signal)],
            group_name = "pads",
            mappers = [
                gtkw.regex_filter(["_[io]$"], negate=True),
                gtkw.regex_sorter(gtkw.suffixes2re(["reset_n", "ck", "cs", "ca", "dq", "wck", "dmi", "rdqs"])),
                gtkw.regex_colorer({
                    "yellow": gtkw.suffixes2re(["cs", "ca"]),
                    "orange": gtkw.suffixes2re(["dq", "wck", "dmi"]),
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
    group.add_argument("--sys-clk-freq",         default="100e6",         help="System clock frequency")
    group.add_argument("--auto-precharge",       action="store_true",     help="Use DRAM auto precharge")
    group.add_argument("--no-refresh",           action="store_true",     help="Disable DRAM refresher")
    group.add_argument("--wck-ck-ratio", default=2, type=int, choices=[2, 4], help="WCK:CK ratio")
    group.add_argument("--log-level",            default="all=INFO",      help="Set simulation logging level")
    group.add_argument("--disable-delay",        action="store_true",     help="Disable CPU delays")
    group.add_argument("--gtkw-savefile",        action="store_true",     help="Generate GTKWave savefile")
    group.add_argument("--no-masked-write",      action="store_true",     help="Use LPDDR4 WRITE instead of MASKED-WRITE")
    group.add_argument("--no-run",               action="store_true",     help="Don't run the simulation, just generate files")
    group.add_argument("--finish-after-memtest", action="store_true",     help="Stop simulation after DRAM memory test")
    args = parser.parse_args()

    soc_kwargs     = soc_core_argdict(args)
    builder_kwargs = builder_argdict(args)

    sim_config = SimConfig()
    sys_clk_freq = int(float(args.sys_clk_freq))
    clocks = get_clocks(sys_clk_freq, wck_ck_ratio=args.wck_ck_ratio)
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
        finish_after_memtest = args.finish_after_memtest,
        wck_ck_ratio    = args.wck_ck_ratio,
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

