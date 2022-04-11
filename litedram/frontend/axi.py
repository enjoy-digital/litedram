#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""
AXI frontend for LiteDRAM

Converts AXI ports to Native ports.

Features:
- Write/Read arbitration.
- Write/Read data buffers (configurable depth).
- Burst support (FIXED/INCR/WRAP).
- ID support (configurable width).
- Optional Read-Modify-Write support (When only full words can be written on the DRAM, ex with ECC).

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
    def __init__(self, axi, port, buffer_depth, base_address, with_read_modify_write=False):
        assert axi.address_width >= log2_int(base_address)
        assert axi.data_width    == port.data_width
        self.cmd_request = Signal()
        self.cmd_grant   = Signal()

        # # #

        can_write = Signal()

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

        # Write Buffer reservation ------------------------------------------------------------------
        # - Incremented when data cmd is send
        # - Decremented when data is read
        w_buffer_queue   = Signal()
        w_buffer_dequeue = Signal()
        w_buffer_level   = Signal(max=buffer_depth + 1)
        self.comb += [
            w_buffer_queue.eq(port.cmd.valid & port.cmd.ready & port.cmd.we),
            w_buffer_dequeue.eq(w_buffer.source.valid & w_buffer.source.ready)
        ]
        self.sync += [
            If(w_buffer_queue,
                If(~w_buffer_dequeue, w_buffer_level.eq(w_buffer_level + 1))
            ).Elif(w_buffer_dequeue,
                w_buffer_level.eq(w_buffer_level - 1)
            )
        ]
        self.comb += can_write.eq(w_buffer.level > w_buffer_level)

        # Command ----------------------------------------------------------------------------------
        # Accept and send command to the controller only if:
        # - Address & Data request are *both* valid.
        # - Data buffer is not empty.
        self.comb += [
            self.cmd_request.eq(aw.valid & can_write),
            If(self.cmd_request & self.cmd_grant,
                port.cmd.valid.eq(1),
                port.cmd.last.eq(aw.last),
                port.cmd.we.eq(1),
                port.cmd.addr.eq((aw.addr - base_address) >> ashift),
                If(port.cmd.ready,
                    aw.ready.eq(1),
                )
            )
        ]

        # Write Data -------------------------------------------------------------------------------
        axi_w_connect = Signal(reset=1)
        self.comb += [
            If(axi_w_connect, axi.w.connect(w_buffer.sink)),
            w_buffer.source.connect(port.wdata, omit={"strb", "id"}),
            port.wdata.we.eq(w_buffer.source.strb)
        ]

        # Read-Modify-Write ------------------------------------------------------------------------
        if with_read_modify_write:
            # RMW Request/Grant signals.
            self.rmw_request = Signal()
            self.rmw_rgrant  = Signal()
            self.rmw_wgrant  = Signal()

            # # #

            rmw_data      = Signal(port.data_width)
            rmw_mask      = Signal(port.data_width)
            rmw_cmd_done  = Signal()
            rmw_data_done = Signal()

            # Grant write when write buffer is empty.
            self.comb += self.rmw_wgrant.eq(~w_buffer_queue & (w_buffer_level == 0))

            # Prevent new write on Read-Modify-Write request.
            self.comb += If(self.rmw_request,
                can_write.eq(0)
            )

            # Disconnect regular Datapath on a Read-Modify-Write cycle.
            self.comb += If(self.rmw_request,
                axi_w_connect.eq(0),
            )

            # Read-Modify-Write FSM.
            self.submodules.rmw_fsm = rmw_fsm = FSM(reset_state="IDLE")
            rmw_fsm.act("IDLE",
                # Clear RMW Cmd/Data done signals.
                NextValue(rmw_cmd_done,  0),
                NextValue(rmw_data_done, 0),
                # Detect partial data and initiate a RMW access.
                If(axi.w.valid & (axi.w.strb != (2**len(axi.w.strb) - 1)),
                    # Before issuing the RMW sequence, we must ensure that all pending writes/reads
                    # access have been done, so issue a request and wait for grant.
                    self.rmw_request.eq(1),
                    If(self.rmw_rgrant & self.rmw_wgrant,
                        NextState("READ")
                    )
                )
            )
            rmw_fsm.act("READ",
                self.rmw_request.eq(1),
                # Issue Read Cmd.
                port.cmd.valid.eq(1),
                port.cmd.last.eq(aw.last),
                port.cmd.we.eq(0),
                port.cmd.addr.eq((aw.addr - base_address) >> ashift),
                If(port.cmd.ready,
                    NextState("MODIFY")
                )
            )
            rmw_fsm.act("MODIFY",
                self.rmw_request.eq(1),
                # Generate mask.
                *[rmw_mask[8*i:8*(i+1)].eq(Replicate(axi.w.strb[i], 8)) for i in range(port.data_width//8)],
                # Receive Read Data and modify it.
                port.rdata.ready.eq(1),
                If(port.rdata.valid,
                    # Keep previous unmasked data and replace masked data with new ones.
                    NextValue(rmw_data, (port.rdata.data & ~rmw_mask) | (axi.w.data & rmw_mask)),
                    NextState("WRITE")
                )
            )
            rmw_fsm.act("WRITE",
                self.rmw_request.eq(1),
                # Isssue Write Cmd.
                port.cmd.valid.eq(~rmw_cmd_done),
                port.cmd.last.eq(aw.last),
                port.cmd.we.eq(1),
                port.cmd.addr.eq((aw.addr - base_address) >> ashift),
                If(port.cmd.valid & port.cmd.ready,
                    aw.ready.eq(1),
                    NextValue(rmw_cmd_done, 1)
                ),
                # Issue Write Data.
                w_buffer.sink.valid.eq(~rmw_data_done),
                w_buffer.sink.last.eq(axi.w.last),
                w_buffer.sink.data.eq(rmw_data),
                w_buffer.sink.strb.eq(2**len(w_buffer.sink.strb) - 1),
                If(w_buffer.sink.valid & w_buffer.sink.ready,
                    axi.w.ready.eq(1),
                    NextValue(rmw_data_done, 1)
                ),
                # Return to Idle when both Cmd/Data are done.
                If((port.cmd.ready | rmw_cmd_done) & (w_buffer.sink.ready | rmw_data_done),
                    NextState("IDLE")
                )
            )

# LiteDRAMAXI2NativeR ------------------------------------------------------------------------------

class LiteDRAMAXI2NativeR(Module):
    def __init__(self, axi, port, buffer_depth, base_address, with_read_modify_write=False):
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
            If(self.cmd_request & self.cmd_grant,
                port.cmd.valid.eq(1),
                port.cmd.last.eq(ar.last),
                port.cmd.we.eq(0),
                port.cmd.addr.eq((ar.addr - base_address) >> ashift),
                If(port.cmd.ready,
                    ar.ready.eq(1),
                )
            )
        ]

        # Read data --------------------------------------------------------------------------------
        self.comb += [
            port.rdata.connect(r_buffer.sink, omit={"bank"}),
            r_buffer.source.connect(axi.r, omit={"id", "last"}),
            axi.r.resp.eq(RESP_OKAY)
        ]

        # Read-Modify-Write ------------------------------------------------------------------------
        if with_read_modify_write:
            # RMW Request/Grant signals.
            self.rmw_request = Signal()
            self.rmw_rgrant  = Signal()

            # # #

            # Grant read when read buffer is empty.
            self.comb += self.rmw_rgrant.eq(~r_buffer_queue & (r_buffer_level == 0))

            # Prevent new read on Read-Modify-Write request.
            self.comb += If(self.rmw_request,
                r_buffer_queue.eq(0),
                can_read.eq(0)
            )

            # Disconnect regular Datapath on a Read-Modify-Write cycle.
            self.comb += If(self.rmw_request & self.rmw_rgrant,
                port.rdata.ready.eq(1),
                r_buffer.sink.valid.eq(0)
            )

# LiteDRAMAXI2Native -------------------------------------------------------------------------------

class LiteDRAMAXI2Native(Module):
    def __init__(self, axi, port, w_buffer_depth=16, r_buffer_depth=16, base_address=0x00000000, with_read_modify_write=False):

        # # #

        # Write path -------------------------------------------------------------------------------
        self.submodules.write = LiteDRAMAXI2NativeW(axi, port, w_buffer_depth, base_address, with_read_modify_write)

        # Read path --------------------------------------------------------------------------------
        self.submodules.read = LiteDRAMAXI2NativeR(axi, port, r_buffer_depth, base_address, with_read_modify_write)

        # Write / Read arbitration -----------------------------------------------------------------
        arbiter = RoundRobin(2, SP_CE)
        self.submodules += arbiter
        self.comb += arbiter.ce.eq(~port.cmd.valid | (port.cmd.ready & port.cmd.last))
        for i, master in enumerate([self.write, self.read]):
            self.comb += arbiter.request[i].eq(master.cmd_request)
            self.comb += master.cmd_grant.eq(arbiter.grant == i)

        # Read-Modify-Write ------------------------------------------------------------------------
        if with_read_modify_write:
            self.comb += [
                # Connect RMW-Request/Grant between Write and Read paths.
                self.read.rmw_request.eq(self.write.rmw_request),
                self.write.rmw_rgrant.eq(self.read.rmw_rgrant),
            ]
