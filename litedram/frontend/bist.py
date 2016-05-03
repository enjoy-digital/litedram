from functools import reduce
from operator import xor

from litex.gen import *

from litex.soc.interconnect.csr import *

from litedram.frontend.dma import LiteDRAMDMAWriter, LiteDRAMDMAReader


@ResetInserter()
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


class LiteDRAMBISTGenerator(Module, AutoCSR):
    def __init__(self, dram_port):
        self.reset = CSR()
        self.shoot = CSR()
        self.done = CSRStatus()
        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)

        # # #

        self.submodules.dma = dma = LiteDRAMDMAWriter(dram_port)

        self.submodules.lfsr = lfsr = LFSR(dram_port.dw)
        self.comb += lfsr.reset.eq(self.reset.re)

        enable = Signal()
        counter = Signal(dram_port.aw)
        self.comb += enable.eq(counter != 0)
        self.sync += [
            If(self.shoot.re,
                counter.eq(self.length.storage)
            ).Elif(lfsr.ce,
                counter.eq(counter - 1)
            )
        ]

        self.comb += [
            dma.sink.valid.eq(enable),
            dma.sink.address.eq(self.base.storage + counter),
            dma.sink.data.eq(lfsr.o),
            lfsr.ce.eq(enable & dma.sink.ready),

            self.done.status.eq(~enable)
        ]


class LiteDRAMBISTChecker(Module, AutoCSR):
    def __init__(self, dram_port):
        self.reset = CSR()
        self.shoot = CSR()
        self.done = CSRStatus()
        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)
        self.error_count = CSRStatus(dram_port.aw)

        # # #

        self.submodules.dma = dma = LiteDRAMDMAReader(dram_port)

        # # #

        self.submodules.lfsr = lfsr = LFSR(dram_port.dw)
        self.comb += lfsr.reset.eq(self.reset.re)

        address_counter = Signal(dram_port.aw)
        address_counter_ce = Signal()
        data_counter = Signal(dram_port.aw)
        data_counter_ce = Signal()
        self.sync += [
            If(self.shoot.re,
                address_counter.eq(self.length.storage)
            ).Elif(address_counter_ce,
                address_counter.eq(address_counter - 1)
            ),
            If(self.shoot.re,
                data_counter.eq(self.length.storage)
            ).Elif(data_counter_ce,
                data_counter.eq(data_counter - 1)
            )
        ]

        address_enable = Signal()
        self.comb += address_enable.eq(address_counter != 0)

        self.comb += [
            dma.sink.valid.eq(address_enable),
            dma.sink.address.eq(self.base.storage + address_counter),
            address_counter_ce.eq(address_enable & dma.sink.ready)
        ]

        data_enable = Signal()
        self.comb += data_enable.eq(data_counter != 0)

        self.comb += [
            lfsr.ce.eq(dma.source.valid),
            dma.source.ready.eq(1)
        ]
        err_cnt = self.error_count.status
        self.sync += \
            If(self.reset.re,
                err_cnt.eq(0)
            ).Elif(dma.source.valid,
                If(dma.source.data != lfsr.o,
                    err_cnt.eq(err_cnt + 1)
                )
            )
        self.comb += data_counter_ce.eq(dma.source.valid)

        self.comb += self.done.status.eq(~data_enable & ~address_enable)
