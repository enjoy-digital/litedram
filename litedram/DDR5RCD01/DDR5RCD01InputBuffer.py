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
from litedram.DDR5RCD01.RCD_interfaces import *
from litedram.DDR5RCD01.RCD_utils import *


class DDR5RCD01InputBuffer(Module):
    """DDR5 RCD01 Input Buffer
    TODO Review
    The input buffer comprises:
      - The analog comparator (with Vref)
      - DFE, most notably the slicer
    The analog blocks may only be modelled as delays, however current 
    implementation is just a pass-through. TODO Add input buffer timing
    constraints (delays).
    The output of the input buffer is an equivalent of the "at the slicer 
    output/after slicer" specification term.

    Module
    ------
    if_ib_i - Input interface {dcs_n,dca_n,dpar}
    if_ib_o - Output interface {dcs_n,dca_n,dpar}
    if_ctrl - Control interface {en}
    ------
    """

    def __init__(self, if_ib_i, if_ib_o, if_ctrl):
        # Pass-through
        self.comb += If(if_ctrl.en,
                        if_ib_o.dcs_n.eq(if_ib_i.dcs_n),
                        if_ib_o.dca.eq(if_ib_i.dca),
                        if_ib_o.dpar.eq(if_ib_i.dpar)
                        ).Else(
            if_ib_o.dcs_n.eq(0x00),
            if_ib_o.dca.eq(0x00),
            if_ib_o.dpar.eq(0x00))


class TestBed(Module):
    def __init__(self):
        #
        self.if_ib_i = If_channel_ibuf()
        self.if_ib_o = If_channel_ibuf()
        self.if_ctrl = If_ctrl_ibuf()
        ###
        self.submodules.dut = DDR5RCD01InputBuffer(
            if_ib_i=self.if_ib_i, if_ib_o=self.if_ib_o, if_ctrl=self.if_ctrl)
        # print(verilog.convert(self.dut))


def run_test(tb):
    logging.debug('Write test')
    yield from behav_write_word(0x00, 0x00, 0x0)
    yield from behav_write_word(0x01, 0x01, 0x1)
    yield from write_ctrl(1)
    yield from behav_write_word(0x02, 0x02, 0x0)
    yield from behav_write_word(0x03, 0x03, 0x0)
    yield from behav_write_word(0x00, 0x04, 0x1)

    logging.debug('Yield from write test.')


def write_ctrl(d):
    yield tb.if_ctrl.en.eq(d)


def behav_write_word(d_dcs, d_dca, d_dpar):
    yield tb.if_ib_i.dcs_n.eq(d_dcs)
    yield tb.if_ib_i.dca.eq(d_dca)
    yield tb.if_ib_i.dpar.eq(d_dpar)
    yield


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
