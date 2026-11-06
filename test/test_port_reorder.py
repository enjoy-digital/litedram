#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Reorder ports: throughput across banks and data integrity against the DRAM model.

Frontends run a subset of widths by default, LITEDRAM_TEST_FULL=1 runs all of them."""

import os
import random
import unittest

from migen import *

from litex.gen.sim import run_simulation
from litex.soc.interconnect import avalon, stream, wishbone
from litex.soc.interconnect.axi import BURST_INCR, AXIInterface

from litedram import modules
from litedram.core import LiteDRAMCore
from litedram.core.controller import ControllerSettings
from litedram.frontend.avalon import LiteDRAMAvalonMM2Native
from litedram.frontend.axi import LiteDRAMAXI2Native
from litedram.frontend.wishbone import LiteDRAMWishbone2Native, LiteDRAMWishbonePipelined2Native
from litedram.phy.model import SDRAMPHYModel, SDRAM_VERBOSE_STD, get_sdram_phy_settings

from test.common import timeout_generator

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


# Frontends ----------------------------------------------------------------------------------------

REORDER_FRONTENDS = True # False runs the same traffic on locked ports, as a reference.

full = unittest.skipUnless(os.environ.get("LITEDRAM_TEST_FULL", "0") == "1", "set LITEDRAM_TEST_FULL=1 to run")

# Words of the controller's data width per region: 2 columns x 8 banks x 4 rows, so that random
# addresses interleave the banks with row hits and misses.
CONTROLLER_WIDTH = 128
REGION_WORDS     = 64


class Shadow:
    """Expected memory content, per byte (the DRAM model starts at 0)."""
    def __init__(self, data_width):
        self.nbytes = data_width//8
        self.mem    = {}

    def write(self, adr, data, sel=None):
        for i in range(self.nbytes):
            if sel is None or (sel >> i) & 1:
                self.mem[adr*self.nbytes + i] = (data >> 8*i) & 0xff

    def read(self, adr):
        return sum(self.mem.get(adr*self.nbytes + i, 0) << 8*i for i in range(self.nbytes))


class FrontendDUT(Module):
    def __init__(self, reorder=REORDER_FRONTENDS, depth=16):
        module   = _DDR3(CLK_FREQ, "1:4")
        settings = get_sdram_phy_settings("DDR3", 16, CLK_FREQ)
        self.submodules.phy = SDRAMPHYModel(module=module, settings=settings, clk_freq=CLK_FREQ, verbosity=SDRAM_VERBOSE_STD)
        self.submodules.core = LiteDRAMCore(self.phy, module.geom_settings, module.timing_settings, CLK_FREQ,
            controller_settings=ControllerSettings(port_reorder_depth=depth))
        self.reorder = reorder
        assert self.core.crossbar.controller.data_width == CONTROLLER_WIDTH

    def get_port(self, **kwargs):
        return self.core.crossbar.get_port(reorder=self.reorder, **kwargs)


def _random_data(prng, data_width):
    return prng.randrange(2**data_width)


def _random_sel(prng, data_width):
    # Mostly full words, as a partial write has to keep the other bytes.
    nbytes = data_width//8
    return 2**nbytes - 1 if prng.randrange(4) else prng.randrange(2**nbytes)


def _idle(n=40):
    for _ in range(n):
        yield


class TestPortReorderFrontends(unittest.TestCase):
    def finish(self, dut, generators, stats, timeout=100000):
        run_simulation(dut, generators + [timeout_generator(timeout)])
        self.assertTrue(stats.get("done"), "traffic not completed")
        self.assertGreater(stats["reads"], 20)
        self.assertEqual(stats["errors"], 0)

    def words(self, data_width):
        return max(1, REGION_WORDS*CONTROLLER_WIDTH//data_width)

    # Native ---------------------------------------------------------------------------------------

    def native_traffic(self, dut, port, master, seed, nops, stats):
        # Bursts of consecutive addresses (gathered by an up-converter), reads checked in order.
        prng     = random.Random(seed)
        words    = self.words(port.data_width)
        shadow   = Shadow(port.data_width)
        expected = []

        def driver():
            yield from _idle()
            for _ in range(nops):
                we  = prng.randrange(2)
                adr = prng.randrange(words)
                n   = prng.choice([1, 1, 2, 4])
                for i in range(n):
                    data = _random_data(prng, port.data_width)
                    yield port.cmd.valid.eq(1)
                    yield port.cmd.we.eq(we)
                    yield port.cmd.addr.eq(adr + i)
                    yield port.cmd.last.eq(i == n - 1)
                    yield master.wr_data.eq(data)
                    yield
                    while not (yield port.cmd.ready):
                        yield
                    if we:
                        shadow.write(adr + i, data)
                    else:
                        expected.append(shadow.read(adr + i))
                yield port.cmd.valid.eq(0)
                for _ in range(prng.choice([0, 0, 0, 1, 3])):
                    yield
            stats["sent"] = True

        def checker():
            n = 0
            while not (stats.get("sent") and n == len(expected)):
                if (yield port.rdata.valid):
                    self.assertEqual((yield port.rdata.data), expected[n], f"read {n}")
                    n += 1
                yield
            stats["reads"] = n
            stats["done"]  = True

        return [driver(), checker()]

    def native_test(self, data_width, depth=16, nops=80):
        dut   = FrontendDUT(depth=depth)
        port  = dut.get_port(data_width=data_width)
        dut.submodules.master = Master(port)
        stats = {}
        generators = self.native_traffic(dut, port, dut.master, 0, nops, stats)
        generators.append(self.check_timings(dut, stats))
        self.finish(dut, generators, stats)

    def native_cdc_test(self, data_width, user_period):
        dut   = FrontendDUT()
        dut.clock_domains.cd_user = ClockDomain()
        port  = dut.get_port(data_width=data_width, clock_domain="user")
        dut.submodules.master = ClockDomainsRenamer("user")(Master(port))
        stats = {}
        generators = {
            "user" : self.native_traffic(dut, port, dut.master, 0, 80, stats),
            "sys"  : [self.check_timings(dut, stats), timeout_generator(100000)],
        }
        run_simulation(dut, generators, clocks={"sys": 10, "user": user_period})
        self.assertTrue(stats.get("done"), "traffic not completed")
        self.assertGreater(stats["reads"], 20)
        self.assertEqual(stats["errors"], 0)

    def check_timings(self, dut, stats):
        while not stats.get("done"):
            yield
        stats["errors"] = (yield dut.phy.timing_checker.errors)

    def test_native_32(self):  self.native_test(32)
    @full
    def test_native_64(self):  self.native_test(64)
    def test_native_256(self): self.native_test(256)
    @full
    def test_native_512(self): self.native_test(512)
    @full
    def test_native_32_depth_2(self):  self.native_test(32,  depth=2)
    @full
    def test_native_256_depth_2(self): self.native_test(256, depth=2)

    def test_native_cdc_128_slower(self): self.native_cdc_test(128, user_period=13)
    @full
    def test_native_cdc_128_faster(self): self.native_cdc_test(128, user_period=7)
    @full
    def test_native_cdc_128_much_slower(self): self.native_cdc_test(128, user_period=40)
    @full
    def test_native_cdc_32(self):         self.native_cdc_test(32,  user_period=13)
    @full
    def test_native_cdc_256(self):        self.native_cdc_test(256, user_period=13)

    # Wishbone (classic) ---------------------------------------------------------------------------

    def wishbone_test(self, data_width, port_width=None, nops=80):
        dut  = FrontendDUT()
        port = dut.get_port(data_width=port_width)
        wb   = wishbone.Interface(data_width=data_width, adr_width=30)
        dut.submodules.bridge = LiteDRAMWishbone2Native(wb, port)
        prng   = random.Random(0)
        words  = self.words(data_width)
        shadow = Shadow(data_width)
        stats  = {"reads": 0}

        def access(adr, we, data=0, sel=0, cti=0):
            yield wb.adr.eq(adr)
            yield wb.we.eq(we)
            yield wb.dat_w.eq(data)
            yield wb.sel.eq(sel if we else 2**(data_width//8) - 1)
            yield wb.cti.eq(cti)
            yield wb.cyc.eq(1)
            yield wb.stb.eq(1)
            yield
            while not (yield wb.ack):
                yield
            if not we:
                self.assertEqual((yield wb.dat_r), shadow.read(adr), f"read at {adr:#x}")
                stats["reads"] += 1

        def driver():
            yield from _idle()
            for _ in range(nops):
                # Incrementing bursts in the same cycle (merged by the burst up-converter) or singles.
                we  = prng.randrange(2)
                adr = prng.randrange(words)
                n   = prng.choice([1, 1, 2, 4])
                for i in range(n):
                    data = _random_data(prng, data_width)
                    sel  = _random_sel(prng, data_width)
                    cti  = wishbone.CTI_BURST_END if i == n - 1 else wishbone.CTI_BURST_INCREMENTING
                    yield from access(adr + i, we, data, sel, cti)
                    if we:
                        shadow.write(adr + i, data, sel)
                yield wb.stb.eq(0)
                yield wb.cyc.eq(0)
                for _ in range(prng.choice([0, 0, 1, 3])):
                    yield
            stats["done"] = True

        self.finish(dut, [driver(), self.check_timings(dut, stats)], stats)

    def test_wishbone_32(self):  self.wishbone_test(32)
    @full
    def test_wishbone_64(self):  self.wishbone_test(64)
    @full
    def test_wishbone_128(self): self.wishbone_test(128)
    def test_wishbone_256(self): self.wishbone_test(256)
    @full
    def test_wishbone_512(self): self.wishbone_test(512)
    # Same widths, converted by the crossbar port instead of the bridge.
    @full
    def test_wishbone_32_port_32(self):   self.wishbone_test(32,  port_width=32)
    @full
    def test_wishbone_64_port_64(self):   self.wishbone_test(64,  port_width=64)
    @full
    def test_wishbone_256_port_256(self): self.wishbone_test(256, port_width=256)

    # Wishbone (pipelined) -------------------------------------------------------------------------

    def wishbone_pipelined_test(self, data_width, nops=200):
        dut  = FrontendDUT()
        port = dut.get_port(data_width=data_width)
        wb   = wishbone.Interface(data_width=data_width, adr_width=30)
        dut.submodules.bridge = bridge = LiteDRAMWishbonePipelined2Native(wb, port)
        prng     = random.Random(0)
        words    = self.words(data_width)
        shadow   = Shadow(data_width)
        expected = []
        stats    = {}

        def driver():
            yield from _idle()
            yield wb.cyc.eq(1)
            for _ in range(nops):
                we   = prng.randrange(2)
                adr  = prng.randrange(words)
                data = _random_data(prng, data_width)
                sel  = _random_sel(prng, data_width)
                yield wb.stb.eq(1)
                yield wb.we.eq(we)
                yield wb.adr.eq(adr)
                yield wb.dat_w.eq(data)
                yield wb.sel.eq(sel)
                yield
                while (yield bridge.stall):
                    yield
                if we:
                    shadow.write(adr, data, sel)
                expected.append(None if we else shadow.read(adr))
                yield wb.stb.eq(0)
                if prng.randrange(4) == 0:
                    yield
            stats["sent"] = True

        def checker():
            n = reads = 0
            while not (stats.get("sent") and n == len(expected)):
                if (yield wb.ack):
                    if expected[n] is not None:
                        self.assertEqual((yield wb.dat_r), expected[n], f"transfer {n}")
                        reads += 1
                    n += 1
                yield
            stats["reads"] = reads
            stats["done"]  = True

        self.finish(dut, [driver(), checker(), self.check_timings(dut, stats)], stats)

    def test_wishbone_pipelined_32(self):  self.wishbone_pipelined_test(32)
    @full
    def test_wishbone_pipelined_128(self): self.wishbone_pipelined_test(128)
    @full
    def test_wishbone_pipelined_256(self): self.wishbone_pipelined_test(256)

    # Avalon ---------------------------------------------------------------------------------------

    def avalon_test(self, data_width, port_width=None, nops=60):
        dut  = FrontendDUT()
        port = dut.get_port(data_width=port_width)
        avl  = avalon.AvalonMMInterface(data_width=data_width, adr_width=30)
        dut.submodules.bridge = LiteDRAMAvalonMM2Native(avl, port)
        prng   = random.Random(0)
        words  = self.words(data_width)
        shadow = Shadow(data_width)
        stats  = {"reads": 0}

        def check(adr, value):
            self.assertEqual(value, shadow.read(adr), f"read at {adr:#x}")
            stats["reads"] += 1

        def driver():
            yield from _idle()
            for _ in range(nops):
                adr   = prng.randrange(words)
                kind  = prng.randrange(4)
                burst = prng.choice([2, 4, 8])
                if kind == 0:
                    data = _random_data(prng, data_width)
                    sel  = _random_sel(prng, data_width)
                    yield from avl.bus_write(adr, data, byteenable=sel)
                    shadow.write(adr, data, sel)
                elif kind == 1:
                    check(adr, (yield from avl.bus_read(adr)))
                elif kind == 2:
                    datas = [_random_data(prng, data_width) for _ in range(burst)]
                    yield from avl.bus_write(adr, datas)
                    for i, data in enumerate(datas):
                        shadow.write(adr + i, data)
                else:
                    check(adr, (yield from avl.bus_read(adr, burstcount=burst)))
                    for i in range(1, burst):
                        check(adr + i, (yield from avl.continue_read_burst()))
                    yield
                for _ in range(prng.choice([0, 0, 1, 3])):
                    yield
            stats["done"] = True

        self.finish(dut, [driver(), self.check_timings(dut, stats)], stats)

    def test_avalon_32(self):  self.avalon_test(32)
    @full
    def test_avalon_64(self):  self.avalon_test(64)
    @full
    def test_avalon_128(self): self.avalon_test(128)
    def test_avalon_256(self): self.avalon_test(256)
    @full
    def test_avalon_32_port_32(self):   self.avalon_test(32,  port_width=32)
    @full
    def test_avalon_256_port_256(self): self.avalon_test(256, port_width=256)

    # AXI ------------------------------------------------------------------------------------------

    def axi_test(self, data_width, depth=16, nbursts=15, **bridge_kwargs):
        # Phases of concurrent bursts, with reads and writes in distinct regions as AXI doesn't order
        # one against the other: writes are in order, and so are reads.
        dut  = FrontendDUT(depth=depth)
        port = dut.get_port(data_width=data_width)
        axi  = AXIInterface(data_width=data_width, address_width=32, id_width=4)
        dut.submodules.bridge = LiteDRAMAXI2Native(axi, port, **bridge_kwargs)
        prng   = random.Random(0)
        words  = self.words(data_width)
        nbytes = data_width//8
        shadow = Shadow(data_width)
        stats  = {}

        def bursts(region, we):
            r = []
            for _ in range(nbursts):
                offset = prng.randrange(words)
                n      = min(prng.choice([1, 1, 2, 4, 8]), words - offset)
                adr    = region*words + offset
                beats  = []
                for i in range(n):
                    if we:
                        data = _random_data(prng, data_width)
                        strb = _random_sel(prng, data_width)
                        beats.append((data, strb))
                        shadow.write(adr + i, data, strb)
                    else:
                        beats.append(shadow.read(adr + i))
                r.append((adr, prng.randrange(16), beats))
            return r

        # Expected data is computed here: a phase only reads what the previous phases have written.
        phases = [(bursts(0, True), [])]
        for w_region, r_region in [(1, 0), (0, 1), (1, 0)]:
            reads  = bursts(r_region, False)
            writes = bursts(w_region, True)
            phases.append((writes, reads))
        phases.append(([], bursts(0, False) + bursts(1, False)))

        nchannels = 5
        arrived   = [0]*len(phases)

        def barrier(phase):
            arrived[phase] += 1
            while arrived[phase] != nchannels:
                yield

        def ax_channel(ep, select):
            yield from _idle()
            for phase, plan in enumerate(phases):
                for adr, id, beats in select(plan):
                    while prng.randrange(4) == 0:
                        yield
                    yield ep.valid.eq(1)
                    yield ep.addr.eq(adr*nbytes)
                    yield ep.burst.eq(BURST_INCR)
                    yield ep.len.eq(len(beats) - 1)
                    yield ep.size.eq(log2_int(nbytes))
                    yield ep.id.eq(id)
                    yield
                    while not (yield ep.ready):
                        yield
                    yield ep.valid.eq(0)
                yield from barrier(phase)

        def w_channel():
            yield from _idle()
            for phase, (writes, _) in enumerate(phases):
                for _, _, beats in writes:
                    for i, (data, strb) in enumerate(beats):
                        while prng.randrange(4) == 0:
                            yield
                        yield axi.w.valid.eq(1)
                        yield axi.w.data.eq(data)
                        yield axi.w.strb.eq(strb)
                        yield axi.w.last.eq(i == len(beats) - 1)
                        yield
                        while not (yield axi.w.ready):
                            yield
                        yield axi.w.valid.eq(0)
                yield from barrier(phase)

        def b_channel():
            for phase, (writes, _) in enumerate(phases):
                for _, id, _ in writes:
                    yield axi.b.ready.eq(prng.randrange(4) != 0)
                    yield
                    while not ((yield axi.b.valid) and (yield axi.b.ready)):
                        yield axi.b.ready.eq(prng.randrange(4) != 0)
                        yield
                    self.assertEqual((yield axi.b.id), id)
                yield axi.b.ready.eq(0)
                yield from barrier(phase)

        def r_channel():
            n = 0
            for phase, (_, reads) in enumerate(phases):
                for _, id, beats in reads:
                    for i, value in enumerate(beats):
                        yield axi.r.ready.eq(prng.randrange(4) != 0)
                        yield
                        while not ((yield axi.r.valid) and (yield axi.r.ready)):
                            yield axi.r.ready.eq(prng.randrange(4) != 0)
                            yield
                        self.assertEqual((yield axi.r.data), value, f"phase {phase}, read beat {n}")
                        self.assertEqual((yield axi.r.id),   id)
                        self.assertEqual((yield axi.r.last), i == len(beats) - 1)
                        n += 1
                yield axi.r.ready.eq(0)
                yield from barrier(phase)
            stats["reads"] = n
            stats["done"]  = True

        self.finish(dut, [
            ax_channel(axi.aw, lambda plan: plan[0]),
            ax_channel(axi.ar, lambda plan: plan[1]),
            w_channel(), b_channel(), r_channel(),
            self.check_timings(dut, stats),
        ], stats)

    def test_axi_32(self):  self.axi_test(32)
    @full
    def test_axi_64(self):  self.axi_test(64)
    @full
    def test_axi_128(self): self.axi_test(128)
    def test_axi_256(self): self.axi_test(256)
    @full
    def test_axi_512(self): self.axi_test(512)
    @full
    def test_axi_128_depth_2(self): self.axi_test(128, depth=2)
    def test_axi_128_rmw(self):     self.axi_test(128, with_read_modify_write=True)
    @full
    def test_axi_32_rmw(self):      self.axi_test(32,  with_read_modify_write=True)
    @full
    def test_axi_64_rmw(self):      self.axi_test(64,  with_read_modify_write=True)


if __name__ == "__main__":
    unittest.main()
