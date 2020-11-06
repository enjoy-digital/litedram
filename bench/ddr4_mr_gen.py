#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import argparse

parser = argparse.ArgumentParser(description="DDR4 Mode Register settings generator for LiteDRAM.")
parser.add_argument("--list",        action="store_true", help="List supported DDR4 settings.")
parser.add_argument("--cl",          default="9",         help="CAS Latency.")
parser.add_argument("--cwl",         default="9",         help="CAS Write Latency.")
parser.add_argument("--rtt_nom",     default="40ohm",     help="RTT_NOM value.")
parser.add_argument("--rtt_wr",      default="120ohm",    help="RTT_WR value.")
parser.add_argument("--ron",         default="34ohm",     help="RON value.")
args = parser.parse_args()

# DDR4 Timing settings -----------------------------------------------------------------------------
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

if args.list:
  print("Supported DDR4 Timing settings:")
  print("cl:")
  for v in cl_to_mr0.keys():
    print(f" - {v}")
  print("cwl:")
  for v in cwl_to_mr2.keys():
    print(f" - {v}")

# DDR4 Electrical settings -------------------------------------------------------------------------
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

if args.list:
  print("Supported DDR4 Electrical settings:")
  print("rtt_nom:")
  for v in z_to_rtt_nom.keys():
    print(f" - {v}")
  print("rtt_wr:")
  for v in z_to_rtt_wr.keys():
    print(f" - {v}")
  print("ron:")
  for v in z_to_ron.keys():
    print(f" - {v}")

# DDR4 Mode Register formating ---------------------------------------------------------------------

if args.list:
  exit()

def format_mr0(bl, cl, wr, dll_reset):
        bl_to_mr0 = {
            4: 0b10,
            8: 0b00
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

def format_mr1(dll_enable, ron, rtt_nom):
    mr1 = dll_enable
    mr1 |= ((ron >> 0) & 0b1) << 1
    mr1 |= ((ron >> 1) & 0b1) << 2
    mr1 |= ((rtt_nom >> 0) & 0b1) << 8
    mr1 |= ((rtt_nom >> 1) & 0b1) << 9
    mr1 |= ((rtt_nom >> 2) & 0b1) << 10
    return mr1

def format_mr2(cwl, rtt_wr):
    mr2 = cwl_to_mr2[cwl] << 3
    mr2 |= rtt_wr << 9
    return mr2

print("DDR4 Timing Settings:")
print(f"cl:  {args.cl}")
print(f"cwl: {args.cwl}")

print("DDR4 Electrical Settings:")
print(f"rtt_nom: {args.rtt_nom}")
print(f"rtt_wr:  {args.rtt_wr}")
print(f"ron:     {args.ron}")

print("Commands to be used with LiteX BIOS:")
print("sdram_mr_write 0 {:d}".format(format_mr0(
  bl         = 8,
  cl         = int(args.cl, 0),
  wr         = 10,
  dll_reset  = 0))
)
print("sdram_mr_write 1 {:d}".format(format_mr1(
  dll_enable = 1,
  ron        = z_to_ron[args.ron],
  rtt_nom    = z_to_rtt_nom[args.rtt_nom]))
)
print("sdram_mr_write 2 {:d}".format(format_mr2(
  cwl    = int(args.cwl, 0),
  rtt_wr = z_to_rtt_wr[args.rtt_wr]))
)
