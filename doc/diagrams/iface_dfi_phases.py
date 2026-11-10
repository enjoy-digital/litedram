#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# DFI phases at a 1:4 ratio: one controller clock spans four DRAM clocks; each DFI phase carries
# the command slot of one DRAM clock and two data beats, so one burst of 8 fits one controller clock.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 215)
    x0, p = 165, 70
    row_name(d, x0, 30, "sys clock")
    clock(d, x0, 30, 4*p, 2)
    row_name(d, x0, 75, "DRAM CK")
    clock(d, x0, 75, p, 8)
    row_name(d, x0, 125, "DFI phase")
    for c in range(2):
        fill = COLOR_ACCENT if c == 0 else COLOR_ACCENT_LIGHT
        cells(d, x0 + c*4*p, 125, [(p, f"phase {i}", fill) for i in range(4)])
    row_name(d, x0, 175, "Data beats")
    for c in range(2):
        fill = COLOR_ACCENT if c == 0 else COLOR_ACCENT_LIGHT
        cells(d, x0 + c*4*p, 175, [(p/2, f"D{i}", fill) for i in range(8)])
    for c in range(3):
        tick(d, x0 + c*4*p, 40, 195)
    return d
