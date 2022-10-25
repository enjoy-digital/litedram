#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020-2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.fhdl.specials import Tristate

from litex.soc.interconnect.csr import CSR

from litedram.phy.rpc.basephy import BasePHY


class SimulationPHY(BasePHY):
    def __init__(self, *args, generate_read_data=True, **kwargs):
        kwargs.update(dict(
            write_ser_latency = 1,
            read_des_latency  = 0,
            phytype           = "RPC" + self.__class__.__name__,
        ))
        super().__init__(*args, **kwargs)

        self.generate_read_data = generate_read_data

        # fake delays (make no nsense in simulation, but sdram.c expects them)
        self.settings.read_leveling = True
        self.settings.delays = 1
        self._rdly_dq_rst = CSR()
        self._rdly_dq_inc = CSR()

        # For simulation purpose (serializers/deserializers)
        self.sd_ddr_90  = getattr(self.sync, "sys4x_90_ddr")
        self.sd_ddr_180 = getattr(self.sync, "sys4x_180_ddr")

    def do_clock_serialization(self, clk_1ck_out, clk_p, clk_n):
        ser = Serializer(self.sync, self.sd_ddr_180, clk_1ck_out, delay=1)
        self.submodules += ser
        self.comb += clk_p.eq(ser.o)
        self.comb += clk_n.eq(~ser.o)

    def do_stb_serialization(self, stb_1ck_out, stb):
        ser = Serializer(self.sync, self.sd_ddr_90, stb_1ck_out, delay=1)
        self.submodules += ser
        self.comb += stb.eq(ser.o)

    def do_dqs_serialization(self, dqs_1ck_out, dqs_1ck_in, dqs_oe, dqs_p, dqs_n):
        # Delay dqs_oe by 1 cycle (Serializer latency) and register it on output domain
        dqs_oe_d   = Signal()
        dqs_oe_cdc = Signal()
        self.sync += dqs_oe_d.eq(dqs_oe)
        self.sync.sys4x_180 += dqs_oe_cdc.eq(dqs_oe_d)

        for i in range(len(dqs_p)):
            dqs_out = Signal()
            dqs_in  = Signal()  # TODO: use it for reading

            ser = Serializer(self.sync, self.sd_ddr_180, dqs_1ck_out, delay=1)
            self.submodules += ser
            self.comb += dqs_out.eq(ser.o)

            if i == 0:
                des = Deserializer(self.sd_ddr_180, dqs_in, dqs_1ck_in)
                self.submodules += des

            # self.specials += Tristate(dqs_p[i],  dqs_out, dqs_oe_cdc, dqs_in)
            # self.specials += Tristate(dqs_n[i], ~dqs_out, dqs_oe_cdc)
            self.comb += [
                If(dqs_oe_cdc,
                    dqs_p[i].eq(dqs_out),
                    dqs_n[i].eq(~dqs_out),
                ),
                dqs_in.eq(dqs_p[i]),
            ]

    def do_db_serialization(self, db_1ck_out, db_1ck_in, db_oe, db):
        if self.generate_read_data:
            # Dummy read data generator for simulation purpose
            dq_in_dummy = Signal(self.databits)
            gen = DummyReadGenerator(dq_in=db, dq_out=dq_in_dummy, stb_in=self.pads.stb,
                                     cl=self.settings.cl)
            self.submodules += ClockDomainsRenamer({"sys": "sys4x_180_ddr"})(gen)

        # Delay db_oe by 1 cycle (Serializer latency) and register it on output domain
        db_oe_d   = Signal()
        db_oe_cdc = Signal()
        self.sync += db_oe_d.eq(db_oe)
        self.sync.sys4x_90 += db_oe_cdc.eq(db_oe_d)

        for i in range(self.databits):
            # To/from tristate
            dq_out = Signal()
            dq_in = Signal()

            ser = Serializer(self.sync, self.sd_ddr_90, db_1ck_out[i], delay=1)
            self.submodules += ser
            self.comb += dq_out.eq(ser.o)

            # Use sd_ddr_90 in simulation, in general leveling would be needed.
            if self.generate_read_data:
                des = Deserializer(self.sd_ddr_90, dq_in_dummy[i], db_1ck_in[i])
            else:
                des = Deserializer(self.sd_ddr_90, dq_in, db_1ck_in[i])
            self.submodules += des

            # self.specials += Tristate(db[i], dq_out, db_oe_cdc, dq_in)
            self.comb += [
                If(db_oe_cdc, db[i].eq(dq_out)),
                dq_in.eq(db[i]),
            ]

    def do_cs_serialization(self, cs_n_1ck_out, cs_n):
        ser = Serializer(self.sync, self.sd_ddr_90, cs_n_1ck_out, delay=1)
        self.submodules += ser
        self.comb += cs_n.eq(ser.o)

# Simulation of READ ouput -------------------------------------------------------------------------

class DummyReadGenerator(Module):
    def __init__(self, stb_in, dq_in, dq_out, cl):
        # self.sync should be a 4x DDR clock phase-aligned with CLK

        data_counter = Signal(max=16)
        cmd_counter = Signal(max=16)
        # count STB zeros, 2 full-rate cycles (4 DDR) mean STB preamble, but more mean RESET
        stb_zero_counter = Signal(max=4 + 2)
        self.sync += \
            If(stb_in == 0,
                If(stb_zero_counter != 2**len(stb_zero_counter) - 1,
                    stb_zero_counter.eq(stb_zero_counter + 1)
                )
            ).Else(
                stb_zero_counter.eq(0)
            )

        # Because the generator clock domain is phase shifted in relation to DB, we have to
        # register the value to hold it until the end of our clock, so that we get correct FSM
        # transitions
        # FIXME: would cause problems if clocks were aligned
        dq_in_r = Signal.like(dq_in)
        self.sync += dq_in_r.eq(dq_in)

        # generate DQS just for viewing signal dump
        dqs_out = Signal()
        dqs_oe  = Signal()

        data = Array([
            0x0000,  # 0x0110,
            0x1111,  # 0x1221,
            0x2222,  # 0x2332,
            0x3333,  # 0x3443,
            0x4444,  # 0x4554,
            0x5555,  # 0x5665,
            0x6666,  # 0x6776,
            0x7777,  # 0x7887,
            0x8888,  # 0x8998,
            0x9999,  # 0x9aa9,
            0xaaaa,  # 0xabba,
            0xbbbb,  # 0xbccb,
            0xcccc,  # 0xcddc,
            0xdddd,  # 0xdeed,
            0xeeee,  # 0xeffe,
            0xffff,  # 0xf00f,
        ])

        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            NextValue(data_counter, 0),
            If(stb_zero_counter == 4,
                NextState("CHECK_CMD_P")
            )
        )
        fsm.act("CHECK_CMD_P",
            If(dq_in_r[:3] == 0,
                NextState("CHECK_CMD_N")
            ).Else(
                NextState("IDLE")
            )
        )
        fsm.act("CHECK_CMD_N",
            If(dq_in_r[0] == 0,
                NextState("CL_WAIT")
            ).Else(
                NextState("IDLE")
            )
        )
        # 2x for DDR, -1 for CHECK_CMD_*, -2 for preamble
        fsm.delayed_enter("CL_WAIT", "PREAMBLE_P", 2*(cl - 1) - 2)
        fsm.act("PREAMBLE_P",
            dqs_oe.eq(1),
            dqs_out.eq(0),
            NextState("PREAMBLE_N")
        )
        fsm.act("PREAMBLE_N",
            dqs_oe.eq(1),
            dqs_out.eq(0),
            NextState("SEND_DATA")
        )
        fsm.act("SEND_DATA",
            dqs_oe.eq(1),
            dqs_out.eq(data_counter[0] == 0),
            dq_out.eq(data[data_counter + cmd_counter]),
            NextValue(data_counter, data_counter + 1),
            If(data_counter == 16 - 1,
                NextValue(cmd_counter, cmd_counter + 1),
                NextState("IDLE")
            )
        )

# I/O Primitives -----------------------------------------------------------------------------------

class Serializer(Module):
    """Serialize input signals into one output with 1 sd_clk clock latency"""
    def __init__(self, sd_clk, sd_clkdiv, inputs, reset=0, name=None, delay=0):
        # `delay` must be used to get correct data_cntr=0 for phase delayed signals
        assert(len(inputs) > 0)
        assert(len(s) == len(inputs[0]) for s in inputs)

        data_width = len(inputs)
        signal_width = len(inputs[0])
        cntr_max = 2 * data_width

        if not isinstance(inputs, Array):
            inputs = Array(inputs)

        self.o = Signal(signal_width)
        data_cntr = Signal(max=cntr_max, name=name, reset=(0 - delay) % cntr_max)
        sd_clkdiv += If(reset, data_cntr.eq(0)).Else(data_cntr.eq(data_cntr+1))

        # If we used inputs combinatorically, then we will have a problem when the serialization
        # clock is not phase-aligned with the `inputs` clock, e.g.
        #  inputs clk 1:      | 0 : 1 : 2 : 3 | 4 : 5 : 6 : 7 |
        #  serialized 90 deg:   | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
        # Here input 3 becomes invalid before serialized output moves to 4, so it would actually
        # send 3 for the 1st half and 7 for the 2nd half. To avoid this we introduce 1 clock
        # latency of the inputs and use 2 registers to hold the values of subsequent inputs.
        inputs_cnt = Signal()
        inputs_d   = Array([Signal.like(i) for i in [*inputs, *inputs]])
        sd_clk += [
            inputs_cnt.eq(inputs_cnt + 1),
            Case(inputs_cnt, {
                0: [i_d.eq(i) for i_d, i in zip(inputs_d[data_width:], inputs)],
                1: [i_d.eq(i) for i_d, i in zip(inputs_d[:data_width], inputs)],
            })
        ]

        self.comb += self.o.eq(inputs_d[data_cntr])


class Deserializer(Module):
    """Deserialize an input signal into outputs in the `sd` clock domain"""
    def __init__(self, sd, input, outputs, reset=0, name=None):
        assert(len(outputs) > 0)
        assert(len(s) == len(outputs[0]) for s in outputs)
        assert(len(outputs[0]) == len(input))

        data_width = len(outputs)
        signal_width = len(outputs[0])

        if not isinstance(outputs, Array):
            outputs = Array(outputs)

        data_cntr = Signal(log2_int(data_width), name=name)
        sd += If(reset, data_cntr.eq(0)).Else(data_cntr.eq(data_cntr+1))
        sd += outputs[data_cntr].eq(input)
