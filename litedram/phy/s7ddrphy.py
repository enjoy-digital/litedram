#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# 1:4, 1:2 frequency-ratio DDR2/DDR3 PHY for Xilinx's Series7
# DDR2: 400, 533, 667, 800 and 1066 MT/s
# DDR3: 800, 1066, 1333 , 1600 and 1866 MT/s
#
# CK phase shift (with_ck_phase_shift, DDR3 1:4 without ODELAYE2: A7DDRPHY, or K7DDRPHY on HR banks
# with with_odelay=False):
#
# Without ODELAYE2 there is no per-lane write leveling. With a fly-by command/clock bus (a DIMM-like
# layout, e.g. the nine x8 chips of a 72-bit channel), each chip sees CK at a different delay from
# its DQS and, with a single static DQS phase, only part of the lanes meet tDQSS. The PHY then moves
# CK against DQ/DQS instead:
# - CK and the command/address pins run on a pair of clocks with MMCM fine phase shift; DQ, DQS
#   and the read capture run on static clocks of the same MMCM, so DQ keeps its DQS at 90 deg and
#   the read capture does not move. The MMCM's fine-PS outputs all share one phase (the
#   FINE_PS_FRAC DRC refuses fine-PS outputs at different sub-VCO phases), so CK is the one that
#   moves.
# - One MMCM per PHY, cascaded from `sys` with its feedback through a BUFG: the static outputs
#   keep the phase of `sys` and Vivado times sys <-> static clocks as synchronous.
# - The commands cross from `sys` to the shifted CLKDIV through registers clocked on the falling
#   edge of `sys` (FDRE IS_C_INVERTED): with the CK phase kept within +-1/2 tCK of `sys`, the
#   crossing keeps about half a `sys` period of setup and hold. add_constraints() adds the phase
#   range as clock uncertainty on that crossing.
# - Each lane keeps its own write latency (write bitslip); the read side adds per-bit selection
#   (`dq_dly_sel`: the IDELAY taps and the read bitslip of single DQ bits) since the ISERDESE2 of
#   one lane do not all frame a word alike.
# The calibration (liblitedram's sdram_s7hr.c, run by the BIOS) scans the CK phase over one tCK,
# runs the per-lane write latency calibration, the per-bit read leveling and a traffic test
# (LiteDRAM BIST) at each step, and settles in the middle of the longest run every lane passes.

from functools import reduce
from operator import or_

import math

from migen import *
from migen.genlib.cdc import PulseSynchronizer
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# CK Phase Shift -----------------------------------------------------------------------------------

class S7DDRPHYCKPhase(Module, AutoCSR):
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


def _negedge(module, signal, clk):
    """`signal` registered on the falling edge of `clk` (one FDRE per bit, IS_C_INVERTED)."""
    q = Signal.like(signal)
    for i in range(len(signal)):
        module.specials += Instance("FDRE",
            p_INIT          = 0,
            p_IS_C_INVERTED = 1,
            i_C  = clk,
            i_CE = 1,
            i_R  = 0,
            i_D  = signal[i],
            o_Q  = q[i],
        )
    return q

# Xilinx Series7 DDR2/DDR3 PHY ---------------------------------------------------------------------

class S7DDRPHY(Module, AutoCSR):
    def __init__(self, pads, with_odelay,
        memtype          = "DDR3",
        nphases          = 4,
        sys_clk_freq     = 100e6,
        iodelay_clk_freq = 200e6,
        cl               = None,
        cwl              = None,
        cmd_latency      = 0,
        cmd_delay        = None,
        ddr_clk          = None,
        csr_cdc          = None,
        is_rdimm         = False,
        write_latency_calibration = True,
        with_ck_phase_shift = False,
        name             = "ddrphy",
        mmcm_loc         = None):
        # with_ck_phase_shift: CK/commands on an MMCM fine phase shift (see the file header), for
        # DDR3 1:4 without ODELAYE2. The PHY then has its own MMCM (cascaded from sys) and clock
        # domains, prefixed with `name` (unique per PHY of a SoC); `mmcm_loc` optionally places
        # the MMCM (add_constraints()).
        assert memtype in ["DDR2", "DDR3", "DDR4"]
        assert not (memtype == "DDR3" and nphases == 2)
        if with_ck_phase_shift:
            assert memtype == "DDR3" and nphases == 4 and not with_odelay
            assert ddr_clk is None and not is_rdimm
        phytype     = self.__class__.__name__
        pads        = PHYPadsCombiner(pads)
        tck         = 2/(2*nphases*sys_clk_freq)
        addressbits = len(pads.a)
        if memtype == "DDR4":
            addressbits += 3 # cas_n/ras_n/we_n multiplexed with address
        bankbits    = len(pads.ba) if memtype != "DDR4" else len(pads.ba) + len(pads.bg)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        strobes     = len(pads.dqs_p)
        with_dm     = hasattr(pads, "dm")
        nphases     = nphases
        assert databits%8 == 0
        if with_ck_phase_shift:
            assert len(pads.groups) == 1
            assert databits == 8*strobes, "x8 lanes (8 DQ per DQS)"
        self.with_ck_phase_shift = with_ck_phase_shift
        self.name                = name
        self.mmcm_loc            = mmcm_loc

        # Parameters -------------------------------------------------------------------------------
        iodelay_tap_average = {
            200e6: 78e-12,
            300e6: 52e-12,
            400e6: 39e-12, # Only valid for -3 and -2/2E speed grades
        }
        half_sys8x_taps = math.floor(tck/(4*iodelay_tap_average[iodelay_clk_freq]))

        cl              = get_default_cl( memtype, tck) if cl  is None else cl
        cwl             = get_default_cwl(memtype, tck) if cwl is None else cwl
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)
        rdphase         = get_sys_phase(nphases, cl_sys_latency,   cl + cmd_latency)
        wrphase         = get_sys_phase(nphases, cwl_sys_latency, cwl + cmd_latency)

        # Artix-7 requires read data one memory-clock phase into the ISERDESE2 word for reliable
        # read leveling. This was previously achieved by programming CL + 1 in the DDR3 MR0. Keep
        # the configured CL unchanged and express the compensation in the PHY schedule instead.
        if (memtype == "DDR3") and (not with_odelay):
            phase_cycles, rdphase = divmod(rdphase + 1, nphases)
            cl_sys_latency -= phase_cycles

        # Registers --------------------------------------------------------------------------------
        self._rst             = CSRStorage()

        self._dly_sel         = CSRStorage(strobes)
        if with_ck_phase_shift:
            self._dq_dly_sel  = CSRStorage(8, description="Read-side per-bit mask (0: all bits).")
        self._half_sys8x_taps = CSRStorage(5, reset=half_sys8x_taps)

        self._wlevel_en     = CSRStorage()
        self._wlevel_strobe = CSR()

        if with_odelay:
            self._cdly_rst = CSR()
            self._cdly_inc = CSR()

        self._rdly_dq_rst         = CSR()
        self._rdly_dq_inc         = CSR()
        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        if with_odelay:
            self._wdly_dq_rst   = CSR()
            self._wdly_dq_inc   = CSR()
            self._wdly_dqs_rst  = CSR()
            self._wdly_dqs_inc  = CSR()

        self._wdly_dq_bitslip_rst = CSR()
        self._wdly_dq_bitslip     = CSR()

        self._rdphase = CSRStorage(int(math.log2(nphases)), reset=rdphase)
        self._wrphase = CSRStorage(int(math.log2(nphases)), reset=wrphase)

        def cdc(i):
            if csr_cdc is None:
                return i
            return csr_cdc(i)

        rdly_dq_rst  = cdc(self._rdly_dq_rst.wr_stb)
        rdly_dq_inc  = cdc(self._rdly_dq_inc.wr_stb)
        rdly_dq_bitslip_rst  = cdc(self._rdly_dq_bitslip_rst.wr_stb)
        rdly_dq_bitslip  = cdc(self._rdly_dq_bitslip.wr_stb)
        wlevel_strobe = cdc(self._wlevel_strobe.wr_stb)
        if with_odelay:
            cdly_rst     = cdc(self._cdly_rst.wr_stb) | self._rst.storage
            cdly_inc     = cdc(self._cdly_inc.wr_stb)
            wdly_dq_rst  = cdc(self._wdly_dq_rst.wr_stb)
            wdly_dq_inc  = cdc(self._wdly_dq_inc.wr_stb)
            wdly_dqs_rst = cdc(self._wdly_dqs_rst.wr_stb)
            wdly_dqs_inc = cdc(self._wdly_dqs_inc.wr_stb)

        wdly_dq_bitslip_rst  = cdc(self._wdly_dq_bitslip_rst.wr_stb)
        wdly_dq_bitslip  = cdc(self._wdly_dq_bitslip.wr_stb)

        # Some calibrations like write_leveling or latency calibration are not supported
        # for DDR2 chip.
        write_calibrations = (with_odelay and (memtype not in ["DDR2"]))
        if memtype == "DDR2":
            write_latency_calibration = False
        if with_ck_phase_shift:
            write_latency_calibration = False

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
            read_latency              = cl_sys_latency + 6,
            write_latency             = cwl_sys_latency - 1,
            cmd_latency               = cmd_latency,
            cmd_delay                 = cmd_delay,
            write_leveling            = write_calibrations,
            write_dq_dqs_training     = write_calibrations,
            write_latency_calibration = write_latency_calibration,
            read_leveling             = True,
            delays                    = 32,
            bitslips                  = 8,
            with_dm                   = with_dm,
        )

        if is_rdimm:
            # All drive settings for an 8-chip load
            self.settings.set_rdimm(
                tck               = tck,
                rcd_pll_bypass    = False,
                rcd_ca_cs_drive   = 0x5,
                rcd_odt_cke_drive = 0x5,
                rcd_clk_drive     = 0x5
            )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, max(4, nphases))
        if memtype == "DDR4":
            dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
            self.submodules += DDR4DFIMux(self.dfi, dfi)

        # # #

        # Clocks/Resets of the Serializers ---------------------------------------------------------
        # CK/commands on ck_clk/ck_clkdiv, DQ/DM/read capture on dq_clk/dq_clkdiv, DQS on dqs_clk.
        ddr_clk = ddr_clk or ("sys2x" if nphases == 2 else "sys4x")
        if with_ck_phase_shift:
            ck_rst, lane_rst = self.add_ck_phase_shift(sys_clk_freq, nphases, strobes)
            ck_clk,  ck_clkdiv  = f"{name}_c4x", f"{name}_c"
            dq_clk,  dq_clkdiv  = f"{name}_w4x", f"{name}_w"
            dqs_clk = f"{name}_w4x_dqs"
        else:
            ck_rst   = ResetSignal("sys") | self._rst.storage
            lane_rst = [ResetSignal("sys") | self._rst.storage]*strobes
            ck_clk,  ck_clkdiv  = ddr_clk, "sys"
            dq_clk,  dq_clkdiv  = ddr_clk, "sys"
            dqs_clk = ddr_clk if with_odelay else ddr_clk+"_dqs"

        # Read-side selection of a DQ bit (dly_sel lanes, dq_dly_sel bits).
        if with_ck_phase_shift:
            dq_sel = Signal(8)
            self.comb += If(self._dq_dly_sel.storage == 0,
                dq_sel.eq(0xff)
            ).Else(
                dq_sel.eq(self._dq_dly_sel.storage)
            )
            def rd_sel(i):
                return self._dly_sel.storage[i//8] & dq_sel[i%8]

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)

            # Clock --------------------------------------------------------------------------------
            for i in range(len(pads.clk_p)):
                sd_clk_se_nodelay = Signal()
                sd_clk_se_delayed = Signal()
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = ck_rst,
                    i_CLK    = ClockSignal(ck_clk),
                    i_CLKDIV = ClockSignal(ck_clkdiv),
                    **{f"i_D{n+1}": (0b10101010 >> n) & 0b1 for n in range(8)},
                    o_OQ     = sd_clk_se_nodelay,
                    i_OCE    = 1,
                )
                if with_odelay:
                   self.specials += Instance("ODELAYE2",
                        p_SIGNAL_PATTERN        = "DATA",
                        p_DELAY_SRC             = "ODATAIN",
                        p_CINVCTRL_SEL          = "FALSE",
                        p_HIGH_PERFORMANCE_MODE = "TRUE",
                        p_PIPE_SEL              = "FALSE",
                        p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                        p_ODELAY_TYPE           = "VARIABLE",
                        p_ODELAY_VALUE          = 0,
                        i_C        = ClockSignal("sys"),
                        i_LD       = cdly_rst | self._rst.storage,
                        i_LDPIPEEN = 0,
                        i_CE       = cdly_inc,
                        i_INC      = 1,
                        o_ODATAIN  = sd_clk_se_nodelay,
                        o_DATAOUT  = sd_clk_se_delayed,
                    )
                self.specials += Instance("OBUFDS",
                    i_I  = sd_clk_se_delayed if with_odelay else sd_clk_se_nodelay,
                    o_O  = pads.clk_p[i],
                    o_OB = pads.clk_n[i]
                )

            # Commands -----------------------------------------------------------------------------
            pads_ba = Signal(bankbits)
            commands = {
                # Pad name: (DFI name,   Pad type (required or optional))
                "reset_n" : ("reset_n", "optional"),
                "cs_n"    : ("cs_n",    "optional"),
                "a"       : ("address", "required"),
                pads_ba   : ("bank"   , "required"),
                "ras_n"   : ("ras_n"  , "required"),
                "cas_n"   : ("cas_n"  , "required"),
                "we_n"    : ("we_n"   , "required"),
                "cke"     : ("cke"    , "optional"),
                "odt"     : ("odt"    , "optional"),
                "act_n"   : ("act_n"  , "optional"),
            }
            for pad_name, (dfi_name, pad_type) in commands.items():
                pad = pad_name if isinstance(pad_name, Signal) else getattr(pads, pad_name, None)
                if (pad is None):
                    if (pad_type == "required"):
                        raise ValueError(f"DRAM pad {pad_name} required but not found in pads.")
                    continue
                dfi_cmd = [getattr(phase, dfi_name) for phase in dfi.phases]
                if with_ck_phase_shift:
                    # Into the shifted CLKDIV through falling-edge registers of sys.
                    dfi_cmd = [_negedge(self, cmd, ClockSignal("sys")) for cmd in dfi_cmd]
                for i in range(len(pad)):
                    oq  = Signal()
                    self.specials += Instance("OSERDESE2",
                        p_SERDES_MODE    = "MASTER",
                        p_DATA_WIDTH     = 2*nphases,
                        p_TRISTATE_WIDTH = 1,
                        p_DATA_RATE_OQ   = "DDR",
                        p_DATA_RATE_TQ   = "BUF",
                        i_RST    = ck_rst,
                        i_CLK    = ClockSignal(ck_clk),
                        i_CLKDIV = ClockSignal(ck_clkdiv),
                        **{f"i_D{n+1}": dfi_cmd[n//2][i] for n in range(8)},
                        i_OCE    = 1,
                        o_OQ     = oq if with_odelay else pad[i],
                    )
                    if with_odelay:
                        self.specials += Instance("ODELAYE2",
                            p_SIGNAL_PATTERN        = "DATA",
                            p_DELAY_SRC             = "ODATAIN",
                            p_CINVCTRL_SEL          = "FALSE",
                            p_HIGH_PERFORMANCE_MODE = "TRUE",
                            p_PIPE_SEL              = "FALSE",
                            p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                            p_ODELAY_TYPE           = "VARIABLE",
                            p_ODELAY_VALUE          = 0,
                            i_C        = ClockSignal("sys"),
                            i_LD       = cdly_rst | self._rst.storage,
                            i_LDPIPEEN = 0,
                            i_CE       = cdly_inc,
                            i_INC      = 1,
                            o_ODATAIN  = oq,
                            o_DATAOUT  = pad[i],
                        )

            self.comb += pads.ba.eq(pads_ba)
            if hasattr(pads, "bg"):
                self.comb += pads.bg.eq(pads_ba[len(pads.ba):])

        # DQS --------------------------------------------------------------------------------------
        dqs_oe        = Signal()
        dqs_preamble  = Signal()
        dqs_postamble = Signal()
        dqs_oe_delay  = TappedDelayLine(ntaps=2 if nphases == 4 else 1)
        dqs_pattern   = DQSPattern(
            #preamble      = dqs_preamble,  # FIXME
            #postamble     = dqs_postamble, # FIXME
            wlevel_en     = self._wlevel_en.storage,
            wlevel_strobe = wlevel_strobe,
            register      = not with_odelay)
        self.submodules += dqs_oe_delay, dqs_pattern
        self.comb += dqs_oe_delay.input.eq(dqs_preamble | dqs_oe | dqs_postamble)
        for i in range(strobes):
            dqs_o_no_delay = Signal()
            dqs_o_delayed  = Signal()
            dqs_t          = Signal()
            dqs_bitslip    = BitSlip(8,
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
                i_CLK    = ClockSignal(dqs_clk),
                i_CLKDIV = ClockSignal(dq_clkdiv),
                **{f"i_D{n+1}": dqs_bitslip.o[n] for n in range(8)},
                i_OCE    = 1,
                o_OFB    = dqs_o_no_delay if with_odelay else Signal(),
                o_OQ     = Signal() if with_odelay else dqs_o_no_delay,
                i_TCE    = 1,
                i_T1     = ~dqs_oe_delay.output,
                o_TQ     = dqs_t,
            )
            if with_odelay:
                self.specials += Instance("ODELAYE2",
                    p_DELAY_SRC             = "ODATAIN",
                    p_SIGNAL_PATTERN        = "DATA",
                    p_CINVCTRL_SEL          = "FALSE",
                    p_HIGH_PERFORMANCE_MODE = "TRUE",
                    p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                    p_PIPE_SEL              = "FALSE",
                    p_ODELAY_TYPE           = "VARIABLE",
                    p_ODELAY_VALUE          = half_sys8x_taps,
                    i_C        = ClockSignal("sys"),
                    i_LD       = (self._dly_sel.storage[i] & wdly_dqs_rst) | self._rst.storage,
                    i_CE       = self._dly_sel.storage[i] & wdly_dqs_inc,
                    i_LDPIPEEN = 0,
                    i_INC      = 1,
                    o_ODATAIN  = dqs_o_no_delay,
                    o_DATAOUT  = dqs_o_delayed
                )
            self.specials += Instance("IOBUFDS",
                i_T    = dqs_t,
                i_I    = dqs_o_delayed if with_odelay else dqs_o_no_delay,
                io_IO  = pads.dqs_p[i],
                io_IOB = pads.dqs_n[i],
            )

        # DM ---------------------------------------------------------------------------------------
        if hasattr(pads, "dm"):
            for i in range(databits//8):
                dm_i = Cat(*[dfi.phases[n//2].wrdata_mask[n%2*databits//8+i] for n in range(8)])
                if memtype == "DDR4":  # Inverted polarity for DDR4
                    dm_i = ~dm_i
                dm_o_nodelay = Signal()
                dm_o_bitslip = BitSlip(8,
                    i      = dm_i,
                    rst    = (self._dly_sel.storage[i] & wdly_dq_bitslip_rst) | self._rst.storage,
                    slp    = self._dly_sel.storage[i] & wdly_dq_bitslip,
                    cycles = 1)
                self.submodules += dm_o_bitslip
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = lane_rst[i],
                    i_CLK    = ClockSignal(dq_clk),
                    i_CLKDIV = ClockSignal(dq_clkdiv),
                    **{f"i_D{n+1}": dm_o_bitslip.o[n] for n in range(8)},
                    i_OCE    = 1,
                    o_OQ     = dm_o_nodelay if with_odelay else pads.dm[i],
                )
                if with_odelay:
                    self.specials += Instance("ODELAYE2",
                        p_SIGNAL_PATTERN        = "DATA",
                        p_DELAY_SRC             = "ODATAIN",
                        p_CINVCTRL_SEL          = "FALSE",
                        p_HIGH_PERFORMANCE_MODE = "TRUE",
                        p_PIPE_SEL              = "FALSE",
                        p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                        p_ODELAY_TYPE           = "VARIABLE",
                        p_ODELAY_VALUE          = 0,
                        i_C        = ClockSignal("sys"),
                        i_LD       = (self._dly_sel.storage[i] & wdly_dq_rst) | self._rst.storage,
                        i_LDPIPEEN = 0,
                        i_CE       = self._dly_sel.storage[i] & wdly_dq_inc,
                        i_INC      = 1,
                        o_ODATAIN  = dm_o_nodelay,
                        o_DATAOUT  = pads.dm[i],
                    )

        # DQ ---------------------------------------------------------------------------------------
        dq_oe = Signal()
        dq_oe_delay = TappedDelayLine(ntaps=2 if nphases == 4 else 1)
        self.submodules += dq_oe_delay
        self.comb += dq_oe_delay.input.eq(dqs_preamble | dq_oe | dqs_postamble)

        dq_dqs_ratio = databits // strobes
        assert (dq_dqs_ratio in [4, 8])
        if not with_ck_phase_shift:
            def rd_sel(i):
                return self._dly_sel.storage[i//dq_dqs_ratio]

        for i in range(databits):
            dq_o_nodelay = Signal()
            dq_o_delayed = Signal()
            dq_i_nodelay = Signal()
            dq_i_delayed = Signal()
            dq_t         = Signal()
            dq_i_data    = Signal(8)
            dq_o_bitslip = BitSlip(8,
                i      = Cat(*[dfi.phases[n//2].wrdata[n%2*databits+i] for n in range(8)]),
                rst    = (self._dly_sel.storage[i//dq_dqs_ratio] & wdly_dq_bitslip_rst) | self._rst.storage,
                slp    = self._dly_sel.storage[i//dq_dqs_ratio] & wdly_dq_bitslip,
                cycles = 1)
            self.submodules += dq_o_bitslip
            self.specials += Instance("OSERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_DATA_WIDTH     = 2*nphases,
                p_TRISTATE_WIDTH = 1,
                p_DATA_RATE_OQ   = "DDR",
                p_DATA_RATE_TQ   = "BUF",
                i_RST    = lane_rst[i//dq_dqs_ratio],
                i_CLK    = ClockSignal(dq_clk),
                i_CLKDIV = ClockSignal(dq_clkdiv),
                **{f"i_D{n+1}": dq_o_bitslip.o[n] for n in range(8)},
                i_TCE    = 1,
                i_T1     = ~dq_oe_delay.output,
                o_TQ     = dq_t,
                i_OCE    = 1,
                o_OQ     = dq_o_nodelay,
            )
            dq_i_bitslip = BitSlip(8,
                rst    = (rd_sel(i) & rdly_dq_bitslip_rst) | self._rst.storage,
                slp    = rd_sel(i) & rdly_dq_bitslip,
                cycles = 1)
            self.submodules += dq_i_bitslip
            self.specials += Instance("ISERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_INTERFACE_TYPE = "NETWORKING",
                p_DATA_WIDTH     = 2*nphases,
                p_DATA_RATE      = "DDR",
                p_NUM_CE         = 1,
                p_IOBDELAY       = "IFD",
                i_RST     = lane_rst[i//dq_dqs_ratio],
                i_CLK     = ClockSignal(dq_clk),
                i_CLKB    = ~ClockSignal(dq_clk),
                i_CLKDIV  = ClockSignal(dq_clkdiv),
                i_BITSLIP = 0,
                i_CE1     = 1,
                i_DDLY    = dq_i_delayed,
                **{f"o_Q{n+1}": dq_i_bitslip.i[8-1-n] for n in range(8)},
            )
            for n in range(8):
                self.comb += dfi.phases[n//2].rddata[n%2*databits+i].eq(dq_i_bitslip.o[n])
            if with_odelay:
                self.specials += Instance("ODELAYE2",
                    p_SIGNAL_PATTERN        = "DATA",
                    p_DELAY_SRC             = "ODATAIN",
                    p_CINVCTRL_SEL          = "FALSE",
                    p_HIGH_PERFORMANCE_MODE = "TRUE",
                    p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                    p_PIPE_SEL              = "FALSE",
                    p_ODELAY_TYPE           = "VARIABLE",
                    p_ODELAY_VALUE          = 0,
                    i_C        = ClockSignal("sys"),
                    i_LD       = (self._dly_sel.storage[i//dq_dqs_ratio] & wdly_dq_rst)| self._rst.storage,
                    i_LDPIPEEN = 0,
                    i_CE       = self._dly_sel.storage[i//dq_dqs_ratio] & wdly_dq_inc,
                    i_INC      = 1,
                    o_ODATAIN  = dq_o_nodelay,
                    o_DATAOUT  = dq_o_delayed,
                )
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
                i_LD       = (rd_sel(i) & rdly_dq_rst) | self._rst.storage,
                i_LDPIPEEN = 0,
                i_CE       = rd_sel(i) & rdly_dq_inc,
                i_INC      = 1,
                i_IDATAIN  = dq_i_nodelay,
                o_DATAOUT  = dq_i_delayed
            )
            self.specials += Instance("IOBUF",
                i_I   = dq_o_delayed if with_odelay else dq_o_nodelay,
                o_O   = dq_i_nodelay,
                i_T   = dq_t,
                io_IO = pads.dq[i]
            )

        # Read Control Path ------------------------------------------------------------------------
        # Creates a delay line of read commands coming from the DFI interface. The output is used to
        # signal a valid read data to the DFI interface.
        #
        # The read data valid is asserted for 1 sys_clk cycle when the data is available on the DFI
        # interface, the latency is the sum of the OSERDESE2, CAS, ISERDESE2 and Bitslip latencies.
        rddata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].rddata_en for i in range(nphases)]),
            ntaps  = self.settings.read_latency
        )
        self.submodules += rddata_en

        self.comb += [phase.rddata_valid.eq(rddata_en.output | self._wlevel_en.storage) for phase in dfi.phases]

        # Write Control Path -----------------------------------------------------------------------
        wrtap = cwl_sys_latency - 1

        # Create a delay line of write commands coming from the DFI interface. This taps are used to
        # control DQ/DQS tristates.
        wrdata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].wrdata_en for i in range(nphases)]),
            ntaps  = wrtap + 2
        )
        self.submodules += wrdata_en

        self.comb += dq_oe.eq(wrdata_en.taps[wrtap])
        self.comb += If(self._wlevel_en.storage, dqs_oe.eq(1)).Else(dqs_oe.eq(dq_oe))

        # Write DQS Postamble/Preamble Control Path ------------------------------------------------
        # Generates DQS Preamble 1 cycle before the first write and Postamble 1 cycle after the last
        # write. During writes, DQS tristate is configured as output for at least 3 sys_clk cycles:
        # 1 for Preamble, 1 for the Write and 1 for the Postamble.
        self.comb += dqs_preamble.eq( wrdata_en.taps[wrtap - 1]  & ~wrdata_en.taps[wrtap + 0])
        self.comb += dqs_postamble.eq(wrdata_en.taps[wrtap + 1]  & ~wrdata_en.taps[wrtap + 0])


    def add_ck_phase_shift(self, sys_clk_freq, nphases, strobes):
        """The PHY's MMCM, clock domains and serializer resets (with_ck_phase_shift).

        One MMCM cascaded from sys (VCO = 2*nphases*sys = the DDR rate):
          c       sys     fine PS   CLKDIV of CK and the commands
          c4x     4x sys  fine PS   CLK of CK and the commands
          w       sys     0         CLKDIV of DQ/DQS/DM and of the read ISERDESE2
          w4x     4x sys  0         CLK of DQ/DM and of the read ISERDESE2
          w4x_dqs 4x sys  90 deg    CLK of DQS
        Returns the CK/commands serializer reset and the per-lane DQ/DQS serializer resets.
        """
        name = self.name
        self.clock_domains.cd_c       = ClockDomain(f"{name}_c")
        self.clock_domains.cd_c4x     = ClockDomain(f"{name}_c4x",     reset_less=True)
        self.clock_domains.cd_w       = ClockDomain(f"{name}_w")
        self.clock_domains.cd_w4x     = ClockDomain(f"{name}_w4x",     reset_less=True)
        self.clock_domains.cd_w4x_dqs = ClockDomain(f"{name}_w4x_dqs", reset_less=True)
        vco_mult = 2*nphases
        vco_freq = sys_clk_freq*vco_mult
        assert 600e6 <= vco_freq <= 1440e6, f"MMCM VCO {vco_freq/1e6:.1f} MHz out of range"
        self.ps_step_ps       = 1e12/vco_freq/56
        self.ps_steps_per_tck = 56*vco_mult//nphases # One tCK = 2 VCO periods = 112 steps (1:4).
        self.settings.ckphase_steps = self.ps_steps_per_tck # SDRAM_PHY_CKPHASE_STEPS (BIOS).
        fb, fb_buf = Signal(), Signal()
        outs       = [Signal() for _ in range(5)]
        self.mmcm_locked = locked = Signal()
        self.submodules.ckphase = ckphase = S7DDRPHYCKPhase()
        self.comb += ckphase.locked.eq(locked)
        self.mmcm_rst = mmcm_rst = Signal()
        self.comb += mmcm_rst.eq(ResetSignal("sys"))
        self.specials += Instance("MMCME2_ADV", name=f"{name}_mmcm",
            p_BANDWIDTH           = "OPTIMIZED",
            p_CLKIN1_PERIOD       = 1e9/sys_clk_freq,
            p_REF_JITTER1         = 0.01,
            p_DIVCLK_DIVIDE       = 1,
            p_CLKFBOUT_MULT_F     = float(vco_mult),
            p_CLKFBOUT_PHASE      = 0.0,
            p_CLKOUT0_DIVIDE_F    = float(vco_mult),
            p_CLKOUT0_PHASE       = 0.0,
            p_CLKOUT0_USE_FINE_PS = "TRUE",
            p_CLKOUT1_DIVIDE      = 2,
            p_CLKOUT1_PHASE       = 0.0,
            p_CLKOUT1_USE_FINE_PS = "TRUE",
            p_CLKOUT2_DIVIDE      = vco_mult,
            p_CLKOUT2_PHASE       = 0.0,
            p_CLKOUT3_DIVIDE      = 2,
            p_CLKOUT3_PHASE       = 0.0,
            p_CLKOUT4_DIVIDE      = 2,
            p_CLKOUT4_PHASE       = 90.0,
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
        # CLKDIV; one register per lane on the DQ/DQS side.
        serdes_rst = Signal()
        self.comb += serdes_rst.eq(ResetSignal("sys") | ~locked | self._rst.storage)
        self.specials += [
            AsyncResetSynchronizer(self.cd_c, serdes_rst),
            AsyncResetSynchronizer(self.cd_w, serdes_rst),
        ]
        lane_rst = [Signal(reset_less=True) for _ in range(strobes)]
        ck_rst   = Signal(reset_less=True)
        sync_w   = getattr(self.sync, f"{name}_w")
        sync_c   = getattr(self.sync, f"{name}_c")
        sync_w  += [r.eq(ResetSignal(f"{name}_w")) for r in lane_rst]
        sync_c  += ck_rst.eq(ResetSignal(f"{name}_c"))
        return ck_rst, lane_rst

    def add_constraints(self, platform):
        """with_ck_phase_shift: timing of the phase-shifted crossing and the MMCM placement.

        The commands leave sys on its falling edge and enter the shifted CLKDIV: the CK phase
        range (+-1/2 tCK) goes in as clock uncertainty on that crossing, setup and hold. The
        MMCM's output clocks only exist once the netlist is linked, so the uncertainty is set
        before placement rather than in the XDC."""
        if not self.with_ck_phase_shift:
            return
        sys_clk = f"[get_clocks -of_objects [get_pins -hierarchical -filter {{{{NAME =~ *{self.name}_mmcm/CLKIN1}}}}]]"
        c_clk   = f"[get_clocks -of_objects [get_pins -hierarchical -filter {{{{NAME =~ *{self.name}_mmcm/CLKOUT0}}}}]]"
        for kind in ("setup", "hold"):
            platform.toolchain.pre_placement_commands.append(
                f"set_clock_uncertainty -{kind} 1.0 -from {sys_clk} -to {c_clk}")
        if self.mmcm_loc is not None:
            platform.add_platform_command(
                f"set_property LOC {self.mmcm_loc} [get_cells -hierarchical -filter {{{{NAME =~ *{self.name}_mmcm}}}}]")

# Xilinx Virtex7 (S7DDRPHY with odelay) ------------------------------------------------------------

class V7DDRPHY(S7DDRPHY):
    def __init__(self, pads, **kwargs):
        S7DDRPHY.__init__(self, pads, with_odelay=True, **kwargs)

# Xilinx Kintex7 (S7DDRPHY with odelay on HP banks, without on HR banks) ---------------------------

class K7DDRPHY(S7DDRPHY):
    # HR banks have no ODELAYE2: with_odelay=False gives the A7DDRPHY's behaviour (sys2/4x_dqs from
    # the CRG), or with with_ck_phase_shift=True write leveling by CK phase (DDR3).
    def __init__(self, pads, with_odelay=True, write_latency_calibration=None, **kwargs):
        if write_latency_calibration is None:
            write_latency_calibration = with_odelay
        S7DDRPHY.__init__(self, pads, with_odelay=with_odelay, write_latency_calibration=write_latency_calibration, **kwargs)

# Xilinx Artix7 (S7DDRPHY without odelay, sys2/4x_dqs generated in CRG with 90° phase vs sys2/4x) --

class A7DDRPHY(S7DDRPHY):
    def __init__(self, pads, write_latency_calibration=False, **kwargs):
        S7DDRPHY.__init__(self, pads, with_odelay=False, write_latency_calibration=write_latency_calibration, **kwargs)


def s7ddrphy_with_ratio(ratio, phy_cls=A7DDRPHY, ddr_clk=None, serdes_reset_cnt=0):
    """Generate PHY class that uses DFIRateConverter to increase MC:PHY frequecy ratio"""
    ddr_clk = ddr_clk or f"sys{4*ratio}x"

    # Generate new class that wraps the original PHY
    wrapper_cls = DFIRateConverter.phy_wrapper(
        phy_cls          = phy_cls,
        ratio            = ratio,
        serdes_reset_cnt = serdes_reset_cnt,
    )

    # Create a wrapper that will ensure that correct ddr_clk kwarg is passed to the PHY
    def wrapper(*args, **kwargs):
        sys_clk_freq = kwargs.pop("sys_clk_freq", 100e6)
        return wrapper_cls(*args, ddr_clk=ddr_clk, sys_clk_freq=ratio * sys_clk_freq, **kwargs)

    return wrapper
