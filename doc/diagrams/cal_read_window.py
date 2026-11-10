#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Read leveling scan of one byte lane: passing delay taps for each read bitslip, and the centre the
# BIOS keeps. Data: module m1 of the KC705 capture of the Calibration chapter.

from core_helpers import *

SCAN = [
    ("b0", "0"*32,                              "-"),
    ("b1", "0"*32,                              "-"),
    ("b2", "0"*32,                              "-"),
    ("b3", "11111111000000000000000000000000",  "04+-04"),
    ("b4", "00000000000011111111100000000000",  "16+-04"),
    ("b5", "00000000000000000000000000111111",  "29+-03"),
    ("b6", "0"*32,                              "-"),
    ("b7", "0"*32,                              "-"),
]


def build():
    d  = Diagram(CANVAS_WIDTH, 300)
    x0, y0, cw, h, pitch = 90, 40, 18, 22, 27
    d.add(Text(70, 20, "bitslip", size=13, anchor="end"))
    d.add(Text(690, 20, "window", size=13, anchor="start"))
    for i, (name, bits, result) in enumerate(SCAN):
        y = y0 + i*pitch
        d.add(Text(70, y + h/2, name, size=13, anchor="end"))
        scan_row(d, x0, y, bits, cw=cw, h=h)
        d.add(Text(690, y + h/2, result, size=13, anchor="start"))
    # Centre kept by the BIOS: bitslip 4, tap 16.
    d.add(Mark(x0 + 16*cw + cw/2, y0 + 4*pitch + h/2, color=COLOR_OK))
    yb = y0 + 8*pitch + 6
    d.add(Text(x0 + cw/2,  yb + 8, "0", size=13))
    d.add(Text(x0 + 31*cw + cw/2, yb + 8, "31", size=13))
    d.add(Text(x0 + 16*cw, yb + 8, "read delay tap", size=13))
    return d
