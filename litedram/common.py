from migen import *
from litex.soc.interconnect import stream


bankbits_max = 3


class PhySettings:
    def __init__(self, memtype, dfi_databits,
                 nphases,
                 rdphase, wrphase,
                 rdcmdphase, wrcmdphase,
                 cl, read_latency, write_latency, cwl=0):
        self.memtype = memtype
        self.dfi_databits = dfi_databits

        self.nphases = nphases
        self.rdphase = rdphase
        self.wrphase = wrphase
        self.rdcmdphase = rdcmdphase
        self.wrcmdphase = wrcmdphase

        self.cl = cl
        self.read_latency = read_latency
        self.write_latency = write_latency
        self.cwl = cwl


class GeomSettings:
    def __init__(self, bankbits, rowbits, colbits):
        self.bankbits = bankbits
        self.rowbits = rowbits
        self.colbits =  colbits
        self.addressbits = max(rowbits, colbits)


class TimingSettings:
    def __init__(self, tRP, tRCD, tWR, tWTR, tREFI, tRFC, tFAW, tCCD, tRRD):
        self.tRP = tRP
        self.tRCD = tRCD
        self.tWR = tWR
        self.tWTR = tWTR
        self.tREFI = tREFI
        self.tRFC = tRFC
        self.tFAW = tFAW
        self.tCCD = tCCD
        self.tRRD = tRRD


def cmd_layout(aw):
    return [
        ("valid",        1, DIR_M_TO_S),
        ("ready",        1, DIR_S_TO_M),
        ("we",           1, DIR_M_TO_S),
        ("adr",         aw, DIR_M_TO_S),
        ("lock",         1, DIR_S_TO_M), # only used internally

        ("wdata_ready",  1, DIR_S_TO_M),
        ("rdata_valid",  1, DIR_S_TO_M)
    ]


def data_layout(dw):
    return [
        ("wdata",           dw, DIR_M_TO_S),
        ("wdata_we",     dw//8, DIR_M_TO_S),
        ("wbank", bankbits_max, DIR_S_TO_M),
        ("rdata",           dw, DIR_S_TO_M),
        ("rbank", bankbits_max, DIR_S_TO_M)
    ]


class LiteDRAMInterface(Record):
    def __init__(self, address_align, settings):
        self.aw = settings.geom.rowbits + settings.geom.colbits - address_align
        self.dw = settings.phy.dfi_databits*settings.phy.nphases
        self.nbanks = 2**settings.geom.bankbits
        self.settings = settings

        layout = [("bank"+str(i), cmd_layout(self.aw)) for i in range(self.nbanks)]
        layout += data_layout(self.dw)
        Record.__init__(self, layout)

def cmd_description(aw):
    return [
        ("we",   1),
        ("adr", aw)
    ]

def wdata_description(dw, with_bank):
    r = [
        ("data", dw),
        ("we",   dw//8)
    ]
    if with_bank:
        r += [("bank", bankbits_max)]
    return r

def rdata_description(dw, with_bank):
    r = [("data", dw)]
    if with_bank:
        r += [("bank", bankbits_max)]
    return r


class LiteDRAMPort:
    def __init__(self, mode, aw, dw, cd="sys", id=0,
        reorder=False):
        self.mode = mode
        self.aw = aw
        self.dw = dw
        self.cd = cd
        self.id = id

        self.lock = Signal()

        self.reorder = reorder

        self.cmd = stream.Endpoint(cmd_description(aw))
        self.wdata = stream.Endpoint(wdata_description(dw, reorder))
        self.rdata = stream.Endpoint(rdata_description(dw, reorder))

        if reorder:
            print("WARNING: Reordering controller is experimental")
        self.flush = Signal()


class LiteDRAMWritePort(LiteDRAMPort):
    def __init__(self, *args, **kwargs):
        LiteDRAMPort.__init__(self, "write", *args, **kwargs)


class LiteDRAMReadPort(LiteDRAMPort):
    def __init__(self, *args, **kwargs):
        LiteDRAMPort.__init__(self, "read", *args, **kwargs)


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
