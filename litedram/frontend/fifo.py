# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2019 Pierre-Olivier Vauboin <po@lambdaconcept>
# License: BSD

from litex.gen import *

from litex.soc.interconnect import stream

from litedram.frontend import dma
from litedram.common import LiteDRAMNativePort


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
        self.pending = Signal()

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
            self.writable.eq(self.level < write_threshold),
            self.readable.eq(self.level > read_threshold)
        ]


class _LiteDRAMFIFOLatch(Module):
    """When enabled, source is valid only if at least depth data have been
    accumulated into the FIFO.
    """
    def __init__(self, dw, depth):
        self.sink = sink = stream.Endpoint([("data", dw)])
        self.source = source = stream.Endpoint([("data", dw)])

        # # #

        # from FIFO router
        self.en = Signal()

        # to FIFO router
        self.writable = Signal()

        # # #

        opened = Signal()
        counter = Signal(max=depth)

        self.submodules.fifo = fifo = stream.SyncFIFO([("data", dw)], 2*depth)

        self.comb += [
            self.writable.eq(fifo.level != fifo.depth),
        ]

        self.comb += [
            If(~self.en,
                sink.connect(fifo.sink),
                fifo.source.connect(source),
            ).Else(
                sink.connect(fifo.sink),
                # output to source only when the latch is opened
                If(opened,
                    fifo.source.connect(source),
                ),
            )
        ]

        self.sync += [
            If(self.en & opened,
                If(fifo.source.valid & fifo.source.ready,
                    If(counter < depth-1,
                        counter.eq(counter + 1),
                    ).Else(
                        counter.eq(0),
                        # not enough data, close the latch
                        If(fifo.level-1 < depth,
                            opened.eq(0),
                        ),
                    ),
                )
            ).Else(
                # enough data accumulated, open the latch
                If(fifo.level >= depth,
                    opened.eq(1),
                ),
            ),
        ]


class _LiteDRAMFIFORouter(Module):
    def __init__(self, dw, depth, ctrl):
        layout = [("data", dw)]
        self.sink0 = sink0 = stream.Endpoint(layout)
        self.source0 = source0 = stream.Endpoint(layout)
        self.sink1 = sink1 = stream.Endpoint(layout)
        self.source1 = source1 = stream.Endpoint(layout)

        # # #

        self.submodules.latch = latch = _LiteDRAMFIFOLatch(dw, depth)

        self.submodules.fsm = fsm = FSM()
        fsm.act("BYPASS",
            latch.en.eq(0),
            sink0.connect(latch.sink),
            latch.source.connect(source0),

            If(~latch.writable,
                NextState("DRAM"),
            ),
        )

        fsm.act("DRAM",
            latch.en.eq(1),
            sink0.connect(latch.sink),

            source1.data.eq(latch.source.data),
            source1.valid.eq(latch.source.valid),
            latch.source.ready.eq(source1.ready),

            sink1.connect(source0),

            If(~latch.source.valid & ~ctrl.pending & ~ctrl.readable,
                NextState("BYPASS"),
            ),
        )


class _LiteDRAMFIFOWriter(Module):
    def __init__(self, port, ctrl):
        assert isinstance(port, LiteDRAMNativePort)
        self.sink = sink = stream.Endpoint([("data", port.data_width)])

        # # #

        (cmd, wdata) = port.cmd, port.wdata

        sendcmd = Signal(reset=1)
        senddata = Signal()

        self.comb += [
            ctrl.pending.eq(sink.valid),
        ]

        self.comb += [
            cmd.we.eq(1),
            cmd.addr.eq(ctrl.base + ctrl.write_address),
            cmd.valid.eq(sink.valid & ctrl.writable & sendcmd),
        ]
        self.sync += [
            If(cmd.valid & cmd.ready,
                sendcmd.eq(0),
                senddata.eq(1),
            ),
        ]

        self.comb += [
            wdata.we.eq(2**(port.data_width//8)-1),
            wdata.data.eq(sink.data),
            wdata.valid.eq(sink.valid & ctrl.writable & senddata),
        ]
        self.sync += [
            If(wdata.valid & wdata.ready,
                sendcmd.eq(1),
                senddata.eq(0),
            ),
        ]

        self.comb += [
            If(wdata.valid & wdata.ready,
                ctrl.write.eq(1),
                sink.ready.eq(1),
            ),
        ]


class _LiteDRAMFIFOReader(Module):
    def __init__(self, port, ctrl):
        assert isinstance(port, LiteDRAMNativePort)
        self.submodules.fifo = fifo = stream.SyncFIFO([("data", port.data_width)], 2)
        self.source = source = fifo.source

        # # #

        (cmd, rdata) = port.cmd, port.rdata

        sendcmd = Signal(reset=1)

        self.comb += [
            cmd.we.eq(0),
            cmd.addr.eq(ctrl.base + ctrl.read_address),
            cmd.valid.eq(ctrl.readable & sendcmd),
        ]
        self.sync += [
            If(cmd.valid & cmd.ready,
                sendcmd.eq(0),
            ),
        ]

        self.comb += [
            rdata.connect(fifo.sink, omit={"id", "resp"}),
            If(source.valid & source.ready,
                ctrl.read.eq(1),
            ),
        ]
        self.sync += [
            If(source.valid & source.ready,
                sendcmd.eq(1),
            ),
        ]


class _FLInterface(Record):
    def __init__(self, description):
        layout = [("payload", description.payload_layout),
                  ("param", description.param_layout),
                  ("first", 1),
                  ("last", 1)]
        # padding align to next power of two
        length = layout_len(layout)
        power = 2**bits_for(length)
        padding = power - length
        layout += [("padding", padding)]

        Record.__init__(self, layout)


class _FLPack(Module):
    def __init__(self, layout_from):
        self.sink = sink = stream.Endpoint(layout_from)
        din = _FLInterface(sink.description)
        self.source = source = stream.Endpoint([("data", len(din))])

        # # #

        self.comb += [
            din.payload.eq(sink.payload),
            din.param.eq(sink.param),
            din.first.eq(sink.first),
            din.last.eq(sink.last),

            source.valid.eq(sink.valid),
            source.data.eq(din.raw_bits()),
            sink.ready.eq(source.ready),
        ]


class _FLUnpack(Module):
    def __init__(self, layout_to):
        self.source = source = stream.Endpoint(layout_to)
        dout = _FLInterface(source.description)
        self.sink = sink = stream.Endpoint([("data", len(dout))])

        # # #

        self.comb += [
            source.payload.eq(dout.payload),
            source.param.eq(dout.param),
            source.first.eq(dout.first),
            source.last.eq(dout.last),

            source.valid.eq(sink.valid),
            dout.raw_bits().eq(sink.data),
            sink.ready.eq(source.ready),
        ]

class LiteDRAMFIFO(Module):
    def __init__(self, layout, depth, base, crossbar,
        read_threshold=None, write_threshold=None,
        preserve_first_last=True):

        self.sink = sink = stream.Endpoint(layout)
        self.source = source = stream.Endpoint(layout)

        # # #

        # preserve first and last fields
        if preserve_first_last:
            self.submodules.pack = _FLPack(layout)
            self.submodules.unpack = _FLUnpack(layout)

            self.comb += [
                sink.connect(self.pack.sink),
                self.unpack.source.connect(source),
            ]

            fifo_in = self.pack.source
            fifo_out = self.unpack.sink
        else:
            fifo_in = sink
            fifo_out = source

        native_width = crossbar.controller.data_width
        dw = len(fifo_in.payload)
        if dw <= native_width:
            if native_width % dw:
                raise ValueError("Ratio must be an int")
            ctrl_ratio = native_width // dw
            ctrl_depth = ((depth-1) // ctrl_ratio) + 1
            fifo_depth = ctrl_ratio
        else:
            raise NotImplementedError("Only upconverter support for now")

        # use native controller width
        read_port = crossbar.get_port(mode="read")
        write_port = crossbar.get_port(mode="write")

        if read_threshold is None:
            read_threshold = 0
        if write_threshold is None:
            write_threshold = ctrl_depth

        # ctrl counts blocks in native width
        self.submodules.ctrl = _LiteDRAMFIFOCtrl(base, ctrl_depth, read_threshold, write_threshold)
        self.submodules.writer = _LiteDRAMFIFOWriter(write_port, self.ctrl)
        self.submodules.reader = _LiteDRAMFIFOReader(read_port, self.ctrl)

        # router chooses bypass or dram
        self.submodules.router = _LiteDRAMFIFORouter(dw, fifo_depth, self.ctrl)
        self.submodules.conv_w = stream.StrideConverter(fifo_in.description, self.writer.sink.description)
        self.submodules.conv_r = stream.StrideConverter(self.reader.source.description, fifo_out.description)

        self.comb += [
            # bypass
            fifo_in.connect(self.router.sink0),
            self.router.source0.connect(fifo_out),

            # dram
            self.router.source1.connect(self.conv_w.sink),
            self.conv_w.source.connect(self.writer.sink),
            self.reader.source.connect(self.conv_r.sink),
            self.conv_r.source.connect(self.router.sink1),
        ]
