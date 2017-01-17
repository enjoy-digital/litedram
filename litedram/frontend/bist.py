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
        ???
    taps : list of int
        ???

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

        # # #

        self.submodules.dma = dma = LiteDRAMDMAWriter(dram_port)
        gen_cls = LFSR if random else Counter
        self.submodules.gen = gen = gen_cls(dram_port.dw)

        self.cmd_counter = cmd_counter = Signal(dram_port.aw)

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(self.start,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            ),
        )
        fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                gen.ce.eq(1),
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (self.length-1),
                    NextState("DONE")
                ),
            ),
        )
        fsm.act("DONE",
            self.done.eq(1),
        )
        self.comb += [
            dma.sink.address.eq(self.base + cmd_counter),
            dma.sink.data.eq(gen.o)
        ]


class LiteDRAMBISTGenerator(Module, AutoCSR):
    """litex module to generate a given pattern in memory.abs

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
    """

    def __init__(self, dram_port, random=True):
        self.reset = CSR()
        self.start = CSR()
        self.done = CSRStatus()
        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)

        # # #

        cd = dram_port.cd

        core = _LiteDRAMBISTGenerator(dram_port, random)
        self.submodules.core = ClockDomainsRenamer(cd)(core)

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


@ResetInserter()
class _LiteDRAMBISTChecker(Module, AutoCSR):

    def __init__(self, dram_port, random):
        self.start = Signal()
        self.done = Signal()

        self.base = Signal(dram_port.aw)
        self.length = Signal(dram_port.aw)

        self.errors = Signal(32)

        # # #

        self.submodules.dma = dma = LiteDRAMDMAReader(dram_port)
        gen_cls = LFSR if random else Counter
        self.submodules.gen = gen = gen_cls(dram_port.dw)

        # address
        self.cmd_counter = cmd_counter = Signal(dram_port.aw)
        self.submodules.cmd_fsm = cmd_fsm = FSM(reset_state="IDLE")

        cmd_fsm.act("IDLE",
            If(self.start,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            ),
        )
        cmd_fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (self.length-1),
                    NextState("DONE")
                ),
            ),
        )
        cmd_fsm.act("DONE")
        self.comb += dma.sink.address.eq(self.base + cmd_counter)

        # data
        self.data_counter = data_counter = Signal(dram_port.aw)
        self.submodules.data_fsm = data_fsm = FSM(reset_state="IDLE")

        data_fsm.act("IDLE",
            If(self.start,
                NextValue(data_counter, 0),
                NextValue(self.errors, 0),
                NextState("RUN")
            ),
        )
        data_fsm.act("RUN",
            dma.source.ready.eq(1),
            If(dma.source.valid,
                gen.ce.eq(1),
                NextValue(data_counter, data_counter + 1),
                If(dma.source.data != gen.o,
                    NextValue(self.errors, self.errors + 1),
                ),
                If(data_counter == (self.length-1),
                    NextState("DONE")
                ),
            ),
        )
        data_fsm.act("DONE")

        self.comb += self.done.eq(cmd_fsm.ongoing("DONE") &
                                  data_fsm.ongoing("DONE"))


class LiteDRAMBISTChecker(Module, AutoCSR):
    """litex module to check a given pattern in memory.

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

    errors : out
        Number of DRAM words which don't match.
    """

    def __init__(self, dram_port, random=True):
        self.reset = CSR()
        self.start = CSR()

        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)

        self.done = CSRStatus()
        self.errors = CSRStatus(32)

        # # #

        cd = dram_port.cd

        core = _LiteDRAMBISTChecker(dram_port, random)
        self.submodules.core = ClockDomainsRenamer(cd)(core)

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

        errors_sync = BusSynchronizer(32, cd, "sys")
        self.submodules += errors_sync
        self.comb += [
            errors_sync.i.eq(core.errors),
            self.errors.status.eq(errors_sync.o)
        ]
