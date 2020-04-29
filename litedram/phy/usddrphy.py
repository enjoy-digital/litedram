# This file is Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

# 1:4 frequency-ratio DDR3/DDR4 PHY for Kintex/Virtex Ultrascale (Plus)
# DDR3: 800, 1066, 1333 and 1600 MT/s
# DDR4: 1600 MT/s

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
        cmd_latency      = 0):
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
        cwl             = cwl + cmd_latency
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        # Registers --------------------------------------------------------------------------------
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

        # PHY settings -----------------------------------------------------------------------------
        rdcmdphase, rdphase = get_sys_phases(nphases, cl_sys_latency, cl)
        wrcmdphase, wrphase = get_sys_phases(nphases, cwl_sys_latency, cwl)
        self.settings = PhySettings(
            phytype       = phytype,
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = 2*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = rdphase,
            wrphase       = wrphase,
            rdcmdphase    = rdcmdphase,
            wrcmdphase    = wrcmdphase,
            cl            = cl,
            cwl           = cwl - cmd_latency,
            read_latency  = 2 + cl_sys_latency + 1 + 2,
            write_latency = cwl_sys_latency
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

            # Clock ------------------------------------------------------------------------------------
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
                    i_RST    = ResetSignal(),
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
                    i_RST          = self._cdly_rst.re,
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

            # Addresses and Commands -------------------------------------------------------------------
            for i in range(addressbits if memtype=="DDR3" else addressbits-3):
                a_o_nodelay = Signal()
                self.specials += [
                    Instance("OSERDESE3",
                        p_SIM_DEVICE         = device,
                        p_DATA_WIDTH         = 8,
                        p_INIT               = 0,
                        p_IS_RST_INVERTED    = 0,
                        p_IS_CLK_INVERTED    = 0,
                        p_IS_CLKDIV_INVERTED = 0,
                        i_RST    = ResetSignal(),
                        i_CLK    = ClockSignal("sys4x"),
                        i_CLKDIV = ClockSignal(),
                        i_D      = Cat(dfi.phases[0].address[i], dfi.phases[0].address[i],
                                       dfi.phases[1].address[i], dfi.phases[1].address[i],
                                       dfi.phases[2].address[i], dfi.phases[2].address[i],
                                       dfi.phases[3].address[i], dfi.phases[3].address[i]),
                         o_OQ     = a_o_nodelay,
                    ),
                    Instance("ODELAYE3",
                        p_SIM_DEVICE       = device,
                        p_CASCADE          = "NONE",
                        p_UPDATE_MODE      = "ASYNC",
                        p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                        p_DELAY_FORMAT     = "TIME",
                        p_DELAY_TYPE       = "VARIABLE",
                        p_DELAY_VALUE      = 0,
                        i_RST     = self._cdly_rst.re,
                        i_CLK     = ClockSignal(),
                        i_EN_VTC  = self._en_vtc.storage,
                        i_CE      = self._cdly_inc.re,
                        i_INC     = 1,
                        i_ODATAIN = a_o_nodelay,
                        o_DATAOUT = pads.a[i],
                    )
                ]

            pads_ba = Signal(bankbits)
            if memtype == "DDR3":
                self.comb += pads.ba.eq(pads_ba)
            else:
                self.comb += pads.ba.eq(pads_ba[:len(pads.ba)])
                self.comb += pads.bg.eq(pads_ba[len(pads.ba):])
            for i in range(bankbits):
                ba_o_nodelay = Signal()
                self.specials += [
                    Instance("OSERDESE3",
                        p_SIM_DEVICE         = device,
                        p_DATA_WIDTH         = 8,
                        p_INIT               = 0,
                        p_IS_RST_INVERTED    = 0,
                        p_IS_CLK_INVERTED    = 0,
                        p_IS_CLKDIV_INVERTED = 0,
                        i_RST    = ResetSignal(),
                        i_CLK    = ClockSignal("sys4x"),
                        i_CLKDIV = ClockSignal(),
                        i_D      = Cat(
                            dfi.phases[0].bank[i], dfi.phases[0].bank[i],
                            dfi.phases[1].bank[i], dfi.phases[1].bank[i],
                            dfi.phases[2].bank[i], dfi.phases[2].bank[i],
                            dfi.phases[3].bank[i], dfi.phases[3].bank[i]),
                        o_OQ     = ba_o_nodelay,
                    ),
                    Instance("ODELAYE3",
                        p_SIM_DEVICE       = device,
                        p_CASCADE          = "NONE",
                        p_UPDATE_MODE      = "ASYNC",
                        p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                        p_DELAY_FORMAT     = "TIME",
                        p_DELAY_TYPE       = "VARIABLE",
                        p_DELAY_VALUE      = 0,
                        i_RST     = self._cdly_rst.re,
                        i_CLK     = ClockSignal(),
                        i_EN_VTC  = self._en_vtc.storage,
                        i_CE      = self._cdly_inc.re,
                        i_INC     = 1,
                        i_ODATAIN = ba_o_nodelay,
                        o_DATAOUT = pads_ba[i],
                    )
                ]

            controls = ["ras_n", "cas_n", "we_n", "cke", "odt"]
            if hasattr(pads, "reset_n"):
                controls.append("reset_n")
            if hasattr(pads, "cs_n"):
                controls.append("cs_n")
            if hasattr(pads, "act_n"):
                controls.append("act_n")
            for name in controls:
                x_o_nodelay = Signal()
                self.specials += [
                    Instance("OSERDESE3",
                        p_SIM_DEVICE         = device,
                        p_DATA_WIDTH         = 8,
                        p_INIT               = 0,
                        p_IS_RST_INVERTED    = 0,
                        p_IS_CLK_INVERTED    = 0,
                        p_IS_CLKDIV_INVERTED = 0,
                        i_RST    = ResetSignal(),
                        i_CLK    = ClockSignal("sys4x"),
                        i_CLKDIV = ClockSignal(),
                        i_D      = Cat(
                            getattr(dfi.phases[0], name), getattr(dfi.phases[0], name),
                            getattr(dfi.phases[1], name), getattr(dfi.phases[1], name),
                            getattr(dfi.phases[2], name), getattr(dfi.phases[2], name),
                            getattr(dfi.phases[3], name), getattr(dfi.phases[3], name)),
                        o_OQ     = x_o_nodelay,
                    ),
                    Instance("ODELAYE3",
                        p_SIM_DEVICE       = device,
                        p_CASCADE          = "NONE",
                        p_UPDATE_MODE      = "ASYNC",
                        p_REFCLK_FREQUENCY = iodelay_clk_freq/1e6,
                        p_DELAY_FORMAT     = "TIME",
                        p_DELAY_TYPE       = "VARIABLE",
                        p_DELAY_VALUE      = 0,
                        i_RST     = self._cdly_rst.re,
                        i_CLK     = ClockSignal(),
                        i_EN_VTC  = self._en_vtc.storage,
                        i_CE      = self._cdly_inc.re,
                        i_INC     = 1,
                        i_ODATAIN = x_o_nodelay,
                        o_DATAOUT = getattr(pads, name),
                    )
                ]

            if hasattr(pads, "ten"):
                self.comb += pads.ten.eq(0)

        # DQS and DM -------------------------------------------------------------------------------
        dqs_oe         = Signal()
        dqs_oe_delayed = Signal() # Tristate control is asynchronous, needs to be delayed.
        dqs_pattern    = DQSPattern(
            wlevel_en     = self._wlevel_en.storage,
            wlevel_strobe = self._wlevel_strobe.re)
        self.submodules += dqs_pattern
        self.sync += dqs_oe_delayed.eq(dqs_pattern.preamble | dqs_oe | dqs_pattern.postamble)
        for i in range(databits//8):
            if hasattr(pads, "dm"):
                dm_o_nodelay = Signal()
                self.specials += [
                    Instance("OSERDESE3",
                        p_SIM_DEVICE         = device,
                        p_DATA_WIDTH         = 8,
                        p_INIT               = 0,
                        p_IS_RST_INVERTED    = 0,
                        p_IS_CLK_INVERTED    = 0,
                        p_IS_CLKDIV_INVERTED = 0,
                        i_RST    = ResetSignal(),
                        i_CLK    = ClockSignal("sys4x"),
                        i_CLKDIV = ClockSignal(),
                        i_D      = Cat(
                            dfi.phases[0].wrdata_mask[i], dfi.phases[0].wrdata_mask[databits//8+i],
                            dfi.phases[1].wrdata_mask[i], dfi.phases[1].wrdata_mask[databits//8+i],
                            dfi.phases[2].wrdata_mask[i], dfi.phases[2].wrdata_mask[databits//8+i],
                            dfi.phases[3].wrdata_mask[i], dfi.phases[3].wrdata_mask[databits//8+i]),
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
                        i_RST     = self._dly_sel.storage[i] & self._wdly_dq_rst.re,
                        i_EN_VTC  = self._en_vtc.storage,
                        i_CLK     = ClockSignal(),
                        i_CE      = self._dly_sel.storage[i] & self._wdly_dq_inc.re,
                        i_INC     = 1,
                        i_ODATAIN = dm_o_nodelay,
                        o_DATAOUT = pads.dm[i],
                    )
                ]

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
                        i_RST    = ResetSignal(),
                        i_CLK    = ClockSignal("sys4x"),
                        i_CLKDIV = ClockSignal(),
                        i_T      = ~dqs_oe_delayed,
                        i_D      = Cat(
                            dqs_pattern.o[0], dqs_pattern.o[1],
                            dqs_pattern.o[2], dqs_pattern.o[3],
                            dqs_pattern.o[4], dqs_pattern.o[5],
                            dqs_pattern.o[6], dqs_pattern.o[7]),
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
                        i_RST         = self._dly_sel.storage[i] & self._wdly_dqs_rst.re,
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

        # DQ ---------------------------------------------------------------------------------------
        dq_oe         = Signal()
        dq_oe_delayed = Signal() # Tristate control is asynchronous, needs to be delayed.
        self.sync += dq_oe_delayed.eq(dqs_pattern.preamble | dq_oe | dqs_pattern.postamble)
        for i in range(databits):
            dq_o_nodelay = Signal()
            dq_o_delayed = Signal()
            dq_i_nodelay = Signal()
            dq_i_delayed = Signal()
            dq_t         = Signal()
            dq_bitslip = BitSlip(8,
                rst = self._dly_sel.storage[i//8] & self._rdly_dq_bitslip_rst.re,
                slp = self._dly_sel.storage[i//8] & self._rdly_dq_bitslip.re)
            self.submodules += dq_bitslip
            self.specials += [
                Instance("OSERDESE3",
                    p_SIM_DEVICE         = device,
                    p_DATA_WIDTH         = 8,
                    p_INIT               = 0,
                    p_IS_RST_INVERTED    = 0,
                    p_IS_CLK_INVERTED    = 0,
                    p_IS_CLKDIV_INVERTED = 0,
                    i_RST    = ResetSignal(),
                    i_CLK    = ClockSignal("sys4x"),
                    i_CLKDIV = ClockSignal(),
                    i_D     = Cat(
                        dfi.phases[0].wrdata[i], dfi.phases[0].wrdata[databits+i],
                        dfi.phases[1].wrdata[i], dfi.phases[1].wrdata[databits+i],
                        dfi.phases[2].wrdata[i], dfi.phases[2].wrdata[databits+i],
                        dfi.phases[3].wrdata[i], dfi.phases[3].wrdata[databits+i]),
                    i_T      = ~dq_oe_delayed,
                    o_OQ     = dq_o_nodelay,
                    o_T_OUT  = dq_t,
                ),
                Instance("ISERDESE3",
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
                    o_Q          = dq_bitslip.i,
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
                    i_RST     = self._dly_sel.storage[i//8] & self._wdly_dq_rst.re,
                    i_CLK     = ClockSignal(),
                    i_EN_VTC  = self._en_vtc.storage,
                    i_CE      = self._dly_sel.storage[i//8] & self._wdly_dq_inc.re,
                    i_INC     = 1,
                    i_ODATAIN = dq_o_nodelay,
                    o_DATAOUT = dq_o_delayed,
                ),
                Instance("IDELAYE3",
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
                    i_RST     = self._dly_sel.storage[i//8] & self._rdly_dq_rst.re,
                    i_CLK     = ClockSignal(),
                    i_EN_VTC  = self._en_vtc.storage,
                    i_CE      = self._dly_sel.storage[i//8] & self._rdly_dq_inc.re,
                    i_INC     = 1,
                    i_IDATAIN = dq_i_nodelay,
                    o_DATAOUT = dq_i_delayed,
                ),
                Instance("IOBUF",
                    i_I   = dq_o_delayed,
                    o_O   = dq_i_nodelay,
                    i_T   = dq_t,
                    io_IO = pads.dq[i],
                )
            ]
            self.comb += [
                dfi.phases[0].rddata[i].eq(dq_bitslip.o[0]),
                dfi.phases[1].rddata[i].eq(dq_bitslip.o[2]),
                dfi.phases[2].rddata[i].eq(dq_bitslip.o[4]),
                dfi.phases[3].rddata[i].eq(dq_bitslip.o[6]),

                dfi.phases[0].rddata[databits+i].eq(dq_bitslip.o[1]),
                dfi.phases[1].rddata[databits+i].eq(dq_bitslip.o[3]),
                dfi.phases[2].rddata[databits+i].eq(dq_bitslip.o[5]),
                dfi.phases[3].rddata[databits+i].eq(dq_bitslip.o[7]),
            ]

        # Read Control Path ------------------------------------------------------------------------
        # Creates a shift register of read commands coming from the DFI interface. This shift register
        # is used to indicate to the DFI interface that the read data is valid.
        #
        # The read data valid is asserted for 1 sys_clk cycle when the data is available on the DFI
        # interface, the latency is the sum of the OSERDESE3, CAS, ISERDESE3 and Bitslip latencies.
        rddata_en      = Signal(self.settings.read_latency)
        rddata_en_last = Signal.like(rddata_en)
        self.comb += rddata_en.eq(Cat(dfi.phases[self.settings.rdphase].rddata_en, rddata_en_last))
        self.sync += rddata_en_last.eq(rddata_en)
        self.sync += [phase.rddata_valid.eq(rddata_en[-1] | self._wlevel_en.storage) for phase in dfi.phases]

        # Write Control Path -----------------------------------------------------------------------
        # Creates a shift register of write commands coming from the DFI interface. This shift register
        # is used to control DQ/DQS tristates.
        wrdata_en = Signal(cwl_sys_latency + 2)
        wrdata_en_last = Signal.like(wrdata_en)
        self.comb += wrdata_en.eq(Cat(dfi.phases[self.settings.wrphase].wrdata_en, wrdata_en_last))
        self.sync += wrdata_en_last.eq(wrdata_en)
        self.comb += dq_oe.eq(wrdata_en[cwl_sys_latency])
        self.comb += If(self._wlevel_en.storage, dqs_oe.eq(1)).Else(dqs_oe.eq(dq_oe))

        # Write DQS Postamble/Preamble Control Path ------------------------------------------------
        # Generates DQS Preamble 1 cycle before the first write and Postamble 1 cycle after the last
        # write. During writes, DQS tristate is configured as output for at least 3 sys_clk cycles:
        # 1 for Preamble, 1 for the Write and 1 for the Postamble.
        self.comb += dqs_pattern.preamble.eq( wrdata_en[cwl_sys_latency - 1]  & ~wrdata_en[cwl_sys_latency])
        self.comb += dqs_pattern.postamble.eq(wrdata_en[cwl_sys_latency + 1]  & ~wrdata_en[cwl_sys_latency])

# Xilinx Ultrascale Plus DDR3/DDR4 PHY -------------------------------------------------------------

class USPDDRPHY(USDDRPHY):
    def __init__(self, pads, **kwargs):
        USDDRPHY.__init__(self, pads, **kwargs)
