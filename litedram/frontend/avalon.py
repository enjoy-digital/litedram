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

class LiteDRAMAvalonMM2Native(Module):
    def __init__(self, avalon, port, base_address=0x00000000):
        avalon_data_width = len(avalon.writedata)
        port_data_width     = 2**int(log2(len(port.wdata.data))) # Round to lowest power 2
        ratio               = avalon_data_width/port_data_width

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

        aborted = Signal()
        offset  = base_address >> log2_int(port.data_width//8)

        self.submodules.fsm = fsm = FSM(reset_state="CMD")
        self.comb += [
            port.cmd.addr.eq(avalon.address - offset),
            port.cmd.we.eq(avalon.write),
            port.cmd.last.eq(~avalon.write), # Always wait for reads.
            port.flush.eq(~(avalon.write | avalon.read)),    # Flush writes when transaction ends.
        ]
        fsm.act("CMD",
            port.cmd.valid.eq(avalon.read | avalon.write),
            If(port.cmd.valid & port.cmd.ready & avalon.write, NextState("WRITE")),
            If(port.cmd.valid & port.cmd.ready & avalon.read,  NextState("READ")),
            avalon.waitrequest.eq(1),
            NextValue(aborted, 0),
        )
        self.comb += [
            If(ratio <= 1, If(~fsm.ongoing("WRITE"), port.wdata.valid.eq(0))),
            port.wdata.data.eq(avalon.writedata),
            port.wdata.we.eq(avalon.byteenable),
            port.wdata.valid.eq(avalon.write),
        ]
        fsm.act("WRITE",
            avalon.waitrequest.eq(~port.wdata.ready),
            NextValue(aborted, ~avalon.write | aborted),
            If(port.wdata.valid & port.wdata.ready,
                avalon.waitrequest.eq(~(avalon.write & ~aborted)),
                NextState("CMD")
            ),
        )
        self.comb += port.rdata.ready.eq(1)
        fsm.act("READ",
            NextValue(aborted, ~avalon.read | aborted),
            avalon.waitrequest.eq(~(port.rdata.ready & ~aborted)),
            If(port.rdata.valid,
                avalon.waitrequest.eq(~(avalon.read & ~aborted)),
                avalon.readdata.eq(port.rdata.data),
                avalon.readdatavalid.eq(1),
                NextState("CMD")
            )
        )
