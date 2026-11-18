#
# This file is part of LiteDRAM.
#
# Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import difflib
import unittest

from litedram.init import get_sdram_phy_c_header, get_sdram_phy_py_header


def compare_with_reference(test_case, content, filename):
    ref_filename = os.path.join("test", "reference", filename)
    with open(ref_filename, "r") as f:
        reference = f.read().split("\n")
    content = content.split("\n")
    diff = list(difflib.unified_diff(content, reference, fromfile=filename, tofile=ref_filename))
    msg = "Unified diff:\n" + "\n".join(diff)
    test_case.assertEqual(len(diff), 0, msg=msg)

def update_c_reference(content, filename):
    f = open(os.path.join("test", "reference", filename), "w")
    f.write(content)
    f.close()

class TestInit(unittest.TestCase):
    def test_ddr3_dll_off(self):
        from types import SimpleNamespace
        from litedram.init import get_ddr3_phy_init_sequence

        phy    = SimpleNamespace(cl=6, cwl=6, nphases=2, dll_off=True)
        timing = SimpleNamespace(tWR=2)
        sequence, registers = get_ddr3_phy_init_sequence(phy, timing)
        modes = {
            bank: address for label, address, bank, command, delay in sequence
            if label.startswith("Load Mode Register")
        }
        self.assertEqual(modes[1], 0x3) # DLL off, RZQ/7 drive, RTT_NOM disabled.
        self.assertEqual(modes[2], 0x8) # CWL6, RTT_WR disabled.
        self.assertEqual(registers[1], modes[1])

        for cl, cwl in ((5, 6), (6, 5), (7, 7)):
            with self.subTest(cl=cl, cwl=cwl):
                phy.cl, phy.cwl = cl, cwl
                with self.assertRaises(ValueError):
                    get_ddr3_phy_init_sequence(phy, timing)

    def test_ddr3_electrical_settings(self):
        from types import SimpleNamespace
        from litedram.init import get_ddr3_phy_init_sequence
        from litedram.common import PhySettings

        phy = PhySettings(
            phytype="test", memtype="DDR3", databits=16, dfi_databits=32,
            nphases=2, rdphase=1, wrphase=0, cl=6,
            read_latency=0, write_latency=0)
        timing = SimpleNamespace(tWR=2)
        phy.add_electrical_settings(rtt_nom="disabled", ron="34ohm")
        sequence, registers = get_ddr3_phy_init_sequence(phy, timing)
        self.assertEqual(registers[1], 0x2)
        self.assertEqual(phy.rtt_nom, "disabled")

    # DDR4 VrefDQ programming (issue #482).

    def _make_ddr4_settings(self, **phy_kwargs):
        from types import SimpleNamespace
        phy    = SimpleNamespace(cl=11, cwl=9, nphases=2, is_rdimm=False, **phy_kwargs)
        timing = SimpleNamespace(tWR=2, tCCD=2, fine_refresh_mode="1x")
        return phy, timing

    def test_ddr4_vref_dq_disabled_by_default(self):
        # Without vref_dq, the init sequence is unchanged: no VrefDQ training entries, MR6 only
        # carries tCCD_L (legacy behavior, DRAM reset default of 60.00% VDDQ, Range 1, code 0).
        from litedram.init import get_ddr4_phy_init_sequence
        phy, timing = self._make_ddr4_settings()
        sequence, _ = get_ddr4_phy_init_sequence(phy, timing)
        mr6_entries = [(comment, address) for comment, address, ba, cmd, delay in sequence
            if ("Mode Register 6" in comment) or comment.startswith("VrefDQ")]
        self.assertEqual(len(mr6_entries), 1)
        self.assertEqual(mr6_entries[0][0], "Load Mode Register 6")
        self.assertEqual(mr6_entries[0][1] & 0x7f, 0) # No VrefDQ value/range/training bits.

    def test_ddr4_vref_dq_programming_sequence(self):
        # vref_dq=80.15% of VDDQ in Range 1 -> JEDEC code 31 (JESD79-4C Table 15).
        from litedram.init import get_ddr4_phy_init_sequence
        phy, timing = self._make_ddr4_settings(vref_dq=80.15, vref_dq_range=1)
        sequence, _ = get_ddr4_phy_init_sequence(phy, timing)
        vref_entries = [(comment, address, delay) for comment, address, ba, cmd, delay in sequence
            if comment.startswith("VrefDQ")]
        self.assertEqual(len(vref_entries), 2)
        enter_c, enter_a, enter_d = vref_entries[0]
        exit_c,  exit_a,  exit_d  = vref_entries[1]
        self.assertEqual(enter_a & (1 << 7), 1 << 7)  # A7=1: VrefDQ training mode entered.
        self.assertEqual(enter_a & (1 << 6), 0)       # A6=0: Range 1.
        self.assertEqual(enter_a & 0x3f, 31)          # A5:A0: VrefDQ value code 31 (80.15% VDDQ).
        self.assertEqual(exit_a & (1 << 7), 0)        # A7=0: training mode exited.
        self.assertEqual(exit_a & 0x7f, 31)           # Same value on exit (JESD79-4C Figure 27, Note 1).
        self.assertEqual(exit_a >> 10, enter_a >> 10) # tCCD_L application settings preserved.
        for _, _, delay in vref_entries:
            self.assertGreaterEqual(delay, 200)       # >> tVREFDQE/tVREFDQX (150ns min).
        # The exit entry is the application MR6 with the VrefDQ value added.
        mr6 = next(address for comment, address, ba, cmd, delay in sequence
            if comment == "Load Mode Register 6")
        self.assertEqual(exit_a, mr6 | 31)

    def test_ddr4_vref_dq_range2(self):
        # vref_dq=50.20% of VDDQ in Range 2 -> JEDEC code 8, A6=1.
        from litedram.init import get_ddr4_phy_init_sequence
        phy, timing = self._make_ddr4_settings(vref_dq=50.20, vref_dq_range=2)
        sequence, _ = get_ddr4_phy_init_sequence(phy, timing)
        enter_a = next(address for comment, address, ba, cmd, delay in sequence
            if comment.startswith("VrefDQ Training: Range=2"))
        self.assertEqual(enter_a & (1 << 7), 1 << 7)  # Training mode.
        self.assertEqual(enter_a & (1 << 6), 1 << 6)  # A6=1: Range 2.
        self.assertEqual(enter_a & 0x3f, 8)           # 45.00% + 8*0.65% = 50.20% VDDQ.

    def test_ddr4_vref_dq_invalid(self):
        from litedram.init import get_ddr4_phy_init_sequence
        for kwargs in [
            dict(vref_dq=59.90, vref_dq_range=1),  # Below Range 1 (60.00%).
            dict(vref_dq=95.00, vref_dq_range=1),  # Above Range 1 (92.50%).
            dict(vref_dq=80.00, vref_dq_range=1),  # Not an encodable 0.65% step (80.15 is).
            dict(vref_dq=40.00, vref_dq_range=2),  # Below Range 2 (45.00%).
            dict(vref_dq=80.00, vref_dq_range=3),  # Invalid range.
        ]:
            with self.subTest(**kwargs):
                phy, timing = self._make_ddr4_settings(**kwargs)
                with self.assertRaises(AssertionError):
                    get_ddr4_phy_init_sequence(phy, timing)

    def test_ddr4_electrical_settings_vref_dq(self):
        # add_electrical_settings accepts DDR4-only VrefDQ settings.
        from types import SimpleNamespace
        from litedram.common import PhySettings
        from litedram.init import get_ddr4_phy_init_sequence
        phy = PhySettings(
            phytype="test", memtype="DDR4", databits=16, dfi_databits=32,
            nphases=2, rdphase=1, wrphase=0, cl=11,
            read_latency=0, write_latency=0)
        phy.cwl      = 9
        phy.is_rdimm = False
        phy.add_electrical_settings(vref_dq=60.65, vref_dq_range=1)
        timing = SimpleNamespace(tWR=2, tCCD=2, fine_refresh_mode="1x")
        sequence, _ = get_ddr4_phy_init_sequence(phy, timing)
        enter_a = next(address for comment, address, ba, cmd, delay in sequence
            if comment.startswith("VrefDQ Training: Range=1"))
        self.assertEqual(enter_a & 0x3f, 1) # 60.00% + 1*0.65% = 60.65% VDDQ.


    def test_sdr(self):
        from litex_boards.targets.scarabhardware_minispartan6 import BaseSoC
        soc       = BaseSoC()
        c_header  = get_sdram_phy_c_header(
            phy_settings    = soc.sdram.controller.settings.phy,
            timing_settings = soc.sdram.controller.settings.timing,
            geom_settings   = soc.sdram.controller.settings.geom,
        )
        py_header = get_sdram_phy_py_header(
            phy_settings    = soc.sdram.controller.settings.phy,
            timing_settings = soc.sdram.controller.settings.timing
        )
        #update_c_reference(c_header, "sdr_init.h")
        compare_with_reference(self, c_header, "sdr_init.h")
        compare_with_reference(self, py_header, "sdr_init.py")

    def test_ddr3(self):
        from litex_boards.targets.xilinx_kc705 import BaseSoC
        soc       = BaseSoC()
        c_header  = get_sdram_phy_c_header(
            phy_settings    = soc.sdram.controller.settings.phy,
            timing_settings = soc.sdram.controller.settings.timing,
            geom_settings   = soc.sdram.controller.settings.geom,
        )
        py_header = get_sdram_phy_py_header(
            phy_settings    = soc.sdram.controller.settings.phy,
            timing_settings = soc.sdram.controller.settings.timing
        )
        #update_c_reference(c_header, "ddr3_init.h")
        compare_with_reference(self, c_header, "ddr3_init.h")
        compare_with_reference(self, py_header, "ddr3_init.py")

    def test_ddr4(self):
        from litex_boards.targets.xilinx_kcu105 import BaseSoC
        soc       = BaseSoC(max_sdram_size=0x4000000)
        c_header  = get_sdram_phy_c_header(
            phy_settings    = soc.sdram.controller.settings.phy,
            timing_settings = soc.sdram.controller.settings.timing,
            geom_settings   = soc.sdram.controller.settings.geom,
        )
        py_header = get_sdram_phy_py_header(
            phy_settings    = soc.sdram.controller.settings.phy,
            timing_settings = soc.sdram.controller.settings.timing
        )
        #update_c_reference(c_header, "ddr4_init.h")
        compare_with_reference(self, c_header, "ddr4_init.h")
        compare_with_reference(self, py_header, "ddr4_init.py")

    def write_recovery_test(self, module_cls, get_init_sequence, phy_kwargs, decode_wr, encodable, configs):
        # The DRAM times the internal precharge of auto-precharged writes with the mode register
        # write recovery: it must be >= RU(tWR/tCK) and as small as the register can encode.
        import math
        from litedram.common import PhySettings
        for sys_clk_freq, rate in configs:
            with self.subTest(sys_clk_freq=sys_clk_freq, rate=rate):
                nphases = int(rate.split(":")[1])
                module  = module_cls(sys_clk_freq, rate)
                phy     = PhySettings(phytype="test", databits=16, dfi_databits=16*2*nphases,
                    nphases=nphases, rdphase=0, wrphase=0, read_latency=0, write_latency=0, **phy_kwargs)
                sequence, _ = get_init_sequence(phy, module.timing_settings)
                mr0 = [addr for label, addr, bank, cmd, delay in sequence
                    if bank == 0 and label.startswith("Load Mode Register")][-1]
                wr       = decode_wr(mr0)
                tck_ps   = round(1e12/(nphases*sys_clk_freq))
                wr_jedec = math.ceil(module.get("tWR").ns*1e3/tck_ps)
                self.assertGreaterEqual(wr, wr_jedec)
                self.assertEqual(wr, min(v for v in encodable if v >= wr_jedec))

    def test_ddr2_write_recovery(self):
        from litedram.modules import MT47H64M16
        from litedram.init import get_ddr2_phy_init_sequence
        self.write_recovery_test(MT47H64M16, get_ddr2_phy_init_sequence,
            phy_kwargs = dict(memtype="DDR2", cl=4, cwl=3),
            decode_wr  = lambda mr: ((mr >> 9) & 0b111) + 1, # A11:A9 = WR-1
            encodable  = range(2, 9),
            configs    = [(75e6, "1:2"), (100e6, "1:2"), (133e6, "1:2")])

    def test_ddr3_write_recovery(self):
        from litedram.modules import MT41K128M16
        from litedram.init import get_ddr3_phy_init_sequence
        wr_table = {0b001: 5, 0b010: 6, 0b011: 7, 0b100: 8, 0b101: 10, 0b110: 12, 0b111: 14, 0b000: 16}
        self.write_recovery_test(MT41K128M16, get_ddr3_phy_init_sequence,
            phy_kwargs = dict(memtype="DDR3", cl=7, cwl=6),
            decode_wr  = lambda mr0: wr_table[(mr0 >> 9) & 0b111], # A11:A9
            encodable  = wr_table.values(),
            configs    = [(100e6, "1:4"), (125e6, "1:4"), (150e6, "1:4"), (165e6, "1:4"), (100e6, "1:2"), (200e6, "1:2")])

    def test_ddr4_write_recovery(self):
        from litedram.modules import MT40A512M8
        from litedram.init import get_ddr4_phy_init_sequence
        wr_table = {0b0000: 10, 0b0001: 12, 0b0010: 14, 0b0011: 16, 0b0100: 18,
                    0b0101: 20, 0b0110: 24, 0b0111: 22, 0b1000: 26, 0b1001: 28}
        self.write_recovery_test(MT40A512M8, get_ddr4_phy_init_sequence,
            phy_kwargs = dict(memtype="DDR4", cl=14, cwl=11),
            decode_wr  = lambda mr0: wr_table[(((mr0 >> 13) & 0b1) << 3) | ((mr0 >> 9) & 0b111)], # A13,A11:A9
            encodable  = wr_table.values(),
            configs    = [(100e6, "1:4"), (125e6, "1:4"), (250e6, "1:4"), (300e6, "1:4")])

    def test_ddr4_tccd_l(self):
        # MR6 A12:A10 programs tCCD_L in DRAM clocks: it must be >= RU(tCCD_L/tCK) (JEDEC min 4)
        # and <= the CAS to CAS spacing enforced by the controller (tCCD sys_clk cycles).
        import math
        from litedram.common import PhySettings
        from litedram.modules import MT40A512M8, EDY4016A
        from litedram.init import get_ddr4_phy_init_sequence
        tccd_table = {0b000: 4, 0b001: 5, 0b010: 6, 0b011: 7, 0b100: 8}
        for module_cls in [MT40A512M8, EDY4016A]:
            for sys_clk_freq, rate in [(125e6, "1:4"), (200e6, "1:4"), (250e6, "1:4"), (300e6, "1:4"),
                (150e6, "1:8")]:
                with self.subTest(module=module_cls.__name__, sys_clk_freq=sys_clk_freq, rate=rate):
                    nphases = int(rate.split(":")[1])
                    module  = module_cls(sys_clk_freq, rate)
                    phy     = PhySettings(phytype="test", memtype="DDR4", databits=16,
                        dfi_databits=16*2*nphases, nphases=nphases, rdphase=0, wrphase=0,
                        cl=14, cwl=11, read_latency=0, write_latency=0)
                    sequence, _ = get_ddr4_phy_init_sequence(phy, module.timing_settings)
                    mr6 = [addr for label, addr, bank, cmd, delay in sequence
                        if label == "Load Mode Register 6"][-1]
                    tccd_l = tccd_table[(mr6 >> 10) & 0b111]
                    tck_ps = round(1e12/(nphases*sys_clk_freq))
                    ck, ns = module.get("tCCD")
                    self.assertEqual(tccd_l, max(4, ck, math.ceil(ns*1e3/tck_ps)))
                    self.assertLessEqual(tccd_l, module.timing_settings.tCCD*nphases)
                    self.assertEqual(mr6 & ~(0b111 << 10), 0) # No other MR6 field set.
