#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Native port exchange: a write and a read, with the wdata_ready and rdata_valid pulses.

from core_helpers import *


def build():
    d = Diagram(CANVAS_WIDTH, 320)
    l = Lanes(d, "User logic", "Native port", rows=4)
    l.msg("cmd: we=1, addr", to_right=True, kind="control", right_note="queued in the bank")
    l.msg("wdata_ready pulse", to_right=False, kind="accent", left_note="data sampled",
        right_note="WR sent")
    l.msg("cmd: we=0, addr", to_right=True, kind="control")
    l.msg("rdata_valid, data", to_right=False, kind="accent", left_note="capture now")
    return d
