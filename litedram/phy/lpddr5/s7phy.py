#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.genlib.cdc import PulseSynchronizer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

from litedram.phy.utils import delayed, Latency, ConstBitSlip
from litedram.phy.lpddr5.basephy import LPDDR5PHY

from litedram.phy.s7common import S7Common

class S7LPDDR5PHY(LPDDR5PHY, S7Common):
    def __init__(self, pads, *, iodelay_clk_freq, with_odelay, ddr_clk = None, csr_cdc = None, **kwargs):
        self.iodelay_clk_freq = iodelay_clk_freq

        super().__init__(pads,
            ser_latency = Latency(sys=1),  # OSERDESE2 8:1 DDR (4 full-rate clocks)
            des_latency = Latency(sys=2),  # ISERDESE2 NETWORKING
            phytype     = self.__class__.__name__,
            **kwargs
        )

        self.settings.delays = 32
        self.settings.write_leveling = True
        self.settings.write_latency_calibration = True
        self.settings.write_dq_dqs_training = True
        self.settings.read_leveling = True

        # Parameters -------------------------------------------------------------------------------
        # Calculate value of taps needed to shift a signal by 90 degrees.
        # Using iodelay_clk_freq of 300MHz/400MHz is only valid for -3 and -2/2E speed grades.
        assert iodelay_clk_freq in [200e6, 300e6, 400e6]
        iodelay_tap_average = 1 / (2*32 * iodelay_clk_freq)
        half_sys4x_taps = math.floor(self.twck / (4 * iodelay_tap_average))
        assert half_sys4x_taps < 32, "Exceeded ODELAYE2 max value: {} >= 32".format(half_sys4x_taps)

        # Registers --------------------------------------------------------------------------------
        # Note: this should be named sys4x, but using sys8x due to a name hard-coded in BIOS
        self._half_sys8x_taps = CSRStorage(5, reset=half_sys4x_taps)

        # delay control
        self._rdly_dq_rst  = CSR()
        self._rdly_dq_inc  = CSR()
        self._rdly_dqs_rst = CSR()
        self._rdly_dqs_inc = CSR()
        if with_odelay:
            self._cdly_rst     = CSR()
            self._cdly_inc     = CSR()
            self._wdly_dq_rst  = CSR()
            self._wdly_dq_inc  = CSR()
            self._wdly_dqs_rst = CSR()
            self._wdly_dqs_inc = CSR()

        def cdc(i):
            if csr_cdc is None:
                return i
            return csr_cdc(i)

        rdly_dq_rst  = cdc(self._rdly_dq_rst.re)
        rdly_dq_inc  = cdc(self._rdly_dq_inc.re)
        rdly_dqs_rst = cdc(self._rdly_dqs_rst.re)
        rdly_dqs_inc = cdc(self._rdly_dqs_inc.re)
        if with_odelay:
            cdly_rst     = cdc(self._cdly_rst.re) | self._rst.storage
            cdly_inc     = cdc(self._cdly_inc.re)
            wdly_dq_rst  = cdc(self._wdly_dq_rst.re)
            wdly_dq_inc  = cdc(self._wdly_dq_inc.re)
            wdly_dqs_rst = cdc(self._wdly_dqs_rst.re)
            wdly_dqs_inc = cdc(self._wdly_dqs_inc.re)

        # In theory we should only need to delay by 2 cycles, but sometimes it happened that
        # DQ/DMI were transmitted incomplete due to OE being asserted too late/released too
        # early. For this reason we add OE margin extending it 1 cycle before and 1 after.
        # For DQS we already have margin so there should be no need for this.
        def oe_delay_data(oe):
            oe_d = Signal()
            delay = TappedDelayLine(oe, 3)
            self.submodules += delay
            self.comb += oe_d.eq(reduce(or_, delay.taps))
            return oe_d

        def oe_delay_dqs(oe):
            delay = TappedDelayLine(oe, 2)
            self.submodules += delay
            return delay.output

        # Serialization ----------------------------------------------------------------------------

        # CK/CS/CA for a single command
        # sys |----____----____
        # CK  |----____----____  (same as sys)
        # CS  |____--------____  (180-deg shift)
        # CA  |______PPPPnnnn__  (270-deg shift)

        # Clock
        ck_dly = Signal()
        ck_ser = Signal()
        self.oserdese2_sdr(din=self.out.ck, dout=ck_ser if with_odelay else ck_dly, clk="sys4x", clkdiv="sys")
        if with_odelay:
            self.odelaye2(din=ck_ser, dout=ck_dly, rst=cdly_rst, inc=cdly_inc, clk="sys")
        self.obufds(din=ck_dly, dout=self.pads.ck_p, dout_b=self.pads.ck_n)

        # CS/RESET_n - 180-deg shifted
        # These signals are 1-bit wide, but shifting can be done laveraging the fact that our serializer
        # will replicate these anyway to get 8-bit input, so we widen them to 2-bit ones here and use
        # ConstBitSlip to produce 2-bit input to the serialzier.
        for cmd in ["cs", "reset_n"]:
            cmd_i = getattr(self.out, cmd)
            cmd_o = getattr(self.pads, cmd)
            cmd_ser = Signal()

            assert len(cmd_i) == 1
            cmd_2bit_i = Signal(2)
            cmd_2bit_o = Signal(2)
            self.comb += cmd_2bit_i.eq(Replicate(cmd_i, 2))
            # slp=1 / dw=2 => 180-deg shift
            self.submodules += ConstBitSlip(dw=2, slp=1, cycles=1, register=False, i=cmd_2bit_i, o=cmd_2bit_o)

            self.oserdese2_sdr(din=cmd_2bit_o, dout=cmd_ser if with_odelay else cmd_o, clk="sys4x", clkdiv="sys")
            if with_odelay:
                self.odelaye2(din=cmd_ser, dout=cmd_o, rst=cdly_rst, inc=cdly_inc, clk="sys")

        # Commands - 270-deg shift, achieved as for CS but with 4-bit ConstBitSlip
        for bit in range(len(self.out.ca)):
            ca_i = self.out.ca[bit]
            ca_ser = Signal()
            ca_dly = self.pads.ca[bit]

            assert len(ca_i) == 2
            ca_4bit_i = Signal(4)
            ca_4bit_o = Signal(4)
            self.comb += cmd_4bit_i.eq(Cat([Replicate(bit, 2) for bit in cmd_i]))
            # slp=3 / dw=4 => 270-deg shift
            self.submodules += ConstBitSlip(dw=4, slp=3, cycles=1, register=False, i=ca_4bit_i, o=ca_4bit_o)

            self.oserdese2_sdr(din=ca_4bit_o, dout=ca_ser if with_odelay else ca_dly, clk="sys4x", clkdiv="sys")
            if with_odelay:
                self.odelaye2(din=ca_ser, dout=ca_dly, rst=cdly_rst, inc=cdly_inc, clk="sys")

        # Data serializer selection
        data_ser = self.oserdese2_sdr if self.settings.wck_ck_ratio == 2 else self.oserdese2_ddr
        data_des = self.iserdese2_sdr if self.settings.wck_ck_ratio == 2 else self.iserdese2_ddr

        # WCK
        for byte in range(self.databits//8):
            wck_ser = Signal()
            wck_dly = Signal()
            data_ser(din=self.out.wck[byte], dout=wck_ser if with_odelay else wck_dly, clk="sys4x", clkdiv="sys")
            if with_odelay:
                self.odelaye2(din=wck_ser, dout=wck_dly, rst=cdly_rst, inc=cdly_inc, clk="sys")

            self.obufds(din=wck_dly, dout=self.pads.wck_p[byte], dout_b=self.pads.wck_n[byte])

        # DQS
        for byte in range(self.databits//8):
            # DQS
            dqs_t     = Signal()
            dqs_ser   = Signal()
            dqs_dly   = Signal()
            dqs_i     = Signal()
            dqs_i_dly = Signal()
            # need to delay DQS if clocks are not phase aligned
            dqs_din = self.out.rdqs_o[byte]
            if not with_odelay:
                dqs_din_d = Signal.like(dqs_din)
                self.sync += dqs_din_d.eq(dqs_din)
                dqs_din = dqs_din_d
            data_ser(
                din     = dqs_din,
                **(dict(dout_fb=dqs_ser) if with_odelay else dict(dout=dqs_dly)),
                tin     = ~oe_delay_dqs(self.out.rdqs_oe),
                tout    = dqs_t,
                clk     = "sys4x" if with_odelay else "sys4x_90",
                clkdiv  = "sys"
            )
            if with_odelay:
                self.odelaye2(
                    din  = dqs_ser,
                    dout = dqs_dly,
                    rst  = self.get_rst(byte, wdly_dqs_rst),
                    inc  = self.get_inc(byte, wdly_dqs_inc),
                    init = half_sys4x_taps,  # shifts by 90 degrees
                    clk  = "sys"
                )
            self.iobufds(
                din      = dqs_dly,
                dout     = dqs_i,
                tin      = dqs_t,
                dinout   = self.pads.rdqs_p[byte],
                dinout_b = self.pads.rdqs_n[byte],
            )
            self.idelaye2(
                din  = dqs_i,
                dout = dqs_i_dly,
                rst  = self.get_rst(byte, rdly_dqs_rst),
                inc  = self.get_inc(byte, rdly_dqs_inc),
                clk  = "sys"
            )
            data_des(
                din    = dqs_i_dly,
                dout   = self.out.rdqs_i[byte],
                clk    = "sys4x",
                clkdiv = "sys",
            )

        # DMI
        for byte in range(self.databits//8):
            dmi_t   = Signal()
            dmi_ser = Signal()
            dmi_dly = Signal()
            data_ser(
                din     = self.out.dmi_o[byte],
                **(dict(dout_fb=dmi_ser) if with_odelay else dict(dout=dmi_dly)),
                tin     = ~oe_delay_data(self.out.dmi_oe),
                tout    = dmi_t,
                clk     = "sys4x",
                clkdiv  = "sys"
            )
            if with_odelay:
                self.odelaye2(
                    din  = dmi_ser,
                    dout = dmi_dly,
                    rst  = self.get_rst(byte, wdly_dq_rst),
                    inc  = self.get_inc(byte, wdly_dq_inc),
                    clk  = "sys"
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
            data_ser(
                din     = self.out.dq_o[bit],
                **(dict(dout_fb=dq_ser) if with_odelay else dict(dout=dq_dly)),
                tin     = ~oe_delay_data(self.out.dmi_oe),
                tout    = dq_t,
                clk     = "sys4x",
                clkdiv  = "sys"
            )
            if with_odelay:
                self.odelaye2(
                    din  = dq_ser,
                    dout = dq_dly,
                    rst  = self.get_rst(bit//8, wdly_dq_rst),
                    inc  = self.get_inc(bit//8, wdly_dq_inc),
                    clk  = "sys"
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
                inc  = self.get_inc(bit//8, rdly_dq_inc),
                clk  = "sys"
            )
            data_des(
                din    = dq_i_dly,
                dout   = self.out.dq_i[bit],
                clk    = "sys4x",
                clkdiv = "sys"
            )

# PHY variants -------------------------------------------------------------------------------------

class V7LPDDR5PHY(S7LPDDR5PHY):
    """Xilinx Virtex7 LPDDR5 PHY (with odelay)"""
    def __init__(self, pads, **kwargs):
        S7LPDDR5PHY.__init__(self, pads, with_odelay=True, **kwargs)

class K7LPDDR5PHY(S7LPDDR5PHY):
    """Xilinx Kintex7 LPDDR5 PHY (with odelay)"""
    def __init__(self, pads, **kwargs):
        S7LPDDR5PHY.__init__(self, pads, with_odelay=True, **kwargs)

class A7LPDDR5PHY(S7LPDDR5PHY):
    """Xilinx Artix7 LPDDR5 PHY (without odelay)

    This variant requires generating sys4x_90 clock in CRG with a 90° phase shift vs sys4x.
    """
    def __init__(self, pads, **kwargs):
        S7LPDDR5PHY.__init__(self, pads, with_odelay=False, **kwargs)
