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
    def setUp(self):
        # define common test data used for both generator and checker tests
        self.bist_test_data = {
            '8bit': dict(
                base = 2,
                end = 2 + 8,  # (end - base) must be pow of 2
                length = 5,
                #                       2     3     4     5     6     7=2+5
                expected = [0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x00],
            ),
            '32bit': dict(
                base = 0x04,
                end = 0x04 + 8,
                length = 5 * 4,
                expected = [
                    0x00000000, # 0x00
                    0x00000000, # 0x04
                    0x00000001, # 0x08
                    0x00000002, # 0x0c
                    0x00000003, # 0x10
                    0x00000004, # 0x14
                    0x00000000, # 0x18
                    0x00000000, # 0x1c
                ],
            ),
            '64bit': dict(
                base = 0x10,
                end = 0x10 + 8,  # TODO: fix address masking to be consistent
                length = 5 * 8,
                expected = [
                    0x0000000000000000, # 0x00
                    0x0000000000000000, # 0x08
                    0x0000000000000000, # 0x10
                    0x0000000000000001, # 0x18
                    0x0000000000000002, # 0x20
                    0x0000000000000003, # 0x28
                    0x0000000000000004, # 0x30
                    0x0000000000000000, # 0x38
                ],
            ),
            '32bit_masked': dict(
                base = 0x04,
                end = 0x04 + 0x04,
                length = 6 * 4,
                expected = [
                    0x00000000, # 0x00
                    0x00000004, # 0x04
                    0x00000005, # 0x08
                    0x00000002, # 0x0c
                    0x00000003, # 0x10
                    0x00000000, # 0x14
                    0x00000000, # 0x18
                    0x00000000, # 0x1c
                ],
            ),
            '32bit_long_sequential': dict(
                base = 0x04,
                end = 0x04 + 0x04,
                length = 6 * 4,
                expected = [
                    0x00000000, # 0x00
                    0x00000004, # 0x04
                    0x00000005, # 0x08
                    0x00000002, # 0x0c
                    0x00000003, # 0x10
                    0x00000000, # 0x14
                    0x00000000, # 0x18
                    0x00000000, # 0x1c
                ],
            ),
        }
        self.bist_test_data['32bit_long_sequential'] = dict(
            base = 16,
            end = 16 + 128,
            length = 64,
            expected = [0x00000000] * 128
        )
        expected = self.bist_test_data['32bit_long_sequential']['expected']
        expected[16//4:(16 + 64)//4] = list(range(64//4))

        self.pattern_test_data = {
            '8bit': dict(
                pattern = [
                    # address, data
                    (0x00, 0xaa),
                    (0x05, 0xbb),
                    (0x02, 0xcc),
                    (0x07, 0xdd),
                ],
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
                ],
            ),
            '32bit': dict(
                pattern = [
                    # address, data
                    (0x00, 0xabadcafe),
                    (0x07, 0xbaadf00d),
                    (0x02, 0xcafefeed),
                    (0x01, 0xdeadc0de),
                ],
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
                ],
            ),
            '64bit': dict(
                pattern = [
                    # address, data
                    (0x00, 0x0ddf00dbadc0ffee),
                    (0x05, 0xabadcafebaadf00d),
                    (0x02, 0xcafefeedfeedface),
                    (0x07, 0xdeadc0debaadbeef),
                ],
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
                ],
            ),
            '32bit_not_aligned': dict(
                pattern = [
                    # address, data
                    (0x00, 0xabadcafe),
                    (0x07, 0xbaadf00d),
                    (0x02, 0xcafefeed),
                    (0x01, 0xdeadc0de),
                ],
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
                ],
            ),
            '32bit_duplicates': dict(
                pattern = [
                    # address, data
                    (0x00, 0xabadcafe),
                    (0x07, 0xbaadf00d),
                    (0x00, 0xcafefeed),
                    (0x07, 0xdeadc0de),
                ],
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
                ],
            ),
        }

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

    def test_bist_generator_8bit(self):
        data = self.bist_test_data['8bit']
        dut, generators = self.bist_generator_test(
            mem_depth=len(data['expected']), data_width=8,
            base=data['base'], end=data['end'], length=data['length'])
        run_simulation(dut, generators)
        self.assertEqual(dut.mem.mem, data['expected'])

    def test_bist_generator_range_must_be_pow2(self):
        # NOTE:
        # in the current implementation (end - start) must be a power of 2,
        # but it would be better if this restriction didn't hold, this test
        # is here just to notice the change if it happens unintentionally
        # and may be removed if we start supporting arbitrary ranges
        data = self.bist_test_data['8bit']
        dut, generators = self.bist_generator_test(
            mem_depth=len(data['expected']), data_width=8,
            base=data['base'], end=data['end'] + 1, length=data['length'])
        run_simulation(dut, generators)
        self.assertNotEqual(dut.mem.mem, data['expected'])

    def test_bist_generator_32bit(self):
        data = self.bist_test_data['32bit']
        dut, generators = self.bist_generator_test(
            mem_depth=len(data['expected']), data_width=32,
            base=data['base'], end=data['end'], length=data['length'])
        run_simulation(dut, generators)
        self.assertEqual(dut.mem.mem, data['expected'])

    def test_bist_generator_64bit(self):
        data = self.bist_test_data['64bit']
        dut, generators = self.bist_generator_test(
            mem_depth=len(data['expected']), data_width=64,
            base=data['base'], end=data['end'], length=data['length'])
        run_simulation(dut, generators)
        self.assertEqual(dut.mem.mem, data['expected'])

    def test_bist_generator_32bit_address_masked(self):
        data = self.bist_test_data['32bit_masked']
        dut, generators = self.bist_generator_test(
            mem_depth=len(data['expected']), data_width=32,
            base=data['base'], end=data['end'], length=data['length'])
        run_simulation(dut, generators)
        self.assertEqual(dut.mem.mem, data['expected'])

    def test_bist_generator_32bit_long_sequential(self):
        data = self.bist_test_data['32bit_long_sequential']
        dut, generators = self.bist_generator_test(
            mem_depth=len(data['expected']), data_width=32,
            base=data['base'], end=data['end'], length=data['length'])
        run_simulation(dut, generators)
        self.assertEqual(dut.mem.mem, data['expected'])

    def test_bist_generator_address_masked_long(self):
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
        run_simulation(dut, generators)

        assert len(mem_expected) == mem_depth
        self.assertEqual(dut.mem.mem, mem_expected)

    def test_pattern_generator_8bit(self):
        data = self.pattern_test_data['8bit']
        self.pattern_generator_test(data['pattern'], data['expected'], data_width=8, mem_depth=len(data['expected']))

    def test_pattern_generator_64bit(self):
        data = self.pattern_test_data['64bit']
        self.pattern_generator_test(data['pattern'], data['expected'], data_width=64, mem_depth=len(data['expected']))

    def test_pattern_generator_32bit(self):
        data = self.pattern_test_data['32bit']
        self.pattern_generator_test(data['pattern'], data['expected'], data_width=32, mem_depth=len(data['expected']))

    def test_pattern_generator_not_aligned(self):
        data = self.pattern_test_data['32bit_not_aligned']
        self.pattern_generator_test(data['pattern'], data['expected'], data_width=32, mem_depth=len(data['expected']))

    def test_pattern_generator_duplicates(self):
        data = self.pattern_test_data['32bit_duplicates']
        self.pattern_generator_test(data['pattern'], data['expected'], data_width=32, mem_depth=len(data['expected']))

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

    def bist_checker_test(self, memory, data_width, pattern=None, config_args=None, expected_errors=0):
        assert pattern is None or config_args is None, '_LiteDRAMBISTChecker xor _LiteDRAMPatternChecker'

        class DUT(Module):
            def __init__(self):
                self.read_port = LiteDRAMNativeReadPort(address_width=32, data_width=data_width)
                if pattern is not None:
                    self.submodules.checker = _LiteDRAMPatternChecker(self.read_port, init=pattern)
                else:
                    self.submodules.checker = _LiteDRAMBISTChecker(self.read_port)
                self.mem = DRAMMemory(data_width, len(memory), init=memory)

        def main_generator(dut):

            yield from dut.reset()
            if pattern is None:
                yield from dut.configure(**config_args)
            yield from dut.run()
            yield

        dut = DUT()
        checker = GenCheckDriver(dut.checker)

        generators = [
            main_generator(checker),
            dut.mem.read_handler(dut.read_port),
        ]
        run_simulation(dut, generators, vcd_name='/tmp/sim.vcd')
        self.assertEqual(checker.errors, expected_errors)


    def test_bist_checker_8bit(self):
        data = self.bist_test_data['8bit']
        memory = data.pop('expected')
        self.bist_checker_test(memory, data_width=8, config_args=data)

    def test_bist_checker_32bit(self):
        data = self.bist_test_data['32bit']
        memory = data.pop('expected')
        self.bist_checker_test(memory, data_width=32, config_args=data)

    def test_bist_checker_64bit(self):
        data = self.bist_test_data['32bit']
        memory = data.pop('expected')
        self.bist_checker_test(memory, data_width=32, config_args=data)

    def test_pattern_checker_8bit(self):
        data = self.pattern_test_data['8bit']
        self.bist_checker_test(memory=data['expected'], data_width=8, pattern=data['pattern'])

    def test_pattern_checker_32bit(self):
        data = self.pattern_test_data['32bit']
        self.bist_checker_test(memory=data['expected'], data_width=32, pattern=data['pattern'])

    def test_pattern_checker_64bit(self):
        data = self.pattern_test_data['64bit']
        self.bist_checker_test(memory=data['expected'], data_width=64, pattern=data['pattern'])

    def test_pattern_checker_32bit_not_aligned(self):
        data = self.pattern_test_data['32bit_not_aligned']
        self.bist_checker_test(memory=data['expected'], data_width=32, pattern=data['pattern'])

    def test_pattern_checker_32bit_duplicates(self):
        data = self.pattern_test_data['32bit_duplicates']
        num_duplicates = len(data['pattern']) - len(set(adr for adr, _ in data['pattern']))
        self.bist_checker_test(memory=data['expected'], data_width=32, pattern=data['pattern'],
                               expected_errors=num_duplicates)

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
