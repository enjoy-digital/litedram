#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import os
import csv
import unittest

import litedram.modules
from litedram.modules import SDRAMModule, DDR3SPDData


def load_spd_reference(filename):
    """Load reference SPD data from a CSV file

    Micron reference SPD data can be obtained from:
    https://www.micron.com/support/tools-and-utilities/serial-presence-detect
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(script_dir, "spd_data", filename)
    data = [0] * 512
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            address = row["Byte Number"]
            value = row["Byte Value"]
            # Ignore ranges (data we care about is specified per byte anyway)
            if len(address.split("-")) == 1:
                data[int(address)] = int(value, 16)
    return data


class TestSPD(unittest.TestCase):
    def test_tck_to_speedgrade(self):
        # Verify that speedgrade transfer rates are calculated correctly from tck
        tck_to_speedgrade = {
            2.5:    800,
            1.875: 1066,
            1.5:   1333,
            1.25:  1600,
            1.071: 1866,
            0.938: 2133,
        }
        for tck, speedgrade in tck_to_speedgrade.items():
            self.assertEqual(speedgrade, DDR3SPDData.speedgrade_freq(tck))

    def test_spd_data(self):
        # Verify that correct _spd_data is added to SDRAMModule
        data = load_spd_reference("MT16KTF1G64HZ-1G6P1.csv")
        module = SDRAMModule.from_spd_data(data, 125e6)
        self.assertEqual(module._spd_data, data)

    def compare_geometry(self, module, module_ref):
        self.assertEqual(module.nbanks, module_ref.nbanks)
        self.assertEqual(module.nrows, module_ref.nrows)
        self.assertEqual(module.ncols, module_ref.ncols)

    def compare_technology_timings(self, module, module_ref, omit=None):
        timings = {"tREFI", "tWTR", "tCCD", "tRRD", "tZQCS"}
        if omit is not None:
            timings -= omit
        for timing in timings:
            txx = getattr(module.technology_timings, timing)
            txx_ref = getattr(module_ref.technology_timings, timing)
            with self.subTest(txx=timing):
                self.assertEqual(txx, txx_ref)

    def compare_speedgrade_timings(self, module, module_ref, omit=None):
        timings = {"tRP", "tRCD", "tWR", "tRFC", "tFAW", "tRAS"}
        if omit is not None:
            timings -= omit
        for freq, speedgrade_timings in module.speedgrade_timings.items():
            if freq == "default":
                continue
            for timing in timings:
                txx = getattr(speedgrade_timings, timing)
                txx_ref = getattr(module_ref.speedgrade_timings[freq], timing)
                with self.subTest(freq=freq, txx=timing):
                    self.assertEqual(txx, txx_ref)

    def compare_modules(self, module, module_ref, omit=None):
        self.assertEqual(module.memtype, module_ref.memtype)
        self.assertEqual(module.rate, module_ref.rate)
        self.compare_geometry(module, module_ref)
        self.compare_technology_timings(module, module_ref, omit=omit)
        self.compare_speedgrade_timings(module, module_ref, omit=omit)

    def test_MT16KTF1G64HZ(self):
        kwargs = dict(clk_freq=125e6, rate="1:4")
        module_ref = litedram.modules.MT16KTF1G64HZ(**kwargs)

        with self.subTest(speedgrade="-1G6"):
            data = load_spd_reference("MT16KTF1G64HZ-1G6P1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            self.compare_modules(module, module_ref)
            sgt = module.speedgrade_timings["1600"]
            self.assertEqual(sgt.tRP,            13.125)
            self.assertEqual(sgt.tRCD,           13.125)
            self.assertEqual(sgt.tRP + sgt.tRAS, 48.125)

        with self.subTest(speedgrade="-1G9"):
            data = load_spd_reference("MT16KTF1G64HZ-1G9E1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            # tRRD it different for this speedgrade
            self.compare_modules(module, module_ref, omit={"tRRD"})
            self.assertEqual(module.technology_timings.tRRD, (4, 5))
            sgt = module.speedgrade_timings["1866"]
            self.assertEqual(sgt.tRP,            13.125)
            self.assertEqual(sgt.tRCD,           13.125)
            self.assertEqual(sgt.tRP + sgt.tRAS, 47.125)

    def test_MT18KSF1G72HZ(self):
        kwargs = dict(clk_freq=125e6, rate="1:4")
        module_ref = litedram.modules.MT18KSF1G72HZ(**kwargs)

        with self.subTest(speedgrade="-1G6"):
            data = load_spd_reference("MT18KSF1G72HZ-1G6E2.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            self.compare_modules(module, module_ref)
            sgt = module.speedgrade_timings["1600"]
            self.assertEqual(sgt.tRP,            13.125)
            self.assertEqual(sgt.tRCD,           13.125)
            self.assertEqual(sgt.tRP + sgt.tRAS, 48.125)

        with self.subTest(speedgrade="-1G4"):
            data = load_spd_reference("MT18KSF1G72HZ-1G4E2.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            self.compare_modules(module, module_ref)
            sgt = module.speedgrade_timings["1333"]
            self.assertEqual(sgt.tRP,            13.125)
            self.assertEqual(sgt.tRCD,           13.125)
            self.assertEqual(sgt.tRP + sgt.tRAS, 49.125)

    def test_MT8JTF12864(self):
        kwargs = dict(clk_freq=125e6, rate="1:4")
        module_ref = litedram.modules.MT8JTF12864(**kwargs)

        data = load_spd_reference("MT8JTF12864AZ-1G4G1.csv")
        module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
        self.compare_modules(module, module_ref)
        sgt = module.speedgrade_timings["1333"]
        self.assertEqual(sgt.tRP,            13.125)
        self.assertEqual(sgt.tRCD,           13.125)
        self.assertEqual(sgt.tRP + sgt.tRAS, 49.125)

    def test_MT8KTF51264(self):
        kwargs = dict(clk_freq=100e6, rate="1:4")
        module_ref = litedram.modules.MT8KTF51264(**kwargs)

        with self.subTest(speedgrade="-1G4"):
            data = load_spd_reference("MT8KTF51264HZ-1G4E1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            self.compare_modules(module, module_ref)
            sgt = module.speedgrade_timings["1333"]
            self.assertEqual(sgt.tRP,            13.125)
            self.assertEqual(sgt.tRCD,           13.125)
            self.assertEqual(sgt.tRP + sgt.tRAS, 49.125)

        with self.subTest(speedgrade="-1G6"):
            data = load_spd_reference("MT8KTF51264HZ-1G6E1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            self.compare_modules(module, module_ref)
            sgt = module.speedgrade_timings["1600"]
            self.assertEqual(sgt.tRP,            13.125)
            self.assertEqual(sgt.tRCD,           13.125)
            self.assertEqual(sgt.tRP + sgt.tRAS, 48.125)

        with self.subTest(speedgrade="-1G9"):
            data = load_spd_reference("MT8KTF51264HZ-1G9P1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            # tRRD different for this timing
            self.compare_modules(module, module_ref, omit={"tRRD"})
            self.assertEqual(module.technology_timings.tRRD, (4, 5))
            sgt = module.speedgrade_timings["1866"]
            self.assertEqual(sgt.tRP,            13.125)
            self.assertEqual(sgt.tRCD,           13.125)
            self.assertEqual(sgt.tRP + sgt.tRAS, 47.125)

    def test_MTA4ATF51264HZ_parsing(self):
        kwargs = dict(clk_freq=100e6, rate="1:4")

        with self.subTest(speedgrade="-2G3"):
            data = load_spd_reference("MTA4ATF51264HZ-2G3B1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            sgt = module.speedgrade_timings["2400"]
            self.assertEqual(sgt.tRP,            13.75)
            self.assertEqual(sgt.tRCD,           13.75)
            self.assertEqual(sgt.tRP + sgt.tRAS, 45.75)

        with self.subTest(speedgrade="-3G2"):
            data = load_spd_reference("MTA4ATF51264HZ-3G2E1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            sgt = module.speedgrade_timings["3200"]
            self.assertEqual(sgt.tRP,            13.75)
            self.assertEqual(sgt.tRCD,           13.75)
            self.assertEqual(sgt.tRP + sgt.tRAS, 45.75)

    # FIXME: when setting timings as seen in SPD, DRAM leveling fails
    @unittest.skip("Using timings from SPD fails DRAM initialzation on this module")
    def test_MTA4ATF51264HZ(self):
        kwargs = dict(clk_freq=100e6, rate="1:4")
        module_ref = litedram.modules.MTA4ATF51264HZ(**kwargs)

        with self.subTest(speedgrade="-2G3"):
            data = load_spd_reference("MTA4ATF51264HZ-2G3B1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            self.compare_modules(module, module_ref)
            sgt = module.speedgrade_timings["2400"]
            self.assertEqual(sgt.tRP,            13.75)
            self.assertEqual(sgt.tRCD,           13.75)
            self.assertEqual(sgt.tRP + sgt.tRAS, 45.75)

        with self.subTest(speedgrade="-3G2"):
            data = load_spd_reference("MTA4ATF51264HZ-3G2E1.csv")
            module = SDRAMModule.from_spd_data(data, kwargs["clk_freq"])
            self.compare_modules(module, module_ref)
            sgt = module.speedgrade_timings["3200"]
            self.assertEqual(sgt.tRP,            13.75)
            self.assertEqual(sgt.tRCD,           13.75)
            self.assertEqual(sgt.tRP + sgt.tRAS, 45.75)
