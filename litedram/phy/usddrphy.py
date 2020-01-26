# This file is Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

# 1:4 frequency-ratio DDR3/DDR4 PHY for Kintex/Virtex Ultrascale
# DDR3: 800, 1066, 1333 and 1600 MT/s
# DDR4: 1600 MT/s

import math

from migen import *
from migen.genlib.misc import BitSlip, WaitTimer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# Xilinx Ultrascale DDR3/DDR4 PHY ------------------------------------------------------------------

class USDDRPHY(Module, AutoCSR):
    def __init__(self, pads,
        memtype          = "DDR3",
        sys_clk_freq     = 100e6,
        iodelay_clk_freq = 200e6,
        cmd_latency      = 0):
        tck         = 2/(2*4*sys_clk_freq)
        addressbits = len(pads.a)
        if memtype == "DDR4":
            addressbits += 3 # cas_n/ras_n/we_n multiplexed with address
        bankbits = len(pads.ba) if memtype == "DDR3" else len(pads.ba) + len(pads.bg)
        nranks   = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits = len(pads.dq)
        nphases  = 4
        assert databits%8 == 0

        if hasattr(pads, "ten"):
            self.comb += pads.ten.eq(0)

        # Registers --------------------------------------------------------------------------------
        self._en_vtc              = CSRStorage(reset=1)

        self._half_sys8x_taps     = CSRStatus(9)

        self._wlevel_en           = CSRStorage()
        self._wlevel_strobe       = CSR()

        self._cdly_rst            = CSR()
        self._cdly_inc            = CSR()

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
        cl, cwl         = get_cl_cw(memtype, tck)
        cwl             = cwl + cmd_latency
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        rdcmdphase, rdphase = get_sys_phases(nphases, cl_sys_latency, cl)
        wrcmdphase, wrphase = get_sys_phases(nphases, cwl_sys_latency, cwl)
        self.settings = PhySettings(
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
            read_latency  = 2 + cl_sys_latency + 1 + 3,
            write_latency = cwl_sys_latency
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
        if memtype == "DDR4":
            dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
            self.submodules += DDR4DFIMux(self.dfi, dfi)

        # # #

        # Clock ------------------------------------------------------------------------------------
        clk_o_nodelay = Signal()
        clk_o_delayed = Signal()
        self.specials += [
            Instance("OSERDESE3",
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
                i_ODATAIN = clk_o_nodelay,
                o_DATAOUT = clk_o_delayed,
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

        # DQS and DM -------------------------------------------------------------------------------
        oe_dqs             = Signal()
        dqs_serdes_pattern = Signal(8)
        self.comb += [
            dqs_serdes_pattern.eq(0b01010101),
            If(self._wlevel_en.storage,
                dqs_serdes_pattern.eq(0b00000000),
                If(self._wlevel_strobe.re,
                    dqs_serdes_pattern.eq(0b00000001)
                )
            )
        ]
        for i in range(databits//8):
            dm_o_nodelay = Signal()
            self.specials += [
                Instance("OSERDESE3",
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

            dqs_nodelay = Signal()
            dqs_delayed = Signal()
            dqs_t       = Signal()
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
            self.specials += [
                Instance("OSERDESE3",
                    p_DATA_WIDTH         = 8,
                    p_INIT               = 0,
                    p_IS_RST_INVERTED    = 0,
                    p_IS_CLK_INVERTED    = 0,
                    p_IS_CLKDIV_INVERTED = 0,
                    i_RST    = ResetSignal(),
                    i_CLK    = ClockSignal("sys4x"),
                    i_CLKDIV = ClockSignal(),
                    i_T      = ~oe_dqs,
                    i_D      = Cat(
                        dqs_serdes_pattern[0], dqs_serdes_pattern[1],
                        dqs_serdes_pattern[2], dqs_serdes_pattern[3],
                        dqs_serdes_pattern[4], dqs_serdes_pattern[5],
                        dqs_serdes_pattern[6], dqs_serdes_pattern[7]),
                    o_OQ     = dqs_nodelay,
                    o_T_OUT  = dqs_t,

                ),
                Instance("ODELAYE3",
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
                    o_CNTVALUEOUT = Signal(9) if i != 0 else dqs_taps,
                    i_ODATAIN     = dqs_nodelay,
                    o_DATAOUT     = dqs_delayed,
                ),
                Instance("IOBUFDSE3",
                    i_I    = dqs_delayed,
                    i_T    = dqs_t,
                    io_IO  = pads.dqs_p[i],
                    io_IOB = pads.dqs_n[i],
                )
            ]

        # DQ ---------------------------------------------------------------------------------------
        oe_dq = Signal()
        for i in range(databits):
            dq_o_nodelay = Signal()
            dq_o_delayed = Signal()
            dq_i_nodelay = Signal()
            dq_i_delayed = Signal()
            dq_t         = Signal()
            dq_bitslip   = BitSlip(8)
            self.sync += \
                If(self._dly_sel.storage[i//8],
                    If(self._rdly_dq_bitslip_rst.re,
                        dq_bitslip.value.eq(0)
                    ).Elif(self._rdly_dq_bitslip.re,
                        dq_bitslip.value.eq(dq_bitslip.value + 1)
                    )
                )
            self.submodules += dq_bitslip
            self.specials += [
                Instance("OSERDESE3",
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
                    i_T     = ~oe_dq,
                    o_OQ     = dq_o_nodelay,
                    o_T_OUT  = dq_t,
                ),
                Instance("ISERDESE3",
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

        # Flow control -----------------------------------------------------------------------------
        #
        # total read latency:
        #  2 cycles through OSERDESE2
        #  cl_sys_latency cycles CAS
        #  2 cycles through ISERDESE2
        #  3 cycles through Bitslip
        rddata_en = dfi.phases[self.settings.rdphase].rddata_en
        for i in range(self.settings.read_latency-1):
            n_rddata_en = Signal()
            self.sync += n_rddata_en.eq(rddata_en)
            rddata_en = n_rddata_en
        for phase in dfi.phases:
            phase_rddata_valid = Signal()
            self.sync += phase_rddata_valid.eq(rddata_en | self._wlevel_en.storage)
            self.comb += phase.rddata_valid.eq(phase_rddata_valid)

        oe = Signal()
        last_wrdata_en = Signal(cwl_sys_latency+2)
        wrphase = dfi.phases[self.settings.wrphase]
        self.sync += last_wrdata_en.eq(Cat(wrphase.wrdata_en, last_wrdata_en[:-1]))
        self.comb += oe.eq(
            last_wrdata_en[cwl_sys_latency-1] |
            last_wrdata_en[cwl_sys_latency] |
            last_wrdata_en[cwl_sys_latency+1])
        self.sync += \
            If(self._wlevel_en.storage,
                oe_dqs.eq(1), oe_dq.eq(0)
            ).Else(
                oe_dqs.eq(oe), oe_dq.eq(oe)
            )
