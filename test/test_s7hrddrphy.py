#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""S7HRDDRPHY (litedram/phy/s7hrddrphy.py): its clocking contract and the CK phase shift control.

The PHY's primitives cannot run in Migen's simulator; what can be checked without hardware is
the structure the technique relies on: CK and the commands on the phase-shifted MMCM outputs
(fed from falling-edge registers of sys), DQ/DQS/read capture on the static ones, every
serializer's CLK/CLKDIV from the one MMCM, the MMCM's VCO at the DDR rate with fine phase shift
on the CK pair only, the latencies the simulation model copies. The phase-shift FSM is simulated.
"""

from migen import *
from migen.sim import passive
from migen.genlib.record import Record

from litedram.common import PHYPadsReducer

from litedram.phy.s7hrddrphy import S7HRDDRPHY, S7HRCKPhase, s7hr_latencies, s7hr_model_settings

# Pads ---------------------------------------------------------------------------------------------

def ddr3_pads(lanes=9):
    """A 72-bit DDR3 channel: 15 address bits, 8 banks, x8 lanes (9 with ECC)."""
    return Record([
        ("a", 15), ("ba", 3), ("ras_n", 1), ("cas_n", 1), ("we_n", 1), ("cs_n", 1),
        ("cke", 1), ("odt", 1), ("reset_n", 1),
        ("dq", 8*lanes), ("dqs_p", lanes), ("dqs_n", lanes), ("clk_p", 1), ("clk_n", 1),
    ])


def phy_and_instances(lanes=8):
    phy = S7HRDDRPHY(PHYPadsReducer(ddr3_pads(), list(range(lanes))), sys_clk_freq=400e6/3,
        cl=7, cwl=6, name="ddrphy0")
    frag = phy.get_fragment()
    insts = [s for s in frag.specials if isinstance(s, Instance)]
    return phy, insts


def items(inst):
    r = {}
    for it in inst.items:
        if isinstance(it, Instance.Parameter):
            r[it.name] = it.value
        else:
            r[it.name] = it.expr
    return r


def domain(expr):
    return expr.cd if isinstance(expr, ClockSignal) else None

# Structure ----------------------------------------------------------------------------------------

def test_serializer_clocking():
    _, insts = phy_and_instances()
    oserdes = [items(i) for i in insts if i.of == "OSERDESE2"]
    iserdes = [items(i) for i in insts if i.of == "ISERDESE2"]
    # CK + 25 command pins (a 15, ba 3, ras/cas/we/cs/cke/odt/reset_n), 8 DQS, 64 DQ.
    assert len(oserdes) == 1 + 25 + 8 + 64
    assert len(iserdes) == 64
    pairs = {}
    for o in oserdes:
        pair = (domain(o["CLK"]), domain(o["CLKDIV"]))
        pairs[pair] = pairs.get(pair, 0) + 1
    assert pairs == {
        ("ddrphy0_c4x",     "ddrphy0_c"): 1 + 25, # CK and the commands: the shifted pair.
        ("ddrphy0_w4x_dqs", "ddrphy0_w"): 8,      # DQS at 90 deg, static.
        ("ddrphy0_w4x",     "ddrphy0_w"): 64,     # DQ, static.
    }
    for i in iserdes:
        assert (domain(i["CLK"]), domain(i["CLKDIV"])) == ("ddrphy0_w4x", "ddrphy0_w")
    assert len([i for i in insts if i.of == "IDELAYE2"]) == 64


def test_commands_cross_on_the_falling_edge():
    _, insts = phy_and_instances()
    fdre = [items(i) for i in insts if i.of == "FDRE"]
    # Every command bit of every DFI phase (4 x 25), on sys' falling edge.
    assert len(fdre) == 4*25
    for f in fdre:
        assert f["IS_C_INVERTED"] == 1 and domain(f["C"]) == "sys"


def test_one_mmcm_vco_at_the_ddr_rate():
    phy, insts = phy_and_instances()
    mmcms = [i for i in insts if i.of == "MMCME2_ADV"]
    assert len(mmcms) == 1 and mmcms[0].name_override == "ddrphy0_mmcm"
    m = items(mmcms[0])
    assert m["DIVCLK_DIVIDE"] == 1 and m["CLKFBOUT_MULT_F"] == 8.0   # VCO 1066.67 MHz.
    assert domain(m["CLKIN1"]) == "sys" and domain(m["PSCLK"]) == "sys"
    # Fine phase shift on the CK pair only, both at phase 0 (one sub-VCO phase: FINE_PS_FRAC).
    assert m["CLKOUT0_USE_FINE_PS"] == "TRUE" and m["CLKOUT1_USE_FINE_PS"] == "TRUE"
    for n in (2, 3, 4):
        assert f"CLKOUT{n}_USE_FINE_PS" not in m
    assert [m[f"CLKOUT{n}_PHASE"] for n in range(5)] == [0.0, 0.0, 0.0, 0.0, 90.0]
    assert (m["CLKOUT0_DIVIDE_F"], m["CLKOUT1_DIVIDE"], m["CLKOUT2_DIVIDE"],
            m["CLKOUT3_DIVIDE"], m["CLKOUT4_DIVIDE"]) == (8.0, 2, 8, 2, 2)
    # Feedback through a BUFG: the static outputs keep sys' phase.
    bufgs = [items(i) for i in insts if i.of == "BUFG"]
    assert any(b["I"] is m["CLKFBOUT"] and b["O"] is m["CLKFBIN"] for b in bufgs)
    # 112 fine steps of 16.7 ps per tCK.
    assert phy.ps_steps_per_tck == 112 and abs(phy.ps_step_ps - 16.74) < 0.01


def test_ecc_lane_left_out():
    _, insts = phy_and_instances(lanes=8)
    iobufs = [i for i in insts if i.of == "IOBUF"]
    assert len(iobufs) == 64


def test_latencies_match_the_model():
    phy, _ = phy_and_instances()
    s = s7hr_model_settings(400e6/3, 64, cl=7, cwl=6)
    for k in ("cl", "cwl", "read_latency", "write_latency", "nphases", "dfi_databits"):
        assert getattr(phy.settings, k) == getattr(s, k), k
    assert phy.settings.rdphase.reset.value == s.rdphase
    assert phy.settings.wrphase.reset.value == s.wrphase
    # The A7DDRPHY schedule: one memory-clock phase into the ISERDESE2 word.
    cl, cwl, rdphase, wrphase, rl, wl = s7hr_latencies(400e6/3, 7, 6)
    assert (cl, cwl) == (7, 6)

# CK Phase Shift -----------------------------------------------------------------------------------

def test_ck_phase_steps():
    dut = S7HRCKPhase()
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
        assert (yield from status()) == (5, 0)
        # A request while busy is dropped.
        yield from strobe(dut._dec)
        yield from strobe(dut._dec)
        for _ in range(20):
            yield
        assert (yield from status()) == (4, 0)
        assert log["psen"] == 6
        # Unlock: back to the reset phase.
        yield dut.locked.eq(0)
        yield
        yield
        assert (yield from status()) == (0, 0)

    run_simulation(dut, [gen(), mmcm()])

# BIOS header --------------------------------------------------------------------------------------

def test_c_header_has_ck_phase_steps():
    from litedram.init import get_sdram_phy_c_header
    from litedram.modules import MT41K256M8
    phy, _ = phy_and_instances()
    module = MT41K256M8(400e6/3, "1:4")
    header = get_sdram_phy_c_header(phy.settings, module.timing_settings, module.geom_settings)
    assert "#define SDRAM_PHY_S7HRDDRPHY" in header
    assert f"#define SDRAM_PHY_CKPHASE_STEPS {phy.ps_steps_per_tck}" in header
