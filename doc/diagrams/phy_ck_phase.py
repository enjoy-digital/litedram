#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# 7-Series CK phase shift: the PHY MMCM moves CK and the commands against static DQ/DQS clocks,
# under control of the CK phase registers.

from svgdiag import *
from phy_helpers import frac


def build():
    d = Diagram(CANVAS_WIDTH, 290)
    sysc = d.add(Box(15, 60, 115, 60, label="sys clock", fill=COLOR_HARDWARE))
    regs = d.add(Box(15, 200, 115, 60, label="CK phase\nregisters", fill=COLOR_ACCENT_LIGHT))
    mmcm = d.add(Box(190, 40, 120, 230, label="PHY MMCM", fill=COLOR_ACCENT))
    cks  = d.add(Box(400, 40, 150, 75, label="CK, commands\nserializers", fill=COLOR_ACCENT))
    dqs  = d.add(Box(400, 195, 150, 75, label="DQ, DQS\nserializers"))
    dram = d.add(Box(615, 40, 130, 230, label="DRAM", fill=COLOR_HARDWARE))
    d.add(Arrow((sysc, "r"), (mmcm, "l", frac(mmcm, 90)), kind="control"))
    d.add(Arrow((regs, "r"), (mmcm, "l", frac(mmcm, 230)), kind="control", label="inc, dec"))
    d.add(Arrow((mmcm, "r", frac(mmcm, 77.5)), (cks, "l"), kind="control", label="fine shift"))
    d.add(Arrow((mmcm, "r", frac(mmcm, 232.5)), (dqs, "l"), kind="control", label="static"))
    d.add(Arrow((cks, "r"), (dram, "l", frac(dram, 77.5)), kind="accent", label="CK"))
    d.add(Arrow((dqs, "r"), (dram, "l", frac(dram, 232.5)), kind="data", label="DQS"))
    return d
