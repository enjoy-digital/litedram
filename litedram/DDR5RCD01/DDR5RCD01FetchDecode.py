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


class DDR5RCD01FetchDecode(Module):
    """DDR5 RCD01 
    TODO this module is a draft, currently unused, untested
    """

    def __init__(self, if_ib_i, if_ib_o, if_ctrl):

        xfsm_cslogic = FSM(reset_state="RESET")
        self.submodules += xfsm_cslogic

        deser_latch = Signal(7)
        deser_en = Signal()
        xfsm_cslogic.act(
            "RESET",
            If(
                if_ctrl.en,
                NextState("IDLE")
            )
        )

        xfsm_cslogic.act(
            "IDLE",
            If(
                if_ib_i.dcs_n == 0x00,
                NextValue(deser_latch, if_ib_i.dca),
                deser_en.eq(1),
                NextState("S_0a")
            ).Else(
                deser_en.eq(0),
            )
        )
        xfsm_cslogic.act(
            "S_0a",
            NextValue(deser_latch, if_ib_i.dca),
            deser_en.eq(1),
            NextState("S_0b")
        )
        xfsm_cslogic.act(
            "S_0b",
            NextValue(deser_latch, if_ib_i.dca),
            deser_en.eq(1),
            NextState("S_1a")
        )
        xfsm_cslogic.act(
            "S_1a",
            NextValue(deser_latch, if_ib_i.dca),
            deser_en.eq(1),
            NextState("S_1b")
        )
        xfsm_cslogic.act(
            "S_1b",
            NextValue(deser_latch, if_ib_i.dca),
            deser_en.eq(0),
            NextState("IDLE")
        )

        # Debug information
        xfsm_debug_state = Signal(4)
        state_names = ["RESET", "IDLE", "S_0a", "S_0b", "S_1a", "S_1b"]
        for id, state_name in enumerate(state_names):
            self.comb += If(xfsm_cslogic.ongoing(state_name),
                            xfsm_debug_state.eq(id))


class TestBed(Module):
    def __init__(self):

        self.if_ib_i = If_channel_ibuf()
        self.if_ib_o = If_channel_ibuf()
        self.if_ctrl = If_ctrl_ibuf()

        self.submodules.dut = DDR5RCD01FetchDecode(
            if_ib_i=self.if_ib_i, if_ib_o=self.if_ib_o, if_ctrl=self.if_ctrl)
        # print(verilog.convert(self.dut))


def run_test(tb):
    logging.debug('Write test')
    yield from write_ctrl(tb, 0)
    yield from behav_write_word(tb, 0x11, 0x00, 0x0)
    yield from write_ctrl(tb, 1)
    for i in range(7):
        yield
    yield from behav_write_word(tb, 0x00, 0x0a, 0x1)
    yield from behav_write_word(tb, 0x11, 0x0b, 0x1)
    yield from behav_write_word(tb, 0x11, 0x1a, 0x1)
    yield from behav_write_word(tb, 0x11, 0x1b, 0x1)
    yield from behav_write_word(tb, 0x11, 0x00, 0x0)
    for i in range(2):
        yield
    logging.debug('Yield from write test.')


def write_ctrl(tb, d):
    yield tb.if_ctrl.en.eq(d)


def behav_write_word(tb, d_dcs, d_dca, d_dpar):
    yield tb.if_ib_i.dcs_n.eq(d_dcs)
    yield tb.if_ib_i.dca.eq(d_dca)
    yield tb.if_ib_i.dpar.eq(d_dpar)
    yield


if __name__ == "__main__":
    eT = EngTest()
    raise NotImplementedError("The test of this block is to be done.")
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
