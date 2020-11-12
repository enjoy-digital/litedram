#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# SPDX-License-Identifier: BSD-2-Clause

# 1:4, 1:2 frequency-ratio DDR2/DDR3 PHY for Xilinx's Series7
# DDR2: 400, 533, 667, 800 and 1066 MT/s
# DDR3: 800, 1066, 1333 and 1600 MT/s

from functools import reduce
from operator import or_

import math

from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# Xilinx Series7 DDR2/DDR3 PHY ---------------------------------------------------------------------

class S7DDRPHY(Module, AutoCSR):
    def __init__(self, pads, with_odelay,
        memtype          = "DDR3",
        nphases          = 4,
        sys_clk_freq     = 100e6,
        iodelay_clk_freq = 200e6,
        cmd_latency      = 1,
        cmd_delay        = None):
        assert not (memtype == "DDR3" and nphases == 2)
        phytype     = self.__class__.__name__
        pads        = PHYPadsCombiner(pads)
        tck         = 2/(2*nphases*sys_clk_freq)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = nphases
        assert databits%8 == 0

        # Parameters -------------------------------------------------------------------------------
        iodelay_tap_average = {
            200e6: 78e-12,
            300e6: 52e-12,
            400e6: 39e-12, # Only valid for -3 and -2/2E speed grades
        }
        half_sys8x_taps = math.floor(tck/(4*iodelay_tap_average[iodelay_clk_freq]))

        cl, cwl         = get_cl_cw(memtype, tck)
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)
        rdphase         = get_sys_phase(nphases, cl_sys_latency,   cl + cmd_latency)
        wrphase         = get_sys_phase(nphases, cwl_sys_latency, cwl + cmd_latency)

        # Registers --------------------------------------------------------------------------------
        self._rst             = CSRStorage()

        self._dly_sel         = CSRStorage(databits//8)
        self._half_sys8x_taps = CSRStorage(5, reset=half_sys8x_taps)

        self._wlevel_en     = CSRStorage()
        self._wlevel_strobe = CSR()

        if with_odelay:
            self._cdly_rst = CSR()
            self._cdly_inc = CSR()

        self._dly_sel = CSRStorage(databits//8)

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

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            phytype       = phytype,
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = 2*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = self._rdphase.storage,
            wrphase       = self._wrphase.storage,
            cl            = cl,
            cwl           = cwl,
            read_latency  = cl_sys_latency + 6,
            write_latency = cwl_sys_latency - 1,
            cmd_latency   = cmd_latency,
            cmd_delay     = cmd_delay,
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, 4)

        # # #

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)

            # Clock --------------------------------------------------------------------------------
            ddr_clk = "sys2x" if nphases == 2 else "sys4x"
            for i in range(len(pads.clk_p)):
                sd_clk_se_nodelay = Signal()
                sd_clk_se_delayed = Signal()
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = ResetSignal() | self._rst.storage,
                    i_CLK    = ClockSignal(ddr_clk),
                    i_CLKDIV = ClockSignal(),
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
                        i_C        = ClockSignal(),
                        i_LD       = self._cdly_rst.re | self._rst.storage,
                        i_LDPIPEEN = 0,
                        i_CE       = self._cdly_inc.re,
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
            commands = {
                "a"    : "address",
                "ba"   : "bank"   ,
                "ras_n": "ras_n"  ,
                "cas_n": "cas_n"  ,
                "we_n" : "we_n"   ,
                "cke"  : "cke"    ,
                "odt"  : "odt"    ,
            }
            if hasattr(pads, "reset_n"): commands.update({"reset_n" : "reset_n"})
            if hasattr(pads, "cs_n")   : commands.update({"cs_n"    : "cs_n"})
            for pad_name, dfi_name in commands.items():
                pad = getattr(pads, pad_name)
                for i in range(len(pad)):
                    oq  = Signal()
                    self.specials += Instance("OSERDESE2",
                        p_SERDES_MODE    = "MASTER",
                        p_DATA_WIDTH     = 2*nphases,
                        p_TRISTATE_WIDTH = 1,
                        p_DATA_RATE_OQ   = "DDR",
                        p_DATA_RATE_TQ   = "BUF",
                        i_RST    = ResetSignal() | self._rst.storage,
                        i_CLK    = ClockSignal(ddr_clk),
                        i_CLKDIV = ClockSignal(),
                        **{f"i_D{n+1}": getattr(dfi.phases[n//2], dfi_name)[i] for n in range(8)},
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
                            i_C        = ClockSignal(),
                            i_LD       = self._cdly_rst.re | self._rst.storage,
                            i_LDPIPEEN = 0,
                            i_CE       = self._cdly_inc.re,
                            i_INC      = 1,
                            o_ODATAIN  = oq,
                            o_DATAOUT  = pad[i],
                        )

        # DQS --------------------------------------------------------------------------------------
        dqs_oe        = Signal()
        dqs_preamble  = Signal()
        dqs_postamble = Signal()
        dqs_oe_delay  = TappedDelayLine(ntaps=2 if nphases == 4 else 1)
        dqs_pattern   = DQSPattern(
            #preamble      = dqs_preamble,  # FIXME
            #postamble     = dqs_postamble, # FIXME
            wlevel_en     = self._wlevel_en.storage,
            wlevel_strobe = self._wlevel_strobe.re,
            register      = not with_odelay)
        self.submodules += dqs_oe_delay, dqs_pattern
        self.comb += dqs_oe_delay.input.eq(dqs_preamble | dqs_oe | dqs_postamble)
        for i in range(databits//8):
            dqs_o_no_delay = Signal()
            dqs_o_delayed  = Signal()
            dqs_t          = Signal()
            dqs_bitslip    = BitSlip(8,
                i      = dqs_pattern.o,
                rst    = (self._dly_sel.storage[i] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[i] & self._wdly_dq_bitslip.re,
                cycles = 1)
            self.submodules += dqs_bitslip
            self.specials += Instance("OSERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_DATA_WIDTH     = 2*nphases,
                p_TRISTATE_WIDTH = 1,
                p_DATA_RATE_OQ   = "DDR",
                p_DATA_RATE_TQ   = "BUF",
                i_RST    = ResetSignal() | self._rst.storage,
                i_CLK    = ClockSignal(ddr_clk) if with_odelay else ClockSignal(ddr_clk+"_dqs"),
                i_CLKDIV = ClockSignal(),
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
                    i_C        = ClockSignal(),
                    i_LD       = (self._dly_sel.storage[i] & self._wdly_dqs_rst.re) | self._rst.storage,
                    i_CE       = self._dly_sel.storage[i] & self._wdly_dqs_inc.re,
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
                dm_o_nodelay = Signal()
                dm_o_bitslip = BitSlip(8,
                    i      = Cat(*[dfi.phases[n//2].wrdata_mask[n%2*databits//8+i] for n in range(8)]),
                    rst    = (self._dly_sel.storage[i] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                    slp    = self._dly_sel.storage[i] & self._wdly_dq_bitslip.re,
                    cycles = 1)
                self.submodules += dm_o_bitslip
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = ResetSignal() | self._rst.storage,
                    i_CLK    = ClockSignal(ddr_clk),
                    i_CLKDIV = ClockSignal(),
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
                        i_C        = ClockSignal(),
                        i_LD       = (self._dly_sel.storage[i] & self._wdly_dq_rst.re) | self._rst.storage,
                        i_LDPIPEEN = 0,
                        i_CE       = self._dly_sel.storage[i] & self._wdly_dq_inc.re,
                        i_INC      = 1,
                        o_ODATAIN  = dm_o_nodelay,
                        o_DATAOUT  = pads.dm[i],
                    )

        # DQ ---------------------------------------------------------------------------------------
        dq_oe = Signal()
        dq_oe_delay = TappedDelayLine(ntaps=2 if nphases == 4 else 1)
        self.submodules += dq_oe_delay
        self.comb += dq_oe_delay.input.eq(dqs_preamble | dq_oe | dqs_postamble)
        for i in range(databits):
            dq_o_nodelay = Signal()
            dq_o_delayed = Signal()
            dq_i_nodelay = Signal()
            dq_i_delayed = Signal()
            dq_t         = Signal()
            dq_i_data    = Signal(8)
            dq_o_bitslip = BitSlip(8,
                i      = Cat(*[dfi.phases[n//2].wrdata[n%2*databits+i] for n in range(8)]),
                rst    = (self._dly_sel.storage[i//8] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[i//8] & self._wdly_dq_bitslip.re,
                cycles = 1)
            self.submodules += dq_o_bitslip
            self.specials += Instance("OSERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_DATA_WIDTH     = 2*nphases,
                p_TRISTATE_WIDTH = 1,
                p_DATA_RATE_OQ   = "DDR",
                p_DATA_RATE_TQ   = "BUF",
                i_RST    = ResetSignal() | self._rst.storage,
                i_CLK    = ClockSignal(ddr_clk),
                i_CLKDIV = ClockSignal(),
                **{f"i_D{n+1}": dq_o_bitslip.o[n] for n in range(8)},
                i_TCE    = 1,
                i_T1     = ~dq_oe_delay.output,
                o_TQ     = dq_t,
                i_OCE    = 1,
                o_OQ     = dq_o_nodelay,
            )
            dq_i_bitslip = BitSlip(8,
                rst    = (self._dly_sel.storage[i//8] & self._rdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[i//8] & self._rdly_dq_bitslip.re,
                cycles = 1)
            self.submodules += dq_i_bitslip
            self.specials += Instance("ISERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_INTERFACE_TYPE = "NETWORKING",
                p_DATA_WIDTH     = 2*nphases,
                p_DATA_RATE      = "DDR",
                p_NUM_CE         = 1,
                p_IOBDELAY       = "IFD",
                i_RST     = ResetSignal() | self._rst.storage,
                i_CLK     = ClockSignal(ddr_clk),
                i_CLKB    = ~ClockSignal(ddr_clk),
                i_CLKDIV  = ClockSignal(),
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
                    i_C        = ClockSignal(),
                    i_LD       = (self._dly_sel.storage[i//8] & self._wdly_dq_rst.re)| self._rst.storage,
                    i_LDPIPEEN = 0,
                    i_CE       = self._dly_sel.storage[i//8] & self._wdly_dq_inc.re,
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
                i_C        = ClockSignal(),
                i_LD       = (self._dly_sel.storage[i//8] & self._rdly_dq_rst.re) | self._rst.storage,
                i_LDPIPEEN = 0,
                i_CE       = self._dly_sel.storage[i//8] & self._rdly_dq_inc.re,
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

# Xilinx Virtex7 (S7DDRPHY with odelay) ------------------------------------------------------------

class V7DDRPHY(S7DDRPHY):
    def __init__(self, pads, **kwargs):
        S7DDRPHY.__init__(self, pads, with_odelay=True, **kwargs)

# Xilinx Kintex7 (S7DDRPHY with odelay) ------------------------------------------------------------

class K7DDRPHY(S7DDRPHY):
    def __init__(self, pads, **kwargs):
        S7DDRPHY.__init__(self, pads, with_odelay=True, **kwargs)

# Xilinx Artix7 (S7DDRPHY without odelay, sys2/4x_dqs generated in CRG with 90° phase vs sys2/4x) --

class A7DDRPHY(S7DDRPHY):
    def __init__(self, pads, cmd_latency=0, **kwargs):
        S7DDRPHY.__init__(self, pads, with_odelay=False, cmd_latency=cmd_latency, **kwargs)
