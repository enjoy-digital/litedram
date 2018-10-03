import math
from migen import *
from migen.genlib.misc import WaitTimer

from litex.soc.interconnect import stream

from litedram.core.multiplexer import *
from litedram.common import *


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
        self.want_writes = Signal()
        self.has_writes = Signal()
        self.has_reads = Signal()
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
        cmd_bufferRead = stream.Buffer(cmd_buffer_layout)
        cmd_bufferWrite = stream.Buffer(cmd_buffer_layout)
        self.submodules += cmd_buffer_lookahead, cmd_bufferRead, cmd_bufferWrite
        self.comb += [
            req.connect(cmd_buffer_lookahead.sink, keep={"valid", "ready", "we", "addr"}),
            
            cmd_buffer_lookahead.source.connect(cmd_bufferRead.sink, omit={"valid", "ready"}),
            cmd_buffer_lookahead.source.connect(cmd_bufferWrite.sink, omit={"valid", "ready"}),

            cmd_bufferRead.sink.valid.eq(cmd_buffer_lookahead.source.valid & ~cmd_buffer_lookahead.source.we),
            cmd_bufferWrite.sink.valid.eq(cmd_buffer_lookahead.source.valid & cmd_buffer_lookahead.source.we),

            cmd_buffer_lookahead.source.ready.eq(req.rdata_valid | req.wdata_ready
                | (cmd_buffer_lookahead.source.we & cmd_bufferWrite.source.ready)
                | (~cmd_buffer_lookahead.source.we & cmd_bufferRead.source.ready)),
            #cmd_buffer_lookahead.source.ready.eq(
            #    ((cmd_bufferRead.sink.ready | cmd_bufferRead.source.ready) & ~cmd_buffer_lookahead.source.we)
            #    | ((cmd_bufferWrite.sink.ready | cmd_bufferWrite.source.ready) & cmd_buffer_lookahead.source.we)),

            cmd_bufferRead.source.ready.eq(req.rdata_valid),
            cmd_bufferWrite.source.ready.eq(req.wdata_ready),

            req.lock.eq(cmd_buffer_lookahead.source.valid | cmd_bufferRead.source.valid | cmd_bufferWrite.source.valid),
        ]
        
        cmd_buffer = Record(cmd_buffer_layout + [("valid",1)])
        slicer = _AddressSlicer(settings.geom.colbits, address_align)

        
        # Row tracking
        openrow = Signal(settings.geom.rowbits, reset_less=True)
        hit = Signal()
        track_open = Signal()
        track_close = Signal()
        self.sync += \
            If(track_open,
                openrow.eq(slicer.row(cmd_buffer.addr))
            )

        # Chose the correct source for the command
        self.sync += [
            If((self.want_writes & cmd_bufferWrite.source.valid) | ~cmd_bufferRead.source.valid,
                cmd_buffer.valid.eq(cmd_bufferWrite.source.valid),
                cmd_buffer.we.eq(cmd_bufferWrite.source.we),
                cmd_buffer.addr.eq(cmd_bufferWrite.source.addr),
                hit.eq(openrow == slicer.row(cmd_bufferWrite.source.addr)),
            ).Else(
                cmd_buffer.valid.eq(cmd_bufferRead.source.valid),
                cmd_buffer.we.eq(cmd_bufferRead.source.we),
                cmd_buffer.addr.eq(cmd_bufferRead.source.addr),
                hit.eq(openrow == slicer.row(cmd_bufferRead.source.addr)),
            ),
        ]
        self.comb += [
            self.has_writes.eq(cmd_bufferWrite.source.valid),
            self.has_reads.eq(cmd_bufferWrite.source.valid)
        ]

        # Address generation
        sel_row_addr = Signal()
        self.comb += [
            cmd.ba.eq(n),
            If(sel_row_addr,
                cmd.a.eq(slicer.row(cmd_buffer.addr))
            ).Else(
                cmd.a.eq((auto_precharge << 10) | slicer.col(cmd_buffer.addr))
            )
        ]

        # Respect write-to-precharge specification
        write_latency = math.ceil(settings.phy.cwl / settings.phy.nphases)
        precharge_time = write_latency + settings.timing.tWR + settings.timing.tCCD # AL=0
        self.submodules.twtpcon = twtpcon = tXXDController(precharge_time)
        self.comb += twtpcon.valid.eq(cmd.valid & cmd.ready & cmd.is_write)

        # Respect tRC activate-activate time
        activate_allowed = Signal(reset=1)
        if settings.timing.tRC is not None:
            self.submodules.trccon = trccon = tXXDController(settings.timing.tRC)
            self.comb += trccon.valid.eq(cmd.valid & cmd.ready & track_open)
            self.comb += activate_allowed.eq(trccon.ready)

        # Respect tRAS activate-precharge time
        precharge_allowed = Signal(reset=1)
        if settings.timing.tRAS is not None:
            self.submodules.trascon = trascon = tXXDController(settings.timing.tRAS)
            self.comb += trascon.valid.eq(cmd.valid & cmd.ready & track_open)
            self.comb += precharge_allowed.eq(trascon.ready)

        # Auto Precharge
        if settings.with_auto_precharge:
            self.comb += [
                If(cmd_buffer_lookahead.source.valid & cmd_buffer.valid,
                    If(slicer.row(cmd_buffer_lookahead.source.addr) != slicer.row(cmd_buffer.addr),
                        auto_precharge.eq(track_close == 0)
                    )
                )
            ]

        # Control and command generation FSM
        # Note: tRRD, tFAW, tCCD, tWTR timings are enforced by the multiplexer
        self.submodules.fsm = fsm = FSM()
        fsm.act("ACTIVATE",
            # The bank is in the IDLE state ready for an ACTIVATE
            If(self.refresh_req,
                NextState("REFRESH")
            ).Elif(cmd_buffer.valid,
                sel_row_addr.eq(1),
                track_open.eq(1),
                cmd.valid.eq(1),
                cmd.is_cmd.eq(1),
                cmd.is_activate.eq(1),
                If(cmd.ready,
                    NextState("TRCD")
                ),
                cmd.ras.eq(1)
           )
        )
        fsm.act("REGULAR",
            # The bank is open and ready for read/writes
            If(self.refresh_req,
                NextState("REFRESH")
            ).Elif(cmd_buffer.valid,
                If(hit,
                    cmd.valid.eq(1),
                    If(cmd_buffer.we,
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
            )
        )
        fsm.act("PRECHARGE",
            # Note: we are presenting the column address, A10 is always low
            If(twtpcon.ready & precharge_allowed,
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
            If(twtpcon.ready & precharge_allowed,
                NextState("TRP")
            ),
            track_close.eq(1)
        )
        fsm.act("REFRESH",
            If(twtpcon.ready,
                self.refresh_gnt.eq(1),
            ),
            track_close.eq(1),
            cmd.is_cmd.eq(1),
            If(~self.refresh_req,
                NextState("ACTIVATE")
            )
        )
        fsm.delayed_enter("TRP", "ACTIVATE", settings.timing.tRP - 1)
        fsm.delayed_enter("TRCD", "REGULAR", settings.timing.tRCD - 1)
