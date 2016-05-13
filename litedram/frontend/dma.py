from litex.gen import *

from litex.soc.interconnect import stream


class LiteDRAMDMAReader(Module):
    def __init__(self, port, fifo_depth=16):
        self.sink = sink = stream.Endpoint([("address", port.aw)])
        self.source = source = stream.Endpoint([("data", port.dw)])

        # # #

        # request issuance
        request_enable = Signal()
        request_issued = Signal()

        self.comb += [
            port.we.eq(0),
            port.valid.eq(sink.valid & request_enable),
            port.adr.eq(sink.address),
            sink.ready.eq(port.ready & request_enable),
            request_issued.eq(port.valid & port.ready)
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
        fifo = stream.SyncFIFO([("data", port.dw)], fifo_depth)
        self.submodules += fifo

        self.comb += [
            fifo.sink.data.eq(port.rdata),
            fifo.sink.valid.eq(port.rdata_valid),

            fifo.source.connect(source),
            data_dequeued.eq(source.valid & source.ready)
        ]


class LiteDRAMDMAWriter(Module):
    def __init__(self, port, fifo_depth=16):
        self.sink = sink = stream.Endpoint([("address", port.aw),
                                            ("data", port.dw)])

        # # #

        fifo = stream.SyncFIFO([("data", port.dw)], fifo_depth)
        self.submodules += fifo

        self.comb += [
            port.we.eq(1),
            port.valid.eq(fifo.sink.ready & sink.valid),
            port.adr.eq(sink.address),
            sink.ready.eq(fifo.sink.ready & port.ready),
            fifo.sink.valid.eq(sink.valid & port.ready),
            fifo.sink.data.eq(sink.data)
        ]

        self.comb += [
            fifo.source.ready.eq(port.wdata_ready),
            port.wdata_we.eq(2**(port.dw//8)-1),
            port.wdata.eq(fifo.source.data)
        ]
