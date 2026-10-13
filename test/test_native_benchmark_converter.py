#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Exercise the benchmark through the production crossbar width adapters.

The byte scoreboard observes the wide ingress independently of the narrow
memory model. Neither model uses the converter's address/chunk expression.
These digital simulations do not establish electrical DDR calibration margin.
"""

import random
import unittest

from collections import deque

from migen import Module
from migen.sim import passive

from litedram.common import LiteDRAMNativePort
from litedram.frontend.adapter import LiteDRAMNativePortConverter
from litedram.frontend.native_benchmark import NativeDMABenchmark
from test.test_native_benchmark import simulate


class TestConvertedBenchmark(unittest.TestCase):
    def run_conversion(self, width, seed):
        rng = random.Random(seed)
        top = Module()
        wp = LiteDRAMNativePort("write", 12, width)
        rp = LiteDRAMNativePort("read", 12, width)
        mw = LiteDRAMNativePort("write", 13, 128)
        mr = LiteDRAMNativePort("read", 13, 128)
        top.submodules.write_converter = LiteDRAMNativePortConverter(wp, mw)
        top.submodules.read_converter = LiteDRAMNativePortConverter(rp, mr)
        top.submodules.benchmark = dut = NativeDMABenchmark(
            wp, rp, capacity=4096, fifo_depth=8, databits=16)
        memory = bytearray([0xa5] * 4096)
        expected = bytearray(memory)
        write_commands, read_commands, ingress_commands = deque(), deque(), deque()
        trace = deque(maxlen=16)
        counts = {"write": 0, "read": 0, "max_pending": 0}
        beat_bytes = width // 8

        @passive
        def model():
            cycle = 0
            # Separate channels have independent readiness and long stalls.
            while True:
                if (yield wp.cmd.valid) and (yield wp.cmd.ready):
                    ingress_commands.append((yield wp.cmd.addr) * beat_bytes)
                if (yield wp.wdata.valid) and (yield wp.wdata.ready):
                    self.assertTrue(ingress_commands, (seed, list(trace)))
                    address = ingress_commands.popleft()
                    value = (yield wp.wdata.data)
                    expected[address:address + beat_bytes] = value.to_bytes(beat_bytes, "little")
                if (yield mw.cmd.valid) and (yield mw.cmd.ready):
                    address = (yield mw.cmd.addr) * 16
                    write_commands.append(address)
                    counts["write"] += 1
                    trace.append((cycle, "write", address))
                if (yield mw.wdata.valid) and (yield mw.wdata.ready):
                    self.assertTrue(write_commands, (seed, list(trace)))
                    address = write_commands.popleft()
                    value = (yield mw.wdata.data).to_bytes(16, "little")
                    mask = (yield mw.wdata.we)
                    self.assertEqual(mask, 0xffff)
                    memory[address:address + 16] = value
                if (yield mr.cmd.valid) and (yield mr.cmd.ready):
                    address = (yield mr.cmd.addr) * 16
                    read_commands.append(address)
                    counts["read"] += 1
                    trace.append((cycle, "read", address))
                if (yield mr.rdata.valid) and (yield mr.rdata.ready):
                    read_commands.popleft()
                counts["max_pending"] = max(counts["max_pending"], len(read_commands))
                yield mw.cmd.ready.eq(rng.randrange(4) != 0 and cycle % 113 > 19)
                yield mw.wdata.ready.eq(bool(write_commands) and rng.randrange(3) != 0 and cycle % 137 > 31)
                yield mr.cmd.ready.eq(rng.randrange(3) != 0 and cycle % 97 > 11)
                # Keep an asserted response stable until the receiver accepts it.
                if not (yield mr.rdata.valid) or (yield mr.rdata.ready):
                    valid = bool(read_commands) and rng.randrange(3) != 0 and cycle % 149 > 39
                    yield mr.rdata.valid.eq(valid)
                    if valid:
                        address = read_commands[0]
                        yield mr.rdata.data.eq(int.from_bytes(memory[address:address + 16], "little"))
                cycle += 1
                yield

        def start(base, length, random_data=0, read_only=0):
            yield dut._base.storage.eq(base)
            yield dut._length.storage.eq(length)
            yield dut._random.storage.eq(random_data)
            yield dut._read_only.storage.eq(read_only)
            yield dut._start.re.eq(1)
            yield
            yield dut._start.re.eq(0)
            yield
            for _ in range(20000):
                if (yield dut._done.status):
                    return
                yield
            self.fail("Timeout: seed={} trace={}".format(seed, list(trace)))

        def main():
            yield dut.allowed.eq(1)
            # Reuse one live DUT across FIFO boundaries, patterns and start modes.
            for pattern in (0, 1):
                for beats in (1, 3, 7, 8, 9, 17, 33):
                    base = 0x2e0
                    length = beats * beat_bytes
                    before = dict(counts)
                    yield from start(base, length, pattern)
                    self.assertEqual((yield dut._fault.status), 0, (seed, list(trace)))
                    self.assertEqual((yield dut._errors.status), 0, (seed, list(trace)))
                    self.assertEqual((yield dut._write_beats.status), beats)
                    self.assertEqual((yield dut._read_beats.status), beats)
                    self.assertEqual(memory, expected)
                    self.assertEqual(counts["write"] - before["write"], length // 16)
                    self.assertEqual(counts["read"] - before["read"], length // 16)
                    self.assertFalse(write_commands)
                    self.assertFalse(read_commands)
                    yield from start(base, length, pattern, 1)
                    self.assertEqual((yield dut._errors.status), 0)
                    self.assertEqual((yield dut._write_beats.status), 0)
                    # Corrupt each physical half of the final wide beat separately.
                    for bit in (5, width - 7):
                        address = base + length - beat_bytes + bit // 8
                        memory[address] ^= 1 << (bit % 8)
                        yield from start(base, length, pattern, 1)
                        self.assertEqual((yield dut._errors.status), 1)
                        self.assertEqual((yield dut._first_error_offset.status), base + length - beat_bytes)
                        self.assertEqual((yield dut._first_error_xor.status), 1 << bit)
                        self.assertEqual((yield dut._dq_error_mask.status), 1 << (bit % 16))
                        memory[address] ^= 1 << (bit % 8)
            # Rejected partial requests must not leave split traffic behind.
            for base, length in ((1, beat_bytes), (64, beat_bytes - 1), (64, 0)):
                before = dict(counts)
                yield from start(base, length)
                self.assertEqual((yield dut._fault.status), 1)
                self.assertEqual(counts, before)
            yield from start(64, beat_bytes)
            self.assertEqual((yield dut._errors.status), 0)
            self.assertGreater(counts["max_pending"], 1)
            self.assertEqual(memory, expected)

        simulate(top, [main(), model()])

    def test_native128_control(self):
        self.run_conversion(128, 42)

    def test_converted256_stalls(self):
        for seed in (42, 123, 2026):
            with self.subTest(seed=seed):
                self.run_conversion(256, seed)

    def test_lost_admission_with_pending_split_is_fatal(self):
        # One accepted narrow command leaves its sibling in the converter.
        # A benchmark-only restart must not discard or reinterpret that traffic.
        top = Module()
        wp = LiteDRAMNativePort("write", 12, 256)
        rp = LiteDRAMNativePort("read", 12, 256)
        mw = LiteDRAMNativePort("write", 13, 128)
        mr = LiteDRAMNativePort("read", 13, 128)
        top.submodules.write_converter = LiteDRAMNativePortConverter(wp, mw)
        top.submodules.read_converter = LiteDRAMNativePortConverter(rp, mr)
        top.submodules.benchmark = dut = NativeDMABenchmark(wp, rp, capacity=4096, fifo_depth=8)

        def main():
            yield dut.allowed.eq(1)
            yield dut._base.storage.eq(64)
            yield dut._length.storage.eq(32)
            yield dut._start.re.eq(1)
            yield
            yield dut._start.re.eq(0)
            for _ in range(40):
                if (yield mw.cmd.valid):
                    break
                yield
            else:
                self.fail("No split command")
            self.assertEqual((yield mw.cmd.addr), 4)
            yield mw.cmd.ready.eq(1)
            yield
            yield mw.cmd.ready.eq(0)
            yield dut.allowed.eq(0)
            for _ in range(4):
                yield
            self.assertEqual((yield mw.cmd.addr), 5)
            self.assertEqual((yield mw.cmd.valid), 1)
            self.assertEqual((yield dut._fault.status), 4)
            self.assertEqual((yield dut._done.status), 1)
            yield dut.allowed.eq(1)
            yield dut._start.re.eq(1)
            yield
            yield dut._start.re.eq(0)
            for _ in range(8):
                yield
            self.assertEqual((yield dut._fault.status), 4)
            self.assertEqual((yield dut._busy.status), 0)
            self.assertEqual((yield mw.cmd.addr), 5)
            self.assertEqual((yield mw.cmd.valid), 1)

        simulate(top, main())
