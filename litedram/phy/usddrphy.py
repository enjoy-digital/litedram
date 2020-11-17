#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# 1:4 frequency-ratio DDR3/DDR4 PHY for Kintex/Virtex Ultrascale (Plus)
# DDR3: 800, 1066, 1333 and 1600 MT/s
# DDR4: 1600 MT/s

from functools import reduce
from operator import or_

import math

from migen import *
from migen.genlib.misc import WaitTimer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# Xilinx Ultrascale (Plus) DDR3/DDR4 PHY -----------------------------------------------------------

class USDDRPHY(Module, AutoCSR):
    def __init__(self, pads,
        memtype          = "DDR3",
        sys_clk_freq     = 100e6,
        iodelay_clk_freq = 200e6,
        cmd_latency      = 1,
        cmd_delay        = None,
        is_rdimm         = False):
        phytype     = self.__class__.__name__
        device      = {"USDDRPHY": "ULTRASCALE", "USPDDRPHY": "ULTRASCALE_PLUS"}[phytype]
        pads        = PHYPadsCombiner(pads)
        tck         = 2/(2*4*sys_clk_freq)
        addressbits = len(pads.a)
        if memtype == "DDR4":
            addressbits += 3 # cas_n/ras_n/we_n multiplexed with address
        bankbits = len(pads.ba) if memtype == "DDR3" else len(pads.ba) + len(pads.bg)
        nranks   = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits = len(pads.dq)
        nphases  = 4
        assert databits%8 == 0
        x4_dimm_mode = (databits / len(pads.dqs_p)) == 4

        # Parameters -------------------------------------------------------------------------------
        if phytype == "USDDRPHY":  assert iodelay_clk_freq >= 200e6
        if phytype == "USPDDRPHY": assert iodelay_clk_freq >= 300e6

        cl, cwl         = get_cl_cw(memtype, tck)
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)
        rdphase         = get_sys_phase(nphases, cl_sys_latency,   cl + cmd_latency)
        wrphase         = get_sys_phase(nphases, cwl_sys_latency, cwl + cmd_latency)

        # Registers --------------------------------------------------------------------------------
        self._rst                 = CSRStorage()

        self._en_vtc              = CSRStorage(reset=1)

        self._half_sys8x_taps     = CSRStatus(9)

        self._wlevel_en           = CSRStorage()
        self._wlevel_strobe       = CSR()

        self._cdly_rst            = CSR()
        self._cdly_inc            = CSR()
        self._cdly_value          = CSRStatus(9)

        self._dly_sel             = CSRStorage(databits//8)

        self._rdly_dq_rst         = CSR()
        self._rdly_dq_inc         = CSR()
        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        self._wdly_dq_rst         = CSR()
        self._wdly_dq_inc         = CSR()
        self._wdly_dqs_rst        = CSR()
        self._wdly_dqs_inc        = CSR()

        self._wdly_dq_bitslip_rst = CSR()
        self._wdly_dq_bitslip     = CSR()

        self._rdphase = CSRStorage(2, reset=rdphase)
        self._wrphase = CSRStorage(2, reset=wrphase)

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
            read_latency  = cl_sys_latency + 5,
            write_latency = cwl_sys_latency - 1,
            cmd_latency   = cmd_latency,
            cmd_delay     = cmd_delay,
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
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
        if memtype == "DDR4":
            dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
            self.submodules += DDR4DFIMux(self.dfi, dfi)

        # # #

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)

            # Clock --------------------------------------------------------------------------------
            clk_o_nodelay = Signal()
            clk_o_delayed = Signal()
            self.specials += [
                Instance("OSERDESE3",
                    p_SIM_DEVICE         = device,
                    p_DATA_WIDTH         = 8,
                    p_INIT               = 0,
                    p_IS_RST_INVERTED    = 0,
                    p_IS_CLK_INVERTED    = 0,
                    p_IS_CLKDIV_INVERTED = 0,
                    i_RST    = ResetSignal() | self._rst.storage,
                    i_CLK    = ClockSignal("sys4x"),
                    i_CLKDIV = ClockSignal(),
                    i_D      = 0b10101010,
                    o_OQ     = clk_o_nodelay,
                ),
                Instance("ODELAYE3",
                    p_SIM_DEVICE       = device,
                    p_CASCADE          = "NONE",
                    p_UPDATE_MODE      = "ASYNC",
                    p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                    p_DELAY_FORMAT     = "TIME",
                    p_DELAY_TYPE       = "VARIABLE",
                    p_DELAY_VALUE      = 0,
                    i_RST          = self._cdly_rst.re | self._rst.storage,
                    i_CLK          = ClockSignal(),
                    i_EN_VTC       = self._en_vtc.storage,
                    i_CE           = self._cdly_inc.re,
                    i_INC          = 1,
                    o_CNTVALUEOUT  = self._cdly_value.status,
                    i_ODATAIN      = clk_o_nodelay,
                    o_DATAOUT      = clk_o_delayed,
                ),
                Instance("OBUFDS",
                    i_I  = clk_o_delayed,
                    o_O  = pads.clk_p,
                    o_OB = pads.clk_n,
                )
            ]

            # Commands -----------------------------------------------------------------------------
            pads_ba = Signal(bankbits)
            commands = {
                "a"     : "address",
                pads_ba : "bank",
                "ras_n" : "ras_n"  ,
                "cas_n" : "cas_n"  ,
                "we_n"  : "we_n"   ,
                "cke"   : "cke"    ,
                "odt"   : "odt"    ,
            }
            if hasattr(pads, "reset_n"): commands.update({"reset_n" : "reset_n"})
            if hasattr(pads, "cs_n")   : commands.update({"cs_n"    : "cs_n"})
            if hasattr(pads, "act_n")  : commands.update({"act_n"   : "act_n"})
            for pad_name, dfi_name in commands.items():
                pad = pad_name if isinstance(pad_name, Signal) else getattr(pads, pad_name)
                for i in range(len(pad)):
                    o_nodelay = Signal()
                    self.specials += [
                        Instance("OSERDESE3",
                            p_SIM_DEVICE         = device,
                            p_DATA_WIDTH         = 8,
                            p_INIT               = 0,
                            p_IS_RST_INVERTED    = 0,
                            p_IS_CLK_INVERTED    = 0,
                            p_IS_CLKDIV_INVERTED = 0,
                            i_RST    = ResetSignal() | self._rst.storage,
                            i_CLK    = ClockSignal("sys4x"),
                            i_CLKDIV = ClockSignal(),
                            i_D      = Cat(*[getattr(dfi.phases[n//2], dfi_name)[i] for n in range(8)]),
                            o_OQ     = o_nodelay,
                        ),
                        Instance("ODELAYE3",
                            p_SIM_DEVICE       = device,
                            p_CASCADE          = "NONE",
                            p_UPDATE_MODE      = "ASYNC",
                            p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                            p_DELAY_FORMAT     = "TIME",
                            p_DELAY_TYPE       = "VARIABLE",
                            p_DELAY_VALUE      = 0,
                            i_RST     = self._cdly_rst.re | self._rst.storage,
                            i_CLK     = ClockSignal(),
                            i_EN_VTC  = self._en_vtc.storage,
                            i_CE      = self._cdly_inc.re,
                            i_INC     = 1,
                            i_ODATAIN = o_nodelay,
                            o_DATAOUT = pad[i],
                        )
                    ]

            self.comb += pads.ba.eq(pads_ba)
            if hasattr(pads, "bg"):
                self.comb += pads.bg.eq(pads_ba[len(pads.ba):])

            if hasattr(pads, "ten"):
                self.comb += pads.ten.eq(0)

        # DQS --------------------------------------------------------------------------------------
        dqs_oe        = Signal()
        dqs_preamble  = Signal()
        dqs_postamble = Signal()
        dqs_oe_delay  = TappedDelayLine(ntaps=1)
        dqs_pattern   = DQSPattern(
            #preamble      = dqs_preamble,  # FIXME
            #postamble     = dqs_postamble, # FIXME
            wlevel_en     = self._wlevel_en.storage,
            wlevel_strobe = self._wlevel_strobe.re)
        self.submodules += dqs_oe_delay, dqs_pattern
        self.comb += dqs_oe_delay.input.eq(dqs_preamble | dqs_oe | dqs_postamble)
        for i in range(databits//8):
            if i == 0:
                # Store initial DQS DELAY_VALUE (in taps) to be able to reload DELAY_VALUE after reset.
                dqs_taps       = Signal(9)
                dqs_taps_timer = WaitTimer(2**16)
                dqs_taps_done  = Signal()
                self.submodules += dqs_taps_timer
                self.comb += dqs_taps_timer.wait.eq(~dqs_taps_done)
                self.sync += \
                    If(dqs_taps_timer.done,
                        dqs_taps_done.eq(1),
                        self._half_sys8x_taps.status.eq(dqs_taps)
                    )
            dqs_bitslip    = BitSlip(8,
                i      = dqs_pattern.o,
                rst    = (self._dly_sel.storage[i] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[i] & self._wdly_dq_bitslip.re,
                cycles = 1)
            self.submodules += dqs_bitslip
            if x4_dimm_mode:
                dqs_pads = ((pads.dqs_p[i*2], pads.dqs_n[i*2]), (pads.dqs_p[i*2 + 1], pads.dqs_n[i*2 + 1]))
            else:
                dqs_pads = ((pads.dqs_p[i], pads.dqs_n[i]), )
            for j, (dqs_p, dqs_n) in enumerate(dqs_pads):
                dqs_nodelay = Signal()
                dqs_delayed = Signal()
                dqs_t       = Signal()
                self.specials += [
                    Instance("OSERDESE3",
                        p_SIM_DEVICE         = device,
                        p_DATA_WIDTH         = 8,
                        p_INIT               = 0,
                        p_IS_RST_INVERTED    = 0,
                        p_IS_CLK_INVERTED    = 0,
                        p_IS_CLKDIV_INVERTED = 0,
                        i_RST    = ResetSignal() | self._rst.storage,
                        i_CLK    = ClockSignal("sys4x"),
                        i_CLKDIV = ClockSignal(),
                        i_T      = ~dqs_oe_delay.output,
                        i_D      = dqs_bitslip.o,
                        o_OQ     = dqs_nodelay,
                        o_T_OUT  = dqs_t,

                    ),
                    Instance("ODELAYE3",
                        p_SIM_DEVICE       = device,
                        p_CASCADE          = "NONE",
                        p_UPDATE_MODE      = "ASYNC",
                        p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                        p_IS_CLK_INVERTED  = 0,
                        p_IS_RST_INVERTED  = 0,
                        p_DELAY_FORMAT     = "TIME",
                        p_DELAY_TYPE       = "VARIABLE",
                        p_DELAY_VALUE      = int(tck*1e12/4),
                        i_RST         = (self._dly_sel.storage[i] & self._wdly_dqs_rst.re) | self._rst.storage,
                        i_CLK         = ClockSignal(),
                        i_EN_VTC      = self._en_vtc.storage,
                        i_CE          = self._dly_sel.storage[i] & self._wdly_dqs_inc.re,
                        i_INC         = 1,
                        o_CNTVALUEOUT = Signal(9) if i != 0 or j != 0 else dqs_taps,
                        i_ODATAIN     = dqs_nodelay,
                        o_DATAOUT     = dqs_delayed,
                    ),
                    Instance("IOBUFDSE3",
                        i_I    = dqs_delayed,
                        i_T    = dqs_t,
                        io_IO  = dqs_p,
                        io_IOB = dqs_n,
                    )
                ]

        # DM ---------------------------------------------------------------------------------------
        for i in range(databits//8):
            if hasattr(pads, "dm"):
                dm_i = Cat(*[dfi.phases[n//2].wrdata_mask[n%2*databits//8+i] for n in range(8)])
                if memtype == "DDR4":  # Inverted polarity for DDR4
                    dm_i = ~dm_i
                dm_o_nodelay = Signal()
                dm_o_bitslip = BitSlip(8,
                    i      = dm_i,
                    rst    = (self._dly_sel.storage[i] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                    slp    = self._dly_sel.storage[i] & self._wdly_dq_bitslip.re,
                    cycles = 1)
                self.submodules += dm_o_bitslip
                self.specials += [
                    Instance("OSERDESE3",
                        p_SIM_DEVICE         = device,
                        p_DATA_WIDTH         = 8,
                        p_INIT               = 0,
                        p_IS_RST_INVERTED    = 0,
                        p_IS_CLK_INVERTED    = 0,
                        p_IS_CLKDIV_INVERTED = 0,
                        i_RST    = ResetSignal() | self._rst.storage,
                        i_CLK    = ClockSignal("sys4x"),
                        i_CLKDIV = ClockSignal(),
                        i_D      = dm_o_bitslip.o,
                        o_OQ     = dm_o_nodelay,
                    ),
                    Instance("ODELAYE3",
                        p_SIM_DEVICE       = device,
                        p_CASCADE          = "NONE",
                        p_UPDATE_MODE      = "ASYNC",
                        p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                        p_IS_CLK_INVERTED  = 0,
                        p_IS_RST_INVERTED  = 0,
                        p_DELAY_FORMAT     = "TIME",
                        p_DELAY_TYPE       = "VARIABLE",
                        p_DELAY_VALUE      = 0,
                        i_RST     = (self._dly_sel.storage[i] & self._wdly_dq_rst.re) | self._rst.storage,
                        i_EN_VTC  = self._en_vtc.storage,
                        i_CLK     = ClockSignal(),
                        i_CE      = self._dly_sel.storage[i] & self._wdly_dq_inc.re,
                        i_INC     = 1,
                        i_ODATAIN = dm_o_nodelay,
                        o_DATAOUT = pads.dm[i],
                    )
                ]

        # DQ ---------------------------------------------------------------------------------------
        dq_oe = Signal()
        dq_oe_delay = TappedDelayLine(ntaps=1)
        self.submodules += dq_oe_delay
        self.comb += dq_oe_delay.input.eq(dqs_preamble | dq_oe | dqs_postamble)
        for i in range(databits):
            dq_o_nodelay = Signal()
            dq_o_delayed = Signal()
            dq_i_nodelay = Signal()
            dq_i_delayed = Signal()
            dq_t         = Signal()
            dq_o_bitslip = BitSlip(8,
                i      = Cat(*[dfi.phases[n//2].wrdata[n%2*databits+i] for n in range(8)]),
                rst    = (self._dly_sel.storage[i//8] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[i//8] & self._wdly_dq_bitslip.re,
                cycles = 1)
            self.submodules += dq_o_bitslip
            self.specials += Instance("OSERDESE3",
                p_SIM_DEVICE         = device,
                p_DATA_WIDTH         = 8,
                p_INIT               = 0,
                p_IS_RST_INVERTED    = 0,
                p_IS_CLK_INVERTED    = 0,
                p_IS_CLKDIV_INVERTED = 0,
                i_RST    = ResetSignal() | self._rst.storage,
                i_CLK    = ClockSignal("sys4x"),
                i_CLKDIV = ClockSignal(),
                i_D      = dq_o_bitslip.o,
                i_T      = ~dq_oe_delay.output,
                o_OQ     = dq_o_nodelay,
                o_T_OUT  = dq_t,
            )
            dq_i_bitslip = BitSlip(8,
                rst    = (self._dly_sel.storage[i//8] & self._rdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[i//8] & self._rdly_dq_bitslip.re,
                cycles = 1)
            self.submodules += dq_i_bitslip
            self.specials += Instance("ISERDESE3",
                p_SIM_DEVICE        = device,
                p_IS_CLK_INVERTED   = 0,
                p_IS_CLK_B_INVERTED = 1,
                p_DATA_WIDTH        = 8,
                i_RST        = ResetSignal(),
                i_CLK        = ClockSignal("sys4x"),
                i_CLK_B      = ClockSignal("sys4x"), # locally inverted
                i_CLKDIV     = ClockSignal(),
                i_D          = dq_i_delayed,
                i_FIFO_RD_EN = 0,
                o_Q          = dq_i_bitslip.i,
            )
            for n in range(8):
                self.comb += dfi.phases[n//2].rddata[n%2*databits+i].eq(dq_i_bitslip.o[n])
            self.specials += Instance("ODELAYE3",
                p_SIM_DEVICE       = device,
                p_CASCADE          = "NONE",
                p_UPDATE_MODE      = "ASYNC",
                p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                p_IS_CLK_INVERTED  = 0,
                p_IS_RST_INVERTED  = 0,
                p_DELAY_FORMAT     = "TIME",
                p_DELAY_TYPE       = "VARIABLE",
                p_DELAY_VALUE      = 0,
                i_RST     = (self._dly_sel.storage[i//8] & self._wdly_dq_rst.re) | self._rst.storage,
                i_CLK     = ClockSignal(),
                i_EN_VTC  = self._en_vtc.storage,
                i_CE      = self._dly_sel.storage[i//8] & self._wdly_dq_inc.re,
                i_INC     = 1,
                i_ODATAIN = dq_o_nodelay,
                o_DATAOUT = dq_o_delayed,
            )
            self.specials += Instance("IDELAYE3",
                p_SIM_DEVICE       = device,
                p_CASCADE          = "NONE",
                p_UPDATE_MODE      = "ASYNC",
                p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                p_IS_CLK_INVERTED  = 0,
                p_IS_RST_INVERTED  = 0,
                p_DELAY_FORMAT     = "TIME",
                p_DELAY_SRC        = "IDATAIN",
                p_DELAY_TYPE       = "VARIABLE",
                p_DELAY_VALUE      = 0,
                i_RST     = (self._dly_sel.storage[i//8] & self._rdly_dq_rst.re) | self._rst.storage,
                i_CLK     = ClockSignal(),
                i_EN_VTC  = self._en_vtc.storage,
                i_CE      = self._dly_sel.storage[i//8] & self._rdly_dq_inc.re,
                i_INC     = 1,
                i_IDATAIN = dq_i_nodelay,
                o_DATAOUT = dq_i_delayed,
            )
            self.specials += Instance("IOBUF",
                i_I   = dq_o_delayed,
                o_O   = dq_i_nodelay,
                i_T   = dq_t,
                io_IO = pads.dq[i],
            )

        # Read Control Path ------------------------------------------------------------------------
        # Creates a delay line of read commands coming from the DFI interface. The output is used to
        # signal a valid read data to the DFI interface.
        #
        # The read data valid is asserted for 1 sys_clk cycle when the data is available on the DFI
        # interface, the latency is the sum of the OSERDESE3, CAS, ISERDESE3 and Bitslip latencies.
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

# Xilinx Ultrascale Plus DDR3/DDR4 PHY -------------------------------------------------------------

class USPDDRPHY(USDDRPHY):
    def __init__(self, pads, **kwargs):
        USDDRPHY.__init__(self, pads, **kwargs)
