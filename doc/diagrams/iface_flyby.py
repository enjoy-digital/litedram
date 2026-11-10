#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Fly-by topology: clock, command and address run along the chips to a termination, so each chip
# sees them later; the data lanes go point to point, one per chip.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 300)
    phy = d.add(Box(10, 40, 110, 230, label="PHY", fill=COLOR_ACCENT))
    vtt = d.add(Box(675, 50, 70, 40, label="VTT", fill=COLOR_HARDWARE))
    d.add(Arrow((phy.x + phy.w, 70), (vtt, "l"), kind="control", label="CK, command, address",
        label_pos=(250, 60)))
    xs = [180, 305, 430, 555]
    for i, x in enumerate(xs):
        chip = d.add(Box(x, 115, 95, 50, label=f"DRAM {i}", fill=COLOR_HARDWARE))
        d.add(Arrow((chip.cx, 70), (chip, "t"), kind="control"))
        y = 190 + 22*i
        d.add(Arrow((phy.x + phy.w, y), (chip, "b"), kind="accent", heads="both"))
        d.add(Text(chip.cx + 10, y - 9, f"lane {i}", size=12, anchor="start"))
    return d
