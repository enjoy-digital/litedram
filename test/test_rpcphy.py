#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.fhdl import verilog
from migen.fhdl.specials import Instance

from litedram.phy.rpc.basephy import RPCPads
from litedram.phy.rpc.s7phy import A7RPCPHY
from litedram.phy.rpc.simphy import SimulationPHY


class TestRPCPHY(unittest.TestCase):
    """Etron RPC DRAM PHYs: the 7-series one (Xilinx primitives: Verilog conversion only) and the
    simulation one (pure Migen: a short simulation)."""
    sys_clk_freq = 100e6

    @staticmethod
    def get_pads(ndqs=1):
        return Record([
            ("clk_p",  1),
            ("clk_n",  1),
            ("cs_n",   1),
            ("dqs_p",  ndqs),
            ("dqs_n",  ndqs),
            ("stb",    1),
            ("db",    16),
        ])

    def get_a7_phy(self, pads=None, **kwargs):
        if pads is None:
            pads = self.get_pads()
        kwargs.setdefault("sys_clk_freq",     self.sys_clk_freq)
        kwargs.setdefault("iodelay_clk_freq", 200e6)
        return A7RPCPHY(pads=pads, **kwargs)

    def get_sim_phy(self, pads=None, **kwargs):
        if pads is None:
            pads = self.get_pads()
        kwargs.setdefault("sys_clk_freq", self.sys_clk_freq)
        return SimulationPHY(pads=pads, **kwargs)

    @staticmethod
    def instances(phy):
        # get_fragment() can only be called once per module (and finalizes the PHY: the
        # serialization is done in do_finalize).
        return [s for s in phy.get_fragment().specials if isinstance(s, Instance)]

    @staticmethod
    def items(inst):
        return {it.name: it.value if isinstance(it, Instance.Parameter) else it.expr
            for it in inst.items}

    @staticmethod
    def domain(expr):
        return expr.cd if isinstance(expr, ClockSignal) else None

    def check_settings(self, phy, phytype, read_latency):
        s = phy.settings
        self.assertEqual(s.phytype,       phytype)
        self.assertEqual(s.memtype,       "RPC")
        self.assertEqual(s.databits,      16)
        self.assertEqual(s.dfi_databits,  4*16)    # BL=16 over 4 phases.
        self.assertEqual(s.nranks,        1)
        self.assertEqual(s.nphases,       4)
        self.assertEqual(s.cl,            8 + 1)   # CL=8, AL=1.
        self.assertEqual(s.cwl,           8 + 1)   # RL=WL.
        self.assertEqual(s.rdphase,       3)
        self.assertEqual(s.wrphase,       3)
        self.assertEqual(s.read_latency,  read_latency)
        self.assertEqual(s.write_latency, 3 + 1)   # cwl_sys_latency + 1 for CS#.
        self.assertEqual(s.bitslips,      16)
        self.assertTrue(s.read_leveling)
        self.assertEqual(len(phy.dfi.phases), 4)
        self.assertEqual(len(phy.dfi.p0.address), 12)
        self.assertEqual(len(phy.dfi.p0.bank),    2)
        self.assertEqual(len(phy.dfi.p0.cs_n),    1)
        self.assertEqual(len(phy.dfi.p0.wrdata),  4*16)
        self.assertEqual(len(phy.dfi.p0.rddata),  4*16)
        self.assertAlmostEqual(phy.tck, 1/(4*self.sys_clk_freq))

    def test_pads(self):
        pads = self.get_pads()
        rpc  = RPCPads(pads)
        for name in ["clk_p", "clk_n", "cs_n", "dqs_p", "dqs_n", "stb", "db"]:
            self.assertIs(getattr(rpc, name), getattr(pads, name))
        # Already mapped pads are accepted as is.
        self.assertIs(self.get_a7_phy(pads=rpc).pads, rpc)
        # 2 DQS strobes (one per DB byte) are a hardware option.
        self.assertEqual(len(RPCPads(self.get_pads(ndqs=2)).dqs_p), 2)
        with self.assertRaises(AssertionError):
            RPCPads(Record([("clk_p", 1), ("clk_n", 1), ("cs_n", 1), ("dqs_p", 1), ("dqs_n", 1), ("stb", 1), ("db", 8)]))
        with self.assertRaises(AttributeError):
            RPCPads(Record([("clk_p", 1), ("clk_n", 1), ("cs_n", 1), ("dqs_p", 1), ("dqs_n", 1), ("db", 16)]))

    def test_a7_settings(self):
        phy = self.get_a7_phy()
        # OSERDESE2 (1) + db/STB/CS (2) + CL (3) = DB; ISERDESE2 (2); mux/bitslip/+1 (3).
        self.check_settings(phy, "A7RPCPHY", read_latency=(2 + 1 + 3) + 2 + 3)
        self.assertEqual(phy.settings.delays, 32)
        self.assertEqual(phy.iodelay_clk_freq, 200e6)
        # Half of a sys8x period in IDELAYE2 taps.
        for iodelay_clk_freq, taps in [(200e6, 8), (300e6, 12), (400e6, 16)]:
            with self.subTest(iodelay_clk_freq=iodelay_clk_freq):
                self.assertEqual(self.get_a7_phy(iodelay_clk_freq=iodelay_clk_freq).half_sys8x_taps, taps)
        with self.assertRaises(KeyError):
            self.get_a7_phy(iodelay_clk_freq=250e6)
        # tCSS=10ns must fit in 2 sys clocks.
        self.get_a7_phy(sys_clk_freq=200e6)
        with self.assertRaises(AssertionError):
            self.get_a7_phy(sys_clk_freq=250e6)

    def test_a7_csrs(self):
        phy = self.get_a7_phy()
        self.assertEqual([csr.name for csr in phy.get_csrs()], [
            "rdly_dq_rst", "rdly_dq_inc", "db_enabled", "dqs_enabled",
            "rst", "dly_sel", "rdly_dq_bitslip_rst", "rdly_dq_bitslip",
            "reset_done", "init_done", "reset_fsm", "burst_stop",
        ])
        self.assertEqual(len(phy._dly_sel.storage), 2)
        self.assertEqual(phy._burst_stop.storage.reset.value,  1)
        self.assertEqual(phy._db_enabled.storage.reset.value,  1)
        self.assertEqual(phy._dqs_enabled.storage.reset.value, 1)

    def test_a7_primitives(self):
        for ndqs in [1, 2]:
            with self.subTest(ndqs=ndqs):
                phy    = self.get_a7_phy(pads=self.get_pads(ndqs=ndqs))
                insts  = self.instances(phy)
                counts = {}
                for i in insts:
                    counts[i.of] = counts.get(i.of, 0) + 1
                self.assertEqual(counts, {
                    "OSERDESE2": 1 + 1 + 16 + ndqs + 1, # CLK, STB, DB, DQS, CS#.
                    "ISERDESE2": 1 + 16 + 1,            # STB, DB, DQS (first strobe only).
                    "IDELAYE2" : 1 + 16 + 1,
                    "IOBUF"    : 1 + 16,                # STB, DB.
                    "IOBUFDS"  : ndqs,                  # DQS.
                    "OBUFDS"   : 1,                     # CLK.
                })
                oserdes = [self.items(i) for i in insts if i.of == "OSERDESE2"]
                clocks  = {}
                for o in oserdes:
                    self.assertEqual((o["DATA_WIDTH"], o["DATA_RATE_OQ"], o["TRISTATE_WIDTH"]), (8, "DDR", 1))
                    self.assertEqual(self.domain(o["CLKDIV"]), "sys")
                    clocks[self.domain(o["CLK"])] = clocks.get(self.domain(o["CLK"]), 0) + 1
                # CLK and DQS edge-aligned, DB/STB/CS# center-aligned (90 deg later).
                self.assertEqual(clocks, {"sys4x_180": 1 + ndqs, "sys4x_90": 1 + 16 + 1})
                for i in [self.items(i) for i in insts if i.of == "ISERDESE2"]:
                    self.assertEqual((i["DATA_WIDTH"], i["DATA_RATE"], i["INTERFACE_TYPE"], i["IOBDELAY"]),
                        (8, "DDR", "NETWORKING", "IFD"))
                    self.assertEqual(self.domain(i["CLKDIV"]), "sys")
                for d in [self.items(i) for i in insts if i.of == "IDELAYE2"]:
                    self.assertEqual((d["IDELAY_TYPE"], d["REFCLK_FREQUENCY"]), ("VARIABLE", 200.0))
                    self.assertEqual(self.domain(d["C"]), "sys")

    def test_a7_verilog(self):
        pads = self.get_pads()
        phy  = self.get_a7_phy(pads=pads)
        v    = str(verilog.convert(phy, ios=set(pads.flatten())))
        self.assertIn("inout [15:0] db", v)
        self.assertIn("inout stb", v)
        for port in ["output clk_p", "output clk_n", "output cs_n", "inout dqs_p", "inout dqs_n"]:
            self.assertIn(port, v)
        for primitive in ["OSERDESE2", "ISERDESE2", "IDELAYE2", "IOBUF", "IOBUFDS", "OBUFDS"]:
            self.assertIn(f"{primitive} ", v)
        for clk in ["sys_clk", "sys4x_90_clk", "sys4x_180_clk"]:
            self.assertIn(clk, v)

    def test_simulation_phy_settings(self):
        for generate_read_data in [False, True]:
            with self.subTest(generate_read_data=generate_read_data):
                pads = self.get_pads()
                phy  = self.get_sim_phy(pads=pads, generate_read_data=generate_read_data)
                # write_ser_latency=1, read_des_latency=0.
                self.check_settings(phy, "RPCSimulationPHY", read_latency=(2 + 1 + 3) + 0 + 3)
                self.assertEqual(phy.settings.delays, 1)
                self.assertEqual([csr.name for csr in phy.get_csrs()], [
                    "rst", "dly_sel", "rdly_dq_bitslip_rst", "rdly_dq_bitslip",
                    "reset_done", "init_done", "reset_fsm", "burst_stop",
                    "rdly_dq_rst", "rdly_dq_inc",
                ])
                v = str(verilog.convert(phy, ios=set(pads.flatten())))
                self.assertNotIn("OSERDESE2", v)
                for clk in ["sys_clk", "sys4x_90_clk", "sys4x_180_clk", "sys4x_90_ddr_clk", "sys4x_180_ddr_clk"]:
                    self.assertIn(clk, v)

    def test_simulation_phy(self):
        # Pure Migen: idle outputs (CLK at the full rate, STB high = NOP, CS# high), the read latency
        # contract (rddata_valid read_latency cycles after rddata_en on rdphase) and the CS# lock on
        # a command with cs_n=0 on phase 0 only. Kept to a few cycles: the simulation is slow.
        pads  = self.get_pads()
        phy   = self.get_sim_phy(pads=pads, generate_read_data=False)
        rl    = phy.settings.read_latency
        ddr   = {"clk_p": [], "clk_n": [], "stb": [], "cs_n": []}
        valid = {}
        ncycles = rl + 4

        def gen():
            dfi = phy.dfi
            yield
            yield
            # READ on rdphase.
            yield dfi.phases[phy.settings.rdphase].rddata_en.eq(1)
            yield
            yield dfi.phases[phy.settings.rdphase].rddata_en.eq(0)
            # cs_n=0 on phase 0 only: CS# locked low from now on.
            yield dfi.p0.cs_n.eq(0)
            for cycle in range(1, ncycles - 2):
                yield
                yield dfi.p0.cs_n.eq(1)
                values = []
                for phase in dfi.phases:
                    values.append((yield phase.rddata_valid))
                valid[cycle] = values

        def monitor():
            for _ in range(ncycles*16):
                for name, log in ddr.items():
                    log.append((yield getattr(pads, name)))
                yield

        run_simulation(phy, {"sys": [gen()], "sys4x_180_ddr": [monitor()]}, clocks={
            # sys4x_90/sys4x_180: 90/180 deg after sys4x (aligned with sys); the DDR clocks run at
            # twice their rate, phase-shifted as in litedram.phy.rpc.simsoc.
            "sys":           (16, 8),
            "sys4x_90":      (4,  1),
            "sys4x_180":     (4,  0),
            "sys4x_90_ddr":  (2,  0),
            "sys4x_180_ddr": (2,  1),
        })

        # Read latency.
        self.assertEqual({cycle: all(v) for cycle, v in valid.items()},
            {cycle: cycle == rl for cycle in valid})
        self.assertEqual({cycle: any(v) for cycle, v in valid.items()},
            {cycle: cycle == rl for cycle in valid})

        # Full-rate clock after the serializers' start-up (2 sys cycles): toggles every DDR tick.
        start = 2*16
        clk_p = ddr["clk_p"][start:]
        self.assertEqual(clk_p[1:], [1 - b for b in clk_p[:-1]])
        self.assertEqual(ddr["clk_n"][start:], [1 - b for b in clk_p])
        # STB held high: NOPs.
        self.assertEqual(set(ddr["stb"][start:]), {1})
        # CS#: high while idle, low once locked (the lock command is issued on sys cycle 3).
        cs_n = ddr["cs_n"][start:]
        self.assertEqual(cs_n[0], 1)
        self.assertEqual(cs_n[-1], 0)
        self.assertEqual(cs_n, [1]*cs_n.index(0) + [0]*(len(cs_n) - cs_n.index(0)))
        self.assertLess(cs_n.index(0)//16 + 2, 3 + 3)


if __name__ == "__main__":
    unittest.main()
