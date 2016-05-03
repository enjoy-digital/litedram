from litex.gen import *


class LiteDRAMWishboneBridge(Module):
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
            port.valid.eq(1),
            port.we.eq(wishbone.we),
            If(port.ready,
                If(wishbone.we,
                    NextState("WRITE_DATA")
                ).Else(
                    NextState("READ_DATA")
                )
            )
        )
        fsm.act("WRITE_DATA",
            If(port.wdata_ready,
                port.wdata_we.eq(wishbone.sel),
                wishbone.ack.eq(1),
                NextState("IDLE")
            )
        )
        fsm.act("READ_DATA",
            If(port.rdata_valid,
                wishbone.ack.eq(1),
                NextState("IDLE")
            )
        )

        # Address / Datapath
        self.comb += [
            port.adr.eq(wishbone.adr),
            If(port.wdata_ready,
                port.wdata.eq(wishbone.dat_w),
            ),
            wishbone.dat_r.eq(port.rdata)
        ]
