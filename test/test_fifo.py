# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import unittest
import random

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import LiteDRAMNativeWritePort
from litedram.common import LiteDRAMNativeReadPort
from litedram.frontend.fifo import LiteDRAMFIFO

from test.common import *


class FIFODUT(Module):
    def __init__(self):
        # ports
        self.write_port = LiteDRAMNativeWritePort(address_width=32, data_width=32)
        self.read_port  = LiteDRAMNativeReadPort(address_width=32,  data_width=32)

        # fifo
        self.submodules.fifo = LiteDRAMFIFO(
            data_width          = 32,
            depth               = 64,
            base                = 0,
            write_port          = self.write_port,
            read_port           = self.read_port,
            read_threshold      = 8,
            write_threshold     = 64-8
        )

        # memory
        self.memory = DRAMMemory(32, 256)


class TestFIFO(unittest.TestCase):
    def test_fifo(self):
        def generator(dut, valid_random=90):
            prng = random.Random(42)
            for i in range(128 + 8):
                while prng.randrange(100) < valid_random:
                    yield
                yield dut.fifo.sink.valid.eq(1)
                yield dut.fifo.sink.data.eq(i)
                yield
                while (yield dut.fifo.sink.ready) != 1:
                    yield
                yield dut.fifo.sink.valid.eq(0)

        def checker(dut, ready_random=90):
            prng = random.Random(42)
            for i in range(128):
                yield dut.fifo.source.ready.eq(0)
                yield
                while (yield dut.fifo.source.valid) != 1:
                    yield
                while prng.randrange(100) < ready_random:
                    yield
                yield dut.fifo.source.ready.eq(1)
                self.assertEqual((yield dut.fifo.source.data), i)
                yield

        dut = FIFODUT()
        generators = [
            generator(dut),
            checker(dut),
            dut.memory.write_handler(dut.write_port),
            dut.memory.read_handler(dut.read_port)
        ]
        run_simulation(dut, generators)
