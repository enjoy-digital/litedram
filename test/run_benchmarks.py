#!/usr/bin/env python3

# This file is Copyright (c) 2020 Jędrzej Boczar <jboczar@antmicro.com>
# License: BSD

import os
import re
import sys
import json
import argparse
import subprocess
from collections import defaultdict, namedtuple

import yaml

from litedram.common import Settings

from .benchmark import LiteDRAMBenchmarkSoC


# constructs python regex named group
def ng(name, regex):
    return r'(?P<{}>{})'.format(name, regex)

def center(text, width, fillc=' '):
    added = width - len(text)
    left = added // 2
    right = added - left
    return fillc * left + text + fillc * right

def human_readable(value):
    binary_prefixes = ['', 'k', 'M', 'G', 'T']
    mult = 1.0
    for prefix in binary_prefixes:
        if value * mult < 1024:
            break
        mult /= 1024
    return mult, prefix

# Benchmark configuration --------------------------------------------------------------------------

class BenchmarkConfiguration(Settings):
    def __init__(self, sdram_module, sdram_data_width, bist_length, bist_random):
        self.set_attributes(locals())
        self._settings = {k: v for k, v in locals().items() if k != 'self'}

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

    def __eq__(self, other):
        if not isinstance(other, BenchmarkConfiguration):
            return NotImplemented
        return all((getattr(self, setting) == getattr(other, setting)
                    for setting in self._settings.keys()))

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
        self._output = output
        self.parse_output(output)
        # instantiate the benchmarked soc to check its configuration
        self.benchmark_soc = LiteDRAMBenchmarkSoC(**self.config._settings)

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

    def write_latency(self):
        assert self.config.bist_length == 1, 'Not a latency benchmark'
        return self.generator_ticks

    def read_latency(self):
        assert self.config.bist_length == 1, 'Not a latency benchmark'
        return self.checker_ticks

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

    @classmethod
    def dump_results_json(cls, results, file):
        """Save multiple results in a JSON file.

        Only configurations and outpits are saved, as they can be used to reconstruct BenchmarkResult.
        """
        # simply use config._settings as it defines the BenchmarkConfiguration
        results_raw = [(r.config._settings, r._output) for r in results]
        with open(file, 'w') as f:
            json.dump(results_raw, f)

    @classmethod
    def load_results_json(cls, file):
        """Load results from a JSON file."""
        with open(file, 'r') as f:
            results_raw = json.load(f)
        return [cls(BenchmarkConfiguration(**settings), output) for (settings, output) in results_raw]

# Results summary ----------------------------------------------------------------------------------

class ResultsSummary:
    # value_scaling is a function: value -> (multiplier, prefix)
    Fmt = namedtuple('MetricFormatting', ['name', 'unit', 'value_scaling'])
    metric_formats = {
        'write_bandwidth':  Fmt('Write bandwidth',  'bps', lambda value: human_readable(value)),
        'read_bandwidth':   Fmt('Read bandwidth',   'bps', lambda value: human_readable(value)),
        'write_efficiency': Fmt('Write efficiency', '',    lambda value: (100, '%')),
        'read_efficiency':  Fmt('Read efficiency',  '',    lambda value: (100, '%')),
        'write_latency':    Fmt('Write latency',    'clk', lambda value: (1, '')),
        'read_latency':     Fmt('Read latency',     'clk', lambda value: (1, '')),
    }

    def __init__(self, results):
        self.results = results

    def by_metric(self, metric):
        """Returns pairs of value of the given metric and the configuration used for benchmark"""
        for result in self.results:
            # omit the results that should not be used to calculate given metric
            if result.config.bist_length == 1 and metric not in ['read_latency', 'write_latency'] \
                    or result.config.bist_length != 1 and metric in ['read_latency', 'write_latency']:
                continue
            value = getattr(result, metric)()
            yield value, result.config

    def print(self):
        legend = '(module, datawidth, length, random, result)'
        fmt = '   {module:15}  {dwidth:2}  {length:4}  {random:1}    {result}'

        # store formatted lines per metric
        metric_lines = defaultdict(list)
        for metric, (_, unit, formatter) in self.metric_formats.items():
            for value, config in self.by_metric(metric):
                mult, prefix = formatter(value)
                value_fmt = '{:5.1f} {}{}' if isinstance(value * mult, float) else '{:5d} {}{}'
                result = value_fmt.format(value * mult, prefix, unit)
                line = fmt.format(module=config.sdram_module,
                                  dwidth=config.sdram_data_width,
                                  length=config.bist_length,
                                  random=int(config.bist_random),
                                  result=result)
                metric_lines[metric].append(line)

        # find length of the longest line
        max_length = max((len(l) for lines in metric_lines.values() for l in lines))
        max_length = max(max_length, len(legend) + 2)
        width = max_length + 2

        # print the formatted summary
        def header(text):
            mid = center(text, width - 6, '=')
            return center(mid, width, '-')
        print(header(' Summary '))
        print(center(legend, width))
        for metric, lines in metric_lines.items():
            print(center(self.metric_formats[metric].name, width))
            for line in lines:
                print(line)
        print(header(''))

    def plot(self, output_dir, backend='Agg', theme='default', save_format='png', **savefig_kwargs):
        """Create plots with benchmark results summary

        Default backend is Agg, which is non-GUI backed and only allows
        to save figures as files. If a GUI backed is passed, plt.show()
        will be called at the end.
        """
        # import locally here to be able to run benchmarks without installing matplotlib
        import matplotlib
        matplotlib.use(backend)

        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.ticker import FuncFormatter, PercentFormatter, ScalarFormatter

        plt.style.use(theme)

        def bandwidth_formatter_func(value, pos):
            mult, prefix = human_readable(value)
            return '{:.1f}{}bps'.format(value * mult, prefix)

        tick_formatters = {
            'write_bandwidth':  FuncFormatter(bandwidth_formatter_func),
            'read_bandwidth':   FuncFormatter(bandwidth_formatter_func),
            'write_efficiency': PercentFormatter(1.0),
            'read_efficiency':  PercentFormatter(1.0),
            'write_latency':    ScalarFormatter(),
            'read_latency':     ScalarFormatter(),
        }

        def config_tick_name(config):
            return '{}\n{}, {}, {}'.format(config.sdram_module, config.sdram_data_width,
                                         config.bist_length, int(config.bist_random))

        for metric, (name, unit, _) in self.metric_formats.items():
            fig = plt.figure()
            axis = plt.gca()

            values, configs = zip(*self.by_metric(metric))
            ticks = np.arange(len(configs))

            axis.barh(ticks, values, align='center')
            axis.set_yticks(ticks)
            axis.set_yticklabels([config_tick_name(c) for c in configs])
            axis.invert_yaxis()
            axis.xaxis.set_major_formatter(tick_formatters[metric])
            axis.xaxis.set_tick_params(rotation=30)
            axis.grid(True)
            axis.spines['top'].set_visible(False)
            axis.spines['right'].set_visible(False)
            axis.set_axisbelow(True)

            # force xmax to 100%
            if metric in ['write_efficiency', 'read_efficiency']:
                axis.set_xlim(right=1.0)

            title = self.metric_formats[metric].name
            axis.set_title(title, fontsize=12)

            plt.tight_layout()
            filename = '{}.{}'.format(metric, save_format)
            fig.savefig(os.path.join(output_dir, filename), **savefig_kwargs)

        if backend != 'Agg':
            plt.show()

# Run ----------------------------------------------------------------------------------------------

def run_benchmark(cmd_args):
    # run as separate process, because else we cannot capture all output from verilator
    benchmark_script = os.path.join(os.path.dirname(__file__), 'benchmark.py')
    command = ['python3', benchmark_script, *cmd_args]
    proc = subprocess.run(command, stdout=subprocess.PIPE)
    return str(proc.stdout)


def run_benchmarks(configurations):
    results = []
    for name, config in configurations.items():
        cmd_args = config.as_args()
        print('{}: {}'.format(name, ' '.join(cmd_args)))
        output = run_benchmark(cmd_args)
        # exit if checker had any read error
        result = BenchmarkResult(config, output)
        if result.checker_errors != 0:
            print('Error during benchmark "{}": checker_errors = {}'.format(
                name, result.checker_errors), file=sys.stderr)
            sys.exit(1)
        results.append(result)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Run LiteDRAM benchmarks and collect the results.')
    parser.add_argument("config",                                  help="YAML config file")
    parser.add_argument('--names',            nargs='*',           help='Limit benchmarks to given names')
    parser.add_argument('--regex',                                 help='Limit benchmarks to names matching the regex')
    parser.add_argument('--not-regex',                             help='Limit benchmarks to names not matching the regex')
    parser.add_argument('--plot',             action='store_true', help='Generate plots with results summary')
    parser.add_argument('--plot-format',      default='png',       help='Specify plots file format (default=png)')
    parser.add_argument('--plot-backend',     default='Agg',       help='Optionally specify matplotlib GUI backend')
    parser.add_argument('--plot-transparent', action='store_true', help='Use transparent background when saving plots')
    parser.add_argument('--plot-output-dir',  default='plots',     help='Specify where to save the plots')
    parser.add_argument('--plot-theme',       default='default',   help='Use different matplotlib theme')
    parser.add_argument('--results-cache',                         help="""Use given JSON file as results cache. If the file exists,
                                                                           it will be loaded instead of running actual benchmarks,
                                                                           else benchmarks will be run normally, and then saved
                                                                           to the given file. This allows to easily rerun the script
                                                                           to generate different summary without having to rerun benchmarks.""")
    args = parser.parse_args(argv)

    # load and filter configurations
    configurations = BenchmarkConfiguration.load_yaml(args.config)
    filters = []
    if args.regex:
        filters.append(lambda name_value: re.search(args.regex, name_value[0]))
    if args.not_regex:
        filters.append(lambda name_value: not re.search(args.not_regex, name_value[0]))
    if args.names:
        filters.append(lambda name_value: name_value[0] in args.names)
    for f in filters:
        configurations = dict(filter(f, configurations.items()))

    cache_exists = args.results_cache and os.path.isfile(args.results_cache)

    # load outputs from cache if it exsits
    if args.results_cache and cache_exists:
        cached_results = BenchmarkResult.load_results_json(args.results_cache)
        # take only those that match configurations
        results = [r for r in cached_results if r.config in configurations.values()]
    else:  # run all the benchmarks normally
        results = run_benchmarks(configurations)

    # store outputs in cache
    if args.results_cache and not cache_exists:
        BenchmarkResult.dump_results_json(results, args.results_cache)

    # display the summary
    summary = ResultsSummary(results)
    summary.print()
    if args.plot:
        if not os.path.isdir(args.plot_output_dir):
            os.makedirs(args.plot_output_dir)
        summary.plot(args.plot_output_dir,
                     backend=args.plot_backend,
                     theme=args.plot_theme,
                     save_format=args.plot_format,
                     transparent=args.plot_transparent)


if __name__ == "__main__":
    main()
