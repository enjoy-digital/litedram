#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Shared helpers of the PHY, LPDDR/RPC and module figures (phy_*, lp_*, mod_*); no build(): not a
# figure.

from svgdiag import *


def frac(box, y):
    """Fraction of the height of box at which an horizontal arrow at ordinate y meets its side."""
    return (y - box.y)/box.h


def hfrac(box, x):
    """Fraction of the width of box at which a vertical arrow at abscissa x meets its side."""
    return (x - box.x)/box.w


def strip(d, x, y, cells, w, h=40, size=13):
    """Row of adjoining square cells of width w: cells = [(label, fill)]; returns the boxes."""
    boxes = []
    for label, fill in cells:
        boxes.append(d.add(Box(x, y, w, h, label=label, radius=0, size=size, fill=fill)))
        x += w
    return boxes
