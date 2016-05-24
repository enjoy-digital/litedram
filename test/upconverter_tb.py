from litex.gen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMPort
from litedram.frontend.crossbar import LiteDRAMConverter

from test.common import DRAMMemory

class TB(Module):
    def __init__(self):
        self.user_port = LiteDRAMPort(aw=32, dw=32)
        self.internal_port = LiteDRAMPort(aw=32, dw=64)
        self.submodules.converter = LiteDRAMConverter(self.user_port, self.internal_port)
        self.memory = DRAMMemory(64, 128)

def main_generator(dut):
    for i in range(8):
        yield
    # write
    for i in range(8):
        yield dut.user_port.cmd.valid.eq(1)
        yield dut.user_port.cmd.we.eq(1)
        yield dut.user_port.cmd.adr.eq(i)
        yield
        while (yield dut.user_port.cmd.ready) == 0:
            yield
        yield dut.user_port.cmd.valid.eq(0)
        yield
        yield dut.user_port.wdata.valid.eq(1)
        if i%2:
            yield dut.user_port.wdata.data.eq(0x01234567)
        else:
            yield dut.user_port.wdata.data.eq(0x89abcdef)        
        yield
        while (yield dut.user_port.wdata.ready) == 0:
            yield
        yield dut.user_port.wdata.valid.eq(0)
        yield
    # read
    for i in range(8):
        yield dut.user_port.rdata.ready.eq(1)
        for j in range(2):
            yield dut.user_port.cmd.valid.eq(1)
            yield dut.user_port.cmd.we.eq(0)
            yield dut.user_port.cmd.adr.eq(i)
            yield
            while (yield dut.user_port.cmd.ready) == 0:
                yield
            yield dut.user_port.cmd.valid.eq(0)
            yield

if __name__ == "__main__":
    tb = TB()
    generators = {
        "sys" :   [main_generator(tb),
                   tb.memory.write_generator(tb.internal_port),
                   tb.memory.read_generator(tb.internal_port)]
    }
    clocks = {"sys": 10}
    run_simulation(tb, generators, clocks, vcd_name="sim.vcd")
