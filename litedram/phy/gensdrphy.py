#
# This file is part of LiteDRAM.
#
# Copyright (c) 2012-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# 1:1, 1:2 frequency-ratio Generic SDR PHY

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

            # Commands -----------------------------------------------------------------------------
            commands = {
                "a"    : "address",
                "ba"   : "bank"   ,
                "ras_n": "ras_n"  ,
                "cas_n": "cas_n"  ,
                "we_n" : "we_n"   ,
            }
            if hasattr(pads, "cke") : commands.update({"cke"  : "cke"})
            if hasattr(pads, "cs_n"): commands.update({"cs_n" : "cs_n"})
            for pad_name, dfi_name in commands.items():
                pad = getattr(pads, pad_name)
                for i in range(len(pad)):
                    self.specials += SDROutput(i=getattr(dfi.p0, dfi_name)[i], o=pad[i])

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
                self.specials += SDROutput(i=dfi.p0.wrdata_en & dfi.p0.wrdata_mask[i], o=pads.dm[i])

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

        # Clocking ---------------------------------------------------------------------------------
        # Select active sys2x phase:
        #  sys_clk   ----____----____
        #  sys2x_clk --__--__--__--__
        #  phase_sel 0   1   0   1
        phase_sel   = Signal()
        phase_sys   = Signal()
        phase_sys2x = Signal()
        self.sync       += phase_sys.eq(phase_sys2x)
        self.sync.sys2x += phase_sys2x.eq(~phase_sel)
        self.sync.sys2x += phase_sel.eq(~phase_sel & (phase_sys2x ^ phase_sys))

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            phytype       = "HalfRateGENSDRPHY",
            memtype       = "SDR",
            databits      = databits,
            dfi_databits  = databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = 0,
            wrphase       = 0,
            cl            = cl,
            read_latency  = (cl + cmd_latency)//2 + 1,
            write_latency = 0
        )

        # DFI adaptation ---------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, databits, nphases)
        self.comb += Case(phase_sel, {
            0: dfi.phases[0].connect(full_rate_phy.dfi.phases[0], omit={"rddata", "rddata_valid", "wrdata_en"}),
            1: dfi.phases[1].connect(full_rate_phy.dfi.phases[0], omit={"rddata", "rddata_valid", "wrdata_en"}),
        })

        # Write Datapath
        wr_data_en   = dfi.phases[self.settings.wrphase].wrdata_en & (phase_sel == 0)
        wr_data_en_d = Signal()
        self.sync.sys2x += wr_data_en_d.eq(wr_data_en)
        self.comb += full_rate_phy.dfi.phases[0].wrdata_en.eq(wr_data_en | wr_data_en_d)

        # Read Datapath
        rddata_d       = Signal(databits)
        self.sync.sys2x += rddata_d.eq(full_rate_phy.dfi.phases[0].rddata)
        self.comb += [
            dfi.phases[0].rddata.eq(rddata_d),
            dfi.phases[0].rddata_valid.eq(full_rate_phy.dfi.phases[0].rddata_valid),
            dfi.phases[1].rddata.eq(full_rate_phy.dfi.phases[0].rddata),
            dfi.phases[1].rddata_valid.eq(full_rate_phy.dfi.phases[0].rddata_valid),
        ]
