#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.sim import run_simulation

from litedram.phy.gw5ddrphy import GW5DDRPHY
from test import test_ddr3_phy_settings


class TestGW5DDRPHY(unittest.TestCase):
    def test_quarter_rate_data_order(self):
        phy = GW5DDRPHY(test_ddr3_phy_settings.TestDDR3PHYSettings.get_pads(),
            nphases      = 4,
            sys_clk_freq = 25e6,
            dll_off      = True,
        )
        fragment  = phy.get_fragment()
        instances = sorted((s for s in fragment.specials if isinstance(s, Instance)), key=lambda s: s.duid)

        def ports(instance):
            return {p.name: p.expr for p in instance.items if isinstance(p, (Instance.Input, Instance.Output))}

        serializers = []
        for instance in instances:
            if instance.of == "OSER8_MEM":
                params = {p.name: p.value for p in instance.items if isinstance(p, Instance.Parameter)}
                if params["TCLK_SOURCE"] == "DQSW270":
                    serializers.append(ports(instance))
        dm, *dq = serializers
        ides = [ports(s) for s in instances if s.of == "IDES8_MEM"]

        # Simulate the fabric data path, driving the memory primitive outputs directly.
        fragment.specials.clear()
        written = [0x13, 0x27, 0x45, 0x89, 0xab, 0xcd, 0xef, 0x01]
        read    = [0x91, 0x82, 0x74, 0x68, 0x5f, 0x4e, 0x3d, 0x2c]
        masks   = 0b10100110

        def generator():
            for p, phase in enumerate(phy.dfi.phases):
                yield phase.wrdata.eq(written[2*p] | written[2*p+1] << 8)
                yield phase.wrdata_mask.eq((masks >> (2*p)) & 3)
            for j, deserializer in enumerate(ides):
                for n in range(8):
                    yield deserializer[f"Q{n}"].eq((read[n] >> j) & 1)
            for _ in range(4):
                yield
            for n in range(8):
                actual = 0
                for j, serializer in enumerate(dq):
                    actual |= (yield serializer[f"D{n}"]) << j
                self.assertEqual(actual, written[n])
                self.assertEqual((yield dm[f"D{n}"]), (masks >> n) & 1)
            for p, phase in enumerate(phy.dfi.phases):
                self.assertEqual((yield phase.rddata), read[2*p] | read[2*p+1] << 8)

        run_simulation(fragment, generator(), clocks={"sys": 40, "init": 20, "sys4x_i": 10})

    def test_quarter_rate_short_burst_flag(self):
        phy = GW5DDRPHY(test_ddr3_phy_settings.TestDDR3PHYSettings.get_pads(),
            nphases      = 4,
            sys_clk_freq = 25e6,
            dll_off      = True,
        )
        fragment = phy.get_fragment()
        dqs      = next(s for s in fragment.specials if isinstance(s, Instance) and s.of == "DQS")
        burst    = next(p.expr for p in dqs.items if isinstance(p, Instance.Output) and p.name == "RBURST")
        fragment.specials = {s for s in fragment.specials if not isinstance(s, Instance)}

        def fast_generator():
            yield burst.eq(0)
            for _ in range(8):
                yield
            # A ten-unit pulse from t=85 to t=95 misses the sys edges at t=60/100.
            yield burst.eq(1)
            yield
            yield burst.eq(0)

        def sys_generator():
            yield phy._burstdet_clr.wr_stb.eq(1)
            yield
            yield phy._burstdet_clr.wr_stb.eq(0)
            for _ in range(8):
                yield
            self.assertEqual((yield phy._burstdet_seen.status), 1)
            yield phy._burstdet_clr.wr_stb.eq(1)
            yield
            yield phy._burstdet_clr.wr_stb.eq(0)
            for _ in range(4):
                yield
            self.assertEqual((yield phy._burstdet_seen.status), 0)

        run_simulation(fragment, {"sys": sys_generator(), "sys4x_i": fast_generator()},
            clocks = {"sys": 40, "sys4x_i": 10, "init": 20},
        )

    def test_supported_ratios(self):
        for nphases in (2, 4):
            phy = GW5DDRPHY(test_ddr3_phy_settings.TestDDR3PHYSettings.get_pads(), nphases=nphases)
            self.assertEqual(sum(len(p.wrdata) for p in phy.dfi.phases), 64)
            self.assertEqual(phy.settings.bitslips, 2*nphases)
        with self.assertRaises(ValueError):
            GW5DDRPHY(test_ddr3_phy_settings.TestDDR3PHYSettings.get_pads(), nphases=3)

    def test_quarter_rate_read_window(self):
        for dll_off, expected in ((True, [0xf]), (False, [0xe, 0x1])):
            with self.subTest(dll_off=dll_off):
                phy = GW5DDRPHY(test_ddr3_phy_settings.TestDDR3PHYSettings.get_pads(),
                    nphases      = 4,
                    sys_clk_freq = 25e6 if dll_off else 100e6,
                    dll_off      = dll_off,
                )
                fragment = phy.get_fragment()
                dqs      = next(s for s in fragment.specials if isinstance(s, Instance) and s.of == "DQS")
                read     = next(p.expr for p in dqs.items if isinstance(p, Instance.Input) and p.name == "READ")
                fragment.specials.clear()
                windows = []

                def generator():
                    yield phy.dfi.phases[phy.settings.rdphase].rddata_en.eq(1)
                    yield
                    yield phy.dfi.phases[phy.settings.rdphase].rddata_en.eq(0)
                    for _ in range(10):
                        windows.append((yield read))
                        yield

                run_simulation(fragment, generator(), clocks={"sys": 40, "sys4x_i": 10, "init": 20})
                # Keep the BL8 gate four CK long, delayed one CK for DLL-on.
                self.assertEqual([window for window in windows if window], expected)
