#!/usr/bin/env python3

# This file is Copyright (c) 2020 Jędrzej Boczar <jboczar@antmicro.com>
# License: BSD

import re
import subprocess

from litedram.common import Settings

from benchmark import LiteDRAMBenchmarkSoC


# constructs python regex named group
def ng(name, regex):
    return r'(?P<{}>{})'.format(name, regex)


def human_readable(value):
    binary_prefixes = ['', 'k', 'M', 'G', 'T']
    for prefix in binary_prefixes:
        if value < 1024:
            break
        value /= 1024
    return value, prefix


def run_benchmark(args):
    command = ['python3', 'benchmark.py', *args]
    proc = subprocess.run(command, capture_output=True, text=True, check=True)
    return proc.stdout


class BenchmarkConfiguration(Settings):
    def __init__(self, sdram_module, sdram_data_width, bist_length, bist_random):
        self.set_attributes(locals())
        self._settings = {k: v for k, v in locals().items() if v != self}

    def as_args(self):
        args = []
        for attr, value in self._settings.items():
            arg_string = '--%s' % attr.replace('_', '-')
            if isinstance(value, bool):
                if value:
                    args.append(arg_string)
            else:
                args.extend([arg_string, str(value)])
        return args


class BenchmarkResult:
    def __init__(self, config, output):
        self.config = config
        self.parse_output(output)
        # instantiate the benchmarked soc to check its configuration
        self.benchmark_soc = LiteDRAMBenchmarkSoC(**self.config._settings)

    def parse_output(self, output):
        bist_pattern = r'{stage}\s+{var}:\s+{value}'

        def find(stage, var):
            pattern = bist_pattern.format(
                stage=stage,
                var=var,
                value=ng('value', '[0-9]+'),
            )
            result = re.search(pattern, output)
            assert result is not None, 'Could not find pattern in output: %s, %s' % (pattern, output)
            return int(result.group('value'))

        self.generator_ticks = find('BIST-GENERATOR', 'ticks')
        self.checker_errors = find('BIST-CHECKER', 'errors')
        self.checker_ticks = find('BIST-CHECKER', 'ticks')

    def cmd_count(self):
        data_width = self.benchmark_soc.sdram.controller.interface.data_width
        return self.config.bist_length / (data_width // 8)

    def clk_period(self):
        clk_freq = self.benchmark_soc.sdrphy.module.clk_freq
        return 1 / clk_freq

    def write_bandwidth(self):
        return (8 * self.config.bist_length) / (self.generator_ticks * self.clk_period())

    def read_bandwidth(self):
        return (8 * self.config.bist_length) / (self.checker_ticks * self.clk_period())

    def write_efficiency(self):
        return self.cmd_count() / self.generator_ticks

    def read_efficiency(self):
        return self.cmd_count() / self.checker_ticks


configurations = [
    BenchmarkConfiguration('MT48LC16M16', 32, 4096,  True),
    BenchmarkConfiguration('MT48LC16M16', 32,  512, False),
    BenchmarkConfiguration('MT46V32M16',  32,  512, False),
    BenchmarkConfiguration('MT46V32M16',  32, 2048, False),
    BenchmarkConfiguration('MT47H64M16',  32, 1024, False),
    BenchmarkConfiguration('MT47H64M16',  16, 1024, False),
    BenchmarkConfiguration('MT41K128M16', 16, 1024, False),
    BenchmarkConfiguration('MT41K128M16', 32, 1024, False),
]


def main():
    results = []
    for config in configurations:
        args = config.as_args()
        print('Benchmark: %s' % ' '.join(args))

        result = BenchmarkResult(config, run_benchmark(args))
        results.append(result)

        print("""\
  write_bandwidth  = {:6.3f} {}bps
  read_bandwidth   = {:6.3f} {}bps
  write_efficiency = {:6.2f} %
  read_efficiency  = {:6.2f} %
        """.rstrip().format(
            *human_readable(result.write_bandwidth()),
            *human_readable(result.read_bandwidth()),
            result.write_efficiency() * 100,
            result.read_efficiency() * 100,
        ))


if __name__ == "__main__":
    main()
