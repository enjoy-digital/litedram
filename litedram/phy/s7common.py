#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

class S7Common(Module):
    def idelaye2(self, *, din, dout, init=0, rst=None, inc=None, clk="sys2x"):
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
                i_C        = ClockSignal(clk),  # must be same as in ODELAYE2
                i_LD       = rst,
                i_CE       = inc,
                i_LDPIPEEN = 0,
                i_INC      = 1,
            ))

        self.specials += Instance("IDELAYE2", **params)

    def odelaye2(self, *, din, dout, init=0, rst=None, inc=None, clk="sys2x"):  # Not available for Artix7
        assert not ((rst is None) ^ (inc is None))
        fixed = rst is None

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
                i_C        = ClockSignal(clk),  # must be same as CLKDIV in OSERDESE2
                i_LD       = rst,
                i_CE       = inc,
                i_LDPIPEEN = 0,
                i_INC      = 1,
            ))

        self.specials += Instance("ODELAYE2", **params)

    def oserdese2_ddr(self, *, din, clk, dout=None, dout_fb=None, tin=None, tout=None, clkdiv="sys2x"):
        data_width = len(din)
        assert data_width == 8, (data_width, din)
        assert not ((tin is None) ^ (tout is None)), "When using tristate specify both `tin` and `tout`"
        assert not ((dout is None) and (dout_fb is None)), "Output to OQ (-> IOB) and/or to OFB (-> ISERDESE2/ODELAYE2)"

        dout = Signal() if dout is None else dout
        dout_fb = Signal() if dout_fb is None else dout_fb

        params = dict(
            p_SERDES_MODE    = "MASTER",
            p_DATA_WIDTH     = data_width,
            p_TRISTATE_WIDTH = 1,
            p_DATA_RATE_OQ   = "DDR",
            p_DATA_RATE_TQ   = "BUF",
            i_RST    = ResetSignal() | self._rst.storage,
            i_CLK    = ClockSignal(clk),
            i_CLKDIV = ClockSignal(clkdiv),
            o_OQ     = dout,
            o_OFB    = dout_fb,
            i_OCE    = 1,
        )

        for i in range(data_width):
            params[f"i_D{i+1}"] = din[i]

        if tin is not None:
            # with DATA_RATE_TQ=BUF tristate is asynchronous, so it should be delayed by OSERDESE2 latency
            params.update(dict(i_TCE=1, i_T1=tin, o_TQ=tout))

        self.specials += Instance("OSERDESE2", **params)

    def oserdese2_sdr(self, **kwargs):
        # Use 8:1 OSERDESE2 DDR instead of 4:1 OSERDESE2 SDR to have the same latency
        din = kwargs["din"]
        data_width = len(din)
        assert data_width in [1, 2, 4]
        ratio = 8 // data_width
        din_ddr = Signal(8)
        kwargs["din"] = din_ddr
        self.comb += din_ddr.eq(Cat(*[Replicate(bit, ratio) for bit in din]))
        self.oserdese2_ddr(**kwargs)

    def iserdese2_ddr(self, *, din, dout, clk, clkdiv="sys2x"):
        data_width = len(dout)
        assert data_width == 8, (data_width, dout)

        params = dict(
            p_SERDES_MODE    = "MASTER",
            p_INTERFACE_TYPE = "NETWORKING",
            p_DATA_WIDTH     = data_width,
            p_DATA_RATE      = "DDR",
            p_NUM_CE         = 1,
            p_IOBDELAY       = "IFD",
            i_RST     = ResetSignal() | self._rst.storage,
            i_CLK     = ClockSignal(clk),
            i_CLKB    = ~ClockSignal(clk),
            i_CLKDIV  = ClockSignal(clkdiv),
            i_BITSLIP = 0,
            i_CE1     = 1,
            i_DDLY    = din,
        )

        for i in range(data_width):
            # invert order
            params[f"o_Q{i+1}"] = dout[(data_width - 1) - i]

        self.specials += Instance("ISERDESE2", **params)

    def iserdese2_sdr(self, **kwargs):
        dout = kwargs["dout"]
        data_width = len(dout)
        assert data_width in [1, 2, 4]
        ratio = 8 // data_width
        dout_ddr = Signal(8)
        kwargs["dout"] = dout_ddr
        self.comb += dout.eq(Cat(*[dout_ddr[bit] for bit in range(0, 8, ratio)]))
        self.iserdese2_ddr(**kwargs)

    def obufds(self, *, din, dout, dout_b):
        self.specials += Instance("OBUFDS",
            i_I  = din,
            o_O  = dout,
            o_OB = dout_b,
        )

    def iobufds(self, *, din, dout, dinout, dinout_b, tin):
        self.specials += Instance("IOBUFDS",
            i_T    = tin,
            i_I    = din,
            o_O    = dout,
            io_IO  = dinout,
            io_IOB = dinout_b,
        )

    def iobuf(self, *, din, dout, dinout, tin):
        self.specials += Instance("IOBUF",
            i_T   = tin,
            i_I   = din,
            o_O   = dout,
            io_IO = dinout,
        )
