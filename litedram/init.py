#
# This file is part of LiteDRAM.
#
# Copyright (c) 2013-2014 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2013-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2017 whitequark <whitequark@whitequark.org>
# Copyright (c) 2014 Yann Sionneau <ys@m-labs.hk>
# Copyright (c) 2018 bunnie <bunnie@kosagi.com>
# Copyright (c) 2019 Gabriel L. Somlo <gsomlo@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

cmds = {
    "PRECHARGE_ALL": "DFII_COMMAND_RAS|DFII_COMMAND_WE|DFII_COMMAND_CS",
    "MODE_REGISTER": "DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS",
    "AUTO_REFRESH":  "DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_CS",
    "UNRESET":       "DFII_CONTROL_ODT|DFII_CONTROL_RESET_N",
    "CKE":           "DFII_CONTROL_CKE|DFII_CONTROL_ODT|DFII_CONTROL_RESET_N"
}

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

    # default electrical settings (point to point)
    rtt_nom = "60ohm"
    rtt_wr  = "60ohm"
    ron     = "34ohm"
    tdqs    = 0

    # override electrical settings if specified
    if hasattr(phy_settings, "rtt_nom"):
        rtt_nom = phy_settings.rtt_nom
    if hasattr(phy_settings, "rtt_wr"):
        rtt_wr = phy_settings.rtt_wr
    if hasattr(phy_settings, "ron"):
        ron = phy_settings.ron
    if getattr(phy_settings, "tdqs", False):
        tdqs = 1

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

    return init_sequence, mr1

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

    # default electrical settings (point to point)
    rtt_nom = "40ohm"
    rtt_wr  = "120ohm"
    ron     = "34ohm"
    tdqs    = 0
    dm      = 1
    assert not (dm and tdqs)

    # override electrical settings if specified
    if hasattr(phy_settings, "rtt_nom"):
        rtt_nom = phy_settings.rtt_nom
    if hasattr(phy_settings, "rtt_wr"):
        rtt_wr = phy_settings.rtt_wr
    if hasattr(phy_settings, "ron"):
        ron = phy_settings.ron
    if getattr(phy_settings, "tdqs", False):
        tdqs = 1

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

        f0rc0a = 0x0A0 | coarse_speed                    # F0RC0A: coarse speed selection and PLL bypass
        f0rc3x = 0x300 | fine_speed                      # F0RC3x: fine speed selection

        rdimm_init = [
            ("Reset RCD", rcd_reset, 7, cmds["MODE_REGISTER"], 50000),
            ("Load RCD F0RC0F", f0rc0f, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC03", f0rc03, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC04", f0rc04, 7, cmds["MODE_REGISTER"], 100),
            ("Load RCD F0RC05", f0rc05, 7, cmds["MODE_REGISTER"], 100),
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

    return init_sequence, mr1

# Init Sequence ------------------------------------------------------------------------------------

def get_sdram_phy_init_sequence(phy_settings, timing_settings):
    return {
        "SDR"  : get_sdr_phy_init_sequence,
        "DDR"  : get_ddr_phy_init_sequence,
        "LPDDR": get_lpddr_phy_init_sequence,
        "DDR2" : get_ddr2_phy_init_sequence,
        "DDR3" : get_ddr3_phy_init_sequence,
        "DDR4" : get_ddr4_phy_init_sequence,
    }[phy_settings.memtype](phy_settings, timing_settings)

# C Header -----------------------------------------------------------------------------------------

def get_sdram_phy_c_header(phy_settings, timing_settings):
    r = "#ifndef __GENERATED_SDRAM_PHY_H\n#define __GENERATED_SDRAM_PHY_H\n"
    r += "#include <hw/common.h>\n"
    r += "#include <generated/csr.h>\n"
    r += "\n"

    r += "#define DFII_CONTROL_SEL        0x01\n"
    r += "#define DFII_CONTROL_CKE        0x02\n"
    r += "#define DFII_CONTROL_ODT        0x04\n"
    r += "#define DFII_CONTROL_RESET_N    0x08\n"
    r += "\n"

    r += "#define DFII_COMMAND_CS         0x01\n"
    r += "#define DFII_COMMAND_WE         0x02\n"
    r += "#define DFII_COMMAND_CAS        0x04\n"
    r += "#define DFII_COMMAND_RAS        0x08\n"
    r += "#define DFII_COMMAND_WRDATA     0x10\n"
    r += "#define DFII_COMMAND_RDDATA     0x20\n"
    r += "\n"

    phytype = phy_settings.phytype.upper()
    nphases = phy_settings.nphases

    # Define PHY type and number of phases
    r += "#define SDRAM_PHY_"+phytype+"\n"
    r += "#define SDRAM_PHY_XDR "+str(1 if phy_settings.memtype == "SDR" else 2) + "\n"
    r += "#define SDRAM_PHY_DATABITS "+str(phy_settings.databits) + "\n"
    r += "#define SDRAM_PHY_PHASES "+str(nphases)+"\n"
    if phy_settings.cl is not None:
        r += "#define SDRAM_PHY_CL "+str(phy_settings.cl)+"\n"
    if phy_settings.cwl is not None:
        r += "#define SDRAM_PHY_CWL "+str(phy_settings.cwl)+"\n"
    if phy_settings.cmd_latency is not None:
        r += "#define SDRAM_PHY_CMD_LATENCY "+str(phy_settings.cmd_latency)+"\n"
    if phy_settings.cmd_delay is not None:
        r += "#define SDRAM_PHY_CMD_DELAY "+str(phy_settings.cmd_delay)+"\n"

    # Define PHY Read.Write phases
    rdphase = phy_settings.rdphase
    if isinstance(rdphase, Signal): rdphase = rdphase.reset.value
    r += "#define SDRAM_PHY_RDPHASE "+str(rdphase)+"\n"
    wrphase = phy_settings.wrphase
    if isinstance(wrphase, Signal): wrphase = wrphase.reset.value
    r += "#define SDRAM_PHY_WRPHASE "+str(wrphase)+"\n"

    # Define Read/Write Leveling capability
    if phytype in ["USDDRPHY", "USPDDRPHY", "K7DDRPHY", "V7DDRPHY"]:
        r += "#define SDRAM_PHY_WRITE_LEVELING_CAPABLE\n"
    if phytype in ["USDDRPHY", "USPDDRPHY"]:
        r += "#define SDRAM_PHY_WRITE_LEVELING_REINIT\n"
    if phytype in ["USDDRPHY", "USPDDRPHY", "A7DDRPHY", "K7DDRPHY", "V7DDRPHY"]:
        r += "#define SDRAM_PHY_WRITE_LATENCY_CALIBRATION_CAPABLE\n"
        r += "#define SDRAM_PHY_READ_LEVELING_CAPABLE\n"
    if phytype in ["ECP5DDRPHY"]:
        r += "#define SDRAM_PHY_READ_LEVELING_CAPABLE\n"

    # Define number of modules/delays/bitslips
    if phytype in ["USDDRPHY", "USPDDRPHY"]:
        r += "#define SDRAM_PHY_MODULES DFII_PIX_DATA_BYTES/2\n"
        r += "#define SDRAM_PHY_DELAYS 512\n"
        r += "#define SDRAM_PHY_BITSLIPS 8\n"
    elif phytype in ["A7DDRPHY", "K7DDRPHY", "V7DDRPHY"]:
        r += "#define SDRAM_PHY_MODULES DFII_PIX_DATA_BYTES/2\n"
        r += "#define SDRAM_PHY_DELAYS 32\n"
        r += "#define SDRAM_PHY_BITSLIPS 8\n"
    elif phytype in ["ECP5DDRPHY"]:
        r += "#define SDRAM_PHY_MODULES DFII_PIX_DATA_BYTES/4\n"
        r += "#define SDRAM_PHY_DELAYS 8\n"
        r += "#define SDRAM_PHY_BITSLIPS 4\n"

    if phy_settings.is_rdimm:
        assert phy_settings.memtype == "DDR4"
        r += "#define SDRAM_PHY_DDR4_RDIMM\n"

    r += "\n"

    r += "static void cdelay(int i);\n"

    # Commands functions
    for n in range(nphases):
        r += """
__attribute__((unused)) static void command_p{n}(int cmd)
{{
    sdram_dfii_pi{n}_command_write(cmd);
    sdram_dfii_pi{n}_command_issue_write(1);
}}""".format(n=str(n))
    r += "\n\n"

    # Write/Read functions
    r += "#define DFII_PIX_DATA_SIZE CSR_SDRAM_DFII_PI0_WRDATA_SIZE\n"
    sdram_dfii_pix_wrdata_addr = []
    for n in range(nphases):
        sdram_dfii_pix_wrdata_addr.append("CSR_SDRAM_DFII_PI{n}_WRDATA_ADDR".format(n=n))
    r += """
const unsigned long sdram_dfii_pix_wrdata_addr[SDRAM_PHY_PHASES] = {{
\t{sdram_dfii_pix_wrdata_addr}
}};
""".format(sdram_dfii_pix_wrdata_addr=",\n\t".join(sdram_dfii_pix_wrdata_addr))

    sdram_dfii_pix_rddata_addr = []
    for n in range(nphases):
        sdram_dfii_pix_rddata_addr.append("CSR_SDRAM_DFII_PI{n}_RDDATA_ADDR".format(n=n))
    r += """
const unsigned long sdram_dfii_pix_rddata_addr[SDRAM_PHY_PHASES] = {{
\t{sdram_dfii_pix_rddata_addr}
}};
""".format(sdram_dfii_pix_rddata_addr=",\n\t".join(sdram_dfii_pix_rddata_addr))
    r += "\n"

    init_sequence, mr1 = get_sdram_phy_init_sequence(phy_settings, timing_settings)

    if phy_settings.memtype in ["DDR3", "DDR4"]:
        # The value of MR1 needs to be modified during write leveling
        r += "#define DDRX_MR1 {}\n\n".format(mr1)

    r += "static void init_sequence(void)\n{\n"
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
            r += "\t/* {0} */\n".format(comment)
            r += "\tsdram_dfii_pi0_address_write({0:#x});\n".format(a ^ a_inv)
            r += "\tsdram_dfii_pi0_baddress_write({0:d});\n".format(ba ^ ba_inv)
            if cmd[:12] == "DFII_CONTROL":
                r += "\tsdram_dfii_control_write({0});\n".format(cmd)
            else:
                r += "\tcommand_p0({0});\n".format(cmd)
            if delay:
                r += "\tcdelay({0:d});\n".format(delay)
            r += "\n"
    r += "}\n"

    r += "#endif\n"

    return r

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

    init_sequence, mr1 = get_sdram_phy_init_sequence(phy_settings, timing_settings)

    if mr1 is not None:
        r += "ddrx_mr1 = 0x{:x}\n".format(mr1)
        r += "\n"

    r += "init_sequence = [\n"
    for comment, a, ba, cmd, delay in init_sequence:
        r += "    "
        r += "(\"" + comment + "\", "
        r += str(a) + ", "
        r += str(ba) + ", "
        r += cmd.lower() + ", "
        r += str(delay) + "),"
        r += "\n"
    r += "]\n"
    return r
