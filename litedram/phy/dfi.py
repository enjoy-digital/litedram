#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.genlib.record import *


def phase_cmd_description(addressbits, bankbits, nranks):
    return [
        ("address", addressbits, DIR_M_TO_S),
        ("bank",       bankbits, DIR_M_TO_S),
        ("cas_n",             1, DIR_M_TO_S),
        ("cs_n",         nranks, DIR_M_TO_S),
        ("ras_n",             1, DIR_M_TO_S),
        ("we_n",              1, DIR_M_TO_S),
        ("cke",          nranks, DIR_M_TO_S),
        ("odt",          nranks, DIR_M_TO_S),
        ("reset_n",           1, DIR_M_TO_S),
        ("act_n",             1, DIR_M_TO_S)
    ]


def phase_wrdata_description(databits):
    return [
        ("wrdata",         databits, DIR_M_TO_S),
        ("wrdata_en",             1, DIR_M_TO_S),
        ("wrdata_mask", databits//8, DIR_M_TO_S)
    ]


def phase_rddata_description(databits):
    return [
        ("rddata_en",           1, DIR_M_TO_S),
        ("rddata",       databits, DIR_S_TO_M),
        ("rddata_valid",        1, DIR_S_TO_M)
    ]


def phase_description(addressbits, bankbits, nranks, databits):
    r = phase_cmd_description(addressbits, bankbits, nranks)
    r += phase_wrdata_description(databits)
    r += phase_rddata_description(databits)
    return r


class Interface(Record):
    def __init__(self, addressbits, bankbits, nranks, databits, nphases=1):
        layout = [("p"+str(i), phase_description(addressbits, bankbits, nranks, databits)) for i in range(nphases)]
        Record.__init__(self, layout)
        self.phases = [getattr(self, "p"+str(i)) for i in range(nphases)]
        for p in self.phases:
            p.cas_n.reset = 1
            p.cs_n.reset = (2**nranks-1)
            p.ras_n.reset = 1
            p.we_n.reset = 1
            p.act_n.reset = 1

    # Returns pairs (DFI-mandated signal name, Migen signal object)
    def get_standard_names(self, m2s=True, s2m=True):
        r = []
        add_suffix = len(self.phases) > 1
        for n, phase in enumerate(self.phases):
            for field, size, direction in phase.layout:
                if (m2s and direction == DIR_M_TO_S) or (s2m and direction == DIR_S_TO_M):
                    if add_suffix:
                        if direction == DIR_M_TO_S:
                            suffix = "_p" + str(n)
                        else:
                            suffix = "_w" + str(n)
                    else:
                        suffix = ""
                    r.append(("dfi_" + field + suffix, getattr(phase, field)))
        return r


class Interconnect(Module):
    def __init__(self, master, slave):
        self.comb += master.connect(slave)


class DDR4DFIMux(Module):
    def __init__(self, dfi_i, dfi_o):
        for i in range(len(dfi_i.phases)):
            p_i = dfi_i.phases[i]
            p_o = dfi_o.phases[i]
            self.comb += [
                p_i.connect(p_o),
                If(~p_i.ras_n & p_i.cas_n & p_i.we_n,
                   p_o.act_n.eq(0),
                   p_o.we_n.eq(p_i.address[14]),
                   p_o.cas_n.eq(p_i.address[15]),
                   p_o.ras_n.eq(p_i.address[16])
                ).Else(
                    p_o.act_n.eq(1),
                )
            ]
