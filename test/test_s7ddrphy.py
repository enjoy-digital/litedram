#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
from types import SimpleNamespace

from migen import *

from litedram.common import get_default_cl
from litedram.init import get_ddr3_phy_init_sequence
from litedram.phy.s7ddrphy import A7DDRPHY, K7DDRPHY


class TestS7DDRPHYSettings(unittest.TestCase):
    sys_clk_freqs       = [50e6, 100e6, 125e6, 150e6, 175e6, 225e6]
    ddr3_cls            = range(5, 15)
    read_pipeline_cycles = 6

    @staticmethod
    def get_pads():
        return Record([
            ("a",       15),
            ("ba",       3),
            ("ras_n",    1),
            ("cas_n",    1),
            ("we_n",     1),
            ("clk_p",    1),
            ("clk_n",    1),
            ("dq",       8),
            ("dm",       1),
            ("dqs_p",    1),
            ("dqs_n",    1),
        ])

    @staticmethod
    def get_rdphase(phy):
        return phy.settings.rdphase.reset.value

    @staticmethod
    def get_mr0_cl(phy):
        init_sequence, _ = get_ddr3_phy_init_sequence(
            phy_settings    = phy.settings,
            timing_settings = SimpleNamespace(tWR=2),
        )
        mr0 = next(address for comment, address, _, _, _ in init_sequence
            if comment.startswith("Load Mode Register 0"))
        mr0_to_cl = {
            0b0010 :  5,
            0b0100 :  6,
            0b0110 :  7,
            0b1000 :  8,
            0b1010 :  9,
            0b1100 : 10,
            0b1110 : 11,
            0b0001 : 12,
            0b0011 : 13,
            0b0101 : 14,
        }
        mr0_cl = ((mr0 >> 2) & 0b1) | (((mr0 >> 4) & 0b111) << 1)
        return mr0_to_cl[mr0_cl]

    def test_a7_default_cl_is_preserved(self):
        for sys_clk_freq in self.sys_clk_freqs:
            with self.subTest(sys_clk_freq=sys_clk_freq):
                phy         = A7DDRPHY(self.get_pads(), sys_clk_freq=sys_clk_freq)
                tck         = 1/(4*sys_clk_freq)
                expected_cl = get_default_cl("DDR3", tck)

                self.assertEqual(phy.settings.cl, expected_cl)
                self.assertEqual(self.get_mr0_cl(phy), expected_cl)

    def test_a7_read_alignment(self):
        for cl in self.ddr3_cls:
            for cmd_latency in range(3):
                with self.subTest(cl=cl, cmd_latency=cmd_latency):
                    phy = A7DDRPHY(self.get_pads(),
                        sys_clk_freq = 100e6,
                        cl           = cl,
                        cmd_latency  = cmd_latency,
                    )
                    rdphase          = self.get_rdphase(phy)
                    read_sys_latency = phy.settings.read_latency - self.read_pipeline_cycles

                    self.assertEqual(phy.settings.cl, cl)
                    self.assertEqual(self.get_mr0_cl(phy), cl)
                    self.assertEqual(
                        rdphase + cl + cmd_latency,
                        read_sys_latency*phy.settings.nphases + 1,
                    )

    def test_k7_read_alignment_is_unchanged(self):
        for cl in self.ddr3_cls:
            with self.subTest(cl=cl):
                phy              = K7DDRPHY(self.get_pads(), sys_clk_freq=100e6, cl=cl)
                rdphase          = self.get_rdphase(phy)
                read_sys_latency = phy.settings.read_latency - self.read_pipeline_cycles

                self.assertEqual(phy.settings.cl, cl)
                self.assertEqual(self.get_mr0_cl(phy), cl)
                self.assertEqual(
                    rdphase + cl,
                    read_sys_latency*phy.settings.nphases,
                )


class TestS7DDRPHYCKPhaseShift(unittest.TestCase):
    """with_ck_phase_shift: the clocking contract and the CK phase shift control.

    The PHY's primitives cannot run in Migen's simulator; what is checked without hardware is the
    structure the technique relies on: CK and the commands on the phase-shifted MMCM outputs (fed
    from falling-edge registers of sys), DQ/DQS/read capture on the static ones, every serializer's
    CLK/CLKDIV from the one MMCM, the MMCM's VCO at the DDR rate with fine phase shift on the CK
    pair only. The phase-shift FSM is simulated.
    """
    @staticmethod
    def get_pads(lanes=9):
        # A 72-bit DDR3 channel: 15 address bits, 8 banks, x8 lanes (9 with ECC), no DM.
        return Record([
            ("a", 15), ("ba", 3), ("ras_n", 1), ("cas_n", 1), ("we_n", 1), ("cs_n", 1),
            ("cke", 1), ("odt", 1), ("reset_n", 1),
            ("dq", 8*lanes), ("dqs_p", lanes), ("dqs_n", lanes), ("clk_p", 1), ("clk_n", 1),
        ])

    def get_phy(self, lanes=8, **kwargs):
        from litedram.common import PHYPadsReducer
        # A Kintex7 HR bank (the typical use); A7DDRPHY takes the same arguments.
        cls = kwargs.pop("cls", K7DDRPHY)
        if cls is K7DDRPHY:
            kwargs.setdefault("with_odelay", False)
        kwargs.setdefault("with_ck_phase_shift", True)
        phy = cls(PHYPadsReducer(self.get_pads(), list(range(lanes))),
            memtype="DDR3", sys_clk_freq=400e6/3, cl=7, cwl=6, name="ddrphy0", **kwargs)
        insts = [s for s in phy.get_fragment().specials if isinstance(s, Instance)]
        return phy, insts

    @staticmethod
    def items(inst):
        r = {}
        for it in inst.items:
            if isinstance(it, Instance.Parameter):
                r[it.name] = it.value
            else:
                r[it.name] = it.expr
        return r

    @staticmethod
    def domain(expr):
        return expr.cd if isinstance(expr, ClockSignal) else None

    def test_serializer_clocking(self):
        _, insts = self.get_phy()
        oserdes = [self.items(i) for i in insts if i.of == "OSERDESE2"]
        iserdes = [self.items(i) for i in insts if i.of == "ISERDESE2"]
        # CK + 25 command pins (a 15, ba 3, ras/cas/we/cs/cke/odt/reset_n), 8 DQS, 64 DQ.
        self.assertEqual(len(oserdes), 1 + 25 + 8 + 64)
        self.assertEqual(len(iserdes), 64)
        pairs = {}
        for o in oserdes:
            pair = (self.domain(o["CLK"]), self.domain(o["CLKDIV"]))
            pairs[pair] = pairs.get(pair, 0) + 1
        self.assertEqual(pairs, {
            ("ddrphy0_c4x",     "ddrphy0_c"): 1 + 25, # CK and the commands: the shifted pair.
            ("ddrphy0_w4x_dqs", "ddrphy0_w"): 8,      # DQS at 90 deg, static.
            ("ddrphy0_w4x",     "ddrphy0_w"): 64,     # DQ, static.
        })
        for i in iserdes:
            self.assertEqual((self.domain(i["CLK"]), self.domain(i["CLKDIV"])),
                ("ddrphy0_w4x", "ddrphy0_w"))
        self.assertEqual(len([i for i in insts if i.of == "IDELAYE2"]), 64)
        self.assertEqual(len([i for i in insts if i.of == "IOBUF"]), 64) # ECC lane left out.

    def test_commands_cross_on_the_falling_edge(self):
        _, insts = self.get_phy()
        fdre = [self.items(i) for i in insts if i.of == "FDRE"]
        # Every command bit of every DFI phase (4 x 25), on sys' falling edge.
        self.assertEqual(len(fdre), 4*25)
        for f in fdre:
            self.assertEqual(f["IS_C_INVERTED"], 1)
            self.assertEqual(self.domain(f["C"]), "sys")

    def test_one_mmcm_vco_at_the_ddr_rate(self):
        phy, insts = self.get_phy()
        mmcms = [i for i in insts if i.of == "MMCME2_ADV"]
        self.assertEqual(len(mmcms), 1)
        self.assertEqual(mmcms[0].name_override, "ddrphy0_mmcm")
        m = self.items(mmcms[0])
        self.assertEqual((m["DIVCLK_DIVIDE"], m["CLKFBOUT_MULT_F"]), (1, 8.0)) # VCO 1066.67 MHz.
        self.assertEqual((self.domain(m["CLKIN1"]), self.domain(m["PSCLK"])), ("sys", "sys"))
        # Fine phase shift on the CK pair only, both at phase 0 (one sub-VCO phase: FINE_PS_FRAC).
        self.assertEqual((m["CLKOUT0_USE_FINE_PS"], m["CLKOUT1_USE_FINE_PS"]), ("TRUE", "TRUE"))
        for n in (2, 3, 4):
            self.assertNotIn(f"CLKOUT{n}_USE_FINE_PS", m)
        self.assertEqual([m[f"CLKOUT{n}_PHASE"] for n in range(5)], [0.0, 0.0, 0.0, 0.0, 90.0])
        self.assertEqual((m["CLKOUT0_DIVIDE_F"], m["CLKOUT1_DIVIDE"], m["CLKOUT2_DIVIDE"],
            m["CLKOUT3_DIVIDE"], m["CLKOUT4_DIVIDE"]), (8.0, 2, 8, 2, 2))
        # Feedback through a BUFG: the static outputs keep sys' phase.
        bufgs = [self.items(i) for i in insts if i.of == "BUFG"]
        self.assertTrue(any(b["I"] is m["CLKFBOUT"] and b["O"] is m["CLKFBIN"] for b in bufgs))
        # 112 fine steps of 16.7 ps per tCK.
        self.assertEqual(phy.ps_steps_per_tck, 112)
        self.assertAlmostEqual(phy.ps_step_ps, 16.74, places=2)

    def test_latencies_are_the_a7_ones(self):
        # Same schedule as without CK phase shift; write latency calibrated by the BIOS.
        phy, _ = self.get_phy()
        ref, _ = self.get_phy(with_ck_phase_shift=False)
        for k in ("cl", "cwl", "read_latency", "write_latency", "nphases", "dfi_databits",
                  "read_leveling", "write_leveling"):
            self.assertEqual(getattr(phy.settings, k), getattr(ref.settings, k), k)
        self.assertEqual(phy.settings.rdphase.reset.value, ref.settings.rdphase.reset.value)
        self.assertEqual(phy.settings.wrphase.reset.value, ref.settings.wrphase.reset.value)
        self.assertFalse(phy.settings.write_latency_calibration)

    def test_k7_hr_bank_is_the_a7_phy(self):
        # K7DDRPHY(with_odelay=False): the A7DDRPHY's settings and primitives, with or without CK
        # phase shift.
        for ck in (False, True):
            k7, k7_insts = self.get_phy(with_ck_phase_shift=ck)
            a7, a7_insts = self.get_phy(with_ck_phase_shift=ck, cls=A7DDRPHY)
            for k in ("cl", "cwl", "read_latency", "write_latency", "write_leveling",
                      "write_latency_calibration", "read_leveling"):
                self.assertEqual(getattr(k7.settings, k), getattr(a7.settings, k), k)
            self.assertEqual(sorted(i.of for i in k7_insts), sorted(i.of for i in a7_insts))
            self.assertEqual([c.name for c in k7.get_csrs()], [c.name for c in a7.get_csrs()])
        self.assertFalse([i for i in k7_insts if i.of == "ODELAYE2"])
        # Default: HP banks, with ODELAYE2 and write latency calibration (unchanged).
        k7_hp, k7_hp_insts = self.get_phy(with_odelay=True, with_ck_phase_shift=False)
        self.assertTrue(k7_hp.settings.write_latency_calibration)
        self.assertTrue([i for i in k7_hp_insts if i.of == "ODELAYE2"])

    def test_csrs(self):
        phy, _ = self.get_phy()
        ref, _ = self.get_phy(with_ck_phase_shift=False)
        names     = [c.name for c in phy.get_csrs()]
        ref_names = [c.name for c in ref.get_csrs()]
        # The A7DDRPHY's CSRs, in order, plus the per-bit read selection and the CK phase control.
        extra     = ["dq_dly_sel", "ckphase_inc", "ckphase_dec", "ckphase_status"]
        self.assertEqual([n for n in names if n not in extra], ref_names)
        self.assertEqual([n for n in names if n in extra], extra)
        # Without CK phase shift: no MMCM, no extra CSRs.
        _, ref_insts = self.get_phy(with_ck_phase_shift=False)
        self.assertFalse([i for i in ref_insts if i.of in ("MMCME2_ADV", "FDRE")])

    def test_ck_phase_steps(self):
        from migen.sim import passive
        from litedram.phy.s7ddrphy import S7DDRPHYCKPhase
        dut = S7DDRPHYCKPhase()
        log = {"psen": 0}

        @passive
        def mmcm():
            # PSDONE 12 cycles after each PSEN, locked throughout.
            yield dut.locked.eq(1)
            pending = []
            while True:
                if (yield dut.psen):
                    log["psen"] += 1
                    pending.append(12)
                pending = [p - 1 for p in pending]
                yield dut.psdone.eq(1 if 0 in pending else 0)
                pending = [p for p in pending if p > 0]
                yield

        def status():
            value = (yield dut._status.fields.value)
            return (value - 0x10000 if value & 0x8000 else value), (yield dut._status.fields.busy)

        def strobe(csr):
            yield csr.re.eq(1)
            yield
            yield csr.re.eq(0)

        def gen():
            for _ in range(4):
                yield
            # Five steps later, waiting for busy each time.
            for _ in range(5):
                yield from strobe(dut._inc)
                for _ in range(20):
                    yield
            self.assertEqual((yield from status()), (5, 0))
            # A request while busy is dropped.
            yield from strobe(dut._dec)
            yield from strobe(dut._dec)
            for _ in range(20):
                yield
            self.assertEqual((yield from status()), (4, 0))
            self.assertEqual(log["psen"], 6)
            # Unlock: back to the reset phase.
            yield dut.locked.eq(0)
            yield
            yield
            self.assertEqual((yield from status()), (0, 0))

        run_simulation(dut, [gen(), mmcm()])

    def test_c_header_has_ck_phase_steps(self):
        from litedram.init import get_sdram_phy_c_header
        from litedram.modules import MT41K256M8
        phy, _ = self.get_phy()
        module = MT41K256M8(400e6/3, "1:4")
        header = get_sdram_phy_c_header(phy.settings, module.timing_settings, module.geom_settings)
        self.assertIn(f"#define SDRAM_PHY_CKPHASE_STEPS {phy.ps_steps_per_tck}", header)
        ref, _ = self.get_phy(with_ck_phase_shift=False)
        header = get_sdram_phy_c_header(ref.settings, module.timing_settings, module.geom_settings)
        self.assertNotIn("SDRAM_PHY_CKPHASE_STEPS", header)


class TestS7DDRPHYWriteControl(unittest.TestCase):
    def test_dqs_preamble_postamble(self):
        # The DQS preamble must come the cycle before the DQ output enable and the postamble the
        # cycle after, including with cwl_sys_latency == 1 (DDR2 1:2 at CL3, i.e. <= 100 MHz
        # sys_clk) where the preamble tap used to wrap onto the postamble tap.
        from litedram.phy.s7ddrphy import S7DDRPHYWriteControl
        for cwl_sys_latency in [1, 2, 3]:
            with self.subTest(cwl_sys_latency=cwl_sys_latency):
                wrdata_en = Signal()
                dut = S7DDRPHYWriteControl(wrdata_en, cwl_sys_latency)
                log = []

                def gen():
                    yield wrdata_en.eq(1) # One sys_clk cycle of write data.
                    yield
                    yield wrdata_en.eq(0)
                    for _ in range(cwl_sys_latency + 4):
                        log.append(((yield dut.dqs_preamble), (yield dut.dq_oe), (yield dut.dqs_postamble)))
                        yield

                run_simulation(dut, gen())
                preamble  = [i for i, (p, _, _) in enumerate(log) if p]
                oe        = [i for i, (_, o, _) in enumerate(log) if o]
                postamble = [i for i, (_, _, q) in enumerate(log) if q]
                self.assertEqual(oe,        [cwl_sys_latency])
                self.assertEqual(preamble,  [cwl_sys_latency - 1])
                self.assertEqual(postamble, [cwl_sys_latency + 1])
