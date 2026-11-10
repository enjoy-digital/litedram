#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# The signals between the FPGA and the DRAM: clock, command and address from the PHY, control pins,
# and the bidirectional data (DQ, DM) and strobes (DQS) per byte lane.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 290)
    d.add(Container(10, 15, 330, 265, title="FPGA", title_pos="bl"))
    ctrl = d.add(Box(25, 55, 110, 170, label="Controller", fill=COLOR_ACCENT_LIGHT))
    phy  = d.add(Box(195, 40, 120, 200, label="PHY", fill=COLOR_ACCENT))
    dram = d.add(Box(560, 40, 180, 200, label="DRAM", fill=COLOR_HARDWARE))
    d.add(Arrow((ctrl, "r"), (phy.x, ctrl.cy), kind="data", heads="both", label="DFI",
        label_pos=(165, 128)))
    rows = [
        (65,  "CK, CK#",            "control", "end"),
        (105, "command, address",   "control", "end"),
        (145, "CKE, ODT, RESET#",   "control", "end"),
        (185, "DQ, DM: data",       "data",    "both"),
        (225, "DQS, DQS#: strobe",  "accent",  "both"),
    ]
    for y, label, kind, heads in rows:
        d.add(Arrow((315, y), (560, y), kind=kind, heads=heads, label=label))
    return d
