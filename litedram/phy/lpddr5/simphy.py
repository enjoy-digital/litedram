#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect.csr import CSR

from litedram.phy.utils import delayed, Serializer, Deserializer, Latency, ConstBitSlip
from litedram.phy.sim_utils import SimPad, SimulationPads, SimSerDesMixin
from litedram.phy.lpddr5.basephy import LPDDR5PHY


class LPDDR5SimulationPads(SimulationPads):
    def layout(self, databits=16):
        return [
            SimPad("reset_n", 1),
            SimPad("ck", 1),
            SimPad("cs", 1),
            SimPad("ca", 7),
            SimPad("dq", databits, io=True),
            SimPad("wck", databits//8),
            SimPad("rdqs", databits//8, io=True),
            SimPad("dmi", databits//8, io=True),
        ]


class LPDDR5SimPHY(SimSerDesMixin, LPDDR5PHY):
    """LPDDR5 simulation PHY

    The following clock domains are used:
        * MC @ sys
        * PHY CK @ sys
        * PHY WCK @ sys2x or sys4x

    For simulation purpose two additional "DDR" clock domains are required (sys4x or sys8x
    depending on WCK ratio).
    """
    def __init__(self, sys_clk_freq, wck_ck_ratio=2, aligned_reset_zero=False, **kwargs):
        pads = LPDDR5SimulationPads()
        self.submodules += pads
        super().__init__(pads,
            ck_freq      = sys_clk_freq,
            wck_ck_ratio = wck_ck_ratio,
            ser_latency  = Latency(sys=Serializer.LATENCY),
            des_latency  = Latency(sys=Deserializer.LATENCY),
            phytype      = "LPDDR5SimPHY",
            **kwargs)

        # fake delays (make no nsense in simulation, but sdram.c expects them)
        self.settings.read_leveling = True
        self._rdly_dq_rst = CSR()
        self._rdly_dq_inc = CSR()

        self.settings.write_leveling = True
        self._cdly_rst = CSR()
        self._cdly_inc = CSR()
        self._wdly_dq_rst = CSR()
        self._wdly_dq_inc = CSR()
        self._wdly_dqs_rst = CSR()
        self._wdly_dqs_inc = CSR()
        self._half_sys8x_taps = CSR()

        self.settings.delays = 1

        delay = lambda sig, cycles: delayed(self, sig, cycles=cycles)
        ddr_ck      = dict(clkdiv="sys", clk="sys2x")
        ddr_ca      = dict(clkdiv="sys", clk="sys4x")
        ddr_wck     = dict(clkdiv="sys", clk={2: "sys4x", 4: "sys8x"}[wck_ck_ratio])
        ddr_wck_180 = dict(clkdiv="sys", clk={2: "sys4x_180", 4: "sys8x_180"}[wck_ck_ratio])

        def cdc(sig, cd):
            latched = Signal.like(sig)
            sd_wck = getattr(self.sync, cd["clk"])
            sd_wck += latched.eq(delay(sig, cycles=Serializer.LATENCY))
            return dict(i=latched, register=False)

        if aligned_reset_zero:
            ddr_ck["reset_cnt"] = 0
            ddr_ca["reset_cnt"] = 0
            ddr_wck["reset_cnt"] = 0

        self.comb += self.pads.reset_n.eq(delay(self.out.reset_n, cycles=Serializer.LATENCY))

        # CK signals
        self.ser(i=self.out.ck, o=self.pads.ck, name='ck', **ddr_ck)

        # CS (SDR) is delayed by 180 deg to be center aligned with CK
        # Use ConstBitSlip to shift it, then serialize that 2-bit signal as DDR (like with CK)
        cs_2bit = Signal(2)
        cs_2bit_d = Signal(2)
        self.comb += cs_2bit.eq(Replicate(self.out.cs, 2))
        self.submodules += ConstBitSlip(dw=2, slp=1, cycles=1, register=False, i=cs_2bit, o=cs_2bit_d)
        self.ser(i=cs_2bit_d, o=self.pads.cs, name='cs', **ddr_ck)

        # To center align CA (DDR) with CK it has to be delayed by 270 deg CK (+90 deg relative to CS)
        for i in range(7):
            # To achieve 270 deg shift we use ConstBitSlip with slp=3 and dw=4.
            # For this to work we first widen CA to 4 bits and use sys4x when serializing.
            ca_4bit = Signal(4)
            ca_4bit_d = Signal(4)
            self.comb += ca_4bit.eq(Cat([Replicate(bit, 2) for bit in self.out.ca[i]]))
            self.submodules += ConstBitSlip(dw=4, slp=3, cycles=1, register=False, i=ca_4bit, o=ca_4bit_d)
            self.ser(i=ca_4bit_d, o=self.pads.ca[i], name=f'ca{i}', **ddr_ca)

        # WCK
        for i in range(self.databits//8):
            self.ser(i=self.out.wck[i], o=self.pads.wck[i], name=f'wck{i}', **ddr_wck_180)
            self.ser(i=self.out.dmi_o[i], o=self.pads.dmi_o[i], name=f'dmi_o{i}', **ddr_wck)
            self.des(o=self.out.dmi_i[i], i=self.pads.dmi[i],   name=f'dmi_i{i}', **ddr_wck)
            self.ser(i=self.out.rdqs_o[i], o=self.pads.rdqs_o[i], name=f'rdqs_o{i}', **ddr_wck_180)
            self.des(o=self.out.rdqs_i[i], i=self.pads.rdqs[i],   name=f'rdqs_i{i}', **ddr_wck_180)
        for i in range(self.databits):
            self.ser(i=self.out.dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}', **ddr_wck)
            self.des(o=self.out.dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}', **ddr_wck)

        # Output enable signals
        self.comb += [
            self.pads.dmi_oe.eq(delay(self.out.dmi_oe, cycles=Serializer.LATENCY)),
            self.pads.rdqs_oe.eq(delay(self.out.rdqs_oe, cycles=Serializer.LATENCY)),
            self.pads.dq_oe.eq(delay(self.out.dq_oe, cycles=Serializer.LATENCY)),
        ]
