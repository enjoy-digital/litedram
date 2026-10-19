#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Fabric-side native FIFO draining, with explicit lane ownership.

The EMPTY inputs must be native FIFO status in the supplied read-clock domain.
This module does not synchronize EMPTY or generate its clock.
"""

from operator import and_
from functools import reduce

from migen import If, Module, Mux, Signal


class NativeFIFORead(Module):
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
        if registered:
            sampled = Signal(len(layout.lanes))
            sampled_independent = Signal()
            pending = Signal(len(layout.lanes))
            mode = self.software_control & self.independent
            self.sync += sampled_independent.eq(mode)
            all_sampled = reduce(and_, sampled)
            for lane in layout.lanes:
                self.comb += pending[lane.index].eq(Mux(
                    sampled_independent, sampled[lane.index], all_sampled))
        for lane in layout.lanes:
            drain = self.lane_drain[lane.index]
            if registered:
                # Register each lane's availability before the cross-lane AND.
                # Sampling ownership with it reconstructs the same pending
                # vector even when software changes mode between cycles.
                # Never schedule a second read from stale EMPTY after a drain.
                self.sync += sampled[lane.index].eq(
                    self.ready & self.lane_available[lane.index] &
                    Mux(mode, ~pending[lane.index], pending == 0))
                self.comb += drain.eq(self.ready & pending[lane.index])
            else:
                self.comb += drain.eq(self.ready & Mux(
                    self.software_control & self.independent,
                    self.lane_available[lane.index], common))
            count = self.read_counts[lane.index]
            self.sync += If(self.clear, count.eq(0)).Elif(drain, count.eq(count + 1))
            for index in lane.dq + (lane.strobe,) + (() if lane.mask is None else (lane.mask,)):
                self.comb += self.read_enable[index].eq(drain)
