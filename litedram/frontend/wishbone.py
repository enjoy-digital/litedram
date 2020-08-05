# This file is Copyright (c) 2016-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

"""Wishbone frontend for LiteDRAM"""

from math import log2

from migen import *

from litex.soc.interconnect import stream
from litedram.common import LiteDRAMNativePort
from litedram.frontend.adaptation import LiteDRAMNativePortConverter


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

        # Write Datapath ---------------------------------------------------------------------------
        self.comb += [
            port.wdata.data.eq(wishbone.dat_w),
            port.wdata.we.eq(wishbone.sel),
        ]

        # Read Datapath ----------------------------------------------------------------------------
        self.comb += [
            wishbone.dat_r.eq(port.rdata.data),
        ]

        # Control ----------------------------------------------------------------------------------
        self.submodules.fsm = fsm = FSM(reset_state="CMD")
        fsm.act("CMD",
            port.flush.eq(~wishbone.cyc),   # Flush write when transaction ends.
            port.cmd.last.eq(~wishbone.we), # Always wait for reads.
            port.cmd.valid.eq(wishbone.cyc & wishbone.stb),
            port.cmd.we.eq(wishbone.we),
            port.cmd.addr.eq(wishbone.adr - adr_offset),
            If(port.cmd.valid & port.cmd.ready,
                If(wishbone.we,
                    NextState("WAIT-WRITE")
                ).Else(
                    NextState("WAIT-READ")
                )
            )
        )
        fsm.act("WAIT-WRITE",
            port.wdata.valid.eq(1),
            If(port.wdata.ready,
                wishbone.ack.eq(1),
                NextState("CMD")
            )
        )
        fsm.act("WAIT-READ",
            port.rdata.ready.eq(1),
            If(port.rdata.valid,
               wishbone.ack.eq(1),
               NextState("CMD")
            )
        )
