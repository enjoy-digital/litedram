"""Wishbone frontend for LiteDRAM"""

from migen import *


class LiteDRAMWishbone2Native(Module):
    def __init__(self, wishbone, port):

        # # #

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(wishbone.cyc & wishbone.stb,
                NextState("ISSUE-CMD")
            )
        )
        fsm.act("ISSUE-CMD",
            port.cmd.valid.eq(1),
            port.cmd.addr.eq(wishbone.adr),
            port.cmd.we.eq(wishbone.we),
            If(port.cmd.ready,
                If(wishbone.we,
                    NextState("WRITE-DATA")
                ).Else(
                    NextState("READ-DATA")
                )
            )
        )
        fsm.act("WRITE-DATA",
            port.wdata.valid.eq(1),
            port.wdata.we.eq(wishbone.sel),
            port.wdata.data.eq(wishbone.dat_w),
            If(port.wdata.ready,
                wishbone.ack.eq(1),
                NextState("IDLE")
            )
        )
        fsm.act("READ-DATA",
            port.rdata.ready.eq(1),
            If(port.rdata.valid,
                wishbone.dat_r.eq(port.rdata.data),
                wishbone.ack.eq(1),
                NextState("IDLE")
            )
        )


class LiteDRAMWishbone2AXI(Module):
    def __init__(self, wishbone, port):

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
            port.ar.addr[ashift:].eq(wishbone.adr),
            If(port.ar.ready,
                NextValue(port.ar.valid, 0)
            ),
            If(port.r.valid,
                port.r.ready.eq(1),
                wishbone.dat_r.eq(port.r.data),
                wishbone.ack.eq(1),
                wishbone.err.eq(port.r.resp != 0b10),
                NextState("IDLE")
            )
        )
