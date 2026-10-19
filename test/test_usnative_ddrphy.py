#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import Signal
from migen.sim import run_simulation

from litedram.phy.usnative.ddrphy import NativeRXBitslip


class TestNativeRXBitslip(unittest.TestCase):
    def test_rotates_each_captured_burst_without_joining_words(self):
        data, reset, slip = Signal(8), Signal(), Signal()
        dut = NativeRXBitslip(data, reset, slip)

        def stimulus():
            yield reset.eq(1)
            yield
            yield
            yield reset.eq(0)
            for rotation in range(8):
                # Alternating bursts expose any accidental use of the preceding
                # FIFO word, including at the wraparound boundary.
                for value in (0x96, 0x31, 0xE8):
                    yield data.eq(value)
                    yield
                    yield
                    expected = ((value >> rotation) |
                                (value << (8 - rotation))) & 0xff
                    self.assertEqual((yield dut.o), expected)
                yield slip.eq(1)
                yield
                yield slip.eq(0)
                yield
            yield data.eq(0x53)
            yield
            yield
            self.assertEqual((yield dut.o), 0x53)
            yield slip.eq(1)
            yield reset.eq(1)  # Reset takes priority over a simultaneous slip.
            yield
            yield
            self.assertEqual((yield dut.o), 0x53)

        run_simulation(dut, stimulus())
