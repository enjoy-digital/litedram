#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Shared helpers of the introduction, primer and interface figures (no build(): not a figure).
#
# Timing rows: one horizontal row per signal (a name on the left, adjoining cells on a common time
# axis), clock rows drawn as square waves, and spans (double-headed arrows) for the timings.

from svgdiag import *


def row_name(d, x, y, name, size=13):
    """Signal name, right-aligned, left of a row whose cells start at x and are centred on y."""
    d.add(Text(x - 10, y, name, size=size, anchor="end"))


def cells(d, x, y, items, h=26, size=13):
    """Row of adjoining square cells: items is a list of (width, label, fill); fill None = gap."""
    out = []
    for w, label, fill in items:
        if fill is not None:
            out.append(d.add(Box(x, y - h/2, w, h, label=label, radius=0, fill=fill, size=size)))
        x += w
    return out


def clock(d, x, y, period, n, h=16, phase=0.0):
    """Square wave of n periods starting at x, low at y + h/2, high at y - h/2.

    phase shifts the first rising edge by a fraction of a period (0.25 = 90 degrees)."""
    hi, lo = y - h/2, y + h/2
    pts = [(x, lo)]
    t = x + phase*period
    if phase:
        pts.append((t, lo))
    for i in range(n):
        r = t + i*period
        f = r + period/2
        pts += [(r, lo), (r, hi), (f, hi), (f, lo)]
    end = t + n*period
    pts.append((end, lo))
    # Drop consecutive duplicates (zero-length segments).
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 0.5 or abs(p[1] - clean[-1][1]) > 0.5:
            clean.append(p)
    d.add(Bus(clean, kind="control"))


def span(d, x0, x1, y, label, kind="control", side="above"):
    """Double-headed horizontal arrow from x0 to x1 at y, with its label above or below."""
    d.add(Arrow((x0, y), (x1, y), kind=kind, heads="both", label=label, label_side=side))


def tick(d, x, y0, y1):
    """Dotted vertical marker (a time reference) from y0 to y1."""
    d.add(Bus([(x, y0), (x, y1)], dash="2,3", color="#9a9a9a"))
