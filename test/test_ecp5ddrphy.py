#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.fhdl.specials import Tristate
from migen.sim import run_simulation

from litedram.phy.ecp5ddrphy import ECP5DDRPHY, ecp5ddrphy_with_ratio
from test import test_ddr3_phy_settings

# Aligned clocks (rising edges of the faster clocks on the sys rising edges).
CLOCKS = {
    1: {"sys": 40, "sys2x": (20, 10), "init": 80},
    2: {"sys": 40, "sys2x": (20, 10), "sys4x": (10, 5), "init": 80},
}

def get_phy(ratio):
    pads = test_ddr3_phy_settings.TestDDR3PHYSettings.get_pads()
    if ratio == 1:
        return ECP5DDRPHY(pads, sys_clk_freq=50e6), pads
    return ecp5ddrphy_with_ratio(ratio)(pads, sys_clk_freq=50e6), pads

def fabric(phy):
    """Fragment without the ECP5 primitives, with the ports of the DQ serializers (per module: DM
    then DQ0-7) and of the DQ tristate controls."""
    fragment  = phy.get_fragment()
    instances = sorted((s for s in fragment.specials if isinstance(s, Instance)), key=lambda s: s.duid)
    def ports(instance):
        return {p.name: p.expr for p in instance.items if isinstance(p, (Instance.Input, Instance.Output))}
    oddr = [ports(s) for s in instances if s.of == "ODDRX2DQA"]
    tsh  = [ports(s) for s in instances if s.of == "TSHX2DQA"]
    fragment.specials = set(s for s in fragment.specials if not isinstance(s, (Instance, Tristate)))
    return fragment, [o for i, o in enumerate(oddr) if i % 9 != 0], tsh

class TestECP5DDRPHY(unittest.TestCase):
    def test_ratio_settings(self):
        phy_12, _ = get_phy(1)
        phy_14, _ = get_phy(2)
        self.assertEqual(phy_14.settings.nphases, 4)
        self.assertEqual(phy_14.settings.dfi_databits, phy_12.settings.dfi_databits//2)
        self.assertEqual(len(phy_14.dfi.phases), 4)
        # PHY timings computed at the PHY clock: same CL/CWL as a 1:2 PHY at 2x the clock.
        phy_12_2x = ECP5DDRPHY(test_ddr3_phy_settings.TestDDR3PHYSettings.get_pads(), sys_clk_freq=100e6)
        self.assertEqual((phy_14.settings.cl, phy_14.settings.cwl), (phy_12_2x.settings.cl, phy_12_2x.settings.cwl))
        # CSRs available through the wrapper (read leveling).
        names = [c.name for c in phy_14.get_csrs()]
        for name in ["dly_sel", "rdly_dq_rst", "rdly_dq_inc", "rdly_dq_bitslip_rst", "rdly_dq_bitslip"]:
            self.assertIn(name, names)

    def write_beats(self, ratio):
        phy, pads = get_phy(ratio)
        fragment, dq_oddr, tsh = fabric(phy)
        self.assertEqual(len(dq_oddr), len(pads.dq))
        s      = phy.settings
        beats  = [0x13, 0x57, 0x24, 0x68, 0x9a, 0xbc, 0xde, 0xf0]
        per    = 8//s.nphases # Beats per DFI phase.
        driven = []

        def controller():
            for _ in range(16):
                yield
            yield phy.dfi.phases[s.wrphase].wrdata_en.eq(1)
            yield
            yield phy.dfi.phases[s.wrphase].wrdata_en.eq(0)
            for _ in range(s.write_latency - 1):
                yield
            for p, phase in enumerate(phy.dfi.phases):
                data = 0
                for b in range(per):
                    data |= beats[p*per + b] << (len(pads.dq)*b)
                yield phase.wrdata.eq(data)
            yield
            for phase in phy.dfi.phases:
                yield phase.wrdata.eq(0)
            for _ in range(16):
                yield

        phy_domain = "sys" if ratio == 1 else "sys2x"
        def monitor():
            for _ in range(200):
                yield
                # DQ driven (TSHX2DQA T inputs low): collect the 4 beats of this PHY cycle.
                if not ((yield tsh[0]["T0"]) & 1):
                    for n in range(4):
                        beat = 0
                        for j, o in enumerate(dq_oddr):
                            beat |= (yield o[f"D{n}"]) << j
                        driven.append(beat)

        generators = {"sys": [controller()]}
        generators.setdefault(phy_domain, []).append(monitor())
        run_simulation(fragment, generators, clocks=CLOCKS[ratio])
        return beats, driven

    def test_write_beats_1_2(self):
        beats, driven = self.write_beats(1)
        self.assertIn(beats, [driven[i:i+8] for i in range(len(driven) - 7)])
