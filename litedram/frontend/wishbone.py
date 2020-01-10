# This file is Copyright (c) 2016-2018 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

"""Wishbone frontend for LiteDRAM"""

from migen import *

from litex.soc.interconnect import stream


# LiteDRAMWishbone2Native --------------------------------------------------------------------------

class LiteDRAMWishbone2Native(Module):
    def __init__(self, wishbone, port, base_address=0x00000000):
        assert len(wishbone.dat_w) == len(port.wdata.data)

        # # #

        adr_offset = base_address >> log2_int(port.data_width//8)

        # Write data buffer-------------------------------------------------------------------------
        wdata_buffer = stream.Buffer([("data", port.data_width), ("we", port.data_width//8)])
        self.submodules += wdata_buffer

        # Control ----------------------------------------------------------------------------------
        self.submodules.fsm = fsm = FSM(reset_state="CMD")
        fsm.act("CMD",
            port.cmd.valid.eq(wishbone.cyc & wishbone.stb),
            port.cmd.we.eq(wishbone.we),
            If(port.cmd.valid & port.cmd.ready,
                If(wishbone.we,
                    NextState("WRITE")
                ).Else(
                    NextState("READ")
                )
            )
        )
        fsm.act("WRITE",
            wdata_buffer.sink.valid.eq(1),
            If(wdata_buffer.sink.ready,
                wishbone.ack.eq(1),
                NextState("CMD")
            )
        )
        fsm.act("READ",
            port.rdata.ready.eq(1),
            If(port.rdata.valid,
                wishbone.ack.eq(1),
                NextState("CMD")
            )
        )

        # Datapath ---------------------------------------------------------------------------------
        self.comb += [
            # Cmd
            port.cmd.addr.eq(wishbone.adr - adr_offset),
            # Write
            wdata_buffer.sink.data.eq(wishbone.dat_w),
            wdata_buffer.sink.we.eq(wishbone.sel),
            wdata_buffer.source.connect(port.wdata),
            # Read
            wishbone.dat_r.eq(port.rdata.data),
        ]
