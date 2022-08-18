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

from litedram.phy.ddr5.simphy import DDR5SimPHY, DoubleRateDDR5SimPHY
from litedram.phy.ddr5.sim import DDR5Sim

from litedram.phy.sim_utils import Clocks, CRG, Platform

# Platform -----------------------------------------------------------------------------------------

# clocks added in main()
_io = {
    4: [
        ("ddr5", 0,
         Subsignal("ck_t",     Pins(1)),
         Subsignal("ck_c",     Pins(1)),
         Subsignal("cs_n",      Pins(1)),
         # dmi is not supported on x4 device, I decided to keep it to make model simpler
         Subsignal("dm_n",      Pins(1)),

         Subsignal("ca",        Pins(14)),
         Subsignal("reset_n",   Pins(1)),
         # DQ and DQS are taken from DDR5 Tester board
         Subsignal("dq",        Pins(4)),
         Subsignal("dqs_t",     Pins(1)),
         Subsignal("dqs_c",     Pins(1)),

         Subsignal("mir",       Pins(1)),
         Subsignal("cai",       Pins(1)),
         Subsignal("ca_odt",    Pins(1)),
        ),
    ],
    8: [
        ("ddr5", 0,
         Subsignal("ck_t",     Pins(1)),
         Subsignal("ck_c",     Pins(1)),
         Subsignal("cs_n",      Pins(1)),

         Subsignal("dm_n",      Pins(1)),

         Subsignal("ca",        Pins(14)),
         Subsignal("reset_n",   Pins(1)),

         Subsignal("dq",        Pins(8)),
         Subsignal("dqs_t",     Pins(1)),
         Subsignal("dqs_c",     Pins(1)),

         Subsignal("mir",       Pins(1)),
         Subsignal("cai",       Pins(1)),
         Subsignal("ca_odt",    Pins(1)),
        ),
    ]
}

# Clocks -------------------------------------------------------------------------------------------

def get_clocks(sys_clk_freq):
    return Clocks({
        "sys":           dict(freq_hz=sys_clk_freq),
        "sys_11_25":     dict(freq_hz=sys_clk_freq, phase_deg=11.25),
        "sys2x":         dict(freq_hz=2*sys_clk_freq),
        "sys4x":         dict(freq_hz=4*sys_clk_freq),
        "sys4x_ddr":     dict(freq_hz=2*4*sys_clk_freq),
        "sys4x_90":      dict(freq_hz=4*sys_clk_freq, phase_deg=90),
        "sys4x_180":     dict(freq_hz=4*sys_clk_freq, phase_deg=180),
        "sys4x_90_ddr":  dict(freq_hz=2*4*sys_clk_freq, phase_deg=2*90),
    })

# SoC ----------------------------------------------------------------------------------------------

class SimSoC(SoCCore):
    """Simulation of SoC with DDR5 DRAM

    This is a SoC used to run Verilator-based simulations of LiteDRAM with a simulated DDR5 chip.
    """
    def __init__(self, clocks, log_level,
            auto_precharge=False, with_refresh=True, trace_reset=0,
            masked_write=False, double_rate_phy=False, finish_after_memtest=False, dq_dqs_ratio=8, **kwargs):
        platform     = Platform(_io[dq_dqs_ratio], clocks)
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

        # DDR5 -----------------------------------------------------------------------------------
        if dq_dqs_ratio == 8:
            sdram_module = litedram_modules.MT60B2G8HB48B(sys_clk_freq, "1:4")
        elif dq_dqs_ratio == 4:
            sdram_module = litedram_modules.M329R8GA0BB0(sys_clk_freq, "1:4")
            if masked_write:
                masked_write = False
                print("Masked Write is unsupported for x4 device (JESD79-5A, section 4.8.1)")
        else:
            raise NotImplementedError(f"Unspupported DQ:DQS ratio: {dq_dqs_ratio}")

        pads = platform.request("ddr5")
        sim_phy_cls = DoubleRateDDR5SimPHY if double_rate_phy else DDR5SimPHY
        self.submodules.ddrphy = sim_phy_cls(
            sys_clk_freq       = sys_clk_freq,
            aligned_reset_zero = True,
            masked_write       = masked_write,
            dq_dqs_ratio       = dq_dqs_ratio,
        )

        for p in _io[dq_dqs_ratio][0][2:]:
            self.comb += getattr(pads, p.name).eq(getattr(self.ddrphy.pads, p.name))

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

        # DDR5 Sim -------------------------------------------------------------------------------
        self.submodules.ddr5sim = DDR5Sim(
            pads          = self.ddrphy.pads,
            cl            = self.sdram.controller.settings.phy.cl,
            cwl           = self.sdram.controller.settings.phy.cwl,
            sys_clk_freq  = sys_clk_freq,
            log_level     = log_level,
            geom_settings = sdram_module.geom_settings
        )
        self.add_csr("ddr5sim")

        self.add_constant("CONFIG_SIM_DISABLE_BIOS_PROMPT")
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
            if isinstance(soc.ddrphy, DoubleRateDDR5SimPHY):
                ser_groups = [("out 1x", soc.ddrphy._out), ("out 2x", soc.ddrphy.out)]
            else:
                ser_groups = [("out", soc.ddrphy.out)]
            for name, out in ser_groups:
                save.group([out.dqs_t_o[0], out.dqs_t_oe, out.dm_n_o[0], out.dm_n_oe],
                    group_name = name,
                    mappers = [
                        gtkw.regex_colorer({
                            "yellow": gtkw.suffixes2re(["cs_n"]),
                            "orange": ["_o[^e]"],
                            "red": gtkw.suffixes2re(["oe"]),
                        })
                    ]
                )
        with save.gtkw.group("deserialization", closed=True):
            if isinstance(soc.ddrphy, DoubleRateDDR5SimPHY):
                ser_groups = [("in 1x", soc.ddrphy._out), ("in 2x", soc.ddrphy.out)]
            else:
                ser_groups = [("in", soc.ddrphy.out)]
            for name, out in ser_groups:
                save.group([out.dq_i[0], out.dq_oe, out.dqs_t_i[0], out.dqs_t_oe],
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
                gtkw.regex_sorter(gtkw.suffixes2re(["clk", "mir", "cai", "ca_odt", "reset_n", "cs_n", "ca", "dq", "dqs", "dmi", "oe"])),
                gtkw.regex_colorer({
                    "yellow": gtkw.suffixes2re(["cs_n", "ca"]),
                    "orange": gtkw.suffixes2re(["dq", "dqs", "dmi"]),
                    "red": gtkw.suffixes2re(["oe"]),
                }),
            ],
        )

def main():
    parser = argparse.ArgumentParser(description="Generic LiteX SoC Simulation")
    builder_args(parser.add_argument_group(title="Builder"))
    soc_core_args(parser.add_argument_group(title="SoC Core"))
    group = parser.add_argument_group(title="DDR5 simulation")
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
    group.add_argument("--no-masked-write",      action="store_true",     help="Use unmasked variant of WRITE command")
    group.add_argument("--no-run",               action="store_true",     help="Don't run the simulation, just generate files")
    group.add_argument("--double-rate-phy",      action="store_true",     help="Use sim PHY with 2-stage serialization")
    group.add_argument("--finish-after-memtest", action="store_true",     help="Stop simulation after DRAM memory test")
    group.add_argument("--dq-dqs-ratio",         default=8,               help="Set DQ:DQS ratio", type=int, choices={4, 8})
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
        masked_write    = not args.no_masked_write,
        double_rate_phy = args.double_rate_phy,
        finish_after_memtest = args.finish_after_memtest,
        dq_dqs_ratio    = args.dq_dqs_ratio,
        **soc_kwargs)

    # Build/Run ------------------------------------------------------------------------------------
    def pre_run_callback(vns):
        if args.trace:
            generate_gtkw_savefile(builder, vns, args.trace_fst)

    builder_kwargs["csr_csv"] = "csr.csv"
    builder = Builder(soc, **builder_kwargs)
    build_kwargs = dict(
        sim_config  = sim_config,
        trace       = args.trace,
        trace_fst   = args.trace_fst,
        trace_start = int(args.trace_start),
        trace_end   = int(args.trace_end),
        pre_run_callback = pre_run_callback,
    )
    builder.build(run=not args.no_run, **build_kwargs)

if __name__ == "__main__":
    main()
