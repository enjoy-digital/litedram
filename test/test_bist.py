# This file is Copyright (c) 2016-2018 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2016 Tim 'mithro' Ansell <mithro@mithis.com>
# License: BSD

import unittest

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

    def configure(self, base, length, end=None, random_addr=None, random_data=None):
        # for non-pattern generators/checkers
        if end is None:
            end = base + 0x100000
        yield self.module.base.eq(base)
        yield self.module.end.eq(end)
        yield self.module.length.eq(length)
        if random_addr is not None:
            yield self.module.random_addr.eq(random_addr)
        if random_data is not None:
            yield self.module.random_data.eq(random_data)

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


class GenCheckCSRDriver:
    def __init__(self, module):
        self.module = module

    def reset(self):
        yield from self.module.reset.write(1)
        yield from self.module.reset.write(0)

    def configure(self, base, length, end=None, random_addr=None, random_data=None):
        # for non-pattern generators/checkers
        if end is None:
            end = base + 0x100000
        yield from self.module.base.write(base)
        yield from self.module.end.write(end)
        yield from self.module.length.write(length)
        if random_addr is not None:
            yield from self.module.random.addr.write(random_addr)
        if random_data is not None:
            yield from self.module.random.data.write(random_data)

    def run(self):
        yield from self.module.run.write(1)
        yield from self.module.start.write(1)
        yield
        yield from self.module.start.write(0)
        yield
        while((yield from self.module.done.read()) == 0):
            yield
        if hasattr(self.module, "errors"):
            self.errors = (yield from self.module.errors.read())


class DMAWriterDriver:
    def __init__(self, dma):
        self.dma = dma

    def write(self, pattern):
        yield self.dma.sink.valid.eq(1)
        for adr, data in pattern:
            yield self.dma.sink.address.eq(adr)
            yield self.dma.sink.data.eq(data)
            while not (yield self.dma.sink.ready):
                yield
            while (yield self.dma.sink.ready):
                yield
        yield self.dma.sink.valid.eq(0)

    @staticmethod
    def wait_complete(port, n):
        for _ in range(n):
            while not (yield port.wdata.ready):
                yield
            while (yield port.wdata.ready):
                yield


class TestBIST(unittest.TestCase):
    def setUp(self):
        # define common test data used for both generator and checker tests
        self.bist_test_data = {
            "8bit": dict(
                base = 2,
                end = 2 + 8,  # (end - base) must be pow of 2
                length = 5,
                #                       2     3     4     5     6     7=2+5
                expected = [0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x00],
            ),
            "32bit": dict(
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
            "64bit": dict(
                base = 0x10,
                end = 0x10 + 8,
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
            "32bit_masked": dict(
                base = 0x04,
                end = 0x04 + 0x04,  # TODO: fix address masking to be consistent
                length = 6 * 4,
                expected = [  # due to masking
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
        self.bist_test_data["32bit_long_sequential"] = dict(
            base = 16,
            end = 16 + 128,
            length = 64,
            expected = [0x00000000] * 128
        )
        expected = self.bist_test_data["32bit_long_sequential"]["expected"]
        expected[16//4:(16 + 64)//4] = list(range(64//4))

        self.pattern_test_data = {
            "8bit": dict(
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
            "32bit": dict(
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
            "64bit": dict(
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
            "32bit_not_aligned": dict(
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
            "32bit_duplicates": dict(
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
            "32bit_sequential": dict(
                pattern = [
                    # address, data
                    (0x02, 0xabadcafe),
                    (0x03, 0xbaadf00d),
                    (0x04, 0xcafefeed),
                    (0x05, 0xdeadc0de),
                ],
                expected = [
                    # data, address
                    0x00000000,  # 0x00
                    0x00000000,  # 0x04
                    0xabadcafe,  # 0x08
                    0xbaadf00d,  # 0x0c
                    0xcafefeed,  # 0x10
                    0xdeadc0de,  # 0x14
                    0x00000000,  # 0x18
                    0x00000000,  # 0x1c
                ],
            ),
            "32bit_long_sequential": dict(pattern=[], expected=[0] * 64),
        }
        for i in range(32):
            data = self.pattern_test_data["32bit_long_sequential"]
            data['pattern'].append((i, 64 + i))
            data['expected'][i] = 64 + i

    def test_generator(self):
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

    def generator_test(self, mem_expected, data_width, pattern=None, config_args=None, check_mem=True):
        assert pattern is None or config_args is None, "_LiteDRAMBISTGenerator xor _LiteDRAMPatternGenerator"

        class DUT(Module):
            def __init__(self):
                self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=data_width)
                if pattern is not None:
                    self.submodules.generator = _LiteDRAMPatternGenerator(self.write_port, init=pattern)
                else:
                    self.submodules.generator = _LiteDRAMBISTGenerator(self.write_port)
                self.mem = DRAMMemory(data_width, len(mem_expected))

        def main_generator(driver):
            yield from driver.reset()
            if pattern is None:
                yield from driver.configure(**config_args)
            yield from driver.run()
            yield

        dut = DUT()
        generators = [
            main_generator(GenCheckDriver(dut.generator)),
            dut.mem.write_handler(dut.write_port),
        ]
        run_simulation(dut, generators)
        if check_mem:
            self.assertEqual(dut.mem.mem, mem_expected)
        return dut

    def test_bist_generator_8bit(self):
        data = self.bist_test_data["8bit"]
        self.generator_test(data.pop("expected"), data_width=8, config_args=data)

    def test_bist_generator_range_must_be_pow2(self):
        # NOTE:
        # in the current implementation (end - start) must be a power of 2,
        # but it would be better if this restriction didn't hold, this test
        # is here just to notice the change if it happens unintentionally
        # and may be removed if we start supporting arbitrary ranges
        data = self.bist_test_data["8bit"]
        data["end"] += 1
        reference = data.pop("expected")
        dut = self.generator_test(reference, data_width=8, config_args=data, check_mem=False)
        self.assertNotEqual(dut.mem.mem, reference)

    def test_bist_generator_32bit(self):
        data = self.bist_test_data["32bit"]
        self.generator_test(data.pop("expected"), data_width=32, config_args=data)

    def test_bist_generator_64bit(self):
        data = self.bist_test_data["64bit"]
        self.generator_test(data.pop("expected"), data_width=64, config_args=data)

    def test_bist_generator_32bit_address_masked(self):
        data = self.bist_test_data["32bit_masked"]
        self.generator_test(data.pop("expected"), data_width=32, config_args=data)

    def test_bist_generator_32bit_long_sequential(self):
        data = self.bist_test_data["32bit_long_sequential"]
        self.generator_test(data.pop("expected"), data_width=32, config_args=data)

    def test_bist_generator_random_data(self):
        data = self.bist_test_data["32bit"]
        data["random_data"] = True
        dut = self.generator_test(data.pop("expected"), data_width=32, config_args=data, check_mem=False)
        # only check that there are no duplicates and that data is not a simple sequence
        mem = [val for val in dut.mem.mem if val != 0]
        self.assertEqual(len(set(mem)), len(mem), msg="Duplicate values in memory")
        self.assertNotEqual(mem, list(range(len(mem))), msg="Values are a sequence")

    def test_bist_generator_random_addr(self):  # write whole memory and check if there are no repetitions?
        data = self.bist_test_data["32bit"]
        data["random_addr"] = True
        dut = self.generator_test(data.pop("expected"), data_width=32, config_args=data, check_mem=False)
        # with random address and address wrapping (generator.end) we _can_ have duplicates
        # we can at least check that the values written are not an ordered sequence
        mem = [val for val in dut.mem.mem if val != 0]
        self.assertNotEqual(mem, list(range(len(mem))), msg="Values are a sequence")
        self.assertLess(max(mem), data["length"], msg="Too big value found")

    def test_pattern_generator_8bit(self):
        data = self.pattern_test_data["8bit"]
        self.generator_test(data["expected"], data_width=8, pattern=data["pattern"])

    def test_pattern_generator_32bit(self):
        data = self.pattern_test_data["32bit"]
        self.generator_test(data["expected"], data_width=32, pattern=data["pattern"])

    def test_pattern_generator_64bit(self):
        data = self.pattern_test_data["64bit"]
        self.generator_test(data["expected"], data_width=64, pattern=data["pattern"])

    def test_pattern_generator_32bit_not_aligned(self):
        data = self.pattern_test_data["32bit_not_aligned"]
        self.generator_test(data["expected"], data_width=32, pattern=data["pattern"])

    def test_pattern_generator_32bit_duplicates(self):
        data = self.pattern_test_data["32bit_duplicates"]
        self.generator_test(data["expected"], data_width=32, pattern=data["pattern"])

    def test_pattern_generator_32bit_sequential(self):
        data = self.pattern_test_data["32bit_sequential"]
        self.generator_test(data["expected"], data_width=32, pattern=data["pattern"])

    def checker_test(self, memory, data_width, pattern=None, config_args=None, check_errors=False):
        assert pattern is None or config_args is None, "_LiteDRAMBISTChecker xor _LiteDRAMPatternChecker"

        class DUT(Module):
            def __init__(self):
                self.read_port = LiteDRAMNativeReadPort(address_width=32, data_width=data_width)
                if pattern is not None:
                    self.submodules.checker = _LiteDRAMPatternChecker(self.read_port, init=pattern)
                else:
                    self.submodules.checker = _LiteDRAMBISTChecker(self.read_port)
                self.mem = DRAMMemory(data_width, len(memory), init=memory)

        def main_generator(driver):
            yield from driver.reset()
            if pattern is None:
                yield from driver.configure(**config_args)
            yield from driver.run()
            yield

        dut = DUT()
        checker = GenCheckDriver(dut.checker)
        generators = [
            main_generator(checker),
            dut.mem.read_handler(dut.read_port),
        ]
        run_simulation(dut, generators)
        if check_errors:
            self.assertEqual(checker.errors, 0)
        return dut, checker

    def test_bist_checker_8bit(self):
        data = self.bist_test_data["8bit"]
        memory = data.pop("expected")
        self.checker_test(memory, data_width=8, config_args=data)

    def test_bist_checker_32bit(self):
        data = self.bist_test_data["32bit"]
        memory = data.pop("expected")
        self.checker_test(memory, data_width=32, config_args=data)

    def test_bist_checker_64bit(self):
        data = self.bist_test_data["32bit"]
        memory = data.pop("expected")
        self.checker_test(memory, data_width=32, config_args=data)

    def test_pattern_checker_8bit(self):
        data = self.pattern_test_data["8bit"]
        self.checker_test(memory=data["expected"], data_width=8, pattern=data["pattern"])

    def test_pattern_checker_32bit(self):
        data = self.pattern_test_data["32bit"]
        self.checker_test(memory=data["expected"], data_width=32, pattern=data["pattern"])

    def test_pattern_checker_64bit(self):
        data = self.pattern_test_data["64bit"]
        self.checker_test(memory=data["expected"], data_width=64, pattern=data["pattern"])

    def test_pattern_checker_32bit_not_aligned(self):
        data = self.pattern_test_data["32bit_not_aligned"]
        self.checker_test(memory=data["expected"], data_width=32, pattern=data["pattern"])

    def test_pattern_checker_32bit_duplicates(self):
        data = self.pattern_test_data["32bit_duplicates"]
        num_duplicates = len(data["pattern"]) - len(set(adr for adr, _ in data["pattern"]))
        dut, checker = self.checker_test(
            memory=data["expected"], data_width=32, pattern=data["pattern"], check_errors=False)
        self.assertEqual(checker.errors, num_duplicates)

    def bist_test(self, generator, checker, mem):
        # write
        yield from generator.reset()
        yield from generator.configure(16, 64)
        yield from generator.run()

        # read (no errors)
        yield from checker.reset()
        yield from checker.configure(16, 64)
        yield from checker.run()
        self.assertEqual(checker.errors, 0)

        # corrupt memory (using generator)
        yield from generator.reset()
        yield from generator.configure(16 + 48, 64)
        yield from generator.run()

        # read (errors)
        yield from checker.reset()
        yield from checker.configure(16, 64)
        yield from checker.run()
        # errors for words:
        # from (16 + 48) / 4 = 16  (corrupting generator start)
        # to   (16 + 64) / 4 = 20  (first generator end)
        self.assertEqual(checker.errors, 4)

        # read (no errors)
        yield from checker.reset()
        yield from checker.configure(16 + 48, 64)
        yield from checker.run()
        self.assertEqual(checker.errors, 0)

    def test_bist_base(self):
        class DUT(Module):
            def __init__(self):
                self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
                self.read_port = LiteDRAMNativeReadPort(address_width=32, data_width=32)
                self.submodules.generator = _LiteDRAMBISTGenerator(self.write_port)
                self.submodules.checker = _LiteDRAMBISTChecker(self.read_port)

        def main_generator(dut, mem):
            generator = GenCheckDriver(dut.generator)
            checker = GenCheckDriver(dut.checker)
            yield from self.bist_test(generator, checker, mem)

        # dut
        dut = DUT()
        mem = DRAMMemory(32, 48)

        # simulation
        generators = [
            main_generator(dut, mem),
            mem.write_handler(dut.write_port),
            mem.read_handler(dut.read_port)
        ]
        run_simulation(dut, generators)

    def test_bist_csr(self):
        class DUT(Module):
            def __init__(self):
                self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
                self.read_port = LiteDRAMNativeReadPort(address_width=32, data_width=32)
                self.submodules.generator = LiteDRAMBISTGenerator(self.write_port)
                self.submodules.checker = LiteDRAMBISTChecker(self.read_port)

        def main_generator(dut, mem):
            generator = GenCheckCSRDriver(dut.generator)
            checker = GenCheckCSRDriver(dut.checker)
            yield from self.bist_test(generator, checker, mem)

        # dut
        dut = DUT()
        mem = DRAMMemory(32, 48)

        # simulation
        generators = [
            main_generator(dut, mem),
            mem.write_handler(dut.write_port),
            mem.read_handler(dut.read_port)
        ]
        run_simulation(dut, generators)

    def test_bist_csr_cdc(self):
        class DUT(Module):
            def __init__(self):
                self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=32, clock_domain="async")
                self.read_port = LiteDRAMNativeReadPort(address_width=32, data_width=32, clock_domain="async")
                self.submodules.generator = LiteDRAMBISTGenerator(self.write_port)
                self.submodules.checker = LiteDRAMBISTChecker(self.read_port)

        def main_generator(dut, mem):
            generator = GenCheckCSRDriver(dut.generator)
            checker = GenCheckCSRDriver(dut.checker)
            yield from self.bist_test(generator, checker, mem)

        # dut
        dut = DUT()
        mem = DRAMMemory(32, 48)

        generators = {
            "sys": [
                main_generator(dut, mem),
            ],
            "async": [
                mem.write_handler(dut.write_port),
                mem.read_handler(dut.read_port)
            ]
        }
        clocks = {
            "sys": 10,
            "async": (7, 3),
        }
        run_simulation(dut, generators, clocks)

    def dma_writer_test_pattern(self, pattern, mem_expected, data_width, **kwargs):
        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativeWritePort(address_width=32, data_width=data_width)
                self.submodules.dma = LiteDRAMDMAWriter(self.port, **kwargs)

        dut = DUT()
        driver = DMAWriterDriver(dut.dma)
        mem = DRAMMemory(data_width, len(mem_expected))

        generators = [
            driver.write(pattern),
            driver.wait_complete(dut.port, len(pattern)),
            mem.write_handler(dut.port),
        ]
        run_simulation(dut, generators)
        self.assertEqual(mem.mem, mem_expected)

    def test_dma_writer_single(self):
        pattern = [(0x04, 0xdeadc0de)]
        mem_expected = [0] * 32
        mem_expected[0x04] = 0xdeadc0de
        self.dma_writer_test_pattern(pattern, mem_expected, data_width=32)

    def test_dma_writer_multiple(self):
        data = self.pattern_test_data["32bit"]
        self.dma_writer_test_pattern(data["pattern"], data["expected"], data_width=32)

    def test_dma_writer_sequential(self):
        data = self.pattern_test_data["32bit_sequential"]
        self.dma_writer_test_pattern(data["pattern"], data["expected"], data_width=32)

    def test_dma_writer_long_sequential(self):
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_writer_test_pattern(data["pattern"], data["expected"], data_width=32)

    def test_dma_writer_no_fifo(self):
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_writer_test_pattern(data["pattern"], data["expected"], data_width=32,
                                     fifo_depth=1)

    def test_dma_writer_fifo_buffered(self):
        data = self.pattern_test_data["32bit_long_sequential"]
        self.dma_writer_test_pattern(data["pattern"], data["expected"], data_width=32,
                                     fifo_buffered=True)

    def test_dma_writer_duplicates(self):
        data = self.pattern_test_data["32bit_duplicates"]
        self.dma_writer_test_pattern(data["pattern"], data["expected"], data_width=32)
