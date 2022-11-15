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

from litedram.phy.utils import delayed, Latency, SimpleCDC
from litedram.phy.ddr5.basephy import DDR5PHY

from litedram.phy.s7common import S7Common

class S7DDR5PHY(DDR5PHY, S7Common):
    def __init__(self, pads, *, iodelay_clk_freq, with_odelay, with_idelay=True,
                 with_per_dq_idelay=False, with_sub_channels=False, **kwargs):
        self.iodelay_clk_freq = iodelay_clk_freq

        def cdc(i):
            o = Signal()
            psync = PulseSynchronizer("sys", "sys2x")
            self.submodules += psync
            self.comb += [
                psync.i.eq(i),
                o.eq(psync.o),
            ]
            return o


        # DoubleRateDDR5PHY outputs half-width signals (comparing to DDR5PHY) in sys2x domain.
        # This allows us to use 8:1 DDR OSERDESE2/ISERDESE2 to (de-)serialize the data.
        super().__init__(pads,
            ser_latency       = Latency(sys2x=1),  # OSERDESE2 4:1 DDR (2 full-rate clocks)
            des_latency       = Latency(sys=2),  # ISERDESE2 NETWORKING
            phytype           = self.__class__.__name__,
            with_sub_channels = with_sub_channels,
            csr_cdc           = cdc,
            with_odelay       = with_odelay,
            with_idelay       = with_idelay,
            rd_extra_delay    = Latency(sys2x=3),
            **kwargs
        )

        _l = self._l

        self.settings.delays = 32
        self.settings.write_leveling = True
        self.settings.write_latency_calibration = True
        self.settings.write_dq_dqs_training = True
        self.settings.read_leveling = True

        # Serialization ----------------------------------------------------------------------------

        ddr     = dict(clkdiv="sys2x", clk="sys4x_unbuf", rst_sig=self._rst_cdc)
        cmd     = dict(clkdiv="sys2x", clk="sys4x_unbuf", rst_sig=self._rst_cdc)
        cs      = dict(clkdiv="sys2x", clk="sys4x_unbuf", rst_sig=self._rst_cdc)
        ddr_90  = dict(clkdiv="sys2x", clk="sys4x_90_unbuf", rst_sig=self._rst_cdc)

        # Clock
        clk_dly = Signal()
        clk_ser = Signal()

        ck_t = self.out.ck_t
        cdc_ck_t = Signal(len(ck_t)//2)
        simple_cdc = SimpleCDC(
            clkdiv="sys", clk="sys2x",
            i_dw=len(ck_t), o_dw=len(cdc_ck_t),
            i=ck_t, o=cdc_ck_t,
            name=f"ck_t",
            register=True,
        )
        self.submodules += simple_cdc

        # Every other signal should be realligned to clock.
        self.oserdese2_ddr(
            din=cdc_ck_t,
            **(dict(dout_fb=clk_ser) if with_odelay else dict(dout=clk_dly)),
            **ddr,
        )
        if with_odelay:
            self.odelaye2(
                din=clk_ser,
                dout=clk_dly,
                rst=_l['ckdly_rst'],
                inc=_l['ckdly_inc'],
                clk="sys2x",
            )
        self.obufds(din=clk_dly, dout=self.pads.ck_t, dout_b=self.pads.ck_c)

        for const in ["mir", "cai", "ca_odt"]:
            if hasattr(self.pads, const):
                self.comb += getattr(self.pads, const).eq(0)

        reset_n = self.out.reset_n
        cdc_reset_n = Signal(len(reset_n)//2)
        simple_cdc = SimpleCDC(
            clkdiv="sys", clk="sys2x",
            i_dw=len(reset_n), o_dw=len(cdc_reset_n),
            i=reset_n, o=cdc_reset_n,
            name=f"reset_n",
            register=True,
        )
        self.submodules += simple_cdc
        reset_n_o = getattr(self.pads, 'reset_n')
        self.oserdese2_ddr(din=cdc_reset_n, dout=reset_n_o, **ddr)

        self.iserdese2_ddr(din=self.pads.alert_n, dout=self.out.alert_n, **ddr_90)

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]
        for prefix in prefixes:
            # Commands
            # CS_n --------------------------------------------------------------------------------
            nranks = len(getattr(self.pads, prefix+"cs_n"))
            cs_n_ser = Signal(nranks)
            for it, (basephy_cs, pad) in enumerate(
                zip(getattr(self.out, prefix+'cs_n'), getattr(self.pads, prefix+'cs_n'))):
                cdc_out_cs = Signal(len(basephy_cs)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(basephy_cs), o_dw=len(cdc_out_cs),
                    i=basephy_cs, o=cdc_out_cs,
                    name=f"{prefix}cs_n_{it}",
                    register=True,
                )
                self.submodules += simple_cdc
                cs_n_ser = Signal()
                self.oserdese2_ddr(
                    din=cdc_out_cs,
                    **(dict(dout_fb=cs_n_ser) if with_odelay else dict(dout=pad)),
                    **cs,
                )
                if with_odelay:
                    self.odelaye2(
                        din=cs_n_ser,
                        dout=pad,
                        rst=self.get_rst(it, _l[prefix+'csdly_rst'], prefix, "sys2x"),
                        inc=self.get_inc(it, _l[prefix+'csdly_inc'], prefix, "sys2x"),
                        clk="sys2x",
                    )

            # CA ----------------------------------------------------------------------------------
            for it, (basephy_ca, pad) in enumerate(
                zip(getattr(self.out, prefix+'ca'), getattr(self.pads, prefix+'ca'))):
                cdc_out_ca = Signal(len(basephy_ca)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(basephy_ca), o_dw=len(cdc_out_ca),
                    i=basephy_ca, o=cdc_out_ca,
                    name=f"{prefix}ca_{it}",
                    register=True,
                )
                self.submodules += simple_cdc
                ca_ser = Signal()
                self.oserdese2_ddr(
                    din=cdc_out_ca,
                    **(dict(dout_fb=ca_ser) if with_odelay else dict(dout=pad)),
                    **cmd,
                )
                if with_odelay:
                    self.odelaye2(
                        din=ca_ser,
                        dout=pad,
                        rst=self.get_rst(it, _l[prefix+'cadly_rst'], prefix, "sys2x"),
                        inc=self.get_inc(it, _l[prefix+'cadly_inc'], prefix, "sys2x"),
                        clk="sys2x",
                    )

            # PAR ---------------------------------------------------------------------------------
            if hasattr(self.pads, prefix+'par'):
                basephy_par = getattr(self.out, prefix+'par')
                pad = getattr(self.pads, prefix+'par')

                cdc_out_par = Signal(len(basephy_par)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(basephy_par), o_dw=len(cdc_out_par),
                    i=basephy_par, o=cdc_out_par,
                    name=f"{prefix}par_{it}",
                    register=True,
                )
                self.submodules += simple_cdc
                par_ser = Signal()
                self.oserdese2_ddr(
                    din=cdc_out_par,
                    **(dict(dout_fb=par_ser) if with_odelay else dict(dout=pad)),
                    **cmd,
                )
                if with_odelay:
                    self.odelaye2(
                        din=par_ser,
                        dout=pad,
                        rst=_l[prefix+'pardly_rst'],
                        inc=_l[prefix+'pardly_inc'],
                        clk="sys2x",
                    )

            # DQS ---------------------------------------------------------------------------------
            strobes = len(pads.dqs_t) if hasattr(pads, "dqs_t") else len(pads.A_dqs_t)
            for it in range(strobes):
                dqs_t_o = getattr(self.out, prefix+'dqs_t_o')[it]
                cdc_dqs_t_o = Signal(len(dqs_t_o)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(dqs_t_o), o_dw=len(cdc_dqs_t_o),
                    i=dqs_t_o, o=cdc_dqs_t_o,
                    name=f"{prefix}dqs_t_o_{it}",
                    register=True,
                )
                self.submodules += simple_cdc

                out_dqs_oe = getattr(self.out, prefix+'dqs_oe')[it]
                cdc_out_dqs_oe = Signal(len(out_dqs_oe)//2)
                simple_cdc = SimpleCDC(
                    clkdiv="sys", clk="sys2x",
                    i_dw=len(out_dqs_oe), o_dw=len(cdc_out_dqs_oe),
                    i=~out_dqs_oe, o=cdc_out_dqs_oe,
                    name=f"{prefix}dqs_t_oe",
                    register=True,
                )
                self.submodules += simple_cdc

                dqs_ser   = Signal()
                dqs_dly   = Signal()
                dqs_i     = Signal()
                dqs_i_dly = Signal()
                dqs_t     = Signal()

                self.oserdese2_ddr_with_tri(
                    din     = cdc_dqs_t_o,
                    **(dict(dout_fb = dqs_ser) if with_odelay else dict(dout = dqs_dly)),
                    tin     = cdc_out_dqs_oe,
                    tout    = dqs_t,
                    **ddr,
                )
                if with_odelay:
                    self.odelaye2(
                        din  = dqs_ser,
                        dout = dqs_dly,
                        rst  = self.get_rst(it, _l[prefix+'wdly_dqs_rst'], prefix, "sys2x"),
                        inc  = self.get_inc(it, _l[prefix+'wdly_dqs_inc'], prefix, "sys2x"),
                        clk="sys2x",
                    )

                self.iobufds(
                    din      = dqs_dly,
                    dout     = dqs_i,
                    tin      = dqs_t,
                    dinout   = getattr(self.pads, prefix+"dqs_t")[it],
                    dinout_b = getattr(self.pads, prefix+"dqs_c")[it],
                )
                self.idelaye2(
                    din  = dqs_i,
                    dout = dqs_i_dly,
                    rst  = self.get_rst(it, _l[prefix+'rdly_dqs_rst'], prefix, "sys2x"),
                    inc  = self.get_inc(it, _l[prefix+'rdly_dqs_inc'], prefix, "sys2x"),
                    clk="sys2x",
                )
                self.iserdese2_ddr(
                    din    = dqs_i_dly,
                    dout   = getattr(self.out, prefix+"dqs_t_i")[it],
                    clk    = "sys4x_unbuf",
                    clkdiv = "sys"
                )

            # DQ ----------------------------------------------------------------------------------
            modules = self.databits // strobes
            dq_oe = {}
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
                    name=f"{prefix}dq_o_{it}",
                    register=True,
                )
                self.submodules += simple_cdc

                if it//modules not in dq_oe:
                    basephy_dq_oe = getattr(self.out, prefix+'dq_oe')[it//modules]
                    delay_dq_oe = Signal.like(basephy_dq_oe)
                    out_dq_oe = Signal.like(basephy_dq_oe)
                    self.sync += delay_dq_oe.eq(basephy_dq_oe[1:])
                    self.comb += out_dq_oe.eq(Cat(delay_dq_oe[:-1], basephy_dq_oe[0]))
                    cdc_out_dq_oe = Signal(len(out_dq_oe)//2)
                    simple_cdc = SimpleCDC(
                        clkdiv="sys", clk="sys2x",
                        i_dw=len(out_dq_oe), o_dw=len(cdc_out_dq_oe),
                        i=~out_dq_oe, o=cdc_out_dq_oe,
                        name=f"{prefix}dq_oe{it//modules}",
                        register=True,
                    )
                    self.submodules += simple_cdc
                    dq_oe[it//modules] = cdc_out_dq_oe

                dq_t     = Signal()
                dq_ser   = Signal()
                dq_dly   = Signal()
                dq_i     = Signal()
                dq_i_dly = Signal()

                self.oserdese2_ddr_with_tri(
                    din     = cdc_out_dq,
                    **(dict(dout_fb=dq_ser) if with_odelay else dict(dout=dq_dly)),
                    tin     = dq_oe[it//modules],
                    tout    = dq_t,
                    **ddr_90,
                )
                if with_odelay:
                    self.odelaye2(
                        din  = dq_ser,
                        dout = dq_dly,
                        rst  = self.get_rst(it, _l[prefix+'wdly_dq_rst'], prefix, "sys2x"),
                        inc  = self.get_inc(it, _l[prefix+'wdly_dq_inc'], prefix, "sys2x"),
                        clk="sys2x",
                    )
                self.iobuf(
                    din    = dq_dly,
                    dout   = dq_i,
                    dinout = getattr(self.pads, prefix+"dq")[it],
                    tin    = dq_t
                )

                basephy_dq_i =  getattr(self.out, prefix+'dq_i')[it]
                in_dq = Signal.like(basephy_dq_i)
                delay_dq_i = Signal(2)

                self.idelaye2(
                    din  = dq_i,
                    dout = dq_i_dly,
                    rst  = self.get_rst(it, _l[prefix+'rdly_dq_rst'], prefix, "sys2x"),
                    inc  = self.get_inc(it, _l[prefix+'rdly_dq_inc'], prefix, "sys2x"),
                    clk="sys2x",
                )
                self.iserdese2_ddr(
                    din  = dq_i_dly,
                    dout = in_dq,
                    clk    = "sys4x_unbuf",
                    clkdiv = "sys"
                )
                self.sync += delay_dq_i.eq(in_dq[-2:])
                self.comb += basephy_dq_i.eq(Cat(delay_dq_i, in_dq[:-2]))

            # DM_n --------------------------------------------------------------------------------
            if hasattr(pads, "dm_n"):
                for it in range(strobes):
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
                        name=f"{prefix}dm_o_{it}",
                        register=True,
                    )
                    self.submodules += simple_cdc

                    dmi_t   = Signal()
                    dmi_ser = Signal()
                    dmi_dly = Signal()
                    self.oserdese2_ddr_with_tri(
                        din     = cdc_out_dm,
                        **(dict(dout_fb=dmi_ser) if with_odelay else dict(dout=dmi_dly)),
                        tin     = dq_oe[it],
                        tout    = dmi_t,
                        clk     = "sys4x",
                    )
                    if with_odelay:
                        self.odelaye2(
                            din  = dmi_ser,
                            dout = dmi_dly,
                            rst  = self.get_rst(it, _l[preifx+'wdly_dm_rst'], prefix, "sys2x"),
                            inc  = self.get_inc(it, _l[prefix+'wdly_dm_inc'], prefix, "sys2x"),
                            clk="sys2x",
                        )
                    self.iobuf(
                        din    = dmi_dly,
                        dout   = Signal(),
                        tin    = dmi_t,
                        dinout = getattr(self.pads, prefix+'dmi')[it],
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
