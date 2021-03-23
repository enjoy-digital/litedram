from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *
from litedram.phy.lpddr4phy import LPDDR4PHY, delayed

class S7LPDDR4PHY(LPDDR4PHY):
    def __init__(self, pads, *, iodelay_clk_freq, **kwargs):
        self.iodelay_clk_freq = iodelay_clk_freq

        super().__init__(pads,
            # TODO: verify
            write_ser_latency = 1, # OSERDESE2 8:1 DDR (4 full-rate clocks)
            read_des_latency  = 2, # ISERDESE2 NETWORKING
            phytype           = self.__class__.__name__,
            **kwargs
        )

        # Parameters -------------------------------------------------------------------------------
        iodelay_tap_average = {
            200e6: 78e-12,
            300e6: 52e-12,
            400e6: 39e-12, # Only valid for -3 and -2/2E speed grades
        }
        half_sys8x_taps = math.floor(self.tck/(4*iodelay_tap_average[iodelay_clk_freq]))

        # Registers --------------------------------------------------------------------------------
        self._half_sys8x_taps = CSRStorage(5, reset=half_sys8x_taps)

        # odelay control
        self._cdly_rst = CSR()
        self._cdly_inc = CSR()
        self._rdly_dq_rst         = CSR()
        self._rdly_dq_inc         = CSR()
        self._wdly_dq_rst   = CSR()
        self._wdly_dq_inc   = CSR()
        self._wdly_dqs_rst  = CSR()
        self._wdly_dqs_inc  = CSR()

        cdly_rst = self._cdly_rst.re | self._rst.storage
        cdly_inc = self._cdly_inc.re

        # Serialization ----------------------------------------------------------------------------
        # TODO: need to implement half-serialization from sys (16 bits) to sys2x (8 bits) before oserdese

        # Clock
        clk_ser = Signal()
        clk_dly = Signal()
        self.oserdese2_ddr(din=self.ck_clk, dout=clk_ser, clk="sys8x")
        self.odelaye2(din=clk_ser, dout=clk_dly, rst=cdly_rst, inc=cdly_inc)
        self.obufds(din=clk_dly, dout=self.pads.clk_p, dout_b=self.pads.clk_n)

        # probably no need for oserdese
        for cmd in ["cke", "odt", "reset_n"]:
            cmd_ser = Signal()
            self.oserdese2_ddr(din=getattr(self, f"ck_{cmd}"), dout=cmd_ser, clk="sys8x")
            self.odelaye2(din=cmd_ser, dout=getattr(self.pads, cmd), rst=cdly_rst, inc=cdly_inc)

        # Commands
        cs_ser = Signal()
        self.oserdese2_ddr(din=self.ck_cs, dout=cs_ser, clk="sys8x")
        self.odelaye2(din=cs_ser, dout=self.pads.cs, rst=cdly_rst, inc=cdly_inc)
        for i in range(6):
            ca_ser = Signal()
            self.oserdese2_ddr(din=self.ck_ca[i], dout=ca_ser, clk="sys8x")
            self.odelaye2(din=ca_ser, dout=self.pads.ca[i], rst=cdly_rst, inc=cdly_inc)

        # DQS
        for i in range(self.databits//8):
            # DQS
            dqs_t = Signal()
            dqs_ser = Signal()
            dqs_dly = Signal()
            rst = (self._dly_sel.storage[i] & self._wdly_dqs_rst.re) | self._rst.storage
            inc = self._dly_sel.storage[i] & self._wdly_dqs_inc.re
            self.oserdese2_ddr(
                din=self.ck_dqs_o[i], dout=dqs_ser,
                tin=~self.dqs_oe, tout=dqs_t,
                clk="sys8x")
            self.odelaye2(din=dqs_ser, dout=dqs_dly, rst=rst, inc=inc)
            self.iobufds(
                din=dqs_dly, dout=Signal(),
                dinout=self.pads.dqs_p[i], dinout_b=self.pads.dqs_n[i],
                tin=dqs_t)

        # DMI
        for i in range(self.databits//8):
            dmi_t = Signal()
            dmi_ser = Signal()
            dmi_dly = Signal()
            rst = (self._dly_sel.storage[i] & self._wdly_dq_rst.re) | self._rst.storage
            inc = self._dly_sel.storage[i] & self._wdly_dq_inc.re
            self.oserdese2_ddr(
                din=self.ck_dmi_o[i], dout=dmi_ser,
                tin=~self.dmi_oe, tout=dmi_t,
                clk="sys8x")
            self.odelaye2(din=dmi_ser, dout=dmi_dly, rst=rst, inc=inc)
            self.iobuf(din=dmi_dly, dout=Signal(), dinout=self.pads.dmi[i], tin=dmi_t)

        # DQ
        for i in range(self.databits):
            dq_t = Signal()
            dq_ser = Signal()
            dq_dly = Signal()
            dq_i = Signal()
            dq_i_dly = Signal()

            rst_w = (self._dly_sel.storage[i//8] & self._wdly_dq_rst.re) | self._rst.storage
            inc_w = self._dly_sel.storage[i//8] & self._wdly_dq_inc.re
            rst_r = (self._dly_sel.storage[i//8] & self._rdly_dq_rst.re) | self._rst.storage
            inc_r = self._dly_sel.storage[i//8] & self._rdly_dq_inc.re

            self.oserdese2_ddr(
                din=self.ck_dq_o[i], dout=dq_ser,
                tin=~self.dq_oe, tout=dq_t,
                clk="sys8x")
            self.odelaye2(din=dq_ser, dout=dq_dly, rst=rst_w, inc=inc_w)
            self.iobuf(din=dq_dly, dout=dq_i, dinout=self.pads.dq[i], tin=dq_t)
            self.idelaye2(din=dq_i, dout=dq_i_dly, rst=rst_r, inc=inc_r)
            self.iserdese2_ddr(din=dq_i_dly, dout=self.ck_dq_i[i], clk="sys8x")

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
        # FIXME: must implement 1 step of serialization manually (16bit -> 8bit)
        # assert self.nphases == 4
        nphases = 4
        assert not ((tin is None) ^ (tout is None))

        params = dict(
            p_SERDES_MODE    = "MASTER",
            p_DATA_WIDTH     = 2*nphases,
            p_TRISTATE_WIDTH = 1,
            p_DATA_RATE_OQ   = "DDR",
            p_DATA_RATE_TQ   = "BUF",
            i_RST    = ResetSignal(),
            i_CLK    = ClockSignal(clk),
            i_CLKDIV = ClockSignal("sys"),
            o_OQ     = dout,
            i_OCE    = 1,
        )

        for i in range(2*nphases):
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
        # FIXME: must implement 1 step of serialization manually (16bit -> 8bit)
        # assert self.nphases == 4
        nphases = 4

        params = dict(
            p_SERDES_MODE    = "MASTER",
            p_INTERFACE_TYPE = "NETWORKING",  # TODO: try using MEMORY mode?
            p_DATA_WIDTH     = 2*nphases,
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

        for i in range(2*nphases):
            # invert order
            params["o_Q{}".format(i+1)] = dout[(2*nphases - 1) - i]

        self.specials += Instance("ISERDESE2", **params)

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
