#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Refresher: tREFI timer, postponer, state machine, refresh sequencer and ZQCS executer.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 230)
    timer = d.add(Box(15,  40,  120, 56, label="Timer\ntREFI"))
    post  = d.add(Box(165, 40,  120, 56, label="Postponer"))
    zqt   = d.add(Box(15,  150, 120, 56, label="ZQCS timer"))
    fsm   = d.add(Box(315, 40,  120, 166, label="Refresher\nstate\nmachine", fill=COLOR_ACCENT))
    seq   = d.add(Box(470, 40,  135, 56, label="Sequencer\nPREA, REF", fill=COLOR_ACCENT_LIGHT))
    zqe   = d.add(Box(470, 150, 135, 56, label="Executer\nPREA, ZQCS", fill=COLOR_ACCENT_LIGHT))
    mux   = d.add(Box(640, 40,  105, 166, label="Multiplexer"))
    d.add(Arrow((timer, "r"), (post, "l")))
    d.add(Arrow((post, "r"), (fsm.x, post.cy)))
    d.add(Arrow((zqt, "r"), (fsm.x, zqt.cy)))
    d.add(Arrow((fsm.x + fsm.w, seq.cy), (seq, "l")))
    d.add(Arrow((fsm.x + fsm.w, zqe.cy), (zqe, "l")))
    d.add(Arrow((seq, "r"), (mux.x, seq.cy), kind="accent"))
    d.add(Arrow((zqe, "r"), (mux.x, zqe.cy), kind="accent"))
    return d
