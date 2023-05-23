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


# LiteDRAMAvalongMM2Native --------------------------------------------------------------------------

class LiteDRAMAvalonMM2Native(Module):
    def __init__(self, avalon, port, base_address=0x00000000, burst_increment=1):
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
        active_burst      = Signal()
        address           = Signal(avalon_data_width)
        byteenable        = Signal.like(avalon.byteenable)
        writedata         = Signal(avalon_data_width)
        start_transaction = Signal()
        cmd_ready_seen    = Signal()

        self.comb += active_burst.eq(2 <= burstcounter)
        self.sync += [
            If(start_transaction,
                byteenable.eq(avalon.byteenable),
                burstcounter.eq(avalon.burstcount),
                address.eq(avalon.address - offset))
        ]

        start_condition = start_transaction if downconvert else (start_transaction & port.cmd.ready)

        self.submodules.fsm = fsm = FSM(reset_state="START")
        fsm.act("START",
            avalon.waitrequest.eq(1),
            port.cmd.addr.eq(avalon.address - offset),
            port.cmd.we.eq(avalon.write),
            port.cmd.valid   .eq(avalon.read | avalon.write),
            start_transaction.eq(avalon.read | avalon.write),

            If(start_condition,
                [] if downconvert else [avalon.waitrequest.eq(0)],
                If (avalon.write,
                    [
                        port.wdata.data.eq(avalon.writedata),
                        port.wdata.valid.eq(1),
                        port.wdata.we.eq(avalon.byteenable),
                    ] if downconvert else [],
                    NextValue(writedata, avalon.writedata),
                    [] if downconvert else [NextValue(port.cmd.last, 0)],
                    NextState("WRITE_DATA")
                ).Elif(avalon.read,
                      NextState("READ_DATA")))
                )

        fsm.act("WRITE_CMD",
            avalon.waitrequest.eq(1),
            port.rdata.ready.eq(0),

            port.cmd.addr.eq(address),
            port.cmd.we.eq(1),
            port.cmd.valid.eq(1),

            If(port.cmd.ready, NextState("WRITE_DATA")))

        fsm.act("WRITE_DATA",
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
                avalon.waitrequest.eq(active_burst if downconvert else ~active_burst),
                NextValue(writedata, avalon.writedata),

                If(~active_burst,
                    port.flush.eq(1),
                    NextValue(cmd_ready_seen, 0) if downconvert else NextValue(port.cmd.last, 1),
                    NextValue(burstcounter, 0),
                    NextValue(byteenable, 0),
                    # this marks the end of a write cycle
                    NextState("START")
                ).Else(
                    NextValue(address, address + burst_increment),
                    NextValue(burstcounter, burstcounter - 1),
                    NextState("WRITE_CMD")))
                )

        if downconvert:
            self.comb += port.cmd.last.eq(~(fsm.ongoing("WRITE_CMD") | fsm.ongoing("WRITE_DATA") | avalon.write))

        fsm.act("READ_CMD",
            avalon.waitrequest.eq(1),
            port.rdata.ready.eq(1),
            port.cmd.addr.eq(address),
            port.cmd.we.eq(0),
            port.cmd.valid.eq(1),

            If(port.cmd.ready,
                NextState("READ_DATA")))

        fsm.act("READ_DATA",
            avalon.waitrequest.eq(1),
            port.rdata.ready.eq(1),

            [
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
            ] if downconvert else [],

            If(port.rdata.valid,
                avalon.readdata.eq(port.rdata.data),
                avalon.readdatavalid.eq(1),

                If(~active_burst,
                    [
                        port.cmd.valid.eq(0),
                        avalon.waitrequest.eq(0),
                        NextValue(cmd_ready_seen, 0),
                    ] if downconvert else [],
                    NextValue(burstcounter, 0),
                    NextState("START")

                ).Else(
                    NextValue(address, address + burst_increment),
                    NextValue(burstcounter, burstcounter - 1),
                    NextState("READ_CMD")))
                )
