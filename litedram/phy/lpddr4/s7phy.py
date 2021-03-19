from migen import *
from migen.genlib.cdc import PulseSynchronizer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

from litedram.phy.lpddr4.utils import delayed as delayed
from litedram.phy.lpddr4.basephy import DoubleRateLPDDR4PHY, Latency


class S7LPDDR4PHY(DoubleRateLPDDR4PHY):
    def __init__(self, pads, *, iodelay_clk_freq, **kwargs):
        # TODO: add `with_odelay` argument to avoid ODELAYE2, currently it won't work on Artix7
        self.iodelay_clk_freq = iodelay_clk_freq

        # DoubleRateLPDDR4PHY outputs half-width signals (comparing to LPDDR4PHY) in sys2x domain.
        # This allows us to use 8:1 DDR OSERDESE2/ISERDESE2 to (de-)serialize the data.
        _sys2x = 4
        super().__init__(pads,
            ser_latency = Latency(sys=0, sys8x=1*_sys2x),  # OSERDESE2 8:1 DDR (4 full-rate clocks)
            des_latency = Latency(sys=0, sys8x=2*_sys2x),  # ISERDESE2 NETWORKING
            phytype     = self.__class__.__name__,
            serdes_reset_cnt=-1,
            **kwargs
        )

        self.submodules.sys2x_delay = ClockDomainsRenamer("sys2x")(Module())

        # Parameters -------------------------------------------------------------------------------
        # Calculate value of taps needed to shift a signal by 90 degrees.
        # Using iodelay_clk_freq of 300MHz/400MHz is only valid for -3 and -2/2E speed grades.
        # FIXME: this should be named sys16x, but using sys8x due to a name hard-coded in BIOS
        assert iodelay_clk_freq in [200e6, 300e6, 400e6]
        iodelay_tap_average = 1 / (2*32 * iodelay_clk_freq)
        half_sys8x_taps = math.floor(self.tck / (4 * iodelay_tap_average))
        assert half_sys8x_taps < 32, "Exceeded ODELAYE2 max value: {} >= 32".format(half_sys8x_taps)

        # Registers --------------------------------------------------------------------------------
        self._half_sys8x_taps = CSRStorage(5, reset=half_sys8x_taps)

        # odelay control
        self._cdly_rst     = CSR()
        self._cdly_inc     = CSR()
        self._rdly_dq_rst  = CSR()
        self._rdly_dq_inc  = CSR()
        self._rdly_dqs_rst = CSR()
        self._rdly_dqs_inc = CSR()
        self._wdly_dq_rst  = CSR()
        self._wdly_dq_inc  = CSR()
        self._wdly_dqs_rst = CSR()
        self._wdly_dqs_inc = CSR()

        def cdc(i):
            o = Signal()
            psync = PulseSynchronizer("sys", "sys2x")
            self.submodules += psync
            self.comb += [
                psync.i.eq(i),
                o.eq(psync.o),
            ]
            return o

        cdly_rst     = cdc(self._cdly_rst.re) | self._rst.storage
        cdly_inc     = cdc(self._cdly_inc.re)
        rdly_dq_rst  = cdc(self._rdly_dq_rst.re)
        rdly_dq_inc  = cdc(self._rdly_dq_inc.re)
        rdly_dqs_rst = cdc(self._rdly_dqs_rst.re)
        rdly_dqs_inc = cdc(self._rdly_dqs_inc.re)
        wdly_dq_rst  = cdc(self._wdly_dq_rst.re)
        wdly_dq_inc  = cdc(self._wdly_dq_inc.re)
        wdly_dqs_rst = cdc(self._wdly_dqs_rst.re)
        wdly_dqs_inc = cdc(self._wdly_dqs_inc.re)

        # with DATA_RATE_TQ=BUF tristate is asynchronous, so we need to delay it
        class OEDelay(Module, AutoCSR):
            def __init__(self, oe, reset):
                self.o = Signal()
                self.mask = CSRStorage(4, reset=reset)
                delay = Array([Signal() for _ in range(4)])

                self.comb += delay[0].eq(oe)
                self.sync += delay[1].eq(delay[0])
                self.sync += delay[2].eq(delay[1])
                self.sync += delay[3].eq(delay[2])
                self.comb += self.o.eq(reduce(or_, [dly & self.mask.storage[i] for i, dly in enumerate(delay)]))

        self.submodules.dqs_oe_delay = ClockDomainsRenamer("sys2x")(OEDelay(self.out.dqs_oe, reset=0b0110))
        self.submodules.dq_oe_delay  = ClockDomainsRenamer("sys2x")(OEDelay(self.out.dq_oe, reset=0b1110))
        self.submodules.dmi_oe_delay = ClockDomainsRenamer("sys2x")(OEDelay(self.out.dmi_oe, reset=0b1110))

        # Serialization ----------------------------------------------------------------------------

        # Clock
        clk_ser = Signal()
        clk_dly = Signal()
        # Invert clk to have it phase shifted in relation to CS/CA, because we serialize it with DDR,
        # rising edge will then be in the middle of a data bit.
        self.oserdese2_ddr(din=~self.out.clk, dout=clk_ser, clk="sys8x")
        self.odelaye2(din=clk_ser, dout=clk_dly, rst=cdly_rst, inc=cdly_inc)
        self.obufds(din=clk_dly, dout=self.pads.clk_p, dout_b=self.pads.clk_n)

        # FIXME: probably no need to serialize those
        for cmd in ["cke", "odt", "reset_n"]:
            cmd_ser = Signal()
            self.oserdese2_sdr(din=getattr(self.out, cmd), dout=cmd_ser, clk="sys8x")
            self.odelaye2(din=cmd_ser, dout=getattr(self.pads, cmd), rst=cdly_rst, inc=cdly_inc)

        # Commands
        cs_ser = Signal()
        self.oserdese2_sdr(din=self.out.cs, dout=cs_ser, clk="sys8x")
        self.odelaye2(din=cs_ser, dout=self.pads.cs, rst=cdly_rst, inc=cdly_inc)
        for bit in range(6):
            ca_ser = Signal()
            self.oserdese2_sdr(din=self.out.ca[bit], dout=ca_ser, clk="sys8x")
            self.odelaye2(din=ca_ser, dout=self.pads.ca[bit], rst=cdly_rst, inc=cdly_inc)

        # DQS
        for byte in range(self.databits//8):
            # DQS
            dqs_t     = Signal()
            dqs_ser   = Signal()
            dqs_dly   = Signal()
            dqs_i     = Signal()
            dqs_i_dly = Signal()
            self.oserdese2_ddr(
                din     = self.out.dqs_o[byte],
                dout_fb = dqs_ser,
                tin     = ~self.dqs_oe_delay.o,
                tout    = dqs_t,
                clk     = "sys8x",  # TODO: if odelay is not avaiable need to use sys8x_90
            )
            self.odelaye2(
                din  = dqs_ser,
                dout = dqs_dly,
                rst  = self.get_rst(byte, wdly_dqs_rst),
                inc  = self.get_inc(byte, wdly_dqs_inc),
                init = half_sys8x_taps,  # shifts by 90 degrees
            )
            self.iobufds(
                din      = dqs_dly,
                dout     = dqs_i,
                tin      = dqs_t,
                dinout   = self.pads.dqs_p[byte],
                dinout_b = self.pads.dqs_n[byte],
            )
            self.idelaye2(
                din  = dqs_i,
                dout = dqs_i_dly,
                rst  = self.get_rst(byte, rdly_dqs_rst),
                inc  = self.get_inc(byte, rdly_dqs_inc),
            )
            self.iserdese2_ddr(
                din  = dqs_i_dly,
                dout = self.out.dqs_i[byte],
                clk  = "sys8x",
            )

        # DMI
        for byte in range(self.databits//8):
            dmi_t   = Signal()
            dmi_ser = Signal()
            dmi_dly = Signal()
            self.oserdese2_ddr(
                din     = self.out.dmi_o[byte],
                dout_fb = dmi_ser,
                tin     = ~self.dmi_oe_delay.o,
                tout    = dmi_t,
                clk     = "sys8x",
            )
            self.odelaye2(
                din  = dmi_ser,
                dout = dmi_dly,
                rst  = self.get_rst(byte, wdly_dq_rst),
                inc  = self.get_inc(byte, wdly_dq_inc),
            )
            self.iobuf(
                din    = dmi_dly,
                dout   = Signal(),
                tin    = dmi_t,
                dinout = self.pads.dmi[byte],
            )

        # DQ
        for bit in range(self.databits):
            dq_t     = Signal()
            dq_ser   = Signal()
            dq_dly   = Signal()
            dq_i     = Signal()
            dq_i_dly = Signal()
            self.oserdese2_ddr(
                din     = self.out.dq_o[bit],
                dout_fb = dq_ser,  # TODO: compare: S7DDRPHY uses OQ not OFB
                tin     = ~self.dq_oe_delay.o,
                tout    = dq_t,
                clk     = "sys8x",
            )
            self.odelaye2(
                din  = dq_ser,
                dout = dq_dly,
                rst  = self.get_rst(bit//8, wdly_dq_rst),
                inc  = self.get_inc(bit//8, wdly_dq_inc),
            )
            self.iobuf(
                din    = dq_dly,
                dout   = dq_i,
                dinout = self.pads.dq[bit],
                tin    = dq_t
            )
            self.idelaye2(
                din  = dq_i,
                dout = dq_i_dly,
                rst  = self.get_rst(bit//8, rdly_dq_rst),
                inc  = self.get_inc(bit//8, rdly_dq_inc)
            )
            self.iserdese2_ddr(
                din  = dq_i_dly,
                dout = self.out.dq_i[bit],
                clk  = "sys8x"
            )

    def delayed_sys2x(self, sig, **kwargs):
        return delayed(self.sys2x_delay, sig, **kwargs)

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
                i_C        = ClockSignal("sys2x"),  # must be same as in ODELAYE2
                i_LD       = rst,
                i_CE       = inc,
                i_LDPIPEEN = 0,
                i_INC      = 1,
            ))

        self.specials += Instance("IDELAYE2", **params)

    def odelaye2(self, *, din, dout, init=0, rst=None, inc=None):  # Not available for Artix7
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
                i_C        = ClockSignal("sys2x"),  # must be same as CLKDIV in OSERDESE2
                i_LD       = rst,
                i_CE       = inc,
                i_LDPIPEEN = 0,
                i_INC      = 1,
            ))

        self.specials += Instance("ODELAYE2", **params)

    def oserdese2_ddr(self, *, din, clk, dout=None, dout_fb=None, tin=None, tout=None):
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
            i_CLKDIV = ClockSignal("sys2x"),
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
        din_ddr = Signal(2*len(din))
        kwargs["din"] = din_ddr
        self.comb += din_ddr.eq(Cat(*[Replicate(bit, 2) for bit in din]))
        self.oserdese2_ddr(**kwargs)

    def iserdese2_ddr(self, *, din, dout, clk):
        data_width = len(dout)
        assert data_width == 8, (data_width, dout)

        params = dict(
            p_SERDES_MODE    = "MASTER",
            p_INTERFACE_TYPE = "NETWORKING",  # TODO: try using MEMORY mode?
            p_DATA_WIDTH     = data_width,
            p_DATA_RATE      = "DDR",
            p_NUM_CE         = 1,
            p_IOBDELAY       = "IFD",
            i_RST     = ResetSignal() | self._rst.storage,
            i_CLK     = ClockSignal(clk),
            i_CLKB    = ~ClockSignal(clk),
            i_CLKDIV  = ClockSignal("sys2x"),
            i_BITSLIP = 0,
            i_CE1     = 1,
            i_DDLY    = din,
        )

        for i in range(data_width):
            # invert order
            params[f"o_Q{i+1}"] = dout[(data_width - 1) - i]

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
