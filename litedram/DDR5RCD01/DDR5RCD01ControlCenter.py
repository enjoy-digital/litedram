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
# RCD
from litedram.DDR5RCD01.RCD_definitions import *
from litedram.DDR5RCD01.RCD_interfaces import *
from litedram.DDR5RCD01.RCD_utils import *
# Submodules
from litedram.DDR5RCD01.DDR5RCD01RegFile import DDR5RCD01RegFile
from litedram.DDR5RCD01.DDR5RCD01Pages import DDR5RCD01Pages


class DDR5RCD01ControlCenter(Module):
    """DDR5 RCD01 Control Center
    TODO Documentation

    -- 3.8 on hard reset
    POWERDOWN - meaning no power supplied, note, this is ambiguous*
    Device should start in the RESET state. DRST_n shall be asserted.
    Effects:
      - floating input receivers
      - non-sticky registers are restored to default (preferred 0)
      - QRST_n is asserted
      - other outputs are to flow, except QCS[x]_n which should be asserted
    This state is also called the low-power state.  

    *Powerdown is widely used to describe a power-state, in which
    the bias circuitry is disabled, however, there is a stable power supply
    on the vdd pin.

    Next:
      - DRST_n is deasserted
      - DCS_n are deasserted
      - Host starts the dck clock
      - host writes to coarse and fine grain frequency registers 
      - host writes to DCA input mode (DDR, SDR)
      - wait for PLL to re-lock
    Next, training:
      - DCS and DCA training
      - BCS and BCOM training (if applicable)

    Note, qrst_n remains asserted until a proper command register write.

    After initilization, a proper write sequence should occur to configure the application.
    -- 3.9 on soft reset (vdd remains on)
    TODO analyze

    TODO List of states:
    HARD_RESET
    SOFT_RESET
    INITILIZATION
    NORMAL
    TRAINING (4 modes)
    POWER_SAVINGS (4 modes)

    Module
    ------
    d - Input : data
    q - Output: data
    ------
    """

    def __init__(self,
                 if_ibuf_2_lbuf,  # Fetch opcodes from here
                 if_ctrl_ibuf, if_ctrl_lbuf, if_ctrl_obuf,  # Control buffers
                 if_ctrl_global,  # Send settings to channel B
                 is_channel_A,
                 *args):

        bank_d = Signal(8)
        bank_page_pointer = Signal(8)
        bank_we = Signal()
        page_addr = Signal(8)
        page_copy = Array(Signal(CW_REG_BIT_SIZE)
                          for y in range(CW_PAGE_PTRS_NUM))

        # TODO Pages are currently unused, so their number is reduced to speed-up the simulation
        xbank_file = DDR5RCD01Pages(
            bank_d, bank_we, bank_page_pointer, page_copy, page_addr, cw_page_num=6)
        self.submodules += xbank_file
        banks = xbank_file.pages

        reg_d = Signal(8)
        reg_addr = Signal(8)
        reg_we = Signal()
        reg_q = Signal(CW_REG_BIT_SIZE)

        xreg_file = DDR5RCD01RegFile(reg_d, reg_addr, reg_we, reg_q, page_copy)
        self.submodules += xreg_file

        regs = xreg_file.registers
        page_addr = regs[ADDR_CW_PAGE]
        page_copy = banks[bank_page_pointer]
        bank_page_pointer = regs[ADDR_CW_PAGE]

        if is_channel_A:
            logging.debug('I am channel A')
            # Set direction of glob_settings
            # Drive the registers
            if not args:
                logging.error(
                    'The global config was not passed to the channel A')
            if_config_pll = args[0]
            if_config_lb = args[1]
            if_config_err = args[2]

        """
        CSR, RW, PAGE
        This section described the CSR of the device. Connects physical functions
        to its control words in Control Registers. 

        """
        # Boot Image
        boot_image_rw00_rw5f = Array(Signal(CW_REG_BIT_SIZE)
                                     for y in range(CW_DA_REGS_NUM))
        DEBUG_NUMBER = 0x39
        boot_image_rw00_rw5f = [DEBUG_NUMBER]*CW_DA_REGS_NUM

        """ Custom Internal CSR
          Implementation dependent, not constrained by the JEDEC spec.

        """
        rw_custom_csr = Signal(8)  # Expand width as needed
        RW_CUSTOM_INBUF_EN = rw_custom_csr[0]
        # ------------------------0b76543210
        rw_custom_csr_boot_word = 0b00000001

        self.comb += if_ctrl_ibuf.en.eq(RW_CUSTOM_INBUF_EN)

        """ Table 98
            RW00
            Global Features Control Word
        """
        RW_GLOBAL_FEATURES = 0x00
        COMMAND_ADDRESS_RATE = regs[RW_GLOBAL_FEATURES][0]
        SDR_MODES = regs[RW_GLOBAL_FEATURES][1]
        CA_PASS_THROUGH_MODE_ENABLE = regs[RW_GLOBAL_FEATURES][2]
        CA_PASS_THROUGH_MODE_RANK_SELECTION = regs[RW_GLOBAL_FEATURES][3]
        BCOM_PASS_THROUGH_MODE_ENABLE = regs[RW_GLOBAL_FEATURES][4]
        OUTPUT_INVERSION_ENABLE = regs[RW_GLOBAL_FEATURES][5]
        POWER_DOWN_MODE_ENABLE = regs[RW_GLOBAL_FEATURES][6]
        TRANSPARENT_MODE_ENABLE = regs[RW_GLOBAL_FEATURES][7]
        # -----------------------------------------0b76543210
        boot_image_rw00_rw5f[RW_GLOBAL_FEATURES] = 0b00100011

        """ Table 99
            RW01
            Parity, CMD Blocking and Alert Global Control Word
            Note, for block_n signals the '0' means block
        """
        RW_SECONDARY_FEATURES = 0x01
        PARITY_CHECKING_ENABLE = regs[RW_SECONDARY_FEATURES][0]
        DRAM_FORWARD_CMDS_BLOCK_N = regs[RW_SECONDARY_FEATURES][1]
        # RESERVED = regs[RW_SECONDARY_FEATURES][2]
        DB_FORWARD_CMDS_BLOCK_N = regs[RW_SECONDARY_FEATURES][3]
        # RESERVED = regs[RW_SECONDARY_FEATURES][4]
        HOST_IF_TRAINING_FEEDBACK = regs[RW_SECONDARY_FEATURES][5]
        ALERT_ASSERTION_MODE = regs[RW_SECONDARY_FEATURES][6]
        ALERT_REENABLE = regs[RW_SECONDARY_FEATURES][7]
        # --------------------------------------------0b76543210
        boot_image_rw00_rw5f[RW_SECONDARY_FEATURES] = 0b10000010

        """ Table 107
            RW08
            Clock driver enable control word
            regs[0x08]
            """
        RW_CLOCK_OUTPUT_CONTROL = 0x08
        QACK_CLK_ENABLE = regs[RW_CLOCK_OUTPUT_CONTROL][0]
        QBCK_CLK_ENABLE = regs[RW_CLOCK_OUTPUT_CONTROL][1]
        QCCK_CLK_ENABLE = regs[RW_CLOCK_OUTPUT_CONTROL][2]
        QDCK_CLK_ENABLE = regs[RW_CLOCK_OUTPUT_CONTROL][3]
        # RESERVED = regs[RW_CLOCK_OUTPUT_CONTROL][4]
        BCK_CLK_ENABLE = regs[RW_CLOCK_OUTPUT_CONTROL][5]
        # RESERVED = regs[RW_CLOCK_OUTPUT_CONTROL][6]
        # RESERVED = regs[RW_CLOCK_OUTPUT_CONTROL][7]
        # ----------------------------------------------0b76543210
        boot_image_rw00_rw5f[RW_CLOCK_OUTPUT_CONTROL] = 0b11000101

        self.comb += if_ctrl_obuf.oe_qack_t.eq(QACK_CLK_ENABLE)
        self.comb += if_ctrl_obuf.oe_qack_c.eq(QACK_CLK_ENABLE)

        self.comb += if_ctrl_obuf.oe_qbck_t.eq(QBCK_CLK_ENABLE)
        self.comb += if_ctrl_obuf.oe_qbck_c.eq(QBCK_CLK_ENABLE)

        self.comb += if_ctrl_obuf.oe_qcck_t.eq(QCCK_CLK_ENABLE)
        self.comb += if_ctrl_obuf.oe_qcck_c.eq(QCCK_CLK_ENABLE)

        self.comb += if_ctrl_obuf.oe_qdck_t.eq(QDCK_CLK_ENABLE)
        self.comb += if_ctrl_obuf.oe_qdck_c.eq(QDCK_CLK_ENABLE)

        """ Table 108 
            RW09
            Output address and Control Enable Control Word
            regs[0x09]
            """
        RW_OUTPUT_CONTROL = 0x09
        QACA_OUTPUT_ENABLE = regs[RW_OUTPUT_CONTROL][0]
        QBCA_OUTPUT_ENABLE = regs[RW_OUTPUT_CONTROL][1]
        DCS_N_AND_QCS_N_ENABLE = regs[RW_OUTPUT_CONTROL][2]
        BCS_BCOM_BRST_ENABLE = regs[RW_OUTPUT_CONTROL][3]
        QBACA13_OUTPUT_ENABLE = regs[RW_OUTPUT_CONTROL][4]
        QACS_N_ENABLE = regs[RW_OUTPUT_CONTROL][5]
        QBCS_N_ENABLE = regs[RW_OUTPUT_CONTROL][6]
        # RESERVED = regs[RW_OUTPUT_CONTROL][7]
        # ----------------------------------------0b76543210
        boot_image_rw00_rw5f[RW_OUTPUT_CONTROL] = 0b01100111

        # Output enable
        self.comb += if_ctrl_obuf.oe_qaca_a.eq(QACA_OUTPUT_ENABLE)
        self.comb += if_ctrl_obuf.oe_qaca_b.eq(QBCA_OUTPUT_ENABLE)

        self.comb += if_ctrl_obuf.oe_qacs_a_n.eq(QACS_N_ENABLE)
        self.comb += if_ctrl_obuf.oe_qacs_b_n.eq(QBCS_N_ENABLE)

        # DCS, DCA Output inversion
        self.comb += if_ctrl_obuf.o_inv_en_qacs_a_n.eq(0)
        self.comb += if_ctrl_obuf.o_inv_en_qacs_b_n.eq(0)

        self.comb += if_ctrl_obuf.o_inv_en_qaca_a.eq(0)
        self.comb += if_ctrl_obuf.o_inv_en_qaca_b.eq(OUTPUT_INVERSION_ENABLE)

        # Clock output inversion
        self.comb += if_ctrl_obuf.o_inv_en_qack_t.eq(OUTPUT_INVERSION_ENABLE)
        self.comb += if_ctrl_obuf.o_inv_en_qack_c.eq(OUTPUT_INVERSION_ENABLE)

        self.comb += if_ctrl_obuf.o_inv_en_qbck_t.eq(OUTPUT_INVERSION_ENABLE)
        self.comb += if_ctrl_obuf.o_inv_en_qbck_c.eq(OUTPUT_INVERSION_ENABLE)

        self.comb += if_ctrl_obuf.o_inv_en_qcck_t.eq(OUTPUT_INVERSION_ENABLE)
        self.comb += if_ctrl_obuf.o_inv_en_qcck_c.eq(OUTPUT_INVERSION_ENABLE)

        self.comb += if_ctrl_obuf.o_inv_en_qdck_t.eq(OUTPUT_INVERSION_ENABLE)
        self.comb += if_ctrl_obuf.o_inv_en_qdck_c.eq(OUTPUT_INVERSION_ENABLE)

        """ Table 115 
            RW11
            Command Latency Adder Configuration Control Word
            regs[0x11]
        """
        RW_LATENCY_ADDER = 0x11
        LATENCY_ADDER_OP_0 = regs[RW_LATENCY_ADDER][0]
        LATENCY_ADDER_OP_1 = regs[RW_LATENCY_ADDER][1]
        LATENCY_ADDER_OP_2 = regs[RW_LATENCY_ADDER][2]
        # RESERVED = regs[RW_LATENCY_ADDER][3]
        # RESERVED = regs[RW_LATENCY_ADDER][4]
        # RESERVED = regs[RW_LATENCY_ADDER][5]
        # RESERVED = regs[RW_LATENCY_ADDER][6]
        # RESERVED = regs[RW_LATENCY_ADDER][7]
        latency_cat = Cat(LATENCY_ADDER_OP_0,
                          LATENCY_ADDER_OP_1,
                          LATENCY_ADDER_OP_2)
        # ----------------------------------------0b76543210
        boot_image_rw00_rw5f[RW_LATENCY_ADDER] = 0b000000001

        self.comb += if_ctrl_lbuf.sel_latency_add.eq(latency_cat)

        """
          Parity checker
        """
        # self.comb += parity_error.eq(0)

        """
          CS Logic
          The control center forwards the cmd to the deserializer by the 
          If_ctrl_lbuf interface. The deserializer is placed inside of the lbuf.
          (Not optimal for synthesis).

          Commands (CA and CS_n) are forwarded in normal mode:
          1. Detect active CS_n
          2. Send the command to the DRAM interface
          Use Cases: 
          
          1 UI command:
            - CS is low
            - CA on this edge and next is captured (c.f. RCD model clocking)
          
          2 UI commands: 
            - CS is low only during 1st UI. Can be low if the non-target termination
            is being signalled. c.f. Table 4
            - CA must be captured on 2 more edges

          Parity error detected during a 1 UI command

          Parity error detected during a 2 UI command

          DRAM Interface Blocking Mode is enabled

          CA Pass-through Mode is enabled

          The decode portion should always listen
        """

        debug_parity_error_occured = Signal()
        self.comb += debug_parity_error_occured.eq(0)

        debug_non_target_termination_signalled = Signal()
        self.comb += debug_non_target_termination_signalled.eq(0)

        """
          Drive deser if a command is sent
        """
        # Normal forward
        xfsm_cslogic = FSM(reset_state="RESET")
        self.submodules += xfsm_cslogic

        fetch_decode_en = Signal()
        self.comb += fetch_decode_en.eq(1)

        xfsm_cslogic.act(
            "RESET",
            If(
                fetch_decode_en,
                NextState("IDLE")
            )
        )
        xfsm_cslogic.act(
            "IDLE",
            If(
                if_ibuf_2_lbuf.dcs_n == 0x00,
                if_ctrl_lbuf.deser_sel_lower_upper.eq(0),
                if_ctrl_lbuf.deser_ca_d_en.eq(1),
                if_ctrl_lbuf.deser_ca_q_en.eq(0),
                if_ctrl_lbuf.deser_cs_n_d_en.eq(1),
                if_ctrl_lbuf.deser_cs_n_q_en.eq(0),
                NextState("S_0a")
            ).Else(
                if_ctrl_lbuf.deser_sel_lower_upper.eq(0),
                if_ctrl_lbuf.deser_ca_d_en.eq(0),
                if_ctrl_lbuf.deser_ca_q_en.eq(0),
                if_ctrl_lbuf.deser_cs_n_d_en.eq(0),
                if_ctrl_lbuf.deser_cs_n_q_en.eq(0),
            )
        )
        xfsm_cslogic.act(
            "S_0a",
            if_ctrl_lbuf.deser_sel_lower_upper.eq(1),
            if_ctrl_lbuf.deser_ca_d_en.eq(1),
            if_ctrl_lbuf.deser_ca_q_en.eq(0),
            if_ctrl_lbuf.deser_cs_n_d_en.eq(1),
            if_ctrl_lbuf.deser_cs_n_q_en.eq(0),
            NextState("S_0b")
        )
        xfsm_cslogic.act(
            "S_0b",
            if_ctrl_lbuf.deser_sel_lower_upper.eq(0),
            if_ctrl_lbuf.deser_ca_d_en.eq(1),
            if_ctrl_lbuf.deser_ca_q_en.eq(1),
            if_ctrl_lbuf.deser_cs_n_d_en.eq(1),
            if_ctrl_lbuf.deser_cs_n_q_en.eq(1),
            NextState("S_1a")
        )
        xfsm_cslogic.act(
            "S_1a",
            if_ctrl_lbuf.deser_sel_lower_upper.eq(1),
            if_ctrl_lbuf.deser_ca_d_en.eq(1),
            if_ctrl_lbuf.deser_ca_q_en.eq(0),
            if_ctrl_lbuf.deser_cs_n_d_en.eq(1),
            if_ctrl_lbuf.deser_cs_n_q_en.eq(0),
            NextState("S_1b")
        )
        xfsm_cslogic.act(
            "S_1b",
            if_ctrl_lbuf.deser_sel_lower_upper.eq(0),
            if_ctrl_lbuf.deser_ca_d_en.eq(0),
            if_ctrl_lbuf.deser_ca_q_en.eq(1),
            if_ctrl_lbuf.deser_cs_n_d_en.eq(0),
            if_ctrl_lbuf.deser_cs_n_q_en.eq(1),
            NextState("POST")
        )
        xfsm_cslogic.act(
            "POST",
            if_ctrl_lbuf.deser_sel_lower_upper.eq(0),
            if_ctrl_lbuf.deser_ca_d_en.eq(0),
            if_ctrl_lbuf.deser_ca_q_en.eq(1),
            if_ctrl_lbuf.deser_cs_n_d_en.eq(0),
            if_ctrl_lbuf.deser_cs_n_q_en.eq(1),
            NextState("IDLE")
        )

        # TODO expand features of the main FSM here
        """ Modal FSM
        RESET_HARD - reset after power-up

        RESET_SOFT - reset after drst_n assertion
        
        INIT_HARD  - initialize after RESET_HARD
        In the init state a boot image is loaded into the CSRs. It is done
        via a sequence of writes to the Register Files. The init state
        should then last approximately (number of directly addressed
        registers =96 ) cycles. After this initial configuration the RCD model
        should go into normal operation and be ready to receive commands 
        from the host device.

        INIT_SOFT  - initialize after RESET_SOF
        
        NORMAL     - normal for RCD means listening for commands
        
        possible other states
        PRE_TRAINING, TRAINING, POST_TRAINING (?)
        """
        xfsm = FSM(reset_state="RESET_HARD")
        self.submodules += xfsm

        xfsm.act(
            "RESET_HARD",
            NextState("INIT_HARD")
        )

        rw_boot_image_reader_start = Signal()
        rw_boot_image_reader_finish = Signal()

        xfsm.act(
            "INIT_HARD",
            NextValue(rw_custom_csr, rw_custom_csr_boot_word),
            rw_boot_image_reader_start.eq(1),

            If(
                rw_boot_image_reader_finish,
                NextState("NORMAL")
            )
        )
        xfsm.act(
            "NORMAL",
            If(
                CA_PASS_THROUGH_MODE_ENABLE,
                NextState("CA_PASS_THROUGH_MODE")
            ).Else(
                NextState("NORMAL"),
            )
        )
        xfsm.act(
            "CA_PASS_THROUGH_MODE",
            If(
                ~CA_PASS_THROUGH_MODE_ENABLE,
                NextState("NORMAL")
            )
        )

        # Debug information
        xfsm_debug_state = Signal(8)
        self.comb += If(xfsm.ongoing("RESET_HARD"), xfsm_debug_state.eq(0))
        self.comb += If(xfsm.ongoing("INIT_HARD"), xfsm_debug_state.eq(1))
        self.comb += If(xfsm.ongoing("NORMAL"), xfsm_debug_state.eq(2))
        self.comb += If(xfsm.ongoing("CA_PASS_THROUGH_MODE"),
                        xfsm_debug_state.eq(3))

        # Boot image reader
        rw_counter = Signal(int(CW_DA_REGS_NUM).bit_length())
        boot_word = Signal(int(CW_DA_REGS_NUM).bit_length())

        for i in range(CW_DA_REGS_NUM):
            self.comb += If(
                rw_counter == i,
                boot_word.eq(boot_image_rw00_rw5f[i])
            )

        self.sync += If(
            rw_counter == CW_DA_REGS_NUM,
            rw_counter.eq(rw_counter),
            rw_boot_image_reader_finish.eq(1)
        ).Else(
            If(
                rw_boot_image_reader_start,
                rw_counter.eq(rw_counter+1)
            )
        )

        self.comb += If(rw_boot_image_reader_start &
                        (rw_counter < CW_DA_REGS_NUM) &
                        (~rw_boot_image_reader_finish),
                        reg_we.eq(1),
                        reg_d.eq(boot_word),
                        reg_addr.eq(rw_counter),
                        )


class TestBed(Module):
    def __init__(self):

        self.d = Signal()

        self.submodules.regfile = DDR5RCD01ControlCenter(d=self.d)
        # print(verilog.convert(self.regfile))


def run_test(dut):
    logging.debug('Write test')
    yield from behav_write_word(0x0)
    yield from behav_write_word(0x1)
    yield from behav_write_word(0x0)
    yield from behav_write_word(0x1)
    yield from behav_write_word(0x0)

    logging.debug('Yield from write test.')


def behav_write_word(tb):
    #
    yield tb.d.eq(1)
    yield


if __name__ == "__main__":
    eT = EngTest()
    raise NotImplementedError("Test of this block is to be done.")
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
