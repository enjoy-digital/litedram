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
