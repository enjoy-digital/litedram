#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2024 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Wishbone frontend for LiteDRAM"""

from math import log2

from migen import *

from litex.gen import *

from litex.soc.interconnect import stream

from litex.soc.interconnect.wishbone import CTI_BURST_INCREMENTING
from litedram.common           import LiteDRAMNativePort
from litedram.frontend.adapter import LiteDRAMNativePortConverter


# LiteDRAMWishbone2Native --------------------------------------------------------------------------

class LiteDRAMWishbone2Native(LiteXModule):
    def __init__(self, wishbone, port, base_address=0x00000000):
        wishbone_data_width = len(wishbone.dat_w)
        port_data_width     = 2**int(log2(len(port.wdata.data))) # Round to lowest power 2
        ratio               = wishbone_data_width/port_data_width

        assert wishbone.addressing == "word"

        # Keep narrow Wishbone bursts on the real native-port width so
        # incrementing bursts can share a wider DRAM command.
        if wishbone_data_width < port_data_width:
            self._init_burst_upconverter(
                wishbone, port, base_address, wishbone_data_width, port_data_width)
            return

        if wishbone_data_width != port_data_width:
            if wishbone_data_width > port_data_width:
                addr_shift = -log2_int(wishbone_data_width//port_data_width)
            else:
                addr_shift = log2_int(port_data_width//wishbone_data_width)
            new_port = LiteDRAMNativePort(
                mode          = port.mode,
                address_width = port.address_width + addr_shift,
                data_width    = wishbone_data_width
            )
            self.submodules += LiteDRAMNativePortConverter(new_port, port)
            port = new_port

        # # #

        aborted = Signal()
        offset  = base_address >> log2_int(port.data_width//8)

        self.fsm = fsm = FSM(reset_state="CMD")
        self.comb += [
            port.cmd.addr.eq(wishbone.adr - offset),
            port.cmd.we.eq(wishbone.we),
            port.cmd.last.eq(~wishbone.we), # Always wait for reads.
            port.flush.eq(~wishbone.cyc)    # Flush writes when transaction ends.
        ]
        fsm.act("CMD",
            port.cmd.valid.eq(wishbone.cyc & wishbone.stb),
            If(port.cmd.valid & port.cmd.ready &  wishbone.we, NextState("WRITE")),
            If(port.cmd.valid & port.cmd.ready & ~wishbone.we, NextState("READ")),
            NextValue(aborted, 0),
        )
        self.comb += [
            port.wdata.valid.eq(wishbone.stb & wishbone.we),
            If(ratio <= 1, If(~fsm.ongoing("WRITE"), port.wdata.valid.eq(0))),
            port.wdata.data.eq(wishbone.dat_w),
            port.wdata.we.eq(wishbone.sel),
        ]
        fsm.act("WRITE",
            NextValue(aborted, ~wishbone.cyc | aborted),
            If(port.wdata.valid & port.wdata.ready,
                wishbone.ack.eq(wishbone.cyc & ~aborted),
                NextState("CMD")
            ),
        )
        self.comb += port.rdata.ready.eq(1)
        fsm.act("READ",
            NextValue(aborted, ~wishbone.cyc | aborted),
            If(port.rdata.valid,
                wishbone.ack.eq(wishbone.cyc & ~aborted),
                wishbone.dat_r.eq(port.rdata.data),
                NextState("CMD")
            )
        )

    def _init_burst_upconverter(self, wishbone, port, base_address, wishbone_data_width, port_data_width):
        assert port_data_width % wishbone_data_width == 0

        ratio                = port_data_width//wishbone_data_width
        ratio_bits           = log2_int(ratio)
        wishbone_sel_width   = wishbone_data_width//8
        port_sel_width       = port_data_width//8
        offset               = base_address >> log2_int(wishbone_sel_width)
        narrow_addr          = Signal(len(wishbone.adr))
        wide_addr            = Signal.like(port.cmd.addr)
        chunk                = Signal(ratio_bits)
        chunk_bit            = Signal(ratio)
        wishbone_last        = Signal()

        # # #

        # Wishbone remains word-addressed at the narrow width. The upper bits
        # select the native word; the lower bits select the lane inside it.
        self.comb += [
            narrow_addr.eq(wishbone.adr - offset),
            wide_addr.eq(narrow_addr[ratio_bits:]),
            chunk.eq(narrow_addr[:ratio_bits]),
            wishbone_last.eq(wishbone.cti != CTI_BURST_INCREMENTING),
            port.flush.eq(~wishbone.cyc),
        ]

        # One-hot version of the selected lane, used by the write merge logic.
        chunk_bit_cases = {i: chunk_bit.eq(2**i) for i in range(ratio)}
        self.comb += [
            chunk_bit.eq(0),
            Case(chunk, chunk_bit_cases),
        ]

        # Write path --------------------------------------------------------------------------------
        wr_valid      = Signal()
        wr_addr       = Signal.like(port.cmd.addr)
        wr_data       = Signal(port_data_width)
        wr_we         = Signal(port_sel_width)
        wr_sel        = Signal(ratio)
        wr_last       = Signal()
        wr_can_merge  = Signal()
        wr_next_sel   = Signal(ratio)
        wr_flush      = Signal()
        wr_chunk_data = Signal(port_data_width)
        wr_chunk_we   = Signal(port_sel_width)

        wr_chunk_cases = {}
        for i in range(ratio):
            # Place the current Wishbone beat and byte enables in their native lane.
            wr_chunk_cases[i] = [
                wr_chunk_data[i*wishbone_data_width:(i + 1)*wishbone_data_width].eq(wishbone.dat_w),
                wr_chunk_we[i*wishbone_sel_width:(i + 1)*wishbone_sel_width].eq(wishbone.sel),
            ]
        self.comb += [
            wr_chunk_data.eq(0),
            wr_chunk_we.eq(0),
            Case(chunk, wr_chunk_cases),
            # Merge only when the next beat targets the same native word and a free lane.
            wr_can_merge.eq(~wr_valid | ((wr_addr == wide_addr) & ((wr_sel & chunk_bit) == 0))),
            wr_next_sel.eq(wr_sel | chunk_bit),
            wr_flush.eq(wishbone_last | (wr_next_sel == 2**ratio - 1)),
        ]

        # Read path ---------------------------------------------------------------------------------
        rd_cache_valid = Signal()
        rd_cache_addr  = Signal.like(port.cmd.addr)
        rd_cache_data  = Signal(port_data_width)
        rd_addr        = Signal.like(port.cmd.addr)
        rd_chunk       = Signal(ratio_bits)
        rd_last        = Signal()
        rd_cache_hit   = Signal()
        rd_cache_rdata = Signal(wishbone_data_width)
        rd_port_rdata  = Signal(wishbone_data_width)
        aborted        = Signal()

        rd_cache_cases = {}
        rd_port_cases  = {}
        for i in range(ratio):
            # Select the requested narrow lane from either cached or returned native data.
            rd_cache_cases[i] = rd_cache_rdata.eq(
                rd_cache_data[i*wishbone_data_width:(i + 1)*wishbone_data_width])
            rd_port_cases[i] = rd_port_rdata.eq(
                port.rdata.data[i*wishbone_data_width:(i + 1)*wishbone_data_width])
        self.comb += [
            rd_cache_hit.eq(rd_cache_valid & (rd_cache_addr == wide_addr)),
            rd_cache_rdata.eq(0),
            rd_port_rdata.eq(0),
            Case(chunk, rd_cache_cases),
            Case(rd_chunk, rd_port_cases),
        ]

        self.fsm = fsm = FSM(reset_state="CMD")
        fsm.act("CMD",
            NextValue(aborted, 0),
            If(~wishbone.cyc,
                NextValue(rd_cache_valid, 0),
                If(wr_valid,
                    # Wishbone ended with a partial native word pending; write it now.
                    NextValue(wr_last, 1),
                    NextState("WRITE_CMD")
                )
            ).Elif(wishbone.stb,
                If(wishbone.we,
                    NextValue(rd_cache_valid, 0),
                    If(wr_can_merge,
                        wishbone.ack.eq(1),
                        NextValue(wr_valid, 1),
                        NextValue(wr_addr, Mux(wr_valid, wr_addr, wide_addr)),
                        NextValue(wr_data, Mux(wr_valid, wr_data | wr_chunk_data, wr_chunk_data)),
                        NextValue(wr_we,   Mux(wr_valid, wr_we   | wr_chunk_we,   wr_chunk_we)),
                        NextValue(wr_sel,  wr_next_sel),
                        NextValue(wr_last, wishbone_last),
                        If(wr_flush,
                            NextState("WRITE_CMD")
                        )
                    ).Else(
                        NextValue(wr_last, 1),
                        NextState("WRITE_CMD")
                    )
                ).Else(
                    If(wr_valid,
                        # Preserve write/read ordering by draining pending writes first.
                        NextValue(wr_last, 1),
                        NextState("WRITE_CMD")
                    ).Elif(rd_cache_hit,
                        # A previous native read already fetched this lane.
                        wishbone.ack.eq(1),
                        wishbone.dat_r.eq(rd_cache_rdata),
                        If(wishbone_last,
                            NextValue(rd_cache_valid, 0)
                        )
                    ).Else(
                        NextValue(rd_addr, wide_addr),
                        NextValue(rd_chunk, chunk),
                        NextValue(rd_last, wishbone_last),
                        NextState("READ_CMD")
                    )
                )
            )
        )
        fsm.act("WRITE_CMD",
            If(wr_valid,
                port.cmd.valid.eq(1),
                port.cmd.we.eq(1),
                port.cmd.addr.eq(wr_addr),
                port.cmd.last.eq(wr_last),
                If(port.cmd.ready,
                    NextState("WRITE_DATA")
                )
            ).Else(
                NextState("CMD")
            )
        )
        fsm.act("WRITE_DATA",
            port.wdata.valid.eq(1),
            port.wdata.data.eq(wr_data),
            port.wdata.we.eq(wr_we),
            If(port.wdata.ready,
                NextValue(wr_valid, 0),
                NextValue(wr_data,  0),
                NextValue(wr_we,    0),
                NextValue(wr_sel,   0),
                NextState("CMD")
            )
        )
        fsm.act("READ_CMD",
            If(~wishbone.cyc,
                NextState("CMD")
            ).Else(
                port.cmd.valid.eq(1),
                port.cmd.we.eq(0),
                port.cmd.addr.eq(rd_addr),
                port.cmd.last.eq(rd_last),
                If(port.cmd.ready,
                    NextState("READ_DATA")
                )
            )
        )
        fsm.act("READ_DATA",
            NextValue(aborted, ~wishbone.cyc | aborted),
            port.rdata.ready.eq(1),
            If(port.rdata.valid,
                NextValue(rd_cache_data, port.rdata.data),
                NextValue(rd_cache_addr, rd_addr),
                If(wishbone.cyc & ~aborted,
                    wishbone.ack.eq(1),
                    wishbone.dat_r.eq(rd_port_rdata),
                    NextValue(rd_cache_valid, ~rd_last)
                ).Else(
                    NextValue(rd_cache_valid, 0)
                ),
                NextState("CMD")
            )
        )

# LiteDRAMNative2Wishbone --------------------------------------------------------------------------

class LiteDRAMNative2Wishbone(LiteXModule):
    def __init__(self, port, wishbone, base_address=0x00000000):
        wishbone_data_width = len(wishbone.dat_w)
        port_data_width     = 2**int(log2(len(port.wdata.data))) # Round to lowest power 2
        ratio               = wishbone_data_width/port_data_width

        assert ratio == 1

        # # #

        # Signals.
        adr = Signal(32)

        # FSM.
        self.fsm = fsm = FSM(reset_state="CMD")
        fsm.act("CMD",
            If(port.cmd.valid,
                port.cmd.ready.eq(1),
                If(wishbone.addressing == "byte",
                    NextValue(adr, port.cmd.addr*int(port_data_width//8) + base_address),
                ).Else(
                    NextValue(adr, port.cmd.addr + base_address//int(port_data_width//8)),
                ),
                If(port.cmd.we,
                    NextState("WRITE")
                ).Else(
                    NextState("READ")
                )
            )
        )
        fsm.act("WRITE",
            If(port.wdata.valid,
                wishbone.stb.eq(1),
                wishbone.cyc.eq(1),
                wishbone.we.eq(1),
                wishbone.adr.eq(adr),
                wishbone.sel.eq(port.wdata.we),
                wishbone.dat_w.eq(port.wdata.data),
                If(wishbone.ack,
                    port.wdata.ready.eq(1),
                    NextState("CMD")
                )
            )
        )
        fsm.act("READ",
            wishbone.stb.eq(1),
            wishbone.cyc.eq(1),
            wishbone.adr.eq(adr),
            wishbone.sel.eq(2**len(wishbone.sel) - 1),
            If(wishbone.ack,
                # Assume port.rdata.ready always 1.
                port.rdata.valid.eq(1),
                port.rdata.data.eq(wishbone.dat_r),
                NextState("CMD"),
            )
        )
