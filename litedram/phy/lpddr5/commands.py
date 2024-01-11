# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import re
import enum

from migen import *

@enum.unique
class BankOrganization(enum.IntEnum):
    """Internal organization (architecture) of banks as set in MR[3]"""
    BG = 0b00   # 4 banks, 4 bank groups   (>3200 Mbps)
    B8 = 0b01   # 8 banks, no bank groups  (all data rates, BL32 only)
    B16 = 0b10  # 16 banks, no bank groups (<=3200 Mbps)

@enum.unique
class SpecialCmd(enum.IntEnum):
    """Codes for special commands encoded in DFI ZQC command

    The number of possible commands in LPDDR5 is too big to encode them
    in DFI in the regular way. DFI ZQC command is used to encode several
    special commands depending on the value of DFI.bank using DFI.address
    for additional data.

    NOP can be used to actually send NOP to the DRAM. By default we send
    DESELECT because LiteDRAM keeps holding CS_n low all the time, so we
    would be sending NOPs (toggling LPDDR5 CS pad) all the time.
    """
    MPC = 0
    MRR = 1
    NOP = 2

@enum.unique
class MPC(enum.IntEnum):
    """Op codes for LPDDR5 multipurpose command

    DFI ZQC command is used to send LPDDR5 MPC. DFI address A[7:0] is translated
    to MPC operand OP[7:0]. DFI bank address BA should be equal to SpecialCmd.MPC.
    """
    WCK2DQI_START = 0b10000001
    WCK2DQI_STOP  = 0b10000010
    WCK2DQO_START = 0b10000011
    WCK2DQO_STOP  = 0b10000100
    ZQC_START     = 0b10000101
    ZQC_LATCH     = 0b10000110
    # all others reserved


def dfi_cmd(dfi_phase):
    return Cat(~dfi_phase.we_n, ~dfi_phase.ras_n, ~dfi_phase.cas_n)

CMD = {  # cas, ras, we (2, 1, 0)
    "NOP": 0b000,
    "ACT": 0b010,
    "RD":  0b100,
    "WR":  0b101,
    "PRE": 0b011,
    "REF": 0b110,
    "ZQC": 0b001,
    "MRS": 0b111,
}


@enum.unique
class WCKSyncType(enum.IntEnum):
    """Corresponds to CAS WCK sync flags"""
    WR = 1
    RD = 2
    FS = 3


class DFIPhaseAdapter(Module):
    """Translates DFI phase into LPDDR5 command (2 or 4 CK edges)

    In LPDDR5 a "full command" may consist of 1 or 2 commands. Each command then consists
    of values for 2 consecutive clock edges. For DFI commands that require only 1 LPDDR5
    command, a DESELECT is inserted in on the first 2 CK edges to simplify timing calculations.

    Parameters
    ----------
    dfi_phase : Record(dfi.phase_description), in
        Input from a single DFI phase.
    masked_write : bool or Signal(1)
        Specifies how DFI write command (cas_n=0, ras_n=1, we_n=0) is interpreted, either
        as LPDDR5 WRITE16 or MASKE-WRITE.

    Attributes
    ----------
    cs : Signal(2), out
        Values of CS on 2 subsequent DRAM SDR CK cycles.
    ca : Array(4, Signal(6)), out
        Values of CA[6:0] on 4 subsequent DRAM DDR clock edges.
    valid : Signal, out
        Indicates that a valid command is presented on the `cs` and `ca` outputs.
    wck_sync_done: Signal, in
        Indicates whether WCK synchronization has already been done. PHY must drive
        this signal to control if CAS commands are sent with WCK sync bits.
    wck_sync: Signal(2), out
        Indicates that a CAS command with WCK sync is being sent in this cycle.
        PHY must use this signal to update `wck_sync_done`. The value is one of
        `WCKSyncType` enum, 0 means no WCK sync.
    """
    def __init__(self, dfi_phase, masked_write=True):
        assert isinstance(masked_write, (bool, Signal)), "Use boolean (static) or Signal (dynamic)"
        if isinstance(masked_write, bool):
            masked_write = int(masked_write)
        else:
            assert len(masked_write) == 1

        self.cs = Signal(2)
        self.ca = Array([Signal(7) for _ in range(4)])
        self.valid = Signal()
        self.wck_sync_done = Signal()
        self.wck_sync = Signal(max=len(WCKSyncType))

        # # #

        self.submodules.cmd1 = Command(dfi_phase, self.wck_sync)
        self.submodules.cmd2 = Command(dfi_phase, self.wck_sync)
        self.comb += [
            self.cs[0].eq(self.cmd1.cs),
            self.cs[1].eq(self.cmd2.cs),
            self.ca[0].eq(self.cmd1.ca[0]),
            self.ca[1].eq(self.cmd1.ca[1]),
            self.ca[2].eq(self.cmd2.ca[0]),
            self.ca[3].eq(self.cmd2.ca[1]),
        ]

        def wck_sync(type):
            return If(self.wck_sync_done == 0,
                self.wck_sync.eq(getattr(WCKSyncType, type.upper())),
            )

        def cmds(*cmd, valid=1):
            if len(cmd) == 1:
                ops = self.cmd1.set("DES") + self.cmd2.set(cmd[0])
            elif len(cmd) == 2:
                ops = self.cmd1.set(cmd[0]) + self.cmd2.set(cmd[1])
            else:
                raise ValueError(cmd)
            return ops + [self.valid.eq(valid)]

        # TODO: we don't actually need CAS command if WCK sync is on, but for now
        # send it to avoid problems when tracking module timings
        deselect = cmds("DES", "DES", valid=0)
        self.comb += If(dfi_phase.cs_n == 0,
            Case(dfi_cmd(dfi_phase), {
                CMD["ACT"]: cmds("ACT-1", "ACT-2"),
                CMD["RD"]: [*cmds("CAS", "RD16"), wck_sync("RD")],
                CMD["WR"]:  Case(masked_write, {
                    0: [*cmds("CAS", "WR16"), wck_sync("WR")],
                    1: [*cmds("CAS", "MWR"), wck_sync("WR")],
                }),
                CMD["PRE"]: cmds("PRE"),
                CMD["REF"]: cmds("REF"),
                CMD["ZQC"]: Case(dfi_phase.bank, {
                    SpecialCmd.MPC: cmds("MPC"),
                    SpecialCmd.MRR: [*cmds("CAS", "MRR"), wck_sync("RD")],
                    SpecialCmd.NOP: cmds("NOP"),
                    "default": deselect,
                }),
                CMD["MRS"]: cmds("MRW-1", "MRW-2"),
                "default": deselect,
            })
        )


class Command(Module):
    """LPDDR5 command decoder

    Decode commands from a DFI phase into LPDDR5 command consisting of 1 CS value
    and 2 CA[6:0] values. CA values are then to be sent over 2 CK edges (DDR),
    while CS is an SDR signal.

    Some LPDDR5 commands may consist of 2 separate "small commands", resulting in
    the command being actually sent over 2 CK cycles = 4 edges (e.g. ACT consists
    of ACTIVATE-1 and ACTIVATE-2).

    Attributes
    ----------
    dfi : Record(dfi.phase_description), in
        Input from single DFI phase.
    cs : Signal(), out
        CS value for that CK SDR cycle
    ca : Array(2, Signal(7)), out
        CA[6:0] values over 2 subsequent DRAM DDR clock edges.
    wck_sync : Signal(2), in
        One of `WCKSyncType`, determines WCK sync bit in CAS.
    """

    TRUTH_TABLE = {
        "DES":   "X X X X X X X             | X X X X X X X",       # DESELECT
        "NOP":   "L L L L L L L             | X X X X X X X",       # NO OPERATION
        "PDE":   "L L L L L L H             | X X X X X X X",       # POWER DOWN
        "ACT-1": "H H H R14-17              | BA0-3 R11-13",        # ACTIVATE-1
        "ACT-2": "H H L R7-10               | R0-6",                # ACTIVATE-2
        "PRE":   "L L L H H H H             | BA0-3 V V AB",        # PRECHARGE
        "REF":   "L L L H H H L             | BA0-2 RFM SB0 V AB",  # REFRESH
        "MWR":   "L H L C0 C3-5             | BA0-3 C1-2 AP",       # MASK WRITE
        "WR16":  "L H H C0 C3-5             | BA0-3 C1-2 AP",       # WRITE
        "WR32":  "L L H L C3-5              | BA0-3 C1-2 AP",       # WRITE32
        "RD16":  "H L L C0 C3-5             | BA0-3 C1-2 AP",       # READ
        "RD32":  "H L H C0 C3-5             | BA0-3 C1-2 AP",       # READ32
        "CAS":   "L L H H WS_WR WS_RD WS_FS | DC0-3 WRX WXSA WXSB", # CAS
        "MPC":   "L L L L H H OP7           | OP0-6",               # MULTI PURPOSE COMMAND
        "SRE":   "L L L H L H H             | V V V V V DSM PD",    # SELF REFRESH ENTRY
        "SRX":   "L L L H L H L             | V V V V V V V",       # SELF REFRESH EXIT
        "MRW-1": "L L L H H L H             | MA0-6",               # MODE REGISTER WRITE-1
        "MRW-2": "L L L H L L OP7           | OP0-6",               # MODE REGISTER WRITE-2
        "MRR":   "L L L H H L L             | MA0-6",               # MODE REGISTER READ
        "WFF":   "L L L L L H H             | L L L L L L L",       # WRITE FIFO
        "RFF":   "L L L L L H L             | L L L L L L L",       # READ FIFO
        "RDC":   "L L L L H L H             | L L L L L L L",       # READ DQ CALIBRATION
    }

    def _parse_truth_table(self):
        # transform TRUTH_TABLE to a form: {name: (['H', 'R1', 'R2', ...], [...]), ...}
        tt = {}
        for cmd, desc in self.TRUTH_TABLE.items():
            edges = desc.strip().split("|")
            assert len(edges) == 2, (cmd, desc)
            edges = map(self._parse_ranges, edges)
            pos_edge, neg_edge = map(lambda e: e.strip().split(), edges)
            for e in (pos_edge, neg_edge):
                assert len(neg_edge) == 7, (cmd, desc)
            tt[cmd] = (pos_edge, neg_edge)
        return tt

    def _parse_ranges(self, string):
        def replace(match):
            name = match.group(1)
            start, end = map(int, (match.group(2), match.group(3)))
            return " ".join(f"{name}{num}" for num in range(start, end+1))

        pattern = re.compile(r"([A-Z]+)(\d+)-(\d+)")
        return pattern.sub(replace, string)

    def __init__(self, dfi_phase, wck_sync, bank_organization=BankOrganization.B16):
        if bank_organization != BankOrganization.B16:
            raise NotImplementedError(f"Unsupported: {bank_organization}")
        self.truth_table = self._parse_truth_table()
        self.cs = Signal()
        self.ca = Array([Signal(7), Signal(7)])
        self.wck_sync = wck_sync
        self.dfi = dfi_phase

    def set(self, cmd):
        ops = []
        for edge, bits in enumerate(self.truth_table[cmd]):
            for bit, bit_desc in enumerate(bits):
                ops.append(self.ca[edge][bit].eq(self.parse_bit(bit_desc, cmd)))
        if cmd != "DES":  # only DESELECT has CS low
            ops.append(self.cs.eq(1))
        return ops

    def parse_bit(self, bit, cmd_str):
        assert len(self.dfi.bank) >= 7, "At least 7 DFI addressbits needed for Mode Register address"
        assert len(self.dfi.address) >= 18, "At least 18 DFI addressbits needed for row address"

        cmd = dfi_cmd(self.dfi)

        is_mrw = cmd_str.startswith("MRW")
        is_mpc = cmd_str == "MPC"

        mr_address = self.dfi.bank if is_mrw else self.dfi.address

        mpc_op = Signal(8)
        self.comb += If(self.dfi.address == 0,
            mpc_op.eq(MPC.ZQC_LATCH)
        ).Else(
            mpc_op.eq(self.dfi.address)
        )
        op = mpc_op if is_mpc else self.dfi.address

        rules = {
            "H":        lambda: 1,  # high
            "L":        lambda: 0,  # low
            "V":        lambda: 0,  # defined logic
            "X":        lambda: 0,  # don't care
            "AB":       lambda: self.dfi.address[10],  # all banks
            "AP":       lambda: self.dfi.address[10],  # auto precharge
            "RFM":      lambda: 0,  # TODO: 1=RFM, 0=REF (Refresh Managemenent, only if r/o MR[27][0]=1, else always REF)
            "SB(\\d+)": lambda i: 0,  # sub-bank selection related to RFM
            "WS_WR":    lambda: self.wck_sync == WCKSyncType.WR,  # Write WCK2CK SYNC
            "WS_RD":    lambda: self.wck_sync == WCKSyncType.RD,  # Read WCK2CK SYNC
            "WS_FS":    lambda: self.wck_sync == WCKSyncType.FS,  # FAST SYNC
            "DC(\\d+)": lambda i: 0,  # Data Copy, unimplemented
            "WRX":      lambda: 0,  # Write X function, unimplemented
            "WXSA":     lambda: 0,  # Write X function, unimplemented
            "WXSB":     lambda: 0,  # Write X function, unimplemented
            "BA(\\d+)": lambda i: self.dfi.bank[i],  # only BA0-2 is used, in BG/B16 modes we always refresh banks (x, x+8)
            "R(\\d+)":  lambda i: self.dfi.address[i],  # row
            # LPDDR5 specs split the regular column address into C[5:0] "column address" and B[3:0] "burst address"
            "C(\\d+)":  lambda i: self.dfi.address[i + 4],
            "MA(\\d+)": lambda i: mr_address[i],  # mode register address
            "OP(\\d+)": lambda i: op[i], # mode register value, or operand for MPC
        }

        for pattern, value in rules.items():
            m = re.match(pattern, bit)
            if m:
                args = [int(g) for g in m.groups()]
                return value(*args)
        raise ValueError(bit)
