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
from litedram.DDR5RCD01.DDR5RCD01Loopback import DDR5RCD01Loopback
from litedram.DDR5RCD01.DDR5RCD01Alert import DDR5RCD01Alert
from litedram.DDR5RCD01.DDR5RCD01PLL import DDR5RCD01PLL


class DDR5RCD01Common(Module):
    """DDR5 RCD01 Common
    TODO
    The common:
        - PLL
        - Loopback
        - Error/alert
        - QRST

    Module
    ------
    <interface> : CS,CA,etc.
    dck, dck_pll 
    """

    def __init__(self,
                 # Distribute clock and reset
                 if_host_ck, if_host_rst_n,
                 if_channel_A_ck, if_channel_A_rst_n,
                 if_channel_B_ck, if_channel_B_rst_n,
                 if_sdram_A_rst_n, if_sdram_B_rst_n,
                 # Error
                 if_host_err,
                 if_channel_A_err,
                 if_channel_B_err,
                 # Loopback
                 if_host_lb,
                 if_rcd_lb,
                 if_sdram_A_lb,
                 if_sdram_B_lb,
                 if_channel_A_lb,
                 if_channel_B_lb,
                 # Control interfaces
                 if_ctrl_pll, if_ctrl_lb, if_ctrl_err,
                 ):

        # TODO Split the channel config

        xlb = DDR5RCD01Loopback(if_host_ck,
                                if_host_lb,
                                if_rcd_lb,
                                if_sdram_A_lb,
                                if_sdram_B_lb,
                                if_channel_A_lb,
                                if_channel_B_lb,
                                if_ctrl_lb)
        self.submodules += xlb

        xalert = DDR5RCD01Alert(if_host_err, if_channel_A_err,
                                if_channel_B_err, if_ctrl_err)
        self.submodules += xalert

        xpll = DDR5RCD01PLL(if_host_ck, if_channel_A_ck,
                            if_channel_B_ck, if_ctrl_pll)
        self.submodules += xpll

        # Reset distribution
        self.comb += if_channel_A_rst_n.rst_n.eq(if_host_rst_n.rst_n)
        self.comb += if_channel_B_rst_n.rst_n.eq(if_host_rst_n.rst_n)
        self.comb += if_sdram_A_rst_n.rst_n.eq(if_host_rst_n.rst_n)
        self.comb += if_sdram_B_rst_n.rst_n.eq(if_host_rst_n.rst_n)


class TestBed(Module):
    def __init__(self):
        if_host_ck = If_ck()
        if_host_rst_n = If_rst_n()

        if_channel_A_ck = If_ck()
        if_channel_A_rst_n = If_rst_n()
        if_channel_B_ck = If_ck()
        if_channel_B_rst_n = If_rst_n()
        if_sdram_A_rst_n = If_rst_n()
        if_sdram_B_rst_n = If_rst_n()
        # Error
        if_host_err = If_error()
        if_channel_A_err = If_error()
        if_channel_B_err = If_error()
        # Loopback
        if_host_lb = If_lb()
        if_rcd_lb = If_lb()
        if_sdram_A_lb = If_lb()
        if_sdram_B_lb = If_lb()
        if_channel_A_lb = If_int_lb()
        if_channel_B_lb = If_int_lb()
        # Control interfaces
        if_ctrl_pll = If_ctrl_pll()
        if_ctrl_lb = If_ctrl_lb()
        if_ctrl_err = If_ctrl_err()
        
        self.clock_domains.dck_t = ClockDomain(name="dck_t")
        self.clock_domains.dck_c = ClockDomain(name="dck_c")

        self.sync += self.dck_t.clk.eq(~self.dck_t.clk)
        self.comb += self.dck_c.clk.eq(~self.dck_t.clk)

        self.comb += if_host_ck.ck_t.eq(self.dck_t.clk)
        self.comb += if_host_ck.ck_c.eq(self.dck_c.clk)

        self.submodules.dut = DDR5RCD01Common(if_host_ck, if_host_rst_n,
                                              if_channel_A_ck, if_channel_A_rst_n,
                                              if_channel_B_ck, if_channel_B_rst_n,
                                              if_sdram_A_rst_n, if_sdram_B_rst_n,
                                              if_host_err,
                                              if_channel_A_err,
                                              if_channel_B_err,
                                              if_host_lb,
                                              if_rcd_lb,
                                              if_sdram_A_lb,
                                              if_sdram_B_lb,
                                              if_channel_A_lb,
                                              if_channel_B_lb,
                                              if_ctrl_pll, if_ctrl_lb, if_ctrl_err)


def run_test(tb):
    logging.debug('Write test')
    for i in range(5):
        yield
    logging.debug('Yield from write test.')


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))