#!/usr/bin/env python

import json
import argparse
import itertools

modules = [
    'IS42S16160',
    'IS42S16320',
    'MT48LC4M16',
    'MT48LC16M16',
    'AS4C16M16',
    'AS4C32M16',
    'AS4C32M8',
    'M12L64322A',
    'M12L16161A',
    'MT46V32M16',
    'MT46H32M16',
    'MT46H32M32',
    'MT47H128M8',
    'MT47H32M16',
    'MT47H64M16',
    'P3R1GE4JGF',
    'MT41K64M16',
    'MT41J128M16',
    'MT41K128M16',
    'MT41J256M16',
    'MT41K256M16',
    'K4B1G0446F',
    'K4B2G1646F',
    'H5TC4G63CFR',
    'IS43TR16128B',
    'MT8JTF12864',
    'MT8KTF51264',
    #  'MT18KSF1G72HZ',
    #  'AS4C256M16D3A',
    #  'MT16KTF1G64HZ',
    #  'EDY4016A',
    #  'MT40A1G8',
    #  'MT40A512M16',
]
data_widths = [32]
bist_lengths = [1, 1024, 8192]
bist_randoms = [False]

parser = argparse.ArgumentParser(description='Generate configuration for all possible argument combinations.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--sdram-modules',     nargs='+', default=modules,      help='--sdram-module options')
parser.add_argument('--sdram-data-widths', nargs='+', default=data_widths,  help='--sdram-data-width options')
parser.add_argument('--bist-lengths',      nargs='+', default=bist_lengths, help='--bist-length options')
parser.add_argument('--bist-randoms',      nargs='+', default=bist_randoms, help='--bist-random options')
parser.add_argument('--name-format',                  default='test_%d',    help='Name format for i-th test')
args = parser.parse_args()

product = itertools.product(args.sdram_modules, args.sdram_data_widths, args.bist_lengths, args.bist_randoms)
configurations = {}
for i, (module, data_width, bist_length, bist_random) in enumerate(product):
    configurations[args.name_format % i] = {
        'sdram_module':     module,
        'sdram_data_width': data_width,
        'bist_length':      bist_length,
        'bist_random':      bist_random,
    }

json_str = json.dumps(configurations, indent=4)
print(json_str)
