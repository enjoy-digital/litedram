#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Registered drain scheduling against queues modeling native FIFO flags."""

import random
import unittest

from types import SimpleNamespace

from migen.sim import run_simulation
from litedram.phy.usnative.fifo import NativeFIFORead


def layout(width):
    lanes = width//8
    return SimpleNamespace(slices=tuple(range(width+2*lanes)), lanes=tuple(
        SimpleNamespace(index=i, dq=tuple(range(8*i, 8*i+8)), strobe=width+i,
                        mask=width+lanes+i) for i in range(lanes)))


class TestRegisteredFIFO(unittest.TestCase):
    def test_skew_backpressure_no_underflow_or_reordering(self):
        for width in (16, 32, 64):
            mapping = layout(width)
            dut = NativeFIFORead(mapping, registered=True)
            rng = random.Random(width)
            queues = [[] for _ in range(width)]
            supplied = [0]*width
            consumed = [0]*width
            prior_read = [False]
            def run():
                for cycle in range(800):
                    # A synchronized word stream with independently late DQ bits.
                    for bit in range(width):
                        if supplied[bit]<cycle//3 and rng.randrange(4):
                            queues[bit].append(supplied[bit])
                            supplied[bit]+=1
                    empty = sum((not queues[bit])<<bit for bit in range(width))
                    ready = cycle%113 not in (50, 51, 52)
                    yield dut.empty.eq(empty)
                    yield dut.ready.eq(ready)
                    yield
                    mask = (yield dut.read_enable)
                    if not ready:
                        self.assertEqual(mask, 0)
                    self.assertIn(mask, (0, (1<<len(mapping.slices))-1))
                    if mask:
                        self.assertFalse(prior_read[0])
                        for bit in range(width):
                            self.assertTrue(queues[bit], (width, cycle, bit))
                            self.assertEqual(queues[bit].pop(0), consumed[bit])
                            consumed[bit]+=1
                    prior_read[0] = bool(mask)
                self.assertGreater(min(consumed), 100)
                self.assertEqual(len(set(consumed)), 1)
            run_simulation(dut, run())

    def test_added_latency_and_rate_limit(self):
        dut = NativeFIFORead(layout(64), registered=True)
        def run():
            yield dut.ready.eq(1)
            yield dut.empty.eq(0)
            samples = []
            for _ in range(10):
                yield
                samples.append((yield dut.lane_drain))
            self.assertEqual(samples, [0, 255, 0, 255, 0, 255, 0, 255, 0, 255])
            # Diagnostic clear must not disturb the drain schedule.
            yield dut.clear.eq(1)
            yield
            self.assertEqual((yield dut.read_enable), 0)
            yield
            self.assertEqual((yield dut.lane_drain), 255)
            for count in dut.read_counts:
                self.assertEqual((yield count), 0)
            yield dut.ready.eq(0)
            yield
            self.assertEqual((yield dut.read_enable), 0)
        run_simulation(dut, run())

    def test_independent_lanes_require_software_ownership(self):
        dut = NativeFIFORead(layout(64), registered=True)
        def run():
            yield dut.ready.eq(1)
            yield dut.independent.eq(1)
            yield dut.empty.eq(1<<63)
            for _ in range(4):
                yield
                self.assertEqual((yield dut.lane_drain), 0)
            yield dut.software_control.eq(1)
            seen = []
            for _ in range(8):
                yield
                seen.append((yield dut.lane_drain))
            self.assertIn(127, seen)
            self.assertTrue(all(value in (0, 127) for value in seen))
        run_simulation(dut, run())
