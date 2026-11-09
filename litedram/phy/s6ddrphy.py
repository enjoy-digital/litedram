#
# This file is part of LiteDRAM.
#
# Copyright (c) 2012 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2012-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# 1:2 and 1:4 frequency-ratio DDR / LPDDR / DDR2 / DDR3 PHYs for Spartan-6.
#
# DFI timing:
# - Assert dfi_wrdata_en and present the data on dfi_wrdata_mask/dfi_wrdata in the same cycle as
#   the write command.
# - Assert dfi_rddata_en in the same cycle as the read command: the data comes back on dfi_rddata
#   read_latency cycles later, along with the assertion of dfi_rddata_valid.
# - Read commands must be sent on phase 0, write commands on phase 1.
#
# CAS latency is fixed: CL3 for DDR/LPDDR/DDR2, CL5/CWL6 for DDR3.
#
# The PHY is not calibrated at runtime: rd_bitslip, wr_bitslip, dqs_ddr_alignment and the phase of
# the CRG clocks are set at build time and may need adjustments for a given board/frequency.

from functools import reduce
from operator import or_

from migen import *
from migen.fhdl.decorators import ClockDomainsRenamer

from litedram.common import *
from litedram.phy.dfi import *

# Helpers ------------------------------------------------------------------------------------------

def _oddr2(clk, clk_n, d0, d1, q, ddr_alignment):
    """DDR output register (DQS and its tristate control)."""
    return Instance("ODDR2",
        p_DDR_ALIGNMENT = ddr_alignment,
        p_INIT          = 0,
        p_SRTYPE        = "ASYNC",
        i_C0            = clk,
        i_C1            = clk_n,
        i_CE            = 1,
        i_D0            = d0,
        i_D1            = d1,
        i_R             = 0,
        i_S             = 0,
        o_Q             = q,
    )

def _oserdes2(clk, clkdiv, ioce, d, oq, t=None, tq=None):
    """4:1 output serializer (DQ and DM). t/tq: optional tristate path (DQ)."""
    params = dict(
        p_DATA_WIDTH     = 4,
        p_DATA_RATE_OQ   = "SDR",
        p_DATA_RATE_OT   = "SDR",
        p_SERDES_MODE    = "NONE",
        p_OUTPUT_MODE    = "SINGLE_ENDED",
        o_OQ             = oq,
        i_OCE            = 1,
        i_CLK0           = clk,
        i_CLK1           = 0,
        i_IOCE           = ioce,
        i_RST            = 0,
        i_CLKDIV         = clkdiv,
        i_D1             = d[0],
        i_D2             = d[1],
        i_D3             = d[2],
        i_D4             = d[3],
    )
    if t is not None:
        params.update(
            o_TQ = tq,
            i_T1 = t[0],
            i_T2 = t[1],
            i_T3 = t[2],
            i_T4 = t[3],
        )
    params.update(
        i_TRAIN     = 0,
        i_TCE       = int(t is not None),
        i_SHIFTIN1  = 0,
        i_SHIFTIN2  = 0,
        i_SHIFTIN3  = 0,
        i_SHIFTIN4  = 0,
    )
    return Instance("OSERDES2", **params)

def _wr_select(words, wr_bitslip, i):
    """Bit i of the OSERDES2.D1-D4 words: words[wr_bitslip+3] on D1 ... words[wr_bitslip] on D4."""
    return [words[wr_bitslip + 3 - k][i] for k in range(4)]

def _wr_select_t(drive_n, wr_bitslip):
    """OSERDES2.T1-T4: tristate control of the current (0) or previous (1) sys cycle."""
    return [drive_n[(wr_bitslip + 3 - k)//4] for k in range(4)]

# Spartan-6 Half Rate DDR PHY ----------------------------------------------------------------------

class S6HalfRateDDRPHY(Module):
    """Spartan-6 1:2 frequency-ratio PHY (DDR, LPDDR, DDR2 and DDR3).

    Clock domains (provided by the CRG):
    - sys:           DFI clock.
    - sdram_half:    2x sys, commands and DQS.
    - sdram_full_wr: 4x sys, OSERDES2 clock for DQ/DM (with clk4x_wr_strb).
    - sdram_full_rd: 4x sys, ISERDES2 clock for DQ (with clk4x_rd_strb).

    Parameters:
    - rd_bitslip:        Number of ISERDES2 bitslips applied after reset (0-15).
    - wr_bitslip:        Write data/mask offset in the OSERDES2 inputs (0-4).
    - dqs_ddr_alignment: ODDR2 DDR_ALIGNMENT of the DQS outputs ("C0" or "C1").
    """
    def __init__(self, pads, memtype, rd_bitslip, wr_bitslip, dqs_ddr_alignment):
        pads        = PHYPadsCombiner(pads)
        if memtype not in ["DDR", "LPDDR", "DDR2", "DDR3"]:
            raise NotImplementedError("S6HalfRateDDRPHY only supports DDR, LPDDR, DDR2 and DDR3")
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = 2
        assert databits%8 == 0

        # PHY settings -----------------------------------------------------------------------------
        if memtype == "DDR3":
            latencies = dict(cl=5, cwl=6, read_latency=6, write_latency=2)
        else:
            latencies = dict(cl=3,        read_latency=5, write_latency=0)
        self.settings = PhySettings(
            phytype      = "S6HalfRateDDRPHY",
            memtype      = memtype,
            databits     = databits,
            dfi_databits = 2*databits,
            nranks       = nranks,
            nphases      = nphases,
            rdphase      = 0,
            wrphase      = 1,
            **latencies
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
        self.clk4x_wr_strb = Signal()
        self.clk4x_rd_strb = Signal()

        # # #

        # Clocks -----------------------------------------------------------------------------------
        sys_clk           = ClockSignal("sys")
        sdram_half_clk    = ClockSignal("sdram_half")
        sdram_full_wr_clk = ClockSignal("sdram_full_wr")
        sdram_full_rd_clk = ClockSignal("sdram_full_rd")

        # Addresses and Commands -------------------------------------------------------------------

        # Select the active phase on sdram_half_clk:
        #             sys_clk   ----____----____
        #  phase_sel(nphases=2) 0   1   0   1     Half Rate
        phase_sel  = Signal(log2_int(nphases))
        phase_half = Signal.like(phase_sel)
        phase_sys  = Signal.like(phase_half)

        self.sync.sys += phase_sys.eq(phase_half)

        self.sync.sdram_half += [
            If(phase_half == phase_sys,
                phase_sel.eq(0),
            ).Else(
                phase_sel.eq(phase_sel+1)
            ),
            phase_half.eq(phase_half+1),
        ]

        # Register the DFI commands on sdram_half_clk.
        cmds  = ["reset_n", "odt", "address", "bank", "cs_n", "cke", "cas_n", "ras_n", "we_n"]
        r_dfi = Array(Record(phase_cmd_description(addressbits, bankbits, nranks=nranks)) for i in range(nphases))
        for n, phase in enumerate(dfi.phases):
            for cmd in cmds:
                self.sync.sdram_half += getattr(r_dfi[n], cmd).eq(getattr(phase, cmd))

        # Output the commands of the active phase.
        pad_cmds = [("a", "address"), ("ba", "bank"), ("cke", "cke"), ("ras_n", "ras_n"),
            ("cas_n", "cas_n"), ("we_n", "we_n")]
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)
            for pad, cmd in pad_cmds:
                self.sync.sdram_half += getattr(pads, pad).eq(getattr(r_dfi[phase_sel], cmd))
            # Optional pads.
            for name in ["reset_n", "cs_n", "odt"]:
                if hasattr(pads, name):
                    self.sync.sdram_half += getattr(pads, name).eq(getattr(r_dfi[phase_sel], name))

        # Read Bitslip -----------------------------------------------------------------------------
        # Pulse the ISERDES2 BITSLIP rd_bitslip times after reset.
        bitslip_cnt = Signal(4)
        bitslip_inc = Signal()

        self.sync.sys += [
            If(bitslip_cnt == rd_bitslip,
                bitslip_inc.eq(0)
            ).Else(
                bitslip_cnt.eq(bitslip_cnt+1),
                bitslip_inc.eq(1)
            )
        ]

        # DQS --------------------------------------------------------------------------------------
        sdram_half_clk_n = Signal()
        self.comb += sdram_half_clk_n.eq(~sdram_half_clk)

        postamble = Signal()
        drive_dqs = Signal()
        dqs_t_d0  = Signal()
        dqs_t_d1  = Signal()

        dqs_o = Signal(databits//8)
        dqs_t = Signal(databits//8)

        self.comb += [
            dqs_t_d0.eq(~(drive_dqs | postamble)),
            dqs_t_d1.eq(~drive_dqs),
        ]

        for i in range(databits//8):
            # DQS output.
            self.specials += _oddr2(sdram_half_clk, sdram_half_clk_n,
                d0            = 0,
                d1            = 1,
                q             = dqs_o[i],
                ddr_alignment = dqs_ddr_alignment,
            )

            # DQS tristate control.
            self.specials += _oddr2(sdram_half_clk, sdram_half_clk_n,
                d0            = dqs_t_d0,
                d1            = dqs_t_d1,
                q             = dqs_t[i],
                ddr_alignment = dqs_ddr_alignment,
            )

            # DQS tristate buffer.
            if hasattr(pads, "dqs_n"):
                self.specials += Instance("IOBUFDS",
                    i_T    = dqs_t[i],
                    i_I    = dqs_o[i],
                    io_IO  = pads.dqs[i],
                    io_IOB = pads.dqs_n[i],
                )
            else:
                self.specials += Instance("IOBUF",
                    i_T   = dqs_t[i],
                    i_I   = dqs_o[i],
                    io_IO = pads.dqs[i],
                )

        self.sync.sdram_half += postamble.eq(drive_dqs)

        # DQ/DM ------------------------------------------------------------------------------------

        # DFI data of the current (d_dfi[0:nphases]) and previous (d_dfi[nphases:]) sys cycles.
        d_dfi = [Record(phase_wrdata_description(nphases*databits)+phase_rddata_description(nphases*databits))
            for i in range(2*nphases)]

        for n, phase in enumerate(dfi.phases):
            self.comb += [
                d_dfi[n].wrdata.eq(phase.wrdata),
                d_dfi[n].wrdata_mask.eq(phase.wrdata_mask),
                d_dfi[n].wrdata_en.eq(phase.wrdata_en),
                d_dfi[n].rddata_en.eq(phase.rddata_en),
            ]
            self.sync.sys += [
                d_dfi[nphases+n].wrdata.eq(phase.wrdata),
                d_dfi[nphases+n].wrdata_mask.eq(phase.wrdata_mask)
            ]

        drive_dq   = Signal()
        drive_dq_n = [Signal() for i in range(2)]
        self.comb += drive_dq_n[0].eq(~drive_dq)
        self.sync.sys += drive_dq_n[1].eq(drive_dq_n[0])

        dq_t = Signal(databits)
        dq_o = Signal(databits)
        dq_i = Signal(databits)

        # Write data/mask words: current then previous sys cycle, phases reversed;
        # wr_bitslip selects 4 consecutive words (see _wr_select).
        dq_wrdata = []
        for i in range(2):
            for j in reversed(range(nphases)):
                dq_wrdata.append(d_dfi[i*nphases+j].wrdata[:databits])
                dq_wrdata.append(d_dfi[i*nphases+j].wrdata[databits:])

        for i in range(databits):
            # DQ serializer.
            self.specials += _oserdes2(sdram_full_wr_clk, sys_clk, self.clk4x_wr_strb,
                d  = _wr_select(dq_wrdata, wr_bitslip, i),
                oq = dq_o[i],
                t  = _wr_select_t(drive_dq_n, wr_bitslip),
                tq = dq_t[i],
            )

            # DQ deserializer.
            self.specials += Instance("ISERDES2",
                p_DATA_WIDTH     = 4,
                p_DATA_RATE      = "SDR",
                p_BITSLIP_ENABLE = "TRUE",
                p_SERDES_MODE    = "NONE",
                p_INTERFACE_TYPE = "RETIMED",

                i_D        = dq_i[i],
                i_CE0      = 1,
                i_CLK0     = sdram_full_rd_clk,
                i_CLK1     = 0,
                i_IOCE     = self.clk4x_rd_strb,
                i_RST      = ResetSignal(),
                i_CLKDIV   = sys_clk,
                i_BITSLIP  = bitslip_inc,

                o_Q1 = d_dfi[0*nphases+0].rddata[i+databits],
                o_Q2 = d_dfi[0*nphases+0].rddata[i],
                o_Q3 = d_dfi[0*nphases+1].rddata[i+databits],
                o_Q4 = d_dfi[0*nphases+1].rddata[i],
            )

            # DQ tristate buffer.
            self.specials += Instance("IOBUF",
                i_I   = dq_o[i],
                o_O   = dq_i[i],
                i_T   = dq_t[i],
                io_IO = pads.dq[i]
            )

        dq_wrdata_mask = []
        for i in range(2):
            for j in reversed(range(nphases)):
                dq_wrdata_mask.append(d_dfi[i*nphases+j].wrdata_mask[:databits//8])
                dq_wrdata_mask.append(d_dfi[i*nphases+j].wrdata_mask[databits//8:])

        for i in range(databits//8):
            # DM serializer.
            self.specials += _oserdes2(sdram_full_wr_clk, sys_clk, self.clk4x_wr_strb,
                d  = _wr_select(dq_wrdata_mask, wr_bitslip, i),
                oq = pads.dm[i],
            )

        # DQ/DQS/DM control ------------------------------------------------------------------------

        # Write: drive DQ and DQS during the write burst.
        wrdata_en = Signal()
        self.comb += wrdata_en.eq(reduce(or_, [d_dfi[p].wrdata_en for p in range(nphases)]))

        if memtype == "DDR3":
            r_drive_dq = Signal(self.settings.cwl-1)
            self.sync.sdram_half += r_drive_dq.eq(Cat(wrdata_en, r_drive_dq))
            self.comb += drive_dq.eq(r_drive_dq[self.settings.cwl-2])
        else:
            self.comb += drive_dq.eq(wrdata_en)

        wrdata_en_d = Signal()
        self.sync.sys += wrdata_en_d.eq(wrdata_en)

        if memtype == "DDR3":
            r_dfi_wrdata_en = Signal(max(self.settings.cwl, self.settings.cl))
        else:
            r_dfi_wrdata_en = Signal(self.settings.cl)
        self.sync.sdram_half += r_dfi_wrdata_en.eq(Cat(wrdata_en_d, r_dfi_wrdata_en))

        if memtype == "DDR3":
            self.comb += drive_dqs.eq(r_dfi_wrdata_en[self.settings.cwl-1])
        else:
            self.comb += drive_dqs.eq(r_dfi_wrdata_en[1])

        # Read: rddata_valid read_latency sys cycles after rddata_en.
        rddata_en = Signal()
        self.comb += rddata_en.eq(reduce(or_, [d_dfi[p].rddata_en for p in range(nphases)]))

        rddata_sr = Signal(self.settings.read_latency)
        self.sync.sys += rddata_sr.eq(Cat(rddata_sr[1:self.settings.read_latency], rddata_en))

        for n, phase in enumerate(dfi.phases):
            self.comb += [
                phase.rddata.eq(d_dfi[n].rddata),
                phase.rddata_valid.eq(rddata_sr[0]),
            ]

# Spartan-6 Quarter Rate DDR PHY -------------------------------------------------------------------

class S6QuarterRateDDRPHY(Module):
    """Spartan-6 1:4 frequency-ratio PHY (DDR3 only).

    S6HalfRateDDRPHY running on sys2x (2x sys) with a 1:2 DFI adaptation from sys. The clock domains
    of the half-rate PHY become: sys2x (DFI), sdram_half, sdram_full_wr and sdram_full_rd, with the
    strobes exposed as clk8x_wr_strb/clk8x_rd_strb. See S6HalfRateDDRPHY for the parameters.
    """
    def __init__(self, pads, rd_bitslip, wr_bitslip, dqs_ddr_alignment):
        pads        = PHYPadsCombiner(pads)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = 4

        # HalfRate PHY -----------------------------------------------------------------------------
        half_rate_phy = S6HalfRateDDRPHY(pads, "DDR3", rd_bitslip, wr_bitslip, dqs_ddr_alignment)
        self.submodules += ClockDomainsRenamer("sys2x")(half_rate_phy)
        self.clk8x_wr_strb = half_rate_phy.clk4x_wr_strb
        self.clk8x_rd_strb = half_rate_phy.clk4x_rd_strb

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            phytype       = "S6QuarterRateDDRPHY",
            memtype       = "DDR3",
            databits      = databits,
            dfi_databits  = 2*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = 0,
            wrphase       = 1,
            cl            = 5,
            cwl           = 6,
            read_latency  = 6//2+1,
            write_latency = 2//2
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)

        # Clocks -----------------------------------------------------------------------------------
        # sys   : DFI clock.
        # sys2x : 2x sys, half-rate PHY DFI clock.

        # Select the active sys2x phase:
        # sys_clk   ----____----____
        # phase_sel 0   1   0   1
        phase_sel   = Signal()
        phase_sys2x = Signal.like(phase_sel)
        phase_sys   = Signal.like(phase_sys2x)

        self.sync.sys += phase_sys.eq(phase_sys2x)

        self.sync.sys2x += [
            If(phase_sys2x == phase_sys,
                phase_sel.eq(0),
            ).Else(
                phase_sel.eq(~phase_sel)
            ),
            phase_sys2x.eq(~phase_sel)
        ]

        # DFI adaptation ---------------------------------------------------------------------------

        # Commands and writes: phases 0/1 on the 1st sys2x cycle, phases 2/3 on the 2nd.
        dfi_omit = set(["rddata", "rddata_valid", "wrdata_en"])
        self.comb += [
            If(~phase_sel,
                dfi.phases[0].connect(half_rate_phy.dfi.phases[0], omit=dfi_omit),
                dfi.phases[1].connect(half_rate_phy.dfi.phases[1], omit=dfi_omit),
            ).Else(
                dfi.phases[2].connect(half_rate_phy.dfi.phases[0], omit=dfi_omit),
                dfi.phases[3].connect(half_rate_phy.dfi.phases[1], omit=dfi_omit),
            ),
        ]
        wr_data_en = dfi.phases[self.settings.wrphase].wrdata_en & ~phase_sel
        wr_data_en_d = Signal()
        self.sync.sys2x += wr_data_en_d.eq(wr_data_en)
        self.comb += half_rate_phy.dfi.phases[half_rate_phy.settings.wrphase].wrdata_en.eq(wr_data_en | wr_data_en_d)

        # Reads: phases 0/1 from the 1st sys2x cycle (registered), phases 2/3 from the 2nd.
        rddata = Array(Signal(2*databits) for i in range(2))
        rddata_valid = Signal(2)

        for i in range(2):
            self.sync.sys2x += [
                rddata_valid[i].eq(half_rate_phy.dfi.phases[i].rddata_valid),
                rddata[i].eq(half_rate_phy.dfi.phases[i].rddata)
            ]

        self.sync.sys += [
            dfi.phases[0].rddata.eq(rddata[0]),
            dfi.phases[0].rddata_valid.eq(rddata_valid[0]),
            dfi.phases[1].rddata.eq(rddata[1]),
            dfi.phases[1].rddata_valid.eq(rddata_valid[1]),
            dfi.phases[2].rddata.eq(half_rate_phy.dfi.phases[0].rddata),
            dfi.phases[2].rddata_valid.eq(half_rate_phy.dfi.phases[0].rddata_valid),
            dfi.phases[3].rddata.eq(half_rate_phy.dfi.phases[1].rddata),
            dfi.phases[3].rddata_valid.eq(half_rate_phy.dfi.phases[1].rddata_valid)
        ]
