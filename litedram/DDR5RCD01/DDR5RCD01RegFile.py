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
from litedram.DDR5RCD01.RCD_utils import *
from litedram.DDR5RCD01.RCD_interfaces import *
# Submodules
from litedram.DDR5RCD01.DDR5RCD01Page import *


class DDR5RCD01RegFile(Module):
    """DDR5 RCD01 Register File
    TODO Documentation
      RCD Register File is used to model the:
          - 96 direct addressable registers
            Addressed 0-95
          - Addresses 96-127 are bank pointers, combined with RW95
      Features:
        - On the CA line, a cmd will appear with an address write or read.
        The address shall be decoded exactly as in the definition.
        Even though all registers in the file shall be visible to the rest of the
        model at all times (behavioral implementation), methods to
         - read at a specific address
         - write at a specific address
        must be provided to implement the DDR5 Commands.
      Block inputs:
       clk, 'Core clock'
       rst, 'Core reset'
       addr, 'Address of the register You wish to modify'
       we, 'Write enable to the register selected with addr'
       d, '8 bit data to be written into the register'
       registers,'all registers at all times are visible as output (unlikely to be synthesized at high-speed)'
       q, 'addr point to some register. q shows its content'
    """

    def pretty_print_regs(self):
        repack = Repr()
        repack.maxstring = 20
        line = '-'*80
        logging.debug(line)
        logging.debug('Register Space')
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

    def load_rcd_definitions(self):
        # self.rcw = RegisterControlWords()
        self.registers_metadata = []
        for id, decode_msg in enumerate(CONTROL_WORD_DECODING):
            decode_msg.append(ControlWordAttributes.RD_WR)
            self.registers_metadata.append(decode_msg)
        # TODO Add tables for page meaning
        # Currently only DA Regs

    def __init__(self, d, addr, we, q, page):
        # Register file
        self.registers = Array(Signal(CW_REG_BIT_SIZE)
                               for y in range(CW_DA_REGS_NUM+CW_PAGE_PTRS_NUM))
        logging.debug('Created Register File: %d x %db', len(
            self.registers), len(self.registers[0]))

        # Attribute registers
        attr_regs = AttributeRegs()
        self.submodules.attr_regs = attr_regs

        # Create da_regs_metadata
        self.load_rcd_definitions()
        # Initialize
        #

        # Translate the address

        self.trans_addr = Signal()
        # Registers
        # 1. Read_only is set via attr_regs
        # 2. Single cycle we to enable a write
        # 3. Directly addressable
        # If in channel A, set channel A to 1; then read_only must be anded with channel X bit
        # TODO Re-enable address translation
        # This line is not recommended for synthesis, produces a huge mux
        for id in range(CW_DA_REGS_NUM):
            self.sync += If(we == 1,
                            If(addr == id,
                               # read_only is 2, need to replace this
                               If(self.attr_regs.attr_regs[id][2] == 0,
                                  self.registers[id].eq(d))
                               )
                            )

        for id in range(CW_DA_REGS_NUM, CW_DA_REGS_NUM+CW_PAGE_PTRS_NUM):
            logging.debug("Register num = " + str(id) +
                          " Page reg num=" + str(id-CW_DA_REGS_NUM))
            self.comb += self.registers[id].eq(
                page[id-CW_DA_REGS_NUM])

        self.comb += q.eq(self.registers[self.registers[ADDR_CW_READ_POINTER]])


class TestBed(Module):
    def __init__(self):
        #
        self.we = Signal()
        self.d = Signal(8)
        self.addr = Signal(8)
        self.q = Signal(CW_REG_BIT_SIZE)

        self.page_we = Signal()
        self.page_addr = Signal(8)
        self.page_d = Signal(8)
        self.page = DDR5RCD01Page(
            addr=self.page_addr, we=self.page_we, d=self.page_d)
        self.submodules += self.page
        ###
        self.submodules.dut = DDR5RCD01RegFile(
            addr=self.addr, we=self.we, d=self.d, q=self.q, page=self.page)
        # print(verilog.convert(self.dut))


def run_test(tb):
    logging.debug('Write test')
    yield from tb.dut.pretty_print_regs()
    yield from behav_write_word(0x04, 0x01)

    yield from behav_write_page(0x0A, 0x04)
    yield from behav_write_word(ADDR_CW_READ_POINTER, ADDR_CW_PAGE+0x0A)
    yield from behav_write_page(0x0B, 0x03)
    yield from behav_write_word(ADDR_CW_READ_POINTER, ADDR_CW_PAGE+0x0B)
    yield from behav_write_page(0x0C, 0x02)
    yield from behav_write_word(ADDR_CW_READ_POINTER, ADDR_CW_PAGE+0x0C)
    yield from behav_iter_addr(0x00)

    for i in range(5):
        yield
    logging.debug('Yield from write test.')


def behav_write_word(addr, data):
    yield tb.d.eq(0x00)
    yield tb.we.eq(0)
    yield tb.addr.eq(0x00)
    yield
    yield tb.d.eq(data)
    yield tb.we.eq(1)
    yield tb.addr.eq(addr)
    yield
    yield tb.d.eq(0x00)
    yield tb.we.eq(0)
    yield tb.addr.eq(0x00)
    yield


def behav_write_page(addr, data):
    yield tb.page_d.eq(0x00)
    yield tb.page_we.eq(0)
    yield tb.page_addr.eq(0x00)
    yield
    yield tb.page_d.eq(data)
    yield tb.page_we.eq(1)
    yield tb.page_addr.eq(addr)
    yield
    yield tb.page_d.eq(0x00)
    yield tb.page_we.eq(0)
    yield tb.page_addr.eq(0x00)
    yield


def behav_iter_addr(addr):
    for i in range(3):
        yield tb.addr.eq(addr+i)
        yield


if __name__ == "__main__":
    eT = EngTest()
    logging.info("<- Module called")
    raise NotImplementedError("Test of this block is to be done.")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
