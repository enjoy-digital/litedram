import re

from migen import *


# MPC (multipurpose command) can be used to perform different actions
# We use ZQC with BA=0 to issue MPC, where OP[6:0] = A[6:0]
MPC = {
    "NOP":           0b0000000,  # only OP[6] must be 0
    "READ-FIFO":     0b1000001,
    "READ-DQ-CAL":   0b1000011,
    # RFU:           0b1000101
    "WRITE-FIFO":    0b1000111,
    # RFU:           0b1001001
    "START-DQS-OSC": 0b1001011,
    "STOP-DQS-OSC":  0b1001101,
    "ZQC-START":     0b1001111,
    "ZQC-LATCH":     0b1010001,
}


class DFIPhaseAdapter(Module):
    """Translates DFI phase into LPDDR4 command (2- or 4-cycle)

    LPDDR4 "full command" consists of 1 or 2 "small commands". Each "small command"
    is transmitted over 2 DRAM clock cycles (SDR). This module translates DFI commands
    on a single DFI phase into sequencs on CS/CA[5:0] buses (4 cycles). Some DFI commands
    consist only of a single "small command". To make counting DRAM timings easier, such
    a "small command" shall be sent on the 2nd slot (i.e. 3rd and 4th cycle). All timings
    are then counted starting from CS low on the 4th cycle.
    """

    def __init__(self, dfi_phase):
        # CS/CA values for 4 SDR cycles
        self.cs = Signal(4)
        self.ca = Array([Signal(6) for _ in range(4)])
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

        def cmds(cmd1, cmd2, valid=1):
            return self.cmd1.set(cmd1) + self.cmd2.set(cmd2) + [self.valid.eq(valid)]

        self.comb += If(dfi_phase.cs_n == 0,  # require dfi.cs_n
            Case(dfi_cmd, {
                _cmd["ACT"]: cmds("ACTIVATE-1", "ACTIVATE-2"),
                _cmd["RD"]:  cmds("READ-1",     "CAS-2"),
                _cmd["WR"]:  cmds("WRITE-1",    "CAS-2"),  # TODO: masked write
                _cmd["PRE"]: cmds("DESELECT",   "PRECHARGE"),
                _cmd["REF"]: cmds("DESELECT",   "REFRESH"),
                _cmd["ZQC"]: cmds("DESELECT",   "MPC"),
                _cmd["MRS"]: cmds("MRW-1",      "MRW-2"),
                "default":   cmds("DESELECT",   "DESELECT", valid=0),
            })
        )


class Command(Module):
    """LPDDR4 command decoder

    Decodes a command from single DFI phase into LPDDR4 "small command"
    consisting of 2 CS values and 2 CA[5:0] values.

    LPDDR4 "small commands" are transmited over 2 clock cycles. In first
    cycle CS is driven high and in the second cycle it stays low. In each
    of the cycles the bits on CA[5:0] are latched and interpreted differently.
    This module translates a DFI command into the values of CS/CA that shall
    be transmitted over 2 DRAM clock cycles.
    """

    # String description of 1st and 2nd edge of each command, later parsed to
    # construct the value. CS is assumed to be H for 1st edge and L for 2nd edge.
    TRUTH_TABLE = {
        "MRW-1":        ["L H H L L OP7",       "MA0 MA1 MA2 MA3 MA4 MA5"],
        "MRW-2":        ["L H H L H OP6",       "OP0 OP1 OP2 OP3 OP4 OP5"],
        "MRR-1":        ["L H H H L V",         "MA0 MA1 MA2 MA3 MA4 MA5"],
        "REFRESH":      ["L L L H L AB",        "BA0 BA1 BA2 V V V"],
        "ACTIVATE-1":   ["H L R12 R13 R14 R15", "BA0 BA1 BA2 R16 R10 R11"],
        "ACTIVATE-2":   ["H H R6 R7 R8 R9",     "R0 R1 R2 R3 R4 R5"],
        "WRITE-1":      ["L L H L L BL",        "BA0 BA1 BA2 V C9 AP"],
        "MASK WRITE-1": ["L L H H L BL",        "BA0 BA1 BA2 V C9 AP"],
        "READ-1":       ["L H L L L BL",        "BA0 BA1 BA2 V C9 AP"],
        "CAS-2":        ["L H L L H C8",        "C2 C3 C4 C5 C6 C7"],
        "PRECHARGE":    ["L L L L H AB",        "BA0 BA1 BA2 V V V"],
        "MPC":          ["L L L L L OP6",       "OP0 OP1 OP2 OP3 OP4 OP5"],
        "DESELECT":     ["X X X X X X",         "X X X X X X"],
    }

    for cmd, (subcmd1, subcmd2) in TRUTH_TABLE.items():
        assert len(subcmd1.split()) == 6, (cmd, subcmd1)
        assert len(subcmd2.split()) == 6, (cmd, subcmd2)

    def __init__(self, dfi_phase):
        self.cs = Signal(2)
        self.ca = Array([Signal(6), Signal(6)])  # CS high, CS low
        self.dfi = dfi_phase

    def set(self, cmd):
        ops = []
        for i, description in enumerate(self.TRUTH_TABLE[cmd]):
            for j, bit in enumerate(description.split()):
                ops.append(self.ca[i][j].eq(self.parse_bit(bit, is_mpc=cmd == "MPC")))
        if cmd != "DESELECT":
            ops.append(self.cs[0].eq(1))
        return ops

    def parse_bit(self, bit, is_mpc=False):
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
            "MA(\d+)": lambda i: self.dfi.address[8+i],  # mode register address
            "OP(\d+)": lambda i: self.dfi.address[i],  # mode register value, or operand for MPC
        }
        for pattern, value in rules.items():
            m = re.match(pattern, bit)
            if m:
                args = [int(g) for g in m.groups()]
                return value(*args)
        raise ValueError(bit)
