#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect import stream

from litedram.common import LiteDRAMNativePort
from litedram.frontend import dma

# Helpers ------------------------------------------------------------------------------------------

def _inc(signal, modulo):
    if modulo == 2**len(signal):
        return signal.eq(signal + 1)
    else:
        return If(signal == (modulo - 1),
            signal.eq(0)
        ).Else(
            signal.eq(signal + 1)
        )

# LiteDRAMFIFOCtrl ---------------------------------------------------------------------------------

class _LiteDRAMFIFOCtrl(Module):
    def __init__(self, base, depth):
        self.base  = base
        self.depth = depth
        self.level = Signal(max=depth+1)

        # # #

        # To write buffer
        self.writable      = Signal()
        self.write_address = Signal(max=depth)

        # From write buffer
        self.write = Signal()

        # To read buffer
        self.readable     = Signal()
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
            self.writable.eq(self.level < depth),
            self.readable.eq(self.level > 0)
        ]

# LiteDRAMFIFOWriter -------------------------------------------------------------------------------

class _LiteDRAMFIFOWriter(Module):
    def __init__(self, data_width, port, ctrl, fifo_depth=32):
        self.sink = sink = stream.Endpoint([("data", data_width)])

        # # #

        self.submodules.writer = writer = dma.LiteDRAMDMAWriter(port, fifo_depth=fifo_depth)
        self.comb += [
            writer.sink.valid.eq(sink.valid & ctrl.writable),
            writer.sink.address.eq(ctrl.base + ctrl.write_address),
            writer.sink.data.eq(sink.data),
            If(writer.sink.valid & writer.sink.ready,
                sink.ready.eq(1)
            ),
            If(port.wdata.valid & port.wdata.ready,
                ctrl.write.eq(1)
            ),
        ]

# LiteDRAMFIFOReader -------------------------------------------------------------------------------

class _LiteDRAMFIFOReader(Module):
    def __init__(self, data_width, port, ctrl, fifo_depth=32):
        self.source = source = stream.Endpoint([("data", data_width)])

        # # #

        self.submodules.reader = reader = dma.LiteDRAMDMAReader(port, fifo_depth=fifo_depth)
        self.comb += [
            reader.sink.valid.eq(ctrl.readable),
            reader.sink.address.eq(ctrl.base + ctrl.read_address),
            If(reader.sink.valid & reader.sink.ready,
                ctrl.read.eq(1)
            )
        ]
        self.comb += reader.source.connect(source)

# LiteDRAMFIFO -------------------------------------------------------------------------------------

class LiteDRAMFIFO(Module):
    """LiteDRAM frontend that allows to use DRAM as a FIFO"""
    def __init__(self, data_width, base, depth, write_port, read_port,
        writer_fifo_depth = 32,
        reader_fifo_depth = 32):
        assert isinstance(write_port, LiteDRAMNativePort)
        assert isinstance(read_port,  LiteDRAMNativePort)
        self.sink   = stream.Endpoint([("data", data_width)])
        self.source = stream.Endpoint([("data", data_width)])

        # # #

        self.submodules.ctrl   = _LiteDRAMFIFOCtrl(base, depth)
        self.submodules.writer = _LiteDRAMFIFOWriter(data_width, write_port, self.ctrl, writer_fifo_depth)
        self.submodules.reader = _LiteDRAMFIFOReader(data_width, read_port,  self.ctrl, reader_fifo_depth)
        self.comb += [
            self.sink.connect(self.writer.sink),
            self.reader.source.connect(self.source)
        ]
