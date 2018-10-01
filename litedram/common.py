from migen import *
from litex.soc.interconnect import stream


bankbits_max = 3


class PhySettings:
    def __init__(self, memtype, dfi_databits,
                 nphases,
                 rdphase, wrphase,
                 rdcmdphase, wrcmdphase,
                 cl, read_latency, write_latency, nranks=1, cwl=None):
        self.memtype = memtype
        self.dfi_databits = dfi_databits
        self.nranks = nranks

        self.nphases = nphases
        self.rdphase = rdphase
        self.wrphase = wrphase
        self.rdcmdphase = rdcmdphase
        self.wrcmdphase = wrcmdphase

        self.cl = cl
        self.read_latency = read_latency
        self.write_latency = write_latency
        if cwl is None:
            self.cwl = cl
        else:
            self.cwl = cwl

    # Optional DDR3 electrical settings
    def add_electrical_settings(self, rtt_nom, rtt_wr, ron):
        assert self.memtype == "DDR3"
        self.rtt_nom = rtt_nom # Non-Writes on-die termination impedance
        self.rtt_wr = rtt_wr   # Writes on-die termination impedance
        self.ron = ron         # Output driver impedance


class GeomSettings:
    def __init__(self, bankbits, rowbits, colbits):
        self.bankbits = bankbits
        self.rowbits = rowbits
        self.colbits =  colbits
        self.addressbits = max(rowbits, colbits)


class TimingSettings:
    def __init__(self, tRP, tRCD, tWR, tWTR, tREFI, tRFC, tFAW, tCCD, tRRD, tRC, tRAS):
        self.tRP = tRP
        self.tRCD = tRCD
        self.tWR = tWR
        self.tWTR = tWTR
        self.tREFI = tREFI
        self.tRFC = tRFC
        self.tFAW = tFAW
        self.tCCD = tCCD
        self.tRRD = tRRD
        self.tRC = tRC
        self.tRAS = tRAS


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
        ("wbank",     bankbits_max, DIR_S_TO_M),
        ("rdata",       data_width, DIR_S_TO_M),
        ("rbank",     bankbits_max, DIR_S_TO_M)
    ]


class LiteDRAMInterface(Record):
    def __init__(self, address_align, settings):
        rankbits = log2_int(settings.phy.nranks)
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


def wdata_description(data_width, with_bank):
    r = [
        ("data", data_width),
        ("we",   data_width//8)
    ]
    if with_bank:
        r += [("bank", bankbits_max)]
    return r

def rdata_description(data_width, with_bank):
    r = [("data", data_width)]
    if with_bank:
        r += [("bank", bankbits_max)]
    return r


class LiteDRAMNativePort:
    def __init__(self, mode, address_width, data_width, clock_domain="sys", id=0, with_bank=False):
        self.mode = mode
        self.address_width = address_width
        self.data_width = data_width
        self.clock_domain = clock_domain
        self.id = id

        self.lock = Signal()

        self.cmd = stream.Endpoint(cmd_description(address_width))
        self.wdata = stream.Endpoint(wdata_description(data_width, with_bank))
        self.rdata = stream.Endpoint(rdata_description(data_width, with_bank))

        self.flush = Signal()

        # retro-compatibility # FIXME: remove
        self.aw = self.address_width
        self.dw = self.data_width
        self.cd = self.clock_domain


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
