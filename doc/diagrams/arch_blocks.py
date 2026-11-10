#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Core architecture: frontends, crossbar, controller, optional DFI ECC, DFI injector, PHY, DRAM.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 280)
    d.add(Container(115, 20, 430, 180, title="LiteDRAMCore", title_pos="bl"))
    fe   = d.add(Box(10,  60, 85, 70, label="Frontends\nuser logic"))
    xbar = d.add(Box(130, 60, 75, 70, label="Crossbar", fill=COLOR_ACCENT_LIGHT))
    ctrl = d.add(Box(230, 60, 85, 70, label="Controller", fill=COLOR_ACCENT))
    ecc  = d.add(Box(340, 60, 75, 70, label="DFI ECC\noptional", fill=COLOR_ACCENT_LIGHT))
    inj  = d.add(Box(440, 60, 80, 70, label="DFI\ninjector", fill=COLOR_ACCENT))
    phy  = d.add(Box(580, 60, 75, 70, label="PHY", fill=COLOR_ACCENT_LIGHT))
    dram = d.add(Box(680, 60, 70, 70, label="DRAM", fill=COLOR_HARDWARE))
    cpu  = d.add(Box(415, 220, 130, 46, label="BIOS on the CPU"))
    for a, b in ((fe, xbar), (xbar, ctrl)):
        d.add(Arrow((a, "r"), (b, "l"), kind="data", heads="both"))
    for a, b in ((ctrl, ecc), (ecc, inj), (inj, phy)):
        d.add(Arrow((a, "r"), (b, "l"), kind="accent", heads="both"))
    d.add(Arrow((phy, "r"), (dram, "l"), kind="data", heads="both"))
    d.add(Arrow((470, cpu.y), (470, inj.y + inj.h), kind="control", label="registers",
        label_pos=(478, 165), label_anchor="start"))
    return d
