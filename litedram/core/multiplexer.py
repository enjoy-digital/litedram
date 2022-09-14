#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2018 John Sully <john@csquare.ca>
# SPDX-License-Identifier: BSD-2-Clause

"""LiteDRAM Multiplexer."""

import math
from functools import reduce
from operator import or_, and_

from migen import *
from migen.genlib.roundrobin import *
from migen.genlib.coding import Decoder

from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import AutoCSR

from litedram.common import *
from litedram.core.bandwidth import Bandwidth

# _CommandChooser ----------------------------------------------------------------------------------

class _CommandChooser(Module):
    """Arbitrates between requests, filtering them based on their type

    Uses RoundRobin to choose current request, filters requests based on
    `want_*` signals.

    Parameters
    ----------
    requests : [Endpoint(cmd_request_rw_layout), ...]
        Request streams to consider for arbitration

    Attributes
    ----------
    want_reads : Signal, in
        Consider read requests
    want_writes : Signal, in
        Consider write requests
    want_cmds : Signal, in
        Consider command requests (without ACT)
    want_activates : Signal, in
        Also consider ACT commands
    cmd : Endpoint(cmd_request_rw_layout)
        Currently selected request stream (when ~cmd.valid, cas/ras/we are 0)
    """
    def __init__(self, requests):
        self.want_reads     = Signal()
        self.want_writes    = Signal()
        self.want_cmds      = Signal()
        self.want_activates = Signal()

        a  = len(requests[0].a)
        ba = len(requests[0].ba)

        # cas/ras/we are 0 when valid is inactive
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(a, ba))

        # # #

        n = len(requests)

        valids = Signal(n)
        for i, request in enumerate(requests):
            is_act_cmd = request.ras & ~request.cas & ~request.we
            command = request.is_cmd & self.want_cmds & (~is_act_cmd | self.want_activates)
            read = request.is_read == self.want_reads
            write = request.is_write == self.want_writes
            self.comb += valids[i].eq(request.valid & (command | (read & write)))


        arbiter = RoundRobin(n, SP_CE)
        self.submodules += arbiter
        choices = Array(valids[i] for i in range(n))
        self.comb += [
            arbiter.request.eq(valids),
            cmd.valid.eq(choices[arbiter.grant])
        ]

        for name in ["a", "ba", "is_read", "is_write", "is_cmd"]:
            choices = Array(getattr(req, name) for req in requests)
            self.comb += getattr(cmd, name).eq(choices[arbiter.grant])

        for name in ["cas", "ras", "we"]:
            # we should only assert those signals when valid is 1
            choices = Array(getattr(req, name) for req in requests)
            self.comb += \
                If(cmd.valid,
                    getattr(cmd, name).eq(choices[arbiter.grant])
                )

        for i, request in enumerate(requests):
            self.comb += \
                If(cmd.valid & cmd.ready & (arbiter.grant == i),
                    request.ready.eq(1)
                )
        # Arbitrate if a command is being accepted or if the command is not valid to ensure a valid
        # command is selected when cmd.ready goes high.
        self.comb += arbiter.ce.eq(cmd.ready | ~cmd.valid)

    # helpers
    def accept(self):
        return self.cmd.valid & self.cmd.ready

    def activate(self):
        return self.cmd.ras & ~self.cmd.cas & ~self.cmd.we

    def write(self):
        return self.cmd.is_write

    def read(self):
        return self.cmd.is_read

class _CommandChooserInt(Module):
    """
    Arbitrates between requests, filtering them based on their type

    Uses RoundRobin to choose current request, filters requests based on
    `want_*` signals.

    Attributes
    ----------
    requests : [Endpoint(cmd_request_rw_layout), ...]
        Request streams to consider for arbitration
    cmd : Endpoint(cmd_request_rw_layout)
        Currently selected request stream (when ~cmd.valid, cas/ras/we are 0)
    want_reads : Signal, in
        Consider read requests
    want_writes : Signal, in
        Consider write requests
    want_cmds : Signal, in
        Consider command requests (without ACT)
    want_activates : Signal, in
        Also consider ACT commands
    """
    def __init__(self, nreqs, a, ba):
        self.requests = requests = [stream.Endpoint(cmd_request_rw_layout(a, ba)) for n in range(nreqs)]
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(a, ba))
        
        self.want_reads     = Signal()
        self.want_writes    = Signal()
        self.want_cmds      = Signal()
        self.want_activates = Signal()

        # # #

        # Find valid requests
        valids = Signal(nreqs)
        for i, request in enumerate(requests):
            is_act_cmd = request.ras & ~request.cas & ~request.we
            command = request.is_cmd & self.want_cmds & (~is_act_cmd | self.want_activates)
            read = request.is_read == self.want_reads
            write = request.is_write == self.want_writes
            self.comb += valids[i].eq(request.valid & (command | (read & write)))

        # Create arbiters
        arbiter = RoundRobin(nreqs, SP_CE)
        self.submodules += arbiter
        choices = Array(valids[i] for i in range(nreqs))
        self.comb += [
            arbiter.request.eq(valids),
            cmd.valid.eq(choices[arbiter.grant])
        ]

        # Connect arbiter selection to cmd
        for name in ["a", "ba", "is_read", "is_write", "is_cmd"]:
            choices = Array(getattr(req, name) for req in requests)
            self.comb += getattr(cmd, name).eq(choices[arbiter.grant])

        for name in ["cas", "ras", "we"]:
            # we should only assert those signals when valid is 1
            choices = Array(getattr(req, name) for req in requests)
            self.comb += \
                If(cmd.valid,
                    getattr(cmd, name).eq(choices[arbiter.grant])
                )

        # Connect arbiter selection to req.ready
        for i, request in enumerate(requests):
            self.comb += \
                If(cmd.valid & cmd.ready & (arbiter.grant == i),
                    request.ready.eq(1)
                )
                
        # Arbitrate if a command is being accepted or if the command is not valid to ensure a valid
        # command is selected when cmd.ready goes high.
        self.comb += arbiter.ce.eq(cmd.ready | ~cmd.valid)

    # helpers
    def accept(self):
        return self.cmd.valid & self.cmd.ready

    def activate(self):
        return self.cmd.ras & ~self.cmd.cas & ~self.cmd.we

    def write(self):
        return self.cmd.is_write

    def read(self):
        return self.cmd.is_read

# _Steerer -----------------------------------------------------------------------------------------

(STEER_NOP, STEER_CMD, STEER_REQ, STEER_REFRESH) = range(4)

class _Steerer(Module):
    """Connects selected request to DFI interface

    cas/ras/we/is_write/is_read are connected only when `cmd.valid & cmd.ready`.
    Rank bits are decoded and used to drive cs_n in multi-rank systems,
    STEER_REFRESH always enables all ranks.

    Parameters
    ----------
    commands : [Endpoint(cmd_request_rw_layout), ...]
        Command streams to choose from. Must be of len=4 in the order:
            NOP, CMD, REQ, REFRESH
        NOP can be of type Record(cmd_request_rw_layout) instead, so that it is
        always considered invalid (because of lack of the `valid` attribute).
    dfi : dfi.Interface
        DFI interface connected to PHY

    Attributes
    ----------
    sel : [Signal(max=len(commands)), ...], in
        Signals for selecting which request gets connected to the corresponding
        DFI phase. The signals should take one of the values from STEER_* to
        select given source.
    """
    def __init__(self, commands, dfi):
        ncmd = len(commands)
        nph  = len(dfi.phases)
        self.sel = [Signal(max=ncmd) for i in range(nph)]

        # # #

        def valid_and(cmd, attr):
            if not hasattr(cmd, "valid"):
                return 0
            else:
                return cmd.valid & cmd.ready & getattr(cmd, attr)

        for i, (phase, sel) in enumerate(zip(dfi.phases, self.sel)):
            nranks   = len(phase.cs_n)
            rankbits = log2_int(nranks)
            if hasattr(phase, "reset_n"):
                self.comb += phase.reset_n.eq(1)
            self.comb += phase.cke.eq(Replicate(Signal(reset=1), nranks))
            if hasattr(phase, "odt"):
                # FIXME: add dynamic drive for multi-rank (will be needed for high frequencies)
                self.comb += phase.odt.eq(Replicate(Signal(reset=1), nranks))
            if rankbits:
                rank_decoder = Decoder(nranks)
                self.submodules += rank_decoder
                self.comb += rank_decoder.i.eq((Array(cmd.ba[-rankbits:] for cmd in commands)[sel]))
                if i == 0: # Select all ranks on refresh.
                    self.sync += If(sel == STEER_REFRESH, phase.cs_n.eq(0)).Else(phase.cs_n.eq(~rank_decoder.o))
                else:
                    self.sync += phase.cs_n.eq(~rank_decoder.o)
                self.sync += phase.bank.eq(Array(cmd.ba[:-rankbits] for cmd in commands)[sel])
            else:
                self.sync += phase.cs_n.eq(0)
                self.sync += phase.bank.eq(Array(cmd.ba[:] for cmd in commands)[sel])

            self.sync += [
                phase.address.eq(Array(cmd.a for cmd in commands)[sel]),
                phase.cas_n.eq(~Array(valid_and(cmd, "cas") for cmd in commands)[sel]),
                phase.ras_n.eq(~Array(valid_and(cmd, "ras") for cmd in commands)[sel]),
                phase.we_n.eq(~Array(valid_and(cmd, "we") for cmd in commands)[sel])
            ]

            rddata_ens = Array(valid_and(cmd, "is_read") for cmd in commands)
            wrdata_ens = Array(valid_and(cmd, "is_write") for cmd in commands)
            self.sync += [
                phase.rddata_en.eq(rddata_ens[sel]),
                phase.wrdata_en.eq(wrdata_ens[sel])
            ]

class _SteererInt(Module):
    """
    Connects selected request to DFI interface

    cas/ras/we/is_write/is_read are connected only when `cmd.valid & cmd.ready`.
    Rank bits are decoded and used to drive cs_n in multi-rank systems,
    STEER_REFRESH always enables all ranks.

    Attributes
    ----------
    commands : [Endpoint(cmd_request_rw_layout), ...]
        Command streams to choose from. Must be of len=4 in the order:
            NOP, CMD, REQ, REFRESH
        NOP can be of type Record(cmd_request_rw_layout) instead, so that it is
        always considered invalid (because of lack of the `valid` attribute).
    dfi : dfi.Interface
        DFI interface connected to PHY
    sel : [Signal(max=len(commands)), ...], in
        Signals for selecting which request gets connected to the corresponding
        DFI phase. The signals should take one of the values from STEER_* to
        select given source.
    """
    def __init__(self, a, ba, nranks, databits, nphases):        
        self.sel = [Signal(max=ncmd) for i in range(nph)]
        self.commands = [stream.Endpoint(cmd_request_rw_layout(a, ba)) for n in range(4)]
        self.dfi = dfi.Interface(a, ba, nranks, databits, nphases)

        # # #

        def valid_and(cmd, attr):
            if not hasattr(cmd, "valid"):
                return 0
            else:
                return cmd.valid & cmd.ready & getattr(cmd, attr)

        for i, (phase, sel) in enumerate(zip(dfi.phases, self.sel)):
            rankbits = log2_int(nranks)
            
            if hasattr(phase, "reset_n"):
                self.comb += phase.reset_n.eq(1)
            self.comb += phase.cke.eq(Replicate(Signal(reset=1), nranks))
            
            if hasattr(phase, "odt"):
                # FIXME: add dynamic drive for multi-rank (will be needed for high frequencies)
                self.comb += phase.odt.eq(Replicate(Signal(reset=1), nranks))
            
            if rankbits:
                rank_decoder = Decoder(nranks)
                self.submodules += rank_decoder
                self.comb += rank_decoder.i.eq((Array(cmd.ba[-rankbits:] for cmd in commands)[sel]))
                if i == 0: # Select all ranks on refresh.
                    self.sync += If(sel == STEER_REFRESH, phase.cs_n.eq(0)).Else(phase.cs_n.eq(~rank_decoder.o))
                else:
                    self.sync += phase.cs_n.eq(~rank_decoder.o)
                self.sync += phase.bank.eq(Array(cmd.ba[:-rankbits] for cmd in commands)[sel])
            else:
                self.sync += phase.cs_n.eq(0)
                self.sync += phase.bank.eq(Array(cmd.ba[:] for cmd in commands)[sel])

            # Connect selection to dfi
            self.sync += [
                phase.address.eq(Array(cmd.a for cmd in commands)[sel]),
                phase.cas_n.eq(~Array(valid_and(cmd, "cas") for cmd in commands)[sel]),
                phase.ras_n.eq(~Array(valid_and(cmd, "ras") for cmd in commands)[sel]),
                phase.we_n.eq(~Array(valid_and(cmd, "we") for cmd in commands)[sel])
            ]

            rddata_ens = Array(valid_and(cmd, "is_read") for cmd in commands)
            wrdata_ens = Array(valid_and(cmd, "is_write") for cmd in commands)
            self.sync += [
                phase.rddata_en.eq(rddata_ens[sel]),
                phase.wrdata_en.eq(wrdata_ens[sel])
            ]

# Multiplexer --------------------------------------------------------------------------------------

class Multiplexer(Module, AutoCSR):
    """Multplexes requets from BankMachines to DFI

    This module multiplexes requests from BankMachines (and Refresher) and
    connects them to DFI. Refresh commands are coordinated between the Refresher
    and BankMachines to ensure there are no conflicts. Enforces required timings
    between commands (some timings are enforced by BankMachines).

    Parameters
    ----------
    settings : ControllerSettings
        Controller settings (with .phy, .geom and .timing settings)
    bank_machines : [BankMachine, ...]
        Bank machines that generate command requests to the Multiplexer
    refresher : Refresher
        Generates REFRESH command requests
    dfi : dfi.Interface
        DFI connected to the PHY
    interface : LiteDRAMInterface
        Data interface connected directly to LiteDRAMCrossbar
    """
    def __init__(self,
            settings,
            bank_machines,
            refresher,
            dfi,
            interface,
            TMRinterface):
        assert(settings.phy.nphases == len(dfi.phases))

        ras_allowed = Signal(reset=1)
        cas_allowed = Signal(reset=1)
        
        self.TMRinterface = TMRinterface
        self.dfi = dfi

        # Read/Write Cmd/Dat phases ----------------------------------------------------------------
        nphases = settings.phy.nphases
        rdphase = settings.phy.rdphase
        wrphase = settings.phy.wrphase
        if isinstance(rdphase, Signal):
            rdcmdphase = Signal.like(rdphase)
            self.comb += rdcmdphase.eq(rdphase - 1) # Implicit %nphases.
        else:
            rdcmdphase = (rdphase - 1)%nphases
        if isinstance(rdphase, Signal):
            wrcmdphase = Signal.like(wrphase)
            self.comb += wrcmdphase.eq(wrphase - 1) # Implicit %nphases.
        else:
            wrcmdphase = (wrphase - 1)%nphases

        # Command choosing -------------------------------------------------------------------------
        
        #Create cmd's from TMRcmd's
        requests = [bm.cmd for bm in bank_machines]
        
        TMRrequests = [stream.Endpoint(cmd_request_rw_layout(settings.geom.addressbits, settings.geom.bankbits + log2_int(settings.phy.nranks))) for bm in bank_machines]
        
        for TMRrequest, bm in zip(TMRrequests, bank_machines):
            self.submodules += TMRInput(bm.TMRcmd.valid, TMRrequest.valid)
            self.submodules += TMRInput(bm.TMRcmd.last, TMRrequest.last)
            self.submodules += TMROutput(TMRrequest.ready, bm.TMRcmd.ready)
            self.submodules += TMRInput(bm.TMRcmd.first, TMRrequest.first)
            self.submodules += TMRInput(bm.TMRcmd.a, TMRrequest.a)
            self.submodules += TMRInput(bm.TMRcmd.ba, TMRrequest.ba)
            self.submodules += TMRInput(bm.TMRcmd.cas, TMRrequest.cas)
            self.submodules += TMRInput(bm.TMRcmd.ras, TMRrequest.ras)
            self.submodules += TMRInput(bm.TMRcmd.we, TMRrequest.we)
            self.submodules += TMRInput(bm.TMRcmd.is_cmd, TMRrequest.is_cmd)
            self.submodules += TMRInput(bm.TMRcmd.is_read, TMRrequest.is_read)
            self.submodules += TMRInput(bm.TMRcmd.is_write, TMRrequest.is_write)
        
        self.submodules.choose_cmd = choose_cmd = _CommandChooser(TMRrequests)
        self.submodules.choose_req = choose_req = _CommandChooser(TMRrequests)
        if settings.phy.nphases == 1:
            # When only 1 phase, use choose_req for all requests
            choose_cmd = choose_req
            self.comb += choose_req.want_cmds.eq(1)
            self.comb += choose_req.want_activates.eq(ras_allowed)
            
        # Refresher cmd
        
        refreshCmd = stream.Endpoint(cmd_request_rw_layout(settings.geom.addressbits, settings.geom.bankbits + log2_int(settings.phy.nranks)))
        
        self.submodules += TMRInput(refresher.TMRcmd.valid, refreshCmd.valid)
        self.submodules += TMRInput(refresher.TMRcmd.last, refreshCmd.last)
        self.submodules += TMROutput(refreshCmd.ready, refresher.TMRcmd.ready)
        self.submodules += TMRInput(refresher.TMRcmd.first, refreshCmd.first)
        self.submodules += TMRInput(refresher.TMRcmd.a, refreshCmd.a)
        self.submodules += TMRInput(refresher.TMRcmd.ba, refreshCmd.ba)
        self.submodules += TMRInput(refresher.TMRcmd.cas, refreshCmd.cas)
        self.submodules += TMRInput(refresher.TMRcmd.ras, refreshCmd.ras)
        self.submodules += TMRInput(refresher.TMRcmd.we, refreshCmd.we)
        self.submodules += TMRInput(refresher.TMRcmd.is_cmd, refreshCmd.is_cmd)
        self.submodules += TMRInput(refresher.TMRcmd.is_read, refreshCmd.is_read)
        self.submodules += TMRInput(refresher.TMRcmd.is_write, refreshCmd.is_write)

        # Command steering -------------------------------------------------------------------------
        nop = Record(cmd_request_layout(settings.geom.addressbits,
                                        log2_int(len(bank_machines))))
        # nop must be 1st
        commands = [nop, choose_cmd.cmd, choose_req.cmd, refreshCmd]
        steerer = _Steerer(commands, dfi)
        self.submodules += steerer

        # tRRD timing (Row to Row delay) -----------------------------------------------------------
        self.submodules.trrdcon = trrdcon = tXXDController(settings.timing.tRRD)
        self.comb += trrdcon.valid.eq(choose_cmd.accept() & choose_cmd.activate())

        # tFAW timing (Four Activate Window) -------------------------------------------------------
        self.submodules.tfawcon = tfawcon = tFAWController(settings.timing.tFAW)
        self.comb += tfawcon.valid.eq(choose_cmd.accept() & choose_cmd.activate())

        # RAS control ------------------------------------------------------------------------------
        self.comb += ras_allowed.eq(trrdcon.ready & tfawcon.ready)

        # tCCD timing (Column to Column delay) -----------------------------------------------------
        self.submodules.tccdcon = tccdcon = tXXDController(settings.timing.tCCD)
        self.comb += tccdcon.valid.eq(choose_req.accept() & (choose_req.write() | choose_req.read()))

        # CAS control ------------------------------------------------------------------------------
        self.comb += cas_allowed.eq(tccdcon.ready)

        # tWTR timing (Write to Read delay) --------------------------------------------------------
        write_latency = math.ceil(settings.phy.cwl / settings.phy.nphases)
        self.submodules.twtrcon = twtrcon = tXXDController(
            settings.timing.tWTR + write_latency +
            # tCCD must be added since tWTR begins after the transfer is complete
            settings.timing.tCCD if settings.timing.tCCD is not None else 0)
        self.comb += twtrcon.valid.eq(choose_req.accept() & choose_req.write())

        # Read/write turnaround --------------------------------------------------------------------
        read_available = Signal()
        write_available = Signal()
        reads = [req.valid & req.is_read for req in requests]
        writes = [req.valid & req.is_write for req in requests]
        self.comb += [
            read_available.eq(reduce(or_, reads)),
            write_available.eq(reduce(or_, writes))
        ]

        # Anti Starvation --------------------------------------------------------------------------

        def anti_starvation(timeout):
            en = Signal()
            max_time = Signal()
            if timeout:
                t = timeout - 1
                time = Signal(max=t+1)
                self.comb += max_time.eq(time == 0)
                self.sync += If(~en,
                        time.eq(t)
                    ).Elif(~max_time,
                        time.eq(time - 1)
                    )
            else:
                self.comb += max_time.eq(0)
            return en, max_time

        read_time_en,   max_read_time = anti_starvation(settings.read_time)
        write_time_en, max_write_time = anti_starvation(settings.write_time)

        # Refresh ----------------------------------------------------------------------------------
        self.comb += [bm.refresh_req.eq(refreshCmd.valid) for bm in bank_machines]
        go_to_refresh = Signal()
        bm_refresh_gnts = [bm.refresh_gnt for bm in bank_machines]
        self.comb += go_to_refresh.eq(reduce(and_, bm_refresh_gnts))

        # Datapath ---------------------------------------------------------------------------------
        all_rddata = [p.rddata for p in dfi.phases]
        all_wrdata = [p.wrdata for p in dfi.phases]
        all_wrdata_mask = [p.wrdata_mask for p in dfi.phases]
        #self.comb += [
        #    interface.rdata.eq(Cat(*all_rddata)),
        #    Cat(*all_wrdata).eq(interface.wdata),
        #    Cat(*all_wrdata_mask).eq(~interface.wdata_we)
        #]
        
        self.submodules += TMROutput(Cat(*all_rddata), TMRinterface.rdata)
        self.submodules += TMRInput(TMRinterface.wdata, Cat(*all_wrdata))
        self.submodules += TMRInput(~TMRinterface.wdata_we, Cat(*all_wrdata_mask))

        def steerer_sel(steerer, access):
            assert access in ["read", "write"]
            r = []
            for i in range(nphases):
                r.append(steerer.sel[i].eq(STEER_NOP))
                if access == "read":
                    r.append(If(i == rdphase,    steerer.sel[i].eq(STEER_REQ)))
                    r.append(If(i == rdcmdphase, steerer.sel[i].eq(STEER_CMD)))
                if access == "write":
                    r.append(If(i == wrphase,    steerer.sel[i].eq(STEER_REQ)))
                    r.append(If(i == wrcmdphase, steerer.sel[i].eq(STEER_CMD)))
            return r

        # Control FSM ------------------------------------------------------------------------------
        self.submodules.fsm = fsm = FSM()
        fsm.act("READ",
            read_time_en.eq(1),
            choose_req.want_reads.eq(1),
            If(settings.phy.nphases == 1,
                choose_req.cmd.ready.eq(cas_allowed & (~choose_req.activate() | ras_allowed))
            ).Else(
                choose_cmd.want_activates.eq(ras_allowed),
                choose_cmd.cmd.ready.eq(~choose_cmd.activate() | ras_allowed),
                choose_req.cmd.ready.eq(cas_allowed)
            ),
            steerer_sel(steerer, access="read"),
            If(write_available,
                # TODO: switch only after several cycles of ~read_available?
                If(~read_available | max_read_time,
                    NextState("RTW")
                )
            ),
            If(go_to_refresh,
                NextState("REFRESH")
            )
        )
        fsm.act("WRITE",
            write_time_en.eq(1),
            choose_req.want_writes.eq(1),
            If(settings.phy.nphases == 1,
                choose_req.cmd.ready.eq(cas_allowed & (~choose_req.activate() | ras_allowed))
            ).Else(
                choose_cmd.want_activates.eq(ras_allowed),
                choose_cmd.cmd.ready.eq(~choose_cmd.activate() | ras_allowed),
                choose_req.cmd.ready.eq(cas_allowed),
            ),
            steerer_sel(steerer, access="write"),
            If(read_available,
                If(~write_available | max_write_time,
                    NextState("WTR")
                )
            ),
            If(go_to_refresh,
                NextState("REFRESH")
            )
        )
        fsm.act("REFRESH",
            steerer.sel[0].eq(STEER_REFRESH),
            refreshCmd.ready.eq(1),
            If(refreshCmd.last,
                NextState("READ")
            )
        )
        fsm.act("WTR",
            If(twtrcon.ready,
                NextState("READ")
            )
        )
        # TODO: reduce this, actual limit is around (cl+1)/nphases
        fsm.delayed_enter("RTW", "WRITE", settings.phy.read_latency-1)

        if settings.with_bandwidth:
            data_width = settings.phy.dfi_databits*settings.phy.nphases
            self.submodules.bandwidth = Bandwidth(self.choose_req.cmd, data_width)

class TMRMultiplexer(Module, AutoCSR):
    def __init__(self,
            settings,
            bank_machines,
            refresher,
            dfi,
            interface,
            TMRinterface):
        assert(settings.phy.nphases == len(dfi.phases))
        
        #TODO Refactor interface here
        self.TMRinterface = TMRinterface
        self.dfi = dfi
        
        ###

        ras_allowed = Signal(reset=1)
        cas_allowed = Signal(reset=1)

        # Read/Write Cmd/Dat phases ----------------------------------------------------------------
        nphases = settings.phy.nphases
        rdphase = settings.phy.rdphase
        wrphase = settings.phy.wrphase
        if isinstance(rdphase, Signal):
            rdcmdphase = Signal.like(rdphase)
            self.comb += rdcmdphase.eq(rdphase - 1) # Implicit %nphases.
        else:
            rdcmdphase = (rdphase - 1)%nphases
            
        if isinstance(rdphase, Signal):
            wrcmdphase = Signal.like(wrphase)
            self.comb += wrcmdphase.eq(wrphase - 1) # Implicit %nphases.
        else:
            wrcmdphase = (wrphase - 1)%nphases

        # Command choosing -------------------------------------------------------------------------
        
        #Create cmd's from TMRcmd's
        requests = [bm.cmd for bm in bank_machines]
        
        TMRrequests = [stream.Endpoint(cmd_request_rw_layout(settings.geom.addressbits, settings.geom.bankbits + log2_int(settings.phy.nranks))) for bm in bank_machines]
        
        for TMRrequest, bm in zip(TMRrequests, bank_machines):
            self.submodules += TMRInput(bm.TMRcmd.valid, TMRrequest.valid)
            self.submodules += TMRInput(bm.TMRcmd.last, TMRrequest.last)
            self.submodules += TMROutput(TMRrequest.ready, bm.TMRcmd.ready)
            self.submodules += TMRInput(bm.TMRcmd.first, TMRrequest.first)
            self.submodules += TMRInput(bm.TMRcmd.a, TMRrequest.a)
            self.submodules += TMRInput(bm.TMRcmd.ba, TMRrequest.ba)
            self.submodules += TMRInput(bm.TMRcmd.cas, TMRrequest.cas)
            self.submodules += TMRInput(bm.TMRcmd.ras, TMRrequest.ras)
            self.submodules += TMRInput(bm.TMRcmd.we, TMRrequest.we)
            self.submodules += TMRInput(bm.TMRcmd.is_cmd, TMRrequest.is_cmd)
            self.submodules += TMRInput(bm.TMRcmd.is_read, TMRrequest.is_read)
            self.submodules += TMRInput(bm.TMRcmd.is_write, TMRrequest.is_write)
        
        
        #CommandChoosers
        a = len(TMRrequests[0].a)
        ba = len(TMRrequests[0].ba)
        
        self.submodules.choose_cmd_int = choose_cmd_int = _CommandChooserInt(len(TMRrequests), a, ba)
        self.submodules.choose_cmd_int2 = choose_cmd_int2 = _CommandChooserInt(len(TMRrequests), a, ba)
        self.submodules.choose_cmd_int3 = choose_cmd_int3 = _CommandChooserInt(len(TMRrequests), a, ba)
        
        self.submodules.choose_req_int = choose_req_int = _CommandChooserInt(len(TMRrequests), a, ba)
        
        for i, TMRrequest in enumerate(TMRrequests):
            choose_cmd_sink = stream.Endpoint(cmd_request_rw_layout(a, ba))
            #vote_TMR(self, choose_cmd_sink, choose_cmd_int.requests[i], choose_cmd_int2.requests[i], choose_cmd_int3.requests[i], master=False)
            self.comb += TMRrequest.connect(choose_cmd_int.requests[i], choose_cmd_int2.requests[i], choose_cmd_int3.requests[i], choose_req_int.requests[i])
            
        choose_cmd_source = stream.Endpoint(cmd_request_rw_layout(a, ba))
        #vote_TMR(self, choose_cmd_source, choose_cmd_int.cmd, choose_cmd_int2.cmd, choose_cmd_int3.cmd)
        #self.comb += [choose_cmd_int2.cmd.ready.eq(choose_cmd_int.cmd.ready), choose_cmd_int3.cmd.ready.eq(choose_cmd_int.cmd.ready)]
        
        if settings.phy.nphases == 1:
            # When only 1 phase, use choose_req for all requests
            choose_cmd_int = choose_req_int
            self.comb += choose_req_int.want_cmds.eq(1)
            self.comb += choose_req_int.want_activates.eq(ras_allowed)
            
        # Refresher cmd
        
        refreshCmd = stream.Endpoint(cmd_request_rw_layout(settings.geom.addressbits, settings.geom.bankbits + log2_int(settings.phy.nranks)))
        
        self.submodules += TMRInput(refresher.TMRcmd.valid, refreshCmd.valid)
        self.submodules += TMRInput(refresher.TMRcmd.last, refreshCmd.last)
        self.submodules += TMROutput(refreshCmd.ready, refresher.TMRcmd.ready)
        self.submodules += TMRInput(refresher.TMRcmd.first, refreshCmd.first)
        self.submodules += TMRInput(refresher.TMRcmd.a, refreshCmd.a)
        self.submodules += TMRInput(refresher.TMRcmd.ba, refreshCmd.ba)
        self.submodules += TMRInput(refresher.TMRcmd.cas, refreshCmd.cas)
        self.submodules += TMRInput(refresher.TMRcmd.ras, refreshCmd.ras)
        self.submodules += TMRInput(refresher.TMRcmd.we, refreshCmd.we)
        self.submodules += TMRInput(refresher.TMRcmd.is_cmd, refreshCmd.is_cmd)
        self.submodules += TMRInput(refresher.TMRcmd.is_read, refreshCmd.is_read)
        self.submodules += TMRInput(refresher.TMRcmd.is_write, refreshCmd.is_write)

        # Command steering -------------------------------------------------------------------------
        nop = Record(cmd_request_layout(settings.geom.addressbits,
                                        log2_int(len(bank_machines))))
        # nop must be 1st
        commands = [nop, choose_cmd_int.cmd, choose_req_int.cmd, refreshCmd]
        
        steerer = _Steerer(commands, dfi)
        
        self.submodules += steerer

        # tRRD timing (Row to Row delay) -----------------------------------------------------------
        self.submodules.trrdcon = trrdcon = tXXDController(settings.timing.tRRD)
        self.comb += trrdcon.valid.eq(choose_cmd_int.accept() & choose_cmd_int.activate())

        self.submodules.trrdcon2 = trrdcon2 = tXXDController(settings.timing.tRRD)
        self.comb += trrdcon2.valid.eq(choose_cmd_int.accept() & choose_cmd_int.activate())

        self.submodules.trrdcon3 = trrdcon3 = tXXDController(settings.timing.tRRD)
        self.comb += trrdcon3.valid.eq(choose_cmd_int.accept() & choose_cmd_int.activate())

        trrdSig = Cat(trrdcon.ready, trrdcon2.ready, trrdcon3.ready)
        trrdVote = TMRInput(trrdSig)
        self.submodules += trrdVote

        # tFAW timing (Four Activate Window) -------------------------------------------------------
        self.submodules.tfawcon = tfawcon = tFAWController(settings.timing.tFAW)
        self.comb += tfawcon.valid.eq(choose_cmd_int.accept() & choose_cmd_int.activate())

        self.submodules.tfawcon2 = tfawcon2 = tFAWController(settings.timing.tFAW)
        self.comb += tfawcon2.valid.eq(choose_cmd_int.accept() & choose_cmd_int.activate())

        self.submodules.tfawcon3 = tfawcon3 = tFAWController(settings.timing.tFAW)
        self.comb += tfawcon3.valid.eq(choose_cmd_int.accept() & choose_cmd_int.activate())

        tfawSig = Cat(tfawcon.ready, tfawcon2.ready, tfawcon3.ready)
        tfawVote = TMRInput(tfawSig)
        self.submodules += tfawVote

        # RAS control ------------------------------------------------------------------------------
        self.comb += ras_allowed.eq(trrdVote.control & tfawVote.control)

        # tCCD timing (Column to Column delay) -----------------------------------------------------
        self.submodules.tccdcon = tccdcon = tXXDController(settings.timing.tCCD)
        self.comb += tccdcon.valid.eq(choose_req_int.accept() & (choose_req_int.write() | choose_req_int.read()))

        self.submodules.tccdcon2 = tccdcon2 = tXXDController(settings.timing.tCCD)
        self.comb += tccdcon2.valid.eq(choose_req_int.accept() & (choose_req_int.write() | choose_req_int.read()))

        self.submodules.tccdcon3 = tccdcon3 = tXXDController(settings.timing.tCCD)
        self.comb += tccdcon3.valid.eq(choose_req_int.accept() & (choose_req_int.write() | choose_req_int.read()))

        tccdSig = Cat(tccdcon.ready, tccdcon2.ready, tccdcon3.ready)
        tccdVote = TMRInput(tccdSig)
        self.submodules += tccdVote

        # CAS control ------------------------------------------------------------------------------
        self.comb += cas_allowed.eq(tccdVote.control)

        # tWTR timing (Write to Read delay) --------------------------------------------------------
        write_latency = math.ceil(settings.phy.cwl / settings.phy.nphases)
        self.submodules.twtrcon = twtrcon = tXXDController(
            settings.timing.tWTR + write_latency +
            # tCCD must be added since tWTR begins after the transfer is complete
            settings.timing.tCCD if settings.timing.tCCD is not None else 0)
        self.comb += twtrcon.valid.eq(choose_req_int.accept() & choose_req_int.write())

        self.submodules.twtrcon2 = twtrcon2 = tXXDController(
            settings.timing.tWTR + write_latency +
            settings.timing.tCCD if settings.timing.tCCD is not None else 0)
        self.comb += twtrcon2.valid.eq(choose_req_int.accept() & choose_req_int.write())

        self.submodules.twtrcon3 = twtrcon3 = tXXDController(
            settings.timing.tWTR + write_latency +
            settings.timing.tCCD if settings.timing.tCCD is not None else 0)
        self.comb += twtrcon3.valid.eq(choose_req_int.accept() & choose_req_int.write())

        twtrSig = Cat(twtrcon.ready, twtrcon2.ready, twtrcon3.ready)
        twtrVote = TMRInput(twtrSig)
        self.submodules += twtrVote

        # Read/write turnaround --------------------------------------------------------------------
        read_available = Signal()
        write_available = Signal()
        reads = [req.valid & req.is_read for req in requests]
        writes = [req.valid & req.is_write for req in requests]
        self.comb += [
            read_available.eq(reduce(or_, reads)),
            write_available.eq(reduce(or_, writes))
        ]

        # Anti Starvation --------------------------------------------------------------------------

        def anti_starvation(timeout):
            en = Signal()
            max_time = Signal()
            if timeout:
                t = timeout - 1
                time = Signal(max=t+1)
                self.comb += max_time.eq(time == 0)
                self.sync += If(~en,
                        time.eq(t)
                    ).Elif(~max_time,
                        time.eq(time - 1)
                    )
            else:
                self.comb += max_time.eq(0)
            return en, max_time

        read_time_en,   max_read_time = anti_starvation(settings.read_time)
        write_time_en, max_write_time = anti_starvation(settings.write_time)

        # Refresh ----------------------------------------------------------------------------------
        self.comb += [bm.refresh_req.eq(refreshCmd.valid) for bm in bank_machines]
        go_to_refresh = Signal()
        bm_refresh_gnts = [bm.refresh_gnt for bm in bank_machines]
        self.comb += go_to_refresh.eq(reduce(and_, bm_refresh_gnts))

        # Datapath ---------------------------------------------------------------------------------
        all_rddata = [p.rddata for p in dfi.phases]
        all_wrdata = [p.wrdata for p in dfi.phases]
        all_wrdata_mask = [p.wrdata_mask for p in dfi.phases]        
        self.submodules += TMROutput(Cat(*all_rddata), TMRinterface.rdata)
        self.submodules += TMRInput(TMRinterface.wdata, Cat(*all_wrdata))
        self.submodules += TMRInput(~TMRinterface.wdata_we, Cat(*all_wrdata_mask))

        def steerer_sel(steerer, access):
            assert access in ["read", "write"]
            r = []
            for i in range(nphases):
                r.append(steerer.sel[i].eq(STEER_NOP))
                if access == "read":
                    r.append(If(i == rdphase,    steerer.sel[i].eq(STEER_REQ)))
                    r.append(If(i == rdcmdphase, steerer.sel[i].eq(STEER_CMD)))
                if access == "write":
                    r.append(If(i == wrphase,    steerer.sel[i].eq(STEER_REQ)))
                    r.append(If(i == wrcmdphase, steerer.sel[i].eq(STEER_CMD)))
            return r

        # Control FSM ------------------------------------------------------------------------------
        self.submodules.fsm = fsm = FSM()
        fsm.act("READ",
            read_time_en.eq(1),
            choose_req_int.want_reads.eq(1),
            If(settings.phy.nphases == 1,
                choose_req_int.cmd.ready.eq(cas_allowed & (~choose_req_int.activate() | ras_allowed))
            ).Else(
                choose_cmd_int.want_activates.eq(ras_allowed),
                choose_cmd_int.cmd.ready.eq(~choose_cmd_int.activate() | ras_allowed),
                choose_req_int.cmd.ready.eq(cas_allowed)
            ),
            steerer_sel(steerer, access="read"),
            If(write_available,
                # TODO: switch only after several cycles of ~read_available?
                If(~read_available | max_read_time,
                    NextState("RTW")
                )
            ),
            If(go_to_refresh,
                NextState("REFRESH")
            )
        )
        fsm.act("WRITE",
            write_time_en.eq(1),
            choose_req_int.want_writes.eq(1),
            If(settings.phy.nphases == 1,
                choose_req_int.cmd.ready.eq(cas_allowed & (~choose_req_int.activate() | ras_allowed))
            ).Else(
                choose_cmd_int.want_activates.eq(ras_allowed),
                choose_cmd_int.cmd.ready.eq(~choose_cmd_int.activate() | ras_allowed),
                choose_req_int.cmd.ready.eq(cas_allowed)
            ),
            steerer_sel(steerer, access="write"),
            If(read_available,
                If(~write_available | max_write_time,
                    NextState("WTR")
                )
            ),
            If(go_to_refresh,
                NextState("REFRESH")
            )
        )
        fsm.act("REFRESH",
            steerer.sel[0].eq(STEER_REFRESH),
            refreshCmd.ready.eq(1),
            If(refreshCmd.last,
                NextState("READ")
            )
        )
        fsm.act("WTR",
            If(twtrVote.control,
                NextState("READ")
            )
        )
        # TODO: reduce this, actual limit is around (cl+1)/nphases
        fsm.delayed_enter("RTW", "WRITE", settings.phy.read_latency-1)

        if settings.with_bandwidth:
            data_width = settings.phy.dfi_databits*settings.phy.nphases
            self.submodules.bandwidth = Bandwidth(self.choose_req.cmd, data_width)
