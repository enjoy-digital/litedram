#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import math
from operator import or_
from functools import reduce
from collections import OrderedDict

from migen import *

from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import AutoCSR
#
from litedram.common import TappedDelayLine
from litedram.phy.utils import edge, delayed
from litedram.phy.sim_utils import SimLogger, Timing, PulseTiming, log_level_getter

from litedram.phy.lpddr5.basephy import get_frange


CMD_INFO_LAYOUT = [
    ("we", 1),
    ("masked", 1),
    ("burst32", 1),
    ("bank", 4),
    ("row", 18),
    ("col", 6),
]

gtkw_dbg = {}

class LPDDR5Sim(Module, AutoCSR):
    """LPDDR5 DRAM simulation
    """
    def __init__(self, pads, *, ck_freq, wck_ck_ratio, log_level, logger_kwargs, check_timings=True):
        log_level = log_level_getter(log_level)

        self.clock_domains.cd_ck = ClockDomain(reset_less=True)
        self.clock_domains.cd_ck_n = ClockDomain(reset_less=True)
        self.comb += [
            self.cd_ck.clk.eq(pads.ck),
            self.cd_ck_n.clk.eq(~pads.ck),
        ]

        self.clock_domains.cd_wck = ClockDomain(reset_less=True)
        self.clock_domains.cd_wck_n = ClockDomain(reset_less=True)
        self.comb += [
            self.cd_wck.clk.eq(pads.wck),
            self.cd_wck_n.clk.eq(~pads.wck),
        ]

        # CommandsSim and DataSim communicate via this endpoint
        cmd_info = stream.Endpoint(CMD_INFO_LAYOUT)
        gtkw_dbg["cmd_info"] = cmd_info

        cmd = CommandsSim(pads, cmd_info, ck_freq=ck_freq, check_timings=check_timings,
            logger_kwargs=logger_kwargs, log_level=log_level)
        self.submodules.cmd = ClockDomainsRenamer("ck")(cmd)

        data = DataSim(pads, cmd_info,
            latency_ready = cmd.data_timer.ready_p,
            mode_regs     = cmd.mode_regs,
            ck_freq       = ck_freq,
            wck_ck_ratio  = wck_ck_ratio,
            logger_kwargs = logger_kwargs,
            log_level     = log_level
        )
        self.submodules.data = ClockDomainsRenamer("wck")(data)


def nested_case(mapping, *, on_leaf, variables, default=None, **kwargs):
    """Generate a nested Case from a mapping

    Parameters
    ----------
    mapping : dict or list
        This is a nested tree structure that maps given variable value to either another mapping
        or a final value.
    on_leaf : Signal or callable(*values, **kwargs)
        If it is a Signal, each tree leaf will assign it a value depending on current variables.
        If it is a callable, then it is called on each tree leaf with all concrete variable values
        passed as `values` and it should return Migen expressions.
    variables : list(tuple(str, Signal))
        List of variables (name + signal) for subsequent tree levels. First variable will be used
        in the outermost Case as `mapping[var]`, 2nd for `mapping[_][var]` and so on...
    default : callable(name, var)
        Optional callback that can add operations added as "default" case for each level.
    kwargs : dict
        User keyword args, passed for each call to `on_leaf`.
    """
    # call the recursive version with initial argument values
    return _nested_case(mapping,
        on_leaf      = on_leaf,
        variables    = variables,
        default      = default,
        values       = [],
        orig_mapping = mapping,
        **kwargs)

def index_recurive(indexable, indices):
    for i in indices:
        indexable = indexable[i]
    return indexable

def _nested_case(mapping, *, on_leaf, variables, default, values, orig_mapping, **kwargs):
    debug = False

    if len(variables) == 0:
        if debug:
            print(f'{" "* 2*len(values)}on_leaf({values})')
        if callable(on_leaf):
            return on_leaf(*values, **kwargs)
        elif isinstance(on_leaf, Signal):
            return on_leaf.eq(index_recurive(orig_mapping, values))
        else:
            raise TypeError(on_leaf)
    else:
        name, var = variables[0]
        cases = {}
        if isinstance(mapping, dict):
            keys = list(mapping.keys())
        else:
            keys = list(range(len(mapping)))
        if debug:
            print(f'{" "* 2*len(values)}Case({name}, <{keys}>')
        for key in keys:
            cases[key] = _nested_case(mapping[key],
                on_leaf      = on_leaf,
                variables    = variables[1:],
                default      = default,
                values       = values + [key],
                orig_mapping = orig_mapping,
                **kwargs)
        if default is not None:
            cases["default"] = default(name, var)
        if debug:
            print(f'{" "* 2*len(values)})')
        return Case(var, cases)


class ModeRegisters(Module, AutoCSR):
    MR_RESET = {
        3: 0b00000110,
        4: 0b10000000,
        17: 0b00111000,
        18: 0b10000000,  # DRAM starts with WCK:CK=2:1
        28: 0b00000100,
        41: 0b01100000,
    }
    FIELD_DEFS = dict(
        # (address, (highest bit, lowest bit)), bits are inclusive
        wl = (1, (7, 4)),
        rl = (2, (3, 0)),
        set_ab = (3, (5, 5)),
        bank_org = (3, (4, 3)),
        ckr = (18, (7, 7)),
    )

    def __init__(self, *, log_level, logger_kwargs):
        self.submodules.log = SimLogger(log_level=log_level("mr"), **logger_kwargs)

        self.mr = Array([
            Signal(8, reset=self.MR_RESET.get(addr, 0), name=f"mr{addr}")
            for addr in range(64)
        ])

        self.fields = fields = {}
        for name, (addr, (bit_hi, bit_lo)) in self.FIELD_DEFS.items():
            fields[name] = Signal(bit_hi - bit_lo + 1)
            self.comb += fields[name].eq(self.mr[addr][bit_lo:bit_hi+1])

        self.ckr = Signal(max=4+1)
        self.comb += Case(fields["ckr"], {0: self.ckr.eq(4), 1: self.ckr.eq(2)})

        self.set_ab = Signal(2)
        self.comb += self.set_ab.eq(fields["set_ab"])

        value_warning = lambda name, var: self.log.warn(f"Unexpected value for '{name}': %d", var)

        self.wl = Signal(max=16+1)
        self.comb += nested_case(
            # DVFSC disabled; mapping[wck:ck][Set A/B][OP[7:4]]
            mapping = {
                2: [
                    [4, 4, 6, 8, 8, 10],
                    [4, 6, 8, 10, 14, 16],
                ],
                4: [
                    [2, 2, 3, 4, 4, 5, 6, 6, 7, 8, 9, 9],
                    [2, 3, 4, 5, 7, 8, 9, 11, 12, 14, 15, 16],
                ],
            },
            on_leaf = self.wl,
            default = value_warning,
            variables = [
                ("wck:ck ratio", self.ckr),
                ("set A/B", self.set_ab),
                ("wl field", fields["wl"]),
            ],
        )

        self.rl = Signal(max=20+1)
        self.comb += nested_case(
            # Link ECC off, DVFSC disabled; mapping[wck:ck][Set][OP[3:0]]
            mapping = {
                2: [
                    [6, 8, 10, 12, 16, 18],
                    [6, 8, 10, 14, 16, 20],
                    [6, 8, 12, 14, 18, 20],
                ],
                4: [
                    [3, 4, 5, 6, 8, 9, 10, 12, 13, 15, 16, 17],
                    [3, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17, 18],
                    [3, 4, 6, 7, 9, 10, 12, 14, 15, 17, 19, 20],
                ],
            },
            on_leaf = self.rl,
            default = value_warning,
            variables = [
                ("wck:ck ratio", self.ckr),
                ("set A/B", self.set_ab),
                ("rl field", fields["rl"]),
            ],
        )


class Sync(list):
    # Helper for combining comb and sync
    def __init__(self, arg):
        if not isinstance(arg, list):
            arg = [arg]
        super().__init__(arg)


class CommandsSim(Module, AutoCSR):
    def __init__(self, pads, cmd_info, *, ck_freq, check_timings, log_level, logger_kwargs):
        self.submodules.log = SimLogger(log_level=log_level("cmd"), **logger_kwargs)
        self.comb += self.log.info("Simulation start")

        self.cmd_info = cmd_info
        self.submodules.mode_regs = ModeRegisters(log_level=log_level, logger_kwargs=logger_kwargs)

        self.nbanks = 16
        self.active_banks = Array([Signal(name=f"bank{i}_active") for i in range(self.nbanks)])
        self.active_rows = Array([Signal(18, name=f"bank{i}_active_row") for i in range(self.nbanks)])

        # MPC operand
        self.mpc_op  = Signal(8)

        # ZQ calibration TODO: implement ZQC logic
        self.zqc_start = Signal()
        self.zqc_latch = Signal()

        # The captured command is delayed and the timer starts 1 cycle later:
        #       CK  --____----____----____----____----____--
        #       CS  __--------______________________________  (center-aligned to CK)
        #       CA  ____ppppNNNN____________________________  (center-aligned to CK DDR)
        # ca_p_pre  ______xxxxxxxx__________________________
        # ca_n_pre  __________xxxxxxxx______________________
        #   ca_p/n  ______________XXXXXXXX__________________  (phase-aligned to CK)
        #   timing  ______________________8-------7-------6-  (phase-aligned to CK)
        cs = Signal()
        cs_pre = Signal()
        ca_p_pre = Signal(7)
        ca_n_pre = Signal(7)
        self.ca_p = Signal(7)
        self.ca_n = Signal(7)
        self.sync.ck_n += ca_n_pre.eq(pads.ca)
        self.sync.ck += [
            cs_pre.eq(pads.cs),
            cs.eq(cs_pre),
            ca_p_pre.eq(pads.ca),
            self.ca_p.eq(ca_p_pre),
            self.ca_n.eq(ca_n_pre),
        ]

        self.handle_cmd = Signal()

        self.data_latency = Signal(max(len(self.mode_regs.wl), len(self.mode_regs.rl)))
        data_latency = Signal.like(self.data_latency)
        data_latency_reg = Signal.like(self.data_latency)
        self.submodules.data_timer = PulseTiming(data_latency)
        self.sync += If(self.data_timer.trigger,
            data_latency_reg.eq(self.data_latency)
        )
        self.comb += If(self.data_timer.trigger,
            data_latency.eq(self.data_latency),
        ).Else(
            data_latency.eq(data_latency_reg),
        ),

        cmds_enabled = Signal()
        allow_unhandled_cmd = Signal()
        cmd_handlers = OrderedDict(
            ACT = self.activate_handler(),
            PRE = self.precharge_handler(),
            REF = self.refresh_handler(),
            MRW = self.mrw_handler(),
            DATA = self.data_handler(),
            CAS = self.cas_handler(),
            MPC = self.mpc_handler(),
            # MRR
            # WFF/RFF?
            # RDC?
        )
        self.comb += [
            self.handle_cmd.eq(cmds_enabled & cs),
            If(self.handle_cmd & ~reduce(or_, cmd_handlers.values()),
                self.log.error("Unexpected command: CA_p=0b%07b CA_n=0b%07b", self.ca_p, self.ca_n)
            ),
            If(cs & ~cmds_enabled & ~allow_unhandled_cmd,
                self.log.warn("Received command when no commands should be sent: CA_p=0b%07b CA_n=0b%07b", self.ca_p, self.ca_n)
            ),
        ]

        check_timings = 1 if check_timings else 0
        ck = lambda t: math.ceil(t * ck_freq)
        ms, us, ns = 1e-3, 1e-6, 1e-9
        self.submodules.tinit0 = PulseTiming(ck(20*ms))  # (max) voltage-ramp at power-up; not applicable in the simulation
        self.submodules.tinit1 = PulseTiming(ck(200*us))  # (min) reset_n low time after voltage-ramp completion
        self.submodules.tinit2 = Timing(ck(10*ns))  # (min) CS low time before reset deassertion
        self.submodules.tinit3 = PulseTiming(ck(2*ms))  # (min) CS low time after reset deassertion
        self.submodules.tinit4 = PulseTiming(5)  # (min) stabilized CK before CS high; not really applicable in this simulation
        self.submodules.tinit5 = PulseTiming(ck(2*us))  # (min) idle time before first MRW/MRR cmmand
        self.submodules.tzqlat = PulseTiming(max(4, ck(30*ns)))  # (min) ZQCAL latch quiet time
        tpw_reset_ck = ck(100*ns) if check_timings else 4  # Avoids double reset during initialization at high frequecies
        self.submodules.tpw_reset = PulseTiming(tpw_reset_ck)  # (min) RESET_n low time for Reset initialization with stable power

        def with_progress(timing, string, *args, as_clocks=False):
            current, full = timing.progress()
            width = len(str(full)) if not isinstance(full, Signal) else len(str(2**len(full)))
            string += f" (%{width}d/%{width}d ck)"
            return (string, *args, current, full)

        self.comb += [
            self.tpw_reset.trigger.eq(~pads.reset_n),
            self.tinit2.valid.eq(~pads.cs),
            If(edge(self, pads.reset_n),
                If(~self.tinit2.ready & check_timings,
                    self.log.warn(*with_progress(self.tinit2, "tINIT2 violated: CS LOW for too short before deasserting RESET"))
                ),
                If(~self.tpw_reset.ready & check_timings,
                    self.log.warn(*with_progress(self.tpw_reset, "tPW_RESET violated: RESET_n held low for too short"))
                ),
            ),
            If(edge(self, pads.reset_n),
                self.log.info("RESET released"),
            ).Elif(edge(self, ~pads.reset_n),
                self.log.info("RESET asserted"),
            ),
        ]

        # We use an FSM that will be automatically reset to the RESET state when reset pad is asserted.
        # NOTE: for simulation purpose we assume that CK is always running because CommandsSim is clocked
        # from it, or else the states up to Tc would make no sense because the timings would not be counted
        class ResetFSM(FSM):
            def __init__(self, tpw_reset):
                self.tpw_reset = tpw_reset
                super().__init__(reset_state="RESET")

            def act(self, state, *statements):
                if state != "RESET":
                    statements = [
                        If(edge(self, self.tpw_reset.ready),
                            NextState("RESET"),
                        ).Else(*statements)
                    ]
                super().act(state, statements)

        self.submodules.fsm = fsm = ResetFSM(self.tpw_reset)
        fsm.act("RESET",
            self.tinit1.trigger.eq(1),
            If(edge(self, pads.reset_n),
                If(~self.tinit1.ready & check_timings,
                    self.log.warn(*with_progress(self.tinit1, "tINIT1 violated: RESET deasserted too fast"))
                ),
                NextState("WAIT-NOP")  # Tc
            ),
        )
        fsm.act("WAIT-NOP",
            self.tinit3.trigger.eq(1),
            If(cs & ~self.tinit3.ready & check_timings,
                self.log.warn(*with_progress(self.tinit3, "tINIT3 violated: CS high too fast after RESET deassertion"))
            ),
            self.tinit4.trigger.eq(1),
            If(cs & ~self.tinit4.ready & check_timings,
                self.log.warn(*with_progress(self.tinit4, "tINIT4 violated: CS high too fast after stable CK"))
            ),
            If(cs,  # NOP; TODO: DRAM probably only checks CS, then we'd better not check CA
                allow_unhandled_cmd.eq(1),
                self.tinit5.trigger.eq(1),
                If(~self.tinit4.ready & check_timings,
                    self.log.warn(*with_progress(self.tinit4, "tINIT4 violated: CS HIGH too fast while waiting for initial NOP"))
                ),
                If((self.ca_p != 0) | (self.ca_n != 0),
                    self.log.warn("Waiting for NOP but got CA_p=0b%07b CA_n=0b%07b", self.ca_p, self.ca_n)
                ),
                NextState("NO-CMDS"),  # Te
            )
        )
        fsm.act("NO-CMDS",
            self.tinit5.trigger.eq(1),
            If(cs & ~self.tinit5.ready & check_timings,
                self.log.warn(*with_progress(self.tinit5, "tINIT5 violated: command issued too fast after initial NOP"))
            ),
            If(self.tinit5.ready | ~check_timings,
                NextState("MODE-REGS")  # Tf
            )
        )
        fsm.act("MODE-REGS",
            cmds_enabled.eq(1),
            # If(self.handle_cmd & ~cmd_handlers["MRW"] & ~cmd_handlers["MRR"] & ~cmd_handlers["MPC"],  # TODO: MRR
            If(self.handle_cmd & ~cmd_handlers["MRW"] & ~cmd_handlers["MPC"],
                self.log.warn("Only MRW/MRR commands expected before ZQ Latch ..."),
                self.log.warn("... " + " ".join("{}=%d".format(cmd) for cmd in cmd_handlers.keys()), *cmd_handlers.values()),
            ),
            If(cmd_handlers["MPC"],
                If(~self.zqc_latch,
                    self.log.error("ZQC-LATCH expected, got MPC with op=0b%07b", self.mpc_op)
                ).Else(
                    NextState("ZQC-LATCH")  # Tg
                )
            ),
        )
        fsm.act("ZQC-LATCH",
            cmds_enabled.eq(1),
            self.tzqlat.trigger.eq(1),
            If(~self.tzqlat.ready & self.handle_cmd & check_timings,
                self.log.error(*with_progress(self.tzqlat, "tZQCAL violated: new command issued too fast: CA_p=0b%07b CA_n=0b%07b", self.ca_p, self.ca_n))
            ),
            If(self.tzqlat.ready | ~check_timings,
                NextState("NORMAL"),  # Th
            )
        )
        fsm.act("NORMAL",
            cmds_enabled.eq(1)
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

    def activate_handler(self):
        bank = Signal(max=self.nbanks)
        row1 = Signal(4)
        row2 = Signal(3)
        row3 = Signal(4)
        row4 = Signal(7)
        row = Signal(18)
        return self.cmd_two_step("ACTIVATE",
            cond1 = self.ca_p[:3] == 0b111,
            body1 = [
                NextValue(row1, self.ca_p[3:]),
                NextValue(row2, self.ca_n[4:]),
                NextValue(bank, self.ca_n[:4]),
            ],
            cond2 = self.ca_p[:3] == 0b011,
            body2 = [
                self.log.info("ACT: bank=%d row=%d", bank, row),
                row3.eq(self.ca_p[3:]),
                row4.eq(self.ca_n),
                row.eq(Cat(row4, row3, row2, row1)),
                NextValue(self.active_banks[bank], 1),
                NextValue(self.active_rows[bank], row),
                If(self.active_banks[bank],
                    self.log.error("ACT on already active bank: bank=%d row=%d", bank, row)
                ),
            ],
            wait_time = 8,  # tAAD
        )

    def precharge_handler(self):
        bank = Signal(max=self.nbanks)
        all_banks = Signal()
        return self.cmd_one_step("PRECHARGE",
            cond = self.ca_p[:7] == 0b1111000,
            body = [
                all_banks.eq(self.ca_n[6]),
                If(all_banks,
                    self.log.debug("PRE: all banks"),
                    bank.eq(2**len(bank) - 1),
                ).Else(
                    self.log.debug("PRE: bank = %d", bank),
                    bank.eq(self.ca_n[:4]),
                ),
                Sync(
                    If(all_banks,
                        *[self.active_banks[b].eq(0) for b in range(2**len(bank))]
                    ).Else(
                        self.active_banks[bank].eq(0),
                        If(~self.active_banks[bank],
                            self.log.warn("PRE on inactive bank: bank=%d", bank)
                        ),
                    ),
                )
            ],
        )

    def refresh_handler(self):
        # TODO: refresh tracking
        bank = Signal(max=self.nbanks)
        all_banks = Signal()
        return self.cmd_one_step("REFRESH",
            cond = self.ca_p[:7] == 0b0111000,
            body = [
                all_banks.eq(self.ca_n[6]),
                If(reduce(or_, self.active_banks),
                    self.log.error("Not all banks precharged during REFRESH")
                )
            ]
        )

    def mrw_handler(self):
        ma  = Signal(7)
        op  = Signal(8)
        return self.cmd_two_step("MRW",
            cond1 = self.ca_p[:7] == 0b1011000,
            body1 = [
                NextValue(ma, self.ca_n),
            ],
            cond2 = self.ca_p[:6] == 0b001000,
            body2 = [
                op.eq(Cat(self.ca_n, self.ca_p[6])),
                self.log.info("MRW: MR[%d] = 0x%02x", ma, op),
                NextValue(self.mode_regs.mr[ma], op),
            ]
        )

    def mpc_handler(self):
        op  = Signal(8)
        return self.cmd_one_step("MRW",
            cond = self.ca_p[:6] == 0b110000,
            body = [
                op.eq(Cat(self.ca_n, self.ca_p[6])),
                self.mpc_op.eq(op),
                self.zqc_start.eq(op == 0b10000101),
                self.zqc_latch.eq(op == 0b10000110),
                If(~(self.zqc_start | self.zqc_latch),
                    self.log.warn("Unsupported MPC command: op=0b%08b", op),
                ),
            ],
        )

    def cas_handler(self):
        ws_wr = Signal()
        ws_rd = Signal()
        ws_fs = Signal()
        dc    = Signal(4)
        wrx   = Signal()
        wxsa  = Signal()
        wxsb  = Signal()
        return self.cmd_one_step("CAS",
            cond = self.ca_p[:4] == 0b1100,
            body = [
                # TODO: implement WCK sync
                ws_wr.eq(self.ca_p[4]),
                ws_rd.eq(self.ca_p[5]),
                ws_fs.eq(self.ca_p[6]),
                dc.eq(self.ca_n[:4]),
                wrx.eq(self.ca_n[4]),
                wxsa.eq(self.ca_n[5]),
                wxsb.eq(self.ca_n[6]),
                If(sum([ws_wr, ws_rd, ws_fs]) > 1,
                    self.log.error("More than one WCK Sync bit in CAS command")
                ),
                If(reduce(or_, [dc, wrx, wxsa, wxsb]),
                    self.log.warn("Unsupported CAS function requested")
                ),
            ]
        )

    def data_handler(self):
        data_cmds = {
            "MASKED-WRITE": self.ca_p[:3] == 0b010,
            "WRITE":        self.ca_p[:3] == 0b110,
            "WRITE32":      self.ca_p[:4] == 0b0100,
            "READ":         self.ca_p[:3] == 0b001,
            "READ32":       self.ca_p[:3] == 0b101,
        }

        bank           = Signal(max=self.nbanks)
        row            = Signal(18)
        col            = Signal(6)
        auto_precharge = Signal()

        return self.cmd_one_step("DATA",
            cond = reduce(or_, data_cmds.values()),
            body = [
                bank.eq(self.ca_n[:4]),
                row.eq(self.active_rows[bank]),
                col.eq(Cat(self.ca_p[3], self.ca_n[4:6], self.ca_p[4:7])),
                auto_precharge.eq(self.ca_n[6]),
                # push to DataSim
                self.cmd_info.we.eq(data_cmds["MASKED-WRITE"] | data_cmds["WRITE"] | data_cmds["WRITE32"]),
                self.cmd_info.masked.eq(data_cmds["MASKED-WRITE"]),
                self.cmd_info.burst32.eq(data_cmds["WRITE32"] | data_cmds["READ32"]),
                self.cmd_info.bank.eq(bank),
                self.cmd_info.row.eq(row),
                self.cmd_info.col.eq(col),
                self.cmd_info.valid.eq(1),
                # data latency
                If(self.cmd_info.we,
                    self.data_latency.eq(self.mode_regs.wl - 1),
                    If(self.mode_regs.wl < 1,
                        self.log.error("WL < 2 is not supported")
                    ),
                ).Else(
                    # FIXME: Currently we need to subtract 1 cycle here and delay additionally in BurstHalf.
                    # We need to check if that's a limitation of PHY not being able to level DRAM only in simulation
                    # or if there's a need to increase read_latency by 1 cycle (or increase bitslip cycles).
                    self.data_latency.eq(self.mode_regs.rl - 2),
                    If(self.mode_regs.rl < 2,
                        self.log.error("RL < 2 is not supported")
                    ),
                ),
                self.data_timer.trigger.eq(1),
                # command info
                *[If(cond, self.log.info(f"{name}: bank=%d row=%d col=%d", bank, row, col))
                    for name, cond in data_cmds.items()],
                # auto precharge
                If(auto_precharge,
                    self.log.info("AUTO-PRECHARGE: bank=%d row=%d", bank, row),
                ),
                Sync(If(auto_precharge,
                    self.active_banks[bank].eq(0),
                )),
                # sanity checks
                If(~self.active_banks[bank],
                    self.log.error("CAS command on inactive bank: bank=%d row=%d col=%d", bank, row, col)
                ),
                If(self.cmd_info.masked & ~((self.mode_regs.fields["bank_org"] == 0b00) | (self.mode_regs.fields["bank_org"] == 0b10)),
                    self.log.error("READ32/WRITE32 are valid in BG/16B mode only")
                ),
            ],
        )

    def cmd_one_step(self, name, cond, body):
        matched = Signal()
        comb = list(filter(lambda i: not isinstance(i, Sync), body))
        sync = list(filter(lambda i: isinstance(i, Sync), body))
        self.comb += If(self.handle_cmd & cond,
            self.log.debug(name),
            matched.eq(1),
            *comb
        )
        if len(sync) > 0:
            self.sync += If(self.handle_cmd & cond,
                *sync
            )
        return matched

    def cmd_two_step(self, name, cond1, body1, cond2, body2, wait_time=None):
        state1, state2 = f"{name}-1", f"{name}-2"
        matched = Signal()

        timeout = 0
        trigger_timer = []
        if wait_time is not None:
            next_cmd_timer = PulseTiming(wait_time)
            self.submodules += next_cmd_timer
            timeout = next_cmd_timer.ready
            trigger_timer = [
                next_cmd_timer.trigger.eq(1),
            ]

        fsm = FSM()
        fsm.act(state1,
            If(self.handle_cmd & cond1,
                self.log.debug(state1),
                matched.eq(1),
                *body1,
                *trigger_timer,
                NextState(state2)
            )
        )
        fsm.act(state2,
            If(timeout,
                self.log.warn(f"Timeout while waiting for {state2}"),
                NextState(state1)
            ).Elif(self.handle_cmd,
                If(cond2,
                    self.log.debug(state2),
                    matched.eq(1),
                    *body2
                ).Else(
                    self.log.error(f"Waiting for {state2} but got unexpected CA_p=0b%07b CA_n=0b%07b", self.ca_p, self.ca_n)
                ),
                NextState(state1)  # always back to first
            )
        )
        self.submodules += fsm

        return matched


class DataSim(Module, AutoCSR):
    def __init__(self, pads, cmd_info, latency_ready, mode_regs, ck_freq, wck_ck_ratio, *, log_level, logger_kwargs, nrows=32768, ncols=1024, nbanks=16):
        self.submodules.log = SimLogger(log_level=log_level("data"), **logger_kwargs)

        # CommandsSim produces the data required for handling a data command via cmd_info endpoint.
        # Using stream.ClockDomainCrossing introduces too much latency, so we do a simplistic CDC
        # and store the information in a FIFO, so that it is possible to pipeline data commands.
        self.submodules.cmd_buf = stream.PipeValid(CMD_INFO_LAYOUT)
        gtkw_dbg["cmd_buf"] = self.cmd_buf

        # The CommandsSim data handling generated command is clocked under the system clock domain.
        # Instead, the DataSim is clocked in the wck clock domain.
        # Given that, with a dynamic wck regime, wck needs to get through a preamble phase where it
        # is not active for a certain amount of clock cycles, the command buffer pipeline may not
        # be able to see changes in the data commands generated by CommandSim.
        #
        # The following logic verifies whether a delay needs to be added and adds it accordingly to
        # the data command, so that the pipe stream can intercept the various commands from the ck
        # domain correctly.
        twck = 1 / (ck_freq * wck_ck_ratio)
        frange = get_frange(twck, wck_ck_ratio).for_set(wl_set="A", rl_set=0)
        taps = max(1, max(frange.t_wckenl_wr, frange.t_wckenl_rd) + frange.t_wckpre_static) - 1

        def delay_cmd_info(signals):
            for signal in signals:
                tapped_delay = ClockDomainsRenamer("ck")(TappedDelayLine(getattr(cmd_info, signal), ntaps=taps))
                setattr(self.submodules, f"{signal}_tap", tapped_delay)

                self.comb += [
                    getattr(self.cmd_buf.sink, signal).eq(reduce(or_, getattr(self, f"{signal}_tap").taps[0:taps])),
                ]

        if taps > 0:
            delay_cmd_info([tup[0] for tup in CMD_INFO_LAYOUT] + ["valid", "ready", "first", "last"])

        else:
            self.comb += [
                cmd_info.connect(self.cmd_buf.sink, omit={"ready", "valid"}),
                # to latch a command only once we use an edge here, which we can do as there is no way
                # for 2 valid commands cycle-by-cycle
                self.cmd_buf.sink.valid.eq(edge(self, cmd_info.valid)),
                # if for some reason buffer hasn't been cleared, then we have an error
                If(self.cmd_buf.sink.valid & ~self.cmd_buf.sink.ready,
                    self.log.error("Simulator internal error: CMD-to-DATA overflow")
                ),
            ]

        self.comb += [
            cmd_info.ready.eq(1),
        ]

        cmd = self.cmd_buf.source

        # DRAM Memory storage
        mems = [Memory(len(pads.dq), depth=nrows * ncols) for _ in range(nbanks)]
        self.specials += mems

        # Combine SDR data from each burst handler into DDR value
        dq_i_p = Signal.like(pads.dq_i)
        dq_i_n = Signal.like(pads.dq_i)
        self.comb += [
            If(pads.wck,
                pads.dq_i.eq(dq_i_n),
            ).Else(
                pads.dq_i.eq(dq_i_p),
            )
        ]

        Burst = lambda wck_cd, dq_i_x: BurstHalf(wck_cd=wck_cd, pads=pads, dq_i=dq_i_x, cmd=cmd,
            mems=mems, nrows=nrows, ncols=ncols, log_level=log_level, logger_kwargs=logger_kwargs)
        self.submodules.burst_p = ClockDomainsRenamer("wck")(Burst("wck", dq_i_p))
        self.submodules.burst_n = ClockDomainsRenamer("wck_n")(Burst("wck_n", dq_i_n))

        def delay(sig, cycles):
            if cycles == 0:
                return sig
            return delayed(self, sig, cycles=cycles)

        # After the WL signal arives we require the data to arrive some time later and then we start
        # reading it. This would be adjustable on hardware, but in simulation we rather must set this
        # so that it matches the delay that PHY introduces.
        wr_start = TappedDelayLine(ntaps=2)
        rd_start = TappedDelayLine(ntaps=2)
        self.submodules += wr_start, rd_start

        def delayed_cases(signal, delay_line, ckr_to_delay):
            cases = {}
            for ckr, delay in ckr_to_delay.items():
                cases[ckr] = signal.eq(delay_line.input if delay == 0 else delay_line.taps[delay - 1])
            return Case(mode_regs.ckr, cases)

        self.comb += [
            wr_start.input.eq(cmd.valid & cmd.we & latency_ready),
            rd_start.input.eq(cmd.valid & ~cmd.we & latency_ready),
            delayed_cases(self.burst_p.enable_wr, wr_start, {2: 0, 4: 0}),
            delayed_cases(self.burst_n.enable_wr, wr_start, {2: 1, 4: 1}),
            delayed_cases(self.burst_p.enable_rd, rd_start, {2: 0, 4: 0}),
            delayed_cases(self.burst_n.enable_rd, rd_start, {2: 1, 4: 1}),
            cmd.ready.eq(self.burst_p.ready),
        ]


class BurstHalf(Module):
    def __init__(self, *, pads, dq_i, cmd, mems, wck_cd, nrows, ncols, log_level, logger_kwargs):
        self.submodules.log = SimLogger(log_level=log_level("burst"), **logger_kwargs)

        self.enable_wr = Signal()
        self.enable_rd = Signal()
        self.ready     = Signal()

        # Register the command
        cmd_d = stream.Endpoint(CMD_INFO_LAYOUT)
        self.sync += cmd_d.eq(cmd)

        # Memory interface
        burst_start = {"wck": 0, "wck_n": 1}[wck_cd]
        mem_addr    = Signal(max=nrows * ncols)
        current_col = Signal(max=ncols)
        col_num     = Signal.like(current_col)
        burst_beat  = Signal.like(current_col, reset=burst_start)

        ports = [
            mem.get_port(write_capable=True, we_granularity=8, async_read=True, clock_domain=wck_cd)
            for mem in mems
        ]
        self.specials += ports
        ports = Array(ports)
        we_all = Signal.like(ports[0].we, reset=2**len(ports[0].we) - 1)

        # Burst control
        burst_length = Signal.like(burst_beat)
        self.comb += [
            self.ready.eq(burst_beat[1:] == burst_length[1:]),
            If(cmd_d.burst32,
                burst_length.eq(32 - 1)
            ).Else(
                burst_length.eq(16 - 1)
            ),
        ]

        self.comb += [
            col_num[4:].eq(cmd_d.col),
            current_col.eq(col_num + burst_beat),
            mem_addr.eq(cmd_d.row * ncols + current_col),
            ports[cmd_d.bank].adr.eq(mem_addr),
        ]

        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            If(self.enable_wr | self.enable_rd,
                NextValue(burst_beat, burst_start),
                If(self.enable_wr,
                    NextState("BURST-WRITE"),
                ).Else(
                    NextState("BURST-READ"),
                ),
            )
        )
        fsm.act("BURST-WRITE",
            If(cmd_d.masked,
                ports[cmd_d.bank].we.eq(delayed(self, ~pads.dmi)),  # DMI HIGH masks a byte
            ).Else(
                ports[cmd_d.bank].we.eq(delayed(self, we_all)),
            ),
            ports[cmd_d.bank].dat_w.eq(delayed(self, pads.dq)),
            self.log.debug("WRITE[%d]: bank=%d, row=%d, col=%d, dq=0x%04x dm=0x%02b",
                burst_beat, cmd_d.bank, cmd_d.row, current_col, delayed(self, pads.dq), pads.dmi,
                once=False
            ),
            If(self.ready,
                NextValue(burst_beat, burst_start),
                If(~self.enable_wr,
                    NextState("IDLE"),
                ),
            ).Else(
                NextValue(burst_beat, burst_beat + 2),
            ),
        )
        fsm.act("BURST-READ",
            ports[cmd_d.bank].we.eq(0),
            dq_i.eq(ports[cmd_d.bank].dat_r),
            self.log.debug("READ[%d]: bank=%d, row=%d, col=%d, dq=0x%04x",
                burst_beat, cmd_d.bank, cmd_d.row, current_col, pads.dq,
                once=False
            ),
            If(self.ready,
                NextValue(burst_beat, burst_start),
                If(~self.enable_rd,
                    NextState("IDLE"),
                ),
            ).Else(
                NextValue(burst_beat, burst_beat + 2),
            ),
        )
