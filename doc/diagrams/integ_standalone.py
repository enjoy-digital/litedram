#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Enjoy-Digital <enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Standalone core (litedram_gen): the port groups of the generated litedram_core module.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 330)
    d.add(Container(200, 20, 345, 295, title="litedram_core", title_pos="bl"))
    cpu  = d.add(Box(220, 140, 110, 50, label="Init CPU"))
    core = d.add(Box(380, 45, 145, 145, label="Clocking,\ncontroller,\ncrossbar", fill=COLOR_ACCENT))
    phy  = d.add(Box(380, 225, 145, 60, label="PHY", fill=COLOR_ACCENT_LIGHT))
    clk  = d.add(Box(20, 52, 140, 36, label="clk, rst"))
    ctl  = d.add(Box(20, 147, 140, 36, label="uart or wb_ctrl"))
    dram = d.add(Box(20, 237, 140, 36, label="DRAM", fill=COLOR_HARDWARE))
    port = d.add(Box(585, 60, 160, 36, label="user ports"))
    init = d.add(Box(585, 140, 160, 36, label="init_done, init_error"))
    d.add(Arrow((clk, "r"), (380, 70), kind="control"))
    d.add(Arrow((ctl, "r"), (cpu, "l"), kind="control", heads="both"))
    d.add(Arrow((cpu, "r"), (380, 165), kind="control"))
    d.add(Arrow((dram, "r"), (380, 255), kind="data", heads="both"))
    d.add(Arrow((port, "l"), (525, 78), kind="accent", heads="both"))
    d.add(Arrow((525, 158), (init, "l"), kind="control"))
    d.add(Arrow((452, 190), (452, 225), kind="data", heads="both", label="DFI", label_side="right"))
    return d
