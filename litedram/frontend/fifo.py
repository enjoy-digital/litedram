#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2021 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import math

from migen import *

from litex.soc.interconnect import stream

from litedram.common import LiteDRAMNativePort
from litedram.frontend import dma

# Helpers ------------------------------------------------------------------------------------------

def _inc(signal, modulo):
    if modulo == 2**len(signal):
        return signal.eq(signal + 1)
    else:
        return If(signal == (modulo - 1),
            signal.eq(0)
        ).Else(
            signal.eq(signal + 1)
        )

# LiteDRAMFIFOCtrl ---------------------------------------------------------------------------------

class _LiteDRAMFIFOCtrl(Module):
    def __init__(self, base, depth):
        self.base  = base
        self.depth = depth
        self.level = Signal(max=depth+1)

        # # #

        # To write buffer
        self.writable      = Signal()
        self.write_address = Signal(max=depth)

        # From write buffer
        self.write = Signal()

        # To read buffer
        self.readable     = Signal()
        self.read_address = Signal(max=depth)

        # From read buffer
        self.read = Signal()

        # # #

        produce = self.write_address
        consume = self.read_address

        self.sync += [
            If(self.write,
                _inc(produce, depth)
            ),
            If(self.read,
                _inc(consume, depth)
            ),
            If(self.write & ~self.read,
                self.level.eq(self.level + 1),
            ).Elif(self.read & ~self.write,
                self.level.eq(self.level - 1)
            )
        ]

        self.comb += [
            self.writable.eq(self.level < depth),
            self.readable.eq(self.level > 0)
        ]

# LiteDRAMFIFOWriter -------------------------------------------------------------------------------

class _LiteDRAMFIFOWriter(Module):
    def __init__(self, data_width, port, ctrl, fifo_depth=16):
        self.sink = sink = stream.Endpoint([("data", data_width)])

        # # #

        self.submodules.writer = writer = dma.LiteDRAMDMAWriter(port, fifo_depth=fifo_depth)
        self.comb += [
            writer.sink.valid.eq(sink.valid & ctrl.writable),
            writer.sink.address.eq(ctrl.base + ctrl.write_address),
            writer.sink.data.eq(sink.data),
            If(writer.sink.valid & writer.sink.ready,
                sink.ready.eq(1)
            ),
            If(port.wdata.valid & port.wdata.ready,
                ctrl.write.eq(1)
            ),
        ]

# LiteDRAMFIFOReader -------------------------------------------------------------------------------

class _LiteDRAMFIFOReader(Module):
    def __init__(self, data_width, port, ctrl, fifo_depth=16):
        self.source = source = stream.Endpoint([("data", data_width)])

        # # #

        self.submodules.reader = reader = dma.LiteDRAMDMAReader(port, fifo_depth=fifo_depth)
        self.comb += [
            reader.sink.valid.eq(ctrl.readable),
            reader.sink.address.eq(ctrl.base + ctrl.read_address),
            If(reader.sink.valid & reader.sink.ready,
                ctrl.read.eq(1)
            )
        ]
        self.comb += reader.source.connect(source)

# _LiteDRAMFIFO ------------------------------------------------------------------------------------

class _LiteDRAMFIFO(Module):
    """LiteDRAM frontend that allows to use DRAM as a FIFO"""
    def __init__(self, data_width, base, depth, write_port, read_port,
        writer_fifo_depth = 16,
        reader_fifo_depth = 16):
        assert isinstance(write_port, LiteDRAMNativePort)
        assert isinstance(read_port,  LiteDRAMNativePort)
        self.sink   = stream.Endpoint([("data", data_width)])
        self.source = stream.Endpoint([("data", data_width)])

        # # #

        self.submodules.ctrl   = _LiteDRAMFIFOCtrl(base, depth)
        self.submodules.writer = _LiteDRAMFIFOWriter(data_width, write_port, self.ctrl, writer_fifo_depth)
        self.submodules.reader = _LiteDRAMFIFOReader(data_width, read_port,  self.ctrl, reader_fifo_depth)
        self.comb += [
            self.sink.connect(self.writer.sink),
            self.reader.source.connect(self.source)
        ]

# LiteDRAMFIFO -------------------------------------------------------------------------------------

class LiteDRAMFIFO(Module):
    """LiteDRAM FIFO with optional/automatic Bypass.


       Description
       -----------

                             ┌──────────┐        ┌──────────┐
                        Sink │   Pre-   │ Bypass │   Post-  │ Source
                    ─────────►   FIFO   ├────────►   FIFO   ├───────►
                             └────┬─────┘        └─────▲────┘
                                  │                    │
                             ┌────▼─────┐        ┌─────┴────┐
                             │   Pre-   │        │   Post-  │
                             │Converter │        │Converter │
                             └────┬─────┘        └─────▲────┘
                                  │                    │
                                  │  ┌─────────────┐   │
                                  │  │    DRAM     │   │
                                  └──►    FIFO     ├───┘
                                     └──────┬──────┘
                                            │
                                            ▼
                                          DRAM

       The DRAM FIFO allows creation of very large FIFO with storage in DRAM. The data-width of the
       input/output streams is automatically adapted to the DRAM's data-width with the Pre/Post con-
       verters and the module switches seamlessly between 2 modes:
       - 1) Bypass mode.
       - 2) DRAM mode.

       1) The module is initialized in Bypass mode, connecting the its Sink to its Source.
       Backpressure from the Source is propagated from the Source to the Post-FIFO, Pre-FIFO
       and the Sink.

                              ┌──────────┐        ┌──────────┐
                         Sink │   Pre-   │ Bypass │   Post-  │ Source
                     ─────────►   FIFO   ├────────►   FIFO   ├───────►
                              └──────────┘        └──────────┘
                                       Backpressure
                                  ◄─────────────────────

        Once the Post-FIFO is full and the Pre-FIFO has enough data to form a DRAM Word, the module
        switches to DRAM mode.

        2) In DRAM mode, the Bypass connection is disabled and Pre-FIFO's Source is redirected to
        Pre-Converter's Sink. Once Pre-Converter has a full DRAM word, the word can be written to the
        DRAM FIFO's Sink


                             ┌──────────┐        ┌──────────┐
                        Sink │   Pre-   │        │   Post-  │ Source
                    ─────────►   FIFO   │        │   FIFO   ├───────►
                             └────┬─────┘        └─────▲────┘
                                  │                    │
                             ┌────▼─────┐        ┌─────┴────┐
                             │   Pre-   │        │   Post-  │
                             │Converter │        │Converter │
                             └────┬─────┘        └─────▲────┘
                                  │                    │
                                  │  ┌─────────────┐   │
                                  │  │    DRAM     │   │
                                  └──►    FIFO     ├───┘
                                     └──────┬──────┘
                                            │
                                            ▼
                                          DRAM

        This data from DRAM FIFO will be generated back on the DRAM FIFO's Source and connected to
        the Post-Converter to re-generate the data with the correct data-width. Data will then be
        generated on the Source.

        Once we no longer have data in the Pre-Converter/DRAM FIFO/Post-Converter path and Pre-FIFO's
        level is below threshold, the modules switches back to Bypass mode.
    """
    def __init__(self, data_width, base, depth, write_port, read_port, with_bypass=False,
        pre_fifo_depth  = 16,
        post_fifo_depth = 16):
        assert isinstance(write_port, LiteDRAMNativePort)
        assert isinstance(read_port,  LiteDRAMNativePort)
        self.sink   = stream.Endpoint([("data", data_width)])
        self.source = stream.Endpoint([("data", data_width)])

        # # #

        # Parameters.
        # -----------
        assert write_port.data_width == read_port.data_width
        port_data_width = write_port.data_width
        assert data_width <= port_data_width
        data_width_ratio = port_data_width//data_width
        if not with_bypass:
            assert data_width_ratio == 1
        pre_fifo_depth  = max( pre_fifo_depth, 2*data_width_ratio)
        post_fifo_depth = max(post_fifo_depth, 2*data_width_ratio)

        # Submodules.
        # -----------
        # Pre-FIFO.
        self.submodules.pre_fifo = pre_fifo = stream.SyncFIFO([("data", data_width)], pre_fifo_depth)

        # Pre-Converter.
        self.submodules.pre_converter = pre_converter = stream.Converter(data_width, port_data_width)

        # DRAM-FIFO.
        self.submodules.dram_fifo = dram_fifo = _LiteDRAMFIFO(
            data_width = port_data_width,
            base       = base,
            depth      = depth,
            write_port = write_port,
            read_port  = read_port,
        )

        # Post-Converter.
        self.submodules.post_converter = post_converter = stream.Converter(port_data_width, data_width)

        # Post-FIFO.
        self.submodules.post_fifo = post_fifo = stream.SyncFIFO([("data", data_width)], post_fifo_depth)

        # Data-Flow.
        # ----------
        dram_bypass          = Signal()
        dram_store           = Signal()
        dram_store_threshold = Signal()
        self.comb += [
            # Sink --> Pre-FIFO.
            self.sink.connect(pre_fifo.sink),

            # DRAM Threshold. We can only enable path to DRAAM when we have enough data for a full
            # DRAM word.
            dram_store_threshold.eq(pre_fifo.level > data_width_ratio),

            # Bypass / DRAM.
            If(with_bypass & dram_bypass,
                # Pre-FIFO --> Post-FIFO.
                pre_fifo.source.connect(post_fifo.sink),
            ).Else(
                # Pre-FIFO --> Pre-Converter.
                If(dram_store | (not with_bypass),
                    pre_fifo.source.connect(pre_converter.sink),
                ),
                # Post-Converter --> Post-FIFO.
                post_converter.source.connect(post_fifo.sink)
            ),

            # Pre-Converter --> DRAM-FIFO.
            pre_converter.source.connect(dram_fifo.sink),

            # DRAM-FIFO --> Post-Converter.
            dram_fifo.source.connect(post_converter.sink),

            # Post-FIFO --> Source.
            post_fifo.source.connect(self.source)
        ]

        # FSM.
        # ----
        if with_bypass:
            self.submodules.fsm = fsm = FSM(reset_state="BYPASS")
            fsm.act("BYPASS",
                dram_bypass.eq(1),
                # Switch to DRAM mode when enough data to store a DRAM word.
                If(dram_store_threshold,
                    NextValue(dram_store, 1),
                    NextState("DRAM")
                )
            )
            dram_cnt_inc = Signal()
            dram_cnt_dec = Signal()
            dram_cnt     = Signal(int(math.log2(depth + pre_fifo_depth + post_fifo_depth) + 1))
            self.sync += dram_cnt.eq(dram_cnt + dram_cnt_inc - dram_cnt_dec)
            fsm.act("DRAM",
                # Increment DRAM Data Count on Pre-Converter's Sink cycle.
                dram_cnt_inc.eq(pre_converter.sink.valid & pre_converter.sink.ready),

                # Decrement DRAM Data Count on Post-Converter's Source cycle.
                dram_cnt_dec.eq(post_converter.source.valid & post_converter.source.ready),

                # Update DRAM store..
                If(pre_converter.source.valid,
                    NextValue(dram_store, dram_store_threshold),
                ),

                # Maintain DRAM Data Count.
                NextValue(dram_cnt, dram_cnt + dram_cnt_inc - dram_cnt_dec),

                # Switch back to Bypass mode when DRAM Data count
                If((dram_store_threshold == 0) & (dram_cnt == 0),
                    NextState("BYPASS")
                )
            )
