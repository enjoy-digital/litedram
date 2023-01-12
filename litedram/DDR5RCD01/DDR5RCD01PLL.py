#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# Python
import logging
# migen
from migen import *
# Litex
from litedram.DDR5RCD01.RCD_definitions import *
from litedram.DDR5RCD01.RCD_interfaces import *
from litedram.DDR5RCD01.RCD_utils import *

class DDR5RCD01PLL(Module):
    """DDR5 RCD01 PLL
    TODO Documentation
    RW05 dimm operating speed, frequency band select - test mode?
    RW06 defines the dck input clock frequency
    Do I need the x64 clock to generate fractions n/64?
    Is the main function of PLL in physical implementation to re-drive the clock?
    Then, in the model it wouldn't have to do much
    TODO current implementation is a bypass mode only (RW05.3-0 == 1111)
    Module
    ------
    dck_t,dck_c : Input clock
    qck_t,qck_c : Output clock (x1); for every rank, row, etc.
    qck64_t,qck64_c : Output clock (x64)

    """

    def __init__(self, iif, oif_A, oif_B, ctrl_if):
        # Just a clock pass-through
        self.comb += oif_A.ck_t.eq(iif.ck_t)
        self.comb += oif_A.ck_c.eq(iif.ck_c)
        
        self.comb += oif_B.ck_t.eq(iif.ck_t)
        self.comb += oif_B.ck_c.eq(iif.ck_c)
        
        # TODO Replace with a real PLL model
        # TODO Implement control interface handler


class TestBed(Module):
    def __init__(self):
        
        self.iif = If_ck()
        self.oif_A = If_ck()
        self.oif_B = If_ck()
        self.ctrl_if = If_ctrl_pll()
        self.comb += self.iif.ck_c.eq(~self.iif.ck_t)
        
        self.submodules.dut = DDR5RCD01PLL(self.iif, self.oif_A, self.oif_B, self.ctrl_if)


def run_test(tb):
    logging.debug('Write test')
    for b in [0, 1]*5:
        yield from behav_write(b)
    logging.debug('Yield from write test.')


def behav_write(b):
    yield tb.iif.ck_t.eq(b)
    yield


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
