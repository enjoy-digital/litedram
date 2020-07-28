# This file is Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

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

        address_width     = port_from.address_width
        data_width        = port_from.data_width
        mode              = port_from.mode
        clock_domain_from = port_from.clock_domain
        clock_domain_to   = port_to.clock_domain

        # # #

        cmd_fifo = stream.AsyncFIFO(
            [("we", 1), ("addr", address_width)], cmd_depth)
        cmd_fifo = ClockDomainsRenamer(
            {"write": clock_domain_from,
             "read":  clock_domain_to})(cmd_fifo)
        self.submodules += cmd_fifo
        self.submodules += stream.Pipeline(
            port_from.cmd, cmd_fifo, port_to.cmd)

        if mode == "write" or mode == "both":
            wdata_fifo = stream.AsyncFIFO(
                [("data", data_width), ("we", data_width//8)], wdata_depth)
            wdata_fifo = ClockDomainsRenamer(
                {"write": clock_domain_from,
                 "read":  clock_domain_to})(wdata_fifo)
            self.submodules += wdata_fifo
            self.submodules += stream.Pipeline(
                port_from.wdata, wdata_fifo, port_to.wdata)

        if mode == "read" or mode == "both":
            rdata_fifo = stream.AsyncFIFO([("data", data_width)], rdata_depth)
            rdata_fifo = ClockDomainsRenamer(
                {"write": clock_domain_to,
                 "read":  clock_domain_from})(rdata_fifo)
            self.submodules += rdata_fifo
            self.submodules += stream.Pipeline(
                port_to.rdata, rdata_fifo, port_from.rdata)

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

        counter       = Signal(max=ratio)
        counter_reset = Signal()
        counter_ce    = Signal()
        self.sync += \
            If(counter_reset,
                counter.eq(0)
            ).Elif(counter_ce,
                counter.eq(counter + 1)
            )

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            counter_reset.eq(1),
            If(port_from.cmd.valid,
                NextState("CONVERT")
            )
        )
        fsm.act("CONVERT",
            port_to.cmd.valid.eq(1),
            port_to.cmd.we.eq(port_from.cmd.we),
            port_to.cmd.addr.eq(port_from.cmd.addr*ratio + counter),
            If(port_to.cmd.ready,
                counter_ce.eq(1),
                If(counter == ratio - 1,
                    port_from.cmd.ready.eq(1),
                    NextState("IDLE")
                )
            )
        )

        if mode == "write" or mode == "both":
            wdata_converter = stream.StrideConverter(
                port_from.wdata.description,
                port_to.wdata.description,
                reverse=reverse)
            self.submodules += wdata_converter
            self.submodules += stream.Pipeline(
                port_from.wdata, wdata_converter, port_to.wdata)

        if mode == "read" or mode == "both":
            rdata_converter = stream.StrideConverter(
                port_to.rdata.description,
                port_from.rdata.description,
                reverse=reverse)
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

        ratio = port_to.data_width//port_from.data_width
        mode  = port_from.mode

        # Command ----------------------------------------------------------------------------------

        # defines cmd type and the chunks that have been requested for the current port_to command
        sel              = Signal(ratio)
        cmd_buffer       = stream.SyncFIFO([("sel", ratio), ("we", 1)], 0)
        self.submodules += cmd_buffer
        # store last received command
        cmd_addr         = Signal.like(port_from.cmd.addr)
        cmd_we           = Signal()
        cmd_last         = Signal()
        # indicates that we need to proceed to the next port_to command
        next_cmd         = Signal()
        addr_changed     = Signal()
        # signals that indicate that write/read convertion has finished
        wdata_finished   = Signal()
        rdata_finished   = Signal()
        # used to prevent reading old memory value if previous command has written the same address
        read_lock        = Signal()
        read_unlocked    = Signal()
        rw_collision     = Signal()

        # different order depending on read/write:
        # read:  new -> cmd -> fill -> commit -> new
        # write: new -> fill -> commit -> cmd -> new
        # for writes we have to send the command at the end to prevent situations when, during
        # a burst, LiteDRAM expects data (wdata_ready=1) but write converter is still converting
        self.submodules.fsm = fsm = FSM()
        fsm.act("NEW",
            port_from.cmd.ready.eq(port_from.cmd.valid & ~read_lock),
            If(port_from.cmd.ready,
                NextValue(cmd_addr, port_from.cmd.addr),
                NextValue(cmd_we, port_from.cmd.we),
                NextValue(cmd_last, port_from.cmd.last),
                NextValue(sel, 1 << port_from.cmd.addr[:log2_int(ratio)]),
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
            port_to.cmd.addr.eq(cmd_addr[log2_int(ratio):]),
            If(port_to.cmd.ready,
                If(cmd_we,
                    NextState("NEW")
                ).Else(
                    NextState("FILL")
                )
            )
        )
        fsm.act("FILL",
            If(next_cmd,
                NextState("COMMIT")
            ).Else(  # acknowledge incomming commands, while filling `sel`
                port_from.cmd.ready.eq(port_from.cmd.valid),
                NextValue(cmd_last, port_from.cmd.last),
                NextValue(sel, sel | 1 << port_from.cmd.addr[:log2_int(ratio)]),
            )
        )
        fsm.act("COMMIT",
            cmd_buffer.sink.valid.eq(1),
            cmd_buffer.sink.sel.eq(sel),
            cmd_buffer.sink.we.eq(cmd_we),
            If(cmd_buffer.sink.ready,
                If(cmd_we,
                    NextState("CMD")
                ).Else(
                    NextState("NEW")
                )
            )
        )

        self.comb += [
            cmd_buffer.source.ready.eq(wdata_finished | rdata_finished),
            addr_changed.eq(cmd_addr[log2_int(ratio):] != port_from.cmd.addr[log2_int(ratio):]),
            # collision happens on write to read transition when address does not change
            rw_collision.eq(cmd_we & (port_from.cmd.valid & ~port_from.cmd.we) & ~addr_changed),
            # go to the next command if one of the following happens:
            #  * port_to address changes
            #  * cmd type changes
            #  * we received all the `ratio` commands
            #  * this is the last command in a sequence
            #  * master requests a flush (even after the command has been sent)
            next_cmd.eq(addr_changed | (cmd_we != port_from.cmd.we) | (sel == 2**ratio - 1)
                        | cmd_last | port_from.flush),
        ]

        self.sync += [
            # block sending read command if we have just written to that address
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

        if mode == "read" or mode == "both":
            # queue received data not to loose it when it comes too fast
            rdata_fifo = stream.SyncFIFO(port_to.rdata.description, ratio - 1)
            rdata_converter = stream.StrideConverter(
                port_to.rdata.description,
                port_from.rdata.description,
                reverse=reverse)
            self.submodules +=  rdata_fifo, rdata_converter

            # shift register with a bitmask of current chunk
            rdata_chunk       = Signal(ratio, reset=1)
            rdata_chunk_valid = Signal()
            self.sync += \
                If(rdata_converter.source.valid &
                   rdata_converter.source.ready,
                    rdata_chunk.eq(Cat(rdata_chunk[ratio-1], rdata_chunk[:ratio-1]))
                )

            self.comb += [
                # port_to -> rdata_fifo -> rdata_converter -> port_from
                port_to.rdata.connect(rdata_fifo.sink),
                rdata_fifo.source.connect(rdata_converter.sink),
                rdata_chunk_valid.eq((cmd_buffer.source.sel & rdata_chunk) != 0),
                If(cmd_buffer.source.valid & ~cmd_buffer.source.we,
                   # if that chunk is valid we send it to the user port and wait for ready
                    If(rdata_chunk_valid,
                        port_from.rdata.valid.eq(rdata_converter.source.valid),
                        port_from.rdata.data.eq(rdata_converter.source.data),
                        rdata_converter.source.ready.eq(port_from.rdata.ready)
                    ).Else(  # if this chunk was not requested in `sel`, ignore it
                        rdata_converter.source.ready.eq(1)
                    ),
                    rdata_finished.eq(rdata_converter.source.valid & rdata_converter.source.ready
                                      & rdata_chunk[ratio - 1])
                ),
            ]

        # Write Datapath ---------------------------------------------------------------------------

        if mode == "write" or mode == "both":
            # queue write data not to miss it when the lower chunks haven't been reqested
            wdata_fifo    = stream.SyncFIFO(port_from.wdata.description, ratio - 1)
            wdata_buffer  = stream.SyncFIFO(port_to.wdata.description, 1)
            wdata_converter = stream.StrideConverter(
                port_from.wdata.description,
                port_to.wdata.description,
                reverse=reverse)
            self.submodules += wdata_converter, wdata_fifo, wdata_buffer

            # shift register with a bitmask of current chunk
            wdata_chunk       = Signal(ratio, reset=1)
            wdata_chunk_valid = Signal()
            self.sync += \
                If(wdata_converter.sink.valid & wdata_converter.sink.ready,
                    wdata_chunk.eq(Cat(wdata_chunk[ratio-1], wdata_chunk[:ratio-1]))
                )

            # replicate `sel` bits to match the width of port_to.wdata.we
            wdata_sel = Signal.like(port_to.wdata.we)
            wdata_sel_parts = [
                Replicate(cmd_buffer.source.sel[i], port_to.wdata.we.nbits // sel.nbits)
                for i in range(ratio)
            ]
            self.sync += \
                If(cmd_buffer.source.valid & cmd_buffer.source.we & wdata_chunk[ratio - 1],
                    wdata_sel.eq(Cat(wdata_sel_parts))
                )

            self.comb += [
                # port_from -> wdata_fifo -> wdata_converter
                port_from.wdata.connect(wdata_fifo.sink),
                wdata_buffer.source.connect(port_to.wdata),
                wdata_chunk_valid.eq((cmd_buffer.source.sel & wdata_chunk) != 0),
                If(cmd_buffer.source.valid & cmd_buffer.source.we,
                    # when the current chunk is valid, read it from wdata_fifo
                    If(wdata_chunk_valid,
                        wdata_converter.sink.valid.eq(wdata_fifo.source.valid),
                        wdata_converter.sink.data.eq(wdata_fifo.source.data),
                        wdata_converter.sink.we.eq(wdata_fifo.source.we),
                        wdata_fifo.source.ready.eq(wdata_converter.sink.ready),
                    ).Else(  # if chunk is not valid, send any data and do not advance fifo
                        wdata_converter.sink.valid.eq(1),
                    ),
                ),
                wdata_buffer.sink.valid.eq(wdata_converter.source.valid),
                wdata_buffer.sink.data.eq(wdata_converter.source.data),
                wdata_buffer.sink.we.eq(wdata_converter.source.we & wdata_sel),
                wdata_converter.source.ready.eq(wdata_buffer.sink.ready),
                wdata_finished.eq(wdata_converter.sink.valid & wdata_converter.sink.ready
                                  & wdata_chunk[ratio-1]),
            ]

# LiteDRAMNativePortConverter ----------------------------------------------------------------------

class LiteDRAMNativePortConverter(Module):
    def __init__(self, port_from, port_to, reverse=False):
        assert port_from.clock_domain == port_to.clock_domain
        assert port_from.mode         == port_to.mode

        # # #

        mode = port_from.mode

        if port_from.data_width > port_to.data_width:
            converter = LiteDRAMNativePortDownConverter(port_from, port_to, reverse)
            self.submodules += converter
        elif port_from.data_width < port_to.data_width:
            converter = LiteDRAMNativePortUpConverter(port_from, port_to, reverse)
            self.submodules += converter
        else:
            self.comb += [
                port_from.cmd.connect(port_to.cmd),
                port_from.wdata.connect(port_to.wdata),
                port_to.rdata.connect(port_from.rdata)
            ]
