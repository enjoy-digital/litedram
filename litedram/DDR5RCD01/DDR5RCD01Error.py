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


class DDR5RCD01Error(Module):
    """DDR5 RCD01 Error Alert
    TODO Documentation
    Handle the alert signal
    if parity is enabled, the alert signal is used to raise the parity error
    if parity is disabled, the alert signal is used to raise the DERROR_IN_n error

    parity check is based on dca and dpar, also it must know whether a true UI is on the line.
    This is why it may be beneficial to include the parity checker as a separate module.
    Then the ErrorAlert module will be a simple mux of errors?

    Use case 1. Parity error detected with parity checking enabled
     - Set CA Parity Error Status (RW24)
     - Clear bit in RW01 to disable parity checking
     - Assert ALERT_n for the length 3 input clocks

    RW01.1 
    This error blocks the pass-through (disable output buffer) until a clear error command!
    RW01.6
    Assertion mode
    RW01.7
    Parity checking remains ... after pulse

    TODO MVP
    1. Assert alert if a parity error occured, only block outputs
    2. Assert alert if a derror_in error occured
    TODO Full implementation
    1. Proper register sequence on error
    2. Add pulse settings and assertion mode supports

    Module
    ------
    d - Input : data
    q - Output: data
    ------
    """

    def __init__(self, iif_err, oif_err):
        # TODO Implement the physical function
        self.comb += oif_err.err_n.eq(iif_err.err_n)


class TestBed(Module):
    def __init__(self):
        iif_err = If_error()
        oif_err = If_error()
        self.submodules.dut = DDR5RCD01Error(iif_err,oif_err)
        # print(verilog.convert(self.dut))


def run_test(dut):
    logging.debug('Run test')
    for i in range(5):
        yield
    logging.debug('Yield from run test.')


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
