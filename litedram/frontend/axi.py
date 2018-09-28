"""
AXI frontend for LiteDRAM

Converts AXI ports to Native ports.

Features:
- Write/Read arbitration.
- Write/Read data buffers (configurable depth).
- Burst support (FIXED/INCR/WRAP).
- ID support (configurable width).

Limitations:
- Response always okay.
- No reordering.
"""

from migen import *
from migen.genlib.record import *
from migen.genlib.roundrobin import *

from litex.soc.interconnect import stream

burst_types = {
    "fixed":    0b00,
    "incr":     0b01,
    "wrap":     0b10,
    "reserved": 0b11
}

resp_types = {
    "okay":   0b00,
    "exokay": 0b01,
    "slverr": 0b10,
    "decerr": 0b11
}

def ax_description(address_width, id_width):
    return [
        ("addr",  address_width),
        ("burst", 2), # Burst type
        ("len",   8), # Number of data transfers (up to 256)
        ("size",  4), # Number of bytes of each data transfer (up to 1024 bits)
        ("id",    id_width)
    ]

def w_description(data_width):
    return [
        ("data", data_width),
        ("strb", data_width//8)
    ]

def b_description(id_width):
    return [
        ("resp", 2),
        ("id", id_width)
    ]

def r_description(data_width, id_width):
    return [
        ("resp", 2),
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
        size = Signal(8 + 4)
        offset = Signal(8 + 4)

        # convert burst size to bytes
        cases = {}
        cases["default"] = size.eq(1024)
        for i in range(10):
            cases[i] = size.eq(2**i)
        self.comb += Case(ax_burst.size, cases)

        # fsm
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            ax_beat.valid.eq(ax_burst.valid),
            ax_beat.last.eq(ax_burst.len == 0),
            ax_beat.addr.eq(ax_burst.addr),
            ax_beat.id.eq(ax_burst.id),
            If(ax_beat.valid & ax_beat.ready,
                If(ax_burst.len != 0,
                    NextState("BURST2BEAT")
                ).Else(
                    ax_burst.ready.eq(1)
                )
            ),
            NextValue(count, 1),
            NextValue(offset, size),
        )
        wrap_offset = Signal(8 + 4)
        self.sync += wrap_offset.eq((ax_burst.len - 1)*size)
        fsm.act("BURST2BEAT",
            ax_beat.valid.eq(1),
            ax_beat.last.eq(count == ax_burst.len),
            If((ax_burst.burst == burst_types["incr"]) |
               (ax_burst.burst == burst_types["wrap"]),
                ax_beat.addr.eq(ax_burst.addr + offset)
            ).Else(
                ax_beat.addr.eq(ax_burst.addr)
            ),
            ax_beat.id.eq(ax_burst.id),
            If(ax_beat.valid & ax_beat.ready,
                If(ax_beat.last,
                    ax_burst.ready.eq(1),
                    NextState("IDLE")
                ),
                NextValue(count, count + 1),
                NextValue(offset, offset + size),
                If(ax_burst.burst == burst_types["wrap"],
                    If(offset == wrap_offset,
                        NextValue(offset, 0)
                    )
                )
            )
        )


class LiteDRAMAXI2NativeW(Module):
    def __init__(self, axi, port, buffer_depth):
        self.cmd_request = Signal()
        self.cmd_grant = Signal()

        # # #

        ashift = log2_int(port.data_width//8)

        # Burst to Beat
        aw_buffer = stream.Buffer(ax_description(axi.address_width, axi.id_width))
        self.comb += axi.aw.connect(aw_buffer.sink)
        aw = stream.Endpoint(ax_description(axi.address_width, axi.id_width))
        aw_burst2beat = LiteDRAMAXIBurst2Beat(aw_buffer.source, aw)
        self.submodules += aw_buffer, aw_burst2beat

        # Write Buffer
        w_buffer = stream.SyncFIFO(w_description(axi.data_width), buffer_depth)
        self.submodules += w_buffer

        # Write ID Buffer & Response
        id_buffer = stream.SyncFIFO([("id", axi.id_width)], buffer_depth)
        resp_buffer = stream.SyncFIFO([("id", axi.id_width), ("resp", 2)], buffer_depth)
        self.submodules += id_buffer, resp_buffer
        self.comb += [
            id_buffer.sink.valid.eq(aw.valid & aw.ready),
            id_buffer.sink.id.eq(aw.id),
            If(axi.w.valid & axi.w.last & axi.w.ready,
                resp_buffer.sink.valid.eq(1),
                resp_buffer.sink.resp.eq(resp_types["okay"]),
                resp_buffer.sink.id.eq(id_buffer.source.id),
                id_buffer.source.ready.eq(1)
            ),
            resp_buffer.source.connect(axi.b)
        ]

        # Command
        self.comb += [
            self.cmd_request.eq(aw.valid),
            If(self.cmd_grant,
                port.cmd.valid.eq(aw.valid),
                aw.ready.eq(port.cmd.ready),
                port.cmd.we.eq(1),
                port.cmd.addr.eq(aw.addr >> ashift)
            )
        ]

        # Write Data
        self.comb += [
            If(id_buffer.source.valid, axi.w.connect(w_buffer.sink)),
            w_buffer.source.connect(port.wdata, omit={"strb"}),
            port.wdata.we.eq(w_buffer.source.strb)
        ]


class LiteDRAMAXI2NativeR(Module):
    def __init__(self, axi, port, buffer_depth):
        self.cmd_request = Signal()
        self.cmd_grant = Signal()

        # # #

        can_read = Signal()

        ashift = log2_int(port.data_width//8)

        # Burst to Beat
        ar_buffer = stream.Buffer(ax_description(axi.address_width, axi.id_width))
        self.comb += axi.ar.connect(ar_buffer.sink)
        ar = stream.Endpoint(ax_description(axi.address_width, axi.id_width))
        ar_burst2beat = LiteDRAMAXIBurst2Beat(ar_buffer.source, ar)
        self.submodules += ar_buffer, ar_burst2beat

        # Read buffer
        r_buffer = stream.SyncFIFO(r_description(axi.data_width, axi.id_width), buffer_depth)
        self.submodules += r_buffer

        # Read Buffer reservation
        # - Incremented when data is planned to be queued
        # - Decremented when data is dequeued
        r_buffer_queue = Signal()
        r_buffer_dequeue = Signal()
        r_buffer_level = Signal(max=buffer_depth + 1)
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
        self.comb += can_read.eq(r_buffer_level != buffer_depth)

        # Read ID Buffer
        id_buffer = stream.SyncFIFO([("id", axi.id_width)], buffer_depth)
        self.submodules += id_buffer
        self.comb += [
            id_buffer.sink.valid.eq(ar.valid & ar.ready),
            id_buffer.sink.last.eq(ar.last),
            id_buffer.sink.id.eq(ar.id),
            axi.r.last.eq(id_buffer.source.last),
            axi.r.id.eq(id_buffer.source.id),
            id_buffer.source.ready.eq(axi.r.valid & axi.r.ready)
        ]

        # Command
        self.comb += [
            self.cmd_request.eq(ar.valid & can_read),
            If(self.cmd_grant,
                port.cmd.valid.eq(ar.valid & can_read),
                ar.ready.eq(port.cmd.ready & can_read),
                port.cmd.we.eq(0),
                port.cmd.addr.eq(ar.addr >> ashift)
            )
        ]

        # Read data
        self.comb += [
            port.rdata.connect(r_buffer.sink, omit={"bank"}),
            r_buffer.source.connect(axi.r, omit={"id", "last"}),
            axi.r.resp.eq(resp_types["okay"])
        ]


class LiteDRAMAXI2Native(Module):
    def __init__(self, axi, port, w_buffer_depth=16, r_buffer_depth=16):

        # # #

        # Write path
        self.submodules.write = LiteDRAMAXI2NativeW(axi, port, w_buffer_depth)

        # Read path
        self.submodules.read = LiteDRAMAXI2NativeR(axi, port, r_buffer_depth)

        # Write / Read arbitration
        arbiter = RoundRobin(2, SP_CE)
        self.submodules += arbiter
        self.comb += arbiter.ce.eq(~port.cmd.valid | port.cmd.ready)
        for i, master in enumerate([self.write, self.read]):
            self.comb += arbiter.request[i].eq(master.cmd_request)
            self.comb += master.cmd_grant.eq(arbiter.grant == i)
