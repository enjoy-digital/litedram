# This file is Copyright (c) 2012-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
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
            for i in range(len(pads.a)):
                self.specials += SDROutput(i=dfi.p0.address[i], o=pads.a[i], clk=ClockSignal("sys"))
            for i in range(len(pads.ba)):
                self.specials += SDROutput(i=dfi.p0.bank[i], o=pads.ba[i], clk=ClockSignal("sys"))
            self.specials += SDROutput(i=dfi.p0.cas_n, o=pads.cas_n, clk=ClockSignal("sys"))
            self.specials += SDROutput(i=dfi.p0.ras_n, o=pads.ras_n, clk=ClockSignal("sys"))
            self.specials += SDROutput(i=dfi.p0.we_n, o=pads.we_n, clk=ClockSignal("sys"))
            if hasattr(pads, "cke"):
                self.specials += SDROutput(i=dfi.p0.cke, o=pads.cke, clk=ClockSignal("sys"))
            if hasattr(pads, "cs_n"):
                self.specials += SDROutput(i=dfi.p0.cs_n, o=pads.cs_n, clk=ClockSignal("sys"))

        # DQ/DM Data Path --------------------------------------------------------------------------
        for i in range(len(pads.dq)):
            self.specials += SDRTristate(
                io  = pads.dq[i],
                o   = dfi.p0.wrdata[i],
                oe  = dfi.p0.wrdata_en,
                i   = dfi.p0.rddata[i],
                clk = ClockSignal("sys")
            )
        if hasattr(pads, "dm"):
            for i in range(len(pads.dm)):
                self.comb += pads.dm[i].eq(0) # FIXME

        # DQ/DM Control Path -----------------------------------------------------------------------
        rddata_en = Signal(cl + cmd_latency)
        self.sync += rddata_en.eq(Cat(dfi.p0.rddata_en, rddata_en))
        self.sync += dfi.p0.rddata_valid.eq(rddata_en[-1])

# Half-rate Generic SDR PHY ------------------------------------------------------------------------

class HalfRateGENSDRPHY(Module):
    def __init__(self, pads, cl=2, cmd_latency=1):
        pads        = PHYPadsCombiner(pads)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = 2

        # FullRate PHY -----------------------------------------------------------------------------
        full_rate_phy = GENSDRPHY(pads, cl, cmd_latency)
        self.submodules += ClockDomainsRenamer("sys2x")(full_rate_phy)

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            phytype       = "HalfRateGENSDRPHY",
            memtype       = "SDR",
            databits      = databits,
            dfi_databits  = databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = 0,
            wrphase       = 1,
            rdcmdphase    = 1,
            wrcmdphase    = 0,
            cl            = cl,
            read_latency  = (cl + cmd_latency)//2 + 1,
            write_latency = 0
        )

        # DFI adaptation ---------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, databits, nphases)

        # Select active sys2x phase
        # sys       ----____----____
        # phase_sel 0   1   0   1
        # sys2x     --__--__--__--__
        phase_sel = Signal(reset=1)
        self.sync.sys2x += phase_sel.eq(~phase_sel)

        # Commands and address
        dfi_omit = set(["rddata", "rddata_valid", "wrdata_en"])
        self.comb += [
            If(~phase_sel,
                dfi.phases[0].connect(full_rate_phy.dfi.phases[0], omit=dfi_omit),
            ).Else(
                dfi.phases[1].connect(full_rate_phy.dfi.phases[0], omit=dfi_omit),
            ),
        ]
        wr_data_en = dfi.phases[self.settings.wrphase].wrdata_en & ~phase_sel
        wr_data_en_d = Signal()
        self.sync.sys2x += wr_data_en_d.eq(wr_data_en)
        self.comb += full_rate_phy.dfi.phases[0].wrdata_en.eq(wr_data_en | wr_data_en_d)

        # Reads
        rddata = Signal(2*databits)
        rddata_valid = Signal()

        self.sync.sys2x += [
            rddata_valid.eq(full_rate_phy.dfi.phases[0].rddata_valid),
            rddata.eq(full_rate_phy.dfi.phases[0].rddata)
        ]

        self.sync += [
            dfi.phases[0].rddata.eq(rddata),
            dfi.phases[0].rddata_valid.eq(rddata_valid),
            dfi.phases[1].rddata.eq(full_rate_phy.dfi.phases[0].rddata),
            dfi.phases[1].rddata_valid.eq(full_rate_phy.dfi.phases[0].rddata_valid),
        ]
