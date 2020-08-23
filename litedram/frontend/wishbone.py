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

        adr_offset = base_address >> log2_int(port.data_width//8)

        cmd_consumed   = Signal()
        wdata_consumed = Signal()
        ack_cmd        = Signal()
        ack_wdata      = Signal()
        ack_rdata      = Signal()

        # Latch ready signals of cmd/wdata and then wait until all are ready.
        self.sync += [
            If(wishbone.ack,
                cmd_consumed.eq(0),
                wdata_consumed.eq(0),
            ).Else(
                If(port.cmd.valid   & port.cmd.ready,   cmd_consumed.eq(1)),
                If(port.wdata.valid & port.wdata.ready, wdata_consumed.eq(1)),
            ),
        ]

        self.comb += [
            port.cmd.addr.eq(wishbone.adr - adr_offset),
            port.cmd.we.eq(wishbone.we),
            port.wdata.data.eq(wishbone.dat_w),
            port.wdata.we.eq(wishbone.sel),
            wishbone.dat_r.eq(port.rdata.data),
            # Always wait for reads, flush write when transaction ends.
            port.flush.eq(~wishbone.cyc),
            port.cmd.last.eq(~wishbone.we),
            # Make sure cmd/wdata won't stay valid after it is consumed.
            port.cmd.valid.eq(wishbone.cyc & wishbone.stb & ~cmd_consumed),
            port.wdata.valid.eq((port.cmd.valid | cmd_consumed) & port.cmd.we & ~wdata_consumed),
            port.rdata.ready.eq((port.cmd.valid | cmd_consumed) & ~port.cmd.we),
            wishbone.ack.eq(ack_cmd & ((wishbone.we & ack_wdata) | (~wishbone.we & ack_rdata))),
            ack_cmd.eq((port.cmd.valid & port.cmd.ready) | cmd_consumed),
            ack_wdata.eq((port.wdata.valid & port.wdata.ready) | wdata_consumed),
            ack_rdata.eq(port.rdata.valid & port.rdata.ready),
        ]
