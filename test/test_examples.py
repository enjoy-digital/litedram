#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
import os


def build_config(name):
    errors = 0
    os.system("rm -rf examples/build")
    os.system("cd examples && python3 ../litedram/gen.py {}.yml".format(name))
    errors += not os.path.isfile("examples/build/gateware/litedram_core.v")
    os.system("rm -rf examples/build")
    return errors


class TestExamples(unittest.TestCase):
    def test_arty(self):
        errors = build_config("arty")
        self.assertEqual(errors, 0)

    def test_nexys4ddr(self):
        errors = build_config("nexys4ddr")
        self.assertEqual(errors, 0)

    def test_genesys2(self):
        errors = build_config("genesys2")
        self.assertEqual(errors, 0)
