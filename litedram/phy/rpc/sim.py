#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# Behavioural RPC DRAM model for simulation.
#
# Models what the RPC PHY uses: parallel commands (Request Packets on DB after the STB preamble),
# single WORD (32 bytes, BC=0) reads/writes with data masks, one open row per bank. Serial commands
# (Burst Stop...), resets, mode register, refresh and ZQ calibration are accepted and ignored: the
# latencies are fixed by `cl`.

from migen import *

# RPC DRAM Model -----------------------------------------------------------------------------------

class RPCDRAMModel(Module):
    """RPC DRAM model, to clock at the DDR rate (one cycle per UI), aligned with CLK.

    `cl` is the read/write latency in tCK (RL = WL = AL + CL). `rowbits` reduces the number of
    rows that are stored (to keep the memory small in simulation).
    """
    # Request Packet opcodes: DB[2:0] of the first (positive edge) word.
    commands = {
        "RD"  : 0b000,
        "WR"  : 0b001, # ZQC when DB[0] of the second word is 1.
        "MRS" : 0b010,
        "PRE" : 0b100,
        "ACT" : 0b101,
        "REF" : 0b110,
        "UTR" : 0b111,
    }
    def __init__(self, stb_in, dq_in, dq_out, cl, dq_oe=None, rowbits=12):
        assert len(dq_in) == 16
        self.dq_oe = dq_oe = Signal() if dq_oe is None else dq_oe
        self.dqs   = dqs   = Signal() # For waveforms.

        # # #

        # STB preamble: STB low for 2 tCK (4 UIs) marks the start of a Request Packet.
        stb_zeros = Signal(max=8)
        self.sync += [
            If(stb_in == 0,
                If(stb_zeros != 7, stb_zeros.eq(stb_zeros + 1))
            ).Else(
                stb_zeros.eq(0)
            )
        ]

        # DB is center-aligned with CLK: register it so that it is stable over a model cycle.
        dq = Signal(16)
        self.sync += dq.eq(dq_in)

        # Memory: 16-bit words, 16 words per WORD, 64 WORDs per row.
        self.mem = mem = Memory(16, 2**(2 + rowbits + 6 + 4))
        wr = mem.get_port(write_capable=True, we_granularity=8)
        rd = mem.get_port(async_read=True)
        self.specials += mem, wr, rd

        # Request Packet.
        cmd_p = Signal(16)
        rows  = Array(Signal(rowbits) for _ in range(4))
        bank  = Signal(2)
        col   = Signal(6)
        mask  = Signal(32)
        write = Signal()
        mask_bits = Array(mask[n] for n in range(32))

        # UIs since the first word of the Request Packet.
        ui   = Signal(max=2*cl + 16 + 1)
        word = Signal(4)
        addr = Signal(2 + rowbits + 6 + 4)
        self.comb += [
            word.eq(ui - 2*cl),
            addr.eq(Cat(word, col, rows[bank], bank)),
            wr.adr.eq(addr),
            rd.adr.eq(addr),
            wr.dat_w.eq(dq),
        ]

        self.fsm = fsm = FSM(reset_state="IDLE")
        self.submodules += fsm
        fsm.act("IDLE",
            If(stb_zeros == 4,
                NextState("CMD-P")
            )
        )
        fsm.act("CMD-P",
            NextValue(cmd_p, dq),
            NextValue(ui, 1),
            NextState("CMD-N")
        )
        fsm.act("CMD-N",
            NextValue(ui, ui + 1),
            NextValue(bank, cmd_p[3:5]),
            NextValue(col,  Cat(cmd_p[13:16], dq[13:16])),
            NextState("IDLE"),
            Case(cmd_p[0:3], {
                self.commands["ACT"] : [
                    NextValue(rows[cmd_p[3:5]], dq[1:1 + rowbits]),
                ],
                self.commands["RD"]  : [
                    If(dq[0] == 0,
                        NextValue(write, 0),
                        NextState("BURST")
                    )
                ],
                self.commands["WR"]  : [
                    If(dq[0] == 0,
                        NextValue(write, 1),
                        NextState("BURST")
                    )
                ],
                "default" : [],
            })
        )
        fsm.act("BURST",
            NextValue(ui, ui + 1),
            If(write,
                # Data masks, 2 tCK before the data (2 x 32 bits: only the first WORD is used).
                If(ui == 2*(cl - 2) + 0, NextValue(mask[ 0:16], dq)),
                If(ui == 2*(cl - 2) + 1, NextValue(mask[16:32], dq)),
                # Data: 16 words, a mask bit set means the byte is not written.
                If(ui >= 2*cl,
                    wr.we.eq(~Cat(mask_bits[Cat(0, word)], mask_bits[Cat(1, word)])),
                ),
            ).Else(
                # DQS preamble (1 tCK), then data.
                If(ui >= 2*(cl - 1),
                    dq_oe.eq(1),
                ),
                If(ui >= 2*cl,
                    dqs.eq(~ui[0]),
                    dq_out.eq(rd.dat_r),
                ),
            ),
            If(ui == 2*cl + 16 - 1,
                NextState("IDLE")
            )
        )
