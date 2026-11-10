#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# LPDDR4 command translation: one DFI READ becomes two subcommands (READ-1, CAS-2), each held two
# DRAM clocks on the CS and CA pins.

from svgdiag import *
from phy_helpers import strip


def build():
    d = Diagram(CANVAS_WIDTH, 175)
    dfi = d.add(Box(15, 60, 120, 70, label="DFI phase\nRD command", fill=COLOR_ACCENT_LIGHT))
    ada = d.add(Box(180, 60, 120, 70, label="Phase\nadapter", fill=COLOR_ACCENT))
    d.add(Text(530, 35, "CS and CA pins", size=FONT_SIZE_SM))
    cells = strip(d, 340, 70, [
        ("READ-1", COLOR_ACCENT),
        ("READ-1", COLOR_ACCENT),
        ("CAS-2",  COLOR_ACCENT_LIGHT),
        ("CAS-2",  COLOR_ACCENT_LIGHT),
    ], w=95, h=50)
    for i, c in enumerate(cells):
        d.add(Text(c.cx, 150, f"clock {i}", size=FONT_SIZE_SM))
    d.add(Arrow((dfi, "r"), (ada, "l"), kind="data"))
    d.add(Arrow((ada, "r", 0.5), (cells[0], "l"), kind="accent"))
    return d
