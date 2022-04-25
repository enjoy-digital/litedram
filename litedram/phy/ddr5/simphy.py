#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect.csr import CSR

from litedram.phy.utils import delayed, Serializer, Deserializer, Latency
from litedram.phy.sim_utils import SimPad, SimulationPads, SimSerDesMixin
from litedram.phy.ddr5.basephy import DDR5PHY, DoubleRateDDR5PHY


class DDR5SimulationPads(SimulationPads):
    def layout(self, databits=8):
        return [
            SimPad("clk", 1),
            SimPad("reset_n", 1),
            SimPad("cs_n", 1),
            SimPad("ca", 14),
            SimPad("dq", databits, io=True),
            SimPad("dqs", databits//8, io=True),
            SimPad("ca_odt", 1),
            SimPad("mir", 1),
            SimPad("cai", 1),
        ]


class DDR5SimPHY(SimSerDesMixin, DDR5PHY):
    """DDR5 simulation PHY with direct 16:1 serializers

    For simulation purpose two additional "DDR" clock domains are requires.
    """
    def __init__(self, aligned_reset_zero=False, **kwargs):
        pads = DDR5SimulationPads()
        self.submodules += pads
        super().__init__(pads,
            ser_latency  = Latency(sys=Serializer.LATENCY),
            des_latency  = Latency(sys=Deserializer.LATENCY),
            phytype      = "DDR5SimPHY",
            **kwargs)

        # fake delays (make no nsense in simulation, but sdram.c expects them)
        self.settings.read_leveling = True
        self.settings.delays = 1
        self._rdly_dq_rst = CSR()
        self._rdly_dq_inc = CSR()

        delay = lambda sig, cycles: delayed(self, sig, cycles=cycles)
        sdr    = dict(clkdiv="sys", clk="sys8x")
        sdr_90 = dict(clkdiv="sys", clk="sys8x_90")
        ddr    = dict(clkdiv="sys", clk="sys8x_ddr")
        ddr_90 = dict(clkdiv="sys", clk="sys8x_90_ddr")

        if aligned_reset_zero:
            sdr["reset_cnt"] = 0
            ddr["reset_cnt"] = 0

        # Clock is shifted 180 degrees to get rising edge in the middle of SDR signals.
        # To achieve that we send negated clock on clk (clk_p).
        self.ser(i=~self.out.clk, o=self.pads.clk, name='clk', **ddr)

        self.ser(i=self.out.reset_n, o=self.pads.reset_n, name='reset_n', **sdr)

        # Command/address
        self.ser(i=self.out.cs_n, o=self.pads.cs_n, name='cs_n', **sdr)
        for i in range(14):
            self.ser(i=self.out.ca[i], o=self.pads.ca[i], name=f'ca{i}', **sdr)

        # Tristate I/O (separate for simulation)
        for i in range(self.databits//8):
            self.ser(i=self.out.dqs_o[i], o=self.pads.dqs_o[i], name=f'dqs_o{i}', **ddr_90)
            self.des(o=self.out.dqs_i[i], i=self.pads.dqs[i],   name=f'dqs_i{i}', **ddr_90)
        for i in range(self.databits):
            self.ser(i=self.out.dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}', **ddr)
            self.des(o=self.out.dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}', **ddr)

        # Output enable signals
        self.comb += [
            self.pads.ca_odt.eq(self.out.ca_odt),
            self.pads.mir.eq(self.out.mir),
            self.pads.cai.eq(self.out.cai),
        ]


class DoubleRateDDR5SimPHY(SimSerDesMixin, DoubleRateDDR5PHY):
    """DDR5 simulation PHY basing of DoubleRateDDR5PHY

    `DoubleRateDDR5PHY` performs a single serialization step between `sys` and `sys2x`,
    so this PHY wrapper has to do the serialization between `sys2x` and `sys8x` (SDR/DDR).

    For simulation purpose two additional "DDR" clock domains are requires.
    """
    def __init__(self, aligned_reset_zero=False, **kwargs):
        pads = DDR5SimulationPads()
        self.submodules += pads
        super().__init__(pads,
            ser_latency  = Latency(sys2x=Serializer.LATENCY),
            des_latency  = Latency(sys2x=Deserializer.LATENCY),
            phytype      = "DDR5SimPHY",
            **kwargs)
        self.submodules.half_delay = ClockDomainsRenamer("sys2x")(Module())

        # fake delays (make no nsense in simulation, but sdram.c expects them)
        self.settings.read_leveling = True
        self.settings.delays = 1
        self._rdly_dq_rst = CSR()
        self._rdly_dq_inc = CSR()

        delay = lambda sig, cycles: delayed(self.half_delay, sig, cycles=cycles)

        sdr    = dict(clkdiv="sys2x", clk="sys8x")
        sdr_90 = dict(clkdiv="sys2x", clk="sys8x_90")
        ddr    = dict(clkdiv="sys2x", clk="sys8x_ddr")
        ddr_90 = dict(clkdiv="sys2x", clk="sys8x_90_ddr")

        if aligned_reset_zero:
            sdr["reset_cnt"] = 0
            ddr["reset_cnt"] = 0

        # Clock is shifted 180 degrees to get rising edge in the middle of SDR signals.
        # To achieve that we send negated clock on clk (clk_p).
        self.ser(i=~self.out.clk, o=self.pads.clk, name='clk', **ddr)

        self.ser(i=self.out.ca_odt, o=self.pads.ca_odt, name='ca_odt', **sdr)
        self.ser(i=self.out.mir, o=self.pads.mir, name='mir', **sdr)
        self.ser(i=self.out.cai, o=self.pads.cai, name='cai', **sdr)
        self.ser(i=self.out.reset_n, o=self.pads.reset_n, name='reset_n', **sdr)

        # Command/address
        self.ser(i=self.out.cs, o=self.pads.cs, name='cs', **sdr)
        for i in range(14):
            self.ser(i=self.out.ca[i], o=self.pads.ca[i], name=f'ca{i}', **sdr)

        # Tristate I/O (separate for simulation)
        for i in range(self.databits//8):
            self.ser(i=self.out.dqs_o[i], o=self.pads.dqs_o[i], name=f'dqs_o{i}', **ddr_90)
            self.des(o=self.out.dqs_i[i], i=self.pads.dqs[i],   name=f'dqs_i{i}', **ddr_90)
        for i in range(self.databits):
            self.ser(i=self.out.dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}', **ddr)
            self.des(o=self.out.dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}', **ddr)

        # Output enable signals
        self.comb += [
            self.pads.ca_odt.eq(self.out.ca_odt),
            self.pads.mir.eq(self.out.mir),
            self.pads.cai.eq(self.out.cai),
        ]
