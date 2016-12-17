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

        cmd_counter = Signal(dram_port.aw)

        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm

        fsm.act("IDLE",
            self.done.eq(1),
            If(self.start,
                NextValue(cmd_counter, 0),
                NextState("RUN")
            )
        )
        fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                gen.ce.eq(1),
                NextValue(cmd_counter, cmd_counter + 1),
                If(cmd_counter == (self.length-1),
                    NextState("IDLE")
                )
            )
        )
        self.comb += [
            dma.sink.address.eq(self.base + cmd_counter),
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
        self.err_count = Signal(32)

        # # #

        self.submodules.dma = dma = LiteDRAMDMAReader(dram_port)
        gen_cls = LFSR if random else Counter
        self.submodules.gen = gen = gen_cls(dram_port.dw)

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
                If(cmd_counter == (self.length-1),
                    NextState("IDLE")
                )
            )
        )
        self.comb += dma.sink.address.eq(self.base + cmd_counter)

        # data
        data_counter = Signal(dram_port.aw)
        data_fsm = FSM(reset_state="IDLE")
        self.submodules += data_fsm

        data_fsm.act("IDLE",
            If(self.start,
                NextValue(data_counter, 0),
                NextValue(self.err_count, 0),
                NextState("RUN")
            )
        )
        data_fsm.act("RUN",
            dma.source.ready.eq(1),
            If(dma.source.valid,
                gen.ce.eq(1),
                NextValue(data_counter, data_counter + 1),
                If(dma.source.data != gen.o,
                    NextValue(self.err_count, self.err_count + 1)
                ),
                If(data_counter == (self.length-1),
                    NextState("IDLE")
                )
            )
        )

        self.comb += self.done.eq(cmd_fsm.ongoing("IDLE") &
                                  data_fsm.ongoing("IDLE"))


class LiteDRAMBISTChecker(Module, AutoCSR):
    def __init__(self, dram_port, random=True):
        self.reset = CSR()
        self.start = CSR()
        self.done = CSRStatus()
        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)
        self.err_count = CSRStatus(32)

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
        err_count_sync = BusSynchronizer(32, cd, "sys")
        self.submodules += base_sync, length_sync, err_count_sync

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

            err_count_sync.i.eq(core.err_count),
            self.err_count.status.eq(err_count_sync.o)
        ]
