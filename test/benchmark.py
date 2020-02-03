#!/usr/bin/env python3

# This file is Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import argparse

from migen import *
from migen.genlib.misc import WaitTimer

from litex.build.sim.config import SimConfig

from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litex.tools.litex_sim import SimSoC

from litedram.frontend.bist import _LiteDRAMBISTGenerator
from litedram.frontend.bist import _LiteDRAMBISTChecker


# LiteDRAM Benchmark SoC ---------------------------------------------------------------------------

class LiteDRAMBenchmarkSoC(SimSoC):
    def __init__(self,
        sdram_module     = "MT48LC16M16",
        sdram_data_width = 32,
        bist_base        = 0x00000000,
        bist_length      = 1024,
        bist_random      = False,
        **kwargs):

        # SimSoC -----------------------------------------------------------------------------------
        SimSoC.__init__(self,
            with_sdram       = True,
            sdram_module     = sdram_module,
            sdram_data_width = sdram_data_width,
            **kwargs
        )

        # make sure that we perform at least one access
        bist_length = max(bist_length, self.sdram.controller.interface.data_width // 8)

        # BIST Generator ---------------------------------------------------------------------------
        bist_generator = _LiteDRAMBISTGenerator(self.sdram.crossbar.get_port())
        self.submodules.bist_generator = bist_generator

        # BIST Checker -----------------------------------------------------------------------------
        bist_checker = _LiteDRAMBISTChecker(self.sdram.crossbar.get_port())
        self.submodules.bist_checker = bist_checker

        # Sequencer --------------------------------------------------------------------------------
        class LiteDRAMCoreControl(Module, AutoCSR):
            def __init__(self):
                self.init_done  = CSRStorage()
                self.init_error = CSRStorage()
        self.submodules.ddrctrl = ddrctrl = LiteDRAMCoreControl()
        self.add_csr("ddrctrl")

        display = Signal()
        finish  = Signal()
        self.submodules.fsm = fsm = FSM(reset_state="WAIT-INIT")
        fsm.act("WAIT-INIT",
            If(self.ddrctrl.init_done.storage, # Written by CPU when initialization is done
                NextState("BIST-GENERATOR")
            )
        )
        fsm.act("BIST-GENERATOR",
            bist_generator.start.eq(1),
            bist_generator.base.eq(bist_base),
            bist_generator.length.eq(bist_length),
            bist_generator.random.eq(bist_random),
            If(bist_generator.done,
                NextState("BIST-CHECKER")
            )
        )
        fsm.act("BIST-CHECKER",
            bist_checker.start.eq(1),
            bist_checker.base.eq(bist_base),
            bist_checker.length.eq(bist_length),
            bist_checker.random.eq(bist_random),
            If(bist_checker.done,
                NextState("DISPLAY")
            )
        )
        fsm.act("DISPLAY",
            display.eq(1),
            NextState("FINISH")
        )
        fsm.act("FINISH",
            finish.eq(1)
        )

        # Simulation Results -----------------------------------------------------------------------
        self.sync += [
            If(display,
                Display("BIST-GENERATOR ticks:  %08d", bist_generator.ticks),
                Display("BIST-CHECKER errors:   %08d", bist_checker.errors),
                Display("BIST-CHECKER ticks:    %08d", bist_checker.ticks),
            )
        ]

        # Simulation End ---------------------------------------------------------------------------
        end_timer = WaitTimer(2**16)
        self.submodules += end_timer
        self.comb += end_timer.wait.eq(finish)
        self.sync += If(end_timer.done, Finish())

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM Benchmark SoC Simulation")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--threads",            default=1,              help="Set number of threads (default=1)")
    parser.add_argument("--sdram-module",       default="MT48LC16M16",  help="Select SDRAM chip")
    parser.add_argument("--sdram-data-width",   default=32,             help="Set SDRAM chip data width")
    parser.add_argument("--trace",              action="store_true",    help="Enable VCD tracing")
    parser.add_argument("--trace-start",        default=0,              help="Cycle to start VCD tracing")
    parser.add_argument("--trace-end",          default=-1,             help="Cycle to end VCD tracing")
    parser.add_argument("--opt-level",          default="O0",           help="Compilation optimization level")
    parser.add_argument("--bist-base",          default="0x00000000",   help="Base address of the test (default=0)")
    parser.add_argument("--bist-length",        default="1024",         help="Length of the test (default=1024)")
    parser.add_argument("--bist-random",        action="store_true",    help="Use random data during the test")
    args = parser.parse_args()

    soc_kwargs     = soc_sdram_argdict(args)
    builder_kwargs = builder_argdict(args)

    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")

    # Configuration --------------------------------------------------------------------------------
    soc_kwargs["sdram_module"]     = args.sdram_module
    soc_kwargs["sdram_data_width"] = int(args.sdram_data_width)
    soc_kwargs["bist_base"]        = int(args.bist_base, 0)
    soc_kwargs["bist_length"]      = int(args.bist_length, 0)
    soc_kwargs["bist_random"]      = args.bist_random

    # SoC ------------------------------------------------------------------------------------------
    soc = LiteDRAMBenchmarkSoC(**soc_kwargs)

    # Build/Run ------------------------------------------------------------------------------------
    builder_kwargs["csr_csv"] = "csr.csv"
    builder = Builder(soc, **builder_kwargs)
    vns = builder.build(
        threads     = args.threads,
        sim_config  = sim_config,
        opt_level   = args.opt_level,
        trace       = args.trace,
        trace_start = int(args.trace_start),
        trace_end   = int(args.trace_end)
    )

if __name__ == "__main__":
    main()
