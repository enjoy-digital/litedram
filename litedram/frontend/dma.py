#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2018 John Sully <john@csquare.ca>
# Copyright (c) 2016 Tim 'mithro' Ansell <mithro@mithis.com>
# SPDX-License-Identifier: BSD-2-Clause

"""Direct Memory Access (DMA) reader and writer modules."""

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

    def __init__(self, port, fifo_depth=16, fifo_buffered=False):
        assert isinstance(port, (LiteDRAMNativePort, LiteDRAMAXIPort))
        self.port   = port
        self.sink   = sink   = stream.Endpoint([("address", port.address_width)])
        self.source = source = stream.Endpoint([("data", port.data_width)])

        # # #

        # Native / AXI selection
        is_native = isinstance(port, LiteDRAMNativePort)
        is_axi    = isinstance(port, LiteDRAMAXIPort)
        if is_native:
            (cmd, rdata) = port.cmd, port.rdata
        elif is_axi:
            (cmd, rdata) = port.ar, port.r
        else:
            raise NotImplementedError

        # Request issuance -------------------------------------------------------------------------
        request_enable = Signal()
        request_issued = Signal()

        if is_native:
            self.comb += cmd.we.eq(0)
        self.comb += [
            cmd.addr.eq(sink.address),
            cmd.valid.eq(sink.valid & request_enable),
            sink.ready.eq(cmd.ready & request_enable),
            request_issued.eq(cmd.valid & cmd.ready)
        ]

        # FIFO reservation level counter -----------------------------------------------------------
        # incremented when data is planned to be queued
        # decremented when data is dequeued
        data_dequeued = Signal()
        self.rsv_level = rsv_level = Signal(max=fifo_depth+1)
        self.sync += [
            If(request_issued,
                If(~data_dequeued, rsv_level.eq(self.rsv_level + 1))
            ).Elif(data_dequeued,
                rsv_level.eq(rsv_level - 1)
            )
        ]
        self.comb += request_enable.eq(rsv_level != fifo_depth)

        # FIFO -------------------------------------------------------------------------------------
        fifo = stream.SyncFIFO([("data", port.data_width)], fifo_depth, fifo_buffered)
        self.submodules += fifo

        self.comb += [
            rdata.connect(fifo.sink, omit={"id", "resp"}),
            fifo.source.connect(source),
            data_dequeued.eq(source.valid & source.ready)
        ]

    def add_csr(self):
        self._base   = CSRStorage(32)
        self._length = CSRStorage(32)
        self._start  = CSR()
        self._done   = CSRStatus()
        self._loop   = CSRStorage()

        # # #

        shift   = log2_int(self.port.data_width//8)
        base    = Signal(self.port.address_width)
        offset  = Signal(self.port.address_width)
        length  = Signal(self.port.address_width)
        self.comb += [
            base.eq(self._base.storage[shift:]),
            length.eq(self._length.storage[shift:]),
        ]

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            self._done.status.eq(1),
            If(self._start.re,
                NextValue(offset, 0),
                NextState("RUN"),
            )
        )
        fsm.act("RUN",
            self.sink.valid.eq(1),
            self.sink.address.eq(base + offset),
            If(self.sink.ready,
                NextValue(offset, offset + 1),
                If(offset == (length - 1),
                    If(self._loop.storage,
                        NextValue(offset, 0)
                    ).Else(
                        NextState("IDLE")
                    )
                )
            )
        )

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
    def __init__(self, port, fifo_depth=16, fifo_buffered=False):
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
        else:
            raise NotImplementedError

        # FIFO -------------------------------------------------------------------------------------
        fifo = stream.SyncFIFO([("data", port.data_width)], fifo_depth, fifo_buffered)
        self.submodules += fifo

        if is_native:
            self.comb += cmd.we.eq(1)
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

    def add_csr(self):
        self._sink = self.sink
        self.sink  = stream.Endpoint([("data", self.port.data_width)])

        self._base   = CSRStorage(32)
        self._length = CSRStorage(32)
        self._start  = CSR()
        self._done   = CSRStatus()
        self._loop   = CSRStorage()

        # # #

        shift   = log2_int(self.port.data_width//8)
        base    = Signal(self.port.address_width)
        offset  = Signal(self.port.address_width)
        length  = Signal(self.port.address_width)
        self.comb += [
            base.eq(self._base.storage[shift:]),
            length.eq(self._length.storage[shift:]),
        ]

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            self._done.status.eq(1),
            If(self._start.re,
                NextValue(offset, 0),
                NextState("RUN"),
            )
        )
        fsm.act("RUN",
            self._sink.valid.eq(self.sink.valid),
            self._sink.data.eq(self.sink.data),
            self._sink.address.eq(base + offset),
            self.sink.ready.eq(self._sink.ready),
            If(self.sink.valid & self.sink.ready,
                NextValue(offset, offset + 1),
                If(offset == (length - 1),
                    If(self._loop.storage,
                        NextValue(offset, 0)
                    ).Else(
                        NextState("IDLE")
                    )
                )
            )
        )
