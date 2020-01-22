# This file is Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# This file is Copyright (c) 2015-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2018 John Sully <john@csquare.ca>
# This file is Copyright (c) 2019 Ambroz Bizjak <abizjak.pro@gmail.com>
# This file is Copyright (c) 2019 Antony Pavlov <antonynpavlov@gmail.com>
# This file is Copyright (c) 2018 bunnie <bunnie@kosagi.com>
# This file is Copyright (c) 2018 David Shah <dave@ds0.me>
# This file is Copyright (c) 2019 Steve Haynal - VSD Engineering
# This file is Copyright (c) 2018 Tim 'mithro' Ansell <me@mith.ro>
# This file is Copyright (c) 2018 Daniel Kucera <daniel.kucera@gmail.com>
# This file is Copyright (c) 2018 Mikołaj Sowiński <mikolaj.sowinski@gmail.com>
# License: BSD

from math import ceil
from collections import namedtuple

from migen import *

from litedram.common import Settings, GeomSettings, TimingSettings

# Timings ------------------------------------------------------------------------------------------

_technology_timings = ["tREFI", "tWTR", "tCCD", "tRRD", "tZQCS"]

class _TechnologyTimings(Settings):
    def __init__(self, tREFI, tWTR, tCCD, tRRD, tZQCS=None):
        self.set_attributes(locals())


_speedgrade_timings = ["tRP", "tRCD", "tWR", "tRFC", "tFAW", "tRAS"]

class _SpeedgradeTimings(Settings):
    def __init__(self, tRP, tRCD, tWR, tRFC, tFAW, tRAS):
        self.set_attributes(locals())

# SDRAMModule --------------------------------------------------------------------------------------

class SDRAMModule:
    """SDRAM module geometry and timings.

    SDRAM controller has to ensure that all geometry and
    timings parameters are fulfilled. Timings parameters
    can be expressed in ns, in SDRAM clock cycles or both
    and controller needs to use the greater value.

    SDRAM modules with the same geometry exist can have
    various speedgrades.
    """
    def __init__(self, clk_freq, rate, speedgrade=None, fine_refresh_mode=None):
        self.clk_freq      = clk_freq
        self.rate          = rate
        self.speedgrade    = speedgrade
        self.geom_settings = GeomSettings(
            bankbits = log2_int(self.nbanks),
            rowbits  = log2_int(self.nrows),
            colbits  = log2_int(self.ncols),
        )
        assert not (self.memtype != "DDR4" and fine_refresh_mode != None)
        assert fine_refresh_mode in [None, "1x", "2x", "4x"]
        if (fine_refresh_mode is None) and (self.memtype == "DDR4"):
            fine_refresh_mode = "1x"
        self.timing_settings = TimingSettings(
            tRP   = self.ns_to_cycles(self.get("tRP")),
            tRCD  = self.ns_to_cycles(self.get("tRCD")),
            tWR   = self.ns_to_cycles(self.get("tWR")),
            tREFI = self.ns_to_cycles(self.get("tREFI", fine_refresh_mode), False),
            tRFC  = self.ck_ns_to_cycles(*self.get("tRFC", fine_refresh_mode)),
            tWTR  = self.ck_ns_to_cycles(*self.get("tWTR")),
            tFAW  = None if self.get("tFAW") is None else self.ck_ns_to_cycles(*self.get("tFAW")),
            tCCD  = None if self.get("tCCD") is None else self.ck_ns_to_cycles(*self.get("tCCD")),
            tRRD  = None if self.get("tRRD") is None else self.ck_ns_to_cycles(*self.get("tRRD")),
            tRC   = None  if self.get("tRAS") is None else self.ns_to_cycles(self.get("tRP") + self.get("tRAS")),
            tRAS  = None if self.get("tRAS") is None else self.ns_to_cycles(self.get("tRAS")),
            tZQCS = None if self.get("tZQCS") is None else self.ck_ns_to_cycles(*self.get("tZQCS"))
        )
        self.timing_settings.fine_refresh_mode = fine_refresh_mode

    def get(self, name, key=None):
        r = None
        if name in _speedgrade_timings:
            if hasattr(self, "speedgrade_timings"):
                speedgrade = "default" if self.speedgrade is None else self.speedgrade
                r = getattr(self.speedgrade_timings[speedgrade], name)
            else:
                name = name + "_" + self.speedgrade if self.speedgrade is not None else name
                try:
                    r = getattr(self, name)
                except:
                    pass
        else:
            if hasattr(self, "technology_timings"):
                r = getattr(self.technology_timings, name)
            else:
                try:
                    r = getattr(self, name)
                except:
                    pass
        if (r is not None) and (key is not None):
            r = r[key]
        return r

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

# SDR ----------------------------------------------------------------------------------------------

class IS42S16160(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=20, tRFC=(None, 70), tFAW=None, tRAS=None)}


class IS42S16320(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=20, tRFC=(None, 70), tFAW=None, tRAS=None)}


class MT48LC4M16(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 4096
    ncols  = 256
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=14, tRFC=(None, 66), tFAW=None, tRAS=None)}


class MT48LC16M16(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 15))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=15, tRFC=(None, 66), tFAW=None, tRAS=44)}


class AS4C16M16(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=18, tRCD=18, tWR=12, tRFC=(None, 60), tFAW=None, tRAS=None)}


class AS4C32M16(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=18, tRCD=18, tWR=12, tRFC=(None, 60), tFAW=None, tRAS=None)}

class AS4C32M8(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 15))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=15, tRFC=(None, 66), tFAW=None, tRAS=44)}

class M12L64322A(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 4
    nrows  = 2048
    ncols  = 256
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/4096, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 10))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 55), tFAW=None, tRAS=40)}

class M12L16161A(SDRAMModule):
    memtype = "SDR"
    # geometry
    nbanks = 2
    nrows  = 2048
    ncols  = 256
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/4096, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 10))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 55), tFAW=None, tRAS=40)}

# DDR ----------------------------------------------------------------------------------------------

class MT46V32M16(SDRAMModule):
    memtype = "DDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 70), tFAW=None, tRAS=None)}


# LPDDR
class MT46H32M16(SDRAMModule):
    memtype = "LPDDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 72), tFAW=None, tRAS=None)}


class MT46H32M32(SDRAMModule):
    memtype = "LPDDR"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 72), tFAW=None, tRAS=None)}


# DDR2 ---------------------------------------------------------------------------------------------
class MT47H128M8(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(None, 7.5), tCCD=(2, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 127.5), tFAW=None, tRAS=None)}


class MT47H32M16(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(None, 7.5), tCCD=(2, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 127.5), tFAW=None, tRAS=None)}


class MT47H64M16(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(None, 7.5), tCCD=(2, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 127.5), tFAW=None, tRAS=None)}


class P3R1GE4JGF(SDRAMModule):
    memtype = "DDR2"
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(None, 7.5), tCCD=(2, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=12.5, tRCD=12.5, tWR=15, tRFC=(None, 127.5), tFAW=None, tRAS=None)}

# DDR3 (Chips) -------------------------------------------------------------------------------------

class MT41K64M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=13.1,  tRCD=13.1,  tWR=13.1,  tRFC=(64,  None), tFAW=(None, 50), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=13.1,  tRCD=13.1,  tWR=13.1,  tRFC=(86,  None), tFAW=(None, 50), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.5,  tRCD=13.5,  tWR=13.5,  tRFC=(107, None), tFAW=(None, 45), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=13.75, tRFC=(128, None), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


class MT41J128M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=13.1,  tRCD=13.1,  tWR=13.1,  tRFC=(64, None),  tFAW=(None, 50), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=13.1,  tRCD=13.1,  tWR=13.1,  tRFC=(86, None),  tFAW=(None, 50), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.5,  tRCD=13.5,  tWR=13.5,  tRFC=(107, None), tFAW=(None, 45), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=13.75, tRFC=(128, None), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


class MT41K128M16(MT41J128M16):
    pass


class MT41J256M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 32768
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=13.1,  tRCD=13.1,  tWR=13.1,  tRFC=(139, None), tFAW=(None, 50), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=13.1,  tRCD=13.1,  tWR=13.1,  tRFC=(138, None), tFAW=(None, 50), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.5,  tRCD=13.5,  tWR=13.5,  tRFC=(174, None), tFAW=(None, 45), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=13.75, tRFC=(208, None), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


class MT41K256M16(MT41J256M16):
    pass


class K4B1G0446F(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(120, None), tFAW=(None, 50), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(160, None), tFAW=(None, 50), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.5,   tRCD=13.5,   tWR=15, tRFC=(200, None), tFAW=(None, 45), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.75,  tRCD=13.75,  tWR=15, tRFC=(240, None), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


class K4B2G1646F(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(104, None), tFAW=(None, 50), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(139, None), tFAW=(None, 50), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.5,   tRCD=13.5,   tWR=15, tRFC=(174, None), tFAW=(None, 45), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.75,  tRCD=13.75,  tWR=15, tRFC=(208, None), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


class H5TC4G63CFR(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 7.5), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(260, None), tFAW=(None, 40), tRAS=37.5),
    }
    speedgrade_timings["default"] = speedgrade_timings["800"]


class IS43TR16128B(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=15, tRFC=(None, 160), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


# DDR3 (SO-DIMM) -----------------------------------------------------------------------------------

class MT8JTF12864(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "1066": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(86,  None), tFAW=(None, 50), tRAS=None),
        "1333": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(107, None), tFAW=(None, 45), tRAS=None),
    }
    speedgrade_timings["default"] = speedgrade_timings["1333"]


class MT8KTF51264(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=13.91, tRCD=13.91, tWR=13.91, tRFC=(260, None), tFAW=(None, 50), tRAS=None),
        "1066": _SpeedgradeTimings(tRP=15,    tRCD=15,    tWR=15,    tRFC=(86,  None), tFAW=(None, 50), tRAS=None),
        "1333": _SpeedgradeTimings(tRP=15,    tRCD=15,    tWR=15,    tRFC=(107, None), tFAW=(None, 45), tRAS=None),
    }
    speedgrade_timings["default"] = speedgrade_timings["1333"]


class MT18KSF1G72HZ(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "1066": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15,             tRFC=(86,  None), tFAW=(None, 50), tRAS=None),
        "1333": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15,             tRFC=(107, None), tFAW=(None, 45), tRAS=None),
        "1600": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=(13.125, None), tRFC=(128, None), tFAW=(None, 40), tRAS=None),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


class AS4C256M16D3A(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 32768
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 7.5), tZQCS=(64, 80))
    speedgrade_timings = {
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=15, tRFC=(None, 260), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


class MT16KTF1G64HZ(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "800" : _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15,     tRFC=(140, None), tFAW=(None, 40), tRAS=None),
        "1066": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15,     tRFC=(187, None), tFAW=(None, 40), tRAS=None),
        "1333": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15,     tRFC=(234, None), tFAW=(None, 30), tRAS=None),
        "1600": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=13.125, tRFC=(280, None), tFAW=(None, 30), tRAS=None),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]


# DDR4 (Chips) -------------------------------------------------------------------------------------
class EDY4016A(SDRAMModule):
    memtype = "DDR4"
    # geometry
    ngroupbanks = 4
    ngroups     = 2
    nbanks      = ngroups * ngroupbanks
    nrows       = 32768
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 260), "2x": (None, 160),   "4x": (None, 110)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 4.9), tZQCS=(128, 80))
    speedgrade_timings = {
        "2400": _SpeedgradeTimings(tRP=13.32, tRCD=13.32, tWR=15, tRFC=trfc, tFAW=(28, 30), tRAS=32),
    }
    speedgrade_timings["default"] = speedgrade_timings["2400"]


class MT40A1G8(SDRAMModule):
    memtype = "DDR4"
    # geometry
    ngroupbanks = 4
    ngroups     = 4
    nbanks      = ngroups * ngroupbanks
    nrows       = 65536
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 350), "2x": (None, 260),   "4x": (None, 160)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6.4), tZQCS=(128, 80))
    speedgrade_timings = {
        "2400": _SpeedgradeTimings(tRP=13.32, tRCD=13.32, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=32),
        "2666": _SpeedgradeTimings(tRP=13.50, tRCD=13.50, tWR=15, tRFC=trfc, tFAW=(20, 21), tRAS=32),
    }
    speedgrade_timings["default"] = speedgrade_timings["2400"]


class MT40A512M16(SDRAMModule):
    memtype = "DDR4"
    # geometry
    ngroupbanks = 4
    ngroups     = 2
    nbanks      = ngroups * ngroupbanks
    nrows       = 65536
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 350), "2x": (None, 260),   "4x": (None, 160)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 4.9), tZQCS=(128, 80))
    speedgrade_timings = {
        "2400": _SpeedgradeTimings(tRP=13.32, tRCD=13.32, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=32),
    }
    speedgrade_timings["default"] = speedgrade_timings["2400"]
