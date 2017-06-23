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


def _raw_layout(endpoint):
    raw_layout = []
    raw_layout.append(endpoint.first)
    raw_layout.append(endpoint.last)
    raw_layout.append(endpoint.payload.raw_bits())
    return Cat(iter(raw_layout))


class _LiteDRAMFIFOCtrl(Module):
    def __init__(self, base, depth):
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
            self.writable.eq(self.level != depth),
            self.readable.eq(self.level != 0)
        ]


class _LiteDRAMFIFOWriter(Module):
    def __init__(self, ctrl, layout, port):
        self.sink = sink = stream.Endpoint(layout)

        # # #

        writer = dma.LiteDRAMDMAWriter(port)
        self.submodules += writer

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(ctrl.writable & sink.valid,
                NextState("WRITE")
            )
        )
        fsm.act("WRITE",
            writer.sink.valid.eq(1),
            If(writer.sink.ready,
                ctrl.write.eq(1),
                sink.ready.eq(1),
                NextState("IDLE")
            )
        )
        self.comb += [
            writer.sink.address.eq(ctrl.write_address + ctrl.base//(port.dw//8)),
            writer.sink.data.eq(_raw_layout(sink))
        ]


class _LiteDRAMFIFOReader(Module):
    def __init__(self, ctrl, layout, port):
        self.source = source = stream.Endpoint(layout)

        # # #

        reader = dma.LiteDRAMDMAReader(port)
        self.submodules += reader

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(ctrl.readable,
                NextState("READ")
            )
        )
        fsm.act("READ",
            reader.sink.valid.eq(1),
            If(reader.sink.ready,
                ctrl.read.eq(1),
                NextState("IDLE")
            )
        )

        self.comb += [
            reader.sink.address.eq(ctrl.read_address + ctrl.base//(port.dw//8)),
            source.valid.eq(reader.source.valid),
            _raw_layout(source).eq(reader.source.data),
            reader.source.ready.eq(source.ready)
        ]


class LiteDRAMFIFO(Module):
    def __init__(self, layout, base, depth, write_port, read_port):
        self.submodules.ctrl = _LiteDRAMFIFOCtrl(base, depth)
        self.submodules.writer = _LiteDRAMFIFOWriter(self.ctrl, layout, write_port)
        self.submodules.reader = _LiteDRAMFIFOReader(self.ctrl, layout, read_port)
        self.sink, self.source = self.writer.sink, self.reader.source
