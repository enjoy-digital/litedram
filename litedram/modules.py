from math import ceil

from migen import *

from litedram.common import GeomSettings, TimingSettings


class SDRAMModule:
    """SDRAM module geometry and timings.

    SDRAM controller has to ensure that all geometry and
    timings parameters are fulfilled. Timings parameters
    can be expressed in ns, in SDRAM clock cycles or both
    and controller needs to use the greater value.

    SDRAM modules with the same geometry exist can have
    various speedgrades.
    """
    def __init__(self, clk_freq, rate, speedgrade=None):
        self.clk_freq = clk_freq
        self.rate = rate
        self.speedgrade = speedgrade
        self.geom_settings = GeomSettings(
            bankbits=log2_int(self.nbanks),
            rowbits=log2_int(self.nrows),
            colbits=log2_int(self.ncols),
        )
        self.timing_settings = TimingSettings(
            tRP=self.ns_to_cycles(self.get("tRP")),
            tRCD=self.ns_to_cycles(self.get("tRCD")),
            tWR=self.ns_to_cycles(self.get("tWR")),
            tREFI=self.ns_to_cycles(self.get("tREFI"), False),
            tRFC=self.ns_to_cycles(self.get("tRFC")),
            tWTR=self.ck_ns_to_cycles(*self.get("tWTR")),
            tFAW=None if self.get("tFAW") is None else self.ck_ns_to_cycles(*self.get("tFAW")),
            tCCD=None if self.get("tCCD") is None else self.ck_ns_to_cycles(*self.get("tCCD")),
            tRRD=None if self.get("tRRD") is None else self.ns_to_cycles_trrd(self.get("tRRD")),
            tRC=None if self.get("tRC") is None else self.ns_to_cycles(self.get("tRC")),
            tRAS=None if self.get("tRAS") is None else self.ns_to_cycles(self.get("tRAS"))
        )

    def get(self, name):
        if self.speedgrade is not None and name in ["tRP", "tRCD", "tWR", "tRFC", "tFAW"]:
            name += "_" + self.speedgrade
        try:
            return getattr(self, name)
        except:
            return None

    def ns_to_cycles_trrd(self, t):
        lower_bound = {
            "1:1" : 4,
            "1:2" : 2,
            "1:4" : 1
        }
        if (t is None):
            if self.memtype == "DDR3":
                return lower_bound[self.rate]
            else:
                return 0    #Review: Is this needed for DDR2 and below?
        return max(lower_bound[self.rate], self.ns_to_cycles(t, margin=False))

    def ns_to_cycles(self, t, margin=True):
        clk_period_ns = 1e9/self.clk_freq
        if margin:
            margins = {
                "1:1" : 0,
                "1:2" : clk_period_ns/2,
                "1:4" : 3*clk_period_ns/4
            }
            t += margins[self.rate]
        return ceil(t/clk_period_ns)

    def ck_to_cycles(self, c):
        d = {
            "1:1" : 1,
            "1:2" : 2,
            "1:4" : 4
        }
        return ceil(c/d[self.rate])

    def ck_ns_to_cycles(self, c, t):
        c = 0 if c is None else c
        t = 0 if t is None else t
        return max(self.ck_to_cycles(c), self.ns_to_cycles(t))


# SDR
class IS42S16160(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # speedgrade invariant timings
    tRP   = 20
    tRCD  = 20
    tWR   = 20
    tREFI = 64e6/8192
    tRFC  = 70
    # speedgrade related timings
    tWTR = (2, None)


class MT48LC4M16(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 4096
    ncols  = 256
    # speedgrade invariant timings
    tREFI = 64e6/4096
    tWTR = (2, None)
    # speedgrade related timings
    tRP   = 15
    tRCD  = 15
    tWR   = 14
    tRFC  = 66


class AS4C16M16(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR = (2, None)
    # speedgrade related timings
    tRP   = 18
    tRCD  = 18
    tWR   = 12
    tRFC  = 60


# DDR
class MT46V32M16(SDRAMModule):
    memtype = "DDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR = (2, None)
    # speedgrade related timings
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tRFC  = 70


# LPDDR
class MT46H32M16(SDRAMModule):
    memtype = "LPDDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR = (2, None)
    # speedgrade related timings
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tRFC  = 72


class MT46H32M32(SDRAMModule):
    memtype = "LPDDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR = (2, None)
    # speedgrade related timings
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tRFC  = 72


# DDR2
class MT47H128M8(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR = (None, 7.5)
    tCCD  = (2, None)
    # speedgrade related timings
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tRFC  = 127.5


class MT47H64M16(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR = (None, 7.5)
    tCCD  = (2, None)
    # speedgrade related timings
    tRP   = 15
    tRCD  = 15
    tWR   = 15
    tREFI = 64e6/8192
    tRFC  = 127.5


class P3R1GE4JGF(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR = (None, 7.5)
    tCCD  = (2, None)
    # speedgrade related timings
    tRP   = 12.5
    tRCD  = 12.5
    tWR   = 15
    tREFI = 64e6/8192
    tRFC  = 127.5


# DDR3 (Chips)
class MT41J128M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR  = (4, 7.5)
    tCCD  = (4, None)
    tRRD  = 10
    # speedgrade related timings
    # DDR3-800
    tRP_800  = 13.1
    tRCD_800 = 13.1
    tWR_800  = 13.1
    tRFC_800 = 64
    tFAW_800 = (None, 50)
    tRC_800 = 50.625
    tRAS_800 = 37.5
    # DDR3-1066
    tRP_1066  = 13.1
    tRCD_1066 = 13.1
    tWR_1066  = 13.1
    tRFC_1066 = 86
    tFAW_1066 = (None, 50)
    tRC_1066 = 50.625
    tRAS_1066 = 37.5
    # DDR3-1333
    tRP_1333  = 13.5
    tRCD_1333 = 13.5
    tWR_1333  = 13.5
    tRFC_1333 = 107
    tFAW_1333 = (None, 45)
    tRC_1333 = 49.5
    tRAS_1333 = 36
    # DDR3-1600
    tRP_1600  = 13.75
    tRCD_1600 = 13.75
    tWR_1600  = 13.75
    tRFC_1600 = 128
    tFAW_1600 = (None, 40)
    tRC_1600 = 48.75
    tRAS_1600 = 35
    # API retro-compatibility
    tRP  = tRP_1600
    tRCD = tRCD_1600
    tWR  = tWR_1600
    tRFC = tRFC_1600
    tFAW = tFAW_1600
    tRC = tRC_1600
    tRAS = tRAS_1600


class MT41K128M16(MT41J128M16):
    pass


class MT41J256M16(MT41J128M16):
    # geometry
    nrows  = 32768
    # speedgrade related timings
    tRFC_1066 = 139
    tRFC_1333 = 174
    tRFC_1600 = 208
    # API retro-compatibility
    tRFC = tRFC_1600


class MT41K256M16(MT41J256M16):
    pass


class K4B2G1646FBCK0(SDRAMModule):  ### TODO: optimize and revalidate all timings, at cold and hot temperatures
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 7800  # 3900 refresh more often at 85C+
    tWTR  = (14, 35)
    tCCD  = (4, None)
    tRRD  = 10  # 4 * clk = 10ns
    # speedgrade related timings
    # DDR3-1600
    tRP_1600  = 13.125
    tRCD_1600 = 13.125
    tWR_1600  = 35  # this is hard-coded in MR0 to be 14 cycles, 14 * 2.5 = 35, see sdram_init.py@L224
    tRFC_1600 = 160
    tFAW_1600 = (None, 40)
    # API retro-compatibility
    tRP  = tRP_1600
    tRCD = tRCD_1600
    tWR  = tWR_1600
    tRFC = tRFC_1600
    tFAW = tFAW_1600


# DDR3 (SO-DIMM)
class MT8JTF12864(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR  = (4, 7.5)
    tCCD  = (4, None)
    # speedgrade related timings
    # DDR3-1066
    tRP_1066  = 15
    tRCD_1066 = 15
    tWR_1066  = 15
    tRFC_1066 = 86
    tFAW_1066 = (None, 50)
    # DDR3-1333
    tRP_1333  = 15
    tRCD_1333 = 15
    tWR_1333  = 15
    tRFC_1333 = 107
    tFAW_1333 = (None, 45)
    # API retro-compatibility
    tRP  = tRP_1333
    tRCD = tRCD_1333
    tWR  = tWR_1333
    tRFC = tRFC_1333
    tFAW = tFAW_1333


class MT18KSF1G72HZ(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # speedgrade invariant timings
    tREFI = 64e6/8192
    tWTR = (4, 7.5)
    tCCD  = (4, None)
    # DDR3-1066
    tRP_1066  = 15
    tRCD_1066 = 15
    tWR_1066  = 15
    tRFC_1066 = 86
    tFAW_1066 = (None, 50)
    # DDR3-1333
    tRP_1333  = 15
    tRCD_1333 = 15
    tWR_1333  = 15
    tRFC_1333 = 107
    tFAW_1333 = (None, 45)
    # DDR3-1600
    tRP_1600  = 13.125
    tRCD_1600 = 13.125
    tWR_1600  = 13.125
    tRFC_1600 = 128
    tFAW_1600 = (None, 40)
    # API retro-compatibility
    tRP  = tRP_1600
    tRCD = tRCD_1600
    tWR  = tWR_1600
    tRFC = tRFC_1600
    tFAW = tFAW_1600
