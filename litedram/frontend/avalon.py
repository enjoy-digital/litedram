#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

"""AvalonMM frontend for LiteDRAM"""

from math import log2

from migen import *

from litex.gen import *

from litex.soc.interconnect import stream

from litedram.common import LiteDRAMNativePort
from litedram.frontend.adapter import LiteDRAMNativePortConverter

# LiteDRAMAvalonMM2Native --------------------------------------------------------------------------

class LiteDRAMAvalonMM2Native(LiteXModule):
    def __init__(self, avalon, port, *, max_burst_length=16, base_address=0x00000000, burst_increment=1):
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
            self.converter = LiteDRAMNativePortConverter(new_port, port)
            port = new_port

        # # #

        # Internal Signals.
        burst_count     = Signal(9)
        address         = Signal(port.address_width)
        address_offset  = Signal(port.address_width)
        byteenable      = Signal(avalon_data_width//8)
        writedata       = Signal(avalon_data_width)
        latch           = Signal()
        cmd_ready_seen  = Signal()
        cmd_ready_count = Signal(9)

        self.comb += address_offset.eq(base_address >> log2_int(port.data_width//8))

        # Layouts.
        cmd_layout   = [("address", len(address))]
        wdata_layout = [
            ("data",       avalon_data_width),
            ("byteenable", avalon_data_width//8),
        ]

        self.sync += [
            If(latch,
                byteenable.eq(avalon.byteenable),
                writedata.eq(avalon.writedata),
                burst_count.eq(avalon.burstcount),
                address.eq(avalon.address - address_offset),
            )
        ]

        # FSM.
        self.fsm = fsm = FSM(reset_state="START")
        fsm.act("START",
            avalon.waitrequest.eq(1),
            NextValue(cmd_ready_seen, 0),
            # Start of Access.
            If(avalon.read | avalon.write,
                latch.eq(1),
                # Burst Access.
                If(avalon.burstcount > 1,
                    If(avalon.write,
                        NextState("BURST_WRITE")
                    ),
                    If(avalon.read,
                        avalon.waitrequest.eq(0),
                        NextValue(cmd_ready_count, avalon.burstcount),
                        NextState("BURST_READ")
                    )
                # Single Access.
                ).Else(
                    port.cmd.addr.eq(avalon.address - address_offset),
                    port.cmd.we.eq(avalon.write),
                    port.cmd.valid.eq(1),
                    port.cmd.last.eq(1),
                    If(port.cmd.ready,
                        avalon.waitrequest.eq(0),
                        If(port.cmd.we,
                            NextState("SINGLE_WRITE")
                        ).Else(
                            NextState("SINGLE_READ")
                        )
                    )
                )
            )
        )

        fsm.act("SINGLE_WRITE",
            avalon.waitrequest.eq(1),
            port.rdata.ready.eq(0),

            port.wdata.data.eq(writedata),
            port.wdata.valid.eq(1),
            port.wdata.we.eq(byteenable),

            If(port.wdata.ready,
                NextState("START")
            )
        )

        fsm.act("SINGLE_READ",
            avalon.waitrequest.eq(1),
            port.rdata.ready.eq(1),

            If(port.rdata.valid,
                avalon.readdata.eq(port.rdata.data),
                avalon.readdatavalid.eq(1),

                NextState("START")
            )
        )

        self.cmd_fifo   = cmd_fifo   = stream.SyncFIFO(cmd_layout,   max_burst_length)
        self.wdata_fifo = wdata_fifo = stream.SyncFIFO(wdata_layout, max_burst_length)

        fsm.act("BURST_WRITE",
            # FIFO producer
            avalon.waitrequest.eq(~(cmd_fifo.sink.ready & wdata_fifo.sink.ready)),
            cmd_fifo.sink.payload.address.eq(address),
            cmd_fifo.sink.valid.eq(avalon.write & ~avalon.waitrequest),

            wdata_fifo.sink.payload.data.eq(avalon.writedata),
            wdata_fifo.sink.payload.byteenable.eq(avalon.byteenable),
            wdata_fifo.sink.valid.eq(avalon.write & ~avalon.waitrequest),

            If(avalon.write & (burst_count > 0),
                If(cmd_fifo.sink.ready & cmd_fifo.sink.valid,
                    NextValue(burst_count, burst_count - 1),
                    NextValue(address, address + burst_increment)
                )
            ).Else(
                avalon.waitrequest.eq(1),
                # Wait for the FIFO to be empty
                If((cmd_fifo.level == 0) & (wdata_fifo.level == 1) & port.wdata.ready,
                    NextState("START")
                )
            ),

            # FIFO consumer
            port.cmd.addr.eq(cmd_fifo.source.payload.address),
            port.cmd.we.eq(port.cmd.valid),
            port.cmd.valid.eq(cmd_fifo.source.valid & (0 < wdata_fifo.level)),
            cmd_fifo.source.ready.eq(port.cmd.ready),

            port.wdata.data.eq(wdata_fifo.source.payload.data),
            port.wdata.we.eq(wdata_fifo.source.payload.byteenable),
            port.wdata.valid.eq(wdata_fifo.source.valid),
            wdata_fifo.source.ready.eq(port.wdata.ready),
        )

        fsm.act("BURST_READ",
            avalon.waitrequest.eq(1),
            port.cmd.addr.eq(address),
            port.cmd.we.eq(0),
            port.cmd.valid.eq(~cmd_ready_seen),

            port.rdata.ready.eq(1),
            avalon.readdata.eq(port.rdata.data),
            avalon.readdatavalid.eq(port.rdata.valid),

            If(port.cmd.ready,
                If(cmd_ready_count == 1,
                    NextValue(cmd_ready_seen, 1)
                ),
                NextValue(cmd_ready_count, cmd_ready_count - 1),
                NextValue(address, address + burst_increment)
            ),

            If(port.rdata.valid,
                If(burst_count == 1,
                    NextState("START")
                ),
                NextValue(burst_count, burst_count - 1)
            )
        )
