#
# This file is part of LiteDRAM.
#
# Copyright (c) 2017-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMNativePort, LiteDRAMNativeWritePort, LiteDRAMNativeReadPort
from litedram.frontend.adapter import LiteDRAMNativePortConverter, LiteDRAMNativePortCDC

from test.common import *

from litex.gen.sim import *


class ConverterDUT(Module):
    def __init__(self, user_data_width, native_data_width, mem_depth, separate_rw=True, read_latency=0):
        self.separate_rw = separate_rw
        if separate_rw:
            self.write_user_port     = LiteDRAMNativeWritePort(address_width=32, data_width=user_data_width)
            self.write_crossbar_port = LiteDRAMNativeWritePort(address_width=32, data_width=native_data_width)
            self.read_user_port      = LiteDRAMNativeReadPort( address_width=32, data_width=user_data_width)
            self.read_crossbar_port  = LiteDRAMNativeReadPort( address_width=32, data_width=native_data_width)
            self.write_driver        = NativePortDriver(self.write_user_port)
            self.read_driver         = NativePortDriver(self.read_user_port)
        else:
            self.write_user_port     = LiteDRAMNativePort(mode="both", address_width=32, data_width=user_data_width)
            self.write_crossbar_port = LiteDRAMNativePort(mode="both", address_width=32, data_width=native_data_width)
            self.write_driver        = NativePortDriver(self.write_user_port)
            self.read_user_port      = self.write_user_port
            self.read_crossbar_port  = self.write_crossbar_port
            self.read_driver         = self.write_driver

        self.driver_generators   = [self.write_driver.write_data_handler(),
                                    self.read_driver.read_data_handler(latency=read_latency)]

        # Memory
        self.memory = DRAMMemory(native_data_width, mem_depth)

    def do_finalize(self):
        if self.separate_rw:
            self.submodules.write_converter = LiteDRAMNativePortConverter(
                self.write_user_port, self.write_crossbar_port)
            self.submodules.read_converter = LiteDRAMNativePortConverter(
                self.read_user_port, self.read_crossbar_port)
        else:
            self.submodules.converter = LiteDRAMNativePortConverter(
                self.write_user_port, self.write_crossbar_port)

    def read(self, address, **kwargs):
        return (yield from self.read_driver.read(address, **kwargs))

    def write(self, address, data, **kwargs):
        if self.write_user_port.data_width > self.write_crossbar_port.data_width:
            kwargs["data_with_cmd"] = True
        return (yield from self.write_driver.write(address, data, **kwargs))


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


class TestAdapter(MemoryTestDataMixin, unittest.TestCase):
    def test_down_converter_ratio_must_be_integer(self):
        with self.assertRaises(ValueError) as cm:
            dut = ConverterDUT(user_data_width=64, native_data_width=24, mem_depth=128)
            dut.finalize()
        self.assertIn("ratio must be an int", str(cm.exception).lower())

    def test_up_converter_ratio_must_be_integer(self):
        with self.assertRaises(ValueError) as cm:
            dut = ConverterDUT(user_data_width=32, native_data_width=48, mem_depth=128)
            dut.finalize()
        self.assertIn("ratio must be an int", str(cm.exception).lower())

    def converter_readback_test(self, dut, pattern, mem_expected, main_generator=None):
        assert len(set(adr for adr, _ in pattern)) == len(pattern), "Pattern has duplicates!"

        if main_generator is None:
            def main_generator(dut):
                for adr, data in pattern:
                    yield from dut.write(adr, data)

                for adr, _ in pattern[:-1]:
                    yield from dut.read(adr, wait_data=False)
                # use cmd.last to indicate last command in the sequence
                # this is needed for the cases in up-converter when it cannot be deduced
                # that port_to.cmd should be sent
                adr, _ = pattern[-1]
                yield from dut.read(adr, wait_data=False, last=1)

                yield from dut.write_driver.wait_all()
                yield from dut.read_driver.wait_all()

        generators = [
            main_generator(dut),
            *dut.driver_generators,
            dut.memory.write_handler(dut.write_crossbar_port),
            dut.memory.read_handler(dut.read_crossbar_port),
            timeout_generator(1000),
        ]
        run_simulation(dut, generators, vcd_name='sim.vcd')
        self.assertEqual(dut.memory.mem, mem_expected)
        self.assertEqual(dut.read_driver.rdata, [data for adr, data in pattern])

    def converter_test(self, test_data, user_data_width, native_data_width, **kwargs):
        for separate_rw in [True, False]:
            with self.subTest(separate_rw=separate_rw):
                data = self.pattern_test_data[test_data]
                dut  = ConverterDUT(user_data_width=user_data_width, native_data_width=native_data_width,
                                    mem_depth=len(data["expected"]), separate_rw=separate_rw, **kwargs)
                self.converter_readback_test(dut, data["pattern"], data["expected"])

    def test_converter_1to1(self):
        # Verify 64-bit to 64-bit identify-conversion.
        self.converter_test(test_data="64bit", user_data_width=64, native_data_width=64)

    def test_converter_2to1(self):
        # Verify 64-bit to 32-bit down-conversion.
        self.converter_test(test_data="64bit_to_32bit", user_data_width=64, native_data_width=32)

    def test_converter_4to1(self):
        # Verify 32-bit to 8-bit down-conversion.
        self.converter_test(test_data="32bit_to_8bit", user_data_width=32, native_data_width=8)

    def test_converter_8to1(self):
        # Verify 64-bit to 8-bit down-conversion.
        self.converter_test(test_data="64bit_to_8bit", user_data_width=64, native_data_width=8)

    def test_converter_1to2(self):
        # Verify 8-bit to 16-bit up-conversion.
        self.converter_test(test_data="8bit_to_16bit", user_data_width=8, native_data_width=16)

    def test_converter_1to4(self):
        # Verify 32-bit to 128-bit up-conversion.
        self.converter_test(test_data="32bit_to_128bit", user_data_width=32, native_data_width=128)

    def test_converter_1to8(self):
        # Verify 32-bit to 256-bit up-conversion.
        self.converter_test(test_data="32bit_to_256bit", user_data_width=32, native_data_width=256)

    def test_up_converter_read_latencies(self):
        # Verify that up-conversion works with different port reader latencies
        cases = {
            "1to2": dict(test_data="8bit_to_16bit",   user_data_width=8,  native_data_width=16),
            "1to4": dict(test_data="32bit_to_128bit", user_data_width=32, native_data_width=128),
            "1to8": dict(test_data="32bit_to_256bit", user_data_width=32, native_data_width=256),
        }
        for latency in [0, 1]:
            with self.subTest(latency=latency):
                for conversion, kwargs in cases.items():
                    with self.subTest(conversion=conversion):
                        self.converter_test(**kwargs, read_latency=latency)

    def test_down_converter_read_latencies(self):
        # Verify that down-conversion works with different port reader latencies
        cases = {
            "2to1": dict(test_data="64bit_to_32bit", user_data_width=64, native_data_width=32),
            "4to1": dict(test_data="32bit_to_8bit",  user_data_width=32, native_data_width=8),
            "8to1": dict(test_data="64bit_to_8bit",  user_data_width=64, native_data_width=8),
        }
        for latency in [0, 1]:
            with self.subTest(latency=latency):
                for conversion, kwargs in cases.items():
                    with self.subTest(conversion=conversion):
                        self.converter_test(**kwargs, read_latency=latency)

    def test_up_converter_write_complete_sequence(self):
        # Verify up-conversion when master sends full sequences (of `ratio` length)
        def main_generator(dut):
            yield from dut.write(0x00, 0x11)  # first
            yield from dut.write(0x01, 0x22)
            yield from dut.write(0x02, 0x33)
            yield from dut.write(0x03, 0x44)
            yield from dut.write(0x04, 0x55)  # second
            yield from dut.write(0x05, 0x66)
            yield from dut.write(0x06, 0x77)
            yield from dut.write(0x07, 0x88)

            yield from dut.write_driver.wait_all()
            for _ in range(8):  # wait for memory
                yield

        mem_expected = [
            #     data  address
            0x44332211,  # 0x00
            0x88776655,  # 0x04
            0x00000000,  # 0x08
            0x00000000,  # 0x0c
        ]

        for separate_rw in [True, False]:
            with self.subTest(separate_rw=separate_rw):
                dut  = ConverterDUT(user_data_width=8, native_data_width=32,
                                    mem_depth=len(mem_expected), separate_rw=separate_rw)
                self.converter_readback_test(dut, pattern=[], mem_expected=mem_expected,
                                             main_generator=main_generator)

    def test_up_converter_write_with_manual_flush(self):
        # Verify that up-conversion writes incomplete data when it receives cmd.last
        def main_generator(dut):
            yield from dut.write(0x00, 0x11, wait_data=False)
            yield from dut.write(0x01, 0x22, wait_data=False)
            yield from dut.write(0x02, 0x33, wait_data=False, last=1)

            yield from dut.write_driver.wait_all()
            for _ in range(8):  # wait for memory
                yield

        mem_expected = [
            #     data  address
            0x00332211,  # 0x00
            0x00000000,  # 0x04
            0x00000000,  # 0x08
            0x00000000,  # 0x0c
        ]

        for separate_rw in [True, False]:
            with self.subTest(separate_rw=separate_rw):
                dut  = ConverterDUT(user_data_width=8, native_data_width=32,
                                    mem_depth=len(mem_expected), separate_rw=separate_rw)
                self.converter_readback_test(dut, pattern=[], mem_expected=mem_expected,
                                             main_generator=main_generator)

    def test_up_converter_auto_flush_on_address_change(self):
        # Verify that up-conversion automatically flushes the cmd if the (shifted) address changes
        def main_generator(dut):
            yield from dut.write(0x00, 0x11, wait_data=False)  # -> 0x00
            yield from dut.write(0x01, 0x22, wait_data=False)  # -> 0x00
            yield from dut.write(0x02, 0x33, wait_data=False)  # -> 0x00
            yield from dut.write(0x04, 0x55, wait_data=False)  # -> 0x01
            yield from dut.write(0x05, 0x66, wait_data=False)  # -> 0x01
            yield from dut.write(0x06, 0x77, wait_data=False)  # -> 0x01
            yield from dut.write(0x07, 0x88, wait_data=False)  # -> 0x01

            yield from dut.write_driver.wait_all()
            for _ in range(8):  # wait for memory
                yield

        mem_expected = [
            #     data  address
            0x00332211,  # 0x00
            0x88776655,  # 0x04
            0x00000000,  # 0x08
            0x00000000,  # 0x0c
        ]


        for separate_rw in [True, False]:
            with self.subTest(separate_rw=separate_rw):
                dut  = ConverterDUT(user_data_width=8, native_data_width=32,
                                    mem_depth=len(mem_expected), separate_rw=separate_rw)
                self.converter_readback_test(dut, pattern=[], mem_expected=mem_expected,
                                             main_generator=main_generator)

    def test_up_converter_auto_flush_on_cmd_we_change(self):
        # Verify that up-conversion automatically flushes the cmd when command type (write/read) changes
        def main_generator(dut):
            yield from dut.write(0x00, 0x11, wait_data=False)
            yield from dut.write(0x01, 0x22, wait_data=False)
            yield from dut.read(0x00, wait_data=False)
            yield from dut.read(0x01, wait_data=False)
            yield from dut.read(0x02, wait_data=False)
            yield from dut.read(0x03, wait_data=False)

            yield from dut.write_driver.wait_all()
            yield from dut.read_driver.wait_all()
            for _ in range(8):  # wait for memory
                yield

        mem_expected = [
            #     data  address
            0x00002211,  # 0x00
            0x00000000,  # 0x04
            0x00000000,  # 0x08
            0x00000000,  # 0x0c
        ]
        pattern = [
            (0x00, 0x11),
            (0x01, 0x22),
            (0x02, 0x00),
            (0x03, 0x00),
        ]

        # with separate_rw=True we will fail because read will happen before write completes
        dut  = ConverterDUT(user_data_width=8, native_data_width=32,
                            mem_depth=len(mem_expected), separate_rw=False)
        self.converter_readback_test(dut, pattern=pattern, mem_expected=mem_expected,
                                     main_generator=main_generator)

    def test_up_converter_write_with_gap(self):
        # Verify that the up-converter can mask data properly when sending non-sequential writes
        def main_generator(dut):
            yield from dut.write(0x00, 0x11, wait_data=False)
            yield from dut.write(0x02, 0x22, wait_data=False)
            yield from dut.write(0x03, 0x33, wait_data=False, last=1)

            yield from dut.write_driver.wait_all()
            for _ in range(8):  # wait for memory
                yield

        mem_expected = [
            # data, address
            0x33220011,  # 0x00
            0x00000000,  # 0x04
            0x00000000,  # 0x08
            0x00000000,  # 0x0c
        ]

        for separate_rw in [True, False]:
            with self.subTest(separate_rw=separate_rw):
                dut  = ConverterDUT(user_data_width=8, native_data_width=32,
                                    mem_depth=len(mem_expected), separate_rw=separate_rw)
                self.converter_readback_test(dut, pattern=[], mem_expected=mem_expected,
                                             main_generator=main_generator)

    def test_up_converter_not_aligned(self):
        data = self.pattern_test_data["8bit_to_32bit_not_aligned"]
        dut  = ConverterDUT(user_data_width=8, native_data_width=32,
                            mem_depth=len(data["expected"]), separate_rw=False)
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
                yield from dut.read(adr, wait_data=False)

            yield from dut.write_driver.wait_all()
            yield from dut.read_driver.wait_all()

        generators = {
            "user": [
                main_generator(dut, pattern),
                read_handler(dut.read_user_port),
                *dut.driver_generators,
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
