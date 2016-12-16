#!/usr/bin/env python3

import random

from litex.gen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMWritePort, LiteDRAMReadPort
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker

from test.common import DRAMMemory

class TB(Module):
    def __init__(self):
        self.write_port = LiteDRAMWritePort(aw=32, dw=32)
        self.read_port = LiteDRAMReadPort(aw=32, dw=32)
        self.submodules.generator = LiteDRAMBISTGenerator(self.write_port)
        self.submodules.checker = LiteDRAMBISTChecker(self.read_port)


def togglereset(module):
    resig = module.reset.re

    # Check that reset isn't set
    reval = yield resig
    assert not reval, reval

    # Toggle the reset
    yield resig.eq(1)
    yield
    yield resig.eq(0)
    yield  # Takes 3 clock cycles for the reset to have an effect
    yield
    yield
    yield
    yield
    yield

    # Check some initial conditions are correct after reset.
    shooted = yield module.core.shooted
    assert shooted == 0, shooted

    done = yield module.done.status
    assert not done, done


def main_generator(dut, mem):
    # Populate memory with random data
    random.seed(0)
    for i in range(0, len(mem.mem)):
        mem.mem[i] = random.randint(0, 2**mem.width)

    # write
    yield from togglereset(dut.generator)

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
    done = yield dut.generator.done.status
    assert done, done

    # read with no errors
    yield from togglereset(dut.checker)
    errors = yield dut.checker.error_count.status
    assert errors == 0, errors

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
    done = yield dut.checker.done.status
    assert done, done
    errors = yield dut.checker.error_count.status
    assert errors == 0, errors

    yield
    yield

    # read with one error
    yield from togglereset(dut.checker)
    errors = yield dut.checker.error_count.status
    assert errors == 0, errors

    assert mem.mem[20] != 0, mem.mem[20]
    mem.mem[20] = 0  # Make position 20 an error

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
    done = yield dut.checker.done.status
    assert done, done
    errors = yield dut.checker.error_count.status
    assert errors == 1, errors

    yield
    yield


if __name__ == "__main__":
    tb = TB()
    mem = DRAMMemory(32, 128)
    generators = {
        "sys" :   [main_generator(tb, mem),
                   mem.write_generator(tb.write_port),
                   mem.read_generator(tb.read_port)]
    }
    clocks = {"sys": 10}
    run_simulation(tb, generators, clocks, vcd_name="sim.vcd")
