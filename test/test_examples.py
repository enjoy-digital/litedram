#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
import os


def build_config(name):
    errors = 0
    os.system(f"rm -rf examples/{name}")
    os.system(f"mkdir -p examples/{name} && cd examples/{name} && python3 ../../litedram/gen.py ../{name}.yml")
    errors += not os.path.isfile(f"examples/{name}/build/gateware/litedram_core.v")
    os.system(f"rm -rf examples/{name}")
    return errors


class TestExamples(unittest.TestCase):
    def test_ulx3s(self):
        errors = build_config("ulx3s")
        self.assertEqual(errors, 0)

    def test_arty(self):
        errors = build_config("arty")
        self.assertEqual(errors, 0)

    def test_nexys4ddr(self):
        errors = build_config("nexys4ddr")
        self.assertEqual(errors, 0)

    def test_genesys2(self):
        errors = build_config("genesys2")
        self.assertEqual(errors, 0)
