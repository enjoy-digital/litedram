#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""DFI phase/edge packing, receive reconstruction and mask polarity."""

import random
import unittest

from migen.sim import run_simulation
from litedram.phy.dfi import Interface
from litedram.phy.usnative.data import NativeDataPacking


class TestUSNativeData(unittest.TestCase):
    def test_edge_and_lane_order(self):
        for width in (16, 32, 64):
            dfi = Interface(17, 3, 1, 2 * width, 4)
            dut = NativeDataPacking(dfi, databits=width)
            rng = random.Random(width)
            def check():
                for _ in range(20):
                    words = [rng.getrandbits(width) for _ in range(8)]
                    received = [rng.getrandbits(width) for _ in range(8)]
                    masks = [rng.getrandbits(width // 8) for _ in range(8)]
                    for p, phase in enumerate(dfi.phases):
                        yield phase.wrdata.eq(words[2*p] | (words[2*p+1] << width))
                        yield phase.wrdata_mask.eq(masks[2*p] | (masks[2*p+1] << (width//8)))
                    for bit in range(width):
                        yield dut.rx_dq[bit].eq(sum(((word >> bit) & 1) << edge
                                                  for edge, word in enumerate(received)))
                    yield
                    yield
                    for edge in range(8):
                        reconstructed = 0
                        for bit in range(width):
                            reconstructed |= (((yield dut.tx_dq[bit]) >> edge) & 1) << bit
                        self.assertEqual(reconstructed, words[edge])
                        for bit in range(width//8):
                            self.assertEqual(((yield dut.tx_dm_n[bit]) >> edge) & 1,
                                             1 ^ ((masks[edge] >> bit) & 1))
                    for p, phase in enumerate(dfi.phases):
                        self.assertEqual((yield phase.rddata), received[2*p] | (received[2*p+1] << width))
            run_simulation(dut, check())

    def test_invalid_ratio_and_width(self):
        for width, phases, databits in ((32, 2, 16), (32, 4, 32), (32, 4, 0), (32, 4, True)):
            with self.assertRaises(ValueError):
                NativeDataPacking(Interface(17, 3, 1, width, phases), databits=databits)
