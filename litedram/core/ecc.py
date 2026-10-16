#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""DFI-level ECC (SECDED) for memories with an ECC byte lane (72-bit DDR channels).

The controller sees a 64-bit-per-beat PHY; `LiteDRAMDFIECC` sits between the controller's DFI and
the DFI injector (which keeps raw 72-bit access to the PHY for the calibration) and:

- on writes, appends to every 64-bit beat its 8 SECDED check bits (on the ECC lane, DQ[64:72]),
- on reads, corrects any single-bit error of a 72-bit beat and flags double-bit errors, one cycle
  later (the controller's read latency includes it: see `ecc_phy_settings`).

The data bits stay on DQ[0:64] in order, the check bits on the ECC lane: a raw read of the data
lanes is the data. Writes must be full beats (the check bits cover the whole 64-bit word): use
it on a memory without data masks, or with full-word writes (the L2 cache and the BIST write full
words; a frontend with partial writes needs read-modify-write, see LiteDRAMAXI2Native).
"""

import copy
from functools import reduce
from operator import or_

from migen import *

from litex.gen import *

from litex.soc.interconnect.csr import *
from litex.soc.cores.ecc import ECCEncoder, ECCDecoder

from litedram.phy import dfi

# Helpers ------------------------------------------------------------------------------------------

ECC_DATABITS  = 64 # Data bits per beat.
ECC_CHECKBITS = 8  # SECDED(64) check bits per beat: 7 syndrome + 1 parity.
ECC_LATENCY   = 1  # Read decode register.

def _codeword_positions():
    """(data, check) bit positions in the 72-bit ECCEncoder output: o[0] is the overall parity,
    o[j] (j = 1..71) the Hamming codeword position j, syndrome bits at the powers of two."""
    check = [0] + [1 << i for i in range(7)]
    data  = [j for j in range(1, 72) if j not in check]
    assert len(data) == ECC_DATABITS and len(check) == ECC_CHECKBITS
    return data, check

def ecc_phy_settings(phy_settings):
    """The controller-side view of a PHY with ECC lanes: 64 data bits per beat (per 72 on the DFI)
    and the decode register in the read latency."""
    assert phy_settings.databits % (ECC_DATABITS + ECC_CHECKBITS) == 0, \
        "DFI ECC needs 72-bit beats (an ECC byte lane per 64 data bits)."
    words    = phy_settings.databits//(ECC_DATABITS + ECC_CHECKBITS)
    settings = copy.copy(phy_settings)
    settings.ecc_databits     = phy_settings.databits     # Raw (DFI) widths, for the C header.
    settings.ecc_dfi_databits = phy_settings.dfi_databits
    settings.databits         = words*ECC_DATABITS
    settings.dfi_databits     = phy_settings.dfi_databits*ECC_DATABITS//(ECC_DATABITS + ECC_CHECKBITS)
    settings.read_latency     = phy_settings.read_latency + ECC_LATENCY
    if getattr(phy_settings, "strobes", None) is not None: # One strobe per byte lane.
        settings.strobes = phy_settings.strobes*ECC_DATABITS//(ECC_DATABITS + ECC_CHECKBITS)
    return settings

# DFI ECC ------------------------------------------------------------------------------------------

class LiteDRAMDFIECC(LiteXModule):
    """SECDED between a controller's DFI (`slave`, 64 bits per beat) and the PHY side (`master`,
    72 bits per beat). CSRs: `enable` (correction on, reset 1), `sec`/`ded` counters of corrected
    single-bit and detected double-bit beats, `clear`."""
    def __init__(self, addressbits, bankbits, nranks, phy_dfi_databits, nphases):
        raw   = ECC_DATABITS + ECC_CHECKBITS
        assert phy_dfi_databits % raw == 0
        beats = phy_dfi_databits//raw # Beats per phase (2 on a DDR PHY).
        self.slave  = slave  = dfi.Interface(addressbits, bankbits, nranks, beats*ECC_DATABITS, nphases)
        self.master = master = dfi.Interface(addressbits, bankbits, nranks, phy_dfi_databits,   nphases)

        self.enable = CSRStorage(1, reset=1, description="Correct single-bit errors.")
        self.clear  = CSR()
        self.sec    = CSRStatus(32, description="Beats with a corrected single-bit error.")
        self.ded    = CSRStatus(32, description="Beats with a detected double-bit error.")

        # # #

        d_pos, c_pos = _codeword_positions()
        sec_any = Signal()
        ded_any = Signal()
        secs, deds = [], []

        for s, m in zip(slave.phases, master.phases):
            # Commands and enables: straight through.
            for name in ["address", "bank", "cas_n", "cs_n", "ras_n", "we_n", "cke", "odt",
                         "reset_n", "act_n", "wrdata_en", "rddata_en"]:
                self.comb += getattr(m, name).eq(getattr(s, name))
            # Valid one cycle later, with the decoded data.
            self.sync += s.rddata_valid.eq(m.rddata_valid)

            for b in range(beats):
                # Write: data on DQ[0:64], check bits on DQ[64:72].
                enc = ECCEncoder(ECC_DATABITS)
                self.submodules += enc
                self.comb += enc.i.eq(s.wrdata[b*ECC_DATABITS:(b + 1)*ECC_DATABITS])
                self.comb += m.wrdata[b*raw:b*raw + ECC_DATABITS].eq(enc.i)
                for k, p in enumerate(c_pos):
                    self.comb += m.wrdata[b*raw + ECC_DATABITS + k].eq(enc.o[p])
                # Masks: the data bytes' as given, the ECC byte never masked (full-word writes).
                self.comb += m.wrdata_mask[b*raw//8:b*raw//8 + ECC_DATABITS//8].eq(
                    s.wrdata_mask[b*ECC_DATABITS//8:(b + 1)*ECC_DATABITS//8])

                # Read: rebuild the codeword, correct, register.
                dec = ECCDecoder(ECC_DATABITS)
                self.submodules += dec
                self.comb += dec.enable.eq(self.enable.storage)
                for k, p in enumerate(d_pos):
                    self.comb += dec.i[p].eq(m.rddata[b*raw + k])
                for k, p in enumerate(c_pos):
                    self.comb += dec.i[p].eq(m.rddata[b*raw + ECC_DATABITS + k])
                self.sync += s.rddata[b*ECC_DATABITS:(b + 1)*ECC_DATABITS].eq(dec.o)
                sec_b, ded_b = Signal(), Signal()
                self.sync += [
                    sec_b.eq(dec.sec & ~dec.ded & m.rddata_valid),
                    ded_b.eq(dec.ded & m.rddata_valid),
                ]
                secs.append(sec_b)
                deds.append(ded_b)

        # Counters (one count per cycle with any corrected / uncorrectable beat).
        sec_cnt = Signal(32)
        ded_cnt = Signal(32)
        self.comb += [
            sec_any.eq(reduce(or_, secs)),
            ded_any.eq(reduce(or_, deds)),
            self.sec.status.eq(sec_cnt),
            self.ded.status.eq(ded_cnt),
        ]
        self.sync += [
            If(self.clear.re,
                sec_cnt.eq(0),
                ded_cnt.eq(0),
            ).Else(
                If(sec_any & (sec_cnt != 0xffffffff), sec_cnt.eq(sec_cnt + 1)),
                If(ded_any & (ded_cnt != 0xffffffff), ded_cnt.eq(ded_cnt + 1)),
            )
        ]
