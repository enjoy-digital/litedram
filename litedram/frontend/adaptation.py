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
        sel = Signal(ratio)
        cmd_buffer = stream.SyncFIFO([("sel", ratio), ("we", 1)], 4)
        self.submodules += cmd_buffer
        # store last received command
        cmd_addr = Signal.like(port_from.cmd.addr)
        cmd_we = Signal()
        cmd_last = Signal()
        # indicates that we need to proceed to the next port_to command
        next_cmd = Signal()
        # signals that indicate that write/read convertion has finished
        wdata_finished = Signal()
        rdata_finished = Signal()

        self.comb += [
            # go to the next command if one of the following happens:
            #  * port_to address changes
            #  * cmd type changes
            #  * we received all the `ratio` commands
            #  * this is the last command in a sequence
            next_cmd.eq(
                (cmd_addr[log2_int(ratio):] != port_from.cmd.addr[log2_int(ratio):])
                | (cmd_we != port_from.cmd.we)
                | (sel == 2**ratio - 1)
                | cmd_last
            ),
            # when the first command is received, send it immediatelly
            If(sel == 0,
                If(port_from.cmd.valid,
                    port_to.cmd.valid.eq(1),
                    port_to.cmd.we.eq(port_from.cmd.we),
                    port_to.cmd.addr.eq(port_from.cmd.addr[log2_int(ratio):]),
                    port_from.cmd.ready.eq(port_to.cmd.ready),
                )
            ).Else(
                # we have already sent the initial command, now either continue sending cmd.ready
                # to the master or send the current command if we have to go to next command
                If(next_cmd,
                    cmd_buffer.sink.valid.eq(1),
                    cmd_buffer.sink.sel.eq(sel),
                    cmd_buffer.sink.we.eq(cmd_we),
                ).Else(
                    port_from.cmd.ready.eq(port_from.cmd.valid),
                )
            ),
            cmd_buffer.source.ready.eq(wdata_finished | rdata_finished)
        ]

        self.sync += [
            # whenever a command gets accepted, update `sel` bitmask and store the command info
            If(port_from.cmd.valid & port_from.cmd.ready,
                cmd_addr.eq(port_from.cmd.addr),
                cmd_we.eq(port_from.cmd.we),
                cmd_last.eq(port_from.cmd.last),
                sel.eq(sel | (1 << port_from.cmd.addr[:log2_int(ratio)])),
            ),
            # clear `sel` after the command has been sent for data procesing
            If(cmd_buffer.sink.valid & cmd_buffer.sink.ready,
                sel.eq(0),
            ),
        ]

        # Read Datapath ----------------------------------------------------------------------------

        if mode == "read" or mode == "both":
            # buffers output from port_to
            rdata_fifo = stream.SyncFIFO(port_to.rdata.description, ratio)
            # connected to the buffered output
            rdata_converter = stream.StrideConverter(
                port_to.rdata.description,
                port_from.rdata.description,
                reverse=reverse)
            self.submodules +=  rdata_fifo, rdata_converter

            # bitmask shift register with single 1 bit and all other 0s
            rdata_chunk       = Signal(ratio, reset=1)
            rdata_chunk_valid = Signal()
            # whenever the converter spits data chunk we shift the chunk bitmask
            self.sync += \
                If(rdata_converter.source.valid &
                   rdata_converter.source.ready,
                    rdata_chunk.eq(Cat(rdata_chunk[ratio-1], rdata_chunk[:ratio-1]))
                )

            self.comb += [
                # port_to -> rdata_fifo -> rdata_converter
                port_to.rdata.connect(rdata_fifo.sink),
                rdata_fifo.source.connect(rdata_converter.sink),
                # chunk is valid if it's bit is in `sel` sent previously to the FIFO
                rdata_chunk_valid.eq((cmd_buffer.source.sel & rdata_chunk) != 0),
                # whenever `sel` from FIFO is valid
                If(cmd_buffer.source.valid & ~cmd_buffer.source.we,
                    # if that chunk is valid we send it to the user port and wait for ready from user
                    If(rdata_chunk_valid,
                        port_from.rdata.valid.eq(rdata_converter.source.valid),
                        port_from.rdata.data.eq(rdata_converter.source.data),
                        rdata_converter.source.ready.eq(port_from.rdata.ready)
                    # if this was not requested by `sel` then we just ack it
                    ).Else(
                        rdata_converter.source.ready.eq(1)
                    ),
                    rdata_finished.eq(rdata_converter.source.valid & rdata_converter.source.ready & rdata_chunk[ratio - 1])
                ),
            ]

        # Write Datapath ---------------------------------------------------------------------------

        if mode == "write" or mode == "both":
            wdata_fifo    = stream.SyncFIFO(port_from.wdata.description, ratio)
            wdata_converter = stream.StrideConverter(
                port_from.wdata.description,
                port_to.wdata.description,
                reverse=reverse)
            self.submodules += wdata_converter, wdata_fifo

            # bitmask shift register with single 1 bit and all other 0s
            wdata_chunk       = Signal(ratio, reset=1)
            wdata_chunk_valid = Signal()
            # whenever the converter spits data chunk we shift the chunk bitmask
            self.sync += \
                If(wdata_converter.sink.valid & wdata_converter.sink.ready,
                    wdata_chunk.eq(Cat(wdata_chunk[ratio-1], wdata_chunk[:ratio-1]))
                )

            # replicate sel so that each bit covers according part of we bitmask (1 sel bit may cover
            # multiple bytes)
            wdata_sel = Signal.like(port_to.wdata.we)
            #  self.comb += wdata_sel.eq(
            #      Cat([Replicate(cmd_buffer.source.sel[i], port_to.wdata.we.nbits // sel.nbits) for i in range(ratio)])
            #  )

            self.sync += [
                If(cmd_buffer.source.valid & cmd_buffer.source.we & wdata_chunk[ratio - 1],
                    wdata_sel.eq(Cat([Replicate(cmd_buffer.source.sel[i], port_to.wdata.we.nbits // sel.nbits)
                                      for i in range(ratio)]))
                )
            ]

            self.comb += [
                port_from.wdata.connect(wdata_fifo.sink),

                wdata_chunk_valid.eq((cmd_buffer.source.sel & wdata_chunk) != 0),

                If(cmd_buffer.source.valid & cmd_buffer.source.we,
                    If(wdata_chunk_valid,
                        wdata_converter.sink.valid.eq(wdata_fifo.source.valid),
                        wdata_converter.sink.data.eq(wdata_fifo.source.data),
                        wdata_converter.sink.we.eq(wdata_fifo.source.we),
                        wdata_fifo.source.ready.eq(1),
                    ).Else(
                        wdata_converter.sink.valid.eq(1),
                        wdata_converter.sink.data.eq(0),
                        wdata_converter.sink.we.eq(0),
                        wdata_fifo.source.ready.eq(0),
                    ),
                ),

                port_to.wdata.valid.eq(wdata_converter.source.valid),
                port_to.wdata.data.eq(wdata_converter.source.data),
                port_to.wdata.we.eq(wdata_converter.source.we & wdata_sel),
                wdata_converter.source.ready.eq(port_to.wdata.ready),
                #  wdata_finished.eq(wdata_converter.source.valid & wdata_converter.source.ready),
                wdata_finished.eq(wdata_converter.sink.valid & wdata_converter.sink.ready & wdata_chunk[ratio-1]),
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
