#
# This file is part of LiteDRAM.
#
# Copyright (c) 2022 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import re
import copy
import unittest
from typing import Mapping
from functools import partial
from collections import defaultdict

from migen import *

from litedram.phy.ddr5.simphy import DDR5SimPHY, DoubleRateDDR5SimPHY
from litedram.phy.ddr5 import simsoc
from litedram.phy.sim_utils import SimLogger

import test.phy_common
from test.phy_common import DFISequencer, PadChecker


# The simulation should start like this (each char is 1 ns):
#   sys          |_--------------------------------
#   sys2x        |_----------------________________
#   sys4x        |_--------________--------________
#   sys4x_ddr    |_----____----____----____----____
#   sys4x_90     |_____--------________--------____
#   sys4x_90_ddr |-____----____----____----____----
#   sys4x_180    |-________--------________--------
#
# sys4x_90_ddr does not trigger at the simulation start (not an edge),
# BUT a generator starts before first edge, so a `yield` is needed to wait until the first
# rising edge!
sim_clocks={
    "sys":          (64, 31),
    "sys_rst":      (64, 30),
    "sys2x":        (32, 15),
    "sys4x":        (16,  7),
    "sys4x_ddr":    ( 8,  3),
    "sys4x_90":     (16,  3),
    "sys4x_90_ddr": ( 8,  7),
    "sys4x_180":    (16, 15),
}
run_simulation = partial(test.phy_common.run_simulation, clocks=sim_clocks)


class DDR5Tests(unittest.TestCase):
    SYS_CLK_FREQ = 50e6
    DATABITS = 8
    BURST_LENGTH = 8
    NPHASES = 4

    def setUp(self):
        self.phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ, aligned_reset_zero=True)

        self.rdphase: int = self.phy.settings.rdphase.reset.value
        self.wrphase: int = self.phy.settings.wrphase.reset.value

        self.cmd_latency:   int = self.phy.settings.cmd_latency
        self.read_latency:  int = self.phy.settings.read_latency
        self.write_latency: int = self.phy.settings.write_latency

        # 0s, 1s and Xs for 1 sys_clk in `*_ddr` clock domain
        self.zeros: str = '0' * self.NPHASES * 2
        self.ones:  str = '1' * self.NPHASES * 2
        self.xs:    str = 'x' * self.NPHASES * 2

        # latencies to use in pad checkers
        self.ca_latency:       str = self.xs + '0' * self.NPHASES + '0' * self.NPHASES * self.cmd_latency
        self.cs_n_latency:     str = self.xs + '0' * self.NPHASES + '1' * self.NPHASES * self.cmd_latency

        self.dqs_t_rd_latency: str = self.xs * 2 + (self.read_latency - 2 - 1) * self.xs + 'x' * (self.NPHASES - 1) * 2
        self.dq_rd_latency:    str = self.xs * 2 + (self.read_latency - 2) * self.zeros  + '0' * (self.NPHASES - 1) * 2
        self.dqs_t_wr_latency: str = self.xs * 2 + (self.cmd_latency + self.write_latency - 1) * self.xs + 'x' * (self.NPHASES - 1) * 2
        self.dq_wr_latency:    str = self.xs * 2 + (self.cmd_latency + self.write_latency) * self.zeros  + '0' * (self.NPHASES - 1) * 2

    @staticmethod
    def process_ca(ca: str) -> int:
        """dfi_address is mapped 1:1 to CA"""
        ca = ca.replace(' ', '') # remove readability spaces
        ca = ca[::-1]            # reverse bit order (also readability)
        return int(ca, 2)        # convert to int

    @classmethod
    def dq_pattern(cls, *args, **kwargs) -> str:
        return test.phy_common.dq_pattern(
            *args,
            databits=cls.DATABITS,
            nphases=cls.NPHASES,
            burst=cls.BURST_LENGTH,
            **kwargs,
        )

    def run_test(self, dfi_sequence, pad_checkers: Mapping[str, Mapping[str, str]], pad_generators=None, **kwargs):
        # pad_checkers: {clock: {sig: values}}
        dut = self.phy
        dfi = DFISequencer([{}, {}] + dfi_sequence)
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

        class CRG(Module):
            def __init__(self, dut):
                r = Signal(2)
                self.sync.sys_rst += [If(r<3, r.eq(r+1))]
                self.submodules.dut = dut
                for clk in sim_clocks:
                    if clk == "sys_rst":
                        continue
                    setattr(self.clock_domains, "cd_{}".format(clk), ClockDomain(clk))
                    cd = getattr(self, 'cd_{}'.format(clk))
                    self.comb += cd.rst.eq(~r[1])
        dut = CRG(dut)
        run_simulation(dut, generators, **kwargs)
        PadChecker.assert_ok(self, checkers)
        dfi.assert_ok(self)

    def test_ddr5_cs_n_phase_0(self):
        # Test that CS_n is serialized correctly when sending command on phase 0
        self.run_test(
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},  # p0: READ
            ],
            pad_checkers = {"sys4x": {
                'cs_n': self.cs_n_latency + '01111111',
            }},
            vcd_name="ddr5_cs_n_phase_0.vcd"
        )

    def test_ddr5_cs_n_phase_3(self):
        # Test that CS_n is serialized correctly when sending command on phase 3
        self.run_test(
            dfi_sequence = [
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0)},  # p3: WRITE
            ],
            pad_checkers = {"sys4x": {
                'cs_n': self.cs_n_latency + '11101111',
            }},
            vcd_name="ddr5_cs_n_phase_3.vcd"
        )

    def test_ddr5_clk(self):
        # Test clock serialization
        self.run_test(
            dfi_sequence = [
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
            ],
            pad_checkers = {"sys4x_90_ddr": {
                'ck_t': self.xs * 2 + '10101010' * (self.cmd_latency + 1),
            }},
            vcd_name="ddr5_clk.vcd"
        )

    def test_ddr5_cs_n_overlapping_commands(self):
        # Test that overlapping commands in same cycle aren't handled
        self.run_test(
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {
                    2: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),
                    3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1), # right now it shouldn't be ignored
                },
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
            ],
            pad_checkers = {"sys4x": {
                'cs_n': self.cs_n_latency + ''.join([
                    '0111',  # p0
                    '1100',  # p2, p3 wasn't ignored
                    '0111',  # p0
                ])
            }},
            vcd_name="ddr5_cs_n_overlapping_commands.vcd"
        )

    def test_ddr5_cs_n_multiple_phases(self):
        # Test that CS_n is serialized on different phases
        self.run_test(
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {1: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {},
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {0: dict(cs_n=0, cas_n=1, ras_n=0, we_n=0)},  # should be ignored due to command on previous cycle
                {2: dict(cs_n=1, cas_n=0, ras_n=1, we_n=1)},  # ignored due to cs_n=1
            ],
            pad_checkers = {"sys4x": {
                'cs_n': self.cs_n_latency + ''.join([
                    '0111',  # p0
                    '1110',  # p3
                    '1011',  # p1
                    '1111',  # empty cycle
                    '1110',  # p3 (1st part)
                    '0111',  # (2nd part of the previous command), p0 ignored
                    '1111',  # p2 ignored
                ])
            }},
            vcd_name="ddr5_cs_n_multiple_phases.vcd"
        )

    def test_ddr5_empty_command_sequence(self):
        # Test CS_n/CA values for empty dfi commands sequence
        self.run_test(
            dfi_sequence = [],
            pad_checkers = {"sys4x": {
                'cs_n': self.cs_n_latency,
                'ca0':  self.ca_latency,
                'ca1':  self.ca_latency,
                'ca2':  self.ca_latency,
                'ca3':  self.ca_latency,
                'ca4':  self.ca_latency,
                'ca5':  self.ca_latency,
                'ca6':  self.ca_latency,
                'ca7':  self.ca_latency,
                'ca8':  self.ca_latency,
                'ca9':  self.ca_latency,
                'ca10': self.ca_latency,
                'ca11': self.ca_latency,
                'ca12': self.ca_latency,
                'ca13': self.ca_latency,
            }},
            vcd_name="ddr5_empty_command_sequence.vcd"
        )

    def test_ddr5_ca_addressing(self):
        # Test that bank/address for different commands are correctly serialized to CA pads
        read_0       = dict(cs_n=0, address=self.process_ca('10111 0 10100 000'))  # RD p0
        read_1       = dict(cs_n=1, address=self.process_ca('001100110 01000'))    # RD p1
        write_0      = dict(cs_n=0, address=self.process_ca('10110 0 11100 000'))  # WR p0
        write_1      = dict(cs_n=1, address=self.process_ca('000000001 01100'))    # WR p1
        activate_0   = dict(cs_n=0, address=self.process_ca('00 1000 01000 000'))  # ACT p0
        activate_1   = dict(cs_n=1, address=self.process_ca('0111100001111 0'))    # ACT p1
        refresh_ab   = dict(cs_n=0, address=self.process_ca('11001 0 00010 000'))  # REFab
        precharge_ab = dict(cs_n=0, address=self.process_ca('11010 0 0000 0 000')) # PREab
        mrw_0        = dict(cs_n=0, address=self.process_ca('10100 11001100 0'))   # MRW p0
        mrw_1        = dict(cs_n=1, address=self.process_ca('01010101 00 0 000'))  # MRW p1
        zqc_start    = dict(cs_n=0, address=self.process_ca('11110 10100000'))     # MPC + ZQCAL START op
        zqc_latch    = dict(cs_n=0, address=self.process_ca('11110 00100000'))     # MPC + ZQCAL LATCH op
        mrr_0        = dict(cs_n=0, address=self.process_ca('10101 10110100 0'))   # MRR p0
        mrr_1        = dict(cs_n=1, address=self.process_ca('0000000000 0 000'))   # MRR p1

        self.run_test(
            dfi_sequence = [
                {0: read_0, 1: read_1},
                {0: write_0, 1: write_1},
                {0: activate_0, 1: activate_1},
                {0: refresh_ab},
                {0: precharge_ab},
                {0: mrw_0, 1: mrw_1},
                {0: zqc_start},
                {0: zqc_latch},
                {0: mrr_0, 1: mrr_1},
            ],
            pad_checkers = {"sys4x": {
                #                            rd     wr       act    ref      pre    mrw      zqcs   zqcl     mrr
                'cs_n': self.cs_n_latency + '0111'+'0111' + '0111'+'0111' + '0111'+'0111' + '0111'+'0111' + '0111'+'1111',
                'ca0':  self.ca_latency   + '1000'+'1x00' + '0000'+'1000' + '1000'+'1000' + '1000'+'1000' + '1000'+'0000',
                'ca1':  self.ca_latency   + '0000'+'0000' + '0100'+'1000' + '1000'+'0100' + '1000'+'1000' + '0000'+'0000',
                'ca2':  self.ca_latency   + '1100'+'1000' + '1100'+'0000' + '0000'+'1000' + '1000'+'1000' + '1x00'+'0000',
                'ca3':  self.ca_latency   + '1100'+'1000' + '0100'+'0000' + '1000'+'0100' + '1000'+'1000' + '0x00'+'0000',
                'ca4':  self.ca_latency   + '1000'+'0000' + '0100'+'1000' + '0000'+'0000' + '0000'+'0000' + '1x00'+'0000',
                'ca5':  self.ca_latency   + '0000'+'0000' + '0000'+'x000' + 'x000'+'1100' + '1000'+'0000' + '1x00'+'0000',
                'ca6':  self.ca_latency   + '1100'+'1000' + '0000'+'x000' + 'x000'+'1000' + '0000'+'0000' + '0x00'+'0000',
                'ca7':  self.ca_latency   + '0100'+'1000' + '1000'+'x000' + 'x000'+'0100' + '1000'+'1000' + '1x00'+'0000',
                'ca8':  self.ca_latency   + '1000'+'1100' + '0000'+'x000' + 'x000'+'0x00' + '0000'+'0000' + '1x00'+'0000',
                'ca9':  self.ca_latency   + '0x00'+'0x00' + '0100'+'x000' + 'x000'+'1x00' + '0000'+'0000' + '0x00'+'0000',
                'ca10': self.ca_latency   + '0100'+'0100' + '0100'+'0000' + '0000'+'1x00' + '0000'+'0000' + '1x00'+'0000',
                'ca11': self.ca_latency   + 'xx00'+'x100' + 'x100'+'x000' + 'x000'+'0x00' + '0000'+'0000' + '0x00'+'0000',
                'ca12': self.ca_latency   + 'xx00'+'xx00' + 'x100'+'x000' + 'x000'+'0x00' + '0000'+'0000' + '0x00'+'0000',
                'ca13': self.ca_latency   + 'xx00'+'xx00' + 'x000'+'x000' + 'x000'+'xx00' + 'x000'+'x000' + 'xx00'+'0000',
            }},
            vcd_name="ddr5_ca_addressing.vcd"
        )

    def test_ddr5_dq_out(self):
        # Test serialization of dfi wrdata to DQ pads
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        zero = '00000000' * 2  # zero for 1 sysclk clock in sys8x_ddr clock domain
        write_latency = phy.settings.write_latency

        dfi_data = {
            0: dict(wrdata=0x1122),
            1: dict(wrdata=0x3344),
            2: dict(wrdata=0x5566),
            3: dict(wrdata=0x7788),
            4: dict(wrdata=0x99aa),
            5: dict(wrdata=0xbbcc),
            6: dict(wrdata=0xddee),
            7: dict(wrdata=0xff00),
        }
        dfi_wrdata_en = {0: dict(wrdata_en=1)}  # wrdata_en=1 required on any single phase

        self.run_test(dut = phy,
            dfi_sequence = [
                dfi_wrdata_en,
                *[{} for _ in range(write_latency - 1)],
                dfi_data,
            ],
            pad_checkers = {"sys4x_90_ddr": {
                f'dq{i}': (phy.settings.cmd_latency + write_latency) * zero + dq_pattern(i, dfi_data, "wrdata") + zero for i in range(8)
            }},
            vcd_name="ddr_dq_out.vcd"
        )

    def test_ddr5_dq_only_1cycle(self):
        # Test that DQ data is sent to pads only during expected cycle, on other cycles there is no data
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        zero = '00000000' * 2
        write_latency = phy.settings.write_latency

        dfi_data = {
            0: dict(wrdata=0x1122),
            1: dict(wrdata=0x3344),
            2: dict(wrdata=0x5566),
            3: dict(wrdata=0x7788),
            4: dict(wrdata=0x99aa),
            5: dict(wrdata=0xbbcc),
            6: dict(wrdata=0xddee),
            7: dict(wrdata=0xff00),
        }
        dfi_wrdata_en = copy.deepcopy(dfi_data)
        dfi_wrdata_en[0].update(dict(wrdata_en=1))

        self.run_test(dut = phy,
            dfi_sequence = [
                dfi_wrdata_en,
                *[dfi_data for _ in range(write_latency)], # only last should be handled
            ],
            pad_checkers = {"sys4x_90_ddr": {
                f'dq{i}': (phy.settings.cmd_latency + write_latency)*zero + dq_pattern(i, dfi_data, "wrdata") + zero for i in range(8)
            }},
            vcd_name="ddr_dq_only_1cycle.vcd"
        )

    def test_ddr5_dqs(self):
        # Test serialization of DQS pattern in relation to DQ data, with proper preamble and postamble
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        zero = '00000000' * 2
        xs = 'xxxxxxxx' * 2
        write_latency = phy.settings.write_latency

        self.run_test(dut = phy,
            dfi_sequence = [
                {0: dict(wrdata_en=1)},
                *[{} for _ in range(write_latency - 1)],
                {  # to get 10101010... pattern on dq0 and only 1s on others
                    0: dict(wrdata=0xfeff),
                    1: dict(wrdata=0xfeff),
                    2: dict(wrdata=0xfeff),
                    3: dict(wrdata=0xfeff),
                    4: dict(wrdata=0xfeff),
                    5: dict(wrdata=0xfeff),
                    6: dict(wrdata=0xfeff),
                    7: dict(wrdata=0xfeff),
                },
            ],
            pad_checkers = {
                "sys4x_90_ddr": {
                    'dq0':  (phy.settings.cmd_latency + write_latency) * zero + '10101010'+'10101010' + '00000000'+'00000000' + zero,
                    'dq1':  (phy.settings.cmd_latency + write_latency) * zero + '11111111'+'11111111' + '00000000'+'00000000' + zero,
                },
                "sys4x_ddr": {
                    "dqs0": (phy.settings.cmd_latency + write_latency - 1) * xs + 'xxxxxxxx'+'xxxxx001' + '01010101'+'01010101' + '0xxxxxxxx' + xs,
                }
            },
            vcd_name="ddr5_dqs.vcd"
        )

    def test_ddr5_cmd_write(self):
        # Test whole WRITE command sequence verifying data on pads and write_latency from MC perspective
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        latency   = '00000000' * phy.settings.cmd_latency
        latency_n = '11111111' * phy.settings.cmd_latency
        zeros = '00000000' * 2
        ones = '11111111' * 2
        xs = 'xxxxxxxx' * 2
        write_latency = phy.settings.write_latency
        wrphase = phy.settings.wrphase.reset.value

        dfi_data = {
            0: dict(wrdata=0x1122),
            1: dict(wrdata=0x3344),
            2: dict(wrdata=0x5566),
            3: dict(wrdata=0x7788),
            4: dict(wrdata=0x99aa),
            5: dict(wrdata=0xbbcc),
            6: dict(wrdata=0xddee),
            7: dict(wrdata=0xff00),
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

        self.run_test(dut = phy,
            dfi_sequence = dfi_sequence,
            pad_checkers = {
                "sys4x_90": {
                    "cs_n": latency_n + "11011111" + ones,
                    "ca0":  latency   + "00100000" + zeros,
                    "ca1":  latency   + "00000000" + zeros,
                    "ca2":  latency   + "00100000" + zeros,
                    "ca3":  latency   + "00100000" + zeros,
                    "ca4":  latency   + "00000000" + zeros,
                    "ca5":  latency   + "00100000" + zeros,
                    "ca6":  latency   + "00000000" + zeros,
                    "ca7":  latency   + "00000000" + zeros,
                    "ca8":  latency   + "00000000" + zeros,
                    "ca9":  latency   + "00000000" + zeros,
                    "ca10":  latency  + "00010000" + zeros,
                    "ca11":  latency  + "00000000" + zeros,
                    "ca12":  latency  + "00000000" + zeros,
                    "ca13":  latency  + "00000000" + zeros,
                },
                "sys4x_90_ddr": {
                    f'dq{i}': (phy.settings.cmd_latency + write_latency) * zeros + dq_pattern(i, dfi_data, "wrdata") + zeros
                            for i in range(8)
                },
                "sys4x_ddr": {
                    "dqs0": (phy.settings.cmd_latency + write_latency - 1) * xs + 'xxxxxxxx'+'xxxxx001' + '01010101'+'01010101' + '0xxxxxxxx' + xs,
                },
            },
            vcd_name="ddr5_write.vcd"
        )

    def test_ddr5_dq_in_rddata_valid(self):
        # Test that rddata_valid is set with correct delay
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        dfi_sequence = [
            {0: dict(rddata_en=1)},  # command is issued by MC (appears on next cycle)
            *[{p: dict(rddata_valid=0) for p in range(8)} for _ in range(phy.settings.read_latency - 1)],  # nothing is sent during write latency
            {p: dict(rddata_valid=1) for p in range(8)},
            {},
        ]

        self.run_test(dut = phy,
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {},
            vcd_name="ddr5_dq_in_rddata_valid.vcd"
        )

    def test_ddr5_dq_in_rddata(self):
        # Test that data on DQ pads is deserialized correctly to DFI rddata.
        # We assume that when there are no commands, PHY will still deserialize the data,
        # which is generally true (tristate oe is 0 whenever we are not writing).
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        dfi_data = {
            0: dict(rddata=0x1122),
            1: dict(rddata=0x3344),
            2: dict(rddata=0x5566),
            3: dict(rddata=0x7788),
            4: dict(rddata=0x99aa),
            5: dict(rddata=0xbbcc),
            6: dict(rddata=0xddee),
            7: dict(rddata=0xff00),
        }

        def sim_dq(pads):
            for _ in range(16 * 1):  # wait 1 sysclk cycle
                yield
            for cyc in range(16):  # send a burst of data on pads
                for bit in range(8):
                    yield pads.dq_i[bit].eq(int(dq_pattern(bit, dfi_data, "rddata")[cyc]))
                yield
            for bit in range(8):
                yield pads.dq_i[bit].eq(0)
            yield

        read_des_delay = 4  # phy.read_des_delay
        dfi_sequence = [
            {},  # wait 1 sysclk cycle
            *[{} for _ in range(read_des_delay - 1)],
            dfi_data,
            {},
        ]

        self.run_test(dut = phy,
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {
                "sys4x_90_ddr": sim_dq,
            },
            vcd_name="ddr_dq_in_rddata.vcd"
        )

    def test_ddr5_cmd_read(self):
        # Test whole READ command sequence simulating DRAM response and verifying read_latency from MC perspective
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        zeros = '00000000' * 2
        ones = '11111111' * 2
        xs = 'xxxxxxxx' * 2
        cmd_latency = phy.settings.cmd_latency
        read_latency = phy.settings.read_latency
        rdphase = phy.settings.rdphase.reset.value
        read_des_delay = 4  # phy.read_des_delay

        # FIXME: The data will appear 1 cycle before rddata_valid. This is because we have one more cycle
        # of read latency that is needed for bitslips to be usable, and here we're not doing read leveling
        # so the bitslip is configured incorrectly. If we increased cl by 1 in Simulator and did a single
        # bitslip increment before the test, it should work, but this would unnecessarily complicate the test.

        data_to_read = {
            0: dict(rddata=0x1122),
            1: dict(rddata=0x3344),
            2: dict(rddata=0x5566),
            3: dict(rddata=0x7788),
            4: dict(rddata=0x99aa),
            5: dict(rddata=0xbbcc),
            6: dict(rddata=0xddee),
            7: dict(rddata=0xff00),
        }

        dfi_data_valid = {
            0: dict(rddata_valid=1),
            1: dict(rddata_valid=1),
            2: dict(rddata_valid=1),
            3: dict(rddata_valid=1),
            4: dict(rddata_valid=1),
            5: dict(rddata_valid=1),
            6: dict(rddata_valid=1),
            7: dict(rddata_valid=1),
        }

        dfi_sequence = [
            {rdphase: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, rddata_en=1)},
            *[{} for _ in range(read_latency - 1 - 1)],
            data_to_read,
            dfi_data_valid,
            {},
            {},
            {},
        ]

        class Simulator:
            def __init__(self, data, test_case, cl):
                self.data = data
                self.read_cmd = False
                self.test_case = test_case
                self.cl = cl

            @passive
            def cmd_checker(self, pads):
                # Monitors CA/CS_n for a READ command
                read = [
                    0b00000000111101,  # READ-1 (1) BL=1, BA=0, BG=0, CID=0
                    0b00010000000000,  # READ-1 (2) BA=0, C=0, AP=0, CID3=0
                ]

                def check_ca(i):
                    err = "{}: CA = 0b{:06b}, expected = 0b{:06b}".format(i, (yield pads.ca), read[i])
                    self.test_case.assertEqual((yield pads.ca), read[i], msg=err)

                while True:
                    while (yield pads.cs_n):
                        yield
                    yield from check_ca(0)
                    yield
                    yield from check_ca(1)
                    self.read_cmd = True

            @passive
            def dq_generator(self, pads):
                # After a READ command is received, wait CL and send data
                while True:
                    while not self.read_cmd:
                        yield
                    data = self.data.pop(0)
                    for _ in range(2*self.cl + 1):
                        yield
                    self.read_cmd = False
                    for cyc in range(16):
                        for bit in range(8):
                            yield pads.dq_i[bit].eq(int(dq_pattern(bit, data, "rddata")[cyc]))
                        yield
                    for bit in range(8):
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
                        yield pads.dqs_i.eq(int((cyc + 1) % 2))
                        yield
                    yield pads.dqs_i.eq(0)
                    yield
                    yield pads.dqs_i.eq(1)
                    yield
                    yield pads.dqs_i.eq(0)

        sim = Simulator([data_to_read], self, cl=22)
        self.run_test(phy,
            dfi_sequence = dfi_sequence,
            pad_checkers = {
                "sys4x_90": {
                    "cs_n": ones  + rdphase * "1" + "0111" + ones,
                    "ca0":  zeros + rdphase * "0" + "1000" + zeros,
                    "ca1":  zeros + rdphase * "0" + "0000" + zeros,
                    "ca2":  zeros + rdphase * "0" + "1000" + zeros,
                    "ca3":  zeros + rdphase * "0" + "1000" + zeros,
                    "ca4":  zeros + rdphase * "0" + "1000" + zeros,
                    "ca5":  zeros + rdphase * "0" + "1000" + zeros,
                    "ca6":  zeros + rdphase * "0" + "0000" + zeros,
                    "ca7":  zeros + rdphase * "0" + "0000" + zeros,
                    "ca8":  zeros + rdphase * "0" + "0000" + zeros,
                    "ca9":  zeros + rdphase * "0" + "0000" + zeros,
                    "ca10": zeros + rdphase * "0" + "0100" + zeros,
                    "ca11": zeros + rdphase * "0" + "0000" + zeros,
                    "ca12": zeros + rdphase * "0" + "0000" + zeros,
                    "ca13": zeros + rdphase * "0" + "0000" + zeros,
                },
                "sys4x_90_ddr": {
                    f'dq{i}': (cmd_latency + 3) * zeros + dq_pattern(i, data_to_read, "rddata") + zeros
                    for i in range(8)
                },
                "sys4x_ddr": {
                    "dqs0": (cmd_latency + 2) * xs + 'xxxxxxxx'+'xxxxx001' + '01010101'+'01010101' + '010xxxxx' + 'xxxxxxxx',
                },
            },
            pad_generators = {
                "sys4x_ddr": [sim.dq_generator, sim.dqs_generator],
                "sys4x_90": sim.cmd_checker,
            },
            vcd_name="ddr5_cmd_read.vcd"
        )
