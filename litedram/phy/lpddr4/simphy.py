#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litedram.phy.lpddr4.utils import delayed, Serializer, Deserializer
from litedram.phy.lpddr4.basephy import LPDDR4PHY, DoubleRateLPDDR4PHY, Latency


class LPDDR4SimulationPads(Module):
    """Pads for simulation purpose

    To avoid simulate tristate behavior of DQ/DQS/DMI pins separate input and output
    pins (_i/_o) are provided. Output pins are to be driven by the PHY and input pins
    are to be driven by the DRAM simulator. This module sets the actual values on pins
    `dq`, `dqs` and `dmi` based on output enable signals.
    """
    def __init__(self, databits=16):
        self.clk_p   = Signal()
        self.clk_n   = Signal()
        self.cke     = Signal()
        self.odt     = Signal()
        self.reset_n = Signal()
        self.cs      = Signal()
        self.ca      = Signal(6)
        # signals for checking actual tristate lines state (PHY reads these)
        self.dq      = Signal(databits)
        self.dqs     = Signal(databits//8)
        self.dmi     = Signal(databits//8)
        # internal tristates i/o that should be driven for simulation
        self.dq_o    = Signal(databits)  # PHY drives these
        self.dq_i    = Signal(databits)  # DRAM chip (simulator) drives these
        self.dq_oe   = Signal()          # PHY drives these
        self.dqs_o   = Signal(databits//8)
        self.dqs_i   = Signal(databits//8)
        self.dqs_oe  = Signal()
        self.dmi_o   = Signal(databits//8)
        self.dmi_i   = Signal(databits//8)
        self.dmi_oe  = Signal()

        self.comb += [
            If(self.dq_oe, self.dq.eq(self.dq_o)).Else(self.dq.eq(self.dq_i)),
            If(self.dqs_oe, self.dqs.eq(self.dqs_o)).Else(self.dqs.eq(self.dqs_i)),
            If(self.dmi_oe, self.dmi.eq(self.dmi_o)).Else(self.dmi.eq(self.dmi_i)),
        ]


class _LPDDR4SimPHYMixin:
    """Common serialization logic for simulation PHYs

    This mixin provides `do_serialization` method for constructing the boilerplate
    serialization/deserialization paths for a simulation PHY. This can serve as a
    reference for implemeing PHYs for concrete FPGAs.

    To make the (de-)serialization work in simulation two additional clock domains
    are required: `sys8x_ddr` and `sys8x_90_ddr`. These correspond to `sys8x` and
    `sys8x_90`, are phase aligned with them and at twice their frequency. These
    clock domains are requried to implement DDR (de-)serialization at 8x sys clock.
    """
    def _add_name(self, prefix, kwargs):
        name = prefix + "_" + kwargs.pop("name", "")
        kwargs["name"] = name.strip("_")

    def _serialize(self, **kwargs):
        self._add_name("ser", kwargs)
        ser = Serializer(o_dw=1, **kwargs)
        self.submodules += ser

    def _deserialize(self, **kwargs):
        self._add_name("des", kwargs)
        des = Deserializer(i_dw=1, **kwargs)
        self.submodules += des

    def do_serialization(self, clkdiv, delay, aligned_reset_zero):
        def add_reset_cnt(phase, kwargs):
            if aligned_reset_zero and phase == 0:
                kwargs["reset_cnt"] = 0

        def ser_sdr(phase=0, **kwargs):
            add_reset_cnt(phase, kwargs)
            clk = {0: "sys8x", 90: "sys8x_90"}[phase]
            self._serialize(clk=clk, clkdiv=clkdiv, i_dw=len(kwargs["i"]), **kwargs)

        def ser_ddr(phase=0, **kwargs):
            add_reset_cnt(phase, kwargs)
            # for simulation we require sys8x_ddr clock (=sys16x)
            clk = {0: "sys8x_ddr", 90: "sys8x_90_ddr"}[phase]
            self._serialize(clk=clk, clkdiv=clkdiv, i_dw=len(kwargs["i"]), **kwargs)

        def des_ddr(phase=0, **kwargs):
            add_reset_cnt(phase, kwargs)
            clk = {0: "sys8x_ddr", 90: "sys8x_90_ddr"}[phase]
            self._deserialize(clk=clk, clkdiv=clkdiv, o_dw=len(kwargs["o"]), **kwargs)

        # Clock is shifted 180 degrees to get rising edge in the middle of SDR signals.
        # To achieve that we send negated clock on clk_p and non-negated on clk_n.
        ser_ddr(i=~self.out.clk,    o=self.pads.clk_p,   name='clk_p')
        ser_ddr(i=self.out.clk,     o=self.pads.clk_n,   name='clk_n')

        ser_sdr(i=self.out.cke,     o=self.pads.cke,     name='cke')
        ser_sdr(i=self.out.odt,     o=self.pads.odt,     name='odt')
        ser_sdr(i=self.out.reset_n, o=self.pads.reset_n, name='reset_n')

        # Command/address
        ser_sdr(i=self.out.cs,      o=self.pads.cs,      name='cs')
        for i in range(6):
            ser_sdr(i=self.out.ca[i], o=self.pads.ca[i], name=f'ca{i}')

        # Tristate I/O (separate for simulation)
        for i in range(self.databits//8):
            ser_ddr(i=self.out.dmi_o[i], o=self.pads.dmi_o[i], name=f'dmi_o{i}')
            des_ddr(o=self.out.dmi_i[i], i=self.pads.dmi[i],   name=f'dmi_i{i}')
            ser_ddr(i=self.out.dqs_o[i], o=self.pads.dqs_o[i], name=f'dqs_o{i}', phase=90)
            des_ddr(o=self.out.dqs_i[i], i=self.pads.dqs[i],   name=f'dqs_i{i}', phase=90)
        for i in range(self.databits):
            ser_ddr(i=self.out.dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}')
            des_ddr(o=self.out.dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}')

        # Output enable signals
        self.comb += self.pads.dmi_oe.eq(delay(self.out.dmi_oe, cycles=Serializer.LATENCY))
        self.comb += self.pads.dqs_oe.eq(delay(self.out.dqs_oe, cycles=Serializer.LATENCY))
        self.comb += self.pads.dq_oe.eq(delay(self.out.dq_oe, cycles=Serializer.LATENCY))


class LPDDR4SimPHY(_LPDDR4SimPHYMixin, LPDDR4PHY):
    """LPDDR4 simulation PHY with direct 16:1 serializers"""
    def __init__(self, aligned_reset_zero=False, **kwargs):
        pads = LPDDR4SimulationPads()
        self.submodules += pads
        super().__init__(pads,
            ser_latency  = Latency(Serializer.LATENCY),
            des_latency  = Latency(Deserializer.LATENCY),
            phytype      = "LPDDR4SimPHY",
            **kwargs)

        self.do_serialization(
            clkdiv             = "sys",
            delay              = lambda sig, cycles: delayed(self, sig, cycles=cycles),
            aligned_reset_zero = aligned_reset_zero,
        )


class DoubleRateLPDDR4SimPHY(_LPDDR4SimPHYMixin, DoubleRateLPDDR4PHY):
    """LPDDR4 simulation PHY basing of DoubleRateLPDDR4PHY

    `DoubleRateLPDDR4PHY` performs a single serialization step between `sys` and `sys2x`,
    so this PHY wrapper has to do the serialization between `sys2x` and `sys8x` (SDR/DDR).
    """
    def __init__(self, aligned_reset_zero=False, **kwargs):
        pads = LPDDR4SimulationPads()
        self.submodules += pads
        super().__init__(pads,
            ser_latency  = Latency(sys=0, sys8x=4*Serializer.LATENCY),
            des_latency  = Latency(sys=0, sys8x=4*Deserializer.LATENCY),
            phytype      = "LPDDR4SimPHY",
            **kwargs)

        self.submodules.half_delay = ClockDomainsRenamer("sys2x")(Module())

        self.do_serialization(
            clkdiv             = "sys2x",
            delay              = lambda sig, cycles: delayed(self.half_delay, sig, cycles=cycles),
            aligned_reset_zero = aligned_reset_zero,
        )
