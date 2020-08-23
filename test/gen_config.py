#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import sys
import json
import pprint
import argparse
import datetime
import itertools


defaults = {
    "--sdram-module": [
        "IS42S16160",
        "IS42S16320",
        "MT48LC4M16",
        "MT48LC16M16",
        "AS4C16M16",
        "AS4C32M16",
        "AS4C32M8",
        "M12L64322A",
        "M12L16161A",
        "MT46V32M16",
        "MT46H32M16",
        "MT46H32M32",
        "MT47H128M8",
        "MT47H32M16",
        "MT47H64M16",
        "P3R1GE4JGF",
        "MT41K64M16",
        "MT41J128M16",
        "MT41K128M16",
        "MT41J256M16",
        "MT41K256M16",
        "K4B1G0446F",
        "K4B2G1646F",
        "H5TC4G63CFR",
        "IS43TR16128B",
        "MT8JTF12864",
        "MT8KTF51264",
        #"MT18KSF1G72HZ",
        #"AS4C256M16D3A",
        #"MT16KTF1G64HZ",
        #"EDY4016A",
        #"MT40A1G8",
        #"MT40A512M16",
    ],
    "--sdram-data-width": [32],
    "--bist-alternating": [True, False],
    "--bist-length":      [1, 4096],
    "--bist-random":      [True, False],
    "--num-generators":   [1],
    "--num-checkers":     [1],
    "--access-pattern":   ["access_pattern.csv"]
}


def convert_string_arg(args, arg, type):
    map_func = {
        bool: lambda s: {"false": False, "true": True}[s.lower()],
        int:  lambda s: int(s, 0),
    }
    setattr(args, arg, [map_func[type](val) if not isinstance(val, type) else val for val in getattr(args, arg)])


def generate_header(args):
    header = "Auto-generated on {} by {}".format(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sys.argv[0],
    )
    #args_str = pprint.pformat(vars(args), sort_dicts=False) # FIXME: python3.7 specific?
    args_str = pprint.pformat(vars(args))
    arg_lines = args_str.split("\n")
    lines = [60*"=", header, 60*"-", *arg_lines, 60*"="]
    return "\n".join("# " + line for line in lines)


def main():
    parser = argparse.ArgumentParser(description="Generate configuration for all possible argument combinations.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--name-format", default="test_%d", help="Name format for i-th test")
    for name, default in defaults.items():
        parser.add_argument(name, nargs="+", default=default, help="%s options" % name)
    args = parser.parse_args()

    # Make sure not to write those as strings
    convert_string_arg(args, "sdram_data_width", int)
    convert_string_arg(args, "bist_alternating", bool)
    convert_string_arg(args, "bist_length",      int)
    convert_string_arg(args, "bist_random",      bool)
    convert_string_arg(args, "num_generators",   int)
    convert_string_arg(args, "num_checkers",     int)

    common_args            = ("sdram_module", "sdram_data_width", "bist_alternating", "num_generators", "num_checkers")
    generated_pattern_args = ("bist_length", "bist_random")
    custom_pattern_args    = ("access_pattern", )

    def generated_pattern_configuration(values):
        config = dict(zip(common_args + generated_pattern_args, values))
        # Move access pattern parameters deeper
        config["access_pattern"] = {
            "bist_length": config.pop("bist_length"),
            "bist_random": config.pop("bist_random"),
        }
        return config

    def custom_pattern_configuration(values):
        config = dict(zip(common_args + custom_pattern_args, values))
        # "rename" --access-pattern to access_pattern.pattern_file due to name difference between
        # command line args and run_benchmarks.py configuration format
        config["access_pattern"] = {
            "pattern_file": config.pop("access_pattern"),
        }
        return config

    # Iterator over the product of given command line arguments
    def args_product(names):
        return itertools.product(*(getattr(args, name) for name in names))

    generated_pattern_iter = zip(itertools.repeat(generated_pattern_configuration), args_product(common_args + generated_pattern_args))
    custom_pattern_iter    = zip(itertools.repeat(custom_pattern_configuration), args_product(common_args + custom_pattern_args))

    i = 0
    configurations = {}
    for config_generator, values in itertools.chain(generated_pattern_iter, custom_pattern_iter):
        config = config_generator(values)
        # Ignore unsupported case: bist_random=True and bist_alternating=False
        if config["access_pattern"].get("bist_random", False) and not config["bist_alternating"]:
            continue
        configurations[args.name_format % i] = config
        i += 1

    json_str = json.dumps(configurations, indent=4)
    print(generate_header(args))
    print(json_str)


if __name__ == "__main__":
    main()
