#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litedram.phy import dfi
from litedram.common import TappedDelayLine
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

# CommandsInjector ------------------------------------------------------------------------------

class CmdInjector(Module, AutoCSR):
    def __init__(self, phases, masked_writes=False):
        num_phases = len(phases)
        assert num_phases > 0
        cs_width = len(phases[0].cs_n)
        wrdata_width = len(phases[0].wrdata)
        rddata_width = len(phases[0].rddata)
        wrdata_mask_width = len(phases[0].wrdata_mask)

        self._command_storage = CSRStorage(fields=[
            CSRField("ca",          size=14,        description="Command/Address bus"),
            CSRField("cs",          size=cs_width,  description="DFI chip select bus"),
            CSRField("wrdata_en",   size=1),
            CSRField("wrdata_mask", size=wrdata_mask_width),
            CSRField("rddata_en",   size=1),
        ], description="DDR5 command and control signals")
        self._phase_addr = CSRStorage(num_phases)
        self._store_continuous_cmd = CSR()
        self._store_singleshot_cmd = CSR()
        self._single_shot = CSRStorage(reset=0b0)
        self._issue_command = CSR() # Only used when in single shot

        self._continuous_phase_signals = Array(Signal(16 + cs_width + wrdata_mask_width, reset=0b11111) for _ in range(num_phases))
        self._singleshot_phase_signals = Array(Signal(16 + cs_width + wrdata_mask_width) for _ in range(num_phases))

        ca_start = 0
        cs_start = ca_end = 0 + 14
        wr_en_start = cs_end = cs_start + cs_width
        wr_mask_start = wr_en_end = wr_en_start + 1
        rd_en_start = wr_mask_end = wr_mask_start + wrdata_mask_width
        rd_en_end = rd_en_start + 1

        for i, phase in enumerate(phases):
            self.sync += [
                If(self._store_continuous_cmd.re,
                    If(self._phase_addr.storage[i],
                        self._continuous_phase_signals[i].eq(self._command_storage.storage),
                    ),
                ),
                If(self._store_singleshot_cmd.re,
                    If(self._phase_addr.storage[i],
                        self._singleshot_phase_signals[i].eq(self._command_storage.storage),
                    ),
                ),
            ]

            self.comb += [
                If(self._single_shot.storage & self._issue_command.re,
                    phase.cs_n.eq(~self._singleshot_phase_signals[i][cs_start:cs_end]),
                    phase.address.eq(self._singleshot_phase_signals[i][ca_start:ca_end]),
                    phase.wrdata_en.eq(self._singleshot_phase_signals[i][wr_en_start:wr_en_end]),
                    phase.wrdata_mask.eq(self._singleshot_phase_signals[i][wr_mask_start:wr_mask_end]),
                    phase.rddata_en.eq(self._singleshot_phase_signals[i][rd_en_start:rd_en_end]),
                ).Else(
                    phase.cs_n.eq(~self._continuous_phase_signals[i][cs_start:cs_end]),
                    phase.address.eq(self._continuous_phase_signals[i][ca_start:ca_end]),
                    phase.wrdata_en.eq(self._continuous_phase_signals[i][wr_en_start:wr_en_end]),
                    phase.wrdata_mask.eq(self._continuous_phase_signals[i][wr_mask_start:wr_mask_end]),
                    phase.rddata_en.eq(self._continuous_phase_signals[i][rd_en_start:rd_en_end]),
                ),
            ]

        self._wrdata_select = CSRStorage(num_phases.bit_length())
        self._wrdata = CSRStorage(wrdata_width)
        self._wrdata_store = CSR()

        self.wrdata = Array(Signal(wrdata_width) for _ in range(num_phases))

        self.sync += [
            If(self._wrdata_store.re,
                self.wrdata[self._wrdata_select.storage].eq(self._wrdata.storage)
            ),
        ]
        self.comb += [
            phase.wrdata.eq(self.wrdata[i]) for i, phase in enumerate(phases)
        ]

        self._rddata_select = CSRStorage(num_phases.bit_length())
        self._rddata = CSRStatus(rddata_width)
        self._rddata_capture = CSR() # force capture of rddata bus

        self.rddata = Array(Signal(rddata_width) for _ in range(num_phases))

        self.sync += [
            self._rddata.status.eq(self.rddata[self._rddata_select.storage])
        ]
        self.sync += [
            If(phase.rddata_valid | self._rddata_capture.re,
                self.rddata[i].eq(phase.rddata)) for i, phase in enumerate(phases)
        ]

# DFIInjector --------------------------------------------------------------------------------------

class DFIInjector(Module, AutoCSR):
    def __init__(self, addressbits, bankbits, nranks, databits, nphases=1,
                 memtype=None, strobes=None, with_sub_channels=False):
        self.slave   = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.master  = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        csr1_dfi     = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.intermediate   = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)

        self.ext_dfi     = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.ext_dfi_sel = Signal()

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]

        if memtype == "DDR5":
            csr2_dfi     = dfi.Interface(14, 1, nranks, databits, nphases, with_sub_channels)
            ddr5_dfi     = dfi.Interface(14, 1, nranks, databits, nphases)

            masked_writes  = False
            if databits//2//strobes in [8, 16]:
                masked_writes = True
            adapters = [DFIPhaseAdapter(phase, masked_writes) for phase in self.intermediate.phases]
            self.submodules += adapters

        if memtype == "DDR5":
            self.master = dfi.Interface(14, 1, nranks, databits, nphases, with_sub_channels)

        extra_fields = []
        if memtype == "DDR5":
            extra_fields.append(
                CSRField("mode_2n", size=1, values=[
                    ("``0b0``", "In 1N mode"),
                    ("``0b1``", "In 2N mode (Default)"),
                ], reset=0b1)
            )
            for prefix in prefixes:
                extra_fields.append(
                    CSRField(prefix+"control", size=1, values=[
                        ("``0b1``", prefix+"Cmd Injector"),
                    ], reset=0b0)
                )

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

        if memtype != "DDR5":
            for n, phase in enumerate(csr1_dfi.phases):
                setattr(self.submodules, "pi" + str(n), PhaseInjector(phase))
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
            self.comb += [self.intermediate.connect(self.master)]

        else: # memtype == "DDR5"
            self.comb += [
                # Hardware Control.
                # -----------------
                # Through External DFI
                If(self.ext_dfi_sel,
                    self.ext_dfi.connect(self.intermediate)
                # Through LiteDRAM controller.
                ).Else(
                    self.slave.connect(self.intermediate)
                ),
            ]

            for prefix in prefixes:
                setattr(self.submodules, prefix.lower()+"cmdinjector", CmdInjector(csr2_dfi.get_subchannel(prefix), masked_writes))

            for ddr5_phase, inter_phase in zip(ddr5_dfi.phases, self.intermediate.phases):
                self.comb += [
                    ddr5_phase.wrdata.eq(inter_phase.wrdata),
                    ddr5_phase.wrdata_en.eq(inter_phase.wrdata_en),
                    ddr5_phase.wrdata_mask.eq(inter_phase.wrdata_mask),
                    ddr5_phase.rddata_en.eq(inter_phase.rddata_en),
                    inter_phase.rddata.eq(ddr5_phase.rddata),
                    inter_phase.rddata_valid.eq(ddr5_phase.rddata_valid),
                ]

            # DDR5 has commands that take either 1 or 2 CA cycles. It also has
            # a 2N mode that is enabled by default. It is designed to stretch
            # single CA packet to 2 clock cycles. It is necessary when CA and
            # CS aren't trained. Adapter modules from phy/ddr5/commands.py solve
            # translation from the old DDR4 commands to DDR5 type. If an adapter
            # creates 2 beat command, and command was in phase 3 and DFI has 4
            # phases, we have to carry next part of command to next clock cycle.
            # This issue is even more profound when 2N mode is used. All commands
            # will take 2 or 4 cycles to be correctly transmitted.

            depth = max(nphases//4, 1)

            delays = [[] * depth]

            for i in range(depth):
                for _ in range(nphases):
                    _input = Signal(14+nranks)
                    delays[i].append((_input, TappedDelayLine(signal=_input, ntaps=i+1)))

            for i, adapter in enumerate(adapters):
                # 0 CA0 always
                # 1 CA0 if 2N mode or CA1 if 1N mode
                # 2 CA1 if 2N mode
                # 3 CA1 if 2N mode

                phase = ddr5_dfi.phases[i]
                self.comb += [
                    If(adapter.valid,
                        phase.address.eq(phase.address | adapter.ca[0]),
                        phase.cs_n.eq(phase.cs_n & adapter.cs_n[0]),
                    ),
                    phase.reset_n.eq(adapter.reset_n[0]),
                    phase.mode_2n.eq(adapter.mode_2n[0]),
                ]

                phase_num = (i+1) % nphases
                delay     = (i+1) // nphases
                if delay:
                    _input, _ = delays[delay-1][phase_num]
                    self.comb += If(self._control.fields.mode_2n & adapter.valid,
                        _input.eq(Cat(adapter.cs_n[0], adapter.ca[0])),
                    ).Elif(adapter.valid,
                        _input.eq(Cat(adapter.cs_n[1], adapter.ca[1])),
                    ).Else(
                        _input.eq(0),
                    )
                else:
                    phase = ddr5_dfi.phases[phase_num]
                    self.comb += If(self._control.fields.mode_2n & adapter.valid,
                        phase.address.eq(phase.address | adapter.ca[0]),
                        phase.cs_n.eq(phase.cs_n & adapter.cs_n[0]),
                    ).Elif(adapter.valid,
                        phase.address.eq(phase.address | adapter.ca[1]),
                        phase.cs_n.eq(phase.cs_n & adapter.cs_n[1]),
                    )

                for j in [2,3]:
                    phase_num = (j+i) % nphases
                    delay     = (i+j) // nphases # Number of cycles to delay
                    if delay:
                        _input, _ = delays[delay-1][phase_num]
                        self.comb += If(self._control.fields.mode_2n & adapter.valid,
                            _input.eq(Cat(adapter.cs_n[j//2], adapter.ca[j//2])),
                        ).Else(
                            _input.eq(0),
                        )
                    else:
                        phase = ddr5_dfi.phases[phase_num]
                        self.comb += If(self._control.fields.mode_2n & adapter.valid,
                            phase.address.eq(phase.address | adapter.ca[j//2]),
                            phase.cs_n.eq(phase.cs_n & adapter.cs_n[j//2]),
                        )

            for i in range(depth):
                for (_, delay_out), phase in zip(delays[i], ddr5_dfi.phases):
                    phase.cs_n.eq(   phase.cs_n    | delay_out.output[0:nranks])
                    phase.address.eq(phase.address | delay_out.output[nranks:-1])

            if with_sub_channels:
                ddr5_dfi.create_sub_channels()
                ddr5_dfi.remove_common_signals()

            self.comb += [
                Case(self._control.fields.sel, {
                    # Software Control (through CSRs).
                    # --------------------------------
                    0: [
                        Case(getattr(self._control.fields, prefix+"control"), {
                            1: [cp.connect(mp) for cp, mp in zip(csr2_dfi.get_subchannel(prefix), self.master.get_subchannel(prefix))],
                            0: [cp.connect(mp) for cp, mp in zip(ddr5_dfi.get_subchannel(prefix), self.master.get_subchannel(prefix))], # Use Hardware control for unselected channel
                        }) for prefix in prefixes
                    ] + [
                        phase.reset_n.eq(self._control.fields.reset_n) for phase in self.master.phases if hasattr(phase, "reset_n")
                    ],
                    # Hardware Control.
                    # -----------------
                    1: ddr5_dfi.connect(self.master),
                })
            ]
