#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# Python
import logging
# migen
from migen import *
from migen.fhdl import verilog
# Litex
from litedram.DDR5RCD01.RCD_definitions import *
from litedram.DDR5RCD01.RCD_utils import *
from litedram.DDR5RCD01.RCD_interfaces import *


class DDR5RCD01OutputBuffer(Module):
    """DDR5 RCD01 Output Buffer
    TODO Documentation
    d         - Input : data
    oe        - Input : output enable
    o_inv_en  - Input : output inversion enable
    frac_p    - Input : Fractional (n/64) phase delay select; frac_p==0 -> no delay
    q         - Output: data
    # Driver strength is not on implementation list, also: slew rate control
    """

    def __init__(self, if_i_csca, if_i_clks, if_o_csca, if_o_clks, if_ctrl, sig_disable_level=1):
        # Hook inputs

        # Output
        # Top Row QACS QACA
        xoutbuf_qacs_a_n = OutBuf(if_i_csca.qacs_a_n, if_o_csca.qacs_a_n, if_ctrl.oe_qacs_a_n,
                                  if_ctrl.o_inv_en_qacs_a_n,  sig_disable_level=1)
        self.submodules += xoutbuf_qacs_a_n
        xoutbuf_qaca_a = OutBuf(if_i_csca.qaca_a, if_o_csca.qaca_a,
                                if_ctrl.oe_qaca_a, if_ctrl.o_inv_en_qaca_a)
        self.submodules += xoutbuf_qaca_a
        # Bottom Row
        xoutbuf_qacs_b_n = OutBuf(if_i_csca.qacs_b_n, if_o_csca.qacs_b_n, if_ctrl.oe_qacs_b_n,
                                  if_ctrl.o_inv_en_qacs_b_n,  sig_disable_level=1)
        self.submodules += xoutbuf_qacs_b_n
        xoutbuf_qaca_b = OutBuf(if_i_csca.qaca_b, if_o_csca.qaca_b,
                                if_ctrl.oe_qaca_b, if_ctrl.o_inv_en_qaca_b)
        self.submodules += xoutbuf_qaca_b

        # Clock A
        xoutbuf_qack_t = OutBuf(if_i_clks.qack_t, if_o_clks.qack_t,
                                if_ctrl.oe_qack_t, if_ctrl.o_inv_en_qack_t)
        self.submodules += xoutbuf_qack_t
        xoutbuf_qack_c = OutBuf(if_i_clks.qack_c, if_o_clks.qack_c,
                                if_ctrl.oe_qack_c, if_ctrl.o_inv_en_qack_c)
        self.submodules += xoutbuf_qack_c
        # Clock B
        xoutbuf_qbck_t = OutBuf(if_i_clks.qbck_t, if_o_clks.qbck_t,
                                if_ctrl.oe_qbck_t, if_ctrl.o_inv_en_qbck_t)
        self.submodules += xoutbuf_qbck_t
        xoutbuf_qbck_c = OutBuf(if_i_clks.qbck_c, if_o_clks.qbck_c,
                                if_ctrl.oe_qbck_c, if_ctrl.o_inv_en_qbck_c)
        self.submodules += xoutbuf_qbck_c
        # Clock C
        xoutbuf_qcck_t = OutBuf(if_i_clks.qcck_t, if_o_clks.qcck_t,
                                if_ctrl.oe_qcck_t, if_ctrl.o_inv_en_qcck_t)
        self.submodules += xoutbuf_qcck_t
        xoutbuf_qcck_c = OutBuf(if_i_clks.qcck_c, if_o_clks.qcck_c,
                                if_ctrl.oe_qcck_c, if_ctrl.o_inv_en_qcck_c)
        self.submodules += xoutbuf_qcck_c
        # Clock D
        xoutbuf_qdck_t = OutBuf(if_i_clks.qdck_t, if_o_clks.qdck_t,
                                if_ctrl.oe_qdck_t, if_ctrl.o_inv_en_qdck_t)
        self.submodules += xoutbuf_qdck_t
        xoutbuf_qdck_c = OutBuf(if_i_clks.qdck_c, if_o_clks.qdck_c,
                                if_ctrl.oe_qdck_c, if_ctrl.o_inv_en_qdck_c)
        self.submodules += xoutbuf_qdck_c

        # TODO Implement fractional delay here
        # If frac_p == xx, delay the clock by yy


class OutBuf(Module):
    """ TODO documentation
    """

    def __init__(self, d, q, oe, o_inv_en, sig_disable_level=0):
        self.comb += If(oe,
                        If(o_inv_en,
                           q.eq(~d)
                           ).Else(q.eq(d))
                        ).Else(q.eq(sig_disable_level))


class TestBed(Module):
    def __init__(self):

        self.ctrl_if = If_ctrl_obuf()
        self.iif_csca = If_channel_obuf_csca()
        self.iif_clks = If_channel_obuf_clks()
        self.oif_csca = If_channel_obuf_csca()
        self.oif_clks = If_channel_obuf_clks()

        self.submodules.dut = DDR5RCD01OutputBuffer(
            self.iif_csca, self.iif_clks, self.oif_csca, self.oif_clks, self.ctrl_if)
        # print(verilog.convert(self.dut))


def run_test(dut):
    logging.debug('Write test')
    yield from behav_rst(tb)
    yield
    yield from set_all_outs(tb, 1)
    yield
    yield from set_all_outs(tb, 0)
    yield
    yield from set_all_oe(tb, 1)
    yield
    yield from set_all_outs(tb, 1)
    yield
    yield from set_all_outs(tb, 0)
    yield
    yield from set_all_inv_en(tb, 1)
    yield
    yield from set_all_outs(tb, 1)
    yield
    yield from set_all_outs(tb, 0)
    yield

    logging.debug('Yield from write test.')


def set_all_inv_en(tb, b):
    yield tb.ctrl_if.o_inv_en_qacs_a_n.eq(b)
    yield tb.ctrl_if.o_inv_en_qaca_a.eq(b)
    yield tb.ctrl_if.o_inv_en_qacs_b_n.eq(b)
    yield tb.ctrl_if.o_inv_en_qaca_b.eq(b)
    yield tb.ctrl_if.o_inv_en_qack_t.eq(b)
    yield tb.ctrl_if.o_inv_en_qack_c.eq(b)
    yield tb.ctrl_if.o_inv_en_qbck_t.eq(b)
    yield tb.ctrl_if.o_inv_en_qbck_c.eq(b)
    yield tb.ctrl_if.o_inv_en_qcck_t.eq(b)
    yield tb.ctrl_if.o_inv_en_qcck_c.eq(b)
    yield tb.ctrl_if.o_inv_en_qdck_t.eq(b)
    yield tb.ctrl_if.o_inv_en_qdck_c.eq(b)


def set_all_oe(tb, b):
    yield tb.ctrl_if.oe_qacs_a_n.eq(b)
    yield tb.ctrl_if.oe_qaca_a.eq(b)
    yield tb.ctrl_if.oe_qacs_b_n.eq(b)
    yield tb.ctrl_if.oe_qaca_b.eq(b)
    yield tb.ctrl_if.oe_qack_t.eq(b)
    yield tb.ctrl_if.oe_qack_c.eq(b)
    yield tb.ctrl_if.oe_qbck_t.eq(b)
    yield tb.ctrl_if.oe_qbck_c.eq(b)
    yield tb.ctrl_if.oe_qcck_t.eq(b)
    yield tb.ctrl_if.oe_qcck_c.eq(b)
    yield tb.ctrl_if.oe_qdck_t.eq(b)
    yield tb.ctrl_if.oe_qdck_c.eq(b)


def set_all_outs(tb, b):
    yield tb.iif_csca.qacs_a_n.eq(b)
    yield tb.iif_csca.qaca_a.eq(b)
    yield tb.iif_csca.qacs_b_n.eq(b)
    yield tb.iif_csca.qaca_b.eq(b)
    yield tb.iif_clks.qack_t.eq(b)
    yield tb.iif_clks.qack_c.eq(b)
    yield tb.iif_clks.qbck_t.eq(b)
    yield tb.iif_clks.qbck_c.eq(b)
    yield tb.iif_clks.qcck_t.eq(b)
    yield tb.iif_clks.qcck_c.eq(b)
    yield tb.iif_clks.qdck_t.eq(b)
    yield tb.iif_clks.qdck_c.eq(b)


def behav_rst(tb):
    yield from set_all_inv_en(tb, 0)
    yield from set_all_oe(tb, 0)
    yield from set_all_outs(tb, 0)


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
