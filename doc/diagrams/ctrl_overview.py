#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Controller: bank machines and refresher feed the multiplexer; the data path goes straight from
# the crossbar to the multiplexer.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 290)
    d.add(Container(140, 20, 380, 250, title="LiteDRAMController", title_pos="bl"))
    xbar = d.add(Box(15,  40, 95,  200, label="Crossbar", fill=COLOR_ACCENT_LIGHT))
    bm   = d.add(Box(165, 40, 140, 60,  label="Bank machines", fill=COLOR_ACCENT, stack=2))
    ref  = d.add(Box(165, 135, 140, 50, label="Refresher", fill=COLOR_ACCENT))
    mux  = d.add(Box(380, 40, 120, 200, label="Multiplexer", fill=COLOR_ACCENT))
    dfi  = d.add(Box(600, 40, 145, 200, label="DFI injector\nand PHY"))
    d.add(Arrow((xbar.x + xbar.w, bm.cy), (bm, "l"), kind="control"))
    d.add(Arrow((bm.x + bm.w + 8, bm.cy), (mux.x, bm.cy), kind="control", label="commands",
        label_pos=(343, bm.cy - 11)))
    d.add(Arrow((ref, "r"), (mux.x, ref.cy), kind="control", label="REF",
        label_pos=(343, ref.cy - 11)))
    d.add(Arrow((xbar.x + xbar.w, 222), (mux.x, 222), kind="data", heads="both",
        label="write and read data", label_pos=(245, 208)))
    d.add(Arrow((mux.x + mux.w, mux.cy), (dfi.x, mux.cy), kind="accent", heads="both",
        label="DFI", label_pos=(560, mux.cy - 12)))
    return d
