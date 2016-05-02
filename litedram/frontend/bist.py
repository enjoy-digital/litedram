from functools import reduce
from operator import xor

from litex.gen import *

from litex.soc.interconnect.csr import *

from litedram.frontend import dma

# TODO: implement or replace DMAControllers in MiSoC


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


memtest_magic = 0x361f


class LiteDRAMBISTGenerator(Module):
    def __init__(self, port):
        self._magic = CSRStatus(16)
        self._reset = CSR()
        self._shoot = CSR()
        self.submodules._dma = DMAWriteController(dma.Writer(port),
                                                  MODE_EXTERNAL)

        # # #

        self.comb += self._magic.status.eq(memtest_magic)

        lfsr = LFSR(port.dw)
        self.submodules += lfsr
        self.comb += lfsr.reset.eq(self._reset.re)

        en = Signal()
        en_counter = Signal(port.aw)
        self.comb += en.eq(en_counter != 0)
        self.sync += [
            If(self._shoot.re,
                en_counter.eq(self._dma.length)
            ).Elif(lfsr.ce,
                en_counter.eq(en_counter - 1)
            )
        ]

        self.comb += [
            self._dma.trigger.eq(self._shoot.re),
            self._dma.data.valid.eq(en),
            lfsr.ce.eq(en & self._dma.data.ready),
            self._dma.data.d.eq(lfsr.o)
        ]

    def get_csrs(self):
        return [self._magic, self._reset, self._shoot] + self._dma.get_csrs()


class LiteDRAMBISTChecker(Module):
    def __init__(self, port):
        self._magic = CSRStatus(16)
        self._reset = CSR()
        self._error_count = CSRStatus(port.aw)
        self.submodules._dma = DMAReadController(dma.Reader(port),
                                                 MODE_SINGLE_SHOT)

        # # #

        self.comb += self._magic.status.eq(memtest_magic)

        lfsr = LFSR(port.dw)
        self.submodules += lfsr
        self.comb += lfsr.reset.eq(self._reset.re)

        self.comb += [
            lfsr.ce.eq(self._dma.data.valid),
            self._dma.data.ready.eq(1)
        ]
        err_cnt = self._error_count.status
        self.sync += [
            If(self._reset.re,
                err_cnt.eq(0)
            ).Elif(self._dma.data.valid,
                If(self._dma.data.d != lfsr.o, err_cnt.eq(err_cnt + 1))
            )
        ]

    def get_csrs(self):
        return [self._magic, self._reset, self._error_count] + self._dma.get_csrs()
