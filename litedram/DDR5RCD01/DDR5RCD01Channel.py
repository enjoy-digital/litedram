#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# Python
import logging
# migen
from migen import *
# RCD
from litedram.DDR5RCD01.RCD_definitions import *
from litedram.DDR5RCD01.RCD_interfaces import *
from litedram.DDR5RCD01.RCD_utils import *
# Submodules
from litedram.DDR5RCD01.DDR5RCD01InputBuffer import DDR5RCD01InputBuffer
from litedram.DDR5RCD01.DDR5RCD01LineBuffer import DDR5RCD01LineBuffer
from litedram.DDR5RCD01.DDR5RCD01OutputBuffer import DDR5RCD01OutputBuffer
from litedram.DDR5RCD01.DDR5RCD01ControlCenter import DDR5RCD01ControlCenter
from litedram.DDR5RCD01.DDR5RCD01Error import DDR5RCD01Error


class DDR5RCD01Channel(Module):
    """DDR5 RCD01 Channel
    TODO
    The channel:
      - Input Buffer
      - Line Buffer
      - Output Buffer 
      - Control Center

    Module
    ------
    <interface> : CS,CA,etc.
    dck, dck_pll 
    """

    def __init__(self, if_channel_ck, if_channel_rst_n,
                 if_ibuf, if_obuf_csca, if_obuf_clks,
                 if_sdram,
                 if_err, if_lb,
                 if_ctrl_global,
                 channel_A,
                 *args
                 ):

        # Control interfaces
        if_ctrl_ibuf = If_ctrl_ibuf()
        if_ctrl_lbuf = If_ctrl_lbuf()
        if_ctrl_obuf = If_ctrl_obuf()

        # Input Buffer
        if_ibuf_2_lbuf = If_channel_ibuf()
        xibuf = DDR5RCD01InputBuffer(if_ibuf, if_ibuf_2_lbuf, if_ctrl_ibuf)
        self.submodules += xibuf

        # Line Buffer
        if_lbuf_2_obuf = If_channel_obuf_csca()
        xlbuf = DDR5RCD01LineBuffer(
            if_ibuf_2_lbuf, if_lbuf_2_obuf, if_ctrl_lbuf)
        self.submodules += xlbuf

        if_clks_2_obuf = If_channel_obuf_clks()
        # Attach Clock outputs
        self.comb += if_clks_2_obuf.qack_t.eq(if_channel_ck.ck_t)
        self.comb += if_clks_2_obuf.qack_c.eq(if_channel_ck.ck_c)

        self.comb += if_clks_2_obuf.qbck_t.eq(if_channel_ck.ck_t)
        self.comb += if_clks_2_obuf.qbck_c.eq(if_channel_ck.ck_c)

        self.comb += if_clks_2_obuf.qcck_t.eq(if_channel_ck.ck_t)
        self.comb += if_clks_2_obuf.qcck_c.eq(if_channel_ck.ck_c)

        self.comb += if_clks_2_obuf.qdck_t.eq(if_channel_ck.ck_t)
        self.comb += if_clks_2_obuf.qdck_c.eq(if_channel_ck.ck_c)

        # Output Buffer
        xobuf = DDR5RCD01OutputBuffer(
            if_lbuf_2_obuf, if_clks_2_obuf, if_obuf_csca, if_obuf_clks, if_ctrl_obuf)
        self.submodules += xobuf

        # Hook inputs
        if channel_A:
            logging.debug('I am channel A')
            # Set direction of glob_settings
            # Drive the registers
            if not args:
                logging.error(
                    'The global config was not passed to the channel A')
            # TODO test if kwargs are of these types:
            if_config_pll = args[0]
            if_config_lb = args[1]
            if_config_err = args[2]

            xcontrol_center = DDR5RCD01ControlCenter(if_ibuf_2_lbuf,  # Fetch opcodes from here
                                                     if_ctrl_ibuf, if_ctrl_lbuf, if_ctrl_obuf,  # Control buffers
                                                     if_ctrl_global,  # Send settings to channel B
                                                     channel_A,
                                                     if_config_pll, if_config_lb, if_config_err  # Send settings to common
                                                     )
        else:
            logging.debug('I am channel B')
            # Set direction of glob_settings
            # Driven from the registers
            xcontrol_center = DDR5RCD01ControlCenter(if_ibuf_2_lbuf,  # Fetch opcodes from here
                                                     if_ctrl_ibuf, if_ctrl_lbuf, if_ctrl_obuf,  # Control buffers
                                                     if_ctrl_global,  # Send settings to channel B
                                                     channel_A
                                                     )

        self.submodules += xcontrol_center

        # TODO implement error handler
        xerror = DDR5RCD01Error(iif_err=if_sdram, oif_err=if_err)
        self.submodules += xerror


class TestBed(Module):
    def __init__(self):
        #
        # self.d = Signal()
        #
        self.submodules.dut = DDR5RCD01Channel()


def run_test(dut):
    logging.debug('Write test')
    # yield from dut.regfile.pretty_print_regs()
    # yield from behav_write_word(0x0,0x0,0x0)

    logging.debug('Yield from write test.')


def behav_write_word(data):
    # yield dut.frac_p.eq(data)
    yield


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    raise NotImplementedError("Test of this block is to be done.")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
