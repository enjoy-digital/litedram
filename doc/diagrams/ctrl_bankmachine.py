#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Bank machine state machine: REGULAR, PRECHARGE, AUTOPRECHARGE, TRP, ACTIVATE, TRCD, REFRESH.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 390)
    w = 150
    reg  = state(d, 15,  150, "REGULAR",       w=w, fill=COLOR_ACCENT)
    pre  = state(d, 245, 50,  "PRECHARGE",     w=w, fill=COLOR_ACCENT_LIGHT)
    apre = state(d, 245, 150, "AUTOPRECHARGE", w=w)
    trp  = state(d, 425, 50,  "TRP",           w=w)
    act  = state(d, 600, 150, "ACTIVATE",      w=w, fill=COLOR_ACCENT_LIGHT)
    trcd = state(d, 425, 260, "TRCD",          w=w)
    ref  = state(d, 15,  330, "REFRESH",       w=w)
    bot  = reg.y + reg.h
    d.add(Arrow((40, reg.y), (720, act.y), via=[(40, 22), (720, 22)], label="no open row",
        label_pos=(380, 10)))
    d.add(Arrow((100, reg.y), (pre, "l"), via=[(100, pre.cy)], label="row miss",
        label_pos=(172, pre.cy - 12)))
    d.add(Arrow((pre, "r"), (trp, "l")))
    d.add(Arrow((reg, "r"), (apre, "l"), label="CAS with\nprecharge", label_pos=(205, 150)))
    d.add(Arrow((apre, "r"), (trp, "b")))
    d.add(Arrow((trp, "r"), (690, act.y), via=[(690, trp.cy)], label="tRP",
        label_pos=(682, 112), label_anchor="end"))
    d.add(Arrow((act, "b"), (trcd, "r"), label="ACT sent", label_pos=(683, 240),
        label_anchor="start"))
    d.add(Arrow((trcd, "l"), (120, bot), via=[(120, trcd.cy)], label="tRCD",
        label_pos=(300, trcd.cy - 12)))
    d.add(Arrow((50, bot), (50, ref.y), heads="both", label="refresh", label_pos=(58, 250),
        label_anchor="start"))
    return d
