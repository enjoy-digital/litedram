#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect.csr import CSR

from litedram.phy.utils import delayed, Serializer, Deserializer, Latency
from litedram.phy.sim_utils import SimPad, SimulationPads, SimSerDesMixin
from litedram.phy.lpddr4.basephy import LPDDR4PHY, DoubleRateLPDDR4PHY


class LPDDR4SimulationPads(SimulationPads):
    def layout(self, databits=16):
        return [
            SimPad("clk", 1),
            SimPad("cke", 1),
            SimPad("odt", 1),
            SimPad("reset_n", 1),
            SimPad("cs", 1),
            SimPad("ca", 6),
            SimPad("dq", databits, io=True),
            SimPad("dqs", databits//8, io=True),
            SimPad("dmi", databits//8, io=True),
        ]


class LPDDR4SimPHY(SimSerDesMixin, LPDDR4PHY):
    """LPDDR4 simulation PHY with direct 16:1 serializers

    For simulation purpose two additional "DDR" clock domains are requires.
    """
    def __init__(self, aligned_reset_zero=False, **kwargs):
        pads = LPDDR4SimulationPads()
        self.submodules += pads
        super().__init__(pads,
            ser_latency  = Latency(sys=Serializer.LATENCY),
            des_latency  = Latency(sys=Deserializer.LATENCY),
            phytype      = "LPDDR4SimPHY",
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

        self.ser(i=self.out.cke, o=self.pads.cke, name='cke', **sdr)
        self.ser(i=self.out.odt, o=self.pads.odt, name='odt', **sdr)
        self.ser(i=self.out.reset_n, o=self.pads.reset_n, name='reset_n', **sdr)

        # Command/address
        self.ser(i=self.out.cs, o=self.pads.cs, name='cs', **sdr)
        for i in range(6):
            self.ser(i=self.out.ca[i], o=self.pads.ca[i], name=f'ca{i}', **sdr)

        # Tristate I/O (separate for simulation)
        for i in range(self.databits//8):
            self.ser(i=self.out.dmi_o[i], o=self.pads.dmi_o[i], name=f'dmi_o{i}', **ddr)
            self.des(o=self.out.dmi_i[i], i=self.pads.dmi[i],   name=f'dmi_i{i}', **ddr)
            self.ser(i=self.out.dqs_o[i], o=self.pads.dqs_o[i], name=f'dqs_o{i}', **ddr_90)
            self.des(o=self.out.dqs_i[i], i=self.pads.dqs[i],   name=f'dqs_i{i}', **ddr_90)
        for i in range(self.databits):
            self.ser(i=self.out.dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}', **ddr)
            self.des(o=self.out.dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}', **ddr)

        # Output enable signals
        self.comb += [
            self.pads.dmi_oe.eq(delay(self.out.dmi_oe, cycles=Serializer.LATENCY)),
            self.pads.dqs_oe.eq(delay(self.out.dqs_oe, cycles=Serializer.LATENCY)),
            self.pads.dq_oe.eq(delay(self.out.dq_oe, cycles=Serializer.LATENCY)),
        ]


class DoubleRateLPDDR4SimPHY(SimSerDesMixin, DoubleRateLPDDR4PHY):
    """LPDDR4 simulation PHY basing of DoubleRateLPDDR4PHY

    `DoubleRateLPDDR4PHY` performs a single serialization step between `sys` and `sys2x`,
    so this PHY wrapper has to do the serialization between `sys2x` and `sys8x` (SDR/DDR).

    For simulation purpose two additional "DDR" clock domains are requires.
    """
    def __init__(self, aligned_reset_zero=False, **kwargs):
        pads = LPDDR4SimulationPads()
        self.submodules += pads
        super().__init__(pads,
            ser_latency  = Latency(sys2x=Serializer.LATENCY),
            des_latency  = Latency(sys2x=Deserializer.LATENCY),
            phytype      = "LPDDR4SimPHY",
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

        self.ser(i=self.out.cke, o=self.pads.cke, name='cke', **sdr)
        self.ser(i=self.out.odt, o=self.pads.odt, name='odt', **sdr)
        self.ser(i=self.out.reset_n, o=self.pads.reset_n, name='reset_n', **sdr)

        # Command/address
        self.ser(i=self.out.cs, o=self.pads.cs, name='cs', **sdr)
        for i in range(6):
            self.ser(i=self.out.ca[i], o=self.pads.ca[i], name=f'ca{i}', **sdr)

        # Tristate I/O (separate for simulation)
        for i in range(self.databits//8):
            self.ser(i=self.out.dmi_o[i], o=self.pads.dmi_o[i], name=f'dmi_o{i}', **ddr)
            self.des(o=self.out.dmi_i[i], i=self.pads.dmi[i],   name=f'dmi_i{i}', **ddr)
            self.ser(i=self.out.dqs_o[i], o=self.pads.dqs_o[i], name=f'dqs_o{i}', **ddr_90)
            self.des(o=self.out.dqs_i[i], i=self.pads.dqs[i],   name=f'dqs_i{i}', **ddr_90)
        for i in range(self.databits):
            self.ser(i=self.out.dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}', **ddr)
            self.des(o=self.out.dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}', **ddr)

        # Output enable signals
        self.comb += [
            self.pads.dmi_oe.eq(delay(self.out.dmi_oe, cycles=Serializer.LATENCY)),
            self.pads.dqs_oe.eq(delay(self.out.dqs_oe, cycles=Serializer.LATENCY)),
            self.pads.dq_oe.eq(delay(self.out.dq_oe, cycles=Serializer.LATENCY)),
        ]
