#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import math
from operator import or_, and_, xor
from functools import reduce
from collections import defaultdict, OrderedDict

from migen import *

from litex.soc.interconnect.stream import AsyncFIFO
from litex.soc.interconnect.csr import AutoCSR

from litedram.common import TappedDelayLine
from litedram.phy.utils import delayed, edge
from litedram.phy.sim_utils import SimLogger, PulseTiming, log_level_getter, SimLoggerComb
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

    It uses sys4x_p_dimm and sys4x_n_dimm clock domains

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
    log_level : str
        SimLogger initial logging level (formatted for parsing with `log_level_getter`).
    """
    def __init__(self, pads, *, sys_clk_freq, cl, cwl, log_level, geom_settings, prefix=""):
        log_level = log_level_getter(log_level)

        bl_max    = 16 # We only support BL8 and BL16, there is no support for BL32
        cd_cmd    = "sys4x_p_dimm"
        cd_dq_wr  = "sys4x_p_dimm"
        cd_dqs_wr = "sys4x_p_dimm"
        cd_dq_rd  = "sys4x_p_dimm"
        cd_dqs_rd = "sys4x_p_dimm"

        self.submodules.data_cdc = ClockDomainsRenamer(
            {"write": cd_cmd,"read": cd_dq_wr}
        )(
            AsyncFIFO(
                [("we", 1),
                 ("masked", 1),
                 ("bank", geom_settings.bankbits),
                 ("row", geom_settings.rowbits),
                 ("col", geom_settings.colbits),
                 ("bl_width", bl_max.bit_length()),
                 ("mrr", 1),
                 ("mrr_data", 8),
                ],
                depth=64)
        )

        direct_dq_controll = Signal()
        dq_value = Signal()

        cmd = CommandsSim(pads,
            data_cdc          = self.data_cdc,
            direct_dq_control = direct_dq_controll,
            dq_value          = dq_value,
            clk_freq          = 4*sys_clk_freq,
            log_level         = log_level("cmd"),
            geom_settings     = geom_settings,
            bl_max            = bl_max,
            prefix            = prefix,
        )
        self.submodules.cmd = ClockDomainsRenamer(cd_cmd)(cmd)

        data = DataSim(pads, self.cmd,
            direct_dq_control = direct_dq_controll,
            dq_value          = dq_value,
            cd_dq_wr      = cd_dq_wr,
            cd_dqs_wr     = cd_dqs_wr,
            cd_dq_rd      = cd_dq_rd,
            cd_dqs_rd     = cd_dqs_rd,
            clk_freq      = 2*4*sys_clk_freq,
            cl            = cl,
            cwl           = cwl,
            log_level     = log_level("data"),
            geom_settings = geom_settings,
            bl_max        = bl_max,
            prefix        = prefix,
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
    def __init__(self, pads, data_cdc, direct_dq_control, dq_value, *,
                 clk_freq, log_level, geom_settings, bl_max, prefix):
        self.submodules.log = log = SimLogger(log_level=log_level, clk_freq=clk_freq, clk_freq_cd="sys4x")
        self.log.add_csrs()

        # Mode Registers storage
        registers = []
        for i in range(256):
            if i == 2:
                registers.append(Signal(8, reset=0))
            elif i == 8:
                registers.append(Signal(8, reset=8))
            elif i == 15:
                registers.append(Signal(8, reset=3))
            else:
                registers.append(Signal(8))

        self.mode_regs = Array(registers)
        # Active banks
        self.number_of_banks = 2 ** geom_settings.bankbits;
        self.active_banks = Array([Signal() for _ in range(self.number_of_banks)])
        self.active_rows = Array([Signal(geom_settings.rowbits) for _ in range(self.number_of_banks)])

        # Connection to DataSim
        self.data_en = TappedDelayLine(ntaps=26)
        self.data = data_cdc
        self.submodules += self.data, self.data_en

        # CS_n/CA shift registers
        cs_n = TappedDelayLine(getattr(pads, prefix+'cs_n'), ntaps=3)
        ca = TappedDelayLine(getattr(pads, prefix+'ca'), ntaps=3)
        self.submodules += cs_n, ca

        self.cs_n_low   = Signal(14)
        self.cs_n_high  = Signal(14)
        self.handle_1_tick_cmd  = Signal()
        self.handle_2_tick_cmd  = Signal()
        self.handled_1_tick_cmd = Signal()
        self.mr13_set   = Signal()
        self.mpc_op     = Signal(8)
        self.bl_max     = bl_max
        self.cs_training_start  = Signal()
        self.cs_training_end    = Signal()
        self.ca_training_start  = Signal()
        self.ca_training_in_prg = Signal()

        cmds_enabled = Signal()
        cmd_handlers = OrderedDict(
            MRW  = self.mrw_handler(prefix),
            REF  = self.refresh_handler(prefix),
            ACT  = self.activate_handler(prefix),
            PRE  = self.precharge_handler(prefix),
            RD   = self.read_handler(prefix),
            MPC  = self.mpc_handler(prefix),
            WR   = self.write_handler(prefix),
            NOP  = self.nop_handler(prefix),
        )

        self.comb += [
            If(cmds_enabled,
                If(~self.mode_regs[2][2],
                    If(Cat(cs_n.taps) == 0b011 | (Cat(cs_n.taps) == 0b001),
                        self.handle_2_tick_cmd.eq(1 & ~self.ca_training_in_prg),
                        self.cs_n_low.eq(ca.taps[2]),
                        self.cs_n_high.eq(ca.taps[0]),
                    ).Elif((Cat(cs_n.taps) == 0b010) | (Cat(cs_n.taps) == 0b000),
                        self.handle_1_tick_cmd.eq(1 & ~self.ca_training_in_prg),
                        self.cs_n_low.eq(ca.taps[2]),
                    ),
                ).Elif(Cat(cs_n.taps)[0:2] == 0b00,
                    self.handle_1_tick_cmd.eq(1 & ~self.ca_training_in_prg),
                    self.cs_n_low.eq(ca.taps[1]),
                ).Elif(Cat(cs_n.taps)[0:2] == 0b01,
                    self.handle_2_tick_cmd.eq(1),
                    self.cs_n_low.eq(ca.taps[1 & ~self.ca_training_in_prg]),
                    self.cs_n_high.eq(ca.taps[0]),
                )
            ),
            If(self.handle_2_tick_cmd & ~reduce(or_, cmd_handlers.values()),
                self.log.error(prefix+"Unexpected command: cs_n_low=0b%14b cs_n_high=0b%14b", self.cs_n_low, self.cs_n_high)
            ),
            If(self.handle_1_tick_cmd & ~reduce(or_, cmd_handlers.values()),
                self.log.error(prefix+"Unexpected command: cs_n_low=0b%14b", self.cs_n_low)
            ),
        ]
        self.sync += [If(self.handle_1_tick_cmd,
                        If(reduce(or_, cmd_handlers.values()),
                            self.handled_1_tick_cmd.eq(1)
                        ).Else(
                            self.handled_1_tick_cmd.eq(0)
                        ))]

        def ck(t, freq):
            return math.ceil(t * freq)

        # We check "Reset Initialization with Stable Power" sequence
        # Power-up Initialization Sequence is cloase to imposible to track in simulation
        self.submodules.tpw_reset = ClockDomainsRenamer("sys4x")(PulseTiming(ck(1e-6, clk_freq)))
        self.submodules.tinit2    = ClockDomainsRenamer("sys4x")(PulseTiming(ck(10e-9, clk_freq)))
        self.submodules.tinit3    = ClockDomainsRenamer("sys4x")(PulseTiming(ck(4e-3, clk_freq)))
        self.submodules.tinit4    = ClockDomainsRenamer("sys4x")(PulseTiming(ck(2e-6, clk_freq)))
        self.submodules.tcksrx    = ClockDomainsRenamer("sys4x")(PulseTiming(max(ck(3.5e-9, clk_freq), 8)))
        self.submodules.tinit5    = ClockDomainsRenamer("sys4x")(PulseTiming(3))
        self.submodules.xpr       = ClockDomainsRenamer("sys4x")(PulseTiming(ck(410e-9, clk_freq)))

        self.submodules.tzqcal = ClockDomainsRenamer("sys4x")(PulseTiming(ck(1e-6, clk_freq)))
        self.submodules.tzqlat = ClockDomainsRenamer("sys4x")(PulseTiming(max(8, ck(30e-9, clk_freq))))

        self.submodules.clk_check = ClockDomainsRenamer("sys4x_ddr")(TappedDelayLine(pads.ck_t))
        tcksrx_triggered = Signal(2)
        self.sync.sys4x_ddr += [If(~self.clk_check.output & pads.ck_t & ~tcksrx_triggered[1], tcksrx_triggered.eq(1))]
        self.sync += [If(tcksrx_triggered == 0b01, tcksrx_triggered.eq(2))]

        self.comb += [
            self.tpw_reset.trigger.eq(~pads.reset_n),
            self.tinit2.trigger.eq(~getattr(pads, prefix+'cs_n')),
            If(~delayed(self, pads.reset_n) & pads.reset_n,
                self.log.info(prefix+"RESET released"),
                If(~self.tinit2.ready,
                    self.log.error(prefix+"tINIT2 violated: RESET deasserted too fast")
                ),
            ),
            self.tcksrx.trigger.eq(tcksrx_triggered[0]),
            If(delayed(self, pads.reset_n) & ~pads.reset_n,
                self.log.info(prefix+"RESET asserted"),
            ),
        ]

        self.submodules.fsm = fsm = ResetInserter()(FSM())
        self.comb += [
            If(self.tpw_reset.ready_p,
                fsm.reset.eq(1),
                self.log.info(prefix+"FSM reset")
            )
        ]
        fsm.act("Reset",
            self.tinit3.trigger.eq(~pads.reset_n),
            If(pads.reset_n,
                NextState("Initialization"),
            )
        )
        fsm.act("Initialization",
            If(~delayed(self, getattr(pads, prefix+'cs_n')) & getattr(pads, prefix+'cs_n'),
                self.log.info(prefix+"CS released"),
                If(~self.tinit3.ready,
                    self.log.error(prefix+"tINIT3 violated: CS_n deasserted too fast"),
                ).Else(
                    self.tinit4.trigger.eq(1),
                    self.log.info(prefix+"Tinit4 triggered"),
                    NextState("CMOS_Registration")
                ),
            ).Elif(getattr(pads, prefix+'cs_n'),
                self.log.error(prefix+"tINIT3 violated: CS_n deasserted too fast"),
            ),
        )
        fsm.act("CMOS_Registration",
            If(delayed(self, getattr(pads, prefix+'cs_n')) & ~getattr(pads, prefix+'cs_n'),
                self.log.info(prefix+"CMOS registration ending"),
                If(~self.tcksrx.ready,
                    self.log.error(prefix+"tCKSRX violated: CS_n asserted too fast"),
                ).Elif(~self.tinit4.ready,
                    self.log.error(prefix+"tINIT4 violated: CS_n asserted too fast"),
                ).Else(
                    self.tinit5.trigger.eq(1),
                    NextState("EXIT-PD")
                ),
            ).Elif(~reduce(and_, getattr(pads, prefix+'ca')) & ~self.tinit4.ready,
                self.log.error(prefix+"CMD bus must be held high")
            ),
        )
        fsm.act("EXIT-PD",
            If(getattr(pads, prefix+'ca')[:5] != 0b11111 | getattr(pads, prefix+'cs_n'),
                self.log.error(prefix+"Incorrect exit sequence"),
            ),
            If(self.tinit5.ready_p,
                self.log.info(prefix+"Reset sequence finished"),
                NextState("MRW")  # Te
            )
        )
        fsm.act("MRW",
            cmds_enabled.eq(1),
            If(self.handle_2_tick_cmd & ~cmd_handlers["MRW"] & ~cmd_handlers["MPC"] & ~self.handled_1_tick_cmd,
                self.log.warn(prefix+"Only MPC/MRW/MRR commands expected before ZQ calibration"),
                self.log.warn(" ".join("{}=%d".format(cmd) for cmd in cmd_handlers.keys()), *cmd_handlers.values()),
                self.log.warn(prefix+"Unexpected command: cs_n_low=0b%14b cs_n_high=0b%14b", self.cs_n_low, self.cs_n_high)
            ),
            If(cmd_handlers["MPC"],
                self.log.info(prefix+"MPC handled op=0b%8b, mr13_set=%b, MPC.DLL_RST=%8b", self.mpc_op, self.mr13_set, int(MPC.DLL_RST)),
                If((self.mpc_op == MPC.DLL_RST) & self.mr13_set,
                    NextState("DLL_RESET")  # Tf
                ),
            ),
        )
        fsm.act("DLL_RESET",
            cmds_enabled.eq(1),
            If(cmd_handlers["MPC"],
                If((self.mpc_op != MPC.ZQC_START) & (self.mpc_op != MPC.DLL_RST),
                    self.log.error(prefix+"DLL-RESET OR ZQC-START expected, got op=0b%07b", self.mpc_op)
                ).Elif((self.mpc_op == MPC.ZQC_START),
                    NextState("ZQC")  # Tf
                )
            ),
        )
        fsm.act("ZQC",
            self.tzqcal.trigger.eq(1),
            cmds_enabled.eq(1),
            If(self.handle_2_tick_cmd | self.handle_1_tick_cmd,
                If(~(cmd_handlers["MPC"] &
                   ((self.mpc_op == MPC.ZQC_LATCH) | (self.mpc_op == MPC.ZQC_START))),
                    self.log.error(prefix+"Expected ZQC-LATCH")
                ).Elif((self.mpc_op == MPC.ZQC_LATCH),
                    If(~self.tzqcal.ready,
                        self.log.warn(prefix+"tZQCAL violated")
                    ),
                    NextState("NORMAL")  # Tg
                )
            ),
        )
        fsm.act("NORMAL",
            cmds_enabled.eq(1),
        )

        # Log state transitions
        fsm.finalize()
        prev_state = delayed(self, fsm.state)
        self.comb += If(prev_state != fsm.state,
            Case(prev_state, {
                state: Case(fsm.state, {
                    next_state: self.log.info(prefix+f"FSM: {state_name} -> {next_state_name}")
                    for next_state, next_state_name in fsm.decoding.items()
                } | {
                    "default": self.log.error(f"FSM: {state_name=} undefined next state")
                })
                for state, state_name in fsm.decoding.items()
            } | {
                "default": self.log.error(f"FSM: Undefined previous state")
            })
        )

        self.submodules.ca_training = ca_training = ResetInserter()(FSM())
        ca_direct_control      = Signal()
        ca_direct_value        = Signal()
        ca_training_counter    = Signal(2)
        ca_last_sampled_value  = Signal()
        ca_nop_sample_cnt      = Signal(4)
        ca_training.act("IDLE",
            ca_direct_control.eq(0),
            ca_direct_value.eq(0),
            If(self.ca_training_start & self.handle_2_tick_cmd,
                NextState("SAMPLE"),
                NextValue(ca_training_counter, 0),
                NextValue(ca_last_sampled_value, 0),
            ),
        )
        ca_training.act("SAMPLE",
            ca_direct_control.eq(1),
            ca_direct_value.eq(ca_last_sampled_value),
            self.ca_training_in_prg.eq(1),
            If(~getattr(pads, prefix+'cs_n'),
                If(ca_training_counter == 0,
                    NextValue(ca_training_counter, 1),
                    NextValue(ca_last_sampled_value, reduce(xor, getattr(pads, prefix+'ca'))),
                    If(getattr(pads, prefix+'ca') == 0x1f,
                        NextValue(ca_nop_sample_cnt, ca_nop_sample_cnt+1),
                    ),
                ).Elif((getattr(pads, prefix+'ca') != 0x1f) | (ca_nop_sample_cnt == 0),
                    self.log.warn("Recived multiple commands in single sample window that aren't continuous NOPs"),
                ).Else(
                    NextValue(ca_nop_sample_cnt, ca_nop_sample_cnt+1),
                )
            ).Else(
                NextValue(ca_nop_sample_cnt, 0),
                If(ca_nop_sample_cnt > 1,
                    NextState("IDLE"),
                )
            ),
            If(ca_nop_sample_cnt > 8,
                self.log.warn("Series of NOPs can only be at most 8 cycles long"),
            ),
            If(ca_training_counter > 0,
                NextValue(ca_training_counter, ca_training_counter+1),
            )
        )
        ca_training.finalize()

        self.submodules.cs_training = cs_training = ResetInserter()(FSM())
        cs_direct_control   = Signal()
        cs_direct_value     = Signal()
        cs_training_counter = Signal(2)
        last_sampled_value  = Signal()
        curent_sample       = Signal()
        cs_training.act("IDLE",
            cs_direct_control.eq(0),
            cs_direct_value.eq(1),
            If(self.cs_training_start,
                NextState("SAMPLE"),
                NextValue(cs_training_counter, 0),
                NextValue(last_sampled_value, 1),
                NextValue(curent_sample, 1),
            ),
        )
        cs_training.act("SAMPLE",
            cs_direct_control.eq(1),
            cs_direct_value.eq(last_sampled_value),
            If(cs_training_counter == 3,
                NextValue(last_sampled_value, ~(
                    curent_sample &
                    (cs_training_counter[0] == getattr(pads, prefix+'cs_n'))
                )),
                NextValue(curent_sample, 1),
            ).Else(
                NextValue(curent_sample, curent_sample & (cs_training_counter[0] == getattr(pads, prefix+'cs_n')))
            ),
            NextValue(cs_training_counter, cs_training_counter + 1),
            If(self.cs_training_end,
                NextState("IDLE"),
            ),
        )
        cs_training.finalize()
        self.comb += [
            dq_value.eq((cs_direct_control & cs_direct_value) | (ca_direct_control & ca_direct_value)),
            direct_dq_control.eq(cs_direct_control | ca_direct_control),
        ]


    def cmd_one_step(self, name, cond, comb, handle_cmd, sync=None):
        matched = Signal()
        self.comb += If(handle_cmd & cond,
            self.log.debug(name),
            matched.eq(1),
            *comb
        )
        if sync is not None:
            self.sync += If(handle_cmd & cond,
                *sync
            )
        return matched

    def mrw_handler(self, prefix):
        ma  = Signal(8)
        op  = Signal(8)
        return self.cmd_one_step("MRW",
            cond = self.cs_n_low[:5] == 0b00101,
            comb = [
                self.log.info(prefix+"MRW: MR[%d] = 0x%02x", ma, op),
                op.eq(self.cs_n_high[:8]),
                ma.eq(self.cs_n_low[5:13]),
            ],
            handle_cmd = self.handle_2_tick_cmd,
            sync = [
                If(ma == 2,
                    self.mode_regs[2].eq(Cat(op[0:2], self.mode_regs[2][2], op[3:])),
                ).Else(
                    self.mode_regs[ma].eq(op),
                ),
            ],
        )

    def nop_handler(self, prefix):
        ma  = Signal(8)
        op  = Signal(8)
        return self.cmd_one_step("NOP",
            cond = self.cs_n_low[:5] == 0b11111,
            comb = [
                self.log.debug(prefix+"NOP"),
            ],
            handle_cmd = self.handle_1_tick_cmd | self.handle_2_tick_cmd,
        )

    def refresh_handler(self, prefix):
        bank = Signal(2)
        return self.cmd_one_step("REFRESH",
            cond = self.cs_n_low[:5] == 0b10011,
            comb = [
                If(~self.cs_n_low[10],
                    self.log.info(prefix+"REF: all banks"),
                    If(reduce(or_, self.active_banks),
                        self.log.error(prefix+"Not all banks precharged during REFRESH")
                    )
                ).Else(
                    self.log.info(prefix+"REF: bank = %d", bank),
                    bank.eq(self.cs_n_low[6:8]),
                )
            ],
            handle_cmd = self.handle_2_tick_cmd,
        )

    def activate_handler(self, prefix):
        bank = Signal(5)
        row  = Signal(18)
        return self.cmd_one_step("ACTIVATE",
            cond = self.cs_n_low[:2] == 0b00,
            comb = [
                bank.eq(self.cs_n_low[6:11]),
                row.eq(Cat(self.cs_n_low[2:6], self.cs_n_high)),
                self.log.info(prefix+"ACT: bank=%d row=%d", bank, row),
                If(self.active_banks[bank],
                   self.log.error(prefix+"ACT on already active bank: bank=%d row=%d", bank, row)
                ),
            ],
            sync = [
                self.active_banks[bank].eq(1),
                self.active_rows[bank].eq(row),
            ],
            handle_cmd = self.handle_2_tick_cmd,
        )

    def precharge_handler(self, prefix):
        bank = Signal(2)
        return self.cmd_one_step("PRECHARGE",
            cond = self.cs_n_low[:5] == 0b01011,
            comb = [
                If(~self.cs_n_low[10],
                    self.log.info(prefix+"PRE: all banks"),
                ).Else(
                    self.log.info(prefix+"PRE: bank = %d", bank),
                    bank.eq(self.cs_n_low[6:8]),
                ),
            ],
            sync = [
                If(~self.cs_n_low[10],
                    *[self.active_banks[b].eq(0) for b in range(self.number_of_banks)]
                ).Else(
                    self.active_banks[bank].eq(0),
                    If(~self.active_banks[bank],
                        self.log.warn(prefix+"PRE on inactive bank: bank=%d", bank)
                    ),
                ),
            ],
            handle_cmd = self.handle_2_tick_cmd,
        )

    def mpc_handler(self, prefix):
        cases = {value: self.log.info(prefix+f"MPC: {name}") for name, value in MPC.__members__.items()}
        cases[0b00000000] = [self.log.info(prefix+"MPC: Exit CS"),  self.cs_training_end.eq(1)]
        cases[0b00000001] = [self.log.info(prefix+"MPC: Enter CS"), self.cs_training_start.eq(1)]
        cases[0b00000011] = [self.log.info(prefix+"MPC: Enter CA"), self.ca_training_start.eq(1)]
        cases[0b00001000] = [self.log.info(prefix+"MPC: 2N")]
        cases[0b00001001] = [self.log.info(prefix+"MPC: 1N")]
        base = 0b10000000
        for i  in range(16):
            cases[base+i] = [self.log.info(prefix+f"MPC: tCCD_L {i}")]
        cases["default"] = self.log.error(prefix+"Invalid MPC op=0b%08b", self.mpc_op)
        return self.cmd_one_step("MPC",
            cond = self.cs_n_low[:5] == 0b01111,
            comb = [
                self.mpc_op.eq(self.cs_n_low[5:13]),
                Case(self.mpc_op, cases)
            ],
            handle_cmd = self.handle_2_tick_cmd | self.handle_1_tick_cmd,
            sync = [
                If(self.mpc_op[1:] == 0b0000100,
                    self.mode_regs[2][2].eq(self.mpc_op[0]),
                ).Elif(self.mpc_op[4:] == 0b1000,
                    self.mr13_set.eq(1),
                    self.mode_regs[13][0:4].eq(self.mpc_op[0:4]),
                ),
            ],
        )

    def read_handler(self, prefix):
        bank     = Signal(5)
        row      = Signal(18)
        col      = Signal(11)
        bl_width = Signal(self.bl_max.bit_length())
        auto_precharge = Signal()

        return self.cmd_one_step("READ",
            cond = self.cs_n_low[:5] == 0b11101,
            comb = [
                If(~self.cs_n_low[5],
                   Case(self.mode_regs[0][:2], {
                        0:  bl_width.eq(8),
                        1:  bl_width.eq(8),
                        "default": [
                            self.log.error(prefix+"Model does not support burst length of 32, setting BL 16", bank, row, col),
                            bl_width.eq(16),
                        ],
                   }),
                ).Else(
                    bl_width.eq(16),
                ),
                bank.eq(self.cs_n_low[6:11]),
                row.eq(self.active_rows[bank]),
                col.eq(Cat(Replicate(0, 2), self.cs_n_high[:9])),
                auto_precharge.eq(~self.cs_n_high[10]),
                self.log.info(prefix+"READ: bank=%d row=%d, col=%d", bank, row, col),

                If(self.active_banks[bank],
                    [
                        # pass the data to data simulator
                        self.data_en.input.eq(1),
                        self.data.sink.valid.eq(1),
                        self.data.sink.we.eq(0),
                        self.data.sink.bank.eq(bank),
                        self.data.sink.row.eq(row),
                        self.data.sink.col.eq(col),
                        self.data.sink.bl_width.eq(bl_width),
                        If(~self.data.sink.ready,
                           self.log.error(prefix+"Simulator data FIFO overflow")
                        ),
                    ],
                ).Else(
                    self.log.error(prefix+"READ command on inactive bank: bank=%d row=%d col=%d", bank, row, col),
                ),
                If(auto_precharge,
                    self.log.info(prefix+"AUTO-PRECHARGE: bank=%d row=%d", bank, row),
                    NextValue(self.active_banks[bank], 0),
                ),
            ],
            handle_cmd = self.handle_2_tick_cmd,
        )

    def write_handler(self, prefix):
        bank     = Signal(5)
        row      = Signal(18)
        col      = Signal(11)
        bl_width = Signal(self.bl_max.bit_length())
        auto_precharge = Signal()

        return self.cmd_one_step("WRITE",
            cond = self.cs_n_low[:5] == 0b01101,
            comb = [
                If(~self.cs_n_low[5],
                   Case(self.mode_regs[0][:2], {
                        0:  bl_width.eq(8),
                        1:  bl_width.eq(8),
                        "default": [
                            self.log.error(prefix+"Model does not support burst length of 32, setting BL 16", bank, row, col),
                            bl_width.eq(16),
                        ],
                   }),
                ).Else(
                    bl_width.eq(16),
                ),
                bank.eq(self.cs_n_low[6:11]),
                row.eq(self.active_rows[bank]),
                col.eq(Cat(Replicate(0, 3), self.cs_n_high[1:9])),
                auto_precharge.eq(~self.cs_n_high[10]),
                self.log.info(prefix+"WRITE: bank=%d row=%d, col=%d", bank, row, col),

                If(self.active_banks[bank],
                    [
                        # pass the data to data simulator
                        self.data_en.input.eq(1),
                        self.data.sink.valid.eq(1),
                        self.data.sink.we.eq(1),
                        self.data.sink.masked.eq(~self.cs_n_high[11]),
                        self.data.sink.bank.eq(bank),
                        self.data.sink.row.eq(row),
                        self.data.sink.col.eq(col),
                        self.data.sink.bl_width.eq(bl_width),
                        If(~self.data.sink.ready,
                           self.log.error(prefix+"Simulator data FIFO overflow")
                        ),
                    ],
                ).Else(
                    self.log.error(prefix+"WRITE command on inactive bank: bank=%d row=%d col=%d", bank, row, col)
                ),
                If(auto_precharge,
                    self.log.info(prefix+"AUTO-PRECHARGE: bank=%d row=%d", bank, row),
                    NextValue(self.active_banks[bank], 0),
                ),
            ],
            handle_cmd = self.handle_2_tick_cmd,
        )
# Data ---------------------------------------------------------------------------------------------

# sys4x_n_dimm

class DataSim(Module, AutoCSR):
    """Data simulator

    This module is responsible for handling read/write bursts. It's operation has to be triggered
    by the command simulator. Data is stored in an internal memory, no state is verified (row
    open/closed, etc.), this must be checked by command simulation.

    This module runs with DDR clocks (simulation clocks with double the frequency of `pads.clk_p`).
    """
    def __init__(self, pads, cmds_sim, direct_dq_control, dq_value, *, cd_dq_wr, cd_dq_rd, cd_dqs_wr,
                 cd_dqs_rd, cl, cwl, clk_freq, log_level, geom_settings, bl_max, prefix):
        self.submodules.log   = log   = SimLogger(log_level=log_level, clk_freq=clk_freq)
        self.submodules.log_n = log_n = SimLogger(log_level=log_level, clk_freq=clk_freq, clk_freq_cd="sys4x_n_dimm")
        self.log.add_csrs()

        nbanks = 2 ** geom_settings.bankbits
        # Per-bank memory
        nrows = 2 ** geom_settings.rowbits
        ncols = 2 ** geom_settings.colbits
        mems = [Memory(len(getattr(pads, prefix+'dq')), depth=(nrows * ncols)) for _ in range(nbanks)]
        ports = [(mem.get_port(write_capable=True, we_granularity=8, async_read=True),
                  mem.get_port(write_capable=True, we_granularity=8, async_read=True, clock_domain="sys4x_n_dimm")) for mem in mems]
        self.specials += mems + ports
        ports = Array(Array([ports[i][0], ports[i][1]]) for i in range(len(ports)))

        bank = Signal(5)
        row = Signal(18)
        col = Signal(11)

        bl_width = Signal(bl_max.bit_length())

        dq_kwargs = dict(bank=bank, row=row, col=col, bl_max=bl_max, nrows=nrows, ncols=ncols,
            log_level=log_level, clk_freq=clk_freq, prefix=prefix)
        dqs_kwargs = dict(bl_max=bl_max, log_level=log_level, clk_freq=clk_freq, prefix=prefix)

        self.submodules.dq_wr = ClockDomainsRenamer(cd_dq_wr)(
            DQWrite(dq=getattr(pads, prefix+'dq'),
                    dmi=getattr(pads, prefix+'dm_n'),
                    bl_width=bl_width,
                    ports=ports,
                    negedge_domain="sys4x_n_dimm",
                    **dq_kwargs)
        )
        self.submodules.dq_rd = ClockDomainsRenamer(cd_dq_rd)(
            DQRead(dq=getattr(pads, prefix+'dq_i'),
                   bl_width=bl_width,
                   ports=ports,
                   negedge_domain="sys4x_n_dimm",
                   direct_dq_control=direct_dq_control,
                   dq_value=dq_value,
                   **dq_kwargs)
        ) # Acording to JEDEC DQS and DQ for reads are edge alligned
        self.submodules.dqs_wr = ClockDomainsRenamer(cd_dqs_wr)(
            DQSWrite(dqs=getattr(pads, prefix+'dqs_t'),
                     dqs_oe=getattr(pads, prefix+'dqs_t_oe'),
                     bl_width=bl_width,
                     negedge_domain="sys4x_n_dimm",
                     **dqs_kwargs)
        )
        self.submodules.dqs_rd = ClockDomainsRenamer(cd_dqs_rd)(
            DQSRead(dqs_t=getattr(pads, prefix+'dqs_t_i'),
                    dqs_c=getattr(pads, prefix+'dqs_c_i'),
                    bl_width=bl_width,
                    negedge_domain="sys4x_n_dimm",
                    **dqs_kwargs)
        )

        write        = Signal()
        masked       = Signal()
        wr_postamble         = Signal(3)
        wr_postamble_trigger = Signal()
        wr_postamble_width   = Signal(max=4)

        wr_preamble         = Signal(8)
        wr_preamble_trigger = Signal()
        wr_preamble_width   = Signal(max=9)

        # SimPHY does not support DQ/DQS traning yet, when in 2N mode reduce CL and CLW latency by 1
        n2_mode      = Signal()

        read = Signal()
        rd_postamble         = Signal(3)
        rd_postamble_trigger = Signal()
        rd_postamble_width   = Signal(max=4)

        rd_pre_sel          = Signal(3)
        rd_preamble         = Signal(8)
        rd_preamble_trigger = Signal()
        rd_preamble_width   = Signal(max=9)

        self.submodules.write_delay    = ClockDomainsRenamer(cd_dq_wr)(TappedDelayLine(write, ntaps=1))
        self.submodules.masked_delay   = ClockDomainsRenamer(cd_dq_wr)(TappedDelayLine(masked, ntaps=1))
        self.submodules.read_delay     = ClockDomainsRenamer(cd_dq_rd)(TappedDelayLine(read, ntaps=1))

        self.comb += [
            rd_pre_sel.eq(cmds_sim.mode_regs[8][:3]),
            Case(cmds_sim.mode_regs[8][:3], {
                0: rd_preamble_width.eq(2), # nCLK * 2 as we are working with 2*dram freq
                1: rd_preamble_width.eq(4), #
                2: rd_preamble_width.eq(4), #
                3: rd_preamble_width.eq(6), #
                4: rd_preamble_width.eq(8), #
                "default": self.log.error(prefix+"Read Preamble %d is reserved", rd_pre_sel),
            }),
            Case(cmds_sim.mode_regs[8][:3], {
                0: rd_preamble.eq(0b01),
                1: rd_preamble.eq(0b0100),
                2: rd_preamble.eq(0b0111),
                3: rd_preamble.eq(0b010000),
                4: rd_preamble.eq(0b01010000),
                "default": self.log.error(prefix+"Read Preamble %d is reserved", rd_pre_sel),
            }),
            Case(cmds_sim.mode_regs[8][3:5], {
                0: self.log.error(prefix+"Write Preamble 0b00 is reserved"),
                1: wr_preamble_width.eq(4), # nCLK * 2 as we are working with 2*dram freq
                2: wr_preamble_width.eq(6), #
                3: wr_preamble_width.eq(8), #
            }),
            Case(cmds_sim.mode_regs[8][3:5], {
                0: self.log.error(prefix+"Write Preamble 0b00 is reserved"),
                1: wr_preamble.eq(0b0100),
                2: wr_preamble.eq(0b010000),
                3: wr_preamble.eq(0b01010000),
            }),
            Case(cmds_sim.mode_regs[8][6], {
                0: rd_postamble_width.eq(0),
                1: rd_postamble_width.eq(2),
            }),
            Case(cmds_sim.mode_regs[8][6], {
                0: rd_postamble.eq(0),
                1: rd_postamble.eq(0b10),
            }),
            Case(cmds_sim.mode_regs[8][7], {
                0: wr_postamble_width.eq(0),
                1: wr_postamble_width.eq(2),
            }),
            Case(cmds_sim.mode_regs[8][7], {
                0: wr_postamble.eq(0),
                1: wr_postamble.eq(0b00),
            }),
            Case(cmds_sim.mode_regs[2][2], {
                0: n2_mode.eq(0b1),
                1: n2_mode.eq(0b0),
            }),
            write.eq(cmds_sim.data_en.taps[cwl - 3 - n2_mode] & cmds_sim.data.source.valid & cmds_sim.data.source.we),
            wr_preamble_trigger.eq(cmds_sim.data_en.taps[cwl - wr_preamble_width[1:] - 3 - n2_mode] &
                                   ~cmds_sim.data_en.taps[cwl - wr_preamble_width[1:] - 2 - n2_mode] &
                                   cmds_sim.data.source.valid &
                                   cmds_sim.data.source.we),

            read.eq(cmds_sim.data_en.taps[cl - 2 - n2_mode] & cmds_sim.data.source.valid & ~cmds_sim.data.source.we),
            rd_preamble_trigger.eq(cmds_sim.data_en.taps[cl - rd_preamble_width[1:] - 2 - n2_mode] &
                                   ~cmds_sim.data_en.taps[cl - rd_preamble_width[1:] - 1 - n2_mode] &
                                   cmds_sim.data.source.valid &
                                   ~cmds_sim.data.source.we),

            cmds_sim.data.source.ready.eq(write | read),
            masked.eq(write & cmds_sim.data.source.masked),
            self.dq_wr.masked.eq(self.masked_delay.output),
            self.dq_wr.trigger.eq(self.write_delay.output),
            self.dq_rd.trigger.eq(self.read_delay.output),

            self.dqs_wr.trigger.eq(self.write_delay.output),

            self.dqs_wr.preamble_trigger.eq(wr_preamble_trigger),
            self.dqs_wr.preamble_width.eq(wr_preamble_width),
            [self.dqs_wr.preamble[i].eq(wr_preamble[i]) for i in range(8)],

            self.dqs_wr.postamble_width.eq(wr_postamble_width),
            [self.dqs_wr.postamble[i].eq(wr_postamble[i]) for i in range(2)],

            self.dqs_rd.trigger.eq(read),
            self.dqs_rd.preamble_width.eq(rd_preamble_width),
            [self.dqs_rd.preamble[i].eq(rd_preamble[i]) for i in range(8)],

            self.dqs_rd.postamble_width.eq(rd_postamble_width),
            [self.dqs_rd.postamble[i].eq(rd_postamble[i]) for i in range(2)],
        ]

        self.comb += [
            If(cmds_sim.data.source.ready,
                If(cmds_sim.data.source.we,
                    self.log.info(prefix+"Write Sync: bl_width=%d", bl_width),
                ).Else(
                    self.log.info(prefix+"Read Sync: bl_width=%d", bl_width),
                ),
            ),
        ]

        self.sync += [
            If(cmds_sim.data.source.ready,
                bank.eq(cmds_sim.data.source.bank),
                row.eq(cmds_sim.data.source.row),
                col.eq(cmds_sim.data.source.col),
                bl_width.eq(cmds_sim.data.source.bl_width),
            ),
        ]

class DataBurst(Module, AutoCSR):
    def __init__(self, *, bl_width, bl_max, log_level, clk_freq, negedge_domain):
        self.submodules.log = log = SimLoggerComb(log_level=log_level, use_time=True)
        self.log.add_csrs()

        self.bl       = bl_width
        self.trigger  = Signal()
        self.burst_counter = Signal(max=bl_max - 1)
        self.burst_counter_n = Signal(max=bl_max - 1)
        self.cd_negedge = negedge_domain

    def add_fsm(self, ops, n_ops, on_trigger=[], n_on_trigger=[]):
        self.submodules.fsm = fsm = FSM()
        self.submodules.n_fsm = n_fsm = ClockDomainsRenamer(self.cd_negedge)(FSM())
        fsm.act("IDLE",
            NextValue(self.burst_counter, 0),
            If(self.trigger,
                *on_trigger,
                NextState("BURST")
            )
        )
        fsm.act("BURST",
            *ops,
            NextValue(self.burst_counter, self.burst_counter + 2),
            If(self.burst_counter == self.bl - 2 & ~self.trigger,
                NextState("IDLE")
            ).Elif( self.burst_counter == self.bl - 2, # Back to back burst
                *on_trigger,
                NextValue(self.burst_counter, 0),
            ),
        )
        n_fsm.act("IDLE",
            NextValue(self.burst_counter_n, 1),
            If(self.trigger,
                *n_on_trigger,
                NextState("BURST")
            )
        )
        n_fsm.act("BURST",
            *n_ops,
            NextValue(self.burst_counter_n, self.burst_counter_n + 2),
            If(self.burst_counter_n == self.bl - 1 & ~self.trigger,
                NextState("IDLE")
            ).Elif(self.burst_counter_n == self.bl - 1, # Back to back burst
                *n_on_trigger,
                NextValue(self.burst_counter, 1),
            ),
        )

class DQBurst(DataBurst):
    def __init__(self, *, nrows, ncols, row, col, **kwargs):
        super().__init__(**kwargs)
        self.addr_p = Signal(max=nrows * ncols)
        self.addr_n = Signal(max=nrows * ncols)
        self.col_burst = Signal(11)
        self.col_burst_n = Signal(11)
        self.comb += [
            self.col_burst.eq(col + self.burst_counter),
            self.col_burst_n.eq(col + self.burst_counter_n),
            self.addr_p.eq(row * ncols + self.col_burst),
            self.addr_n.eq(row * ncols + self.col_burst_n),
        ]

class DQWrite(DQBurst):
    def __init__(self, *, dq, dmi, ports, nrows, ncols, bank, row, col, prefix, **kwargs):
        super().__init__(nrows=nrows, ncols=ncols, row=row, col=col, **kwargs)

        assert len(dmi) == len(ports[0][0].we), "port.we should have the same width as the DMI line"
        assert len(dmi) == len(ports[0][1].we), "port.we should have the same width as the DMI line"
        self.masked = Signal()
        masked = Signal()

        self.add_fsm(
            on_trigger = [
                NextValue(masked, self.masked),
                If(self.masked,
                    ports[bank][0].we.eq(~dmi),  # DMI high masks the beat
                ).Else(
                    ports[bank][0].we.eq(2**len(ports[bank][0].we) - 1),
                ),
                ports[bank][0].adr.eq(self.addr_p),
                ports[bank][0].dat_w[:len(dq)].eq(dq),
                NextValue(self.burst_counter, 2),
                self.log.debug(prefix+"P_WRITE[%d]: bank=%d, row=%d, col=%d, dq=0x%02x, dm=0x%01b",
                    self.burst_counter, bank, row, self.col_burst, dq, dmi, once=False),
            ],
            ops = [
                self.log.debug(prefix+"P_WRITE[%d]: bank=%d, row=%d, col=%d, dq=0x%02x, dm=0x%01b",
                    self.burst_counter, bank, row, self.col_burst, dq, dmi, once=False),
                If(masked,
                    ports[bank][0].we.eq(~dmi),  # DMI high masks the beat
                ).Else(
                    ports[bank][0].we.eq(2**len(ports[bank][0].we) - 1),
                ),
                ports[bank][0].adr.eq(self.addr_p),
                ports[bank][0].dat_w.eq(dq),
            ],
            n_ops = [
                self.log.debug(prefix+"N_WRITE[%d]: bank=%d, row=%d, col=%d, dq=0x%02x, dm=0x%01b",
                    self.burst_counter_n, bank, row, self.col_burst, dq, dmi, once=False),
                If(masked,
                    ports[bank][1].we.eq(~dmi),  # DMI high masks the beat
                ).Else(
                    ports[bank][1].we.eq(2**len(ports[bank][0].we) - 1),
                ),
                ports[bank][1].adr.eq(self.addr_n),
                ports[bank][1].dat_w.eq(dq),
            ],
        )

class DQRead(DQBurst):
    def __init__(self, *, dq, ports, direct_dq_control, dq_value,
                 nrows, ncols, bank, row, col, prefix, **kwargs):
        super().__init__(nrows=nrows, ncols=ncols, row=row, col=col, **kwargs)
        self.add_fsm(
            on_trigger = [
                self.log.debug(prefix+"READ[%d]: bank=%d, row=%d, col=%d, dq=0x%02x",
                    self.burst_counter, bank, row, self.col_burst, dq, once=False),
                ports[bank][0].we.eq(0),
                ports[bank][0].adr.eq(self.addr_p),
                NextValue(self.burst_counter, 2),
                If(ClockSignal(),
                    dq.eq(ports[bank][0].dat_r),
                )
            ],
            ops = [
                self.log.debug(prefix+"READ[%d]: bank=%d, row=%d, col=%d, dq=0x%02x",
                    self.burst_counter, bank, row, self.col_burst, dq, once=False),
                ports[bank][0].we.eq(0),
                ports[bank][0].adr.eq(self.addr_p),
                If(ClockSignal(),
                    dq.eq(ports[bank][0].dat_r),
                )
            ],
            n_ops = [
                self.log.debug(prefix+"READ[%d]: bank=%d, row=%d, col=%d, dq=0x%02x",
                    self.burst_counter_n, bank, row, self.col_burst, dq, once=False),
                ports[bank][1].we.eq(0),
                ports[bank][1].adr.eq(self.addr_n),
                If(ClockSignal(self.cd_negedge),
                    dq.eq(ports[bank][1].dat_r),
                ),
            ],
        )
        self.comb += [
            If(direct_dq_control,
                dq.eq(Replicate(dq_value, len(dq))),
            ),
        ]

class DQSWrite(DataBurst):
    def __init__(self, *, dqs, dqs_oe, prefix, **kwargs):
        super().__init__(**kwargs)
        self.preamble_trigger   = Signal()
        self.preamble_width     = Signal(max=9)
        self.preamble           = Array(Signal() for _ in range(8))

        preamble_sampled        = Array(Signal() for _ in range(8))
        preamble_oe_sampled     = Array(Signal() for _ in range(8))
        preamble_good           = Signal(reset=1)

        preamble_               = [Signal(i) for i in range(2,9,2)]
        preamble_sampled_       = [Signal(i) for i in range(2,9,2)]
        preamble_oe_sampled_    = [Signal(i) for i in range(2,9,2)]

        p_pre_dqs0      = Signal(reset=1)
        n_pre_dqs0      = Signal(reset=0)
        p_pre_dqs0_oe   = Signal()
        n_pre_dqs0_oe   = Signal()
        p_pre_counter = Signal(max=8)
        n_pre_counter = Signal(max=8)

        self.submodules.p_pre = p_pre = FSM()
        self.submodules.n_pre = n_pre = ClockDomainsRenamer(self.cd_negedge)(FSM())
        p_pre.act("IDLE",
            NextValue(p_pre_counter, 0),
            If(self.preamble_trigger,
                NextState("PRECOUNT"),
            )
        )
        p_pre.act("PRECOUNT",
            p_pre_dqs0.eq(dqs[0]),
            p_pre_dqs0_oe.eq(dqs_oe[0]),
            self.log.info(prefix+"PREAMBLE_P: DQS preamble on bit=%d, dqs %d dqs_oe %d",
                          p_pre_counter, p_pre_dqs0, p_pre_dqs0_oe),
            NextValue(preamble_sampled[p_pre_counter], p_pre_dqs0),
            NextValue(preamble_oe_sampled[p_pre_counter], p_pre_dqs0_oe),
            NextValue(p_pre_counter, p_pre_counter + 2),
            If((p_pre_counter == self.preamble_width - 2),
                NextValue(p_pre_counter, 0),
                NextState("CHECK"),
            ),
        )
        pre_cases_= {}
        for i in range(2,9,2):
            signals = [(preamble_sampled[j]==self.preamble[j]) & preamble_oe_sampled[j] for j in range(i)]
            pre_cases_[i] = NextValue(preamble_good, reduce(and_, signals));

        p_pre.act("CHECK",
            Case(self.preamble_width,
                pre_cases_
            ),
            *[NextValue(preamble_sampled[i], 0) for i in range(8)],
            *[NextValue(preamble_oe_sampled[i], 0) for i in range(8)],
            NextState("IDLE"),
        )
        n_pre.act("IDLE",
            NextValue(n_pre_counter, 1),
            If(self.preamble_trigger,
                NextState("DELAY"),
            ),
        )
        n_pre.act("DELAY",
            NextState("PRECOUNT"),
        )
        n_pre.act("PRECOUNT",
            n_pre_dqs0.eq(dqs[0]),
            n_pre_dqs0_oe.eq(dqs_oe[0]),
            self.log.info(prefix+"PREAMBLE_N: DQS preamble on bit=%d, dqs %d dqs_oe %d",
                          n_pre_counter, n_pre_dqs0, n_pre_dqs0_oe),
            NextValue(preamble_sampled[n_pre_counter], n_pre_dqs0),
            NextValue(preamble_oe_sampled[n_pre_counter], n_pre_dqs0_oe),
            NextValue(n_pre_counter, n_pre_counter + 2),
            If((n_pre_counter == self.preamble_width - 1),
                NextValue(n_pre_counter, 0),
                NextState("IDLE"),
            ),
        )
        pre_error_cases_ = {}
        for i in range(2,9,2):
            pre_error_cases_[i] = [
                preamble_[i//2-1].eq(Cat([self.preamble[j] for j in range(i)])),
                preamble_sampled_[i//2-1].eq(Cat([preamble_sampled[j] for j in range(i)])),
                preamble_oe_sampled_[i//2-1].eq(Cat([preamble_oe_sampled[j] for j in range(i)])),
                self.log.error(prefix+"INCORRECT PREAMBLE: Expected preamble %b, got %b, DQS_oe %b",
                    preamble_[i//2-1], preamble_sampled_[i//2-1], preamble_oe_sampled_[i//2-1],
                ),
            ]
        self.sync += If(~preamble_good,
            Case(self.preamble_width,
                pre_error_cases_
            ),
            Finish()
        )

        p_dqs_sample    = Signal()
        n_dqs_sample    = Signal()
        p_dqs_sample_oe = Signal()
        n_dqs_sample_oe = Signal()
        n_dqs_skip      = Signal()
        n_dqs_check     = Signal()
        n_counter       = Signal.like(self.burst_counter_n)

        self.add_fsm(
            ops = [
                If((p_dqs_sample != 1) | ~p_dqs_sample_oe,
                    self.log.warn(prefix+"DQS_P:Wrong DQS=%d for cycle=%d", p_dqs_sample, self.burst_counter),
                ),
                NextValue(p_dqs_sample, dqs[0]),
                NextValue(p_dqs_sample_oe, dqs_oe[0]),
            ],
            n_ops = [
                n_counter.eq(self.burst_counter_n - 2),
                If(((n_dqs_sample != 0) | ~n_dqs_sample_oe) & ~n_dqs_skip,
                    self.log.warn(prefix+"DQS_N:Wrong DQS=%d for cycle=%d", n_dqs_sample, n_counter),
                ),
                NextValue(n_dqs_skip, 0),
                NextValue(n_dqs_check, 1),
                NextValue(n_dqs_sample, dqs[0]),
                NextValue(n_dqs_sample_oe, dqs_oe[0]),
            ],
            on_trigger = [
                NextValue(p_dqs_sample, dqs[0]),
                NextValue(p_dqs_sample_oe, dqs_oe[0]),
            ],
            n_on_trigger = [
                NextValue(n_dqs_skip, 1),
            ]
        )
        self.n_fsm.actions["IDLE"] += [
            If(n_dqs_check,
                n_counter.eq(self.burst_counter_n - 2),
                If((n_dqs_sample != 0) & ~n_dqs_skip,
                    self.log.warn(prefix+"DQS_N:Wrong DQS=%d for cycle=%d", n_dqs_sample, n_counter),
                ),
            ),
            NextValue(n_dqs_check, 0),
        ]

        self.postamble_width    = Signal(max=3)
        self.postamble          = Array(Signal() for _ in range(2))

        postamble_sampled       = Array(Signal() for _ in range(2))
        postamble_oe_sampled    = Array(Signal() for _ in range(2))
        postamble_good          = Signal(reset=1)

        postamble_              = [Signal(i) for i in range(2,3,2)]
        postamble_sampled_      = [Signal(i) for i in range(2,3,2)]
        postamble_oe_sampled_   = [Signal(i) for i in range(2,3,2)]

        p_post_dqs0    = Signal(reset=1)
        n_post_dqs0    = Signal(reset=0)
        p_post_dqs0_oe = Signal()
        n_post_dqs0_oe = Signal()

        p_post_counter = Signal(max=3)
        n_post_counter = Signal(max=3)
        self.submodules.p_post = p_post = FSM()
        self.submodules.n_post = n_post = ClockDomainsRenamer(self.cd_negedge)(FSM())
        p_post.act("IDLE",
            NextValue(p_post_counter, 0),
            If((self.burst_counter == self.bl - 2) & ~self.trigger & (self.postamble_width  != 0),
                p_post_dqs0.eq(dqs[0]),
                p_post_dqs0_oe.eq(dqs_oe[0]),
                self.log.info(prefix+"POSTAMBLE_P: DQS postamble on bit=%d, dqs %d dqs_oe %d",
                              p_post_counter, p_post_dqs0, p_post_dqs0_oe),
                NextValue(postamble_sampled[p_post_counter], p_post_dqs0),
                NextValue(postamble_oe_sampled[p_post_counter], p_post_dqs0_oe),
                NextValue(p_post_counter, p_post_counter + 2),
                NextState("POSTCOUNT"),
            )
        )
        p_post.act("POSTCOUNT",
            p_post_dqs0.eq(dqs[0]),
            p_post_dqs0_oe.eq(dqs_oe[0]),
            self.log.info(prefix+"POSTAMBLE_P: DQS postamble on bit=%d, dqs %d dqs_oe %d",
                          p_post_counter, p_post_dqs0, p_post_dqs0_oe),
            NextValue(postamble_sampled[p_post_counter], p_post_dqs0),
            NextValue(postamble_oe_sampled[p_post_counter], p_post_dqs0_oe),
            NextValue(p_post_counter, p_post_counter + 2),
            If((p_post_counter == self.postamble_width - 2),
                NextValue(p_post_counter, 0),
                NextState("CHECK"),
            ),
        )
        post_cases_= {}
        for i in range(0,3,2):
            signals = [(postamble_sampled[j]==self.postamble[j]) & postamble_oe_sampled[j] for j in range(i)]
            post_cases_[i] = NextValue(postamble_good, reduce(and_, signals, 1));
        p_post.act("CHECK",
            Case(self.postamble_width,
                post_cases_
            ),
            NextState("IDLE"),
        )
        n_post.act("IDLE",
            NextValue(n_post_counter, 1),
            If((self.burst_counter_n == self.bl - 1) & ~self.trigger & (self.postamble_width  != 0),
                NextState("POSTCOUNT"),
            )
        )
        n_post.act("POSTCOUNT",
            n_post_dqs0.eq(dqs[0]),
            n_post_dqs0_oe.eq(dqs_oe[0]),
            self.log.info(prefix+"POSTAMBLE_N: DQS postamble on bit=%d, dqs %d dqs_oe %d",
                          n_post_counter, n_post_dqs0, n_post_dqs0_oe),
            NextValue(postamble_sampled[n_post_counter], n_post_dqs0),
            NextValue(postamble_oe_sampled[n_post_counter], n_post_dqs0_oe),
            NextValue(n_post_counter, n_post_counter + 2),
            If((n_post_counter == self.postamble_width - 1),
                NextValue(n_post_counter, 0),
                NextState("IDLE"),
            ),
        )
        post_error_cases_ = {}
        for i in range(2,3,2):
            post_error_cases_[i] = [
                postamble_[i//2-1].eq(Cat([self.postamble[j] for j in range(i)])),
                postamble_sampled_[i//2-1].eq(Cat([postamble_sampled[j] for j in range(i)])),
                postamble_oe_sampled_[i//2-1].eq(Cat([postamble_oe_sampled[j] for j in range(i)])),
                self.log.error(prefix+"INCORRECT POSTAMBLE: Expected postamble %b, got %b, DQS_oe %b",
                    postamble_[i//2-1], postamble_sampled_[i//2-1], postamble_oe_sampled_[i//2-1],
                ),
            ]
        self.sync += If(~postamble_good,
            Case(self.postamble_width,
                post_error_cases_
            ),
            Finish()
        )

        self.fsm.finalize()
        self.n_fsm.finalize()
        p_pre.finalize()
        n_pre.finalize()

class DQSRead(DataBurst):
    def __init__(self, *, dqs_t, dqs_c, prefix, negedge_domain, **kwargs):
        super().__init__(**kwargs, negedge_domain=negedge_domain)
        dqs0 = Signal()

        self.preamble_trigger   = Signal()
        self.preamble_width     = Signal(max=8)
        self.preamble           = Array(Signal() for _ in range(8))

        self.postamble_width    = Signal(max=2)
        self.postamble          = Array(Signal() for _ in range(2))

        clk = ClockSignal()
        n_clk = ClockSignal(negedge_domain)

        self.add_fsm(
            ops = [],
            n_ops = [],
            on_trigger = [],
        )

        self.comb += [If(self.trigger|self.fsm.ongoing("BURST"),i.eq(clk)) for i in dqs_t] +\
                     [If(self.trigger|self.fsm.ongoing("BURST"),i.eq(~clk)) for i in dqs_c]
