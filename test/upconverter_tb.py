#!/usr/bin/env python3

from litex.gen import *

from litex.soc.interconnect.stream import *
from litex.soc.interconnect.stream_sim import check

from litedram.common import LiteDRAMWritePort, LiteDRAMReadPort
from litedram.frontend.adaptation import LiteDRAMPortConverter

from test.common import *

class TB(Module):
    def __init__(self):
        self.write_user_port = LiteDRAMWritePort(aw=32, dw=32)
        self.write_crossbar_port = LiteDRAMWritePort(aw=32, dw=64)
        self.submodules.write_converter = LiteDRAMPortConverter(self.write_user_port,
                                                                self.write_crossbar_port)

        self.read_user_port = LiteDRAMReadPort(aw=32, dw=32)
        self.read_crossbar_port = LiteDRAMReadPort(aw=32, dw=64)
        self.submodules.read_converter = LiteDRAMPortConverter(self.read_user_port,
                                                               self.read_crossbar_port)

        self.memory = DRAMMemory(64, 128)


write_data = [seed_to_data(i, nbits=32) for i in range(8)]
read_data = []


@passive
def read_generator(dut):
    yield dut.read_user_port.rdata.ready.eq(1)
    while True:
        if (yield dut.read_user_port.rdata.valid):
            read_data.append((yield dut.read_user_port.rdata.data))
        yield


def main_generator(dut):
    # write
    for i in range(8):
        yield dut.write_user_port.cmd.valid.eq(1)
        yield dut.write_user_port.cmd.we.eq(1)
        yield dut.write_user_port.cmd.adr.eq(i)
        yield
        while (yield dut.write_user_port.cmd.ready) == 0:
            yield
        yield dut.write_user_port.cmd.valid.eq(0)
        yield
        yield dut.write_user_port.wdata.valid.eq(1)
        yield dut.write_user_port.wdata.data.eq(write_data[i])   
        yield
        while (yield dut.write_user_port.wdata.ready) == 0:
            yield
        yield dut.write_user_port.wdata.valid.eq(0)
        yield

    # read
    for i in range(8):
        for j in range(2):
            yield dut.read_user_port.cmd.valid.eq(1)
            yield dut.read_user_port.cmd.we.eq(0)
            yield dut.read_user_port.cmd.adr.eq(i)
            yield
            while (yield dut.read_user_port.cmd.ready) == 0:
                yield
            yield dut.read_user_port.cmd.valid.eq(0)
            yield

    # delay
    for i in range(32):
        yield

    # check
    s, l, e = check(write_data, read_data)
    print("shift " + str(s) + " / length " + str(l) + " / errors " + str(e))


if __name__ == "__main__":
    tb = TB()
    generators = {
        "sys" :   [main_generator(tb),
                   read_generator(tb),
                   tb.memory.write_generator(tb.write_crossbar_port),
                   tb.memory.read_generator(tb.read_crossbar_port)]
    }
    clocks = {"sys": 10}
    run_simulation(tb, generators, clocks, vcd_name="sim.vcd")
