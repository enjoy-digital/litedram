#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Ordered paired ports for opt-in DDR4 bank-group interleaving."""

from migen import *

from litex.soc.interconnect import stream

from litedram.common import LiteDRAMNativePort
from litedram.frontend.dma import LiteDRAMDMAWriter


class PairedPort(Module):
    """Join two 128-bit native masters into ordered 256-bit read/write words.

    Child addresses are 2*address and 2*address+1. The crossbar must use bank-
    group interleaving so these select opposite groups for all system masters.
    Writes support full-word masks only: an invalid mask sets sticky ``error``
    and discards that word before either child can issue it. After an error,
    new commands are blocked; data for already accepted addresses is consumed
    and discarded. Previously issued good child writes continue to drain.
    Reads reserve space before issuing; overflow or unsolicited data sets error.

    ``error`` clears only on reset. The caller must stop new traffic after an
    error and quiesce/reset the system, not reset this adapter in isolation.
    The caller must still supply data for accepted addresses before ``drained``
    can assert. A drained adapter with ``error`` set has aborted writes; it does
    not indicate successful completion of all accepted commands.
    ``drained`` covers queued commands/data accepted by native ports (or read
    responses consumed upstream), not analog DDR completion or write recovery.
    """
    def __init__(self, ports, mode, depth=64):
        if len(ports) != 2 or mode not in ("write", "read") or depth < 2:
            raise ValueError("PairedPort requires two read or write ports and depth >= 2")
        if not all(p.data_width == 128 and p.mode == mode and p.clock_domain == "sys"
                   and p.address_width == ports[0].address_width for p in ports):
            raise ValueError("PairedPort requires matching 128-bit sys-domain native ports")
        self.port = upstream = LiteDRAMNativePort(mode, ports[0].address_width-1, 256)
        self.error = Signal()
        self.drained = Signal()

        if mode == "write":
            # Reserve each half's data before presenting its command to a bank:
            # scheduled native writes cannot wait for data to become available.
            addresses = stream.SyncFIFO([("addr", upstream.address_width)], depth, buffered=True)
            self.submodules.addresses = addresses
            self.comb += [
                upstream.cmd.connect(addresses.sink, keep={"addr", "last"}),
                addresses.sink.valid.eq(upstream.cmd.valid & ~self.error),
                upstream.cmd.ready.eq(addresses.sink.ready & ~self.error)]
            reject = Signal()
            self.comb += reject.eq(self.error | (upstream.wdata.we != 0xffffffff))
            sent = Signal(2)
            transfers = []
            writers = []
            command_queues = []
            for group, port in enumerate(ports):
                queued = LiteDRAMNativePort("write", port.address_width, 128)
                commands = stream.SyncFIFO(port.cmd.description, 4, buffered=True)
                setattr(self.submodules, "write_commands" + str(group), commands)
                command_queues.append(commands)
                self.comb += [
                    queued.cmd.connect(commands.sink),
                    commands.source.connect(port.cmd),
                    queued.wdata.connect(port.wdata)]
                writer = LiteDRAMDMAWriter(queued, depth, fifo_buffered=True)
                setattr(self.submodules, "writer" + str(group), writer)
                writers.append(writer)
                transfer = Signal()
                transfers.append(transfer)
                self.comb += [
                    writer.sink.valid.eq(upstream.wdata.valid & addresses.source.valid &
                        ~sent[group] & ~reject),
                    writer.sink.address.eq((addresses.source.addr << 1) | group),
                    writer.sink.data.eq(upstream.wdata.data[128*group:128*(group+1)]),
                    writer.sink.last.eq(addresses.source.last),
                    transfer.eq(writer.sink.valid & writer.sink.ready)]
            self.sync += If(upstream.wdata.valid & upstream.wdata.ready &
                    (upstream.wdata.we != 0xffffffff),
                self.error.eq(1))
            self.comb += [
                upstream.wdata.ready.eq(addresses.source.valid &
                    (reject | ((sent[0] | transfers[0]) & (sent[1] | transfers[1])))),
                addresses.source.ready.eq(upstream.wdata.valid & upstream.wdata.ready),
                self.drained.eq(~addresses.source.valid &
                    (writers[0].fifo.level == 0) & (writers[1].fifo.level == 0) &
                    (command_queues[0].level == 0) & (command_queues[1].level == 0))]
            self.sync += If(upstream.wdata.valid & upstream.wdata.ready,
                sent.eq(0)
            ).Else(sent.eq(sent | Cat(transfers)))
            return

        sent = Signal(2)
        accepted = [Signal() for _ in ports]
        credit = [Signal(max=depth+1) for _ in ports]
        joined = Signal()
        self.comb += [
            self.drained.eq((credit[0] == 0) & (credit[1] == 0) & (sent == 0)),
            upstream.cmd.ready.eq((sent[0] | accepted[0]) & (sent[1] | accepted[1]))]
        self.sync += If(upstream.cmd.valid & upstream.cmd.ready,
            sent.eq(0)
        ).Else(sent.eq(sent | Cat(accepted)))
        queues = []
        for group, port in enumerate(ports):
            self.comb += [
                port.cmd.valid.eq(upstream.cmd.valid & ~sent[group] & (credit[group] < depth)),
                port.cmd.addr.eq((upstream.cmd.addr << 1) | group),
                port.cmd.we.eq(0),
                port.cmd.last.eq(upstream.cmd.last),
                accepted[group].eq(port.cmd.valid & port.cmd.ready)]
            self.sync += credit[group].eq(credit[group] + accepted[group] - joined)
            queue = stream.SyncFIFO([("data", 128)], depth, buffered=True)
            setattr(self.submodules, "read_queue" + str(group), queue)
            queues.append(queue)
            # Native read returns cannot be backpressured. Credits include
            # responses still in flight as well as data already in this FIFO.
            self.comb += [
                port.rdata.ready.eq(1),
                queue.sink.valid.eq(port.rdata.valid),
                queue.sink.data.eq(port.rdata.data)]
            outstanding = Signal(max=depth+1)
            self.sync += [
                If(accepted[group] & ~port.rdata.valid, outstanding.eq(outstanding + 1)),
                If(port.rdata.valid & ~accepted[group] & (outstanding != 0),
                    outstanding.eq(outstanding - 1)),
                If(port.rdata.valid & (~queue.sink.ready |
                        ((outstanding == 0) & ~accepted[group])), self.error.eq(1))]
        self.comb += [
            upstream.rdata.valid.eq(queues[0].source.valid & queues[1].source.valid),
            upstream.rdata.data.eq(Cat(queue.source.data for queue in queues)),
            joined.eq(upstream.rdata.valid & upstream.rdata.ready)]
        self.comb += [queue.source.ready.eq(joined) for queue in queues]
