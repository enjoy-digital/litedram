from litex.gen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMPort
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker

class TB(Module):
    def __init__(self):
        self.write_port = LiteDRAMPort(aw=32, dw=32)
        self.read_port = LiteDRAMPort(aw=32, dw=32)
        self.submodules.generator = LiteDRAMBISTGenerator(self.write_port)
        self.submodules.checker = LiteDRAMBISTChecker(self.read_port)


class DRAMMemory:
    def __init__(self, width, depth, init=[]):
        self.width = width
        self.depth = depth
        self.mem = []
        for d in init:
            self.mem.append(d)
        for _ in range(depth-len(init)):
            self.mem.append(0)

    @passive
    def read_generator(self, dram_port):
        address = 0
        pending = 0
        while True:
            yield dram_port.ready.eq(0)
            yield dram_port.rdata_valid.eq(0)
            if pending:
                yield dram_port.rdata_valid.eq(1)
                yield dram_port.rdata.eq(self.mem[address%self.depth])
                yield
                yield dram_port.rdata_valid.eq(0)
                yield dram_port.rdata.eq(0)
                pending = 0
            elif (yield dram_port.valid):
                pending = not (yield dram_port.we)
                address = (yield dram_port.adr)
                yield
                yield dram_port.ready.eq(1)
            yield

    @passive
    def write_generator(self, dram_port):
        address = 0
        pending = 0
        while True:
            yield dram_port.ready.eq(0)
            yield dram_port.wdata_ready.eq(0)
            if pending:
                yield dram_port.wdata_ready.eq(1)
                yield
                self.mem[address%self.depth] = (yield dram_port.wdata) # TODO manage we
                yield dram_port.wdata_ready.eq(0)
                yield
                pending = 0
            elif (yield dram_port.valid):
                pending = yield dram_port.we
                address = (yield dram_port.adr)
                yield
                yield dram_port.ready.eq(1)
            yield


def main_generator(dut):
    for i in range(100):
        yield
    # write
    yield dut.generator.base.storage.eq(16)
    yield dut.generator.length.storage.eq(64)
    yield
    yield dut.generator.shoot.re.eq(1)
    yield
    yield dut.generator.shoot.re.eq(0)
    yield
    while((yield dut.generator.done.status) == 0):
        yield
    # read
    yield dut.checker.base.storage.eq(16)
    yield dut.checker.length.storage.eq(64)
    yield
    yield dut.checker.shoot.re.eq(1)
    yield
    yield dut.checker.shoot.re.eq(0)
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
