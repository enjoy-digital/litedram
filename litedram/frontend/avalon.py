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

        # DownConverter (Optional).
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
            self.submodules += LiteDRAMNativePortConverter(new_port, port)
            port = new_port

        # # #

        # Internal Signals.
        offset  = (base_address >> log2_int(port.data_width//8))

        burst_count       = Signal(9)
        burst_start       = Signal()
        burst_active      = Signal()
        address           = Signal(port.address_width)
        byteenable        = Signal(avalon_data_width//8)
        writedata         = Signal(avalon_data_width)
        start_transaction = Signal()
        start_condition   = Signal()
        cmd_ready_seen    = Signal()
        cmd_ready_count   = Signal(9)

        # Layouts.
        cmd_layout   = [("address", len(address))]
        wdata_layout = [
            ("data",       avalon_data_width),
            ("byteenable", avalon_data_width//8),
        ]

        self.comb += [
            burst_start .eq(avalon.burstcount >= 2),
            burst_active.eq(burst_count       >= 1),
        ]
        self.sync += [
            If(start_transaction,
                byteenable.eq(avalon.byteenable),
                burst_count.eq(avalon.burstcount),
                address.eq(avalon.address - offset),
            )
        ]

        # FSM.
        self.submodules.fsm = fsm = FSM(reset_state="START")
        fsm.act("START",
            avalon.waitrequest.eq(1),
            If(~burst_start,
                port.cmd.addr.eq(avalon.address - offset),
                port.cmd.we.eq(avalon.write),
                port.cmd.valid.eq(avalon.read | avalon.write)
            ),

            start_transaction.eq(avalon.read | avalon.write),
            If(downconvert,
                start_condition.eq(start_transaction)
            ).Else(
                start_condition.eq(start_transaction & (burst_start | port.cmd.ready))
            ),
            If(start_condition,
                If(downconvert,
                    avalon.waitrequest.eq(1)
                ).Else(
                    If(~burst_start, avalon.waitrequest.eq(0))
                ),
                If(avalon.write,
                    If(burst_start,
                        NextState("BURST_WRITE")
                    ).Else(
                        If(downconvert,
                            port.wdata.data.eq(avalon.writedata),
                            port.wdata.valid.eq(1),
                            port.wdata.we.eq(avalon.byteenable),
                        ),
                        NextValue(writedata, avalon.writedata),
                        port.cmd.last.eq(1),
                        NextState("SINGLE_WRITE")
                    )
                ).Elif(avalon.read,
                    If(burst_start,
                        avalon.waitrequest.eq(0),
                        NextValue(cmd_ready_count, avalon.burstcount),
                        NextState("BURST_READ")
                    ).Else(
                        port.cmd.last.eq(1),
                        NextState("SINGLE_READ")
                    )
                )
            )
        )

        fsm.act("SINGLE_WRITE",
            avalon.waitrequest.eq(1),
            port.rdata.ready.eq(0),

            If(downconvert,
                port.cmd.addr.eq(address),
                port.cmd.we.eq(1),
                port.cmd.valid.eq(1),

                If(port.cmd.ready,
                    NextValue(cmd_ready_seen, 1)
                ),
                If(cmd_ready_seen,
                    port.cmd.valid.eq(0),
                    port.cmd.we.eq(0)
                ),
            ),

            port.wdata.data.eq(writedata),
            port.wdata.valid.eq(1),
            port.wdata.we.eq(byteenable),

            If(port.wdata.ready,
                If(downconvert,
                    avalon.waitrequest.eq(0)
                ),
                NextValue(writedata, avalon.writedata),

                port.flush.eq(1),
                If(downconvert,
                    NextValue(cmd_ready_seen, 0)
                ).Else(
                    NextValue(port.cmd.last, 1)
                ),
                NextValue(byteenable, 0),
                NextState("START")
            )
        )

        fsm.act("SINGLE_READ",
            avalon.waitrequest.eq(1),
            port.rdata.ready.eq(1),

            If(downconvert,
                port.cmd.addr.eq(address),
                port.cmd.we.eq(0),
                port.cmd.valid.eq(1),

                If(port.cmd.ready,
                    NextValue(cmd_ready_seen, 1)
                ),
                If(cmd_ready_seen,
                    port.cmd.valid.eq(0),
                    port.cmd.we.eq(0)
                ),
            ),

            If(port.rdata.valid,
                avalon.readdata.eq(port.rdata.data),
                avalon.readdatavalid.eq(1),

                If(downconvert,
                    port.cmd.valid.eq(0),
                    avalon.waitrequest.eq(0),
                    NextValue(cmd_ready_seen, 0),
                ),

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

            If(avalon.write & burst_active,
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
                    NextValue(cmd_ready_seen, 0),
                    NextState("START")
                ),
                NextValue(burst_count, burst_count - 1)
            )
        )
