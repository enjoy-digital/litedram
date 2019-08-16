# This file is Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# License: BSD

"""LiteDRAM Refresher."""

from migen import *
from migen.genlib.misc import timeline

from litex.soc.interconnect import stream

from litedram.core.multiplexer import *

# RefreshExecuter ----------------------------------------------------------------------------------

class RefreshExecuter(Module):
    """Refresh Executer

    Execute the refresh sequence to the DRAM:
    - Send a "Precharge All" command
    - Wait tRP
    - Send an "Auto Refresh" command
    - Wait rRFC
    """
    def __init__(self, cmd, trp, trfc):
        self.start = Signal()
        self.done  = Signal()

        # # #

        self.sync += [
            cmd.a.eq(2**10),
            cmd.ba.eq(0),
            cmd.cas.eq(0),
            cmd.ras.eq(0),
            cmd.we.eq(0),
        ]
        self.sync += [
            self.done.eq(0),
            # Wait start
            timeline(self.start, [
                # Precharge All
                (0,          [cmd.ras.eq(1), cmd.we.eq(1)]),
                # Auto Refresh after tRP
                (trp,        [cmd.cas.eq(1), cmd.ras.eq(1)]),
                # Done after tRP + tRFC
                (trp + trfc, [self.done.eq(1)])
            ])
        ]

# RefreshSequencer ---------------------------------------------------------------------------------

class RefreshSequencer(Module):
    """Refresh Sequencer

    Sequence N refreshs to the DRAM.
    """
    def __init__(self, cmd, trp, trfc, n=1):
        self.start = Signal()
        self.done  = Signal()

        # # #

        executer = RefreshExecuter(cmd, trp, trfc)
        self.submodules += executer

        count = Signal(bits_for(n), reset=n-1)
        self.sync += [
            If(self.start,
                count.eq(count.reset)
            ).Elif(executer.done,
                If(count != 0,
                    count.eq(count - 1)
                )
            )
        ]
        self.comb += executer.start.eq(self.start | (count != 0))
        self.comb += self.done.eq(executer.done & (count == 0))

# RefreshTimer -------------------------------------------------------------------------------------

class RefreshTimer(Module):
    """Refresh Timer

    Generate periodic pulses (tREFI period) to trigger DRAM refresh.
    """
    def __init__(self, trefi):
        self.wait  = Signal()
        self.done  = Signal()
        self.count = Signal(bits_for(trefi))

        # # #

        done  = Signal()
        count = Signal(bits_for(trefi), reset=trefi-1)

        self.sync += [
            If(self.wait & ~self.done,
                count.eq(count - 1)
            ).Else(
                count.eq(count.reset)
            )
        ]
        self.comb += [
            done.eq(count == 0),
            self.done.eq(done),
            self.count.eq(count)
        ]

# RefreshAccumulator -------------------------------------------------------------------------------

class RefreshAccumulator(Module):
    """Refresh Accumulator

    Accumulate N Refresh requests and generate a request when N is reached.
    """
    def __init__(self, n=1):
        self.req_i = Signal()
        self.req_o = Signal()

        # # #

        count = Signal(bits_for(n), reset=n-1)
        self.sync += [
            self.req_o.eq(0),
            If(self.req_i,
                count.eq(count - 1),
                If(count == 0,
                    count.eq(count.reset),
                    self.req_o.eq(1)
                )
            )
        ]

# Refresher ----------------------------------------------------------------------------------------

class Refresher(Module):
    """Refresher

    Manage DRAM refresh.

    The DRAM needs to be periodically refreshed with a tREFI period to avoid data corruption. During
    a refresh, the controller send a "Precharge All" command to close and precharge all rows and then
    send a "Auto Refresh" command.

    Before executing the refresh, the Refresher advertises the Controller that a refresh should occur,
    this allows the Controller to finish the current transaction and block next transactions. Once all
    transactions are done, the Refresher can execute the refresh Sequence and release the Controller.

    """
    def __init__(self, settings, n=1):
        abits  = settings.geom.addressbits
        babits = settings.geom.bankbits + log2_int(settings.phy.nranks)
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))

        # # #

        # Refresh Timer ----------------------------------------------------------------------------
        timer = RefreshTimer(settings.timing.tREFI)
        self.submodules.timer = timer
        self.comb += self.timer.wait.eq(~self.timer.done)

        # Refresh Accumulator ----------------------------------------------------------------------
        accum = RefreshAccumulator(n=n)
        self.submodules.accum = accum
        self.comb += accum.req_i.eq(self.timer.done)

        # Refresh Sequencer ------------------------------------------------------------------------
        sequencer = RefreshSequencer(cmd, settings.timing.tRP, settings.timing.tRFC, n=n)
        self.submodules.sequencer = sequencer

        # Refresh FSM ------------------------------------------------------------------------------
        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            If(settings.with_refresh,
                # Wait refresh accumulator
                If(accum.req_o,
                    NextState("WAIT-GRANT")
                )
            )
        )
        fsm.act("WAIT-GRANT",
            # Advertise Controller, wait grant and start Sequencer
            cmd.valid.eq(1),
            If(cmd.ready,
                sequencer.start.eq(1),
                NextState("WAIT-SEQUENCER")
            )
        )
        fsm.act("WAIT-SEQUENCER",
            # Wait Sequencer and advertise Controller when done
            cmd.valid.eq(1),
            If(sequencer.done,
                cmd.last.eq(1),
                NextState("IDLE")
            )
        )
