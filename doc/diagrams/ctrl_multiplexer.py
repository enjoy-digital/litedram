#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Multiplexer state machine: READ and WRITE, the RTW and WTR turnarounds, REFRESH.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 320)
    w = 150
    rd  = state(d, 15,  140, "READ",    w=w, fill=COLOR_ACCENT)
    wr  = state(d, 595, 140, "WRITE",   w=w, fill=COLOR_ACCENT)
    rtw = state(d, 305, 30,  "RTW",     w=w)
    wtr = state(d, 305, 140, "WTR",     w=w)
    ref = state(d, 305, 260, "REFRESH", w=w, fill=COLOR_ACCENT_LIGHT)
    d.add(Arrow((rd, "t"), (rtw, "l"), label="writes waiting", label_pos=(200, rtw.cy - 12)))
    d.add(Arrow((rtw, "r"), (wr, "t"), label="read to write", label_pos=(678, 95),
        label_anchor="start"))
    d.add(Arrow((wr, "l"), (wtr, "r"), label="reads waiting", label_pos=(525, wtr.cy - 12)))
    d.add(Arrow((wtr, "l"), (rd, "r"), label="tWTR", label_pos=(235, wtr.cy - 12)))
    d.add(Arrow((rd, "b"), (ref, "l"), heads="both", label="refresh", label_pos=(200, ref.cy - 12)))
    d.add(Arrow((wr, "b"), (ref, "r"), heads="both", label="refresh", label_pos=(525, ref.cy - 12)))
    return d
