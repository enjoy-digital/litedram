# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
# License: BSD

import unittest
import random

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMNativeWritePort
from litedram.common import LiteDRAMNativeReadPort
from litedram.frontend.fifo import LiteDRAMFIFO, _LiteDRAMFIFOCtrl
from litedram.frontend.fifo import _LiteDRAMFIFOWriter, _LiteDRAMFIFOReader

from test.common import *

class TestFIFO(unittest.TestCase):
    @passive
    def fifo_ctrl_flag_checker(self, fifo_ctrl, write_threshold, read_threshold):
        # Checks the combinational logic
        while True:
            level = (yield fifo_ctrl.level)
            self.assertEqual((yield fifo_ctrl.writable), level < write_threshold)
            self.assertEqual((yield fifo_ctrl.readable), level > read_threshold)
            yield

    # _LiteDRAMFIFOCtrl ----------------------------------------------------------------------------

    def test_fifo_ctrl_address_changes(self):
        # Verify FIFOCtrl address changes.
        # We are ignoring thresholds (so readable/writable signals)
        dut = _LiteDRAMFIFOCtrl(base=0, depth=16, read_threshold=0, write_threshold=16)

        def main_generator():
            self.assertEqual((yield dut.write_address), 0)
            self.assertEqual((yield dut.read_address), 0)

            # Write address
            yield dut.write.eq(1)
            yield
            # Write_address gets updated 1 cycle later
            for i in range(24 - 1):
                self.assertEqual((yield dut.write_address), i % 16)
                yield
            yield dut.write.eq(0)
            yield
            self.assertEqual((yield dut.write_address), 24 % 16)

            # Read address
            yield dut.read.eq(1)
            yield
            for i in range(24 - 1):
                self.assertEqual((yield dut.read_address), i % 16)
                yield
            yield dut.read.eq(0)
            yield
            self.assertEqual((yield dut.read_address), 24 % 16)

        generators = [
            main_generator(),
            self.fifo_ctrl_flag_checker(dut, write_threshold=16, read_threshold=0),
        ]
        run_simulation(dut, generators)

    def test_fifo_ctrl_level_changes(self):
        # Verify FIFOCtrl level changes.
        dut = _LiteDRAMFIFOCtrl(base=0, depth=16, read_threshold=0, write_threshold=16)

        def main_generator():
            self.assertEqual((yield dut.level), 0)

            # Level
            def check_level_diff(write, read, diff):
                level = (yield dut.level)
                yield dut.write.eq(write)
                yield dut.read.eq(read)
                yield
                yield dut.write.eq(0)
                yield dut.read.eq(0)
                yield
                self.assertEqual((yield dut.level), level + diff)

            check_level_diff(write=1, read=0, diff=+1)
            check_level_diff(write=1, read=0, diff=+1)
            check_level_diff(write=1, read=1, diff=+0)
            check_level_diff(write=1, read=1, diff=+0)
            check_level_diff(write=0, read=1, diff=-1)
            check_level_diff(write=0, read=1, diff=-1)

        generators = [
            main_generator(),
            self.fifo_ctrl_flag_checker(dut, write_threshold=16, read_threshold=0),
        ]
        run_simulation(dut, generators)

    # _LiteDRAMFIFOWriter --------------------------------------------------------------------------

    def fifo_writer_test(self, depth, sequence_len, write_threshold):
        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
                ctrl = _LiteDRAMFIFOCtrl(base=8, depth=depth,
                    read_threshold  = 0,
                    write_threshold = write_threshold)
                self.submodules.ctrl = ctrl
                writer = _LiteDRAMFIFOWriter(data_width=32, port=self.port, ctrl=ctrl)
                self.submodules.writer = writer

                self.memory = DRAMMemory(32, 128)
                assert 8 + sequence_len <= len(self.memory.mem)

        write_data = [seed_to_data(i) for i in range(sequence_len)]

        def generator(dut):
            for data in write_data:
                yield dut.writer.sink.valid.eq(1)
                yield dut.writer.sink.data.eq(data)
                yield
                while (yield dut.writer.sink.ready) == 0:
                    yield
                yield dut.writer.sink.valid.eq(0)

            for _ in range(16):
                yield

        dut = DUT()
        generators = [
            generator(dut),
            dut.memory.write_handler(dut.port),
            self.fifo_ctrl_flag_checker(dut.ctrl,
                write_threshold = write_threshold,
                read_threshold  = 0),
            timeout_generator(1500),
        ]
        run_simulation(dut, generators)

        mem_expected = [0] * len(dut.memory.mem)
        for i, data in enumerate(write_data):
            mem_expected[8 + i%depth] = data
        self.assertEqual(dut.memory.mem, mem_expected)

    def test_fifo_writer_sequence(self):
        # Verify simple FIFOWriter sequence.
        self.fifo_writer_test(sequence_len=48, depth=64, write_threshold=64)

    def test_fifo_writer_address_wraps(self):
        # Verify FIFOWriter sequence with address wraps.
        self.fifo_writer_test(sequence_len=48, depth=32, write_threshold=64)

    def test_fifo_writer_stops_after_threshold(self):
        # Verify FIFOWriter sequence with stop after threshold is reached.
        with self.assertRaises(TimeoutError):
            self.fifo_writer_test(sequence_len=48, depth=32, write_threshold=32)

    # _LiteDRAMFIFOReader --------------------------------------------------------------------------

    def fifo_reader_test(self, depth, sequence_len, read_threshold, inital_writes=0):
        memory_data = [seed_to_data(i) for i in range(128)]
        read_data   = []

        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeReadPort(address_width=32, data_width=32)
                ctrl = _LiteDRAMFIFOCtrl(base=8, depth=depth,
                    read_threshold  = read_threshold,
                    write_threshold = depth)
                reader = _LiteDRAMFIFOReader(data_width=32, port=self.port, ctrl=ctrl)
                self.submodules.ctrl = ctrl
                self.submodules.reader = reader

                self.memory = DRAMMemory(32, len(memory_data), init=memory_data)
                assert 8 + sequence_len <= len(self.memory.mem)

        def reader(dut):
            # Fake writing to fifo
            yield dut.ctrl.write.eq(1)
            for _ in range(inital_writes):
                yield
            yield dut.ctrl.write.eq(0)
            yield

            for _ in range(sequence_len):
                # Fake single write
                yield dut.ctrl.write.eq(1)
                yield
                yield dut.ctrl.write.eq(0)

                while (yield dut.reader.source.valid) == 0:
                    yield
                read_data.append((yield dut.reader.source.data))
                yield dut.reader.source.ready.eq(1)
                yield
                yield dut.reader.source.ready.eq(0)
                yield

        dut = DUT()
        generators = [
            reader(dut),
            dut.memory.read_handler(dut.port),
            self.fifo_ctrl_flag_checker(dut.ctrl,
                write_threshold = depth,
                read_threshold  = read_threshold),
            timeout_generator(1500),
        ]
        run_simulation(dut, generators)

        read_data_expected = [memory_data[8 + i%depth] for i in range(sequence_len)]
        self.assertEqual(read_data, read_data_expected)

    def test_fifo_reader_sequence(self):
        # Verify simple FIFOReader sequence.
        self.fifo_reader_test(sequence_len=48, depth=64, read_threshold=0)

    def test_fifo_reader_address_wraps(self):
        # Verify FIFOReader sequence with address wraps.
        self.fifo_reader_test(sequence_len=48, depth=32, read_threshold=0)

    def test_fifo_reader_requires_threshold(self):
        # Verify FIFOReader sequence with start after threshold is reached.
        with self.assertRaises(TimeoutError):
            self.fifo_reader_test(sequence_len=48, depth=32, read_threshold=8)
        # Will work after we perform the initial writes
        self.fifo_reader_test(sequence_len=48, depth=32, read_threshold=8, inital_writes=8)

    # LiteDRAMFIFO ---------------------------------------------------------------------------------

    def test_fifo_default_thresholds(self):
        # Verify FIFO with default threshold.
        # Defaults: read_threshold=0, write_threshold=depth
        read_threshold, write_threshold = (0, 128)
        write_port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
        read_port  = LiteDRAMNativeReadPort(address_width=32,  data_width=32)
        fifo = LiteDRAMFIFO(data_width=32, base=0, depth=write_threshold,
            write_port = write_port,
            read_port  = read_port)

        def generator():
            yield write_port.cmd.ready.eq(1)
            yield write_port.wdata.ready.eq(1)
            for i in range(write_threshold):
                yield fifo.sink.valid.eq(1)
                yield fifo.sink.data.eq(0)
                yield
                while (yield fifo.sink.ready) == 0:
                    yield
            yield

        checker = self.fifo_ctrl_flag_checker(fifo.ctrl, write_threshold, read_threshold)
        run_simulation(fifo, [generator(), checker])

    def test_fifo(self):
        # Verify FIFO.
        class DUT(Module):
            def __init__(self):
                self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
                self.read_port  = LiteDRAMNativeReadPort(address_width=32,  data_width=32)
                self.submodules.fifo = LiteDRAMFIFO(
                    data_width          = 32,
                    depth               = 32,
                    base                = 16,
                    write_port          = self.write_port,
                    read_port           = self.read_port,
                    read_threshold      = 8,
                    write_threshold     = 32 - 8
                )

                self.memory = DRAMMemory(32, 128)

        def generator(dut, valid_random=90):
            prng = random.Random(42)
            # We need 8 more writes to account for read_threshold=8
            for i in range(64 + 8):
                while prng.randrange(100) < valid_random:
                    yield
                yield dut.fifo.sink.valid.eq(1)
                yield dut.fifo.sink.data.eq(i)
                yield
                while (yield dut.fifo.sink.ready) != 1:
                    yield
                yield dut.fifo.sink.valid.eq(0)

        def checker(dut, ready_random=90):
            prng = random.Random(42)
            for i in range(64):
                yield dut.fifo.source.ready.eq(0)
                yield
                while (yield dut.fifo.source.valid) != 1:
                    yield
                while prng.randrange(100) < ready_random:
                    yield
                yield dut.fifo.source.ready.eq(1)
                self.assertEqual((yield dut.fifo.source.data), i)
                yield

        dut = DUT()
        generators = [
            generator(dut),
            checker(dut),
            dut.memory.write_handler(dut.write_port),
            dut.memory.read_handler(dut.read_port)
        ]
        run_simulation(dut, generators)
