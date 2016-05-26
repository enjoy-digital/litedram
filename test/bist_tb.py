#!/usr/bin/env python3

from litex.gen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMPort
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker

from test.common import DRAMMemory

class TB(Module):
    def __init__(self):
        self.write_port = LiteDRAMPort(aw=32, dw=32)
        self.read_port = LiteDRAMPort(aw=32, dw=32)
        self.submodules.generator = LiteDRAMBISTGenerator(self.write_port)
        self.submodules.checker = LiteDRAMBISTChecker(self.read_port)

def main_generator(dut):
    for i in range(8):
        yield
    # write
    yield dut.generator.base.storage.eq(16)
    yield dut.generator.length.storage.eq(64)
    for i in range(8):
        yield
    yield dut.generator.shoot.re.eq(1)
    yield
    yield dut.generator.shoot.re.eq(0)
    for i in range(8):
        yield
    while((yield dut.generator.done.status) == 0):
        yield
    # read
    yield dut.checker.base.storage.eq(16)
    yield dut.checker.length.storage.eq(64)
    for i in range(8):
        yield
    yield dut.checker.shoot.re.eq(1)
    yield
    yield dut.checker.shoot.re.eq(0)
    for i in range(8):
        yield
    while((yield dut.checker.done.status) == 0):
        yield
    # check
    print("errors {:d}".format((yield dut.checker.error_count.status)))
    yield

if __name__ == "__main__":
    tb = TB()
    mem = DRAMMemory(32, 128)
    generators = {
        "sys" :   [main_generator(tb),
                   mem.write_generator(tb.write_port),
                   mem.read_generator(tb.read_port)]
    }
    clocks = {"sys": 10}
    run_simulation(tb, generators, clocks, vcd_name="sim.vcd")
