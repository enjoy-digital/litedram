# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import unittest
import random

from migen import *

from litedram.common import tXXDController, tFAWController


def c2bool(c):
    return {"-": 1, "_": 0}[c]


class TestTiming(unittest.TestCase):
    def txxd_controller_test(self, txxd, valids, readys):
        def generator(dut):
            dut.errors = 0
            for valid, ready in zip(valids, readys):
                yield dut.valid.eq(c2bool(valid))
                yield
                if (yield dut.ready) != c2bool(ready):
                    dut.errors += 1

        dut = tXXDController(txxd)
        run_simulation(dut, [generator(dut)])
        self.assertEqual(dut.errors, 0)

    def test_txxd_controller(self):
        txxd = 1
        valids = "_-______"
        readys = "--------"
        self.txxd_controller_test(txxd, valids, readys)

        txxd = 2
        valids = "_-______"
        readys = "--_-----"
        self.txxd_controller_test(txxd, valids, readys)

        txxd = 3
        valids = "_-______"
        readys = "--__----"
        self.txxd_controller_test(txxd, valids, readys)

        txxd = 4
        valids = "_-______"
        readys = "--___---"
        self.txxd_controller_test(txxd, valids, readys)

    def txxd_controller_random_test(self, txxd, loops):
        def generator(dut, valid_rand):
            prng = random.Random(42)
            for l in range(loops):
                while prng.randrange(100) < valid_rand:
                    yield
                yield dut.valid.eq(1)
                yield
                yield dut.valid.eq(0)

        @passive
        def checker(dut):
            dut.ready_gaps = []
            while True:
                while (yield dut.ready) != 0:
                    yield
                ready_gap = 1
                while (yield dut.ready) != 1:
                    ready_gap += 1
                    yield
                dut.ready_gaps.append(ready_gap)

        dut = tXXDController(txxd)
        run_simulation(dut, [generator(dut, valid_rand=90), checker(dut)])
        self.assertEqual(min(dut.ready_gaps), txxd)

    def test_txxd_controller_random(self):
        for i in range(2, 32):
            self.txxd_controller_random_test(i, 512)


    def tfaw_controller_test(self, txxd, valids, readys):
        def generator(dut):
            dut.errors = 0
            for valid, ready in zip(valids, readys):
                yield dut.valid.eq(c2bool(valid))
                yield
                if (yield dut.ready) != c2bool(ready):
                    dut.errors += 1

        dut = tFAWController(txxd)
        run_simulation(dut, [generator(dut)])
        self.assertEqual(dut.errors, 0)

    def test_tfaw_controller(self):
        tfaw = 8
        valids = "_----___________"
        readys = "-----______-----"
        self.tfaw_controller_test(tfaw, valids, readys)

        tfaw = 8
        valids = "_-_-_-_-________"
        readys = "--------___-----"
        self.tfaw_controller_test(tfaw, valids, readys)

        tfaw = 8
        valids = "_-_-___-_-______"
        readys = "----------_-----"
        self.tfaw_controller_test(tfaw, valids, readys)

        tfaw = 8
        valids = "_-_-____-_-______"
        readys = "-----------------"
        self.tfaw_controller_test(tfaw, valids, readys)
