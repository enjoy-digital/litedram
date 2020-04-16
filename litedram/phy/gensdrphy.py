# This file is Copyright (c) 2012-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

# 1:1 frequency-ratio Generic SDR PHY

from migen import *

from litex.build.io import SDRInput, SDROutput, SDRTristate

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
            phytype       = "GENSDRPHY",
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
            self.specials += [SDROutput(i=dfi.p0.address[i], o=pads.a[i])  for i in range(len(pads.a))]
            self.specials += [SDROutput(i=dfi.p0.bank[i], o=pads.ba[i]) for i in range(len(pads.ba))]
            self.specials += SDROutput(i=dfi.p0.cas_n, o=pads.cas_n)
            self.specials += SDROutput(i=dfi.p0.ras_n, o=pads.ras_n)
            self.specials += SDROutput(i=dfi.p0.we_n, o=pads.we_n)
            if hasattr(pads, "cke"):
                self.specials += SDROutput(i=dfi.p0.cke, o=pads.cke)
            if hasattr(pads, "cs_n"):
                self.specials += SDROutput(i=dfi.p0.cs_n, o=pads.cs_n)

        # DQ/DM Data Path --------------------------------------------------------------------------
        for i in range(len(pads.dq)):
            self.specials += SDRTristate(
                io = pads.dq[i],
                o  = dfi.p0.wrdata[i],
                oe = dfi.p0.wrdata_en,
                i  = dfi.p0.rddata[i],
            )
        if hasattr(pads, "dm"):
            for i in range(len(pads.dm)):
                self.comb += pads.dm[i].eq(0) # FIXME

        # DQ/DM Control Path -----------------------------------------------------------------------
        rddata_en = Signal(cl + cmd_latency)
        self.sync += rddata_en.eq(Cat(dfi.p0.rddata_en, rddata_en))
        self.sync += dfi.p0.rddata_valid.eq(rddata_en[-1])
