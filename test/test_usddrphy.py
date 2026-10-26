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
    def instances(phy):
        # get_fragment() can only be called once per module.
        return [s for s in phy.get_fragment().specials if isinstance(s, Instance)]

    @staticmethod
    def count_instances(insts, names=("IOBUF", "IOBUFE3", "HPIO_VREF")):
        return {name: sum(i.of == name for i in insts) for name in names}

    def test_default_unchanged(self):
        phy = self.get_phy()
        self.assertFalse(hasattr(phy, "_rd_vref"))
        self.assertEqual(self.count_instances(self.instances(phy)),
            {"IOBUF": 16, "IOBUFE3": 0, "HPIO_VREF": 0})

    def test_hpio_vref(self):
        for nbytes in [1, 2, 8, 9]:
            for tune in [0, 31, 72]:
                with self.subTest(nbytes=nbytes, tune=tune):
                    phy = self.get_phy(nbytes=nbytes, with_hpio_vref=True, hpio_vref_tune=tune)
                    storage = phy._rd_vref.storage
                    self.assertEqual(len(storage), 7)
                    self.assertEqual(storage.reset.value, tune)
                    insts = self.instances(phy)
                    self.assertEqual(self.count_instances(insts),
                        {"IOBUF": 0, "IOBUFE3": 8*nbytes, "HPIO_VREF": nbytes})
                    # Each byte has its own 7-bit code, reset to hpio_vref_tune.
                    tunes = [self.items(i)["FABRIC_VREF_TUNE"] for i in insts if i.of == "HPIO_VREF"]
                    self.assertEqual(len(set(map(id, tunes))), nbytes)
                    for t in tunes:
                        self.assertEqual(len(t), 7)
                        self.assertEqual(t.reset.value, tune)

    @staticmethod
    def items(inst):
        return {it.name: it.value if isinstance(it, Instance.Parameter) else it.expr
            for it in inst.items}

    def test_hpio_vref_wiring(self):
        nbytes   = 2
        phy      = self.get_phy(nbytes=nbytes, with_hpio_vref=True)
        insts    = self.instances(phy)
        iobufs   = [self.items(i) for i in insts if i.of == "IOBUFE3"]
        vrefs    = [self.items(i) for i in insts if i.of == "HPIO_VREF"]
        # Each HPIO_VREF uses the POD range.
        for v in vrefs:
            self.assertEqual(v["VREF_CNTR"], "FABRIC_RANGE1")
        # The 8 DQ IOBUFE3s of a byte share one HPIO_VREF, and bytes do not share.
        byte_vref = {}
        for b in iobufs:
            self.assertEqual(b["SIM_DEVICE"], "ULTRASCALE_PLUS")
            byte_vref.setdefault(b["IO"].start//8, set()).add(id(b["VREF"]))
        self.assertEqual(sorted(byte_vref), list(range(nbytes)))
        for ids in byte_vref.values():
            self.assertEqual(len(ids), 1)
        self.assertEqual(set.union(*byte_vref.values()), {id(v["VREF"]) for v in vrefs})

    def test_hpio_vref_csr_order(self):
        # rdly_vref is appended after the existing CSRs so their offsets do not change.
        default = [csr.name for csr in self.get_phy().get_csrs()]
        vref    = [csr.name for csr in self.get_phy(with_hpio_vref=True).get_csrs()]
        self.assertEqual(vref, default + ["rd_vref"])

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
