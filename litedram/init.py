#
# This file is part of LiteDRAM.
#
# Copyright (c) 2013-2014 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2013-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2017 whitequark <whitequark@whitequark.org>
# Copyright (c) 2014 Yann Sionneau <ys@m-labs.hk>
# Copyright (c) 2018 bunnie <bunnie@kosagi.com>
# Copyright (c) 2019 Gabriel L. Somlo <gsomlo@gmail.com>
# Copyright (c) 2020-2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import math
from contextlib import contextmanager

from migen import *

cmds = {
    "PRECHARGE_ALL": "DFII_COMMAND_RAS|DFII_COMMAND_WE|DFII_COMMAND_CS",
    "MODE_REGISTER": "DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS",
    "AUTO_REFRESH":  "DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_CS",
    "UNRESET":       "DFII_CONTROL_ODT|DFII_CONTROL_RESET_N",
    "CKE":           "DFII_CONTROL_CKE|DFII_CONTROL_ODT|DFII_CONTROL_RESET_N"
}

# Swap two bits in num
# https://www.techiedelight.com/swap-two-bits-given-position-integer/
def swap_bit(num, a, b):
    if ((num >> a) & 1) != ((num >> b) & 1):
        num = num ^ (1 << a)
        num = num ^ (1 << b)
    return num

def reg(fields):
    # takes a list of tuples: [(bit_offset, bit_width, value), ...]
    regval = 0
    written = 0
    for shift, width, val in fields:
        mask = (2**width - 1) << shift
        assert written & mask == 0, "Would overwrite another field, xor=0b{:032b}".format(mask ^ written)
        assert val < 2**width, "Value larger than field width: val={}, width={}".format(val, width)
        regval |= (val << shift) & mask
        written |= mask
    return regval

# SDR ----------------------------------------------------------------------------------------------

def get_sdr_phy_init_sequence(phy_settings, timing_settings):
    cl = phy_settings.cl
    bl = phy_settings.nphases
    mr = log2_int(bl) + (cl << 4)
    reset_dll = 1 << 8

    init_sequence = [
        ("Bring CKE high", 0x0000, 0, cmds["CKE"], 20000),
        ("Precharge All",  0x0400, 0, cmds["PRECHARGE_ALL"], 0),
        ("Load Mode Register / Reset DLL, CL={0:d}, BL={1:d}".format(cl, bl), mr + reset_dll, 0, cmds["MODE_REGISTER"], 200),
        ("Precharge All", 0x0400, 0, cmds["PRECHARGE_ALL"], 0),
        ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
        ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
        ("Load Mode Register / CL={0:d}, BL={1:d}".format(cl, bl), mr, 0, cmds["MODE_REGISTER"], 200)
    ]

    return init_sequence, None

# DDR ----------------------------------------------------------------------------------------------

def get_ddr_phy_init_sequence(phy_settings, timing_settings):
    cl  = phy_settings.cl
    bl  = 4
    mr  = log2_int(bl) + (cl << 4)
    emr = 0
    reset_dll = 1 << 8

    init_sequence = [
        ("Bring CKE high", 0x0000, 0, cmds["CKE"], 20000),
        ("Precharge All",  0x0400, 0, cmds["PRECHARGE_ALL"], 0),
        ("Load Extended Mode Register", emr, 1, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register / Reset DLL, CL={0:d}, BL={1:d}".format(cl, bl), mr + reset_dll, 0, cmds["MODE_REGISTER"], 200),
        ("Precharge All", 0x0400, 0, cmds["PRECHARGE_ALL"], 0),
        ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
        ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
        ("Load Mode Register / CL={0:d}, BL={1:d}".format(cl, bl), mr, 0, cmds["MODE_REGISTER"], 200)
    ]

    return init_sequence, None

# LPDDR --------------------------------------------------------------------------------------------

def get_lpddr_phy_init_sequence(phy_settings, timing_settings):
    cl  = phy_settings.cl
    bl  = 4
    mr  = log2_int(bl) + (cl << 4)
    emr = 0
    reset_dll = 1 << 8

    init_sequence = [
        ("Bring CKE high", 0x0000, 0, cmds["CKE"], 20000),
        ("Precharge All",  0x0400, 0, cmds["PRECHARGE_ALL"], 0),
        ("Load Extended Mode Register", emr, 2, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register / Reset DLL, CL={0:d}, BL={1:d}".format(cl, bl), mr + reset_dll, 0, cmds["MODE_REGISTER"], 200),
        ("Precharge All", 0x0400, 0, cmds["PRECHARGE_ALL"], 0),
        ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
        ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
        ("Load Mode Register / CL={0:d}, BL={1:d}".format(cl, bl), mr, 0, cmds["MODE_REGISTER"], 200)
    ]

    return init_sequence, None

# DDR2 ---------------------------------------------------------------------------------------------

def get_ddr2_phy_init_sequence(phy_settings, timing_settings):
    cl   = phy_settings.cl
    bl   = 4
    wr   = 2
    mr   = log2_int(bl) + (cl << 4) + (wr << 9)
    emr  = 0
    emr2 = 0
    emr3 = 0
    ocd  = 7 << 7
    reset_dll = 1 << 8

    init_sequence = [
        ("Bring CKE high", 0x0000, 0, cmds["CKE"], 20000),
        ("Precharge All",  0x0400, 0, cmds["PRECHARGE_ALL"], 0),
        ("Load Extended Mode Register 3", emr3, 3, cmds["MODE_REGISTER"], 0),
        ("Load Extended Mode Register 2", emr2, 2, cmds["MODE_REGISTER"], 0),
        ("Load Extended Mode Register", emr, 1, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register / Reset DLL, CL={0:d}, BL={1:d}".format(cl, bl), mr + reset_dll, 0, cmds["MODE_REGISTER"], 200),
        ("Precharge All", 0x0400, 0, cmds["PRECHARGE_ALL"], 0),
        ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
        ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
        ("Load Mode Register / CL={0:d}, BL={1:d}".format(cl, bl), mr, 0, cmds["MODE_REGISTER"], 200),
        ("Load Extended Mode Register / OCD Default", emr+ocd, 1, cmds["MODE_REGISTER"], 0),
        ("Load Extended Mode Register / OCD Exit", emr, 1, cmds["MODE_REGISTER"], 0),
    ]

    return init_sequence, None

# DDR3 ---------------------------------------------------------------------------------------------

def get_ddr3_phy_init_sequence(phy_settings, timing_settings):
    cl  = phy_settings.cl
    bl  = 8
    cwl = phy_settings.cwl

    def format_mr0(bl, cl, wr, dll_reset):
        bl_to_mr0 = {
            4: 0b10,
            8: 0b00
        }
        cl_to_mr0 = {
             5: 0b0010,
             6: 0b0100,
             7: 0b0110,
             8: 0b1000,
             9: 0b1010,
            10: 0b1100,
            11: 0b1110,
            12: 0b0001,
            13: 0b0011,
            14: 0b0101
        }
        wr_to_mr0 = {
            16: 0b000,
             5: 0b001,
             6: 0b010,
             7: 0b011,
             8: 0b100,
            10: 0b101,
            12: 0b110,
            14: 0b111
        }
        mr0 = bl_to_mr0[bl]
        mr0 |= (cl_to_mr0[cl] & 1) << 2
        mr0 |= ((cl_to_mr0[cl] >> 1) & 0b111) << 4
        mr0 |= dll_reset << 8
        mr0 |= wr_to_mr0[wr] << 9
        return mr0

    def format_mr1(ron, rtt_nom, tdqs):
        mr1 = ((ron >> 0) & 1) << 1
        mr1 |= ((ron >> 1) & 1) << 5
        mr1 |= ((rtt_nom >> 0) & 1) << 2
        mr1 |= ((rtt_nom >> 1) & 1) << 6
        mr1 |= ((rtt_nom >> 2) & 1) << 9
        mr1 |= (tdqs & 1) << 11
        return mr1

    def format_mr2(cwl, rtt_wr):
        mr2 = (cwl-5) << 3
        mr2 |= rtt_wr << 9
        return mr2

    z_to_rtt_nom = {
        "disabled" : 0,
        "60ohm"    : 1,
        "120ohm"   : 2,
        "40ohm"    : 3,
        "20ohm"    : 4,
        "30ohm"    : 5
    }

    z_to_rtt_wr = {
        "disabled" : 0,
        "60ohm"    : 1,
        "120ohm"   : 2,
    }

    z_to_ron = {
        "40ohm" : 0,
        "34ohm" : 1,
    }

    # Get Electrical Settings (or use default: Point to Point).
    rtt_nom = getattr(phy_settings, "rtt_nom", "60ohm")
    rtt_wr  = getattr(phy_settings, "rtt_wr",  "60ohm")
    ron     = getattr(phy_settings, "ron",     "34ohm")
    tdqs    = getattr(phy_settings, "tdqs",    0)

    wr  = max(timing_settings.tWTR*phy_settings.nphases, 5) # >= ceiling(tWR/tCK)
    mr0 = format_mr0(bl, cl, wr, 1)
    mr1 = format_mr1(z_to_ron[ron], z_to_rtt_nom[rtt_nom], tdqs)
    mr2 = format_mr2(cwl, z_to_rtt_wr[rtt_wr])
    mr3 = 0

    init_sequence = [
        ("Release reset", 0x0000, 0, cmds["UNRESET"], 50000),
        ("Bring CKE high", 0x0000, 0, cmds["CKE"], 10000),
        ("Load Mode Register 2, CWL={0:d}".format(cwl), mr2, 2, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 3", mr3, 3, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 1", mr1, 1, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 0, CL={0:d}, BL={1:d}".format(cl, bl), mr0, 0, cmds["MODE_REGISTER"], 200),
        ("ZQ Calibration", 0x0400, 0, "DFII_COMMAND_WE|DFII_COMMAND_CS", 200),
    ]

    return init_sequence, {1: mr1}

# RPC ----------------------------------------------------------------------------------------------

def get_rpc_phy_init_sequence(phy_settings, timing_settings):
    from litedram.phy.rpc.commands import ModeRegister

    assert phy_settings.cl == phy_settings.cwl
    # subtract that +1 always added for AL
    cl  = phy_settings.cl - 1

    nwr = 8
    zout = 60
    odt = 30
    odt_stb = 1  # disable ODT on STB
    csr_fx = 0  # do not use loop refresh mode
    odt_pd = 0  # ODT during PD disabled by DRAM

    mr_a, mr_ba = ModeRegister.dfi_encode(
        cl      = ModeRegister.CL[cl],
        nwr     = ModeRegister.NWR[nwr],
        zout    = ModeRegister.ZOUT[zout],
        odt     = ModeRegister.ODT[odt],
        csr_fx  = csr_fx,
        odt_stb = odt_stb,
        odt_pd  = odt_pd,
    )

    def ck(sec):
        # FIXME: use sys_clk_freq (should be added e.g. to TimingSettings), using arbitrary value for now
        fmax = 200e6
        return int(math.ceil(sec * fmax))

    init_sequence = [
        # Apply power, stabilize clocks for 200us, CS# and STB should be high
        ("Stabilize clocks", 0x0000, 0, cmds["UNRESET"], ck(200e-6)),
        # Send CS# low once, to make PHY start holding it all the time
        ("Hold CS# low", 0x0000, 0, "DFII_COMMAND_CS", ck(100e-9)),
        # Enter PU RESET, by issuing ACT with reset_n=0, PHY will perform the reset sequence
        ("RPC special commands: ON", 0x0000, 0, "DFII_CONTROL_ODT", ck(100e-9)),
        ("PU RESET sequence (ACT)", 0x0000, 0, "DFII_COMMAND_RAS|DFII_COMMAND_CS", ck(5e-6)),
        ("RPC special commands: OFF", 0x0000, 0, cmds["UNRESET"], ck(100e-9)),
        # Setup mode register
        ("Precharge ALL", 0x0400, 0, cmds["PRECHARGE_ALL"], ck(100e-9)),
        ("Load Mode Register: CL={}".format(cl), mr_a, mr_ba, cmds["MODE_REGISTER"], ck(100e-9)),
        # ZQ Calibration (ZQ LONG will be translated to RPC ZQ INIT by PHY)
        ("RPC special commands: ON", 0x0000, 0, "DFII_CONTROL_ODT", ck(100e-9)),
        ("ZQ Init Calibration", 0x0400, 0, "DFII_COMMAND_WE|DFII_COMMAND_CS", ck(1e-6)),
        ("RPC special commands: OFF", 0x0000, 0, cmds["UNRESET"], ck(100e-9)),
    ]

    return init_sequence, None

# DDR4 ---------------------------------------------------------------------------------------------

def get_ddr4_phy_init_sequence(phy_settings, timing_settings):
    cl  = phy_settings.cl
    bl  = 8
    cwl = phy_settings.cwl

    def format_mr0(bl, cl, wr, dll_reset):
        bl_to_mr0 = {
            4: 0b10,
            8: 0b00
        }
        cl_to_mr0 = {
             9: 0b00000,
            10: 0b00001,
            11: 0b00010,
            12: 0b00011,
            13: 0b00100,
            14: 0b00101,
            15: 0b00110,
            16: 0b00111,
            18: 0b01000,
            20: 0b01001,
            22: 0b01010,
            24: 0b01011,
            23: 0b01100,
            17: 0b01101,
            19: 0b01110,
            21: 0b01111,
            25: 0b10000,
            26: 0b10001,
            27: 0b10010,
            28: 0b10011,
            29: 0b10100,
            30: 0b10101,
            31: 0b10110,
            32: 0b10111,
        }
        wr_to_mr0 = {
            10: 0b0000,
            12: 0b0001,
            14: 0b0010,
            16: 0b0011,
            18: 0b0100,
            20: 0b0101,
            24: 0b0110,
            22: 0b0111,
            26: 0b1000,
            28: 0b1001,
        }
        mr0 = bl_to_mr0[bl]
        mr0 |= (cl_to_mr0[cl] & 0b1) << 2
        mr0 |= ((cl_to_mr0[cl] >> 1) & 0b111) << 4
        mr0 |= ((cl_to_mr0[cl] >> 4) & 0b1) << 12
        mr0 |= dll_reset << 8
        mr0 |= (wr_to_mr0[wr] & 0b111) << 9
        mr0 |= (wr_to_mr0[wr] >> 3) << 13
        return mr0

    def format_mr1(dll_enable, ron, rtt_nom, tdqs):
        mr1 = dll_enable
        mr1 |= ((ron >> 0) & 0b1) << 1
        mr1 |= ((ron >> 1) & 0b1) << 2
        mr1 |= ((rtt_nom >> 0) & 0b1) << 8
        mr1 |= ((rtt_nom >> 1) & 0b1) << 9
        mr1 |= ((rtt_nom >> 2) & 0b1) << 10
        mr1 |= (tdqs & 0b1) << 11
        return mr1

    def format_mr2(cwl, rtt_wr):
        cwl_to_mr2 = {
             9: 0b000,
            10: 0b001,
            11: 0b010,
            12: 0b011,
            14: 0b100,
            16: 0b101,
            18: 0b110,
            20: 0b111
        }
        mr2 = cwl_to_mr2[cwl] << 3
        mr2 |= rtt_wr << 9
        return mr2

    def format_mr3(fine_refresh_mode):
        fine_refresh_mode_to_mr3 = {
            "1x": 0b000,
            "2x": 0b001,
            "4x": 0b010
        }
        mr3 = fine_refresh_mode_to_mr3[fine_refresh_mode] << 6
        return mr3

    def format_mr6(tccd):
        tccd_to_mr6 = {
            4: 0b000,
            5: 0b001,
            6: 0b010,
            7: 0b011,
            8: 0b100
        }
        mr6 = tccd_to_mr6[tccd] << 10
        return mr6

    z_to_rtt_nom = {
        "disabled" : 0b000,
        "60ohm"    : 0b001,
        "120ohm"   : 0b010,
        "40ohm"    : 0b011,
        "240ohm"   : 0b100,
        "48ohm"    : 0b101,
        "80ohm"    : 0b110,
        "34ohm"    : 0b111
    }

    z_to_rtt_wr = {
        "disabled" : 0b000,
        "120ohm"   : 0b001,
        "240ohm"   : 0b010,
        "high-z"   : 0b011,
        "80ohm"    : 0b100,
    }

    z_to_ron = {
        "34ohm" : 0b00,
        "48ohm" : 0b01,
    }

    # Get Electrical Settings (or use default: Point to Point).
    rtt_nom = getattr(phy_settings, "rtt_nom", "40ohm")
    rtt_wr  = getattr(phy_settings, "rtt_wr",  "120ohm")
    ron     = getattr(phy_settings, "ron",     "34ohm")
    tdqs    = getattr(phy_settings, "tdqs",    0)
    dm      = 1
    assert not (dm and tdqs)

    wr  = max(timing_settings.tWTR*phy_settings.nphases, 10) # >= ceiling(tWR/tCK)
    mr0 = format_mr0(bl, cl, wr, 1)
    mr1 = format_mr1(1, z_to_ron[ron], z_to_rtt_nom[rtt_nom], tdqs)
    mr2 = format_mr2(cwl, z_to_rtt_wr[rtt_wr])
    mr3 = format_mr3(timing_settings.fine_refresh_mode)
    mr4 = 0
    mr5 = (dm << 10)
    mr6 = format_mr6(4) # FIXME: tCCD

    rdimm_init = []
    if phy_settings.is_rdimm:
        def get_coarse_speed(tck, pll_bypass):
            # JESD82-31A page 78
            f_to_coarse_speed = {
                1600e6: 0,
                1866e6: 1,
                2133e6: 2,
                2400e6: 3,
                2666e6: 4,
                2933e6: 5,
                3200e6: 6,
            }
            if pll_bypass:
                return 7
            else:
                for f, speed in f_to_coarse_speed.items():
                        if tck >= 2/f:
                            return speed
                raise ValueError
        def get_fine_speed(tck):
            # JESD82-31A page 83
            freq = 2/tck
            fine_speed = int((freq - 1240e6) // 20e6)
            fine_speed = max(fine_speed, 0)
            fine_speed = min(fine_speed, 0b1100001)
            return fine_speed

        coarse_speed = get_coarse_speed(phy_settings.tck, phy_settings.rcd_pll_bypass)
        fine_speed = get_fine_speed(phy_settings.tck)

        rcd_reset = 0x060 | 0x0                          # F0RC06: command space control; 0: reset RCD

        f0rc0f = 0x0F0 | 0x4                             # F0RC05: 0 nCK latency adder

        f0rc03 = 0x030 | phy_settings.rcd_ca_cs_drive    # F0RC03: CA/CS drive strength
        f0rc04 = 0x040 | phy_settings.rcd_odt_cke_drive  # F0RC04: ODT/CKE drive strength
        f0rc05 = 0x050 | phy_settings.rcd_clk_drive      # F0RC04: ODT/CKE drive strength
        f0rc0d = 0x0D0 | 0x4                             # F0RC0D: DIMM configration; 4: Direct DualCS RDIMM

        f0rc0a = 0x0A0 | coarse_speed                    # F0RC0A: coarse speed selection and PLL bypass
        f0rc3x = 0x300 | fine_speed                      # F0RC3x: fine speed selection

        rdimm_init = [
            ("Reset RCD", rcd_reset, 7, cmds["MODE_REGISTER"], 50000),
            ("Load RCD F0RC0F", f0rc0f, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC03", f0rc03, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC04", f0rc04, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC05", f0rc05, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC0D", f0rc0d, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC0A", f0rc0a, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC3X", f0rc3x, 7, cmds["MODE_REGISTER"], 100),
        ]

    init_sequence = [
        ("Release reset", 0x0000, 0, cmds["UNRESET"], 50000),
        ("Bring CKE high", 0x0000, 0, cmds["CKE"], 10000),
    ] + rdimm_init + [
        ("Load Mode Register 3", mr3, 3, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 6", mr6, 6, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 5", mr5, 5, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 4", mr4, 4, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 2, CWL={0:d}".format(cwl), mr2, 2, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 1", mr1, 1, cmds["MODE_REGISTER"], 0),
        ("Load Mode Register 0, CL={0:d}, BL={1:d}".format(cl, bl), mr0, 0, cmds["MODE_REGISTER"], 200),
        ("ZQ Calibration", 0x0400, 0, "DFII_COMMAND_WE|DFII_COMMAND_CS", 200),
    ]

    return init_sequence, {1: mr1}

# LPDDR4 -------------------------------------------------------------------------------------------

def get_lpddr4_phy_init_sequence(phy_settings, timing_settings):
    cl = phy_settings.cl
    cwl = phy_settings.cwl
    bl = 16
    dq_odt = getattr(phy_settings, "dq_odt", "RZQ/2")
    ca_odt = getattr(phy_settings, "ca_odt", "RZQ/2")
    pull_down_drive_strength = getattr(phy_settings, "pull_down_drive_strength", "RZQ/2")
    vref_ca_range = getattr(phy_settings, "vref_ca_range", 1)
    vref_ca = getattr(phy_settings, "vref_ca", 30.4)
    vref_dq_range = getattr(phy_settings, "vref_dq_range", 1)
    vref_dq = getattr(phy_settings, "vref_dq", 30.4)

    def get_nwr():
        frequency_ranges = [  # Table 28. Frequency Ranges for RL, WL, nWR, and nRTP Settings
            # RL (DBI)   WL (set)  nWR nRTP  frequency
            # w/o  w/    A   B               >     <=
            [( 6,  6),  ( 4,  4),   6,  8,  (  10,  266)],
            [(10, 12),  ( 6,  8),  10,  8,  ( 266,  533)],
            [(14, 16),  ( 8, 12),  16,  8,  ( 533,  800)],
            [(20, 22),  (10, 18),  20,  8,  ( 800, 1066)],
            [(24, 28),  (12, 22),  24, 10,  (1066, 1333)],
            [(28, 32),  (14, 26),  30, 12,  (1333, 1600)],
            [(32, 36),  (16, 30),  34, 14,  (1600, 1866)],
            [(36, 40),  (18, 34),  40, 16,  (1866, 2133)],
        ]
        # We use no DBI and WL set A
        for (rl, _), (wl, _), nwr, nrtp, (fmin, fmax) in frequency_ranges:
            if rl == cl:
                assert wl == cwl, "Wrong (RL, WL) combination"
                return nwr

    nwr = get_nwr()

    odt_map = {
        "disable": 0b000,
        "RZQ/1":   0b001,
        "RZQ/2":   0b010,
        "RZQ/3":   0b011,
        "RZQ/4":   0b100,
        "RZQ/5":   0b101,
        "RZQ/6":   0b110,
    }

    # Table 215: VREF Setting for Range[0] and Range[1] (LPDDR4 1.10V VDDQ)
    # vref_ranges[range][percent_vddx]
    vref_ranges = {
        0: {
            10.0: 0b000000, 10.4: 0b000001, 10.8: 0b000010, 11.2: 0b000011, 11.6: 0b000100,
            12.0: 0b000101, 12.4: 0b000110, 12.8: 0b000111, 13.2: 0b001000, 13.6: 0b001001,
            14.0: 0b001010, 14.4: 0b001011, 14.8: 0b001100, 15.2: 0b001101, 15.6: 0b001110,
            16.0: 0b001111, 16.4: 0b010000, 16.8: 0b010001, 17.2: 0b010010, 17.6: 0b010011,
            18.0: 0b010100, 18.4: 0b010101, 18.8: 0b010110, 19.2: 0b010111, 19.6: 0b011000,
            20.0: 0b011001, 20.4: 0b011010, 20.8: 0b011011, 21.2: 0b011100, 21.6: 0b011101,
            22.0: 0b011110, 22.4: 0b011111, 22.8: 0b100000, 23.2: 0b100001, 23.6: 0b100010,
            24.0: 0b100011, 24.4: 0b100100, 24.8: 0b100101, 25.2: 0b100110, 25.6: 0b100111,
            26.0: 0b101000, 26.4: 0b101001, 26.8: 0b101010, 27.2: 0b101011, 27.6: 0b101100,
            28.0: 0b101101, 28.4: 0b101110, 28.8: 0b101111, 29.2: 0b110000, 29.6: 0b110001,
            30.0: 0b110010,
        },
        1: {
            22.0: 0b000000, 22.4: 0b000001, 22.8: 0b000010, 23.2: 0b000011, 23.6: 0b000100,
            24.0: 0b000101, 24.4: 0b000110, 24.8: 0b000111, 25.2: 0b001000, 25.6: 0b001001,
            26.0: 0b001010, 26.4: 0b001011, 26.8: 0b001100, 27.2: 0b001101, 27.6: 0b001110,
            28.0: 0b001111, 28.4: 0b010000, 28.8: 0b010001, 29.2: 0b010010, 29.6: 0b010011,
            30.0: 0b010100, 30.4: 0b010101, 30.8: 0b010110, 31.2: 0b010111, 31.6: 0b011000,
            32.0: 0b011001, 32.4: 0b011010, 32.8: 0b011011, 33.2: 0b011100, 33.6: 0b011101,
            34.0: 0b011110, 34.4: 0b011111, 34.8: 0b100000, 35.2: 0b100001, 35.6: 0b100010,
            36.0: 0b100011, 36.4: 0b100100, 36.8: 0b100101, 37.2: 0b100110, 37.6: 0b100111,
            38.0: 0b101000, 38.4: 0b101001, 38.8: 0b101010, 39.2: 0b101011, 39.6: 0b101100,
            40.0: 0b101101, 40.4: 0b101110, 40.8: 0b101111, 41.2: 0b110000, 41.6: 0b110001,
            42.0: 0b110010,
        },
    }

    mr = {}
    mr[1] = reg([
        (0, 2, {16: 0b00, 32: 0b01, "on-the-fly": 0b10}[bl]),
        (2, 1, 1),  # 2tCK WR preamble
        (3, 1, 0),  # static RD preamble
        (4, 3, {
            6:  0b000,
            10: 0b001,
            16: 0b010,
            20: 0b011,
            24: 0b100,
            30: 0b101,
            34: 0b110,
            40: 0b111,
        }[nwr]),
        (7, 1, 0),  # 0.5tCK RD postamble
    ])
    mr[2] = reg([
        (0, 3, {  # RL assuming DBI-RD disabled
            6:  0b000,
            10: 0b001,
            14: 0b010,
            20: 0b011,
            24: 0b100,
            28: 0b101,
            32: 0b110,
            36: 0b111,
        }[cl]),
        (3, 3, {  # WL, set A
            4:  0b000,
            6:  0b001,
            8:  0b010,
            10: 0b011,
            12: 0b100,
            14: 0b101,
            16: 0b110,
            18: 0b111,
        }[cwl]),
        (6, 1, 0),  # use set A
        (7, 1, 0),  # write leveling disabled
    ])
    mr[3] = reg([  # defaults
        (0, 1, 1),
        (1, 1, 0),
        (2, 1, 0),
        (3, 3, odt_map[pull_down_drive_strength]),
        (6, 1, 0),
        (7, 1, 0),
    ])
    mr[11] = reg([
        (0, 3, odt_map[dq_odt]),
        (4, 3, odt_map[ca_odt]),
    ])
    mr[12] = reg([
        (0, 6, vref_ranges[vref_ca_range][vref_ca]),  # Vref(CA) % of VDD2
        (6, 1, vref_ca_range),
    ])
    mr[14] = reg([
        (0, 6, vref_ranges[vref_dq_range][vref_dq]),  # Vref(DQ) % of VDDQ
        (6, 1, vref_dq_range),
    ])
    mr[13] = 0  # defaults (data mask enabled, frequency set point 0)

    from litedram.phy.lpddr4.commands import SpecialCmd, MPC

    def cmd_mr(ma):
        # Convert Mode Register Write command to DFI as expected by PHY
        op = mr[ma]
        assert ma < 2**6, "MR address to big: {}".format(ma)
        assert op < 2**8, "MR opcode to big: {}".format(op)
        a = op
        ba = ma
        return ("Load More Register {}".format(ma), a, ba, cmds["MODE_REGISTER"], 200)

    def ck(sec):
        # FIXME: use sys_clk_freq (should be added e.g. to TimingSettings), using arbitrary value for now
        fmax = 200e6
        return int(math.ceil(sec * fmax))

    init_sequence = [
        # Perform "Reset Initialization with Stable Power"
        # We assume that loading the bistream will take at least tINIT1 (200us)
        # Because LiteDRAM will start with reset_n=1 during hw control, first reset the chip (for tPW_RESET)
        ("Assert reset", 0x0000, 0, "DFII_CONTROL_ODT", ck(100e-9)),
        ("Release reset", 0x0000, 0, cmds["UNRESET"], ck(2e-3)),
        ("Bring CKE high", 0x0000, 0, cmds["CKE"], ck(2e-6)),
        *[cmd_mr(ma) for ma in sorted(mr.keys())],
        ("ZQ Calibration start", MPC.ZQC_START, SpecialCmd.MPC, "DFII_COMMAND_WE|DFII_COMMAND_CS", ck(1e-6)),
        ("ZQ Calibration latch", MPC.ZQC_LATCH, SpecialCmd.MPC, "DFII_COMMAND_WE|DFII_COMMAND_CS", max(8, ck(30e-9))),
    ]

    return init_sequence, mr

# LPDDR5 -------------------------------------------------------------------------------------------

def get_lpddr5_phy_init_sequence(phy_settings, timing_settings):
    from litedram.phy.lpddr5.basephy import FREQUENCY_RANGES
    from litedram.phy.lpddr5.commands import SpecialCmd, MPC, BankOrganization

    rl = phy_settings.cl
    wl = phy_settings.cwl
    wck_ck_ratio = phy_settings.wck_ck_ratio
    bl = 16
    dq_odt = getattr(phy_settings, "dq_odt", "RZQ/2")
    ca_odt = getattr(phy_settings, "dq_odt", "RZQ/2")
    pull_down_drive_strength = getattr(phy_settings, "pull_down_drive_strength", "RZQ/2")
    soc_odt = getattr(phy_settings, "soc_odt", "disable")
    wck_odt = getattr(phy_settings, "wck_odt", "disable")
    vref_ca = getattr(phy_settings, "vref_ca", 34.0)
    vref_dq = getattr(phy_settings, "vref_dq", 34.0)

    # find definitions for given wck_ck_ratio/wl/rl
    def get_frange():
        for fr in FREQUENCY_RANGES[wck_ck_ratio]:
            fr = fr.for_set(wl_set="A", rl_set=0)
            if fr.wl == wl and fr.rl == rl:
                return fr
        raise ValueError

    frange = get_frange()

    rzq_map = {
        "disable": 0b000,
        "RZQ/1":   0b001,
        "RZQ/2":   0b010,
        "RZQ/3":   0b011,
        "RZQ/4":   0b100,
        "RZQ/5":   0b101,
        "RZQ/6":   0b110,
    }

    # Both VrefCA and VrefDQ have the same mapping <10.0%, 73.5%> => <0b0000000, 0b1111111>
    def get_vref(vref_percent, testing=False):
        assert 10.0 <= vref_percent <= 73.5
        assert testing or vref_percent >= 15.0, f"Vref of {vref_percent:.2f}% (<15%) meant only for testing purpose"
        vref_percent = round(vref_percent * 2) / 2  # round to x.5
        reg = int((vref_percent - 10.0) * 2)
        assert 0 <= reg <= 0b1111111
        return reg

    mr = {}
    mr[1] = reg([
        (3, 1, 0),  # differential CK
        (4, 4, frange.mr),
    ])
    mr[2] = reg([
        (0, 4, frange.mr),  # seems that in both MR1 and MR2 we need the same value
        (4, 4, frange.n_wr_op),
    ])
    mr[3] = reg([
        (0, 3, rzq_map[pull_down_drive_strength]),
        (3, 2, BankOrganization.B16),
        (5, 1, 0),  # WL Set "A"
    ])
    mr[10] = reg([
        (0, 0, 0),  # RDQS postamble toggle mode
        (2, 2, 0b00),  # WCK postamble 2.5*tWCK
        (4, 2, 0b00),  # RDQS preamble 4*tWCK static + 0 toggle
        (6, 2, 0b00),  # RDQS postamble 0.5*tWCK
    ])
    mr[11] = reg([
        (0, 3, rzq_map[dq_odt]),
        (3, 1, 0),  # non-target ODT disabled
        (4, 3, rzq_map[ca_odt]),
    ])
    mr[12] = reg([
        (0, 7, get_vref(vref_ca)),
        (7, 1, 0),
    ])
    mr[13] = 0 # defaults, DM enabled
    mr[14] = reg([
        (0, 7, get_vref(vref_dq)),
        (7, 1, 0),
    ])
    mr[15] = get_vref(vref_dq)
    mr[17] = reg([
        (0, 3, rzq_map[soc_odt]),
        # defaults
        (3, 1, 1),
        (4, 1, 1),
        (5, 1, 1),
        (6, 1, 0),
        (7, 1, 0),
    ])
    mr[18] = reg([
        (0, 3, rzq_map[wck_odt]),
        (3, 1, 0),  # WCK low frequency mode
        (4, 1, 0),  # WCK always on mode disabled
        (6, 1, 0),  # WCK2CK leveling disabled
        (7, 1, {2: 1, 4: 0}[wck_ck_ratio]),
    ])
    # MR19 - defaults
    mr[20] = reg([
        (0, 2, 0b01),  # TODO: as we don't actually use RDQS, maybe we can just disable it
        # zero-defaults
    ])
    mr[22] = 0  # Write/read link ECC disabled
    mr[28] = reg([
        (0, 1, 0), # ZQ Reset
        (1, 1, 0), # ZQ Stop
        (2, 2, 0b01), # ZQ background calibration interval (64ms default)
        (5, 1, 0), # ZQ mode
    ])

    def cmd_mr(ma):
        # Convert Mode Register Write command to DFI as expected by PHY
        op = mr[ma]
        assert ma < 2**7, "MR address to big: {}".format(ma)
        assert op < 2**8, "MR opcode to big: {}".format(op)
        a = op
        ba = ma
        return ("Load More Register {}".format(ma), a, ba, cmds["MODE_REGISTER"], 200)

    def ck(sec):
        fmax = 200e6
        return int(math.ceil(sec * fmax))

    init_sequence = [
        ("Assert reset", 0x0000, 0, "DFII_CONTROL_ODT", ck(200e-6)),  # ??
        ("Release reset", 0x0000, 0, cmds["UNRESET"], ck(2e-3) + 5),
        ("Toggle CS", 0, SpecialCmd.NOP, "DFII_COMMAND_WE|DFII_COMMAND_CS", ck(2e-6)),
        *[cmd_mr(ma) for ma in sorted(mr.keys())],
        ("ZQ Calibration latch", MPC.ZQC_LATCH, SpecialCmd.MPC, "DFII_COMMAND_WE|DFII_COMMAND_CS", max(4, ck(30e-9))),
    ]

    return init_sequence, mr

# Init Sequence ------------------------------------------------------------------------------------

def get_sdram_phy_init_sequence(phy_settings, timing_settings):
    return {
        "SDR":    get_sdr_phy_init_sequence,
        "DDR":    get_ddr_phy_init_sequence,
        "LPDDR":  get_lpddr_phy_init_sequence,
        "DDR2":   get_ddr2_phy_init_sequence,
        "DDR3":   get_ddr3_phy_init_sequence,
        "RPC":    get_rpc_phy_init_sequence,
        "DDR4":   get_ddr4_phy_init_sequence,
        "LPDDR4": get_lpddr4_phy_init_sequence,
        "LPDDR5": get_lpddr5_phy_init_sequence,
    }[phy_settings.memtype](phy_settings, timing_settings)

# C Header -----------------------------------------------------------------------------------------

class CGenerator(list):
    # C code generator - list of strings (=lines) or CGenerator instances (sub-generators)
    def __init__(self, indent=0, indent_str="\t"):
        self.indent = indent
        self.indent_str = indent_str

    def __iadd__(self, x):
        # make `c += "int x = 0;"` append it as line, not char-by-char
        if isinstance(x, str):
            x = [x]
        return super().__iadd__(x)

    def header_guard(self, name):
        self._header_guard = name

    def generate_lines(self):
        if getattr(self, "_header_guard", None) is not None:
            self.insert(0, f"#ifndef {self._header_guard}")
            self.insert(1, f"#define {self._header_guard}")
            self.insert(2, "")
            self.append("")
            self.append(f"#endif /* {self._header_guard} */")
            self._header_guard = None
        lines = []
        for entry in self:
            if isinstance(entry, CGenerator):
                lines.extend(entry.generate_lines())
            else:
                line = (self.indent * self.indent_str) + entry
                lines.append(line.rstrip())
        return lines

    def generate(self):
        lines = self.generate_lines()
        return "\n".join(lines).strip() + "\n"

    def include(self, path):
        self.append(f"#include {path}")

    def define(self, var, value=None):
        if isinstance(value, (int, float)):
            value = str(value)
        self.append(f"#define {var}" + (f" {value}" if value is not None else ""))

    def newline(self, n=1):
        self.extend([""] * n)

    @contextmanager
    def block(self, head=None, newline=True):
        if head is not None:
            self.append(head + (" {" if not newline else ""))
            if newline:
                self.append("{")
        else:
            self.append("{")
        subgenerator = CGenerator(indent=self.indent + 1, indent_str=self.indent_str)
        yield subgenerator
        self.append(subgenerator)
        self.append("}")


def get_sdram_phy_c_header(phy_settings, timing_settings, geom_settings):
    r = CGenerator()
    r.header_guard("__GENERATED_SDRAM_PHY_H")
    r.include("<hw/common.h>")
    r.include("<generated/csr.h>")
    r.newline()

    r.define("DFII_CONTROL_SEL",     "0x01")
    r.define("DFII_CONTROL_CKE",     "0x02")
    r.define("DFII_CONTROL_ODT",     "0x04")
    r.define("DFII_CONTROL_RESET_N", "0x08")
    r.newline()

    r.define("DFII_COMMAND_CS",     "0x01")
    r.define("DFII_COMMAND_WE",     "0x02")
    r.define("DFII_COMMAND_CAS",    "0x04")
    r.define("DFII_COMMAND_RAS",    "0x08")
    r.define("DFII_COMMAND_WRDATA", "0x10")
    r.define("DFII_COMMAND_RDDATA", "0x20")
    if phy_settings.is_clam_shell:
        r.define("DFII_COMMAND_CS_TOP",  "0x40")
        r.define("DFII_COMMAND_CS_BOTTOM",  "0x80")
    r.newline()

    phytype = phy_settings.phytype.upper()
    nphases = phy_settings.nphases

    # Define PHY type and number of phases
    r.define(f"SDRAM_PHY_{phytype}")
    r.define("SDRAM_PHY_XDR", 1 if phy_settings.memtype == "SDR" else 2)
    r.define("SDRAM_PHY_DATABITS", phy_settings.databits)
    r.define("SDRAM_PHY_DFI_DATABITS", phy_settings.dfi_databits)
    r.define("SDRAM_PHY_PHASES", nphases)
    for setting in ["cl", "cwl", "cmd_latency", "cmd_delay"]:
        if getattr(phy_settings, setting, None) is not None:
            r.define(f"SDRAM_PHY_{setting.upper()}", getattr(phy_settings, setting))

    # Define PHY Read.Write phases
    rdphase = phy_settings.rdphase
    if isinstance(rdphase, Signal): rdphase = rdphase.reset.value
    r.define("SDRAM_PHY_RDPHASE", rdphase)
    wrphase = phy_settings.wrphase
    if isinstance(wrphase, Signal): wrphase = wrphase.reset.value
    r.define("SDRAM_PHY_WRPHASE", wrphase)

    # Define Read/Write Leveling capability
    if phy_settings.write_leveling:
        r.define("SDRAM_PHY_WRITE_LEVELING_CAPABLE")
    if phy_settings.write_latency_calibration:
        r.define("SDRAM_PHY_WRITE_LATENCY_CALIBRATION_CAPABLE")
    if phy_settings.write_dq_dqs_training:
        r.define("SDRAM_PHY_WRITE_DQ_DQS_TRAINING_CAPABLE")
    if phy_settings.read_leveling:
        r.define("SDRAM_PHY_READ_LEVELING_CAPABLE")

    # Define DQ / DQS ratio
    r.define("SDRAM_PHY_DQ_DQS_RATIO", phy_settings.databits // phy_settings.strobes)

    # Define number of modules/delays/bitslips
    r.define("SDRAM_PHY_MODULES", phy_settings.strobes)
    if phy_settings.delays > 0:
        r.define("SDRAM_PHY_DELAYS", phy_settings.delays)
    if phy_settings.bitslips > 0:
        r.define("SDRAM_PHY_BITSLIPS", phy_settings.bitslips)

    r.define(f"SDRAM_PHY_{phy_settings.memtype}")
    if phy_settings.is_rdimm:
        assert phy_settings.memtype == "DDR4"
        r.define("SDRAM_PHY_DDR4_RDIMM")
    if phy_settings.is_clam_shell:
        assert phy_settings.memtype == "DDR4"
        r.define("SDRAM_PHY_CLAM_SHELL")

    # Define memory size.
    supported_memory = 2**(geom_settings.bankbits +
                           geom_settings.rowbits +
                           geom_settings.colbits)*phy_settings.nranks*phy_settings.databits//8
    r.define("SDRAM_PHY_SUPPORTED_MEMORY", f"0x{supported_memory:016x}ULL")

    r.newline()

    r += "void cdelay(int i);"
    r.newline()

    # Commands functions
    for n in range(nphases):
        with r.block(f"__attribute__((unused)) static inline void command_p{n}(int cmd)") as b:
            b += f"sdram_dfii_pi{n}_command_write(cmd);"
            b += f"sdram_dfii_pi{n}_command_issue_write(1);"
    r.newline()

    # Write/Read functions
    r.define("DFII_PIX_DATA_SIZE", "CSR_SDRAM_DFII_PI0_WRDATA_SIZE")
    r.newline()
    for data in ["wrdata", "rddata"]:
        with r.block(f"static inline unsigned long sdram_dfii_pix_{data}_addr(int phase)") as b:
            with b.block("switch (phase)", newline=False) as s:
                for n in range(nphases):
                    s += f"case {n}: return CSR_SDRAM_DFII_PI{n}_{data.upper()}_ADDR;"
                s += "default: return 0;"
    r.newline()

    init_sequence, mr = get_sdram_phy_init_sequence(phy_settings, timing_settings)

    if phy_settings.memtype in ["DDR3", "DDR4"]:
        # The value of MR1[7] needs to be modified during write leveling
        r.define("DDRX_MR_WRLVL_ADDRESS", 1)
        r.define("DDRX_MR_WRLVL_RESET", mr[1])
        r.define("DDRX_MR_WRLVL_BIT", 7)
        r.newline()
    elif phy_settings.memtype in ["LPDDR4"]:
        # Write leveling enabled by MR2[7]
        r.define("DDRX_MR_WRLVL_ADDRESS", 2)
        r.define("DDRX_MR_WRLVL_RESET", mr[2])
        r.define("DDRX_MR_WRLVL_BIT", 7)
        r.newline()
    elif phy_settings.memtype in ["LPDDR5"]:
        # Write leveling enabled by MR18[6]
        r.define("DDRX_MR_WRLVL_ADDRESS", 18)
        r.define("DDRX_MR_WRLVL_RESET", mr[18])
        r.define("DDRX_MR_WRLVL_BIT", 6)
        r.newline()

    with r.block("static inline void init_sequence(void)") as b:
        for comment, a, ba, cmd, delay in init_sequence:
            invert_masks = [(0, 0), ]
            if phy_settings.is_rdimm:
                assert phy_settings.memtype == "DDR4"
                # JESD82-31A page 38
                #
                # B-side chips have certain usually-inconsequential address and BA
                # bits inverted by the RCD to reduce SSO current. For mode register
                # writes, however, we must compensate for this. BG[1] also directs
                # writes either to the A side (BG[1]=0) or B side (BG[1]=1)
                #
                # The 'ba != 7' is because we don't do this to writes to the RCD
                # itself.
                if ba != 7:
                    invert_masks.append((0b10101111111000, 0b1111))

            for a_inv, ba_inv in invert_masks:
                # handle clam shell topology
                if cmd == cmds["MODE_REGISTER"] and phy_settings.is_clam_shell:
                    b += f"/* {comment} for top */"
                    b += f"sdram_dfii_pi0_address_write({a ^ a_inv:#x});"
                    b += f"sdram_dfii_pi0_baddress_write({ba ^ ba_inv:d});"
                    b += f"command_p0({cmd}|DFII_COMMAND_CS_TOP);"
                    if delay:
                        b += f"cdelay({delay});\n"
                    b.newline()

                    # swap addr and pass to bottom
                    b += f"/* {comment} for bottom */"
                    addr = a ^ a_inv
                    addr = swap_bit(addr, 3, 4)
                    addr = swap_bit(addr, 5, 6)
                    addr = swap_bit(addr, 7, 8)
                    addr = swap_bit(addr, 11, 13)
                    b += f"sdram_dfii_pi0_address_write({addr:#x});"
                    baddr = ba ^ ba_inv
                    baddr = swap_bit(baddr, 0, 1)
                    b += f"sdram_dfii_pi0_baddress_write({baddr:d});"
                    b += f"command_p0({cmd}|DFII_COMMAND_CS_BOTTOM);"
                    if delay:
                        b += f"cdelay({delay});\n"
                    b.newline()
                    continue

                b += f"/* {comment} */"
                b += f"sdram_dfii_pi0_address_write({a ^ a_inv:#x});"
                b += f"sdram_dfii_pi0_baddress_write({ba ^ ba_inv:d});"
                if cmd.startswith("DFII_CONTROL"):
                    b += f"sdram_dfii_control_write({cmd});"
                else:
                    b += f"command_p0({cmd});"
                if delay:
                    b += f"cdelay({delay});\n"
                b.newline()

    return r.generate()

# Python Header ------------------------------------------------------------------------------------

def get_sdram_phy_py_header(phy_settings, timing_settings):
    r = ""
    r += "dfii_control_sel     = 0x01\n"
    r += "dfii_control_cke     = 0x02\n"
    r += "dfii_control_odt     = 0x04\n"
    r += "dfii_control_reset_n = 0x08\n"
    r += "\n"
    r += "dfii_command_cs     = 0x01\n"
    r += "dfii_command_we     = 0x02\n"
    r += "dfii_command_cas    = 0x04\n"
    r += "dfii_command_ras    = 0x08\n"
    r += "dfii_command_wrdata = 0x10\n"
    r += "dfii_command_rddata = 0x20\n"
    r += "\n"

    init_sequence, mr = get_sdram_phy_init_sequence(phy_settings, timing_settings)

    if mr is not None and 1 in mr:
        r += "ddrx_mr1 = 0x{:x}\n".format(mr[1])
        r += "\n"

    r += "init_sequence = [\n"
    for comment, a, ba, cmd, delay in init_sequence:
        invert_masks = [(0, 0), ]
        if phy_settings.is_rdimm:
            assert phy_settings.memtype == "DDR4"
            # JESD82-31A page 38
            #
            # B-side chips have certain usually-inconsequential address and BA
            # bits inverted by the RCD to reduce SSO current. For mode register
            # writes, however, we must compensate for this. BG[1] also directs
            # writes either to the A side (BG[1]=0) or B side (BG[1]=1)
            #
            # The 'ba != 7' is because we don't do this to writes to the RCD
            # itself.
            if ba != 7:
                invert_masks.append((0b10101111111000, 0b1111))

        for a_inv, ba_inv in invert_masks:
            r += f"    (\"{comment}\", {a ^ a_inv:d}, {ba ^ ba_inv:d}, {cmd.lower()}, {delay}),\n"
    r += "]\n"
    return r
