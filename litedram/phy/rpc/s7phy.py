#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020-2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *
from litedram.phy.rpc.basephy import BasePHY, bitpattern

# Xilinx Artix7 RPC PHY ----------------------------------------------------------------------------

class A7RPCPHY(BasePHY):
    def __init__(self, iodelay_clk_freq, **kwargs):
        self._rdly_dq_rst = CSR()
        self._rdly_dq_inc = CSR()

        self._db_enabled = CSRStorage(reset=1)
        self._dqs_enabled = CSRStorage(reset=1)

        kwargs.update(dict(
            write_ser_latency = 1,  # OSERDESE2 8:1 DDR (4 full-rate clocks)
            read_des_latency  = 2,  # ISERDESE2 NETWORKING
            phytype           = self.__class__.__name__,
        ))

        super().__init__(**kwargs)

        self.settings.delays = 32
        self.settings.read_leveling = True

        self.iodelay_clk_freq = iodelay_clk_freq
        iodelay_tap_average = {
            200e6: 78e-12,
            300e6: 52e-12,
            400e6: 39e-12,  # Only valid for -3 and -2/2E speed grades
        }
        self.half_sys8x_taps = math.floor(self.tck/(4*iodelay_tap_average[iodelay_clk_freq]))

    def do_clock_serialization(self, clk_1ck_out, clk_p, clk_n):
        clk = Signal()
        self.oserdese2_ddr(din=clk_1ck_out, dout=clk, clk="sys4x_180")
        self.specials += Instance("OBUFDS",
            i_I  = clk,
            o_O  = clk_p,
            o_OB = clk_n,
        )

    def do_stb_serialization(self, stb_1ck_out, stb):
        stb_out        = Signal()
        stb_in         = Signal()
        stb_in_delayed = Signal()
        stb_t          = Signal()

        self.stb_1ck_in = stb_1ck_in = Signal.like(stb_1ck_out)

        self.oserdese2_ddr(din=stb_1ck_out, dout=stb_out,
                           tin=Constant(0), tout=stb_t,
                           clk="sys4x_90")

        # Read path
        self.idelaye2(
            din=stb_in, dout=stb_in_delayed,
            rst=self.get_rst(0, self._rdly_dq_rst.re),
            inc=self.get_inc(0, self._rdly_dq_inc.re),
        )
        self.iserdese2_ddr(din=stb_in_delayed, dout=stb_1ck_in, clk="sys4x_180")

        self.specials += Instance("IOBUF",
            i_I   = stb_out,
            o_O   = stb_in,
            i_T   = stb_t,
            io_IO = stb,
        )

    def do_db_serialization(self, db_1ck_out, db_1ck_in, db_oe, db):
        for i in range(self.databits):
            db_out        = Signal()
            db_t          = Signal()
            db_in         = Signal()
            db_in_delayed = Signal()

            # Write path
            self.oserdese2_ddr(
                din=db_1ck_out[i], dout=db_out,
                tin=~(db_oe & self._db_enabled.storage), tout=db_t,
                clk="sys4x_90",
            )

            # Read path
            self.idelaye2(
                din=db_in, dout=db_in_delayed,
                rst=self.get_rst(i//8, self._rdly_dq_rst.re),
                inc=self.get_inc(i//8, self._rdly_dq_inc.re),
            )
            self.iserdese2_ddr(din=db_in_delayed, dout=db_1ck_in[i], clk="sys4x_180")

            self.specials += Instance("IOBUF",
                i_I   = db_out,
                o_O   = db_in,
                i_T   = db_t,
                io_IO = db[i],
            )

    def do_dqs_serialization(self, dqs_1ck_out, dqs_1ck_in, dqs_oe, dqs_p, dqs_n):
        for i in range(len(dqs_p)):
            dqs_out  = Signal()
            dqs_in   = Signal()
            dqs_t    = Signal()
            dqs_in_delayed  = Signal()

            self.oserdese2_ddr(
                clk="sys4x_180",
                din=dqs_1ck_out, dout=dqs_out,
                tin=~(dqs_oe & self._dqs_enabled.storage), tout=dqs_t,
            )

            # TODO: proper deserialization
            if i == 0:
                self.idelaye2(
                    din=dqs_in, dout=dqs_in_delayed,
                    rst=self.get_rst(i//8, self._rdly_dq_rst.re),
                    inc=self.get_inc(i//8, self._rdly_dq_inc.re),
                )
                self.iserdese2_ddr(
                    clk="sys4x_90",
                    din=dqs_in_delayed, dout=dqs_1ck_in)

            self.specials += Instance("IOBUFDS",
                i_T    = dqs_t,
                i_I    = dqs_out,
                o_O    = dqs_in,
                io_IO  = dqs_p[i],
                io_IOB = dqs_n[i],
            )

    def do_cs_serialization(self, cs_n_1ck_out, cs_n):
        self.oserdese2_ddr(din=cs_n_1ck_out, dout=cs_n, clk="sys4x_90")

    def idelaye2(self, *, din, dout, init=0, rst=None, inc=None):
        assert not ((rst is None) ^ (inc is None))
        fixed = rst is None

        params = dict(
            p_SIGNAL_PATTERN        = "DATA",
            p_DELAY_SRC             = "IDATAIN",
            p_CINVCTRL_SEL          = "FALSE",
            p_HIGH_PERFORMANCE_MODE = "TRUE",
            p_REFCLK_FREQUENCY      = self.iodelay_clk_freq/1e6,
            p_PIPE_SEL              = "FALSE",
            p_IDELAY_VALUE          = init,
            p_IDELAY_TYPE           = "FIXED",
            i_IDATAIN  = din,
            o_DATAOUT  = dout,
        )

        if not fixed:
            params.update(dict(
                p_IDELAY_TYPE  = "VARIABLE",
                i_C        = ClockSignal(),
                i_LD       = rst,
                i_CE       = inc,
                i_LDPIPEEN = 0,
                i_INC      = 1,
            ))

        self.specials += Instance("IDELAYE2", **params)

    def odelaye2(self, *, din, dout, init=0, rst=None, inc=None):  # Not available for Artix7
        assert not ((rst is None) ^ (inc is None))
        fixed = rst is not None

        params = dict(
            p_SIGNAL_PATTERN        = "DATA",
            p_DELAY_SRC             = "ODATAIN",
            p_CINVCTRL_SEL          = "FALSE",
            p_HIGH_PERFORMANCE_MODE = "TRUE",
            p_REFCLK_FREQUENCY      = self.iodelay_clk_freq/1e6,
            p_PIPE_SEL              = "FALSE",
            p_ODELAY_VALUE          = init,
            p_ODELAY_TYPE           = "FIXED",
            i_ODATAIN  = din,
            o_DATAOUT  = dout,
        )

        if not fixed:
            params.update(dict(
                p_ODELAY_TYPE  = "VARIABLE",
                i_C        = ClockSignal(),
                i_LD       = rst,
                i_CE       = inc,
                i_LDPIPEEN = 0,
                i_INC      = 1,
            ))

        self.specials += Instance("ODELAYE2", **params)

    def oserdese2_ddr(self, *, din, dout, clk, tin=None, tout=None):
        assert self.nphases == 4
        assert not ((tin is None) ^ (tout is None))

        params = dict(
            p_SERDES_MODE    = "MASTER",
            p_DATA_WIDTH     = 2*self.nphases,
            p_TRISTATE_WIDTH = 1,
            p_DATA_RATE_OQ   = "DDR",
            p_DATA_RATE_TQ   = "BUF",
            i_RST    = ResetSignal(),
            i_CLK    = ClockSignal(clk),
            i_CLKDIV = ClockSignal("sys"),
            o_OQ     = dout,
            i_OCE    = 1,
        )

        for i in range(2*self.nphases):
            params["i_D{}".format(i+1)] = din[i]

        if tin is not None:
            # with DATA_RATE_TQ=BUF tristate is asynchronous, so we need to delay it
            tin_d = Signal()
            self.sync += tin_d.eq(tin)

            # register it on the CLKDIV (as it would be too short for 180 deg shifted clk)
            tin_cdc = Signal()
            sd_clkdiv = getattr(self.sync, clk)
            sd_clkdiv += tin_cdc.eq(tin_d)

            params.update(dict(i_TCE=1, i_T1=tin_cdc, o_TQ=tout))

        self.specials += Instance("OSERDESE2", **params)

    def iserdese2_ddr(self, *, din, dout, clk):
        assert self.nphases == 4

        params = dict(
            p_SERDES_MODE    = "MASTER",
            p_INTERFACE_TYPE = "NETWORKING",  # TODO: try using MEMORY mode?
            p_DATA_WIDTH     = 2*self.nphases,
            p_DATA_RATE      = "DDR",
            p_NUM_CE         = 1,
            p_IOBDELAY       = "IFD",
            i_RST     = ResetSignal(),
            i_CLK     = ClockSignal(clk),
            i_CLKB    = ~ClockSignal(clk),
            i_CLKDIV  = ClockSignal("sys"),
            i_BITSLIP = 0,
            i_CE1     = 1,
            i_DDLY    = din,
        )

        for i in range(2*self.nphases):
            # invert order
            params["o_Q{}".format(i+1)] = dout[(2*self.nphases - 1) - i]

        self.specials += Instance("ISERDESE2", **params)
