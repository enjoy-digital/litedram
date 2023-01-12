#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from enum import Enum
from migen import *
#
TIE_LOW = 0
TIE_HIGH = 1
#
# Directle addressed registers (DA Regs)
# DA are 8 bit
CW_REG_BIT_SIZE = 8
# DA Addressing starts at 0
CW_ADDR_DA_REGS_OFFSET = 0x00
# There are 96 DA
CW_DA_REGS_NUM = 96  # Directly addressable register count
# 8-bit addressed pages
CW_PAGE_ADDR_SIZE = 8
# 32 page pointer
# TODO Fix value, should be 32
CW_PAGE_PTRS_NUM = 32
# TODO Duplicate debug value of 1
# CW_PAGE_SIZE = 1
CW_ADDR_PAGE_PTRS_OFFSET = 0x60
# 256 pages
CW_PAGE_NUM = (2**CW_PAGE_ADDR_SIZE)
# Total number of paged registers 8192
CW_PAGE_REG_NUM = CW_PAGE_PTRS_NUM*CW_PAGE_NUM
# All registers: 96+32+8192
# CW_ALL_NUM = CW_DA_REGS_NUM+CW_PAGE_PTRS_NUM+CW_PAGE_REG_NUM
CW_ALL_NUM = CW_DA_REGS_NUM+CW_PAGE_PTRS_NUM+CW_PAGE_REG_NUM

ADDR_CW_READ_POINTER = 0x5E
ADDR_CW_PAGE = 0x5F


class ControlWordAttributes(Enum):
    UNUSED_0 = 0
    RESERVED = 1
    READ_ONLY = 2
    WRITE_ONLY = 3
    RD_WR = 4
    OTP = 5  # One Time Programmable
    STICKY = 6  # Cleared by power cycle not Reset
    # --Implementation specific
    GLOBAL_ONLY = 7
    IN_CHAN_A = 8
    # If GLOBAL_ONLY AND IN_CHAN_A, then allow access
    # else don't allow access (neither write nor read)


class AttributeRegs(Module):
    def __init__(self):
        cwatr = ControlWordAttributes
        bit_size = len(cwatr)
        self.attr_regs = Array(Signal(CW_REG_BIT_SIZE)
                               for y in range(CW_ALL_NUM))
        glob_config_attr_regs = Array(
            Constant(0b0001_0000, bits_sign=(8, 'signed')) for y in range(CW_ALL_NUM))
        # TODO Assign the attributes based on specification
        # Current implementation shall:
        # - all registers are RD_WR, except:
        # - register 0x02 shall be sticky
        # - register 0x03 shall be read_only
        #                          0b7654_3210 <- bit order as in ControlWordAttributes
        # glob_config_attr_regs[2] = 0b0101_0000
        # glob_config_attr_regs[3] = 0b0000_0100
        for id, reg in enumerate(self.attr_regs):
            self.comb += self.attr_regs[id].eq(glob_config_attr_regs[id])

# Metadata
    # Bits
    # 7        6         5          4     3   2      1  0
    # RESERVED READ_ONLY WRITE_ONLY RD_WR OTP STICKY NU NU
    # NU - not used
    # attr_reserved = 7
    # attr_read_only = 6
    # attr_write_only = 5
    # attr_rd_wr = 4
    # attr_otp = 3
    # attr_sticky = 2
    # self.metadata = [Array(Signal(8) for y in range(CW_ALL_NUM))]


# Control Word Space
#
# -----------------------0x00
# 96 directly addressed registers
# -----------------------0x5F (95d)

# -----------------------0x60 (96d)
# 32 page pointer RW
# -----------------------0x7F (127d)

#
# 256 Pages of 32 registers
#


# Table 88
# Name, Address, Description, Global (Only Channel A)
CONTROL_WORD_DECODING = [
    ["RW00", 0x00, "Global Features", "Yes"],
    ["RW01", 0x01, "Parity, CMD Blocking, and Alert", "Yes"],
    ["RW02", 0x02, "Host Interface Training Mode", "Yes"],
    ["RW03", 0x03, "DRAM & DB Interface Training Mode", "Yes"],
    ["RW04", 0x04, "Command Space", "Yes"],
    ["RW05", 0x05, "DIMM Operating Speed", "Yes"],
    ["RW06", 0x06, "Fine Granularity DIMM Operating Speed", "Yes"],
    ["RW07", 0x07, "Validation Pass-Through and Lockout Protection", "Yes"],
    ["RW08", 0x08, "Clock Driver Enable", "No"],
    ["RW09", 0x09, "Output Address and Control Enable", "No"],
    ["RW0A", 0x0A, "QCK Signals Driver Characteristics", "No"],
    ["RW0B", 0x0B, "Reserved", "No"],
    ["RW0C", 0x0C, "QCA and QxCS_n Signals Characteristics", "No"],
    ["RW0D", 0x0D, "Data Buffer Interface Driver Characteristics", "No"],
    ["RW0E", 0x0E, "QCK, QCA and QCS Output Slew Rate", "No"],
    ["RW0F", 0x0F, "BCK, BCOM and BCS Output Slew Rate", "No"],
    ["RW10", 0x10, "IBT", "Yes"],
    ["RW11", 0x11, "Command Latency Adder", "No"],
    ["RW12", 0x12, "QACK Output Delay", "No"],
    ["RW13", 0x13, "QBCK Output Delay", "No"],
    ["RW14", 0x14, "QCCK Output Delay Control", "No"],
    ["RW15", 0x15, "QDCK Output Delay Control", "No"],
    ["RW16", 0x16, "Reserved", "No"],
    ["RW17", 0x17, "QACS0 Output Delay", "No"],
    ["RW18", 0x18, "QACS1 Output Delay", "No"],
    ["RW19", 0x19, "QBCS0 Output Delay", "No"],
    ["RW1A", 0x1A, "QBCS1 Output Delay", "No"],
    ["RW1B", 0x1B, "QACA Output Delay", "No"],
    ["RW1C", 0x1C, "QBCA Output Delay", "No"],
    ["RW1D", 0x1D, "BCS and BCOM Output Delay", "No"],
    ["RW1E", 0x1E, "BCK Output Delay", "No"],
    ["RW1F", 0x1F, "Reserved", "No"],
    ["RW20", 0x20, "Error Log Register", "No"],
    ["RW21", 0x21, "Error Log Register", "No"],
    ["RW22", 0x22, "Error Log Register", "No"],
    ["RW23", 0x23, "Error Log Register", "No"],
    ["RW24", 0x24, "Error Log Register", "No"],
    ["RW25", 0x25, "SidebandBus", "Yes"],
    ["RW26", 0x26, "Loopback", "Yes"],
    ["RW27", 0x27, "Loop-back I/O", "Yes"],
    ["RW28", 0x28, "I2C & I3C Basic Error Status", "Yes"],
    ["RW29", 0x29, "I2C & I3C Basic Clear Error Status", "Yes"],
    ["RW2A", 0x2A, "Vendor Specific", "Yes"],
    ["RW2B", 0x2B, "Reserved", "No"],
    ["RW2C", 0x2C, "Reserved", "No"],
    ["RW2D", 0x2D, "Reserved", "No"],
    ["RW2E", 0x2E, "Reserved", "No"],
    ["RW2F", 0x2F, "Reserved", "No"],
    ["RW30", 0x30, "DFE_Vref Range Limit", "Yes"],
    ["RW31", 0x31, "DFE Configuration", "No"],
    ["RW32", 0x32, "DPAR and DCA[6:0] DFE Training Mode", "No"],
    ["RW33", 0x33, "Additional Filtering for DFE Training Mode", "No"],
    ["RW34", 0x34, "LFSR DFE Training Mode", "No"],
    ["RW35", 0x35, "LFSR State for DFE Training Mode", "No"],
    ["RW36", 0x36, "DFETM Inner Loop Start Value", "No"],
    ["RW37", 0x37, "DFETM Outer Loop Start Value", "No"],
    ["RW38", 0x38, "DFETM Inner Loop Current Value", "No"],
    ["RW39", 0x39, "DFETM Outer Loop Current Value", "No"],
    ["RW3A", 0x3A, "DFETM Inner and Outer Loop Step Size", "No"],
    ["RW3B", 0x3B, "DFETM Inner Loop Number of Increments", "No"],
    ["RW3C", 0x3C, "DFETM Outer Loop Number of Increments", "No"],
    ["RW3D", 0x3D, "DFETM Inner Loop Current Increment", "No"],
    ["RW3E", 0x3E, "DFETM Outer Loop Current Increment", "No"],
    ["RW3F", 0x3F, "DFE Vref Range Selection", "No"],
    ["RW40", 0x40, "DCA0 Internal Vref", "No"],
    ["RW41", 0x41, "DCA1 Internal Vref", "No"],
    ["RW42", 0x42, "DCA2 Internal Vref", "No"],
    ["RW43", 0x43, "DCA3 Internal Vref", "No"],
    ["RW44", 0x44, "DCA4 Internal Vref", "No"],
    ["RW45", 0x45, "DCA5 Internal Vref", "No"],
    ["RW46", 0x46, "DCA6 Internal Vref", "No"],
    ["RW47", 0x47, "DPAR Internal Vref", "No"],
    ["RW48", 0x48, "DCS0 Internal Vref", "No"],
    ["RW49", 0x49, "DCS1 Internal Vref", "No"],
    ["RW4A", 0x4A, "DERROR_IN_n Vref", "No"],
    ["RW4B", 0x4B, "Loop-Back Vref", "No"],
    ["RW4C", 0x4C, "Reserved", "No"],
    ["RW4D", 0x4D, "Reserved", "No"],
    ["RW4E", 0x4E, "Reserved", "No"],
    ["RW4F", 0x4F, "Reserved", "No"],
    ["RW50", 0x50, "Reserved", "No"],
    ["RW51", 0x51, "Reserved", "No"],
    ["RW52", 0x52, "Reserved", "No"],
    ["RW53", 0x53, "Reserved", "No"],
    ["RW54", 0x54, "Reserved", "No"],
    ["RW55", 0x55, "Reserved", "No"],
    ["RW56", 0x56, "Reserved", "No"],
    ["RW57", 0x57, "Reserved", "No"],
    ["RW58", 0x58, "Reserved", "No"],
    ["RW59", 0x59, "Reserved", "No"],
    ["RW5A", 0x5A, "Reserved", "No"],
    ["RW5B", 0x5B, "Reserved", "No"],
    ["RW5C", 0x5C, "Reserved", "No"],
    ["RW5D", 0x5D, "Reserved", "No"],
    ["RW5E", 0x5E, "CW Read Pointer", "No"],
    ["RW5F", 0x5F, "CW Page", "No"],
]


# Name, Address, Bits selector
sticky_bits = [
    ["RW00", 0x00, "[1:0]"],
    ["RW05", 0x05, "[3:0]"],
    ["RW05", 0x05, "[6:5]"],
    ["RW06", 0x06, "[7:0]"],
    ["RW08", 0x08, "[7:0]"],
    ["RW09", 0x09, "[7:0]"],
    ["RW0A", 0x0A, "[7:0]"],
    ["RW0C", 0x0C, "[7:0]"],
    ["RW0D", 0x0D, "[7:0]"],
    ["RW0E", 0x0E, "[7:0]"],
    ["RW0F", 0x0F, "[7:0]"],
    ["RW10", 0x10, "[7:0]"],
    ["RW11", 0x11, "[7:0]"],
    ["RW12", 0x12, "[7:0]"],
    ["RW13", 0x13, "[7:0]"],
    ["RW14", 0x14, "[7:0]"],
    ["RW15", 0x15, "[7:0]"],
    ["RW17", 0x17, "[7:0]"],
    ["RW18", 0x18, "[7:0]"],
    ["RW19", 0x19, "[7:0]"],
    ["RW1A", 0x1A, "[7:0]"],
    ["RW1B", 0x1B, "[7:0]"],
    ["RW1C", 0x1C, "[7:0]"],
    ["RW1D", 0x1D, "[7:0]"],
    ["RW1E", 0x1E, "[7:0]"],
    ["RW25", 0x25, "[5]"],
    ["RW28", 0x28, "[7:0]"],
    ["RW31", 0x31, "[7:0]"],
    ["RW40", 0x40, "[7:0]"],
    ["RW41", 0x41, "[7:0]"],
    ["RW42", 0x42, "[7:0]"],
    ["RW43", 0x43, "[7:0]"],
    ["RW44", 0x44, "[7:0]"],
    ["RW45", 0x45, "[7:0]"],
    ["RW46", 0x46, "[7:0]"],
    ["RW47", 0x47, "[7:0]"],
    ["RW48", 0x48, "[7:0]"],
    ["RW49", 0x49, "[7:0]"],
]

sticky_pages = [
    ["PG[1]RW", [1], [0x61, 0x69, 0x71, 0x79],
        "DPAR and DCA[6:0] Receiver DFE Tap 1 Coefficients"],
    ["PG[0]RW", [0], [0x61, 0x69, 0x71, 0x79],
        "DPAR and DCA[6:0] Receiver DFE Tap 1 Coefficients"],
    ["PG[1]RW", [1], [0x62, 0x6A, 0x72, 0x7A],
        "DPAR and DCA[6:0] Receiver DFE Tap 2 Coefficients"],
    ["PG[0]RW", [0], [0x62, 0x6A, 0x72, 0x7A],
        "DPAR and DCA[6:0] Receiver DFE Tap 2 Coefficients"],
    ["PG[1]RW", [1], [0x63, 0x6B, 0x73, 0x7B],
        "DPAR and DCA[6:0] Receiver DFE Tap 3 Coefficients"],
    ["PG[0]RW", [0], [0x63, 0x6B, 0x73, 0x7B],
        "DPAR and DCA[6:0] Receiver DFE Tap 3 Coefficients"],
    ["PG[1]RW", [1], [0x64, 0x6C, 0x74, 0x7C],
        "DPAR and DCA[6:0] Receiver DFE Tap 4 Coefficients"],
    ["PG[0]RW", [0], [0x64, 0x6C, 0x74, 0x7C],
        "DPAR and DCA[6:0] Receiver DFE Tap 4 Coefficients"],
    ["PG[1]RW", [1], [0x60, 0x68, 0x70, 0x78],
        "DPAR and DCA[6:0] Receiver DFE Gain Offset Adjustment"],
    ["PG[0]RW", [0], [0x60, 0x68, 0x70, 0x78],
        "DPAR and DCA[6:0] Receiver DFE Gain Offset Adjustment"],
]

rcd_pages = {
    "rcd_generic": [
        ["RW60", 0x60, "not implemented"],
        ["RW61", 0x61, "not implemented"],
        ["RW62", 0x62, "not implemented"],
        ["RW63", 0x63, "not implemented"],
        ["RW64", 0x64, "not implemented"],
        ["RW65", 0x65, "not implemented"],
        ["RW66", 0x66, "not implemented"],
        ["RW67", 0x67, "not implemented"],
        ["RW68", 0x68, "not implemented"],
        ["RW69", 0x69, "not implemented"],
        ["RW6A", 0x6A, "not implemented"],
        ["RW6B", 0x6B, "not implemented"],
        ["RW6C", 0x6C, "not implemented"],
        ["RW6D", 0x6D, "not implemented"],
        ["RW6E", 0x6E, "not implemented"],
        ["RW6F", 0x6F, "not implemented"],
        ["RW70", 0x70, "not implemented"],
        ["RW71", 0x71, "not implemented"],
        ["RW72", 0x72, "not implemented"],
        ["RW73", 0x73, "not implemented"],
        ["RW74", 0x74, "not implemented"],
        ["RW75", 0x75, "not implemented"],
        ["RW76", 0x76, "not implemented"],
        ["RW77", 0x77, "not implemented"],
        ["RW78", 0x78, "not implemented"],
        ["RW79", 0x79, "not implemented"],
        ["RW7A", 0x7A, "not implemented"],
        ["RW7B", 0x7B, "not implemented"],
        ["RW7C", 0x7C, "not implemented"],
        ["RW7D", 0x7D, "not implemented"],
        ["RW7E", 0x7E, "not implemented"],
        ["RW7F", 0x7F, "not implemented"],],
    "rcd_page_0": [
        ["RW60", 0x60, "DCA0 Rx DFE Gain Coefficients"],
        ["RW61", 0x61, "DCA0 Rx DFE Tap 1 Coefficients"],
        ["RW62", 0x62, "DCA0 Rx DFE Tap 2 Coefficients"],
        ["RW63", 0x63, "DCA0 Rx DFE Tap 3 Coefficients"],
        ["RW64", 0x64, "DCA0 Rx DFE Tap 4 Coefficients"],
        ["RW65", 0x65, "RFU   "],
        ["RW66", 0x66, "RFU   "],
        ["RW67", 0x67, "RFU   "],
        ["RW68", 0x68, "DCA1 Rx DFE Gain Coefficients"],
        ["RW69", 0x69, "DCA1 Rx DFE Tap 1 Coefficients"],
        ["RW6A", 0x6A, "DCA1 Rx DFE Tap 2 Coefficients"],
        ["RW6B", 0x6B, "DCA1 Rx DFE Tap 3 Coefficients"],
        ["RW6C", 0x6C, "DCA1 Rx DFE Tap 4 Coefficients"],
        ["RW6D", 0x6D, "RFU   "],
        ["RW6E", 0x6E, "RFU   "],
        ["RW6F", 0x6F, "RFU   "],
        ["RW70", 0x70, "DCA2 Rx DFE Gain Coefficients"],
        ["RW71", 0x71, "DCA2 Rx DFE Tap 1 Coefficients"],
        ["RW72", 0x72, "DCA2 Rx DFE Tap 2 Coefficients"],
        ["RW73", 0x73, "DCA2 Rx DFE Tap 3 Coefficients"],
        ["RW74", 0x74, "DCA2 Rx DFE Tap 4 Coefficients"],
        ["RW75", 0x75, "RFU   "],
        ["RW76", 0x76, "RFU   "],
        ["RW77", 0x77, "RFU   "],
        ["RW78", 0x78, "DCA3 Rx DFE Gain Coefficients"],
        ["RW79", 0x79, "DCA3 Rx DFE Tap 1 Coefficients"],
        ["RW7A", 0x7A, "DCA3 Rx DFE Tap 2 Coefficients"],
        ["RW7B", 0x7B, "DCA3 Rx DFE Tap 3 Coefficients"],
        ["RW7C", 0x7C, "DCA3 Rx DFE Tap 4 Coefficients"],
        ["RW7D", 0x7D, "RFU   "],
        ["RW7E", 0x7E, "RFU   "],
        ["RW7F", 0x7F, "RFU   "],]
}


if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
