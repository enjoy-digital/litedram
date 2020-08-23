#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import csv
import logging
import argparse
from operator import and_
from functools import reduce
from itertools import zip_longest

from migen import *
from migen.genlib.misc import WaitTimer

from litex.build.sim.config import SimConfig

from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litex.tools.litex_sim import SimSoC

from litedram.frontend.bist import _LiteDRAMBISTGenerator, _LiteDRAMBISTChecker
from litedram.frontend.bist import _LiteDRAMPatternGenerator, _LiteDRAMPatternChecker

# LiteDRAM Benchmark SoC ---------------------------------------------------------------------------

class LiteDRAMBenchmarkSoC(SimSoC):
    def __init__(self,
        mode             = "bist",
        sdram_module     = "MT48LC16M16",
        sdram_data_width = 32,
        bist_base        = 0x0000000,
        bist_end         = 0x0100000,
        bist_length      = 1024,
        bist_random      = False,
        bist_alternating = False,
        num_generators   = 1,
        num_checkers     = 1,
        access_pattern   = None,
        **kwargs):
        assert mode in ["bist", "pattern"]
        assert not (mode == "pattern" and access_pattern is None)

        # SimSoC -----------------------------------------------------------------------------------
        SimSoC.__init__(self,
            with_sdram       = True,
            sdram_module     = sdram_module,
            sdram_data_width = sdram_data_width,
            **kwargs
        )

        # BIST/Pattern Generator / Checker ---------------------------------------------------------
        if mode == "pattern":
            make_generator = lambda: _LiteDRAMPatternGenerator(self.sdram.crossbar.get_port(), init=access_pattern)
            make_checker   = lambda: _LiteDRAMPatternChecker(self.sdram.crossbar.get_port(),   init=access_pattern)
        if mode == "bist":
            make_generator = lambda: _LiteDRAMBISTGenerator(self.sdram.crossbar.get_port())
            make_checker   = lambda: _LiteDRAMBISTChecker(self.sdram.crossbar.get_port())

        generators = [make_generator() for _ in range(num_generators)]
        checkers   = [make_checker()   for _ in range(num_checkers)]
        self.submodules += generators + checkers

        if mode == "pattern":
            def bist_config(module):
                return []

            if not bist_alternating:
                address_set = set()
                for addr, _ in access_pattern:
                    assert addr not in address_set, \
                        "Duplicate address 0x%08x in access_pattern, write will overwrite previous value!" % addr
                    address_set.add(addr)
        if mode == "bist":
            # Make sure that we perform at least one access
            bist_length = max(bist_length, self.sdram.controller.interface.data_width // 8)
            def bist_config(module):
                return [
                    module.base.eq(bist_base),
                    module.end.eq(bist_end),
                    module.length.eq(bist_length),
                    module.random_addr.eq(bist_random),
                ]

            assert not (bist_random and not bist_alternating), \
                "Write to random address may overwrite previously written data before reading!"

            # Check address correctness
            assert bist_end > bist_base
            assert bist_end <= 2**(len(generators[0].end)) - 1, "End address outside of range"
            bist_addr_range = bist_end - bist_base
            assert bist_addr_range > 0 and bist_addr_range & (bist_addr_range - 1) == 0, \
                "Length of the address range must be a power of 2"

        def combined_read(modules, signal, operator):
            sig = Signal()
            self.comb += sig.eq(reduce(operator, (getattr(m, signal) for m in modules)))
            return sig

        def combined_write(modules, signal):
            sig = Signal()
            self.comb += [getattr(m, signal).eq(sig) for m in modules]
            return sig

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
        if bist_alternating:
            # Force generators to wait for checkers and vice versa. Connect them in pairs, with each
            # unpaired connected to the first of the others.
            bist_connections = []
            for generator, checker in zip_longest(generators, checkers):
                g = generator or generators[0]
                c = checker   or checkers[0]
                bist_connections += [
                    g.run_cascade_in.eq(c.run_cascade_out),
                    c.run_cascade_in.eq(g.run_cascade_out),
                ]

            fsm.act("BIST-GENERATOR",
                combined_write(generators + checkers, "start").eq(1),
                *bist_connections,
                *map(bist_config, generators + checkers),
                If(combined_read(checkers, "done", and_),
                    NextState("DISPLAY")
                )
            )
        else:
            fsm.act("BIST-GENERATOR",
                combined_write(generators, "start").eq(1),
                *map(bist_config, generators),
                If(combined_read(generators, "done", and_),
                    NextState("BIST-CHECKER")
                )
            )
            fsm.act("BIST-CHECKER",
                combined_write(checkers, "start").eq(1),
                *map(bist_config, checkers),
                If(combined_read(checkers, "done", and_),
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
        def max_signal(signals):
            signals = iter(signals)
            s       = next(signals)
            out     = Signal(len(s))
            self.comb += out.eq(s)
            for curr in signals:
                prev = out
                out = Signal(max(len(prev), len(curr)))
                self.comb +=  If(prev > curr, out.eq(prev)).Else(out.eq(curr))
            return out

        generator_ticks = max_signal((g.ticks  for g in generators))
        checker_errors  = max_signal((c.errors for c in checkers))
        checker_ticks   = max_signal((c.ticks  for c in checkers))

        self.sync += [
            If(display,
                Display("BIST-GENERATOR ticks:  %08d", generator_ticks),
                Display("BIST-CHECKER errors:   %08d", checker_errors),
                Display("BIST-CHECKER ticks:    %08d", checker_ticks),
            )
        ]

        # Simulation End ---------------------------------------------------------------------------
        end_timer = WaitTimer(2**16)
        self.submodules += end_timer
        self.comb += end_timer.wait.eq(finish)
        self.sync += If(end_timer.done, Finish())

# Build --------------------------------------------------------------------------------------------

def load_access_pattern(filename):
    with open(filename, newline="") as f:
        reader = csv.reader(f)
        access_pattern = [(int(addr, 0), int(data, 0)) for addr, data in reader]
    return access_pattern

def main():
    parser = argparse.ArgumentParser(description="LiteDRAM Benchmark SoC Simulation")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--threads",          default=1,              help="Set number of threads (default=1)")
    parser.add_argument("--sdram-module",     default="MT48LC16M16",  help="Select SDRAM chip")
    parser.add_argument("--sdram-data-width", default=32,             help="Set SDRAM chip data width")
    parser.add_argument("--sdram-verbosity",  default=0,              help="Set SDRAM checker verbosity")
    parser.add_argument("--trace",            action="store_true",    help="Enable VCD tracing")
    parser.add_argument("--trace-start",      default=0,              help="Cycle to start VCD tracing")
    parser.add_argument("--trace-end",        default=-1,             help="Cycle to end VCD tracing")
    parser.add_argument("--opt-level",        default="O0",           help="Compilation optimization level")
    parser.add_argument("--bist-base",        default="0x00000000",   help="Base address of the test (default=0)")
    parser.add_argument("--bist-length",      default="1024",         help="Length of the test (default=1024)")
    parser.add_argument("--bist-random",      action="store_true",    help="Use random data during the test")
    parser.add_argument("--bist-alternating", action="store_true",    help="Perform alternating writes/reads (WRWRWR... instead of WWW...RRR...)")
    parser.add_argument("--num-generators",   default=1,              help="Number of BIST generators")
    parser.add_argument("--num-checkers",     default=1,              help="Number of BIST checkers")
    parser.add_argument("--access-pattern",                           help="Load access pattern (address, data) from CSV (ignores --bist-*)")
    parser.add_argument("--log-level",        default="info",         help="Set logging verbosity",
        choices=["critical", "error", "warning", "info", "debug"])
    args = parser.parse_args()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, args.log_level.upper()))

    soc_kwargs     = soc_sdram_argdict(args)
    builder_kwargs = builder_argdict(args)

    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")

    # Configuration --------------------------------------------------------------------------------
    soc_kwargs["uart_name"]        = "sim"
    soc_kwargs["sdram_module"]     = args.sdram_module
    soc_kwargs["sdram_data_width"] = int(args.sdram_data_width)
    soc_kwargs["sdram_verbosity"]  = int(args.sdram_verbosity)
    soc_kwargs["bist_base"]        = int(args.bist_base, 0)
    soc_kwargs["bist_length"]      = int(args.bist_length, 0)
    soc_kwargs["bist_random"]      = args.bist_random
    soc_kwargs["bist_alternating"] = args.bist_alternating
    soc_kwargs["num_generators"]   = int(args.num_generators)
    soc_kwargs["num_checkers"]     = int(args.num_checkers)

    if args.access_pattern:
        soc_kwargs["access_pattern"] = load_access_pattern(args.access_pattern)

    # SoC ------------------------------------------------------------------------------------------
    soc = LiteDRAMBenchmarkSoC(mode="pattern" if args.access_pattern else "bist", **soc_kwargs)

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
