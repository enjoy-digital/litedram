import math
from migen import *
from migen.genlib.misc import WaitTimer

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
    def __init__(self, n, aw, address_align, nranks, settings):
        self.req = req = Record(cmd_layout(aw))
        self.refresh_req = Signal()
        self.refresh_gnt = Signal()
        a = settings.geom.addressbits
        ba = settings.geom.bankbits + log2_int(nranks)
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(a, ba))

        # # #

        auto_precharge = Signal()

        # Command buffer
        cmd_buffer_layout = [("we", 1), ("addr", len(req.addr))]
        cmd_buffer_lookahead = stream.SyncFIFO(
            cmd_buffer_layout, settings.cmd_buffer_depth,
            buffered=settings.cmd_buffer_buffered)
        cmd_buffer = stream.Buffer(cmd_buffer_layout) # 1 depth buffer to detect row change
        self.submodules += cmd_buffer_lookahead, cmd_buffer
        self.comb += [
            req.connect(cmd_buffer_lookahead.sink, keep={"valid", "ready", "we", "addr"}),
            cmd_buffer_lookahead.source.connect(cmd_buffer.sink),
            cmd_buffer.source.ready.eq(req.wdata_ready | req.rdata_valid),
            req.lock.eq(cmd_buffer_lookahead.source.valid | cmd_buffer.source.valid),
        ]

        slicer = _AddressSlicer(settings.geom.colbits, address_align)

        # Row tracking
        has_openrow = Signal()
        openrow = Signal(settings.geom.rowbits, reset_less=True)
        hit = Signal()
        self.comb += hit.eq(openrow == slicer.row(cmd_buffer.source.addr))
        track_open = Signal()
        track_close = Signal()
        self.sync += \
            If(track_close,
                has_openrow.eq(0)
            ).Elif(track_open,
                has_openrow.eq(1),
                openrow.eq(slicer.row(cmd_buffer.source.addr))
            )

        # Address generation
        sel_row_addr = Signal()
        self.comb += [
            cmd.ba.eq(n),
            If(sel_row_addr,
                cmd.a.eq(slicer.row(cmd_buffer.source.addr))
            ).Else(
                cmd.a.eq((auto_precharge << 10) | slicer.col(cmd_buffer.source.addr))
            )
        ]

        # Respect write-to-precharge specification
        write_latency = math.ceil(settings.phy.cwl / settings.phy.nphases)
        precharge_time = write_latency + settings.timing.tWR - 1 + settings.timing.tCCD # AL=0
        precharge_timer = WaitTimer(precharge_time)
        self.submodules += precharge_timer
        self.comb += precharge_timer.wait.eq(~(cmd.valid & cmd.ready & cmd.is_write))

        # Respect tRC activate-activate time
        activate_allowed = Signal(reset=1)
        if settings.timing.tRC is not None:
            trc_time = settings.timing.tRC - 1
            trc_timer = WaitTimer(trc_time)
            self.submodules += trc_timer
            self.comb += trc_timer.wait.eq(~(cmd.valid & cmd.ready & track_open))
            self.comb += activate_allowed.eq(trc_timer.done)

        # Respect tRAS activate-precharge time
        precharge_allowed = Signal(reset=1)
        if settings.timing.tRAS is not None:
            tras_time = settings.timing.tRAS - 1
            tras_timer = WaitTimer(tras_time)
            self.submodules += tras_timer
            self.comb += tras_timer.wait.eq(~(cmd.valid & cmd.ready & track_open))
            self.comb += precharge_allowed.eq(tras_timer.done)

        # Auto Precharge
        if settings.with_auto_precharge:
            self.comb += [
                If(cmd_buffer_lookahead.source.valid & cmd_buffer.source.valid,
                    If(slicer.row(cmd_buffer_lookahead.source.addr) != slicer.row(cmd_buffer.source.addr),
                        auto_precharge.eq(track_close == 0)
                    )
                )
            ]

        # Control and command generation FSM
        # Note: tRRD, tFAW, tCCD, tWTR timings are enforced by the multiplexer
        self.submodules.fsm = fsm = FSM()
        fsm.act("REGULAR",
            If(self.refresh_req,
                NextState("REFRESH")
            ).Elif(cmd_buffer.source.valid,
                If(has_openrow,
                    If(hit,
                        cmd.valid.eq(1),
                        If(cmd_buffer.source.we,
                            req.wdata_ready.eq(cmd.ready),
                            cmd.is_write.eq(1),
                            cmd.we.eq(1),
                        ).Else(
                            req.rdata_valid.eq(cmd.ready),
                            cmd.is_read.eq(1)
                        ),
                        cmd.cas.eq(1),
                        If(cmd.ready & auto_precharge,
                           NextState("AUTOPRECHARGE")
                        )
                    ).Else(
                        NextState("PRECHARGE")
                    )
                ).Else(
                    NextState("ACTIVATE")
                )
            )
        )
        fsm.act("PRECHARGE",
            # Note: we are presenting the column address, A10 is always low
            If(precharge_timer.done & precharge_allowed,
                cmd.valid.eq(1),
                If(cmd.ready,
                    NextState("TRP")
                ),
                cmd.ras.eq(1),
                cmd.we.eq(1),
                cmd.is_cmd.eq(1)
            ),
            track_close.eq(1)
        )
        fsm.act("AUTOPRECHARGE",
            If(precharge_timer.done & precharge_allowed,
                NextState("TRP")
            ),
            track_close.eq(1)
        )
        fsm.act("ACTIVATE",
            sel_row_addr.eq(1),
            track_open.eq(1),
            cmd.valid.eq(1),
            cmd.is_cmd.eq(1),
            If(cmd.ready,
                NextState("TRCD")
            ),
            cmd.ras.eq(1)
        )
        fsm.act("REFRESH",
            If(precharge_timer.done,
                self.refresh_gnt.eq(1),
            ),
            track_close.eq(1),
            cmd.is_cmd.eq(1),
            If(~self.refresh_req,
                NextState("REGULAR")
            )
        )
        fsm.delayed_enter("TRP", "ACTIVATE", settings.timing.tRP - 1)
        fsm.delayed_enter("TRCD", "REGULAR", settings.timing.tRCD - 1)
