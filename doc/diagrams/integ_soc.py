#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Enjoy-Digital <enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# LiteDRAM in a LiteX SoC (add_sdram): the CPU reaches the DRAM through the L2 cache and a crossbar
# port; user logic and the BIST take their own ports.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 300)
    d.add(Container(240, 20, 270, 260, title="LiteDRAMCore", title_pos="br"))
    cpu  = d.add(Box(15, 50, 80, 60, label="CPU"))
    l2   = d.add(Box(130, 50, 80, 60, label="L2 cache", fill=COLOR_ACCENT_LIGHT))
    xbar = d.add(Box(260, 50, 90, 60, label="Crossbar", fill=COLOR_ACCENT))
    ctrl = d.add(Box(390, 50, 100, 60, label="Controller", fill=COLOR_ACCENT))
    phy  = d.add(Box(545, 50, 70, 60, label="PHY", fill=COLOR_ACCENT_LIGHT))
    dram = d.add(Box(650, 50, 95, 60, label="DRAM", fill=COLOR_HARDWARE))
    user = d.add(Box(110, 160, 100, 60, label="User logic"))
    bist = d.add(Box(380, 160, 100, 60, label="BIST", fill=COLOR_ACCENT_LIGHT))
    d.add(Arrow((cpu, "r"), (l2, "l"), kind="data", heads="both"))
    d.add(Arrow((l2, "r"), (xbar, "l"), kind="data", heads="both"))
    d.add(Arrow((xbar, "r"), (ctrl, "l"), kind="data", heads="both"))
    d.add(Arrow((ctrl, "r"), (phy, "l"), kind="data", heads="both", label="DFI", label_pos=(529, 42)))
    d.add(Arrow((phy, "r"), (dram, "l"), kind="data", heads="both"))
    d.add(Arrow((user, "r"), (290, 110), via=[(290, 190)], kind="accent", heads="both"))
    d.add(Arrow((bist, "l"), (325, 110), via=[(325, 190)], kind="data", heads="both"))
    return d
