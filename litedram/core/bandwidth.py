# This file is Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# This file is Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2018 John Sully <john@csquare.ca>
# License: BSD

"""LiteDRAM Bandwidth."""

from migen import *

from litex.soc.interconnect.csr import *

# Bandwidth ----------------------------------------------------------------------------------------

class Bandwidth(Module, AutoCSR):
    def __init__(self, cmd_read_write, cmd_act_precharge, data_width, period_bits=24):
        self.update = CSR()
        self.nreads = CSRStatus(period_bits)
        self.nwrites = CSRStatus(period_bits)
        self.nactivates = CSRStatus(period_bits)
        self.data_width = CSRStatus(bits_for(data_width), reset=data_width)

        # # #

        cmd_valid    = Signal()
        cmd_ready    = Signal()
        cmd_is_read  = Signal()
        cmd_is_write = Signal()

        cmd_act_valid = Signal()
        cmd_act_ready = Signal()
        cmd_act_is_act = Signal()
        self.sync += [
            cmd_valid.eq(cmd_read_write.valid),
            cmd_ready.eq(cmd_read_write.ready),
            cmd_is_read.eq(cmd_read_write.is_read),
            cmd_is_write.eq(cmd_read_write.is_write),

            cmd_act_valid.eq(cmd_act_precharge.valid),
            cmd_act_ready.eq(cmd_act_precharge.ready),
            cmd_act_is_act.eq(cmd_act_precharge.ras & ~cmd_act_precharge.cas & ~cmd_act_precharge.we),
        ]

        counter = Signal(period_bits)
        period = Signal()
        nreads = Signal(period_bits)
        nwrites = Signal(period_bits)
        nacts = Signal(period_bits)
        nreads_r = Signal(period_bits)
        nwrites_r = Signal(period_bits)
        nacts_r = Signal(period_bits)

        self.sync += [
            Cat(counter, period).eq(counter + 1),
            If(self.update.re,
                self.nreads.status.eq(nreads),
                self.nwrites.status.eq(nwrites),
                self.nactivates.status.eq(nacts),
                nreads.eq(0),
                nwrites.eq(0),
                nacts.eq(0),
            ).Else(
                If(cmd_valid & cmd_ready,
                    If(cmd_is_read, nreads.eq(nreads + 1)),
                    If(cmd_is_write, nwrites.eq(nwrites + 1)),
                ),
                If(cmd_act_valid,  # cmd_act_ready never gets activated
                    If(cmd_act_is_act, nacts.eq(nacts + 1))
                )
            ),
        ]
