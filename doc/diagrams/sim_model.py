#
# This file is part of LiteDRAM project.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Migen unit tests: port drivers send traffic through the crossbar and the controller to the DFI-level
# DRAM model, whose timings checker watches every command on the DFI.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 330)
    tb   = d.add(Container(20, 20, 180, 290, title="Test", title_pos="bl"))
    core = d.add(Container(220, 20, 290, 290, title="LiteDRAM core", title_pos="bl"))
    mdl  = d.add(Container(540, 20, 200, 290, title="SDRAMPHYModel", title_pos="bl"))
    drv  = d.add(Box(35, 60, 150, 50, label="Port drivers\n(native, AXI)", fill=COLOR_ACCENT_LIGHT))
    xbar = d.add(Box(240, 60, 110, 50, label="Crossbar"))
    ctrl = d.add(Box(370, 60, 120, 50, label="Controller"))
    phs  = d.add(Box(565, 60, 150, 50, label="DFI phase\nmodels", fill=COLOR_ACCENT))
    bank = d.add(Box(565, 140, 150, 50, label="Bank models\n(memory)", fill=COLOR_ACCENT))
    chk  = d.add(Box(565, 220, 150, 50, label="DFI timings\nchecker", fill=COLOR_ACCENT))
    d.add(Arrow((drv, "r"), (xbar, "l"), kind="data", heads="both"))
    d.add(Arrow((xbar, "r"), (ctrl, "l"), kind="data", heads="both"))
    d.add(Arrow((ctrl, "r"), (phs, "l"), kind="accent", heads="both", label="DFI", label_pos=(525, 77)))
    d.add(Arrow((phs, "b"), (bank, "t"), kind="data", heads="both"))
    d.add(Arrow((ctrl, "b"), (chk, "l"), kind="feedback", via=[(430, 245)], label="commands",
        label_pos=(470, 237)))
    return d
