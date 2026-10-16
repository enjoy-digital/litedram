#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import random
import unittest

from migen import *

from litedram.core.ecc import LiteDRAMDFIECC, ecc_phy_settings, ECC_LATENCY


class TestDFIECC(unittest.TestCase):
    def run_loopback(self, flips, enable=1, n=64, seed=0):
        """Write random 64-bit beats on every phase, loop the PHY-side write data back as read
        data with `flips(beat_index) -> [bit, ...]` raw bits inverted, check the decoded data."""
        rng   = random.Random(seed)
        nph   = 4
        dut   = LiteDRAMDFIECC(addressbits=15, bankbits=3, nranks=1, phy_dfi_databits=144, nphases=nph)
        sent  = []
        got   = []

        def loopback():
            # PHY side: read data = write data (+ flips), valid when written.
            k = 0
            for _ in range(n + 8):
                for i, (s, m) in enumerate(zip(dut.slave.phases, dut.master.phases)):
                    raw = (yield m.wrdata)
                    for b in flips(k):
                        raw ^= 1 << b
                    yield m.rddata.eq(raw)
                    yield m.rddata_valid.eq((yield s.wrdata_en))
                    k += 1
                yield

        def stim():
            yield dut.enable.storage.eq(enable)
            for t in range(n):
                for s in dut.slave.phases:
                    data = rng.getrandbits(128)
                    sent.append(data)
                    yield s.wrdata.eq(data)
                    yield s.wrdata_en.eq(1)
                yield
            for s in dut.slave.phases:
                yield s.wrdata_en.eq(0)
            for _ in range(8):
                yield

        def check():
            for _ in range(n + 8):
                for s in dut.slave.phases:
                    if (yield s.rddata_valid):
                        got.append((yield s.rddata))
                yield

        run_simulation(dut, [stim(), loopback(), check()])
        return sent, got, dut

    def test_clean(self):
        sent, got, _ = self.run_loopback(lambda k: [])
        self.assertEqual(got[:len(sent)], sent)

    def test_single_bit_corrected(self):
        # One flipped bit per beat (data or ECC lane, both 72-bit beats of the phase).
        sent, got, _ = self.run_loopback(lambda k: [k % 72, 72 + (7*k) % 72])
        self.assertEqual(got[:len(sent)], sent)

    def test_single_bit_not_corrected_when_disabled(self):
        sent, got, _ = self.run_loopback(lambda k: [k % 64], enable=0)
        self.assertNotEqual(got[:len(sent)], sent)

    def test_double_bit_detected(self):
        sent, got, _ = self.run_loopback(lambda k: [3, 17])
        self.assertNotEqual(got[:len(sent)], sent)

    def test_settings(self):
        class S: pass
        s = S()
        s.databits, s.dfi_databits, s.read_latency = 72, 144, 7
        e = ecc_phy_settings(s)
        self.assertEqual((e.databits, e.dfi_databits, e.read_latency), (64, 128, 7 + ECC_LATENCY))
        self.assertEqual((e.ecc_databits, e.ecc_dfi_databits), (72, 144))


if __name__ == "__main__":
    unittest.main()
