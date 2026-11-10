#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# A DRAM cell: an access transistor and a capacitor at the crossing of a word line and a bit line;
# the sense amplifier at the end of the bit line reads the charge and writes it back.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 270)
    d.add(Bus([(230, 40), (640, 40)], kind="data"))
    d.add(Text(220, 40, "word line (row)", size=13, anchor="end"))
    d.add(Bus([(250, 85), (250, 200)], kind="data"))
    d.add(Text(240, 140, "bit line (column)", size=13, anchor="end"))
    tr  = d.add(Box(330, 75, 120, 50, label="Access\ntransistor", fill=COLOR_ACCENT))
    cap = d.add(Box(330, 150, 120, 50, label="Capacitor\none bit", fill=COLOR_ACCENT))
    sa  = d.add(Box(170, 200, 160, 44, label="Sense amplifier", fill=COLOR_ACCENT_LIGHT))
    d.add(Arrow((390, 40), (tr, "t"), kind="control", label="select", label_anchor="start",
        label_pos=(398, 57)))
    d.add(Bus([(330, 100), (250, 100)], kind="data"))
    d.add(Bus([(390, 125), (390, 150)], kind="data"))
    d.add(Arrow((sa, "r"), (tr, "r"), via=[(500, 222), (500, 100)], kind="feedback",
        label="restore", label_anchor="start", label_pos=(510, 160)))
    return d
