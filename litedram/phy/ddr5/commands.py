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

    DFI ZQC command is used to send DDR5 MPC. DFI address A[6:0] is
    translated to MPC op code OP[6:0]. DFI bank address BA should be 0.
    """
    NOP           = 0b0000000  # only OP[6] must be 0
    READ_FIFO     = 0b1000001
    READ_DQ_CAL   = 0b1000011
    # RFU           0b1000101
    WRITE_FIFO    = 0b1000111
    # RFU           0b1001001
    START_DQS_OSC = 0b1001011
    STOP_DQS_OSC  = 0b1001101
    ZQC_START     = 0b1001111
    ZQC_LATCH     = 0b1010001


class DFIPhaseAdapter(Module):
    """Translates DFI phase into DDR5 command (2- or 4-cycle)

    DDR5 "full command" consists of 1 or 2 "small commands". Each "small command"
    is transmitted over 2 DRAM clock cycles (SDR). This module translates DFI commands
    on a single DFI phase into sequencs on CS/CA[5:0] buses (4 cycles). Some DFI commands
    consist only of a single "small command". To make counting DRAM timings easier, such
    a "small command" shall be sent on the 2nd slot (i.e. 3rd and 4th cycle). All timings
    are then counted starting from CS low on the 4th cycle.

    Parameters
    ----------
    dfi_phase : Record(dfi.phase_description), in
        Input from a single DFI phase.
    masked_write : bool or Signal(1)
        Specifies how DFI write command (cas_n=0, ras_n=1, we_n=0) is interpreted, either
        as DDR5 WRITE or MASKED-WRITE. MASKED-WRITE requires larger tCCD, but WRITE does
        not permit masking of data, so if masking is needed MASKED-WRITE has to be used.

    Attributes
    ----------
    cs : Signal(4), out
        Values of CS on 4 subsequent DRAM SDR clock cycles.
    ca : Array(4, Signal(6)), out
        Values of CA[5:0] on 4 subsequent DRAM SDR clock cycles.
    valid : Signal, out
        Indicates that a valid command is presented on the `cs` and `ca` outputs.
    """
    def __init__(self, dfi_phase, masked_write=True):
        assert isinstance(masked_write, (bool, Signal)), "Use boolean (static) or Signal (dynamic)"
        if isinstance(masked_write, bool):
            masked_write = int(masked_write)
        else:
            assert len(masked_write) == 1

        # CS/CA values for 4 SDR cycles
        self.cs = Signal(4)
        self.ca = Array([Signal(14) for _ in range(4)])
        self.valid = Signal()

        # # #

        self.submodules.cmd1 = Command(dfi_phase)
        self.submodules.cmd2 = Command(dfi_phase)
        self.comb += [
            self.cs[:2].eq(self.cmd1.cs),
            self.cs[2:].eq(self.cmd2.cs),
            self.ca[0].eq(self.cmd1.ca[0]),
            self.ca[1].eq(self.cmd1.ca[1]),
            self.ca[2].eq(self.cmd2.ca[0]),
            self.ca[3].eq(self.cmd2.ca[1]),
        ]

        dfi_cmd = Signal(3)
        self.comb += dfi_cmd.eq(Cat(~dfi_phase.we_n, ~dfi_phase.ras_n, ~dfi_phase.cas_n)),
        _cmd = {  # cas, ras, we
            "NOP": 0b000,
            "ACT": 0b010,
            "RD":  0b100,
            "WR":  0b101,
            "PRE": 0b011,
            "REF": 0b110,
            "ZQC": 0b001,
            "MRS": 0b111,
        }

        def cmds(cmd2, valid=1):
            return self.cmd1.set("DESELECT") + self.cmd2.set(cmd2) + [self.valid.eq(valid)]

        self.comb += If(dfi_phase.cs_n == 0,  # require dfi.cs_n
            Case(dfi_cmd, {
                _cmd["ACT"]: cmds("ACTIVATE"),
                _cmd["RD"]:  cmds("READ"),
                _cmd["WR"]:  cmds("WRITE"),
                _cmd["PRE"]: cmds("PRECHARGE"),
                _cmd["REF"]: cmds("REFRESH"),
                # Use bank address to select command type
                _cmd["ZQC"]: Case(dfi_phase.bank, {
                    SpecialCmd.MPC: cmds("MPC"),
                    SpecialCmd.MRR: cmds("MRR"),
                    "default": cmds("DESELECT", valid=0),
                }),
                _cmd["MRS"]: cmds("MRW"),
                "default": cmds("DESELECT", valid=0),
            })
        )


class Command(Module):
    """DDR5 command decoder

    Decodes a command from single DFI phase into DDR5 "small command"
    consisting of 2 CS values and 2 CA[5:0] values.

    DDR5 "small commands" are transmited over 2 clock cycles. In the first
    cycle CS is driven high and in the second cycle it stays low. In each
    of the cycles the bits on CA[5:0] are latched and interpreted differently.
    This module translates a DFI command into the values of CS/CA that shall
    be transmitted over 2 DRAM clock cycles.

    Attributes
    ----------
    dfi : Record(dfi.phase_description), in
        Input from single DFI phase.
    cs : Signal(2), out
        CS values over 2 subsequent DRAM SDR clock cycles.
    ca : Array(2, Signal(14)), out
        CA[13:0] values over 2 subsequent DRAM SDR clock cycles.
    """

    # String description of 1st and 2nd edge of each command, later parsed to
    # construct the value. CS is assumed to be H for 1st edge and L for 2nd edge.
    # TODO: Fix currently fake truth table to be consistent with the JEDEC specs for DDR5
    TRUTH_TABLE = {
        "MRW-1":        ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "MRW-2":        ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "MRR-1":        ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "REFRESH":      ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "ACTIVATE-1":   ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "ACTIVATE-2":   ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "WRITE-1":      ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "MASK WRITE-1": ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "READ-1":       ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "CAS-2":        ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "PRECHARGE":    ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "MPC":          ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
        "DESELECT":     ["H H H H H H H H H H H H H H", "H H H H H H H H H H H H H H"],
    }

    for cmd, (subcmd1, subcmd2) in TRUTH_TABLE.items():
        assert len(subcmd1.split()) == 14, (cmd, subcmd1)
        assert len(subcmd2.split()) == 14, (cmd, subcmd2)

    def __init__(self, dfi_phase):
        self.cs = Signal(2)
        self.ca = Array([Signal(14), Signal(14)])  # CS high, CS low
        self.dfi = dfi_phase

    def set(self, cmd):
        ops = []
        for cyc, description in enumerate(self.TRUTH_TABLE[cmd]):
            for bit, bit_desc in enumerate(description.split()):
                ops.append(self.ca[cyc][bit].eq(self.parse_bit(bit_desc, is_mrw=cmd.startswith("MRW"))))
        if cmd != "DESELECT":
            ops.append(self.cs[0].eq(1))
        return ops

    def parse_bit(self, bit, is_mrw):
        assert len(self.dfi.bank) >= 8, "At least 8 DFI bankbits needed for Mode Register address"
        assert len(self.dfi.address) >= 17, "At least 17 DFI addressbits needed for row address"
        mr_address = self.dfi.bank if is_mrw else self.dfi.address
        rules = {
            "H":       lambda: 1,  # high
            "L":       lambda: 0,  # low
            "V":       lambda: 0,  # defined logic
            "X":       lambda: 0,  # don't care
            "BL":      lambda: 0,  # on-the-fly burst length, not using
            "AP":      lambda: self.dfi.address[10],  # auto precharge
            "AB":      lambda: self.dfi.address[10],  # all banks
            "BA(\d+)": lambda i: self.dfi.bank[i],
            "R(\d+)":  lambda i: self.dfi.address[i],  # row
            "C(\d+)":  lambda i: self.dfi.address[i],  # column
            "MA(\d+)": lambda i: mr_address[i],  # mode register address
            "OP(\d+)": lambda i: self.dfi.address[i],  # mode register value, or operand for MPC
        }
        for pattern, value in rules.items():
            m = re.match(pattern, bit)
            if m:
                args = [int(g) for g in m.groups()]
                return value(*args)
        raise ValueError(bit)
