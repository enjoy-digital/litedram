#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

"""AvalonMM frontend for LiteDRAM"""

from math import log2

from migen import *

from litex.soc.interconnect import stream
from litedram.common import LiteDRAMNativePort
from litedram.frontend.adapter import LiteDRAMNativePortConverter


# LiteDRAMAvalonMM2Native --------------------------------------------------------------------------

class LiteDRAMAvalonMM2Native(Module):
    def __init__(self, avalon, port, *, max_burst_length=16, base_address=0x00000000, burst_increment=1):
        avalon_data_width = len(avalon.writedata)
        port_data_width     = 2**int(log2(len(port.wdata.data))) # Round to lowest power 2
        ratio               = avalon_data_width/port_data_width
        downconvert         = ratio > 1
        upconvert           = ratio < 1

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

        offset  = base_address >> log2_int(port.data_width//8)

        burstcounter      = Signal(9)
        start_burst       = Signal()
        active_burst      = Signal()
        address           = Signal.like(port.cmd.addr)
        byteenable        = Signal.like(avalon.byteenable)
        writedata         = Signal(avalon_data_width)
        start_transaction = Signal()
        cmd_ready_seen    = Signal()
        cmd_ready_counter = Signal.like(burstcounter)

        cmd_layout = [("address", len(address))]
        wdata_layout = [
            ("data", avalon_data_width),
            ("byteenable", len(avalon.byteenable))
        ]

        self.comb += [
            start_burst .eq(2 <= avalon.burstcount),
            active_burst.eq(1 <= burstcounter)
        ]
        self.sync += [
            If(start_transaction,
                byteenable.eq(avalon.byteenable),
                burstcounter.eq(avalon.burstcount),
                address.eq(avalon.address - offset))
        ]

        start_condition = start_transaction if downconvert else (start_transaction & (start_burst | port.cmd.ready))

        self.submodules.fsm = fsm = FSM(reset_state="START")
        fsm.act("START",
            avalon.waitrequest.eq(1),
            If (~start_burst,
                port.cmd.addr.eq(avalon.address - offset),
                port.cmd.we.eq(avalon.write),
                port.cmd.valid.eq(avalon.read | avalon.write)
            ),

            start_transaction.eq(avalon.read | avalon.write),

            If(start_condition,
                [] if downconvert else [If (~start_burst, avalon.waitrequest.eq(0))],
                If (avalon.write,
                    If (start_burst,
                        NextState("BURST_WRITE")
                    ).Else(
                        [
                            port.wdata.data.eq(avalon.writedata),
                            port.wdata.valid.eq(1),
                            port.wdata.we.eq(avalon.byteenable),
                        ] if downconvert else [],
                        NextValue(writedata, avalon.writedata),
                        port.cmd.last.eq(1),
                        NextState("SINGLE_WRITE")
                    )
                ).Elif(avalon.read,
                    If (start_burst,
                        avalon.waitrequest.eq(0),
                        NextValue(cmd_ready_counter, avalon.burstcount),
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

            [
                port.cmd.addr.eq(address),
                port.cmd.we.eq(1),
                port.cmd.valid.eq(1),

                If(port.cmd.ready, NextValue(cmd_ready_seen, 1)),
                If(cmd_ready_seen,
                    port.cmd.valid.eq(0),
                    port.cmd.we.eq(0)
                ),
            ] if downconvert else [],

            port.wdata.data.eq(writedata),
            port.wdata.valid.eq(1),
            port.wdata.we.eq(byteenable),

            If(port.wdata.ready,
                avalon.waitrequest.eq(0 if downconvert else 1),
                NextValue(writedata, avalon.writedata),

                port.flush.eq(1),
                NextValue(cmd_ready_seen, 0) if downconvert else NextValue(port.cmd.last, 1),
                NextValue(byteenable, 0),
                NextState("START")
            )
        )

        fsm.act("SINGLE_READ",
            avalon.waitrequest.eq(1),
            port.rdata.ready.eq(1),

            [
                port.cmd.addr.eq(address),
                port.cmd.we.eq(0),
                port.cmd.valid.eq(1),

                If(port.cmd.ready, NextValue(cmd_ready_seen, 1)),
                If(cmd_ready_seen,
                    port.cmd.valid.eq(0),
                    port.cmd.we.eq(0)
                ),
            ] if downconvert else [],

            If(port.rdata.valid,
                avalon.readdata.eq(port.rdata.data),
                avalon.readdatavalid.eq(1),

                [
                    port.cmd.valid.eq(0),
                    avalon.waitrequest.eq(0),
                    NextValue(cmd_ready_seen, 0),
                ] if downconvert else [],
                NextState("START")
            )
        )

        self.submodules.cmd_fifo   = cmd_fifo   = stream.SyncFIFO(cmd_layout,   max_burst_length)
        self.submodules.wdata_fifo = wdata_fifo = stream.SyncFIFO(wdata_layout, max_burst_length)

        fsm.act("BURST_WRITE",
            # FIFO producer
            avalon.waitrequest.eq(~(cmd_fifo.sink.ready & wdata_fifo.sink.ready)),
            cmd_fifo.sink.payload.address.eq(address),
            cmd_fifo.sink.valid.eq(avalon.write & ~avalon.waitrequest),

            wdata_fifo.sink.payload.data.eq(avalon.writedata),
            wdata_fifo.sink.payload.byteenable.eq(avalon.byteenable),
            wdata_fifo.sink.valid.eq(avalon.write & ~avalon.waitrequest),

            If (avalon.write & active_burst,
                If (cmd_fifo.sink.ready & cmd_fifo.sink.valid,
                    NextValue(burstcounter, burstcounter - 1),
                    NextValue(address, address + burst_increment))
            ).Else(
                avalon.waitrequest.eq(1),
                # wait for the FIFO to be empty
                If ((cmd_fifo  .level == 0) &
                    (wdata_fifo.level == 1) & port.wdata.ready,
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

            If (port.cmd.ready,
                If (cmd_ready_counter == 1, NextValue(cmd_ready_seen, 1)),
                NextValue(cmd_ready_counter, cmd_ready_counter - 1),
                NextValue(address, address + burst_increment)
            ),

            If (port.rdata.valid,
                If (burstcounter == 1,
                    NextValue(cmd_ready_seen, 0),
                    NextState("START")),
                NextValue(burstcounter, burstcounter - 1)
            )
        )
