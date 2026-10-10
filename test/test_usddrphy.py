#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Paulo Dalla Santa <paulo@dspro.com.br>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.fhdl.specials import Instance

from litedram.phy.usddrphy import USDDRPHY, USPDDRPHY


class TestUSDDRPHYHPIOVREF(unittest.TestCase):
    @staticmethod
    def get_pads(nbytes=2, x4=False):
        ndqs = nbytes*(2 if x4 else 1)
        return Record([
            ("a",      17),
            ("ba",      2),
            ("bg",      2),
            ("ras_n",   1),
            ("cas_n",   1),
            ("we_n",    1),
            ("cs_n",    1),
            ("act_n",   1),
            ("clk_p",   1),
            ("clk_n",   1),
            ("cke",     1),
            ("odt",     1),
            ("reset_n", 1),
            ("dq",      8*nbytes),
            ("dm",      nbytes),
            ("dqs_p",   ndqs),
            ("dqs_n",   ndqs),
        ])

    @staticmethod
    def get_phy(cls=USPDDRPHY, memtype="DDR4", nbytes=2, x4=False, **kwargs):
        return cls(TestUSDDRPHYHPIOVREF.get_pads(nbytes, x4),
            memtype          = memtype,
            sys_clk_freq     = 125e6,
            iodelay_clk_freq = 400e6,
            **kwargs)

    @staticmethod
    def count_instances(phy, names=("IOBUF", "IOBUFE3", "HPIO_VREF")):
        # get_fragment() can only be called once per module.
        specials = phy.get_fragment().specials
        return {name: sum(isinstance(s, Instance) and s.of == name for s in specials)
            for name in names}

    def test_default_unchanged(self):
        phy = self.get_phy()
        self.assertFalse(hasattr(phy, "_rdly_vref"))
        self.assertEqual(self.count_instances(phy), {"IOBUF": 16, "IOBUFE3": 0, "HPIO_VREF": 0})

    def test_hpio_vref(self):
        for nbytes in [1, 2, 8, 9]:
            for tune in [0, 31, 72]:
                with self.subTest(nbytes=nbytes, tune=tune):
                    phy = self.get_phy(nbytes=nbytes, with_hpio_vref=True, hpio_vref_tune=tune)
                    storage = phy._rdly_vref.storage
                    self.assertEqual(len(storage), 7*nbytes)
                    for i in range(nbytes):
                        self.assertEqual((storage.reset.value >> (7*i)) & 0x7f, tune)
                    self.assertEqual(self.count_instances(phy),
                        {"IOBUF": 0, "IOBUFE3": 8*nbytes, "HPIO_VREF": nbytes})

    @staticmethod
    def items(inst):
        return {it.name: it.value if isinstance(it, Instance.Parameter) else it.expr
            for it in inst.items}

    def test_hpio_vref_wiring(self):
        nbytes   = 2
        phy      = self.get_phy(nbytes=nbytes, with_hpio_vref=True)
        storage  = phy._rdly_vref.storage
        insts    = [s for s in phy.get_fragment().specials if isinstance(s, Instance)]
        iobufs   = [self.items(i) for i in insts if i.of == "IOBUFE3"]
        vrefs    = [self.items(i) for i in insts if i.of == "HPIO_VREF"]
        # Each HPIO_VREF uses the POD range and reads its byte's 7 bits of rdly_vref.
        byte_vref = {}
        for v in vrefs:
            tune = v["FABRIC_VREF_TUNE"]
            self.assertEqual(v["VREF_CNTR"], "FABRIC_RANGE1")
            self.assertIs(tune.value, storage)
            self.assertEqual(tune.stop - tune.start, 7)
            byte_vref[tune.start//7] = v["VREF"]
        self.assertEqual(sorted(byte_vref), list(range(nbytes)))
        # Each DQ IOBUFE3 takes its VREF from the HPIO_VREF of its own byte.
        for b in iobufs:
            self.assertEqual(b["SIM_DEVICE"], "ULTRASCALE_PLUS")
            self.assertIs(b["VREF"], byte_vref[b["IO"].start//8])

    def test_hpio_vref_csr_order(self):
        # rdly_vref is appended after the existing CSRs so their offsets do not change.
        default = [csr.name for csr in self.get_phy().get_csrs()]
        vref    = [csr.name for csr in self.get_phy(with_hpio_vref=True).get_csrs()]
        self.assertEqual(vref, default + ["rdly_vref"])

    def test_hpio_vref_invalid(self):
        for kwargs in [
            dict(cls=USDDRPHY),                  # UltraScale+ only.
            dict(memtype="DDR3"),                # DDR4 (POD12) only.
            dict(x4=True),                       # x4 DIMMs not supported.
            dict(hpio_vref_tune=-1),
            dict(hpio_vref_tune=73),
        ]:
            with self.subTest(**{k: str(v) for k, v in kwargs.items()}):
                with self.assertRaises(AssertionError):
                    self.get_phy(with_hpio_vref=True, **kwargs)
