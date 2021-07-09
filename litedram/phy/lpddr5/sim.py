#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from operator import or_
from functools import reduce
from collections import OrderedDict

from migen import *

from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import AutoCSR
#
from litedram.common import TappedDelayLine
from litedram.phy.utils import edge
from litedram.phy.sim_utils import SimLogger, PulseTiming, log_level_getter


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
    def __init__(self, pads, *, log_level, logger_kwargs):
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

        cmd = CommandsSim(pads, cmd_info, logger_kwargs=logger_kwargs, log_level=log_level("cmd"))
        self.submodules.cmd = ClockDomainsRenamer("ck")(cmd)

        data = DataSim(pads, cmd_info, cmd.data_timer.ready_p, logger_kwargs=logger_kwargs, log_level=log_level("data"))
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
    MR_RESET = {}
    FIELD_DEFS = dict(
        # (address, (highest bit, lowest bit)), bits are inclusive
        wl = (1, (7, 4)),
        rl = (2, (3, 0)),
        set_ab = (3, (5, 5)),
        bank_org = (3, (4, 3)),
        ckr = (18, (7, 7)),
    )

    def __init__(self, *, log_level, logger_kwargs):
        self.submodules.log = log = SimLogger(log_level=log_level, **logger_kwargs)
        self.log.add_csrs()

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
    def __init__(self, pads, cmd_info, *, log_level, logger_kwargs):
        self.submodules.log = log = SimLogger(log_level=log_level, **logger_kwargs)
        self.log.add_csrs()
        self.comb += self.log.info("Simulation start")

        self.cmd_info = cmd_info
        self.submodules.mode_regs = ModeRegisters(log_level=log_level, logger_kwargs=logger_kwargs)

        self.nbanks = 16
        self.active_banks = Array([Signal(name=f"bank{i}_active") for i in range(self.nbanks)])
        self.active_rows = Array([Signal(18, name=f"bank{i}_active_row") for i in range(self.nbanks)])

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
        cmd_handlers = OrderedDict(
            ACT = self.activate_handler(),
            PRE = self.precharge_handler(),
            REF = self.refresh_handler(),
            MRW = self.mrw_handler(),
            DATA = self.data_handler(),
            # WRITE/MASKED-WRITE
            # READ
            # CAS
            # MPC
            # MRR
            # WFF/RFF?
            # RDC?
        )
        self.comb += [
            self.handle_cmd.eq(cmds_enabled & cs),
            If(self.handle_cmd & ~reduce(or_, cmd_handlers.values()),
                self.log.error("Unexpected command: CA_p=0b%07b CA_n=0b%07b", self.ca_p, self.ca_n)
            ),

            cmds_enabled.eq(1),
        ]

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
                    self.log.info("PRE: all banks"),
                    bank.eq(2**len(bank) - 1),
                ).Else(
                    self.log.info("PRE: bank = %d", bank),
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
                If(~self.cmd_info.ready,
                    self.log.error("Simulator CMD-to-DATA overflow")
                ),
                # data latency
                If(self.cmd_info.we,
                    self.data_latency.eq(self.mode_regs.wl - 2),
                    If(self.mode_regs.wl < 2,
                        self.log.error("WL < 2 is currently not supported")
                    ),
                ).Else(
                    self.data_latency.eq(self.mode_regs.rl - 2),
                    If(self.mode_regs.rl < 2,
                        self.log.error("RL < 2 is currently not supported")
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

        if wait_time is not None:
            wait_time = wait_time - 1
        next_cmd_timer = PulseTiming(wait_time)
        self.submodules += next_cmd_timer

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
            next_cmd_timer.trigger.eq(1),
            If(next_cmd_timer.ready,
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
    def __init__(self, pads, cmd_info, latency_ready, *, log_level, logger_kwargs, nrows=32768, ncols=1024, nbanks=16):
        self.submodules.log = log = SimLogger(log_level=log_level, **logger_kwargs)
        self.log.add_csrs()

        # CommandsSim produces the data required for handling a data command via cmd_info endpoint.
        # Using stream.ClockDomainCrossing introduces too much latency, so we do a simplistic CDC
        # and store the information in a FIFO, so that it is possible to pipeline data commands.
        self.submodules.cmds = stream.SyncFIFO(CMD_INFO_LAYOUT, depth=4)
        gtkw_dbg["cmds"] = self.cmds
        self.comb += [
            cmd_info.connect(self.cmds.sink, omit={"ready", "valid"}),
            # ~ready will signalize that somehow our FIFO is full, which is an internal error
            cmd_info.ready.eq(cmd_info.valid & self.cmds.sink.ready),
            # to latch a command only once we use an edge here, which we can do as there is no way
            # for 2 valid commands cycle-by-cycle
            self.cmds.sink.valid.eq(edge(self, cmd_info.valid)),
        ]

        wr_start = Signal()
        rd_start = Signal()
        self.comb += [
            wr_start.eq(self.cmds.source.valid & self.cmds.source.we & latency_ready),
            rd_start.eq(self.cmds.source.valid & ~self.cmds.source.we & latency_ready),
        ]

        # After the WL signal arives we require the data to arrive some time later and then we start
        # reading it. This would be adjustable on hardware, but in simulation we rather must set this
        # so that it matches the delay that PHY introduces.
        t_wckdqi = 2 - 1 -1

        wr_start_d = wr_start
        for _ in range(t_wckdqi):
            _wr_start_d = Signal()
            self.sync += _wr_start_d.eq(wr_start_d)
            wr_start_d = _wr_start_d

        current_cmd = stream.Endpoint(CMD_INFO_LAYOUT)
        gtkw_dbg["current_cmd"] = current_cmd
        cmd_buf = stream.PipeValid(CMD_INFO_LAYOUT)
        gtkw_dbg["cmd_buf"] = cmd_buf
        self.submodules += cmd_buf
        self.comb += [
            self.cmds.source.connect(cmd_buf.sink),
            cmd_buf.source.connect(current_cmd),
        ]

        burst_counter = Signal(max=32)
        burst_length = Signal.like(burst_counter)
        self.comb += [
            If(current_cmd.burst32,
                burst_length.eq(32 - 1)
            ).Else(
                burst_length.eq(16 - 1)
            )
        ]

        class BurstWriter(Module):
            def __init__(self, ports, burst_start):
                self.enable = Signal()

                self.submodules.log = log = SimLogger(log_level=log_level, **logger_kwargs)
                self.log.add_csrs()

                mem_addr = Signal(max=nrows * ncols)
                current_col = Signal(max=ncols)
                burst_beat = Signal.like(current_col, reset=burst_start)

                self.sync += If(self.enable,
                    burst_beat.eq(burst_beat + 2)
                ).Else(
                    burst_beat.eq(burst_start)
                )
                self.comb += [
                    If(self.enable,
                        current_col.eq(current_cmd.col + burst_beat),
                        mem_addr.eq(current_cmd.row * ncols + current_col),
                        ports[current_cmd.bank].we.eq(2**len(ports[current_cmd.bank].we) - 1),
                        ports[current_cmd.bank].adr.eq(mem_addr),
                        ports[current_cmd.bank].dat_w.eq(pads.dq),
                        self.log.debug("WRITE[%d]: bank=%d, row=%d, col=%d, dq=0x%04x dm=0x%02b",
                            burst_beat, current_cmd.bank, current_cmd.row, current_col, pads.dq, pads.dmi,
                            once=False
                        ),
                    ),
                ]

        # DRAM Memory storage
        mems = [Memory(len(pads.dq), depth=nrows * ncols) for _ in range(nbanks)]
        ports_p = [mem.get_port(write_capable=True, we_granularity=8, async_read=True, clock_domain="wck") for mem in mems]
        ports_n = [mem.get_port(write_capable=True, we_granularity=8, async_read=True, clock_domain="wck_n") for mem in mems]
        self.specials += mems + ports_p + ports_n
        ports_p = Array(ports_p)
        ports_n = Array(ports_n)

        self.submodules.write_p = ClockDomainsRenamer("wck")(BurstWriter(ports_p, 0))
        self.submodules.write_n = ClockDomainsRenamer("wck_n")(BurstWriter(ports_n, 1))
        write_enable = Signal()
        self.sync.wck_n += If(write_enable,
            self.write_p.enable.eq(1),
            self.write_n.enable.eq(1),
        ).Else(
            self.write_p.enable.eq(0),
            self.write_n.enable.eq(0),
        )

        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            If(wr_start_d,
                current_cmd.ready.eq(1),
                NextValue(burst_counter, 0),
                NextState("WRITE-BURST"),
            )
        )
        fsm.act("WRITE-BURST",
            write_enable.eq(1),
            If(burst_counter == burst_length[1:],
                # TODO: continuous bursts
                # If(wr_start, NextValue(burst_counter, current_cmd.burst32)),
                NextValue(burst_counter, 0),
                NextState("IDLE")
            ).Else(
                NextValue(burst_counter, burst_counter + 1),
            ),
        )
        fsm.act("READ-BURST",
        )



        pass
