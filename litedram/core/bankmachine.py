from migen.fhdl.std import *
from migen.genlib.roundrobin import *
from migen.genlib.fsm import FSM, NextState
from migen.genlib.misc import optree, WaitTimer
from migen.actorlib.fifo import SyncFIFO
from migen.flow.plumbing import Multiplexer

from litedram.common import *


class LiteDRAMRowTracker(Module):
    def __init__(self, rw):
        self.row = Signal(rw)
        self.open = Signal()
        self.close = Signal()

        # # #

        self.hasopenrow = Signal()
        self._openrow = Signal(rw)
        self.sync += \
            If(self.open,
                self.hasopenrow.eq(1),
                self._openrow.eq(self.row)
            ).Elif(self.close,
                self.hasopenrow.eq(0)
            )

    def row_hit(self, row):
        return self._openrow == row


class LiteDRAMBankMachine(Module):
    def __init__(self, sdram_module, cmd_fifo_depth):
        self.refresh = Sink(dram_refresh_description())
        self.write_cmd = Sink(dram_cmd_description(sdram_module.geom_settings.rowbits,
                                                   sdram_module.geom_settings.colbits))
        self.read_cmd = Sink(dram_cmd_description(sdram_module.geom_settings.rowbits,
                                                  sdram_module.geom_settings.colbits))
        self.cmd = Source(dram_bank_cmd_description(32)) # XXX

        # # #

        read_write_n = FlipFlop()
        self.comb += read_write_n.d.eq(1)
        self.submodules += read_write_n

        # Cmd fifos
        write_cmd_fifo = SyncFIFO(self.write_cmd.description, cmd_fifo_depth)
        read_cmd_fifo = SyncFIFO(self.read_cmd.description, cmd_fifo_depth)
        self.submodules += write_cmd_fifo, read_cmd_fifo
        self.comb += [
            Record.connect(self.write_cmd, write_cmd_fifo.sink),
            Record.connect(self.read_cmd, read_cmd_fifo.sink)
        ]

        # Cmd mux
        mux = Multiplexer(self.write_cmd.description, 2) # XXX
        self.submodules += mux
        self.comb += [
            mux.sel.eq(read_write_n.q),
            Record.connect(write_cmd_fifo.source, mux.sink0),
            Record.connect(read_cmd_fifo.source, mux.sink1)
        ]

        # Row tracking
        tracker = LiteDRAMRowTracker(sdram_module.geom_settings.rowbits)
        self.submodules += tracker

        write_available = Signal()
        write_hit = Signal()
        self.comb += [
            write_available.eq(write_cmd_fifo.source.stb),
            write_hit.eq(tracker.row_hit(write_cmd_fifo.source.row))
        ]

        read_available = Signal()
        read_hit = Signal()
        self.comb += [
            read_available.eq(read_cmd_fifo.source.stb),
            read_hit.eq(tracker.row_hit(read_cmd_fifo.source.row))
        ]

        # Respect write-to-precharge specification
        write2precharge_timer = WaitTimer(2 + sdram_module.timing_settings.tWR - 1)
        self.submodules += write2precharge_timer
        self.comb += write2precharge_timer.wait.eq(self.cmd.stb &
                                                   self.cmd.is_write &
                                                   self.cmd.ack)

        # Control and command generation FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(read_write_n.q,
                NextState("WRITE")
            ).Else(
                NextState("READ")
            )
        )
        fsm.act("WRITE",
            read_write_n.reset.eq(1),
            If(self.refresh.stb,
                NextState("REFRESH")
            ).Else(
                If(~write_available & read_available, # XXX add anti-starvation
                    NextState("READ")
                ).Else(
                    If(tracker.hasopenrow,
                        If(write_hit,
                            self.cmd.stb.eq(1),
                            self.cmd.is_write.eq(1),
                            self.cmd.cas_n.eq(0),
                            self.cmd.we_n.eq(0),
                            mux.source.ack.eq(self.cmd.ack)
                        ).Else(
                            NextState("PRECHARGE")
                        )
                    ).Else(
                        NextState("ACTIVATE")
                    )
                )
            )
        )
        fsm.act("READ",
            read_write_n.ce.eq(1),
            If(self.refresh.stb,
                NextState("REFRESH")
            ).Else(
                If(~read_available & write_available, # XXX add anti starvation
                    NextState("READ")
                ).Else(
                    If(tracker.hasopenrow,
                        If(read_hit,
                            self.cmd.stb.eq(1),
                            self.cmd.is_read.eq(1),
                            self.cmd.cas_n.eq(0),
                            self.cmd.we_n.eq(1),
                            mux.source.ack.eq(self.cmd.ack)
                        ).Else(
                            NextState("PRECHARGE")
                        )
                    ).Else(
                        NextState("ACTIVATE")
                    )
                )
            )
        )
        fsm.act("PRECHARGE",
            If(write2precharge_timer.done,
                self.cmd.stb.eq(1),
                self.cmd.is_cmd.eq(1),
                self.cmd.ras_n.eq(0),
                self.cmd.we_n.eq(0),
                self.cmd.adr.eq(mux.source.col),
                If(self.cmd.ack,
                    NextState("TRP")
                )
            )
        )
        fsm.act("ACTIVATE",
            tracker.open.eq(1),
            self.cmd.stb.eq(1),
            self.cmd.is_cmd.eq(1),
            self.cmd.ras_n.eq(0),
            self.cmd.adr.eq(mux.source.row),
            If(self.cmd.ack, NextState("TRCD"))
        )
        fsm.act("REFRESH",
            tracker.close.eq(1),
            self.cmd.is_cmd.eq(1),
            self.refresh.ack.eq(write2precharge_timer.done),
            If(~self.refresh.stb,
                NextState("IDLE")
            )
        )
        fsm.delayed_enter("TRP", "ACTIVATE", sdram_module.timing_settings.tRP-1)
        fsm.delayed_enter("TRCD", "IDLE", sdram_module.timing_settings.tRCD-1)
