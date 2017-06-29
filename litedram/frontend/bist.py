"""Built In Self Test (BIST) modules for testing liteDRAM functionality."""

from functools import reduce
from operator import xor

from litex.gen import *
from litex.gen.genlib.cdc import PulseSynchronizer, BusSynchronizer

from litex.soc.interconnect.csr import *

from litedram.frontend.dma import LiteDRAMDMAWriter, LiteDRAMDMAReader


@CEInserter()
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
    o : in
        Output data
    """
    def __init__(self, n_out, n_state=31, taps=[27, 30]):
        self.o = Signal(n_out)

        # # #

        state = Signal(n_state)
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


@CEInserter()
class Counter(Module):
    """Simple incremental counter.

    Parameters
    ----------
    n_out : int
        Width of the output data signal.

    Attributes
    ----------
    o : in
        Output data
    """
    def __init__(self, n_out):
        self.o = Signal(n_out)

        # # #

        self.sync += self.o.eq(self.o + 1)


@ResetInserter()
class _LiteDRAMBISTGenerator(Module):
    def __init__(self, dram_port, random):
        self.start = Signal()
        self.done = Signal()
        self.base = Signal(dram_port.aw)
        self.length = Signal(dram_port.aw)
        self.ticks = Signal(32)

        # # #

        gen_cls = LFSR if random else Counter
        gen = gen_cls(dram_port.dw)
        dma = LiteDRAMDMAWriter(dram_port)
        self.submodules += dma, gen

        cmd_counter = Signal(dram_port.aw)

        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm
        fsm.act("IDLE",
            If(self.start,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            ),
            NextValue(self.ticks, 0)
        )
        fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                gen.ce.eq(1),
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (self.length - 1),
                    NextState("DONE")
                )
            ),
            NextValue(self.ticks, self.ticks + 1)
        )
        fsm.act("DONE",
            self.done.eq(1)
        )
        self.comb += [
            dma.sink.address.eq(self.base + cmd_counter),
            dma.sink.data.eq(gen.o)
        ]


class LiteDRAMBISTGenerator(Module, AutoCSR):
    """DRAM memory pattern generator.

    Attributes
    ----------
    reset : in
        Reset the module.
    start : in
        Start the generation.

    base : in
        DRAM address to start from.
    length : in
        Number of DRAM words to write.

    done : out
        The module has completed writing the pattern.

    ticks : out
        Duration of the generation.
    """
    def __init__(self, dram_port, random=True):
        self.reset = CSR()
        self.start = CSR()
        self.done = CSRStatus()
        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)
        self.ticks = CSRStatus(32)

        # # #

        cd = dram_port.cd

        core = _LiteDRAMBISTGenerator(dram_port, random)
        core = ClockDomainsRenamer(cd)(core)
        self.submodules += core

        reset_sync = PulseSynchronizer("sys", cd)
        start_sync = PulseSynchronizer("sys", cd)
        self.submodules += reset_sync, start_sync
        self.comb += [
            reset_sync.i.eq(self.reset.re),
            core.reset.eq(reset_sync.o),

            start_sync.i.eq(self.start.re),
            core.start.eq(start_sync.o)
        ]

        done_sync = BusSynchronizer(1, cd, "sys")
        self.submodules += done_sync
        self.comb += [
            done_sync.i.eq(core.done),
            self.done.status.eq(done_sync.o)
        ]

        base_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        length_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        self.submodules += base_sync, length_sync
        self.comb += [
            base_sync.i.eq(self.base.storage),
            core.base.eq(base_sync.o),

            length_sync.i.eq(self.length.storage),
            core.length.eq(length_sync.o)
        ]

        ticks_sync = BusSynchronizer(32, cd, "sys")
        self.submodules += ticks_sync
        self.comb += [
            ticks_sync.i.eq(core.ticks),
            self.ticks.status.eq(ticks_sync.o)
        ]


@ResetInserter()
class _LiteDRAMBISTChecker(Module, AutoCSR):
    def __init__(self, dram_port, random):
        self.start = Signal()
        self.done = Signal()
        self.base = Signal(dram_port.aw)
        self.length = Signal(dram_port.aw)
        self.ticks = Signal(32)
        self.errors = Signal(32)

        # # #

        gen_cls = LFSR if random else Counter
        gen = gen_cls(dram_port.dw)
        dma = LiteDRAMDMAReader(dram_port)
        self.submodules += dma, gen

        # address
        cmd_counter = Signal(dram_port.aw)

        cmd_fsm = FSM(reset_state="IDLE")
        self.submodules += cmd_fsm
        cmd_fsm.act("IDLE",
            If(self.start,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            )
        )
        cmd_fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (self.length - 1),
                    NextState("DONE")
                )
            )
        )
        cmd_fsm.act("DONE")
        self.comb += dma.sink.address.eq(self.base + cmd_counter)

        # data
        data_counter = Signal(dram_port.aw)

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
                gen.ce.eq(1),
                NextValue(data_counter, data_counter + 1),
                If(dma.source.data != gen.o,
                    NextValue(self.errors, self.errors + 1)
                ),
                If(data_counter == (self.length - 1),
                    NextState("DONE")
                )
            ),
            NextValue(self.ticks, self.ticks + 1)
        )
        data_fsm.act("DONE",
            self.done.eq(1)
        )


class LiteDRAMBISTChecker(Module, AutoCSR):
    """DRAM memory pattern checker.

    Attributes
    ----------
    reset : in
        Reset the module
    start : in
        Start the checking

    base : in
        DRAM address to start from.
    length : in
        Number of DRAM words to check.

    done : out
        The module has completed checking

    ticks: out
        Duration of the check.

    errors : out
        Number of DRAM words which don't match.
    """
    def __init__(self, dram_port, random=True):
        self.reset = CSR()
        self.start = CSR()
        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)
        self.done = CSRStatus()
        self.ticks = CSRStatus(32)
        self.errors = CSRStatus(32)

        # # #

        cd = dram_port.cd

        core = _LiteDRAMBISTChecker(dram_port, random)
        core = ClockDomainsRenamer(cd)(core)
        self.submodules += core

        reset_sync = PulseSynchronizer("sys", cd)
        start_sync = PulseSynchronizer("sys", cd)
        self.submodules += reset_sync, start_sync
        self.comb += [
            reset_sync.i.eq(self.reset.re),
            core.reset.eq(reset_sync.o),

            start_sync.i.eq(self.start.re),
            core.start.eq(start_sync.o)
        ]

        done_sync = BusSynchronizer(1, cd, "sys")
        self.submodules += done_sync
        self.comb += [
            done_sync.i.eq(core.done),
            self.done.status.eq(done_sync.o)
        ]

        base_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        length_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        self.submodules += base_sync, length_sync
        self.comb += [
            base_sync.i.eq(self.base.storage),
            core.base.eq(base_sync.o),

            length_sync.i.eq(self.length.storage),
            core.length.eq(length_sync.o)
        ]

        ticks_sync = BusSynchronizer(32, cd, "sys")
        self.submodules += ticks_sync
        self.comb += [
            ticks_sync.i.eq(core.ticks),
            self.ticks.status.eq(ticks_sync.o)
        ]

        errors_sync = BusSynchronizer(32, cd, "sys")
        self.submodules += errors_sync
        self.comb += [
            errors_sync.i.eq(core.errors),
            self.errors.status.eq(errors_sync.o)
        ]
