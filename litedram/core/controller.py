#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""LiteDRAM Controller."""

from migen import *

from litedram.common import *
from litedram.phy import dfi
from litedram.core.refresher import Refresher
from litedram.core.bankmachine import BankMachine
from litedram.core.multiplexer import Multiplexer

# Settings -----------------------------------------------------------------------------------------

class ControllerSettings(Settings):
    def __init__(self,
        # Command buffers.
        cmd_buffer_depth    = 8,              # Depth of the command buffer (number of entries).
        cmd_buffer_buffered = False,          # Enable or disable buffered command mode.

        # Bank machines.
        nbankmachines       = None,           # Number of bank machines (None: one per bank). Fewer
                                              # bank machines share them between consecutive banks
                                              # (power of 2 dividing nbanks, nranks=1): less resources
                                              # but one open row per bank machine, so less efficiency
                                              # when accesses alternate between banks.

        # Read/Write times (anti-starvation): maximum time (in cycles) the multiplexer keeps issuing
        # reads (resp. writes) while writes (resp. reads) are pending, before switching. Each switch
        # costs a read-to-write or write-to-read turnaround (several cycles), so longer windows give
        # more bandwidth on mixed traffic (DDR3-1600 1:4 saturated read/write mix: 32/16 -> 74% of
        # cycles with a CAS, 64/32 -> 85%, 128/64 -> 92%) at the cost of a longer worst-case wait for
        # the other direction.
        read_time           = 64,
        write_time          = 32,

        # Bandwidth.
        with_bandwidth      = False,          # Enable bandwidth calculation and monitoring.

        # Refresh.
        with_refresh        = True,           # Enable periodic refresh operations.
        refresh_cls         = Refresher,      # Class used for refresh logic.
        refresh_zqcs_freq   = 1e0,            # Frequency of ZQCS (ZQ Calibration Short) commands.
        refresh_postponing  = 1,              # Maximum number of refresh postponements allowed.

        # Auto-Precharge.
        with_auto_precharge = True,           # Enable auto-precharge after read/write operations.

        # Address mapping.
        address_mapping     = "ROW_BANK_COL", # Address mapping scheme (e.g., row-bank-column).

        # Bank byte alignment.
        bank_byte_alignment = 0):             # Minimum byte alignment between bank changes. Ensures a
                                              # specific byte distance between consecutive banks to optimize
                                              # data placement for cache line mapping (e.g., aligning to L2
                                              # cache set size). For a 256KB L2 cache with 4 ways, the set
                                              # size is 256KB / 4 = 64KB, suggesting a bank_byte_alignment
                                              # of 0x10000.
        self.set_attributes(locals())


# Controller ---------------------------------------------------------------------------------------

class LiteDRAMController(Module):
    def __init__(self, phy_settings, geom_settings, timing_settings, clk_freq,
        controller_settings=None):
        if controller_settings is None:
            controller_settings = ControllerSettings()
        if phy_settings.memtype == "SDR":
            burst_length = phy_settings.nphases
        else:
            burst_length = burst_lengths[phy_settings.memtype]
        address_align = log2_int(burst_length)

        # Settings ---------------------------------------------------------------------------------
        self.settings        = controller_settings
        self.settings.phy    = phy_settings
        self.settings.geom   = geom_settings
        self.settings.timing = timing_settings

        nranks = phy_settings.nranks
        nbanks = 2**geom_settings.bankbits

        # LiteDRAM Interface (User) ----------------------------------------------------------------
        self.interface = interface = LiteDRAMInterface(address_align, self.settings)

        # DFI Interface (Memory) -------------------------------------------------------------------
        self.dfi = dfi.Interface(
            addressbits = geom_settings.addressbits,
            bankbits    = geom_settings.bankbits,
            nranks      = phy_settings.nranks,
            databits    = phy_settings.dfi_databits,
            nphases     = phy_settings.nphases)

        # # #

        # Refresher --------------------------------------------------------------------------------
        self.submodules.refresher = self.settings.refresh_cls(self.settings,
            clk_freq   = clk_freq,
            zqcs_freq  = self.settings.refresh_zqcs_freq,
            postponing = self.settings.refresh_postponing)

        # Bank Machines ----------------------------------------------------------------------------
        nbankmachines = getattr(self.settings, "nbankmachines", None) or nranks*nbanks
        if (nbankmachines & (nbankmachines - 1)) or (nranks*nbanks) % nbankmachines:
            raise ValueError("nbankmachines ({}) must be a power of 2 dividing nranks*nbanks ({}).".format(
                nbankmachines, nranks*nbanks))
        if (nbankmachines != nranks*nbanks) and (nranks > 1):
            raise NotImplementedError("Shared bank machines (nbankmachines) only support nranks=1.")
        banks_per_bm  = (nranks*nbanks)//nbankmachines
        bank_machines = []
        for n in range(0, nranks*nbanks, banks_per_bm):
            bank_machine = BankMachine(n,
                address_width = interface.address_width,
                address_align = address_align,
                nranks        = nranks,
                settings      = self.settings,
                nbanks        = banks_per_bm)
            bank_machines.append(bank_machine)
            self.submodules += bank_machine
            for i, req in enumerate(bank_machine.reqs):
                self.comb += getattr(interface, "bank"+str(n+i)).connect(req)

        # Multiplexer ------------------------------------------------------------------------------
        self.submodules.multiplexer = Multiplexer(
            settings      = self.settings,
            bank_machines = bank_machines,
            refresher     = self.refresher,
            dfi           = self.dfi,
            interface     = interface)

    def get_csrs(self):
        return self.multiplexer.get_csrs()
