from litex.gen import *

from litex.soc.interconnect import stream

from litedram.frontend import dma


def _inc(signal, modulo):
    if modulo == 2**len(signal):
        return signal.eq(signal + 1)
    else:
        return If(signal == (modulo - 1),
            signal.eq(0)
        ).Else(
            signal.eq(signal + 1)
        )


class _LiteDRAMFIFOCtrl(Module):
    def __init__(self, base, depth, read_threshold, write_threshold):
        self.base = base
        self.depth = depth
        self.level = Signal(max=depth+1)

        # # #

        # to buffer write
        self.writable = Signal()
        self.write_address = Signal(max=depth)

        # from buffer write
        self.write = Signal()

        # to buffer read
        self.readable = Signal()
        self.read_address = Signal(max=depth)

        # from buffer read
        self.read = Signal()

        # # #

        produce = self.write_address
        consume = self.read_address

        self.sync += [
            If(self.write,
                _inc(produce, depth)
            ),
            If(self.read,
                _inc(consume, depth)
            ),
            If(self.write & ~self.read,
                self.level.eq(self.level + 1),
            ).Elif(self.read & ~self.write,
                self.level.eq(self.level - 1)
            )
        ]

        self.comb += [
            self.writable.eq(self.level <= write_threshold),
            self.readable.eq(self.level >= read_threshold)
        ]


class _LiteDRAMFIFOWriter(Module):
    def __init__(self, dw, port, ctrl):
        self.sink = stream.Endpoint([("data", dw)])

        # # #

        writer = dma.LiteDRAMDMAWriter(port)
        self.submodules += writer

        self.comb += [
            writer.sink.valid.eq(self.sink.valid & ctrl.writable),
            writer.sink.address.eq(ctrl.base + ctrl.write_address),
            writer.sink.data.eq(self.sink.data),
            If(writer.sink.valid & writer.sink.ready,
                ctrl.write.eq(1),
                self.sink.ready.eq(1)
            )
        ]


class _LiteDRAMFIFOReader(Module):
    def __init__(self, dw, port, ctrl):
        self.source = source = stream.Endpoint([("data", dw)])

        # # #

        reader = dma.LiteDRAMDMAReader(port)
        self.submodules += reader

        self.comb += [
            reader.sink.valid.eq(ctrl.readable),
            reader.sink.address.eq(ctrl.base + ctrl.read_address),
            If(reader.sink.valid & reader.sink.ready,
                ctrl.read.eq(1)
            )
        ]
        self.comb += reader.source.connect(self.source)


class LiteDRAMFIFO(Module):
    def __init__(self, dw, base, depth, write_port, read_port,
        read_threshold=None, write_threshold=None):
        self.sink = stream.Endpoint([("data", dw)])
        self.source = stream.Endpoint([("data", dw)])

        # # #

        if read_threshold is None:
            read_threshold = 0
        if write_threshold is None:
            write_threshold = depth

        self.submodules.ctrl = _LiteDRAMFIFOCtrl(base, depth, read_threshold, write_threshold)
        self.submodules.writer = _LiteDRAMFIFOWriter(dw, write_port, self.ctrl)
        self.submodules.reader = _LiteDRAMFIFOReader(dw, read_port, self.ctrl)
        self.comb += [
            self.sink.connect(self.writer.sink),
            self.reader.source.connect(self.source)
        ]
