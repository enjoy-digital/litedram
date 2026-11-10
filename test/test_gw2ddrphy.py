#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.sim import run_simulation

from litedram.common import get_sys_latency
from litedram.phy.gw2ddrphy import GW2DDRPHY
from test import test_ddr3_phy_settings

CLOCKS = {"sys": 20, "init": 20}

def get_phy(**kwargs):
    return GW2DDRPHY(test_ddr3_phy_settings.TestDDR3PHYSettings.get_pads(), sys_clk_freq=100e6, **kwargs)

def ports(instance):
    return {p.name: p.expr for p in instance.items if isinstance(p, (Instance.Input, Instance.Output))}

def params(instance):
    return {p.name: p.value for p in instance.items if isinstance(p, Instance.Parameter)}

def fabric(phy):
    """Fragment without the Gowin primitives, with the primitives (sorted by creation)."""
    fragment  = phy.get_fragment()
    instances = sorted((s for s in fragment.specials if isinstance(s, Instance)), key=lambda s: s.duid)
    fragment.specials = set(s for s in fragment.specials if not isinstance(s, Instance))
    return fragment, instances


class TestGW2DDRPHY(unittest.TestCase):
    def test_settings(self):
        phy = get_phy()
        cl_sys_latency = get_sys_latency(2, phy.settings.cl)
        self.assertEqual(phy.settings.nphases, 2)
        self.assertEqual(len(phy.dfi.phases), 2)
        self.assertEqual(sum(len(p.wrdata) for p in phy.dfi.phases), 64)
        self.assertEqual(phy.settings.bitslips, 4)
        self.assertEqual(phy.settings.read_latency, cl_sys_latency + 9)

    def test_elaboration(self):
        phy = get_phy()
        _, instances = fabric(phy)
        count = lambda of: sum(s.of == of for s in instances)
        # 1 byte: DQS + DM + 8 DQ output serializers, 8 DQ deserializers.
        self.assertEqual(count("DQS"),       1)
        self.assertEqual(count("OSER4_MEM"), 10)
        self.assertEqual(count("IDES4_MEM"), 8)
        self.assertEqual(count("IOBUF"),     8)
        self.assertEqual(count("DLL"),       1)
        # Clock and commands: a, ba, ras_n, cas_n, we_n (+ clk) on OSER4.
        self.assertEqual(count("OSER4"), 1 + 15 + 3 + 3)

    def test_command_phases(self):
        # Command OSER4 D0/D1 come from DFI phase 0, D2/D3 from phase 1.
        phy = get_phy()
        _, instances = fabric(phy)
        oser4 = [ports(s) for s in instances if s.of == "OSER4"]
        ras_n = oser4[1 + 15 + 3] # After clk, a, ba.
        for n in range(4):
            self.assertIs(ras_n[f"D{n}"].value, phy.dfi.phases[n//2].ras_n)

    def test_write_data_order(self):
        phy = get_phy()
        fragment, instances = fabric(phy)
        serializers = [ports(s) for s in instances
            if s.of == "OSER4_MEM" and params(s)["TCLK_SOURCE"] == "DQSW270"]
        dm, *dq = serializers
        written = [0x13, 0x27, 0x45, 0x89, 0xab, 0xcd, 0xef, 0x01]
        masks   = 0b10100110
        beats   = []

        def generator():
            for p, phase in enumerate(phy.dfi.phases):
                yield phase.wrdata.eq(Cat(*[Constant(written[4*p + n], 8) for n in range(4)]))
                yield phase.wrdata_mask.eq((masks >> (4*p)) & 0xf)
            yield
            yield phy.dfi.phases[phy.settings.wrphase].wrdata_en.eq(1)
            yield
            yield phy.dfi.phases[phy.settings.wrphase].wrdata_en.eq(0)
            for _ in range(16):
                if ((yield dq[0]["TX0"]) & 1) == 0: # Migen sim ~ is not width limited.
                    data = []
                    for n in range(4):
                        value = 0
                        for j, serializer in enumerate(dq):
                            value |= (yield serializer[f"D{n}"]) << j
                        data.append((value, (yield dm[f"D{n}"])))
                    beats.append(data)
                yield

        run_simulation(fragment, generator(), clocks=CLOCKS)
        # DQ driven for the preamble then the two halves of the BL8 burst.
        self.assertEqual(len(beats), 3)
        burst = beats[1] + beats[2]
        self.assertEqual([d for d, _ in burst], written)
        self.assertEqual([m for _, m in burst], [(masks >> n) & 1 for n in range(8)])

    def test_read_data_order(self):
        phy = get_phy()
        fragment, instances = fabric(phy)
        ides = [ports(s) for s in instances if s.of == "IDES4_MEM"]
        read = [0x91, 0x82, 0x74, 0x68, 0x5f, 0x4e, 0x3d, 0x2c]

        def drive(beats):
            for j, deserializer in enumerate(ides):
                for n in range(4):
                    yield deserializer[f"Q{n}"].eq((beats[n] >> j) & 1)

        def generator():
            yield from drive(read[:4])
            yield
            yield from drive(read[4:])
            for _ in range(3):
                yield
            for p, phase in enumerate(phy.dfi.phases):
                rddata = yield phase.rddata
                self.assertEqual([(rddata >> 8*n) & 0xff for n in range(4)], read[4*p:4*p+4])

        run_simulation(fragment, generator(), clocks=CLOCKS)

    def test_read_window(self):
        phy = get_phy()
        fragment, instances = fabric(phy)
        dqs   = next(ports(s) for s in instances if s.of == "DQS")
        rdphase = phy.dfi.phases[phy.settings.rdphase]
        windows = []
        valids  = []

        def generator():
            yield rdphase.rddata_en.eq(1)
            yield
            for _ in range(phy.settings.read_latency + 4):
                yield rdphase.rddata_en.eq(0)
                windows.append((yield dqs["READ"]))
                valids.append((yield phy.dfi.phases[0].rddata_valid))
                yield

        run_simulation(fragment, generator(), clocks=CLOCKS)
        # BL8 read gate two sys cycles (four CK) long, data valid after read_latency.
        self.assertEqual([window for window in windows if window], [0xf, 0xf])
        self.assertEqual(valids.index(1), phy.settings.read_latency)
        self.assertEqual(sum(valids), 1)

    def test_burstdet_sticky(self):
        phy = get_phy()
        fragment, instances = fabric(phy)
        dqs   = next(ports(s) for s in instances if s.of == "DQS")
        burst = dqs["RBURST"]

        def generator():
            yield phy._burstdet_clr.wr_stb.eq(1)
            yield
            yield phy._burstdet_clr.wr_stb.eq(0)
            yield
            self.assertEqual((yield phy._burstdet_seen.status), 0)
            yield burst.eq(1)
            yield
            yield burst.eq(0)
            for _ in range(4):
                yield
            self.assertEqual((yield phy._burstdet_seen.status), 1)
            yield phy._burstdet_clr.wr_stb.eq(1)
            yield
            yield phy._burstdet_clr.wr_stb.eq(0)
            yield
            self.assertEqual((yield phy._burstdet_seen.status), 0)

        run_simulation(fragment, generator(), clocks=CLOCKS)
