#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# SDRAM simulation PHY at DFI level tested with SDR/DDR/DDR2/LPDDR/DDR3
# TODO:
# - add multirank support.

from migen import *

from litedram.common import burst_lengths
from litedram.phy.dfi import *
from litedram.modules import _speedgrade_timings, _technology_timings

from functools import reduce
from operator import or_

import struct


SDRAM_VERBOSE_OFF = 0
SDRAM_VERBOSE_STD = 1
SDRAM_VERBOSE_DBG = 2

# Bank Model ---------------------------------------------------------------------------------------

class BankModel(Module):
    def __init__(self, data_width, nrows, ncols, burst_length, nphases, we_granularity, init):
        self.activate     = Signal()
        self.activate_row = Signal(max=nrows)
        self.precharge    = Signal()

        self.write        = Signal()
        self.write_col    = Signal(max=ncols)
        self.write_data   = Signal(data_width)
        self.write_mask   = Signal(data_width//8)

        self.read         = Signal()
        self.read_col     = Signal(max=ncols)
        self.read_data    = Signal(data_width)

        # # #

        active = Signal()
        row    = Signal(max=nrows)

        self.sync += \
            If(self.precharge,
                active.eq(0),
            ).Elif(self.activate,
                active.eq(1),
                row.eq(self.activate_row)
            )

        bank_mem_len   = nrows*ncols//(burst_length*nphases)
        mem            = Memory(data_width, bank_mem_len, init=init)
        write_port     = mem.get_port(write_capable=True, we_granularity=we_granularity)
        read_port      = mem.get_port(async_read=True)
        self.specials += mem, read_port, write_port

        wraddr         = Signal(max=bank_mem_len)
        rdaddr         = Signal(max=bank_mem_len)

        self.comb += [
            wraddr.eq((row*ncols | self.write_col)[log2_int(burst_length*nphases):]),
            rdaddr.eq((row*ncols | self.read_col)[log2_int(burst_length*nphases):]),
        ]

        self.comb += [
            If(active,
                write_port.adr.eq(wraddr),
                write_port.dat_w.eq(self.write_data),
                If(we_granularity,
                    write_port.we.eq(Replicate(self.write, data_width//8) & ~self.write_mask),
                ).Else(
                    write_port.we.eq(self.write),
                ),
                If(self.read,
                    read_port.adr.eq(rdaddr),
                    self.read_data.eq(read_port.dat_r)
                )
            )
        ]

# DFI Phase Model ----------------------------------------------------------------------------------

class DFIPhaseModel(Module):
    def __init__(self, dfi, n):
        phase = getattr(dfi, "p"+str(n))

        self.bank         = phase.bank
        self.address      = phase.address

        self.wrdata       = phase.wrdata
        self.wrdata_mask  = phase.wrdata_mask

        self.rddata       = phase.rddata
        self.rddata_valid = phase.rddata_valid

        self.activate     = Signal()
        self.precharge    = Signal()
        self.write        = Signal()
        self.read         = Signal()

        # # #

        self.comb += [
            If(~phase.cs_n & ~phase.ras_n & phase.cas_n,
                self.activate.eq(phase.we_n),
                self.precharge.eq(~phase.we_n)
            ),
            If(~phase.cs_n & phase.ras_n & ~phase.cas_n,
                self.write.eq(~phase.we_n),
                self.read.eq(phase.we_n)
            )
        ]

# DFI Timings Checker ------------------------------------------------------------------------------

class SDRAMCMD:
    def __init__(self, name: str, enc: int, idx: int):
        self.name = name
        self.enc  = enc
        self.idx  = idx


class TimingRule:
    def __init__(self, prev: str, curr: str, delay: int):
        self.name  = prev + "->" + curr
        self.prev  = prev
        self.curr  = curr
        self.delay = delay


class DFITimingsChecker(Module):
    CMDS = [
        # Name, cs & ras & cas & we value
        ("PRE",  "0010"), # Precharge
        ("REF",  "0001"), # Self refresh
        ("ACT",  "0011"), # Activate
        ("RD",   "0101"), # Read
        ("WR",   "0100"), # Write
        ("ZQCS", "0110"), # ZQCS
    ]

    RULES = [
        # tRP
        ("PRE",  "ACT", "tRP"),
        ("PRE",  "REF", "tRP"),
        # tRCD
        ("ACT",  "WR",  "tRCD"),
        ("ACT",  "RD",  "tRCD"),
        # tRAS
        ("ACT",  "PRE", "tRAS"),
        # tRFC
        ("REF",  "PRE", "tRFC"),
        ("REF",  "ACT", "tRFC"),
        # tCCD
        ("WR",   "RD",  "tCCD"),
        ("WR",   "WR",  "tCCD"),
        ("RD",   "RD",  "tCCD"),
        ("RD",   "WR",  "tCCD"),
        # tRC
        ("ACT",  "ACT", "tRC"),
        # tWR
        ("WR",   "PRE", "tWR"),
        # tWTR
        ("WR",   "RD",  "tWTR"),
        # tZQCS
        ("ZQCS", "ACT", "tZQCS"),
    ]

    def add_cmds(self):
        self.cmds = {}
        for idx, (name, pattern) in enumerate(self.CMDS):
            self.cmds[name] = SDRAMCMD(name, int(pattern, 2), idx)

    def add_rule(self, prev, curr, delay):
        if not isinstance(delay, int):
            delay = self.timings[delay]
        self.rules.append(TimingRule(prev, curr, delay))

    def add_rules(self):
        self.rules = []
        for rule in self.RULES:
            self.add_rule(*rule)

    # Convert ns to ps
    def ns_to_ps(self, val):
        return int(val * 1e3)

    def ck_ns_to_ps(self, val, tck):
        c, t = val
        c = 0 if c is None else c * tck
        t = 0 if t is None else t
        return self.ns_to_ps(max(c, t))

    def prepare_timings(self, timings, refresh_mode, memtype):
        CK_NS = ["tRFC", "tWTR", "tFAW", "tCCD", "tRRD", "tZQCS"]
        REF   = ["tREFI", "tRFC"]
        self.timings = timings
        new_timings  = {}

        tck = self.timings["tCK"]

        for key, val in self.timings.items():
            if refresh_mode is not None and key in REF:
                val = val[refresh_mode]

            if val is None:
                val = 0
            elif key in CK_NS:
                val = self.ck_ns_to_ps(val, tck)
            else:
                val = self.ns_to_ps(val)

            new_timings[key] = val

        new_timings["tRC"] = new_timings["tRAS"] + new_timings["tRP"]

        # Adjust timings relative to write burst - tWR & tWTR
        wrburst = burst_lengths[memtype] if memtype == "SDR" else burst_lengths[memtype] // 2
        wrburst = (new_timings["tCK"] * (wrburst - 1))
        new_timings["tWR"]  = new_timings["tWR"]  + wrburst
        new_timings["tWTR"] = new_timings["tWTR"] + wrburst

        self.timings = new_timings

    def __init__(self, dfi, nbanks, nphases, timings, refresh_mode, memtype, verbose=False):
        self.prepare_timings(timings, refresh_mode, memtype)
        self.add_cmds()
        self.add_rules()

        cnt = Signal(64)
        self.sync += cnt.eq(cnt + nphases)

        phases = [getattr(dfi, "p" + str(n)) for n in range(nphases)]

        last_cmd_ps = [[Signal.like(cnt) for _ in range(len(self.cmds))] for _ in range(nbanks)]
        last_cmd    = [Signal(4) for i in range(nbanks)]

        act_ps   = Array([Signal().like(cnt) for i in range(4)])
        act_curr = Signal(max=4)

        ref_issued = Signal(nphases)

        for np, phase in enumerate(phases):
            ps = Signal().like(cnt)
            self.comb += ps.eq((cnt + np)*self.timings["tCK"])
            state = Signal(4)
            self.comb += state.eq(Cat(phase.we_n, phase.cas_n, phase.ras_n, phase.cs_n))
            all_banks = Signal()

            self.comb += all_banks.eq(
                (self.cmds["REF"].enc == state) |
                ((self.cmds["PRE"].enc == state) & phase.address[10])
            )

            # tREFI
            self.comb += ref_issued[np].eq(self.cmds["REF"].enc == state)

            # Print debug information
            if verbose:
                for _, cmd in self.cmds.items():
                    self.sync += [
                        If(state == cmd.enc,
                            If(all_banks,
                                Display("[%016dps] P%0d " + cmd.name, ps, np)
                            ).Else(
                                Display("[%016dps] P%0d B%0d " + cmd.name, ps, np, phase.bank)
                            )
                        )
                    ]

            # Bank command monitoring
            for i in range(nbanks):
                for _, curr in self.cmds.items():
                    cmd_recv = Signal()
                    self.comb += cmd_recv.eq(((phase.bank == i) | all_banks) & (state == curr.enc))

                    # Checking rules from self.rules
                    for _, prev in self.cmds.items():
                        for rule in self.rules:
                            if rule.prev == prev.name and rule.curr == curr.name:
                                self.sync += [
                                    If(cmd_recv & (last_cmd[i] == prev.enc) &
                                       (ps < (last_cmd_ps[i][prev.idx] + rule.delay)),
                                        Display("[%016dps] {} violation on bank %0d".format(rule.name), ps, i)
                                    )
                                ]

                    # Save command timestamp in an array
                    self.sync += If(cmd_recv, last_cmd_ps[i][curr.idx].eq(ps), last_cmd[i].eq(state))

                    # tRRD & tFAW
                    if curr.name == "ACT":
                        act_next = Signal().like(act_curr)
                        self.comb += act_next.eq(act_curr+1)

                        # act_curr points to newest ACT timestamp
                        self.sync += [
                            If(cmd_recv & (ps < (act_ps[act_curr] + self.timings["tRRD"])),
                                Display("[%016dps] tRRD violation on bank %0d", ps, i)
                            )
                        ]

                        # act_next points to the oldest ACT timestamp
                        self.sync += [
                            If(cmd_recv & (ps < (act_ps[act_next] + self.timings["tFAW"])),
                                Display("[%016dps] tFAW violation on bank %0d", ps, i)
                            )
                        ]

                        # Save ACT timestamp in a circular buffer
                        self.sync += If(cmd_recv, act_ps[act_next].eq(ps), act_curr.eq(act_next))

        # tREFI
        ref_ps      = Signal().like(cnt)
        ref_ps_mod  = Signal().like(cnt)
        ref_ps_diff = Signal(min=-2**63, max=2**63)
        curr_diff   = Signal().like(ref_ps_diff)

        self.comb += curr_diff.eq(ps - (ref_ps + self.timings["tREFI"]))

        # Work in 64ms periods
        self.sync += [
            If(ref_ps_mod < int(64e9),
                ref_ps_mod.eq(ref_ps_mod + nphases * self.timings["tCK"])
            ).Else(
                ref_ps_mod.eq(0)
            )
        ]

        # Update timestamp and difference
        self.sync += If(ref_issued != 0, ref_ps.eq(ps), ref_ps_diff.eq(ref_ps_diff - curr_diff))

        self.sync += [
            If((ref_ps_mod == 0) & (ref_ps_diff > 0),
                Display("[%016dps] tREFI violation (64ms period): %0d", ps, ref_ps_diff)
            )
        ]

        # Report any refresh periods longer than tREFI
        if verbose:
            ref_done = Signal()
            self.sync += [
                If(ref_issued != 0,
                    ref_done.eq(1),
                    If(~ref_done,
                        Display("[%016dps] Late refresh", ps)
                    )
                )
            ]

            self.sync += [
                If((curr_diff > 0) & ref_done & (ref_issued == 0),
                    Display("[%016dps] tREFI violation", ps),
                    ref_done.eq(0)
                )
            ]

        # There is a maximum delay between refreshes on >=DDR
        ref_limit = {"1x": 9, "2x": 17, "4x": 36}
        if memtype != "SDR":
            refresh_mode = "1x" if refresh_mode is None else refresh_mode
            ref_done = Signal()
            self.sync += If(ref_issued != 0, ref_done.eq(1))
            self.sync += [
                If((ref_issued == 0) & ref_done &
                   (ref_ps > (ps + ref_limit[refresh_mode] * self.timings['tREFI'])),
                    Display("[%016dps] tREFI violation (too many postponed refreshes)", ps),
                    ref_done.eq(0)
                )
            ]

# SDRAM PHY Model ----------------------------------------------------------------------------------

class SDRAMPHYModel(Module):
    def __prepare_bank_init_data(self, init, nbanks, nrows, ncols, data_width, address_mapping):
        mem_size          = (self.settings.databits//8)*(nrows*ncols*nbanks)
        bank_size         = mem_size // nbanks
        column_size       = bank_size // nrows
        model_bank_size   = bank_size // (data_width//8)
        model_column_size = model_bank_size // nrows
        model_data_ratio  = data_width // 32
        data_width_bytes  = data_width // 8
        bank_init         = [[] for i in range(nbanks)]

        # Pad init if too short
        if len(init)%data_width_bytes != 0:
            init.extend([0]*(data_width_bytes-len(init)%data_width_bytes))


        # Convert init data width from 32-bit to data_width if needed
        if model_data_ratio > 1:
            new_init = [0]*(len(init)//model_data_ratio)
            for i in range(0, len(init), model_data_ratio):
                ints = init[i:i+model_data_ratio]
                strs = "".join("{:08x}".format(x) for x in reversed(ints))
                new_init[i//model_data_ratio] = int(strs, 16)
            init = new_init
        elif model_data_ratio == 0:
            assert data_width_bytes in [1, 2]
            model_data_ratio = 4 // data_width_bytes
            struct_unpack_patterns = {1: "4B", 2: "2H"}
            new_init = [0]*int(len(init)*model_data_ratio)
            for i in range(len(init)):
                new_init[model_data_ratio*i:model_data_ratio*(i+1)] = struct.unpack(
                    struct_unpack_patterns[data_width_bytes],
                    struct.pack("I", init[i])
                )[0:model_data_ratio]
            init = new_init

        if address_mapping == "ROW_BANK_COL":
            for row in range(nrows):
                for bank in range(nbanks):
                    start = (row*nbanks*model_column_size + bank*model_column_size)
                    end   = min(start + model_column_size, len(init))
                    if start > len(init):
                        break
                    bank_init[bank].extend(init[start:end])
        elif address_mapping == "BANK_ROW_COL":
            for bank in range(nbanks):
                start = bank*model_bank_size
                end   = min(start + model_bank_size, len(init))
                if start > len(init):
                    break
                bank_init[bank] = init[start:end]

        return bank_init

    def __init__(self, module, settings, clk_freq=100e6,
        we_granularity         = 8,
        init                   = [],
        address_mapping        = "ROW_BANK_COL",
        verbosity              = SDRAM_VERBOSE_OFF):

        # Parameters -------------------------------------------------------------------------------
        burst_length = {
            "SDR":   1,
            "DDR":   2,
            "LPDDR": 2,
            "DDR2":  2,
            "DDR3":  2,
            "DDR4":  2,
            }[settings.memtype]

        addressbits   = module.geom_settings.addressbits
        bankbits      = module.geom_settings.bankbits
        rowbits       = module.geom_settings.rowbits
        colbits       = module.geom_settings.colbits

        self.settings = settings
        self.module   = module

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = Interface(
            addressbits = addressbits,
            bankbits    = bankbits,
            nranks      = self.settings.nranks,
            databits    = self.settings.dfi_databits,
            nphases     = self.settings.nphases
        )

        # # #

        nphases    = self.settings.nphases
        nbanks     = 2**bankbits
        nrows      = 2**rowbits
        ncols      = 2**colbits
        data_width = self.settings.dfi_databits*self.settings.nphases

        # DFI phases -------------------------------------------------------------------------------
        phases = [DFIPhaseModel(self.dfi, n) for n in range(self.settings.nphases)]
        self.submodules += phases

        # DFI timing checker -----------------------------------------------------------------------
        if verbosity > SDRAM_VERBOSE_OFF:
            timings = {"tCK": (1e9 / clk_freq) / nphases}

            for name in _speedgrade_timings + _technology_timings:
                timings[name] = self.module.get(name)

            timing_checker = DFITimingsChecker(
                dfi          = self.dfi,
                nbanks       = nbanks,
                nphases      = nphases,
                timings      = timings,
                refresh_mode = self.module.timing_settings.fine_refresh_mode,
                memtype      = settings.memtype,
                verbose      = verbosity > SDRAM_VERBOSE_DBG)
            self.submodules += timing_checker

        # Bank init data ---------------------------------------------------------------------------
        bank_init  = [None for i in range(nbanks)]

        if init:
            bank_init = self.__prepare_bank_init_data(
                init            = init,
                nbanks          = nbanks,
                nrows           = nrows,
                ncols           = ncols,
                data_width      = data_width,
                address_mapping = address_mapping
            )

        # Banks ------------------------------------------------------------------------------------
        banks = [BankModel(
            data_width     = data_width,
            nrows          = nrows,
            ncols          = ncols,
            burst_length   = burst_length,
            nphases        = nphases,
            we_granularity = we_granularity,
            init           = bank_init[i]) for i in range(nbanks)]
        self.submodules += banks

        # Connect DFI phases to Banks (CMDs, Write datapath) ---------------------------------------
        for nb, bank in enumerate(banks):
            # Bank activate
            activates = Signal(len(phases))
            cases     = {}
            for np, phase in enumerate(phases):
                self.comb += activates[np].eq(phase.activate)
                cases[2**np] = [
                    bank.activate.eq(phase.bank == nb),
                    bank.activate_row.eq(phase.address)
                ]
            self.comb += Case(activates, cases)

            # Bank precharge
            precharges = Signal(len(phases))
            cases      = {}
            for np, phase in enumerate(phases):
                self.comb += precharges[np].eq(phase.precharge)
                cases[2**np] = [
                    bank.precharge.eq((phase.bank == nb) | phase.address[10])
                ]
            self.comb += Case(precharges, cases)

            # Bank writes
            bank_write = Signal()
            bank_write_col = Signal(max=ncols)
            writes = Signal(len(phases))
            cases  = {}
            for np, phase in enumerate(phases):
                self.comb += writes[np].eq(phase.write)
                cases[2**np] = [
                    bank_write.eq(phase.bank == nb),
                    bank_write_col.eq(phase.address)
                ]
            self.comb += Case(writes, cases)
            self.comb += [
                bank.write_data.eq(Cat(*[phase.wrdata for phase in phases])),
                bank.write_mask.eq(Cat(*[phase.wrdata_mask for phase in phases]))
            ]

            # Simulate write latency
            for i in range(self.settings.write_latency):
                new_bank_write     = Signal()
                new_bank_write_col = Signal(max=ncols)
                self.sync += [
                    new_bank_write.eq(bank_write),
                    new_bank_write_col.eq(bank_write_col)
                ]
                bank_write = new_bank_write
                bank_write_col = new_bank_write_col

            self.comb += [
                bank.write.eq(bank_write),
                bank.write_col.eq(bank_write_col)
            ]

            # Bank reads
            reads = Signal(len(phases))
            cases = {}
            for np, phase in enumerate(phases):
                self.comb += reads[np].eq(phase.read)
                cases[2**np] = [
                    bank.read.eq(phase.bank == nb),
                    bank.read_col.eq(phase.address)
            ]
            self.comb += Case(reads, cases)

        # Connect Banks to DFI phases (CMDs, Read datapath) ----------------------------------------
        banks_read      = Signal()
        banks_read_data = Signal(data_width)
        self.comb += [
            banks_read.eq(reduce(or_, [bank.read for bank in banks])),
            banks_read_data.eq(reduce(or_, [bank.read_data for bank in banks]))
        ]

        # Simulate read latency --------------------------------------------------------------------
        for i in range(self.settings.read_latency):
            new_banks_read      = Signal()
            new_banks_read_data = Signal(data_width)
            self.sync += [
                new_banks_read.eq(banks_read),
                new_banks_read_data.eq(banks_read_data)
            ]
            banks_read      = new_banks_read
            banks_read_data = new_banks_read_data

        self.comb += [
            Cat(*[phase.rddata_valid for phase in phases]).eq(banks_read),
            Cat(*[phase.rddata for phase in phases]).eq(banks_read_data)
        ]
