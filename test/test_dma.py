#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *

from litex.gen.sim import *

from litedram.common import *
from litedram.frontend.axi import *
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

    def test_dma_writer_csr_disabled_sink_not_ready(self):
        # Verify DMAWriter with CSR control does not sink data before being enabled.
        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
                self.submodules.dma = LiteDRAMDMAWriter(self.port, with_csr=True)

        def main_generator(dut):
            yield dut.dma._base.storage.eq(0x00)
            yield dut.dma._length.storage.eq(0x04)
            yield dut.dma.sink.valid.eq(1)
            yield dut.dma.sink.data.eq(0xdeadbeef)

            for _ in range(4):
                self.assertEqual((yield dut.dma.sink.ready), 0)
                yield

            yield dut.dma._enable.storage.eq(1)
            while not (yield dut.dma.sink.ready):
                yield
            yield
            yield dut.dma.sink.valid.eq(0)

            for _ in range(8):  # wait for memory
                yield

        dut = DUT()
        mem = DRAMMemory(32, 4)

        run_simulation(dut, [
            main_generator(dut),
            mem.write_handler(dut.port),
            timeout_generator(1000),
        ])
        self.assertEqual(mem.mem[0], 0xdeadbeef)

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

    # AXI with CSR ---------------------------------------------------------------------------------

    def dma_axi_csr_dut(self, dma_cls, data_width):
        class DUT(Module):
            def __init__(self):
                self.axi_port    = LiteDRAMAXIPort(data_width=data_width, address_width=32, id_width=1)
                self.native_port = LiteDRAMNativePort("both", 32, data_width)
                self.submodules.axi2native = LiteDRAMAXI2Native(self.axi_port, self.native_port)
                self.submodules.dma        = dma_cls(self.axi_port, with_csr=True)
        return DUT()

    def test_dma_writer_axi_csr(self):
        # CSR base/length are in bytes, AXI addresses must be byte addresses and each single beat
        # burst must be closed with WLAST (to get a write response).
        for data_width in [32, 64]:
            with self.subTest(data_width=data_width):
                nbytes = data_width//8
                words  = [0x11223344 + i for i in range(4)]
                dut    = self.dma_axi_csr_dut(LiteDRAMDMAWriter, data_width)
                mem    = DRAMMemory(data_width, 64)
                bresps = []

                def generator():
                    yield dut.dma._base.storage.eq(0x40)
                    yield dut.dma._length.storage.eq(len(words)*nbytes)
                    yield dut.dma._enable.storage.eq(1)
                    for word in words:
                        yield dut.dma.sink.valid.eq(1)
                        yield dut.dma.sink.data.eq(word)
                        yield
                        while not (yield dut.dma.sink.ready):
                            yield
                    yield dut.dma.sink.valid.eq(0)
                    for _ in range(256):
                        yield

                @passive
                def b_monitor():
                    while True:
                        if (yield dut.axi_port.b.valid) and (yield dut.axi_port.b.ready):
                            bresps.append((yield dut.axi_port.b.resp))
                        yield

                run_simulation(dut, [generator(), b_monitor(), mem.write_handler(dut.native_port), mem.read_handler(dut.native_port)])
                self.assertEqual(mem.mem[0x40//nbytes:0x40//nbytes + len(words)], words)
                self.assertEqual(bresps, [0]*len(words))

    def test_dma_reader_axi_csr(self):
        # CSR base/length are in bytes, AXI addresses must be byte addresses.
        for data_width in [32, 64]:
            with self.subTest(data_width=data_width):
                nbytes   = data_width//8
                words    = [0x11223344, 0x55667788]
                mem_init = [0xdeadbeef]*64
                mem_init[0x40//nbytes:0x40//nbytes + len(words)] = words
                dut      = self.dma_axi_csr_dut(LiteDRAMDMAReader, data_width)
                mem      = DRAMMemory(data_width, 64, init=mem_init)
                data     = []

                def generator():
                    yield dut.dma._base.storage.eq(0x40)
                    yield dut.dma._length.storage.eq(len(words)*nbytes)
                    yield dut.dma._enable.storage.eq(1)
                    yield dut.dma.source.ready.eq(1)
                    for _ in range(256):
                        yield
                        if (yield dut.dma.source.valid):
                            data.append((yield dut.dma.source.data))

                run_simulation(dut, [generator(), mem.read_handler(dut.native_port), mem.write_handler(dut.native_port)])
                self.assertEqual(data, words)

    # CSR loop mode --------------------------------------------------------------------------------

    def dma_reader_csr_loop_test(self, loop):
        # With loop set, the reader restarts from base after the last address and keeps streaming
        # (last marks the end of each pass); clearing loop stops it at the end of the current
        # pass. Without loop, it stops (done) after a single pass.
        nbytes   = 4
        base     = 0x10
        words    = [0x11111111, 0x22222222, 0x33333333, 0x44444444]
        mem_init = [0xdeadbeef]*32
        mem_init[base//nbytes:base//nbytes + len(words)] = words

        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeReadPort(address_width=32, data_width=32)
                self.submodules.dma = LiteDRAMDMAReader(self.port, with_csr=True)

        dut   = DUT()
        mem   = DRAMMemory(32, len(mem_init), init=mem_init)
        data  = []
        lasts = []
        done  = {}

        def generator():
            yield dut.dma._base.storage.eq(base)
            yield dut.dma._length.storage.eq(len(words)*nbytes)
            yield dut.dma._loop.storage.eq(loop)
            yield dut.dma._enable.storage.eq(1)
            yield dut.dma.source.ready.eq(1)
            cycles = 0
            while True:
                yield
                cycles += 1
                if (yield dut.dma.source.valid):
                    data.append((yield dut.dma.source.data))
                    lasts.append((yield dut.dma.source.last))
                if loop:
                    # Two full passes have been streamed: stop looping.
                    if len(data) == 2*len(words):
                        done["two_passes"] = (yield dut.dma._done.status)
                        yield dut.dma._loop.storage.eq(0)
                    if len(data) >= 2*len(words) and cycles >= 256:
                        break
                elif cycles >= 256:
                    break
            done["end"] = (yield dut.dma._done.status)

        run_simulation(dut, [generator(), mem.read_handler(dut.port), timeout_generator(1000)])

        if loop:
            # At least 2 passes, stopped at a pass boundary once loop is cleared.
            self.assertGreaterEqual(len(data), 2*len(words))
            self.assertEqual(len(data) % len(words), 0)
            self.assertEqual(done["two_passes"], 0)
        else:
            # A single pass.
            self.assertEqual(len(data), len(words))
        self.assertEqual(data, words*(len(data)//len(words)))
        self.assertEqual(lasts, [int(i % len(words) == len(words) - 1) for i in range(len(data))])
        self.assertEqual(done["end"], 1)

    def test_dma_reader_csr_loop(self):
        self.dma_reader_csr_loop_test(loop=1)

    def test_dma_reader_csr_no_loop(self):
        self.dma_reader_csr_loop_test(loop=0)

    def dma_writer_csr_loop_test(self, loop):
        # With loop set, the writer wraps to base after the last address and keeps accepting
        # data (the memory holds the last pass). Without loop, it stops (done, sink not ready)
        # after a single pass.
        nbytes = 4
        base   = 0x10
        n      = 4
        passes = 3
        values = [0x100*(p + 1) + i for p in range(passes) for i in range(n)]

        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
                self.submodules.dma = LiteDRAMDMAWriter(self.port, with_csr=True)

        dut      = DUT()
        mem      = DRAMMemory(32, 32)
        accepted = []
        done     = {}

        def generator():
            yield dut.dma._base.storage.eq(base)
            yield dut.dma._length.storage.eq(n*nbytes)
            yield dut.dma._loop.storage.eq(loop)
            yield dut.dma._enable.storage.eq(1)
            for value in values:
                yield dut.dma.sink.valid.eq(1)
                yield dut.dma.sink.data.eq(value)
                yield
                stalled = 0
                while not (yield dut.dma.sink.ready):
                    yield
                    stalled += 1
                    if stalled == 32:
                        break
                if stalled == 32:
                    break
                accepted.append(value)
            yield dut.dma.sink.valid.eq(0)
            for _ in range(64): # Drain the writes.
                yield
            done["end"]   = (yield dut.dma._done.status)
            done["ready"] = (yield dut.dma.sink.ready)

        run_simulation(dut, [generator(), mem.write_handler(dut.port), timeout_generator(2000)])

        if loop:
            self.assertEqual(accepted, values)
            self.assertEqual(mem.mem[base//nbytes:base//nbytes + n], values[-n:])
            self.assertEqual(done["end"], 0)
        else:
            self.assertEqual(accepted, values[:n])
            self.assertEqual(mem.mem[base//nbytes:base//nbytes + n], values[:n])
            self.assertEqual(done["end"], 1)
            self.assertEqual(done["ready"], 0)
        # Nothing written outside of [base, base + length).
        self.assertEqual(mem.mem[:base//nbytes], [0]*(base//nbytes))
        self.assertEqual(mem.mem[base//nbytes + n:], [0]*(len(mem.mem) - base//nbytes - n))

    def test_dma_writer_csr_loop(self):
        self.dma_writer_csr_loop_test(loop=1)

    def test_dma_writer_csr_no_loop(self):
        self.dma_writer_csr_loop_test(loop=0)
