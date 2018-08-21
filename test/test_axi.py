import unittest
import random

from migen import *

from litedram.common import LiteDRAMNativePort
from litedram.frontend.axi import *

from litex.gen.sim import *


def main_generator(axi_port, dram_port, dut):
    prng = random.Random(42)
    # axi_port always accepting wresps/rdatas
    yield axi_port.b.ready.eq(1)
    yield axi_port.r.ready.eq(1)
    yield
    # test writes
    for i in range(16):
        # write command
        yield axi_port.aw.valid.eq(1)
        yield axi_port.aw.addr.eq(i)
        while (yield dram_port.cmd.ready) == 0:
            if prng.randrange(100) < 20:
                yield dram_port.cmd.ready.eq(1)
            yield
        yield axi_port.aw.valid.eq(0)
        yield dram_port.cmd.ready.eq(0)
        yield
        # write data
        yield axi_port.w.valid.eq(1)
        yield axi_port.w.data.eq(i)
        while (yield dram_port.wdata.ready) == 0:
            if prng.randrange(100) < 20:
                yield dram_port.wdata.ready.eq(1)
            yield
            if (yield axi_port.w.ready) == 1:
                yield axi_port.w.valid.eq(0)
        yield axi_port.aw.valid.eq(0)
        yield dram_port.wdata.ready.eq(0)
        yield
    # test reads
    for i in range(16):
        # read command
        yield axi_port.ar.valid.eq(1)
        yield axi_port.ar.addr.eq(i)
        while (yield dram_port.cmd.ready) == 0:
            if prng.randrange(100) < 20:
                yield dram_port.cmd.ready.eq(1)
            yield
        yield axi_port.ar.valid.eq(0)
        yield dram_port.cmd.ready.eq(0)
        yield
        # read data
        yield dram_port.rdata.valid.eq(1)
        yield dram_port.rdata.data.eq(i)
        while (yield dram_port.rdata.valid) == 0:
            if prng.randrange(100) < 20:
                yield dram_port.rdata.valid.eq(1)
            yield
        yield axi_port.ar.valid.eq(0)
        yield dram_port.rdata.valid.eq(0)
        yield
    for i in range(128):
        yield

class TestAXI(unittest.TestCase):
    def test(self):
        axi_port = LiteDRAMAXIPort(32, 24, 32)
        dram_port = LiteDRAMNativePort("both", 24, 32)
        dut = LiteDRAMAXI2Native(axi_port, dram_port)
        run_simulation(dut, main_generator(axi_port, dram_port, dut), vcd_name="axi.vcd")
