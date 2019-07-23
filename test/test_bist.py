# This file is Copyright (c) 2016-2018 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2016 Tim 'mithro' Ansell <mithro@mithis.com>
# License: BSD

import unittest
import random

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import *
from litedram.frontend.bist import *
from litedram.frontend.bist import _LiteDRAMBISTGenerator
from litedram.frontend.bist import _LiteDRAMBISTChecker

from test.common import *

from litex.gen.sim import *


class GenCheckDriver:
    def __init__(self, module):
        self.module = module

    def reset(self):
        yield self.module.reset.eq(1)
        yield
        yield self.module.reset.eq(0)
        yield

    def run(self, base, length):
        yield self.module.base.eq(base)
        yield self.module.length.eq(length)
        yield self.module.start.eq(1)
        yield
        yield self.module.start.eq(0)
        yield
        while((yield self.module.done) == 0):
            yield
        if hasattr(self.module, "errors"):
            self.errors = (yield self.module.errors)


class TestBIST(unittest.TestCase):
    def test_generator(self):
        port = LiteDRAMNativeWritePort(address_width=32, data_width=32)

        def main_generator(dut):
            self.errors = 0

            # test incr
            yield dut.ce.eq(1)
            yield dut.random_enable.eq(0)
            yield
            for i in range(1024):
                data = (yield dut.o)
                if data != i:
                    self.errors += 1
                yield

            # test random
            datas = []
            yield dut.ce.eq(1)
            yield dut.random_enable.eq(1)
            for i in range(1024):
                data = (yield dut.o)
                if data in datas:
                    self.errors += 1
                datas.append(data)
                yield

        # dut
        dut = Generator(23, n_state=23, taps=[17, 22])

         # simulation
        generators = [main_generator(dut)]
        run_simulation(dut, main_generator(dut))
        self.assertEqual(self.errors, 0)

    def test_bist(self):
        class DUT(Module):
            def __init__(self):
                self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
                self.read_port = LiteDRAMNativeReadPort(address_width=32, data_width=32)
                self.submodules.generator = _LiteDRAMBISTGenerator(self.write_port)
                self.submodules.checker = _LiteDRAMBISTChecker(self.read_port)

        def main_generator(dut, mem):
            generator = GenCheckDriver(dut.generator)
            checker = GenCheckDriver(dut.checker)

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
            assert checker.errors != 0

            # read (no errors)
            yield from checker.reset()
            yield from checker.run(16 + 60, 64)
            assert checker.errors == 0

        # dut
        dut = DUT()
        mem = DRAMMemory(32, 128)

        # simulation
        generators = [
            main_generator(dut, mem),
            mem.write_handler(dut.write_port),
            mem.read_handler(dut.read_port)
         ]
        run_simulation(dut, generators)
