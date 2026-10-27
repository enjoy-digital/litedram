#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.fhdl import verilog
from migen.fhdl.specials import Instance

from litedram.phy.s6ddrphy import S6HalfRateDDRPHY, S6QuarterRateDDRPHY


class TestS6DDRPHY(unittest.TestCase):
    """Spartan-6 PHYs: settings, pads and primitives. The Xilinx primitives (ODDR2, OSERDES2,
    ISERDES2, IOBUF/IOBUFDS) are Instances: Verilog conversion works, simulation does not."""
    databits = 16

    @staticmethod
    def get_pads(databits=16, with_dqs_n=True, with_cs_n=True, with_odt=True, with_reset_n=True):
        layout = [
            ("a",     13),
            ("ba",     3),
            ("ras_n",  1),
            ("cas_n",  1),
            ("we_n",   1),
            ("cke",    1),
            ("dq",    databits),
            ("dm",    databits//8),
            ("dqs",   databits//8),
        ]
        if with_dqs_n:
            layout.append(("dqs_n", databits//8))
        if with_cs_n:
            layout.append(("cs_n", 1))
        if with_odt:
            layout.append(("odt", 1))
        if with_reset_n:
            layout.append(("reset_n", 1))
        return Record(layout)

    @staticmethod
    def get_phy(cls=S6HalfRateDDRPHY, memtype="DDR3", pads=None, **kwargs):
        if pads is None:
            pads = TestS6DDRPHY.get_pads()
        kwargs.setdefault("rd_bitslip", 0)
        kwargs.setdefault("wr_bitslip", 4)
        kwargs.setdefault("dqs_ddr_alignment", "C0")
        if cls is S6HalfRateDDRPHY:
            return cls(pads, memtype, **kwargs)
        return cls(pads, **kwargs)

    @staticmethod
    def instances(phy):
        # get_fragment() can only be called once per module.
        return [s for s in phy.get_fragment().specials if isinstance(s, Instance)]

    @staticmethod
    def items(inst):
        return {it.name: it.value if isinstance(it, Instance.Parameter) else it.expr
            for it in inst.items}

    @staticmethod
    def domain(expr):
        return expr.cd if isinstance(expr, ClockSignal) else None

    def test_half_rate_settings(self):
        for memtype, cl, cwl, read_latency, write_latency in [
            ("DDR",   3, 3, 5, 0), # No CWL: PhySettings defaults it to CL.
            ("LPDDR", 3, 3, 5, 0),
            ("DDR2",  3, 3, 5, 0),
            ("DDR3",  5, 6, 6, 2),
        ]:
            with self.subTest(memtype=memtype):
                phy = self.get_phy(memtype=memtype)
                s   = phy.settings
                self.assertEqual(s.phytype,       "S6HalfRateDDRPHY")
                self.assertEqual(s.memtype,       memtype)
                self.assertEqual(s.databits,      self.databits)
                self.assertEqual(s.dfi_databits,  2*self.databits)
                self.assertEqual(s.nranks,        1)
                self.assertEqual(s.nphases,       2)
                self.assertEqual(s.rdphase,       0)
                self.assertEqual(s.wrphase,       1)
                self.assertEqual(s.cl,            cl)
                self.assertEqual(s.cwl,           cwl)
                self.assertEqual(s.read_latency,  read_latency)
                self.assertEqual(s.write_latency, write_latency)
                self.assertEqual(len(phy.dfi.phases), 2)
                self.assertEqual(len(phy.dfi.p0.wrdata), 2*self.databits)
                self.assertEqual(len(phy.dfi.p0.rddata), 2*self.databits)
                self.assertEqual(len(phy.clk4x_wr_strb), 1)
                self.assertEqual(len(phy.clk4x_rd_strb), 1)
        for memtype in ["SDR", "DDR4", "LPDDR4"]:
            with self.subTest(memtype=memtype):
                with self.assertRaises(NotImplementedError):
                    self.get_phy(memtype=memtype)

    def test_quarter_rate_settings(self):
        phy = self.get_phy(cls=S6QuarterRateDDRPHY)
        s   = phy.settings
        self.assertEqual(s.phytype,       "S6QuarterRateDDRPHY")
        self.assertEqual(s.memtype,       "DDR3")
        self.assertEqual(s.databits,      self.databits)
        self.assertEqual(s.dfi_databits,  2*self.databits)
        self.assertEqual(s.nranks,        1)
        self.assertEqual(s.nphases,       4)
        self.assertEqual(s.rdphase,       0)
        self.assertEqual(s.wrphase,       1)
        self.assertEqual(s.cl,            5)
        self.assertEqual(s.cwl,           6)
        self.assertEqual(s.read_latency,  6//2 + 1)
        self.assertEqual(s.write_latency, 2//2)
        self.assertEqual(len(phy.dfi.phases), 4)
        self.assertEqual(len(phy.dfi.p0.wrdata), 2*self.databits)
        # The half-rate PHY's strobes, renamed.
        self.assertEqual(len(phy.clk8x_wr_strb), 1)
        self.assertEqual(len(phy.clk8x_rd_strb), 1)

    def test_primitives(self):
        for databits in [8, 16, 32]:
            for with_dqs_n in [True, False]:
                with self.subTest(databits=databits, with_dqs_n=with_dqs_n):
                    nbytes = databits//8
                    phy    = self.get_phy(pads=self.get_pads(databits, with_dqs_n=with_dqs_n))
                    insts  = self.instances(phy)
                    counts = {}
                    for i in insts:
                        counts[i.of] = counts.get(i.of, 0) + 1
                    self.assertEqual(counts, {
                        "ODDR2"    : 2*nbytes,          # DQS output and tristate.
                        "OSERDES2" : databits + nbytes, # DQ and DM.
                        "ISERDES2" : databits,          # DQ.
                        "IOBUF"    : databits + (0 if with_dqs_n else nbytes),
                        **({"IOBUFDS": nbytes} if with_dqs_n else {}),
                    })
                    for i in insts:
                        it = self.items(i)
                        if i.of == "OSERDES2":
                            self.assertEqual((self.domain(it["CLK0"]), self.domain(it["CLKDIV"])),
                                ("sdram_full_wr", "sys"))
                            self.assertIs(it["IOCE"], phy.clk4x_wr_strb)
                        elif i.of == "ISERDES2":
                            self.assertEqual((self.domain(it["CLK0"]), self.domain(it["CLKDIV"])),
                                ("sdram_full_rd", "sys"))
                            self.assertIs(it["IOCE"], phy.clk4x_rd_strb)
                            self.assertEqual(it["BITSLIP_ENABLE"], "TRUE")
                        elif i.of == "ODDR2":
                            self.assertEqual(it["DDR_ALIGNMENT"], "C0")
                            self.assertEqual(self.domain(it["C0"]), "sdram_half")

    def test_quarter_rate_primitives(self):
        # The half-rate PHY is renamed to sys2x: its sys clock domain becomes sys2x.
        phy   = self.get_phy(cls=S6QuarterRateDDRPHY)
        insts = self.instances(phy)
        self.assertEqual(len([i for i in insts if i.of == "OSERDES2"]), self.databits + self.databits//8)
        for i in insts:
            it = self.items(i)
            if i.of in ["OSERDES2", "ISERDES2"]:
                self.assertEqual(self.domain(it["CLKDIV"]), "sys2x")

    def test_bitslips_and_alignment(self):
        for wr_bitslip in range(5):
            for rd_bitslip in [0, 3, 15]:
                for dqs_ddr_alignment in ["C0", "C1"]:
                    with self.subTest(wr_bitslip=wr_bitslip, rd_bitslip=rd_bitslip, dqs_ddr_alignment=dqs_ddr_alignment):
                        phy   = self.get_phy(rd_bitslip=rd_bitslip, wr_bitslip=wr_bitslip,
                            dqs_ddr_alignment=dqs_ddr_alignment)
                        insts = self.instances(phy)
                        for i in insts:
                            if i.of == "ODDR2":
                                self.assertEqual(self.items(i)["DDR_ALIGNMENT"], dqs_ddr_alignment)
        # wr_bitslip indexes the 2 cycles x 2 phases x 2 halves of write data.
        with self.assertRaises(IndexError):
            self.instances(self.get_phy(wr_bitslip=5))

    def test_optional_pads(self):
        for with_cs_n, with_odt, with_reset_n in [(False, False, False), (True, False, True), (True, True, True)]:
            with self.subTest(with_cs_n=with_cs_n, with_odt=with_odt, with_reset_n=with_reset_n):
                pads = self.get_pads(with_cs_n=with_cs_n, with_odt=with_odt, with_reset_n=with_reset_n)
                phy  = self.get_phy(pads=pads)
                self.assertEqual(phy.settings.nranks, 1)
                str(verilog.convert(phy, ios=set(pads.flatten())))

    def test_verilog(self):
        for cls in [S6HalfRateDDRPHY, S6QuarterRateDDRPHY]:
            for memtype in (["DDR", "DDR2", "DDR3"] if cls is S6HalfRateDDRPHY else ["DDR3"]):
                with self.subTest(cls=cls.__name__, memtype=memtype):
                    pads = self.get_pads()
                    phy  = self.get_phy(cls=cls, memtype=memtype, pads=pads)
                    v    = str(verilog.convert(phy, ios=set(pads.flatten())))
                    self.assertIn("inout [15:0] dq", v)
                    self.assertIn("inout [1:0] dqs", v)
                    for primitive in ["ODDR2", "OSERDES2", "ISERDES2", "IOBUF", "IOBUFDS"]:
                        self.assertIn(f"{primitive} ", v)
                    for clk in ["sdram_half_clk", "sdram_full_wr_clk", "sdram_full_rd_clk"]:
                        self.assertIn(clk, v)
                    if cls is S6QuarterRateDDRPHY:
                        self.assertIn("sys2x_clk", v)


if __name__ == "__main__":
    unittest.main()
