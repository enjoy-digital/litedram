#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Ordered lane assembly, backpressure and flush behavior with bounded FIFOs."""

import random
import unittest
from migen import Memory, Signal
from migen.sim import run_simulation
from litedram.phy.usnative.elastic import NativeReadAssembler


def simulate(dut, process):
    # This checkout's Migen FIFO creates write-only RAM ports, while its
    # simulator still expects dat_r on every port. Supply an unused read sink;
    # the FIFO memory, write enables and real synchronous read port are intact.
    fragment = dut.get_fragment()
    for special in fragment.specials:
        if isinstance(special, Memory):
            for port in special.ports:
                if port.dat_r is None:
                    port.dat_r = Signal(special.width)
    run_simulation(fragment, process)


class TestNativeReadAssembler(unittest.TestCase):
    def test_skew_backpressure_and_full_rate(self):
        for lanes in (2, 4, 8):
            dut = NativeReadAssembler(lanes, depth=4)
            rng = random.Random(lanes)
            def process():
                sent = [0]*lanes
                received = 0
                consecutive = 0
                longest = 0
                for cycle in range(1600):
                    # First stress skew/backpressure, then demand full-rate flow.
                    full = cycle>=800
                    mask = sum(int(full or rng.randrange(4)!=0)<<i for i in range(lanes))
                    yield dut.lane_valid.eq(mask)
                    for i in range(lanes):
                        yield dut.lane_data[i].eq((sent[i]<<8)|i)
                    consume = full or rng.randrange(3)!=0
                    yield dut.ready.eq(consume)
                    yield
                    accepted = (yield dut.lane_ready)&mask
                    for i in range(lanes):
                        if accepted>>i&1:
                            sent[i]+=1
                    if (yield dut.valid) and consume:
                        value = (yield dut.data)
                        for i in range(lanes):
                            self.assertEqual((value>>(64*i))&((1<<64)-1), (received<<8)|i)
                        received+=1
                        consecutive+=1
                        longest = max(longest, consecutive)
                    else:
                        consecutive = 0
                self.assertGreater(received, 900)
                self.assertGreater(longest, 500)
            simulate(dut, process())

    def test_flush_blocks_handshakes_and_discards_partial_words(self):
        dut = NativeReadAssembler(8)
        def process():
            yield dut.lane_valid.eq(127)
            for i in range(8):
                yield dut.lane_data[i].eq(123+i)
            for _ in range(12):
                yield
            self.assertEqual((yield dut.valid), 0)
            self.assertEqual((yield dut.lane_ready)&127, 0)
            yield dut.flush.eq(1)
            yield dut.lane_valid.eq(255)
            yield dut.ready.eq(1)
            yield
            self.assertEqual((yield dut.valid), 0)
            self.assertEqual((yield dut.lane_ready), 0)
            yield
            yield dut.lane_valid.eq(0)
            yield dut.flush.eq(0)
            for _ in range(4):
                yield
            self.assertEqual((yield dut.valid), 0)
            self.assertEqual((yield dut.lane_ready), 255)
            for level in dut.level:
                self.assertEqual((yield level), 0)
        simulate(dut, process())
