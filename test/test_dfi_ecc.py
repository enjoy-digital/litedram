#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import random
import unittest

from migen import *

from litedram.core.ecc import LiteDRAMDFIECC, ecc_phy_settings, ECC_LATENCY

# The ECC is per phase and per 72-bit beat within a phase (2 beats on a 144-bit DFI phase): a
# single phase covers the mechanism, including the beat interleaving, and keeps the simulation
# short. The 4-phase configuration (DDR3/DDR4 PHYs) runs the same checks on every phase and is
# only enabled with LITEDRAM_TEST_FULL=1.
LITEDRAM_TEST_FULL = os.environ.get("LITEDRAM_TEST_FULL", "0") == "1"


class TestDFIECC(unittest.TestCase):
    nphases = 1

    def run_loopback(self, flips, enable=1, n=72, seed=0, read_bits=()):
        """Write random 128-bit phase data (2 beats of 64 bits) on every phase for `n` cycles,
        loop the PHY-side write data back as read data with `flips(beat_index) -> [bit, ...]`
        raw bits inverted (0-143 of the phase: beat 0 on 0-71, beat 1 on 72-143), check the
        decoded data. `n` is at least 72 so that every bit position of a phase is reached by
        the flips of the single-phase configuration."""
        rng   = random.Random(seed)
        nph   = self.nphases
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

        cnts = {}
        def read_counters():
            for _ in range(n + 12):
                yield
            for i in read_bits:
                yield dut.bitsel.storage.eq(i)
                yield; yield; yield
                cnts[i] = (yield dut.bitcnt.status)

        run_simulation(dut, [stim(), loopback(), check(), read_counters()])
        return (sent, got, dut, cnts) if read_bits else (sent, got, dut)

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

    def test_bit_stats(self):
        # One flipped DQ (bit 21) on every beat: its counter counts, its neighbours stay at 0.
        sent, got, _, cnts = self.run_loopback(lambda k: [21], n=16, read_bits=[20, 21, 22])
        self.assertEqual(got[:len(sent)], sent)
        self.assertEqual(cnts[20], 0)
        self.assertGreater(cnts[21], 0)
        self.assertEqual(cnts[22], 0)

    def test_bit_stats_option(self):
        # with_bit_stats builds the per-DQ counters and their CSRs (bitsel/bitcnt), nothing else.
        def csr_names(with_bit_stats):
            dut = LiteDRAMDFIECC(addressbits=15, bankbits=3, nranks=1, phy_dfi_databits=144, nphases=4,
                with_bit_stats=with_bit_stats)
            return {csr.name for csr in dut.get_csrs()}
        self.assertEqual(csr_names(True),  {"enable", "clear", "sec", "ded", "bitsel", "bitcnt"})
        self.assertEqual(csr_names(False), {"enable", "clear", "sec", "ded"})

    def test_core_option(self):
        # LiteDRAMCore(with_ecc=True) builds the per-DQ counters only with with_ecc_bit_stats (off by
        # default); the option is accepted (and ignored) without the ECC.
        from litedram.core import LiteDRAMCore
        from litedram.modules import MT41K128M16
        from litedram.phy import dfi
        from litedram.phy.model import get_sdram_phy_settings

        module = MT41K128M16(100e6, "1:4")

        class PHY: # What LiteDRAMCore uses of a PHY: its settings and DFI (72-bit DDR3 channel, 1:4).
            def __init__(self):
                self.settings = get_sdram_phy_settings("DDR3", 72, 100e6)
                self.dfi      = dfi.Interface(module.geom_settings.addressbits, module.geom_settings.bankbits,
                    self.settings.nranks, self.settings.dfi_databits, self.settings.nphases)

        def core(**kwargs):
            return LiteDRAMCore(PHY(), module.geom_settings, module.timing_settings, 100e6, **kwargs)

        def ecc_csrs(**kwargs):
            return {csr.name for csr in core(with_ecc=True, **kwargs).ecc.get_csrs()}

        self.assertNotIn("bitsel", ecc_csrs())
        self.assertNotIn("bitsel", ecc_csrs(with_ecc_bit_stats=False))
        self.assertIn("bitsel",    ecc_csrs(with_ecc_bit_stats=True))
        self.assertFalse(hasattr(core(with_ecc_bit_stats=True), "ecc"))

    def test_double_bit_detected(self):
        sent, got, _ = self.run_loopback(lambda k: [3, 17])
        self.assertNotEqual(got[:len(sent)], sent)


@unittest.skipUnless(LITEDRAM_TEST_FULL, "4-phase DFI ECC configuration, set LITEDRAM_TEST_FULL=1 to run it")
class TestDFIECC4Phases(TestDFIECC):
    # Same checks on a 4-phase DFI (DDR3/DDR4 PHYs): the flips walk the phases, each phase gets
    # a bit position every 4 beats.
    nphases = 4


class TestDFIECCSettings(unittest.TestCase):
    def test_settings(self):
        class S: pass
        s = S()
        s.databits, s.dfi_databits, s.read_latency = 72, 144, 7
        e = ecc_phy_settings(s)
        self.assertEqual((e.databits, e.dfi_databits, e.read_latency), (64, 128, 7 + ECC_LATENCY))
        self.assertEqual((e.ecc_databits, e.ecc_dfi_databits), (72, 144))


if __name__ == "__main__":
    unittest.main()
