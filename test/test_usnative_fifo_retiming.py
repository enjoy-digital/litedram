#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Cycle equivalence against the original drain scheduler, including mode changes."""
import random
import unittest
from types import SimpleNamespace
from migen import Module, ResetInserter
from migen.sim import run_simulation
from litedram.phy.usnative.fifo import NativeFIFORead


# Frozen pre-retiming implementation; independent reference for cycle behavior.
from functools import reduce
from operator import and_

from migen import If, Module, Mux, Signal


class Reference(Module):
    def __init__(self, layout, *, registered=False):
        """Optionally register drains, with an idle cycle to avoid stale EMPTY.

        Registered mode adds one read-clock cycle and caps drain throughput at
        one word per two cycles. The caller must enforce that arrival limit,
        account for latency, and qualify the native FIFO status timing.
        """
        self.empty = Signal(len(layout.slices), reset=(1 << len(layout.slices)) - 1)
        self.ready = Signal()
        self.software_control = Signal()
        self.independent = Signal()
        self.clear = Signal()
        self.read_enable = Signal(len(layout.slices))
        self.lane_available = Signal(len(layout.lanes))
        self.lane_drain = Signal(len(layout.lanes))
        self.read_counts = [Signal(32) for _ in layout.lanes]
        for lane in layout.lanes:
            self.comb += self.lane_available[lane.index].eq(
                reduce(and_, (~self.empty[bit] for bit in lane.dq)))
        common = reduce(and_, self.lane_available)
        pending = Signal(len(layout.lanes))
        for lane in layout.lanes:
            drain = self.lane_drain[lane.index]
            if registered:
                # EMPTY was sampled before the previous edge. Never schedule
                # a second read from that stale sample after consuming a word.
                available = Mux(self.software_control & self.independent,
                    self.lane_available[lane.index] & ~pending[lane.index],
                    common & (pending == 0))
                self.sync += pending[lane.index].eq(self.ready & available)
                self.comb += drain.eq(self.ready & pending[lane.index])
            else:
                self.comb += drain.eq(self.ready & Mux(
                    self.software_control & self.independent,
                    self.lane_available[lane.index], common))
            count = self.read_counts[lane.index]
            self.sync += If(self.clear, count.eq(0)).Elif(drain, count.eq(count + 1))
            for index in lane.dq + (lane.strobe,) + (() if lane.mask is None else (lane.mask,)):
                self.comb += self.read_enable[index].eq(drain)


class TestRetimedFIFORead(unittest.TestCase):
    def test_cycle_equivalence_all_modes_empty_ready_clear_reset(self):
        for lanes, registered in ((n, r) for n in (1, 2, 8) for r in (False, True)):
            with self.subTest(lanes=lanes, registered=registered):
                layout = SimpleNamespace(slices=range(lanes*10), lanes=[
                    SimpleNamespace(index=i, dq=tuple(range(i*10, i*10+8)),
                                    strobe=i*10+8, mask=i*10+9) for i in range(lanes)])
                top = Module()
                top.submodules.a = a = ResetInserter()(Reference(layout, registered=registered))
                top.submodules.b = b = ResetInserter()(NativeFIFORead(layout, registered=registered))
                def sim():
                    rng = random.Random(8320+lanes)
                    for cycle in range(1600):
                        # Long all-ready runs exercise full two-cycle drain
                        # throughput; partial lane arrivals stress common mode.
                        empty = 0 if cycle < 100 else sum(
                            (rng.randrange(3)==0) << bit for bit in range(lanes*10))
                        ready = 1 if cycle < 100 else rng.randrange(7)!=0
                        mode = 0 if cycle < 100 else rng.randrange(2)
                        software = 1 if cycle < 100 else rng.randrange(2)
                        for dut in (a, b):
                            yield dut.empty.eq(empty)
                            yield dut.ready.eq(ready)
                            yield dut.independent.eq(mode)
                            yield dut.software_control.eq(software)
                            yield dut.clear.eq(cycle % 137 == 0)
                            yield dut.reset.eq(cycle in (33, 518))
                        yield
                        for x, y in ((a.read_enable, b.read_enable),
                                    (a.lane_available, b.lane_available),
                                    (a.lane_drain, b.lane_drain)):
                            self.assertEqual((yield x), (yield y), (lanes, cycle))
                        for x, y in zip(a.read_counts, b.read_counts):
                            self.assertEqual((yield x), (yield y), (lanes, cycle))
                run_simulation(top, sim())


if __name__ == '__main__':
    unittest.main()
