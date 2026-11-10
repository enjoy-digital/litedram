#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Enjoy-Digital <enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Clocking of a 7-Series DDR3 PHY at 1:4 (Arty A7 target): one PLL makes sys, sys4x, the 90 degree
# sys4x_dqs and the IDELAYCTRL reference.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 290)
    osc  = d.add(Box(15, 130, 100, 50, label="Oscillator", fill=COLOR_HARDWARE))
    pll  = d.add(Box(160, 40, 90, 230, label="PLL", fill=COLOR_ACCENT))
    phy  = d.add(Box(470, 40, 130, 150, label="PHY", fill=COLOR_ACCENT))
    idly = d.add(Box(470, 220, 130, 50, label="IDELAYCTRL", fill=COLOR_ACCENT_LIGHT))
    dram = d.add(Box(650, 90, 95, 50, label="DRAM", fill=COLOR_HARDWARE))
    d.add(Arrow((osc, "r"), (pll, "l"), kind="control", label="clk100", label_pos=(137, 146)))
    d.add(Arrow((250, 70),  (470, 70),  kind="control", label="sys", label_pos=(360, 62)))
    d.add(Arrow((250, 115), (470, 115), kind="control", label="sys4x", label_pos=(360, 107)))
    d.add(Arrow((250, 160), (470, 160), kind="control", label="sys4x_dqs (90 degrees)",
        label_pos=(360, 152)))
    d.add(Arrow((250, 245), (idly, "l"), kind="control", label="idelay (200 MHz)",
        label_pos=(360, 237)))
    d.add(Arrow((idly, "t"), (phy, "b"), kind="control"))
    d.add(Arrow((phy, "r"), (dram, "l"), kind="data", heads="both"))
    return d
