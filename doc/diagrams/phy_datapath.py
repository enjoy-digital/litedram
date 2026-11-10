#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Common datapath of the DDR PHYs: DFI phases, bitslips, serializers and IO delays on the write
# and read paths between the controller and the DRAM pads.

from svgdiag import *
from phy_helpers import frac


def build():
    d = Diagram(CANVAS_WIDTH, 270)
    d.add(Container(163, 15, 430, 240, title="PHY", title_pos="tr"))
    dfi  = d.add(Box(15, 45, 100, 190, label="Controller\nDFI phases", fill=COLOR_ACCENT_LIGHT))
    wbs  = d.add(Box(175, 55, 110, 60, label="Write\nbitslip", fill=COLOR_ACCENT))
    ser  = d.add(Box(320, 55, 110, 60, label="Serializer", fill=COLOR_ACCENT))
    odly = d.add(Box(465, 55, 110, 60, label="Output\ndelay"))
    rbs  = d.add(Box(175, 165, 110, 60, label="Read\nbitslip", fill=COLOR_ACCENT))
    des  = d.add(Box(320, 165, 110, 60, label="Deserializer", fill=COLOR_ACCENT))
    idly = d.add(Box(465, 165, 110, 60, label="Input\ndelay"))
    dram = d.add(Box(630, 45, 115, 190, label="DRAM\nDQ, DQS", fill=COLOR_HARDWARE))
    yw, yr = 85, 195
    d.add(Arrow((dfi, "r", frac(dfi, yw)), (wbs, "l"), kind="accent", label="wrdata", label_pos=(137, 75)))
    d.add(Arrow((wbs, "r"), (ser, "l"), kind="accent"))
    d.add(Arrow((ser, "r"), (odly, "l"), kind="accent"))
    d.add(Arrow((odly, "r"), (dram, "l", frac(dram, yw)), kind="accent"))
    d.add(Arrow((dram, "l", frac(dram, yr)), (idly, "r"), kind="data"))
    d.add(Arrow((idly, "l"), (des, "r"), kind="data"))
    d.add(Arrow((des, "l"), (rbs, "r"), kind="data"))
    d.add(Arrow((rbs, "l"), (dfi, "r", frac(dfi, yr)), kind="data", label="rddata", label_pos=(137, 185)))
    return d
