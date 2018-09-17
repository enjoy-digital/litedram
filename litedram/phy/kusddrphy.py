# 1:4 frequency-ratio DDR3 PHY for Kintex Ultrascale
# tCK=5ns CL=7 CWL=6

from migen import *
from migen.genlib.misc import BitSlip, WaitTimer

from litex.soc.interconnect.csr import *

from litedram.common import PhySettings
from litedram.phy.dfi import *


class KUSDDRPHY(Module, AutoCSR):
    def __init__(self, pads):
        addressbits = len(pads.a)
        bankbits = len(pads.ba)
        nranks = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits = len(pads.dq)
        nphases = 4

        self._en_vtc = CSRStorage(reset=1)

        self._wlevel_en = CSRStorage()
        self._wlevel_strobe = CSR()

        self._dly_sel = CSRStorage(databits//8)

        self._rdly_dq_rst = CSR()
        self._rdly_dq_inc = CSR()
        self._rdly_dq_bitslip = CSR()

        self._wdly_dq_rst = CSR()
        self._wdly_dq_inc = CSR()
        self._wdly_dqs_rst = CSR()
        self._wdly_dqs_inc = CSR()
        self._wdly_dqs_taps = CSRStatus(9)

        self.settings = PhySettings(
            memtype="DDR3",
            dfi_databits=2*databits,
            nranks=nranks,
            nphases=nphases,
            rdphase=0,
            wrphase=2,
            rdcmdphase=1,
            wrcmdphase=0,
            cl=7,
            cwl=6,
            read_latency=8,
            write_latency=2
        )

        self.dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)

        # # #

        # Clock
        clk_o_nodelay = Signal()
        clk_o_delayed = Signal()
        self.specials += [
            Instance("OSERDESE3",
                p_DATA_WIDTH=8, p_INIT=0,
                p_IS_CLK_INVERTED=0, p_IS_CLKDIV_INVERTED=0, p_IS_RST_INVERTED=0,

                o_OQ=clk_o_nodelay,
                i_RST=ResetSignal(),
                i_CLK=ClockSignal("sys4x"), i_CLKDIV=ClockSignal(),
                i_D=0b10101010
            ),
            Instance("ODELAYE3",
                p_CASCADE="NONE", p_UPDATE_MODE="ASYNC", p_REFCLK_FREQUENCY=200.0,
                p_DELAY_FORMAT="TIME", p_DELAY_TYPE="FIXED", p_DELAY_VALUE=0,
                i_CLK=ClockSignal(),
                i_RST=ResetSignal(),
                i_EN_VTC=1,
                i_ODATAIN=clk_o_nodelay, o_DATAOUT=clk_o_delayed
            ),
            Instance("OBUFDS",
                i_I=clk_o_delayed,
                o_O=pads.clk_p,
                o_OB=pads.clk_n
            )
        ]

        # Addresses and commands
        for i in range(addressbits):
            a_o_nodelay = Signal()
            self.specials += [
                Instance("OSERDESE3",
                    p_DATA_WIDTH=8, p_INIT=0,
                    p_IS_CLK_INVERTED=0, p_IS_CLKDIV_INVERTED=0, p_IS_RST_INVERTED=0,

                    o_OQ=a_o_nodelay,
                    i_RST=ResetSignal(),
                    i_CLK=ClockSignal("sys4x"), i_CLKDIV=ClockSignal(),
                    i_D=Cat(self.dfi.phases[0].address[i], self.dfi.phases[0].address[i],
                            self.dfi.phases[1].address[i], self.dfi.phases[1].address[i],
                            self.dfi.phases[2].address[i], self.dfi.phases[2].address[i],
                            self.dfi.phases[3].address[i], self.dfi.phases[3].address[i])
                ),
                Instance("ODELAYE3",
                    p_CASCADE="NONE", p_UPDATE_MODE="ASYNC", p_REFCLK_FREQUENCY=200.0,
                    p_DELAY_FORMAT="TIME", p_DELAY_TYPE="FIXED", p_DELAY_VALUE=0,
                    i_CLK=ClockSignal(),
                    i_RST=ResetSignal(),
                    i_EN_VTC=1,
                    i_ODATAIN=a_o_nodelay, o_DATAOUT=pads.a[i]
                )
            ]

        for i in range(bankbits):
            ba_o_nodelay = Signal()
            self.specials += [
                Instance("OSERDESE3",
                    p_DATA_WIDTH=8, p_INIT=0,
                    p_IS_CLK_INVERTED=0, p_IS_CLKDIV_INVERTED=0, p_IS_RST_INVERTED=0,

                    o_OQ=ba_o_nodelay,
                    i_RST=ResetSignal(),
                    i_CLK=ClockSignal("sys4x"), i_CLKDIV=ClockSignal(),
                    i_D=Cat(self.dfi.phases[0].bank[i], self.dfi.phases[0].bank[i],
                            self.dfi.phases[1].bank[i], self.dfi.phases[1].bank[i],
                            self.dfi.phases[2].bank[i], self.dfi.phases[2].bank[i],
                            self.dfi.phases[3].bank[i], self.dfi.phases[3].bank[i])
                ),
                Instance("ODELAYE3",
                    p_CASCADE="NONE", p_UPDATE_MODE="ASYNC", p_REFCLK_FREQUENCY=200.0,
                    p_DELAY_FORMAT="TIME", p_DELAY_TYPE="FIXED", p_DELAY_VALUE=0,
                    i_CLK=ClockSignal(),
                    i_RST=ResetSignal(),
                    i_EN_VTC=1,
                    i_ODATAIN=ba_o_nodelay, o_DATAOUT=pads.ba[i]
                )
            ]
        for name in "ras_n", "cas_n", "we_n", "cs_n", "cke", "odt", "reset_n":
            x_o_nodelay = Signal()
            self.specials += [
                Instance("OSERDESE3",
                    p_DATA_WIDTH=8, p_INIT=0,
                    p_IS_CLK_INVERTED=0, p_IS_CLKDIV_INVERTED=0, p_IS_RST_INVERTED=0,

                    o_OQ=x_o_nodelay,
                    i_RST=ResetSignal(),
                    i_CLK=ClockSignal("sys4x"), i_CLKDIV=ClockSignal(),
                    i_D=Cat(getattr(self.dfi.phases[0], name), getattr(self.dfi.phases[0], name),
                            getattr(self.dfi.phases[1], name), getattr(self.dfi.phases[1], name),
                            getattr(self.dfi.phases[2], name), getattr(self.dfi.phases[2], name),
                            getattr(self.dfi.phases[3], name), getattr(self.dfi.phases[3], name))
                ),
                Instance("ODELAYE3",
                    p_CASCADE="NONE", p_UPDATE_MODE="ASYNC", p_REFCLK_FREQUENCY=200.0,
                    p_DELAY_FORMAT="TIME", p_DELAY_TYPE="FIXED", p_DELAY_VALUE=0,
                    i_CLK=ClockSignal(),
                    i_RST=ResetSignal(),
                    i_EN_VTC=1,
                    i_ODATAIN=x_o_nodelay, o_DATAOUT=getattr(pads, name)
                )
            ]

        # DQS and DM
        oe_dqs = Signal()
        dqs_serdes_pattern = Signal(8)
        self.comb += \
            If(self._wlevel_en.storage,
                If(self._wlevel_strobe.re,
                    dqs_serdes_pattern.eq(0b00000001)
                ).Else(
                    dqs_serdes_pattern.eq(0b00000000)
                )
            ).Else(
                dqs_serdes_pattern.eq(0b01010101)
            )
        for i in range(databits//8):
            dm_o_nodelay = Signal()
            self.specials += \
                Instance("OSERDESE3",
                    p_DATA_WIDTH=8, p_INIT=0,
                    p_IS_CLK_INVERTED=0, p_IS_CLKDIV_INVERTED=0, p_IS_RST_INVERTED=0,

                    o_OQ=dm_o_nodelay,
                    i_RST=ResetSignal(),
                    i_CLK=ClockSignal("sys4x"), i_CLKDIV=ClockSignal(),
                    i_D=Cat(self.dfi.phases[0].wrdata_mask[i], self.dfi.phases[0].wrdata_mask[databits//8+i],
                            self.dfi.phases[1].wrdata_mask[i], self.dfi.phases[1].wrdata_mask[databits//8+i],
                            self.dfi.phases[2].wrdata_mask[i], self.dfi.phases[2].wrdata_mask[databits//8+i],
                            self.dfi.phases[3].wrdata_mask[i], self.dfi.phases[3].wrdata_mask[databits//8+i])
                )
            self.specials += \
                Instance("ODELAYE3",
                    p_CASCADE="NONE", p_UPDATE_MODE="ASYNC", p_REFCLK_FREQUENCY=200.0,
                    p_IS_CLK_INVERTED=0, p_IS_RST_INVERTED=0,
                    p_DELAY_FORMAT="TIME", p_DELAY_TYPE="VARIABLE", p_DELAY_VALUE=0,

                    i_CLK=ClockSignal(),
                    i_INC=1, i_EN_VTC=self._en_vtc.storage,
                    i_RST=ResetSignal() | (self._dly_sel.storage[i] & self._wdly_dq_rst.re),
                    i_CE=self._dly_sel.storage[i] & self._wdly_dq_inc.re,

                    i_ODATAIN=dm_o_nodelay, o_DATAOUT=pads.dm[i]
                )

            dqs_nodelay = Signal()
            dqs_delayed = Signal()
            dqs_t = Signal()
            if i == 0:
                # Store initial DQS DELAY_VALUE (in taps) to
                # be able to reload DELAY_VALUE after reset.
                dqs_taps = Signal(9)
                dqs_taps_timer = WaitTimer(2**16)
                self.submodules += dqs_taps_timer
                dqs_taps_done = Signal()
                self.comb += dqs_taps_timer.wait.eq(~dqs_taps_done)
                self.sync += \
                    If(dqs_taps_timer.done,
                        dqs_taps_done.eq(1),
                        self._wdly_dqs_taps.status.eq(dqs_taps)
                    )
            self.specials += [
                Instance("OSERDESE3",
                    p_DATA_WIDTH=8, p_INIT=0,
                    p_IS_CLK_INVERTED=0, p_IS_CLKDIV_INVERTED=0, p_IS_RST_INVERTED=0,

                    o_OQ=dqs_nodelay, o_T_OUT=dqs_t,
                    i_RST=ResetSignal(),
                    i_CLK=ClockSignal("sys4x"), i_CLKDIV=ClockSignal(),
                    i_D=Cat(dqs_serdes_pattern[0], dqs_serdes_pattern[1],
                            dqs_serdes_pattern[2], dqs_serdes_pattern[3],
                            dqs_serdes_pattern[4], dqs_serdes_pattern[5],
                            dqs_serdes_pattern[6], dqs_serdes_pattern[7]),
                    i_T=~oe_dqs,
                ),
                Instance("ODELAYE3",
                    p_CASCADE="NONE", p_UPDATE_MODE="ASYNC", p_REFCLK_FREQUENCY=200.0,
                    p_IS_CLK_INVERTED=0, p_IS_RST_INVERTED=0,
                    p_DELAY_FORMAT="TIME", p_DELAY_TYPE="VARIABLE", p_DELAY_VALUE=500,

                    i_CLK=ClockSignal(),
                    i_INC=1, i_EN_VTC=self._en_vtc.storage,
                    i_RST=ResetSignal() | (self._dly_sel.storage[i] & self._wdly_dqs_rst.re),
                    i_CE=self._dly_sel.storage[i] & self._wdly_dqs_inc.re,
                    o_CNTVALUEOUT=Signal(9) if i != 0 else dqs_taps,

                    i_ODATAIN=dqs_nodelay, o_DATAOUT=dqs_delayed
                ),
                Instance("IOBUFDSE3",
                    i_I=dqs_delayed, i_T=dqs_t,
                    io_IO=pads.dqs_p[i], io_IOB=pads.dqs_n[i]
                )
            ]

        # DQ
        oe_dq = Signal()
        for i in range(databits):
            dq_o_nodelay = Signal()
            dq_o_delayed = Signal()
            dq_i_nodelay = Signal()
            dq_i_delayed = Signal()
            dq_t = Signal()
            dq_bitslip = BitSlip(8)
            self.sync += \
                If(self._dly_sel.storage[i//8],
                    If(self._wdly_dq_rst.re,
                        dq_bitslip.value.eq(0)
                    ).Elif(self._rdly_dq_bitslip.re,
                        dq_bitslip.value.eq(dq_bitslip.value + 1)
                    )
                )
            self.submodules += dq_bitslip
            self.specials += [
                Instance("OSERDESE3",
                    p_DATA_WIDTH=8, p_INIT=0,
                    p_IS_CLK_INVERTED=0, p_IS_CLKDIV_INVERTED=0, p_IS_RST_INVERTED=0,

                    o_OQ=dq_o_nodelay, o_T_OUT=dq_t,
                    i_RST=ResetSignal(),
                    i_CLK=ClockSignal("sys4x"), i_CLKDIV=ClockSignal(),
                    i_D=Cat(self.dfi.phases[0].wrdata[i], self.dfi.phases[0].wrdata[databits+i],
                            self.dfi.phases[1].wrdata[i], self.dfi.phases[1].wrdata[databits+i],
                            self.dfi.phases[2].wrdata[i], self.dfi.phases[2].wrdata[databits+i],
                            self.dfi.phases[3].wrdata[i], self.dfi.phases[3].wrdata[databits+i]),
                    i_T=~oe_dq
                ),
                Instance("ISERDESE3",
                    p_IS_CLK_INVERTED=0,
                    p_IS_CLK_B_INVERTED=1,
                    p_DATA_WIDTH=8,

                    i_D=dq_i_delayed,
                    i_RST=ResetSignal(),
                    i_FIFO_RD_EN=0,
                    i_CLK=ClockSignal("sys4x"),
                    i_CLK_B=ClockSignal("sys4x"), # locally inverted
                    i_CLKDIV=ClockSignal(),
                    o_Q=dq_bitslip.i
                ),
                Instance("ODELAYE3",
                    p_CASCADE="NONE", p_UPDATE_MODE="ASYNC", p_REFCLK_FREQUENCY=200.0,
                    p_IS_CLK_INVERTED=0, p_IS_RST_INVERTED=0,
                    p_DELAY_FORMAT="TIME", p_DELAY_TYPE="VARIABLE", p_DELAY_VALUE=0,

                    i_CLK=ClockSignal(),
                    i_INC=1, i_EN_VTC=self._en_vtc.storage,
                    i_RST=ResetSignal() | (self._dly_sel.storage[i//8] & self._wdly_dq_rst.re),
                    i_CE=self._dly_sel.storage[i//8] & self._wdly_dq_inc.re,

                    i_ODATAIN=dq_o_nodelay, o_DATAOUT=dq_o_delayed
                ),
                Instance("IDELAYE3",
                    p_CASCADE="NONE", p_UPDATE_MODE="ASYNC",p_REFCLK_FREQUENCY=200.0,
                    p_IS_CLK_INVERTED=0, p_IS_RST_INVERTED=0,
                    p_DELAY_FORMAT="TIME", p_DELAY_SRC="IDATAIN",
                    p_DELAY_TYPE="VARIABLE", p_DELAY_VALUE=0,

                    i_CLK=ClockSignal(),
                    i_INC=1, i_EN_VTC=self._en_vtc.storage,
                    i_RST=ResetSignal() | (self._dly_sel.storage[i//8] & self._rdly_dq_rst.re),
                    i_CE=self._dly_sel.storage[i//8] & self._rdly_dq_inc.re,

                    i_IDATAIN=dq_i_nodelay, o_DATAOUT=dq_i_delayed
                ),
                Instance("IOBUF",
                    i_I=dq_o_delayed, o_O=dq_i_nodelay, i_T=dq_t,
                    io_IO=pads.dq[i]
                )
            ]
            self.comb += [
                self.dfi.phases[0].rddata[i].eq(dq_bitslip.o[0]),
                self.dfi.phases[1].rddata[i].eq(dq_bitslip.o[2]),
                self.dfi.phases[2].rddata[i].eq(dq_bitslip.o[4]),
                self.dfi.phases[3].rddata[i].eq(dq_bitslip.o[6]),

                self.dfi.phases[0].rddata[databits+i].eq(dq_bitslip.o[1]),
                self.dfi.phases[1].rddata[databits+i].eq(dq_bitslip.o[3]),
                self.dfi.phases[2].rddata[databits+i].eq(dq_bitslip.o[5]),
                self.dfi.phases[3].rddata[databits+i].eq(dq_bitslip.o[7]),
            ]

        # Flow control
        #
        # total read latency = 8:
        #  2 cycles through OSERDESE3
        #  2 cycles CAS
        #  2 cycles through ISERDESE3
        #  2 cycles through BitSlip
        rddata_en = self.dfi.phases[self.settings.rdphase].rddata_en
        for i in range(8-1):
            n_rddata_en = Signal()
            self.sync += n_rddata_en.eq(rddata_en)
            rddata_en = n_rddata_en
        self.sync += [phase.rddata_valid.eq(rddata_en | self._wlevel_en.storage)
            for phase in self.dfi.phases]

        oe = Signal()
        last_wrdata_en = Signal(4)
        wrphase = self.dfi.phases[self.settings.wrphase]
        self.sync += last_wrdata_en.eq(Cat(wrphase.wrdata_en, last_wrdata_en[:3]))
        self.comb += oe.eq(last_wrdata_en[1] | last_wrdata_en[2] | last_wrdata_en[3])
        self.sync += \
            If(self._wlevel_en.storage,
                oe_dqs.eq(1), oe_dq.eq(0)
            ).Else(
                oe_dqs.eq(oe), oe_dq.eq(oe)
            )
