# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
# License: BSD

import os
import csv
import unittest

import litedram.modules
from litedram.modules import SDRAMModule


def load_spd_reference(filename):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(script_dir, "spd_data", filename)
    data = [0] * 256
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            address = row["Byte Number"]
            value = row["Byte Value"]
            # ignore ranges (timings are specified per byte)
            if len(address.split("-")) == 1:
                data[int(address)] = int(value, 16)
    return data


class TestSPD(unittest.TestCase):
    def compare_geometry(self, module, module_ref):
        self.assertEqual(module.memtype, module_ref.memtype)
        self.assertEqual(module.nbanks, module_ref.nbanks)
        self.assertEqual(module.nrows, module_ref.nrows)
        self.assertEqual(module.ncols, module_ref.ncols)

    def compare_timings(self, module, module_ref):
        self.assertEqual(module.memtype, module_ref.memtype)

        # technology timings
        compared_timings = ["tREFI", "tWTR", "tCCD", "tRRD", "tZQCS"]
        for timing in compared_timings:
            txx = getattr(module.technology_timings, timing)
            txx_ref = getattr(module_ref.technology_timings, timing)
            with self.subTest(txx="technology_timings:" + timing):
                self.assertEqual(txx, txx_ref)

        # speedgrade timings
        compared_timings = ["tRP", "tRCD", "tWR", "tRFC", "tFAW", "tRAS"]
        for freq, timings in module.speedgrade_timings.items():
            for timing in compared_timings:
                txx = getattr(timings, timing)
                txx_ref = getattr(module_ref.speedgrade_timings[freq], timing)
                with self.subTest(txx="speedgrade_timings:" + timing):
                    self.assertEqual(txx, txx_ref)

    def test_MT16KTF1G64HZ(self):
        data = load_spd_reference("MT16KTF1G64HZ-1G6N1.csv")
        kwargs = dict(clk_freq=125e6, rate="1:4")
        module_ref = litedram.modules.MT16KTF1G64HZ(**kwargs)
        module = SDRAMModule.from_spd_data(data, **kwargs)
        self.compare_geometry(module, module_ref)
        sgt = module.speedgrade_timings["1600"]
        self.assertEqual(sgt.tRP,            13.125)
        self.assertEqual(sgt.tRCD,           13.125)
        self.assertEqual(sgt.tRP + sgt.tRAS, 48.125)

    def test_MT18KSF1G72HZ(self):
        data = load_spd_reference("MT18KSF1G72HZ-1G6E2.csv")
        kwargs = dict(clk_freq=125e6, rate="1:4")
        module_ref = litedram.modules.MT18KSF1G72HZ(**kwargs)
        module = SDRAMModule.from_spd_data(data, **kwargs)
        self.compare_geometry(module, module_ref)
        sgt = module.speedgrade_timings["1600"]
        self.assertEqual(sgt.tRP,            13.125)
        self.assertEqual(sgt.tRCD,           13.125)
        self.assertEqual(sgt.tRP + sgt.tRAS, 48.125)

    def test_MT8JTF12864(self):
        data = load_spd_reference("MT8JTF12864AZ-1G4G1.csv")
        kwargs = dict(clk_freq=125e6, rate="1:4")
        module_ref = litedram.modules.MT8JTF12864(**kwargs)
        module = SDRAMModule.from_spd_data(data, **kwargs)
        self.compare_geometry(module, module_ref)
        sgt = module.speedgrade_timings["1333"]
        self.assertEqual(sgt.tRP,            13.125)
        self.assertEqual(sgt.tRCD,           13.125)
        self.assertEqual(sgt.tRP + sgt.tRAS, 49.125)

    def test_MT8KTF51264(self):
        data = load_spd_reference("MT8KTF51264HZ-1G4E1.csv")
        kwargs = dict(clk_freq=100e6, rate="1:4")
        module_ref = litedram.modules.MT8KTF51264(**kwargs)
        module = SDRAMModule.from_spd_data(data, **kwargs)
        self.compare_geometry(module, module_ref)
        sgt = module.speedgrade_timings["1333"]
        self.assertEqual(sgt.tRP,            13.125)
        self.assertEqual(sgt.tRCD,           13.125)
        self.assertEqual(sgt.tRP + sgt.tRAS, 49.125)
