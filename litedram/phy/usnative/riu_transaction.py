#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Acknowledged RIU register access across related sys and riu clock domains."""

from migen import *
from migen.genlib.cdc import MultiReg

class RIUTransaction(Module):
    """One outstanding, acknowledged RIU transaction; no timing exceptions.

    The caller supplies related sys and riu clocks with sys running at twice
    the riu frequency. Payload and response buses are held stable around the
    synchronized request/acknowledge toggles; they are not independently
    synchronized data buses for arbitrary asynchronous clocks.

    Soft reset cancels responses but drains the outstanding handshake. Busy
    requests are rejected without changing the held payload. Local bounded
    timeout prevents absent native valid from wedging future transactions.
    """
    def __init__(self, controls, riu_indices, timeout=255):
        if not isinstance(controls, int) or controls < 1:
            raise ValueError('At least one native control is required')
        if len(riu_indices) != controls or any(not isinstance(i, int) or i < 0 for i in riu_indices):
            raise ValueError('Each control requires a nonnegative RIU byte index')
        if not isinstance(timeout, int) or timeout < 4:
            raise ValueError('RIU timeout must allow the four-cycle settling state')
        # System-side request and sticky completion status.
        self.request        = Signal()
        self.write          = Signal()
        self.reset          = Signal()
        self.address        = Signal(6)
        self.select         = Signal(max=max(2, controls))
        self.wdata          = Signal(16)
        self.busy           = Signal()
        self.valid          = Signal()
        self.error          = Signal()
        self.rdata          = Signal(16)
        self.native_address = Signal(6)
        self.native_select  = Signal(controls)
        self.native_wdata   = Signal(16)
        self.native_write   = Signal()
        nr                  = max(riu_indices)+1
        self.native_rdata   = Signal(16*nr)
        self.native_valid   = Signal(nr)
        # Hold the entire request until the RIU domain acknowledges completion.
        payload   = Signal(23+len(self.select))
        local     = Signal(len(payload))
        req       = Signal()
        req_r     = Signal()
        ack       = Signal()
        ack_s     = Signal()
        soft_r    = Signal()
        response  = Signal(16)
        ok        = Signal()
        cancelled = Signal()
        self.specials += [MultiReg(req, req_r, 'riu'), MultiReg(ack, ack_s), MultiReg(self.reset, soft_r, 'riu')]
        self.comb += self.busy.eq(req != ack_s)
        self.sync += [
            If(self.reset, self.valid.eq(0), self.error.eq(0), cancelled.eq(1)),
            If(self.request & ~self.reset,
                If(self.busy, self.error.eq(1)).Else(
                    payload.eq(Cat(self.address, self.wdata, self.write, self.select)),
                    req.eq(~req), self.valid.eq(0), self.error.eq(0), cancelled.eq(0))),
            If((req == ack_s) & ~self.request & ~self.reset & ~cancelled & ~self.valid,
                self.rdata.eq(response), self.valid.eq(ok), self.error.eq(self.error | ~ok))]
        # Completion flag prevents idle reset state from being reported as error.
        active = Signal()
        self.sync += [If(self.request & ~self.busy & ~self.reset, active.eq(1)),
                     If(self.reset, active.eq(0))]
        # Response is stable before ack synchronizes. valid is hidden while idle
        # with no completed request (including power-on and reset).
        self.sync += If(~active, self.valid.eq(0), self.error.eq(0))
        state    = Signal(3)
        wait     = Signal(max=timeout+1)
        selected = local[23:]
        addr     = local[:6]
        data     = local[6:22]
        write    = local[22]
        # RIU sequence: capture, select, wait for availability, launch, settle,
        # wait for valid readback, capture, then acknowledge. Address and select
        # remain stable until completion, including timeout and reset paths.
        self.sync.riu += [self.native_write.eq(0),
            If(state==0,
                If(req_r != ack, local.eq(payload), state.eq(1))),
            If(state==1,
                self.native_address.eq(addr), self.native_wdata.eq(data),
                self.native_select.eq(Mux(selected<controls, 1<<selected, 0)), wait.eq(0), state.eq(2)),
            If(state==2,
                If(soft_r | (selected>=controls), ok.eq(0), state.eq(5)).Elif(
                    Array(self.native_valid[i] for i in riu_indices)[selected],
                    self.native_write.eq(write), wait.eq(0), state.eq(3)
                ).Elif(wait==timeout-1, ok.eq(0), state.eq(5)).Else(wait.eq(wait+1))),
            If(state==3,
                If(wait==4, wait.eq(0), state.eq(4)).Else(wait.eq(wait+1))),
            If(state==4,
                If(soft_r, ok.eq(0), state.eq(5)).Elif(
                    Array(self.native_valid[i] for i in riu_indices)[selected],
                    state.eq(6)).Elif(wait==timeout-1, ok.eq(0), state.eq(5)).Else(wait.eq(wait+1))),
            # VALID signals transaction availability; the registered readback
            # may lag commit by one RIU edge. Keep address/select stable through
            # a further edge and only capture while valid remains asserted.
            If(state==6,
                If(soft_r, ok.eq(0), state.eq(5)).Elif(
                    Array(self.native_valid[i] for i in riu_indices)[selected],
                    response.eq(Array(self.native_rdata[16*i:16*i+16] for i in riu_indices)[selected]),
                    ok.eq(1), state.eq(5)).Elif(wait==timeout-1, ok.eq(0), state.eq(5)).Else(wait.eq(wait+1), state.eq(4))),
            # Acknowledge even cancelled/failed requests so the source can
            # issue another transaction. This cannot undo a native write.
            If(state==5, self.native_select.eq(0), ack.eq(req_r), state.eq(0))]
