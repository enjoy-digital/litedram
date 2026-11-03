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
    def __init__(self, pads, sys_clk_freq=100e6, cl=None):
        pads        = PHYPadsCombiner(pads)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        with_dm     = hasattr(pads, "dm")
        assert databits%8 == 0

        # Parameters -------------------------------------------------------------------------------
        cl = get_default_cl(memtype="SDR", tck=1/sys_clk_freq) if cl is None else cl

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
            read_latency  = cl + 1,
            write_latency = 0,
            with_dm       = with_dm,
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, databits)

        # # #

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)


            # Commands -----------------------------------------------------------------------------
            commands = {
                # Pad name: (DFI name,   Pad type (required or optional))
                "cs_n"    : ("cs_n",    "optional"),
                "a"       : ("address", "required"),
                "ba"      : ("bank"   , "required"),
                "ras_n"   : ("ras_n"  , "required"),
                "cas_n"   : ("cas_n"  , "required"),
                "we_n"    : ("we_n"   , "required"),
                "cke"     : ("cke"    , "optional"),
            }
            for pad_name, (dfi_name, pad_type) in commands.items():
                pad = getattr(pads, pad_name, None)
                if (pad is None):
                    if (pad_type == "required"):
                        raise ValueError(f"DRAM pad {pad_name} required but not found in pads.")
                    continue
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
        rddata_en = Signal(self.settings.read_latency)
        self.sync += rddata_en.eq(Cat(dfi.p0.rddata_en, rddata_en))
        self.sync += dfi.p0.rddata_valid.eq(rddata_en[-1])

# Half-rate Generic SDR PHY ------------------------------------------------------------------------

class HalfRateGENSDRPHY(Module):
    """1:2 SDR PHY: the full-rate PHY in sys2x, two DFI phases per sys cycle.

    `with_dfi_reg`: registers the controller-to-PHY DFI signals in sys before they reach the sys2x
    IO registers. Without it, the controller's write data and commands (combinational from the
    user ports) have half a sys period to settle at the sys2x IOs, which can limit the SDRAM
    frequency; with it, commands and write data are delayed together by one sys cycle
    (write_latency unchanged) and read_latency is one sys cycle longer.
    """
    def __init__(self, pads, sys_clk_freq=100e6, cl=None, with_dfi_reg=False):
        pads        = PHYPadsCombiner(pads)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        with_dm     = hasattr(pads, "dm")
        nphases     = 2


        # Parameters -------------------------------------------------------------------------------
        # The SDRAM runs at 2 x sys_clk_freq: CL from the SDRAM clock period.
        cl = get_default_cl(memtype="SDR", tck=1/(2*sys_clk_freq)) if cl is None else cl

        # FullRate PHY -----------------------------------------------------------------------------
        full_rate_phy = GENSDRPHY(pads, 2*sys_clk_freq, cl)
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
            read_latency  = full_rate_phy.settings.read_latency//2 + 1 + int(with_dfi_reg),
            write_latency = 0,
            with_dm       = with_dm,
        )

        # DFI (optionally registered) --------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, databits, nphases)
        if with_dfi_reg:
            dfi = Interface(addressbits, bankbits, nranks, databits, nphases)
            for i, o in zip(self.dfi.phases, dfi.phases):
                for name, _, direction in i.layout:
                    if direction == DIR_M_TO_S:
                        self.sync += getattr(o, name).eq(getattr(i, name))
                    else:
                        self.comb += getattr(i, name).eq(getattr(o, name))

        # DFI adaptation ---------------------------------------------------------------------------
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
