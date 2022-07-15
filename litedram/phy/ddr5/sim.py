#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import math
from operator import or_
from functools import reduce
from collections import defaultdict, OrderedDict

from migen import *

from litex.soc.interconnect.stream import ClockDomainCrossing
from litex.soc.interconnect.csr import AutoCSR

from litedram.common import TappedDelayLine
from litedram.phy.utils import delayed, edge
from litedram.phy.sim_utils import SimLogger, PulseTiming, log_level_getter
from litedram.phy.ddr5.commands import MPC
from litedram import modules


class DDR5Sim(Module, AutoCSR):
    """DDR5 DRAM simulator

    This module simulates an DDR5 DRAM chip to aid DDR5 PHY development/testing.
    It does not aim to simulate the internals of an DDR5 chip, rather it's behavior
    as seen by the PHY.

    The simulator monitors CS_n/CA pads listening for DDR5 commands and updates the module
    state depending on the command received. Any unexpected sequences are logged in simulation
    as errors/warnings. On read/write commands the data simulation module is triggered
    after CL/CWL and a data burst is handled, updating memory state.

    The simulator requires the following clock domains:
        sys4x:        4x the memory controller clock frequency, phase aligned.
        sys4x_90:     Phase shifted by 90 degrees vs sys4x.
        sys4x_ddr:    Phase aligned with sys4x, double the frequency.
        sys4x_90_ddr: Phase aligned with sys4x_90, double the frequency.

    Parameters
    ----------
    pads : DDR5SimulationPads
        DRAM pads
    sys_clk_freq : float
        System clock frequency
    cl : int
        DDR5 read latency (RL).
    cwl : int
        DDR5 write latency (WL).
    disable_delay : bool
        Disable checking of timings that rely on long CPU delays (mostly init sequence
        timings). This is useful when running LiteX BIOS with CONFIG_DISABLE_DELAYS on.
    log_level : str
        SimLogger initial logging level (formatted for parsing with `log_level_getter`).
    """
    def __init__(self, pads, *, sys_clk_freq, cl, cwl, disable_delay, log_level, geom_settings):
        log_level = log_level_getter(log_level)

        cd_cmd    = "sys4x_90"
        cd_dq_wr  = "sys4x_90_ddr"
        cd_dqs_wr = "sys4x_ddr"
        cd_dq_rd  = "sys4x_90_ddr"
        cd_dqs_rd = "sys4x_ddr"

        self.submodules.data_cdc = ClockDomainCrossing(
            [("we", 1), ("masked", 1), ("bank", geom_settings.bankbits), ("row", 18), ("col", 11)],
            cd_from=cd_cmd, cd_to=cd_dq_wr)

        cmd = CommandsSim(pads,
            data_cdc      = self.data_cdc,
            clk_freq      = 4*sys_clk_freq,
            log_level     = log_level("cmd"),
            geom_settings = geom_settings,
            init_delays   = not disable_delay,
        )
        self.submodules.cmd = ClockDomainsRenamer(cd_cmd)(cmd)

        data = DataSim(pads, self.cmd,
            cd_dq_wr  = cd_dq_wr,
            cd_dqs_wr = cd_dqs_wr,
            cd_dq_rd  = cd_dq_rd,
            cd_dqs_rd = cd_dqs_rd,
            clk_freq  = 2*4*sys_clk_freq,
            cl        = cl,
            cwl       = cwl,
            log_level = log_level("data"),
        )
        self.submodules.data = ClockDomainsRenamer(cd_dq_wr)(data)

# Commands -----------------------------------------------------------------------------------------

class CommandsSim(Module, AutoCSR):
    """Command simulation

    This module interprets DDR5 commands found on the CS_n/CA pads. It keeps track of currently
    opened rows (per bank) and stores the values of Mode Registers. It also checks that the DRAM
    initialization sequence is performed according to specification. On any read/write commands
    signals indicating a burst are sent to the data simulator for handling.

    Command simulator should work in the clock domain of `pads.clk_p` (SDR).
    """
    def __init__(self, pads, data_cdc, *, clk_freq, log_level, geom_settings, init_delays=False):
        self.submodules.log = log = SimLogger(log_level=log_level, clk_freq=clk_freq)
        self.log.add_csrs()

        # Mode Registers storage
        self.mode_regs = Array([Signal(8) for _ in range(256)])
        # Active banks
        self.number_of_banks = 2 ** geom_settings.bankbits;
        self.active_banks = Array([Signal() for _ in range(self.number_of_banks)])
        self.active_rows = Array([Signal(18) for _ in range(self.number_of_banks)])
        # Connection to DataSim
        self.data_en = TappedDelayLine(ntaps=26)
        self.data = data_cdc
        self.submodules += self.data, self.data_en

        # CS_n/CA shift registers
        cs_n = TappedDelayLine(pads.cs_n, ntaps=2)
        ca = TappedDelayLine(pads.ca, ntaps=2)
        self.submodules += cs_n, ca

        self.cs_n_low   = Signal(14)
        self.cs_n_high  = Signal(14)
        self.handle_cmd = Signal()
        self.mpc_op     = Signal(8)

        cmds_enabled = Signal()
        cmd_handlers = OrderedDict(
            MRW = self.mrw_handler(),
            REF = self.refresh_handler(),
            ACT = self.activate_handler(),
            PRE = self.precharge_handler(),
            RD  = self.read_handler(),
            MPC = self.mpc_handler(),
            WR  = self.write_handler(),
        )

        self.comb += [
            If(cmds_enabled,
                If(Cat(cs_n.taps) == 0b01,
                    self.handle_cmd.eq(1),
                    self.cs_n_low.eq(ca.taps[1]),
                    self.cs_n_high.eq(ca.taps[0]),
                )
            ),
            If(self.handle_cmd & ~reduce(or_, cmd_handlers.values()),
                self.log.error("Unexpected command: cs_n_low=0b%14b cs_n_high=0b%14b", self.cs_n_low, self.cs_n_high)
            ),
        ]

        def ck(t):
            return math.ceil(t * clk_freq)

        self.submodules.tinit0 = PulseTiming(ck(20e-3))  # makes no sense in simulation
        self.submodules.tinit1 = PulseTiming(ck(200e-6))
        self.submodules.tinit2 = PulseTiming(ck(10e-9))
        self.submodules.tinit3 = PulseTiming(ck(2e-3))
        self.submodules.tinit4 = PulseTiming(5)  # TODO: would require counting pads.clk_p ticks
        self.submodules.tinit5 = PulseTiming(ck(2e-6))
        self.submodules.tzqcal = PulseTiming(ck(1e-6))
        self.submodules.tzqlat = PulseTiming(max(8, ck(30e-9)))
        self.submodules.tpw_reset = PulseTiming(ck(100e-9))

        self.comb += [
            self.tinit1.trigger.eq(1),
            self.tinit3.trigger.eq(pads.reset_n),
            self.tpw_reset.trigger.eq(~pads.reset_n),
            If(~delayed(self, pads.reset_n) & pads.reset_n,
                self.log.info("RESET released"),
                If(~self.tinit1.ready,
                    self.log.warn("tINIT1 violated: RESET deasserted too fast")
                ),
            ),
            If(delayed(self, pads.reset_n) & ~pads.reset_n,
                self.log.info("RESET asserted"),
            ),
        ]

        self.submodules.fsm = fsm = ResetInserter()(FSM())
        self.comb += [
            If(self.tpw_reset.ready_p,
                fsm.reset.eq(1),
                self.log.info("FSM reset")
            )
        ]
        fsm.act("RESET",
            If(self.tinit3.ready_p | (not init_delays),
                NextState("EXIT-PD")  # Td
            )
        )
        fsm.act("EXIT-PD",
            self.tinit5.trigger.eq(1),
            If(self.tinit5.ready_p | (not init_delays),
                NextState("MRW")  # Te
            )
        )
        fsm.act("MRW",
            cmds_enabled.eq(1),
            If(self.handle_cmd & ~cmd_handlers["MRW"] & ~cmd_handlers["MPC"],
                self.log.warn("Only MRW/MRR commands expected before ZQ calibration"),
                self.log.warn(" ".join("{}=%d".format(cmd) for cmd in cmd_handlers.keys()), *cmd_handlers.values()),
            ),
            If(cmd_handlers["MPC"],
                If(self.mpc_op != MPC.ZQC_START,
                    self.log.error("ZQC-START expected, got op=0b%07b", self.mpc_op)
                ).Else(
                    NextState("ZQC")  # Tf
                )
            ),
        )
        fsm.act("ZQC",
            self.tzqcal.trigger.eq(1),
            cmds_enabled.eq(1),
            If(self.handle_cmd,
                If(~(cmd_handlers["MPC"] & (self.mpc_op == MPC.ZQC_LATCH)),
                    self.log.error("Expected ZQC-LATCH")
                ).Else(
                    If(init_delays & ~self.tzqcal.ready,
                        self.log.warn("tZQCAL violated")
                    ),
                    NextState("NORMAL")  # Tg
                )
            ),
        )
        fsm.act("NORMAL",
            cmds_enabled.eq(1),
            self.tzqlat.trigger.eq(1),
            If(init_delays & self.handle_cmd & ~self.tzqlat.ready,
                self.log.warn("tZQLAT violated")
            ),
        )

        # Log state transitions
        fsm.finalize()
        prev_state = delayed(self, fsm.state)
        self.comb += If(prev_state != fsm.state,
            Case(prev_state, {
                state: Case(fsm.state, {
                    next_state: self.log.info(f"FSM: {state_name} -> {next_state_name}")
                    for next_state, next_state_name in fsm.decoding.items()
                })
                for state, state_name in fsm.decoding.items()
            })
        )

    def cmd_one_step(self, name, cond, comb, sync=None):
        matched = Signal()
        self.comb += If(self.handle_cmd & cond,
            self.log.debug(name),
            matched.eq(1),
            *comb
        )
        if sync is not None:
            self.sync += If(self.handle_cmd & cond,
                *sync
            )
        return matched

    def mrw_handler(self):
        ma  = Signal(8)
        op  = Signal(8)
        return self.cmd_one_step("MRW",
            cond = self.cs_n_low[:5] == 0b00101,
            comb = [
                self.log.info("MRW: MR[%d] = 0x%02x", ma, op),
                op.eq(self.cs_n_high[:8]),
                ma.eq(self.cs_n_low[5:13]),
                NextValue(self.mode_regs[ma], op),
            ],
        )

    def refresh_handler(self):
        bank = Signal(2)
        return self.cmd_one_step("REFRESH",
            cond = self.cs_n_low[:5] == 0b10011,
            comb = [
                If(~self.cs_n_low[10],
                    self.log.info("REF: all banks"),
                    If(reduce(or_, self.active_banks),
                        self.log.error("Not all banks precharged during REFRESH")
                    )
                ).Else(
                    self.log.info("REF: bank = %d", bank),
                    bank.eq(self.cs_n_low[6:8]),
                )
            ]
        )

    def activate_handler(self):
        bank = Signal(5)
        row  = Signal(18)
        return self.cmd_one_step("ACTIVATE",
            cond = self.cs_n_low[:2] == 0b00,
            comb = [
                bank.eq(self.cs_n_low[6:11]),
                row.eq(Cat(self.cs_n_low[2:6], self.cs_n_high)),
                self.log.info("ACT: bank=%d row=%d", bank, row),
                If(self.active_banks[bank],
                   self.log.error("ACT on already active bank: bank=%d row=%d", bank, row)
                ),
            ],
            sync = [
                self.active_banks[bank].eq(1),
                self.active_rows[bank].eq(row),
            ],
        )

    def precharge_handler(self):
        bank = Signal(2)
        return self.cmd_one_step("PRECHARGE",
            cond = self.cs_n_low[:5] == 0b01011,
            comb = [
                If(~self.cs_n_low[10],
                    self.log.info("PRE: all banks"),
                ).Else(
                    self.log.info("PRE: bank = %d", bank),
                    bank.eq(self.cs_n_low[6:8]),
                ),
            ],
            sync = [
                If(~self.cs_n_low[10],
                    *[self.active_banks[b].eq(0) for b in range(self.number_of_banks)]
                ).Else(
                    self.active_banks[bank].eq(0),
                    If(~self.active_banks[bank],
                        self.log.warn("PRE on inactive bank: bank=%d", bank)
                    ),
                ),
            ]
        )

    def mpc_handler(self):
        cases = {value: self.log.info(f"MPC: {name}") for name, value in MPC.__members__.items()}
        cases["default"] = self.log.error("Invalid MPC op=0b%08b", self.mpc_op)
        return self.cmd_one_step("MPC",
            cond = self.cs_n_low[:5] == 0b01111,
            comb = [
                self.mpc_op.eq(self.cs_n_low[5:13]),
                Case(self.mpc_op, cases)
            ],
        )

    def read_handler(self):
        bank = Signal(5)
        row  = Signal(18)
        col  = Signal(11)
        auto_precharge = Signal()

        return self.cmd_one_step("READ",
            cond = self.cs_n_low[:5] == 0b11101,
            comb = [
                If(~self.cs_n_low[5],
                   self.log.warn("Command places the DRAM into alternate burst mode; currently unsupported")
                   ),
                bank.eq(self.cs_n_low[6:11]),
                row.eq(self.active_rows[bank]),
                col.eq(Cat(Replicate(0, 2), self.cs_n_high[:9])),
                auto_precharge.eq(~self.cs_n_high[10]),
                self.log.info("READ: bank=%d row=%d, col=%d", bank, row, col),

                # sanity checks
                If(~self.active_banks[bank],
                    self.log.error("READ command on inactive bank: bank=%d row=%d col=%d", bank, row, col)
                ),
                If(auto_precharge,
                    self.log.info("AUTO-PRECHARGE: bank=%d row=%d", bank, row),
                    NextValue(self.active_banks[bank], 0),
                ),

                # pass the data to data simulator
                self.data_en.input.eq(1),
                self.data.sink.valid.eq(1),
                self.data.sink.bank.eq(bank),
                self.data.sink.row.eq(row),
                self.data.sink.col.eq(col),
                If(~self.data.sink.ready,
                    self.log.error("Simulator data FIFO overflow")
                ),
            ],
        )

    def write_handler(self):
        bank = Signal(5)
        row  = Signal(18)
        col  = Signal(11)
        auto_precharge = Signal()

        return self.cmd_one_step("WRITE",
            cond = self.cs_n_low[:5] == 0b01101,
            comb = [
                If(~self.cs_n_low[5],
                   self.log.warn("Command places the DRAM into alternate burst mode; currently unsupported")
                   ),
                bank.eq(self.cs_n_low[6:11]),
                row.eq(self.active_rows[bank]),
                col.eq(Cat(Replicate(0, 3), self.cs_n_high[1:9])),
                auto_precharge.eq(~self.cs_n_high[10]),
                self.log.info("WRITE: bank=%d row=%d, col=%d", bank, row, col),

                # sanity checks
                If(~self.active_banks[bank],
                    self.log.error("WRITE command on inactive bank: bank=%d row=%d col=%d", bank, row, col)
                ),
                If(auto_precharge,
                    self.log.info("AUTO-PRECHARGE: bank=%d row=%d", bank, row),
                    NextValue(self.active_banks[bank], 0),
                ),

                # pass the data to data simulator
                self.data_en.input.eq(1),
                self.data.sink.valid.eq(1),
                self.data.sink.we.eq(1),
                self.data.sink.masked.eq(~self.cs_n_high[11]),
                self.data.sink.bank.eq(bank),
                self.data.sink.row.eq(row),
                self.data.sink.col.eq(col),
                If(~self.data.sink.ready,
                    self.log.error("Simulator data FIFO overflow")
                ),
            ],
        )
# Data ---------------------------------------------------------------------------------------------

class DataSim(Module, AutoCSR):
    """Data simulator

    This module is responsible for handling read/write bursts. It's operation has to be triggered
    by the command simulator. Data is stored in an internal memory, no state is verified (row
    open/closed, etc.), this must be checked by command simulation.

    This module runs with DDR clocks (simulation clocks with double the frequency of `pads.clk_p`).
    """
    def __init__(self, pads, cmds_sim, *, cd_dq_wr, cd_dq_rd, cd_dqs_wr, cd_dqs_rd, cl, cwl, clk_freq, log_level):
        self.submodules.log = log = SimLogger(log_level=log_level, clk_freq=clk_freq)
        self.log.add_csrs()

        bl = 16

        dq_dqs_ratio = len(pads.dq) // len(pads.dqs_t)
        if dq_dqs_ratio == 8:
            module = modules.MT60B2G8HB48B
        elif dq_dqs_ratio == 4:
            module = modules.M329R8GA0BB0

        nbanks = module.nbanks
        # Per-bank memory
        nrows = module.nrows
        ncols = module.ncols
        mems = [Memory(len(pads.dq), depth=nrows * ncols) for _ in range(nbanks)]
        ports = [mem.get_port(write_capable=True, we_granularity=8, async_read=True) for mem in mems]
        self.specials += mems + ports
        ports = Array(ports)

        bank = Signal(5)
        row = Signal(18)
        col = Signal(11)

        dq_kwargs = dict(bank=bank, row=row, col=col, bl=bl, nrows=nrows, ncols=ncols,
            log_level=log_level, clk_freq=clk_freq)
        dqs_kwargs = dict(bl=bl, log_level=log_level, clk_freq=clk_freq)

        self.submodules.dq_wr = ClockDomainsRenamer(cd_dq_wr)(DQWrite(dq=pads.dq, dmi=pads.dm_n, ports=ports, **dq_kwargs))
        self.submodules.dq_rd = ClockDomainsRenamer(cd_dq_rd)(DQRead(dq=pads.dq_i, ports=ports, **dq_kwargs))
        self.submodules.dqs_wr = ClockDomainsRenamer(cd_dqs_wr)(DQSWrite(dqs=pads.dqs_t, **dqs_kwargs))
        self.submodules.dqs_rd = ClockDomainsRenamer(cd_dqs_rd)(DQSRead(dqs=pads.dqs_t_i,**dqs_kwargs))

        write = Signal()
        read = Signal()

        read_skew = 1  # shift the read data as in hardware it will be coming with a delay
        self.comb += [
            write.eq(cmds_sim.data_en.taps[cwl-1] & cmds_sim.data.source.valid & cmds_sim.data.source.we),
            read.eq(cmds_sim.data_en.taps[cl-1 + read_skew] & cmds_sim.data.source.valid & ~cmds_sim.data.source.we),
            cmds_sim.data.source.ready.eq(write | read),
            self.dq_wr.masked.eq(write & cmds_sim.data.source.masked),
            self.dq_wr.trigger.eq(write),
            self.dq_rd.trigger.eq(read),
            self.dqs_wr.trigger.eq(write),
            self.dqs_rd.trigger.eq(read),
        ]

        self.sync += [
            If(cmds_sim.data.source.ready,
                bank.eq(cmds_sim.data.source.bank),
                row.eq(cmds_sim.data.source.row),
                col.eq(cmds_sim.data.source.col),
            )
        ]


class DataBurst(Module, AutoCSR):
    def __init__(self, *, bl, log_level, clk_freq):
        self.submodules.log = log = SimLogger(log_level=log_level, clk_freq=clk_freq)
        self.log.add_csrs()

        self.bl = bl
        self.trigger = Signal()
        self.burst_counter = Signal(max=bl - 1)

    def add_fsm(self, ops, on_trigger=[]):
        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            NextValue(self.burst_counter, 0),
            If(self.trigger,
                *on_trigger,
                NextState("BURST")
            )
        )
        fsm.act("BURST",
            *ops,
            NextValue(self.burst_counter, self.burst_counter + 1),
            If(self.burst_counter == self.bl - 1,
                NextState("IDLE")
            ),
        )

class DQBurst(DataBurst):
    def __init__(self, *, nrows, ncols, row, col, **kwargs):
        super().__init__(**kwargs)
        self.addr = Signal(max=nrows * ncols)
        self.col_burst = Signal(11)
        self.comb += [
            self.col_burst.eq(col + self.burst_counter),
            self.addr.eq(row * ncols + self.col_burst),
        ]

class DQWrite(DQBurst):
    def __init__(self, *, dq, dmi, ports, nrows, ncols, bank, row, col, **kwargs):
        super().__init__(nrows=nrows, ncols=ncols, row=row, col=col, **kwargs)

        assert len(dmi) == len(ports[0].we), "port.we should have the same width as the DMI line"
        self.masked = Signal()
        masked = Signal()

        self.add_fsm(
            on_trigger = [
                NextValue(masked, self.masked),
            ],
            ops = [
                self.log.debug("WRITE[%d]: bank=%d, row=%d, col=%d, dq=0x%02x, dm=0x%01b",
                    self.burst_counter, bank, row, self.col_burst, dq, dmi, once=False),
                If(masked,
                    ports[bank].we.eq(~dmi),  # DMI high masks the beat
                ).Else(
                    ports[bank].we.eq(2**len(ports[bank].we) - 1),
                ),
                ports[bank].adr.eq(self.addr),
                ports[bank].dat_w.eq(dq),
            ]
        )

class DQRead(DQBurst):
    def __init__(self, *, dq, ports, nrows, ncols, bank, row, col, **kwargs):
        super().__init__(nrows=nrows, ncols=ncols, row=row, col=col, **kwargs)
        self.add_fsm([
            self.log.debug("READ[%d]: bank=%d, row=%d, col=%d, dq=0x%02x",
                self.burst_counter, bank, row, self.col_burst, dq, once=False),
            ports[bank].we.eq(0),
            ports[bank].adr.eq(self.addr),
            dq.eq(ports[bank].dat_r),
        ])

class DQSWrite(DataBurst):
    def __init__(self, *, dqs, **kwargs):
        super().__init__(**kwargs)
        dqs0 = Signal()
        self.add_fsm([
            dqs0.eq(dqs[0]),
            If(dqs[0] != self.burst_counter[0],
                self.log.warn("Wrong DQS=%d for cycle=%d", dqs0, self.burst_counter, once=False)
            ),
        ])

class DQSRead(DataBurst):
    def __init__(self, *, dqs, **kwargs):
        super().__init__(**kwargs)
        dqs0 = Signal()
        self.add_fsm([
            *[i.eq(self.burst_counter[0]) for i in dqs],
        ])
