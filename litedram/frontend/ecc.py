#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""
ECC frontend for LiteDRAM

Adds ECC support to Native ports.

Features:
- Single Error Correction.
- Double Error Detection.
- Errors injection.
- Errors reporting.

Limitations:
- Byte enable not supported for writes.
"""

from migen import *

from litex.soc.interconnect.csr import *
from litex.soc.interconnect.stream import *
from litex.soc.cores.ecc import *

from litedram.common import wdata_description, rdata_description


# LiteDRAMNativePortECCW ---------------------------------------------------------------------------

class LiteDRAMNativePortECCW(Module):
    def __init__(self, data_width_from, data_width_to):
        self.sink   = sink   = Endpoint(wdata_description(data_width_from))
        self.source = source = Endpoint(wdata_description(data_width_to))

        # # #

        for i in range(8):
            encoder = ECCEncoder(data_width_from//8)
            self.submodules += encoder
            self.comb += [
                sink.connect(source, omit={"data", "we"}),
                encoder.i.eq(sink.data[i*data_width_from//8:(i+1)*data_width_from//8]),
                source.data[i*data_width_to//8:(i+1)*data_width_to//8].eq(encoder.o)
            ]
        self.comb += source.we.eq(2**len(source.we)-1)

# LiteDRAMNativePortECCR ---------------------------------------------------------------------------

class LiteDRAMNativePortECCR(Module):
    def __init__(self, data_width_from, data_width_to):
        self.sink   = sink   = Endpoint(rdata_description(data_width_to))
        self.source = source = Endpoint(rdata_description(data_width_from))
        self.enable = Signal()
        self.sec    = Signal(8)
        self.ded    = Signal(8)

        # # #

        self.comb +=  sink.connect(source, omit={"data"})

        for i in range(8):
            decoder = ECCDecoder(data_width_from//8)
            self.submodules += decoder
            self.comb += [
                decoder.enable.eq(self.enable),
                decoder.i.eq(sink.data[i*data_width_to//8:(i+1)*data_width_to//8]),
                source.data[i*data_width_from//8:(i+1)*data_width_from//8].eq(decoder.o),
                If(source.valid,
                    self.sec[i].eq(decoder.sec),
                    self.ded[i].eq(decoder.ded)
                )
            ]

# LiteDRAMNativePortECC ----------------------------------------------------------------------------

class LiteDRAMNativePortECC(Module, AutoCSR):
    def __init__(self, port_from, port_to, with_error_injection=False):
        _ , n = compute_m_n(port_from.data_width//8)
        assert port_to.data_width >= (n + 1)*8

        self.enable     = CSRStorage(reset=1)
        self.clear      = CSR()
        self.sec_errors = CSRStatus(32)
        self.ded_errors = CSRStatus(32)
        self.sec_detected = sec_detected = Signal()
        self.ded_detected = ded_detected = Signal()
        if with_error_injection:
            self.flip = CSRStorage(8)

        # # #

        # Cmd --------------------------------------------------------------------------------------
        self.comb += port_from.cmd.connect(port_to.cmd)

        # Wdata (ecc encoding) ---------------------------------------------------------------------
        ecc_wdata = LiteDRAMNativePortECCW(port_from.data_width, port_to.data_width)
        ecc_wdata = BufferizeEndpoints({"source": DIR_SOURCE})(ecc_wdata)
        self.submodules += ecc_wdata
        self.comb += [
            port_from.wdata.connect(ecc_wdata.sink),
            ecc_wdata.source.connect(port_to.wdata)
        ]
        if with_error_injection:
            self.comb += port_to.wdata.data[:8].eq(self.flip.storage ^ ecc_wdata.source.data[:8])

        # Rdata (ecc decoding) ---------------------------------------------------------------------
        sec = Signal()
        ded = Signal()
        ecc_rdata = LiteDRAMNativePortECCR(port_from.data_width, port_to.data_width)
        ecc_rdata = BufferizeEndpoints({"source": DIR_SOURCE})(ecc_rdata)
        self.submodules += ecc_rdata
        self.comb += [
            ecc_rdata.enable.eq(self.enable.storage),
            port_to.rdata.connect(ecc_rdata.sink),
            ecc_rdata.source.connect(port_from.rdata)
        ]

        # Errors count -----------------------------------------------------------------------------
        sec_errors = self.sec_errors.status
        ded_errors = self.ded_errors.status
        self.sync += [
            If(self.clear.re,
                sec_errors.eq(0),
                ded_errors.eq(0),
                sec_detected.eq(0),
                ded_detected.eq(0),
            ).Else(
                If(sec_errors != (2**len(sec_errors) - 1),
                    If(ecc_rdata.sec != 0,
                        sec_detected.eq(1),
                        sec_errors.eq(sec_errors + 1)
                    )
                ),
                If(ded_errors != (2**len(ded_errors) - 1),
                    If(ecc_rdata.ded != 0,
                        ded_detected.eq(1),
                        ded_errors.eq(ded_errors + 1)
                    )
                )
            )
        ]
