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

from litedram.phy.utils import delayed, Latency
from litedram.phy.lpddr4.basephy import DoubleRateLPDDR4PHY

from litedram.phy.s7common import S7Common

class S7LPDDR4PHY(DoubleRateLPDDR4PHY, S7Common):
    def __init__(self, pads, *, iodelay_clk_freq, with_odelay, **kwargs):
        self.iodelay_clk_freq = iodelay_clk_freq

        # DoubleRateLPDDR4PHY outputs half-width signals (comparing to LPDDR4PHY) in sys2x domain.
        # This allows us to use 8:1 DDR OSERDESE2/ISERDESE2 to (de-)serialize the data.
        super().__init__(pads,
            ser_latency = Latency(sys2x=1),  # OSERDESE2 8:1 DDR (4 full-rate clocks)
            des_latency = Latency(sys2x=2),  # ISERDESE2 NETWORKING
            phytype     = self.__class__.__name__,
            serdes_reset_cnt=-1,
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
        # Note: this should be named sys16x, but using sys8x due to a name hard-coded in BIOS
        assert iodelay_clk_freq in [200e6, 300e6, 400e6]
        iodelay_tap_average = 1 / (2*32 * iodelay_clk_freq)
        half_sys8x_taps = math.floor(self.tck / (4 * iodelay_tap_average))
        assert half_sys8x_taps < 32, "Exceeded ODELAYE2 max value: {} >= 32".format(half_sys8x_taps)

        # Registers --------------------------------------------------------------------------------
        self._half_sys8x_taps = CSRStorage(5, reset=half_sys8x_taps)

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
            o = Signal()
            psync = PulseSynchronizer("sys", "sys2x")
            self.submodules += psync
            self.comb += [
                psync.i.eq(i),
                o.eq(psync.o),
            ]
            return o

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
            self.submodules += ClockDomainsRenamer("sys2x")(delay)
            self.comb += oe_d.eq(reduce(or_, delay.taps))
            return oe_d

        def oe_delay_dqs(oe):
            delay = TappedDelayLine(oe, 2)
            self.submodules += ClockDomainsRenamer("sys2x")(delay)
            return delay.output

        # Serialization ----------------------------------------------------------------------------

        # Clock
        clk_dly = Signal()
        clk_ser = Signal()
        # Invert clk to have it phase shifted in relation to CS/CA, because we serialize it with DDR,
        # rising edge will then be in the middle of a data bit.
        self.oserdese2_ddr(din=~self.out.clk, dout=clk_ser if with_odelay else clk_dly, clk="sys8x")
        if with_odelay:
            self.odelaye2(din=clk_ser, dout=clk_dly, rst=cdly_rst, inc=cdly_inc)
        self.obufds(din=clk_dly, dout=self.pads.clk_p, dout_b=self.pads.clk_n)

        for cmd in ["cke", "odt", "reset_n"]:
            cmd_i = getattr(self.out, cmd)
            cmd_o = getattr(self.pads, cmd)
            cmd_ser = Signal()
            self.oserdese2_sdr(din=cmd_i, dout=cmd_ser if with_odelay else cmd_o, clk="sys8x")
            if with_odelay:
                self.odelaye2(din=cmd_ser, dout=cmd_o, rst=cdly_rst, inc=cdly_inc)

        # Commands
        cs_ser = Signal()
        if with_odelay:
            self.oserdese2_sdr(din=self.out.cs, dout=cs_ser, clk="sys8x")
            self.odelaye2(din=cs_ser, dout=self.pads.cs, rst=cdly_rst, inc=cdly_inc)
        else:
            self.oserdese2_sdr(din=self.out.cs, dout=self.pads.cs, clk="sys8x")
        for bit in range(6):
            ca_ser = Signal()
            if with_odelay:
                self.oserdese2_sdr(din=self.out.ca[bit], dout=ca_ser, clk="sys8x")
                self.odelaye2(din=ca_ser, dout=self.pads.ca[bit], rst=cdly_rst, inc=cdly_inc)
            else:
                self.oserdese2_sdr(din=self.out.ca[bit], dout=self.pads.ca[bit], clk="sys8x")

        # DQS
        for byte in range(self.databits//8):
            # DQS
            dqs_t     = Signal()
            dqs_ser   = Signal()
            dqs_dly   = Signal()
            dqs_i     = Signal()
            dqs_i_dly = Signal()
            # need to delay DQS if clocks are not phase aligned
            dqs_din = self.out.dqs_o[byte]
            if not with_odelay:
                dqs_din_d = Signal.like(dqs_din)
                self.sync.sys2x += dqs_din_d.eq(dqs_din)
                dqs_din = dqs_din_d
            self.oserdese2_ddr(
                din     = dqs_din,
                **(dict(dout_fb=dqs_ser) if with_odelay else dict(dout=dqs_dly)),
                tin     = ~oe_delay_dqs(self.out.dqs_oe),
                tout    = dqs_t,
                clk     = "sys8x" if with_odelay else "sys8x_90",
            )
            if with_odelay:
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
                **(dict(dout_fb=dmi_ser) if with_odelay else dict(dout=dmi_dly)),
                tin     = ~oe_delay_data(self.out.dmi_oe),
                tout    = dmi_t,
                clk     = "sys8x",
            )
            if with_odelay:
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
                **(dict(dout_fb=dq_ser) if with_odelay else dict(dout=dq_dly)),
                tin     = ~oe_delay_data(self.out.dmi_oe),
                tout    = dq_t,
                clk     = "sys8x",
            )
            if with_odelay:
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

# PHY variants -------------------------------------------------------------------------------------

class V7LPDDR4PHY(S7LPDDR4PHY):
    """Xilinx Virtex7 LPDDR4 PHY (with odelay)"""
    def __init__(self, pads, **kwargs):
        S7LPDDR4PHY.__init__(self, pads, with_odelay=True, **kwargs)

class K7LPDDR4PHY(S7LPDDR4PHY):
    """Xilinx Kintex7 LPDDR4 PHY (with odelay)"""
    def __init__(self, pads, **kwargs):
        S7LPDDR4PHY.__init__(self, pads, with_odelay=True, **kwargs)

class A7LPDDR4PHY(S7LPDDR4PHY):
    """Xilinx Artix7 LPDDR4 PHY (without odelay)

    This variant requires generating sys8x_90 clock in CRG with a 90° phase shift vs sys8x.
    """
    def __init__(self, pads, **kwargs):
        S7LPDDR4PHY.__init__(self, pads, with_odelay=False, **kwargs)
