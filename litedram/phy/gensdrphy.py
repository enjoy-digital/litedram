# This file is Copyright (c) 2012-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

# 1:1 frequency-ratio Generic SDR PHY

from migen import *
from migen.genlib.record import *
from migen.fhdl.specials import Tristate

from litedram.common import *
from litedram.phy.dfi import *

# Generic SDR PHY ----------------------------------------------------------------------------------

class GENSDRPHY(Module):
    def __init__(self, pads, cl=2, cmd_latency=1):
        pads        = PHYPadsCombiner(pads)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        assert cl in [2, 3]
        assert databits%8 == 0

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            memtype       = "SDR",
            databits      = databits,
            dfi_databits  = databits,
            nranks        = nranks,
            nphases       = 1,
            rdphase       = 0,
            wrphase       = 0,
            rdcmdphase    = 0,
            wrcmdphase    = 0,
            cl            = cl,
            read_latency  = cl + cmd_latency,
            write_latency = 0
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, databits)

        # # #

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)

            # Addresses and Commands ---------------------------------------------------------------
            self.sync += [
                pads.a.eq(dfi.p0.address),
                pads.ba.eq(dfi.p0.bank),
                pads.cas_n.eq(dfi.p0.cas_n),
                pads.ras_n.eq(dfi.p0.ras_n),
                pads.we_n.eq(dfi.p0.we_n)
            ]
            if hasattr(pads, "cke"):
                self.sync += pads.cke.eq(dfi.p0.cke)
            if hasattr(pads, "cs_n"):
                self.sync += pads.cs_n.eq(dfi.p0.cs_n)

        # DQ/DQS/DM Data ---------------------------------------------------------------------------
        dq_o  = Signal(databits)
        dq_oe = Signal()
        dq_i  = Signal(databits)
        self.sync += dq_o.eq(dfi.p0.wrdata)
        for i in range(len(pads.dq)):
            self.specials += Tristate(pads.dq[i], dq_o[i], dq_oe, dq_i[i])
        if hasattr(pads, "dm"):
            assert len(pads.dm)*8 == databits
            for i in range(len(pads.dm)):
                self.sync += [
                    pads.dm[i].eq(0),
                    If(dfi.p0.wrdata_en,
                        pads.dm[i].eq(dfi.p0.wrdata_mask)
                    )
                ]
        self.sync += dfi.p0.rddata.eq(dq_i)

        # DQ/DM Control ----------------------------------------------------------------------------
        wrdata_en = Signal()
        self.sync += wrdata_en.eq(dfi.p0.wrdata_en)
        self.comb += dq_oe.eq(wrdata_en)

        rddata_en = Signal(cl + cmd_latency)
        self.sync += rddata_en.eq(Cat(dfi.p0.rddata_en, rddata_en))
        self.sync += dfi.p0.rddata_valid.eq(rddata_en[-1])
