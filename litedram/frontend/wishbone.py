# This file is Copyright (c) 2016-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

"""Wishbone frontend for LiteDRAM"""

from migen import *

from litex.soc.interconnect import stream


# LiteDRAMWishbone2Native --------------------------------------------------------------------------

class LiteDRAMWishbone2Native(Module):
    def __init__(self, wishbone, port, base_address=0x00000000):
        wishbone_data_width = len(wishbone.dat_w)
        port_data_width     = len(port.wdata.data)
        assert wishbone_data_width >= port_data_width

        # # #

        adr_offset = base_address >> log2_int(port.data_width//8)

        # Write Datapath ---------------------------------------------------------------------------
        wdata_converter = stream.StrideConverter(
            [("data", wishbone_data_width), ("we", wishbone_data_width//8)],
            [("data", port_data_width),     ("we", port_data_width//8)],
        )
        self.submodules += wdata_converter
        self.comb += [
            wdata_converter.sink.valid.eq(wishbone.cyc & wishbone.stb & wishbone.we),
            wdata_converter.sink.data.eq(wishbone.dat_w),
            wdata_converter.sink.we.eq(wishbone.sel),
            wdata_converter.source.connect(port.wdata)
        ]

        # Read Datapath ----------------------------------------------------------------------------
        rdata_converter = stream.StrideConverter(
            [("data", port_data_width)],
            [("data", wishbone_data_width)],
        )
        self.submodules += rdata_converter
        self.comb += [
            port.rdata.connect(rdata_converter.sink),
            rdata_converter.source.ready.eq(1),
            wishbone.dat_r.eq(rdata_converter.source.data),
        ]

        # Control ----------------------------------------------------------------------------------
        ratio = wishbone_data_width//port_data_width
        count = Signal(max=max(ratio, 2))
        self.submodules.fsm = fsm = FSM(reset_state="CMD")
        fsm.act("CMD",
            port.cmd.valid.eq(wishbone.cyc & wishbone.stb),
            port.cmd.we.eq(wishbone.we),
            port.cmd.addr.eq(wishbone.adr*ratio + count - adr_offset),
            If(port.cmd.valid & port.cmd.ready,
                NextValue(count, count + 1),
                If(count == (ratio - 1),
                    NextValue(count, 0),
                    If(wishbone.we,
                        NextState("WAIT-WRITE")
                    ).Else(
                        NextState("WAIT-READ")
                    )
                )
            )
        )
        fsm.act("WAIT-WRITE",
            If(wdata_converter.sink.ready,
                wishbone.ack.eq(1),
                NextState("CMD")
            )
        )
        fsm.act("WAIT-READ",
            If(rdata_converter.source.valid,
               wishbone.ack.eq(1),
               NextState("CMD")
            )
        )
