#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020-2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *


class ModeRegister:
    """RPC Mode Register encoding (RPC has only 1 mode register)"""
    def __init__(self):
        self.cl      = Signal(3)
        # TODO: in LPDDR3 nWR is the number of clock cycles determining when to start internal
        # precharge for a write burst when auto-precharge is enabled (ceil(tRW/tCK) ?)
        self.nwr     = Signal(3)
        self.zout    = Signal(4)
        self.odt     = Signal(3)
        self.odt_stb = Signal(1)
        self.csr_fx  = Signal(1)
        self.odt_pd  = Signal(1)
        self.tm      = Signal(1)

    CL = {
        8:  0b000,  # default
        10: 0b001,
        11: 0b010,
        13: 0b011,
        3:  0b110,
    }
    NWR = {
        4:  0b000,
        6:  0b001,
        7:  0b010,
        8:  0b011,  # default
        10: 0b100,
        12: 0b101,
        14: 0b110,
        16: 0b111,
    }
    ZOUT = {  # resistance in Ohms
        120:     0b0010,
        90:      0b0100,
        51.4:    0b0110,
        60:      0b1000,
        40:      0b1010,
        36:      0b1100,
        27.7:    0b1110,
        "short": 0b0001,  # 0bxxx1
        "open":  0b0000,  # output disabled, default
    }
    ODT = {
        60:     0b001,
        45:     0b010,
        25.7:   0b011,
        30:     0b100,
        20:     0b101,
        18:     0b110,
        13.85:  0b111,
        "open": 0b000,
    }

    # Encode mode register information in DFI address/bank
    DFI_ENCODING = {
        # field: (dfi_signal, width, offset)
        "cl":      ("address", 3,  0),
        # FIXME: not enough bits in DFI to store all data
        "nwr":     None,  # ("address", 3,  3),
        "zout":    ("address", 4,  3),
        "odt":     ("address", 3,  7),
        "csr_fx":  ("address", 1, 10),
        "odt_stb": ("bank",    1,  0),
        "odt_pd":  ("bank",    1,  1),
        "tm":      None,
    }

    @classmethod
    def dfi_encode(cls, **kwargs):
        address = 0
        bank = 0
        for field, encoding in cls.DFI_ENCODING.items():
            if encoding is None:
                continue
            sig, width, offset = encoding
            value = (kwargs[field] & (2**width - 1)) << offset
            if sig == "address":
                address |= value
            elif sig == "bank":
                bank |= value
            else:
                raise ValueError(sig)
        return address, bank

    def dfi_decode(self, dfi_phase):
        r = []
        for field, encoding in self.DFI_ENCODING.items():
            if encoding is None:
                continue
            sig, width, offset = encoding
            r += [getattr(self, field).eq(getattr(dfi_phase, sig)[offset:offset+width])]
        return r


class DFIAdapter(Module):
    """Translate DFI commands into RPC parallel commands format (Request Packet)

    Maps DFI commands to RPC parallel packet commands (sent over DB lines). Some commands cannot
    be represented by cas_n/ras_n/we_n combinations, for that reason when reset_n=0, some DFI
    commands are interpreted specially:
    - ACT -> perform a RESET sequence
    - MRS -> write UTR, utr_op and utr_en are encoded in phase.address (see `dfi_utr_encode`)
    - ZQC -> will perform di_ferent types of ZQ calibration: "init" when auto_precharge=1,
             "reset" if auto_precharge=0
    """
    ZQC_OP = {
        "init":  0b00,  # calibration after initialization
        "long":  0b01,
        "short": 0b10,
        "reset": 0b11,  # ZQ reset
    }
    REF_OP = {
        "FST": 0b00,  # FST refresh: tREFi = 100ns
        "LP":  0b00,  # LP refresh:  tREFi = 3.2us
    }
    UTR_OP = {  # Utility Register read pattern
        "0101": 0b00,
        "1100": 0b01,
        "0011": 0b10,
        "1010": 0b11,
    }

    SPECIAL_CMDS = {
        "RESET":    "ACT",
        "UTR":      "MRS",
        "ZQC_INIT": "ZQC",
    }

    @classmethod
    def dfi_utr_encode(cls, utr_op, utr_en):
        if isinstance(utr_op, str):
            utr_op = cls.UTR_OP[utr_op]
        address = 0
        address |= (utr_en &  0b1) << 0
        address |= (utr_op & 0b11) << 1
        return address

    def __init__(self, phase):
        self.db_p = Signal(16)  # on positive edge
        self.db_n = Signal(16)  # on negative edge

        self.cmd_valid = Signal()
        self.do_reset  = Signal()  # force sending RESET command
        self.bc        = Signal(6)  # burst count (bs+1 = number of 32-byte words in the transfer)
        self.ref_op    = Signal(2)

        # # #

        self.phase_cmd = phase_cmd = Signal(3)
        self.comb += phase_cmd.eq(Cat(phase.cas_n, phase.ras_n, phase.we_n))

        def _cmd(cas, ras, we):
            assert cas in [0, 1] and ras in [0, 1] and we in [0, 1]
            return ((1 - cas) << 0) | ((1 - ras) << 1) | ((1 - we) << 2)

        self.dfi_cmds = dfi_cmds = {
            "NOP": _cmd(cas=0, ras=0, we=0),
            "ACT": _cmd(cas=0, ras=1, we=0),
            "RD":  _cmd(cas=1, ras=0, we=0),
            "WR":  _cmd(cas=1, ras=0, we=1),
            "PRE": _cmd(cas=0, ras=1, we=1),
            "REF": _cmd(cas=1, ras=1, we=0),
            "ZQC": _cmd(cas=0, ras=0, we=1),
            "MRS": _cmd(cas=1, ras=1, we=1),
        }

        # precharge/refresh use a bank bitmask, so PRECHARGE ALL uses 0b1111
        self.special_cmds = special_cmds = Signal()
        self.utr_en       = utr_en       = phase.address[0]
        utr_op         = phase.address[1:3]
        bk             = Signal(4)
        zqc_op         = Signal(2)
        auto_precharge = Signal()
        mr             = ModeRegister()

        self.comb += mr.dfi_decode(phase)
        self.comb += [
            special_cmds.eq(~phase.reset_n),
            auto_precharge.eq(phase.address[10]),
            If(auto_precharge,
                bk.eq(0b1111),
            ).Else(  # binary to one-hot encoded
                Case(phase.bank[:2], {i: bk.eq(1 << i) for i in range(4)}),
            ),
            If(special_cmds,
                If(auto_precharge,
                    zqc_op.eq(self.ZQC_OP["init"]),
                ).Else(
                    zqc_op.eq(self.ZQC_OP["reset"]),
                )
            ).Else(
                If(auto_precharge,
                    zqc_op.eq(self.ZQC_OP["long"]),
                ).Else(
                    zqc_op.eq(self.ZQC_OP["short"]),
                )
            ),
        ]

        cases = {
            "NOP": [
                self.db_p.eq(0),
                self.db_n.eq(0),
            ],
            "ACT": [
                self.db_p[0:2  +1].eq(0b101),
                self.db_p[3:4  +1].eq(phase.bank[:2]),
                self.db_n[0      ].eq(0),
                self.db_n[1:12 +1].eq(phase.address[:12]),  # row address
            ],
            "RD": [
                self.db_p[0:2   +1].eq(0b000),
                self.db_p[3:4   +1].eq(phase.bank[:2]),
                self.db_p[5:10  +1].eq(self.bc),
                self.db_p[13:15 +1].eq(phase.address[4:6 +1]),
                self.db_n[0       ].eq(0),
                self.db_n[13:15 +1].eq(phase.address[7:9 +1]),
            ],
            "WR": [
                self.db_p[0:2   +1].eq(0b001),
                self.db_p[3:4   +1].eq(phase.bank[:2]),
                self.db_p[5:10  +1].eq(self.bc),
                self.db_p[13:15 +1].eq(phase.address[4:6 +1]),
                self.db_n[0       ].eq(0),
                self.db_n[13:15 +1].eq(phase.address[7:9 +1]),
            ],
            "PRE": [
                self.db_p[6:9+1].eq(bk),
                self.db_p[0:2+1].eq(0b100),
                self.db_n[0    ].eq(0),
            ],
            "REF": [
                self.db_p[6:9+1].eq(bk),
                self.db_p[0:2+1].eq(0b110),
                self.db_n[1:2+3].eq(self.ref_op),
                self.db_n[0    ].eq(0),
            ],
            "ZQC": [
                self.db_p[0:2  +1].eq(0b001),
                self.db_p[14:15+1].eq(zqc_op),
                self.db_n[0      ].eq(1),
            ],
            "MRS": [
                self.db_p[0:2  +1].eq(0b010),
                self.db_p[3:15 +1].eq(Cat(mr.cl, mr.nwr, mr.zout, mr.odt)),
                self.db_n[0      ].eq(0),
                self.db_n[12:15+1].eq(Cat(mr.odt_stb, mr.csr_fx, mr.odt_pd, mr.tm)),
            ],
            "UTR": [
                self.db_p[0:2  +1].eq(0b111),
                self.db_p[3      ].eq(utr_en),
                self.db_p[4:5  +1].eq(utr_op),
                self.db_n[0      ].eq(0),
            ],
            "RESET": [
                self.db_p.eq(0),
                self.db_n.eq(1),
            ],
        }

        self.comb += [
            If(self._is_cmd("RESET"),
                cases["RESET"],
                self.cmd_valid.eq(1),
            ).Elif(self._is_cmd("UTR"),
                cases["UTR"],
                self.cmd_valid.eq(1),
            ).Else(
                self.cmd_valid.eq(~self._is_cmd("NOP")),
                Case(phase_cmd, {dfi_cmds[cmd]: cases[cmd] for cmd in dfi_cmds.keys()}),
            ),
        ]

    def _is_cmd(self, cmd):
        if isinstance(cmd, list):
            return reduce(or_, (self._is_cmd(c) for c in cmd))
        if cmd in ["RESET", "UTR", "ZQC_INIT"]:
            return self.special_cmds & (self.phase_cmd == self.dfi_cmds[self.SPECIAL_CMDS[cmd]])
        return self.phase_cmd == self.dfi_cmds[cmd]

    def is_cmd(self, cmd):
        return self._is_cmd(cmd) & self.cmd_valid
