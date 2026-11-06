#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Reorder ports: throughput across banks and data integrity against the DRAM model."""

import random
import unittest

from migen import *

from litex.gen.sim import run_simulation
from litex.soc.interconnect import stream

from litedram import modules
from litedram.core import LiteDRAMCore
from litedram.core.controller import ControllerSettings
from litedram.phy.model import SDRAMPHYModel, SDRAM_VERBOSE_STD, get_sdram_phy_settings

CLK_FREQ = 100e6


# Small geometry: the DRAM model's memory is what makes this simulation slow.
class _DDR3(modules.MT41K128M16):
    nrows, ncols = 2048, 16


class Master(Module):
    # Native port master following the contract: the write data is available the cycle after the
    # command is accepted, from a FIFO popped by wdata.ready.
    def __init__(self, port, fifo_depth=32):
        self.port = port
        self.wr_data = Signal(port.data_width)
        self.fifo = fifo = stream.SyncFIFO([("data", port.data_width)], fifo_depth)
        self.submodules += fifo
        self.comb += [
            fifo.sink.valid.eq(port.cmd.valid & port.cmd.ready & port.cmd.we),
            fifo.sink.data.eq(self.wr_data),
            port.wdata.data.eq(fifo.source.data),
            port.wdata.valid.eq(fifo.source.valid),
            port.wdata.we.eq(2**(port.data_width//8) - 1),
            fifo.source.ready.eq(port.wdata.ready),
            port.rdata.ready.eq(1),
        ]


class DUT(Module):
    def __init__(self, depth, reorder, second_port=None):
        module   = _DDR3(CLK_FREQ, "1:4")
        settings = get_sdram_phy_settings("DDR3", 16, CLK_FREQ)
        self.submodules.phy = SDRAMPHYModel(module=module, settings=settings, clk_freq=CLK_FREQ, verbosity=SDRAM_VERBOSE_STD)
        self.submodules.core = LiteDRAMCore(self.phy, module.geom_settings, module.timing_settings, CLK_FREQ,
            controller_settings=ControllerSettings(port_reorder_depth=depth))
        self.submodules.master = Master(self.core.crossbar.get_port(reorder=reorder))
        if second_port is not None:
            self.submodules.master2 = Master(self.core.crossbar.get_port(reorder=second_port))
        self.bank_shift = module.geom_settings.colbits - self.core.controller.interface.address_align


class TestPortReorder(unittest.TestCase):
    def throughput(self, dut, nbanks, we, n=300):
        port = dut.master.port
        result = {}
        cycles = Signal(32)
        dut.sync += cycles.eq(cycles + 1)

        def gen():
            for _ in range(40):
                yield
            yield port.cmd.valid.eq(1)
            yield port.cmd.we.eq(we)
            for i in range(n):
                yield port.cmd.addr.eq((i//nbanks)%2**dut.bank_shift | (i%nbanks) << dut.bank_shift)
                yield
                for _ in range(1000):
                    if (yield port.cmd.ready):
                        break
                    yield
                else:
                    self.fail("command not accepted")
                if i == 40:
                    t0 = (yield cycles)
            result["rate"] = (n - 41)/((yield cycles) - t0)
            yield port.cmd.valid.eq(0)

        run_simulation(dut, [gen()])
        return result["rate"]

    def test_throughput_across_banks(self):
        # Without reorder, each change of bank waits for the previous command to be issued.
        for we in [0, 1]:
            with self.subTest(we=we):
                locked  = self.throughput(DUT(depth=0, reorder=False), 4, we)
                # 16 commands in flight: a read takes about 14 cycles to come back.
                reorder = self.throughput(DUT(depth=16, reorder=True), 4, we)
                self.assertLess(locked, 0.4)
                self.assertGreater(reorder, 0.8)

    def traffic(self, dut, master, seed, nops, stats, row_base=0):
        # Random writes/reads, the read data being checked in command order against the last
        # value written, which is the order the commands of a bank keep.
        port     = master.port
        prng     = random.Random(seed)
        expected = []
        shadow   = {}

        def driver():
            for _ in range(40):
                yield
            for _ in range(nops):
                # A few addresses per bank, so that banks are interleaved with row hits and misses.
                bank = prng.randrange(8)
                adr  = ((row_base + prng.randrange(4)) << dut.bank_shift + 3) | (bank << dut.bank_shift) | prng.randrange(2**dut.bank_shift)
                we   = prng.randrange(2)
                data = prng.randrange(2**port.data_width)
                yield port.cmd.valid.eq(1)
                yield port.cmd.we.eq(we)
                yield port.cmd.addr.eq(adr)
                yield master.wr_data.eq(data)
                yield
                for _ in range(1000):
                    if (yield port.cmd.ready):
                        break
                    yield
                else:
                    self.fail("command not accepted")
                if we:
                    shadow[adr] = data
                else:
                    expected.append(shadow.get(adr))
                yield port.cmd.valid.eq(0)
                for _ in range(prng.choice([0, 0, 0, 1, 3])):
                    yield
            stats["sent"] = True

        def checker():
            n = 0
            for _ in range(nops*200):
                if (yield port.rdata.valid):
                    value = expected[n]
                    if value is not None:
                        self.assertEqual((yield port.rdata.data), value, f"read {n}")
                    n += 1
                if stats.get("sent") and n == len(expected):
                    stats["reads"] = n
                    stats["timing_errors"] = (yield dut.phy.timing_checker.errors)
                    return
                yield
            self.fail("read data missing")

        return [driver(), checker()]

    def test_data_integrity(self):
        for seed in range(3):
            with self.subTest(seed=seed):
                dut   = DUT(depth=8, reorder=True)
                stats = {}
                run_simulation(dut, self.traffic(dut, dut.master, seed, 600, stats))
                self.assertGreater(stats["reads"], 100)
                self.assertEqual(stats["timing_errors"], 0)

    def test_data_integrity_depth_16(self):
        dut   = DUT(depth=16, reorder=True)
        stats = {}
        run_simulation(dut, self.traffic(dut, dut.master, 3, 600, stats))
        self.assertGreater(stats["reads"], 100)
        self.assertEqual(stats["timing_errors"], 0)

    def test_data_integrity_depth_2(self):
        dut   = DUT(depth=2, reorder=True)
        stats = {}
        run_simulation(dut, self.traffic(dut, dut.master, 0, 300, stats))
        self.assertGreater(stats["reads"], 50)

    def test_two_ports(self):
        # Each port in its own rows, sharing the banks: with a reorder port, and with a locked one.
        for second_port in [True, False]:
            with self.subTest(second_port=second_port):
                dut    = DUT(depth=8, reorder=True, second_port=second_port)
                stats1, stats2 = {}, {}
                run_simulation(dut,
                    self.traffic(dut, dut.master,  0, 300, stats1, row_base=0) +
                    self.traffic(dut, dut.master2, 1, 300, stats2, row_base=8))
                self.assertGreater(stats1["reads"], 50)
                self.assertGreater(stats2["reads"], 50)
                self.assertEqual(stats1["timing_errors"], 0)

    def test_requires_setting(self):
        dut = DUT(depth=0, reorder=False)
        with self.assertRaises(ValueError):
            dut.core.crossbar.get_port(reorder=True)


if __name__ == "__main__":
    unittest.main()
