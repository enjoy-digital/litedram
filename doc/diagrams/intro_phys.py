#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# One core on many PHYs: the same controller and frontends, one PHY per FPGA family and memory.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 250)
    d.add(Box(180, 15, 400, 44, label="LiteDRAM core and frontends", fill=COLOR_ACCENT))
    d.add(Text(392, 72, "DFI", size=12, anchor="start"))
    phys = [
        (10,  "Generic SDR\nany FPGA",          "SDR"),
        (135, "Xilinx\n7-Series",               "DDR2, DDR3"),
        (260, "Xilinx\nUS, US+",                "DDR3, DDR4"),
        (385, "Lattice\nECP5, Nexus",           "DDR3"),
        (510, "Gowin\nGW2A, GW5A",              "DDR3"),
        (635, "Xilinx 7-Series\nin development", "LPDDR4/5, RPC"),
    ]
    d.add(Bus([(380, 59), (380, 90)], kind="data"))
    d.add(Bus([(67, 90), (692, 90)], kind="data"))
    for x, label, mem in phys:
        fill = COLOR_ACCENT_LIGHT if x < 600 else COLOR_FILL
        b = d.add(Box(x, 115, 115, 52, label=label, size=13, fill=fill))
        d.add(Arrow((b.cx, 90), (b, "t"), kind="data"))
        m = d.add(Box(x + 5, 195, 105, 36, label=mem, size=13, fill=COLOR_HARDWARE))
        d.add(Arrow((b, "b"), (m, "t"), kind="data", heads="both"))
    return d
