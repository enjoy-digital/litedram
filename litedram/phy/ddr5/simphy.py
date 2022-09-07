#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect.csr import CSR

from litedram.phy.utils import delayed, Serializer, Deserializer, Latency
from litedram.phy.sim_utils import SimPad, SimulationPads, SimSerDesMixin
from litedram.phy.ddr5.basephy import DDR5PHY


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
            ser_latency       = Latency(sys=Serializer.LATENCY),
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

        sdr     = dict(clkdiv="sys", clk="sys4x")
        sdr_90  = dict(clkdiv="sys", clk="sys4x_90")
        cs      = dict(clkdiv="sys", clk="sys4x_180")
        cmd     = dict(clkdiv="sys", clk="sys4x_180s_ddr")
        ddr     = dict(clkdiv="sys", clk="sys4x_ddr")
        ddr_90  = dict(clkdiv="sys", clk="sys4x_90_ddr")

        if aligned_reset_zero:
            sdr["reset_cnt"] = 0
            sdr_90["reset_cnt"] = 0
            cs["reset_cnt"] = 0
            cmd["reset_cnt"] = 0
            ddr["reset_cnt"] = 0
            ddr["aligned"] = True
            ddr_90["reset_cnt"] = 0

        # Clock is shifted 180 degrees to get rising edge in the middle of SDR signals.
        # To achieve that we send negated clock on clk (clk_p).
        self.ser(i=self.out.ck_t, o=self.pads.ck_t, name='ck_t', **ddr)
        self.ser(i=self.out.ck_c, o=self.pads.ck_c, name='ck_c', **ddr)

        self.ser(i=self.out.reset_n, o=self.pads.reset_n, name='reset_n', **sdr)
        self.des(i=self.pads.alert_n, o=self.out.alert_n, name='alert_n', **sdr_90)

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]

        for prefix in prefixes:

            # Command/address
            for rank in range(nranks):
                self.ser(i=getattr(self.out, prefix+'cs_n')[rank],
                         o=getattr(self.pads, prefix+'cs_n')[rank],
                         name=f'{prefix}cs_n', **cs)
            for i in range(14):
                self.ser(i=getattr(self.out, prefix+'ca')[i],
                         o=getattr(self.pads, prefix+'ca')[i],
                         name=f'{prefix}ca{i}', **cmd)
            self.ser(i=getattr(self.out, prefix+'par'),
                     o=getattr(self.pads, prefix+'par'),
                     name=f'{prefix}par', **cmd)

            # Tristate I/O (separate for simulation)
            for i in range(self.databits//dq_dqs_ratio):
                self.ser(i=getattr(self.out, prefix+'dqs_t_o')[i],
                         o=getattr(self.pads, prefix+'dqs_t_o')[i],
                         name=f'{prefix}dqs_t_o{i}', **ddr)
                self.des(o=getattr(self.out, prefix+'dqs_t_i')[i],
                         i=getattr(self.pads, prefix+'dqs_t')[i],
                         name=f'{prefix}dqs_t_i{i}', **ddr)
                self.ser(i=getattr(self.out, prefix+'dqs_c_o')[i],
                         o=getattr(self.pads, prefix+'dqs_c_o')[i],
                         name=f'{prefix}dqs_c_o{i}', **ddr)
                self.des(o=getattr(self.out, prefix+'dqs_c_i')[i],
                         i=getattr(self.pads, prefix+'dqs_c')[i],
                         name=f'{prefix}dqs_c_i{i}', **ddr)
                self.ser(i=getattr(self.out, prefix+'dm_n_o')[i],
                         o=getattr(self.pads, prefix+'dm_n_o')[i],
                         name=f'{prefix}dm_n_o{i}', **ddr_90)
                self.des(o=getattr(self.out, prefix+'dm_n_i')[i],
                         i=getattr(self.pads, prefix+'dm_n')[i],
                         name=f'{prefix}dm_n_i{i}', **ddr_90)
            for i in range(self.databits):
                self.ser(i=getattr(self.out, prefix+'dq_o')[i],
                         o=getattr(self.pads, prefix+'dq_o')[i],
                         name=f'{prefix}dq_o{i}', **ddr_90)
                self.des(o=getattr(self.out, prefix+'dq_i')[i],
                         i=getattr(self.pads, prefix+'dq')[i],
                         name=f'{prefix}dq_i{i}', **ddr_90)

            # Output enable signals can be and should be serialized as well
            self.ser(i=getattr(self.out, prefix+'dqs_oe'),
                     o=getattr(self.pads, prefix+'dqs_t_oe'),
                     name=f'{prefix}dqs_t_oe', **ddr)
            self.ser(i=getattr(self.out, prefix+'dqs_oe'),
                     o=getattr(self.pads, prefix+'dqs_c_oe'),
                     name=f'{prefix}dqs_c_oe', **ddr)
            self.ser(i=getattr(self.out, prefix+'dqs_oe'),
                     o=getattr(self.pads, prefix+'dm_n_oe'),
                     name=f'{prefix}dm_n_oe', **ddr)
            self.ser(i=getattr(self.out, prefix+'dqs_oe'),
                     o=getattr(self.pads, prefix+'dq_oe'),
                     name=f'{prefix}dq_oe', **ddr)
