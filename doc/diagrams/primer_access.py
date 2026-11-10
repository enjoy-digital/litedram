#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# One access to a closed row: ACT opens the row, RD reads a burst CL clocks later, PRE closes the
# row; tRCD, CL, tRP and tRAS separate the commands. Clock counts are an example.

from primer_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 230)
    x0, p = 130, 28
    t = lambda n: x0 + n*p
    row_name(d, x0, 35, "CK")
    clock(d, x0, 35, p, 22)
    row_name(d, x0, 110, "Command")
    cells(d, t(0),  110, [(p, "ACT", COLOR_ACCENT)])
    cells(d, t(5),  110, [(p, "RD", COLOR_ACCENT)])
    cells(d, t(15), 110, [(p + 6, "PRE", COLOR_ACCENT_LIGHT)])
    cells(d, t(20), 110, [(p + 6, "ACT", COLOR_ACCENT)])
    row_name(d, x0, 175, "DQ")
    cells(d, t(10), 175, [(4*p, "burst of 8", COLOR_ACCENT)])
    span(d, t(0), t(5), 80, "tRCD")
    span(d, t(15), t(20), 80, "tRP")
    span(d, t(5), t(10), 145, "CL")
    span(d, t(0), t(15), 210, "tRAS")
    return d
