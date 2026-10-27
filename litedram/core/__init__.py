#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.soc.interconnect.csr import AutoCSR

from litedram.dfii import DFIInjector
from litedram.core.controller import ControllerSettings, LiteDRAMController
from litedram.core.crossbar import LiteDRAMCrossbar

# Core ---------------------------------------------------------------------------------------------

class LiteDRAMCore(Module, AutoCSR):
    def __init__(self, phy, geom_settings, timing_settings, clk_freq, with_ecc=False, with_ecc_bit_stats=False, **kwargs):
        # with_ecc: SECDED on the PHY's ECC lanes (72-bit beats, see core/ecc.py). The controller
        # then sees 64 data bits per beat; the DFI injector keeps the raw PHY width (calibration).
        # with_ecc_bit_stats: with the ECC, a corrected-error counter per DQ bit (bitsel/bitcnt
        # CSRs: which bits of the interface fail). It costs ~4000 flip-flops on a 72-bit 1:4 PHY
        # (72 32-bit counters, a re-encoder and 3 registered beats per DFI beat, a 72:1 read mux),
        # off the data path. Off by default: the BIOS read-eye scan uses the counters when present
        # (CSR_SDRAM_ECC_BITSEL_ADDR) and otherwise finds the failing bits one at a time with the
        # beat counters; enable it for a faster scan or to see which DQ fail in operation.
        self.submodules.dfii = DFIInjector(
            addressbits   = max(geom_settings.addressbits, getattr(phy, "addressbits", 0)),
            bankbits      = max(geom_settings.bankbits, getattr(phy, "bankbits", 0)),
            nranks        = phy.settings.nranks,
            databits      = phy.settings.dfi_databits,
            nphases       = phy.settings.nphases,
            is_clam_shell = phy.settings.is_clam_shell)
        self.comb += self.dfii.master.connect(phy.dfi)

        phy_settings = phy.settings
        if with_ecc:
            from litedram.core.ecc import LiteDRAMDFIECC, ecc_phy_settings
            phy_settings = ecc_phy_settings(phy.settings)

        self.submodules.controller = controller = LiteDRAMController(
            phy_settings    = phy_settings,
            geom_settings   = geom_settings,
            timing_settings = timing_settings,
            clk_freq        = clk_freq,
            **kwargs)
        if with_ecc:
            self.submodules.ecc = ecc = LiteDRAMDFIECC(
                addressbits      = max(geom_settings.addressbits, getattr(phy, "addressbits", 0)),
                bankbits         = max(geom_settings.bankbits, getattr(phy, "bankbits", 0)),
                nranks           = phy.settings.nranks,
                phy_dfi_databits = phy.settings.dfi_databits,
                nphases          = phy.settings.nphases,
                with_bit_stats   = with_ecc_bit_stats)
            self.comb += controller.dfi.connect(ecc.slave)
            self.comb += ecc.master.connect(self.dfii.slave)
        else:
            self.comb += controller.dfi.connect(self.dfii.slave)

        self.submodules.crossbar = LiteDRAMCrossbar(controller.interface)
