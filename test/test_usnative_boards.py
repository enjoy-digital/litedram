#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Optional LiteX-Boards pin extraction checks, not PHY compatibility tests."""

import json
import unittest
import importlib
import importlib.util

from pathlib import Path

from litedram.phy.usnative.pins import extract_ddr_pins


@unittest.skipUnless(importlib.util.find_spec("litex_boards"), "LiteX-Boards not installed")
class TestUSNativeBoards(unittest.TestCase):
    pass


def board_test(row):
    def check(self):
        if row["memory"] != "DDR4":
            self.skipTest("DDR3 is deferred")
        board = importlib.import_module("litex_boards.platforms." + row["board"])
        platform = board.Platform()
        pads = platform.request("ddram", 0)
        pins = extract_ddr_pins(platform, pads)
        self.assertGreater(len(pins.pins), len(pads.dq))
        self.assertEqual(sum(p.signal == "dq" for p in pins.pins), len(pads.dq))
    return check


matrix = json.loads((Path(__file__).parent / "reference/usnative_boards.json").read_text())
for row in matrix["boards"]:
    setattr(TestUSNativeBoards, "test_" + row["board"], board_test(row))
