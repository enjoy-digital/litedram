# This file is Copyright (c) 2016-2018 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2016 Tim 'mithro' Ansell <mithro@mithis.com>
# License: BSD

import unittest
import random

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import *
from litedram.frontend.bist import *
from litedram.frontend.bist import _LiteDRAMBISTGenerator, _LiteDRAMBISTChecker, \
    _LiteDRAMPatternGenerator, _LiteDRAMPatternChecker

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

    def configure(self, base, length, end=None):
        # for non-pattern generators/checkers
        if end is None:
            end = base + 0x100000
        yield self.module.base.eq(base)
        yield self.module.end.eq(end)
        yield self.module.length.eq(length)

    def run(self):
        yield self.module.run.eq(1)
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
        run_simulation(dut, generators)
        self.assertEqual(self.errors, 0)

    def bist_generator_test(self, data_width, base, length, end, mem_depth, init_generator=None):
        end_addr = base + length
        start_word = base // (data_width//8)
        end_word = end_addr // (data_width//8)
        n_words = end_word - start_word

        class DUT(Module):
            def __init__(self):
                self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=data_width)
                self.submodules.generator = _LiteDRAMBISTGenerator(self.write_port)
                self.mem = DRAMMemory(data_width, mem_depth)

        def main_generator(dut):
            generator = GenCheckDriver(dut.generator)

            if init_generator is not None:
                yield from init_generator(dut)

            yield from generator.reset()
            yield from generator.configure(base, length, end=end)
            yield from generator.run()
            yield

        dut = DUT()

        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.write_port),
        ]
        return dut, generators

    def test_bist_generator(self):
        dut, generators = self.bist_generator_test(mem_depth=128, data_width=32, end=128 * 4,
                                                   base=16, length=64)
        run_simulation(dut, generators)

        before = 16 // 4
        mem_expected = [0] * before + list(range(64//4)) + [0] * (128 - 64//4 - before)
        self.assertEqual(dut.mem.mem, mem_expected)

    def test_bist_generator_random_data(self):
        def init(dut):
            yield dut.generator.random_data.eq(1)
            yield

        # fill whole memory
        dut, generators = self.bist_generator_test(mem_depth=128, data_width=32, end=128 * 4,
                                                   base=0, length=128 * 4, init_generator=init)
        run_simulation(dut, generators)

        # only check if there are no duplicates and if data is not a simple sequence
        self.assertEqual(len(set(dut.mem.mem)), len(dut.mem.mem), msg='Duplicate values in memory')
        self.assertNotEqual(dut.mem.mem, list(range(128)), msg='Values are a sequence')

    def test_bist_generator_random_addr(self):  # write whole memory and check if there are no repetitions?
        def init(dut):
            yield dut.generator.random_addr.eq(1)
            yield

        # fill whole memory
        dut, generators = self.bist_generator_test(mem_depth=128, data_width=32, end=128 * 4,
                                                   base=0, length=128 * 4, init_generator=init)
        run_simulation(dut, generators)

        # with random address and address wrapping (generator.end) we _can_ have duplicates
        # we can at least check that the values written are not an ordered sequence
        self.assertNotEqual(dut.mem.mem, list(range(128)), msg='Values are a sequence')

    def test_bist_generator_wraps_addr(self):
        dut, generators = self.bist_generator_test(mem_depth=128, data_width=32,
                                                   base=16, length=96, end=32)
        run_simulation(dut, generators)

        # we restrict address to <16, 32) and write 96 bytes (which results in 96/4=24 words generated)
        # this means that the address should wrap and last 8 generated words should overwrite memory
        # at address <16, 24)
        before = 16 // 4
        mem_expected = [0] * 4 + list(range(16)) + [0] * (128 - 4 - 16)
        mem_expected[4:4+8] = list(range(16, 24))
        self.assertEqual(dut.mem.mem, mem_expected)

    def pattern_generator_test(self, pattern, mem_expected, data_width, mem_depth):
        class DUT(Module):
            def __init__(self, init):
                self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=data_width)
                self.submodules.generator = _LiteDRAMPatternGenerator(self.write_port, init=init)
                self.mem = DRAMMemory(data_width, mem_depth)

        def main_generator(dut):
            generator = GenCheckDriver(dut.generator)

            yield from generator.reset()
            yield from generator.run()
            yield

        dut = DUT(init=pattern)

        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.write_port),
        ]
        run_simulation(dut, generators, vcd_name='/tmp/sim.vcd')

        assert len(mem_expected) == mem_depth
        self.assertEqual(dut.mem.mem, mem_expected)

    def test_pattern_generator_8bit(self):
        pattern = [
            # address, data
            (0x00, 0xaa),
            (0x05, 0xbb),
            (0x02, 0xcc),
            (0x07, 0xdd),
        ]
        expected = [
            # data, address
            0xaa,  # 0x00
            0x00,  # 0x01
            0xcc,  # 0x02
            0x00,  # 0x03
            0x00,  # 0x04
            0xbb,  # 0x05
            0x00,  # 0x06
            0xdd,  # 0x07
        ]
        self.pattern_generator_test(pattern, expected, data_width=8, mem_depth=8)

    def test_pattern_generator_64bit(self):
        pattern = [
            # address, data
            (0x00, 0x0ddf00dbadc0ffee),
            (0x05, 0xabadcafebaadf00d),
            (0x02, 0xcafefeedfeedface),
            (0x07, 0xdeadc0debaadbeef),
        ]
        expected = [
            # data, address
            0x0ddf00dbadc0ffee,  # 0x00
            0x0000000000000000,  # 0x08
            0xcafefeedfeedface,  # 0x10
            0x0000000000000000,  # 0x18
            0x0000000000000000,  # 0x20
            0xabadcafebaadf00d,  # 0x28
            0x0000000000000000,  # 0x30
            0xdeadc0debaadbeef,  # 0x38
        ]
        self.pattern_generator_test(pattern, expected, data_width=64, mem_depth=8)

    def test_pattern_generator_aligned(self):
        pattern = [
            # address, data
            (0x00, 0xabadcafe),
            (0x07, 0xbaadf00d),
            (0x02, 0xcafefeed),
            (0x01, 0xdeadc0de),
        ]
        expected = [
            # data, address
            0xabadcafe,  # 0x00
            0xdeadc0de,  # 0x04
            0xcafefeed,  # 0x08
            0x00000000,  # 0x0c
            0x00000000,  # 0x10
            0x00000000,  # 0x14
            0x00000000,  # 0x18
            0xbaadf00d,  # 0x1c
        ]
        self.pattern_generator_test(pattern, expected, data_width=32, mem_depth=8)

    def test_pattern_generator_not_aligned(self):
        pattern = [
            # address, data
            (0x00, 0xabadcafe),
            (0x07, 0xbaadf00d),
            (0x02, 0xcafefeed),
            (0x01, 0xdeadc0de),
        ]
        expected = [
            # data, address
            0xabadcafe,  # 0x00
            0xdeadc0de,  # 0x04
            0xcafefeed,  # 0x08
            0x00000000,  # 0x0c
            0x00000000,  # 0x10
            0x00000000,  # 0x14
            0x00000000,  # 0x18
            0xbaadf00d,  # 0x1c
        ]
        self.pattern_generator_test(pattern, expected, data_width=32, mem_depth=8)

    def test_pattern_generator_overwriting(self):
        pattern = [
            # address, data
            (0x00, 0xabadcafe),
            (0x07, 0xbaadf00d),
            (0x00, 0xcafefeed),
            (0x07, 0xdeadc0de),
        ]
        expected = [
            # data, address
            0xcafefeed,  # 0x00
            0x00000000,  # 0x04
            0x00000000,  # 0x08
            0x00000000,  # 0x0c
            0x00000000,  # 0x10
            0x00000000,  # 0x14
            0x00000000,  # 0x18
            0xdeadc0de,  # 0x1c
        ]
        self.pattern_generator_test(pattern, expected, data_width=32, mem_depth=8)

    def test_pattern_generator_sequential(self):
        length = 64
        prng = random.Random(42)
        address = [a for a in range(length)]
        data =  prng.choices(range(2**32 - 1), k=length)
        pattern = list(zip(address, data))

        expected = [0x00000000] * 128
        for adr, data in pattern:
            expected[adr] = data

        self.pattern_generator_test(pattern, expected, data_width=32, mem_depth=128)

    def test_pattern_generator_random(self):
        length = 64
        prng = random.Random(42)
        address = [a for a in prng.sample(range(128), k=length)]
        data =  prng.choices(range(2**32 - 1), k=length)
        pattern = list(zip(address, data))

        expected = [0x00000000] * 128
        for adr, data in pattern:
            expected[adr] = data

        self.pattern_generator_test(pattern, expected, data_width=32, mem_depth=128)

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
            yield from generator.configure(16, 64)
            yield from generator.run()

            # read (no errors)
            yield from checker.reset()
            yield from checker.configure(16, 64)
            yield from checker.run()
            assert checker.errors == 0

            # corrupt memory (using generator)
            yield from generator.reset()
            yield from generator.configure(16 + 60, 64)
            yield from generator.run()

            # read (4 errors)
            yield from checker.reset()
            yield from checker.configure(16, 64)
            yield from checker.run()
            assert checker.errors != 0

            # read (no errors)
            yield from checker.reset()
            yield from checker.configure(16 + 60, 64)
            yield from checker.run()
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
