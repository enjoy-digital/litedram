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


class DDR5RCD01Loopback(Module):
    """DDR5 RCD01 Loopback
    TODO Documentation
    In order to enable loopback RW26 word must be set (select input).
    DFE Training Mode should not be used simultaneously

    transitions in the incoming data signal are aligned to the rising od the incoming strobe
    rcd will sample incoming data with the falling edge of the incoming strobe
    rcd will apply logic inversion in the outgoing strobe signal
    c.f figure 20

    RW26.0-2 select input source (external or internal)

    [EXTERNAL] RW26.6 signals are 1/4 or 1/2 rate
    The host is responsible for generation of these signals and timing requirements.
    I could not find explicit information on how these are generated. The remark
    'signals are 1/4 or 1/2 rate' is understood to mean 'the strobe and data signals
    are generated in the dck_t(c) domain at every other (every 4th) positive edge'
    As such if the loopback module uses the dck_t(c) signals we know the relationship
    betweend strobe signal and dck_t. They are aligned?


    [INTERNAL] RW26.3-5 internal RCD bit selection
    In the internal use case select which signal (dca0, dca1, ..., dca7, dpar) is selected
    Case(RW26.3-5, 0, d = dca0; 1, d = dca1;...)
    Signals dca,dpar are taken from the DFE slicer

    [INTERNAL] RW26.7 Phase select - A or B
    What is a phase? Phase select whether the signal is aligned with dck_t or dck_c
    PHASE_A => dck_t
    PHASE_B => dck_c
    Internal loopback uses the 'line' dck, not from PLL
    Internal use case is fixed at 1/2 rate.

    Module
    ------
    Inputs : possible sources of loopback. All ports come in pairs (data,strobe)
    [EXTERNAL USE CASE]
    dlbd_a, dlbs_a             - Channel A data and strobe
    dlbd_b, dlbs_b             - Channel B data and strobe
    [INTERNAL USE CASE]
    cha_dca_dfe, cha_dpar_dfe  - Channel A DFE Circuit data
    dck_t, dck_c               - Clock inputs are the strobes for the internal use case
    chb_dca_dfe, chb_dpar_dfe  - Channel B DFE Circuit data
    [CONFIG, c.f. RW26]
    sel_mode - Select disable,internal,external, A or B channel
    sel_phase_ab - Select phase (A or B)
    sel_int_bit - Select internal bit (DCA[6:0] or DPAR)


    Outputs: loopback data.
    qlbd_ab, qlbs_ab      - Loopback output data and strobe

    ------
    Parameters
    TIE_VALUE = {TIE_LOW, TIE_HIGH}. Should be evaluated to const 0 or const 1.
    TODO determine if i/o timings are to be kept in the model
    tDCK2QLBS - time delay from input to output. (migen can't evaluate it)
    """

    """
  @(negedge strobe)
    data <= d_in
  """

    def __init__(self,
                 if_ck,
                 if_host_lb,
                 if_rcd_lb,
                 if_sdram_A_lb,
                 if_sdram_B_lb,
                 if_channel_A_dfe_lb,
                 if_channel_B_dfe_lb,
                 if_ctrl_lb):

        #
        # Internal path
        #

        int_da = Signal()
        int_db = Signal()
        # Mux : select bit
        # breakpoint()
        self.comb += Case(if_ctrl_lb.sel_int_bit, {0: int_da.eq(if_channel_A_dfe_lb.dca_lb[0]),
                                                   1: int_da.eq(if_channel_A_dfe_lb.dca_lb[1]),
                                                   2: int_da.eq(if_channel_A_dfe_lb.dca_lb[2]),
                                                   3: int_da.eq(if_channel_A_dfe_lb.dca_lb[3]),
                                                   4: int_da.eq(if_channel_A_dfe_lb.dca_lb[4]),
                                                   5: int_da.eq(if_channel_A_dfe_lb.dca_lb[5]),
                                                   6: int_da.eq(if_channel_A_dfe_lb.dca_lb[6]),
                                                   7: int_da.eq(if_channel_A_dfe_lb.dpar_lb)}
                          )
        self.comb += Case(if_ctrl_lb.sel_int_bit, {0: int_db.eq(if_channel_B_dfe_lb.dca_lb[0]),
                                                   1: int_db.eq(if_channel_B_dfe_lb.dca_lb[1]),
                                                   2: int_db.eq(if_channel_B_dfe_lb.dca_lb[2]),
                                                   3: int_db.eq(if_channel_B_dfe_lb.dca_lb[3]),
                                                   4: int_db.eq(if_channel_B_dfe_lb.dca_lb[4]),
                                                   5: int_db.eq(if_channel_B_dfe_lb.dca_lb[5]),
                                                   6: int_db.eq(if_channel_B_dfe_lb.dca_lb[6]),
                                                   7: int_db.eq(if_channel_B_dfe_lb.dpar_lb)}
                          )

        # Mux : select phase for internal
        phase_ck = Signal()
        self.comb += If(if_ctrl_lb.sel_phase_ab == 1,
                        phase_ck.eq(if_ck.ck_t)
                        ).Else(phase_ck.eq(if_ck.ck_c))

        # Mux : select A or B channel
        int_d = Signal()
        self.comb += If(if_ctrl_lb.sel_mode == 1,
                        int_d.eq(int_da)
                        ).Elif(if_ctrl_lb.sel_mode == 2,
                               int_d.eq(int_db)
                               ).Else(int_d.eq(0))
        # TODO Change domain of this sync to phase_ck
        int_dd = Signal()
        self.sync += int_dd.eq(int_d)

        # External path

        # Mux between internal and external
        self.comb += Case(if_ctrl_lb.sel_mode, {0: [if_rcd_lb.lbs.eq(TIE_LOW),
                                                    if_rcd_lb.lbd.eq(TIE_LOW)],
                                                1: [if_rcd_lb.lbs.eq(if_ck.ck_t),
                                                    if_rcd_lb.lbd.eq(int_dd)],
                                                2: [if_rcd_lb.lbs.eq(if_ck.ck_c),
                                                    if_rcd_lb.lbd.eq(int_dd)],
                                                3: [if_rcd_lb.lbs.eq(0),
                                                    if_rcd_lb.lbd.eq(0)],
                                                4: [if_rcd_lb.lbs.eq(0),
                                                    if_rcd_lb.lbd.eq(0)],
                                                5: [if_rcd_lb.lbs.eq(0),
                                                    if_rcd_lb.lbd.eq(0)],
                                                })


class TestBed(Module):
    def __init__(self):
        #
        self.if_ck = If_ck()
        self.if_host_lb = If_lb()
        self.if_rcd_lb = If_lb()
        self.if_sdram_A_lb = If_lb()
        self.if_sdram_B_lb = If_lb()
        self.if_channel_A_dfe_lb = If_int_lb()
        self.if_channel_B_dfe_lb = If_int_lb()
        self.if_ctrl_lb = If_ctrl_lb()
        ###
        self.submodules.dut = DDR5RCD01Loopback(self.if_ck,
                                               self.if_host_lb,
                                               self.if_rcd_lb,
                                               self.if_sdram_A_lb,
                                               self.if_sdram_B_lb,
                                               self.if_channel_A_dfe_lb,
                                               self.if_channel_B_dfe_lb,
                                               self.if_ctrl_lb)
        # print(verilog.convert(self.lb))


def run_test(tb):
    logging.debug('Write test')
    yield from behav_write_word(0x0)

    logging.debug('Yield from write test.')


def behav_write_word(tb):
    #
    # yield dut.d.eq(data)
    yield


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))