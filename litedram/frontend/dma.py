from litex.gen import *
from litex.gen.genlib.fifo import SyncFIFO

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
        fifo = SyncFIFO(port.dw, fifo_depth)
        self.submodules += fifo

        self.comb += [
            fifo.din.eq(port.rdata),
            fifo.we.eq(port.rdata_valid),

            source.valid.eq(fifo.readable),
            fifo.re.eq(source.ready),
            source.data.eq(fifo.dout),
            data_dequeued.eq(source.valid & source.ready)
        ]


class LiteDRAMDMAWriter(Module):
    def __init__(self, port, fifo_depth=16):
        self.sink = sink = stream.Endpoint([("address", port.aw),
                                            ("data", port.dw)])

        # # #

        fifo = SyncFIFO(port.dw, fifo_depth)
        self.submodules += fifo

        self.comb += [
            port.we.eq(1),
            port.valid.eq(fifo.writable & sink.valid),
            port.adr.eq(sink.address),
            sink.ready.eq(fifo.writable & port.ready),
            fifo.we.eq(sink.valid & port.ready),
            fifo.din.eq(sink.data)
        ]

        self.comb += [
            If(port.wdata_ready,
                fifo.re.eq(1),
                port.wdata_we.eq(2**(port.dw//8)-1),
                port.wdata.eq(fifo.dout)
            )
        ]
