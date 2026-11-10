#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Crossbar: ports (direct, through a CDC, through a width converter), per-bank arbiters, bank
# machines and the shared data path to the multiplexer.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 260)
    p0   = d.add(Box(15, 30,  120, 50, label="Port 0\nsys, full width"))
    p1   = d.add(Box(15, 105, 120, 50, label="Port 1\nthrough a CDC"))
    p2   = d.add(Box(15, 180, 120, 50, label="Port 2\nwidth converter"))
    xbar = d.add(Box(195, 30, 130, 200, label="Crossbar\nper-bank\narbiters", fill=COLOR_ACCENT))
    bm   = d.add(Box(400, 30, 140, 60, label="Bank machines", fill=COLOR_ACCENT_LIGHT, stack=2))
    mux  = d.add(Box(615, 30, 130, 200, label="Multiplexer"))
    for p in (p0, p1, p2):
        d.add(Arrow((p, "r"), (xbar.x, p.cy), kind="data", heads="both"))
    d.add(Arrow((xbar.x + xbar.w, bm.cy), (bm, "l"), kind="accent", label="commands",
        label_pos=(362, bm.cy - 12)))
    d.add(Arrow((bm.x + bm.w + 8, bm.cy), (mux.x, bm.cy)))
    d.add(Arrow((xbar.x + xbar.w, 200), (mux.x, 200), kind="data", heads="both",
        label="write and read data", label_pos=(470, 187)))
    return d
