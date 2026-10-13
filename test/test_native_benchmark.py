#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import sys
import unittest
from migen import Module, Memory, Signal
from migen.sim import run_simulation
from litedram.common import LiteDRAMNativePort
from litex.soc.interconnect import stream
from test.common import DRAMMemory
from litedram.frontend.native_benchmark import NativeDMABenchmark

def simulate(dut, generators):
    fragment = dut.get_fragment()
    # The pinned simulator's MemoryToArray assumes every port has dat_r,
    # whereas the current buffered FIFO creates write-only memory ports.
    # Add unused read wires only to the simulation fragment; RTL is unchanged.
    for special in fragment.specials:
        if isinstance(special, Memory):
            for port in special.ports:
                if port.dat_r is None:
                    port.dat_r = Signal(special.width)
    run_simulation(fragment, generators)

class DMATest(unittest.TestCase):
    def test_one_beat_per_cycle_with_outstanding_reads(self):
        wp = LiteDRAMNativePort('write', 10, 128)
        rp = LiteDRAMNativePort('read', 10, 128)
        top = Module()
        top.submodules.dut = dut = NativeDMABenchmark(wp, rp, capacity=16384)
        memory = Memory(128, 1024)
        wr = memory.get_port(write_capable=True)
        rd = memory.get_port(async_read=True)
        top.specials += memory, wr, rd
        top.submodules.addresses = addresses = stream.SyncFIFO([('address', 10)], 64)
        top.comb += [addresses.sink.valid.eq(wp.cmd.valid), addresses.sink.address.eq(wp.cmd.addr),
            wp.cmd.ready.eq(addresses.sink.ready), wp.wdata.ready.eq(addresses.source.valid),
            addresses.source.ready.eq(wp.wdata.valid), wr.adr.eq(addresses.source.address),
            wr.dat_w.eq(wp.wdata.data), wr.we.eq(wp.wdata.valid & wp.wdata.ready),
            rp.cmd.ready.eq(1), rd.adr.eq(rp.cmd.addr)]
        pipeline = [Signal(128) for _ in range(16)]
        valid = [Signal() for _ in range(16)]
        top.sync += [pipeline[0].eq(rd.dat_r), valid[0].eq(rp.cmd.valid & rp.cmd.ready)]
        for i in range(1, 16):
            top.sync += [pipeline[i].eq(pipeline[i-1]), valid[i].eq(valid[i-1])]
        top.comb += [rp.rdata.data.eq(pipeline[-1]), rp.rdata.valid.eq(valid[-1])]
        def main():
            yield dut.allowed.eq(1)
            yield dut._base.storage.eq(0)
            yield dut._length.storage.eq(4096)
            yield dut._start.re.eq(1)
            yield
            yield dut._start.re.eq(0)
            for _ in range(2000):
                if (yield dut._done.status):
                    break
                yield
            self.assertEqual((yield dut._done.status), 1)
            self.assertEqual((yield dut._fault.status), 0)
            self.assertEqual((yield dut._errors.status), 0)
            self.assertEqual((yield dut._write_beats.status), 256)
            self.assertEqual((yield dut._read_beats.status), 256)
            self.assertLessEqual((yield dut._write_cycles.status), 264)
            self.assertLessEqual((yield dut._read_cycles.status), 280)
        simulate(top, main())

    def run_case(self, random_data=1, corrupt=False, width=128):
        beat_bytes = width//8
        beats = 1024//beat_bytes
        first = 64//beat_bytes
        last = first+beats-1
        wp = LiteDRAMNativePort('write', address_width=10, data_width=width)
        rp = LiteDRAMNativePort('read', address_width=10, data_width=width)
        dut = NativeDMABenchmark(wp, rp, capacity=16384, fifo_depth=8, databits=16)
        memory = DRAMMemory(width, 1024)
        def start(read_only=0):
            yield dut._read_only.storage.eq(read_only)
            yield dut._start.re.eq(1)
            yield
            yield dut._start.re.eq(0)
            yield
        def wait():
            for _ in range(10000):
                if (yield dut._done.status):
                    return
                yield
            self.fail('DMA did not finish')
        def main():
            yield dut.allowed.eq(1)
            yield dut._base.storage.eq(64)
            yield dut._length.storage.eq(1024)
            yield dut._random.storage.eq(random_data)
            yield from start()
            yield from wait()
            self.assertEqual((yield dut._fault.status), 0)
            self.assertEqual((yield dut._errors.status), 0)
            self.assertEqual((yield dut._write_beats.status), beats)
            self.assertEqual((yield dut._read_beats.status), beats)
            self.assertGreaterEqual((yield dut._write_cycles.status), beats)
            self.assertGreaterEqual((yield dut._read_cycles.status), beats)
            self.assertEqual(memory.mem[:first], [0]*first)
            self.assertEqual(memory.mem[last+1:], [0]*(1024-last-1))
            if corrupt:
                memory.mem[last]^=1<<100  # final beat must also be checked
            yield from start(1)
            yield from wait()
            self.assertEqual((yield dut._fault.status), 0)
            self.assertEqual((yield dut._write_beats.status), 0)
            self.assertEqual((yield dut._read_beats.status), beats)
            self.assertEqual((yield dut._errors.status), int(corrupt))
            if corrupt:
                self.assertEqual((yield dut._first_error_offset.status), last*beat_bytes)
                self.assertEqual((yield dut._first_error_xor.status), 1<<100)
                self.assertEqual((yield dut._dq_error_mask.status), 1<<(100%16))
            # An invalid request must issue no commands and allow a later valid run.
            yield dut._length.storage.eq(0)
            yield from start()
            yield from wait()
            self.assertEqual((yield dut._fault.status), 1)
            self.assertEqual((yield dut._write_beats.status), 0)
            yield dut._length.storage.eq(beat_bytes)
            yield from start()
            yield from wait()
            self.assertEqual((yield dut._fault.status), 0)
            self.assertEqual((yield dut._errors.status), 0)
            self.assertEqual((yield dut._read_beats.status), 1)
        simulate(dut, [main(), memory.write_handler(wp, wdata_ready_random=60),
                            memory.read_handler(rp, rdata_valid_random=60)])
    def test_counter_backpressure(self):
        self.run_case(0)
    def test_prbs_backpressure_and_corruption(self):
        self.run_case(1, True)
    def test_256_bit_counter(self):
        self.run_case(0, width=256)
    def test_256_bit_prbs_corruption(self):
        self.run_case(1, True, width=256)
    def test_reject_and_timeout(self):
        wp = LiteDRAMNativePort('write', 10, 128)
        rp = LiteDRAMNativePort('read', 10, 128)
        dut = NativeDMABenchmark(wp, rp, capacity=16384)
        def start():
            yield dut._start.re.eq(1)
            yield
            yield dut._start.re.eq(0)
            for _ in range(4):
                yield
        def main():
            yield dut._base.storage.eq(0)
            yield dut._length.storage.eq(16)
            yield from start()
            self.assertEqual((yield dut._fault.status), 2)
            yield dut.allowed.eq(1)
            yield dut._base.storage.eq(16384)
            yield from start()
            self.assertEqual((yield dut._fault.status), 1)
            yield dut._base.storage.eq(1)
            yield from start()
            self.assertEqual((yield dut._fault.status), 1)
            yield dut._base.storage.eq(0xfffffff0)
            yield dut._length.storage.eq(32)
            yield from start()
            self.assertEqual((yield dut._fault.status), 1)
            yield dut._length.storage.eq(16)
            yield dut._base.storage.eq(0)
            yield dut._timeout.storage.eq(16)
            yield from start()
            for _ in range(32):
                yield
            self.assertEqual((yield dut._fault.status), 3)
            self.assertEqual((yield dut._done.status), 1)
            self.assertEqual((yield dut._busy.status), 0)
            yield from start()
            self.assertEqual((yield dut._fault.status), 3)
        simulate(dut, main())

    def test_lost_readiness_is_fatal_and_cannot_restart(self):
        wp = LiteDRAMNativePort('write', 10, 128)
        rp = LiteDRAMNativePort('read', 10, 128)
        dut = NativeDMABenchmark(wp, rp, capacity=16384)
        def main():
            yield dut.allowed.eq(1)
            yield dut._base.storage.eq(0)
            yield dut._length.storage.eq(4096)
            yield dut._start.re.eq(1)
            yield
            yield dut._start.re.eq(0)
            for _ in range(10):
                yield
            self.assertEqual((yield dut._busy.status), 1)
            yield dut.allowed.eq(0)
            for _ in range(5):
                yield
            self.assertEqual((yield dut._fault.status), 4)
            self.assertEqual((yield dut._done.status), 1)
            self.assertEqual((yield dut._busy.status), 0)
            yield dut.allowed.eq(1)
            yield dut._start.re.eq(1)
            yield
            yield dut._start.re.eq(0)
            for _ in range(5):
                yield
            self.assertEqual((yield dut._fault.status), 4)
            self.assertEqual((yield dut._busy.status), 0)
        simulate(dut, main())

if __name__=='__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DMATest)
    sys.exit(not unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite).wasSuccessful())
