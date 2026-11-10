#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Clocking of the 7-Series DDR PHY at 1:4 without ODELAYE2: sys, sys4x, sys4x_dqs and the IDELAYCTRL
# reference clock.

from svgdiag import *
from phy_helpers import frac


def build():
    d = Diagram(CANVAS_WIDTH, 275)
    ref  = d.add(Box(15, 110, 100, 60, label="Board\nclock", fill=COLOR_HARDWARE))
    pll  = d.add(Box(165, 15, 110, 245, label="PLL or\nMMCM", fill=COLOR_ACCENT_LIGHT))
    ctrl = d.add(Box(440, 15, 150, 45, label="Controller"))
    ser  = d.add(Box(440, 80, 150, 50, label="DQ, CK\nserializers", fill=COLOR_ACCENT))
    dqs  = d.add(Box(440, 150, 150, 45, label="DQS serializers", fill=COLOR_ACCENT))
    idc  = d.add(Box(440, 215, 150, 45, label="IDELAYCTRL"))
    dly  = d.add(Box(630, 215, 115, 45, label="IO delays"))
    d.add(Arrow((ref, "r"), (pll, "l", frac(pll, 140)), kind="control"))
    d.add(Arrow((pll, "r", frac(pll, 37.5)), (ctrl, "l"), kind="control", label="sys"))
    d.add(Arrow((pll, "r", frac(pll, 105)), (ser, "l"), kind="control", label="sys, sys4x"))
    d.add(Arrow((pll, "r", frac(pll, 172.5)), (dqs, "l"), kind="control", label="sys4x_dqs, 90 degrees"))
    d.add(Arrow((pll, "r", frac(pll, 237.5)), (idc, "l"), kind="control", label="iodelay"))
    d.add(Arrow((idc, "r"), (dly, "l"), kind="feedback"))
    return d
