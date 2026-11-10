#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Structure of the LPDDR4, LPDDR5 and RPC PHYs: a base PHY in the controller clock domain, then a
# 7-Series backend for the FPGA or a simulation PHY with a pad-level DRAM simulator.

from svgdiag import *
from phy_helpers import frac


def build():
    d = Diagram(CANVAS_WIDTH, 260)
    dfi  = d.add(Box(15, 30, 110, 210, label="Controller\nDFI", fill=COLOR_ACCENT_LIGHT))
    base = d.add(Box(175, 30, 140, 210, label="Base PHY\ncommands\nbitslips", fill=COLOR_ACCENT))
    s7   = d.add(Box(400, 30, 150, 75, label="7-Series backend\nSERDES, delays", fill=COLOR_ACCENT))
    sim  = d.add(Box(400, 165, 150, 75, label="Simulation PHY\nMigen SERDES"))
    dram = d.add(Box(610, 30, 135, 75, label="DRAM", fill=COLOR_HARDWARE))
    model = d.add(Box(610, 165, 135, 75, label="DRAM\nsimulator"))
    d.add(Arrow((dfi, "r"), (base, "l"), kind="data", heads="both"))
    d.add(Arrow((base, "r", frac(base, 67.5)), (s7, "l"), kind="accent", heads="both", label="out"))
    d.add(Arrow((base, "r", frac(base, 202.5)), (sim, "l"), kind="data", heads="both", label="out"))
    d.add(Arrow((s7, "r"), (dram, "l"), kind="accent", heads="both", label="pads"))
    d.add(Arrow((sim, "r"), (model, "l"), kind="data", heads="both", label="pads"))
    return d
