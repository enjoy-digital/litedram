#
# This file is part of LiteDRAM.
#
# Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
import random

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMNativeWritePort
from litedram.common import LiteDRAMNativeReadPort
from litedram.frontend.fifo import LiteDRAMFIFO, _LiteDRAMFIFOCtrl
from litedram.frontend.fifo import _LiteDRAMFIFOWriter, _LiteDRAMFIFOReader

from test.common import *


class FIFODUT(Module):
    def __init__(self, base, depth, data_width=8, address_width=32):
        self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=data_width)
        self.read_port  = LiteDRAMNativeReadPort(address_width=32,  data_width=data_width)
        self.submodules.fifo = LiteDRAMFIFO(
            data_width = data_width,
            base       = base,
            depth      = depth,
            write_port = self.write_port,
            read_port  = self.read_port,
        )

        margin = 8
        self.memory = DRAMMemory(data_width, base + depth + margin)

    def write(self, data):
        yield self.fifo.sink.valid.eq(1)
        yield self.fifo.sink.data.eq(data)
        yield
        while not (yield self.fifo.sink.ready):
            yield
        yield self.fifo.sink.valid.eq(0)

    def read(self):
        while not (yield self.fifo.source.valid):
            yield
        yield self.fifo.source.ready.eq(1)
        data = (yield self.fifo.source.data)
        yield
        yield self.fifo.source.ready.eq(0)
        yield
        return data


class TestFIFO(unittest.TestCase):
    # _LiteDRAMFIFOCtrl ----------------------------------------------------------------------------

    def test_fifo_ctrl_address_changes(self):
        # Verify FIFOCtrl address changes.
        dut = _LiteDRAMFIFOCtrl(base=0, depth=16)

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

        run_simulation(dut, main_generator())

    def test_fifo_ctrl_level_changes(self):
        # Verify FIFOCtrl level changes.
        dut = _LiteDRAMFIFOCtrl(base=0, depth=16)

        def main_generator():
            self.assertEqual((yield dut.level), 0)

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

        run_simulation(dut, main_generator())

    # _LiteDRAMFIFOWriter --------------------------------------------------------------------------

    def fifo_writer_test(self, depth, sequence_len, consume=False):
        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
                ctrl = _LiteDRAMFIFOCtrl(base=8, depth=depth)
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

                if consume:
                    yield dut.ctrl.read.eq(1)

            for _ in range(16):
                yield

        dut = DUT()
        generators = [
            generator(dut),
            dut.memory.write_handler(dut.port),
            timeout_generator(1500),
        ]
        run_simulation(dut, generators)

        mem_expected = [0] * len(dut.memory.mem)
        for i, data in enumerate(write_data):
            mem_expected[8 + i%depth] = data
        self.assertEqual(dut.memory.mem, mem_expected)

    def test_fifo_writer_sequence(self):
        # Verify simple FIFOWriter sequence.
        self.fifo_writer_test(sequence_len=48, depth=64)

    def test_fifo_writer_stops_when_full(self):
        # Verify FIFOWriter won't continue writing if noone reads the data.
        with self.assertRaises(TimeoutError):
            self.fifo_writer_test(sequence_len=48, depth=32)

    def test_fifo_writer_address_wraps(self):
        # Verify FIFOWriter address wraps.
        self.fifo_writer_test(sequence_len=48, depth=32, consume=True)

    # _LiteDRAMFIFOReader --------------------------------------------------------------------------

    def fifo_reader_test(self, depth, sequence_len, inital_writes=0):
        memory_data = [seed_to_data(i) for i in range(128)]
        read_data   = []

        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeReadPort(address_width=32, data_width=32)
                ctrl = _LiteDRAMFIFOCtrl(base=8, depth=depth)
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
            timeout_generator(1500),
        ]
        run_simulation(dut, generators)

        read_data_expected = [memory_data[8 + i%depth] for i in range(sequence_len)]
        self.assertEqual(read_data, read_data_expected)

    def test_fifo_reader_sequence(self):
        # Verify simple FIFOReader sequence.
        self.fifo_reader_test(sequence_len=48, depth=64)

    def test_fifo_reader_address_wraps(self):
        # Verify FIFOReader sequence with address wraps.
        self.fifo_reader_test(sequence_len=48, depth=32)

    # LiteDRAMFIFO ---------------------------------------------------------------------------------

    def test_fifo_continuous_stream_short(self):
        # Verify FIFO operation with continuous writes and reads without wrapping
        def generator(dut):
            for i in range(64):
                yield from dut.write(10 + i)

        def checker(dut):
            for i in range(64):
                data = (yield from dut.read())
                self.assertEqual(data, 10 + i)

        dut = FIFODUT(base=16, depth=128)
        generators = [
            generator(dut),
            checker(dut),
            dut.memory.write_handler(dut.write_port),
            dut.memory.read_handler(dut.read_port),
            timeout_generator(1500),
        ]
        run_simulation(dut, generators)

    def test_fifo_continuous_stream_long(self):
        # Verify FIFO operation with continuous writes and reads with wrapping
        def generator(dut):
            for i in range(64):
                yield from dut.write(10 + i)

        def checker(dut):
            for i in range(64):
                data = (yield from dut.read())
                self.assertEqual(data, 10 + i)

        dut = FIFODUT(base=16, depth=32)
        generators = [
            generator(dut),
            checker(dut),
            dut.memory.write_handler(dut.write_port),
            dut.memory.read_handler(dut.read_port),
            timeout_generator(1500),
        ]
        run_simulation(dut, generators)

    def test_fifo_delayed_reader(self):
        # Verify FIFO works correctly when reader starts reading only after writer is full
        def generator(dut):
            for i in range(64):
                yield from dut.write(10 + i)

        def checker(dut):
            # Wait until both the internal writer FIFO and our in-memory FIFO are full
            while (yield dut.fifo.ctrl.writable):
                yield
            for i in range(64):
                data = (yield from dut.read())
                self.assertEqual(data, 10 + i)

        dut = FIFODUT(base=16, depth=32)
        generators = [
            generator(dut),
            checker(dut),
            dut.memory.write_handler(dut.write_port),
            dut.memory.read_handler(dut.read_port),
            timeout_generator(1500),
        ]
        run_simulation(dut, generators)
