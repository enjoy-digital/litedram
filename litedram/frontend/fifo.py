# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

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
        self.base  = base
        self.depth = depth
        self.level = Signal(max=depth+1)

        # # #

        # To write buffer
        self.writable = Signal()
        self.write_address = Signal(max=depth)

        # From write buffer
        self.write = Signal()

        # To read buffer
        self.readable = Signal()
        self.read_address = Signal(max=depth)

        # From read buffer
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
            self.writable.eq(self.level < write_threshold),
            self.readable.eq(self.level > read_threshold)
        ]


class _LiteDRAMFIFOWriter(Module):
    def __init__(self, data_width, port, ctrl):
        self.sink = sink = stream.Endpoint([("data", data_width)])

        # # #

        self.submodules.writer = writer = dma.LiteDRAMDMAWriter(port, fifo_depth=32)
        self.comb += [
            writer.sink.valid.eq(sink.valid & ctrl.writable),
            writer.sink.address.eq(ctrl.base + ctrl.write_address),
            writer.sink.data.eq(sink.data),
            If(writer.sink.valid & writer.sink.ready,
                ctrl.write.eq(1),
                sink.ready.eq(1)
            )
        ]


class _LiteDRAMFIFOReader(Module):
    def __init__(self, data_width, port, ctrl):
        self.source = source = stream.Endpoint([("data", data_width)])

        # # #

        self.submodules.reader = reader = dma.LiteDRAMDMAReader(port, fifo_depth=32)
        self.comb += [
            reader.sink.valid.eq(ctrl.readable),
            reader.sink.address.eq(ctrl.base + ctrl.read_address),
            If(reader.sink.valid & reader.sink.ready,
                ctrl.read.eq(1)
            )
        ]
        self.comb += reader.source.connect(source)


class LiteDRAMFIFO(Module):
    def __init__(self, data_width, base, depth, write_port, read_port,
        read_threshold=None, write_threshold=None):
        self.sink   = stream.Endpoint([("data", data_width)])
        self.source = stream.Endpoint([("data", data_width)])

        # # #

        if read_threshold is None:
            read_threshold = 0
        if write_threshold is None:
            write_threshold = depth

        self.submodules.ctrl   = _LiteDRAMFIFOCtrl(base, depth, read_threshold, write_threshold)
        self.submodules.writer = _LiteDRAMFIFOWriter(data_width, write_port, self.ctrl)
        self.submodules.reader = _LiteDRAMFIFOReader(data_width, read_port, self.ctrl)
        self.comb += [
            self.sink.connect(self.writer.sink),
            self.reader.source.connect(self.source)
        ]
