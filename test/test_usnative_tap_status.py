#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Tap-status selection and freshness after the documented settling interval."""

import unittest
from migen import *
from migen.sim import run_simulation
from litedram.phy.usnative.tap_status import RegisteredTapStatus

class TapStatusTest(unittest.TestCase):
    def test_small_and_partial_groups(self):
        for entries in (1, 2, 7, 8, 9, 45):
            with self.subTest(entries=entries):
                dut = RegisteredTapStatus(entries)
                def driver():
                    yield dut.source.eq(sum((i+11) << (9*i) for i in range(entries)))
                    yield dut.ready.eq(1)
                    for index in range(entries):
                        yield dut.select.eq(index)
                        yield dut.change.eq(1)
                        yield
                        self.assertEqual((yield dut.valid), 0)
                        yield dut.change.eq(0)
                        for _ in range(36):
                            yield
                        self.assertEqual((yield dut.valid), 1)
                        self.assertEqual((yield dut.value), index+11)
                run_simulation(dut, driver(), clocks={'sys': 10, 'riu': 20})

    def test_invalid_entry_count(self):
        for entries in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                RegisteredTapStatus(entries)

    def test_all_selections_settle_and_reset(self):
        dut = RegisteredTapStatus(105)
        def driver():
            values = [(i*3+1)%512 for i in range(105)]
            yield dut.source.eq(sum(v<<(9*i) for i, v in enumerate(values)))
            yield dut.ready.eq(1)
            for index in range(105):
                yield dut.select.eq(index)
                yield dut.change.eq(1)
                yield
                self.assertEqual((yield dut.valid), 0)
                yield dut.change.eq(0)
                for cycle in range(36):
                    yield
                    if (yield dut.valid):
                        self.assertEqual((yield dut.value), values[index])
                self.assertEqual((yield dut.valid), 1)
            # Count changes after an operation traverse RIU capture and tree.
            yield dut.change.eq(1)
            yield
            yield dut.change.eq(0)
            for _ in range(12):
                yield
            values[-1] = 377
            yield dut.source.eq(sum(v<<(9*i) for i, v in enumerate(values)))
            for _ in range(25):
                yield
            self.assertEqual((yield dut.valid), 1)
            self.assertEqual((yield dut.value), 377)
            yield dut.ready.eq(0)
            yield
            self.assertEqual((yield dut.valid), 0)
        run_simulation(dut, driver(), clocks={'sys':10, 'riu':20})
    def test_group_changes_and_out_of_range_stay_invalid_until_settled(self):
        dut = RegisteredTapStatus(105)
        values = [(i*7+3) % 512 for i in range(105)]
        def driver():
            yield dut.source.eq(sum(value << (9*i) for i, value in enumerate(values)))
            yield dut.ready.eq(1)
            for selected in (7, 8, 63, 64, 104, 105, 127, 0):
                yield dut.select.eq(selected)
                yield dut.change.eq(1)
                yield
                self.assertEqual((yield dut.valid), 0)
                yield dut.change.eq(0)
                for _ in range(36):
                    yield
                    if (yield dut.valid):
                        self.assertEqual((yield dut.value), values[selected] if selected < 105 else 0)
                self.assertEqual((yield dut.valid), 1)
        run_simulation(dut, driver(), clocks={"sys": 10, "riu": 20})

if __name__=='__main__':
    unittest.main()
