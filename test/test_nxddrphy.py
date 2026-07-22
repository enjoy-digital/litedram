#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.sim import run_simulation

from litedram.phy.nxddrphy import NexusDDRPHY, _NexusDDRPHYWriteBitSlip


class TestNexusDDRPHYWriteBitSlip(unittest.TestCase):
    @staticmethod
    def run_bitslip(dw, inputs, idle=0):
        dut     = _NexusDDRPHYWriteBitSlip(dw)
        outputs = []

        def generator():
            # Fill the history with the inactive value used by the stream.
            yield dut.i.eq(idle)
            yield
            for current in inputs:
                yield dut.i.eq(current)
                yield
                outputs.append((yield dut.o))

        run_simulation(dut, generator())
        return outputs

    def test_half_word_shift(self):
        for dw, inputs in [
            (4, [0b1101, 0b0011, 0b1010, 0b0110]),
            (2, [0b11,   0b00,   0b10,   0b01]),
        ]:
            with self.subTest(dw=dw):
                outputs = self.run_bitslip(dw, inputs)

                half = dw//2
                mask = (1 << half) - 1
                expected = []
                previous = 0
                for current in inputs:
                    expected.append((previous >> half) | ((current & mask) << half))
                    previous = current
                self.assertEqual(outputs, expected)

    def test_one_memory_clock_advance(self):
        streams = [
            # DQS data: idle, preamble, data, data, postamble, idle.
            (4, 0b0000, [0b0000, 0b1000, 0b1010, 0b1010, 0b0000, 0b0000]),
            # DQS tristate: T0 is serialized before T1.
            (2, 0b0011, [0b0011, 0b0001, 0b0000, 0b0000, 0b0010, 0b0011]),
        ]
        for dw, idle, original in streams:
            with self.subTest(dw=dw):
                early   = original[1:] + [idle]
                shifted = self.run_bitslip(dw, early, idle=idle)

                original_bits = [((word >> n) & 1) for word in original for n in range(dw)]
                shifted_bits  = [((word >> n) & 1) for word in shifted  for n in range(dw)]
                half          = dw//2
                idle_bits     = [((idle >> n) & 1) for n in range(half)]
                self.assertEqual(shifted_bits, original_bits[half:] + idle_bits)


class TestNexusDDRPHYSettings(unittest.TestCase):
    @staticmethod
    def get_pads():
        return Record([
            ("a",       14),
            ("ba",       3),
            ("ras_n",    1),
            ("cas_n",    1),
            ("we_n",     1),
            ("clk_p",    1),
            ("dq",       8),
            ("dm",       1),
            ("dqs_p",    1),
        ])

    def test_standard_cwl(self):
        dut = NexusDDRPHY(self.get_pads(), sys_clk_freq=75e6)

        self.assertEqual(dut.settings.cwl, 5)
        self.assertEqual(dut.settings.wrphase, 1)
        self.assertEqual(dut.settings.write_latency, 2)
