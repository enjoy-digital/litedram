#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# DRAM initialization by the BIOS (sdram_init): software control, PHY reset, JEDEC sequence,
# leveling, hardware control, memory test with retry, init_done.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 240)
    w = 160
    sw   = d.add(Box(15,  40,  w, 46, label="Software control"))
    rst  = d.add(Box(200, 40,  w, 46, label="PHY reset"))
    seq  = d.add(Box(385, 40,  w, 46, label="JEDEC sequence"))
    lev  = d.add(Box(570, 40,  w, 46, label="Leveling", fill=COLOR_ACCENT))
    hw   = d.add(Box(570, 170, w, 46, label="Hardware control"))
    mt   = d.add(Box(385, 170, w, 46, label="Memory test", fill=COLOR_ACCENT_LIGHT))
    ms   = d.add(Box(200, 170, w, 46, label="Speed test"))
    done = d.add(Box(15,  170, w, 46, label="init_done set", fill=COLOR_ACCENT_LIGHT))
    for a, b in ((sw, rst), (rst, seq), (seq, lev)):
        d.add(Arrow((a, "r"), (b, "l")))
    d.add(Arrow((lev.x + 120, lev.y + lev.h), (lev.x + 120, hw.y)))
    for a, b in ((hw, mt), (mt, ms), (ms, done)):
        d.add(Arrow((a, "l"), (b, "r")))
    d.add(Arrow((mt.cx, mt.y), (lev.x + 40, lev.y + lev.h), via=[(mt.cx, 128), (lev.x + 40, 128)],
        kind="feedback", label="retry", label_pos=(mt.cx + 10, 108), label_anchor="start"))
    return d
