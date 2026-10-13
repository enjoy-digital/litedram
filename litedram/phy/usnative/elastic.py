#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Fabric-side lane buffering for ordered, full-word native read assembly."""

from operator import and_
from functools import reduce
from migen import Cat, Module, ResetInserter, Signal
from migen.genlib.fifo import SyncFIFOBuffered


class NativeReadAssembler(Module):
    """Join independent, ordered byte-lane streams with bounded buffering.

    Each accepted lane item is eight DDR samples of one byte (64 bits).
    Input items must already have native FIFO read latency and bitslip applied.
    ``lane_ready`` is a fabric handshake, NOT permission to read a native FIFO:
    an adapter must reserve capacity for every outstanding native read first.
    All lanes must share a transaction sequence. Reset/flush must also cancel
    outstanding native reads; late responses must not enter the next epoch.
    This does not provide the fixed-latency DFI read-valid contract by itself.
    """
    def __init__(self, lanes, *, depth=4):
        if type(lanes) is not int or lanes not in (2, 4, 8):
            raise ValueError('Expected 2, 4 or 8 byte lanes')
        if type(depth) is not int or depth < 2:
            raise ValueError('At least two FIFO entries required')
        self.flush = Signal()
        self.lane_valid = Signal(lanes)
        self.lane_ready = Signal(lanes)
        self.lane_data = [Signal(64) for _ in range(lanes)]
        self.valid = Signal()
        self.ready = Signal()
        self.data = Signal(lanes*64)
        self.level = []
        fifos = []
        for lane in range(lanes):
            fifo = ResetInserter()(SyncFIFOBuffered(64, depth))
            self.submodules += fifo
            fifos.append(fifo)
            self.level.append(fifo.level)
            self.comb += [
                fifo.reset.eq(self.flush), fifo.din.eq(self.lane_data[lane]),
                self.lane_ready[lane].eq(fifo.writable & ~self.flush),
                fifo.we.eq(self.lane_valid[lane] & self.lane_ready[lane]),
                fifo.re.eq(self.valid & self.ready),
            ]
        # All lane FIFOs advance together when the assembled word is accepted,
        # preserving byte-lane correspondence under downstream backpressure.
        self.comb += [
            self.valid.eq(reduce(and_, (fifo.readable for fifo in fifos)) & ~self.flush),
            self.data.eq(Cat(*(fifo.dout for fifo in fifos))),
        ]
