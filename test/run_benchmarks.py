#!/usr/bin/env python3

# This file is Copyright (c) 2020 Jędrzej Boczar <jboczar@antmicro.com>
# License: BSD

import os
import re
import yaml
import argparse
import subprocess

from litedram.common import Settings

from .benchmark import LiteDRAMBenchmarkSoC


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

# Benchmark configuration --------------------------------------------------------------------------

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

    @classmethod
    def load_yaml(cls, yaml_file):
        with open(yaml_file) as f:
            description = yaml.safe_load(f)
        configurations = {name: cls(**desc) for name, desc in description.items()}
        return configurations

# Benchmark results --------------------------------------------------------------------------------

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

# Results summary ----------------------------------------------------------------------------------

class ResultsSummary:
    def __init__(self, results):
        self.results = results
        # convert results, which map config->metrics to a mapping metric->(config->result)
        self.write_bandwidth = self.collect('write_bandwidth')
        self.read_bandwidth = self.collect('read_bandwidth')
        self.write_efficiency = self.collect('write_efficiency')
        self.read_efficiency = self.collect('read_efficiency')

    def create_name(self, config):
        return '{}:{}:{}:{}'.format(
            config.sdram_module, config.sdram_data_width,
            config.bist_length, config.bist_random)

    def collect(self, attribute):
        by_case = {}
        for result in self.results:
            value = getattr(result, attribute)()
            by_case[self.create_name(result.config)] = value
        return by_case

    def value_string(self, metric, value):
        if metric in ['write_bandwidth', 'read_bandwidth']:
            return '{:6.3f} {}bps'.format(*human_readable(value))
        elif ['write_efficiency', 'read_efficiency']:
            return '{:5.1f} %'.format(100 * value)
        else:
            raise ValueError()

    def print(self):
        print('\n---====== Summary ======---')
        for metric in ['write_bandwidth', 'read_bandwidth', 'write_efficiency', 'read_efficiency']:
            print(metric)
            for case, value in getattr(self, metric).items():
                print('  {:30}  {}'.format(case, self.value_string(metric, value)))

    def plot(self):
        raise NotImplementedError()

# Run ----------------------------------------------------------------------------------------------

def run_benchmark(args):
    benchmark_script = os.path.join(os.path.dirname(__file__), 'benchmark.py')
    command = ['python3', benchmark_script, *args]
    proc = subprocess.run(command, capture_output=True, text=True, check=True)
    return proc.stdout


def main():
    parser = argparse.ArgumentParser(
        description='Run LiteDRAM benchmarks and collect the results')
    parser.add_argument('--yaml', required=True, help='Load benchmark configurations from YAML file')
    parser.add_argument('--names', nargs='*', help='Limit benchmarks to given names')
    parser.add_argument('--regex', help='Limit benchmarks to names matching the regex')
    parser.add_argument('--not-regex', help='Limit benchmarks to names not matching the regex')
    args = parser.parse_args()

    # load and filter configurations
    configurations = BenchmarkConfiguration.load_yaml(args.yaml)
    filters = []
    if args.regex:
        filters.append(lambda name_value: re.search(args.regex, name_value[0]))
    if args.not_regex:
        filters.append(lambda name_value: not re.search(args.not_regex, name_value[0]))
    if args.names:
        filters.append(lambda name_value: name_value[0] in args.names)
    for f in filters:
        configurations = dict(filter(f, configurations.items()))

    # run the benchmarks
    results = []
    for name, config in configurations.items():
        args = config.as_args()
        print('{}: {}'.format(name, ' '.join(args)))

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

    summary = ResultsSummary(results)
    summary.print()

if __name__ == "__main__":
    main()
