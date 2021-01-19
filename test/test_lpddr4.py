import re
import copy
import pprint
import random
import unittest
import itertools
from collections import defaultdict
from typing import Mapping, Sequence

from migen import *

from litedram.phy import dfi
from litedram.phy.lpddr4.simphy import LPDDR4SimPHY, Serializer, Deserializer

from litex.gen.sim import run_simulation as _run_simulation


def bit(n, val):
    return (val & (1 << n)) >> n

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def run_simulation(dut, generators, debug_clocks=False, **kwargs):
    # Migen simulator supports reset signals so we could add CRG to start all the signals
    # in the same time, however the clock signals will still be visible in the VCD dump
    # and the generators we assign to them will still work before reset. For this reason we
    # use clocks set up in such a way that we have all the phase aligned clocks start in tick
    # 1 (not zero), so that we avoid any issues with clock alignment.
    #
    # NOTE: On hardware proper reset must be ensured!
    #
    # The simulation should start like this:
    #   sys          |_--------------
    #   sys_11_25    |___------------
    #   sys8x        |_----____----__
    #   sys8x_ddr    |_--__--__--__--
    #   sys8x_90     |___----____----
    #   sys8x_90_ddr |-__--__--__--__
    #
    # sys8x_90_ddr does not trigger at the simulation start (not an edge),
    # BUT a generator starts before first edge, so a `yield` is needed to wait until the first
    # rising edge!
    clocks = {
        "sys":          (64, 31),
        "sys_11_25":    (64, 29),  # aligned to sys8x_90 (phase shift of 11.25)
        "sys8x":        ( 8,  3),
        "sys8x_ddr":    ( 4,  1),
        "sys8x_90":     ( 8,  1),
        "sys8x_90_ddr": ( 4,  3),
    }

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


class TestSimSerializers(unittest.TestCase):
    @staticmethod
    def data_generator(i, datas):
        for data in datas:
            yield i.eq(data)
            yield
        yield i.eq(0)
        yield

    @staticmethod
    def data_checker(o, datas, n, latency, yield1=False):
        if yield1:
            yield
        for _ in range(latency):
            yield
        for _ in range(n):
            datas.append((yield o))
            yield
        yield

    def serializer_test(self, *, data_width, datas, clk, clkdiv, latency, clkgen=None, clkcheck=None, **kwargs):
        clkgen = clkgen if clkgen is not None else clk
        clkcheck = clkcheck if clkcheck is not None else clkdiv

        received = []
        dut = Serializer(clk=clk, clkdiv=clkdiv, i_dw=data_width, o_dw=1)
        generators = {
            clkgen: self.data_generator(dut.i, datas),
            clkcheck: self.data_checker(dut.o, received, n=len(datas) * data_width, latency=latency * data_width, yield1=True),
        }
        run_simulation(dut, generators, **kwargs)

        received = list(chunks(received, data_width))
        datas  = [[bit(i, d) for i in range(data_width)] for d in datas]
        self.assertEqual(received, datas)

    def deserializer_test(self, *, data_width, datas, clk, clkdiv, latency, clkgen=None, clkcheck=None, **kwargs):
        clkgen = clkgen if clkgen is not None else clkdiv
        clkcheck = clkcheck if clkcheck is not None else clk

        datas = [[bit(i, d) for i in range(data_width)] for d in datas]

        received = []
        dut = Deserializer(clk=clk, clkdiv=clkdiv, i_dw=1, o_dw=data_width)
        generators = {
            clkgen: self.data_generator(dut.i, itertools.chain(*datas)),
            clkcheck: self.data_checker(dut.o, received, n=len(datas), latency=latency),
        }

        run_simulation(dut, generators, **kwargs)

        received = [[bit(i, d) for i in range(data_width)] for d in received]
        self.assertEqual(received, datas)

    DATA_8 = [0b11001100, 0b11001100, 0b00110011, 0b00110011, 0b10101010]
    DATA_16 = [0b1100110011001100, 0b0011001100110011, 0b0101010101010101]

    ARGS_8 = dict(
        data_width = 8,
        datas = DATA_8,
        clk = "sys",
        clkdiv = "sys8x",
        latency = Serializer.LATENCY,
    )

    ARGS_16 = dict(
        data_width = 16,
        datas = DATA_16,
        clk = "sys",
        clkdiv = "sys8x_ddr",
        latency = Serializer.LATENCY,
    )

    def _s(default, **kwargs):
        def test(self):
            new = default.copy()
            new.update(kwargs)
            self.serializer_test(**new)
        return test

    def _d(default, **kwargs):
        def test(self):
            new = default.copy()
            new["latency"] = Deserializer.LATENCY
            new.update(kwargs)
            self.deserializer_test(**new)
        return test

    test_sim_serializer_8 = _s(ARGS_8)
    test_sim_serializer_8_phase90 = _s(ARGS_8, clk="sys_11_25", clkdiv="sys8x_90")
    # when clkgen and clk are not phase aligned  (clk is delayed), there will be lower latency
    test_sim_serializer_8_phase90_gen0 = _s(ARGS_8, clk="sys_11_25", clkdiv="sys8x_90", clkgen="sys", latency=Serializer.LATENCY - 1)
    test_sim_serializer_8_phase90_check0 = _s(ARGS_8, clk="sys_11_25", clkdiv="sys8x_90", clkcheck="sys8x")

    test_sim_serializer_16 = _s(ARGS_16)
    test_sim_serializer_16_phase90 = _s(ARGS_16, clk="sys_11_25", clkdiv="sys8x_90_ddr")
    test_sim_serializer_16_phase90_gen0 = _s(ARGS_16, clk="sys_11_25", clkdiv="sys8x_90_ddr", clkgen="sys", latency=Serializer.LATENCY - 1)
    test_sim_serializer_16_phase90_check0 = _s(ARGS_16, clk="sys_11_25", clkdiv="sys8x_90_ddr", clkcheck="sys8x_ddr")

    # for phase aligned clocks the latency will be bigger (preferably avoid phase aligned reading?)
    test_sim_deserializer_8 = _d(ARGS_8, latency=Deserializer.LATENCY + 1)
    test_sim_deserializer_8_check90 = _d(ARGS_8, clkcheck="sys_11_25")
    test_sim_deserializer_8_gen90_check90 = _d(ARGS_8, clkcheck="sys_11_25", clkgen="sys8x_90")
    test_sim_deserializer_8_phase90 = _d(ARGS_8, clk="sys_11_25", clkdiv="sys8x_90", latency=Deserializer.LATENCY + 1)
    test_sim_deserializer_8_phase90_check0 = _d(ARGS_8, clk="sys_11_25", clkdiv="sys8x_90", clkcheck="sys", latency=Deserializer.LATENCY + 1)

    test_sim_deserializer_16 = _d(ARGS_16, latency=Deserializer.LATENCY + 1)
    test_sim_deserializer_16_check90 = _d(ARGS_16, clkcheck="sys_11_25")
    test_sim_deserializer_16_gen90_check90 = _d(ARGS_16, clkcheck="sys_11_25", clkgen="sys8x_90_ddr")
    test_sim_deserializer_16_phase90 = _d(ARGS_16, clk="sys_11_25", clkdiv="sys8x_90_ddr", latency=Deserializer.LATENCY + 1)
    test_sim_deserializer_16_phase90_check0 = _d(ARGS_16, clk="sys_11_25", clkdiv="sys8x_90_ddr", clkcheck="sys", latency=Deserializer.LATENCY + 1)


BOLD = '\033[1m'
HIGHLIGHT = '\033[91m'
CLEAR = '\033[0m'

def highlight(s, hl=True):
    return BOLD + (HIGHLIGHT if hl else '') + s + CLEAR


class PadsHistory(defaultdict):
    def __init__(self):
        super().__init__(str)

    def format(self, hl_cycle=None, hl_signal=None, underline_cycle=False, key_strw=None):
        if key_strw is None:
            key_strw = max(len(k) for k in self)
        lines = []
        for k in self:
            vals = list(self[k])
            if hl_cycle is not None and hl_signal is not None:
                vals = [highlight(val, hl=hl_signal == k) if i == hl_cycle else val
                        for i, val in enumerate(vals)]
            hist = ' '.join(''.join(chunk) for chunk in chunks(vals, 8))
            line = '{:{n}} {}'.format(k + ':', hist, n=key_strw+1)
            lines.append(line)
        if underline_cycle:
            assert hl_cycle is not None
            n = hl_cycle + hl_cycle//8
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
    def __init__(self, pads, signals: Mapping[str, str]):
        # signals: {sig: values}, values: a string of '0'/'1'/'x'/' '
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
    def assert_ok(test_case, clock_checkers):
        # clock_checkers: {clock: PadChecker(...), ...}
        errors = list(filter(None, [c.find_error() for c in clock_checkers.values()]))
        if errors:
            all_histories = [c.history for c in clock_checkers.values()]
            all_histories += [c.ref_history for c in clock_checkers.values()]
            key_strw = PadsHistory.width_for(all_histories)
            summaries = ['{}\n{}'.format(highlight(clock, hl=False), checker.summary(key_strw=key_strw))
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


class DFIPhaseValues(dict):
    """Dictionary {dfi_signal_name: value}"""
    def __init__(self, **kwargs):
        # widths are not important
        names = dfi_names()
        for sig in kwargs:
            assert sig in names
        super().__init__(**kwargs)


class DFISequencer:
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

    def _dfi_reset_values(self):
        return {sig: 1 if sig.endswith("_n") else 0 for sig in dfi_names()}

    def _reset(self, dfi):
        for phase in dfi.phases:
            for sig, val in self._dfi_reset_values().items():
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


def dfi_data_to_dq(dq_i, dfi_phases, dfi_name, nphases=8):
    # data on DQ should go in a pattern:
    # dq0: p0.wrdata[0], p0.wrdata[16], p1.wrdata[0], p1.wrdata[16], ...
    # dq1: p0.wrdata[1], p0.wrdata[17], p1.wrdata[1], p1.wrdata[17], ...
    for p in range(nphases):
        data = dfi_phases[p][dfi_name]
        yield bit(0  + dq_i, data)
        yield bit(16 + dq_i, data)

def dq_pattern(i, dfi_data, dfi_name):
    return ''.join(str(v) for v in dfi_data_to_dq(i, dfi_data, dfi_name))


class TestLPDDR4(unittest.TestCase):
    CMD_LATENCY = 2

    def run_test(self, dut, dfi_sequence, pad_checkers: Mapping[str, Mapping[str, str]], pad_generators=None, **kwargs):
        # pad_checkers: {clock: {sig: values}}
        dfi = DFISequencer(dfi_sequence)
        checkers = {clk: PadChecker(dut.pads, pad_signals) for clk, pad_signals in pad_checkers.items()}
        generators = defaultdict(list)
        generators["sys"].append(dfi.generator(dut.dfi))
        generators["sys"].append(dfi.reader(dut.dfi))
        for clock, checker in checkers.items():
            generators[clock].append(checker.run())
        pad_generators = pad_generators or {}
        for clock, gens in pad_generators.items():
            gens = gens if isinstance(gens, list) else [gens]
            for gen in gens:
                generators[clock].append(gen(dut.pads))
        run_simulation(dut, generators, **kwargs)
        PadChecker.assert_ok(self, checkers)
        dfi.assert_ok(self)

    def test_lpddr4_cs_phase_0(self):
        # Test that CS is serialized correctly when sending command on phase 0
        latency = '00000000' * self.CMD_LATENCY
        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},  # p0: READ
            ],
            pad_checkers = {"sys8x_90": {
                'cs': latency + '10100000',
            }},
        )

    def test_lpddr4_clk(self):
        # Test clock serialization, first few cycles are undefined so ignore them
        latency = 'xxxxxxxx' * self.CMD_LATENCY
        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = [
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
            ],
            pad_checkers = {"sys8x_90_ddr": {
                'clk_p': latency + '01010101' * 3,
            }},
        )

    def test_lpddr4_cs_multiple_phases(self):
        # Test that CS is serialized on different phases and that overlapping commands are handled
        latency = '00000000' * self.CMD_LATENCY
        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {
                    1: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),
                    4: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),  # should be ignored
                },
                {
                    1: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),
                    5: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),  # should NOT be ignored
                },
                {6: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},  # crosses cycle boundaries
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},  # should be ignored
                {2: dict(cs_n=1, cas_n=0, ras_n=1, we_n=1)},  # ignored due to cs_n=1
            ],
            pad_checkers = {"sys8x_90": {
                'cs': latency + ''.join([
                    '10100000',  # p0
                    '00010100',  # p3
                    '01010000',  # p1, p4 ignored
                    '01010101',  # p1, p5
                    '00000010',  # p6 (cyc 0)
                    '10000000',  # p6 (cyc 1), p0 ignored
                    '00000000',  # p2 ignored
                ])
            }},
        )

    def test_lpddr4_ca_sequencing(self):
        # Test proper serialization of commands to CA pads and that overlapping commands are handled
        latency = '00000000' * self.CMD_LATENCY
        read = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)
        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = [
                {0: read, 3: read},  # p4 should be ignored
                {0: read, 4: read},
                {6: read},
                {0: read}, # ignored
            ],
            pad_checkers = {"sys8x_90": {
                'cs':  latency + '10100000' + '10101010' + '00000010' + '10000000',
                'ca0': latency + '00000000' + '00000000' + '00000000' + '00000000',
                'ca1': latency + '10100000' + '10101010' + '00000010' + '10000000',
                'ca2': latency + '00000000' + '00000000' + '00000000' + '00000000',
                'ca3': latency + '0x000000' + '0x000x00' + '0000000x' + '00000000',
                'ca4': latency + '00100000' + '00100010' + '00000000' + '10000000',
                'ca5': latency + '00000000' + '00000000' + '00000000' + '00000000',
            }},
        )

    def test_lpddr4_ca_addressing(self):
        # Test that bank/address for different commands are correctly serialized to CA pads
        latency = '00000000' * self.CMD_LATENCY
        read       = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b101, address=0b1100110011)  # actually invalid because CA[1:0] should always be 0
        write_ap   = dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, bank=0b111, address=0b10000000000)
        activate   = dict(cs_n=0, cas_n=1, ras_n=0, we_n=1, bank=0b010, address=0b11110000111100001)
        refresh_ab = dict(cs_n=0, cas_n=0, ras_n=0, we_n=1, bank=0b100, address=0b10000000000)
        precharge  = dict(cs_n=0, cas_n=1, ras_n=0, we_n=0, bank=0b011, address=0)
        mrw        = dict(cs_n=0, cas_n=0, ras_n=0, we_n=0, bank=0,     address=(0b110011 << 8) | 0b10101010)  # 6-bit address | 8-bit op code
        zqc_start  = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=0,     address=0b1001111)  # MPC with ZQCAL START operand
        zqc_latch  = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=0,     address=0b1010001)  # MPC with ZQCAL LATCH operand
        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = [
                {0: read, 4: write_ap},
                {0: activate, 4: refresh_ab},
                {0: precharge, 4: mrw},
                {0: zqc_start, 4: zqc_latch},
            ],
            pad_checkers = {"sys8x_90": {
                # note that refresh and precharge have a single command so these go as cmd2
                #                 rd     wr       act    ref      pre    mrw      zqcs   zqcl
                'cs':  latency + '1010'+'1010' + '1010'+'0010' + '0010'+'1010' + '0010'+'0010',
                'ca0': latency + '0100'+'0100' + '1011'+'0000' + '0001'+'0100' + '0001'+'0001',
                'ca1': latency + '1010'+'0110' + '0110'+'0000' + '0001'+'1111' + '0001'+'0000',
                'ca2': latency + '0101'+'1100' + '0010'+'0001' + '0000'+'1010' + '0001'+'0000',
                'ca3': latency + '0x01'+'0x00' + '1110'+'001x' + '000x'+'0001' + '0001'+'0000',
                'ca4': latency + '0110'+'0010' + '1010'+'000x' + '001x'+'0110' + '0000'+'0001',
                'ca5': latency + '0010'+'0100' + '1001'+'001x' + '000x'+'1101' + '0010'+'0010',
            }},
        )

    def test_lpddr4_command_pads(self):
        # Test serialization of DFI command pins (cs/cke/odt/reset_n)
        latency = '00000000' * self.CMD_LATENCY
        read = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)
        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = [
                {
                    0: dict(cke=1, odt=1, reset_n=1, **read),
                    2: dict(cke=0, odt=1, reset_n=0, **read),
                    3: dict(cke=1, odt=0, reset_n=0, **read),
                    5: dict(cke=0, odt=1, reset_n=1, **read),
                    7: dict(cke=0, odt=0, reset_n=0, **read),
                },
            ],
            pad_checkers = {"sys8x_90": {
                'cs':      latency + '10100101',  # p2, p3, p7 ignored
                'cke':     latency + '10010000',
                'odt':     latency + '10100100',
                'reset_n': latency + '11001110',
            }},
        )

    def test_lpddr4_dq_out(self):
        # Test serialization of dfi wrdata to DQ pads
        dut = LPDDR4SimPHY()
        zero = '00000000' * 2  # zero for 1 sysclk clock in sys8x_ddr clock domain

        dfi_data = {
            0: dict(wrdata=0x11112222),
            1: dict(wrdata=0x33334444),
            2: dict(wrdata=0x55556666),
            3: dict(wrdata=0x77778888),
            4: dict(wrdata=0x9999aaaa),
            5: dict(wrdata=0xbbbbcccc),
            6: dict(wrdata=0xddddeeee),
            7: dict(wrdata=0xffff0000),
        }
        dfi_wrdata_en = {0: dict(wrdata_en=1)}  # wrdata_en=1 required on any single phase

        self.run_test(dut,
            dfi_sequence = [dfi_wrdata_en, {}, dfi_data],
            pad_checkers = {"sys8x_90_ddr": {
                f'dq{i}': (self.CMD_LATENCY+1)*zero + zero + dq_pattern(i, dfi_data, "wrdata") + zero for i in range(16)
            }},
        )

    def test_lpddr4_dq_only_1cycle(self):
        # Test that DQ data is sent to pads only during expected cycle, on other cycles there is no data
        dut = LPDDR4SimPHY()
        zero = '00000000' * 2

        dfi_data = {
            0: dict(wrdata=0x11112222),
            1: dict(wrdata=0x33334444),
            2: dict(wrdata=0x55556666),
            3: dict(wrdata=0x77778888),
            4: dict(wrdata=0x9999aaaa),
            5: dict(wrdata=0xbbbbcccc),
            6: dict(wrdata=0xddddeeee),
            7: dict(wrdata=0xffff0000),
        }
        dfi_wrdata_en = copy.deepcopy(dfi_data)
        dfi_wrdata_en[0].update(dict(wrdata_en=1))

        self.run_test(dut,
            dfi_sequence = [dfi_wrdata_en, dfi_data, dfi_data],
            pad_checkers = {"sys8x_90_ddr": {
                f'dq{i}': (self.CMD_LATENCY+1)*zero + zero + dq_pattern(i, dfi_data, "wrdata") + zero for i in range(16)
            }},
        )

    def test_lpddr4_dqs(self):
        # Test serialization of DQS pattern in relation to DQ data, with proper preamble and postamble
        zero = '00000000' * 2

        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = [
                {0: dict(wrdata_en=1)},
                {},
                {  # to get 10101010... pattern on dq0 and only 1s on others
                    0: dict(wrdata=0xfffeffff),
                    1: dict(wrdata=0xfffeffff),
                    2: dict(wrdata=0xfffeffff),
                    3: dict(wrdata=0xfffeffff),
                    4: dict(wrdata=0xfffeffff),
                    5: dict(wrdata=0xfffeffff),
                    6: dict(wrdata=0xfffeffff),
                    7: dict(wrdata=0xfffeffff),
                },
            ],
            pad_checkers = {
                "sys8x_90_ddr": {
                    'dq0':  (self.CMD_LATENCY+1)*zero + '00000000'+'00000000' + '10101010'+'10101010' + '00000000'+'00000000' + zero,
                    'dq1':  (self.CMD_LATENCY+1)*zero + '00000000'+'00000000' + '11111111'+'11111111' + '00000000'+'00000000' + zero,
                },
                "sys8x_ddr": {  # preamble, pattern, preamble
                    'dqs0': (self.CMD_LATENCY+1)*zero + '01010101'+'01010100' + '01010101'+'01010101' + '00010101'+'01010101' + zero,
                    'dqs1': (self.CMD_LATENCY+1)*zero + '01010101'+'01010100' + '01010101'+'01010101' + '00010101'+'01010101' + zero,
                }
            },
        )

    def test_lpddr4_dmi_no_mask(self):
        # Test proper output on DMI pads. We don't implement masking now, so nothing should be sent to DMI pads
        zero = '00000000' * 2

        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = [
                {0: dict(wrdata_en=1)},
                {},
                {
                    0: dict(wrdata=0xffffffff),
                    1: dict(wrdata=0xffffffff),
                    2: dict(wrdata=0xffffffff),
                    3: dict(wrdata=0xffffffff),
                    4: dict(wrdata=0xffffffff),
                    5: dict(wrdata=0xffffffff),
                    6: dict(wrdata=0xffffffff),
                    7: dict(wrdata=0xffffffff),
                },
            ],
            pad_checkers = {
                "sys8x_90_ddr": {
                    'dq0':  (self.CMD_LATENCY+1)*zero + zero + '11111111'+'11111111' + 2*zero,
                },
                "sys8x_ddr": {
                    'dmi0': (self.CMD_LATENCY+1)*zero + (3 + 1)*zero,
                    'dmi1': (self.CMD_LATENCY+1)*zero + (3 + 1)*zero,
                }
            },
        )

    def test_lpddr4_dq_in_rddata_valid(self):
        # Test that rddata_valid is set with correct delay
        read_latency = 8  # settings.read_latency
        dfi_sequence = [
            {0: dict(rddata_en=1)},  # command is issued by MC (appears on next cycle)
            *[{p: dict(rddata_valid=0) for p in range(8)} for _ in range(read_latency - 1)],  # nothing is sent during write latency
            {p: dict(rddata_valid=1) for p in range(8)},
            {},
        ]

        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {},
        )

    def test_lpddr4_dq_in_rddata(self):
        # Test that data on DQ pads is deserialized correctly to DFI rddata.
        # We assume that when there are no commands, PHY will still still deserialize the data,
        # which is generally true (tristate oe is 0 whenever we are not writing).
        dfi_data = {
            0: dict(rddata=0x11112222),
            1: dict(rddata=0x33334444),
            2: dict(rddata=0x55556666),
            3: dict(rddata=0x77778888),
            4: dict(rddata=0x9999aaaa),
            5: dict(rddata=0xbbbbcccc),
            6: dict(rddata=0xddddeeee),
            7: dict(rddata=0xffff0000),
        }

        def sim_dq(pads):
            for _ in range(16 * 1):  # wait 1 sysclk cycle
                yield
            for cyc in range(16):  # send a burst of data on pads
                for bit in range(16):
                    yield pads.dq_i[bit].eq(int(dq_pattern(bit, dfi_data, "rddata")[cyc]))
                yield
            for bit in range(16):
                yield pads.dq_i[bit].eq(0)
            yield

        read_des_delay = 3  # phy.read_des_delay
        dfi_sequence = [
            {},  # wait 1 sysclk cycle
            *[{} for _ in range(read_des_delay)],
            dfi_data,
            {},
        ]

        self.run_test(LPDDR4SimPHY(),
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {
                "sys8x_90_ddr": sim_dq,
            },
        )

    def test_lpddr4_cmd_write(self):
        # Test whole WRITE command sequence verifying data on pads and write_latency from MC perspective
        phy = LPDDR4SimPHY()
        zero = '00000000' * 2
        write_latency = phy.settings.write_latency
        wrphase = phy.settings.wrphase.reset.value

        dfi_data = {
            0: dict(wrdata=0x11112222),
            1: dict(wrdata=0x33334444),
            2: dict(wrdata=0x55556666),
            3: dict(wrdata=0x77778888),
            4: dict(wrdata=0x9999aaaa),
            5: dict(wrdata=0xbbbbcccc),
            6: dict(wrdata=0xddddeeee),
            7: dict(wrdata=0xffff0000),
        }
        dfi_sequence = [
            {wrphase: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
            *[{} for _ in range(write_latency - 1)],
            dfi_data,
            {},
            {},
            {},
            {},
            {},
        ]

        self.run_test(phy,
            dfi_sequence = dfi_sequence,
            pad_checkers = {
                "sys8x_90": {
                    "cs":  "00000000"*2 + "00001010" + "00000000"*2,
                    "ca0": "00000000"*2 + "00000000" + "00000000"*2,
                    "ca1": "00000000"*2 + "00000010" + "00000000"*2,
                    "ca2": "00000000"*2 + "00001000" + "00000000"*2,
                    "ca3": "00000000"*2 + "00000000" + "00000000"*2,
                    "ca4": "00000000"*2 + "00000010" + "00000000"*2,
                    "ca5": "00000000"*2 + "00000000" + "00000000"*2,
                },
                "sys8x_90_ddr": {
                    f'dq{i}': (self.CMD_LATENCY+1)*zero + zero + dq_pattern(i, dfi_data, "wrdata") + zero
                    for i in range(16)
                },
                "sys8x_ddr": {
                    "dqs0": (self.CMD_LATENCY+1)*zero + '01010101'+'01010100' + '01010101'+'01010101' + '00010101'+'01010101' + zero,
                },
            },
        )

    def test_lpddr4_cmd_read(self):
        # Test whole READ command sequence simulating DRAM response and verifying read_latency from MC perspective
        phy = LPDDR4SimPHY()
        zero = '00000000' * 2
        read_latency = phy.settings.read_latency
        rdphase = phy.settings.rdphase.reset.value

        dfi_data = {
            0: dict(rddata=0x11112222, rddata_valid=1),
            1: dict(rddata=0x33334444, rddata_valid=1),
            2: dict(rddata=0x55556666, rddata_valid=1),
            3: dict(rddata=0x77778888, rddata_valid=1),
            4: dict(rddata=0x9999aaaa, rddata_valid=1),
            5: dict(rddata=0xbbbbcccc, rddata_valid=1),
            6: dict(rddata=0xddddeeee, rddata_valid=1),
            7: dict(rddata=0xffff0000, rddata_valid=1),
        }
        dfi_sequence = [
            {rdphase: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, rddata_en=1)},
            *[{} for _ in range(read_latency - 1)],
            dfi_data,
            {},
            {},
            {},
            {},
            {},
        ]

        class Simulator:
            def __init__(self, dfi_data, test_case, cl):
                self.dfi_data = dfi_data
                self.read_cmd = False
                self.test_case = test_case
                self.cl = cl

            @passive
            def cmd_checker(self, pads):
                # Monitors CA/CS for a READ command
                read = [
                    0b000010,  # READ-1 (1) BL=0
                    0b000000,  # READ-1 (2) BA=0, C9=0, AP=0
                    0b010010,  # CAS-2 (1) C8=0
                    0b000000,  # CAS-2 (2) C=0
                ]

                def check_ca(i):
                    err = "{}: CA = 0b{:06b}, expected = 0b{:06b}".format(i, (yield pads.ca), read[i])
                    self.test_case.assertEqual((yield pads.ca), read[i], msg=err)

                while True:
                    while not (yield pads.cs):
                        yield
                    yield from check_ca(0)
                    yield
                    yield from check_ca(1)
                    yield
                    self.test_case.assertEqual((yield pads.cs), 1, msg="Found CS on 1st cycle but not on 3rd cycle")
                    yield from check_ca(2)
                    yield
                    yield from check_ca(3)
                    self.read_cmd = True

            @passive
            def dq_generator(self, pads):
                # After a READ command is received, wait CL and send data
                while True:
                    while not self.read_cmd:
                        yield
                    dfi_data = self.dfi_data.pop(0)
                    for _ in range(2*self.cl + 1):
                        yield
                    self.read_cmd = False
                    for cyc in range(16):
                        for bit in range(16):
                            yield pads.dq_i[bit].eq(int(dq_pattern(bit, dfi_data, "rddata")[cyc]))
                        yield
                    for bit in range(16):
                        yield pads.dq_i[bit].eq(0)

            @passive
            def dqs_generator(self, pads):
                # After a READ command is received, wait CL and send data strobe
                while True:
                    while not self.read_cmd:
                        yield
                    for _ in range(2*self.cl - 1):  # DQS to transmit DQS preamble
                        yield
                    for cyc in range(16 + 1):  # send a burst of data on pads
                        for bit in range(2):
                            yield pads.dqs_i[bit].eq(int((cyc + 1) % 2))
                        yield
                    for bit in range(2):
                        yield pads.dqs_i[bit].eq(0)

        sim = Simulator([dfi_data], self, cl=14)
        self.run_test(phy,
            dfi_sequence = dfi_sequence,
            pad_checkers = {
                "sys8x_90": {
                    "cs":  "00000000"*2 + rdphase*"0" + "1010" + "00000000"*2,
                    "ca0": "00000000"*2 + rdphase*"0" + "0000" + "00000000"*2,
                    "ca1": "00000000"*2 + rdphase*"0" + "1010" + "00000000"*2,
                    "ca2": "00000000"*2 + rdphase*"0" + "0000" + "00000000"*2,
                    "ca3": "00000000"*2 + rdphase*"0" + "0000" + "00000000"*2,
                    "ca4": "00000000"*2 + rdphase*"0" + "0010" + "00000000"*2,
                    "ca5": "00000000"*2 + rdphase*"0" + "0000" + "00000000"*2,
                },
                "sys8x_90_ddr": { #?
                    f'dq{i}': (self.CMD_LATENCY+2)*zero + zero + dq_pattern(i, dfi_data, "rddata") + zero
                    for i in range(16)
                },
                "sys8x_ddr": {
                    "dqs0": (self.CMD_LATENCY+2)*zero + '00000000'+'00000001' + '01010101'+'01010101' + zero,
                },
            },
            pad_generators = {
                "sys8x_ddr": [sim.dq_generator, sim.dqs_generator],
                "sys8x_90": sim.cmd_checker,
            },
        )
