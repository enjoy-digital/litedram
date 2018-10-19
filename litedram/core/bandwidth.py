"""LiteDRAM Bandwidth."""

from migen import *

from litex.soc.interconnect.csr import *


class Bandwidth(Module, AutoCSR):
    def __init__(self, cmd, data_width, period_bits=24):
        self.update = CSR()
        self.nreads = CSRStatus(period_bits)
        self.nwrites = CSRStatus(period_bits)
        self.data_width = CSRStatus(bits_for(data_width), reset=data_width)

        # # #

        cmd_valid = Signal()
        cmd_ready = Signal()
        cmd_is_read = Signal()
        cmd_is_write = Signal()
        self.sync += [
            cmd_valid.eq(cmd.valid),
            cmd_ready.eq(cmd.ready),
            cmd_is_read.eq(cmd.is_read),
            cmd_is_write.eq(cmd.is_write)
        ]

        counter = Signal(period_bits)
        period = Signal()
        nreads = Signal(period_bits)
        nwrites = Signal(period_bits)
        nreads_r = Signal(period_bits)
        nwrites_r = Signal(period_bits)
        self.sync += [
            Cat(counter, period).eq(counter + 1),
            If(period,
                nreads_r.eq(nreads),
                nwrites_r.eq(nwrites),
                nreads.eq(0),
                nwrites.eq(0)
            ).Elif(cmd_valid & cmd_ready,
                If(cmd_is_read, nreads.eq(nreads + 1)),
                If(cmd_is_write, nwrites.eq(nwrites + 1)),
            ),
            If(self.update.re,
                self.nreads.status.eq(nreads_r),
                self.nwrites.status.eq(nwrites_r)
            )
        ]
