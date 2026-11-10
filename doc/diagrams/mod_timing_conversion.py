#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Conversion of a module timing (DRAM clocks and nanoseconds) into controller clock cycles.

from svgdiag import *
from phy_helpers import frac


def build():
    d = Diagram(CANVAS_WIDTH, 250)
    mod  = d.add(Box(15, 90, 110, 70, label="Module\nck, ns", fill=COLOR_ACCENT_LIGHT))
    ns   = d.add(Box(170, 30, 135, 70, label="ns to cycles\nplus margin", fill=COLOR_ACCENT))
    ck   = d.add(Box(170, 150, 135, 70, label="ck to cycles\nck / ratio", fill=COLOR_ACCENT))
    mx   = d.add(Box(345, 90, 90, 70, label="Maximum", fill=COLOR_ACCENT))
    ts   = d.add(Box(475, 90, 130, 70, label="TimingSettings\nsys cycles"))
    ctrl = d.add(Box(640, 90, 105, 70, label="Controller"))
    d.add(Arrow((mod, "r", frac(mod, 110)), (ns, "l"), kind="data", via=[(147, 110), (147, 65)]))
    d.add(Arrow((mod, "r", frac(mod, 140)), (ck, "l"), kind="data", via=[(147, 140), (147, 185)]))
    d.add(Arrow((ns, "r"), (mx, "l", frac(mx, 110)), kind="data", via=[(325, 65), (325, 110)]))
    d.add(Arrow((ck, "r"), (mx, "l", frac(mx, 140)), kind="data", via=[(325, 185), (325, 140)]))
    d.add(Arrow((mx, "r"), (ts, "l"), kind="accent"))
    d.add(Arrow((ts, "r"), (ctrl, "l"), kind="data"))
    return d
