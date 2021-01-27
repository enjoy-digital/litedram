from migen import *

from litedram.phy.lpddr4.utils import delayed
from litedram.phy.lpddr4.basephy import LPDDR4PHY


class LPDDR4SimulationPads(Module):
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


class LPDDR4SimPHY(LPDDR4PHY):
    def __init__(self, sys_clk_freq=100e6, aligned_reset_zero=False, **kwargs):
        pads = LPDDR4SimulationPads()
        self.submodules += pads
        super().__init__(pads,
            sys_clk_freq       = sys_clk_freq,
            write_ser_latency  = Serializer.LATENCY,
            read_des_latency   = Deserializer.LATENCY,
            phytype            = "LPDDR4SimPHY",
            **kwargs)

        def add_reset_value(phase, kwargs):
            if aligned_reset_zero and phase == 0:
                kwargs["reset_value"] = 0

        # Serialization
        def serialize(**kwargs):
            name = 'ser_' + kwargs.pop('name', '')
            ser = Serializer(o_dw=1, name=name.strip('_'), **kwargs)
            self.submodules += ser

        def deserialize(**kwargs):
            name = 'des_' + kwargs.pop('name', '')
            des = Deserializer(i_dw=1, name=name.strip('_'), **kwargs)
            self.submodules += des

        def ser_sdr(phase=0, **kwargs):
            clkdiv = {0: "sys8x", 90: "sys8x_90"}[phase]
            # clk = {0: "sys", 90: "sys_11_25"}[phase]
            clk = {0: "sys", 90: "sys"}[phase]
            add_reset_value(phase, kwargs)
            serialize(clk=clk, clkdiv=clkdiv, i_dw=8, **kwargs)

        def ser_ddr(phase=0, **kwargs):
            # for simulation we require sys8x_ddr clock (=sys16x)
            clkdiv = {0: "sys8x_ddr", 90: "sys8x_90_ddr"}[phase]
            # clk = {0: "sys", 90: "sys_11_25"}[phase]
            clk = {0: "sys", 90: "sys"}[phase]
            add_reset_value(phase, kwargs)
            serialize(clk=clk, clkdiv=clkdiv, i_dw=16, **kwargs)

        def des_ddr(phase=0, **kwargs):
            clkdiv = {0: "sys8x_ddr", 90: "sys8x_90_ddr"}[phase]
            clk = {0: "sys", 90: "sys_11_25"}[phase]
            add_reset_value(phase, kwargs)
            deserialize(clk=clk, clkdiv=clkdiv, o_dw=16, **kwargs)

        # Clock is shifted 180 degrees to get rising edge in the middle of SDR signals.
        # To achieve that we send negated clock on clk_p and non-negated on clk_n.
        ser_ddr(i=~self.ck_clk,    o=self.pads.clk_p,   name='clk_p')
        ser_ddr(i=self.ck_clk,     o=self.pads.clk_n,   name='clk_n')

        ser_sdr(i=self.ck_cke,     o=self.pads.cke,     name='cke')
        ser_sdr(i=self.ck_odt,     o=self.pads.odt,     name='odt')
        ser_sdr(i=self.ck_reset_n, o=self.pads.reset_n, name='reset_n')

        # Command/address
        ser_sdr(i=self.ck_cs,      o=self.pads.cs,      name='cs')
        for i in range(6):
            ser_sdr(i=self.ck_ca[i], o=self.pads.ca[i], name=f'ca{i}')

        # Tristate I/O (separate for simulation)
        for i in range(self.databits//8):
            ser_ddr(i=self.ck_dmi_o[i], o=self.pads.dmi_o[i], name=f'dmi_o{i}')
            des_ddr(o=self.ck_dmi_i[i], i=self.pads.dmi[i],   name=f'dmi_i{i}')
            ser_ddr(i=self.ck_dqs_o[i], o=self.pads.dqs_o[i], name=f'dqs_o{i}', phase=90)
            des_ddr(o=self.ck_dqs_i[i], i=self.pads.dqs[i],   name=f'dqs_i{i}', phase=90)
        for i in range(self.databits):
            ser_ddr(i=self.ck_dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}')
            des_ddr(o=self.ck_dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}')
        # Output enable signals
        self.comb += self.pads.dmi_oe.eq(delayed(self, self.dmi_oe, cycles=Serializer.LATENCY))
        self.comb += self.pads.dqs_oe.eq(delayed(self, self.dqs_oe, cycles=Serializer.LATENCY))
        self.comb += self.pads.dq_oe.eq(delayed(self, self.dq_oe, cycles=Serializer.LATENCY))


class Serializer(Module):
    """Serialize given input signal

    It latches the input data on the rising edge of `clk`. Output data counter `cnt` is incremented
    on rising edges of `clkdiv` and it determines current slice of `i` that is presented on `o`.
    `latency` is specified in `clk` cycles.

    NOTE: both `clk` and `clkdiv` should be phase aligned.
    NOTE: `reset_value` is set to `ratio - 1` so that on the first clock edge after reset it is 0
    """
    LATENCY = 1

    def __init__(self, clk, clkdiv, i_dw, o_dw, i=None, o=None, reset=None, reset_value=-1, name=None):
        assert i_dw > o_dw
        assert i_dw % o_dw == 0
        ratio = i_dw // o_dw

        sd_clk = getattr(self.sync, clk)
        sd_clkdiv = getattr(self.sync, clkdiv)

        if i is None: i = Signal(i_dw)
        if o is None: o = Signal(o_dw)
        if reset is None: reset = Signal()

        self.i = i
        self.o = o
        self.reset = reset

        if reset_value < 0:
            reset_value = ratio + reset_value

        cnt = Signal(max=ratio, reset=reset_value, name='{}_cnt'.format(name) if name is not None else None)
        sd_clkdiv += If(reset | cnt == ratio - 1, cnt.eq(0)).Else(cnt.eq(cnt + 1))

        i_d = Signal.like(self.i)
        sd_clk += i_d.eq(self.i)
        i_array = Array([i_d[n*o_dw:(n+1)*o_dw] for n in range(ratio)])
        self.comb += self.o.eq(i_array[cnt])


class Deserializer(Module):
    """Deserialize given input signal

    Latches the input data on the rising edges of `clkdiv` and stores them in the `o_pre` buffer.
    Additional latency cycle is used to ensure that the last input bit is deserialized correctly.

    NOTE: both `clk` and `clkdiv` should be phase aligned.
    NOTE: `reset_value` is set to `ratio - 1` so that on the first clock edge after reset it is 0
    """
    LATENCY = 2

    def __init__(self, clk, clkdiv, i_dw, o_dw, i=None, o=None, reset=None, reset_value=-1, name=None):
        assert i_dw < o_dw
        assert o_dw % i_dw == 0
        ratio = o_dw // i_dw

        sd_clk = getattr(self.sync, clk)
        sd_clkdiv = getattr(self.sync, clkdiv)

        if i is None: i = Signal(i_dw)
        if o is None: o = Signal(o_dw)
        if reset is None: reset = Signal()

        self.i = i
        self.o = o
        self.reset = reset

        if reset_value < 0:
            reset_value = ratio + reset_value

        cnt = Signal(max=ratio, reset=reset_value, name='{}_cnt'.format(name) if name is not None else None)
        sd_clkdiv += If(reset, cnt.eq(0)).Else(cnt.eq(cnt + 1))

        o_pre = Signal.like(self.o)
        o_array = Array([o_pre[n*i_dw:(n+1)*i_dw] for n in range(ratio)])
        sd_clkdiv += o_array[cnt].eq(self.i)
        # we need to ensure that the last bit will be correct if clocks are phase aligned
        o_pre_d = Signal.like(self.o)
        sd_clk += o_pre_d.eq(o_pre)
        sd_clk += self.o.eq(Cat(o_pre_d[:-1], o_pre[-1]))  # would work as self.comb (at least in simulation)
