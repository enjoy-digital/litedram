# This file is Copyright (c) 2016-2018 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

"""Wishbone frontend for LiteDRAM"""

from migen import *


class LiteDRAMWishbone2Native(Module):
    def __init__(self, wishbone, port, base_address=0x00000000):
        assert len(wishbone.dat_w) == len(port.wdata.data)

        # # #

        adr_offset = base_address >> log2_int(port.data_width//8)

        # Control
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
            port.wdata.valid.eq(1),
            If(port.wdata.ready,
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

        # Datapath
        self.comb += [
            # cmd
            port.cmd.addr.eq(wishbone.adr - adr_offset),
            # write
            port.wdata.we.eq(wishbone.sel),
            port.wdata.data.eq(wishbone.dat_w),
            # read
            wishbone.dat_r.eq(port.rdata.data),
        ]


class LiteDRAMWishbone2AXI(Module):
    def __init__(self, wishbone, port):
        assert len(wishbone.dat_w) == len(port.w.data)

        # # #

        ashift = log2_int(port.data_width//8)

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(wishbone.cyc & wishbone.stb,
                If(wishbone.we,
                    NextValue(port.aw.valid, 1),
                    NextValue(port.w.valid, 1),
                    NextState("WRITE")
                ).Else(
                    NextValue(port.ar.valid, 1),
                    NextState("READ")
                )
            )
        )
        fsm.act("WRITE",
            port.aw.size.eq(ashift),
            port.aw.addr[ashift:].eq(wishbone.adr),
            port.w.last.eq(1),
            port.w.data.eq(wishbone.dat_w),
            port.w.strb.eq(wishbone.sel),
            If(port.aw.ready,
                NextValue(port.aw.valid, 0)
            ),
            If(port.w.ready,
                NextValue(port.w.valid, 0)
            ),
            If(port.b.valid,
                port.b.ready.eq(1),
                wishbone.ack.eq(1),
                wishbone.err.eq(port.b.resp != 0b00),
                NextState("IDLE")
            )
        )
        fsm.act("READ",
            port.ar.size.eq(ashift),
            port.ar.addr[ashift:].eq(wishbone.adr),
            If(port.ar.ready,
                NextValue(port.ar.valid, 0)
            ),
            If(port.r.valid,
                port.r.ready.eq(1),
                wishbone.dat_r.eq(port.r.data),
                wishbone.ack.eq(1),
                wishbone.err.eq(port.r.resp != 0b00),
                NextState("IDLE")
            )
        )
