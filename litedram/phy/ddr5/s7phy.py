#
# This file is part of LiteDRAM.
#
# Copyright (c) 2022 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.genlib.cdc import PulseSynchronizer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

from litedram.phy.utils import delayed, Latency
from litedram.phy.ddr5.basephy import DDR5PHY

from litedram.phy.s7common import S7Common

class S7DDR5PHY(DDR5PHY, S7Common):
    def __init__(self, pads, *, iodelay_clk_freq, with_odelay,
                 with_per_dq_idelay=False, with_sub_channels=False, **kwargs):
        self.iodelay_clk_freq = iodelay_clk_freq

        # DoubleRateDDR5PHY outputs half-width signals (comparing to DDR5PHY) in sys2x domain.
        # This allows us to use 8:1 DDR OSERDESE2/ISERDESE2 to (de-)serialize the data.
        super().__init__(pads,
            ser_latency       = Latency(sys2x=1),  # OSERDESE2 4:1 DDR (2 full-rate clocks)
            des_latency       = Latency(sys=2),  # ISERDESE2 NETWORKING
            phytype           = self.__class__.__name__,
            with_sub_channels = with_sub_channels,
            **kwargs
        )

        self.settings.delays = 32
        self.settings.write_leveling = True
        self.settings.write_latency_calibration = True
        self.settings.write_dq_dqs_training = True
        self.settings.read_leveling = True

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
        # Invert clk to have it phase shifted in relation to CS_n/CA, because we serialize it with DDR,
        # rising edge will then be in the middle of a data bit.
        self.oserdese2_ddr(din=~self.out.ck_t, dout=clk_ser if with_odelay else clk_dly, clk="sys4x")
        if with_odelay:
            self.odelaye2(din=clk_ser, dout=clk_dly, rst=cdly_rst, inc=cdly_inc)
        self.obufds(din=clk_dly, dout=self.pads.ck_t, dout_b=self.pads.ck_c)

        for const in ["mir", "cai", "ca_odt"]:
            if hasattr(self.pads, const):
                self.comb += getattr(self.pads, const).eq(0)

        for cmd in ["reset_n"]:
            cmd_i = getattr(self.out, cmd)
            cmd_o = getattr(self.pads, cmd)
            cmd_ser = Signal()
            self.oserdese2_ddr(din=cmd_i, dout=cmd_ser if with_odelay else cmd_o, clk="sys4x")
            if with_odelay:
                self.odelaye2(din=cmd_ser, dout=cmd_o, rst=cdly_rst, inc=cdly_inc)

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]
        for prefix in prefixes:
            # Commands
            nranks = len(getattr(self.pads, prefix+"cs_n"))
            cs_n_ser = Signal(nranks)
            for bit in range(nranks):
                if with_odelay:
                    self.oserdese2_sdr(din=getattr(self.out, prefix+"cs_n")[bit], dout=cs_n_ser[bit], clk="sys4x")
                    self.odelaye2(din=cs_n_ser[bit], dout=getattr(self.pads, prefix+"cs_n")[bit], rst=cdly_rst, inc=cdly_inc)
                else:
                    self.oserdese2_sdr(din=getattr(self.out, prefix+"cs_n")[bit], dout=getattr(self.pads, prefix+"cs_n")[bit], clk="sys4x")
            for bit in range(len(getattr(self.pads, prefix+"ca"))):
                ca_ser = Signal()
                if with_odelay:
                    self.oserdese2_ddr(din=getattr(self.out, prefix+"ca")[bit], dout=ca_ser, clk="sys4x")
                    self.odelaye2(din=ca_ser, dout=getattr(self.pads, prefix+"ca")[bit], rst=cdly_rst, inc=cdly_inc)
                else:
                    self.oserdese2_sdr(din=getattr(self.out, prefix+"ca")[bit], dout=getattr(self.pads, prefix+"ca")[bit], clk="sys4x")

            # DQS
            for byte in range(self.databits//8):
                # DQS
                dqs_t     = Signal()
                dqs_ser   = Signal()
                dqs_dly   = Signal()
                dqs_i     = Signal()
                dqs_i_dly = Signal()
                # need to delay DQS if clocks are not phase aligned
                dqs_din = getattr(self.out, prefix+"dqs_t_o")[byte]
                if not with_odelay:
                    dqs_din_d = Signal.like(dqs_din)
                    self.sync.sys2x += dqs_din_d.eq(dqs_din)
                    dqs_din = dqs_din_d
                self.oserdese2_ddr(
                    din     = dqs_din,
                    **(dict(dout_fb=dqs_ser) if with_odelay else dict(dout=dqs_dly)),
                    tin     = ~oe_delay_dqs(getattr(self.out, prefix+"dqs_oe")),
                    tout    = dqs_t,
                    clk     = "sys4x" if with_odelay else "sys4x_90",
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
                    dinout   = getattr(self.pads, prefix+"dqs_t")[byte],
                    dinout_b = getattr(self.pads, prefix+"dqs_c")[byte],
                )
                self.idelaye2(
                    din  = dqs_i,
                    dout = dqs_i_dly,
                    rst  = self.get_rst(byte, rdly_dqs_rst),
                    inc  = self.get_inc(byte, rdly_dqs_inc),
                )
                self.iserdese2_ddr(
                    din  = dqs_i_dly,
                    dout = getattr(self.out, prefix+"dqs_t_i")[byte],
                    clk  = "sys4x",
                )

            # DQ
            for bit in range(self.databits):
                dq_t     = Signal()
                dq_ser   = Signal()
                dq_dly   = Signal()
                dq_i     = Signal()
                dq_i_dly = Signal()
                self.oserdese2_ddr(
                    din     = getattr(self.out, prefix+"dq_o")[bit],
                    **(dict(dout_fb=dq_ser) if with_odelay else dict(dout=dq_dly)),
                    tin     = ~oe_delay_data(getattr(self.out, prefix+"dq_oe")),
                    tout    = dq_t,
                    clk     = "sys4x",
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
                    dinout = getattr(self.pads, prefix+"dq")[bit],
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
                    dout = getattr(self.out, prefix+"dq_i")[bit],
                    clk  = "sys4x"
                )

        # DMI
        if hasattr(pads, "dm"):
            for byte in range(self.databits//8):
                dmi_t   = Signal()
                dmi_ser = Signal()
                dmi_dly = Signal()
                self.oserdese2_ddr(
                    din     = self.out.dmi_o[byte],
                    **(dict(dout_fb=dmi_ser) if with_odelay else dict(dout=dmi_dly)),
                    tin     = ~oe_delay_data(self.out.dmi_oe),
                    tout    = dmi_t,
                    clk     = "sys4x",
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

# PHY variants -------------------------------------------------------------------------------------

class V7DDR5PHY(S7DDR5PHY):
    """Xilinx Virtex7 DDR5 PHY (with odelay)"""
    def __init__(self, pads, **kwargs):
        S7DDR5PHY.__init__(self, pads, with_odelay=True, **kwargs)

class K7DDR5PHY(S7DDR5PHY):
    """Xilinx Kintex7 DDR5 PHY (with odelay)"""
    def __init__(self, pads, **kwargs):
        S7DDR5PHY.__init__(self, pads, with_odelay=True, **kwargs)

class A7DDR5PHY(S7DDR5PHY):
    """Xilinx Artix7 DDR5 PHY (without odelay)

    This variant requires generating sys4x_90 clock in CRG with a 90° phase shift vs sys4x.
    """
    def __init__(self, pads, **kwargs):
        S7DDR5PHY.__init__(self, pads, with_odelay=False, **kwargs)
