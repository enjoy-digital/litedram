#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *

from litex.gen.sim import *

from litedram.common import *
from litedram.frontend.dma import *

from test.common import *


class DMAWriterDriver:
    def __init__(self, dma):
        self.dma = dma

    def write(self, pattern):
        yield self.dma.sink.valid.eq(1)
        for adr, data in pattern:
            yield self.dma.sink.address.eq(adr)
            yield self.dma.sink.data.eq(data)
            while not (yield self.dma.sink.ready):
                yield
            yield
        yield self.dma.sink.valid.eq(0)

    @staticmethod
    def wait_complete(port, n):
        for _ in range(n):
            while not (yield port.wdata.ready):
                yield
            yield


class DMAReaderDriver:
    def __init__(self, dma):
        self.dma  = dma
        self.data = []

    def read(self, address_list):
        n_last = len(self.data)
        yield self.dma.sink.valid.eq(1)
        for adr in address_list:
            yield self.dma.sink.address.eq(adr)
            while not (yield self.dma.sink.ready):
                yield
            while (yield self.dma.sink.ready):
                yield
        yield self.dma.sink.valid.eq(0)
        while len(self.data) < n_last + len(address_list):
            yield

    @passive
    def read_handler(self):
        yield self.dma.source.ready.eq(1)
        while True:
            if (yield self.dma.source.valid):
                self.data.append((yield self.dma.source.data))
            yield


class TestDMA(MemoryTestDataMixin, unittest.TestCase):

    # LiteDRAMDMAWriter ----------------------------------------------------------------------------

    def dma_writer_test(self, pattern, mem_expected, data_width, **kwargs):
        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeWritePort(address_width=32, data_width=data_width)
                self.submodules.dma = LiteDRAMDMAWriter(self.port, **kwargs)

        dut = DUT()
        driver = DMAWriterDriver(dut.dma)
        mem = DRAMMemory(data_width, len(mem_expected))

        generators = [
            driver.write(pattern),
            driver.wait_complete(dut.port, len(pattern)),
            mem.write_handler(dut.port),
        ]
        run_simulation(dut, generators)
        self.assertEqual(mem.mem, mem_expected)

    def test_dma_writer_single(self):
        # Verify DMAWriter with a single 32-bit data.
        pattern            = [(0x04, 0xdeadc0de)]
        mem_expected       = [0] * 32
        mem_expected[0x04] = 0xdeadc0de
        self.dma_writer_test(pattern, mem_expected, data_width=32)

    def test_dma_writer_multiple(self):
        # Verify DMAWriter with multiple 32-bit datas.
        data = self.pattern_test_data["32bit"]
        self.dma_writer_test(data["pattern"], data["expected"], data_width=32)

    def test_dma_writer_sequential(self):
        # Verify DMAWriter with sequential 32-bit datas.
        data = self.pattern_test_data["32bit_sequential"]
        self.dma_writer_test(data["pattern"], data["expected"], data_width=32)

    def test_dma_writer_long_sequential(self):
        # Verify DMAWriter with long sequential 32-bit datas.
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_writer_test(data["pattern"], data["expected"], data_width=32)

    def test_dma_writer_no_fifo(self):
        # Verify DMAWriter without FIFO.
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_writer_test(data["pattern"], data["expected"], data_width=32, fifo_depth=1)

    def test_dma_writer_fifo_buffered(self):
        # Verify DMAWriter with a buffered FIFO.
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_writer_test(data["pattern"], data["expected"], data_width=32, fifo_buffered=True)

    def test_dma_writer_duplicates(self):
        # Verify DMAWriter with a duplicate addresses.
        data = self.pattern_test_data["32bit_duplicates"]
        self.dma_writer_test(data["pattern"], data["expected"], data_width=32)

    # LiteDRAMDMAReader ----------------------------------------------------------------------------

    def dma_reader_test(self, pattern, mem_expected, data_width, **kwargs):
        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeReadPort(address_width=32, data_width=data_width)
                self.submodules.dma = LiteDRAMDMAReader(self.port, **kwargs)

        dut    = DUT()
        driver = DMAReaderDriver(dut.dma)
        mem    = DRAMMemory(data_width, len(mem_expected), init=mem_expected)

        generators = [
            driver.read([adr for adr, data in pattern]),
            driver.read_handler(),
            mem.read_handler(dut.port),
        ]
        run_simulation(dut, generators)
        self.assertEqual(driver.data, [data for adr, data in pattern])

    def test_dma_reader_single(self):
        # Verify DMAReader with a single 32-bit data.
        pattern            = [(0x04, 0xdeadc0de)]
        mem_expected       = [0] * 32
        mem_expected[0x04] = 0xdeadc0de
        self.dma_reader_test(pattern, mem_expected, data_width=32)

    def test_dma_reader_multiple(self):
        # Verify DMAReader with multiple 32-bit datas.
        data = self.pattern_test_data["32bit"]
        self.dma_reader_test(data["pattern"], data["expected"], data_width=32)

    def test_dma_reader_sequential(self):
        # Verify DMAReader with sequential 32-bit datas.
        data = self.pattern_test_data["32bit_sequential"]
        self.dma_reader_test(data["pattern"], data["expected"], data_width=32)

    def test_dma_reader_long_sequential(self):
        # Verify DMAReader with long sequential 32-bit datas.
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_reader_test(data["pattern"], data["expected"], data_width=32)

    def test_dma_reader_no_fifo(self):
        # Verify DMAReader without FIFO.
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_reader_test(data["pattern"], data["expected"], data_width=32, fifo_depth=1)

    def test_dma_reader_fifo_buffered(self):
        # Verify DMAReader with a buffered FIFO.
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_reader_test(data["pattern"], data["expected"], data_width=32, fifo_buffered=True)
