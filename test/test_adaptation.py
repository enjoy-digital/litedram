# This file is Copyright (c) 2017-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
# License: BSD

import unittest

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMNativeWritePort, LiteDRAMNativeReadPort
from litedram.frontend.adaptation import LiteDRAMNativePortConverter, LiteDRAMNativePortCDC

from test.common import *

from litex.gen.sim import *


class ConverterDUT(Module):
    def __init__(self, user_data_width, native_data_width, mem_depth):
        self.write_user_port     = LiteDRAMNativeWritePort(address_width=32, data_width=user_data_width)
        self.write_crossbar_port = LiteDRAMNativeWritePort(address_width=32, data_width=native_data_width)
        self.read_user_port      = LiteDRAMNativeReadPort( address_width=32, data_width=user_data_width)
        self.read_crossbar_port  = LiteDRAMNativeReadPort( address_width=32, data_width=native_data_width)

        # Memory
        self.memory = DRAMMemory(native_data_width, mem_depth)

    def do_finalize(self):
        self.submodules.write_converter = LiteDRAMNativePortConverter(
            self.write_user_port, self.write_crossbar_port)
        self.submodules.read_converter = LiteDRAMNativePortConverter(
            self.read_user_port, self.read_crossbar_port)

    def read(self, address, read_data=True):
        port = self.read_user_port
        yield port.cmd.valid.eq(1)
        yield port.cmd.we.eq(0)
        yield port.cmd.addr.eq(address)
        yield
        while (yield port.cmd.ready) == 0:
            yield
        yield port.cmd.valid.eq(0)
        yield
        if read_data:
            while (yield port.rdata.valid) == 0:
                yield
            data = (yield port.rdata.data)
            yield port.rdata.ready.eq(1)
            yield
            yield port.rdata.ready.eq(0)
            yield
            return data

    def write(self, address, data, we=None):
        if we is None:
            we = 2**self.write_user_port.wdata.we.nbits - 1
        if self.write_user_port.data_width > self.write_crossbar_port.data_width:
            yield from self._write_down(address, data, we)
        else:
            yield from self._write_up(address, data, we)

    def _write_up(self, address, data, we):
        port = self.write_user_port
        yield port.cmd.valid.eq(1)
        yield port.cmd.we.eq(1)
        yield port.cmd.addr.eq(address)
        yield
        while (yield port.cmd.ready) == 0:
            yield
        yield port.cmd.valid.eq(0)
        yield
        yield port.wdata.valid.eq(1)
        yield port.wdata.data.eq(data)
        yield port.wdata.we.eq(we)
        yield
        while (yield port.wdata.ready) == 0:
            yield
        yield port.wdata.valid.eq(0)
        yield

    def _write_down(self, address, data, we):
        # Down converter must have all the data available along with cmd, it will set
        # user_port.cmd.ready only when it sends all input words.
        port = self.write_user_port
        yield port.cmd.valid.eq(1)
        yield port.cmd.we.eq(1)
        yield port.cmd.addr.eq(address)
        yield port.wdata.valid.eq(1)
        yield port.wdata.data.eq(data)
        yield port.wdata.we.eq(we)
        yield
        # Ready goes up only after StrideConverter copied all words
        while (yield port.cmd.ready) == 0:
            yield
        yield port.cmd.valid.eq(0)
        yield
        while (yield port.wdata.ready) == 0:
            yield
        yield port.wdata.valid.eq(0)
        yield


class CDCDUT(ConverterDUT):
    def do_finalize(self):
        # Change clock domains
        self.write_user_port.clock_domain     = "user"
        self.read_user_port.clock_domain      = "user"
        self.write_crossbar_port.clock_domain = "native"
        self.read_crossbar_port.clock_domain  = "native"

        # Add CDC
        self.submodules.write_converter = LiteDRAMNativePortCDC(
            port_from = self.write_user_port,
            port_to   = self.write_crossbar_port)
        self.submodules.read_converter = LiteDRAMNativePortCDC(
            port_from = self.read_user_port,
            port_to   = self.read_crossbar_port)


class TestAdaptation(MemoryTestDataMixin, unittest.TestCase):
    def test_converter_down_ratio_must_be_integer(self):
        with self.assertRaises(ValueError) as cm:
            dut = ConverterDUT(user_data_width=64, native_data_width=24, mem_depth=128)
            dut.finalize()
        self.assertIn("ratio must be an int", str(cm.exception).lower())

    def test_converter_up_ratio_must_be_integer(self):
        with self.assertRaises(ValueError) as cm:
            dut = ConverterDUT(user_data_width=32, native_data_width=48, mem_depth=128)
            dut.finalize()
        self.assertIn("ratio must be an int", str(cm.exception).lower())

    def converter_readback_test(self, dut, pattern, mem_expected):
        assert len(set(adr for adr, _ in pattern)) == len(pattern), "Pattern has duplicates!"
        read_data = []

        @passive
        def read_handler(read_port):
            yield read_port.rdata.ready.eq(1)
            while True:
                if (yield read_port.rdata.valid):
                    read_data.append((yield read_port.rdata.data))
                yield

        def main_generator(dut, pattern):
            for adr, data in pattern:
                yield from dut.write(adr, data)

            for adr, _ in pattern:
                yield from dut.read(adr, read_data=False)

            # Latency delay
            for _ in range(32):
                yield

        generators = [
            main_generator(dut, pattern),
            read_handler(dut.read_user_port),
            dut.memory.write_handler(dut.write_crossbar_port),
            dut.memory.read_handler(dut.read_crossbar_port),
            timeout_generator(5000),
        ]
        run_simulation(dut, generators)
        self.assertEqual(dut.memory.mem, mem_expected)
        self.assertEqual(read_data, [data for adr, data in pattern])

    def test_converter_1to1(self):
        # Verify 64-bit to 64-bit identify-conversion.
        data = self.pattern_test_data["64bit"]
        dut  = ConverterDUT(user_data_width=64, native_data_width=64, mem_depth=len(data["expected"]))
        self.converter_readback_test(dut, data["pattern"], data["expected"])

    def test_converter_2to1(self):
        # Verify 64-bit to 32-bit down-conversion.
        data = self.pattern_test_data["64bit_to_32bit"]
        dut  = ConverterDUT(user_data_width=64, native_data_width=32, mem_depth=len(data["expected"]))
        self.converter_readback_test(dut, data["pattern"], data["expected"])

    def test_converter_4to1(self):
        # Verify 32-bit to 8-bit down-conversion.
        data = self.pattern_test_data["32bit_to_8bit"]
        dut  = ConverterDUT(user_data_width=32, native_data_width=8, mem_depth=len(data["expected"]))
        self.converter_readback_test(dut, data["pattern"], data["expected"])

    def test_converter_8to1(self):
        # Verify 64-bit to 8-bit down-conversion.
        data = self.pattern_test_data["64bit_to_8bit"]
        dut  = ConverterDUT(user_data_width=64, native_data_width=8, mem_depth=len(data["expected"]))
        self.converter_readback_test(dut, data["pattern"], data["expected"])

    def test_converter_1to2(self):
        # Verify 8-bit to 16-bit up-conversion.
        data = self.pattern_test_data["8bit_to_16bit"]
        dut  = ConverterDUT(user_data_width=8, native_data_width=16, mem_depth=len(data["expected"]))
        self.converter_readback_test(dut, data["pattern"], data["expected"])

    def test_converter_1to4(self):
        # Verify 32-bit to 128-bit up-conversion.
        data = self.pattern_test_data["32bit_to_128bit"]
        dut  = ConverterDUT(user_data_width=32, native_data_width=128, mem_depth=len(data["expected"]))
        self.converter_readback_test(dut, data["pattern"], data["expected"])

    def test_converter_1to8(self):
        # Verify 32-bit to 256-bit up-conversion.
        data = self.pattern_test_data["32bit_to_256bit"]
        dut  = ConverterDUT(user_data_width=32, native_data_width=256, mem_depth=len(data["expected"]))
        self.converter_readback_test(dut, data["pattern"], data["expected"])

    # TODO: implement case when user does not write all words (LiteDRAMNativeWritePortUpConverter)
    @unittest.skip("Only full-burst writes currently supported")
    def test_converter_up_not_aligned(self):
        data = self.pattern_test_data["8bit_to_32bit_not_aligned"]
        dut  = ConverterDUT(user_data_width=8, native_data_width=32, mem_depth=len(data["expected"]))
        self.converter_readback_test(dut, data["pattern"], data["expected"])

    def cdc_readback_test(self, dut, pattern, mem_expected, clocks):
        assert len(set(adr for adr, _ in pattern)) == len(pattern), "Pattern has duplicates!"
        read_data = []

        @passive
        def read_handler(read_port):
            yield read_port.rdata.ready.eq(1)
            while True:
                if (yield read_port.rdata.valid):
                    read_data.append((yield read_port.rdata.data))
                yield

        def main_generator(dut, pattern):
            for adr, data in pattern:
                yield from dut.write(adr, data)

            for adr, _ in pattern:
                yield from dut.read(adr, read_data=False)

            # Latency delay
            for _ in range(32):
                yield

        generators = {
            "user": [
                main_generator(dut, pattern),
                read_handler(dut.read_user_port),
                timeout_generator(5000),
            ],
            "native": [
                dut.memory.write_handler(dut.write_crossbar_port),
                dut.memory.read_handler(dut.read_crossbar_port),
            ],
        }
        run_simulation(dut, generators, clocks)
        self.assertEqual(dut.memory.mem, mem_expected)
        self.assertEqual(read_data, [data for adr, data in pattern])

    def test_port_cdc_same_clocks(self):
        # Verify CDC with same clocks (frequency and phase).
        data = self.pattern_test_data["32bit"]
        dut  = CDCDUT(user_data_width=32, native_data_width=32, mem_depth=len(data["expected"]))
        clocks = {
            "user": 10,
            "native": (7, 3),
        }
        self.cdc_readback_test(dut, data["pattern"], data["expected"], clocks=clocks)

    def test_port_cdc_different_period(self):
        # Verify CDC with different clock frequencies.
        data = self.pattern_test_data["32bit"]
        dut  = CDCDUT(user_data_width=32, native_data_width=32, mem_depth=len(data["expected"]))
        clocks = {
            "user": 10,
            "native": 7,
        }
        self.cdc_readback_test(dut, data["pattern"], data["expected"], clocks=clocks)

    def test_port_cdc_out_of_phase(self):
        # Verify CDC with different clock phases.
        data = self.pattern_test_data["32bit"]
        dut  = CDCDUT(user_data_width=32, native_data_width=32, mem_depth=len(data["expected"]))
        clocks = {
            "user": 10,
            "native": (7, 3),
        }
        self.cdc_readback_test(dut, data["pattern"], data["expected"], clocks=clocks)
