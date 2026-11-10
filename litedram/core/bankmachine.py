#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""LiteDRAM BankMachine (Rows/Columns management)."""

import math

from migen import *
from migen.genlib import roundrobin

from litex.soc.interconnect import stream

from litedram.common import *
from litedram.core.multiplexer import *

# AddressSlicer ------------------------------------------------------------------------------------

class _AddressSlicer:
    """Helper for extracting row/col from address

    Column occupies lower bits of the address, row - higher bits. Address has
    a forced alignment, so column does not contain alignment bits.
    """
    def __init__(self, colbits, address_align):
        self.colbits       = colbits
        self.address_align = address_align

    def row(self, address):
        split = self.colbits - self.address_align
        return address[split:]

    def col(self, address):
        split = self.colbits - self.address_align
        if self.colbits > 10:
            # A10 is reserved for auto-precharge, this bit needs to be skipped for col addresses.
            return Cat(
                Replicate(0, self.address_align),
                address[:10-self.address_align],
                Replicate(0, 1),
                address[10-self.address_align:split]
            )
        else:
            return Cat(
                Replicate(0, self.address_align),
                address[:split]
            )

# BankMachine --------------------------------------------------------------------------------------

class BankMachine(Module):
    """Converts requests from ports into DRAM commands

    BankMachine abstracts single DRAM bank by keeping track of the currently
    selected row. It converts requests from LiteDRAMCrossbar to targetted
    to that bank into DRAM commands that go to the Multiplexer, inserting any
    needed activate/precharge commands (with optional auto-precharge). It also
    keeps track and enforces some DRAM timings (other timings are enforced in
    the Multiplexer).

    BankMachines work independently from the data path (which connects
    LiteDRAMCrossbar with the Multiplexer directly).

    Stream of requests from LiteDRAMCrossbar is being queued, so that reqeust
    can be "looked ahead", and auto-precharge can be performed (if enabled in
    settings).

    Lock (cmd_layout.lock) is used to synchronise with LiteDRAMCrossbar. It is
    being held when:
     - there is a valid command awaiting in `cmd_buffer_lookahead` - this buffer
       becomes ready simply when the next data gets fetched to the `cmd_buffer`
     - there is a valid command in `cmd_buffer` - `cmd_buffer` becomes ready
       when the BankMachine sends wdata_ready/rdata_valid back to the crossbar

    A BankMachine can also be shared between several consecutive banks (nbanks > 1, to reduce
    resource usage): requests of its banks are arbitrated (round-robin) into the command buffer and
    only one row of one of its banks is kept open at a time: a request to another bank of the
    machine closes the open row first (precharge or auto-precharge). The timings it enforces are
    then shared by its banks (conservative).

    Parameters
    ----------
    n : int
        Bank number (first bank number when nbanks > 1)
    address_width : int
        LiteDRAMInterface address width
    address_align : int
        Address alignment depending on burst length
    nranks : int
        Number of separate DRAM chips (width of chip select)
    settings : ControllerSettings
        LiteDRAMController settings
    nbanks : int
        Number of consecutive banks (n to n+nbanks-1) handled by the BankMachine

    Attributes
    ----------
    req : Record(cmd_layout)
        Stream of requests from LiteDRAMCrossbar (nbanks == 1)
    reqs : [Record(cmd_layout), ...]
        Streams of requests from LiteDRAMCrossbar, one per bank ([req] when nbanks == 1)
    refresh_req : Signal(), in
        Indicates that refresh needs to be done, connects to Refresher.cmd.valid
    refresh_gnt : Signal(), out
        Indicates that refresh permission has been granted, satisfying timings
    cmd : Endpoint(cmd_request_rw_layout)
        Stream of commands to the Multiplexer
    """
    def __init__(self, n, address_width, address_align, nranks, settings, nbanks=1):
        assert nbanks >= 1 and (nbanks & (nbanks - 1)) == 0
        assert n % nbanks == 0
        shared = (nbanks > 1)
        self.req = req = Record(cmd_layout(address_width))
        self.reqs = [req]
        if shared:
            self.reqs = reqs = [Record(cmd_layout(address_width)) for i in range(nbanks)]
        self.refresh_req = refresh_req = Signal()
        self.refresh_gnt = refresh_gnt = Signal()

        a  = settings.geom.addressbits
        ba = settings.geom.bankbits + log2_int(nranks)
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(a, ba))

        # # #

        auto_precharge = Signal()

        # Command buffer ---------------------------------------------------------------------------
        cmd_buffer_layout    = [("we", 1), ("addr", len(req.addr))]
        if shared:
            cmd_buffer_layout += [("bank", log2_int(nbanks))]
        cmd_buffer_lookahead = stream.SyncFIFO(
            cmd_buffer_layout, settings.cmd_buffer_depth,
            buffered=settings.cmd_buffer_buffered)
        cmd_buffer = stream.Buffer(cmd_buffer_layout) # 1 depth buffer to detect row change
        self.submodules += cmd_buffer_lookahead, cmd_buffer
        self.comb += [
            req.connect(cmd_buffer_lookahead.sink, keep={"valid", "ready", "we", "addr"}),
            cmd_buffer_lookahead.source.connect(cmd_buffer.sink),
            cmd_buffer.source.ready.eq(req.wdata_ready | req.rdata_valid),
            req.lock.eq(cmd_buffer_lookahead.source.valid | cmd_buffer.source.valid),
        ]

        # Shared BankMachine: requests arbitration and per-bank responses --------------------------
        if shared:
            bank_bits = log2_int(nbanks)
            cmd_bank  = cmd_buffer.source.bank # Bank of the current command.

            # Round-robin between the requests of the banks, keeping the granted bank while it has
            # requests (runs of row hits, as with a bank machine per bank: switching on each request
            # would interleave the banks in the command buffer and close the row on almost every
            # command) for at most run_length accepted requests (no starvation of the other banks).
            run_length = 8*settings.cmd_buffer_depth
            arbiter    = roundrobin.RoundRobin(nbanks, roundrobin.SP_CE)
            run        = Signal(max=run_length + 1)
            run_end    = Signal()
            self.submodules += arbiter
            self.sync += If(arbiter.ce,
                run.eq(0)
            ).Elif(req.valid & req.ready,
                run.eq(run + 1)
            )
            self.comb += [
                run_end.eq(req.valid & req.ready & (run == run_length - 1)),
                arbiter.request.eq(Cat(*[r.valid for r in reqs])),
                arbiter.ce.eq(~req.valid | run_end),
                req.valid.eq(Array(r.valid for r in reqs)[arbiter.grant]),
                req.we.eq(Array(r.we for r in reqs)[arbiter.grant]),
                req.addr.eq(Array(r.addr for r in reqs)[arbiter.grant]),
                cmd_buffer_lookahead.sink.bank.eq(arbiter.grant),
            ]
            for i, r in enumerate(reqs):
                # Lock each bank while it has commands in the BankMachine (as an unshared BankMachine
                # does): locking all the banks would block the crossbar's masters on the other banks.
                pending = Signal(bits_for(settings.cmd_buffer_depth + 2))
                push    = Signal()
                pop     = Signal()
                self.comb += [
                    r.ready.eq(req.ready & (arbiter.grant == i)),
                    r.wdata_ready.eq(req.wdata_ready & (cmd_bank == i)),
                    r.rdata_valid.eq(req.rdata_valid & (cmd_bank == i)),
                    push.eq(r.valid & r.ready),
                    pop.eq((req.wdata_ready | req.rdata_valid) & (cmd_bank == i)),
                    r.lock.eq(pending != 0),
                ]
                self.sync += If(push & ~pop,
                    pending.eq(pending + 1)
                ).Elif(~push & pop,
                    pending.eq(pending - 1)
                )

        slicer = _AddressSlicer(settings.geom.colbits, address_align)

        # Row tracking -----------------------------------------------------------------------------
        row        = Signal(settings.geom.rowbits, reset_less=True) # Only compared when row_opened.
        row_opened = Signal()
        row_hit    = Signal()
        row_open   = Signal()
        row_close  = Signal()
        same_row   = (row == slicer.row(cmd_buffer.source.addr))
        if shared:
            # Bank of the open row: a hit also needs the same bank.
            row_bank = Signal(bank_bits, reset_less=True) # Only compared when row_opened.
            same_row = same_row & (row_bank == cmd_bank)
            self.sync += If(row_open, row_bank.eq(cmd_bank))
        self.comb += row_hit.eq(same_row)
        self.sync += \
            If(row_close,
                row_opened.eq(0)
            ).Elif(row_open,
                row_opened.eq(1),
                row.eq(slicer.row(cmd_buffer.source.addr))
            )

        # Address generation -----------------------------------------------------------------------
        row_col_n_addr_sel = Signal()
        ba = n
        if shared:
            # ACTIVATE: bank of the command. CAS (row hit: same bank) and PRECHARGE: bank of the
            # open row.
            ba = n + Mux(row_col_n_addr_sel, cmd_bank, row_bank)
        self.comb += [
            cmd.ba.eq(ba),
            If(row_col_n_addr_sel,
                cmd.a.eq(slicer.row(cmd_buffer.source.addr))
            ).Else(
                cmd.a.eq((auto_precharge << 10) | slicer.col(cmd_buffer.source.addr))
            )
        ]

        # tWTP (write-to-precharge) controller -----------------------------------------------------
        write_latency = math.ceil(settings.phy.cwl / settings.phy.nphases)
        precharge_time = write_latency + settings.timing.tWR + settings.timing.tCCD # AL=0
        self.submodules.twtpcon = twtpcon = tXXDController(precharge_time)
        self.comb += twtpcon.valid.eq(cmd.valid & cmd.ready & cmd.is_write)

        # tRC (activate-activate) controller -------------------------------------------------------
        self.submodules.trccon = trccon = tXXDController(settings.timing.tRC)
        self.comb += trccon.valid.eq(cmd.valid & cmd.ready & row_open)

        # tRAS (activate-precharge) controller -----------------------------------------------------
        self.submodules.trascon = trascon = tXXDController(settings.timing.tRAS)
        self.comb += trascon.valid.eq(cmd.valid & cmd.ready & row_open)

        # tRTP (read-to-precharge) controller ------------------------------------------------------
        # Also the delay of the internal precharge of an auto-precharged read (AL=0).
        self.submodules.trtpcon = trtpcon = tXXDController(settings.timing.tRTP)
        self.comb += trtpcon.valid.eq(cmd.valid & cmd.ready & cmd.is_read)

        # Auto Precharge generation ----------------------------------------------------------------
        # generate auto precharge when current and next cmds are to different rows
        if settings.with_auto_precharge:
            other_row = (slicer.row(cmd_buffer_lookahead.source.addr) !=
                         slicer.row(cmd_buffer.source.addr))
            if shared:
                # Shared BankMachine: also close the row when the next command is to another bank.
                other_row = other_row | (cmd_buffer_lookahead.source.bank != cmd_bank)
            self.comb += \
                If(cmd_buffer_lookahead.source.valid & cmd_buffer.source.valid,
                    If(other_row,
                        auto_precharge.eq(row_close == 0)
                    )
                )

        # Control and command generation FSM -------------------------------------------------------
        # Note: tRRD, tFAW, tCCD, tWTR timings are enforced by the multiplexer
        self.submodules.fsm = fsm = FSM()
        fsm.act("REGULAR",
            If(refresh_req,
                NextState("REFRESH")
            ).Elif(cmd_buffer.source.valid,
                If(row_opened,
                    If(row_hit,
                        cmd.valid.eq(1),
                        If(cmd_buffer.source.we,
                            req.wdata_ready.eq(cmd.ready),
                            cmd.is_write.eq(1),
                            cmd.we.eq(1),
                        ).Else(
                            req.rdata_valid.eq(cmd.ready),
                            cmd.is_read.eq(1)
                        ),
                        cmd.cas.eq(1),
                        If(cmd.ready & auto_precharge,
                           NextState("AUTOPRECHARGE")
                        )
                    ).Else(  # row_opened & ~row_hit
                        NextState("PRECHARGE")
                    )
                ).Else(  # ~row_opened
                    NextState("ACTIVATE")
                )
            )
        )
        fsm.act("PRECHARGE",
            # Note: we are presenting the column address, A10 is always low
            If(twtpcon.ready & trtpcon.ready & trascon.ready,
                cmd.valid.eq(1),
                If(cmd.ready,
                    NextState("TRP")
                ),
                cmd.ras.eq(1),
                cmd.we.eq(1),
                cmd.is_cmd.eq(1)
            ),
            row_close.eq(1)
        )
        fsm.act("AUTOPRECHARGE",
            If(twtpcon.ready & trtpcon.ready & trascon.ready,
                NextState("TRP")
            ),
            row_close.eq(1)
        )
        fsm.act("ACTIVATE",
            If(trccon.ready,
                row_col_n_addr_sel.eq(1),
                row_open.eq(1),
                cmd.valid.eq(1),
                cmd.is_cmd.eq(1),
                If(cmd.ready,
                    NextState("TRCD")
                ),
                cmd.ras.eq(1)
            )
        )
        fsm.act("REFRESH",
            # The refresher precharges all banks: respect tRAS (and tWTP) from this bank's last
            # ACTIVATE/write, as PRECHARGE/AUTOPRECHARGE do.
            If(twtpcon.ready & trtpcon.ready & trascon.ready,
                refresh_gnt.eq(1),
            ),
            row_close.eq(1),
            cmd.is_cmd.eq(1),
            If(~refresh_req,
                NextState("REGULAR")
            )
        )
        fsm.delayed_enter("TRP", "ACTIVATE", settings.timing.tRP - 1)
        fsm.delayed_enter("TRCD", "REGULAR", settings.timing.tRCD - 1)
