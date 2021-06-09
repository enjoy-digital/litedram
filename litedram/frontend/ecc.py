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
- Write byte enable granularity of DRAM's data-width.
"""

from migen import *

from litex.soc.interconnect.csr import *
from litex.soc.interconnect.stream import *
from litex.soc.cores.ecc import *

from litedram.common import wdata_description, rdata_description


# LiteDRAMNativePortECCW ---------------------------------------------------------------------------

class LiteDRAMNativePortECCW(Module):
    def __init__(self, data_width_from, data_width_to, burst_cycles=8):
        self.sink     = sink   = Endpoint(wdata_description(data_width_from))
        self.source   = source = Endpoint(wdata_description(data_width_to))
        self.we_error = Signal()

        # # #

        # Control (ECC encoding is combinatorial).
        self.comb += sink.connect(source, omit={"data", "we"}),

        # Data Path.
        for i in range(burst_cycles):
            ecc_width_from = data_width_from // burst_cycles
            ecc_width_to   = data_width_to   // burst_cycles

            # Encoder.
            self.submodules.encoder = encoder = ECCEncoder(ecc_width_from)
            self.comb += [
                # Input.
                encoder.i.eq(sink.data[i*ecc_width_from:(i+1)*ecc_width_from]),
                # Output.
                # We always have to store the full ECC-Word so byte enable is not supported within
                # an ECC word. If any of the byte enable is set, the full ECC-Word is written.
                If(sink.we[i*ecc_width_from//8:(i+1)*ecc_width_from//8] != 0,
                    source.we[i*ecc_width_to//8:(i+1)*ecc_width_to//8].eq(2**ecc_width_to//8-1)
                ),
                source.data[i*ecc_width_to:(i+1)*ecc_width_to].eq(encoder.o),
                # Byte enable granularity  error detection.
                If(sink.valid & (sink.we[i*ecc_width_from//8:(i+1)*ecc_width_from//8] != (2**ecc_width_from//8-1)),
                    self.we_error.eq(1)
                )
            ]

# LiteDRAMNativePortECCR ---------------------------------------------------------------------------

class LiteDRAMNativePortECCR(Module):
    def __init__(self, data_width_from, data_width_to, burst_cycles=8):
        self.sink   = sink   = Endpoint(rdata_description(data_width_to))
        self.source = source = Endpoint(rdata_description(data_width_from))
        self.enable = Signal()
        self.sec    = Signal(burst_cycles)
        self.ded    = Signal(burst_cycles)

        # # #

        # Control Path (ECC decoding is combinatorial).
        self.comb +=  sink.connect(source, omit={"data"})

        # Data Path.
        for i in range(burst_cycles):
            ecc_width_to   = data_width_to   // burst_cycles
            ecc_width_from = data_width_from // burst_cycles

            # Decoder.
            self.submodules.decoder = decoder = ECCDecoder(ecc_width_from)
            self.comb += [
                # Enable.
                decoder.enable.eq(self.enable),
                # Input.
                decoder.i.eq(sink.data[i*ecc_width_to:(i+1)*ecc_width_to]),
                # Output.
                source.data[i*ecc_width_from:(i+1)*ecc_width_from].eq(decoder.o),
                # Bitflip/Error reporting.
                If(source.valid,
                    self.sec[i].eq(decoder.sec),
                    self.ded[i].eq(decoder.ded)
                )
            ]

# LiteDRAMNativePortECC ----------------------------------------------------------------------------

class LiteDRAMNativePortECC(Module, AutoCSR):
    def __init__(self, port_from, port_to, burst_cycles=8, with_error_injection=False, with_we_error_detection=False):
        _ , n = compute_m_n(port_from.data_width//burst_cycles)
        assert port_to.data_width >= (n + 1)*burst_cycles

        self.enable     = CSRStorage(reset=1)
        self.clear      = CSR()
        self.sec_errors = CSRStatus(32)
        self.ded_errors = CSRStatus(32)
        self.sec_detected = sec_detected = Signal()
        self.ded_detected = ded_detected = Signal()
        if with_error_injection:
            self.flip = CSRStorage(8)
        if with_we_error_detection:
            self.we_errors = CSRStatus(32)

        # # #

        # Cmd --------------------------------------------------------------------------------------
        self.comb += port_from.cmd.connect(port_to.cmd)

        # Wdata (ECC) encoding) --------------------------------------------------------------------
        ecc_wdata = LiteDRAMNativePortECCW(port_from.data_width, port_to.data_width, burst_cycles)
        ecc_wdata = BufferizeEndpoints({"source": DIR_SOURCE})(ecc_wdata)
        self.submodules += ecc_wdata
        self.comb += [
            port_from.wdata.connect(ecc_wdata.sink),
            ecc_wdata.source.connect(port_to.wdata)
        ]
        if with_error_injection:
            self.comb += port_to.wdata.data[:8].eq(self.flip.storage ^ ecc_wdata.source.data[:8])

        # Rdata (ECC decoding) ---------------------------------------------------------------------
        sec = Signal()
        ded = Signal()
        ecc_rdata = LiteDRAMNativePortECCR(port_from.data_width, port_to.data_width, burst_cycles)
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
        if with_we_error_detection:
            we_errors = self.we_errors.status
            self.sync += [
                If(self.clear.re,
                    we_errors.eq(0),
                ).Else(
                    If(we_errors != (2**len(we_errors) - 1),
                        If(ecc_wdata.we_error,
                            we_errors.eq(we_errors + 1)
                        )
                    )
                )
            ]
