#
# This file is part of LiteDRAM project.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# LPDDR4, LPDDR5 and RPC Verilator simulations: a SoC with the BIOS, the core and the simulation PHY
# drives a pad-level DRAM simulator that logs the commands and the timing violations.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 260)
    sim  = d.add(Container(20, 20, 720, 220, title="Verilator simulation (simsoc.py)", title_pos="bl"))
    cpu  = d.add(Box(40, 60, 130, 50, label="CPU and BIOS"))
    core = d.add(Box(195, 60, 135, 50, label="LiteDRAM core"))
    phy  = d.add(Box(375, 60, 150, 50, label="Simulation PHY\n(serializers)", fill=COLOR_ACCENT))
    dram = d.add(Box(560, 60, 160, 50, label="DRAM simulator\n(sim.py)", fill=COLOR_ACCENT))
    log  = d.add(Box(560, 140, 160, 50, label="SimLogger\n(commands, errors)", fill=COLOR_ACCENT_LIGHT))
    d.add(Arrow((cpu, "r"), (core, "l"), kind="data", heads="both"))
    d.add(Arrow((core, "r"), (phy, "l"), kind="data", heads="both", label="DFI", label_side="above"))
    d.add(Arrow((phy, "r"), (dram, "l"), kind="accent", heads="both", label="pads", label_side="above"))
    d.add(Arrow((dram, "b"), (log, "t"), kind="feedback"))
    return d
