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
try:
    import numpy as np
    import pandas as pd
    import matplotlib
    from matplotlib.ticker import FuncFormatter, PercentFormatter, ScalarFormatter
    _summary = True
except ImportError as e:
    _summary = False
    print('[WARNING] Results summary not available:', e, file=sys.stderr)

from litedram.common import Settings as _Settings

from . import benchmark
from .benchmark import LiteDRAMBenchmarkSoC, load_access_pattern


# Benchmark configuration --------------------------------------------------------------------------

class Settings(_Settings):
    def as_dict(self):
        d = dict()
        for attr, value in vars(self).items():
            if attr == 'self' or attr.startswith('_'):
                continue
            if isinstance(value, Settings):
                value = value.as_dict()
            d[attr] = value
        return d


class GeneratedAccess(Settings):
    def __init__(self, bist_length, bist_random):
        self.set_attributes(locals())

    @property
    def length(self):
        return self.bist_length

    def as_args(self):
        args = ['--bist-length=%d' % self.bist_length]
        if self.bist_random:
            args.append('--bist-random')
        return args


class CustomAccess(Settings):
    def __init__(self, pattern_file):
        self.set_attributes(locals())

    @property
    def pattern(self):
        # we have to load the file to know pattern length, cache it when requested
        if not hasattr(self, '_pattern'):
            path = self.pattern_file
            if not os.path.isabs(path):
                benchmark_dir = os.path.dirname(benchmark.__file__)
                path = os.path.join(benchmark_dir, path)
            self._pattern = load_access_pattern(path)
        return self._pattern

    @property
    def length(self):
        return len(self.pattern)

    def as_args(self):
        return ['--access-pattern=%s' % self.pattern_file]


class BenchmarkConfiguration(Settings):
    def __init__(self, name, sdram_module, sdram_data_width, access_pattern):
        self.set_attributes(locals())

    def as_args(self):
        args = [
            '--sdram-module=%s' % self.sdram_module,
            '--sdram-data-width=%d' % self.sdram_data_width,
        ]
        args += self.access_pattern.as_args()
        return args

    def __eq__(self, other):
        if not isinstance(other, BenchmarkConfiguration):
            return NotImplemented
        return self.as_dict() == other.as_dict()

    @property
    def length(self):
        return self.access_pattern.length

    @classmethod
    def from_dict(cls, d):
        access_cls = CustomAccess if 'pattern_file' in d['access_pattern'] else GeneratedAccess
        d['access_pattern'] = access_cls(**d['access_pattern'])
        return cls(**d)

    @classmethod
    def load_yaml(cls, yaml_file):
        with open(yaml_file) as f:
            description = yaml.safe_load(f)
        configs = []
        for name, desc in description.items():
            desc['name'] = name
            configs.append(cls.from_dict(desc))
        return configs

    def __repr__(self):
        return 'BenchmarkConfiguration(%s)' % self.as_dict()

    @property
    def soc(self):
        if not hasattr(self, '_soc'):
            kwargs = dict(
                sdram_module=self.sdram_module,
                sdram_data_width=self.sdram_data_width,
            )
            if isinstance(self.access_pattern, GeneratedAccess):
                kwargs['bist_length'] = self.access_pattern.bist_length
                kwargs['bist_random'] = self.access_pattern.bist_random
            elif isinstance(self.access_pattern, CustomAccess):
                kwargs['pattern_init'] = self.access_pattern.pattern
            else:
                raise ValueError(self.access_pattern)
            self._soc = LiteDRAMBenchmarkSoC(**kwargs)
        return self._soc

# Benchmark results --------------------------------------------------------------------------------

# constructs python regex named group
def ng(name, regex):
    return r'(?P<{}>{})'.format(name, regex)


def _compiled_pattern(stage, var):
    pattern_fmt = r'{stage}\s+{var}:\s+{value}'
    pattern = pattern_fmt.format(
        stage=stage,
        var=var,
        value=ng('value', '[0-9]+'),
    )
    return re.compile(pattern)
    result = re.search(pattern, benchmark_output)


class BenchmarkResult:
    # pre-compiled patterns for all benchmarks
    patterns = {
        'generator_ticks': _compiled_pattern('BIST-GENERATOR', 'ticks'),
        'checker_errors': _compiled_pattern('BIST-CHECKER', 'errors'),
        'checker_ticks': _compiled_pattern('BIST-CHECKER', 'ticks'),
    }

    @staticmethod
    def find(pattern, output):
        result = pattern.search(output)
        assert result is not None, \
            'Could not find pattern "%s" in output' % (pattern)
        return int(result.group('value'))

    def __init__(self, output):
        self._output = output
        for attr, pattern in self.patterns.items():
            setattr(self, attr, self.find(pattern, output))

    def __repr__(self):
        d = {attr: getattr(self, attr) for attr in self.patterns.keys()}
        return 'BenchmarkResult(%s)' % d

# Results summary ----------------------------------------------------------------------------------

def human_readable(value):
    binary_prefixes = ['', 'k', 'M', 'G', 'T']
    mult = 1.0
    for prefix in binary_prefixes:
        if value * mult < 1024:
            break
        mult /= 1024
    return mult, prefix


def clocks_fmt(clocks):
    return '{:d} clk'.format(int(clocks))


def bandwidth_fmt(bw):
    mult, prefix = human_readable(bw)
    return '{:.1f} {}bps'.format(bw * mult, prefix)


def efficiency_fmt(eff):
    return '{:.1f} %'.format(eff * 100)


class ResultsSummary:
    def __init__(self, run_data, plots_dir='plots'):
        self.plots_dir = plots_dir

        # filter out failures
        self.failed_configs = [data.config for data in run_data if data.result is None]
        run_data = [data for data in run_data if data.result is not None]

        # gather results into tabular data
        column_mappings = {
            'name':             lambda d: d.config.name,
            'sdram_module':     lambda d: d.config.sdram_module,
            'sdram_data_width': lambda d: d.config.sdram_data_width,
            'bist_length':      lambda d: getattr(d.config.access_pattern, 'bist_length', None),
            'bist_random':      lambda d: getattr(d.config.access_pattern, 'bist_random', None),
            'pattern_file':     lambda d: getattr(d.config.access_pattern, 'pattern_file', None),
            'length':           lambda d: d.config.length,
            'generator_ticks':  lambda d: d.result.generator_ticks,
            'checker_errors':   lambda d: d.result.checker_errors,
            'checker_ticks':    lambda d: d.result.checker_ticks,
            'ctrl_data_width':  lambda d: d.config.soc.sdram.controller.interface.data_width,
            'clk_freq':         lambda d: d.config.soc.sdrphy.module.clk_freq,
        }
        columns = {name: [mapping(data) for data in run_data] for name, mapping, in column_mappings.items()}
        self.df = df = pd.DataFrame(columns)

        # replace None with NaN
        df.fillna(value=np.nan, inplace=True)

        # compute other metrics based on ticks and configuration parameters
        df['clk_period'] = 1 / df['clk_freq']
        df['write_bandwidth'] = (8 * df['length']) / (df['generator_ticks'] * df['clk_period'])
        df['read_bandwidth']  = (8 * df['length']) / (df['checker_ticks'] * df['clk_period'])

        df['cmd_count'] = df['length'] / (df['ctrl_data_width'] / 8)
        df['write_efficiency'] = df['cmd_count'] / df['generator_ticks']
        df['read_efficiency'] = df['cmd_count'] / df['checker_ticks']

        df['write_latency'] = df[df['bist_length'] == 1]['generator_ticks']
        df['read_latency'] = df[df['bist_length'] == 1]['checker_ticks']

        # boolean distinction between latency benchmarks and sequence benchmarks,
        # as thier results differ significanly
        df['is_latency'] = ~pd.isna(df['write_latency'])
        assert (df['is_latency'] == ~pd.isna(df['read_latency'])).all(), \
            'write_latency and read_latency should both have a value or both be NaN'

        # data formatting for text summary
        self.text_formatters = {
            'write_bandwidth':  bandwidth_fmt,
            'read_bandwidth':   bandwidth_fmt,
            'write_efficiency': efficiency_fmt,
            'read_efficiency':  efficiency_fmt,
            'write_latency':    clocks_fmt,
            'read_latency':     clocks_fmt,
        }

        # data formatting for plot summary
        self.plot_xticks_formatters = {
            'write_bandwidth':  FuncFormatter(lambda value, pos: bandwidth_fmt(value)),
            'read_bandwidth':   FuncFormatter(lambda value, pos: bandwidth_fmt(value)),
            'write_efficiency': PercentFormatter(1.0),
            'read_efficiency':  PercentFormatter(1.0),
            'write_latency':    ScalarFormatter(),
            'read_latency':     ScalarFormatter(),
        }

    def header(self, text):
        return '===> {}'.format(text)

    def print_df(self, title, df):
        # make sure all data will be shown
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None):
            print(self.header(title + ':'))
            print(df)

    def get_summary(self, mask=None, columns=None, column_formatting=None, sort_kwargs=None):
        # work on a copy
        df = self.df.copy()

        if sort_kwargs is not None:
            df = df.sort_values(**sort_kwargs)

        if column_formatting is not None:
            for column, mapping in column_formatting.items():
                old = '_{}'.format(column)
                df[old] = df[column].copy()
                df[column] = df[column].map(lambda value: mapping(value) if not pd.isna(value) else value)

        df = df[mask] if mask is not None else df
        df = df[columns] if columns is not None else df

        return df

    def text_summary(self):
        for title, df in self.groupped_results():
            self.print_df(title, df)
            print()

    def groupped_results(self, formatted=True):
        df = self.df

        formatters = self.text_formatters if formatted else {}

        common_columns = ['name', 'sdram_module', 'sdram_data_width']
        latency_columns = ['write_latency', 'read_latency']
        performance_columns = ['write_bandwidth', 'read_bandwidth', 'write_efficiency', 'read_efficiency']

        yield 'Latency', self.get_summary(
            mask=df['is_latency'] == True,
            columns=common_columns + latency_columns,
            column_formatting=formatters,
        )
        #  yield 'Any access pattern', self.get_summary(
        #      mask=(df['is_latency'] == False),
        #      columns=common_columns + performance_columns + ['length', 'bist_random', 'pattern_file'],
        #      column_formatting=self.text_formatters,
            #  **kwargs,
        #  ),
        yield 'Custom access pattern', self.get_summary(
            mask=(df['is_latency'] == False) & (~pd.isna(df['pattern_file'])),
            columns=common_columns + performance_columns + ['length', 'pattern_file'],
            column_formatting=formatters,
        ),
        yield 'Sequential access pattern', self.get_summary(
            mask=(df['is_latency'] == False) & (pd.isna(df['pattern_file'])) & (df['bist_random'] == False),
            columns=common_columns + performance_columns + ['bist_length'], # could be length
            column_formatting=formatters,
        ),
        yield 'Random access pattern', self.get_summary(
            mask=(df['is_latency'] == False) & (pd.isna(df['pattern_file'])) & (df['bist_random'] == True),
            columns=common_columns + performance_columns + ['bist_length'],
            column_formatting=formatters,
        ),

    def plot_summary(self, plots_dir='plots', backend='Agg', theme='default', save_format='png', **savefig_kw):
        matplotlib.use(backend)
        import matplotlib.pyplot as plt
        plt.style.use(theme)

        for title, df in self.groupped_results(formatted=False):
            for column in self.plot_xticks_formatters.keys():
                if column not in df.columns or df[column].empty:
                    continue
                axis = self.plot_df(title, df, column)

                # construct path
                def path_name(name):
                    return name.lower().replace(' ', '_')

                filename = '{}.{}'.format(path_name(column), save_format)
                path = os.path.join(plots_dir, path_name(title), filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)

                # save figure
                axis.get_figure().savefig(path, **savefig_kw)

        if backend != 'Agg':
            plt.show()

    def plot_df(self, title, df, column, save_format='png', save_filename=None):
        if save_filename is None:
            save_filename = os.path.join(self.plots_dir, title.lower().replace(' ', '_'))

        axis = df.plot(kind='barh', x='name', y=column, title=title, grid=True, legend=False)
        if column in self.plot_xticks_formatters:
            axis.xaxis.set_major_formatter(self.plot_xticks_formatters[column])
            axis.xaxis.set_tick_params(rotation=15)
        axis.spines['top'].set_visible(False)
        axis.spines['right'].set_visible(False)
        axis.set_axisbelow(True)

        #  # force xmax to 100%
        #  if column in ['write_efficiency', 'read_efficiency']:
        #      axis.set_xlim(right=1.0)

        return axis

    def failuers_summary(self):
        if len(self.failed_configs) > 0:
            print(self.header('Failures:'))
            for config in self.failed_configs:
                print('  {}: {}'.format(config.name, config.as_args()))
        else:
            print(self.header('All benchmarks ok.'))

# Run ----------------------------------------------------------------------------------------------

class RunCache(list):
    RunData = namedtuple('RunData', ['config', 'result'])

    def dump_json(self, filename):
        json_data = [{'config': data.config.as_dict(), 'output': getattr(data.result, '_output', None) } for data in self]
        with open(filename, 'w') as f:
            json.dump(json_data, f)

    @classmethod
    def load_json(cls, filename):
        with open(filename, 'r') as f:
            json_data = json.load(f)
        loaded = []
        for data in json_data:
            config = BenchmarkConfiguration.from_dict(data['config'])
            result = BenchmarkResult(data['output']) if data['output'] is not None else None
            loaded.append(cls.RunData(config=config, result=result))
        return loaded


def run_python(script, args):
    command = ['python3', script, *args]
    proc = subprocess.run(command, stdout=subprocess.PIPE, cwd=os.path.dirname(script))
    return str(proc.stdout)


def run_single_benchmark(func_args):
    config, output_dir, ignore_failures = func_args
    # run as separate process, because else we cannot capture all output from verilator
    print('  {}: {}'.format(config.name, ' '.join(config.as_args())))
    try:
        output = run_python(benchmark.__file__, config.as_args() + ['--output-dir', output_dir])
        result = BenchmarkResult(output)
        # exit if checker had any read error
        if result.checker_errors != 0:
            raise RuntimeError('Error during benchmark: checker_errors = {}, args = {}'.format(
                result.checker_errors, args
            ))
    except Exception as e:
        if ignore_failures:
            print('  {}: ERROR: {}'.format(config.name, e))
            return None
        else:
            raise
    print('  {}: ok'.format(config.name))
    return result


def run_benchmarks(configurations, output_base_dir, njobs, ignore_failures):
    print('Running {:d} benchmarks ...'.format(len(configurations)))
    if njobs == 1:
        results = [run_single_benchmark((config, output_base_dir, ignore_failures)) for config in configurations]
    else:
        import multiprocessing
        func_args = [(config, os.path.join(output_base_dir, config.name.replace(' ', '_')), ignore_failures)
                     for config in configurations]
        if njobs == 0:
            njobs = os.cpu_count()
        print('Using {:d} parallel jobs'.format(njobs))
        with multiprocessing.Pool(processes=njobs) as pool:
            results = pool.map(run_single_benchmark, func_args)
    run_data = [RunCache.RunData(config, result) for config, result in zip(configurations, results)]
    return run_data


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
    parser.add_argument('--fail-fast',        action='store_true', help='Exit on any benchmark error, do not continue')
    parser.add_argument('--output-dir',       default='build',     help='Directory to store benchmark build output')
    parser.add_argument('--njobs',            default=0, type=int, help='Use N parallel jobs to run benchmarks (default=0, which uses CPU count)')
    parser.add_argument('--results-cache',                         help="""Use given JSON file as results cache. If the file exists,
                                                                           it will be loaded instead of running actual benchmarks,
                                                                           else benchmarks will be run normally, and then saved
                                                                           to the given file. This allows to easily rerun the script
                                                                           to generate different summary without having to rerun benchmarks.""")
    args = parser.parse_args(argv)

    if not args.results_cache and not _summary:
        print('Summary not available and not running with --results-cache - run would not produce any results! Aborting.',
              file=sys.stderr)
        sys.exit(1)

    # load and filter configurations
    configurations = BenchmarkConfiguration.load_yaml(args.config)
    filters = {
        'regex':     lambda config: re.search(args.regex, config.name),
        'not_regex': lambda config: not re.search(args.not_regex, config.name),
        'names':     lambda config: config.name in args.names,
    }
    for arg, f in filters.items():
        if getattr(args, arg):
            configurations = filter(f, configurations)
    configurations = list(configurations)

    # load outputs from cache if it exsits
    cache_exists = args.results_cache and os.path.isfile(args.results_cache)
    if args.results_cache and cache_exists:
        cache = RunCache.load_json(args.results_cache)

        # take only those that match configurations
        names_to_load = [c.name for c in configurations]
        run_data = [data for  data in cache if data.config.name in names_to_load]
    else:  # run all the benchmarks normally
        run_data = run_benchmarks(configurations, args.output_dir, args.njobs, not args.fail_fast)

    # store outputs in cache
    if args.results_cache and not cache_exists:
        cache = RunCache(run_data)
        cache.dump_json(args.results_cache)

    # display summary
    if _summary:
        summary = ResultsSummary(run_data)
        summary.text_summary()
        summary.failuers_summary()
        if args.plot:
            summary.plot_summary(
                plots_dir=args.plot_output_dir,
                backend=args.plot_backend,
                theme=args.plot_theme,
                save_format=args.plot_format,
                transparent=args.plot_transparent,
            )


if __name__ == "__main__":
    main()
