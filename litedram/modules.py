#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2015-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2018 John Sully <john@csquare.ca>
# Copyright (c) 2019 Ambroz Bizjak <abizjak.pro@gmail.com>
# Copyright (c) 2019 Antony Pavlov <antonynpavlov@gmail.com>
# Copyright (c) 2018 bunnie <bunnie@kosagi.com>
# Copyright (c) 2018 David Shah <dave@ds0.me>
# Copyright (c) 2019 Steve Haynal - VSD Engineering
# Copyright (c) 2018 Tim 'mithro' Ansell <me@mith.ro>
# Copyright (c) 2018 Daniel Kucera <daniel.kucera@gmail.com>
# Copyright (c) 2018 Mikołaj Sowiński <mikolaj.sowinski@gmail.com>
# Copyright (c) 2020-2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

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

# SPD ----------------------------------------------------------------------------------------------

def _read_field(byte, nbits, shift):
    mask = 2**nbits - 1
    return (byte & (mask << shift)) >> shift

def _twos_complement(value, nbits):
    if value & (1 << (nbits - 1)):
        value -= (1 << nbits)
    return value

def _word(msb, lsb):
    return (msb << 8) | lsb

# most signifficant (upper) / least signifficant (lower) nibble
def _msn(byte):
    return _read_field(byte, nbits=4, shift=4)

def _lsn(byte):
    return _read_field(byte, nbits=4, shift=0)


class DDR3SPDData:
    memtype = "DDR3"
    _speedgrades = [800, 1066, 1333, 1600, 1866, 2133]

    def __init__(self, spd_data):
        self.get_geometry(spd_data)
        self.init_timebase(spd_data)
        self.get_timings(spd_data)

    def get_geometry(self, data):
        bankbits = {
            0b000: 3,
            0b001: 4,
            0b010: 5,
            0b011: 6,
        }[_read_field(data[4], nbits=3, shift=4)]
        rowbits = {
            0b000: 12,
            0b001: 13,
            0b010: 14,
            0b011: 15,
            0b100: 16,
        }[_read_field(data[5], nbits=3, shift=3)]
        colbits = {
            0b000:  9,
            0b001: 10,
            0b010: 11,
            0b011: 12,
        }[_read_field(data[5], nbits=3, shift=0)]

        self.nbanks = 2**bankbits
        self.nrows = 2**rowbits
        self.ncols = 2**colbits

    def get_timings(self, spd_data):
        b = spd_data
        tck_min  = self.txx_ns(mtb=b[12], ftb=b[34])
        taa_min  = self.txx_ns(mtb=b[16], ftb=b[35])
        twr_min  = self.txx_ns(mtb=b[17])
        trcd_min = self.txx_ns(mtb=b[18], ftb=b[36])
        trrd_min = self.txx_ns(mtb=b[19])
        trp_min  = self.txx_ns(mtb=b[20], ftb=b[37])
        tras_min = self.txx_ns(mtb=_word(_lsn(b[21]), b[22]))
        trc_min  = self.txx_ns(mtb=_word(_msn(b[21]), b[23]), ftb=b[38])
        trfc_min = self.txx_ns(mtb=_word(b[25], b[24]))
        twtr_min = self.txx_ns(mtb=b[26])
        trtp_min = self.txx_ns(mtb=b[27])
        tfaw_min = self.txx_ns(mtb=_word(_lsn(b[28]), b[29]))

        technology_timings = _TechnologyTimings(
            tREFI = 64e6/8192,      # 64ms/8192ops
            tWTR  = (4, twtr_min),  # min 4 cycles
            tCCD  = (4, None),      # min 4 cycles
            tRRD  = (4, trrd_min),  # min 4 cycles
            tZQCS = (64, 80),
        )
        speedgrade_timings = _SpeedgradeTimings(
            tRP  = trp_min,
            tRCD = trcd_min,
            tWR  = twr_min,
            tRFC = (None, trfc_min),
            tFAW = (None, tfaw_min),
            tRAS = tras_min,
        )

        self.speedgrade = str(self.speedgrade_freq(tck_min))
        self.technology_timings = technology_timings
        self.speedgrade_timings = {
            self.speedgrade: speedgrade_timings,
            "default": speedgrade_timings,
        }

    def init_timebase(self, data):
        # All the DDR3 timings are defined in the units of "timebase", which
        # consists of medium timebase (nanosec) and fine timebase (picosec).
        fine_timebase_dividend = _read_field(data[9], nbits=4, shift=4)
        fine_timebase_divisor  = _read_field(data[9], nbits=4, shift=0)
        fine_timebase_ps = fine_timebase_dividend / fine_timebase_divisor
        self.fine_timebase_ns = fine_timebase_ps * 1e-3
        medium_timebase_dividend = data[10]
        medium_timebase_divisor  = data[11]
        self.medium_timebase_ns = medium_timebase_dividend / medium_timebase_divisor

    def txx_ns(self, mtb, ftb=0):
        """Get tXX in nanoseconds from medium and (optional) fine timebase."""
        # decode FTB encoded in 8-bit two's complement
        ftb = _twos_complement(ftb, 8)
        return mtb * self.medium_timebase_ns + ftb * self.fine_timebase_ns

    @classmethod
    def speedgrade_freq(cls, tck_ns):
        # Calculate rounded speedgrade frequency from tck_min
        freq_mhz = (1 / (tck_ns * 1e-9)) / 1e6
        freq_mhz *= 2  # clock rate -> transfer rate (DDR)
        for f in cls._speedgrades:
            # Due to limited tck accuracy of 1ps, calculations may yield higher
            # frequency than in reality (e.g. for DDR3-1866: tck=1.071 ns ->
            # -> f=1867.4 MHz, while real is f=1866.6(6) MHz).
            max_error = 2
            if abs(freq_mhz - f) < max_error:
                return f
        raise ValueError("Transfer rate = {:.2f} does not correspond to any speedgrade"
                         .format(freq_mhz))


class DDR4SPDData(DDR3SPDData):
    memtype = "DDR4"
    _speedgrades = [1600, 1866, 2133, 2400, 2666, 2933, 3200]

    def get_geometry(self, data):
        bankgroupbits = {
            0b00: 0,
            0b01: 1,
            0b10: 2,
        }[_read_field(data[4], nbits=2, shift=6)]
        bankbits = {
            0b00: 2,
            0b01: 3,
        }[_read_field(data[4], nbits=2, shift=4)]
        rowbits = {
            0b000: 12,
            0b001: 13,
            0b010: 14,
            0b011: 15,
            0b100: 16,
            0b101: 17,
            0b110: 18,
        }[_read_field(data[5], nbits=3, shift=3)]
        colbits = {
            0b000:  9,
            0b001: 10,
            0b010: 11,
            0b011: 12,
        }[_read_field(data[5], nbits=3, shift=0)]

        self.ngroups = 2**bankgroupbits
        self.ngroupbanks = 2**bankbits
        self.nbanks = self.ngroups * self.ngroupbanks
        self.nrows = 2**rowbits
        self.ncols = 2**colbits

    def init_timebase(self, data):
        # there is only one possible value for DDR4
        self.medium_timebase_ns = {
            0b00: 125e-3,
        }[_read_field(data[17], nbits=2, shift=2)]
        self.fine_timebase_ns = {
            0b00: 1e-3,
        }[_read_field(data[17], nbits=2, shift=0)]

    def get_timings(self, data):
        b = data

        self.trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}

        tckavg_min  = self.txx_ns(mtb=b[18], ftb=b[125])
        tckavg_max  = self.txx_ns(mtb=b[19], ftb=b[124])
        taa_min  = self.txx_ns(mtb=b[24], ftb=b[123])
        trcd_min = self.txx_ns(mtb=b[25], ftb=b[122])
        trp_min  = self.txx_ns(mtb=b[26], ftb=b[121])
        tras_min = self.txx_ns(mtb=_word(_lsn(b[27]), b[28]))
        trc_min  = self.txx_ns(mtb=_word(_msn(b[27]), b[29]), ftb=b[120])
        self.trfc = {
            "1x": (None, self.txx_ns(mtb=_word(b[31], b[30]))),
            "2x": (None, self.txx_ns(mtb=_word(b[33], b[32]))),
            "4x": (None, self.txx_ns(mtb=_word(b[35], b[34]))),
        }
        tfaw_min = self.txx_ns(mtb=_word(_lsn(b[36]), b[37]))
        trrd_s_min = self.txx_ns(mtb=b[38], ftb=b[119])
        trrd_l_min = self.txx_ns(mtb=b[39], ftb=b[118])
        tccd_l_min = self.txx_ns(mtb=b[40], ftb=b[117])  # min 6 cycles?
        twr_min  = self.txx_ns(mtb=_word(_lsn(b[41]), b[42]))
        twtr_s_min = self.txx_ns(mtb=_word(_lsn(b[43]), b[44]))
        twtr_l_min = self.txx_ns(mtb=_word(_msn(b[43]), b[45]))

        # minimum tFAW in clock cycles depends on page size
        sdram_device_width = {
            0b000:  4,
            0b001:  8,
            0b010: 16,
            0b011: 32,
        }[_read_field(b[12], nbits=3, shift=0)]
        page_size_bytes = self.ncols * sdram_device_width / 8
        tfaw_min_ck = {
            512:  16,
            1024: 20,
            2048: 28,
        }[page_size_bytes]

        technology_timings = _TechnologyTimings(
            tREFI = self.trefi,
            tWTR  = (4, twtr_l_min),
            tCCD  = (4, tccd_l_min),
            tRRD  = (4, trrd_l_min),
            tZQCS = (128, 80),
        )
        speedgrade_timings = _SpeedgradeTimings(
            tRP  = trp_min,
            tRCD = trcd_min,
            tWR  = twr_min,
            tRFC = self.trfc,
            tFAW = (tfaw_min_ck, tfaw_min),
            tRAS = tras_min,
        )

        self.speedgrade = str(self.speedgrade_freq(tckavg_min))
        self.technology_timings = technology_timings
        self.speedgrade_timings = {
            self.speedgrade: speedgrade_timings,
            "default": speedgrade_timings,
        }

def parse_spd_hexdump(filename):
    """Parse data dumped using the `spdread` command in LiteX BIOS

    This will read files in format:
        Memory dump:
        0x00000000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  ................
        0x00000010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f  ................
    """
    data = []
    last_addr = -1
    with open(filename) as f:
        for line in f:
            if line.startswith("0x"):
                tokens = line.strip().split()
                addr = int(tokens[0], 16)
                assert addr > last_addr
                values = [int(v, 16) for v in tokens[1:17]]
                data.extend(values)
                last_addr = addr
    return data

# SDRAMModule --------------------------------------------------------------------------------------

Frac = namedtuple("Frac", ["num", "denom"])

class Timing(namedtuple("Timing", ["ck", "ns"])):
    def __add__(self, other):
        return Timing(self.ck + other.ck, self.ns + other.ns)

class SDRAMModule:
    """SDRAM module geometry and timings.

    SDRAM controller has to ensure that all geometry and
    timings parameters are fulfilled. Timings parameters
    can be expressed in ns, in SDRAM clock cycles or both
    and controller needs to use the greater value.

    SDRAM modules with the same geometry exist can have
    various speedgrades.
    """
    registered = False
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
            tRP   = self.ck_ns_to_cycles(self.get("tRP")),
            tRCD  = self.ck_ns_to_cycles(self.get("tRCD")),
            tWR   = self.ck_ns_to_cycles(self.get("tWR")),
            tREFI = self.ck_ns_to_cycles(self.get("tREFI", fine_refresh_mode), margin=False),
            tRFC  = self.ck_ns_to_cycles(self.get("tRFC", fine_refresh_mode)),
            tWTR  = self.ck_ns_to_cycles(self.get("tWTR")),
            tFAW  = None if self.get("tFAW") is None else self.ck_ns_to_cycles(self.get("tFAW")),
            tCCD  = None if self.get("tCCD") is None else self.ck_ns_to_cycles(self.get("tCCD")),
            tRRD  = None if self.get("tRRD") is None else self.ck_ns_to_cycles(self.get("tRRD")),
            tRC   = None if self.get("tRAS") is None else self.ck_ns_to_cycles(self.get("tRP") + self.get("tRAS")),
            tRAS  = None if self.get("tRAS") is None else self.ck_ns_to_cycles(self.get("tRAS")),
            tZQCS = None if self.get("tZQCS") is None else self.ck_ns_to_cycles(self.get("tZQCS"))
        )
        self.timing_settings.fine_refresh_mode = fine_refresh_mode

    def get(self, name, key=None):
        assert name in _speedgrade_timings + _technology_timings, "Unknown name: {}".format(name)
        timing = self.get_timing(name)
        if timing is None:
            return None
        if (timing is not None) and (key is not None):
            timing = timing[key]
        if isinstance(timing, tuple):
            ck, ns = timing
        else:
            ck, ns = 0, timing
        ck = ck or 0
        ns = ns or 0
        return Timing(ck, ns)

    def get_timing(self, name):
        if name in _speedgrade_timings:
            return self.get_speedgrade_timing(name)
        return self.get_technology_timing(name)

    def get_speedgrade_timing(self, name):
        if hasattr(self, "speedgrade_timings"):
            speedgrade = "default" if self.speedgrade is None else self.speedgrade
            return getattr(self.speedgrade_timings[speedgrade], name)
        name = name + "_" + self.speedgrade if self.speedgrade is not None else name
        try:
            return getattr(self, name)
        except:
            pass

    def get_technology_timing(self, name):
        if hasattr(self, "technology_timings"):
            return getattr(self.technology_timings, name)
        else:
            try:
                return getattr(self, name)
            except:
                pass

    def ns_to_cycles(self, t, margin=True):
        clk_period_ns = 1e9/self.clk_freq
        t += self.margin if margin else 0
        return ceil(t/clk_period_ns)

    def ck_to_cycles(self, c):
        return ceil(c/self.rate_frac.denom)

    def ck_ns_to_cycles(self, timing, **kwargs):
        return max(self.ck_to_cycles(timing.ck), self.ns_to_cycles(timing.ns, **kwargs))

    @property
    def rate_frac(self):
        num, denom = map(int, self.rate.split(":"))
        assert num == 1, "Rate: numerator must be 1: {}".format(self.rate)
        return Frac(num, denom)

    @property
    def margin(self):
        clk_period_ns = 1e9 / self.clk_freq
        frac = self.rate_frac
        return clk_period_ns * (1 - frac.num/frac.denom)

    @classmethod
    def from_spd_data(cls, spd_data, clk_freq, fine_refresh_mode=None):
        # set parameters from SPD data based on memory type
        spd_cls = {
            0x0b: DDR3SPDData,
            0x0c: DDR4SPDData,
        }[spd_data[2]]
        spd = spd_cls(spd_data)

        # Create a deriving class to avoid modifying this one
        class _SDRAMModule(cls):
            memtype = spd.memtype
            nbanks = spd.nbanks
            nrows = spd.nrows
            ncols = spd.ncols
            technology_timings = spd.technology_timings
            speedgrade_timings = spd.speedgrade_timings
            # Save data for runtime verification
            _spd_data = spd_data

        nphases = {
            "SDR":   1,
            "DDR":   2,
            "LPDDR": 2,
            "DDR2":  2,
            "DDR3":  4,
            "DDR4":  4,
        }[spd.memtype]
        rate = "1:{}".format(nphases)

        return _SDRAMModule(clk_freq,
            rate              = rate,
            speedgrade        = spd.speedgrade,
            fine_refresh_mode = fine_refresh_mode)

class SDRAMRegisteredModule(SDRAMModule): registered = True

# SDR ----------------------------------------------------------------------------------------------

class SDRModule(SDRAMModule):                     memtype = "SDR"
class SDRRegisteredModule(SDRAMRegisteredModule): memtype = "SDR"

class IS42S16160(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=20, tRFC=(None, 70), tFAW=None, tRAS=None)}

class IS42S16320(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=20, tRFC=(None, 70), tFAW=None, tRAS=None)}

class MT48LC4M16(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 4096
    ncols  = 256
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=14, tRFC=(None, 66), tFAW=None, tRAS=None)}

class MT48LC16M16(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 15))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=15, tRFC=(None, 66), tFAW=None, tRAS=44)}

class MT48LC32M8(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 15))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=15, tRFC=(None, 66), tFAW=None, tRAS=44)}

class AS4C4M16(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 4096
    ncols  = 256
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/4096, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 14))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=22, tRCD=21, tWR=20, tRFC=(None, 63), tFAW=None, tRAS=42)}

class AS4C16M16(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=18, tRCD=18, tWR=12, tRFC=(None, 60), tFAW=None, tRAS=None)}

class AS4C32M16(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=18, tRCD=18, tWR=12, tRFC=(None, 60), tFAW=None, tRAS=None)}

class AS4C32M8(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 15))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=20, tRCD=20, tWR=15, tRFC=(None, 66), tFAW=None, tRAS=44)}

class M12L64322A(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 2048
    ncols  = 256
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/4096, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 10))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 55), tFAW=None, tRAS=40)}

class M12L16161A(SDRModule):
    # geometry
    nbanks = 2
    nrows  = 2048
    ncols  = 256
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/4096, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 10))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 55), tFAW=None, tRAS=40)}

class W9825G6KH6(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 512
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 10))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 60), tFAW=None, tRAS=42)}

class W9812G6JB(SDRModule):
    # geometry
    nbanks = 4
    nrows  = 4096
    ncols  = 512
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=(None, 12))
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=20, tRFC=(None, 60), tFAW=None, tRAS=42)}

# DDR ----------------------------------------------------------------------------------------------

class DDRModule(SDRAMModule):                     memtype = "DDR"
class DDRRegisteredModule(SDRAMRegisteredModule): memtype = "DDR"

class MT46V32M16(DDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 70), tFAW=None, tRAS=None)}

# LPDDR --------------------------------------------------------------------------------------------

class LPDDRModule(SDRAMModule):                     memtype = "LPDDR"
class LPDDRRegisteredModule(SDRAMRegisteredModule): memtype = "LPDDR"

class MT46H32M16(LPDDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 72), tFAW=None, tRAS=None)}

class MT46H64M16(LPDDRModule):
    # geometry
    nbanks = 4
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 72), tFAW=None, tRAS=None)}

class MT46H128M16(LPDDRModule):
    # geometry
    nbanks = 4
    nrows  = 16384
    ncols  = 2048
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 72), tFAW=None, tRAS=None)}

class MT46H32M32(LPDDRModule):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(2, None), tCCD=(1, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 72), tFAW=None, tRAS=None)}

# DDR2 ---------------------------------------------------------------------------------------------

class DDR2Module(SDRAMModule):                     memtype = "DDR2"
class DDR2RegisteredModule(SDRAMRegisteredModule): memtype = "DDR2"

class MT47H128M8(DDR2Module):
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(None, 7.5), tCCD=(2, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 127.5), tFAW=None, tRAS=None)}

class MT47H32M16(DDR2Module):
    # geometry
    nbanks = 4
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(None, 7.5), tCCD=(2, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 127.5), tFAW=None, tRAS=None)}

class MT47H64M16(DDR2Module):
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(None, 7.5), tCCD=(2, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=15, tRCD=15, tWR=15, tRFC=(None, 127.5), tFAW=None, tRAS=None)}

class P3R1GE4JGF(DDR2Module):
    # geometry
    nbanks = 8
    nrows  = 8192
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(None, 7.5), tCCD=(2, None), tRRD=None)
    speedgrade_timings = {"default": _SpeedgradeTimings(tRP=12.5, tRCD=12.5, tWR=15, tRFC=(None, 127.5), tFAW=None, tRAS=None)}

# DDR3 (Chips) -------------------------------------------------------------------------------------

class DDR3Module(SDRAMModule):                     memtype = "DDR3"
class DDR3RegisteredModule(SDRAMRegisteredModule): memtype = "DDR3"

class AS4C128M16(DDR3Module):
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=13.75, tRFC=(160, None), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]

class MT41K64M16(DDR3Module):
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

class MT41J256M8(DDR3Module):
    # geometry
    nbanks = 8
    nrows  = 32768
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=13.1,  tRCD=13.1,  tWR=15,  tRFC=(64, None),  tFAW=(None, 50), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=13.1,  tRCD=13.1,  tWR=15,  tRFC=(86, None),  tFAW=(None, 50), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.5,  tRCD=13.5,  tWR=15,  tRFC=(107, None), tFAW=(None, 45), tRAS=36),
    }
    speedgrade_timings["default"] = speedgrade_timings["1333"]

class MT41K256M8(DDR3Module):
    # geometry
    nbanks = 8
    nrows  = 32768
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
          "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=15, tRFC=(128, None), tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]

class MT41J128M16(DDR3Module):
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

class MT41K128M16(MT41J128M16): pass

class MT41J256M16(DDR3Module):
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

class MT41K256M16(MT41J256M16): pass

class MT41J512M16(DDR3Module):
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=13.75, tRFC=(280, None), tFAW=(None, 40), tRAS=39),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]

class MT41K512M16(MT41J512M16): pass

class K4B1G0446F(DDR3Module):
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

class K4B2G1646F(DDR3Module):
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

class H5TC4G63CFR(DDR3Module):
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

class IS43TR16128B(DDR3Module):
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

class IS43TR16256A(DDR3Module):
    # geometry
    nbanks = 8
    nrows  = 32768
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=15, tRFC=(None, 260), tFAW=(None, 30), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]

class IS43TR16512B(DDR3Module):
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 10), tZQCS=(64, 80))
    speedgrade_timings = {
        "800":  _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(None, 350), tFAW=(None, 50), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 350), tFAW=(None, 50), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.5,   tRCD=13.5,   tWR=15, tRFC=(None, 350), tFAW=(None, 50), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.75,  tRCD=13.75,  tWR=15, tRFC=(None, 350), tFAW=(None, 50), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]

# DDR3 (SO-DIMM) -----------------------------------------------------------------------------------

class MT8JTF12864(DDR3Module):
    # base chip: MT41J128M8
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
        "1066": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(None, 110), tFAW=(None, 37.5), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 110), tFAW=(None, 30),   tRAS=36),
    }
    speedgrade_timings["default"] = speedgrade_timings["1333"]

class MT8KTF51264(DDR3Module):
    # base chip: MT41K512M8
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
        "800" : _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(None, 260), tFAW=(None, 40), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(None, 260), tFAW=(None, 40), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 260), tFAW=(None, 30), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 260), tFAW=(None, 30), tRAS=35),
        "1866": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 260), tFAW=(None, 27), tRAS=34),
    }
    speedgrade_timings["default"] = speedgrade_timings["1866"]

class MT18KSF1G72HZ(DDR3Module):
    # base chip: MT41K512M8
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
        "1066": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(None, 260), tFAW=(None, 40), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 260), tFAW=(None, 30), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 260), tFAW=(None, 30), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]

class AS4C256M16D3A(DDR3Module):
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

class MT16KTF1G64HZ(DDR3Module):
    # base chip: MT41K512M8
    # geometry
    nbanks = 8
    nrows  = 65536
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 6), tZQCS=(64, 80))
    speedgrade_timings = {
        "800" : _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(None, 260), tFAW=(None, 40), tRAS=37.5),
        "1066": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(None, 260), tFAW=(None, 40), tRAS=37.5),
        "1333": _SpeedgradeTimings(tRP=15,     tRCD=15,     tWR=15, tRFC=(None, 260), tFAW=(None, 30), tRAS=36),
        "1600": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 260), tFAW=(None, 30), tRAS=35),
        "1866": _SpeedgradeTimings(tRP=13.125, tRCD=13.125, tWR=15, tRFC=(None, 260), tFAW=(None, 27), tRAS=34),
    }
    speedgrade_timings["default"] = speedgrade_timings["1866"]

# RPC ----------------------------------------------------------------------------------------------

class RPCModule(SDRAMModule): memtype = "RPC"

class EM6GA16L(RPCModule):
    # 64MBits per bank => 256Mb
    # TODO: the timings may need further verification
    # geometry
    nbanks = 4     #
    ncols = 1024
    nrows = 4096  # 64M / 1024 / 16 = 4k
    # timings
    technology_timings = _TechnologyTimings(
        tREFI=64e6/8192,
        # It seems that we need to calculate tCCD from tBESL by assuming BC=1, then it is:
        # RL=WL + burst_time + tBESL
        tCCD=(13+1 + 8 + 7, None),
        # CCD enforces tBESL for read commands, we use tWTR to ensure it for writes
        tWTR=(11 + 2, None),  # 11 for tBESL + 2 for STB low before a command
        tRRD=(None, 7.5),
        tZQCS=(None, 90),
    )
    speedgrade_timings = {
        # FIXME: we're increasing tWR by 1 sysclk to compensate for long write (assuming max sysclk 200 MHz)
        # Should we use tRFQSd for tRFC?
        "1600": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=15 + 1e9/200e6, tRFC=(3*100, None), tFAW=None, tRAS=35),
        "1866": _SpeedgradeTimings(tRP=13.91, tRCD=13.91, tWR=15 + 1e9/200e6, tRFC=(3*100, None), tFAW=None, tRAS=34),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]

# DDR4 (Chips) -------------------------------------------------------------------------------------

class DDR4Module(SDRAMModule):                     memtype = "DDR4"
class DDR4RegisteredModule(SDRAMRegisteredModule): memtype = "DDR4"

class EDY4016A(DDR4Module):
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

class MT40A1G8(DDR4Module):
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

class MT40A2G8(DDR4Module):
    # geometry
    ngroupbanks = 4
    ngroups     = 4
    nbanks      = ngroups * ngroupbanks
    nrows       = 131072
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

class MT40A2G16(MT40A2G8):
    pass # TwinDie MT40A2G8.

class MT40A256M16(DDR4Module):
    # geometry
    ngroupbanks = 4
    ngroups     = 2
    nbanks      = ngroups * ngroupbanks
    nrows       = 32768
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192, "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 260), "2x": (None, 160), "4x": (None, 110)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 4.9), tZQCS=(128, 80))
    speedgrade_timings = {
        "2400": _SpeedgradeTimings(tRP=13.32, tRCD=13.32, tWR=15, tRFC=trfc, tFAW=(28, 35), tRAS=32),
    }
    speedgrade_timings["default"] = speedgrade_timings["2400"]

class MT40A512M8(DDR4Module):
    # geometry
    ngroupbanks = 4
    ngroups     = 4
    nbanks      = ngroups * ngroupbanks
    nrows       = 32768
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 350), "2x": (None, 260),   "4x": (None, 160)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 4.9), tZQCS=(128, 80))
    speedgrade_timings = {
        "2400": _SpeedgradeTimings(tRP=13.32, tRCD=13.32, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=32),
        "2666": _SpeedgradeTimings(tRP=13.50, tRCD=13.50, tWR=15, tRFC=trfc, tFAW=(20, 21), tRAS=32),
    }
    speedgrade_timings["default"] = speedgrade_timings["2400"]

class MT40A512M16(DDR4Module):
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

# DDR4 (SO-DIMM) -----------------------------------------------------------------------------------

class KVR21SE15S84(DDR4Module):
    # geometry
    ngroupbanks = 4
    ngroups     = 4
    nbanks      = ngroups * ngroupbanks
    nrows       = 32768
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 350), "2x": (None, 260),   "4x": (None, 160)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 4.9), tZQCS=(128, 80))
    speedgrade_timings = {
        "2133": _SpeedgradeTimings(tRP=13.5, tRCD=13.5, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=33),
    }
    speedgrade_timings["default"] = speedgrade_timings["2133"]

class MTA4ATF51264HZ(DDR4Module):
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
        "2133": _SpeedgradeTimings(tRP=13.5, tRCD=13.5, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=33),
    }
    speedgrade_timings["default"] = speedgrade_timings["2133"]

# DDR4 (RDIMM) -------------------------------------------------------------------------------------

class MTA18ASF2G72PZ(DDR4RegisteredModule):
    # geometry
    ngroupbanks = 4
    ngroups     = 4
    nbanks      = ngroups * ngroupbanks
    nrows       = 131072
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 350), "2x": (None, 260),   "4x": (None, 160)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(4, 4.9), tZQCS=(128, 80))
    speedgrade_timings = {
        "2400": _SpeedgradeTimings(tRP=14.16, tRCD=14.16, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=32),
        "2666": _SpeedgradeTimings(tRP=14.25, tRCD=14.25, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=32),
        "2933": _SpeedgradeTimings(tRP=14.32, tRCD=14.32, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=32),
        "3200": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=15, tRFC=trfc, tFAW=(20, 25), tRAS=32),
    }
    speedgrade_timings["default"] = speedgrade_timings["2400"]

class MTA36ASF4G72PZ(MTA18ASF2G72PZ): pass
    # This module is similar to MTA18ASF2G72PZ, with the exception that it is a dual-rank module. The rank number
    # can be specified in the PHY settings.

class HMA82GR7DJR4N(DDR4RegisteredModule):
    # geometry
    ngroupbanks = 4
    ngroups     = 4
    nbanks      = ngroups * ngroupbanks
    nrows       = 131072
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 350), "2x": (None, 260),   "4x": (None, 160)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, 5), tRRD=(4, 4.9), tZQCS=(128, 80))
    speedgrade_timings = {
        "3200": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=15, tRFC=trfc, tFAW=10, tRAS=32),
    }
    speedgrade_timings["default"] = speedgrade_timings["3200"]

class HMA84GR7DJR4N(HMA82GR7DJR4N): pass
    # This module is similar to HMA82GR7DJR4N, with the exception that it is a dual-rank module. The rank number
    # can be specified in the PHY settings.

class M393A2K40DB3(DDR4RegisteredModule):
    # geometry
    ngroupbanks = 4
    ngroups     = 4
    nbanks      = ngroups * ngroupbanks
    nrows       = 131072
    ncols       = 1024
    # timings
    trefi = {"1x": 64e6/8192,   "2x": (64e6/8192)/2, "4x": (64e6/8192)/4}
    trfc  = {"1x": (None, 350), "2x": (None, 260),   "4x": (None, 160)}
    technology_timings = _TechnologyTimings(tREFI=trefi, tWTR=(4, 7.5), tCCD=(4, 5), tRRD=(4, 4.9), tZQCS=(128, 80))
    speedgrade_timings = {
        "3200": _SpeedgradeTimings(tRP=13.75, tRCD=13.75, tWR=15, tRFC=trfc, tFAW=10, tRAS=32),
    }
    speedgrade_timings["default"] = speedgrade_timings["3200"]

class M393A4K40DB3(M393A2K40DB3): pass
    # This module is similar to M393A2K40DB3, with the exception that it is a dual-rank module. The rank number
    # can be specified in the PHY settings.

# LPDDR4 -------------------------------------------------------------------------------------------

class MT53E256M16D1(SDRAMModule):
    memtype = "LPDDR4"

    nbanks = 8
    nrows = 32768
    ncols = 1024

    # TODO: find a way to select if we need masked writes
    tccd = {"write": (8, None), "masked-write": (32, None)}

    # TODO: tZQCS - performing ZQC during runtime will require modifying Refresher, as ZQC has to be done in 2 phases
    # 1. ZQCAL START is issued 2. ZQCAL LATCH updates the values, the time START->LATCH tZQCAL=1us, so we cannot block
    # the controller during this time, after ZQCAL LATCH we have to wait tZQLAT=max(8ck, 30ns)
    technology_timings = _TechnologyTimings(tREFI=32e6/8192, tWTR=(8, 10), tCCD=tccd["masked-write"], tRRD=(4, 10), tZQCS=None)
    speedgrade_timings = {
        "1866": _SpeedgradeTimings(tRP=(3, 21), tRCD=(4, 18), tWR=(4, 18), tRFC=180, tFAW=40, tRAS=(3, 42)),  # TODO: tRAS_max
    }
    speedgrade_timings["default"] = speedgrade_timings["1866"]
