#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# One bank of a DRAM chip: the row decoder opens one row of the cell array into the sense
# amplifiers (the row buffer); the column select moves one burst between the row buffer and DQ.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 320)
    d.add(Box(110, 30, 465, 275, label="", stack=3, fill=COLOR_PANEL))
    d.add(Text(125, 285, "One bank of N", size=18, italic=True, anchor="start"))
    dec = d.add(Box(125, 55, 80, 160, label="Row\ndecoder", fill=COLOR_ACCENT_LIGHT))
    for r in range(6):
        for c in range(17):
            fill = COLOR_ACCENT if r == 2 else COLOR_FILL
            d.add(Box(220 + 20*c, 55 + 20*r, 20, 20, label="", radius=0, fill=fill))
    sa  = d.add(Box(220, 180, 340, 34, label="Sense amplifiers: row buffer", fill=COLOR_ACCENT))
    col = d.add(Box(220, 228, 340, 34, label="Column select", fill=COLOR_ACCENT_LIGHT))
    dq  = d.add(Box(640, 224, 105, 42, label="DQ pins", fill=COLOR_HARDWARE))
    d.add(Arrow((20, 135), (dec, "l"), kind="control", label="ACT: row", label_pos=(62, 123)))
    d.add(Arrow((20, 245), (col, "l"), kind="control", label="RD, WR: column", label_pos=(62, 233)))
    d.add(Arrow((col, "r"), (dq, "l"), kind="data", heads="both", label="burst", label_pos=(618, 233)))
    return d
