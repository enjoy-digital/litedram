#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# DRAM FIFO: pre-FIFO, bypass, post-FIFO and the DRAM path through the converters.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 320)
    pre   = d.add(Box(60,  40,  130, 46, label="Pre-FIFO", fill=COLOR_ACCENT_LIGHT))
    post  = d.add(Box(570, 40,  130, 46, label="Post-FIFO", fill=COLOR_ACCENT_LIGHT))
    prec  = d.add(Box(60,  150, 130, 46, label="Pre-converter"))
    postc = d.add(Box(570, 150, 130, 46, label="Post-converter"))
    dram  = d.add(Box(315, 140, 130, 50, label="DRAM", fill=COLOR_HARDWARE))
    fifo  = d.add(Box(290, 250, 180, 50, label="DRAM FIFO", fill=COLOR_ACCENT))
    d.add(Arrow((10, pre.cy), (pre, "l"), kind="data", label="sink", label_pos=(32, pre.cy - 12)))
    d.add(Arrow((post, "r"), (750, post.cy), kind="data", label="source",
        label_pos=(726, post.cy - 12)))
    d.add(Arrow((pre, "r"), (post, "l"), kind="data", label="bypass",
        label_pos=(380, pre.cy - 12)))
    d.add(Arrow((pre, "b"), (prec, "t"), kind="accent"))
    d.add(Arrow((prec, "b"), (fifo, "l"), kind="accent"))
    d.add(Arrow((fifo, "r"), (postc, "b"), kind="accent"))
    d.add(Arrow((postc, "t"), (post, "b"), kind="accent"))
    d.add(Arrow((fifo, "t"), (dram, "b"), kind="data", heads="both", label="ports",
        label_pos=(400, 220), label_anchor="start"))
    return d
