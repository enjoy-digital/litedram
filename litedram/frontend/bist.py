from functools import reduce
from operator import xor

from litex.gen import *
from litex.gen.genlib.cdc import PulseSynchronizer, BusSynchronizer

from litex.soc.interconnect.csr import *

from litedram.frontend.dma import LiteDRAMDMAWriter, LiteDRAMDMAReader


@CEInserter()
class LFSR(Module):
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
	def __init__(self, n_out):
		self.o = Signal(n_out)

		# # #

		self.sync += self.o.eq(self.o + 1)


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

        offset = Signal(dram_port.aw)

        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm

        fsm.act("IDLE",
            self.done.eq(1),
            If(self.start,
                NextValue(offset, 0),
                NextState("RUN")
            )
        )
        fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                gen.ce.eq(1),
                NextValue(offset, offset + 1),
                If(offset == (self.length-1),
                    NextState("IDLE")
                )
            )
        )
        self.comb += [
            dma.sink.address.eq(self.base + offset),
            dma.sink.data.eq(gen.o)
        ]


class LiteDRAMBISTGenerator(Module, AutoCSR):
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
        self.done = Signal()
        self.base = Signal(dram_port.aw)
        self.length = Signal(dram_port.aw)
        self.error_count = Signal(32)

        # # #

        self.submodules.dma = dma = LiteDRAMDMAReader(dram_port)

        if random:
        	self.submodules.gen = gen = LFSR(dram_port.dw)
        else:
        	self.submodules.gen = gen = Counter(dram_port.dw)

        started = Signal()
        address_counter = Signal(dram_port.aw)
        address_counter_ce = Signal()
        data_counter = Signal(dram_port.aw)
        data_counter_ce = Signal()
        self.sync += [
            If(self.start,
                started.eq(1)
            ),
            If(self.start,
                address_counter.eq(0)
            ).Elif(address_counter_ce,
                address_counter.eq(address_counter + 1)
            ),
            If(self.start,
                data_counter.eq(0),
            ).Elif(data_counter_ce,
                data_counter.eq(data_counter + 1)
            )
        ]

        address_enable = Signal()
        self.comb += address_enable.eq(started & (address_counter != (self.length - 1)))

        self.comb += [
            dma.sink.valid.eq(address_enable),
            dma.sink.address.eq(self.base + address_counter),
            address_counter_ce.eq(address_enable & dma.sink.ready)
        ]

        data_enable = Signal()
        self.comb += data_enable.eq(started & (data_counter != (self.length - 1)))

        self.comb += [
            gen.ce.eq(dma.source.valid),
            dma.source.ready.eq(1)
        ]
        self.sync += \
            If(dma.source.valid,
                If(dma.source.data != gen.o,
                    self.error_count.eq(self.error_count + 1)
                )
            )
        self.comb += data_counter_ce.eq(dma.source.valid)

        self.comb += self.done.eq(~data_enable & ~address_enable)


class LiteDRAMBISTChecker(Module, AutoCSR):
    def __init__(self, dram_port, random=True):
        self.reset = CSR()
        self.start = CSR()
        self.done = CSRStatus()
        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)
        self.error_count = CSRStatus(32)

        # # #

        cd = dram_port.cd

        core = ResetInserter()(_LiteDRAMBISTChecker(dram_port, random))
        self.submodules.core = ClockDomainsRenamer(cd)(core)

        reset_sync = BusSynchronizer(1, "sys", cd)
        start_sync = PulseSynchronizer("sys", cd)
        done_sync = BusSynchronizer(1, cd, "sys")
        self.submodules += reset_sync, start_sync, done_sync

        base_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        length_sync = BusSynchronizer(dram_port.aw, "sys", cd)
        error_count_sync = BusSynchronizer(32, cd, "sys")
        self.submodules += base_sync, length_sync, error_count_sync

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
            core.length.eq(length_sync.o),

            error_count_sync.i.eq(core.error_count),
            self.error_count.status.eq(error_count_sync.o)
        ]
