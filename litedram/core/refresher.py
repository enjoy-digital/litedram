#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# SPDX-License-Identifier: BSD-2-Clause

"""LiteDRAM Refresher."""

from migen import *
from migen.genlib.misc import timeline

from litex.soc.interconnect import stream

from litedram.common import *
from litedram.core.multiplexer import *

# RefreshExecuter ----------------------------------------------------------------------------------

class RefreshExecuter(Module):
    """Refresh Executer

    Execute the refresh sequence to the DRAM:
    - Send a "Precharge All" command
    - Wait tRP
    - Send an "Auto Refresh" command
    - Wait tRFC
    """
    def __init__(self, cmd, trp, trfc):
        self.start = Signal()
        self.done  = Signal()

        # # #

        self.sync += [
            cmd.a.eq(  0),
            cmd.ba.eq( 0),
            cmd.cas.eq(0),
            cmd.ras.eq(0),
            cmd.we.eq( 0),
            self.done.eq(0),
            # Wait start
            timeline(self.start, [
                # Precharge All
                (0, [
                    cmd.a.eq(  2**10),
                    cmd.ba.eq( 0),
                    cmd.cas.eq(0),
                    cmd.ras.eq(1),
                    cmd.we.eq( 1)
                ]),
                # Auto Refresh after tRP
                (trp, [
                    cmd.a.eq(  2**10),  # all banks in LPDDR4/DDR5, ignored in other memories
                    cmd.ba.eq( 0),
                    cmd.cas.eq(1),
                    cmd.ras.eq(1),
                    cmd.we.eq( 0),
                ]),
                # Done after tRP + tRFC
                (trp + trfc, [
                    cmd.a.eq(  0),
                    cmd.ba.eq( 0),
                    cmd.cas.eq(0),
                    cmd.ras.eq(0),
                    cmd.we.eq( 0),
                    self.done.eq(1),
                ]),
            ])
        ]

# RefreshSequencer ---------------------------------------------------------------------------------

class RefreshSequencer(Module):
    """Refresh Sequencer

    Sequence N refreshs to the DRAM.
    """
    def __init__(self, cmd, trp, trfc, postponing=1):
        self.start = Signal()
        self.done  = Signal()

        # # #

        executer = RefreshExecuter(cmd, trp, trfc)
        self.submodules += executer

        count = Signal(bits_for(postponing), reset=postponing-1)
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

# RefreshPostponer -------------------------------------------------------------------------------

class RefreshPostponer(Module):
    """Refresh Postponer

    Postpone N Refresh requests and generate a request when N is reached.
    """
    def __init__(self, postponing=1):
        self.req_i = Signal()
        self.req_o = Signal()

        # # #

        count = Signal(bits_for(postponing), reset=postponing-1)
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

# ZQCSExecuter ----------------------------------------------------------------------------------

class ZQCSExecuter(Module):
    """ZQ Short Calibration Executer

    Execute the ZQCS sequence to the DRAM:
    - Send a "Precharge All" command
    - Wait tRP
    - Send an "ZQ Short Calibration" command
    - Wait tZQCS
    """
    def __init__(self, cmd, trp, tzqcs):
        self.start = Signal()
        self.done  = Signal()

        # # #

        self.sync += [
            # Note: Don't set cmd to 0 since already done in RefreshExecuter
            self.done.eq(0),
            # Wait start
            timeline(self.start, [
                # Precharge All
                (0, [
                    cmd.a.eq(  2**10),
                    cmd.ba.eq( 0),
                    cmd.cas.eq(0),
                    cmd.ras.eq(1),
                    cmd.we.eq( 1)
                ]),
                # ZQ Short Calibration after tRP
                (trp, [
                    cmd.a.eq(  0),
                    cmd.ba.eq( 0),
                    cmd.cas.eq(0),
                    cmd.ras.eq(0),
                    cmd.we.eq( 1),
                ]),
                # Done after tRP + tZQCS
                (trp + tzqcs, [
                    cmd.a.eq(  0),
                    cmd.ba.eq( 0),
                    cmd.cas.eq(0),
                    cmd.ras.eq(0),
                    cmd.we.eq( 0),
                    self.done.eq(1)
                ]),
            ])
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
    def __init__(self, settings, clk_freq, zqcs_freq=1e0, postponing=1):
        assert postponing <= 8
        abits  = settings.geom.addressbits
        babits = settings.geom.bankbits + log2_int(settings.phy.nranks)
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))
        self.TMRcmd = TMRcmd = TMRRecord(cmd)

        # # #
        
        # TMR Setup
        
        self.submodules += TMROutput(cmd.valid, TMRcmd.valid)
        self.submodules += TMROutput(cmd.last, TMRcmd.last)
        self.submodules += TMROutput(cmd.first, TMRcmd.first)
        self.submodules += TMRInput(TMRcmd.ready, cmd.ready)
        self.submodules += TMROutput(cmd.a, TMRcmd.a)
        self.submodules += TMROutput(cmd.ba, TMRcmd.ba)
        self.submodules += TMROutput(cmd.cas, TMRcmd.cas)
        self.submodules += TMROutput(cmd.ras, TMRcmd.ras)
        self.submodules += TMROutput(cmd.we, TMRcmd.we)
        self.submodules += TMROutput(cmd.is_cmd, TMRcmd.is_cmd)
        self.submodules += TMROutput(cmd.is_read, TMRcmd.is_read)
        self.submodules += TMROutput(cmd.is_write, TMRcmd.is_write)

        wants_refresh = Signal()
        wants_zqcs    = Signal()

        # Refresh Timer ----------------------------------------------------------------------------
        if settings.timing.tREFI < 100: # FIXME: Reduce Margin.
            raise ValueError("Clk/tREFI is ratio too low , please increase Clk frequency or disable Refresh.")
        timer = RefreshTimer(settings.timing.tREFI)
        self.submodules.timer = timer
        self.comb += timer.wait.eq(~timer.done)
            
        # Refresh Postponer ------------------------------------------------------------------------
        postponer = RefreshPostponer(postponing)
        self.submodules.postponer = postponer
        self.comb += postponer.req_i.eq(self.timer.done)
        self.comb += wants_refresh.eq(postponer.req_o)

        # Refresh Sequencer ------------------------------------------------------------------------
        sequencer = RefreshSequencer(cmd, settings.timing.tRP, settings.timing.tRFC, postponing)
        self.submodules.sequencer = sequencer

        if settings.timing.tZQCS is not None:
            # ZQCS Timer ---------------------------------------------------------------------------
            zqcs_timer = RefreshTimer(int(clk_freq/zqcs_freq))
            self.submodules.zqcs_timer = zqcs_timer
            self.comb += wants_zqcs.eq(zqcs_timer.done)

            # ZQCS Executer ------------------------------------------------------------------------
            zqcs_executer = ZQCSExecuter(cmd, settings.timing.tRP, settings.timing.tZQCS)
            self.submodules.zqs_executer = zqcs_executer
            self.comb += zqcs_timer.wait.eq(~zqcs_executer.done)

        # Refresh FSM ------------------------------------------------------------------------------
        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            If(settings.with_refresh,
                If(wants_refresh,
                    NextState("WAIT-BANK-MACHINES")
                )
            )
        )
        fsm.act("WAIT-BANK-MACHINES",
            cmd.valid.eq(1),
            If(cmd.ready,
                sequencer.start.eq(1),
                NextState("DO-REFRESH")
            )
        )
        if settings.timing.tZQCS is None:
            fsm.act("DO-REFRESH",
                cmd.valid.eq(1),
                If(sequencer.done,
                    cmd.valid.eq(0),
                    cmd.last.eq(1),
                    NextState("IDLE")
                )
            )
        else:
            fsm.act("DO-REFRESH",
                cmd.valid.eq(1),
                If(sequencer.done,
                    If(wants_zqcs,
                        zqcs_executer.start.eq(1),
                        NextState("DO-ZQCS")
                    ).Else(
                        cmd.valid.eq(0),
                        cmd.last.eq(1),
                        NextState("IDLE")
                    )
                )
            )
            fsm.act("DO-ZQCS",
                cmd.valid.eq(1),
                If(zqcs_executer.done,
                    cmd.valid.eq(0),
                    cmd.last.eq(1),
                    NextState("IDLE")
                )
            )

class TMRRefresher(Module):
    def __init__(self, settings, clk_freq, zqcs_freq=1e0, postponing=1):
        assert postponing <= 8
        abits  = settings.geom.addressbits
        babits = settings.geom.bankbits + log2_int(settings.phy.nranks)
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))
        self.TMRcmd = TMRcmd = TMRRecord(cmd)

        # # #
        
        # TMR Setup
        
        self.submodules += TMROutput(cmd.valid, TMRcmd.valid)
        self.submodules += TMROutput(cmd.last, TMRcmd.last)
        self.submodules += TMROutput(cmd.first, TMRcmd.first)
        self.submodules += TMRInput(TMRcmd.ready, cmd.ready)
        self.submodules += TMROutput(cmd.a, TMRcmd.a)
        self.submodules += TMROutput(cmd.ba, TMRcmd.ba)
        self.submodules += TMROutput(cmd.cas, TMRcmd.cas)
        self.submodules += TMROutput(cmd.ras, TMRcmd.ras)
        self.submodules += TMROutput(cmd.we, TMRcmd.we)
        self.submodules += TMROutput(cmd.is_cmd, TMRcmd.is_cmd)
        self.submodules += TMROutput(cmd.is_read, TMRcmd.is_read)
        self.submodules += TMROutput(cmd.is_write, TMRcmd.is_write)

        wants_refresh = Signal()
        wants_zqcs    = Signal()

        # Refresh Timer ----------------------------------------------------------------------------
        timer = RefreshTimer(settings.timing.tREFI)
        self.submodules.timer = timer
        self.comb += timer.wait.eq(~timer.done)
        
        timer2 = RefreshTimer(settings.timing.tREFI)
        self.submodules.timer2 = timer2
        self.comb += timer2.wait.eq(~timer2.done)
        
        timer3 = RefreshTimer(settings.timing.tREFI)
        self.submodules.timer3 = timer3
        self.comb += timer3.wait.eq(~timer3.done)
        
        timerSigs = Cat(timer.done, timer2.done, timer3.done)
        timerVote = TMRInput(timerSigs)
        self.submodules += timerVote
            
        # Refresh Postponer ------------------------------------------------------------------------
        postponer = RefreshPostponer(postponing)
        self.submodules.postponer = postponer
        self.comb += postponer.req_i.eq(timerVote.control)
        
        postponer2 = RefreshPostponer(postponing)
        self.submodules.postponer2 = postponer2
        self.comb += postponer2.req_i.eq(timerVote.control)
        
        postponer3 = RefreshPostponer(postponing)
        self.submodules.postponer3 = postponer3
        self.comb += postponer3.req_i.eq(timerVote.control)
        
        postponeSigs = Cat(postponer.req_o, postponer2.req_o, postponer3.req_o)
        postponeVote = TMRInput(postponeSigs)
        self.submodules += postponeVote
        self.comb += wants_refresh.eq(postponeVote.control)

        # Refresh Sequencer ------------------------------------------------------------------------
        self.cmd1 = cmd1 = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))
        sequencer = RefreshSequencer(cmd1, settings.timing.tRP, settings.timing.tRFC, postponing)
        self.submodules.sequencer = sequencer
        
        self.cmd2 = cmd2 = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))
        sequencer2 = RefreshSequencer(cmd2, settings.timing.tRP, settings.timing.tRFC, postponing)
        self.submodules.sequencer2 = sequencer2
        
        self.cmd3 = cmd3 = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))
        sequencer3 = RefreshSequencer(cmd3, settings.timing.tRP, settings.timing.tRFC, postponing)
        self.submodules.sequencer3 = sequencer3
        
        def vote_sync(signame):
            sig = Cat(getattr(cmd1,signame), getattr(cmd2,signame), getattr(cmd3,signame))
            vote = TMRInput(sig)
            self.sync += getattr(cmd,signame).eq(vote.control)
        
        vote_sync('valid')
        vote_sync('last')
        vote_sync('first')
        vote_sync('a')
        vote_sync('ba')
        vote_sync('cas')
        vote_sync('ras')
        vote_sync('we')
        vote_sync('is_cmd')
        vote_sync('is_read')
        vote_sync('is_write')
        
        self.sync += [self.cmd1.ready.eq(cmd.ready), self.cmd2.ready.eq(cmd.ready), self.cmd3.ready.eq(cmd.ready)]
        
        sequenceSigs = Cat(sequencer.done, sequencer2.done, sequencer3.done)
        sequenceVote = TMRInput(sequenceSigs)
        self.submodules += sequenceVote

        if settings.timing.tZQCS is not None:
            # ZQCS Timer ---------------------------------------------------------------------------
            zqcs_timer = RefreshTimer(int(clk_freq/zqcs_freq))
            self.submodules.zqcs_timer = zqcs_timer
            self.comb += wants_zqcs.eq(zqcs_timer.done)

            # ZQCS Executer ------------------------------------------------------------------------
            zqcs_executer = ZQCSExecuter(cmd, settings.timing.tRP, settings.timing.tZQCS)
            self.submodules.zqs_executer = zqcs_executer
            self.comb += zqcs_timer.wait.eq(~zqcs_executer.done)

        # Refresh FSM ------------------------------------------------------------------------------
        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            If(settings.with_refresh,
                If(wants_refresh,
                    NextState("WAIT-BANK-MACHINES")
                )
            )
        )
        fsm.act("WAIT-BANK-MACHINES",
            cmd.valid.eq(1),
            If(cmd.ready,
                sequencer.start.eq(1),
                sequencer2.start.eq(1),
                sequencer3.start.eq(1),
                NextState("DO-REFRESH")
            )
        )
        if settings.timing.tZQCS is None:
            fsm.act("DO-REFRESH",
                cmd.valid.eq(1),
                If(sequenceVote.control,
                    cmd.valid.eq(0),
                    cmd.last.eq(1),
                    NextState("IDLE")
                )
            )
        else:
            fsm.act("DO-REFRESH",
                cmd.valid.eq(1),
                If(sequenceVote.control,
                    If(wants_zqcs,
                        zqcs_executer.start.eq(1),
                        NextState("DO-ZQCS")
                    ).Else(
                        cmd.valid.eq(0),
                        cmd.last.eq(1),
                        NextState("IDLE")
                    )
                )
            )
            fsm.act("DO-ZQCS",
                cmd.valid.eq(1),
                If(zqcs_executer.done,
                    cmd.valid.eq(0),
                    cmd.last.eq(1),
                    NextState("IDLE")
                )
            )