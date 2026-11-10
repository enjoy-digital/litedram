#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Row hit against row miss: reads to the open row follow each other every tCCD and keep DQ busy;
# a read to another row of the same bank first pays tRP and tRCD. Clock counts are an example.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 270)
    x0, p = 150, 28
    t = lambda n: x0 + n*p
    d.add(Text(15, 20, "Row hit", size=15, italic=True, anchor="start"))
    row_name(d, x0, 50, "Command")
    for n in (0, 4, 8):
        cells(d, t(n), 50, [(p, "RD", COLOR_ACCENT)])
    row_name(d, x0, 100, "DQ")
    cells(d, t(5), 100, [(4*p, "burst", COLOR_ACCENT), (4*p, "burst", COLOR_ACCENT_LIGHT),
        (4*p, "burst", COLOR_ACCENT)])
    span(d, t(0), t(4), 75, "tCCD")
    d.add(Text(15, 140, "Row miss", size=15, italic=True, anchor="start"))
    row_name(d, x0, 190, "Command")
    cells(d, t(0),  190, [(p + 6, "PRE", COLOR_ACCENT_LIGHT)])
    cells(d, t(5),  190, [(p + 6, "ACT", COLOR_ACCENT_LIGHT)])
    cells(d, t(10), 190, [(p, "RD", COLOR_ACCENT)])
    row_name(d, x0, 245, "DQ")
    cells(d, t(15), 245, [(4*p, "burst", COLOR_ACCENT)])
    span(d, t(0), t(5) - 3, 162, "tRP")
    span(d, t(5) + 3, t(10), 162, "tRCD")
    span(d, t(10), t(15), 220, "CL")
    return d
