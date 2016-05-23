from litex.gen import *

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
            yield dram_port.cmd.ready.eq(0)
            yield dram_port.rdata.valid.eq(0)
            if pending:
                yield dram_port.rdata.valid.eq(1)
                yield dram_port.rdata.data.eq(self.mem[address%self.depth])
                yield
                yield dram_port.rdata.valid.eq(0)
                yield dram_port.rdata.data.eq(0)
                pending = 0
            elif (yield dram_port.cmd.valid):
                pending = not (yield dram_port.cmd.we)
                address = (yield dram_port.cmd.adr)
                yield
                yield dram_port.cmd.ready.eq(1)
            yield

    @passive
    def write_generator(self, dram_port):
        address = 0
        pending = 0
        while True:
            yield dram_port.cmd.ready.eq(0)
            yield dram_port.wdata.ready.eq(0)
            if pending:
                yield dram_port.wdata.ready.eq(1)
                yield
                self.mem[address%self.depth] = (yield dram_port.wdata.data) # TODO manage we
                yield dram_port.wdata.ready.eq(0)
                yield
                pending = 0
            elif (yield dram_port.cmd.valid):
                pending = yield dram_port.cmd.we
                address = (yield dram_port.cmd.adr)
                yield
                yield dram_port.cmd.ready.eq(1)
            yield
