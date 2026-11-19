#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# Behavioural RPC DRAM model for simulation.
#
# Models what the RPC PHY uses: parallel commands (Request Packets on DB after the STB preamble),
# WORD (32 bytes) reads/writes with data masks, one open row per bank, and the Serial Packets on
# STB that follow a read/write Request Packet (one per 8 tCK): read/write of another WORD (Address
# Streaming, the data follow each other without gap), NOP, Activate and Burst Stop. Resets, mode
# register, refresh and ZQ calibration are accepted and ignored: the latencies are fixed by `cl`.
# `error` is set (and stays set) on a Serial Packet that the model does not support or that is
# not legal (direction change without Toggle RW...).

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
        # (STB has to be seen high first: the PHY outputs are low until its serializers start)
        stb_zeros = Signal(max=8)
        stb_high  = Signal()
        self.sync += [
            If(stb_in == 0,
                If((stb_zeros != 7) & stb_high, stb_zeros.eq(stb_zeros + 1))
            ).Else(
                stb_high.eq(1),
                stb_zeros.eq(0)
            )
        ]

        # DB/STB are center-aligned with CLK: register them so that they are stable over a model
        # cycle.
        dq  = Signal(16)
        stb = Signal(reset=1)
        self.sync += dq.eq(dq_in)
        self.sync += stb.eq(stb_in)

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
        mask  = Signal(64) # First WORD mask (WL-2), last WORD mask (WL-1).
        write = Signal()
        first = Signal()   # First WORD of the burst.
        mask_bits = Array(mask[n] for n in range(64))

        # UIs since the first word of the Request Packet (stays in the data window once there:
        # 2*cl ... 2*cl + 15, so ui[0:4] is always the position in the current Serial Packet).
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

        # Serial Packets: 16 bits on STB (both CLK edges), the first one starts with the Request
        # Packet. The packet received in slot n tells what follows the WORD n of the burst: slot n
        # ends before WORD n starts and slot n + 2 after WORD n ends, so 2 entries are enough.
        self.error  = error  = Signal()
        self.nwords = nwords = Signal(32) # WORDs transferred (for the tests).
        sp      = Signal(16)
        sp_bits = Array(sp[n] for n in range(16))
        packet  = Signal(16)
        serial  = Signal() # Address Streaming: the burst lasts until a Burst Stop.
        slot    = Signal()
        chunk   = Signal()
        NEXT_STOP, NEXT_INC, NEXT_LOAD = range(3)
        nxt_kind = Array(Signal(2) for _ in range(2))
        nxt_bank = Array(Signal(2) for _ in range(2))
        nxt_col  = Array(Signal(6) for _ in range(2))
        self.comb += packet.eq(Cat(sp[:15], stb))
        receive_serial = [
            NextValue(sp_bits[ui[0:4]], stb),
            If(ui[0:4] == 15,
                NextValue(slot, ~slot),
                NextValue(nxt_kind[slot], Mux(serial, NEXT_INC, NEXT_STOP)),
                Case(packet[0:2], {
                    # NOP.
                    0b11 : [],
                    # Read/Write.
                    0b10 : [
                        NextValue(serial, 1),
                        NextValue(nxt_kind[slot], NEXT_LOAD),
                        NextValue(nxt_bank[slot], packet[2:4]),
                        NextValue(nxt_col[slot],  packet[5:11]),
                        If(packet[4] == write, NextValue(error, 1)),
                    ],
                    # Activate.
                    0b01 : [
                        NextValue(rows[packet[2:4]], packet[4:4 + rowbits]),
                    ],
                    # Utility: Burst Stop only.
                    0b00 : [
                        NextValue(nxt_kind[slot], NEXT_STOP),
                        If(packet[2:6] != 0b0010, NextValue(error, 1)),
                    ],
                })
            )
        ]

        self.fsm = fsm = FSM(reset_state="IDLE")
        self.submodules += fsm
        fsm.act("IDLE",
            NextValue(serial, 0),
            NextValue(slot,   0),
            NextValue(chunk,  0),
            NextValue(first,  1),
            If(stb_zeros == 4,
                NextState("CMD-P")
            )
        )
        fsm.act("CMD-P",
            NextValue(cmd_p, dq),
            NextValue(ui, 1),
            NextValue(sp_bits[0], stb),
            NextState("CMD-N")
        )
        fsm.act("CMD-N",
            NextValue(ui, ui + 1),
            NextValue(sp_bits[1], stb),
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
        last = Signal()
        self.comb += last.eq(nxt_kind[chunk] == NEXT_STOP)
        fsm.act("BURST",
            NextValue(ui, ui + 1),
            *receive_serial,
            If(write,
                # Data masks, 2 tCK before the data: 32 bits for the first WORD of the burst, then
                # 32 bits for the last one (when it is not the first one too).
                If(ui == 2*(cl - 2) + 0, NextValue(mask[ 0:16], dq)),
                If(ui == 2*(cl - 2) + 1, NextValue(mask[16:32], dq)),
                If(ui == 2*(cl - 1) + 0, NextValue(mask[32:48], dq)),
                If(ui == 2*(cl - 1) + 1, NextValue(mask[48:64], dq)),
                # Data: 16 words, a mask bit set means the byte is not written.
                If(ui >= 2*cl,
                    If(first,
                        wr.we.eq(~Cat(mask_bits[Cat(0, word, 0)], mask_bits[Cat(1, word, 0)])),
                    ).Elif(last,
                        wr.we.eq(~Cat(mask_bits[Cat(0, word, 1)], mask_bits[Cat(1, word, 1)])),
                    ).Else(
                        wr.we.eq(0b11),
                    )
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
            # End of a WORD: stop, or go on with the next WORD or with the WORD of a Serial Packet.
            If(ui == 2*cl + 16 - 1,
                NextValue(ui,     2*cl),
                NextValue(chunk,  ~chunk),
                NextValue(first,  0),
                NextValue(nwords, nwords + 1),
                Case(nxt_kind[chunk], {
                    NEXT_STOP : NextState("IDLE"),
                    NEXT_INC  : NextValue(col, col + 1),
                    NEXT_LOAD : [
                        NextValue(bank, nxt_bank[chunk]),
                        NextValue(col,  nxt_col[chunk]),
                    ],
                })
            )
        )
