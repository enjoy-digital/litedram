#
# This file is part of LiteDRAM project.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Debug views: what the BIOS tests, the controller registers, LiteScope and the leveling tables tell
# about each part of the memory path.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 320)
    dp = d.add(Container(20, 20, 720, 120, title="Memory path", title_pos="tl"))
    cpu  = d.add(Box(40, 70, 150, 46, label="CPU and L2"))
    ctrl = d.add(Box(215, 70, 150, 46, label="Crossbar and\ncontroller"))
    phy  = d.add(Box(390, 70, 150, 46, label="PHY"))
    dram = d.add(Box(565, 70, 150, 46, label="DRAM", fill=COLOR_HARDWARE))
    d.add(Arrow((cpu, "r"), (ctrl, "l"), kind="data", heads="both"))
    d.add(Arrow((ctrl, "r"), (phy, "l"), kind="data", heads="both", label="DFI", label_side="above"))
    d.add(Arrow((phy, "r"), (dram, "l"), kind="data", heads="both"))
    dbg = d.add(Container(20, 180, 720, 120, title="Debug views", title_pos="br"))
    mt   = d.add(Box(40, 205, 150, 46, label="memtest,\nmemspeed", fill=COLOR_ACCENT_LIGHT))
    bist = d.add(Box(215, 205, 150, 46, label="BIST, ECC,\nbandwidth", fill=COLOR_ACCENT))
    ls   = d.add(Box(390, 205, 150, 46, label="LiteScope\non the DFI", fill=COLOR_ACCENT))
    lvl  = d.add(Box(565, 205, 150, 46, label="Leveling\ntables", fill=COLOR_ACCENT))
    for a, b in ((cpu, mt), (ctrl, bist), (phy, ls), (dram, lvl)):
        d.add(Arrow((a, "b"), (b, "t"), kind="feedback"))
    return d
