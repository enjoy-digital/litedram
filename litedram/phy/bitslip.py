from litex.gen import *


class BitSlip(Module):
    def __init__(self, dw):
        self.i = Signal(dw)
        self.o = Signal(dw)
        self.value = Signal(max=dw)

        # # #

        r = Signal(2*dw)
        self.sync += r.eq(Cat(r[dw:], self.i))
        cases = {}
        for i in range(dw):
            cases[i] = self.o.eq(r[i:dw+i])
        self.sync += Case(self.value, cases)
