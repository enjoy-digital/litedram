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
        self.sync += self.o.eq(self.o + 1)


class _LiteDRAMBISTGenerator(Module):

    def __init__(self, dram_port, random):
        self.start = Signal()
        self.done = Signal()
        self.base = Signal(dram_port.aw)
        self.length = Signal(dram_port.aw)

        # # #

        self.submodules.dma = dma = LiteDRAMDMAWriter(dram_port)

        if random:
            self.submodules.gen = gen = LFSR(dram_port.dw)
        else:
            self.submodules.gen = gen = Counter(dram_port.dw)

        self.running = running = Signal()
        not_finished = Signal()
        counter = Signal(dram_port.aw)
        self.comb += not_finished.eq(running & (counter != (self.length - 1)))
        self.sync += [
            If(self.start,
                running.eq(1),
                counter.eq(0)
            ).Elif(gen.ce,
                counter.eq(counter + 1)
            )
        ]

        self.comb += [
            dma.sink.valid.eq(not_finished),
            dma.sink.address.eq(self.base + counter),
            dma.sink.data.eq(gen.o),
            gen.ce.eq(not_finished & dma.sink.ready),

            self.done.eq(~not_finished & running)
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

        core = ResetInserter()(_LiteDRAMBISTGenerator(dram_port, random))
        self.submodules.core = ClockDomainsRenamer(cd)(core)

        reset_sync = BusSynchronizer(1, "sys", cd)
        start_sync = PulseSynchronizer("sys", cd)
        done_sync = BusSynchronizer(1, cd, "sys")
        self.submodules += reset_sync, start_sync, done_sync

        base_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        length_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        self.submodules += base_sync, length_sync

        self.comb += [
            reset_sync.i.eq(self.reset.re),
            core.reset.eq(reset_sync.o),

            start_sync.i.eq(self.start.re),
            core.start.eq(start_sync.o),

            done_sync.i.eq(core.done),
            self.done.status.eq(done_sync.o),

            base_sync.i.eq(self.base.storage),
            core.base.eq(base_sync.o),

            length_sync.i.eq(self.length.storage),
            core.length.eq(length_sync.o)
        ]


class _LiteDRAMBISTChecker(Module, AutoCSR):

    def __init__(self, dram_port, random):
        self.start = Signal()

        self.base = Signal(dram_port.aw)
        self.length = Signal(dram_port.aw)

        self.error_count = Signal(32)

        self.running = running = Signal()
        self.done = Signal()

        self.submodules.dma = dma = LiteDRAMDMAReader(dram_port)

        # Address generation
        self._address_counter = address_counter = Signal(dram_port.aw)
        address_not_finished = Signal()
        address_counter_ce = Signal()
        self.comb += [
            address_not_finished.eq(running & (address_counter != (self.length - 1))),
            address_counter_ce.eq(address_not_finished & dma.sink.ready),

            dma.sink.valid.eq(address_not_finished),
            dma.sink.address.eq(self.base + address_counter),
        ]
        self.sync += [
            If(address_counter_ce,
                address_counter.eq(address_counter + 1)
            ),
        ]

        # Data receiving 
        self._data_counter = data_counter = Signal(dram_port.aw)
        data_not_finished = Signal()
        data_counter_ce = Signal()
        self.comb += [
            data_not_finished.eq(running & (data_counter != address_counter)),
            data_counter_ce.eq(data_not_finished & dma.source.valid),

            dma.source.ready.eq(data_counter_ce),
        ]
        self.sync += [
            If(data_counter_ce, data_counter.eq(data_counter + 1)),
        ]

        # Data checking
        if random:
            self.submodules.gen = gen = LFSR(dram_port.dw)
        else:
            self.submodules.gen = gen = Counter(dram_port.dw)
        self.comb += [
            gen.ce.eq(data_counter_ce),
        ]

        self.expected = expected = Signal(dram_port.dw)
        self.comb += [
            expected.eq(gen.o),
        ]
        self.actual = actual = Signal(dram_port.dw)
        self.comb += [
            actual.eq(dma.source.data),
        ]

        self.error = error = Signal()
        self.comb += [
            error.eq(data_counter_ce & (expected != actual)),
        ]
        self.sync += [
            If(error, self.error_count.eq(self.error_count + 1)),
        ]

        # States
        self.sync += If(self.start, running.eq(1))
        self.comb += self.done.eq(~data_not_finished & ~address_not_finished & running)


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

    error_count : out
        Number of DRAM words which don't match.
    """

    def __init__(self, dram_port, random=True):
        self.reset = CSR()
        self.start = CSR()

        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)
        self.halt_on_error = CSRStorage()

        self.done = CSRStatus()

        self.error_count = CSRStatus(32)

        # # #

        cd = dram_port.cd

        core = ResetInserter()(_LiteDRAMBISTChecker(dram_port, random))
        self.submodules.core = ClockDomainsRenamer(cd)(core)

        #reset_sync = PulseSynchronizer("sys", cd)
        reset_sync = BusSynchronizer(1, "sys", cd)
        start_sync = PulseSynchronizer("sys", cd)
        self.submodules += reset_sync, start_sync
        self.comb += [
            reset_sync.i.eq(self.reset.re),
            core.reset.eq(reset_sync.o),

            start_sync.i.eq(self.start.re),
            core.start.eq(start_sync.o),
        ]

        done_sync = BusSynchronizer(1, cd, "sys")
        self.submodules += done_sync
        self.comb += [
            done_sync.i.eq(core.done),
            self.done.status.eq(done_sync.o),
        ]

        base_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        length_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        self.submodules += base_sync, length_sync
        self.comb += [
            base_sync.i.eq(self.base.storage),
            core.base.eq(base_sync.o),

            length_sync.i.eq(self.length.storage),
            core.length.eq(length_sync.o),
        ]

        error_count_sync = BusSynchronizer(32, cd, "sys")
        self.submodules += error_count_sync
        self.comb += [
            error_count_sync.i.eq(core.error_count),
            self.error_count.status.eq(error_count_sync.o),
        ]
