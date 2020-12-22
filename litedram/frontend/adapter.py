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

        address_width     = port_from.address_width
        data_width        = port_from.data_width
        mode              = port_from.mode

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

        count = Signal(max=ratio)

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            NextValue(count, 0),
            If(port_from.cmd.valid,
                NextState("CONVERT")
            )
        )
        fsm.act("CONVERT",
            port_to.cmd.valid.eq(1),
            port_to.cmd.we.eq(port_from.cmd.we),
            port_to.cmd.addr.eq(port_from.cmd.addr*ratio + count),
            If(port_to.cmd.ready,
                NextValue(count, count + 1),
                If(count == ratio - 1,
                    port_from.cmd.ready.eq(1),
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
    def __init__(self, port_from, port_to, reverse=False,
                 rx_buffer_depth=4, tx_buffer_depth=4, cmd_buffer_depth=4):
        assert port_from.clock_domain == port_to.clock_domain
        assert port_from.data_width    < port_to.data_width
        assert port_from.mode         == port_to.mode
        if port_to.data_width % port_from.data_width:
            raise ValueError("Ratio must be an int")

        # # #

        self.ratio  = ratio     = port_to.data_width//port_from.data_width
        mode        = port_from.mode

        # Command ----------------------------------------------------------------------------------

        # Defines read/write ordering of chunks that have been requested
        ordering_layout  = [
            ("counter", log2_int(ratio) + 1),
            ("ordering", ratio * log2_int(ratio))
        ]
        self.rx_buffer   = rx_buffer    = stream.SyncFIFO(ordering_layout, rx_buffer_depth)
        self.tx_buffer   = tx_buffer    = stream.SyncFIFO(ordering_layout, tx_buffer_depth)

        self.submodules += rx_buffer, tx_buffer
        # Store last received command
        cmd_addr         = Signal.like(port_to.cmd.addr)
        cmd_we           = Signal()
        cmd_last         = Signal()
        # Indicates that we need to proceed to the next port_to command
        cmd_finished     = Signal()
        addr_changed     = Signal()
        # Signals that indicate that write/read convertion has finished
        wdata_finished   = Signal()
        rdata_finished   = Signal()

        # Used to keep access order for reads and writes
        counter          = Signal(log2_int(ratio) + 1)
        ordering         = Signal(ratio * log2_int(ratio))

        # Send Command -----------------------------------------------------------------------------

        self.send_cmd       = send_cmd      = Signal()
        self.send_cmd_addr  = send_cmd_addr = Signal.like(port_to.cmd.addr)
        self.send_cmd_we    = send_cmd_we   = Signal.like(port_to.cmd.we)
        self.send_cmd_busy  = send_cmd_busy = Signal()

        send_inner_cmd_addr = Signal.like(port_to.cmd.addr)
        send_inner_cmd_we   = Signal.like(port_to.cmd.we)

        self.cmd_buffer     = cmd_buffer    = stream.SyncFIFO([ ("cmd_addr", send_cmd_addr.nbits),
                                                                ("cmd_we", send_cmd_we.nbits)],
                                                                cmd_buffer_depth)
        self.submodules    += cmd_buffer
        self.comb += [
            send_cmd_busy.eq(~cmd_buffer.sink.ready),
            cmd_buffer.sink.valid.eq(send_cmd),
            cmd_buffer.sink.cmd_addr.eq(send_cmd_addr),
            cmd_buffer.sink.cmd_we.eq(send_cmd_we)
        ]

        self.submodules.sender = send_fsm   = FSM(reset_state="IDLE")
        send_fsm.act("IDLE",
            If(cmd_buffer.source.valid,
                cmd_buffer.source.ready.eq(1),
                NextValue(send_inner_cmd_addr, cmd_buffer.source.cmd_addr),
                NextValue(send_inner_cmd_we, cmd_buffer.source.cmd_we),
                NextState("SEND")
            )
        )
        send_fsm.act("SEND",
            port_to.cmd.valid.eq(1),
            port_to.cmd.addr.eq(send_inner_cmd_addr),
            port_to.cmd.we.eq(send_inner_cmd_we),
            If(port_to.cmd.ready,
                If(cmd_buffer.source.valid,
                    cmd_buffer.source.ready.eq(1),
                    NextValue(send_inner_cmd_addr, cmd_buffer.source.cmd_addr),
                    NextValue(send_inner_cmd_we, cmd_buffer.source.cmd_we),
                    NextState("SEND")
                ).Else(
                    NextState("IDLE")
                )
            )
        )
        # Command flow is quite complicate, nonlinear and it depends on type read/write,
        # so here is summary:
        # This FSM receives commands from `port_from` and pushes them to `cmd_buffer` queue,
        # which is then handled by the `send_fsm` which sends commands to `port_to`.
        # In the FILL phase we gather the requested ordering of data chunks that map to a single
        # `port_to` transaction. The order of states in the FSM depends on command type: read
        # commands are queued on reception, write commands after the FILL phase.
        # Data order is also queued after FILL phase, at that point we know right order

        # Longer version
        # WAIT-FOR-CMD:
        # - if there is new cmd available do
        #   - set internal variable
        #   - check if it's read or write
        #       - write: go to FILL
        #       - read: try to send (queue) read cmd
        #           - if successful goto FILL
        #           - else goto WAIT-TO-SEND
        #
        # WAIT-TO-SEND:
        # - set cmd addr and cmd we to be sent (queued)
        # - if we can send (queue)
        #       - if cmd was read goto FILL
        #       - else
        #           - if there is new cmd waiting and it's write goto FILL
        #           - else goto WAIT-FOR-CMD
        # - else goto WAIT-TO-SEND
        #
        # FILL:
        # - if cmd finished
        #   - if cmd was write do tx_commit
        #   - else do rx_commit
        # - else
        #   - acknowledged incoming cmds
        #   - store their relative addresses (which subword of DRAM word)
        #
        # tx_commit(not a state, just combinational logic):
        # - try to store data ordering in tx_buffer
        #   - if successful
        #       - try to send (queue) cmd:
        #       - if successful
        #           - if there is new cmd and it's write
        #               - set internal variables as in WAIT-FOR-CMD
        #               - goto FILL
        #           -else goto WAIT-FOR-CMD
        #       - else goto WAIT_TO_SEND
        #   - else goto WAIT-FOR-SPACE-IN-TX_BUFFER
        #
        # rx_commit(not a state, just combinational logic):
        # - try to store data ordering in rx_buffer
        #   - if successful
        #       - if there is new cmd and it's read
        #           - set internal variables as in WAIT-FOR-CMD
        #           - try to send (queue) cmd
        #           - if successful
        #               - acknowledge cmd
        #               - store their relative address
        #               - goto FILL
        #           - else goto WAIT-TO-SEND
        #   - else goto WAIT-FOR-CMD
        # - else goto WAIT-FOR-SPACE-IN-RX_BUFFER
        #
        # WAIT-FOR-SPACE-IN-TX_BUFFER:
        # - tx_commit
        #
        # WAIT-FOR-SPACE-IN-RX_BUFFER:
        # - rx_commit

        self.submodules.fsm = fsm = FSM(reset_state="WAIT-FOR-CMD")
        fsm.act("WAIT-FOR-CMD",
            If(port_from.cmd.valid,
                NextValue(counter, 0),
                NextValue(cmd_addr, port_from.cmd.addr[log2_int(ratio):]),
                NextValue(cmd_we, port_from.cmd.we),
                If(port_from.cmd.we,
                    NextState("FILL")
                ).Else(
                    self.send_cmd.eq(1),
                    self.send_cmd_addr.eq(port_from.cmd.addr[log2_int(ratio):]),
                    self.send_cmd_we.eq(port_from.cmd.we),
                    If(self.send_cmd_busy,
                        NextState("WAIT-TO-SEND")
                    ).Else(
                        NextState("FILL")
                    )
                )
            )
        )
        fsm.act("WAIT-TO-SEND",
            send_cmd.eq(1),
            send_cmd_addr.eq(cmd_addr),
            send_cmd_we.eq(cmd_we),
            If(~send_cmd_busy,
                If(cmd_we,
                    If(port_from.cmd.valid & port_from.cmd.we,
                        NextValue(counter, 0),
                        NextValue(cmd_addr, port_from.cmd.addr[log2_int(ratio):]),
                        NextValue(cmd_we, port_from.cmd.we),
                        NextState("FILL")
                    ).Else(
                        NextState("WAIT-FOR-CMD")
                    )
                ).Else(
                    NextState("FILL")
                )
            )
        )
        cases = {}
        for i in range(ratio):
            cases[i] = NextValue(ordering[i * log2_int(ratio) : (i + 1) * log2_int(ratio)],
                                 port_from.cmd.addr[:log2_int(ratio)])

        fsm.act("FILL",
            If(cmd_finished,
                If(cmd_we,
                    self.tx_commit(cmd_addr, cmd_we, cmd_last, port_from, counter, ordering)
                ).Else(
                    self.rx_commit(cmd_addr, cmd_we, cmd_last, port_from, counter, ordering)
                )
            ).Else(
                port_from.cmd.ready.eq(1),
                If(port_from.cmd.valid,
                    NextValue(cmd_last, port_from.cmd.last),
                    NextValue(counter, counter + 1),
                    Case(counter, cases),
                )
            )
        )
        fsm.act("WAIT-FOR-SPACE-IN-RX_BUFFER",
            self.rx_commit(cmd_addr, cmd_we, cmd_last, port_from, counter, ordering)
        )
        fsm.act("WAIT-FOR-SPACE-IN-TX_BUFFER",
            self.tx_commit(cmd_addr, cmd_we, cmd_last, port_from, counter, ordering)
        )
        self.comb += [
            tx_buffer.source.ready.eq(wdata_finished),
            rx_buffer.source.ready.eq(rdata_finished),
            addr_changed.eq(cmd_addr != port_from.cmd.addr[log2_int(ratio):]),
            # Go to the next command if one of the following happens:
            #  - port_to address changes.
            #  - cmd type changes.
            #  - we received all the `ratio` commands.
            #  - this is the last command in a sequence.
            #  - master requests a flush (even after the command has been sent).
            cmd_finished.eq(addr_changed | (cmd_we != port_from.cmd.we) | (counter == ratio)
                        | cmd_last | port_from.flush),
        ]

        # Read Datapath ----------------------------------------------------------------------------

        if mode in ["read", "both"]:
            read_upper_counter   = Signal.like(counter)
            read_inner_counter   = Signal.like(counter)
            read_inner_ordering  = Signal.like(ordering)

            read_chunk           = Signal(log2_int(ratio))

            # Queue received data not to loose it when it comes too fast
            rdata_fifo = stream.SyncFIFO(port_to.rdata.description, cmd_buffer.depth + rx_buffer.depth + 1)
            self.submodules +=  rdata_fifo

            cases = {}
            for i in range(ratio):
                n = ratio-i-1 if reverse else i
                cases[i] = port_from.rdata.data.eq(rdata_fifo.source.data[
                    n * port_from.data_width :(n + 1) * port_from.data_width]),

            self.comb += [

                # Port_to -> rdata_fifo -> order_mux -> port_from
                port_to.rdata.connect(rdata_fifo.sink),
                rdata_fifo.source.ready.eq(rdata_finished),

                If(rdata_fifo.source.valid & rx_buffer.source.valid,
                   # If that chunk is valid we send it to the user port and wait for ready
                    If(read_inner_counter < read_upper_counter,
                        port_from.rdata.valid.eq(1),
                        Case(read_chunk, cases),
                    )
                )
            ]

            cases = {}
            for i in range(ratio):
                cases[i] = read_chunk.eq(read_inner_ordering[
                        i * log2_int(ratio) : (i + 1) * log2_int(ratio)]),

            self.comb += [
                # Select source of address order
                If(rx_buffer.source.valid,
                    read_upper_counter.eq(rx_buffer.source.counter),
                    read_inner_ordering.eq(rx_buffer.source.ordering)
                ),
                # Select read chunk
                Case(read_inner_counter, cases),

                rdata_finished.eq((read_inner_counter == read_upper_counter - 1) & rx_buffer.source.valid
                                  & (port_from.rdata.valid & port_from.rdata.ready))
            ]

            self.sync += [
                If(rdata_finished,
                    read_inner_counter.eq(0)
                ).Elif(port_from.rdata.valid & port_from.rdata.ready &
                    (read_inner_counter < read_upper_counter),
                    read_inner_counter.eq(read_inner_counter + 1)
                )
            ]

        # Write Datapath ---------------------------------------------------------------------------

        if mode in ["write", "both"]:
            write_upper_counter   = Signal.like(counter)
            write_inner_counter   = Signal.like(counter)
            write_inner_ordering  = Signal.like(ordering)

            write_chunk           = Signal(log2_int(ratio))

            # Queue write data not to miss it when the lower chunks haven't been reqested
            wdata_fifo    = stream.SyncFIFO(port_from.wdata.description, ratio)
            wdata_buffer  = Record([("data", port_to.wdata.data.nbits),
                                    ("we", port_to.wdata.we.nbits)])
            self.submodules += wdata_fifo

            self.comb += [
                # port_from -> wdata_fifo -> wdata_buffer (keeps order)
                port_from.wdata.connect(wdata_fifo.sink),
                port_to.wdata.data.eq(wdata_buffer.data),
                port_to.wdata.we.eq(wdata_buffer.we),
                port_to.wdata.valid.eq((write_inner_counter == write_upper_counter) & tx_buffer.source.valid),
                wdata_fifo.source.ready.eq(write_inner_counter < write_upper_counter),
            ]

            cases = {}
            for i in range(ratio):
                cases[i] = write_chunk.eq(write_inner_ordering[
                        i * log2_int(ratio) : (i + 1) * log2_int(ratio)]),

            self.comb += [
                # Select source of address order
                If(tx_buffer.source.valid,
                    write_upper_counter.eq(tx_buffer.source.counter),
                    write_inner_ordering.eq(tx_buffer.source.ordering)
                ).Else(
                    write_upper_counter.eq(counter),
                    write_inner_ordering.eq(ordering)
                ),

                Case(write_inner_counter, cases),

                wdata_finished.eq(port_to.wdata.valid & port_to.wdata.ready),
            ]

            cases = {}
            for i in range(ratio):
                n = ratio-i-1 if reverse else i
                cases[i] = [
                    wdata_buffer.data[n * port_from.data_width : (n + 1) * port_from.data_width].eq(
                            wdata_fifo.source.data),
                    wdata_buffer.we[n * port_from.wdata.we.nbits : (n + 1) * port_from.wdata.we.nbits].eq(
                            wdata_fifo.source.we),
                ]

            self.sync += [
                If(wdata_fifo.source.valid & wdata_fifo.source.ready,
                    Case(write_chunk, cases)
                ),
                If(wdata_finished,
                    write_inner_counter.eq(0),
                    wdata_buffer.we.eq(0),
                ).Elif(wdata_fifo.source.valid & wdata_fifo.source.ready,
                    write_inner_counter.eq(write_inner_counter + 1)
                )
            ]


    def tx_commit (self, cmd_addr, cmd_we, cmd_last, port_from, counter, ordering):
        return [
            self.tx_buffer.sink.valid.eq(1),
            self.tx_buffer.sink.counter.eq(counter),
            self.tx_buffer.sink.ordering.eq(ordering),
            If(self.tx_buffer.sink.ready,
                self.send_cmd.eq(1),
                self.send_cmd_addr.eq(cmd_addr),
                self.send_cmd_we.eq(cmd_we),
                If(self.send_cmd_busy,
                    NextState("WAIT-TO-SEND")
                ).Else(
                    If(port_from.cmd.valid & port_from.cmd.we,
                        NextValue(counter, 0),
                        NextValue(cmd_addr, port_from.cmd.addr[log2_int(self.ratio):]),
                        NextValue(cmd_we, port_from.cmd.we),
                        NextState("FILL")
                    ).Else(
                        NextState("WAIT-FOR-CMD")
                    )
                )
            ).Else(
                NextState("WAIT-FOR-SPACE-IN-TX_BUFFER")
            )
        ]


    def rx_commit (self, cmd_addr, cmd_we, cmd_last, port_from, counter, ordering):
        return [
            self.rx_buffer.sink.valid.eq(1),
            self.rx_buffer.sink.counter.eq(counter),
            self.rx_buffer.sink.ordering.eq(ordering),
            If(self.rx_buffer.sink.ready,
                If(port_from.cmd.valid & ~port_from.cmd.we,
                    self.send_cmd.eq(1),
                    self.send_cmd_addr.eq(port_from.cmd.addr[log2_int(self.ratio):]),
                    self.send_cmd_we.eq(port_from.cmd.we),
                    NextValue(cmd_addr, port_from.cmd.addr[log2_int(self.ratio):]),
                    NextValue(cmd_we, port_from.cmd.we),
                    If(self.send_cmd_busy,
                        NextValue(counter, 0),
                        NextState("WAIT-TO-SEND")
                    ).Else(
                        port_from.cmd.ready.eq(1),
                        NextValue(counter, 1),
                        NextValue(ordering[:1 * log2_int(self.ratio)],
                                     port_from.cmd.addr[:log2_int(self.ratio)]),
                        NextValue(cmd_last, port_from.cmd.last),
                        NextState("FILL")
                    )
                ).Else(
                    NextState("WAIT-FOR-CMD")
                )
            ).Else(
                NextState("WAIT-FOR-SPACE-IN-RX_BUFFER")
            )
        ]

# LiteDRAMNativePortConverter ----------------------------------------------------------------------

class LiteDRAMNativePortConverter(Module):
    def __init__(self, port_from, port_to, reverse=False,
            rx_buffer_depth=4, tx_buffer_depth=4, cmd_buffer_depth=4):
        assert port_from.clock_domain == port_to.clock_domain
        assert port_from.mode         == port_to.mode

        # # #

        ratio = port_from.data_width/port_to.data_width

        if ratio > 1:
            # DownConverter
            self.submodules.converter = LiteDRAMNativePortDownConverter(port_from, port_to, reverse)
        elif ratio < 1:
            # UpConverter
            self.submodules.converter = LiteDRAMNativePortUpConverter(
                port_from, port_to, reverse,
                rx_buffer_depth, tx_buffer_depth, cmd_buffer_depth)
        else:
            # Identity
            self.comb += port_from.connect(port_to)
