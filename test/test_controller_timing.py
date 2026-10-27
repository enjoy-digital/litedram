#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Full controller (bank machines, multiplexer, refresher, crossbar) under random traffic, with the
DFI timings checker of the PHY model verifying the DRAM command timings on the DFI interface."""

import random
import unittest

from migen import *

from litedram import modules
from litedram.common import burst_lengths
from litedram.modules import _speedgrade_timings, _technology_timings
from litedram.phy.dfi import Interface as DFIInterface
from litedram.phy.model import DFITimingsChecker, get_sdram_phy_settings
from litedram.core.controller import LiteDRAMController, ControllerSettings
from litedram.core.crossbar import LiteDRAMCrossbar


# Reduced geometry (2048 rows keep A10 in the DFI address for the precharge-all checks, 128 columns
# make most random accesses row misses); the timings are the module's.
class _DDR2(modules.MT47H64M16):  nrows, ncols = 2048, 128
class _DDR3(modules.MT41K128M16): nrows, ncols = 2048, 128
class _DDR4(modules.MT40A512M16): nrows, ncols = 2048, 128


class ControllerTimingDUT(Module):
    def __init__(self, module_cls, rate, clk_freq, data_width, trefi, controller_settings=None, verbose=False):
        module  = module_cls(clk_freq, rate)
        memtype = module.memtype
        nphases = int(rate.split(":")[1])
        # Short refresh period to get several refreshes in a short simulation (the checker only
        # verifies the refresh rate over 64ms, a shorter period never violates it).
        module.timing_settings.tREFI = trefi

        settings = get_sdram_phy_settings(memtype, data_width, clk_freq)
        dfi      = DFIInterface(
            addressbits = module.geom_settings.addressbits,
            bankbits    = module.geom_settings.bankbits,
            nranks      = settings.nranks,
            databits    = settings.dfi_databits,
            nphases     = settings.nphases)

        # DFI timings checker (as instantiated by SDRAMPHYModel).
        timings = {"tCK": (1e9/clk_freq)/nphases}
        for name in _speedgrade_timings + _technology_timings:
            key = module.timing_settings.fine_refresh_mode if name in ["tREFI", "tRFC"] else None
            timings[name] = module.get(name, key)
        self.submodules.checker = DFITimingsChecker(
            dfi          = dfi,
            nbanks       = 2**module.geom_settings.bankbits,
            nphases      = nphases,
            timings      = timings,
            refresh_mode = module.timing_settings.fine_refresh_mode,
            memtype      = memtype,
            verbose      = verbose)

        # Controller and crossbar.
        if controller_settings is None:
            controller_settings = ControllerSettings()
        self.submodules.controller = controller = LiteDRAMController(
            phy_settings        = settings,
            geom_settings       = module.geom_settings,
            timing_settings     = module.timing_settings,
            clk_freq            = clk_freq,
            controller_settings = controller_settings)
        self.comb += controller.dfi.connect(dfi)
        self.submodules.crossbar = crossbar = LiteDRAMCrossbar(controller.interface)
        self.port    = crossbar.get_port()
        # Port address layout (ROW_BANK_COL): column bits (the port address is aligned on the
        # burst length), then bank bits, then row bits.
        self.colbits  = module.geom_settings.colbits - log2_int(burst_lengths[memtype])
        self.bankbits = module.geom_settings.bankbits


class TestControllerTiming(unittest.TestCase):
    def controller_timing_test(self, module_cls, rate, clk_freq, data_width=16, trefi=100, ncycles=600,
                               seed=0, **kwargs):
        dut   = ControllerTimingDUT(module_cls, rate, clk_freq, data_width, trefi, **kwargs)
        port  = dut.port
        prng  = random.Random(seed)
        stats = {"cmds": 0}

        @passive
        def traffic():
            # Random reads/writes with row locality: a few accesses to random columns of a random
            # row (so that reads are followed by row hits, then by a precharge), with short gaps.
            # The controller does not need the read data back (the crossbar derives rdata.valid).
            yield port.rdata.ready.eq(1)
            yield port.wdata.valid.eq(1)
            yield port.wdata.we.eq(2**len(port.wdata.we) - 1)
            colbits = dut.colbits
            while True:
                row = prng.randrange(2**port.address_width) & ~(2**colbits - 1)
                for _ in range(prng.randrange(1, 5)):
                    yield port.cmd.valid.eq(1)
                    yield port.cmd.we.eq(prng.randrange(2))
                    yield port.cmd.addr.eq(row | prng.randrange(2**colbits))
                    yield port.wdata.data.eq(prng.randrange(2**port.data_width))
                    yield
                    while not (yield port.cmd.ready):
                        yield
                    stats["cmds"] += 1
                    yield port.cmd.valid.eq(0)
                    for _ in range(prng.randrange(8)):
                        yield

        def main():
            for _ in range(ncycles):
                yield
            self.assertEqual((yield dut.checker.errors), 0)
            self.assertGreater(stats["cmds"], ncycles//50)

        run_simulation(dut, [main(), traffic()])

    def directed_timing_test(self, module_cls, rate, clk_freq, **kwargs):
        # Deterministic scenarios on bank 0: a read with auto-precharge followed by an ACTIVATE,
        # and ACTIVATEs at every offset before a refresh request (the refresh PRECHARGE ALL has
        # to respect tRAS).
        dut  = ControllerTimingDUT(module_cls, rate, clk_freq, 16, trefi=100, **kwargs)
        port = dut.port

        def address(row, col=0):
            return (row << (dut.colbits + dut.bankbits)) | col

        def access(addr, we):
            yield port.cmd.valid.eq(1)
            yield port.cmd.we.eq(we)
            yield port.cmd.addr.eq(addr)
            yield
            while not (yield port.cmd.ready):
                yield
            yield port.cmd.valid.eq(0)

        def main():
            yield port.rdata.ready.eq(1)
            yield port.wdata.valid.eq(1)
            yield port.wdata.we.eq(2**len(port.wdata.we) - 1)
            for _ in range(8):
                yield
            # Open row 0, then (back-to-back) read it and read row 1: the first read gets the
            # auto-precharge, the ACTIVATE of row 1 has to come tRTP + tRP later.
            yield from access(address(0), 1)
            for _ in range(32):
                yield
            yield from access(address(0, 1), 0)
            yield from access(address(1), 0)
            for _ in range(32):
                yield
            # ACTIVATE k cycles before the refresh request.
            for k in range(8):
                while (yield dut.controller.refresher.timer.count) != k:
                    yield
                yield from access(address(2 + k), 1)
                for _ in range(48):
                    yield
            self.assertEqual((yield dut.checker.errors), 0)

        run_simulation(dut, [main()])

    def test_ddr2_1to2(self):
        self.controller_timing_test(_DDR2, "1:2", clk_freq=150e6)

    def test_ddr3_1to4(self):
        self.controller_timing_test(_DDR3, "1:4", clk_freq=200e6)

    def test_ddr3_1to4_without_auto_precharge(self):
        self.controller_timing_test(_DDR3, "1:4", clk_freq=200e6,
            controller_settings=ControllerSettings(with_auto_precharge=False))

    def test_ddr4_1to4(self):
        self.controller_timing_test(_DDR4, "1:4", clk_freq=300e6)

    def test_ddr3_1to4_directed(self):
        self.directed_timing_test(_DDR3, "1:4", clk_freq=200e6)

    def test_ddr4_1to4_directed(self):
        self.directed_timing_test(_DDR4, "1:4", clk_freq=300e6)
