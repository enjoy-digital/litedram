#
# This file is part of LiteDRAM.
#
# Copyright (c) 2022 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import re
import enum

from migen import *

@enum.unique
class SpecialCmd(enum.IntEnum):
    """Codes for special commands encoded in DFI ZQC command

    The number of possible commands in DDR5 is too big to encode them
    in DFI in the regular way. Currently the DFI ZQC command is used to
    encode several DDR5 commands depending on the value of DFI.bank.

    NOTE: This encoding is still subject to change if needed.

    The following commands are possible:
    * MPC - uses DFI.address as the op code for DDR5 MPC command
    * MRR - uses DFI.address as Moder Register address to be read
    """
    MPC = 0
    MRR = 1

@enum.unique
class MPC(enum.IntEnum):
    """Op codes for DDR5 multipurpose command

    DFI ZQC command is used to send DDR5 MPC. DFI address A[7:0] is
    translated to MPC op code OP[7:0]. DFI bank address BA should be 0.
    """

    CS_EX     = 0b00000000 # Exit CS training mode
    CS_EN     = 0b00000001 # Enter CS training mode
    DLL_RST   = 0b00000010
    CA_EN     = 0b00000011 # Enter CA training mode
    ZQC_LATCH = 0b00000100
    ZQC_START = 0b00000101
    RFU       = 0b00001101

class DFIPhaseAdapter(Module):
    """Translates DFI phase into DDR5 command (2-cycle)

    Each DDR5 command is transmitted over 2 DRAM clock cycles (SDR). This module translates DFI commands
    on a single DFI phase into sequencs on CS_n/CA[13:0] buses (2 cycles).

    Parameters
    ----------
    dfi_phase : Record(dfi.phase_description), in
        Input from a single DFI phase.
    masked_write : bool or Signal(1)
        Specifies if masked write variant of write command should be chosen.

    Attributes
    ----------
    cs : Array(2, Signal(nranks)), out
        Values of CS on 2 subsequent DRAM SDR clock cycles.
    ca : Array(2, Signal(14)), out
        Values of CA[13:0] on 2 subsequent DRAM SDR clock cycles.
    valid : Signal, out
        Indicates that a valid command is presented on the `cs` and `ca` outputs.
    """
    def __init__(self, dfi_phase, masked_write=True):
        # CS/CA values for 2 SDR cycles
        self.cs_n     = Array([Signal(len(dfi_phase.cs_n)) for _ in range(2)])
        self.cke      = Array([Signal(len(dfi_phase.cke)) for _ in range(2)])
        self.odt      = Array([Signal(len(dfi_phase.odt)) for _ in range(2)])
        self.reset_n  = Array([Signal() for _ in range(2)])
        self.act_n    = Array([Signal() for _ in range(2)])
        self.mode_2n  = Array([Signal() for _ in range(2)])
        self.ca       = Array([Signal(14) for _ in range(2)])
        self.valid = Signal()

        # # #

        self.submodules.cmd = Command(dfi_phase, masked_write)
        for i in range(2):
            self.comb += [
                self.cs_n[i].eq(self.cmd.cs_n[i]),
                self.cke[i].eq(dfi_phase.cke),
                self.odt[i].eq(dfi_phase.odt),
                self.reset_n[i].eq(dfi_phase.reset_n),
                self.act_n[i].eq(dfi_phase.act_n),
                self.mode_2n[i].eq(dfi_phase.mode_2n),
                self.ca[i].eq(self.cmd.ca[i]),
            ]

        dfi_cmd = Signal(3)
        self.comb += dfi_cmd.eq(Cat(~dfi_phase.we_n, ~dfi_phase.ras_n, ~dfi_phase.cas_n)),
        _cmd = {  # cas, ras, we
            "NOP": 0b000,
            "ZQC": 0b001,
            "ACT": 0b010,
            "PRE": 0b011,
            "RD":  0b100,
            "WR":  0b101,
            "REF": 0b110,
            "MRS": 0b111,
        }

        def cmds(cmd, valid=1):
            return self.cmd.set(cmd) + [self.valid.eq(valid)]

        self.comb += If(dfi_phase.cs_n == 0,  # require dfi.cs_n
            Case(dfi_cmd, {
                _cmd["ACT"]: cmds("ACTIVATE"),
                _cmd["RD"]:  cmds("READ"),
                _cmd["WR"]:  cmds("WRITE"),
                _cmd["PRE"]: cmds("PRECHARGE ALL"),
                _cmd["REF"]: cmds("REFRESH ALL"),
                # Use bank address to select command type
                _cmd["ZQC"]: Case(dfi_phase.bank, {
                    SpecialCmd.MPC: cmds("MPC"),
                    SpecialCmd.MRR: cmds("MRR"),
                    "default": cmds("DESELECT", valid=0),
                }),
                _cmd["MRS"]: cmds("MRW"),
                "default": cmds("DESELECT", valid=0),
            })
        ).Else(cmds("DESELECT", valid=0))


class Command(Module):
    """DDR5 command decoder

    Decodes a command from single DFI phase into DDR5 command
    consisting of 2 CS values and 2 CA[13:0] values.

    DDR5 commands are transmited over 2 clock cycles. In the first
    cycle CS_n is driven low and in the second cycle it stays high. In each
    of the cycles the bits on CA[13:0] are latched and interpreted differently.
    This module translates a DFI command into the values of CS_n/CA that shall
    be transmitted over 2 DRAM clock cycles.

    Attributes
    ----------
    dfi : Record(dfi.phase_description), in
        Input from single DFI phase.
    cs_n : Signal(2), out
        CS_n values over 2 subsequent DRAM SDR clock cycles.
    ca : Array(2, Signal(14)), out
        CA[13:0] values over 2 subsequent DRAM SDR clock cycles.
    """

    # String description of 1st and 2nd edge of each command, later parsed to
    # construct the value. CS_n is assumed to be L for 1st edge and H for 2nd edge.

    TRUTH_TABLE = {
        # 2-cycle commands:
        "ACTIVATE":      ["L L R0 R1 R2 R3 BA0 BA1 BG0 BG1 BG2 CID0 CID1 CID2",
                          "R4 R5 R6 R7 R8 R9 R10 R11 R12 R13 R14 R15 R16 CID3/R17"],
        "READ":          ["H L H H H BL BA0 BA1 BG0 BG1 BG2 CID0 CID1 CID2",
                          "C2 C3 C4 C5 C6 C7 C8 C9 C10 V H V V CID3"],
        "WRITE":         ["H L H H L BL BA0 BA1 BG0 BG1 BG2 CID0 CID1 CID2",
                          "V C3 C4 C5 C6 C7 C8 C9 C10 V H WRP V CID3"],
        "MRR":           ["H L H L H MRA0 MRA1 MRA2 MRA3 MRA4 MRA5 MRA6 MRA7 V",
                          "L L V V V V V V V V CW V V V"],
        "MRW":           ["H L H L L MRA0 MRA1 MRA2 MRA3 MRA4 MRA5 MRA6 MRA7 V",
                          "OP0 OP1 OP2 OP3 OP4 OP5 OP6 OP7 V V CW V V V"],
        # 1-cycle commands:
        "PRECHARGE ALL": ["H H L H L CID3 V V V V L CID0 CID1 CID2",
                          "X X X X X X X X X X X X X X"],
        "REFRESH ALL":   ["H H L L H CID3 V V VorRIR VorH L CID0 CID1 CID2",
                          "X X X X X X X X X X X X X X"],
        "MPC":           ["H H H H L OP0 OP1 OP2 OP3 OP4 OP5 OP6 OP7 V",
                          "X X X X X X X X X X X X X X"],
        "DESELECT":      ["X X X X X X X X X X X X X X",
                          "X X X X X X X X X X X X X X"]
    }

    # BL is abbreviation for BL*=L from table from standard
    # WRP is abbreviation for WR_partial=L

    for cmd, (ca_pins_low, ca_pins_high) in TRUTH_TABLE.items():
        assert len(ca_pins_low.split()) == 14, (cmd, ca_pins_low)
        assert len(ca_pins_high.split()) == 14, (cmd, ca_pins_high)

    def __init__(self, dfi_phase, masked_write):
        self.cs_n = Array([Signal(), Signal()])
        self.ca = Array([Signal(14), Signal(14)])  # CS_n low, CS_n high
        self.dfi = dfi_phase
        self.masked_write = masked_write

    def set(self, cmd):
        ops = []
        for cyc, description in enumerate(self.TRUTH_TABLE[cmd]):
            for bit, bit_desc in enumerate(description.split()):
                ops.append(self.ca[cyc][bit].eq(self.parse_bit(bit_desc, is_mrw=(cmd == "MRW"))))

        if cmd == "DESELECT":
            ops.append(self.cs_n[0].eq(1))
            ops.append(self.cs_n[1].eq(1))
        else:
            ops.append(self.cs_n[0].eq(0)) # CS_n needs to be low on the first cycle
            ops.append(self.cs_n[1].eq(1)) # CS_n needs to be high on the second cycle

        return ops

    def parse_bit(self, bit, is_mrw):
        assert len(self.dfi.bank) >= 8, "At least 8 DFI bankbits needed for Mode Register address"
        assert len(self.dfi.address) >= 18, "At least 18 DFI addressbits needed for row address"
        mr_address = self.dfi.bank if is_mrw else self.dfi.address
        rules = {
            r"H":        lambda: 1,  # high
            r"L":        lambda: 0,  # low
            r"V":        lambda: 0,  # defined logic
            r"X":        lambda: 0,  # don't care
            r"BL":       lambda: 0,  # Force BL8 for time being
            r"WRP":      lambda: ~self.masked_write,  # LOW value means masked variant
            r"VorRIR":   lambda: 0,  # Assume for now that Refresh Management Required bit is 0
            r"VorH":     lambda: 1,  # depending Refresh Management Required bit, it has to be just valid or H, let's use 1 as more general
            r"BG(\d+)":  lambda i: self.dfi.bank[i + 2],  # bank group address
            r"BA(\d+)":  lambda i: self.dfi.bank[i],  # bank address
            r"R(\d+)":   lambda i: self.dfi.address[i],  # row
            r"C(\d+)":   lambda i: self.dfi.address[i],  # column
            r"MRA(\d+)": lambda i: mr_address[i],  # mode register address
            r"OP(\d+)":  lambda i: self.dfi.address[i],  # mode register value, or operand for MPC
            r"CID(\d+)": lambda i: 0,  # chip id; used for 3DS stacking, need to be just valid if unused
            r"CID3/R17": lambda: self.dfi.address[17],  # we chose R17 variant, because 3DS stacking is unsupported for now
            r"CW":       lambda: 0  # control word
        }
        for pattern, value in rules.items():
            m = re.fullmatch(pattern, bit)
            if m:
                args = [int(g) for g in m.groups()]
                return value(*args)
        raise ValueError(bit)
