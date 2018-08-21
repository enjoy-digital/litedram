"""Wishbone frontend for LiteDRAM"""

from migen import *


class LiteDRAMWishbone2Native(Module):
    def __init__(self, wishbone, port):

        # # #

        # Control FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(wishbone.cyc & wishbone.stb,
                NextState("REQUEST")
            )
        )
        fsm.act("REQUEST",
            port.cmd.valid.eq(1),
            port.cmd.we.eq(wishbone.we),
            If(port.cmd.ready,
                If(wishbone.we,
                    NextState("WRITE_DATA")
                ).Else(
                    NextState("READ_DATA")
                )
            )
        )
        fsm.act("WRITE_DATA",
            port.wdata.valid.eq(1),
            If(port.wdata.ready,
                wishbone.ack.eq(1),
                NextState("IDLE")
            )
        )
        fsm.act("READ_DATA",
            port.rdata.ready.eq(1),
            If(port.rdata.valid,
                wishbone.ack.eq(1),
                NextState("IDLE")
            )
        )

        # Address / Datapath
        self.comb += [
            port.cmd.adr.eq(wishbone.adr),
            port.wdata.we.eq(wishbone.sel),
            port.wdata.data.eq(wishbone.dat_w),
            wishbone.dat_r.eq(port.rdata.data)
        ]
