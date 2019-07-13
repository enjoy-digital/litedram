# This file is Copyright (c) 2017-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import unittest

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMNativeWritePort, LiteDRAMNativeReadPort
from litedram.frontend.adaptation import LiteDRAMNativePortConverter

from test.common import *

from litex.gen.sim import *


class ConverterDUT(Module):
    def __init__(self, user_data_width, native_data_width):
        # write port and converter
        self.write_user_port = LiteDRAMNativeWritePort(address_width=32, data_width=user_data_width)
        self.write_crossbar_port = LiteDRAMNativeWritePort(address_width=32, data_width=native_data_width)
        write_converter = LiteDRAMNativePortConverter(
            self.write_user_port, self.write_crossbar_port)
        self.submodules += write_converter

        # read port and converter
        self.read_user_port = LiteDRAMNativeReadPort(address_width=32, data_width=user_data_width)
        self.read_crossbar_port = LiteDRAMNativeReadPort(address_width=32, data_width=native_data_width)
        read_converter = LiteDRAMNativePortConverter(
            self.read_user_port, self.read_crossbar_port)
        self.submodules += read_converter

        # memory
        self.memory = DRAMMemory(native_data_width, 128)


class TestAdaptation(unittest.TestCase):
    def test_up_converter(self):
        write_data = [seed_to_data(i, nbits=32) for i in range(16)]
        read_data = []

        @passive
        def read_handler(read_port):
            yield read_port.rdata.ready.eq(1)
            while True:
                if (yield read_port.rdata.valid):
                    read_data.append((yield read_port.rdata.data))
                yield


        def main_generator(write_port, read_port):
            # write
            for i in range(16):
                yield write_port.cmd.valid.eq(1)
                yield write_port.cmd.we.eq(1)
                yield write_port.cmd.addr.eq(i)
                yield
                while (yield write_port.cmd.ready) == 0:
                    yield
                yield write_port.cmd.valid.eq(0)
                yield
                yield write_port.wdata.valid.eq(1)
                yield write_port.wdata.data.eq(write_data[i])
                yield
                while (yield write_port.wdata.ready) == 0:
                    yield
                yield write_port.wdata.valid.eq(0)
                yield

            # read
            for i in range(16):
                yield read_port.cmd.valid.eq(1)
                yield read_port.cmd.we.eq(0)
                yield read_port.cmd.addr.eq(i)
                yield
                while (yield read_port.cmd.ready) == 0:
                    yield
                yield read_port.cmd.valid.eq(0)
                yield

            # delay
            for i in range(32):
                yield

        dut = ConverterDUT(user_data_width=32, native_data_width=128)
        generators = [
            main_generator(dut.write_user_port, dut.read_user_port),
            read_handler(dut.read_user_port),
            dut.memory.write_handler(dut.write_crossbar_port),
            dut.memory.read_handler(dut.read_crossbar_port)
        ]
        run_simulation(dut, generators)
        self.assertEqual(write_data, read_data)

    def test_down_converter(self):
        write_data = [seed_to_data(i, nbits=64) for i in range(8)]
        read_data = []

        @passive
        def read_handler(read_port):
            yield read_port.rdata.ready.eq(1)
            while True:
                if (yield read_port.rdata.valid):
                    read_data.append((yield read_port.rdata.data))
                yield

        def main_generator(write_port, read_port):
            # write
            for i in range(8):
                yield write_port.cmd.valid.eq(1)
                yield write_port.cmd.we.eq(1)
                yield write_port.cmd.addr.eq(i)
                yield write_port.wdata.valid.eq(1)
                yield write_port.wdata.data.eq(write_data[i])
                yield
                while (yield write_port.cmd.ready) == 0:
                    yield
                while (yield write_port.wdata.ready) == 0:
                    yield
                yield

            # read
            yield read_port.rdata.ready.eq(1)
            for i in range(8):
                yield read_port.cmd.valid.eq(1)
                yield read_port.cmd.we.eq(0)
                yield read_port.cmd.addr.eq(i)
                yield
                while (yield read_port.cmd.ready) == 0:
                    yield
                yield read_port.cmd.valid.eq(0)
                yield

            # latency delay
            for i in range(32):
                yield

        dut = ConverterDUT(user_data_width=64, native_data_width=32)
        generators = [
            main_generator(dut.write_user_port, dut.read_user_port),
            read_handler(dut.read_user_port),
            dut.memory.write_handler(dut.write_crossbar_port),
            dut.memory.read_handler(dut.read_crossbar_port)
        ]
        run_simulation(dut, generators)
        self.assertEqual(write_data, read_data)
