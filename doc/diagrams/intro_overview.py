#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# LiteDRAM at a glance: user logic, frontends, the core (crossbar, controller, DFI injector), the
# PHY and the DRAM; the BIOS reaches the DFI injector through registers for the initialization.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 265)
    d.add(Container(222, 15, 326, 165, title="Core", title_pos="bl"))
    user  = d.add(Box(10,  60, 75, 70, label="User\nlogic", fill=COLOR_FILL))
    fe    = d.add(Box(110, 60, 85, 70, label="Frontends", stack=2, size=14, fill=COLOR_ACCENT_LIGHT))
    xbar  = d.add(Box(237, 60, 70, 70, label="Cross-\nbar", fill=COLOR_ACCENT))
    ctrl  = d.add(Box(337, 60, 95, 70, label="Controller", fill=COLOR_ACCENT))
    inj   = d.add(Box(462, 60, 72, 70, label="DFI\ninjector", fill=COLOR_ACCENT))
    phy   = d.add(Box(578, 60, 70, 70, label="PHY", fill=COLOR_ACCENT_LIGHT))
    dram  = d.add(Box(678, 60, 72, 70, label="DRAM", fill=COLOR_HARDWARE))
    bios  = d.add(Box(443, 205, 110, 44, label="LiteX BIOS", fill=COLOR_FILL))
    d.add(Arrow((user, "r"), (fe, "l"), kind="data", heads="both"))
    d.add(Arrow((fe.x + fe.w + 2*STACK_DX, fe.cy), (xbar, "l"), kind="data", heads="both"))
    d.add(Arrow((xbar, "r"), (ctrl, "l"), kind="data", heads="both"))
    d.add(Arrow((ctrl, "r"), (inj, "l"), kind="data", heads="both", label="DFI", label_pos=(447, 50)))
    d.add(Arrow((inj, "r"), (phy, "l"), kind="data", heads="both", label="DFI", label_pos=(563, 50)))
    d.add(Arrow((phy, "r"), (dram, "l"), kind="data", heads="both", label="pads", label_pos=(663, 50)))
    d.add(Arrow((inj.cx, 205), (inj, "b"), kind="control", label="registers", label_side="right",
        label_pos=(506, 160)))
    return d
