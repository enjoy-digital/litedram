#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Series-7 DDR3 PHY for HR banks, with write leveling by CK phase (S7HRDDRPHY).

LiteDRAM's A7DDRPHY structure (1:4, OSERDESE2/ISERDESE2, read leveling with IDELAYE2 + bitslip,
per-lane write latency bitslip) for DDR3 on high-range banks, where there is no ODELAYE2 and
therefore no per-lane write leveling. A fly-by command/clock bus (a DIMM-like layout, e.g. the
nine x8 chips of a 72-bit channel) puts each chip's CK at a different delay from its DQS: with a
single static DQS phase only part of the lanes meet tDQSS. The technique:

- CK and the command/address pins run on a pair of clocks with MMCM fine phase shift; DQ, DQS
  and the read capture run on static clocks of the same MMCM, so DQ keeps its DQS at 90 deg and
  the read capture does not move. Moving CK against DQ/DQS is the relative motion write leveling
  needs, and the MMCM's fine-PS outputs all share one phase (the FINE_PS_FRAC DRC refuses
  fine-PS outputs at different sub-VCO phases, so CK is the one that moves).
- One MMCM per PHY, cascaded from the controller clock (`sys`) with its feedback through a
  BUFG: the static outputs keep the phase of `sys` and Vivado times sys <-> static clocks as
  synchronous. Every OSERDESE2's CLK/CLKDIV pair comes from that one VCO.
- The commands cross from `sys` to the shifted CLKDIV through registers clocked on the falling
  edge of `sys` (FDRE IS_C_INVERTED on the global clock, not a LUT inverter): with the CK phase
  kept within +-1/2 tCK of `sys` (+-0.94 ns at DDR3-1066), the crossing keeps ~2.8 ns of setup
  and hold. add_constraints() adds the phase range as clock uncertainty on that crossing.
- Each lane keeps its own write latency (the A7DDRPHY's write bitslip); the read side adds
  per-bit selection (`dq_dly_sel`, liblitedram's SDRAM_DELAY_PER_DQ CSR name: the IDELAY taps and
  the read bitslip of single DQ bits) since the ISERDESE2 of one lane do not all frame a word
  alike.

The calibration (liblitedram's sdram_s7hr.c, run by the BIOS) scans the CK phase over one tCK, runs the per-lane write
latency calibration, the per-bit read leveling and a traffic test (LiteDRAM BIST) at each step,
and settles in the middle of the longest run that every lane passes. A single-burst DFI check
is not enough to pick the phase (a lane can pass it and fail under traffic).

CSRs (on top of the A7DDRPHY's):
- ckphase_inc / ckphase_dec: one fine phase step of CK (1/56 of the VCO period, 16.7 ps at
  DDR3-1066) later / earlier; the MMCM takes ~12 cycles (busy).
- ckphase_status: value (signed fine steps from the reset phase), busy, locked.
- dq_dly_sel: per-bit mask of the read-side delay/bitslip strobes within the lanes `dly_sel`
  selects (0: every bit, the A7DDRPHY behaviour).
"""

import math
from functools import reduce
from operator import or_

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import Interface

# Helpers ------------------------------------------------------------------------------------------

def _negedge(module, signal, clk):
    """`signal` registered on the falling edge of `clk` (one FDRE per bit, IS_C_INVERTED)."""
    q = Signal.like(signal)
    for i in range(len(signal)):
        module.specials += Instance("FDRE",
            p_INIT         = 0,
            p_IS_C_INVERTED = 1,
            i_C  = clk,
            i_CE = 1,
            i_R  = 0,
            i_D  = signal[i],
            o_Q  = q[i],
        )
    return q

# Latencies ----------------------------------------------------------------------------------------

def s7hr_latencies(sys_clk_freq, cl=None, cwl=None, cmd_latency=0, nphases=4):
    """(cl, cwl, rdphase, wrphase, read_latency, write_latency) of the 1:4 PHY: the A7DDRPHY's
    schedule (read data one memory-clock phase into the ISERDESE2 word)."""
    tck             = 2/(2*nphases*sys_clk_freq)
    cl              = get_default_cl( "DDR3", tck) if cl  is None else cl
    cwl             = get_default_cwl("DDR3", tck) if cwl is None else cwl
    cl_sys_latency  = get_sys_latency(nphases, cl)
    cwl_sys_latency = get_sys_latency(nphases, cwl)
    rdphase         = get_sys_phase(nphases, cl_sys_latency,   cl + cmd_latency)
    wrphase         = get_sys_phase(nphases, cwl_sys_latency, cwl + cmd_latency)
    phase_cycles, rdphase = divmod(rdphase + 1, nphases)
    cl_sys_latency -= phase_cycles
    return cl, cwl, rdphase, wrphase, cl_sys_latency + 6, cwl_sys_latency - 1


def s7hr_model_settings(sys_clk_freq, databits, cl=None, cwl=None):
    """PhySettings for LiteDRAM's SDRAMPHYModel with this PHY's latencies (the simulation)."""
    cl, cwl, rdphase, wrphase, read_latency, write_latency = s7hr_latencies(sys_clk_freq, cl, cwl)
    return PhySettings(
        phytype       = "SDRAMPHYModel",
        memtype       = "DDR3",
        databits      = databits,
        dfi_databits  = 2*databits,
        nphases       = 4,
        rdphase       = rdphase,
        wrphase       = wrphase,
        cl            = cl,
        cwl           = cwl,
        read_latency  = read_latency,
        write_latency = write_latency,
    )

# CK Phase Shift -----------------------------------------------------------------------------------

class S7HRCKPhase(LiteXModule):
    """The MMCM fine phase shift of CK, one step per CSR write (PSCLK = sys).

    CSRs: inc / dec (one step later / earlier), status (value: signed steps from the MMCM's reset
    phase, busy: a step in progress, the MMCM takes ~12 cycles; locked). A step requested while
    busy is dropped: wait for busy low. The value follows the MMCM: back to 0 when it unlocks.
    """
    def __init__(self):
        self.psen     = Signal()
        self.psincdec = Signal()
        self.psdone   = Signal()
        self.locked   = Signal()

        self._inc    = CSR()
        self._dec    = CSR()
        self._status = CSRStatus(fields=[
            CSRField("value",  size=16, description="CK phase, signed fine steps from reset."),
            CSRField("busy",   size=1,  description="A phase step is in progress."),
            CSRField("locked", size=1,  description="The PHY's MMCM is locked."),
        ])

        # # #

        busy  = Signal()
        value = Signal((16, True))
        self.sync += [
            self.psen.eq(0),
            If(~busy & (self._inc.re | self._dec.re),
                self.psen.eq(1),
                self.psincdec.eq(self._inc.re),
                busy.eq(1),
            ),
            If(self.psdone,
                busy.eq(0),
                If(self.psincdec,
                    value.eq(value + 1)
                ).Else(
                    value.eq(value - 1)
                )
            ),
            If(~self.locked,
                busy.eq(0),
                value.eq(0),
            ),
        ]
        self.comb += [
            self._status.fields.value.eq(value),
            self._status.fields.busy.eq(busy),
            self._status.fields.locked.eq(self.locked),
        ]

# S7HRDDRPHY ---------------------------------------------------------------------------------------

class S7HRDDRPHY(LiteXModule):
    """DDR3 1:4 PHY for Series-7 HR banks, write leveling by CK phase (see the module doc).

    pads:      DDR3 pads (one group; PHYPadsReducer to leave out an ECC lane).
    name:      prefix of the PHY's own clock domains (unique per PHY of a SoC).
    mmcm_loc:  optional MMCME2_ADV site (the CMT of the channel's banks).
    """
    def __init__(self, pads, sys_clk_freq, iodelay_clk_freq=200e6, cl=None, cwl=None,
                 cmd_latency=0, name="ddrphy", mmcm_loc=None):
        memtype     = "DDR3"
        nphases     = 4
        phytype     = self.__class__.__name__
        tck         = 2/(2*nphases*sys_clk_freq)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        strobes     = len(pads.dqs_p)
        assert databits == 8*strobes, "x8 lanes (8 DQ per DQS)"
        assert strobes <= 16
        self.name     = name
        self.mmcm_loc = mmcm_loc

        # Parameters -------------------------------------------------------------------------------
        iodelay_tap_average = {200e6: 78e-12, 300e6: 52e-12, 400e6: 39e-12}
        half_sys8x_taps = math.floor(tck/(4*iodelay_tap_average[iodelay_clk_freq]))

        cl, cwl, rdphase, wrphase, read_latency, write_latency = s7hr_latencies(
            sys_clk_freq, cl, cwl, cmd_latency, nphases)
        cwl_sys_latency = write_latency + 1

        # Registers --------------------------------------------------------------------------------
        self._rst             = CSRStorage()
        self._dly_sel         = CSRStorage(strobes)
        self._dq_dly_sel      = CSRStorage(8, description="Read-side per-bit mask (0: all bits).")
        self._half_sys8x_taps = CSRStorage(5, reset=half_sys8x_taps)

        self._wlevel_en     = CSRStorage()
        self._wlevel_strobe = CSR()

        self._rdly_dq_rst         = CSR()
        self._rdly_dq_inc         = CSR()
        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        self._wdly_dq_bitslip_rst = CSR()
        self._wdly_dq_bitslip     = CSR()

        self._rdphase = CSRStorage(int(math.log2(nphases)), reset=rdphase)
        self._wrphase = CSRStorage(int(math.log2(nphases)), reset=wrphase)

        self.settings = PhySettings(
            phytype                   = phytype,
            memtype                   = memtype,
            databits                  = databits,
            strobes                   = strobes,
            dfi_databits              = 2*databits,
            nranks                    = nranks,
            nphases                   = nphases,
            rdphase                   = self._rdphase.storage,
            wrphase                   = self._wrphase.storage,
            cl                        = cl,
            cwl                       = cwl,
            read_latency              = read_latency,
            write_latency             = write_latency,
            cmd_latency               = cmd_latency,
            write_leveling            = False,
            write_dq_dqs_training     = False,
            # The per-lane write latency is calibrated (liblitedram's sdram_s7hr.c), but not by
            # liblitedram's sequence: its write latency calibration does not build without
            # write leveling (the write bitslip accessors are behind it).
            write_latency_calibration = False,
            read_leveling             = True,
            delays                    = 32,
            bitslips                  = 8,
            with_dm                   = hasattr(pads, "dm"),
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)

        # # #

        # Clocking ---------------------------------------------------------------------------------
        # One MMCM per PHY, cascaded from sys (VCO = 2*nphases*sys = the DDR rate):
        #   c       sys     fine PS   CLKDIV of CK and the commands
        #   c4x     4x sys  fine PS   CLK of CK and the commands
        #   w       sys     0         CLKDIV of DQ/DQS/DM and of the read ISERDESE2
        #   w4x     4x sys  0         CLK of DQ/DM and of the read ISERDESE2
        #   w4x_dqs 4x sys  90 deg    CLK of DQS
        self.cd_c       = ClockDomain(f"{name}_c")
        self.cd_c4x     = ClockDomain(f"{name}_c4x",     reset_less=True)
        self.cd_w       = ClockDomain(f"{name}_w")
        self.cd_w4x     = ClockDomain(f"{name}_w4x",     reset_less=True)
        self.cd_w4x_dqs = ClockDomain(f"{name}_w4x_dqs", reset_less=True)
        vco_mult  = 2*nphases
        vco_freq  = sys_clk_freq*vco_mult
        assert 600e6 <= vco_freq <= 1440e6, f"MMCM VCO {vco_freq/1e6:.1f} MHz out of range"
        self.ps_step_ps = 1e12/vco_freq/56
        self.ps_steps_per_tck = 56*vco_mult//nphases # One tCK = 2 VCO periods = 112 steps (1:4).
        self.settings.ckphase_steps = self.ps_steps_per_tck # SDRAM_PHY_CKPHASE_STEPS (BIOS).
        fb, fb_buf = Signal(), Signal()
        outs       = [Signal() for _ in range(5)]
        self.mmcm_locked = locked = Signal()
        self.ckphase = ckphase = S7HRCKPhase()
        self.comb += ckphase.locked.eq(locked)
        self.mmcm_rst = mmcm_rst = Signal()
        self.comb += mmcm_rst.eq(ResetSignal("sys"))
        self.specials += Instance("MMCME2_ADV", name=f"{name}_mmcm",
            p_BANDWIDTH          = "OPTIMIZED",
            p_CLKIN1_PERIOD      = 1e9/sys_clk_freq,
            p_REF_JITTER1        = 0.01,
            p_DIVCLK_DIVIDE      = 1,
            p_CLKFBOUT_MULT_F    = float(vco_mult),
            p_CLKFBOUT_PHASE     = 0.0,
            p_CLKOUT0_DIVIDE_F   = float(vco_mult),
            p_CLKOUT0_PHASE      = 0.0,
            p_CLKOUT0_USE_FINE_PS = "TRUE",
            p_CLKOUT1_DIVIDE     = 2,
            p_CLKOUT1_PHASE      = 0.0,
            p_CLKOUT1_USE_FINE_PS = "TRUE",
            p_CLKOUT2_DIVIDE     = vco_mult,
            p_CLKOUT2_PHASE      = 0.0,
            p_CLKOUT3_DIVIDE     = 2,
            p_CLKOUT3_PHASE      = 0.0,
            p_CLKOUT4_DIVIDE     = 2,
            p_CLKOUT4_PHASE      = 90.0,
            i_CLKIN1   = ClockSignal("sys"),
            i_CLKIN2   = 0,
            i_CLKINSEL = 1,
            i_CLKFBIN  = fb_buf,
            o_CLKFBOUT = fb,
            i_RST      = mmcm_rst,
            i_PWRDWN   = 0,
            o_LOCKED   = locked,
            i_PSCLK    = ClockSignal("sys"),
            i_PSEN     = ckphase.psen,
            i_PSINCDEC = ckphase.psincdec,
            o_PSDONE   = ckphase.psdone,
            i_DCLK = 0, i_DEN = 0, i_DWE = 0, i_DADDR = 0, i_DI = 0,
            o_CLKOUT0 = outs[0],
            o_CLKOUT1 = outs[1],
            o_CLKOUT2 = outs[2],
            o_CLKOUT3 = outs[3],
            o_CLKOUT4 = outs[4],
        )
        self.specials += Instance("BUFG", i_I=fb, o_O=fb_buf)
        for o, cd in zip(outs, [self.cd_c, self.cd_c4x, self.cd_w, self.cd_w4x, self.cd_w4x_dqs]):
            self.specials += Instance("BUFG", i_I=o, o_O=cd.clk)

        # Serializer resets: held while the MMCM is unlocked, released synchronously to each
        # CLKDIV; one register per lane on the write/read side.
        serdes_rst = Signal()
        self.comb += serdes_rst.eq(ResetSignal("sys") | ~locked | self._rst.storage)
        self.specials += [
            AsyncResetSynchronizer(self.cd_c, serdes_rst),
            AsyncResetSynchronizer(self.cd_w, serdes_rst),
        ]
        lane_rst = [Signal(reset_less=True) for _ in range(strobes)]
        c_rst    = Signal(reset_less=True)
        sync_w   = getattr(self.sync, f"{name}_w")
        sync_c   = getattr(self.sync, f"{name}_c")
        sync_w  += [r.eq(ResetSignal(f"{name}_w")) for r in lane_rst]
        sync_c  += c_rst.eq(ResetSignal(f"{name}_c"))

        # Per-bit selection (read side) ------------------------------------------------------------
        dq_sel = Signal(8)
        self.comb += If(self._dq_dly_sel.storage == 0,
            dq_sel.eq(0xff)
        ).Else(
            dq_sel.eq(self._dq_dly_sel.storage)
        )
        def bit_sel(i):
            return self._dly_sel.storage[i//8] & dq_sel[i%8]

        rdly_dq_rst         = self._rdly_dq_rst.re
        rdly_dq_inc         = self._rdly_dq_inc.re
        rdly_dq_bitslip_rst = self._rdly_dq_bitslip_rst.re
        rdly_dq_bitslip     = self._rdly_dq_bitslip.re
        wdly_dq_bitslip_rst = self._wdly_dq_bitslip_rst.re
        wdly_dq_bitslip     = self._wdly_dq_bitslip.re
        wlevel_strobe       = self._wlevel_strobe.re

        # Clock ------------------------------------------------------------------------------------
        for i in range(len(pads.clk_p)):
            sd_clk_se = Signal()
            self.specials += Instance("OSERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_DATA_WIDTH     = 2*nphases,
                p_TRISTATE_WIDTH = 1,
                p_DATA_RATE_OQ   = "DDR",
                p_DATA_RATE_TQ   = "BUF",
                i_RST    = c_rst,
                i_CLK    = ClockSignal(f"{name}_c4x"),
                i_CLKDIV = ClockSignal(f"{name}_c"),
                **{f"i_D{n+1}": (0b10101010 >> n) & 0b1 for n in range(8)},
                i_OCE    = 1,
                o_OQ     = sd_clk_se,
            )
            self.specials += Instance("OBUFDS",
                i_I  = sd_clk_se,
                o_O  = pads.clk_p[i],
                o_OB = pads.clk_n[i],
            )

        # Commands ---------------------------------------------------------------------------------
        # The DFI phases cross into the shifted CLKDIV through falling-edge registers of sys.
        commands = {
            "reset_n" : ("reset_n", False),
            "cs_n"    : ("cs_n",    False),
            "a"       : ("address", True),
            "ba"      : ("bank",    True),
            "ras_n"   : ("ras_n",   True),
            "cas_n"   : ("cas_n",   True),
            "we_n"    : ("we_n",    True),
            "cke"     : ("cke",     False),
            "odt"     : ("odt",     False),
        }
        for pad_name, (dfi_name, required) in commands.items():
            pad = getattr(pads, pad_name, None)
            if pad is None:
                if required:
                    raise ValueError(f"DRAM pad {pad_name} required but not found in pads.")
                continue
            phases = [_negedge(self, getattr(dfi.phases[p], dfi_name), ClockSignal("sys"))
                for p in range(nphases)]
            for i in range(len(pad)):
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = c_rst,
                    i_CLK    = ClockSignal(f"{name}_c4x"),
                    i_CLKDIV = ClockSignal(f"{name}_c"),
                    **{f"i_D{n+1}": phases[n//2][i] for n in range(8)},
                    i_OCE    = 1,
                    o_OQ     = pad[i],
                )

        # DQS --------------------------------------------------------------------------------------
        dqs_oe        = Signal()
        dqs_preamble  = Signal()
        dqs_postamble = Signal()
        dqs_oe_delay  = TappedDelayLine(ntaps=2)
        dqs_pattern   = DQSPattern(
            wlevel_en     = self._wlevel_en.storage,
            wlevel_strobe = wlevel_strobe,
            register      = True)
        self.submodules += dqs_oe_delay, dqs_pattern
        self.comb += dqs_oe_delay.input.eq(dqs_preamble | dqs_oe | dqs_postamble)
        for i in range(strobes):
            dqs_o = Signal()
            dqs_t = Signal()
            dqs_bitslip = BitSlip(8,
                i      = dqs_pattern.o,
                rst    = (self._dly_sel.storage[i] & wdly_dq_bitslip_rst) | self._rst.storage,
                slp    = self._dly_sel.storage[i] & wdly_dq_bitslip,
                cycles = 1)
            self.submodules += dqs_bitslip
            self.specials += Instance("OSERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_DATA_WIDTH     = 2*nphases,
                p_TRISTATE_WIDTH = 1,
                p_DATA_RATE_OQ   = "DDR",
                p_DATA_RATE_TQ   = "BUF",
                i_RST    = lane_rst[i],
                i_CLK    = ClockSignal(f"{name}_w4x_dqs"),
                i_CLKDIV = ClockSignal(f"{name}_w"),
                **{f"i_D{n+1}": dqs_bitslip.o[n] for n in range(8)},
                i_OCE    = 1,
                o_OQ     = dqs_o,
                i_TCE    = 1,
                i_T1     = ~dqs_oe_delay.output,
                o_TQ     = dqs_t,
            )
            self.specials += Instance("IOBUFDS",
                i_T    = dqs_t,
                i_I    = dqs_o,
                io_IO  = pads.dqs_p[i],
                io_IOB = pads.dqs_n[i],
            )

        # DM ---------------------------------------------------------------------------------------
        if hasattr(pads, "dm"):
            for i in range(strobes):
                dm_i = Cat(*[dfi.phases[n//2].wrdata_mask[n%2*databits//8+i] for n in range(8)])
                dm_bitslip = BitSlip(8,
                    i      = dm_i,
                    rst    = (self._dly_sel.storage[i] & wdly_dq_bitslip_rst) | self._rst.storage,
                    slp    = self._dly_sel.storage[i] & wdly_dq_bitslip,
                    cycles = 1)
                self.submodules += dm_bitslip
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = lane_rst[i],
                    i_CLK    = ClockSignal(f"{name}_w4x"),
                    i_CLKDIV = ClockSignal(f"{name}_w"),
                    **{f"i_D{n+1}": dm_bitslip.o[n] for n in range(8)},
                    i_OCE    = 1,
                    o_OQ     = pads.dm[i],
                )

        # DQ ---------------------------------------------------------------------------------------
        dq_oe       = Signal()
        dq_oe_delay = TappedDelayLine(ntaps=2)
        self.submodules += dq_oe_delay
        self.comb += dq_oe_delay.input.eq(dqs_preamble | dq_oe | dqs_postamble)
        for i in range(databits):
            dq_o         = Signal()
            dq_i         = Signal()
            dq_i_delayed = Signal()
            dq_t         = Signal()
            dq_o_bitslip = BitSlip(8,
                i      = Cat(*[dfi.phases[n//2].wrdata[n%2*databits+i] for n in range(8)]),
                rst    = (self._dly_sel.storage[i//8] & wdly_dq_bitslip_rst) | self._rst.storage,
                slp    = self._dly_sel.storage[i//8] & wdly_dq_bitslip,
                cycles = 1)
            self.submodules += dq_o_bitslip
            self.specials += Instance("OSERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_DATA_WIDTH     = 2*nphases,
                p_TRISTATE_WIDTH = 1,
                p_DATA_RATE_OQ   = "DDR",
                p_DATA_RATE_TQ   = "BUF",
                i_RST    = lane_rst[i//8],
                i_CLK    = ClockSignal(f"{name}_w4x"),
                i_CLKDIV = ClockSignal(f"{name}_w"),
                **{f"i_D{n+1}": dq_o_bitslip.o[n] for n in range(8)},
                i_TCE    = 1,
                i_T1     = ~dq_oe_delay.output,
                o_TQ     = dq_t,
                i_OCE    = 1,
                o_OQ     = dq_o,
            )
            dq_i_bitslip = BitSlip(8,
                rst    = (bit_sel(i) & rdly_dq_bitslip_rst) | self._rst.storage,
                slp    = bit_sel(i) & rdly_dq_bitslip,
                cycles = 1)
            self.submodules += dq_i_bitslip
            self.specials += Instance("ISERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_INTERFACE_TYPE = "NETWORKING",
                p_DATA_WIDTH     = 2*nphases,
                p_DATA_RATE      = "DDR",
                p_NUM_CE         = 1,
                p_IOBDELAY       = "IFD",
                i_RST     = lane_rst[i//8],
                i_CLK     = ClockSignal(f"{name}_w4x"),
                i_CLKB    = ~ClockSignal(f"{name}_w4x"),
                i_CLKDIV  = ClockSignal(f"{name}_w"),
                i_BITSLIP = 0,
                i_CE1     = 1,
                i_DDLY    = dq_i_delayed,
                **{f"o_Q{n+1}": dq_i_bitslip.i[8-1-n] for n in range(8)},
            )
            for n in range(8):
                self.comb += dfi.phases[n//2].rddata[n%2*databits+i].eq(dq_i_bitslip.o[n])
            self.specials += Instance("IDELAYE2",
                p_SIGNAL_PATTERN        = "DATA",
                p_DELAY_SRC             = "IDATAIN",
                p_CINVCTRL_SEL          = "FALSE",
                p_HIGH_PERFORMANCE_MODE = "TRUE",
                p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                p_PIPE_SEL              = "FALSE",
                p_IDELAY_TYPE           = "VARIABLE",
                p_IDELAY_VALUE          = 0,
                i_C        = ClockSignal("sys"),
                i_LD       = (bit_sel(i) & rdly_dq_rst) | self._rst.storage,
                i_LDPIPEEN = 0,
                i_CE       = bit_sel(i) & rdly_dq_inc,
                i_INC      = 1,
                i_IDATAIN  = dq_i,
                o_DATAOUT  = dq_i_delayed,
            )
            self.specials += Instance("IOBUF",
                i_I   = dq_o,
                o_O   = dq_i,
                i_T   = dq_t,
                io_IO = pads.dq[i],
            )

        # Read Control Path ------------------------------------------------------------------------
        rddata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].rddata_en for i in range(nphases)]),
            ntaps  = self.settings.read_latency)
        self.submodules += rddata_en
        self.comb += [phase.rddata_valid.eq(rddata_en.output | self._wlevel_en.storage)
            for phase in dfi.phases]

        # Write Control Path -----------------------------------------------------------------------
        wrtap = cwl_sys_latency - 1
        wrdata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].wrdata_en for i in range(nphases)]),
            ntaps  = wrtap + 2)
        self.submodules += wrdata_en
        self.comb += dq_oe.eq(wrdata_en.taps[wrtap])
        self.comb += If(self._wlevel_en.storage, dqs_oe.eq(1)).Else(dqs_oe.eq(dq_oe))
        self.comb += dqs_preamble.eq( wrdata_en.taps[wrtap - 1] & ~wrdata_en.taps[wrtap + 0])
        self.comb += dqs_postamble.eq(wrdata_en.taps[wrtap + 1] & ~wrdata_en.taps[wrtap + 0])

    def add_constraints(self, platform):
        """Timing of the phase-shifted crossing and the MMCM placement.

        The commands leave sys on its falling edge and enter the shifted CLKDIV: the CK phase
        range (+-1/2 tCK) goes in as clock uncertainty on that crossing, setup and hold. The
        MMCM's output clocks only exist once the netlist is linked, so the uncertainty is set
        before placement rather than in the XDC."""
        sys_clk = f"[get_clocks -of_objects [get_pins -hierarchical -filter {{{{NAME =~ *{self.name}_mmcm/CLKIN1}}}}]]"
        c_clk   = f"[get_clocks -of_objects [get_pins -hierarchical -filter {{{{NAME =~ *{self.name}_mmcm/CLKOUT0}}}}]]"
        for kind in ("setup", "hold"):
            platform.toolchain.pre_placement_commands.append(
                f"set_clock_uncertainty -{kind} 1.0 -from {sys_clk} -to {c_clk}")
        if self.mmcm_loc is not None:
            platform.add_platform_command(
                f"set_property LOC {self.mmcm_loc} [get_cells -hierarchical -filter {{{{NAME =~ *{self.name}_mmcm}}}}]")
