#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import re
import pprint
import itertools
from collections import defaultdict
from typing import Mapping, Sequence

from migen import *

from litex.gen.sim.core import run_simulation as _run_simulation

from litedram.phy import dfi
from litedram.phy.utils import bit, chunks

BOLD = '\033[1m'
HIGHLIGHT = '\033[91m'
CLEAR = '\033[0m'

def highlight(s, hl=True):
    return BOLD + (HIGHLIGHT if hl else '') + s + CLEAR


def run_simulation(dut, generators, clocks, debug_clocks=False, **kwargs):
    """Wrapper that can be used to easily debug clock configuration"""

    if not isinstance(generators, dict):
        assert "sys" in clocks
    else:
        for clk in generators:
            assert clk in clocks, clk

    if debug_clocks:
        class DUT(Module):
            def __init__(self, dut):
                self.submodules.dut = dut
                for clk in clocks:
                    setattr(self.clock_domains, "cd_{}".format(clk), ClockDomain(clk))
                    cd = getattr(self, 'cd_{}'.format(clk))
                    self.comb += cd.rst.eq(0)

                    s = Signal(4, name='dbg_{}'.format(clk))
                    sd = getattr(self.sync, clk)
                    sd += s.eq(s + 1)
        dut = DUT(dut)

    _run_simulation(dut, generators, clocks, **kwargs)


def dfi_data_to_dq(dq_i, dfi_phases, dfi_name, nphases, databits, burst):
    # e.g. for nphases=8 DDR (burst=16), data on DQ should go in a pattern:
    # dq0: p0.wrdata[0], p0.wrdata[16], p1.wrdata[0], p1.wrdata[16], ...
    # dq1: p0.wrdata[1], p0.wrdata[17], p1.wrdata[1], p1.wrdata[17], ...
    assert burst % nphases == 0
    for p in range(nphases):
        data = dfi_phases[p][dfi_name]
        for i in range(burst//nphases):
            yield bit(i*databits + dq_i, data)

def dq_pattern(i, dfi_data, dfi_name, **kwargs):
    return ''.join(str(v) for v in dfi_data_to_dq(i, dfi_data, dfi_name, **kwargs))


class PadsHistory(defaultdict):
    """Storage for hisotry of per-pad values with human-readable printing

    Keys are pad names and for each pad, the history of its values is represented as a string
    of '0' and '1'. Additionally 'x' is used for any value and ' ' is ignored.
    """
    def __init__(self):
        super().__init__(str)

    def format(self, hl_cycle=None, hl_signal=None, underline_cycle=False, key_strw=None, chunk_size=8):
        if key_strw is None:
            key_strw = max(len(k) for k in self)
        lines = []
        for k in self:
            vals = list(self[k])
            if hl_cycle is not None and hl_signal is not None:
                vals = [highlight(val, hl=hl_signal == k) if i == hl_cycle else val
                        for i, val in enumerate(vals)]
            hist = ' '.join(''.join(chunk) for chunk in chunks(vals, chunk_size))
            line = '{:{n}} {}'.format(k + ':', hist, n=key_strw+1)
            lines.append(line)
        if underline_cycle:
            assert hl_cycle is not None
            n = hl_cycle + hl_cycle//chunk_size
            line = ' ' * (key_strw+1) + ' ' + ' ' * n + '^'
            lines.append(line)
        if hl_signal is not None and hl_cycle is None:
            keys = list(self.keys())
            sig_i = keys.index(hl_signal)
            lines = ['{} {}'.format('>' if i == sig_i else ' ', line) for i, line in enumerate(lines)]
        return '\n'.join(lines)

    @staticmethod
    def width_for(histories):
        keys = itertools.chain.from_iterable(h.keys() for h in histories)
        return max(len(k) for k in keys)


class PadChecker:
    """Helper class for defining expected sequences on pads"""
    def __init__(self, pads, signals: Mapping[str, str]):
        # signals: {sig: values}, values: a string of '0'/'1'/'x'/' '
        signals = {clk: values.replace(' ', '') for clk, values in signals.items()}
        self.pads = pads
        self.signals = signals
        self.history = PadsHistory()  # registered values
        self.ref_history = PadsHistory()  # expected values

        assert all(v in '01x' for values in signals.values() for v in values)

        lengths = [len(vals) for vals in signals.values()]
        assert all(l == lengths[0] for l in lengths)

    @property
    def length(self):
        values = list(self.signals.values())
        return len(values[0]) if values else 1

    def run(self):
        for i in range(self.length):
            for sig, vals in self.signals.items():
                # transform numbered signal names to pad indicies (e.g. dq1 -> dq[1])
                m = re.match(r'([a-zA-Z_]+)(\d+)', sig)
                pad = getattr(self.pads, m.group(1))[int(m.group(2))] if m else getattr(self.pads, sig)

                # save the value at current cycle
                val = vals[i]
                self.history[sig] += str((yield pad))
                self.ref_history[sig] += val
            yield

    def find_error(self, start=0):
        for i in range(start, self.length):
            for sig in self.history:
                val = self.history[sig][i]
                ref = self.ref_history[sig][i]
                if ref != 'x' and val != ref:
                    return (i, sig, val, ref)
        return None

    def summary(self, **kwargs):
        error = self.find_error()
        cycle, sig = None, None
        if error is not None:
            cycle, sig, val, ref = error
        lines = []
        lines.append(self.history.format(hl_cycle=cycle, hl_signal=sig, **kwargs))
        lines.append('vs ref:')
        lines.append(self.ref_history.format(hl_cycle=cycle, hl_signal=sig, **kwargs))
        return '\n'.join(lines)

    @staticmethod
    def assert_ok(test_case, clock_checkers, **kwargs):
        # clock_checkers: {clock: PadChecker(...), ...}
        errors = list(filter(None, [c.find_error() for c in clock_checkers.values()]))
        if errors:
            all_histories = [c.history for c in clock_checkers.values()]
            all_histories += [c.ref_history for c in clock_checkers.values()]
            key_strw = PadsHistory.width_for(all_histories)
            summaries = ['{}\n{}'.format(highlight(clock, hl=False), checker.summary(key_strw=key_strw, **kwargs))
                         for clock, checker in clock_checkers.items()]
            first_error = min(errors, key=lambda e: e[0])  # first error
            i, sig, val, ref = first_error
            msg = f'Cycle {i} Signal `{sig}`: {val} vs {ref}\n'
            test_case.assertEqual(val, ref, msg=msg + '\n'.join(summaries))


def dfi_names(cmd=True, wrdata=True, rddata=True):
    names = []
    if cmd:    names += [name for name, _, _ in dfi.phase_cmd_description(1, 1, 1)]
    if wrdata: names += [name for name, _, _ in dfi.phase_wrdata_description(16)]
    if rddata: names += [name for name, _, _ in dfi.phase_rddata_description(16)]
    return names

def dfi_reset_values(**kwargs):
    return {sig: 1 if sig.endswith("_n") else 0 for sig in dfi_names(**kwargs)}


class DFIPhaseValues(dict):
    """Dictionary {dfi_signal_name: value}"""
    def __init__(self, **kwargs):
        # widths are not important
        names = dfi_names()
        for sig in kwargs:
            assert sig in names
        super().__init__(**kwargs)


class DFISequencer:
    """Generator that drives DFI interface with given commands and stores any read data"""
    Cycle = int
    DFIPhase = int
    DFISequence = Sequence[Mapping[DFIPhase, DFIPhaseValues]]

    def __init__(self, sequence: DFISequence = []):
        # sequence: [{phase: {sig: value}}]
        self.sequence = []  # generated on DFI
        self.read_sequence = []  # read from DFI
        self.expected_sequence = []  # expected to read from DFI

        # split sequence into read/write
        for cycle in sequence:
            read = {}
            write = {}
            for p, phase in cycle.items():
                read[p] = DFIPhaseValues()
                write[p] = DFIPhaseValues()
                for sig, val in phase.items():
                    is_write = sig in dfi_names(rddata=False) + ["rddata_en"]
                    target = write[p] if is_write else read[p]
                    target[sig] = val
            self.sequence.append(write)
            self.expected_sequence.append(read)

    def add(self, dfi_cycle: Mapping[DFIPhase, DFIPhaseValues]):
        self.sequence.append(dfi_cycle)

    def _reset(self, dfi):
        for phase in dfi.phases:
            for sig, val in dfi_reset_values().items():
                yield getattr(phase, sig).eq(val)

    def assert_ok(self, test_case):
        # expected: should contain only input signals
        names = ["rddata", "rddata_valid"]
        for cyc, (read, expected) in enumerate(zip(self.read_sequence, self.expected_sequence)):
            for p in expected:
                for sig in expected[p]:
                    assert sig in names, f"`{sig}` is not DFI input signal"
                    val = read[p][sig]
                    ref = expected[p][sig]
                    if sig in ["wrdata", "rddata"]:
                        err = f"Cycle {cyc} signal `{sig}`: 0x{val:08x} vs 0x{ref:08x}"
                    else:
                        err = f"Cycle {cyc} signal `{sig}`: {val:} vs {ref}"
                    err += "\nread: \n{}".format(pprint.pformat(self.read_sequence))
                    err += "\nexpected: \n{}".format(pprint.pformat(self.expected_sequence))
                    test_case.assertEqual(val, ref, msg=err)

    def generator(self, dfi):
        names = dfi_names(cmd=True, wrdata=True, rddata=False) + ["rddata_en"]
        for per_phase in self.sequence:
            # reset in case of any previous changes
            (yield from self._reset(dfi))
            # set values
            for phase, values in per_phase.items():
                for sig, val in values.items():
                    assert sig in names, f"`{sig}` is not DFI output signal"
                    yield getattr(dfi.phases[phase], sig).eq(val)
            yield
        (yield from self._reset(dfi))
        yield

    def reader(self, dfi):
        yield  # do not include data read on start (a.k.a. cycle=-1)
        for _ in range(len(self.expected_sequence)):
            phases = {}
            for i, p in enumerate(dfi.phases):
                values = DFIPhaseValues(rddata_en=(yield p.rddata_en), rddata=(yield p.rddata),
                                        rddata_valid=(yield p.rddata_valid))
                phases[i] = values
            self.read_sequence.append(phases)
            yield

    @staticmethod
    def input_generator(dfi, sequence: DFISequence):
        names = dfi_names(cmd=True, wrdata=True, rddata=False) + ["rddata_en"]
        for per_phase in sequence:
            # set values
            for phase, values in per_phase.items():
                for sig, val in values.items():
                    assert sig not in names, f"`{sig}` is not DFI input signal"
                    yield getattr(dfi.phases[phase], sig).eq(val)
            yield
            # reset values
            for phase, values in per_phase.items():
                for sig in values.keys():
                    yield getattr(dfi.phases[phase], sig).eq(0)
        yield
