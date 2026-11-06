#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect import stream

from litedram.common import *

# LiteDRAMNativePortCDC ----------------------------------------------------------------------------

class LiteDRAMNativePortCDC(Module):
    """LiteDRAM port Clock Domain Crossing

    Crosses a native port between two clock domains through asynchronous FIFOs.

    The controller side does not stall on rdata (read data is returned as soon as available), so
    reads are only accepted on port_from while the read data of all the reads in flight fits in
    the rdata FIFO: a slow port_from rdata consumer then stalls the commands instead of losing
    read data. rdata_depth also bounds the read throughput: a read stream only sustains one word
    per cycle when rdata_depth covers the read round-trip latency (in port_from cycles).
    """
    def __init__(self, port_from, port_to,
                 cmd_depth   = 8,
                 wdata_depth = 16,
                 rdata_depth = 32):
        assert port_from.address_width == port_to.address_width
        assert port_from.data_width    == port_to.data_width
        assert port_from.mode          == port_to.mode

        address_width = port_from.address_width
        data_width    = port_from.data_width
        mode          = port_from.mode

        # # #

        cmd_stall = Signal()

        cmd_cdc = stream.ClockDomainCrossing(
            layout  = [("we", 1), ("addr", address_width)],
            cd_from = port_from.clock_domain,
            cd_to   = port_to.clock_domain,
            depth   = cmd_depth,
            with_common_rst = False)
        self.submodules += cmd_cdc
        self.comb += [
            port_from.cmd.connect(cmd_cdc.sink, omit={"valid", "ready"}),
            cmd_cdc.sink.valid.eq(port_from.cmd.valid & ~cmd_stall),
            port_from.cmd.ready.eq(cmd_cdc.sink.ready & ~cmd_stall),
            cmd_cdc.source.connect(port_to.cmd),
        ]

        if mode in ["write", "both"]:
            wdata_cdc = stream.ClockDomainCrossing(
                layout  = [("data", data_width), ("we", data_width//8)],
                cd_from = port_from.clock_domain,
                cd_to   = port_to.clock_domain,
                depth   = wdata_depth,
                with_common_rst = False)
            self.submodules += wdata_cdc
            self.submodules += stream.Pipeline(port_from.wdata, wdata_cdc, port_to.wdata)

        if mode in ["read", "both"]:
            rdata_cdc = stream.ClockDomainCrossing(
                layout  = [("data", data_width)],
                cd_from = port_to.clock_domain,
                cd_to   = port_from.clock_domain,
                depth   = rdata_depth,
                with_common_rst = False)
            self.submodules += rdata_cdc
            self.submodules += stream.Pipeline(port_to.rdata, rdata_cdc, port_from.rdata)

            # Read credits (port_from clock domain): reads accepted minus read data delivered. Every
            # read returns one rdata word, so the reads in flight never exceed the rdata FIFO's depth.
            if port_from.clock_domain != port_to.clock_domain:
                rdata_inflight = Signal(max=rdata_depth + 1)
                rdata_cmd      = Signal()
                rdata_ack      = Signal()
                self.comb += [
                    rdata_cmd.eq(port_from.cmd.valid & port_from.cmd.ready & ~port_from.cmd.we),
                    rdata_ack.eq(port_from.rdata.valid & port_from.rdata.ready),
                    cmd_stall.eq(~port_from.cmd.we & (rdata_inflight == rdata_depth)),
                ]
                sync_from = getattr(self.sync, port_from.clock_domain)
                sync_from += [
                    If(rdata_cmd & ~rdata_ack,
                        rdata_inflight.eq(rdata_inflight + 1)
                    ).Elif(~rdata_cmd & rdata_ack,
                        rdata_inflight.eq(rdata_inflight - 1)
                    )
                ]

# LiteDRAMNativePortReorder ------------------------------------------------------------------------

class LiteDRAMNativePortReorder(Module):
    """Let a native port have commands in several banks at once.

    Without it, the crossbar locks a port on a bank until its commands are issued, which is what
    keeps the port's data in command order. Here, commands carry a tag to the bank machines and the
    data is kept in buffers so that banks can complete out of order:
    - Writes: the data is stored when pulled from the master, the cycle after the command is
      accepted (the native port contract), and sent to the controller from the tag it returns.
    - Reads: the data is stored at the tag returned by the controller and given back to the master
      in command order.

    The master sees the usual native port protocol, with up to depth commands in flight per
    direction. Commands of a bank keep their order, so accesses to a given address do too.
    """
    def __init__(self, port_from, port_to, depth):
        assert port_from.clock_domain == port_to.clock_domain
        assert port_from.data_width   == port_to.data_width
        assert depth >= 2 and (depth & (depth - 1)) == 0
        tag_width = log2_int(depth)
        port_to.cmd_tag   = Signal(tag_width)
        port_to.wdata_tag = Signal(tag_width)
        port_to.rdata_tag = Signal(tag_width)

        # # #

        data_width = port_from.data_width
        we_width   = data_width//8

        # Write buffer -----------------------------------------------------------------------------
        wr_mem   = Memory(data_width + we_width, depth)
        wr_write = wr_mem.get_port(write_capable=True)
        wr_read  = wr_mem.get_port(async_read=True)
        self.specials += wr_mem, wr_write, wr_read

        wr_tail    = Signal(tag_width) # Next slot given to a write command.
        wr_store   = Signal(tag_width) # Next slot to store the master's data in.
        wr_pending = Signal(tag_width + 1)
        wr_busy    = Array(Signal() for _ in range(depth))
        wr_accept  = Signal()
        wr_pull    = Signal()
        wr_done    = Signal()
        self.comb += [
            wr_pull.eq(wr_pending != 0),
            port_from.wdata.ready.eq(wr_pull),
            wr_write.adr.eq(wr_store),
            wr_write.dat_w.eq(Cat(port_from.wdata.data, port_from.wdata.we)),
            wr_write.we.eq(wr_pull),
            wr_read.adr.eq(port_to.wdata_tag),
            port_to.wdata.valid.eq(1),
            port_to.wdata.data.eq(wr_read.dat_r[:data_width]),
            port_to.wdata.we.eq(wr_read.dat_r[data_width:]),
            wr_done.eq(port_to.wdata.ready),
        ]
        self.sync += [
            If(wr_accept,
                wr_tail.eq(wr_tail + 1),
                wr_busy[wr_tail].eq(1),
            ),
            If(wr_done, wr_busy[port_to.wdata_tag].eq(0)),
            If(wr_pull, wr_store.eq(wr_store + 1)),
            wr_pending.eq(wr_pending + wr_accept - wr_pull),
        ]

        # Read buffer ------------------------------------------------------------------------------
        rd_mem   = Memory(data_width, depth)
        rd_write = rd_mem.get_port(write_capable=True)
        rd_read  = rd_mem.get_port(async_read=True)
        self.specials += rd_mem, rd_write, rd_read

        rd_tail   = Signal(tag_width) # Next slot given to a read command.
        rd_head   = Signal(tag_width) # Next slot to give back to the master.
        rd_level  = Signal(tag_width + 1)
        rd_valid  = Array(Signal() for _ in range(depth))
        rd_accept = Signal()
        rd_pop    = Signal()
        self.comb += [
            port_to.rdata.ready.eq(1),
            rd_write.adr.eq(port_to.rdata_tag),
            rd_write.dat_w.eq(port_to.rdata.data),
            rd_write.we.eq(port_to.rdata.valid),
            rd_read.adr.eq(rd_head),
            rd_pop.eq(rd_valid[rd_head]),
            port_from.rdata.valid.eq(rd_pop),
            port_from.rdata.data.eq(rd_read.dat_r),
        ]
        self.sync += [
            If(rd_accept, rd_tail.eq(rd_tail + 1)),
            If(rd_pop,
                rd_head.eq(rd_head + 1),
                rd_valid[rd_head].eq(0),
            ),
            If(port_to.rdata.valid, rd_valid[port_to.rdata_tag].eq(1)),
            rd_level.eq(rd_level + rd_accept - rd_pop),
        ]

        # Command ----------------------------------------------------------------------------------
        allowed = Signal()
        self.comb += [
            If(port_from.cmd.we,
                allowed.eq(~wr_busy[wr_tail]),
                port_to.cmd_tag.eq(wr_tail),
            ).Else(
                allowed.eq(rd_level != depth),
                port_to.cmd_tag.eq(rd_tail),
            ),
            port_to.cmd.valid.eq(port_from.cmd.valid & allowed),
            port_to.cmd.we.eq(port_from.cmd.we),
            port_to.cmd.addr.eq(port_from.cmd.addr),
            port_to.cmd.last.eq(port_from.cmd.last),
            port_from.cmd.ready.eq(port_to.cmd.ready & allowed),
            wr_accept.eq(port_to.cmd.valid & port_to.cmd.ready &  port_to.cmd.we),
            rd_accept.eq(port_to.cmd.valid & port_to.cmd.ready & ~port_to.cmd.we),
            port_to.flush.eq(port_from.flush),
            port_from.lock.eq(port_to.lock),
        ]

# LiteDRAMNativePortDownConverter ------------------------------------------------------------------

class LiteDRAMNativePortDownConverter(Module):
    """LiteDRAM port DownConverter

    This module reduces user port data width to fit controller data width.
    With N = port_from.data_width/port_to.data_width:
    - Address is adapted (multiplied by N + internal increments)
    - A write from the user is splitted and generates N writes to the
    controller.
    - A read from the user generates N reads to the controller and returned
      datas are regrouped in a single data presented to the user.
    """
    def __init__(self, port_from, port_to, reverse=False):
        assert port_from.clock_domain == port_to.clock_domain
        assert port_from.data_width    > port_to.data_width
        assert port_from.mode         == port_to.mode
        if port_from.data_width % port_to.data_width:
            raise ValueError("Ratio must be an int")

        # # #

        ratio = port_from.data_width//port_to.data_width
        mode  = port_from.mode

        cmd_count = Signal(max=ratio)
        cmd_addr  = Signal(len(port_from.cmd.addr))
        cmd_we    = Signal()

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            port_from.cmd.ready.eq(1),
            If(port_from.cmd.valid,
                NextValue(cmd_count, 0),
                NextValue(cmd_addr,  port_from.cmd.addr),
                NextValue(cmd_we,    port_from.cmd.we),
                NextState("CONVERT")
            )
        )
        fsm.act("CONVERT",
            port_to.cmd.valid.eq(1),
            port_to.cmd.we.eq(cmd_we),
            port_to.cmd.addr.eq(cmd_addr*ratio + cmd_count),
            If(port_to.cmd.ready,
                NextValue(cmd_count, cmd_count + 1),
                If(cmd_count == (ratio - 1),
                    NextState("IDLE")
                )
            )
        )

        if mode in ["write", "both"]:
            wdata_converter = stream.StrideConverter(
                description_from = port_from.wdata.description,
                description_to   = port_to.wdata.description,
                reverse          = reverse)
            self.submodules += wdata_converter
            self.submodules += stream.Pipeline(port_from.wdata, wdata_converter, port_to.wdata)

        if mode in ["read", "both"]:
            rdata_converter = stream.StrideConverter(
                description_from = port_to.rdata.description,
                description_to   = port_from.rdata.description,
                reverse          = reverse)
            self.submodules += rdata_converter
            self.submodules += stream.Pipeline(
                port_to.rdata, rdata_converter, port_from.rdata)

# LiteDRAMNativePortUpConverter --------------------------------------------------------------------

class LiteDRAMNativePortUpConverter(Module):
    """LiteDRAM port UpConverter

    This module increase user port data width to fit controller data width.
    With N = port_to.data_width/port_from.data_width:
    - Address is adapted (divided by N)
    - N read from user are regrouped in a single one to the controller
    (when possible, ie when consecutive and bursting)
    - N writes from user are regrouped in a single one to the controller
    (when possible, ie when consecutive and bursting)
    Incomplete writes/reads (i.e. with n < N) are handled automatically in the
    middle of a burst, but last command has to use cmd.last=1 if the last burst
    is not complete (not all N addresses have been used).
    Up to read_depth reads to the controller can be in flight (0: one at a time).
    """
    def __init__(self, port_from, port_to, reverse=False, read_depth=8):
        assert port_from.clock_domain == port_to.clock_domain
        assert port_from.data_width    < port_to.data_width
        assert port_from.mode         == port_to.mode
        if port_to.data_width % port_from.data_width:
            raise ValueError("Ratio must be an int")

        # # #

        ratio      = port_to.data_width//port_from.data_width
        mode       = port_from.mode
        chunk_bits = log2_int(ratio)

        # Command ----------------------------------------------------------------------------------

        # Store the subword request order for the current port_to command.
        # This preserves command order for reads and maps write data back to address lanes.
        # Reads: up to `read_depth` port_to commands are kept in flight (with a pass-through
        # buffer, each read has to return its data before the next one is accepted).
        # Writes: committed only when nothing is outstanding and issued once their data has
        # been assembled.
        cmd_count        = Signal(max=ratio + 1)
        cmd_order        = Signal(ratio*chunk_bits)
        cmd_chunks       = Signal(ratio)
        cmd_sel          = Signal(ratio)
        cmd_selected     = Signal()
        cmd_buffer       = stream.SyncFIFO([
            ("we",    1),
            ("count", len(cmd_count)),
            ("order", len(cmd_order)),
        ], read_depth)
        self.submodules += cmd_buffer
        # Store last received command.
        cmd_addr         = Signal.like(port_from.cmd.addr)
        cmd_we           = Signal()
        cmd_last         = Signal()
        # Indicates that we need to proceed to the next port_to command.
        next_cmd         = Signal()
        addr_changed     = Signal()
        # Signals that indicate that write/read conversion has finished.
        wdata_finished   = Signal()
        rdata_finished   = Signal()
        # Used to prevent reading old memory value if previous command has written the same address.
        read_lock        = Signal()
        read_unlocked    = Signal()
        rw_collision     = Signal()

        # Different order depending on read/write:
        # - read:  new -> cmd -> fill -> commit -> new
        # - write: new -> fill -> commit -> cmd -> new
        # For writes we have to send the command at the end to prevent situations when, during
        # a burst, LiteDRAM expects data (wdata_ready=1) but write converter is still converting.
        self.submodules.fsm = fsm = FSM()
        fsm.act("NEW",
            port_from.cmd.ready.eq(port_from.cmd.valid & ~read_lock),
            If(port_from.cmd.ready,
                NextValue(cmd_addr, port_from.cmd.addr),
                NextValue(cmd_we, port_from.cmd.we),
                NextValue(cmd_last, port_from.cmd.last),
                NextValue(cmd_count, 1),
                NextValue(cmd_order[:chunk_bits], port_from.cmd.addr[:chunk_bits]),
                NextValue(cmd_chunks, cmd_sel),
                If(port_from.cmd.we,
                    NextState("FILL"),
                ).Else(
                    NextState("CMD"),
                )
            )
        )
        fsm.act("CMD",
            port_to.cmd.valid.eq(1),
            port_to.cmd.we.eq(cmd_we),
            port_to.cmd.addr.eq(cmd_addr[chunk_bits:]),
            If(port_to.cmd.ready,
                If(cmd_we,
                    NextState("NEW")
                ).Else(
                    NextState("FILL")
                )
            )
        )
        cmd_order_cases = {}
        for i in range(ratio):
            cmd_order_cases[i] = NextValue(
                cmd_order[i*chunk_bits:(i + 1)*chunk_bits],
                port_from.cmd.addr[:chunk_bits])

        fsm.act("FILL",
            If(next_cmd,
                NextState("COMMIT")
            ).Else(  # Acknowledge incoming commands, while filling the request order.
                port_from.cmd.ready.eq(port_from.cmd.valid),
                If(port_from.cmd.valid,
                    NextValue(cmd_last, port_from.cmd.last),
                    NextValue(cmd_count, cmd_count + 1),
                    Case(cmd_count, cmd_order_cases),
                    NextValue(cmd_chunks, cmd_chunks | cmd_sel)
                )
            )
        )
        fsm.act("COMMIT",
            cmd_buffer.sink.we.eq(cmd_we),
            cmd_buffer.sink.count.eq(cmd_count),
            cmd_buffer.sink.order.eq(cmd_order),
            If(cmd_we,
                # Write: commit when nothing else is outstanding (head of the buffer), go to
                # CMD when its data has been assembled.
                cmd_buffer.sink.valid.eq(cmd_buffer.level == 0),
                If(wdata_finished,
                    NextState("CMD")
                )
            ).Else(
                cmd_buffer.sink.valid.eq(1),
                If(cmd_buffer.sink.ready,
                    NextState("NEW")
                )
            )
        )

        self.comb += [
            cmd_sel.eq(1 << port_from.cmd.addr[:log2_int(ratio)]),
            cmd_selected.eq((cmd_chunks & cmd_sel) != 0),
            cmd_buffer.source.ready.eq(wdata_finished | rdata_finished),
            addr_changed.eq(cmd_addr[chunk_bits:] != port_from.cmd.addr[chunk_bits:]),
            # Collision happens on write to read transition when address does not change.
            rw_collision.eq(cmd_we & (port_from.cmd.valid & ~port_from.cmd.we) & ~addr_changed),
            # Go to the next command if one of the following happens:
            #  - a valid command has a different port_to address.
            #  - a valid command has a different type.
            #  - a valid command requests a chunk that has already been selected.
            #  - we received all the `ratio` commands.
            #  - this is the last command in a sequence.
            #  - master requests a flush (even after the command has been sent).
            # The address/type/chunk comparisons are only made on valid commands: a master that
            # deasserts valid between the beats of a sequence (with don't-care addr/we) must not
            # make us flush a partial word.
            next_cmd.eq((port_from.cmd.valid & (addr_changed | (cmd_we != port_from.cmd.we) | cmd_selected))
                        | (cmd_count == ratio) | cmd_last | port_from.flush),
        ]

        self.sync += [
            # Block sending read command if we have just written to that address
            If(wdata_finished,
                read_lock.eq(0),
                read_unlocked.eq(1),
            ).Elif(rw_collision & ~port_to.cmd.valid & ~read_unlocked,
                read_lock.eq(1)
            ),
            If(port_from.cmd.valid & port_from.cmd.ready,
                read_unlocked.eq(0)
            )
        ]

        # Read Datapath ----------------------------------------------------------------------------

        if mode in ["read", "both"]:
            # Queue received data not to lose it when it comes too fast: one word per read in
            # flight (read_depth buffered + 1 issued and waiting to be buffered).
            rdata_fifo = stream.SyncFIFO(port_to.rdata.description, max(ratio - 1, read_depth + 1))
            self.submodules += rdata_fifo

            rdata_count = Signal(max=ratio)
            rdata_chunk = Signal(chunk_bits)
            rdata_valid = Signal()

            rdata_order_cases = {}
            rdata_mux_cases   = {}
            for i in range(ratio):
                n = ratio - 1 - i if reverse else i
                rdata_order_cases[i] = rdata_chunk.eq(
                    cmd_buffer.source.order[i*chunk_bits:(i + 1)*chunk_bits])
                rdata_mux_cases[i] = port_from.rdata.data.eq(
                    rdata_fifo.source.data[
                        n*port_from.data_width:(n + 1)*port_from.data_width])

            self.comb += [
                # port_to -> rdata_fifo -> order mux -> port_from
                port_to.rdata.connect(rdata_fifo.sink),
                Case(rdata_count, rdata_order_cases),
                Case(rdata_chunk, rdata_mux_cases),
                rdata_valid.eq(cmd_buffer.source.valid & ~cmd_buffer.source.we & rdata_fifo.source.valid),
                port_from.rdata.valid.eq(rdata_valid),
                rdata_fifo.source.ready.eq(rdata_finished),
                rdata_finished.eq(rdata_valid & port_from.rdata.ready
                                  & (rdata_count == (cmd_buffer.source.count - 1))),
            ]
            self.sync += [
                If(rdata_finished,
                    rdata_count.eq(0)
                ).Elif(rdata_valid & port_from.rdata.ready,
                    rdata_count.eq(rdata_count + 1)
                )
            ]

        # Write Datapath ---------------------------------------------------------------------------

        if mode in ["write", "both"]:
            # Queue write data not to miss it when the lower chunks haven't been requested.
            wdata_fifo    = stream.SyncFIFO(port_from.wdata.description, ratio - 1)
            wdata_buffer  = stream.SyncFIFO(port_to.wdata.description, 1)
            self.submodules += wdata_fifo, wdata_buffer

            wdata_count   = Signal(max=ratio)
            wdata_chunk   = Signal(chunk_bits)
            wdata_data    = Signal.like(port_to.wdata.data)
            wdata_we      = Signal(len(port_to.wdata.we)) # Not Signal.like: the payload is reset-less.
            wdata_pending = Signal()
            wdata_accept  = Signal()
            wdata_last    = Signal()

            wdata_order_cases = {}
            wdata_store_cases = {}
            for i in range(ratio):
                n = ratio - 1 - i if reverse else i
                wdata_order_cases[i] = wdata_chunk.eq(
                    cmd_buffer.source.order[i*chunk_bits:(i + 1)*chunk_bits])
                wdata_store_cases[i] = [
                    wdata_data[
                        n*port_from.data_width:(n + 1)*port_from.data_width
                    ].eq(wdata_fifo.source.data),
                    wdata_we[
                        n*port_from.wdata.we.nbits:(n + 1)*port_from.wdata.we.nbits
                    ].eq(wdata_fifo.source.we),
                ]

            self.comb += [
                # port_from -> wdata_fifo -> ordered wide buffer -> port_to
                port_from.wdata.connect(wdata_fifo.sink),
                wdata_buffer.source.connect(port_to.wdata),
                wdata_buffer.sink.valid.eq(wdata_pending),
                wdata_buffer.sink.data.eq(wdata_data),
                wdata_buffer.sink.we.eq(wdata_we),
                Case(wdata_count, wdata_order_cases),
                wdata_fifo.source.ready.eq(cmd_buffer.source.valid & cmd_buffer.source.we
                                           & ~wdata_pending),
                wdata_accept.eq(wdata_fifo.source.valid & wdata_fifo.source.ready),
                wdata_last.eq(wdata_count == (cmd_buffer.source.count - 1)),
                wdata_finished.eq(wdata_buffer.sink.valid & wdata_buffer.sink.ready),
            ]

            self.sync += [
                If(wdata_finished,
                    wdata_count.eq(0),
                    wdata_data.eq(0),
                    wdata_we.eq(0),
                    wdata_pending.eq(0),
                ).Elif(wdata_accept,
                    Case(wdata_chunk, wdata_store_cases),
                    If(wdata_last,
                        wdata_pending.eq(1)
                    ).Else(
                        wdata_count.eq(wdata_count + 1)
                    )
                )
            ]

# LiteDRAMNativePortConverter ----------------------------------------------------------------------

class LiteDRAMNativePortConverter(Module):
    def __init__(self, port_from, port_to, reverse=False):
        assert port_from.clock_domain == port_to.clock_domain
        assert port_from.mode         == port_to.mode

        # # #

        ratio = port_from.data_width/port_to.data_width

        if ratio > 1:
            # DownConverter
            self.submodules.converter = LiteDRAMNativePortDownConverter(port_from, port_to, reverse)
        elif ratio < 1:
            # UpConverter
            self.submodules.converter = LiteDRAMNativePortUpConverter(port_from, port_to, reverse)
        else:
            # Identity
            self.comb += port_from.connect(port_to)
