"""AXI frontend for LiteDRAM"""

from migen import *
from migen.genlib.record import *
from migen.genlib.roundrobin import *

from litex.soc.interconnect import stream

burst_types = {
    "fixed":    0b00,
    "incr":     0b01,
    "wrap":     0b10, # FIXME: Not implemented
    "reserved": 0b11
}

def ax_description(address_width, id_width):
    return [
        ("addr",  address_width),
        ("burst", 2), # burst type
        ("len",   8), # number of data transfers (up to 256)
        ("size",  4), # number of bytes of each data transfer (up to 1024 bits)
        ("id",    id_width)
    ]

def w_description(data_width):
    return [
        ("data", data_width),
        ("strb", data_width//8)
    ]

def b_description(id_width):
    return [
        ("id", id_width)
    ]

def r_description(data_width, id_width):
    return [
        ("data", data_width),
        ("id", id_width)
    ]


class LiteDRAMAXIPort(Record):
    def __init__(self, data_width, address_width, id_width, clock_domain="sys"):
        self.data_width = data_width
        self.address_width = address_width
        self.id_width = id_width
        self.clock_domain = clock_domain

        self.aw = stream.Endpoint(ax_description(address_width, id_width))
        self.w = stream.Endpoint(w_description(data_width))
        self.b = stream.Endpoint(b_description(id_width))
        self.ar = stream.Endpoint(ax_description(address_width, id_width))
        self.r = stream.Endpoint(r_description(data_width, id_width))


class LiteDRAMAXIBurst2Beat(Module):
    def __init__(self, ax_burst, ax_beat):

        # # #

        count = Signal(8)
        size = Signal(8+4)
        offset = Signal(8+4)

        # convert burst size to bytes
        cases = {}
        for i in range(11):
            cases[i] = size.eq(2**i)
        self.comb += Case(ax_burst.size, cases)

        # fsm
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            ax_beat.valid.eq(ax_burst.valid),
            ax_beat.addr.eq(ax_burst.addr),
            ax_beat.id.eq(ax_burst.id),
            If(ax_beat.valid & ax_beat.ready,
                If(ax_burst.len != 0,
                    NextValue(count, 0),
                    NextValue(offset, size),
                    NextState("BURST2BEAT")
                ).Else(
                    ax_burst.ready.eq(1)
                )
            )
        )
        fsm.act("BURST2BEAT",
            ax_beat.valid.eq(1),
            If(ax_burst.burst == burst_types["incr"],
                ax_beat.addr.eq(ax_burst.addr + offset)
            ).Else(
                ax_beat.addr.eq(ax_burst.addr)
            ),
            ax_beat.id.eq(ax_burst.id),
            If(ax_beat.valid & ax_beat.ready,
                If(count == (ax_burst.len - 1),
                    ax_burst.ready.eq(1),
                    NextState("IDLE")
                ).Else(
                    NextValue(count, count + 1),
                    NextValue(offset, offset + size)
                )
            )
        )


class LiteDRAMAXI2Native(Module):
    def __init__(self, axi, port, w_buffer_depth=8, r_buffer_depth=8):

        # # #

        ashift = log2_int(port.data_width//8)

        can_write = Signal()
        can_read = Signal()

        # Burst to beat
        aw = stream.Endpoint(ax_description(axi.address_width, axi.id_width))
        ar = stream.Endpoint(ax_description(axi.address_width, axi.id_width))
        aw_burst2beat = LiteDRAMAXIBurst2Beat(axi.aw, aw)
        ar_burst2beat = LiteDRAMAXIBurst2Beat(axi.ar, ar)
        self.submodules += aw_burst2beat, ar_burst2beat

        # Write / Read buffers
        w_buffer = stream.SyncFIFO(w_description(axi.data_width), w_buffer_depth)
        r_buffer = stream.SyncFIFO(r_description(axi.data_width, axi.id_width), r_buffer_depth)
        self.submodules += w_buffer, r_buffer

        # Write Buffer reservation
        self.comb += can_write.eq(w_buffer.sink.ready)

        # Write Buffer ID & Response
        w_buffer_id = stream.SyncFIFO([("id", axi.id_width)], w_buffer_depth)
        self.submodules += w_buffer_id
        self.comb += [
            w_buffer_id.sink.valid.eq(aw.valid & aw.ready),
            w_buffer_id.sink.id.eq(aw.id),
            axi.b.valid.eq(axi.w.valid & axi.w.ready), # FIXME: axi.b always supposed to be ready
            axi.b.id.eq(w_buffer_id.source.id),
            w_buffer_id.source.ready.eq(axi.b.valid & axi.b.ready)
        ]

        # Read Buffer reservation
        # - incremented when data is planned to be queued
        # - decremented when data is dequeued
        r_buffer_queue = Signal()
        r_buffer_dequeue = Signal()
        r_buffer_level = Signal(max=r_buffer_depth+1)
        self.comb += [
            r_buffer_queue.eq(port.cmd.valid & port.cmd.ready & ~port.cmd.we),
            r_buffer_dequeue.eq(r_buffer.source.valid & r_buffer.source.ready)
        ]
        self.sync += [
            If(r_buffer_queue,
                If(~r_buffer_dequeue, r_buffer_level.eq(r_buffer_level + 1))
            ).Elif(r_buffer_dequeue,
                r_buffer_level.eq(r_buffer_level - 1)
            )
        ]
        self.comb += can_read.eq(r_buffer_level != r_buffer_depth)

        # Read Buffer ID
        r_buffer_id = stream.SyncFIFO([("id", axi.id_width)], r_buffer_depth)
        self.submodules += r_buffer_id
        self.comb += [
            r_buffer_id.sink.valid.eq(ar.valid & ar.ready),
            r_buffer_id.sink.id.eq(ar.id),
            axi.r.id.eq(r_buffer_id.source.id),
            r_buffer_id.source.ready.eq(axi.r.valid & axi.r.ready)
        ]

        # Write / Read command arbitration
        arbiter = RoundRobin(2, SP_CE)
        self.submodules += arbiter
        self.comb += [
            arbiter.request[0].eq(aw.valid & can_write),
            arbiter.request[1].eq(ar.valid & can_read),
            arbiter.ce.eq(~port.cmd.valid | port.cmd.ready)
        ]

        self.comb += [
            If(arbiter.grant,
                port.cmd.valid.eq(ar.valid & can_read),
                ar.ready.eq(port.cmd.ready & can_read),
                port.cmd.we.eq(0),
                port.cmd.adr.eq(ar.addr >> ashift)
            ).Else(
                port.cmd.valid.eq(aw.valid & can_write),
                aw.ready.eq(port.cmd.ready & can_write),
                port.cmd.we.eq(1),
                port.cmd.adr.eq(aw.addr >> ashift)
            )
        ]

        # Write data
        self.comb += [
            axi.w.connect(w_buffer.sink),
            w_buffer.source.connect(port.wdata, omit={"strb"}),
            port.wdata.we.eq(w_buffer.source.strb)
        ]

        # Read data
        self.comb += [
            port.rdata.connect(r_buffer.sink),
            r_buffer.source.connect(axi.r)
        ]
