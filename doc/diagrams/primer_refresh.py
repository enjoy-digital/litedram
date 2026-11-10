#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Refresh: every tREFI the controller closes all rows (PREA) and sends REF, then waits tRFC.
# With postponing, several refreshes are grouped and sent back to back.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 210)
    x0 = 140
    T, P, R, W = COLOR_ACCENT_LIGHT, COLOR_SHADE, COLOR_ACCENT, COLOR_FILL
    period = [(110, "traffic", T), (45, "PREA", P), (40, "REF", R), (55, "tRFC", W)]
    d.add(Text(15, 20, "Regular", size=15, italic=True, anchor="start"))
    row_name(d, x0, 65, "Bank use")
    cells(d, x0, 65, period + period + [(100, "traffic", T)])
    span(d, x0 + 155, x0 + 405, 37, "tREFI")
    d.add(Text(15, 115, "Postponed by 2", size=15, italic=True, anchor="start"))
    row_name(d, x0, 160, "Bank use")
    cells(d, x0, 160, [(360, "traffic", T), (45, "PREA", P), (40, "REF", R), (55, "tRFC", W),
        (40, "REF", R), (55, "tRFC", W), (5, "", None)])
    return d
