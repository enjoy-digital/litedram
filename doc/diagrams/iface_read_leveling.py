#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Read leveling scan: for each bitslip, the delay taps are swept and each read is checked; the
# BIOS keeps the bitslip with the widest passing window and sets the delay at its centre.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 235)
    x0, w, h = 160, 17, 24
    passing = {0: range(4, 21), 1: range(25, 32), 2: (), 3: ()}
    for b in range(4):
        y = 40 + 32*b
        d.add(Text(x0 - 10, y + h/2, f"bitslip {b}", size=13, anchor="end"))
        for t in range(32):
            fill = COLOR_ACCENT if t in passing[b] else COLOR_SHADE
            d.add(Box(x0 + t*w, y, w, h, label="", radius=0, fill=fill))
    d.add(Mark(x0 + 12.5*w, 40 + h/2, color=COLOR_OK))
    d.add(Arrow((x0 + 4*w, 32), (x0 + 21*w, 32), kind="control", heads="both", label="window",
        label_pos=(x0 + 12.5*w, 22)))
    d.add(Arrow((x0, 185), (x0 + 32*w, 185), kind="control", label="delay taps 0 to 31",
        label_pos=(x0 + 16*w, 200), label_side="below"))
    d.add(Box(x0, 210, 17, 17, label="", radius=0, fill=COLOR_ACCENT))
    d.add(Text(x0 + 24, 218, "pass", size=12, anchor="start"))
    d.add(Box(x0 + 80, 210, 17, 17, label="", radius=0, fill=COLOR_SHADE))
    d.add(Text(x0 + 104, 218, "fail", size=12, anchor="start"))
    return d
