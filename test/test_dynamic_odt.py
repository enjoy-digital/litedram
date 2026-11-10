#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Dynamic ODT (ControllerSettings.with_dynamic_odt): ODT asserted around the WRITEs only, checked
in DRAM clocks on the DFI interface of the full controller under random traffic: the DRAM
termination (ODT delayed by ODTLon/ODTLoff = CWL-2) covers each write burst and is off around each
read burst (from before the preamble to after the postamble), with the DFI timings checker."""

import random
import unittest

from migen import *

from litedram.core.controller import ControllerSettings

from test.test_controller_timing import ControllerTimingDUT, _DDR3, _DDR4


class TestDynamicODT(unittest.TestCase):
    def odt_test(self, rate, clk_freq, ncycles=1500, seed=0, **settings_kwargs):
        cs   = ControllerSettings(with_dynamic_odt=True, **settings_kwargs)
        dut  = ControllerTimingDUT(_DDR3, rate, clk_freq, 16, trefi=200, controller_settings=cs)
        port = dut.port
        phy  = dut.controller.settings.phy
        nph  = phy.nphases
        cl, cwl = phy.cl, phy.cwl
        prng = random.Random(seed)
        odt, writes, reads = {}, [], []

        @passive
        def traffic():
            yield port.rdata.ready.eq(1)
            yield port.wdata.valid.eq(1)
            yield port.wdata.we.eq(2**len(port.wdata.we) - 1)
            while True:
                # Runs of reads or writes (back-to-back WRITEs: continuous ODT) and turnarounds.
                row = prng.randrange(2**port.address_width) & ~(2**dut.colbits - 1)
                we  = prng.randrange(2)
                for _ in range(prng.randrange(1, 6)):
                    yield port.cmd.valid.eq(1)
                    yield port.cmd.we.eq(we)
                    yield port.cmd.addr.eq(row | prng.randrange(2**dut.colbits))
                    yield
                    while not (yield port.cmd.ready):
                        yield
                    yield port.cmd.valid.eq(0)
                    for _ in range(prng.choice([0, 0, 1, 3, 8])):
                        yield

        def monitor():
            dfi = dut.controller.dfi
            for cycle in range(ncycles):
                yield
                for i, p in enumerate(dfi.phases):
                    k = cycle*nph + i # DRAM clock.
                    odt[k] = (yield p.odt)
                    if not (yield p.cs_n) and (yield p.ras_n) and not (yield p.cas_n):
                        (writes if not (yield p.we_n) else reads).append(k)
            self.assertEqual((yield dut.checker.errors), 0)

        run_simulation(dut, [monitor(), traffic()])
        self.assertGreater(len(writes), 20)
        self.assertGreater(len(reads), 20)
        nclks = ncycles*nph

        # ODT: asserted with each WRITE for ODTH8 = 6 clocks, deasserted otherwise.
        expected = {k: 0 for k in range(nclks)}
        for w in writes:
            for k in range(w, min(w + 6, nclks)):
                expected[k] = 1
        # (First mismatch reported: a diff of the full lists is too slow.)
        mismatches = [k for k in range(nclks) if odt[k] != expected[k]]
        self.assertEqual(mismatches[:1], [], f"ODT {odt[mismatches[0]] if mismatches else ''} at clock "
            f"{mismatches[:1]} ({len(mismatches)} mismatches)")

        # DRAM termination: RTT during DRAM clock k when ODT was registered at k - (CWL-2).
        def rtt(k):
            return odt.get(k - (cwl - 2), 0)
        margin = 0
        for w in writes:
            # Write preamble (WL-1) to the last data beat (WL+3).
            for k in range(w + cwl - 1, w + cwl + 4):
                if k - (cwl - 2) < nclks:
                    self.assertEqual(rtt(k), 1, f"no RTT during the WRITE at {w} (clock {k})")
        for r in reads:
            # From 1 clock before the read preamble (RL-1) to the postamble (RL+4).
            for k in range(r + cl - 2, r + cl + 5):
                self.assertEqual(rtt(k), 0, f"RTT during the READ at {r} (clock {k})")
        return writes, reads

    def test_ddr3_1to4(self):
        self.odt_test("1:4", 100e6)

    def test_ddr3_1to4_without_auto_precharge(self):
        self.odt_test("1:4", 100e6, with_auto_precharge=False)

    def test_ddr3_1to2(self):
        self.odt_test("1:2", 100e6)

    def test_ddr3_1to4_shared_bankmachines(self):
        self.odt_test("1:4", 100e6, nbankmachines=2)

    def test_unsupported(self):
        with self.assertRaises(NotImplementedError):
            ControllerTimingDUT(_DDR4, "1:4", 200e6, 16, trefi=200,
                controller_settings=ControllerSettings(with_dynamic_odt=True))

    def test_default_static_odt(self):
        # Without with_dynamic_odt, ODT stays asserted.
        dut = ControllerTimingDUT(_DDR3, "1:4", 100e6, 16, trefi=200)
        def check():
            for _ in range(20):
                yield
            for p in dut.controller.dfi.phases:
                self.assertEqual((yield p.odt), 1)
        run_simulation(dut, [check()])
