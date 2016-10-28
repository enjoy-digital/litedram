from litex.gen import *

from litex.soc.interconnect import stream


class LiteDRAMDMAReader(Module):
    def __init__(self, port, fifo_depth=16, fifo_buffered=False):
        self.sink = sink = stream.Endpoint([("address", port.aw)])
        self.source = source = stream.Endpoint([("data", port.dw)])

        # # #

        # request issuance
        request_enable = Signal()
        request_issued = Signal()

        self.comb += [
            port.cmd.we.eq(0),
            port.cmd.valid.eq(sink.valid & request_enable),
            port.cmd.adr.eq(sink.address),
            sink.ready.eq(port.cmd.ready & request_enable),
            request_issued.eq(port.cmd.valid & port.cmd.ready)
        ]

        # FIFO reservation level counter
        # incremented when data is planned to be queued
        # decremented when data is dequeued
        data_dequeued = Signal()
        rsv_level = Signal(max=fifo_depth+1)
        self.sync += [
            If(request_issued,
                If(~data_dequeued, rsv_level.eq(rsv_level + 1))
            ).Elif(data_dequeued,
                rsv_level.eq(rsv_level - 1)
            )
        ]
        self.comb += request_enable.eq(rsv_level != fifo_depth)

        # FIFO
        fifo = stream.SyncFIFO([("data", port.dw)], fifo_depth, fifo_buffered)
        self.submodules += fifo

        self.comb += [
            port.rdata.connect(fifo.sink),
            fifo.source.connect(source),
            data_dequeued.eq(source.valid & source.ready)
        ]


class LiteDRAMDMAWriter(Module):
    def __init__(self, port, fifo_depth=16, fifo_buffered=False):
        self.sink = sink = stream.Endpoint([("address", port.aw),
                                            ("data", port.dw)])

        # # #

        fifo = stream.SyncFIFO([("data", port.dw)], fifo_depth, fifo_buffered)
        self.submodules += fifo

        self.comb += [
            port.cmd.we.eq(1),
            port.cmd.valid.eq(fifo.sink.ready & sink.valid),
            port.cmd.adr.eq(sink.address),
            sink.ready.eq(fifo.sink.ready & port.cmd.ready),
            fifo.sink.valid.eq(sink.valid & port.cmd.ready),
            fifo.sink.data.eq(sink.data)
        ]

        self.comb += [
            port.wdata.valid.eq(fifo.source.valid),
            fifo.source.ready.eq(port.wdata.ready),
            port.wdata.we.eq(2**(port.dw//8)-1),
            port.wdata.data.eq(fifo.source.data)
        ]
