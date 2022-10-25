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
from litedram.phy.lpddr4.commands import MPC


class LPDDR4Sim(Module, AutoCSR):
    """LPDDR4 DRAM simulator

    This module simulates an LPDDR4 DRAM chip to aid LPDDR4 PHY development/testing.
    It does not aim to simulate the internals of an LPDDR4 chip, rather it's behavior
    as seen by the PHY.

    The simulator monitors CS/CA pads listening for LPDDR4 commands and updates the module
    state depending on the command received. Any unexpected sequences are logged in simulation
    as errors/warnings. On read/write commands the data simulation module is triggered
    after CL/CWL and a data burst is handled, updating memory state.

    The simulator requires the following clock domains:
        sys8x:        8x the memory controller clock frequency, phase aligned.
        sys8x_90:     Phase shifted by 90 degrees vs sys8x.
        sys8x_ddr:    Phase aligned with sys8x, double the frequency.
        sys8x_90_ddr: Phase aligned with sys8x_90, double the frequency.

    Parameters
    ----------
    pads : LPDDR4SimulationPads
        DRAM pads
    sys_clk_freq : float
        System clock frequency
    cl : int
        LPDDR4 read latency (RL).
    cwl : int
        LPDDR4 write latency (WL).
    disable_delay : bool
        Disable checking of timings that rely on long CPU delays (mostly init sequence
        timings). This is useful when running LiteX BIOS with CONFIG_DISABLE_DELAYS on.
    log_level : str
        SimLogger initial logging level (formatted for parsing with `log_level_getter`).
    """
    def __init__(self, pads, *, sys_clk_freq, cl, cwl, disable_delay, log_level):
        log_level = log_level_getter(log_level)

        cd_cmd    = "sys8x_90"
        cd_dq_wr  = "sys8x_90_ddr"
        cd_dqs_wr = "sys8x_ddr"
        cd_dq_rd  = "sys8x_90_ddr"
        cd_dqs_rd = "sys8x_ddr"

        self.submodules.data_cdc = ClockDomainCrossing(
            [("we", 1), ("masked", 1), ("bank", 3), ("row", 17), ("col", 10)],
            cd_from=cd_cmd, cd_to=cd_dq_wr)

        cmd = CommandsSim(pads,
            data_cdc    = self.data_cdc,
            clk_freq    = 8*sys_clk_freq,
            log_level   = log_level("cmd"),
            init_delays = not disable_delay,
        )
        self.submodules.cmd = ClockDomainsRenamer(cd_cmd)(cmd)

        data = DataSim(pads, self.cmd,
            cd_dq_wr  = cd_dq_wr,
            cd_dqs_wr = cd_dqs_wr,
            cd_dq_rd  = cd_dq_rd,
            cd_dqs_rd = cd_dqs_rd,
            clk_freq  = 2*8*sys_clk_freq,
            cl        = cl,
            cwl       = cwl,
            log_level = log_level("data"),
        )
        self.submodules.data = ClockDomainsRenamer(cd_dq_wr)(data)

# Commands -----------------------------------------------------------------------------------------

class CommandsSim(Module, AutoCSR):
    """Command simulation

    This module interprets LPDDR4 commands found on the CS/CA pads. It keeps track of currently
    opened rows (per bank) and stores the values of Mode Registers. It also checks that the DRAM
    initialization sequence is performed according to specification. On any read/write commands
    signals indicating a burst are sent to the data simulator for handling.

    Command simulator should work in the clock domain of `pads.clk_p` (SDR).
    """
    def __init__(self, pads, data_cdc, *, clk_freq, log_level, init_delays=False):
        self.submodules.log = log = SimLogger(log_level=log_level, clk_freq=clk_freq)
        self.log.add_csrs()

        # Mode Registers storage
        self.mode_regs = Array([Signal(8) for _ in range(64)])
        # Active banks
        self.active_banks = Array([Signal() for _ in range(8)])
        self.active_rows = Array([Signal(17) for _ in range(8)])
        # Connection to DataSim
        self.data_en = TappedDelayLine(ntaps=20)
        self.data = data_cdc
        self.submodules += self.data, self.data_en

        # CS/CA shift registers
        cs = TappedDelayLine(pads.cs, ntaps=2)
        ca = TappedDelayLine(pads.ca, ntaps=2)
        self.submodules += cs, ca

        self.cs_low     = Signal(6)
        self.cs_high    = Signal(6)
        self.handle_cmd = Signal()
        self.mpc_op     = Signal(7)

        cmds_enabled = Signal()
        cmd_handlers = OrderedDict(
            MRW = self.mrw_handler(),
            REF = self.refresh_handler(),
            ACT = self.activate_handler(),
            PRE = self.precharge_handler(),
            CAS = self.cas_handler(),
            MPC = self.mpc_handler(),
        )
        self.comb += [
            If(cmds_enabled,
                If(Cat(cs.taps) == 0b10,
                    self.handle_cmd.eq(1),
                    self.cs_high.eq(ca.taps[1]),
                    self.cs_low.eq(ca.taps[0]),
                )
            ),
            If(self.handle_cmd & ~reduce(or_, cmd_handlers.values()),
                self.log.error("Unexpected command: cs_high=0b%06b cs_low=0b%06b", self.cs_high, self.cs_low)
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
            self.tinit2.trigger.eq(~pads.cke),
            self.tinit3.trigger.eq(pads.reset_n),
            self.tpw_reset.trigger.eq(~pads.reset_n),
            If(~delayed(self, pads.reset_n) & pads.reset_n,
                self.log.info("RESET released"),
                If(~self.tinit1.ready,
                    self.log.warn("tINIT1 violated: RESET deasserted too fast")
                ),
                If(~self.tinit2.ready,
                    self.log.warn("tINIT2 violated: CKE LOW too short before RESET being released")
                ),
            ),
            If(delayed(self, pads.reset_n) & ~pads.reset_n,
                self.log.info("RESET asserted"),
            ),
            If(delayed(self, pads.cke) & ~pads.cke,
                self.log.info("CKE falling edge"),
            ),
            If(~delayed(self, pads.cke) & pads.cke,
                self.log.info("CKE rising edge"),
                If(~self.tinit3.ready,
                    self.log.warn("tINIT3 violated: CKE set HIGH too fast after RESET being released")
                ),
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

    def cmd_two_step(self, name, cond1, body1, cond2, body2):
        state1, state2 = f"{name}-1", f"{name}-2"
        matched = Signal()

        fsm = FSM()
        fsm.act(state1,
            If(self.handle_cmd & cond1,
                self.log.debug(state1),
                matched.eq(1),
                *body1,
                NextState(state2)
            )
        )
        fsm.act(state2,
            If(self.handle_cmd,
                If(cond2,
                    self.log.debug(state2),
                    matched.eq(1),
                    *body2
                ).Else(
                    self.log.error(f"Waiting for {state2} but got unexpected cs_high=0b%06b cs_low=0b%06b", self.cs_high, self.cs_low)
                ),
                NextState(state1)  # always back to first
            )
        )
        self.submodules += fsm

        return matched

    def mrw_handler(self):
        ma  = Signal(6)
        op7 = Signal()
        op  = Signal(8)
        return self.cmd_two_step("MRW",
            cond1 = self.cs_high[:5] == 0b00110,
            body1 = [
                NextValue(ma, self.cs_low),
                NextValue(op7, self.cs_high[5]),
            ],
            cond2 = self.cs_high[:5] == 0b10110,
            body2 = [
                self.log.info("MRW: MR[%d] = 0x%02x", ma, op),
                op.eq(Cat(self.cs_low, self.cs_high[5], op7)),
                NextValue(self.mode_regs[ma], op),
            ]
        )

    def refresh_handler(self):
        return self.cmd_one_step("REFRESH",
            cond = self.cs_high[:5] == 0b01000,
            comb = [
                If(reduce(or_, self.active_banks),
                    self.log.error("Not all banks precharged during REFRESH")
                )
            ]
        )

    def activate_handler(self):
        bank = Signal(3)
        row1 = Signal(7)
        row2 = Signal(10)
        row  = Signal(17)
        return self.cmd_two_step("ACTIVATE",
            cond1 = self.cs_high[:2] == 0b01,
            body1 = [
                NextValue(bank, self.cs_low[:3]),
                NextValue(row1, Cat(self.cs_low[4:6], self.cs_high[2:6], self.cs_low[3])),
            ],
            cond2 = self.cs_high[:2] == 0b11,
            body2 = [
                self.log.info("ACT: bank=%d row=%d", bank, row),
                row2.eq(Cat(self.cs_low, self.cs_high[2:])),
                row.eq(Cat(row2, row1)),
                NextValue(self.active_banks[bank], 1),
                NextValue(self.active_rows[bank], row),
                If(self.active_banks[bank],
                    self.log.error("ACT on already active bank: bank=%d row=%d", bank, row)
                ),
            ]
        )

    def precharge_handler(self):
        bank = Signal(3)
        return self.cmd_one_step("PRECHARGE",
            cond = self.cs_high[:5] == 0b10000,
            comb = [
                If(self.cs_high[5],
                    self.log.info("PRE: all banks"),
                    bank.eq(2**len(bank) - 1),
                ).Else(
                    self.log.info("PRE: bank = %d", bank),
                    bank.eq(self.cs_low[:3]),
                ),
            ],
            sync = [
                If(self.cs_high[5],
                    *[self.active_banks[b].eq(0) for b in range(2**len(bank))]
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
        cases["default"] = self.log.error("Invalid MPC op=0b%07b", self.mpc_op)
        return self.cmd_one_step("MPC",
            cond = self.cs_high[:5] == 0b00000,
            comb = [
                self.mpc_op.eq(Cat(self.cs_low, self.cs_high[5])),
                If(self.cs_high[5] == 0,
                    self.log.info("MPC: NOOP")
                ).Else(
                    Case(self.mpc_op, cases)
                )
            ],
        )

    def cas_handler(self):
        cas1 = Signal(5)
        cas2 = 0b10010
        cas1_cmds = {
            "WRITE":        0b00100,
            "MASKED-WRITE": 0b01100,
            "READ":         0b00010,
        }

        bank           = Signal(3)
        row            = Signal(17)
        col9           = Signal()
        col            = Signal(10)
        burst_len      = Signal()
        auto_precharge = Signal()

        return self.cmd_two_step("CAS",
            cond1 = reduce(or_, [self.cs_high[:5] == cmd for cmd in cas1_cmds.values()]),
            body1 = [
                NextValue(cas1, self.cs_high[:5]),
                NextValue(bank, self.cs_low[:3]),
                NextValue(col9, self.cs_low[4]),
                NextValue(burst_len, self.cs_high[5]),
                NextValue(auto_precharge, self.cs_low[5]),
            ],
            cond2 = self.cs_high[:5] == cas2,
            body2 = [
                row.eq(self.active_rows[bank]),
                col.eq(Cat(Replicate(0, 2), self.cs_low, self.cs_high[5], col9)),
                # command type info
                Case(cas1, {
                    value: self.log.info(f"{name}: bank=%d row=%d col=%d", bank, row, col)
                    for name, value in cas1_cmds.items()
                }),
                # sanity checks
                If(~self.active_banks[bank],
                    self.log.error("CAS command on inactive bank: bank=%d row=%d col=%d", bank, row, col)
                ),
                If((cas1 != cas1_cmds["READ"]) & (col[:4] != 0),
                    self.log.error("WRITE commands must use C[3:2]=0 (must be aligned to full burst)")
                ),
                If(self.mode_regs[3][6] | self.mode_regs[3][7],
                    self.log.error("DBI currently not supported in the simulator")
                ),
                If((cas1 == cas1_cmds['MASKED-WRITE']) & (self.mode_regs[13][5] == 1),
                    self.log.error("MASKED-WRITE but Data Mask operation disabled in MR13[5]")
                ),
                If(auto_precharge,
                    self.log.info("AUTO-PRECHARGE: bank=%d row=%d", bank, row),
                    NextValue(self.active_banks[bank], 0),
                ),
                # pass the data to data simulator
                self.data_en.input.eq(1),
                self.data.sink.valid.eq(1),
                self.data.sink.we.eq(cas1 != cas1_cmds["READ"]),
                self.data.sink.masked.eq(cas1 == cas1_cmds["MASKED-WRITE"]),
                self.data.sink.bank.eq(bank),
                self.data.sink.row.eq(row),
                self.data.sink.col.eq(col),
                If(~self.data.sink.ready,
                    self.log.error("Simulator data FIFO overflow")
                )
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

        # Per-bank memory
        nrows, ncols = 32768, 1024
        mems = [Memory(len(pads.dq), depth=nrows * ncols) for _ in range(8)]
        ports = [mem.get_port(write_capable=True, we_granularity=8, async_read=True) for mem in mems]
        self.specials += mems + ports
        ports = Array(ports)

        bank = Signal(3)
        row = Signal(17)
        col = Signal(10)

        dq_kwargs = dict(bank=bank, row=row, col=col, bl=bl, nrows=nrows, ncols=ncols,
            log_level=log_level, clk_freq=clk_freq)
        dqs_kwargs = dict(bl=bl, log_level=log_level, clk_freq=clk_freq)

        self.submodules.dq_wr = ClockDomainsRenamer(cd_dq_wr)(DQWrite(dq=pads.dq, dmi=pads.dmi, ports=ports, **dq_kwargs))
        self.submodules.dq_rd = ClockDomainsRenamer(cd_dq_rd)(DQRead(dq=pads.dq_i, ports=ports, **dq_kwargs))
        self.submodules.dqs_wr = ClockDomainsRenamer(cd_dqs_wr)(DQSWrite(dqs=pads.dqs, **dqs_kwargs))
        self.submodules.dqs_rd = ClockDomainsRenamer(cd_dqs_rd)(DQSRead(dqs=pads.dqs_i,**dqs_kwargs))

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
        self.col_burst = Signal(10)
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
                self.log.debug("WRITE[%d]: bank=%d, row=%d, col=%d, dq=0x%04x dm=0x%02b",
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
            self.log.debug("READ[%d]: bank=%d, row=%d, col=%d, dq=0x%04x",
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
