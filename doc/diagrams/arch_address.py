#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Address mapping: the ROW_BANK_COL split of a port word address into row, bank and column.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 230)
    d.add(Text(60, 22, "most significant", size=13, anchor="start"))
    d.add(Text(700, 22, "least significant", size=13, anchor="end"))
    row, bank, col = fields(d, 60, 40, [
        (300, "Row",    COLOR_ACCENT_LIGHT),
        (120, "Bank",   COLOR_ACCENT),
        (220, "Column", COLOR_ACCENT_LIGHT),
    ], h=44)
    act = d.add(Box(row.cx - 80, 150, 160, 56, label="ACT\nrow address"))
    bm  = d.add(Box(bank.cx - 65, 150, 130, 56, label="Bank machine\nselection", fill=COLOR_ACCENT))
    cas = d.add(Box(col.cx - 75, 150, 150, 56, label="RD or WR\ncolumn address"))
    for f, b in ((row, act), (bank, bm), (col, cas)):
        d.add(Arrow((f.cx, f.y + f.h), (b.cx, b.y), kind="data"))
    return d
