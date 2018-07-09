from math import ceil

from migen import *

from litedram.common import GeomSettings, TimingSettings

# TODO:
# - add speedgrade support
# - specify tWTR, tFAW in ck or ns

class SDRAMModule:
    def __init__(self, clk_freq, rate):
        self.clk_freq = clk_freq
        self.rate = rate
        self.geom_settings = GeomSettings(
            bankbits=log2_int(self.nbanks),
            rowbits=log2_int(self.nrows),
            colbits=log2_int(self.ncols),
        )
        self.timing_settings = TimingSettings(
            tRP=self.ns(self.tRP),
            tRCD=self.ns(self.tRCD),
            tWR=self.ns(self.tWR),
            tREFI=self.ns(self.tREFI, False),
            tRFC=self.ns(self.tRFC),
            tWTR=self.tWTR,
            tFAW=None if not hasattr(self, "tFAW") else self.tFAW
        )

    def ns(self, t, margin=True):
        clk_period_ns = 1000000000/self.clk_freq
        if margin:
            margins = {
                "1:1" : 0,
                "1:2" : clk_period_ns/2,
                "1:4" : 3*clk_period_ns/4
            }
            t += margins[self.rate]
        return ceil(t/clk_period_ns)


# SDR
class IS42S16160(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings (ns)
    tRP   = 20
    tRCD  = 20
    tWR   = 20
    tREFI = 64*1000*1000/8192
    tRFC  = 70
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = None


class MT48LC4M16(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 4096
    ncols  = 256
    # timings (ns)
    tRP   = 15
    tRCD  = 15
    tWR   = 14
    tREFI = 64*1000*1000/4096
    tRFC  = 66
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = None


class AS4C16M16(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings (ns)
    tRP   = 18
    tRCD  = 18
    tWR   = 12

    tREFI = 64*1000*1000/8192
    tRFC  = 60
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = None


# DDR
class MT46V32M16(SDRAMModule):
    memtype = "DDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings (ns)
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tREFI = 64*1000*1000/8192
    tRFC  = 70
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = None


# LPDDR
class MT46H32M16(SDRAMModule):
    memtype = "LPDDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings (ns)
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tREFI = 64*1000*1000/8192
    tRFC  = 72
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = None

class MT46H32M32(SDRAMModule):
    memtype = "LPDDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings (ns)
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tREFI = 64*1000*1000/8192
    tRFC  = 72
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = None


# DDR2
class MT47H128M8(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings (ns)
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tREFI = 7800
    tRFC  = 127.5
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = None


class MT47H64M16(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # timings (ns)
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tREFI = 7800
    tRFC  = 127.5
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = None


class P3R1GE4JGF(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # timings (ns)
    tRP   = 12.5
    tRCD  = 12.5
    tWR   = 15
    tREFI = 7800
    tRFC  = 127.5
    # timings (sys_clk cycles)
    tWTR = 3
    tFAW = None

# DDR3
class MT8JTF12864(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings (ns)
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tREFI = 7800
    tRFC  = 70
    # timings (sys_clk cycles)
    tWTR = 2
    tFAW = ceil(32/4)


class MT41J128M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings (ns)
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tREFI = 64*1000*1000/16384
    tRFC  = 260
    # timings (sys_clk cycles)
    tWTR = 3
    tFAW = ceil(32/4)


class MT41K128M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings (ns)
    tRP   = 13.75
    tRCD  = 13.75
    tWR   = 15
    tREFI = 64*1000*1000/8192
    tRFC  = 160
    # timings (sys_clk cycles)
    tWTR = 3
    tFAW = ceil(32/4)


class MT41K256M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 32768
    ncols  = 1024
    # timings (ns)
    tRP   = 13.75
    tRCD  = 13.75
    tWR   = 15
    tREFI = 64*1000*1000/8192
    tRFC  = 260
    # timings (sys_clk cycles)
    tWTR = 3
    tFAW = ceil(32/4)


class MT41J256M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 32768
    ncols  = 1024
    # timings (ns)
    tRP   = 13.75
    tRCD  = 13.75
    tWR   = 15
    tREFI = 64*1000*1000/8192
    tRFC  = 260
    # timings (sys_clk cycles)
    tWTR = 3
    tFAW = ceil(32/4)


class MT18KSF1G72HZ_1G6(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # timings (ns)
    tRP   = 13.75
    tRCD  = 13.75
    tWR   = 15
    tREFI = 64*1000*1000/8192
    tRFC  = 260
    # timings (sys_clk cycles)
    tWTR = 3
    tFAW = ceil(32/4)
