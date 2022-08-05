#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litedram.phy import dfi
from litex.soc.interconnect.csr import *
from litedram.phy.ddr5.commands import DFIPhaseAdapter

# PhaseInjector ------------------------------------------------------------------------------------

class PhaseInjector(Module, AutoCSR):
    def __init__(self, phase):
        self._command       = CSRStorage(fields=[
            CSRField("cs",   size=1, description="DFI chip select bus"),
            CSRField("we",   size=1, description="DFI write enable bus"),
            CSRField("cas",  size=1, description="DFI column address strobe bus"),
            CSRField("ras",  size=1, description="DFI row address strobe bus"),
            CSRField("wren", size=1, description="DFI write data enable bus"),
            CSRField("rden", size=1, description="DFI read data enable bus"),
        ], description="Control DFI signals on a single phase")

        self._command_issue = CSR() # description="The command gets commited on a write to this register"
        self._address       = CSRStorage(len(phase.address), reset_less=True,  description="DFI address bus")
        self._baddress      = CSRStorage(len(phase.bank),    reset_less=True,  description="DFI bank address bus")
        self._wrdata        = CSRStorage(len(phase.wrdata),  reset_less=True,  description="DFI write data bus")
        self._rddata        = CSRStatus(len(phase.rddata), description="DFI read data bus")

        # # #

        self.comb += [
            If(self._command_issue.re,
                phase.cs_n.eq(Replicate(~self._command.fields.cs, len(phase.cs_n))),
                phase.we_n.eq(~self._command.fields.we),
                phase.cas_n.eq(~self._command.fields.cas),
                phase.ras_n.eq(~self._command.fields.ras)
            ).Else(
                phase.cs_n.eq(Replicate(1, len(phase.cs_n))),
                phase.we_n.eq(1),
                phase.cas_n.eq(1),
                phase.ras_n.eq(1)
            ),
            phase.address.eq(self._address.storage),
            phase.bank.eq(self._baddress.storage),
            phase.wrdata_en.eq(self._command_issue.re & self._command.fields.wren),
            phase.rddata_en.eq(self._command_issue.re & self._command.fields.rden),
            phase.wrdata.eq(self._wrdata.storage),
            phase.wrdata_mask.eq(0)
        ]
        self.sync += If(phase.rddata_valid, self._rddata.status.eq(phase.rddata))

# CSInjector ------------------------------------------------------------------------------------

class ConstInjector(Module, AutoCSR):
    def __init__(self, phases):
        self._command       = CSRStorage(fields=[
            CSRField("cs",   size=1, description="DFI chip select bus"),
            CSRField("ca",   size=14, description="DFI chip select bus"),
        ], description="Control DFI signals on all Bus phases")

        # # #
        for phase in phases:
            self.comb += [
                phase.cs_n.eq(Replicate(~self._command.fields.cs, len(phase.cs_n))),
                phase.address.eq(self._command.fields.ca),
            ]

# NOPInjector ------------------------------------------------------------------------------------

class NOPInjector(Module, AutoCSR):
    def __init__(self, phases):
        # # #
        for phase in phases:
            self.comb += [
                phase.cs_n.eq(Replicate(0, len(phase.cs_n))),
                phase.address.eq(0b11111),
            ]

# DFIInjector --------------------------------------------------------------------------------------

class DFIInjector(Module, AutoCSR):
    def __init__(self, addressbits, bankbits, nranks, databits, nphases=1, memtype=None, strobes=None):
        self.slave   = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.master  = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        csr1_dfi     = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.intermediate   = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)

        self.ext_dfi     = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.ext_dfi_sel = Signal()

        if memtype == "DDR5":
            csr2_dfi     = dfi.Interface(14, 1, nranks, databits, nphases)
            csr3_dfi     = dfi.Interface(14, 1, nranks, databits, nphases)
            ddr5_dfi     = dfi.Interface(14, 1, nranks, databits, nphases)

            masked_writes  = False
            if databits//2//strobes in [8, 16]:
                masked_writes = True
            adapters = [DFIPhaseAdapter(phase, masked_writes) for phase in self.intermediate.phases]
            self.submodules += adapters

        if memtype == "DDR5":
            self.master = dfi.Interface(14, 1, nranks, databits, nphases)

        extra_fields = []
        if memtype == "DDR5":
            extra_fields = [
                CSRField("ddr5", size=2, values=[
                    ("``0b0``", "Pass through adapters signals"),
                    ("``0b1``", "Const Injector"),
                    ("``0b10``", "NOP Injector"),
                ], reset=0b0)
            ]

        self._control = CSRStorage(fields=[
            CSRField("sel",     size=1, values=[
                ("``0b0``", "Software (CPU) control."),
                ("``0b1``", "Hardware control (default)."),
            ], reset=0b1), # Defaults to HW control.
            CSRField("cke",     size=1, description="DFI clock enable bus"),
            CSRField("odt",     size=1, description="DFI on-die termination bus"),
            CSRField("reset_n", size=1, description="DFI clock reset bus"),
        ] + extra_fields,
        description="Control DFI signals common to all phases")

        for n, phase in enumerate(csr1_dfi.phases):
            setattr(self.submodules, "pi" + str(n), PhaseInjector(phase))
        if memtype == "DDR5":
            self.submodules.constinjector   = ConstInjector(csr2_dfi.phases)
            self.submodules.nopinjector     = NOPInjector(csr3_dfi.phases)

        # # #

        self.comb += [
            Case(self._control.fields.sel, {
                # Software Control (through CSRs).
                # --------------------------------
                0: csr1_dfi.connect(self.intermediate),
                # Hardware Control.
                # -----------------
                1: # Through External DFI.
                    If(self.ext_dfi_sel,
                        self.ext_dfi.connect(self.intermediate)
                    # Through LiteDRAM controller.
                    ).Else(
                        self.slave.connect(self.intermediate)
                    ),
            })
        ]
        for i in range(nranks):
            self.comb += [phase.cke[i].eq(self._control.fields.cke) for phase in csr1_dfi.phases]
            self.comb += [phase.odt[i].eq(self._control.fields.odt) for phase in csr1_dfi.phases if hasattr(phase, "odt")]
        self.comb += [phase.reset_n.eq(self._control.fields.reset_n) for phase in csr1_dfi.phases if hasattr(phase, "reset_n")]

        if memtype == "DDR5":
            for i in range(nranks):
                self.comb += [phase.cke[i].eq(self._control.fields.cke) for phase in csr2_dfi.phases]
                self.comb += [phase.odt[i].eq(self._control.fields.odt) for phase in csr2_dfi.phases if hasattr(phase, "odt")]

                self.comb += [phase.cke[i].eq(self._control.fields.cke) for phase in csr3_dfi.phases]
                self.comb += [phase.odt[i].eq(self._control.fields.odt) for phase in csr3_dfi.phases if hasattr(phase, "odt")]

            self.comb += [phase.reset_n.eq(self._control.fields.reset_n) for phase in csr2_dfi.phases if hasattr(phase, "reset_n")]
            self.comb += [phase.reset_n.eq(self._control.fields.reset_n) for phase in csr3_dfi.phases if hasattr(phase, "reset_n")]

            for ddr5_phase, inter_phase in zip(ddr5_dfi.phases, self.intermediate.phases):
                self.comb += [
                    ddr5_phase.wrdata.eq(inter_phase.wrdata),
                    ddr5_phase.wrdata_en.eq(inter_phase.wrdata_en),
                    ddr5_phase.wrdata_mask.eq(inter_phase.wrdata_mask),
                    ddr5_phase.rddata_en.eq(inter_phase.rddata_en),
                    inter_phase.rddata.eq(ddr5_phase.rddata),
                    inter_phase.rddata_valid.eq(ddr5_phase.rddata_valid),
                ]

            for phase in ddr5_dfi.phases:
                self.comb += [
                    phase.reset_n.eq(1),
                    phase.cs_n.eq(1),
                    phase.act_n.eq(1),
                    phase.address.eq(0),
                    phase.cke.eq(0),
                    phase.odt.eq(0),
                    phase.mode_2n.eq(0),
                ]
            for i, adapter in enumerate(adapters):
                for j in range(2):
                    phase_num = (j+i)%nphases
                    phase     = ddr5_dfi.phases[phase_num]
                    self.comb += [
                        If(adapter.valid,
                            phase.address.eq(phase.address | adapter.ca[j]),
                            phase.cs_n.eq(phase.cs_n & adapter.cs_n[j]),
                            phase.act_n.eq(phase.act_n & adapter.act_n[j]),
                        ),
                        phase.cke.eq(phase.cke | adapter.cke[j]),
                        phase.odt.eq(phase.odt | adapter.odt[j]),
                        phase.reset_n.eq(phase.reset_n & adapter.reset_n[j]),
                        phase.mode_2n.eq(phase.mode_2n | adapter.mode_2n[j])
                    ]

            self.comb += [
                Case(self._control.fields.ddr5, {
                    # Pass through.
                    # -------------
                    0: ddr5_dfi.connect(self.master),
                    # Const Injector.
                    # ---------------
                    1: csr2_dfi.connect(self.master),
                    # NOP Injector.
                    # -------------
                    2: csr3_dfi.connect(self.master),
                })
            ]
        else:
            self.comb += [self.intermediate.connect(self.master)]
