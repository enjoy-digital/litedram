# 1:1 frequency-ratio Generic SDR PHY
#
# The SDR PHY needs 2 Clock domains:
#  - sys_clk    : The System Clock domain
#  - sys_clk_ps : The System Clock domain with its phase shifted by -3ns at 100Mhz
#
# Assert dfi_wrdata_en and present the data on dfi_wrdata_mask/dfi_wrdata in the
# same cycle as the write command.
#
# Assert dfi_rddata_en in the same cycle as the read command. The data will come
# back on dfi_rddata 4 cycles later, along with the assertion of dfi_rddata_valid.
#
# This SDR PHY only supports CAS Latency 2.
#

from migen import *
from migen.genlib.record import *
from migen.fhdl.specials import Tristate

from litedram.common import PhySettings
from litedram.phy.dfi import *


class GENSDRPHY(Module):
    def __init__(self, pads):
        addressbits = len(pads.a)
        bankbits = len(pads.ba)
        nranks = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits = len(pads.dq)

        self.settings = PhySettings(
            memtype="SDR",
            dfi_databits=databits,
            nranks=nranks,
            nphases=1,
            rdphase=0,
            wrphase=0,
            rdcmdphase=0,
            wrcmdphase=0,
            cl=2,
            read_latency=4,
            write_latency=0
        )

        self.dfi = dfi = Interface(addressbits, bankbits, nranks, databits)

        # # #

        # Command/address
        self.sync += [
            pads.a.eq(dfi.p0.address),
            pads.ba.eq(dfi.p0.bank),
            pads.cke.eq(dfi.p0.cke),
            pads.cas_n.eq(dfi.p0.cas_n),
            pads.ras_n.eq(dfi.p0.ras_n),
            pads.we_n.eq(dfi.p0.we_n)
        ]
        if hasattr(pads, "cs_n"):
            self.sync += pads.cs_n.eq(dfi.p0.cs_n)

        # DQ/DQS/DM data
        dq_o = Signal(databits)
        dq_oe = Signal()
        dq_i = Signal(databits)
        self.sync += dq_o.eq(dfi.p0.wrdata)
        self.specials += Tristate(pads.dq, dq_o, dq_oe, dq_i)
        self.sync += \
            If(dfi.p0.wrdata_en,
                pads.dm.eq(dfi.p0.wrdata_mask)
            ).Else(
                pads.dm.eq(0)
            )
        dq_in = Signal(databits)
        self.sync.sys_ps += dq_in.eq(dq_i)
        self.sync += dfi.p0.rddata.eq(dq_in)

        # DQ/DM control
        wrdata_en = Signal()
        self.sync += wrdata_en.eq(dfi.p0.wrdata_en)
        self.comb += dq_oe.eq(wrdata_en)

        rddata_en = Signal(4)
        self.sync += rddata_en.eq(Cat(dfi.p0.rddata_en, rddata_en[:3]))
        self.comb += dfi.p0.rddata_valid.eq(rddata_en[3])
