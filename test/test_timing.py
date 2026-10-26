#
# This file is part of LiteDRAM.
#
# Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

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
        valids = "__-______"
        readys = "_--------"
        self.txxd_controller_test(txxd, valids, readys)

        txxd = 2
        valids = "__-______"
        readys = "_--_-----"
        self.txxd_controller_test(txxd, valids, readys)

        txxd = 3
        valids = "____-______"
        readys = "___--__----"
        self.txxd_controller_test(txxd, valids, readys)

        txxd = 4
        valids = "____-______"
        readys = "___--___---"
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
        for txxd in range(2, 32):
            with self.subTest(txxd=txxd):
                self.txxd_controller_random_test(txxd, 512)


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
        # ready is low exactly while 4 ACTIVATEs were issued in the last tfaw-1 cycles.
        tfaw = 8
        valids = "_----___________"
        readys = "-----____-------"
        with self.subTest(tfaw=tfaw, valids=valids, readys=readys):
            self.tfaw_controller_test(tfaw, valids, readys)

        tfaw = 8
        valids = "_-_-_-_-________"
        readys = "--------_-------"
        with self.subTest(tfaw=tfaw, valids=valids, readys=readys):
            self.tfaw_controller_test(tfaw, valids, readys)

        tfaw = 8
        valids = "_-_-___-_-______"
        readys = "----------------"
        with self.subTest(tfaw=tfaw, valids=valids, readys=readys):
            self.tfaw_controller_test(tfaw, valids, readys)

        tfaw = 8
        valids = "_-_-____-_-______"
        readys = "-----------------"
        with self.subTest(tfaw=tfaw, valids=valids, readys=readys):
            self.tfaw_controller_test(tfaw, valids, readys)

    def test_tfaw_controller_exact_spacing(self):
        # With a same-cycle valid/ready handshake (as in the multiplexer) and continuous requests,
        # the 5th ACTIVATE is accepted exactly tfaw cycles after the 1st, never earlier.
        class DUT(Module):
            def __init__(self, tfaw):
                self.submodules.tfawcon = tFAWController(tfaw)
                self.want = Signal()
                self.comb += self.tfawcon.valid.eq(self.tfawcon.ready & self.want)

        for tfaw in [2, 4, 5, 6, 8, 9, 12]:
            with self.subTest(tfaw=tfaw):
                dut = DUT(tfaw)
                accepted = []

                def generator(dut):
                    yield dut.want.eq(1)
                    yield
                    for cycle in range(64):
                        if (yield dut.tfawcon.valid):
                            accepted.append(cycle)
                        yield

                run_simulation(dut, generator(dut))
                for i in range(len(accepted) - 4):
                    self.assertEqual(accepted[i + 4] - accepted[i], max(tfaw, 4))
