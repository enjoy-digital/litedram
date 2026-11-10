#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Enjoy-Digital <enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Signals between the FPGA and a DDR3 DRAM on a custom board: clock, command/address and control
# pins in one direction, one bidirectional byte lane per 8 data bits, and the VREF supply.

from svgdiag import *


def build():
    d = Diagram(CANVAS_WIDTH, 350)
    d.add(Container(20, 20, 270, 262, title="FPGA", title_pos="bl"))
    phy  = d.add(Box(60, 40, 170, 192, label="PHY", fill=COLOR_ACCENT))
    dram = d.add(Box(560, 40, 180, 192, label="DRAM", fill=COLOR_HARDWARE))
    vref = d.add(Box(320, 295, 160, 44, label="VREF supply", fill=COLOR_HARDWARE))
    d.add(Arrow((230, 65),  (560, 65),  kind="control", label="CK_P, CK_N", label_pos=(420, 57)))
    d.add(Arrow((230, 105), (560, 105), kind="data", label="command, address", label_pos=(420, 95)))
    d.add(Arrow((230, 145), (560, 145), kind="control", label="CKE, ODT, RESET_N", label_pos=(420, 137)))
    d.add(Arrow((230, 185), (560, 185), kind="accent", heads="both",
        label="byte lane 0: DQ, DM, DQS", label_pos=(420, 175)))
    d.add(Arrow((230, 215), (560, 215), kind="accent", heads="both",
        label="byte lane N", label_pos=(420, 205)))
    d.add(Arrow((vref, "l"), (145, 232), via=[(145, 317)], kind="control"))
    d.add(Arrow((vref, "r"), (650, 232), via=[(650, 317)], kind="control"))
    return d
