#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Clocking of the Lattice ECP5 and Gowin DDR3 PHYs: PLL, gated edge clock, divided sys clock and the
# PHY init sequence that stops and resets them.

from svgdiag import *
from phy_helpers import frac, hfrac


def build():
    d = Diagram(CANVAS_WIDTH, 300)
    pll  = d.add(Box(15, 35, 90, 70, label="PLL", fill=COLOR_ACCENT_LIGHT))
    gate = d.add(Box(200, 35, 140, 70, label="Clock gate\nECLKSYNCB\nDHCEN, DHCE", fill=COLOR_ACCENT))
    div  = d.add(Box(395, 35, 140, 70, label="Divider\nCLKDIVF\nCLKDIV", fill=COLOR_ACCENT))
    ctrl = d.add(Box(600, 35, 145, 70, label="Controller\nPHY logic"))
    init = d.add(Box(15, 180, 140, 70, label="PHY init\nsequence", fill=COLOR_ACCENT_LIGHT))
    io   = d.add(Box(600, 210, 145, 70, label="IO gearing\nDQS buffers"))
    d.add(Arrow((pll, "r"), (gate, "l"), kind="control", label="DRAM clock"))
    d.add(Arrow((gate, "r"), (div, "l"), kind="control", label="edge"))
    d.add(Arrow((div, "r"), (ctrl, "l"), kind="control", label="sys"))
    d.add(Arrow((init, "r", frac(init, 195)), (gate, "b", hfrac(gate, 225)), kind="control",
        via=[(225, 195)], label="stop", label_pos=(195, 186)))
    d.add(Arrow((init, "r", frac(init, 235)), (div, "b", hfrac(div, 440)), kind="control",
        via=[(440, 235)], label="reset", label_pos=(410, 226)))
    d.add(Arrow((gate, "b", hfrac(gate, 300)), (io, "l", frac(io, 265)), kind="control",
        via=[(300, 265)], label="edge clock", label_pos=(540, 256)))
    d.add(Arrow((div, "b", hfrac(div, 500)), (io, "l", frac(io, 225)), kind="control",
        via=[(500, 225)], label="sys", label_pos=(560, 216)))
    return d
