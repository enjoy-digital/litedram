#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

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
from litex.soc.interconnect.axi import *

# LiteDRAMAXIPort ----------------------------------------------------------------------------------

class LiteDRAMAXIPort(AXIInterface):
    pass

# LiteDRAMAXI2NativeW ------------------------------------------------------------------------------

class LiteDRAMAXI2NativeW(Module):
    def __init__(self, axi, port, buffer_depth, base_address):
        assert axi.address_width >= log2_int(base_address)
        assert axi.data_width    == port.data_width
        self.cmd_request = Signal()
        self.cmd_grant   = Signal()

        # # #

        ashift = log2_int(port.data_width//8)

        # Burst to Beat ----------------------------------------------------------------------------
        aw_buffer = stream.Buffer(ax_description(axi.address_width, axi.id_width))
        self.submodules += aw_buffer
        self.comb += axi.aw.connect(aw_buffer.sink)
        aw = stream.Endpoint(ax_description(axi.address_width, axi.id_width))
        aw_burst2beat = AXIBurst2Beat(aw_buffer.source, aw)
        self.submodules.aw_burst2beat = aw_burst2beat

        # Write Buffer -----------------------------------------------------------------------------
        w_buffer = stream.SyncFIFO(w_description(axi.data_width, axi.id_width),
            buffer_depth, buffered=True)
        self.submodules.w_buffer = w_buffer

        # Write ID Buffer & Response ---------------------------------------------------------------
        id_buffer   = stream.SyncFIFO([("id", axi.id_width)], buffer_depth)
        resp_buffer = stream.SyncFIFO([("id", axi.id_width), ("resp", 2)], buffer_depth)
        self.submodules += id_buffer, resp_buffer
        self.comb += [
            id_buffer.sink.valid.eq(aw.valid & aw.first & aw.ready),
            id_buffer.sink.id.eq(aw.id),
            If(w_buffer.source.valid &
               w_buffer.source.last &
               w_buffer.source.ready,
                resp_buffer.sink.valid.eq(1),
                resp_buffer.sink.resp.eq(RESP_OKAY),
                resp_buffer.sink.id.eq(id_buffer.source.id),
                id_buffer.source.ready.eq(1)
            ),
            resp_buffer.source.connect(axi.b)
        ]

        # Command ----------------------------------------------------------------------------------
        # Accept and send command to the controller only if:
        # - Address & Data request are *both* valid.
        # - Data buffer is not full.
        self.comb += [
            self.cmd_request.eq(aw.valid & axi.w.valid & w_buffer.sink.ready),
            If(self.cmd_request & self.cmd_grant,
                port.cmd.valid.eq(1),
                port.cmd.we.eq(1),
                port.cmd.addr.eq((aw.addr - base_address) >> ashift),
                aw.ready.eq(port.cmd.ready),
                axi.w.connect(w_buffer.sink, omit={"valid", "ready"}),
                If(port.cmd.ready,
                    w_buffer.sink.valid.eq(1),
                    axi.w.ready.eq(1)
                )
            )
        ]

        # Write Data -------------------------------------------------------------------------------
        self.comb += [
            w_buffer.source.connect(port.wdata, omit={"strb", "id"}),
            port.wdata.we.eq(w_buffer.source.strb)
        ]

# LiteDRAMAXI2NativeR ------------------------------------------------------------------------------

class LiteDRAMAXI2NativeR(Module):
    def __init__(self, axi, port, buffer_depth, base_address):
        assert axi.address_width >= log2_int(base_address)
        assert axi.data_width    == port.data_width
        self.cmd_request = Signal()
        self.cmd_grant   = Signal()

        # # #

        can_read = Signal()

        ashift = log2_int(port.data_width//8)

        # Burst to Beat ----------------------------------------------------------------------------
        ar_buffer = stream.Buffer(ax_description(axi.address_width, axi.id_width))
        self.submodules += ar_buffer
        self.comb += axi.ar.connect(ar_buffer.sink)
        ar = stream.Endpoint(ax_description(axi.address_width, axi.id_width))
        ar_burst2beat = AXIBurst2Beat(ar_buffer.source, ar)
        self.submodules.ar_burst2beat = ar_burst2beat

        # Read buffer ------------------------------------------------------------------------------
        r_buffer = stream.SyncFIFO(r_description(axi.data_width, axi.id_width), buffer_depth, buffered=True)
        self.submodules.r_buffer = r_buffer

        # Read Buffer reservation ------------------------------------------------------------------
        # - Incremented when data is planned to be queued
        # - Decremented when data is dequeued
        r_buffer_queue   = Signal()
        r_buffer_dequeue = Signal()
        r_buffer_level   = Signal(max=buffer_depth + 1)
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

        # Read ID Buffer ---------------------------------------------------------------------------
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

        # Command ----------------------------------------------------------------------------------
        self.comb += [
            self.cmd_request.eq(ar.valid & can_read),
            If(self.cmd_grant,
                port.cmd.valid.eq(ar.valid & can_read),
                ar.ready.eq(port.cmd.ready & can_read),
                port.cmd.we.eq(0),
                port.cmd.addr.eq((ar.addr - base_address) >> ashift)
            )
        ]

        # Read data --------------------------------------------------------------------------------
        self.comb += [
            port.rdata.connect(r_buffer.sink, omit={"bank"}),
            r_buffer.source.connect(axi.r, omit={"id", "last"}),
            axi.r.resp.eq(RESP_OKAY)
        ]

# LiteDRAMAXI2Native -------------------------------------------------------------------------------

class LiteDRAMAXI2Native(Module):
    def __init__(self, axi, port, w_buffer_depth=16, r_buffer_depth=16, base_address=0x00000000):

        # # #

        # Write path -------------------------------------------------------------------------------
        self.submodules.write = LiteDRAMAXI2NativeW(axi, port, w_buffer_depth, base_address)

        # Read path --------------------------------------------------------------------------------
        self.submodules.read = LiteDRAMAXI2NativeR(axi, port, r_buffer_depth, base_address)

        # Write / Read arbitration -----------------------------------------------------------------
        arbiter = RoundRobin(2, SP_CE)
        self.submodules += arbiter
        self.comb += arbiter.ce.eq(~port.cmd.valid | port.cmd.ready)
        for i, master in enumerate([self.write, self.read]):
            self.comb += arbiter.request[i].eq(master.cmd_request)
            self.comb += master.cmd_grant.eq(arbiter.grant == i)
