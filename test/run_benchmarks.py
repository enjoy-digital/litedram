#!/usr/bin/env python3

#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# Limitations/TODO
# - add configurable sdram_clk_freq - using hardcoded value now
# - sdram_controller_data_width - try to expose the value from litex_sim to avoid duplicated code

import os
import re
import sys
import json
import argparse
import datetime
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
    print("[WARNING] Results summary not available:", e, file=sys.stderr)

from litex.tools.litex_sim import get_sdram_phy_settings, sdram_module_nphases
from litedram import modules as litedram_modules
from litedram.common import Settings as _Settings

from test import benchmark

# Benchmark configuration --------------------------------------------------------------------------

class Settings(_Settings):
    def as_dict(self):
        d = dict()
        for attr, value in vars(self).items():
            if attr == "self" or attr.startswith("_"):
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
        args = ["--bist-length=%d" % self.bist_length]
        if self.bist_random:
            args.append("--bist-random")
        return args


class CustomAccess(Settings):
    def __init__(self, pattern_file):
        self.set_attributes(locals())

    @property
    def pattern(self):
        # We have to load the file to know pattern length, cache it when requested
        if not hasattr(self, "_pattern"):
            path = self.pattern_file
            if not os.path.isabs(path):
                benchmark_dir = os.path.dirname(benchmark.__file__)
                path = os.path.join(benchmark_dir, path)
            self._pattern = benchmark.load_access_pattern(path)
        return self._pattern

    @property
    def length(self):
        return len(self.pattern)

    def as_args(self):
        return ["--access-pattern=%s" % self.pattern_file]


class BenchmarkConfiguration(Settings):
    def __init__(self, name, sdram_module, sdram_data_width, bist_alternating,
                 num_generators, num_checkers, access_pattern):
        self.set_attributes(locals())

    def as_args(self):
        args = [
            "--sdram-module=%s" % self.sdram_module,
            "--sdram-data-width=%d" % self.sdram_data_width,
            "--num-generators=%d" % self.num_generators,
            "--num-checkers=%d" % self.num_checkers,
        ]
        if self.bist_alternating:
            args.append("--bist-alternating")
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
        access_cls = CustomAccess if "pattern_file" in d["access_pattern"] else GeneratedAccess
        d["access_pattern"] = access_cls(**d["access_pattern"])
        return cls(**d)

    @classmethod
    def load_yaml(cls, yaml_file):
        with open(yaml_file) as f:
            description = yaml.safe_load(f)
        configs = []
        for name, desc in description.items():
            desc["name"] = name
            configs.append(cls.from_dict(desc))
        return configs

    def __repr__(self):
        return "BenchmarkConfiguration(%s)" % self.as_dict()

    @property
    def sdram_clk_freq(self):
        return 100e6  # FIXME: Value of 100MHz is hardcoded in litex_sim

    @property
    def sdram_memtype(self):
        # Use values from module class (no need to instantiate it)
        sdram_module_cls = getattr(litedram_modules, self.sdram_module)
        return sdram_module_cls.memtype

    @property
    def sdram_controller_data_width(self):
        nphases = sdram_module_nphases[self.sdram_memtype]
        dfi_databits = self.sdram_data_width * (1 if self.sdram_memtype == "SDR" else 2)
        return dfi_databits * nphases

# Benchmark results --------------------------------------------------------------------------------

# Constructs python regex named group
def ng(name, regex):
    return r"(?P<{}>{})".format(name, regex)


def _compiled_pattern(stage, var):
    pattern_fmt = r"{stage}\s+{var}:\s+{value}"
    pattern = pattern_fmt.format(
        stage = stage,
        var   = var,
        value = ng("value", "[0-9]+"),
    )
    return re.compile(pattern)
    result = re.search(pattern, benchmark_output)


class BenchmarkResult:
    # Pre-compiled patterns for all benchmarks
    patterns = {
        "generator_ticks": _compiled_pattern("BIST-GENERATOR", "ticks"),
        "checker_errors":  _compiled_pattern("BIST-CHECKER", "errors"),
        "checker_ticks":   _compiled_pattern("BIST-CHECKER", "ticks"),
    }

    @staticmethod
    def find(pattern, output):
        result = pattern.search(output)
        assert result is not None, \
            "Could not find pattern {} in output".format(pattern)
        return int(result.group("value"))

    def __init__(self, output):
        self._output = output
        for attr, pattern in self.patterns.items():
            setattr(self, attr, self.find(pattern, output))

    def __repr__(self):
        d = {attr: getattr(self, attr) for attr in self.patterns.keys()}
        return "BenchmarkResult(%s)" % d

# Results summary ----------------------------------------------------------------------------------

def human_readable(value):
    binary_prefixes = ["", "k", "M", "G", "T"]
    mult = 1.0
    for prefix in binary_prefixes:
        if value * mult < 1024:
            break
        mult /= 1024
    return mult, prefix


def clocks_fmt(clocks):
    return "{:d} clk".format(int(clocks))


def bandwidth_fmt(bw):
    mult, prefix = human_readable(bw)
    return "{:.1f} {}bps".format(bw * mult, prefix)


def efficiency_fmt(eff):
    return "{:.1f} %".format(eff * 100)


def get_git_file_path(filename):
    cmd  = ["git", "ls-files", "--full-name", filename]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, cwd=os.path.dirname(__file__))
    return proc.stdout.decode().strip() if proc.returncode == 0 else ""


def get_git_revision_hash(short=False):
    short = ["--short"] if short else []
    cmd   = ["git", "rev-parse", *short, "HEAD"]
    proc  = subprocess.run(cmd, stdout=subprocess.PIPE, cwd=os.path.dirname(__file__))
    return proc.stdout.decode().strip() if proc.returncode == 0 else ""


class ResultsSummary:
    def __init__(self, run_data, plots_dir="plots"):
        self.plots_dir = plots_dir

        # Because .sdram_controller_data_width may fail for unimplemented modules
        def except_none(func):
            try:
                return func()
            except:
                return None

        # Gather results into tabular data
        column_mappings = {
            "name":             lambda d: d.config.name,
            "sdram_module":     lambda d: d.config.sdram_module,
            "sdram_data_width": lambda d: d.config.sdram_data_width,
            "bist_alternating": lambda d: d.config.bist_alternating,
            "num_generators":   lambda d: d.config.num_generators,
            "num_checkers":     lambda d: d.config.num_checkers,
            "bist_length":      lambda d: getattr(d.config.access_pattern, "bist_length", None),
            "bist_random":      lambda d: getattr(d.config.access_pattern, "bist_random", None),
            "pattern_file":     lambda d: getattr(d.config.access_pattern, "pattern_file", None),
            "length":           lambda d: d.config.length,
            "generator_ticks":  lambda d: getattr(d.result, "generator_ticks", None),  # None means benchmark failure
            "checker_errors":   lambda d: getattr(d.result, "checker_errors", None),
            "checker_ticks":    lambda d: getattr(d.result, "checker_ticks", None),
            "ctrl_data_width":  lambda d: except_none(lambda: d.config.sdram_controller_data_width),
            "sdram_memtype":    lambda d: except_none(lambda: d.config.sdram_memtype),
            "clk_freq":         lambda d: d.config.sdram_clk_freq,
        }
        columns = {name: [mapping(data) for data in run_data] for name, mapping, in column_mappings.items()}
        self._df = df = pd.DataFrame(columns)

        # Replace None with NaN
        df.fillna(value=np.nan, inplace=True)

        # Compute other metrics based on ticks and configuration parameters
        df["clk_period"] = 1 / df["clk_freq"]
        # Bandwidth is the number of bits per time
        # in case with N generators/checkers we actually process N times more data
        df["write_bandwidth"] = (8 * df["length"] * df["num_generators"]) / (df["generator_ticks"] * df["clk_period"])
        df["read_bandwidth"]  = (8 * df["length"] * df["num_checkers"]) / (df["checker_ticks"] * df["clk_period"])

        # Efficiency calculated as number of write/read commands to number of cycles spent on writing/reading (ticks)
        # for multiple generators/checkers multiply by their number
        df["cmd_count"]        = df["length"] / (df["ctrl_data_width"] / 8)
        df["write_efficiency"] = df["cmd_count"] * df["num_generators"] / df["generator_ticks"]
        df["read_efficiency"]  = df["cmd_count"] * df["num_checkers"] / df["checker_ticks"]

        df["write_latency"] = df[df["bist_length"] == 1]["generator_ticks"]
        df["read_latency"]  = df[df["bist_length"] == 1]["checker_ticks"]

        # Boolean distinction between latency benchmarks and sequence benchmarks,
        # as thier results differ significanly
        df["is_latency"] = ~pd.isna(df["write_latency"])
        assert (df["is_latency"] == ~pd.isna(df["read_latency"])).all(), \
            "write_latency and read_latency should both have a value or both be NaN"

        # Data formatting for text summary
        self.text_formatters = {
            "write_bandwidth":  bandwidth_fmt,
            "read_bandwidth":   bandwidth_fmt,
            "write_efficiency": efficiency_fmt,
            "read_efficiency":  efficiency_fmt,
            "write_latency":    clocks_fmt,
            "read_latency":     clocks_fmt,
        }

        # Data formatting for plot summary
        self.plot_xticks_formatters = {
            "write_bandwidth":  FuncFormatter(lambda value, pos: bandwidth_fmt(value)),
            "read_bandwidth":   FuncFormatter(lambda value, pos: bandwidth_fmt(value)),
            "write_efficiency": PercentFormatter(1.0),
            "read_efficiency":  PercentFormatter(1.0),
            "write_latency":    ScalarFormatter(),
            "read_latency":     ScalarFormatter(),
        }

    def df(self, ok=True, failures=False):
        is_failure = lambda df: pd.isna(df["generator_ticks"]) | pd.isna(df["checker_ticks"]) | pd.isna(df["checker_errors"])
        df = self._df
        if not ok:  # remove ok
            is_ok = ~is_failure(df)
            df = df[~is_ok]
        if not failures:  # remove failures
            df = df[~is_failure(df)]
        return df

    def header(self, text):
        return "===> {}".format(text)

    def print_df(self, title, df):
        # Make sure all data will be shown
        with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", None):
            print(self.header(title + ":"))
            print(df)

    def get_summary(self, df, mask=None, columns=None, column_formatting=None, sort_kwargs=None):
        # Work on a copy
        df = df.copy()

        if sort_kwargs is not None:
            df = df.sort_values(**sort_kwargs)

        if column_formatting is not None:
            for column, mapping in column_formatting.items():
                old        = "_{}".format(column)
                df[old]    = df[column].copy()
                df[column] = df[column].map(lambda value: mapping(value) if not pd.isna(value) else value)

        df = df[mask] if mask is not None else df
        df = df[columns] if columns is not None else df

        return df

    def text_summary(self):
        for title, df in self.groupped_results():
            self.print_df(title, df)
            print()

    def html_summary(self, output_dir):
        import jinja2

        tables = {}
        names  = {}
        for title, df in self.groupped_results():
            table_id = title.lower().replace(" ", "_")

            tables[table_id] = df.to_html(table_id=table_id, border=0)
            names[table_id]  = title

        template_dir = os.path.join(os.path.dirname(__file__), "summary")
        env          = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        template     = env.get_template("summary.html.jinja2")

        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "summary.html"), "w") as f:
            f.write(template.render(
                title           = "LiteDRAM benchmarks summary",
                tables          = tables,
                names           = names,
                script_path     = get_git_file_path(__file__),
                revision        = get_git_revision_hash(),
                revision_short  = get_git_revision_hash(short=True),
                generation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))

    def groupped_results(self, formatters=None):
        df = self.df()

        if formatters is None:
            formatters = self.text_formatters

        common_columns = [
            "name", "sdram_module", "sdram_memtype", "sdram_data_width",
            "bist_alternating", "num_generators", "num_checkers"
        ]
        latency_columns = ["write_latency", "read_latency"]
        performance_columns = [
            "write_bandwidth", "read_bandwidth", "write_efficiency", "read_efficiency"
        ]
        failure_columns = [
            "bist_length", "bist_random", "pattern_file", "length",
            "generator_ticks", "checker_errors", "checker_ticks"
        ]

        yield "Latency", self.get_summary(df,
            mask              = df["is_latency"] == True,
            columns           = common_columns + latency_columns,
            column_formatting = formatters,
        )
        yield "Custom access pattern", self.get_summary(df,
            mask              = (df["is_latency"] == False) & (~pd.isna(df["pattern_file"])),
            columns           = common_columns + ["length", "pattern_file"] + performance_columns,
            column_formatting = formatters,
        ),
        yield "Sequential access pattern", self.get_summary(df,
            mask              = (df["is_latency"] == False) & (pd.isna(df["pattern_file"])) & (df["bist_random"] == False),
            columns           = common_columns + ["bist_length"] + performance_columns, # could be length
            column_formatting = formatters,
        ),
        yield "Random access pattern", self.get_summary(df,
            mask              = (df["is_latency"] == False) & (pd.isna(df["pattern_file"])) & (df["bist_random"] == True),
            columns           = common_columns + ["bist_length"] + performance_columns,
            column_formatting = formatters,
        ),
        yield "Failures", self.get_summary(self.df(ok=False, failures=True),
            columns           = common_columns + failure_columns,
            column_formatting = None,
        ),

    def plot_summary(self, plots_dir="plots", backend="Agg", theme="default", save_format="png", **savefig_kw):
        matplotlib.use(backend)
        import matplotlib.pyplot as plt
        plt.style.use(theme)

        for title, df in self.groupped_results(formatters={}):
            for column in self.plot_xticks_formatters.keys():
                if column not in df.columns or df[column].empty:
                    continue
                axis = self.plot_df(title, df, column)

                # construct path
                def path_name(name):
                    return name.lower().replace(" ", "_")

                filename = "{}.{}".format(path_name(column), save_format)
                path     = os.path.join(plots_dir, path_name(title), filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)

                # save figure
                axis.get_figure().savefig(path, **savefig_kw)

        if backend != "Agg":
            plt.show()

    def plot_df(self, title, df, column, fig_width=6.4, fig_min_height=2.2, save_format="png", save_filename=None):
        if save_filename is None:
            save_filename = os.path.join(self.plots_dir, title.lower().replace(" ", "_"))

        axis = df.plot(kind="barh", x="name", y=column, title=title, grid=True, legend=False)
        fig = axis.get_figure()

        if column in self.plot_xticks_formatters:
            axis.xaxis.set_major_formatter(self.plot_xticks_formatters[column])
            axis.xaxis.set_tick_params(rotation=15)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.set_axisbelow(True)
        axis.set_ylabel("")  # No need for label as we have only one series

        # For large number of rows, the bar labels start overlapping
        # use fixed ratio between number of rows and height of figure
        n_ok = 16
        new_height = (fig_width / n_ok) * len(df)
        fig.set_size_inches(fig_width, max(fig_min_height, new_height))

        # Remove empty spaces
        fig.tight_layout()

        return axis

# Run ----------------------------------------------------------------------------------------------

class RunCache(list):
    RunData = namedtuple("RunData", ["config", "result"])

    def dump_json(self, filename):
        json_data = [{"config": data.config.as_dict(), "output": getattr(data.result, "_output", None) } for data in self]
        with open(filename, "w") as f:
            json.dump(json_data, f)

    @classmethod
    def load_json(cls, filename):
        with open(filename, "r") as f:
            json_data = json.load(f)
        loaded = []
        for data in json_data:
            config = BenchmarkConfiguration.from_dict(data["config"])
            result = BenchmarkResult(data["output"]) if data["output"] is not None else None
            loaded.append(cls.RunData(config=config, result=result))
        return loaded


def run_python(script, args, **kwargs):
    command = ["python3", script, *args]
    proc = subprocess.run(command, stdout=subprocess.PIPE, cwd=os.path.dirname(script), **kwargs)
    return str(proc.stdout)


BenchmarkArgs = namedtuple("BenchmarkArgs", ["config", "output_dir", "ignore_failures", "timeout"])


def run_single_benchmark(fargs):
    # Run as separate process, because else we cannot capture all output from verilator
    print("  {}: {}".format(fargs.config.name, " ".join(fargs.config.as_args())))
    try:
        args   = fargs.config.as_args() + ["--output-dir", fargs.output_dir, "--log-level", "warning"]
        output = run_python(benchmark.__file__, args, timeout=fargs.timeout)
        result = BenchmarkResult(output)
        # Exit if checker had any read error
        if result.checker_errors != 0:
            raise RuntimeError("Error during benchmark: checker_errors = {}, args = {}".format(
                result.checker_errors, fargs.config.as_args()
            ))
    except Exception as e:
        if fargs.ignore_failures:
            print("  {}: ERROR: {}".format(fargs.config.name, e))
            return None
        else:
            raise
    print("  {}: ok".format(fargs.config.name))
    return result


InQueueItem = namedtuple("InQueueItem", ["index", "config"])
OutQueueItem = namedtuple("OutQueueItem", ["index", "result"])


def run_parallel(configurations, output_base_dir, njobs, ignore_failures, timeout):
    from multiprocessing import Process, Queue
    import queue

    def worker(in_queue, out_queue, out_dir):
        while True:
            in_item = in_queue.get()
            if in_item is None:
                return
            fargs  = BenchmarkArgs(in_item.config, out_dir, ignore_failures, timeout)
            result = run_single_benchmark(fargs)
            out_queue.put(OutQueueItem(in_item.index, result))

    if njobs == 0:
        njobs = os.cpu_count()
    print("Using {:d} parallel jobs".format(njobs))

    # Use one directory per worker, as running each benchmark in separate directory
    # takes too much disk space (~2GB per 100 benchmarks)
    dir_pool = [os.path.join(output_base_dir, "worker_%02d" % i) for i in range(njobs)]

    in_queue, out_queue = Queue(), Queue()
    workers = [Process(target=worker, args=(in_queue, out_queue, dir)) for dir in dir_pool]
    for w in workers:
        w.start()

    # Put all benchmark configurations with index to retrieve them in order
    for i, config in enumerate(configurations):
        in_queue.put(InQueueItem(i, config))

    # Send "finish signal" for each worker
    for _ in workers:
        in_queue.put(None)

    # Retrieve results in proper order
    out_items = [out_queue.get() for _ in configurations]
    results   = [out.result for out in sorted(out_items, key=lambda o: o.index)]

    for p in workers:
        p.join()

    return results


def run_benchmarks(configurations, output_base_dir, njobs, ignore_failures, timeout):
    print("Running {:d} benchmarks ...".format(len(configurations)))
    if njobs == 1:
        results = [run_single_benchmark(BenchmarkArgs(config, output_base_dir, ignore_failures, timeout))
                   for config in configurations]
    else:
        results = run_parallel(configurations, output_base_dir, njobs, ignore_failures, timeout)
    run_data = [RunCache.RunData(config, result) for config, result in zip(configurations, results)]
    return run_data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run LiteDRAM benchmarks and collect the results.")
    parser.add_argument("config",                                  help="YAML config file")
    parser.add_argument("--names",            nargs="*",           help="Limit benchmarks to given names")
    parser.add_argument("--regex",                                 help="Limit benchmarks to names matching the regex")
    parser.add_argument("--not-regex",                             help="Limit benchmarks to names not matching the regex")
    parser.add_argument("--html",             action="store_true", help="Generate HTML summary")
    parser.add_argument("--html-output-dir",  default="html",      help="Output directory for generated HTML")
    parser.add_argument("--plot",             action="store_true", help="Generate plots with results summary")
    parser.add_argument("--plot-format",      default="png",       help="Specify plots file format (default=png)")
    parser.add_argument("--plot-backend",     default="Agg",       help="Optionally specify matplotlib GUI backend")
    parser.add_argument("--plot-transparent", action="store_true", help="Use transparent background when saving plots")
    parser.add_argument("--plot-output-dir",  default="plots",     help="Specify where to save the plots")
    parser.add_argument("--plot-theme",       default="default",   help="Use different matplotlib theme")
    parser.add_argument("--fail-fast",        action="store_true", help="Exit on any benchmark error, do not continue")
    parser.add_argument("--output-dir",       default="build",     help="Directory to store benchmark build output")
    parser.add_argument("--njobs",            default=0, type=int, help="Use N parallel jobs to run benchmarks (default=0, which uses CPU count)")
    parser.add_argument("--heartbeat",        default=0, type=int, help="Print heartbeat message with given interval (default=0 => never)")
    parser.add_argument("--timeout",          default=None,        help="Set timeout for a single benchmark")
    parser.add_argument("--results-cache",                         help="""Use given JSON file as results cache. If the file exists,
                                                                           it will be loaded instead of running actual benchmarks,
                                                                           else benchmarks will be run normally, and then saved
                                                                           to the given file. This allows to easily rerun the script
                                                                           to generate different summary without having to rerun benchmarks.""")
    args = parser.parse_args(argv)

    if not args.results_cache and not _summary:
        print("Summary not available and not running with --results-cache - run would not produce any results! Aborting.",
              file=sys.stderr)
        sys.exit(1)

    # Load and filter configurations
    configurations = BenchmarkConfiguration.load_yaml(args.config)
    filters = {
        "regex":     lambda config: re.search(args.regex, config.name),
        "not_regex": lambda config: not re.search(args.not_regex, config.name),
        "names":     lambda config: config.name in args.names,
    }
    for arg, f in filters.items():
        if getattr(args, arg):
            configurations = filter(f, configurations)
    configurations = list(configurations)

    # Load outputs from cache if it exsits
    cache_exists = args.results_cache and os.path.isfile(args.results_cache)
    if args.results_cache and cache_exists:
        cache = RunCache.load_json(args.results_cache)

        # Take only those that match configurations
        names_to_load = [c.name for c in configurations]
        run_data = [data for  data in cache if data.config.name in names_to_load]
    else:  # Run all the benchmarks normally
        if args.heartbeat:
            heartbeat_cmd = ["/bin/sh", "-c", "while true; do sleep %d; echo Heartbeat...; done" % args.heartbeat]
            heartbeat = subprocess.Popen(heartbeat_cmd)
        if args.timeout is not None:
            args.timeout = int(args.timeout)
        run_data = run_benchmarks(configurations, args.output_dir, args.njobs, not args.fail_fast, args.timeout)
        if args.heartbeat:
            heartbeat.kill()

    # Store outputs in cache
    if args.results_cache and not cache_exists:
        cache = RunCache(run_data)
        cache.dump_json(args.results_cache)

    # Display summary
    if _summary:
        summary = ResultsSummary(run_data)
        summary.text_summary()
        if args.html:
            summary.html_summary(args.html_output_dir)
        if args.plot:
            summary.plot_summary(
                plots_dir=args.plot_output_dir,
                backend=args.plot_backend,
                theme=args.plot_theme,
                save_format=args.plot_format,
                transparent=args.plot_transparent,
            )

    # Exit with error when there is no single benchmark that succeeded
    succeeded = sum(1 if d.result is not None else 0 for d in run_data)
    if succeeded == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
