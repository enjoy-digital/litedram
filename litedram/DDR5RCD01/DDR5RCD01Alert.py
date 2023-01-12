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


class DDR5RCD01Alert(Module):
    """DDR5 RCD01 Alert
    TODO Documentation
    Handle the alert signal

    TODO Add pulse settings and assertion mode supports

    Module
    ------
    d - Input : data
    q - Output: data
    ------
    """

    def __init__(self, if_host_err, if_channel_A_err,
                 if_channel_B_err, if_ctrl_err):
        # TODO take errors from channel and create a pulse
        # TODO implement control

        # TODO Implementation forces no error
        self.comb += if_host_err.err_n.eq(1)


class TestBed(Module):
    def __init__(self):

        self.if_host_err = If_error()
        self.if_channel_A_err = If_error()
        self.if_channel_B_err = If_error()
        self.if_ctrl_err = If_ctrl_err()

        self.submodules.dut = DDR5RCD01Alert(
            self.if_host_err, self.if_channel_A_err, self.if_channel_B_err, self.if_ctrl_err)
        # print(verilog.convert(self.dut))


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
