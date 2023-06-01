#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Hans Baier <hansfbaier@gmail.com>
# Copyright (c) 2023 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""AvalonMM frontend for LiteDRAM"""

# TODO:
# - Try to merge SINGLE-WRITE/BURST-WRITE (Consider single access as a 1 word burst).
# - Try to merge SINGLE-READ /BURST-READ  (Consider single access as a 1 word burst).

from math import log2

from migen import *

from litex.gen import *

from litex.soc.interconnect import stream

from litedram.common import LiteDRAMNativePort
from litedram.frontend.adapter import LiteDRAMNativePortConverter

# LiteDRAMAvalonMM2Native --------------------------------------------------------------------------

class LiteDRAMAvalonMM2Native(LiteXModule):
    def __init__(self, avalon, port, max_burst_length=16, base_address=0x00000000, burst_increment=1):
        # Parameters.
        avalon_data_width = len(avalon.writedata)
        port_data_width   = 2**int(log2(len(port.wdata.data))) # Round to lowest power 2
        ratio             = avalon_data_width/port_data_width
        downconvert       = ratio > 1
        upconvert         = ratio < 1

        # Data-Width Converter (Optional).
        if avalon_data_width != port_data_width:
            if avalon_data_width > port_data_width:
                addr_shift = -log2_int(avalon_data_width//port_data_width)
            else:
                addr_shift = log2_int(port_data_width//avalon_data_width)
            new_port = LiteDRAMNativePort(
                mode          = port.mode,
                address_width = port.address_width + addr_shift,
                data_width    = avalon_data_width
            )
            self.converter = LiteDRAMNativePortConverter(new_port, port, early_cmd_ready=True)
            port = new_port

        # # #

        # Internal Signals.
        burst_count     = Signal(9)
        address         = Signal(port.address_width)
        address_offset  = Signal(port.address_width)
        self.comb += address_offset.eq(base_address >> log2_int(port.data_width//8))

        # Write Data-path.
        wdata_layout = [
            ("data",       avalon_data_width),
            ("byteenable", avalon_data_width//8),
        ]
        self.wdata_fifo = wdata_fifo = stream.SyncFIFO(wdata_layout, max_burst_length)
        self.comb += [
            wdata_fifo.sink.payload.data.eq(avalon.writedata),
            wdata_fifo.sink.payload.byteenable.eq(avalon.byteenable),
            wdata_fifo.sink.valid.eq(avalon.write & ~avalon.waitrequest),

            port.wdata.data.eq(wdata_fifo.source.payload.data),
            port.wdata.we.eq(wdata_fifo.source.payload.byteenable),
            port.wdata.valid.eq(wdata_fifo.source.valid),
            wdata_fifo.source.ready.eq(port.wdata.ready),
        ]

        # Read Data-path.
        self.comb += [
            port.rdata.ready.eq(1),
            avalon.readdata.eq(port.rdata.data),
            avalon.readdatavalid.eq(port.rdata.valid),
        ]

        # Control-Path.
        self.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            avalon.waitrequest.eq(1),
            # Start of Access.
            If(avalon.read | avalon.write,
                NextValue(burst_count, avalon.burstcount),
                NextValue(address, avalon.address - address_offset),
                # Burst Access.
                If(avalon.burstcount > 1,
                    If(avalon.write,
                        NextState("BURST-WRITE")
                    ),
                    If(avalon.read,
                        avalon.waitrequest.eq(0),
                        NextState("BURST-READ")
                    )
                # Single Access.
                ).Else(
                    port.cmd.addr.eq(avalon.address - address_offset),
                    port.cmd.we.eq(avalon.write),
                    port.cmd.valid.eq(avalon.read | (avalon.write & wdata_fifo.sink.ready)),
                    port.cmd.last.eq(1),
                    If(port.cmd.valid & port.cmd.ready,
                        avalon.waitrequest.eq(0),
                    )
                )
            )
        )
        fsm.act("BURST-WRITE",
            avalon.waitrequest.eq(1),
            port.cmd.addr.eq(address),
            port.cmd.we.eq(1),
            port.cmd.valid.eq(avalon.write & wdata_fifo.sink.ready),
            port.cmd.last.eq(burst_count == 1),
            If(port.cmd.valid & port.cmd.ready,
                avalon.waitrequest.eq(0),
                If(port.cmd.last,
                    NextState("IDLE")
                ).Else(
                    NextValue(burst_count, burst_count - 1),
                    NextValue(address, address + burst_increment)
                )
            )
        )

        fsm.act("BURST-READ",
            avalon.waitrequest.eq(1),
            port.cmd.addr.eq(address),
            port.cmd.we.eq(0),
            port.cmd.valid.eq(1),
            port.cmd.last.eq(burst_count == 1),
            If(port.cmd.valid & port.cmd.ready,
                If(port.cmd.last,
                    NextState("IDLE")
                ).Else(
                    NextValue(burst_count, burst_count - 1),
                    NextValue(address, address + burst_increment)
                )
            )
        )
