import unittest
import random

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMWritePort, LiteDRAMReadPort
from litedram.frontend.bist import _LiteDRAMBISTGenerator
from litedram.frontend.bist import _LiteDRAMBISTChecker

from test.common import *


class DUT(Module):
    def __init__(self):
        self.write_port = LiteDRAMWritePort(aw=32, dw=32)
        self.read_port = LiteDRAMReadPort(aw=32, dw=32)
        self.submodules.generator = _LiteDRAMBISTGenerator(self.write_port, True)
        self.submodules.checker = _LiteDRAMBISTChecker(self.read_port, True)


def main_generator(dut, mem):
    generator = BISTDriver(dut.generator)
    checker = BISTDriver(dut.checker)

    # write
    yield from generator.reset()
    yield from generator.run(16, 64)

    # read (no errors)
    yield from checker.reset()
    yield from checker.run(16, 64)
    assert checker.errors == 0

    # corrupt memory (using generator)
    yield from generator.reset()
    yield from generator.run(16 + 60, 64)

    # read (4 errors)
    yield from checker.reset()
    yield from checker.run(16, 64)
    assert checker.errors == 4

    # read (no errors)
    yield from checker.reset()
    yield from checker.run(16 + 60, 64)
    assert checker.errors == 0


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
