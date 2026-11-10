#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Clock domains: port clock, sys (crossbar and controller), PHY fast clocks, DRAM clock.

from core_helpers import *


def boundary(d, x, top, bottom, gaps):
    """Dotted clock boundary from top to bottom, interrupted where it crosses a box."""
    y = top
    for g0, g1 in gaps:
        d.add(Bus([(x, y), (x, g0)], dash=DASH_FEEDBACK))
        y = g1
    d.add(Bus([(x, y), (x, bottom)], dash=DASH_FEEDBACK))


def build():
    d = Diagram(CANVAS_WIDTH, 200)
    user = d.add(Box(15,  80, 110, 60, label="User logic"))
    cdc  = d.add(Box(165, 80, 90,  60, label="Port CDC", fill=COLOR_ACCENT_LIGHT))
    core = d.add(Box(295, 80, 150, 60, label="Crossbar and\ncontroller", fill=COLOR_ACCENT))
    phy  = d.add(Box(485, 80, 120, 60, label="PHY\nserializers", fill=COLOR_ACCENT_LIGHT))
    dram = d.add(Box(655, 80, 90,  60, label="DRAM", fill=COLOR_HARDWARE))
    for a, b in ((user, cdc), (cdc, core), (core, phy), (phy, dram)):
        d.add(Arrow((a, "r"), (b, "l"), kind="data", heads="both"))
    boundary(d, cdc.cx, 45, 185, [(cdc.y, cdc.y + cdc.h)])
    boundary(d, phy.cx, 45, 185, [(phy.y, phy.y + phy.h)])
    boundary(d, 630,    45, 185, [])
    d.add(Text((15 + cdc.cx)/2,     30, "port clock", size=13))
    d.add(Text((cdc.cx + phy.cx)/2, 30, "sys", size=13))
    d.add(Text((phy.cx + 630)/2,    30, "sys2x, sys4x", size=13))
    d.add(Text((630 + 760)/2,       30, "DRAM clock", size=13))
    return d
