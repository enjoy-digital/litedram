#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2021 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2018 John Sully <john@csquare.ca>
# Copyright (c) 2016 Tim 'mithro' Ansell <mithro@mithis.com>
# SPDX-License-Identifier: BSD-2-Clause

"""Direct Memory Access (DMA) reader and writer modules."""

from math import log2

from migen import *

from litex.soc.interconnect.csr import *
from litex.soc.interconnect import stream

from litedram.common import LiteDRAMNativePort
from litedram.frontend.axi import LiteDRAMAXIPort

# LiteDRAMDMAReader --------------------------------------------------------------------------------

class LiteDRAMDMAReader(Module, AutoCSR):
    """Read data from DRAM memory.

    For every address written to the sink, one DRAM word will be produced on
    the source.

    Parameters
    ----------
    port : port
        Port on the DRAM memory controller to read from (Native or AXI).

    fifo_depth : int
        How many request results the output FIFO can contain (and thus how many
        read requests can be outstanding at once).

    fifo_buffered : bool
        Implement FIFO in Block Ram.

    Attributes
    ----------
    sink : Record("address")
        Sink for DRAM addresses to be read.

    source : Record("data")
        Source for DRAM word results from reading.

    rsv_level: Signal()
        FIFO reservation level counter
    """

    def __init__(self, port, fifo_depth=16, fifo_buffered=False, with_csr=False):
        assert isinstance(port, (LiteDRAMNativePort, LiteDRAMAXIPort))
        self.port   = port
        self.enable = enable = Signal(reset=1)
        self.sink   = sink   = stream.Endpoint([("address", port.address_width)])
        self.source = source = stream.Endpoint([("data", port.data_width)])

        # # #

        # Native / AXI selection -------------------------------------------------------------------
        is_native = isinstance(port, LiteDRAMNativePort)
        is_axi    = isinstance(port, LiteDRAMAXIPort)
        if is_native:
            (cmd, rdata) = port.cmd, port.rdata
        elif is_axi:
            (cmd, rdata) = port.ar, port.r
        else:
            raise NotImplementedError

        # Reservation FIFO -------------------------------------------------------------------------

        res_fifo = stream.SyncFIFO([("dummy", 1)], fifo_depth)
        self.submodules += res_fifo

        # Request issuance -------------------------------------------------------------------------

        if is_native:
            self.comb += cmd.we.eq(0)
        if is_axi:
            self.comb += cmd.size.eq(int(log2(port.data_width//8)))
        self.comb += [
            cmd.addr.eq(sink.address),
            cmd.last.eq(sink.last),
            cmd.valid.eq(enable & sink.valid & res_fifo.sink.ready),
            sink.ready.eq(enable & cmd.ready & res_fifo.sink.ready),
        ]
        self.comb += [
            res_fifo.sink.valid.eq(cmd.valid & cmd.ready),
            res_fifo.sink.last.eq(cmd.last),
        ]

        # FIFO -------------------------------------------------------------------------------------
        fifo = stream.SyncFIFO([("data", port.data_width)], fifo_depth, fifo_buffered)
        self.submodules += fifo

        self.comb += [
            rdata.connect(fifo.sink, omit={"id", "resp", "dest", "user"}),
            fifo.source.connect(source, omit={"valid", "ready", "last"}),
            If(res_fifo.source.valid,
                source.valid.eq(fifo.source.valid),
                source.last.eq(res_fifo.source.last),
            ),
            fifo.source.ready.eq(source.ready | ~enable), # Flush FIFO/Reservation counter when disabled.
        ]
        self.comb += res_fifo.source.ready.eq(fifo.source.valid & fifo.source.ready)

        if with_csr:
            self.add_csr()

    def add_csr(self, default_base=0, default_length=0, default_enable=0, default_loop=0):
        self._base   = CSRStorage(32, reset=default_base)
        self._length = CSRStorage(32, reset=default_length)
        self._enable = CSRStorage(reset=default_enable)
        self._done   = CSRStatus()
        self._loop   = CSRStorage(reset=default_loop)
        self._offset = CSRStatus(32)

        # # #

        shift  = log2_int(self.port.data_width//8)
        base   = Signal(self.port.address_width)
        offset = Signal(self.port.address_width)
        length = Signal(self.port.address_width)
        self.comb += self.enable.eq(self._enable.storage)
        self.comb += base.eq(self._base.storage[shift:])
        self.comb += length.eq(self._length.storage[shift:])

        self.comb += self._offset.status.eq(offset)

        fsm = FSM(reset_state="IDLE")
        fsm = ResetInserter()(fsm)
        self.submodules.fsm = fsm
        self.comb += fsm.reset.eq(~self._enable.storage)
        fsm.act("IDLE",
            NextValue(offset, 0),
            NextState("RUN"),
        )
        fsm.act("RUN",
            self.sink.valid.eq(1),
            self.sink.last.eq(offset == (length - 1)),
            self.sink.address.eq(base + offset),
            If(self.sink.ready,
                NextValue(offset, offset + 1),
                If(self.sink.last,
                    If(self._loop.storage,
                        NextValue(offset, 0)
                    ).Else(
                        NextState("DONE")
                    )
                )
            )
        )
        fsm.act("DONE", self._done.status.eq(1))

# LiteDRAMDMAWriter --------------------------------------------------------------------------------

class LiteDRAMDMAWriter(Module, AutoCSR):
    """Write data to DRAM memory.

    Parameters
    ----------
    port : port
        Port on the DRAM memory controller to write to (Native or AXI).

    fifo_depth : int
        How many requests the input FIFO can contain (and thus how many write
        requests can be outstanding at once).

    fifo_buffered : bool
        Implement FIFO in Block Ram.

    Attributes
    ----------
    sink : Record("address", "data")
        Sink for DRAM addresses and DRAM data word to be written too.
    """
    def __init__(self, port, fifo_depth=16, fifo_buffered=False, with_csr=False):
        assert isinstance(port, (LiteDRAMNativePort, LiteDRAMAXIPort))
        self.port = port
        self.sink = sink = stream.Endpoint([("address", port.address_width),
                                            ("data", port.data_width)])

        # # #

        # Native / AXI selection -------------------------------------------------------------------
        is_native = isinstance(port, LiteDRAMNativePort)
        is_axi    = isinstance(port, LiteDRAMAXIPort)
        if is_native:
            (cmd, wdata) = port.cmd, port.wdata
        elif is_axi:
            (cmd, wdata) = port.aw, port.w
            self.comb += port.b.ready.eq(1) # Always ack write responses.
        else:
            raise NotImplementedError

        # FIFO -------------------------------------------------------------------------------------
        self.submodules.fifo = fifo = stream.SyncFIFO([("data", port.data_width)], fifo_depth, fifo_buffered)

        if is_native:
            self.comb += cmd.we.eq(1)
        if is_axi:
            self.comb += cmd.size.eq(int(log2(port.data_width//8)))
        self.comb += [
            cmd.addr.eq(sink.address),
            cmd.valid.eq(fifo.sink.ready & sink.valid),
            sink.ready.eq(fifo.sink.ready & cmd.ready),
            fifo.sink.valid.eq(sink.valid & cmd.ready),
            fifo.sink.data.eq(sink.data)
        ]

        if is_native:
            self.comb += wdata.we.eq(2**(port.data_width//8)-1)
        if is_axi:
            self.comb += wdata.strb.eq(2**(port.data_width//8)-1)
        self.comb += [
            wdata.valid.eq(fifo.source.valid),
            fifo.source.ready.eq(wdata.ready),
            wdata.data.eq(fifo.source.data)
        ]

        if with_csr:
            self.add_csr()

    def add_csr(self, default_base=0, default_length=0, default_enable=0, default_loop=0):
        self._sink = self.sink
        self.sink  = stream.Endpoint([("data", self.port.data_width)])

        self._base   = CSRStorage(32, reset=default_base)
        self._length = CSRStorage(32, reset=default_length)
        self._enable = CSRStorage(reset=default_enable)
        self._done   = CSRStatus()
        self._loop   = CSRStorage(reset=default_loop)
        self._offset = CSRStatus(32)

        # # #

        shift  = log2_int(self.port.data_width//8)
        base   = Signal(self.port.address_width)
        offset = Signal(self.port.address_width)
        length = Signal(self.port.address_width)
        self.comb += base.eq(self._base.storage[shift:])
        self.comb += length.eq(self._length.storage[shift:])

        self.comb += self._offset.status.eq(offset)

        fsm = FSM(reset_state="IDLE")
        fsm = ResetInserter()(fsm)
        self.submodules.fsm = fsm
        self.comb += fsm.reset.eq(~self._enable.storage)
        fsm.act("IDLE",
            self.sink.ready.eq(1),
            NextValue(offset, 0),
            NextState("RUN"),
        )
        fsm.act("RUN",
            self._sink.valid.eq(self.sink.valid),
            self._sink.last.eq(offset == (length - 1)),
            self._sink.address.eq(base + offset),
            self._sink.data.eq(self.sink.data),
            self.sink.ready.eq(self._sink.ready),
            If(self.sink.valid & self.sink.ready,
                NextValue(offset, offset + 1),
                If(self._sink.last,
                    If(self._loop.storage,
                        NextValue(offset, 0)
                    ).Else(
                        NextState("DONE")
                    )
                )
            )
        )
        fsm.act("DONE", self._done.status.eq(1))
