#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# DQS against DQ: on writes the controller sends DQS centred in the data eye; on reads the DRAM
# sends DQS edge aligned with the data, and the receiver shifts it by a quarter clock.

from primer_helpers import *


def panel(d, x0, title, centred):
    h = 40
    d.add(Text(x0 - 60, 20, title, size=15, italic=True, anchor="start"))
    row_name(d, x0, 60, "DQS")
    # DQS low for half a period (the end of the preamble), then rising edges at x0 + h, x0 + 3h...
    clock(d, x0, 60, 2*h, 3, phase=0.5)
    row_name(d, x0, 115, "DQ")
    # Write: each bit centred on a DQS edge. Read: each bit starts on a DQS edge.
    off = -h/2 if centred else 0
    for k in range(1, 7):
        cells(d, x0 + k*h + off, 115, [(h, f"D{k - 1}", COLOR_ACCENT if k % 2 else COLOR_ACCENT_LIGHT)])
    for k in range(1, 7):
        tick(d, x0 + k*h, 70, 135)


def build():
    d = Diagram(CANVAS_WIDTH, 150)
    panel(d, 80,  "Write: DQS centred", True)
    panel(d, 440, "Read: DQS edge aligned", False)
    return d
