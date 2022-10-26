#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect.csr import CSR

from litedram.phy.utils import delayed, Serializer, Deserializer, Latency, SimpleCDC
from litedram.phy.sim_utils import SimPad, SimulationPads, SimSerDesMixin
from litedram.phy.ddr5.basephy import DDR5PHY, DDR5Output


class DDR5SimulationPads(SimulationPads):
    def layout(self, databits=8, nranks=1, dq_dqs_ratio=8, with_sub_channels=False):
        common = [
            SimPad("ck_t", 1),
            SimPad("ck_c", 1),
            SimPad("reset_n", 1),
            SimPad("alert_n", 1),
        ]
        per_channel = [
            ('cs_n', nranks, False),
            ('ca', 14, False),
            ('par', 1, False),
            ('dq', databits, True),
            ('dm_n',  databits // dq_dqs_ratio, True),
            ('dqs_t',  databits // dq_dqs_ratio, True),
            ('dqs_c',  databits // dq_dqs_ratio, True),
        ]
        channels_prefix = [""] if not with_sub_channels else ["A_", "B_"]
        return common + \
                [SimPad(prefix+name, size, io) for prefix in channels_prefix for name, size, io in per_channel]


class DDR5SimPHY(SimSerDesMixin, DDR5PHY):
    """DDR5 simulation PHY with direct 16:1 serializers

    For simulation purpose two additional "DDR" clock domains are requires.
    """
    def __init__(self, aligned_reset_zero=False, dq_dqs_ratio=8, nranks=1, with_sub_channels=False, **kwargs):
        databits = 0
        if dq_dqs_ratio == 8:
            databits=8
            pads = DDR5SimulationPads(databits=8,
                                      nranks=nranks,
                                      dq_dqs_ratio=8,
                                      with_sub_channels=with_sub_channels)
        elif dq_dqs_ratio == 4:
            databits=4
            # databits length taken from DDR5 Tester
            pads = DDR5SimulationPads(databits=4,
                                      nranks=nranks,
                                      dq_dqs_ratio=4,
                                      with_sub_channels=with_sub_channels)
        else:
            raise NotImplementedError(f"Unspupported DQ:DQS ratio: {dq_dqs_ratio}")

        self.submodules += pads
        super().__init__(pads,
            ser_latency       = Latency(sys2x=Serializer.LATENCY),
            des_latency       = Latency(sys=(Deserializer.LATENCY-1 if aligned_reset_zero else Deserializer.LATENCY)),
            phytype           = "DDR5SimPHY",
            with_sub_channels = with_sub_channels,
            **kwargs)

        # fake delays (make no sense in simulation, but sdram.c expects them)
        self.settings.read_leveling = True
        self.settings.delays = 1
        self._rdly_dq_rst = CSR()
        self._rdly_dq_inc = CSR()

        common = [
            ("ck_t", 1),
            ("ck_c", 1),
            ("reset_n", 1),
            ("alert_n", 1),
        ]
        per_channel = [
            ('cs_n', nranks, False),
            ('ca', 14, False),
            ('par', 1, False),
            ('dq', databits, True),
            ('dm_n',  databits // dq_dqs_ratio, True),
            ('dqs_t',  databits // dq_dqs_ratio, True),
            ('dqs_c',  databits // dq_dqs_ratio, True),
        ]
        channels_prefix = [""] if not with_sub_channels else ["A_", "B_"]
        delay = lambda sig, cycles: delayed(self, sig, cycles=cycles)

        cs      = dict(clkdiv="sys2x", clk="sys4x_180", xilinx=True)
        cmd     = dict(clkdiv="sys2x", clk="sys4x_90_ddr", xilinx=True)
        ddr     = dict(clkdiv="sys2x", clk="sys4x_ddr", xilinx=True)
        ddr_90  = dict(clkdiv="sys2x", clk="sys4x_90_ddr", xilinx=True)

        # This configuration mimics Xilinx 7-series serdes behavior
        if aligned_reset_zero:
            ddr["reset_cnt"] = 0
            ddr["aligned"] = True

        # Clock is shifted 180 degrees to get rising edge in the middle of SDR signals.
        # To achieve that we send negated clock on clk (clk_p).
        self.ser(i=self.out.ck_t, o=self.pads.ck_t, name='ck_t', **ddr)
        self.ser(i=self.out.ck_c, o=self.pads.ck_c, name='ck_c', **ddr)

        self.ser(i=self.out.reset_n, o=self.pads.reset_n, name='reset_n', **ddr)
        self.des(i=self.pads.alert_n, o=self.out.alert_n, name='alert_n', **ddr_90)

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]

        for prefix in prefixes:

            # Command/address
            for it, (basephy_cs, pad) in enumerate(zip(getattr(self.out, prefix+'cs_n'), getattr(self.pads, prefix+'cs_n'))):
                delay_out = Signal.like(basephy_cs)
                self.sync += delay_out.eq(basephy_cs)
                cdc_out = Signal(len(delay_out)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(delay_out), o_dw=len(cdc_out),
                    i=delay_out, o=cdc_out,
                    name=f"{prefix}cs_n_{it}"
                )
                self.submodules += simple_cdc
                self.ser(i=cdc_out, o=pad, name=f'{prefix}cs_n_{it}', **cs)

            for it, (basephy_ca, pad) in enumerate(zip(getattr(self.out, prefix+'ca'), getattr(self.pads, prefix+'ca'))):
                delay_ca = Signal()
                out_ca = Signal.like(basephy_ca)
                self.sync += delay_ca.eq(basephy_ca[-1])
                self.sync += out_ca.eq(Cat(delay_ca, basephy_ca[0:-1]))
                cdc_out_ca = Signal(len(out_ca)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(out_ca), o_dw=len(cdc_out_ca),
                    i=out_ca, o=cdc_out_ca,
                    name=f"{prefix}ca_{it}"
                )
                self.submodules += simple_cdc
                self.ser(i=cdc_out_ca, o=pad, name=f'{prefix}ca{it}', **cmd)

            basephy_par = getattr(self.out, prefix+'par')
            pad = getattr(self.pads, prefix+'par')

            delay_par = Signal()
            out_par = Signal.like(basephy_par)
            self.sync += delay_par.eq(basephy_par[-1])
            self.sync += out_par.eq(Cat(delay_par, basephy_par[0:-1]))
            cdc_out_par = Signal(len(basephy_par)//2)
            simple_cdc = SimpleCDC(
                clkdiv="sys", clk="sys2x",
                i_dw=len(out_par), o_dw=len(cdc_out_par),
                i=out_par, o=cdc_out_par,
                name=f"{prefix}par_{it}"
            )
            self.submodules += simple_cdc
            self.ser(i=cdc_out_par, o=pad, name=f'{prefix}par', **cmd)

            # Tristate I/O (separate for simulation)
            for it in range(self.databits//dq_dqs_ratio):
                dqs_t_o = getattr(self.out, prefix+'dqs_t_o')[it]
                cdc_dqs_t_o = Signal(len(dqs_t_o)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(dqs_t_o), o_dw=len(cdc_dqs_t_o),
                    i=dqs_t_o, o=cdc_dqs_t_o,
                    name=f"{prefix}dqs_t_o_{it}"
                )
                self.submodules += simple_cdc
                self.ser(i=cdc_dqs_t_o,
                         o=getattr(self.pads, prefix+'dqs_t_o')[it],
                         name=f'{prefix}dqs_t_o{it}', **ddr)
                self.des(o=getattr(self.out, prefix+'dqs_t_i')[it],
                         i=getattr(self.pads, prefix+'dqs_t')[it],
                         name=f'{prefix}dqs_t_i{it}', **ddr)

                dqs_c_o = getattr(self.out, prefix+'dqs_c_o')[it]
                cdc_dqs_c_o = Signal(len(dqs_c_o)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(dqs_c_o), o_dw=len(cdc_dqs_c_o),
                    i=dqs_c_o, o=cdc_dqs_c_o,
                    name=f"{prefix}dqs_c_o_{it}"
                )
                self.submodules += simple_cdc
                self.ser(i=cdc_dqs_c_o,
                         o=getattr(self.pads, prefix+'dqs_c_o')[it],
                         name=f'{prefix}dqs_c_o{it}', **ddr)
                self.des(o=getattr(self.out, prefix+'dqs_c_i')[it],
                         i=getattr(self.pads, prefix+'dqs_c')[it],
                         name=f'{prefix}dqs_c_i{it}', **ddr)

                basephy_dm = getattr(self.out, prefix+'dm_n_o')[it]
                delay_dm = Signal.like(basephy_dm)
                out_dm = Signal.like(basephy_dm)
                self.sync += delay_dm.eq(basephy_dm[1:])
                self.comb += out_dm.eq(Cat(delay_dm[:-1], basephy_dm[0]))
                cdc_out_dm = Signal(len(out_dm)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(out_dm), o_dw=len(cdc_out_dm),
                    i=out_dm, o=cdc_out_dm,
                    name=f"{prefix}dm_o_{it}"
                )
                self.submodules += simple_cdc
                self.ser(i=cdc_out_dm, o=getattr(self.pads, prefix+'dm_n_o')[it],
                         name=f'{prefix}dm_n_o{it}', **ddr_90)

                basephy_dm_i =  getattr(self.out, prefix+'dm_n_i')[it]
                in_dm = Signal.like(basephy_dm_i)
                self.des(o=in_dm, i=getattr(self.pads, prefix+'dm_n')[it],
                         name=f'{prefix}dm_n_i{it}', **ddr_90)
                delay_dm_i = Signal(2)
                self.sync += delay_dm_i.eq(in_dm[-2:])
                self.comb += basephy_dm_i.eq(Cat(delay_dm_i, in_dm[:-2]))

            for it in range(self.databits):
                basephy_dq = getattr(self.out, prefix+'dq_o')[it]
                delay_dq = Signal.like(basephy_dq)
                out_dq = Signal.like(basephy_dq)
                self.sync += delay_dq.eq(basephy_dq[1:])
                self.comb += out_dq.eq(Cat(delay_dq[:-1], basephy_dq[0]))
                cdc_out_dq = Signal(len(out_dq)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(out_dq), o_dw=len(cdc_out_dq),
                    i=out_dq, o=cdc_out_dq,
                    name=f"{prefix}dq_o_{it}"
                )
                self.submodules += simple_cdc
                self.ser(i=cdc_out_dq, o=getattr(self.pads, prefix+'dq_o')[it],
                         name=f'{prefix}dq_o{it}', **ddr_90)

                basephy_dq_i =  getattr(self.out, prefix+'dq_i')[it]
                in_dq = Signal.like(basephy_dq_i)
                self.des(o=in_dq, i=getattr(self.pads, prefix+'dq')[it],
                         name=f'{prefix}dq_i{it}', reset_cnt=-2, **ddr_90)
                delay_dq_i = Signal(2)
                self.sync += delay_dq_i.eq(in_dq[-2:])
                self.comb += basephy_dq_i.eq(Cat(delay_dq_i, in_dq[:-2]))

            # Output enable signals can be and should be serialized as well
            out_dqs_t_oe = getattr(self.out, prefix+'dqs_oe')[0]
            cdc_out_dqs_t_oe = Signal(len(out_dqs_t_oe)//2)
            simple_cdc = SimpleCDC(
                clkdiv="sys", clk="sys2x",
                i_dw=len(out_dqs_t_oe), o_dw=len(cdc_out_dqs_t_oe),
                i=out_dqs_t_oe, o=cdc_out_dqs_t_oe,
                name=f"{prefix}dqs_t_oe"
            )
            self.submodules += simple_cdc
            self.ser(i=cdc_out_dqs_t_oe,
                     o=getattr(self.pads, prefix+'dqs_t_oe'),
                     name=f'{prefix}dqs_t_oe', **ddr)
            out_dqs_c_oe = getattr(self.out, prefix+'dqs_oe')[0]
            cdc_out_dqs_c_oe = Signal(len(out_dqs_c_oe)//2)
            simple_cdc = SimpleCDC(
                clkdiv="sys", clk="sys2x",
                i_dw=len(out_dqs_c_oe), o_dw=len(cdc_out_dqs_c_oe),
                i=out_dqs_c_oe, o=cdc_out_dqs_c_oe,
                name=f"{prefix}dqs_c_oe"
            )
            self.submodules += simple_cdc
            self.ser(i=cdc_out_dqs_c_oe,
                     o=getattr(self.pads, prefix+'dqs_c_oe'),
                     name=f'{prefix}dqs_c_oe', **ddr)

            basephy_dq_oe = getattr(self.out, prefix+'dq_oe')[0]
            delay_dq_oe = Signal.like(basephy_dq_oe)
            out_dq_oe = Signal.like(basephy_dq_oe)
            self.sync += delay_dq_oe.eq(basephy_dq_oe[1:])
            self.comb += out_dq_oe.eq(Cat(delay_dq_oe[:-1], basephy_dq_oe[0]))
            out_dqs_c_oe = getattr(self.out, prefix+'dqs_oe')[0]
            cdc_out_dq_oe = Signal(len(out_dq_oe)//2)
            simple_cdc = SimpleCDC(
                clkdiv="sys", clk="sys2x",
                i_dw=len(out_dq_oe), o_dw=len(cdc_out_dq_oe),
                i=out_dq_oe, o=cdc_out_dq_oe,
                name=f"{prefix}dq_oe"
            )
            self.submodules += simple_cdc
            self.ser(i=cdc_out_dq_oe,
                     o=getattr(self.pads, prefix+'dq_oe'),
                     name=f'{prefix}dq_oe', **ddr_90)

            self.ser(i=cdc_out_dq_oe,
                     o=getattr(self.pads, prefix+'dm_n_oe'),
                     name=f'{prefix}dm_n_oe', **ddr_90)
