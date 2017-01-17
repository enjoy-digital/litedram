import unittest
import random

from litex.gen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMWritePort, LiteDRAMReadPort
from litedram.frontend.bist import _LiteDRAMBISTGenerator
from litedram.frontend.bist import _LiteDRAMBISTChecker

from test.common import *


class DUT(Module):
    def __init__(self):
        self.write_port = LiteDRAMWritePort(aw=32, dw=32)
        self.read_port = LiteDRAMReadPort(aw=32, dw=32)
        self.submodules.generator = _LiteDRAMBISTGenerator(self.write_port, False)
        self.submodules.checker = _LiteDRAMBISTChecker(self.read_port, False)


def main_generator(dut, mem):
    # write
    yield dut.generator.reset.eq(1)
    yield
    yield dut.generator.reset.eq(0)
    yield

    yield dut.generator.base.eq(16)
    yield dut.generator.length.eq(64)
    for i in range(8):
        yield
    yield dut.generator.start.eq(1)
    yield
    yield dut.generator.start.eq(0)
    for i in range(8):
        yield
    while((yield dut.generator.done) == 0):
        yield
    done = yield dut.generator.done
    assert done, done

    # read (no errors)
    yield dut.checker.reset.eq(1)
    yield
    yield dut.checker.reset.eq(0)
    yield

    yield dut.checker.base.eq(16)
    yield dut.checker.length.eq(64)
    for i in range(8):
        yield
    yield dut.checker.start.eq(1)
    yield
    yield dut.checker.start.eq(0)
    yield
    while True:
        done = (yield dut.checker.done)
        if not done:
            yield
        else:
            break
    assert done, done
    errors = yield dut.checker.err_count
    assert errors == 0, errors

    # corrupt memory (4 errors)
    for i in range(4):
        mem.mem[i+16] = ~mem.mem[i+16]

    # read (4 errors)
    yield dut.checker.reset.eq(1)
    yield
    yield dut.checker.reset.eq(0)
    yield

    yield dut.checker.base.eq(16)
    yield dut.checker.length.eq(64)
    yield dut.checker.start.eq(1)
    yield
    yield dut.checker.start.eq(0)
    yield
    while True:
        done = (yield dut.checker.done)
        if not done:
            yield
        else:
            break
    assert done, done
    errors = yield dut.checker.err_count
    assert errors == 4, errors

    # revert memory
    for i in range(4):
        mem.mem[i+16] = ~mem.mem[i+16]

    # read (no errors)
    yield dut.checker.reset.eq(1)
    yield
    yield dut.checker.reset.eq(0)
    yield

    yield dut.checker.base.eq(16)
    yield dut.checker.length.eq(64)
    for i in range(8):
        yield
    yield dut.checker.start.eq(1)
    yield
    yield dut.checker.start.eq(0)
    yield
    while True:
        done = (yield dut.checker.done)
        if not done:
            yield
        else:
            break
    assert done, done
    errors = yield dut.checker.err_count
    assert errors == 0, errors


class TestBIST(unittest.TestCase):
    def test(self):
        dut = DUT()
        mem = DRAMMemory(32, 128)
        generators = {
            "sys" : [
                main_generator(dut, mem),
                mem.write_generator(dut.write_port),
                mem.read_generator(dut.read_port)
            ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks, vcd_name="sim.vcd")
