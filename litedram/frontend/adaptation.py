from litex.gen import *

from litex.soc.interconnect import stream

from litedram.common import *


class LiteDRAMPortCDC(Module):
    # TODO: check cmd/wdata/rdata fifo depths
    def __init__(self, port_from, port_to):
        assert port_from.aw == port_to.aw
        assert port_from.dw == port_to.dw

        aw = port_from.aw
        dw = port_from.dw
        cd_from = port_from.cd
        cd_to = port_to.cd

        # # #

        cmd_fifo = stream.AsyncFIFO([("we", 1), ("adr", aw)], 4)
        cmd_fifo = ClockDomainsRenamer({"write": cd_from,
                                        "read": cd_to})(cmd_fifo)
        self.submodules += cmd_fifo
        self.comb += [
            port_from.cmd.connect(cmd_fifo.sink),
            cmd_fifo.source.connect(port_to.cmd)
        ]

        wdata_fifo = stream.AsyncFIFO([("data", dw), ("we", dw//8)], 16)
        wdata_fifo = ClockDomainsRenamer({"write": cd_from,
                                          "read": cd_to})(wdata_fifo)
        self.submodules += wdata_fifo
        self.comb += [
            port_from.wdata.connect(wdata_fifo.sink),
            wdata_fifo.source.connect(port_to.wdata)
        ]

        rdata_fifo = stream.AsyncFIFO([("data", dw)], 16)
        rdata_fifo = ClockDomainsRenamer({"write": cd_to,
                                          "read": cd_from})(rdata_fifo)
        self.submodules += rdata_fifo
        self.comb += [
            port_to.rdata.connect(rdata_fifo.sink),
            rdata_fifo.source.connect(port_from.rdata)
        ]


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
        if port_from.dw % port_to.dw:
            raise ValueError("Ratio must be an int")

        # # #

        ratio = port_from.dw//port_to.dw

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

        wdata_converter = stream.StrideConverter(port_from.wdata.description,
                                                 port_to.wdata.description)
        self.submodules += wdata_converter
        self.comb += [
            port_from.wdata.connect(wdata_converter.sink),
            wdata_converter.source.connect(port_to.wdata)
        ]

        rdata_converter = stream.StrideConverter(port_to.rdata.description,
                                                 port_from.rdata.description)
        self.submodules += rdata_converter
        self.comb += [
            port_to.rdata.connect(rdata_converter.sink),
            rdata_converter.source.connect(port_from.rdata)
        ]


class LiteDRAMPortUpConverter(Module):
    # TODO:
    # - handle all specials cases (incomplete / non aligned bursts)
    # - add exceptions on datapath for such cases
    """LiteDRAM port UpConverter

    This module increase user port data width to fit controller data width.
    With N = port_to.dw/port_from.dw:
    - Address is adapted (divided by N)
    - N writes and read from user are regrouped in a single one to the controller
    (when possible, ie when consecutive and bursting)
    """
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd
        assert port_from.dw < port_to.dw
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
            counter_reset.eq(1),
            If(port_from.cmd.valid,
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
        self.comb += [
            port_from.wdata.connect(wdata_converter.sink),
            wdata_converter.source.connect(port_to.wdata)
        ]

        rdata_converter = stream.StrideConverter(port_to.rdata.description,
                                                 port_from.rdata.description)
        self.submodules += rdata_converter
        self.comb += [
            port_to.rdata.connect(rdata_converter.sink),
            rdata_converter.source.connect(port_from.rdata)
        ]


class LiteDRAMPortConverter(Module):
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd

        # # #

        if port_from.dw > port_to.dw:
            converter = LiteDRAMPortDownConverter(port_from, port_to)
            self.submodules += converter
        elif port_from.dw < port_to.dw:
            converter = LiteDRAMPortUpConverter(port_from, port_to)
            self.submodules += converter
        else:
            self.comb += [
                port_from.cmd.connect(port_to.cmd),
                port_from.wdata.connect(port_to.wdata),
                port_to.rdata.connect(port_from.rdata)
            ]
