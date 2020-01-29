#!/usr/bin/env python3

# This file is Copyright (c) 2020 Jędrzej Boczar <jboczar@antmicro.com>
# License: BSD

import re
import subprocess

from litedram.common import Settings


# constructs python regex named group
def ng(name, regex):
    return r'(?P<{}>{})'.format(name, regex)


class BenchmarkConfiguration(Settings):
    def __init__(self, sdram_module, sdram_data_width, bist_base, bist_length, bist_random):
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


def run_benchmark(args):
    command = ['python3', 'benchmark.py', *args]
    proc = subprocess.run(command, capture_output=True, text=True, check=True)
    return proc.stdout


configurations = [
    BenchmarkConfiguration('MT48LC16M16', 32, 0, 4096,  True),
    BenchmarkConfiguration('MT48LC16M16', 32, 0, 4096, False),
    BenchmarkConfiguration('MT48LC16M16', 32, 0,  512, False),
    BenchmarkConfiguration('MT41K128M16',  8, 0, 1024, False),
    BenchmarkConfiguration('MT41K128M16', 16, 0, 1024, False),
    BenchmarkConfiguration('MT41K128M16', 32, 0, 1024, False),
]


results = []
for config in configurations:
    args = config.as_args()
    print('Benchmark: %s' % ' '.join(args))

    result = BenchmarkResult(config, run_benchmark(args))
    results.append(result)

    print("""\
  generator_ticks  = {:d}
  checker_ticks    = {:d}
  checker_errors   = {:d}
    """.rstrip().format(
        result.generator_ticks,
        result.checker_ticks,
        result.checker_errors,
    ))
