#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# Python
from reprlib import *
import logging
# migen
from migen import *
from migen.fhdl import verilog
# Litex
from litedram.DDR5RCD01.RCD_definitions import *
from litedram.DDR5RCD01.RCD_interfaces import *
from litedram.DDR5RCD01.RCD_utils import *


class DDR5RCD01Page(Module):
    """DDR5 RCD01 Page
    TODO Documentation
      In an RCD, there are 256 pages. A page is a set of 32 registers.
      The page pointer is held in the RW5F.

    """

    def pretty_print(self):
        """ Prints current value of registers and their metadata
        """
        repack = Repr()
        repack.maxstring = 20
        line = '-'*80
        logging.debug(line)
        logging.debug('Page')
        logging.debug(line+'0x00')
        logging.debug("Signal "+"value "+"name "+"address " +
                      "description "+"global "+"attribute ")
        for id, meta in enumerate(self.registers_metadata):
            reg = self.registers[id]
            str_format = repack.repr(str(reg))+' | '
            reg_val = (yield reg)
            str_format = str_format + str(reg_val)+' | '
            for m in meta:
                # TODO Fix the global flag print
                str_format = str_format + repack.repr(str(m)) + ' | '
            logging.debug(str_format)
            # TODO Fix
            # This if-statement is here to prevent very long prints
            # Repr can be used to limit the list output
            if id == 5:
                break
        logging.debug(line+'0x05')

    def load_page_def(self, page_id=0):
        """ Loads string data from RCD_definitions.py to an object regsiters_metadata
        """
        logging.debug('Reading information in page ' +
                      str(page_id) + ' definition')
        self.registers_metadata = []
        prefix = "rcd_page_"
        string_name = prefix+str(page_id)
        table_handle = rcd_pages[string_name]
        for id, msg in enumerate(table_handle):
            self.registers_metadata.append(msg)

    def __init__(self, d, addr, we):
        # Register file
        self.registers = Array(Signal(CW_REG_BIT_SIZE)
                               for y in range(CW_PAGE_PTRS_NUM))
        logging.debug('Created Page: %d x %db', len(
            self.registers), len(self.registers[0]))

        # Attribute registers
        # Attribute regs are created in a weird way now.
        # TODO fix attr regs, they should be embedded
        # attr_regs = AttributeRegs()
        # self.submodules.attr_regs = attr_regs

        # Output of a page are all registers at the same time.

        # Create da_regs_metadata
        self.load_page_def()

        for id, reg in enumerate(self.registers):
            self.sync += If(we,
                            If(addr == id,
                                self.registers[id].eq(d)
                               )
                            )
            # read_only is 2, need to replace this
            # If( self.attr_regs.attr_regs[id][2] == 0,
            # self.registers[id].eq(d) )
            # )


class TestBed(Module):
    def __init__(self):

        self.we = Signal()
        self.d = Signal(CW_REG_BIT_SIZE)
        self.addr = Signal(8)
        self.submodules.dut = DDR5RCD01Page(
            we=self.we, addr=self.addr, d=self.d)
        # print(verilog.convert(self.regfile))


def run_test(tb):
    logging.debug('Write test')

    yield from tb.dut.pretty_print()
    yield from behav_write_word(tb, 0x23, 0x00)
    yield from behav_write_word(tb, 0x24, 0x01)
    yield from behav_write_word(tb, 0x25, 0x03)
    yield from behav_write_word(tb, 0x26, 0x0A)
    for i in range(3):
        yield

    logging.debug('Yield from write test.')


def behav_write_word(tb, data, addr):
    yield tb.d.eq(data)
    yield tb.addr.eq(addr)
    yield tb.we.eq(1)
    yield
    yield tb.we.eq(0)
    yield


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
