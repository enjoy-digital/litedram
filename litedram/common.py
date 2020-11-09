#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2018 John Sully <john@csquare.ca>
# Copyright (c) 2018 bunnie <bunnie@kosagi.com>
# SPDX-License-Identifier: BSD-2-Clause

import math
from functools import reduce
from operator import add
from collections import OrderedDict

from migen import *

from litex.soc.interconnect import stream

# Helpers ------------------------------------------------------------------------------------------

burst_lengths = {
    "SDR":   1,
    "DDR":   4,
    "LPDDR": 4,
    "DDR2":  4,
    "DDR3":  8,
    "DDR4":  8
}

def get_cl_cw(memtype, tck):
    f_to_cl_cwl = OrderedDict()
    if memtype == "DDR2":
        f_to_cl_cwl[400e6]  = (3, 2)
        f_to_cl_cwl[533e6]  = (4, 3)
        f_to_cl_cwl[677e6]  = (5, 4)
        f_to_cl_cwl[800e6]  = (6, 5)
        f_to_cl_cwl[1066e6] = (7, 5)
    elif memtype == "DDR3":
        f_to_cl_cwl[800e6]  = ( 6, 5)
        f_to_cl_cwl[1066e6] = ( 7, 6)
        f_to_cl_cwl[1333e6] = (10, 7)
        f_to_cl_cwl[1600e6] = (11, 8)
    elif memtype == "DDR4":
        f_to_cl_cwl[1333e6] = (9,   9)
        f_to_cl_cwl[1600e6] = (11,  9)
        f_to_cl_cwl[1866e6] = (13, 10)
        f_to_cl_cwl[2133e6] = (15, 11)
        f_to_cl_cwl[2400e6] = (16, 12)
        f_to_cl_cwl[2666e6] = (18, 14)
    else:
        raise ValueError
    for f, (cl, cwl) in f_to_cl_cwl.items():
        if tck >= 2/f:
            return cl, cwl
    raise ValueError

def get_sys_latency(nphases, cas_latency):
    return math.ceil(cas_latency/nphases)

def get_sys_phase(nphases, sys_latency, cas_latency):
    return sys_latency*nphases - cas_latency

# PHY Pads Transformers ----------------------------------------------------------------------------

class PHYPadsReducer:
    """PHY Pads Reducer

    Reduce DRAM pads to only use specific modules.

    For testing purposes, we often need to use only some of the DRAM modules. PHYPadsReducer allows
    selecting specific modules and avoid re-definining dram pins in the Platform for this.
    """
    def __init__(self, pads, modules, with_cat=False):
        self.pads     = pads
        self.modules  = modules
        self.with_cat = with_cat

    def __getattr__(self, name):
        if name in ["dq"]:
            r = Array([getattr(self.pads, name)[8*i + j]
                for i in self.modules
                for j in range(8)])
            return r if not self.with_cat else Cat(r)
        if name in ["dm", "dqs", "dqs_p", "dqs_n"]:
            r = Array([getattr(self.pads, name)[i] for i in self.modules])
            return r if not self.with_cat else Cat(r)
        else:
            return getattr(self.pads, name)

class PHYPadsCombiner:
    """PHY Pads Combiner

    Combine DRAM pads from fully dissociated chips in a unique DRAM pads structure.

    Most generally, DRAM chips are sharing command/address lines between chips (using a fly-by
    topology since DDR3). On some boards, the DRAM chips are using separate command/address lines
    and this combiner can be used to re-create a single pads structure (that will be compatible with
    LiteDRAM's PHYs) to create a single DRAM controller from multiple fully dissociated DRAMs chips.
    """
    def __init__(self, pads):
        if not isinstance(pads, list):
            self.groups = [pads]
        else:
            self.groups = pads
        self.sel = 0

    def sel_group(self, n):
        self.sel = n

    def __getattr__(self, name):
        if name in ["dm", "dq", "dqs", "dqs_p", "dqs_n"]:
            return Array([getattr(self.groups[j], name)[i]
                for i in range(len(getattr(self.groups[0], name)))
                for j in range(len(self.groups))])
        else:
            return getattr(self.groups[self.sel], name)

# BitSlip ------------------------------------------------------------------------------------------

class BitSlip(Module):
    def __init__(self, dw, i=None, o=None, rst=None, slp=None, cycles=1):
        self.i   = Signal(dw) if i is None else i
        self.o   = Signal(dw) if o is None else o
        self.rst = Signal()   if rst is None else rst
        self.slp = Signal()   if slp is None else slp
        assert cycles >= 1

        # # #

        value = Signal(max=cycles*dw, reset=cycles*dw-1)
        self.sync += If(self.slp, value.eq(value + 1))
        self.sync += If(self.rst, value.eq(value.reset))

        r = Signal((cycles+1)*dw, reset_less=True)
        self.sync += r.eq(Cat(r[dw:], self.i))
        cases = {}
        for i in range(cycles*dw):
            cases[i] = self.o.eq(r[i+1:dw+i+1])
        self.comb += Case(value, cases)

# TappedDelayLine ----------------------------------------------------------------------------------

class TappedDelayLine(Module):
    def __init__(self, signal=None, ntaps=1):
        self.input = Signal() if signal is None else signal
        self.taps  = Array(Signal.like(self.input) for i in range(ntaps))
        for i in range(ntaps):
            self.sync += self.taps[i].eq(self.input if i == 0 else self.taps[i-1])
        self.output = self.taps[-1]

# DQS Pattern --------------------------------------------------------------------------------------

class DQSPattern(Module):
    def __init__(self, preamble=None, postamble=None, wlevel_en=0, wlevel_strobe=0, register=False):
        self.preamble  = Signal() if preamble  is None else preamble
        self.postamble = Signal() if postamble is None else postamble
        self.o = Signal(8)

        # # #

        # DQS Pattern transmitted as LSB-first.

        self.comb += [
            self.o.eq(0b01010101),
            If(self.preamble,
                self.o.eq(0b00010101)
            ),
            If(self.postamble,
                self.o.eq(0b01010100)
            ),
            If(wlevel_en,
                self.o.eq(0b00000000),
                If(wlevel_strobe,
                    self.o.eq(0b00000001)
                )
            )
        ]
        if register:
            o = Signal.like(self.o)
            self.sync += o.eq(self.o)
            self.o = o

# Settings -----------------------------------------------------------------------------------------

class Settings:
    def set_attributes(self, attributes):
        for k, v in attributes.items():
            setattr(self, k, v)


class PhySettings(Settings):
    def __init__(self, phytype, memtype, databits, dfi_databits,
                 nphases,
                 rdphase, wrphase,
                 cl, read_latency, write_latency, nranks=1, cwl=None,
                 cmd_latency=None, cmd_delay=None):
        self.set_attributes(locals())
        self.cwl = cl if cwl is None else cwl
        self.is_rdimm = False

    # Optional DDR3/DDR4 electrical settings:
    # rtt_nom: Non-Writes on-die termination impedance
    # rtt_wr: Writes on-die termination impedance
    # ron: Output driver impedance
    # tdqs: Termination Data Strobe enable.
    def add_electrical_settings(self, rtt_nom, rtt_wr, ron, tdqs=False):
        assert self.memtype in ["DDR3", "DDR4"]
        self.set_attributes(locals())

    # Optional RDIMM configuration
    def set_rdimm(self, tck, rcd_pll_bypass, rcd_ca_cs_drive, rcd_odt_cke_drive, rcd_clk_drive):
        assert self.memtype == "DDR4"
        self.is_rdimm = True
        self.set_attributes(locals())

class GeomSettings(Settings):
    def __init__(self, bankbits, rowbits, colbits):
        self.set_attributes(locals())
        self.addressbits = max(rowbits, colbits)


class TimingSettings(Settings):
    def __init__(self, tRP, tRCD, tWR, tWTR, tREFI, tRFC, tFAW, tCCD, tRRD, tRC, tRAS, tZQCS):
        self.set_attributes(locals())

# Layouts/Interface --------------------------------------------------------------------------------

def cmd_layout(address_width):
    return [
        ("valid",            1, DIR_M_TO_S),
        ("ready",            1, DIR_S_TO_M),
        ("we",               1, DIR_M_TO_S),
        ("addr", address_width, DIR_M_TO_S),
        ("lock",             1, DIR_S_TO_M), # only used internally

        ("wdata_ready",      1, DIR_S_TO_M),
        ("rdata_valid",      1, DIR_S_TO_M)
    ]

def data_layout(data_width):
    return [
        ("wdata",       data_width, DIR_M_TO_S),
        ("wdata_we", data_width//8, DIR_M_TO_S),
        ("rdata",       data_width, DIR_S_TO_M)
    ]

def cmd_request_layout(a, ba):
    return [
        ("a",     a),
        ("ba",   ba),
        ("cas",   1),
        ("ras",   1),
        ("we",    1)
    ]

def cmd_request_rw_layout(a, ba):
    return cmd_request_layout(a, ba) + [
        ("is_cmd", 1),
        ("is_read", 1),
        ("is_write", 1)
    ]


class LiteDRAMInterface(Record):
    def __init__(self, address_align, settings):
        rankbits = log2_int(settings.phy.nranks)
        self.address_align = address_align
        self.address_width = settings.geom.rowbits + settings.geom.colbits + rankbits - address_align
        self.data_width    = settings.phy.dfi_databits*settings.phy.nphases
        self.nbanks   = settings.phy.nranks*(2**settings.geom.bankbits)
        self.nranks   = settings.phy.nranks
        self.settings = settings

        layout = [("bank"+str(i), cmd_layout(self.address_width)) for i in range(self.nbanks)]
        layout += data_layout(self.data_width)
        Record.__init__(self, layout)

# Ports --------------------------------------------------------------------------------------------

def cmd_description(address_width):
    return [
        ("we",               1), # Write (1) or Read (0).
        ("addr", address_width)  # Address (in Controller's words).
    ]

def wdata_description(data_width):
    return [
        ("data",    data_width), # Write Data.
        ("we",   data_width//8), # Write Data byte enable.
    ]

def rdata_description(data_width):
    return [("data", data_width)] # Read Data.

class LiteDRAMNativePort(Settings):
    def __init__(self, mode, address_width, data_width, clock_domain="sys", id=0):
        self.set_attributes(locals())

        self.flush = Signal()
        self.lock  = Signal()

        self.cmd   = stream.Endpoint(cmd_description(address_width))
        self.wdata = stream.Endpoint(wdata_description(data_width))
        self.rdata = stream.Endpoint(rdata_description(data_width))

        # retro-compatibility # FIXME: remove
        self.aw = self.address_width
        self.dw = self.data_width
        self.cd = self.clock_domain

    def get_bank_address(self, bank_bits, cba_shift):
        cba_upper = cba_shift + bank_bits
        return self.cmd.addr[cba_shift:cba_upper]

    def get_row_column_address(self, bank_bits, rca_bits, cba_shift):
        cba_upper = cba_shift + bank_bits
        if cba_shift < rca_bits:
            if cba_shift:
                return Cat(self.cmd.addr[:cba_shift], self.cmd.addr[cba_upper:])
            else:
                return self.cmd.addr[cba_upper:]
        else:
            return self.cmd.addr[:cba_shift]

    def connect(self, port):
        return [
            self.cmd.connect(port.cmd),
            self.wdata.connect(port.wdata),
            port.rdata.connect(self.rdata),
            port.flush.eq(self.flush),
            self.lock.eq(port.lock),
        ]

class LiteDRAMNativeWritePort(LiteDRAMNativePort):
    def __init__(self, *args, **kwargs):
        LiteDRAMNativePort.__init__(self, "write", *args, **kwargs)


class LiteDRAMNativeReadPort(LiteDRAMNativePort):
    def __init__(self, *args, **kwargs):
        LiteDRAMNativePort.__init__(self, "read", *args, **kwargs)


# Timing Controllers -------------------------------------------------------------------------------

class tXXDController(Module):
    def __init__(self, txxd):
        self.valid = valid = Signal()
        self.ready = ready = Signal(reset=txxd is None)
        ready.attr.add("no_retiming")

        # # #

        if txxd is not None:
            count = Signal(max=max(txxd, 2))
            self.sync += \
                If(valid,
                    count.eq(txxd - 1),
                    If((txxd - 1) == 0,
                        ready.eq(1)
                    ).Else(
                        ready.eq(0)
                    )
                ).Elif(~ready,
                    count.eq(count - 1),
                    If(count == 1,
                        ready.eq(1)
                    )
                )


class tFAWController(Module):
    def __init__(self, tfaw):
        self.valid = valid = Signal()
        self.ready = ready = Signal(reset=1)
        ready.attr.add("no_retiming")

        # # #

        if tfaw is not None:
            count  = Signal(max=max(tfaw, 2))
            window = Signal(tfaw)
            self.sync += window.eq(Cat(valid, window))
            self.comb += count.eq(reduce(add, [window[i] for i in range(tfaw)]))
            self.sync += \
                If(count < 4,
                    If(count == 3,
                        ready.eq(~valid)
                    ).Else(
                        ready.eq(1)
                    )
                )
