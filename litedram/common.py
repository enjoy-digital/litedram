from migen import *

from litex.soc.interconnect import stream


burst_lengths = {
    "SDR":   1,
    "DDR":   4,
    "LPDDR": 4,
    "DDR2":  4,
    "DDR3":  8,
    "DDR4":  8
}


class Settings:
    def set_attributes(self, attributes):
        for k, v in attributes.items():
            setattr(self, k, v)


class PhySettings(Settings):
    def __init__(self, memtype, dfi_databits,
                 nphases,
                 rdphase, wrphase,
                 rdcmdphase, wrcmdphase,
                 cl, read_latency, write_latency, nranks=1, cwl=None):
        self.set_attributes(locals())
        self.cwl = cl if cwl is None else cwl

    # Optional DDR3 electrical settings:
    # rtt_nom: Non-Writes on-die termination impedance
    # rtt_wr: Writes on-die termination impedance
    # ron: Output driver impedance
    def add_electrical_settings(self, rtt_nom, rtt_wr, ron):
        assert self.memtype == "DDR3"
        self.set_attributes(locals())


class GeomSettings(Settings):
    def __init__(self, bankbits, rowbits, colbits):
        self.set_attributes(locals())
        self.addressbits = max(rowbits, colbits)


class TimingSettings(Settings):
    def __init__(self, tRP, tRCD, tWR, tWTR, tREFI, tRFC, tFAW, tCCD, tRRD, tRC, tRAS):
        self.set_attributes(locals())


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


class LiteDRAMInterface(Record):
    def __init__(self, address_align, settings):
        rankbits = log2_int(settings.phy.nranks)
        self.address_align = address_align
        self.address_width = settings.geom.rowbits + settings.geom.colbits + rankbits - address_align
        self.data_width = settings.phy.dfi_databits*settings.phy.nphases
        self.nbanks = settings.phy.nranks*(2**settings.geom.bankbits)
        self.nranks = settings.phy.nranks
        self.settings = settings

        layout = [("bank"+str(i), cmd_layout(self.address_width)) for i in range(self.nbanks)]
        layout += data_layout(self.data_width)
        Record.__init__(self, layout)

def cmd_description(address_width):
    return [
        ("we",   1),
        ("addr", address_width)
    ]


def wdata_description(data_width):
    r = [
        ("data", data_width),
        ("we",   data_width//8)
    ]
    return r

def rdata_description(data_width):
    r = [("data", data_width)]
    return r


class LiteDRAMNativePort(Settings):
    def __init__(self, mode, address_width, data_width, clock_domain="sys", id=0):
        self.set_attributes(locals())

        self.lock = Signal()

        self.cmd = stream.Endpoint(cmd_description(address_width))
        self.wdata = stream.Endpoint(wdata_description(data_width))
        self.rdata = stream.Endpoint(rdata_description(data_width))

        self.flush = Signal()

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


class LiteDRAMNativeWritePort(LiteDRAMNativePort):
    def __init__(self, *args, **kwargs):
        LiteDRAMNativePort.__init__(self, "write", *args, **kwargs)


class LiteDRAMNativeReadPort(LiteDRAMNativePort):
    def __init__(self, *args, **kwargs):
        LiteDRAMNativePort.__init__(self, "read", *args, **kwargs)


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


class tXXDController(Module):
    def __init__(self, txxd):
        self.valid = valid = Signal()
        self.ready = ready = Signal(reset=1)
        ready.attr.add("no_retiming")

        # # #

        if txxd is not None:
            count = Signal(max=max(txxd, 2))
            self.sync += \
                If(valid,
                    count.eq(txxd-1),
                    If((txxd - 1) == 0,
                        ready.eq(1)
                    ).Else(
                        ready.eq(0)
                    )
                ).Elif(~ready,
                    count.eq(count - 1),
                    If(count == 1, ready.eq(1))
                )
