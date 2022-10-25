#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
from typing import Mapping
from collections import defaultdict
from functools import partial, wraps

from migen import *

from litedram.phy.lpddr5.simphy import LPDDR5SimPHY
from litedram.phy.lpddr5 import simsoc
from litedram.phy.sim_utils import SimLogger

import test.phy_common
from test.phy_common import DFISequencer, PadChecker, run_simulation as _run_simulation


def generate_clocks(max):
    def phase(ck, phase):
        assert ck % 2 == 0
        assert phase % 90 == 0 and 0 <= phase < 360
        if phase in [90, 270]:
            assert ck % 4 == 0
        p = ck // 2 - 1
        p -= (ck // 4) * phase//90
        p %= ck
        assert 1 <= p <= ck-1
        return p

    sys = 8 * max
    clocks = {
        "sys": (sys, phase(sys, 0)),
        "sys_90": (sys, phase(sys, 90)),
        "sys_180": (sys, phase(sys, 180)),
        "sys_270": (sys, phase(sys, 270)),
    }

    for i in range(1, log2_int(max) + 1):
        n = 2**i
        assert sys % n == 0
        clocks[f"sys{n}x"] = (sys // n, phase(sys // n, 0))
        if n < max or True:
            clocks[f"sys{n}x_90"] = (sys // n, phase(sys // n, 90))
            clocks[f"sys{n}x_180"] = (sys // n, phase(sys // n, 180))
            clocks[f"sys{n}x_270"] = (sys // n, phase(sys // n, 270))

    return clocks


# Clocks are set up such that the first rising edge is on tic 1 (not 0), just as in test_lpddr4.
run_simulation = partial(test.phy_common.run_simulation, clocks=generate_clocks(max=8))


dfi_data_to_dq = partial(test.phy_common.dfi_data_to_dq, databits=16, nphases=1, burst=16)
dq_pattern = partial(test.phy_common.dq_pattern, databits=16, nphases=1, burst=16)


def wck_ratio_subtests(testfunc):
    """Wraps a test running it for both WCK:CK=2:1 and 4:1. Passes wrapped LPDDR5SimPHY constructor as an argument."""
    @wraps(testfunc)
    def wrapper(self):
        for wck_ck_ratio in [2, 4]:
            with self.subTest(wck_ck_ratio=wck_ck_ratio):
                Phy = lambda *args, **kwargs: LPDDR5SimPHY(*args, wck_ck_ratio=wck_ck_ratio, **kwargs)
                testfunc(self, Phy)
    return wrapper


class LPDDR5Tests(unittest.TestCase):
    SYS_CLK_FREQ = 100e6

    def run_test(self, dut, dfi_sequence, pad_checkers: Mapping[str, Mapping[str, str]], pad_generators=None, chunk_size=8, **kwargs):
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
        PadChecker.assert_ok(self, checkers, chunk_size=chunk_size)
        dfi.assert_ok(self)

    @wck_ratio_subtests
    def test_lpddr5_reset_n(self, Phy):
        # Test serialization of DFI reset_n
        phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ)
        read = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)
        self.run_test(phy,
            dfi_sequence = [
                {0: dict(reset_n=1, **read)},
                {},
                {}, {},
                {0: dict(reset_n=0, **read)},
                {},
                {0: dict(reset_n=0)},
                {0: dict(reset_n=0)},
            ],
            pad_checkers = {"sys_270": {
                "cs":      "0 1100 1100",
                "reset_n": "x 1111 0100",
            }},
        )

    @wck_ratio_subtests
    def test_lpddr5_cs(self, Phy):
        # Test that CS is serialized correctly
        phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ)
        self.run_test(phy,
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=1, ras_n=0, we_n=1)},  # ACT
                {},
                {0: dict(cs_n=0, cas_n=1, ras_n=0, we_n=0)},  # PRE
                {},
                {},
                {0: dict(cs_n=0, cas_n=1, ras_n=0, we_n=1)},  # ACT
                {0: dict(cs_n=0, cas_n=1, ras_n=0, we_n=1)},  # ACT (will be ignored)
            ],
            # use 270 phase shift to sample when the data is valid, i.e. CS is shifted 180 deg
            # by PHY (to make it center aligned with CK), then we add 90 to sample in the center of CS
            pad_checkers = {"sys_270": {
                'cs': '0 1101011000',
            }},
        )

    @wck_ratio_subtests
    def test_lpddr5_ck(self, Phy):
        # Test clock serialization, first cycle is undefined so ignore them
        phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ)
        self.run_test(phy,
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
            ],
            pad_checkers = {"sys2x_90": {  # sampling at DDR CK
                'ck': 'xx' + '10101010' * 3,
            }},
        )

    @wck_ratio_subtests
    def test_lpddr5_ca(self, Phy):
        # Test proper serialization of commands to CA pads and that overlapping commands are handled
        phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ)
        read = {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)}  # CAS+RD16
        precharge = {0: dict(cs_n=0, cas_n=1, ras_n=0, we_n=0)}
        self.run_test(phy,
            dfi_sequence = [
                read,
                {},
                {},
                precharge,
                read,  # ignored
            ],
            pad_checkers = {
                "sys_270": {
                    'cs':       '0' ' 1 1  0  0 1 ', },
                "sys2x": {  # it is serialized on DDR sys_270 so check at sys2x with additional cycle (00)
                    'ca0': '00' '00' '0010 00 0000',
                    'ca1': '00' '00' '0000 00 0000',
                    'ca2': '00' '00' '1000 00 0000',
                    'ca3': '00' '00' '1000 00 0010',
                    'ca4': '00' '00' '0000 00 0010',
                    'ca5': '00' '00' '1000 00 0010',
                    'ca6': '00' '00' '0000 00 0010',
                }
            },
            chunk_size=4,
        )

    @wck_ratio_subtests
    def test_lpddr5_cas_wck_sync_read(self, Phy):
        # Test that WCK sync bit in CAS command is set on first read command
        phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ)
        read = {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)}  # CAS+RD16
        self.run_test(phy,
            dfi_sequence = [
                read,  # with WCK sync
                {},
                {},
                read,  # with WCK sync
                {},
                {},
            ],
            pad_checkers = {
                "sys_270": {
                    'cs':       '0' ' 1 1  0 1  1 0 ', },
                "sys2x": {
                    'ca0': '00' '00' '0010 0000 1000',
                    'ca1': '00' '00' '0000 0000 0000',
                    'ca2': '00' '00' '1000 0010 0000',
                    'ca3': '00' '00' '1000 0010 0000',
                    'ca4': '00' '00' '0000 0000 0000',
                    'ca5': '00' '00' '1000 0010 0000',
                    'ca6': '00' '00' '0000 0000 0000',
                }
            },
            chunk_size=4,
        )

    @wck_ratio_subtests
    def test_lpddr5_cas_wck_sync_mrr(self, Phy):
        # Test that WCK sync bit in CAS command is set on first MRR command (CAS with WS_RD)
        phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ)
        mrr = {0: dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=1)}  # MRR is ZQC with bank=1
        self.run_test(phy,
            dfi_sequence = [
                mrr,  # with WCK sync
                {},
                {},
                mrr,  # with WCK sync
                {},
                {},
            ],
            pad_checkers = {
                "sys_270": {
                    'cs':       '0' ' 1 1  0 1  1 0 ', },
                "sys2x": {
                    'ca0': '00' '00' '0000 0000 0000',
                    'ca1': '00' '00' '0000 0000 0000',
                    'ca2': '00' '00' '1000 0010 0000',
                    'ca3': '00' '00' '1010 0010 1000',
                    'ca4': '00' '00' '0010 0000 1000',
                    'ca5': '00' '00' '1000 0010 0000',
                    'ca6': '00' '00' '0000 0000 0000',
                }
            },
            chunk_size=4,
        )

    @wck_ratio_subtests
    def test_lpddr5_cas_wck_sync_write(self, Phy):
        # Test that WCK sync bit in CAS command is set on first write command
        write = {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0)}  # CAS+WR16
        for masked_write in [True, False]:
            with self.subTest(masked_write=masked_write):
                phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ, masked_write=masked_write)
                w1 = f"10{int(not masked_write)}0"
                w2 = f"{int(not masked_write)}000"
                self.run_test(phy,
                    dfi_sequence = [
                        write,  # with WCK sync
                        {},
                        {},
                        write,  # with WCK sync
                        {},
                        {},
                    ],
                    pad_checkers = {
                        "sys_270": {
                            'cs':       '0' ' 1 1  0 1  1 0 ', },
                        "sys2x": {
                            'ca0': '00' '00' '0000 0000 0000',
                            'ca1': '00' '00' '0010 0000 1000',
                            'ca2': '00' '00'f'{w1} 0010 {w2}',
                            'ca3': '00' '00' '1000 0010 0000',
                            'ca4': '00' '00' '1000 0010 0000',
                            'ca5': '00' '00' '0000 0000 0000',
                            'ca6': '00' '00' '0000 0000 0000',
                        }
                    },
                    chunk_size=4,
                )

    @wck_ratio_subtests
    def test_lpddr5_ca_addressing(self, Phy):
        # Test that bank/address for different commands are correctly serialized to CA pads
        # LPDDR5 has only 64 columns, but uses optional 4-bit "burst address"
        read       = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b1111, address=0b1101010000)
        write_ap   = dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, bank=0b1010, address=0b10000000000)
        activate   = dict(cs_n=0, cas_n=1, ras_n=0, we_n=1, bank=0b0010, address=0b111110000111100001)
        refresh_ab = dict(cs_n=0, cas_n=0, ras_n=0, we_n=1, bank=0b1001, address=0b10000000000)
        precharge  = dict(cs_n=0, cas_n=1, ras_n=0, we_n=0, bank=0b0111, address=0)
        mrw        = dict(cs_n=0, cas_n=0, ras_n=0, we_n=0, bank=0b1010011, address=0b10101010)  # bank=7-bit address, address=8-bit op code
        mrr        = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=1,     address=0b1101101)  # 7-bit address (bank=1 selects MRR)
        zqc_start  = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=0,     address=0b10000101)  # MPC with ZQCAL START operand
        zqc_latch  = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=0,     address=0b10000110)  # MPC with ZQCAL LATCH operand

        for masked_write in [True, False]:
            with self.subTest(masked_write=masked_write):
                phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ, masked_write=masked_write)
                mw = f"10{int(not masked_write)}0"
                self.run_test(phy,
                    dfi_sequence = [
                        {},
                        {0: read}, {},  # WCK sync
                        {0: write_ap}, {},  # with WCK sync
                        {0: activate}, {},
                        {0: refresh_ab},{},
                        {0: precharge}, {},
                        {0: mrw}, {},
                        {0: mrr}, {},  # with WCK sync
                        {0: zqc_start}, {},
                        {0: zqc_latch}, {},
                    ],
                    pad_checkers = {
                        "sys_270": {  #         RD   WR   ACT  REF  PRE  MRW  MRR  ZQCS ZQCL
                            'cs':       '0 0 ' '1 1  1 1  1 1  0 1  0 1  1 1  1 1  0 1  0 1 ', },
                        "sys2x": {
                            'ca0': '00' '0000' '0011 0000 1011 0001 0001 0100 0001 0001 0000',
                            'ca1': '00' '0000' '0001 0011 1110 0000 0001 0101 0000 0000 0001',
                            'ca2': '00' '0000'f'1001 {mw} 1000 0000 0001 0000 1001 0001 0001',
                            'ca3': '00' '0000' '1011 1001 1010 0010 0010 1011 1011 0000 0000',
                            'ca4': '00' '0000' '0000 1000 1010 0010 001x 1100 0010 0010 0010',
                            'ca5': '00' '0000' '1011 0000 1001 0010 001x 0001 1001 0010 0010',
                            'ca6': '00' '0000' '0010 0001 1101 0001 0010 1110 0001 0010 0010',
                        }
                    },
                    chunk_size=4,
                )

    def test_lpddr5_dq_out_2to1(self):
        # Test serialization of dfi wrdata to DQ pads
        phy = LPDDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        dfi_data = {
            0: dict(wrdata=0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000),
        }
        dfi_wrdata_en = {0: dict(wrdata_en=1)}
        latency = [{}] * (phy.settings.write_latency - 1)
        self.run_test(phy,
            dfi_sequence = [dfi_wrdata_en, *latency, dfi_data],
            pad_checkers = {"sys4x_90": {
                f'dq{i}': "0000"*phy.settings.write_latency + "0000 0000" + dq_pattern(i, dfi_data, "wrdata") + "0000"
                for i in range(16)
            }},
            chunk_size=4,
        )

    def test_lpddr5_dq_out_4to1(self):
        # Test serialization of dfi wrdata to DQ pads
        phy = LPDDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ, wck_ck_ratio=4)
        dfi_data = {
            0: dict(wrdata=0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000),
        }
        dfi_wrdata_en = {0: dict(wrdata_en=1)}
        latency = [{}] * (phy.settings.write_latency - 1)
        self.run_test(phy,
            dfi_sequence = [dfi_wrdata_en, *latency, dfi_data],
            pad_checkers = {"sys8x_90": {
                f'dq{i}': "00000000"*phy.settings.write_latency + "00000000 00000000" + dq_pattern(i, dfi_data, "wrdata") + "00000000"
                for i in range(16)
            }},
        )

    def test_lpddr5_dmi_out_2to1(self):
        # Test serialization of dfi wrdata to DQ pads
        for masked_write in [False, True]:
            with self.subTest(masked_write=masked_write):
                phy = LPDDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ, masked_write=masked_write)
                wl = phy.settings.write_latency
                dfi_data = {
                    0: dict(  # all DQs have the same value on each cycle, each mask bit is 1 byte
                        wrdata = 0xffff0000ffffffff00000000ffffffff0000ffff00000000ffffffff0000ffff,
                        wrdata_mask = 0b11001000110110110101010010110011,
                    ),
                }
                dfi_wrdata_en = {0: dict(wrdata_en=1)}
                latency = [{}] * (wl - 1)
                pads = {
                    f"dq{i}": "0000"*wl + "0000 0000" "1011 0010 1100 1101" "0000"
                    for i in range(16)
                }
                pads["dmi0"] = "0000"*wl + "0000 0000" + ("1010011110110001" if masked_write else 16*"0") + "0000"
                pads["dmi1"] = "0000"*wl + "0000 0000" + ("1011000011010101" if masked_write else 16*"0") + "0000"
                self.run_test(phy,
                    dfi_sequence = [dfi_wrdata_en, *latency, dfi_data],
                    pad_checkers = {"sys4x_90": pads},
                    chunk_size=4,
                )

    def test_lpddr5_dmi_out_4to1(self):
        # Test serialization of dfi wrdata to DQ pads
        for masked_write in [False, True]:
            with self.subTest(masked_write=masked_write):
                phy = LPDDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ, masked_write=masked_write, wck_ck_ratio=4)
                wl = phy.settings.write_latency
                dfi_data = {
                    0: dict(  # all DQs have the same value on each cycle, each mask bit is 1 byte
                        wrdata = 0xffff0000ffffffff00000000ffffffff0000ffff00000000ffffffff0000ffff,
                        wrdata_mask = 0b11001000110110110101010010110011,
                    ),
                }
                dfi_wrdata_en = {0: dict(wrdata_en=1)}
                latency = [{}] * (wl - 1)
                pads = {
                    f"dq{i}": "00000000"*wl + "00000000 00000000" "1011 0010 1100 1101" "00000000"
                    for i in range(16)
                }
                pads["dmi0"] = "00000000"*wl + "00000000 00000000" + ("1010011110110001" if masked_write else 16*"0") + "00000000"
                pads["dmi1"] = "00000000"*wl + "00000000 00000000" + ("1011000011010101" if masked_write else 16*"0") + "00000000"
                self.run_test(phy,
                    dfi_sequence = [dfi_wrdata_en, *latency, dfi_data],
                    pad_checkers = {"sys8x_90": pads},
                )

    def test_lpddr5_dq_out_only_1_cycle(self):
        # Test that only single cycle of wrdata after write_latency gets serialized
        phy = LPDDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        dfi_data = {
            0: dict(wrdata=0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000),
        }
        dfi_wrdata_en = {0: dict(wrdata_en=1)}
        latency = [dfi_data] * (phy.settings.write_latency - 1)
        self.run_test(phy,
            dfi_sequence = [dfi_wrdata_en, *latency, dfi_data],
            pad_checkers = {"sys4x_90": {
                f'dq{i}': "0000"*phy.settings.write_latency + "0000 0000" + dq_pattern(i, dfi_data, "wrdata") + "0000"
                for i in range(16)
            }},
            chunk_size=4,
        )

    @wck_ratio_subtests
    def test_lpddr5_dq_in_rddata_valid(self, Phy):
        # Test that rddata_valid is set with correct delay
        phy = Phy(sys_clk_freq=self.SYS_CLK_FREQ)
        dfi_sequence = [
            {0: dict(rddata_en=1)},  # command is issued by MC (appears on next cycle)
            *[{0: dict(rddata_valid=0)} for _ in range(phy.settings.read_latency - 1)],  # nothing is sent during write latency
            {0: dict(rddata_valid=1)},
            {},
        ]
        self.run_test(phy,
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {},
        )

    def test_lpddr5_dq_in_rddata(self):
        # Test that data on DQ pads is deserialized correctly to DFI rddata.
        phy = LPDDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        dfi_data = {
            0: dict(
                rddata=0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000,
                rddata_valid=1
            ),
        }

        def sim_dq(pads):
            i = 0
            while not (yield pads.cs):
                i += 1
                assert i < 40, "Timeout waiting for RD cmd"
                yield
            # RD is registered on the second CS, then wait for RL (everyting in CK domain)
            for _ in range(4 * (1 + phy.settings.cl)):
                yield
            # wait one more cycle, need to verify the latencies on actual hardware
            for _ in range(2):
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
            {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, rddata_en=1)},
            *[{} for _ in range(phy.settings.read_latency - 1)],
            dfi_data,
            {},
        ]

        self.run_test(phy,
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {
                "sys4x_180": sim_dq,
            },
        )

    def test_lpddr5_wck_sync_2to1_write(self):
        # Test that correct WCK sequence is generated during WCK sync before burst write for WCK:CK=2:1
        cases = {  # sys_clk_freq: timings
            100e6: dict(t_wckenl_wr=1, t_wckenl_static=1, t_wckenl_toggle_wr=3),  # data rate 400 MT/s
            200e6: dict(t_wckenl_wr=0, t_wckenl_static=2, t_wckenl_toggle_wr=3),  # 800 MT/s
            300e6: dict(t_wckenl_wr=1, t_wckenl_static=2, t_wckenl_toggle_wr=4),  # 1200 MT/s
            500e6: dict(t_wckenl_wr=2, t_wckenl_static=3, t_wckenl_toggle_wr=4),  # 2000 MT/s
            600e6: dict(t_wckenl_wr=1, t_wckenl_static=4, t_wckenl_toggle_wr=4),  # 2400 MT/s
            800e6: dict(t_wckenl_wr=3, t_wckenl_static=4, t_wckenl_toggle_wr=4),  # 3200 MT/s
        }
        for sys_clk_freq, t in cases.items():
            with self.subTest(sys_clk_freq=sys_clk_freq, timings=t):
                phy = LPDDR5SimPHY(sys_clk_freq=sys_clk_freq)
                wl = phy.settings.write_latency
                dfi_data = {  # `10101010...` pattern on dq0 and `11111...` on others
                    0: dict(wrdata=0xfffefffffffefffffffefffffffefffffffefffffffefffffffefffffffeffff),
                }
                latency = [{}] * (wl - 1)

                # minimum latency to have correct wck synchronization
                consecutive_burst_latency = [{}] * 6

                wck_preamble = "00 00" * t["t_wckenl_wr"] + "00 00" * t["t_wckenl_static"] + "10 10" * t["t_wckenl_toggle_wr"]
                wck_burst = "10 10" * (16//4)
                wck_postamble = "10 10" + "10 00"

                self.run_test(phy,
                    dfi_sequence = [
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
                        *latency,
                        dfi_data,
                        *consecutive_burst_latency,
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
                        *latency,
                        dfi_data,
                        *consecutive_burst_latency,
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
                        *latency,
                        dfi_data,
                        *consecutive_burst_latency,
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
                        *latency,
                        dfi_data,
                    ],
                    pad_checkers = {
                        "sys_270": {
                            "cs": "01100000",
                        },
                        "sys4x_90": {  # DQ just for reference
                            "dq0": "0000"*wl + "0000 0000" + "10101010 10101010" + "0000",
                            "dq1": "0000"*wl + "0000 0000" + "11111111 11111111" + "0000",
                        },
                        "sys4x_270": {
                            # tWCKENL_WR starts counting from first command (CAS) so we add command latency,
                            # then preamble, then toggle for the whole burst, then postamble for tWCKPST=2.5tCK
                            # (but for now we assume that WCK is never disabled)
                            "wck0": "0000 0000" + \
                                    "0000" + wck_preamble + wck_burst + wck_postamble + \
                                    "0000" + wck_preamble + wck_burst + wck_postamble + \
                                    "0000" + wck_preamble + wck_burst + wck_postamble + \
                                    "0000" + wck_preamble + wck_burst + wck_postamble,
                        },
                    },
                    chunk_size=4,
                )

    def test_lpddr5_wck_sync_4to1_write(self):
        # Test that correct WCK sequence is generated during WCK sync before burst write for WCK:CK=4:1
        cases = {  # sys_clk_freq: timings
            50e6:  dict(t_wckenl_wr=0, t_wckenl_static=1, t_wckenl_toggle_wr=2),  # data rate 400 MT/s
            100e6: dict(t_wckenl_wr=0, t_wckenl_static=1, t_wckenl_toggle_wr=2),  # 800 MT/s
            150e6: dict(t_wckenl_wr=1, t_wckenl_static=1, t_wckenl_toggle_wr=2),  # 1200 MT/s
            250e6: dict(t_wckenl_wr=1, t_wckenl_static=2, t_wckenl_toggle_wr=2),  # 2000 MT/s
            300e6: dict(t_wckenl_wr=1, t_wckenl_static=2, t_wckenl_toggle_wr=2),  # 2400 MT/s
            400e6: dict(t_wckenl_wr=2, t_wckenl_static=2, t_wckenl_toggle_wr=2),  # 3200 MT/s
        }
        for sys_clk_freq, t in cases.items():
            with self.subTest(sys_clk_freq=sys_clk_freq, timings=t):
                phy = LPDDR5SimPHY(sys_clk_freq=sys_clk_freq, wck_ck_ratio=4)
                wl = phy.settings.write_latency
                dfi_data = {  # `10101010...` pattern on dq0 and `11111...` on others
                    0: dict(wrdata=0xfffefffffffefffffffefffffffefffffffefffffffefffffffefffffffeffff),
                }
                latency = [{}] * (wl - 1)

                # minimum latency to have correct wck synchronization
                consecutive_burst_latency = [{}] * 3

                wck_preamble = "00000000" * (t["t_wckenl_wr"] + t["t_wckenl_static"]) + "11001100" + "10101010" * (t["t_wckenl_toggle_wr"] - 1)
                wck_burst = "10101010" * (16//8)
                wck_postamble = "10101000"

                self.run_test(phy,
                    dfi_sequence = [
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
                        *latency,
                        dfi_data,
                        *consecutive_burst_latency,
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
                        *latency,
                        dfi_data,
                        *consecutive_burst_latency,
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
                        *latency,
                        dfi_data,
                        *consecutive_burst_latency,
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, wrdata_en=1)},
                        *latency,
                        dfi_data,
                    ],
                    pad_checkers = {
                        "sys_270": {
                            "cs": "01100000",
                        },
                        "sys8x_90": {  # DQ just for reference
                            "dq0": "00000000"*wl + "00000000 00000000" + "10101010 10101010" + "00000000",
                            "dq1": "00000000"*wl + "00000000 00000000" + "11111111 11111111" + "00000000",
                        },
                        "sys8x_270": {
                            # tWCKENL_WR starts counting from first command (CAS) so we add command latency,
                            # then preamble, then toggle for the whole burst, then postamble for tWCKPST=2.5tCK
                            # (but for now we assume that WCK is never disabled)
                            "wck0": "00000000 00000000" + \
                                    "00000000" + wck_preamble + wck_burst + wck_postamble + \
                                    "00000000" + wck_preamble + wck_burst + wck_postamble + \
                                    "00000000" + wck_preamble + wck_burst + wck_postamble + \
                                    "00000000" + wck_preamble + wck_burst + wck_postamble,
                        },
                    },
                )

    def test_lpddr5_wck_sync_2to1_read(self):
        # Test that correct WCK sequence is generated during WCK sync before burst read for WCK:CK=2:1
        cases = {  # sys_clk_freq: timings
            100e6: dict(t_wckenl_rd=0, t_wckenl_static=1, t_wckenl_toggle_rd=6),  # data rate 400 MT/s
            200e6: dict(t_wckenl_rd=0, t_wckenl_static=2, t_wckenl_toggle_rd=7),  # 800 MT/s
            300e6: dict(t_wckenl_rd=1, t_wckenl_static=2, t_wckenl_toggle_rd=8),  # 1200 MT/s
            500e6: dict(t_wckenl_rd=2, t_wckenl_static=3, t_wckenl_toggle_rd=8),  # 2000 MT/s
            600e6: dict(t_wckenl_rd=3, t_wckenl_static=4, t_wckenl_toggle_rd=10),  # 2400 MT/s
            800e6: dict(t_wckenl_rd=5, t_wckenl_static=4, t_wckenl_toggle_rd=10),  # 3200 MT/s
        }
        for sys_clk_freq, t in cases.items():
            with self.subTest(sys_clk_freq=sys_clk_freq, timings=t):
                phy = LPDDR5SimPHY(sys_clk_freq=sys_clk_freq)
                rl = phy.settings.read_latency
                latency = [{}] * (rl - 1)

                wck_preamble = "00 00" * t["t_wckenl_rd"] + "00 00" * t["t_wckenl_static"] + "10 10" * t["t_wckenl_toggle_rd"]
                wck_burst = "10 10" * (16//4)
                wck_postamble = "10 10" + "10 00"

                self.run_test(phy,
                    dfi_sequence = [
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, rddata_en=1)},
                        *latency,
                        {0: dict(rddata_valid=1)},
                    ],
                    pad_checkers = {
                        "sys_270": {
                            "cs": "01100000",
                        },
                        "sys4x_270": {
                            "wck0": "0000 0000 0000" + wck_preamble + wck_burst + wck_postamble + "00 00",
                        },
                    },
                    chunk_size=4,
                )

    def test_lpddr5_wck_sync_4to1_read(self):
        # Test that correct WCK sequence is generated during WCK sync before burst read for WCK:CK=4:1
        cases = {  # sys_clk_freq: timings
            50e6:  dict(t_wckenl_rd=0, t_wckenl_static=1, t_wckenl_toggle_rd=3),  # data rate 400 MT/s
            100e6: dict(t_wckenl_rd=0, t_wckenl_static=1, t_wckenl_toggle_rd=4),  # 800 MT/s
            150e6: dict(t_wckenl_rd=1, t_wckenl_static=1, t_wckenl_toggle_rd=4),  # 1200 MT/s
            250e6: dict(t_wckenl_rd=1, t_wckenl_static=2, t_wckenl_toggle_rd=4),  # 2000 MT/s
            300e6: dict(t_wckenl_rd=2, t_wckenl_static=2, t_wckenl_toggle_rd=5),  # 2400 MT/s
            400e6: dict(t_wckenl_rd=3, t_wckenl_static=2, t_wckenl_toggle_rd=5),  # 3200 MT/s
        }
        for sys_clk_freq, t in cases.items():
            with self.subTest(sys_clk_freq=sys_clk_freq, timings=t):
                phy = LPDDR5SimPHY(sys_clk_freq=sys_clk_freq, wck_ck_ratio=4)
                rl = phy.settings.read_latency
                latency = [{}] * (rl - 1)

                wck_preamble = "00000000" * (t["t_wckenl_rd"] + t["t_wckenl_static"]) + "11001100" + "10101010" * (t["t_wckenl_toggle_rd"] - 1)
                wck_burst = "10101010" * (16//8)
                wck_postamble = "10101000"

                self.run_test(phy,
                    dfi_sequence = [
                        {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, rddata_en=1)},
                        *latency,
                        {0: dict(rddata_valid=1)},
                    ],
                    pad_checkers = {
                        "sys_270": {
                            "cs": "01100000",
                        },
                        "sys8x_270": {
                            "wck0": "00000000 00000000 00000000" + wck_preamble + wck_burst + wck_postamble + "00000000",
                        },
                    },
                )

    def test_lpddr5_wck_leveling(self):

        # Test that correct WCK sequence is generated during WCK sync before burst write for WCK:CK=4:1
        for wck_ck_ratio in [2, 4]:
            with self.subTest(wck_ck_ratio=wck_ck_ratio):
                phy = LPDDR5SimPHY(sys_clk_freq=50e6, wck_ck_ratio=wck_ck_ratio)

                def write_leveling(pads):
                    for _ in range(4):
                        yield from phy._wlevel_en.write(1)
                        yield from phy._wlevel_strobe.write(1)
                        for i in range(4):
                            yield
                        yield from phy._wlevel_en.write(0)


                self.run_test(phy,
                    dfi_sequence = {},
                    pad_checkers = {
                        f"sys4x_270": {
                            "wck0": "0000" + \
                                    "0000" * 3 + "1010" * 4 + \
                                    "0000" * 3 + "1010" * 4 + \
                                    "0000" * 3 + "1010" * 4 + \
                                    "0000" * 3 + "1010" * 4,
                        },
                    },
                    pad_generators = {
                        "sys": write_leveling,
                    }
                )


class VerilatorLPDDR5Tests(unittest.TestCase):
    def check_logs(self, logs, allowed):
        for match in SimLogger.LOG_PATTERN.finditer(logs):
            if match.group("level") in ["WARN", "ERROR"]:
                is_allowed = any(
                    lvl == match.group("level") and msg in match.group("msg")
                    for lvl, msg in allowed
                )
                self.assertTrue(is_allowed, msg=match.group(0))

    def run_test(self, args, allowed=None, **kwargs):
        import pexpect

        command = ["python3", simsoc.__file__, *args]
        timeout = 12 * 60  # give more than enough time
        p = pexpect.spawn(" ".join(command), timeout=timeout, **kwargs)

        res = p.expect(["Memtest OK", "Memtest KO"])
        self.assertEqual(res, 0, msg="{}\nGot '{}'".format(p.before.decode(), p.after.decode()))

        # print(p.before.decode())
        self.check_logs(p.before.decode(), allowed=allowed or [])

    def test_lpddr5_sim_no_delays(self):
        # Fast test of simulation with L2 cache (so no data masking is required)
        for wck_ck_ratio in [2, 4]:
            with self.subTest(wck_ck_ratio=wck_ck_ratio):
                self.run_test([
                    "--finish-after-memtest", "--log-level=warn",
                    "--output-dir", "build/test_lpddr5_sim_no_delays",
                    "--disable-delay",
                    f"--wck-ck-ratio={wck_ck_ratio}",
                    "--no-refresh",  # FIXME: avoids warnings before initialization
                ])

    def test_lpddr5_sim_delays_no_cache(self):
        # Test simulation with regular delays and no L2 cache (masked write must work)
        for wck_ck_ratio in [2, 4]:
            with self.subTest(wck_ck_ratio=wck_ck_ratio):
                # These happen due the fact that LiteDRAM starts in hw control mode which holds reset_n=1
                # all the time. When the DRAM initialization starts we do a reset once more, this time properly.
                allowed = [
                    ("WARN", "tPW_RESET violated: RESET_n held low for too short"),
                    ("WARN", "tINIT1 violated: RESET deasserted too fast"),
                    ("WARN", "tINIT2 violated: CS LOW for too short before deasserting RESET (1/1 ck)"),
                ]
                self.run_test([
                    "--finish-after-memtest", "--log-level=warn",
                    "--output-dir", "build/test_lpddr5_sim_delays_no_cache",
                    "--l2-size=0",
                    f"--wck-ck-ratio={wck_ck_ratio}",
                    "--no-refresh",  # FIXME: LiteDRAM sends refresh commands when only MRW/MRR are allowed
                ], allowed=allowed)
