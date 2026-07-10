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
    def __init__(self, port_from, port_to,
                 cmd_depth   = 4,
                 wdata_depth = 16,
                 rdata_depth = 16):
        assert port_from.address_width == port_to.address_width
        assert port_from.data_width    == port_to.data_width
        assert port_from.mode          == port_to.mode

        address_width = port_from.address_width
        data_width    = port_from.data_width
        mode          = port_from.mode

        # # #

        cmd_cdc = stream.ClockDomainCrossing(
            layout  = [("we", 1), ("addr", address_width)],
            cd_from = port_from.clock_domain,
            cd_to   = port_to.clock_domain,
            depth   = cmd_depth,
            with_common_rst = False)
        self.submodules += cmd_cdc
        self.submodules += stream.Pipeline(port_from.cmd, cmd_cdc, port_to.cmd)

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
    """
    def __init__(self, port_from, port_to, reverse=False):
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
        cmd_count        = Signal(max=ratio + 1)
        cmd_order        = Signal(ratio*chunk_bits)
        cmd_chunks       = Signal(ratio)
        cmd_sel          = Signal(ratio)
        cmd_selected     = Signal()
        cmd_buffer       = stream.SyncFIFO([
            ("we",    1),
            ("count", len(cmd_count)),
            ("order", len(cmd_order)),
        ], 0)
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
                NextValue(cmd_last, port_from.cmd.last),
                If(port_from.cmd.valid,
                    NextValue(cmd_count, cmd_count + 1),
                    Case(cmd_count, cmd_order_cases),
                    NextValue(cmd_chunks, cmd_chunks | cmd_sel)
                )
            )
        )
        fsm.act("COMMIT",
            cmd_buffer.sink.valid.eq(1),
            cmd_buffer.sink.we.eq(cmd_we),
            cmd_buffer.sink.count.eq(cmd_count),
            cmd_buffer.sink.order.eq(cmd_order),
            If(cmd_buffer.sink.ready,
                If(cmd_we,
                    NextState("CMD")
                ).Else(
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
            #  - port_to address changes.
            #  - cmd type changes.
            #  - the requested chunk has already been selected.
            #  - we received all the `ratio` commands.
            #  - this is the last command in a sequence.
            #  - master requests a flush (even after the command has been sent).
            next_cmd.eq(addr_changed | (cmd_we != port_from.cmd.we)
                        | (port_from.cmd.valid & cmd_selected)
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
            # Queue received data not to lose it when it comes too fast.
            rdata_fifo = stream.SyncFIFO(port_to.rdata.description, ratio - 1)
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
            wdata_we      = Signal.like(port_to.wdata.we)
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
