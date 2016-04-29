from functools import reduce
from operator import or_
from collections import namedtuple

from litex.gen import *

PhySettingsT = namedtuple("PhySettings", "memtype dfi_databits nphases rdphase wrphase rdcmdphase wrcmdphase cl cwl read_latency write_latency")
def PhySettings(memtype, dfi_databits, nphases, rdphase, wrphase, rdcmdphase, wrcmdphase, cl, read_latency, write_latency, cwl=0):
    return PhySettingsT(memtype, dfi_databits, nphases, rdphase, wrphase, rdcmdphase, wrcmdphase, cl, cwl, read_latency, write_latency)

GeomSettingsT = namedtuple("_GeomSettings", "bankbits rowbits colbits addressbits")
def GeomSettings(bankbits, rowbits, colbits):
    return GeomSettingsT(bankbits, rowbits, colbits, max(rowbits, colbits))

TimingSettings = namedtuple("TimingSettings", "tRP tRCD tWR tWTR tREFI tRFC")



class Interface(Record):
    def __init__(self, aw, dw, nbanks, req_queue_size, read_latency, write_latency):
        self.aw = aw
        self.dw = dw
        self.nbanks = nbanks
        self.req_queue_size = req_queue_size
        self.read_latency = read_latency
        self.write_latency = write_latency

        bank_layout = [
            ("adr",      aw, DIR_M_TO_S),
            ("we",        1, DIR_M_TO_S),
            ("stb",       1, DIR_M_TO_S),
            ("req_ack",   1, DIR_S_TO_M),
            ("dat_w_ack", 1, DIR_S_TO_M),
            ("dat_r_ack", 1, DIR_S_TO_M),
            ("lock",      1, DIR_S_TO_M)
        ]
        if nbanks > 1:
            layout = [("bank"+str(i), bank_layout) for i in range(nbanks)]
        else:
            layout = bank_layout
        layout += [
            ("dat_w",     dw, DIR_M_TO_S),
            ("dat_we", dw//8, DIR_M_TO_S),
            ("dat_r",     dw, DIR_S_TO_M)
        ]
        Record.__init__(self, layout)
