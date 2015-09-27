from migen.fhdl.std import *
from migen.genlib.fsm import FSM, NextState
from migen.genlib.misc import optree, WaitTimer
from migen.actorlib.fifo import SyncFIFO
from migen.flow.plumbing import Multiplexer

from litedram.common import *


class LiteDRAMRowTracker(Module):
    def __init__(self, rowbits):
        self.row = Signal(rowbits)
        self.open = Signal()
        self.close = Signal()

        # # #

        self.hasopenrow = Signal()
        self._openrow = Signal(rowbits)
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
    def __init__(self, dram_module, cmd_fifo_depth):
        rowbits = dram_module.geom_settings.rowbits
        colbits = dram_module.geom_settings.colbits

        self.refresh = refresh = Sink(dram_refresh_description())
        self.write_cmd = write_cmd = Sink(dram_cmd_description(rowbits, colbits))
        self.read_cmd = read_cmd = Sink(dram_cmd_description(rowbits, colbits))
        self.cmd = cmd = Source(dram_bank_cmd_description(rowbits, colbits))

        # # #

        read_write_n = FlipFlop()
        self.comb += read_write_n.d.eq(1)
        self.submodules += read_write_n

        # Cmd fifos
        write_cmd_fifo = SyncFIFO(write_cmd.description, cmd_fifo_depth)
        read_cmd_fifo = SyncFIFO(read_cmd.description, cmd_fifo_depth)
        self.submodules += write_cmd_fifo, read_cmd_fifo
        self.comb += [
            Record.connect(write_cmd, write_cmd_fifo.sink),
            Record.connect(read_cmd, read_cmd_fifo.sink)
        ]

        # Cmd mux
        mux = Multiplexer(write_cmd.description, 2) # XXX
        self.submodules += mux
        self.comb += [
            mux.sel.eq(read_write_n.q),
            Record.connect(write_cmd_fifo.source, mux.sink0),
            Record.connect(read_cmd_fifo.source, mux.sink1)
        ]

        # Row tracking
        tracker = LiteDRAMRowTracker(dram_module.geom_settings.rowbits)
        self.submodules += tracker
        self.comb += tracker.row.eq(mux.source.row)

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
        write2precharge_timer = WaitTimer(2 + dram_module.timing_settings.tWR - 1)
        self.submodules += write2precharge_timer
        self.comb += write2precharge_timer.wait.eq(~(cmd.stb & cmd.write & cmd.ack))

        # Control and command generation FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(read_write_n.q,
                NextState("READ")
            ).Else(
                NextState("WRITE")
            )
        )
        fsm.act("WRITE",
            read_write_n.reset.eq(1),
            If(refresh.stb,
                NextState("REFRESH")
            ).Else(
                If(~write_available,
                    If(read_available, # XXX add anti-starvation
                        NextState("READ")
                    )
                ).Else(
                    If(tracker.hasopenrow,
                        If(write_hit,
                            cmd.stb.eq(1),
                            cmd.write.eq(1),
                            mux.source.ack.eq(cmd.ack)
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
            If(refresh.stb,
                NextState("REFRESH")
            ).Else(
                If(~read_available,
                    If(write_available, # XXX add anti starvation
                        NextState("WRITE")
                    )
                ).Else(
                    If(tracker.hasopenrow,
                        If(read_hit,
                            cmd.stb.eq(1),
                            cmd.read.eq(1),
                            mux.source.ack.eq(cmd.ack)
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
            cmd.precharge.eq(1),
            If(write2precharge_timer.done,
                cmd.stb.eq(1),
                If(cmd.ack,
                    NextState("TRP")
                )
            )
        )
        fsm.act("ACTIVATE",
            tracker.open.eq(1),
            cmd.stb.eq(1),
            cmd.activate.eq(1),
            If(cmd.ack,
                NextState("TRCD")
            )
        )
        fsm.act("REFRESH",
            tracker.close.eq(1),
            refresh.ack.eq(write2precharge_timer.done),
            If(~refresh.stb,
                NextState("IDLE")
            )
        )
        fsm.delayed_enter("TRP", "ACTIVATE", dram_module.timing_settings.tRP-1)
        fsm.delayed_enter("TRCD", "IDLE", dram_module.timing_settings.tRCD-1)
