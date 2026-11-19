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
from litedram.phy.rpc.nxphy import NXRPCPHY, _NXRPCPHYShift
from litedram.phy.rpc.simphy import SimulationPHY


class TestRPCPHY(unittest.TestCase):
    """Etron RPC DRAM PHYs: the 7-series and Nexus ones (vendor primitives: Verilog conversion only)
    and the simulation one (pure Migen: short simulations, with the DRAM model)."""
    sys_clk_freq = 100e6

    @staticmethod
    def get_pads(ndqs=1, nranks=1):
        return Record([
            ("clk_p",  1),
            ("clk_n",  1),
            ("cs_n",   nranks),
            ("dqs_p",  ndqs),
            ("dqs_n",  ndqs),
            ("stb",    nranks),
            ("db",    16),
        ])

    def get_a7_phy(self, pads=None, **kwargs):
        if pads is None:
            pads = self.get_pads()
        kwargs.setdefault("sys_clk_freq",     self.sys_clk_freq)
        kwargs.setdefault("iodelay_clk_freq", 200e6)
        return A7RPCPHY(pads=pads, **kwargs)

    def get_nx_phy(self, pads=None, **kwargs):
        if pads is None:
            pads = self.get_pads(ndqs=2, nranks=2)
        kwargs.setdefault("sys_clk_freq", self.sys_clk_freq)
        return NXRPCPHY(pads=pads, **kwargs)

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

    def check_settings(self, phy, phytype, read_latency, bitslips=16):
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
        self.assertEqual(s.bitslips,      bitslips)
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

    def test_nx_settings(self):
        phy = self.get_nx_phy()
        # ODDRX4 (1) + db/STB/CS (2) + CL (3) = DB; write shift register, IDDRX4DQ/DQSBUF/DATAVALID (7); mux/bitslip/+1 (3).
        self.check_settings(phy, "NXRPCPHY", read_latency=(2 + 1 + 3) + 7 + 3, bitslips=8)
        self.assertEqual(phy.settings.delays, 16)
        # STB/CS# delay: tCK/4 less the STB skew (450ps) in 12.5ps taps, limited to the delay line.
        for sys_clk_freq, taps in [(100e6, 14), (50e6, 64), (25e6, 127), (200e6, 0)]:
            with self.subTest(sys_clk_freq=sys_clk_freq):
                self.assertEqual(self.get_nx_phy(sys_clk_freq=sys_clk_freq).stb_delay, taps)
        self.assertEqual(self.get_nx_phy(stb_delay=10).stb_delay, 10)
        with self.assertRaises(AssertionError):
            self.get_nx_phy(stb_delay=128)

    def test_nx_csrs(self):
        phy = self.get_nx_phy()
        self.assertEqual([csr.name for csr in phy.get_csrs()], [
            "stb_shift", "dqs_shift", "db_shift", "rd_en_sel", "rd_en_phase",
            "rdly_dq_rst", "rdly_dq_inc", "wlvl_rst", "wlvl_inc", "wdly_dir", "wdly_rst", "wdly_move", "rdqs_dir", "rdqs_rst", "rdqs_move", "stb_dly_dir", "stb_dly_rst", "stb_dly_move", "burstdet_clr", "burstdet_seen", "datavalid_cnt",
            "rst", "dly_sel", "rdly_dq_bitslip_rst", "rdly_dq_bitslip",
            "reset_done", "init_done", "reset_fsm", "burst_stop",
        ])

    def test_nx_primitives(self):
        for ndqs, nranks in [(1, 1), (2, 2)]:
            with self.subTest(ndqs=ndqs, nranks=nranks):
                phy   = self.get_nx_phy(pads=self.get_pads(ndqs=ndqs, nranks=nranks))
                insts = self.instances(phy)
                count = {}
                for i in insts:
                    count[i.of] = count.get(i.of, 0) + 1
                # A pin is only bidirectional at X4 with the memory (DQ/DQS) primitives.
                self.assertEqual(count, {
                    "DDRDLL"    : 1,
                    "DQSBUF"    : ndqs,
                    "ODDRX4"    : 1 + 2*nranks, # CLK, STB and CS# (one per rank).
                    "DELAYA"    : 2*nranks,
                    "ODDRX4DQS" : ndqs,
                    "TSHX4DQS"  : ndqs,
                    "ODDRX4DQ"  : 16,
                    "TSHX4DQ"   : 16,
                    "IDDRX4DQ"  : 16,
                })
                for i in [self.items(i) for i in insts]:
                    if "ECLK" in i:
                        self.assertEqual(self.domain(i["ECLK"]), "sys4x")
                        self.assertEqual(self.domain(i["SCLK"]), "sys")
                for d in [self.items(i) for i in insts if i.of == "DQSBUF"]:
                    self.assertEqual(d["MODX"], "MDDRX4")
                    self.assertEqual(self.domain(d["ECLKIN"]), "sys4x")
                for d in [self.items(i) for i in insts if i.of == "DELAYA"]:
                    self.assertEqual(d["DEL_VALUE"], "14") # tCK/4 less the STB skew, in taps.

    def test_nx_verilog(self):
        pads = self.get_pads(ndqs=2, nranks=2)
        phy  = self.get_nx_phy(pads=pads)
        v    = str(verilog.convert(phy, ios=set(pads.flatten())))
        for primitive in ["ODDRX4", "ODDRX4DQ", "ODDRX4DQS", "TSHX4DQ", "TSHX4DQS", "IDDRX4DQ",
            "DELAYA", "DQSBUF", "DDRDLL"]:
            self.assertIn(f"{primitive} ", v)
        for primitive in ["IDDRX4", "DELAYB"]:
            self.assertNotIn(f"{primitive} ", v)
        for clk in ["sys_clk", "sys4x_clk", "init_clk"]:
            self.assertIn(clk, v)

    def test_nx_write_shift(self):
        # A word delayed by n UIs: bit k of the stream moves to bit k + n.
        for shift in [0, 1, 7, 8, 13, 15]:
            with self.subTest(shift=shift):
                i   = Signal(8)
                s   = Signal(4, reset=shift)
                dut = _NXRPCPHYShift(i, s)
                words = [0xa5, 0x3c, 0x01, 0x80, 0xff, 0x00, 0x5a, 0x00, 0x00, 0x00]
                out = []
                def gen():
                    for w in words:
                        yield i.eq(w)
                        yield
                        out.append((yield dut.o))
                run_simulation(dut, gen())
                stream_i = [(w >> b) & 1 for w in words for b in range(8)]
                # Outputs are registered: one more word (8 UIs).
                stream_o = [(w >> b) & 1 for w in out   for b in range(8)]
                self.assertEqual(stream_o[shift + 8:], stream_i[:len(stream_i) - shift - 8])

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

    def test_simulation_dram_model(self):
        # Pure Migen: PU RESET/ZQ INIT through the PHY FSM, ACT, a full write then a masked one on
        # the same WORD (32 bytes) of the DRAM model, and a read back. Checks the Request Packets,
        # the write data/mask and read data paths of the PHY against the model.
        pads = self.get_pads()
        phy  = self.get_sim_phy(pads=pads, sys_clk_freq=1e6, with_dram_model=True, dram_model_rowbits=2)
        dfi  = phy.dfi
        s    = phy.settings
        self.assertEqual(s.read_latency, (2 + 1 + 3) + 1 + 3)
        res  = {}

        def cmd(phase, cas=1, ras=1, we=1, reset_n=1, address=0, bank=0):
            p = dfi.phases[phase]
            yield p.cas_n.eq(cas)
            yield p.ras_n.eq(ras)
            yield p.we_n.eq(we)
            yield p.cs_n.eq(0)
            yield p.reset_n.eq(reset_n)
            yield p.address.eq(address)
            yield p.bank.eq(bank)

        def nop(cycles=0):
            for p in dfi.phases:
                yield p.cas_n.eq(1)
                yield p.ras_n.eq(1)
                yield p.we_n.eq(1)
                yield p.cs_n.eq(1)
                yield p.reset_n.eq(1)
                yield p.wrdata_en.eq(0)
                yield p.rddata_en.eq(0)
            for _ in range(cycles):
                yield

        def write(bank, col, data, mask=0):
            yield from cmd(s.wrphase, cas=0, we=0, address=col, bank=bank)
            yield dfi.phases[s.wrphase].wrdata_en.eq(1)
            yield
            yield from nop(s.write_latency - 1)
            for p in range(4):
                yield dfi.phases[p].wrdata.eq((data >> (64*p)) & (2**64 - 1))
                yield dfi.phases[p].wrdata_mask.eq((mask >> (8*p)) & 0xff)
            yield
            yield from nop(8)

        def read(bank, col):
            yield from cmd(s.rdphase, cas=0, address=col, bank=bank)
            yield dfi.phases[s.rdphase].rddata_en.eq(1)
            yield
            yield from nop()
            for cycle in range(1, s.read_latency + 4):
                yield
                if (yield dfi.phases[0].rddata_valid):
                    data = 0
                    for p in range(4):
                        data |= (yield dfi.phases[p].rddata) << (64*p)
                    return cycle, data
            return None, None

        d0   = int.from_bytes(bytes(range(0x01, 0x21)), "little")
        d1   = int.from_bytes(bytes(range(0x81, 0xa1)), "little")
        mask = 0x0f0f00ff # 1: byte not written.
        def gen():
            yield from nop(4)
            # CS# lock (cs_n=0 on phase 0 only), PU RESET (ACT with reset_n=0), ZQ INIT.
            yield dfi.p0.cs_n.eq(0)
            yield
            yield from nop(2)
            yield from cmd(0, ras=0, reset_n=0)
            yield
            yield from nop(16)
            yield from cmd(0, we=0, reset_n=0, address=1 << 10)
            yield
            yield from nop(8)
            res["init_done"] = (yield phy._init_done.status)
            # ACT bank 1, row 2.
            yield from cmd(0, ras=0, address=2, bank=1)
            yield
            yield from nop(4)
            yield from write(1, 0x10, d0)
            yield from write(1, 0x10, d1, mask=mask)
            res["read"] = yield from read(1, 0x10)
            yield from nop(4)
            # Model memory: bank 1, row 2, WORD 1 (column 0x10).
            base = (1 << (2 + 6 + 4)) | (2 << (6 + 4)) | (1 << 4)
            res["mem"] = []
            for n in range(16):
                res["mem"].append((yield phy.dram.mem[base + n]))

        run_simulation(phy, {"sys": [gen()]}, clocks={
            "sys":           (16, 8),
            "sys4x_90":      (4,  1),
            "sys4x_180":     (4,  0),
            "sys4x_90_ddr":  (2,  0),
            "sys4x_180_ddr": (2,  1),
        })

        expected = 0
        for n in range(32):
            byte = ((d0 if (mask >> n) & 1 else d1) >> (8*n)) & 0xff
            expected |= byte << (8*n)
        self.assertEqual(res["init_done"], 1)
        self.assertEqual(res["mem"], [(expected >> (16*n)) & 0xffff for n in range(16)])
        self.assertEqual(res["read"], (s.read_latency, expected))

    def test_simulation_dram_model_stream(self):
        # Pure Migen: Address Streaming. Reads/writes issued every 2 sys_clk are sent as Serial
        # Packets on STB (other bank/column of an open row included) and their data follow each
        # other; the burst ends with a Burst Stop. Checked against the DRAM model: memory content,
        # read data, read latency of each WORD and Serial Packets all legal.
        pads = self.get_pads()
        phy  = self.get_sim_phy(pads=pads, sys_clk_freq=1e6, with_dram_model=True, dram_model_rowbits=2)
        dfi  = phy.dfi
        s    = phy.settings
        rows = {1: 2, 2: 1} # bank: open row.

        def word(n):
            return int.from_bytes(bytes((17*n + 3*i + 1) & 0xff for i in range(32)), "little")

        # (bank, column): the columns are in 16-bit words, 16 per WORD.
        stream = [(1, 0x010), (1, 0x020), (1, 0x3f0), (2, 0x050), (2, 0x060)]
        single = (1, 0x030)
        mask   = 0x0f0f00ff # 1: byte not written.

        events = {} # cycle: [(signal, value)].
        def at(cycle, *assigns):
            events.setdefault(cycle, []).extend(assigns)
        def cmd(cycle, phase, cas=1, ras=1, we=1, reset_n=1, address=0, bank=0):
            p = dfi.phases[phase]
            at(cycle, (p.cas_n, cas), (p.ras_n, ras), (p.we_n, we), (p.cs_n, 0), (p.reset_n, reset_n),
                (p.address, address), (p.bank, bank))
        def write(cycle, bank, col, data, mask=0):
            cmd(cycle, s.wrphase, cas=0, we=0, address=col, bank=bank)
            at(cycle, (dfi.phases[s.wrphase].wrdata_en, 1))
            for p in range(4):
                at(cycle + s.write_latency,
                    (dfi.phases[p].wrdata,      (data >> (64*p)) & (2**64 - 1)),
                    (dfi.phases[p].wrdata_mask, (mask >> (8*p)) & 0xff))
        def read(cycle, bank, col):
            cmd(cycle, s.rdphase, cas=0, address=col, bank=bank)
            at(cycle, (dfi.phases[s.rdphase].rddata_en, 1))

        # CS# lock (cs_n=0 on phase 0 only), PU RESET (ACT with reset_n=0), ZQ INIT, ACTs.
        at(4, (dfi.p0.cs_n, 0))
        cmd(7,  0, ras=0, reset_n=0)
        cmd(24, 0, we=0, reset_n=0, address=1 << 10)
        for n, (bank, row) in enumerate(rows.items()):
            cmd(34 + 4*n, 0, ras=0, address=row, bank=bank)
        # Write stream, single masked write (over the pattern of another WORD), read stream (in
        # another order) and single read.
        t_write = 44
        for n, (bank, col) in enumerate(stream):
            write(t_write + 2*n, bank, col, word(n))
        t_single = t_write + 2*len(stream) + 12
        write(t_single,      *single, word(10))
        write(t_single + 12, *single, word(11), mask=mask)
        t_read = t_single + 24
        order  = [3, 0, 4, 1, 2]
        for n, i in enumerate(order):
            read(t_read + 2*n, *stream[i])
        t_read_single = t_read + 2*len(order) + 12
        read(t_read_single, *single)
        ncycles = t_read_single + s.read_latency + 4

        res = {"read": {}}
        def gen():
            signals = set()
            for cycle in range(ncycles):
                for p in dfi.phases:
                    for name, value in [("cas_n", 1), ("ras_n", 1), ("we_n", 1), ("cs_n", 1),
                        ("reset_n", 1), ("wrdata_en", 0), ("rddata_en", 0)]:
                        yield getattr(p, name).eq(value)
                for signal, value in events.get(cycle, []):
                    yield signal.eq(value)
                yield
                if (yield dfi.phases[0].rddata_valid):
                    data = 0
                    for p in range(4):
                        data |= (yield dfi.phases[p].rddata) << (64*p)
                    res["read"][cycle] = data
            res["error"]  = (yield phy.dram.error)
            res["nwords"] = (yield phy.dram.nwords)
            res["mem"]    = {}
            for bank, col in stream + [single]:
                base = (bank << (2 + 6 + 4)) | (rows[bank] << (6 + 4)) | col
                data = 0
                for n in range(16):
                    data |= (yield phy.dram.mem[base + n]) << (16*n)
                res["mem"][(bank, col)] = data

        run_simulation(phy, {"sys": [gen()]}, clocks={
            "sys":           (16, 8),
            "sys4x_90":      (4,  1),
            "sys4x_180":     (4,  0),
            "sys4x_90_ddr":  (2,  0),
            "sys4x_180_ddr": (2,  1),
        })

        masked = 0
        for n in range(32):
            byte = ((word(10) if (mask >> n) & 1 else word(11)) >> (8*n)) & 0xff
            masked |= byte << (8*n)
        expected = {addr: word(n) for n, addr in enumerate(stream)}
        expected[single] = masked
        self.assertEqual(res["error"], 0)
        self.assertEqual(res["nwords"], 2*len(stream) + 3)
        self.assertEqual(res["mem"], expected)
        # The data of the WORD n of a stream come 2*n sys_clk after the ones of the first WORD.
        reads = {t_read + 2*n + s.read_latency: expected[stream[i]] for n, i in enumerate(order)}
        reads[t_read_single + s.read_latency] = masked
        self.assertEqual(res["read"], reads)


if __name__ == "__main__":
    unittest.main()
