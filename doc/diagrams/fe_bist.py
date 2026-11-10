#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# BIST: generator writes a pattern through one port, checker reads it back through another and
# counts the errors; both are driven by registers.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 230)
    regs = d.add(Box(15,  40,  110, 156, label="Registers"))
    gen  = d.add(Box(200, 40,  150, 56, label="BIST generator", fill=COLOR_ACCENT))
    chk  = d.add(Box(200, 140, 150, 56, label="BIST checker", fill=COLOR_ACCENT))
    xbar = d.add(Box(430, 40,  100, 156, label="Crossbar", fill=COLOR_ACCENT_LIGHT))
    dram = d.add(Box(600, 40,  145, 156, label="Controller\nand DRAM", fill=COLOR_HARDWARE))
    d.add(Arrow((regs.x + regs.w, gen.cy), (gen, "l"), label="start", label_pos=(162, gen.cy - 11)))
    d.add(Arrow((chk, "l"), (regs.x + regs.w, chk.cy), label="errors",
        label_pos=(162, chk.cy - 11)))
    d.add(Arrow((gen, "r"), (xbar.x, gen.cy), kind="accent", label="writes",
        label_pos=(390, gen.cy - 12)))
    d.add(Arrow((xbar.x, chk.cy), (chk, "r"), kind="accent", label="reads",
        label_pos=(390, chk.cy - 12)))
    d.add(Arrow((xbar.x + xbar.w, 118), (dram.x, 118), kind="data", heads="both"))
    return d
