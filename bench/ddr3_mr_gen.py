#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import argparse

parser = argparse.ArgumentParser(description="DDR3 Mode Register settings generator for LiteDRAM.")
parser.add_argument("--list",        action="store_true", help="List supported DDR3 settings.")
parser.add_argument("--cl",          default="5",         help="CAS Latency.")
parser.add_argument("--cwl",         default="5",         help="CAS Write Latency.")
parser.add_argument("--rtt_nom",     default="60ohm",     help="RTT_NOM value.")
parser.add_argument("--rtt_wr",      default="60ohm",     help="RTT_WR value.")
parser.add_argument("--ron",         default="34ohm",     help="RON value.")
args = parser.parse_args()

# DDR3 Timing settings -----------------------------------------------------------------------------
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

cwl_to_mr2 = {
   5: 0b000,
   6: 0b001,
   7: 0b010,
   8: 0b011,
   9: 0b100,
  10: 0b101,
}

if args.list:
  print("Supported DDR3 Timing settings:")
  print("cl:")
  for v in cl_to_mr0.keys():
    print(f" - {v}")
  print("cwl:")
  for v in cwl_to_mr2.keys():
    print(f" - {v}")

# DDR3 Electrical settings -------------------------------------------------------------------------
z_to_rtt_nom = {
    "disabled" : 0b000,
    "60ohm"    : 0b001,
    "120ohm"   : 0b010,
    "40ohm"    : 0b011,
    "20ohm"    : 0b100,
    "30ohm"    : 0b101
}

z_to_rtt_wr = {
    "disabled" : 0b00,
    "60ohm"    : 0b01,
    "120ohm"   : 0b10,
}

z_to_ron = {
    "40ohm" : 0b0,
    "34ohm" : 0b1,
}

if args.list:
  print("Supported DDR3 Electrical settings:")
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

def format_mr1(ron, rtt_nom, tdqs=1):
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

print("DDR3 Timing Settings:")
print(f"cl:  {args.cl}")
print(f"cwl: {args.cwl}")

print("DDR3 Electrical Settings:")
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
  ron        = z_to_ron[args.ron],
  rtt_nom    = z_to_rtt_nom[args.rtt_nom]))
)
print("sdram_mr_write 2 {:d}".format(format_mr2(
  cwl    = int(args.cwl, 0),
  rtt_wr = z_to_rtt_wr[args.rtt_wr]))
)
