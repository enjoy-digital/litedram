from litex.gen import *

from litex.soc.interconnect import stream

from litedram.common import *


class LiteDRAMPortCDC(Module):
    def __init__(self, port_from, port_to,
                 cmd_depth=4,
                 wdata_depth=16,
                 rdata_depth=16):
        assert port_from.aw == port_to.aw
        assert port_from.dw == port_to.dw
        assert port_from.mode == port_to.mode

        aw = port_from.aw
        dw = port_from.dw
        mode = port_from.mode
        cd_from = port_from.cd
        cd_to = port_to.cd

        # # #

        cmd_fifo = stream.AsyncFIFO([("we", 1), ("adr", aw)], cmd_depth)
        cmd_fifo = ClockDomainsRenamer({"write": cd_from,
                                        "read":  cd_to})(cmd_fifo)
        self.submodules += cmd_fifo
        self.submodules += stream.Pipeline(port_from.cmd,
                                           cmd_fifo,
                                           port_to.cmd)

        if mode == "write" or mode == "both":
            wdata_fifo = stream.AsyncFIFO([("data", dw), ("we", dw//8)], wdata_depth)
            wdata_fifo = ClockDomainsRenamer({"write": cd_from,
                                              "read":  cd_to})(wdata_fifo)
            self.submodules += wdata_fifo
            self.submodules += stream.Pipeline(port_from.wdata,
                                               wdata_fifo,
                                               port_to.wdata)

        if mode == "read" or mode == "both":
            rdata_fifo = stream.AsyncFIFO([("data", dw)], rdata_depth)
            rdata_fifo = ClockDomainsRenamer({"write": cd_to,
                                              "read":  cd_from})(rdata_fifo)
            self.submodules += rdata_fifo
            self.submodules += stream.Pipeline(port_to.rdata,
                                               rdata_fifo,
                                               port_from.rdata)


class LiteDRAMPortDownConverter(Module):
    """LiteDRAM port DownConverter

    This module reduces user port data width to fit controller data width.
    With N = port_from.dw/port_to.dw:
    - Address is adapted (multiplied by N + internal increments)
    - A write from the user is splitted and generates N writes to the
    controller.
    - A read from the user generates N reads to the controller and returned datas are regrouped
    in a single data presented to the user.
    """
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd
        assert port_from.dw > port_to.dw
        assert port_from.mode == port_to.mode
        if port_from.dw % port_to.dw:
            raise ValueError("Ratio must be an int")

        # # #

        ratio = port_from.dw//port_to.dw
        mode = port_from.mode

        counter = Signal(max=ratio)
        counter_reset = Signal()
        counter_ce = Signal()
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
            port_to.cmd.adr.eq(port_from.cmd.adr*ratio + counter),
            If(port_to.cmd.ready,
                counter_ce.eq(1),
                If(counter == ratio - 1,
                    port_from.cmd.ready.eq(1),
                    NextState("IDLE")
                )
            )
        )

        if mode == "write" or mode == "both":
            wdata_converter = stream.StrideConverter(port_from.wdata.description,
                                                     port_to.wdata.description)
            self.submodules += wdata_converter
            self.submodules += stream.Pipeline(port_from.wdata,
                                               wdata_converter,
                                               port_to.wdata)

        if mode == "read" or mode == "both":
            rdata_converter = stream.StrideConverter(port_to.rdata.description,
                                                     port_from.rdata.description)
            self.submodules += rdata_converter
            self.submodules += stream.Pipeline(port_to.rdata,
                                               rdata_converter,
                                               port_from.rdata)


class LiteDRAMWritePortUpConverter(Module):
    # TODO: finish and remove hack
    """LiteDRAM write port UpConverter

    This module increase user port data width to fit controller data width.
    With N = port_to.dw/port_from.dw:
    - Address is adapted (divided by N)
    - N writes from user are regrouped in a single one to the controller
    (when possible, ie when consecutive and bursting)
    """
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd
        assert port_from.dw < port_to.dw
        assert port_from.mode == port_to.mode
        assert port_from.mode == "write"
        if port_to.dw % port_from.dw:
            raise ValueError("Ratio must be an int")

        # # #

        ratio = port_to.dw//port_from.dw

        we = Signal()
        address = Signal(port_to.aw)

        counter = Signal(max=ratio)
        counter_reset = Signal()
        counter_ce = Signal()
        self.sync += \
            If(counter_reset,
                counter.eq(0)
            ).Elif(counter_ce,
                counter.eq(counter + 1)
            )

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            port_from.cmd.ready.eq(1),
            If(port_from.cmd.valid,
                counter_ce.eq(1),
                NextValue(we, port_from.cmd.we),
                NextValue(address, port_from.cmd.adr),
                NextState("RECEIVE")
            )
        )
        fsm.act("RECEIVE",
            port_from.cmd.ready.eq(1),
            If(port_from.cmd.valid,
                counter_ce.eq(1),
                If(counter == ratio-1,
                    NextState("GENERATE")
                )
            )
        )
        fsm.act("GENERATE",
            port_to.cmd.valid.eq(1),
            port_to.cmd.we.eq(we),
            port_to.cmd.adr.eq(address[log2_int(ratio):]),
            If(port_to.cmd.ready,
                NextState("IDLE")
            )
        )

        wdata_converter = stream.StrideConverter(port_from.wdata.description,
                                                 port_to.wdata.description)
        self.submodules += wdata_converter
        self.submodules += stream.Pipeline(port_from.wdata,
                                           wdata_converter,
                                           port_to.wdata)


class LiteDRAMReadPortUpConverter(Module):
    """LiteDRAM port UpConverter

    This module increase user port data width to fit controller data width.
    With N = port_to.dw/port_from.dw:
    - Address is adapted (divided by N)
    - N read from user are regrouped in a single one to the controller
    (when possible, ie when consecutive and bursting)
    """
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd
        assert port_from.dw < port_to.dw
        assert port_from.mode == port_to.mode
        assert port_from.mode == "read"
        if port_to.dw % port_from.dw:
            raise ValueError("Ratio must be an int")

        # # #

        ratio = port_to.dw//port_from.dw


        # cmd

        cmd_buffer = stream.SyncFIFO([("sel", ratio)], 4)
        self.submodules += cmd_buffer

        counter = Signal(max=ratio)
        counter_ce = Signal()
        self.sync += \
            If(counter_ce,
                counter.eq(counter + 1)
            )

        self.comb += \
            If(port_from.cmd.valid,
                If(counter == 0,
                    port_to.cmd.valid.eq(1),
                    port_to.cmd.adr.eq(port_from.cmd.adr[log2_int(ratio):]),
                    port_from.cmd.ready.eq(port_to.cmd.ready),
                    counter_ce.eq(port_to.cmd.ready)
                ).Else(
                    port_from.cmd.ready.eq(1),
                    counter_ce.eq(1)
                )
            )

        # TODO: fix sel
        self.comb += \
            If(port_to.cmd.valid & port_to.cmd.ready,
                cmd_buffer.sink.valid.eq(1),
                cmd_buffer.sink.sel.eq(2**ratio-1)
            )

        # datapath

        rdata_buffer  = stream.Buffer(port_to.rdata.description)
        rdata_converter = stream.StrideConverter(port_to.rdata.description,
                                                 port_from.rdata.description)
        self.submodules +=  rdata_buffer, rdata_converter

        rdata_chunk = Signal(ratio, reset=1)
        rdata_chunk_valid = Signal()
        self.sync += \
            If(rdata_converter.source.valid &
               rdata_converter.source.ready,
                rdata_chunk.eq(Cat(rdata_chunk[ratio-1], rdata_chunk[:ratio-1]))
            )

        self.comb += [
            port_to.rdata.connect(rdata_buffer.sink),
            rdata_buffer.source.connect(rdata_converter.sink),
            rdata_chunk_valid.eq((cmd_buffer.source.sel & rdata_chunk) != 0),
            If(cmd_buffer.source.valid,
                If(rdata_chunk_valid,
                    port_from.rdata.valid.eq(rdata_converter.source.valid),
                    port_from.rdata.data.eq(rdata_converter.source.data),
                    rdata_converter.source.ready.eq(port_from.rdata.ready)
                ).Else(
                    rdata_converter.source.ready.eq(1)
                )
            ),
            cmd_buffer.source.ready.eq(rdata_converter.source.ready & rdata_chunk[ratio-1])
        ]


class LiteDRAMPortConverter(Module):
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd
        assert port_from.mode == port_to.mode

        # # #

        mode = port_from.mode

        if port_from.dw > port_to.dw:
            converter = LiteDRAMPortDownConverter(port_from, port_to)
            self.submodules += converter
        elif port_from.dw < port_to.dw:
            if mode == "write":
                converter = LiteDRAMWritePortUpConverter(port_from, port_to)
            elif mode == "read":
                converter = LiteDRAMReadPortUpConverter(port_from, port_to)
            else:
                raise NotImplementedError

            converter
            self.submodules += converter
        else:
            self.comb += [
                port_from.cmd.connect(port_to.cmd),
                port_from.wdata.connect(port_to.wdata),
                port_to.rdata.connect(port_from.rdata)
            ]
