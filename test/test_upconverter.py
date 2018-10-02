import unittest

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMNativeWritePort, LiteDRAMNativeReadPort
from litedram.frontend.adaptation import LiteDRAMNativePortConverter

from test.common import *

from litex.gen.sim import *


class DUT(Module):
    def __init__(self):
        # write port and converter
        self.write_user_port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
        self.write_crossbar_port = LiteDRAMNativeWritePort(address_width=32, data_width=128)
        write_converter = LiteDRAMNativePortConverter(
            self.write_user_port, self.write_crossbar_port)
        self.submodules += write_converter

        # read port and converter
        self.read_user_port = LiteDRAMNativeReadPort(address_width=32, data_width=32)
        self.read_crossbar_port = LiteDRAMNativeReadPort(address_width=32, data_width=128)
        read_converter = LiteDRAMNativePortConverter(
            self.read_user_port, self.read_crossbar_port)
        self.submodules += read_converter

        # memory
        self.memory = DRAMMemory(128, 128)


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


class TestUpConverter(unittest.TestCase):
    def test(self):
        dut = DUT()
        generators = {
            "sys" :   [
                main_generator(dut.write_user_port, dut.read_user_port),
                read_handler(dut.read_user_port),
                dut.memory.write_handler(dut.write_crossbar_port),
                dut.memory.read_handler(dut.read_crossbar_port)
            ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks, vcd_name="sim.vcd")
        self.assertEqual(write_data, read_data)
