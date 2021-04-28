#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Wishbone frontend for LiteDRAM"""

from math import log2

from migen import *

from litex.soc.interconnect import stream
from litedram.common import LiteDRAMNativePort
from litedram.frontend.adapter import LiteDRAMNativePortConverter


# LiteDRAMWishbone2Native --------------------------------------------------------------------------

class LiteDRAMWishbone2Native(Module):
    def __init__(self, wishbone, port, base_address=0x00000000):
        wishbone_data_width = len(wishbone.dat_w)
        port_data_width     = 2**int(log2(len(port.wdata.data))) # Round to lowest power 2
        ratio               = wishbone_data_width/port_data_width

        if wishbone_data_width != port_data_width:
            if wishbone_data_width > port_data_width:
                addr_shift = -log2_int(wishbone_data_width//port_data_width)
            else:
                addr_shift = log2_int(port_data_width//wishbone_data_width)
            new_port = LiteDRAMNativePort(
                mode          = port.mode,
                address_width = port.address_width + addr_shift,
                data_width    = wishbone_data_width
            )
            self.submodules += LiteDRAMNativePortConverter(new_port, port)
            port = new_port

        # # #

        aborted = Signal()
        offset  = base_address >> log2_int(port.data_width//8)

        self.submodules.fsm = fsm = FSM(reset_state="CMD")
        self.comb += [
            port.cmd.addr.eq(wishbone.adr - offset),
            port.cmd.we.eq(wishbone.we),
            port.cmd.last.eq(~wishbone.we), # Always wait for reads.
            port.flush.eq(~wishbone.cyc)    # Flush writes when transaction ends.
        ]
        fsm.act("CMD",
            port.cmd.valid.eq(wishbone.cyc & wishbone.stb),
            If(port.cmd.valid & port.cmd.ready &  wishbone.we, NextState("WRITE")),
            If(port.cmd.valid & port.cmd.ready & ~wishbone.we, NextState("READ")),
            NextValue(aborted, 0),
        )
        self.comb += [
            port.wdata.valid.eq(wishbone.stb & wishbone.we),
            If(ratio <= 1, If(~fsm.ongoing("WRITE"), port.wdata.valid.eq(0))),
            port.wdata.data.eq(wishbone.dat_w),
            port.wdata.we.eq(wishbone.sel),
        ]
        fsm.act("WRITE",
            NextValue(aborted, ~wishbone.cyc | aborted),
            If(port.wdata.valid & port.wdata.ready,
                wishbone.ack.eq(wishbone.cyc & ~aborted),
                NextState("CMD")
            ),
        )
        self.comb += port.rdata.ready.eq(1)
        fsm.act("READ",
            NextValue(aborted, ~wishbone.cyc | aborted),
            If(port.rdata.valid,
                wishbone.ack.eq(wishbone.cyc & ~aborted),
                wishbone.dat_r.eq(port.rdata.data),
                NextState("CMD")
            )
        )
