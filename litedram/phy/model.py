# This file is Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2020 Piotr Binkowski <pbinkowski@antmicro.com>
# License: BSD

# SDRAM simulation PHY at DFI level tested with SDR/DDR/DDR2/LPDDR/DDR3
# TODO:
# - test/add DDR4 support.
# - add init/dump capabilities.
# - add multirank support.
# - add bandwidth/efficiency measurements.
# - add timings checks.

from migen import *

from litedram.phy.dfi import *

from functools import reduce
from operator import or_

# Bank Model ---------------------------------------------------------------------------------------

class BankModel(Module):
    def __init__(self, data_width, nrows, ncols, burst_length, we_granularity, init):
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

        # FIXME: understand and cleanup
        init.extend([0]*(4-len(init)%4))
        for i in range(0, len(init), 4):
            init[i], init[i+1], init[i+2], init[i+3] = init[i+3], init[i+2], init[i+1], init[i]

        active = Signal()
        row    = Signal(max=nrows)

        self.sync += \
            If(self.precharge,
                active.eq(0),
            ).Elif(self.activate,
                active.eq(1),
                row.eq(self.activate_row)
            )

        mem        = Memory(data_width, nrows*ncols//burst_length, init=init)
        write_port = mem.get_port(write_capable=True, we_granularity=we_granularity)
        read_port  = mem.get_port(async_read=True)
        self.specials += mem, read_port, write_port

        self.comb += [
            If(active,
                write_port.adr.eq(row*ncols | self.write_col),
                write_port.dat_w.eq(self.write_data),
                If(we_granularity,
                    write_port.we.eq(Replicate(self.write, data_width//8) & ~self.write_mask),
                ).Else(
                    write_port.we.eq(self.write),
                ),
                If(self.read,
                    read_port.adr.eq(row*ncols | self.read_col),
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

# SDRAM PHY Model ----------------------------------------------------------------------------------

class SDRAMPHYModel(Module):
    def __init__(self, module, settings, we_granularity=8, init=[], address_mapping="ROW_BANK_COL"):
        # Parameters
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

        # DFI Interface
        self.dfi = Interface(
            addressbits = addressbits,
            bankbits    = bankbits,
            nranks      = self.settings.nranks,
            databits    = self.settings.dfi_databits,
            nphases     = self.settings.nphases
        )

        # # #

        nbanks     = 2**bankbits
        nrows      = 2**rowbits
        ncols      = 2**colbits
        data_width = self.settings.dfi_databits*self.settings.nphases

        # DFI phases -------------------------------------------------------------------------------
        phases = [DFIPhaseModel(self.dfi, n) for n in range(self.settings.nphases)]
        self.submodules += phases

        # Bank init data ---------------------------------------------------------------------------
        bank_size   = (data_width//8)*(nrows*ncols//burst_length) // 4
        column_size = bank_size // nrows
        bank_init   = [[] for i in range(nbanks)]

        if address_mapping == "ROW_BANK_COL":
            for row in range(nrows):
                for bank in range(nbanks):
                    start = row*nbanks*column_size + bank*column_size
                    end   = min(start + column_size, len(init))
                    if start > len(init):
                        break
                    bank_init[bank].extend(init[start:end])
        elif address_mapping == "BANK_ROW_COL":
            for bank in range(nbanks):
                start = bank*bank_size
                end   = min(start + bank_size, len(init))
                if start > len(init):
                    break
                bank_init[bank] = init[start:end]

        # Banks ------------------------------------------------------------------------------------
        banks = [BankModel(data_width, nrows, ncols, burst_length, we_granularity, bank_init[i]) for i in range(nbanks)]
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
