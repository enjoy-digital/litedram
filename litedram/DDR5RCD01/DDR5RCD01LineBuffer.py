#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# Python
from random import randrange
import logging
# migen
from migen import *
from migen.fhdl import verilog
# Litex
from litedram.DDR5RCD01.RCD_definitions import *
from litedram.DDR5RCD01.RCD_utils import *
from litedram.DDR5RCD01.RCD_interfaces import *


class DDR5RCD01LineBuffer(Module):
    """DDR5 RCD01 Line Buffer
    TODO Documentation
    This module servers 3 purposes:
      1. Deserialize the 2UI into 1 UI
      2. Model the latency from the input buffer to the output buffer. It's a constant delay
      is estimated from:
        - analog input buffer delay
        - time required for internal control, register file accesses, etc.
        - analog output buffer delay
      Currently, rcd_t_prop_delay_nck is set to 1, but this may be a subject of change.
      3. Latency Equalization Support
      Model the latency equalization, which is a programmable feature of additionally
      delaying the output by nCK, n={0,1,2,3,4}

    Module
    ------
    d               - Input interface {dcs_n, dca_n}
    q               - Output interface {qcs_n, qca_n}
    c               - Config interface {sel_latency_add}

    sel_latency_add - Input : Select added latency (3 bits should be enough)
    ------
    Parameters
    rcd_t_prop_delay_nck : Constant time delay, expressed in clock periods
      Expected value : 1
                 Min : 1
                 Max : n/a
    rcd_t_eq_latency_nck_max : Maximum value of programmable time
    delay (latency equalization), expressed in clock periods
      Expected value : 4
    """

    def __init__(self, if_i, if_o, if_ctrl, rcd_t_prop_delay_nck=1, rcd_t_eq_latency_nck_max=4):

        len_dcs_n = len(if_i.dcs_n)
        len_dca = len(if_i.dca)
        len_qca = 2*len_dca

        # Deserializer
        # TODO Should The Deserializer also perform the dcs sync for different modes SDR,DDR??
        deser_qca = Signal(len_qca)
        deser_qcs_n = Signal(len_dcs_n)
        xdeser_dca = Deserializer_2_to_1(d=if_i.dca,
                                         d_en=if_ctrl.deser_ca_d_en,
                                         q=deser_qca,
                                         q_en=if_ctrl.deser_ca_q_en,
                                         sel=if_ctrl.deser_sel_lower_upper)
        self.submodules += xdeser_dca

        xdeser_dcs_n = Deserializer_2_to_1(d=if_i.dcs_n,
                                           d_en=if_ctrl.deser_cs_n_d_en,
                                           q=deser_qcs_n,
                                           q_en=if_ctrl.deser_cs_n_q_en,
                                           sel=0)

        self.submodules += xdeser_dcs_n

        # TODO Check if both ranks get the same values

        # d_const_delay = Array(Signal(len_dcs_n)
        #                       for y in range(rcd_t_prop_delay_nck))
        # Static delay
        sta_qcs_n = Signal(len_dcs_n)
        static_delay_qcs = StaticDelay(
            d=deser_qcs_n, q=sta_qcs_n, delay=rcd_t_prop_delay_nck)
        self.submodules.static_delay_qcs = static_delay_qcs

        sta_qca = Signal(len_qca)
        static_delay_qca = StaticDelay(
            deser_qca, sta_qca, delay=rcd_t_prop_delay_nck)
        self.submodules.static_delay_qca = static_delay_qca

        # Programmable delay
        prog_qcs_n = Signal(len_dcs_n)
        prog_delay_qcs = ProgDelay(
            sta_qcs_n, prog_qcs_n, if_ctrl.sel_latency_add, delay_prog_max=rcd_t_eq_latency_nck_max)
        self.submodules.prog_delay_qcs = prog_delay_qcs

        prog_qca = Signal(len_qca)
        prog_delay_qca = ProgDelay(
            sta_qca, prog_qca, if_ctrl.sel_latency_add, delay_prog_max=rcd_t_eq_latency_nck_max)
        self.submodules.prog_delay_qca = prog_delay_qca
        # breakpoint()

        self.comb += if_o.qacs_a_n.eq(prog_qcs_n)
        self.comb += if_o.qaca_a.eq(prog_qca)

        self.comb += if_o.qacs_b_n.eq(prog_qcs_n)
        self.comb += if_o.qaca_b.eq(prog_qca)


class Deserializer_2_to_1(Module):
    """
    The incoming stream of DCAs of width 7 must be serialized into 14 bits, c.f. Table 8
    UI DCA0 DCA1 DCA2 DCA3 DCA4 DCA5 DCA6
    0  QCA0 QCA1 QCA2 QCA3 QCA4 QCA5 QCA6
    1  QCA7 QCA8 QCA9 QCAA QCAB QCAC QCAD

    First UI (number 0) goes to the lower part of the word QCA[6:0]
    Second UI (number 1) goes to the upper part of the word QCA[13:7]

    DCA -> Demux -> D -> D--> QCA[6:0]
                 -> D ------> QCA[13:7]
    Module
    ------
    d - input
    sel_lower_upper - Select where the word goes
    q - output

    Parameters
    ----------
    d_w - bit width of d

    Local Parameters
    ---------------
    q_w - Assumed double the width of d_w
    """

    def __init__(self, d, d_en, q, q_en, sel, d_w=7):

        d_lower = Signal(d_w)
        d_upper = Signal(d_w)

        self.sync += If(
            d_en,
            If(sel,
                d_upper.eq(d),
               ).Else(
                d_lower.eq(d)
            )
        )

        self.sync += If(
            q_en,
            q.eq(Cat(d_lower, d_upper))
        ).Else(
            If(~d_en,
               q.eq(~0)
               )
        )


class StaticDelay(Module):
    """
    Q signal is the D signal delayed by 'delay' clocks

    Module
    ------
    d - input
    q - output

    Parameters
    ----------
    delay - number of clocks to delay
    """

    def __init__(self, d, q, delay=1):
        len_d = len(d)
        d_const_delay = Array(Signal(len_d) for y in range(delay))
        # rcd_t_prop_delay is modelled with a set of series registers
        # d-d-d-d-d-...-d
        debug_string = "In --> "
        for i in range(delay):
            debug_string = debug_string + " [D] --> "
            if i == 0:
                self.sync += d_const_delay[0].eq(d)
            else:
                self.sync += d_const_delay[i].eq(d_const_delay[i-1])
        debug_string = debug_string + " q_int --> mux_i "
        logging.debug(debug_string)
        # Last register is then at index rcd_t_prop_delay_nck-1
        id_last = delay-1
        # Drive output
        self.comb += q.eq(d_const_delay[id_last])


class ProgDelay(Module):
    """
    Programmable delay
    Create a path for each delayed signal?
    0-4 possible outputs
    """

    def __init__(self, d, q, sel_latency_add, delay_prog_max=4):

        d_prog_delay_num = delay_prog_max+1
        len_d = len(d)
        mux_i = Array(Signal(len_d) for y in range(d_prog_delay_num))

        for i in range(d_prog_delay_num):
            logging.debug("%d-delay path", i)
            debug_string = "mux_i --> "
            d_prog_delay = Array(Signal(len_d) for y in range(i))
            if i == 0:
                self.comb += mux_i[i].eq(d)
            for j in range(i):
                debug_string = debug_string + " [D]int_"+str(j)+" --> "
                # Connect the first signal
                if j == 0:
                    self.sync += d_prog_delay[0].eq(d)
                # Series connect
                else:
                    self.sync += d_prog_delay[j].eq(d_prog_delay[j-1])
                # Connect to the mux
                if j == (i-1):
                    self.comb += mux_i[i].eq(d_prog_delay[j])
            debug_string = debug_string + " --> mux_o "
            logging.debug(debug_string)
        # Create a dictionary: mux_select: mux_inputs
        mux_dict = {}
        mux_o = Signal(len_d)
        for i in range(d_prog_delay_num):
            mux_dict[i] = mux_o.eq(mux_i[i])
        self.comb += Case(sel_latency_add, mux_dict)
        self.comb += q.eq(mux_o)


class TestBed(Module):
    def __init__(self):
        
        self.ctrl_if = If_ctrl_lbuf()
        self.iif = If_channel_ibuf()
        self.oif = If_channel_obuf_csca()

        self.submodules.dut = DDR5RCD01LineBuffer(
            self.iif, self.oif, self.ctrl_if)
        # print(verilog.convert(self.dut))


def run_test(dut):
    logging.debug('Write test')
    yield from behav_rst()
    pattern_dcs = [0x00, 0x01, 0x02, 0x03, 0x00]
    pattern_dca = [0x5A, 0xA5, 0x0A, 0x0B, 0x0C]
    pattern = list(zip(pattern_dcs, pattern_dca))
    logging.debug("Test [DCS,DCA] pattern: " + str(pattern))
    yield
    yield from write_set_pattern(pattern)
    yield
    yield from write_random_pattern()
    yield
    yield from sweep_mux()
    yield
    logging.debug('Yield from write test.')


def behav_rst():
    yield tb.iif.dcs_n.eq(1)
    yield tb.iif.dca.eq(0)
    yield tb.ctrl_if.sel_latency_add.eq(0)
    yield tb.ctrl_if.deser_sel_lower_upper.eq(0)
    yield tb.ctrl_if.deser_ca_d_en.eq(0)
    yield tb.ctrl_if.deser_ca_q_en.eq(0)


def behav_write_word(dcs_n, dca_n):
    yield tb.iif.dcs_n.eq(dcs_n)
    yield tb.iif.dca.eq(dca_n)
    yield


def write_random_pattern():
    bits = [randrange(2) for y in range(10)]
    logging.debug('random pattern = '+str(bits))
    for bit in bits:
        yield from behav_write_word(bit, bit)


def write_set_pattern(pattern):
    even = True
    for word_dcs, word_dca in pattern:
        yield tb.ctrl_if.deser_ca_d_en.eq(1)
        yield tb.ctrl_if.deser_ca_q_en.eq(1)
        if even:
            yield tb.ctrl_if.deser_sel_lower_upper.eq(0)
        else:
            yield tb.ctrl_if.deser_sel_lower_upper.eq(1)
        even = not even

        yield from behav_write_word(word_dcs, word_dca)
        yield tb.ctrl_if.deser_ca_d_en.eq(0)
        yield tb.ctrl_if.deser_ca_q_en.eq(0)


def sweep_mux(rcd_t_eq_latency_nck_max=4):
    for i in range(rcd_t_eq_latency_nck_max+1):
        yield tb.ctrl_if.sel_latency_add.eq(i)
        yield


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
