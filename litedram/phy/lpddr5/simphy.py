#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litedram.phy.utils import delayed, Serializer, Deserializer, Latency
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

        delay = lambda sig, cycles: delayed(self, sig, cycles=cycles)
        ddr_ck     = dict(clkdiv="sys", clk="sys2x")
        ddr_ck_90  = dict(clkdiv="sys", clk="sys2x_90")
        ddr_wck    = dict(clkdiv="sys", clk={2: "sys4x", 4: "sys8x"}[wck_ck_ratio])
        ddr_wck_90 = dict(clkdiv="sys", clk={2: "sys4x_90", 4: "sys8x_90"}[wck_ck_ratio])

        if aligned_reset_zero:
            ddr_ck["reset_cnt"] = 0
            ddr_wck["reset_cnt"] = 0

        # CK signals
        # CK is shifted by 90 deg just by inversion
        # CS will then be properly aligned with respect to CK
        # CA needs 90 phase shift
        self.comb += [
            self.pads.reset_n.eq(delay(self.out.reset_n, cycles=Serializer.LATENCY)),
            self.pads.cs.eq(delay(self.out.cs, cycles=Serializer.LATENCY)), # SDR
        ]
        self.ser(i=~self.out.ck, o=self.pads.ck, name='ck', **ddr_ck)
        for i in range(7):
            self.ser(i=self.out.ca[i], o=self.pads.ca[i], name=f'ca{i}', **ddr_ck_90)

        # WCK
        for i in range(self.databits//8):
            self.ser(i=self.out.wck[i], o=self.pads.wck[i], name=f'wck{i}', **ddr_wck_90)
            self.ser(i=self.out.dmi_o[i], o=self.pads.dmi_o[i], name=f'dmi_o{i}', **ddr_wck)
            self.des(o=self.out.dmi_i[i], i=self.pads.dmi[i],   name=f'dmi_i{i}', **ddr_wck)
            self.ser(i=self.out.rdqs_o[i], o=self.pads.rdqs_o[i], name=f'dqs_o{i}', **ddr_wck_90)
            self.des(o=self.out.rdqs_i[i], i=self.pads.rdqs[i],   name=f'dqs_i{i}', **ddr_wck_90)
        for i in range(self.databits):
            self.ser(i=self.out.dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}', **ddr_wck)
            self.des(o=self.out.dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}', **ddr_wck)

        # Output enable signals
        self.comb += [
            self.pads.dmi_oe.eq(delay(self.out.dmi_oe, cycles=Serializer.LATENCY)),
            self.pads.rdqs_oe.eq(delay(self.out.rdqs_oe, cycles=Serializer.LATENCY)),
            self.pads.dq_oe.eq(delay(self.out.dq_oe, cycles=Serializer.LATENCY)),
        ]
