#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import unittest
from migen import *
from litedram.common import LiteDRAMNativePort
from litedram.frontend.paired import PairedPort
from litedram.frontend.native_benchmark import NativeDMABenchmark
from test.test_native_benchmark import simulate
from test.common import DRAMMemory


class WideTest(unittest.TestCase):
    def test_paired_counter_and_prbs(self):
        for random in (0, 1):
            with self.subTest(random=random):
                top = Module()
                wp = [LiteDRAMNativePort('write', 10, 128) for _ in range(2)]
                rp = [LiteDRAMNativePort('read', 10, 128) for _ in range(2)]
                top.submodules.w = w = PairedPort(wp, 'write', depth=8)
                top.submodules.r = r = PairedPort(rp, 'read', depth=8)
                top.submodules.dma = dma = NativeDMABenchmark(w.port, r.port, capacity=16384,
                                                              fifo_depth=8, drained=w.drained, databits=16)
                memory = [DRAMMemory(128, 1024) for _ in range(2)]

                def main():
                    yield dma.allowed.eq(1)
                    yield dma._base.storage.eq(32)
                    yield dma._length.storage.eq(4096)
                    yield dma._random.storage.eq(random)
                    for trial, readonly in enumerate((0, 1, 1, 1, 0)):
                        if trial == 2:
                            memory[1].mem[257] ^= 1 << 127
                        if trial == 3:
                            memory[0].mem[2] ^= 1
                        expected_errors = 1 if trial == 2 else (2 if trial == 3 else 0)
                        yield dma._read_only.storage.eq(readonly)
                        yield dma._start.re.eq(1)
                        yield
                        yield dma._start.re.eq(0)
                        yield
                        for _ in range(20000):
                            if (yield dma._done.status):
                                break
                            yield
                        self.assertEqual((yield dma._done.status), 1)
                        self.assertEqual((yield dma._fault.status), 0)
                        self.assertEqual((yield dma._errors.status), expected_errors)
                        self.assertEqual((yield dma._read_beats.status), 128)
                        self.assertEqual((yield dma._write_beats.status), 0 if readonly else 128)
                        self.assertEqual((yield w.drained), 1)
                        self.assertEqual((yield r.error), 0)
                        self.assertEqual((yield dma._dq_error_mask.status), 0x8000 if trial == 2 else (0x8001 if trial == 3 else 0))
                        if expected_errors:
                            self.assertEqual((yield dma._first_error_offset.status), 4096 if trial == 2 else 32)
                            self.assertEqual((yield dma._first_error_xor.status), 1 << 255 if trial == 2 else 1)
                    if not random:
                        for index in range(127):
                            expected = sum(index << (31*k) for k in range(9)) & ((1 << 256)-1)
                            self.assertEqual(memory[0].mem[2*(index+1)], expected & ((1 << 128)-1))
                            self.assertEqual(memory[1].mem[2*(index+1)+1], expected >> 128)
                simulate(top, [main(),
                               memory[0].write_handler(wp[0], wdata_ready_random=60),
                               memory[1].write_handler(wp[1], wdata_ready_random=15),
                               memory[0].read_handler(rp[0], rdata_valid_random=10),
                               memory[1].read_handler(rp[1], rdata_valid_random=65)])

    def test_group_spacing_and_full_rate(self):
        import test.test_multiplexer as tm
        top = tm.MultiplexerDUT(
            controller_settings=dict(with_bank_group_interleaving=True),
            phy_settings=dict(memtype='DDR4', nphases=4, rdphase=0, wrphase=2),
            timing_settings=dict(tCCD=2))
        accepted = []

        def main():
            for bank in (0, 1, 4, 5):
                cmd = top.bank_machines[bank].cmd
                yield cmd.valid.eq(1)
                yield cmd.is_read.eq(1)
                yield cmd.cas.eq(1)
                yield cmd.ba.eq(bank)
            last_group = {}
            last_any = -10
            for cycle in range(180):
                for bank in (0, 1, 4, 5):
                    cmd = top.bank_machines[bank].cmd
                    if (yield cmd.valid) and (yield cmd.ready):
                        group = bank >> 2
                        self.assertGreaterEqual(cycle-last_group.get(group, -10), 2)
                        self.assertGreaterEqual(cycle-last_any, 1)
                        last_group[group] = last_any = cycle
                        if cycle > 20:
                            accepted.append(cycle)
                yield
            self.assertGreater(len(accepted), 150)
        simulate(top, main())

    def test_address_mapping_bijection(self):
        # Independent integer model: adjacent halves select opposite BGs.
        addresses = set()
        for word in range(1 << 14):
            bank = ((word >> 8) & 3) | ((word & 1) << 2)
            row_col = ((word >> 1) & 127) | ((word >> 10) << 7)
            physical = (row_col & 127) | (bank << 7) | ((row_col >> 7) << 10)
            self.assertNotIn(physical, addresses)
            addresses.add(physical)
            self.assertEqual(bank >> 2, word & 1)


class PairedContractTest(unittest.TestCase):
    def test_benchmark_write_cycles_include_child_queue_drain(self):
        ports = [LiteDRAMNativePort("write", 10, 128) for _ in range(2)]
        top = Module()
        top.submodules.paired = paired = PairedPort(ports, "write", depth=4)
        read_port = LiteDRAMNativePort("read", 9, 256)
        top.submodules.benchmark = benchmark = NativeDMABenchmark(
            paired.port, read_port, capacity=16384, drained=paired.drained, databits=16)

        def main():
            yield benchmark.allowed.eq(1)
            yield benchmark._base.storage.eq(0)
            yield benchmark._length.storage.eq(32)
            yield benchmark._start.re.eq(1)
            yield
            yield benchmark._start.re.eq(0)
            # Drain child data, but deliberately hold their queued commands.
            for port in ports:
                yield port.wdata.ready.eq(1)
            for _ in range(40):
                yield
            self.assertEqual((yield benchmark._write_beats.status), 1)
            self.assertGreater((yield benchmark._write_cycles.status), 30)
            self.assertEqual((yield benchmark._read_cycles.status), 0)
            self.assertEqual((yield paired.drained), 0)
            for port in ports:
                yield port.cmd.ready.eq(1)
            for _ in range(160):
                yield
            self.assertEqual((yield paired.drained), 1)
            self.assertGreater((yield benchmark._read_cycles.status), 0)
            self.assertGreater((yield benchmark._write_cycles.status), 30)

        simulate(top, main())

    def test_full_mask_and_write_drain(self):
        ports = [LiteDRAMNativePort("write", 10, 128) for _ in range(2)]
        dut = PairedPort(ports, "write", depth=4)

        def main():
            yield dut.port.cmd.addr.eq(3)
            yield dut.port.cmd.valid.eq(1)
            yield
            while not (yield dut.port.cmd.ready):
                yield
            yield
            yield dut.port.cmd.valid.eq(0)
            yield dut.port.wdata.data.eq(0x1234)
            yield dut.port.wdata.we.eq(0xffffffff)
            yield dut.port.wdata.valid.eq(1)
            yield
            while not (yield dut.port.wdata.ready):
                yield
            yield
            yield dut.port.wdata.valid.eq(0)
            for _ in range(6):
                yield
            self.assertEqual((yield dut.error), 0)
            self.assertEqual((yield dut.drained), 0)
            # Data can drain before its corresponding queued command. Both
            # queues must be empty before the benchmark stops its write timer.
            for port in ports:
                yield port.wdata.ready.eq(1)
            for _ in range(6):
                yield
            self.assertEqual((yield dut.drained), 0)
            for port in ports:
                yield port.cmd.ready.eq(1)
            for _ in range(8):
                yield
            self.assertEqual((yield dut.drained), 1)
            self.assertEqual((yield dut.error), 0)

        simulate(dut, main())

    def test_read_credits_backpressure_and_unsolicited_response(self):
        ports = [LiteDRAMNativePort("read", 10, 128) for _ in range(2)]
        dut = PairedPort(ports, "read", depth=2)

        def main():
            for port in ports:
                yield port.cmd.ready.eq(1)
            for address in (5, 6):
                yield dut.port.cmd.addr.eq(address)
                yield dut.port.cmd.valid.eq(1)
                yield
                self.assertEqual((yield dut.port.cmd.ready), 1)
                yield dut.port.cmd.valid.eq(0)
                yield
            yield dut.port.cmd.addr.eq(7)
            yield dut.port.cmd.valid.eq(1)
            yield
            self.assertEqual((yield dut.port.cmd.ready), 0)
            self.assertEqual((yield dut.drained), 0)
            yield dut.port.cmd.valid.eq(0)
            # Both reserved responses can return while upstream is stalled.
            for value in (0x11, 0x22):
                for group, port in enumerate(ports):
                    yield port.rdata.valid.eq(1)
                    yield port.rdata.data.eq(value + group)
                yield
            for port in ports:
                yield port.rdata.valid.eq(0)
            for _ in range(5):
                yield
            self.assertEqual((yield dut.error), 0)
            self.assertEqual((yield dut.drained), 0)
            self.assertEqual((yield dut.port.rdata.data), 0x11 | (0x12 << 128))
            yield dut.port.rdata.ready.eq(1)
            for _ in range(6):
                yield
            self.assertEqual((yield dut.drained), 1)
            # Returning data without a reservation is detected immediately,
            # rather than waiting for a later FIFO overflow.
            yield ports[0].rdata.valid.eq(1)
            yield
            yield ports[0].rdata.valid.eq(0)
            yield
            self.assertEqual((yield dut.error), 1)

        simulate(dut, main())

    def test_registered_refresh_timer_cycle_equivalence(self):
        from litedram.core.refresher import RefreshTimer
        for interval in (1, 2, 3, 19):
            with self.subTest(interval=interval):
                top = Module()
                top.submodules.reference = reference = RefreshTimer(interval)
                top.submodules.registered = registered = RefreshTimer(interval, registered=True)

                def main():
                    for cycle in range(120):
                        wait = (cycle % 13) not in (0, 1, 7)
                        yield reference.wait.eq(wait)
                        yield registered.wait.eq(wait)
                        yield
                        self.assertEqual((yield reference.done), (yield registered.done))
                        self.assertEqual((yield reference.count), (yield registered.count))

                simulate(top, main())
