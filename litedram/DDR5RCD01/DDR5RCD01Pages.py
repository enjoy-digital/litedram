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
from litedram.DDR5RCD01.DDR5RCD01Page import *
from litedram.DDR5RCD01.RCD_definitions import *
from litedram.DDR5RCD01.RCD_interfaces import *
from litedram.DDR5RCD01.RCD_utils import *


class DDR5RCD01Pages(Module):
    """DDR5 RCD01 Pages
    TODO Documentation
      In an RCD, there are 256 pages. A page is a set of 32 registers.
      The page pointer is held in the RW5F.

      Module
      ------
      d - input, a whole page
      we - write enable to override whole page
      page_pointer - connect to RW5F, selects page from 0 to 255
      q_page -
    """

    def __init__(self, d, we, page_pointer, q_page, page_addr, cw_page_num = CW_PAGE_NUM):
        # Hook inputs
        # Page file
        self.pages = Array(DDR5RCD01Page(d, page_addr, we)
                           for y in range(cw_page_num))
        logging.debug('Created Pages: %d', len(self.pages))
        #
        # TODO Initialize

        # PAGES
        # foreach page
        for id, page in enumerate(self.pages):
            # foreach register in page
            for id_r, reg in enumerate(page.registers):
                # d is a page, which overwrites currently stored page
                # breakpoint()
                self.sync += If(we == 1,
                                If(page_pointer == id,
                                   If(page_addr == id_r,
                                      self.pages[id].registers[id_r].eq(d)
                                      )
                                   )
                                )
        # OUTPUT
        # q_pages is an output, which present a page currently selected by the page pointer
        # self.q_pages = Array(Signal(CW_REG_BIT_SIZE)
        #                      for y in range(CW_PAGE_PTRS_NUM))
        # for id_r, reg in enumerate(q_pages):
        #     self.comb += q_pages[id_r].eq(
        #         (self.pages[page_pointer]).registers[id_r])
        # breakpoint()
        # foreach register in page
        for id_r, reg in enumerate(page.registers):
            self.comb += q_page[id_r].eq(
                self.pages[page_pointer].registers[id_r])


class TestBed(Module):
    def __init__(self):
        # TODO fix the scenario
        raise NotImplementedError("This test is to be done.")
        self.we = Signal()
        self.d = Array(Signal(CW_REG_BIT_SIZE)
                       for y in range(CW_PAGE_PTRS_NUM))
        self.page_pointer = Signal(8)
        self.q_page = Signal()
        self.page_addr = Signal()
        self.submodules.pages = DDR5RCD01Pages(
            we=self.we, d=self.d, page_pointer=self.page_pointer, q_page=self.q_page, page_addr=self.page_addr)

        # print(verilog.convert(self.regfile))


def run_test(tb):
    logging.debug('Write test')
    yield from tb.dut.regfile.pretty_print()
    yield from behav_write_word(0x23, 0x00)
    yield from behav_write_word(0x24, 0x01)
    yield from behav_write_word(0x25, 0x03)
    yield from behav_write_word(0x26, 0x0A)

    for i in range(5):
        yield
    logging.debug('Yield from write test.')


def behav_write_word(data, id_d):
    yield tb.d[id_d].eq(0x00)
    yield tb.page_pointer.eq(0x02)
    yield tb.we.eq(0)
    yield
    yield tb.d[id_d].eq(data)
    yield tb.we.eq(1)
    yield
    yield tb.d[id_d].eq(0x00)
    yield tb.we.eq(0)


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
