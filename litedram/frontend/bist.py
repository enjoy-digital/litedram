#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2016 Tim 'mithro' Ansell <mithro@mithis.com>
# SPDX-License-Identifier: BSD-2-Clause

"""Built In Self Test (BIST) modules for testing LiteDRAM functionality."""

from functools import reduce
from operator import xor

from migen import *

from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *

from litedram.common import LiteDRAMNativePort
from litedram.frontend.axi import LiteDRAMAXIPort
from litedram.frontend.dma import LiteDRAMDMAWriter, LiteDRAMDMAReader

# LFSR ---------------------------------------------------------------------------------------------

class LFSR(Module):
    """Linear-Feedback Shift Register to generate a pseudo-random sequence.

    Parameters
    ----------
    n_out : int
        Width of the output data signal.
    n_state : int
        LFSR internal state
    taps : list of int
        LFSR taps (from polynom)

    Attributes
    ----------
    o : out
        Output data
    """
    def __init__(self, n_out, n_state, taps):
        self.o = Signal(n_out)

        # # #

        state  = Signal(n_state)
        curval = [state[i] for i in range(n_state)]
        curval += [0]*(n_out - n_state)
        for i in range(n_out):
            nv = ~reduce(xor, [curval[tap] for tap in taps])
            curval.insert(0, nv)
            curval.pop()

        self.sync += [
            state.eq(Cat(*curval[:n_state])),
            self.o.eq(Cat(*curval))
        ]

# Counter ------------------------------------------------------------------------------------------

class Counter(Module):
    """Simple incremental counter.

    Parameters
    ----------
    n_out : int
        Width of the output data signal.

    Attributes
    ----------
    o : out
        Output data
    """
    def __init__(self, n_out):
        self.o = Signal(n_out)

        # # #

        self.sync += self.o.eq(self.o + 1)

# Generator ----------------------------------------------------------------------------------------

@CEInserter()
class Generator(Module):
    """Address/Data Generator.

    Parameters
    ----------
    n_out : int
        Width of the output data signal.

    Attributes
    ----------
    random_enable : in
        Enable Random (LFSR)

    o : out
        Output data
    """
    def __init__(self, n_out, n_state, taps):
        self.random_enable = Signal()
        self.o = Signal(n_out)

        # # #

        lfsr  = LFSR(n_out, n_state, taps)
        count = Counter(n_out)
        self.submodules += lfsr, count

        self.comb += \
            If(self.random_enable,
                self.o.eq(lfsr.o)
            ).Else(
                self.o.eq(count.o)
            )


def get_ashift_awidth(dram_port):
    if isinstance(dram_port, LiteDRAMNativePort):
        ashift = log2_int(dram_port.data_width//8)
        awidth = dram_port.address_width + ashift
    elif isinstance(dram_port, LiteDRAMAXIPort):
        ashift = log2_int(dram_port.data_width//8)
        awidth = dram_port.address_width
    else:
        raise NotImplementedError
    return ashift, awidth

# _LiteDRAMBISTGenerator ---------------------------------------------------------------------------

@ResetInserter()
class _LiteDRAMBISTGenerator(Module):
    def __init__(self, dram_port):
        ashift, awidth = get_ashift_awidth(dram_port)
        self.start       = Signal()
        self.done        = Signal()
        self.base        = Signal(awidth)
        self.end         = Signal(awidth)
        self.length      = Signal(awidth)
        self.random_data = Signal()
        self.random_addr = Signal()
        self.ticks       = Signal(32)

        self.run_cascade_in  = Signal(reset=1)
        self.run_cascade_out = Signal()

        # # #

        # Data / Address generators ----------------------------------------------------------------
        data_gen = Generator(31, n_state=31, taps=[27, 30]) # PRBS31
        addr_gen = Generator(31, n_state=31, taps=[27, 30])
        self.submodules += data_gen, addr_gen
        self.comb += data_gen.random_enable.eq(self.random_data)
        self.comb += addr_gen.random_enable.eq(self.random_addr)

        # mask random address to the range <base, end), range size must be power of 2
        addr_mask = Signal(awidth)
        self.comb += addr_mask.eq((self.end - self.base) - 1)

        # DMA --------------------------------------------------------------------------------------
        dma = LiteDRAMDMAWriter(dram_port)
        self.submodules += dma

        cmd_counter = Signal(dram_port.address_width, reset_less=True)

        # Data / Address FSM -----------------------------------------------------------------------
        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm
        fsm.act("IDLE",
            If(self.start,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            ),
            NextValue(self.ticks, 0)
        )
        fsm.act("WAIT",
            If(self.run_cascade_in,
                NextState("RUN")
            )
        )
        fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                self.run_cascade_out.eq(1),
                data_gen.ce.eq(1),
                addr_gen.ce.eq(1),
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (self.length[ashift:] - 1),
                    NextState("DONE")
                ).Elif(~self.run_cascade_in,
                    NextState("WAIT")
                )
            ),
            NextValue(self.ticks, self.ticks + 1)
        )
        fsm.act("DONE",
            self.run_cascade_out.eq(1),
            self.done.eq(1)
        )

        if isinstance(dram_port, LiteDRAMNativePort): # addressing in dwords
            dma_sink_addr = dma.sink.address
        elif isinstance(dram_port, LiteDRAMAXIPort):  # addressing in bytes
            dma_sink_addr = dma.sink.address[ashift:]
        else:
            raise NotImplementedError

        self.comb += dma_sink_addr.eq(self.base[ashift:] + (addr_gen.o & addr_mask))
        self.comb += dma.sink.data.eq(data_gen.o)


@ResetInserter()
class _LiteDRAMPatternGenerator(Module):
    def __init__(self, dram_port, init=[]):
        ashift, awidth = get_ashift_awidth(dram_port)
        self.start  = Signal()
        self.done   = Signal()
        self.ticks  = Signal(32)

        self.run_cascade_in  = Signal(reset=1)
        self.run_cascade_out = Signal()

        # # #

        # Data / Address pattern -------------------------------------------------------------------
        addr_init, data_init = zip(*init)
        addr_mem = Memory(dram_port.address_width, len(addr_init), init=addr_init)
        data_mem = Memory(dram_port.data_width,    len(data_init), init=data_init)
        addr_port = addr_mem.get_port(async_read=True)
        data_port = data_mem.get_port(async_read=True)
        self.specials += addr_mem, data_mem, addr_port, data_port

        # DMA --------------------------------------------------------------------------------------
        dma = LiteDRAMDMAWriter(dram_port)
        self.submodules += dma

        cmd_counter = Signal(dram_port.address_width, reset_less=True)

        # Data / Address FSM -----------------------------------------------------------------------
        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm
        fsm.act("IDLE",
            If(self.start,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            ),
            NextValue(self.ticks, 0)
        )
        fsm.act("WAIT",
            If(self.run_cascade_in,
                NextState("RUN")
            )
        )
        fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                self.run_cascade_out.eq(1),
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (len(init) - 1),
                    NextState("DONE")
                ).Elif(~self.run_cascade_in,
                    NextState("WAIT")
                )
            ),
            NextValue(self.ticks, self.ticks + 1)
        )
        fsm.act("DONE",
            self.run_cascade_out.eq(1),
            self.done.eq(1)
        )

        if isinstance(dram_port, LiteDRAMNativePort): # addressing in dwords
            dma_sink_addr = dma.sink.address
        elif isinstance(dram_port, LiteDRAMAXIPort):  # addressing in bytes
            dma_sink_addr = dma.sink.address[ashift:]
        else:
            raise NotImplementedError

        self.comb += [
            addr_port.adr.eq(cmd_counter),
            dma_sink_addr.eq(addr_port.dat_r),
            data_port.adr.eq(cmd_counter),
            dma.sink.data.eq(data_port.dat_r),
        ]

# LiteDRAMBISTGenerator ----------------------------------------------------------------------------

class LiteDRAMBISTGenerator(Module, AutoCSR):
    """DRAM memory pattern generator.

    Attributes
    ----------
    reset : in
        Reset the module.

    start : in
        Start the generation.

    done : out
        The module has completed writing the pattern.

    base : in
        DRAM address to start from.

    end : in
        Max DRAM address.

    length : in
        Number of DRAM words to write.

    random_data : in
        Enable random data (LFSR)

    random_addr : in
        Enable random address (LFSR). Wrapped to (end - base), so may not be unique.

    ticks : out
        Duration of the generation.
    """
    def __init__(self, dram_port):
        ashift, awidth = get_ashift_awidth(dram_port)
        self.reset       = CSR()
        self.start       = CSR()
        self.done        = CSRStatus()
        self.base        = CSRStorage(awidth)
        self.end         = CSRStorage(awidth)
        self.length      = CSRStorage(awidth)
        self.random      = CSRStorage(fields=[
            CSRField("data", size=1),
            CSRField("addr", size=1),
        ])
        self.ticks       = CSRStatus(32)

        # # #

        clock_domain = dram_port.clock_domain

        core = _LiteDRAMBISTGenerator(dram_port)
        core = ClockDomainsRenamer(clock_domain)(core)
        self.submodules.core = core

        if clock_domain != "sys":
            control_layout = [
                ("reset", 1),
                ("start", 1),
                ("base",   awidth),
                ("end",    awidth),
                ("length", awidth),
                ("random_data", 1),
                ("random_addr", 1),
            ]
            status_layout = [
                ("done",  1),
                ("ticks", 32),
            ]
            control_cdc = stream.AsyncFIFO(control_layout)
            control_cdc = ClockDomainsRenamer({"write" : "sys", "read": clock_domain})(control_cdc)
            status_cdc  = stream.AsyncFIFO(status_layout)
            status_cdc  = ClockDomainsRenamer({"write" : clock_domain, "read": "sys"})(status_cdc)
            self.submodules += control_cdc, status_cdc
            # Control CDC In
            self.comb += [
                control_cdc.sink.valid.eq(self.reset.re | self.start.re),
                control_cdc.sink.reset.eq(self.reset.re),
                control_cdc.sink.start.eq(self.start.re),
                control_cdc.sink.base.eq(self.base.storage),
                control_cdc.sink.end.eq(self.end.storage),
                control_cdc.sink.length.eq(self.length.storage),
                control_cdc.sink.random_data.eq(self.random.fields.data),
                control_cdc.sink.random_addr.eq(self.random.fields.addr),
            ]
            # Control CDC Out
            self.comb += [
                control_cdc.source.ready.eq(1),
                core.reset.eq(control_cdc.source.valid & control_cdc.source.reset),
                core.start.eq(control_cdc.source.valid & control_cdc.source.start),
            ]
            self.sync += [
                If(control_cdc.source.valid,
                    core.base.eq(control_cdc.source.base),
                    core.end.eq(control_cdc.source.end),
                    core.length.eq(control_cdc.source.length),
                    core.random_data.eq(control_cdc.source.random_data),
                    core.random_addr.eq(control_cdc.source.random_addr),
                )
            ]
            # Status CDC In
            self.comb += [
                status_cdc.sink.valid.eq(1),
                status_cdc.sink.done.eq(core.done),
                status_cdc.sink.ticks.eq(core.ticks),
            ]
            # Status CDC Out
            self.comb += status_cdc.source.ready.eq(1)
            self.sync += [
                If(status_cdc.source.valid,
                    self.done.status.eq(status_cdc.source.done),
                    self.ticks.status.eq(status_cdc.source.ticks),
                )
            ]
        else:
            self.comb += [
                core.reset.eq(self.reset.re),
                core.start.eq(self.start.re),
                self.done.status.eq(core.done),
                core.base.eq(self.base.storage),
                core.end.eq(self.end.storage),
                core.length.eq(self.length.storage),
                core.random_data.eq(self.random.fields.data),
                core.random_addr.eq(self.random.fields.addr),
                self.ticks.status.eq(core.ticks)
            ]

# _LiteDRAMBISTChecker -----------------------------------------------------------------------------

@ResetInserter()
class _LiteDRAMBISTChecker(Module, AutoCSR):
    def __init__(self, dram_port):
        ashift, awidth = get_ashift_awidth(dram_port)
        self.start       = Signal()
        self.done        = Signal()
        self.base        = Signal(awidth)
        self.end         = Signal(awidth)
        self.length      = Signal(awidth)
        self.random_data = Signal()
        self.random_addr = Signal()
        self.ticks       = Signal(32)
        self.errors      = Signal(32)

        self.run_cascade_in  = Signal(reset=1)
        self.run_cascade_out = Signal()

        # # #

        # Data / Address generators ----------------------------------------------------------------
        data_gen = Generator(31, n_state=31, taps=[27, 30]) # PRBS31
        addr_gen = Generator(31, n_state=31, taps=[27, 30])
        self.submodules += data_gen, addr_gen
        self.comb += data_gen.random_enable.eq(self.random_data)
        self.comb += addr_gen.random_enable.eq(self.random_addr)

        # mask random address to the range <base, end), range size must be power of 2
        addr_mask = Signal(awidth)
        self.comb += addr_mask.eq((self.end - self.base) - 1)

        # DMA --------------------------------------------------------------------------------------
        dma = LiteDRAMDMAReader(dram_port)
        self.submodules += dma

        # Address FSM ------------------------------------------------------------------------------
        cmd_counter = Signal(dram_port.address_width, reset_less=True)

        cmd_fsm = FSM(reset_state="IDLE")
        self.submodules += cmd_fsm
        cmd_fsm.act("IDLE",
            If(self.start,
                NextValue(cmd_counter, 0),
                NextState("WAIT")
            )
        )
        cmd_fsm.act("WAIT",
            If(self.run_cascade_in,
                NextState("RUN")
            )
        )
        cmd_fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                self.run_cascade_out.eq(1),
                addr_gen.ce.eq(1),
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (self.length[ashift:] - 1),
                    NextState("DONE")
                ).Elif(~self.run_cascade_in,
                    NextState("WAIT")
                )
            )
        )
        cmd_fsm.act("DONE")

        if isinstance(dram_port, LiteDRAMNativePort): # addressing in dwords
            dma_sink_addr = dma.sink.address
        elif isinstance(dram_port, LiteDRAMAXIPort):  # addressing in bytes
            dma_sink_addr = dma.sink.address[ashift:]
        else:
            raise NotImplementedError

        self.comb += dma_sink_addr.eq(self.base[ashift:] + (addr_gen.o & addr_mask))

        # Data FSM ---------------------------------------------------------------------------------
        data_counter = Signal(dram_port.address_width, reset_less=True)

        data_fsm = FSM(reset_state="IDLE")
        self.submodules += data_fsm
        data_fsm.act("IDLE",
            If(self.start,
                NextValue(data_counter, 0),
                NextValue(self.errors, 0),
                NextState("RUN")
            ),
            NextValue(self.ticks, 0)
        )

        data_fsm.act("RUN",
            dma.source.ready.eq(1),
            If(dma.source.valid,
                data_gen.ce.eq(1),
                NextValue(data_counter, data_counter + 1),
                If(dma.source.data != data_gen.o[:min(len(data_gen.o), dram_port.data_width)],
                    NextValue(self.errors, self.errors + 1)
                ),
                If(data_counter == (self.length[ashift:] - 1),
                    NextState("DONE")
                )
            ),
            NextValue(self.ticks, self.ticks + 1)
        )
        data_fsm.act("DONE",
            self.done.eq(1)
        )

@ResetInserter()
class _LiteDRAMPatternChecker(Module, AutoCSR):
    def __init__(self, dram_port, init=[]):
        ashift, awidth = get_ashift_awidth(dram_port)
        self.start  = Signal()
        self.done   = Signal()
        self.ticks  = Signal(32)
        self.errors = Signal(32)

        self.run_cascade_in  = Signal(reset=1)
        self.run_cascade_out = Signal()

        # # #

        # Data / Address pattern -------------------------------------------------------------------
        addr_init, data_init = zip(*init)
        addr_mem = Memory(dram_port.address_width, len(addr_init), init=addr_init)
        data_mem = Memory(dram_port.data_width,    len(data_init), init=data_init)
        addr_port = addr_mem.get_port(async_read=True)
        data_port = data_mem.get_port(async_read=True)
        self.specials += addr_mem, data_mem, addr_port, data_port

        # DMA --------------------------------------------------------------------------------------
        dma = LiteDRAMDMAReader(dram_port)
        self.submodules += dma

        # Address FSM ------------------------------------------------------------------------------
        cmd_counter = Signal(dram_port.address_width, reset_less=True)

        cmd_fsm = FSM(reset_state="IDLE")
        self.submodules += cmd_fsm
        cmd_fsm.act("IDLE",
            If(self.start,
                NextValue(cmd_counter, 0),
                If(self.run_cascade_in,
                    NextState("RUN")
                ).Else(
                    NextState("WAIT")
                )
            )
        )
        cmd_fsm.act("WAIT",
            If(self.run_cascade_in,
                NextState("RUN")
            ),
            NextValue(self.ticks, self.ticks + 1)
        )
        cmd_fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                self.run_cascade_out.eq(1),
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (len(init) - 1),
                    NextState("DONE")
                ).Elif(~self.run_cascade_in,
                    NextState("WAIT")
                )
            )
        )
        cmd_fsm.act("DONE")

        if isinstance(dram_port, LiteDRAMNativePort): # addressing in dwords
            dma_sink_addr = dma.sink.address
        elif isinstance(dram_port, LiteDRAMAXIPort):  # addressing in bytes
            dma_sink_addr = dma.sink.address[ashift:]
        else:
            raise NotImplementedError

        self.comb += [
            addr_port.adr.eq(cmd_counter),
            dma_sink_addr.eq(addr_port.dat_r),
        ]

        # Data FSM ---------------------------------------------------------------------------------
        data_counter = Signal(dram_port.address_width, reset_less=True)

        expected_data = Signal.like(dma.source.data)
        self.comb += [
            data_port.adr.eq(data_counter),
            expected_data.eq(data_port.dat_r),
        ]

        data_fsm = FSM(reset_state="IDLE")
        self.submodules += data_fsm
        data_fsm.act("IDLE",
            If(self.start,
                NextValue(data_counter, 0),
                NextValue(self.errors, 0),
                NextState("RUN")
            ),
            NextValue(self.ticks, 0)
        )

        data_fsm.act("RUN",
            dma.source.ready.eq(1),
            If(dma.source.valid,
                NextValue(data_counter, data_counter + 1),
                If(dma.source.data != expected_data,
                    NextValue(self.errors, self.errors + 1)
                ),
                If(data_counter == (len(init) - 1),
                    NextState("DONE")
                )
            ),
            NextValue(self.ticks, self.ticks + 1)
        )
        data_fsm.act("DONE",
            self.done.eq(1)
        )

# LiteDRAMBISTChecker ------------------------------------------------------------------------------

class LiteDRAMBISTChecker(Module, AutoCSR):
    """DRAM memory pattern checker.

    Attributes
    ----------
    reset : in
        Reset the module
    start : in
        Start the checking

    done : out
        The module has completed checking

    base : in
        DRAM address to start from.
    end : in
        Max DRAM address.
    length : in
        Number of DRAM words to check.

    random_data : in
        Enable random data (LFSR)
    random_addr : in
        Enable random address (LFSR). Wrapped to (end - base), so may not be unique.

    ticks: out
        Duration of the check.

    errors : out
        Number of DRAM words which don't match.
    """
    def __init__(self, dram_port):
        ashift, awidth = get_ashift_awidth(dram_port)
        self.reset       = CSR()
        self.start       = CSR()
        self.done        = CSRStatus()
        self.base        = CSRStorage(awidth)
        self.end         = CSRStorage(awidth)
        self.length      = CSRStorage(awidth)
        self.random      = CSRStorage(fields=[
            CSRField("data", size=1),
            CSRField("addr", size=1),
        ])
        self.ticks       = CSRStatus(32)
        self.errors      = CSRStatus(32)

        # # #

        clock_domain = dram_port.clock_domain

        core = _LiteDRAMBISTChecker(dram_port)
        core = ClockDomainsRenamer(clock_domain)(core)
        self.submodules.core = core

        if clock_domain != "sys":
            control_layout = [
                ("reset", 1),
                ("start", 1),
                ("base",   awidth),
                ("end",    awidth),
                ("length", awidth),
                ("random_data", 1),
                ("random_addr", 1),
            ]
            status_layout = [
                ("done",    1),
                ("ticks",  32),
                ("errors", 32),
            ]
            control_cdc = stream.AsyncFIFO(control_layout)
            control_cdc = ClockDomainsRenamer({"write" : "sys", "read": clock_domain})(control_cdc)
            status_cdc  = stream.AsyncFIFO(status_layout)
            status_cdc  = ClockDomainsRenamer({"write" : clock_domain, "read": "sys"})(status_cdc)
            self.submodules += control_cdc, status_cdc
            # Control CDC In
            self.comb += [
                control_cdc.sink.valid.eq(self.reset.re | self.start.re),
                control_cdc.sink.reset.eq(self.reset.re),
                control_cdc.sink.start.eq(self.start.re),
                control_cdc.sink.base.eq(self.base.storage),
                control_cdc.sink.end.eq(self.end.storage),
                control_cdc.sink.length.eq(self.length.storage),
                control_cdc.sink.random_data.eq(self.random.fields.data),
                control_cdc.sink.random_addr.eq(self.random.fields.addr),
            ]
            # Control CDC Out
            self.comb += [
                control_cdc.source.ready.eq(1),
                core.reset.eq(control_cdc.source.valid & control_cdc.source.reset),
                core.start.eq(control_cdc.source.valid & control_cdc.source.start),
            ]
            self.sync += [
                If(control_cdc.source.valid,
                    core.base.eq(control_cdc.source.base),
                    core.end.eq(control_cdc.source.end),
                    core.length.eq(control_cdc.source.length),
                    core.random_data.eq(control_cdc.source.random_data),
                    core.random_addr.eq(control_cdc.source.random_addr),
                )
            ]
            # Status CDC In
            self.comb += [
                status_cdc.sink.valid.eq(1),
                status_cdc.sink.done.eq(core.done),
                status_cdc.sink.ticks.eq(core.ticks),
                status_cdc.sink.errors.eq(core.errors),
            ]
            # Status CDC Out
            self.comb += status_cdc.source.ready.eq(1)
            self.sync += [
                If(status_cdc.source.valid,
                    self.done.status.eq(status_cdc.source.done),
                    self.ticks.status.eq(status_cdc.source.ticks),
                    self.errors.status.eq(status_cdc.source.errors),
                )
            ]
        else:
            self.comb += [
                core.reset.eq(self.reset.re),
                core.start.eq(self.start.re),
                self.done.status.eq(core.done),
                core.base.eq(self.base.storage),
                core.end.eq(self.end.storage),
                core.length.eq(self.length.storage),
                core.random_data.eq(self.random.fields.data),
                core.random_addr.eq(self.random.fields.addr),
                self.ticks.status.eq(core.ticks),
                self.errors.status.eq(core.errors),
            ]
