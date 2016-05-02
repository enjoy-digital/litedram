from litex.gen import *
from litex.gen.genlib.roundrobin import *
from litex.gen.genlib.misc import WaitTimer

from litex.soc.interconnect import stream

from litedram.core.multiplexer import *


class _AddressSlicer:
    def __init__(self, colbits, address_align):
        self.colbits = colbits
        self.address_align = address_align

    def row(self, address):
        split = self.colbits - self.address_align
        if isinstance(address, int):
            return address >> split
        else:
            return address[split:]

    def col(self, address):
        split = self.colbits - self.address_align
        if isinstance(address, int):
            return (address & (2**split - 1)) << self.address_align
        else:
            return Cat(Replicate(0, self.address_align), address[:split])


class BankMachine(Module):
    def __init__(self, aw, n, address_align, geom_settings, timing_settings, controller_settings):
        self.req = req = Record(cmd_layout(aw))
        self.refresh_req = Signal()
        self.refresh_gnt = Signal()
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(geom_settings.addressbits,
                                                               geom_settings.bankbits))

        # # #

        # Request FIFO
        fifo = stream.SyncFIFO([("we", 1), ("adr", len(req.adr))],
                               controller_settings.req_queue_size)
        self.submodules += fifo
        self.comb += [
            req.connect(fifo.sink, omit=["dat_w_ack", "dat_r_ack", "lock"]),
            fifo.source.ready.eq(req.dat_w_ack | req.dat_r_ack),
            req.lock.eq(fifo.source.valid),
        ]

        slicer = _AddressSlicer(geom_settings.colbits, address_align)

        # Row tracking
        has_openrow = Signal()
        openrow = Signal(geom_settings.rowbits)
        hit = Signal()
        self.comb += hit.eq(openrow == slicer.row(fifo.source.adr))
        track_open = Signal()
        track_close = Signal()
        self.sync += [
            If(track_open,
                has_openrow.eq(1),
                openrow.eq(slicer.row(fifo.source.adr))
            ),
            If(track_close,
                has_openrow.eq(0)
            )
        ]

        # Address generation
        s_row_adr = Signal()
        self.comb += [
            cmd.ba.eq(n),
            If(s_row_adr,
                cmd.a.eq(slicer.row(fifo.source.adr))
            ).Else(
                cmd.a.eq(slicer.col(fifo.source.adr))
            )
        ]

        # Respect write-to-precharge specification
        self.submodules.precharge_timer = WaitTimer(2 + timing_settings.tWR - 1 + 1)
        self.comb += self.precharge_timer.wait.eq(~(cmd.valid &
                                                    cmd.ready &
                                                    cmd.is_write))

        # Control and command generation FSM
        self.submodules.fsm = fsm = FSM()
        fsm.act("REGULAR",
            If(self.refresh_req,
                NextState("REFRESH")
            ).Elif(fifo.source.valid,
                If(has_openrow,
                    If(hit,
                        # NB: write-to-read specification is enforced by multiplexer
                        cmd.valid.eq(1),
                        If(fifo.source.we,
                            req.dat_w_ack.eq(cmd.ready),
                            cmd.is_write.eq(1),
                            cmd.we.eq(1),
                        ).Else(
                            req.dat_r_ack.eq(cmd.ready),
                            cmd.is_read.eq(1)
                        ),
                        cmd.cas.eq(1)
                    ).Else(
                        NextState("PRECHARGE")
                    )
                ).Else(
                    NextState("ACTIVATE")
                )
            )
        )
        fsm.act("PRECHARGE",
            # Notes:
            # 1. we are presenting the column address, A10 is always low
            # 2. since we always go to the ACTIVATE state, we do not need
            # to assert track_close.
            If(self.precharge_timer.done,
                cmd.valid.eq(1),
                If(cmd.ready,
                    NextState("TRP")
                ),
                cmd.ras.eq(1),
                cmd.we.eq(1),
                cmd.is_cmd.eq(1)
            )
        )
        fsm.act("ACTIVATE",
            s_row_adr.eq(1),
            track_open.eq(1),
            cmd.valid.eq(1),
            cmd.is_cmd.eq(1),
            If(cmd.ready,
                NextState("TRCD")
            ),
            cmd.ras.eq(1)
        )
        fsm.act("REFRESH",
            If(self.precharge_timer.done,
                self.refresh_gnt.eq(1),
            ),
            track_close.eq(1),
            cmd.is_cmd.eq(1),
            If(~self.refresh_req,
                NextState("REGULAR")
            )
        )
        fsm.delayed_enter("TRP", "ACTIVATE", timing_settings.tRP-1)
        fsm.delayed_enter("TRCD", "REGULAR", timing_settings.tRCD-1)
