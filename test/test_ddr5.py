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

from litedram.phy.ddr5.simphy import DDR5SimPHY
from litedram.phy.ddr5 import simsoc
from litedram.phy.sim_utils import SimLogger
from litedram.phy.utils import Serializer, Deserializer

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
    "sys":            (64, 31),
    "sys_rst":        (64, 30),
    "sys2x":          (32, 15),
    "sys4x":          (16,  7),
    "sys4x_ddr":      ( 8,  3),
    "sys4x_90":       (16,  3),
    "sys4x_90_ddr":   ( 8,  7),
    "sys4x_180":      (16, 15),
    "sys4x_180s_ddr": ( 8,  5),
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
        self.dq_wr_latency:    str = self.xs * 2 + (self.cmd_latency + self.write_latency) * self.zeros  + 'x' * (self.NPHASES - 1) * 2

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
                'ck_t': self.xs * 3 + '10101010' * (self.cmd_latency),
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

        dfi_data = [
            {
                0: dict(wrdata=0x1122),
                1: dict(wrdata=0x3344),
                2: dict(wrdata=0x5566),
                3: dict(wrdata=0x7788),
            },
            {
                0: dict(wrdata=0x99aa),
                1: dict(wrdata=0xbbcc),
                2: dict(wrdata=0xddee),
                3: dict(wrdata=0xff00),
            },
        ]
        dfi_wrdata_en = {self.wrphase: dict(wrdata_en=1)}  # wrdata_en=1 required on any single phase

        self.run_test(
            dfi_sequence = [
                dfi_wrdata_en,
                dfi_wrdata_en,
                *[{} for _ in range(self.write_latency - 2)],
                *dfi_data,
            ],
            pad_checkers = {"sys4x_ddr": {
                f'dq{i}': self.dq_wr_latency +
                    self.dq_pattern(i, dfi_data[0], "wrdata") + self.dq_pattern(i, dfi_data[1], "wrdata") +
                    self.zeros for i in range(self.DATABITS)
            }},
            vcd_name="ddr5_dq_out.vcd"
        )

    def test_ddr5_dq_only_1cycle(self):
        # Test that DQ data is sent to pads only during expected cycle, on other cycles there is no data

        dfi_data = {
            0: dict(wrdata=0x1122),
            1: dict(wrdata=0x3344),
            2: dict(wrdata=0x5566),
            3: dict(wrdata=0x7788),
        }
        dfi_wrdata_en = copy.deepcopy(dfi_data)
        dfi_wrdata_en[self.wrphase].update(dict(wrdata_en=1))

        self.run_test(
            dfi_sequence = [
                dfi_wrdata_en,
                *[dfi_data for _ in range(self.write_latency)], # only last should be handled
            ],
            pad_checkers = {"sys4x_ddr": {
                f'dq{i}': self.dq_wr_latency + self.dq_pattern(i, dfi_data, "wrdata") + self.zeros for i in range(self.DATABITS)
            }},
            vcd_name="ddr5_dq_only_1cycle.vcd"
        )

    def test_ddr5_dqs(self):
        # Test serialization of DQS pattern in relation to DQ data, with proper preamble and postamble


        self.run_test(
            dfi_sequence = [
                {self.wrphase: dict(wrdata_en=1)},
                *[{} for _ in range(self.write_latency - 1)],
                {  # to get 10101010... pattern on dq0 and only 1s on others
                    0: dict(wrdata=0xfeff),
                    1: dict(wrdata=0xfeff),
                    2: dict(wrdata=0xfeff),
                    3: dict(wrdata=0xfeff),
                },
                {
                },
            ],
            pad_checkers = {
                "sys4x_90_ddr": {
                    "dqs_t0": self.dqs_t_wr_latency + 'xxxx0010' + '10101010'+ '0xxxxxxx',
                },
                "sys4x_ddr": {
                    "dq0":  self.dq_wr_latency + '10101010' + self.zeros,
                    "dq1":  self.dq_wr_latency + '11111111' + self.zeros,
                }
            },
            vcd_name="ddr5_dqs.vcd"
        )

    def test_ddr5_cmd_write(self):
        # Test whole WRITE command sequence verifying data on pads and write_latency from MC perspective

        dfi_data = [
            {
                0: dict(wrdata=0x1122),
                1: dict(wrdata=0x3344),
                2: dict(wrdata=0x5566),
                3: dict(wrdata=0x7788),
            },
            {
                0: dict(wrdata=0x99aa),
                1: dict(wrdata=0xbbcc),
                2: dict(wrdata=0xddee),
                3: dict(wrdata=0xff00),
            },
        ]

        write_0   = dict(cs_n=0, address=self.process_ca('10110 0 00000 000'))  # WR p0
        write_1   = dict(cs_n=1, address=self.process_ca('000000000 01100'))    # WR p1

        dfi_sequence = [
            {
                self.wrphase:     write_0 | dict(wrdata_en=1),
                self.wrphase + 1: write_1,
            },
            {
                self.wrphase:     write_0 | dict(wrdata_en=1),
                self.wrphase + 1: write_1,
            },
            *[{} for _ in range(self.write_latency - 2)],
            *dfi_data,
            {},
            {},
            {},
            {},
            {},
        ]

        self.run_test(
            dfi_sequence = dfi_sequence,
            pad_checkers = {
                "sys4x": {
                    "cs_n": self.cs_n_latency + "11011101" + self.ones,
                    "ca0":  self.ca_latency   + "00100010" + self.zeros,
                    "ca1":  self.ca_latency   + "00000000" + self.zeros,
                    "ca2":  self.ca_latency   + "00100010" + self.zeros,
                    "ca3":  self.ca_latency   + "00100010" + self.zeros,
                    "ca4":  self.ca_latency   + "00000000" + self.zeros,
                    "ca5":  self.ca_latency   + "00000000" + self.zeros,
                    "ca6":  self.ca_latency   + "00000000" + self.zeros,
                    "ca7":  self.ca_latency   + "00000000" + self.zeros,
                    "ca8":  self.ca_latency   + "00000000" + self.zeros,
                    "ca9":  self.ca_latency   + "00000000" + self.zeros,
                    "ca10": self.ca_latency   + "00010001" + self.zeros,
                    "ca11": self.ca_latency   + "00010001" + self.zeros,
                    "ca12": self.ca_latency   + "00000000" + self.zeros,
                    "ca13": self.ca_latency   + "00000000" + self.zeros,
                },
                "sys4x_90_ddr": { #                    preamble                              postamble
                    "dqs_t0": self.dqs_t_wr_latency + 'xxxx0010' + '10101010' + '10101010' + '0xxxxxxx',
                },
                "sys4x_ddr": {
                    f'dq{i}': self.dq_wr_latency +
                        self.dq_pattern(i, dfi_data[0], "wrdata") + self.dq_pattern(i, dfi_data[1], "wrdata") +
                        self.zeros for i in range(self.BURST_LENGTH)
                }
            },
            vcd_name="ddr5_cmd_write.vcd"
        )

    def test_ddr5_dq_in_rddata_valid(self):
        # Test that rddata_valid is set with correct delay
        dfi_sequence = [
            {0: dict(rddata_en=1)},  # command is issued by MC (appears on next cycle)
            *[{p: dict(rddata_valid=0) for p in range(self.NPHASES)} for _ in range(self.read_latency)],  # nothing is sent during read latency
            {p: dict(rddata_valid=1) for p in range(self.NPHASES)},
            {},
        ]

        self.run_test(
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {},
            vcd_name="ddr5_dq_in_rddata_valid.vcd"
        )

    def test_ddr5_dq_in_rddata(self):
        # Test that data on DQ pads is deserialized correctly to DFI rddata.
        # We assume that when there are no commands, PHY will still deserialize the data,
        # which is generally true (tristate oe is 0 whenever we are not writing).
        dfi_data = {
            0: dict(rddata=0x1122),
            1: dict(rddata=0x3344),
            2: dict(rddata=0x5566),
            3: dict(rddata=0x7788),
        }

        expected_data = [
            {
                1: dict(rddata=0x1122),
                2: dict(rddata=0x3344),
                3: dict(rddata=0x5566),
            },
            {
                0: dict(rddata=0x7788),
            }
        ]

        def sim_dq(pads):
            for _ in range(self.NPHASES * 4):  # wait reset
                yield
            for _ in range(self.NPHASES * 2):  # wait 1 sysclk cycle
                yield
            for cyc in range(self.BURST_LENGTH):  # send a burst of data on pads
                for bit in range(self.DATABITS):
                    yield pads.dq_i[bit].eq(int(self.dq_pattern(bit, dfi_data, "rddata")[cyc]))
                yield
            for bit in range(self.DATABITS):
                yield pads.dq_i[bit].eq(0)
            yield

        dfi_sequence = [
            {},  # wait 1 sysclk cycle
            *[{} for _ in range(Deserializer.LATENCY-1)],
            *expected_data,
            {},
        ]

        self.run_test(
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {
                "sys4x_ddr": sim_dq,
            },
            vcd_name="ddr5_dq_in_rddata.vcd"
        )

    def test_ddr5_cmd_read(self):
        # Test whole READ command sequence simulating DRAM response and verifying read_latency from MC perspective

        data_to_read = {
            0: dict(rddata=0x1122),
            1: dict(rddata=0x3344),
            2: dict(rddata=0x5566),
            3: dict(rddata=0x7788),
        }

        dfi_data_valid = {
            0: dict(rddata_valid=1),
            1: dict(rddata_valid=1),
            2: dict(rddata_valid=1),
            3: dict(rddata_valid=1),
        }

        read_0 = dict(cs_n=0, address=self.process_ca('10111 0 00000 000'))  # RD p0
        read_1 = dict(cs_n=1, address=self.process_ca('000000000 01000'))    # RD p1
        dfi_sequence = [
            {
                self.rdphase:     read_0 | dict(rddata_en=1),
                self.rdphase + 1: read_1,
            },
            *[{} for _ in range(self.read_latency - 1)],
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
                    0b00000000011101,  # READ-1 (1) BL=0, BA=0, BG=0, CID=0
                    0b00010000000000,  # READ-1 (2) BA=0, C=0, AP=0, CID3=0
                ]

                def check_ca(i):
                    err = "{}: CA = 0b{:06b}, expected = 0b{:06b}".format(i, (yield pads.ca), read[i])
                    self.test_case.assertEqual((yield pads.ca), read[i], msg=err)

                # wait reset
                for _ in range(self.test_case.NPHASES * 4):
                    yield

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
                    for _ in range(2*self.cl - 1):
                        yield
                    self.read_cmd = False
                    for cyc in range(self.test_case.BURST_LENGTH):
                        for bit in range(self.test_case.DATABITS):
                            yield pads.dq_i[bit].eq(int(self.test_case.dq_pattern(bit, data, "rddata")[cyc]))
                        yield
                    for bit in range(self.test_case.DATABITS):
                        yield pads.dq_i[bit].eq(0)

            @passive
            def dqs_generator(self, pads):
                # After a READ command is received, wait CL and send data strobe
                while True:
                    while not self.read_cmd:
                        yield
                    preamble = "0010"
                    for _ in range(2*self.cl - len(preamble) - 1):  # wait CL without DQS preamble
                        yield
                    for bit in preamble: # send DQS preamble
                        yield pads.dqs_t_i.eq(int(bit))
                        yield
                    for cyc in range(1, self.test_case.BURST_LENGTH):  # send a burst of data on pads
                        yield pads.dqs_t_i.eq(cyc % 2)
                        yield
                    for bit in "010": # send DQS postamble
                        yield pads.dqs_t_i.eq(int(bit))
                        yield

        sim = Simulator([data_to_read], self, cl=22)
        self.run_test(
            dfi_sequence = dfi_sequence,
            pad_checkers = {
                "sys4x": {
                    "cs_n": self.cs_n_latency + self.rdphase * "1" + "0111" + self.ones,
                    "ca0":  self.ca_latency   + self.rdphase * "0" + "1000" + self.zeros,
                    "ca1":  self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                    "ca2":  self.ca_latency   + self.rdphase * "0" + "1000" + self.zeros,
                    "ca3":  self.ca_latency   + self.rdphase * "0" + "1000" + self.zeros,
                    "ca4":  self.ca_latency   + self.rdphase * "0" + "1000" + self.zeros,
                    "ca5":  self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                    "ca6":  self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                    "ca7":  self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                    "ca8":  self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                    "ca9":  self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                    "ca10": self.ca_latency   + self.rdphase * "0" + "0100" + self.zeros,
                    "ca11": self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                    "ca12": self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                    "ca13": self.ca_latency   + self.rdphase * "0" + "0000" + self.zeros,
                },
                "sys4x_90_ddr": { #                    preamble                  postamble
                    "dqs_t0": self.dqs_t_rd_latency + 'xxxx0010' + '10101010' + '10xxxxxx',
                } | {
                    f'dq{i}': self.dq_rd_latency + self.dq_pattern(i, data_to_read, "rddata") + self.zeros
                    for i in range(self.DATABITS)
                },
            },
            pad_generators = {
                "sys4x_ddr": [sim.dq_generator, sim.dqs_generator],
                "sys4x_90": sim.cmd_checker,
            },
            vcd_name="ddr5_cmd_read.vcd"
        )


class VerilatorDDR5Tests(unittest.TestCase):
    ALLOWED = []

    def check_logs(self, logs):
        memory_init = False
        for line in logs.splitlines():
            if "Switching SDRAM to software control." in line:
                memory_init = True

            match = SimLogger.LOG_PATTERN.match(line)
            if memory_init and match and match.group("level") in ["WARN", "ERROR"]:
                allowed = any(
                    lvl == match.group("level") and msg in match.group("msg")
                    for lvl, msg in self.ALLOWED
                )
                self.assertTrue(allowed, msg=match.group(0))

    def run_test(self, args, **kwargs):
        import pexpect

        command = ["python3", simsoc.__file__, *args]
        timeout = 30 * 60  # give more than enough time for CI
        p = pexpect.spawn(" ".join(command), timeout=timeout, **kwargs)

        res = p.expect(["Memtest OK", "Memtest KO"])
        self.assertEqual(res, 0, msg="{}\nGot '{}'".format(p.before.decode(), p.after.decode()))

        self.check_logs(p.before.decode())

    def test_ddr5_sim_dq_dqs_ratio_4(self):
        # Test simulation with regular delays, intermediate serialization stage,
        # refresh and with L2 cache (masked write doesn't work for x4)
        self.run_test([
            "--finish-after-memtest", "--log-level", "warn",
            "--output-dir", "build/test_ddr5_sim_dq_dqs_ratio_4",
            "--l2-size", "32",
            "--dq-dqs-ratio", "4",
        ])

    def test_ddr5_sim_dq_dqs_ratio_8(self):
        # Test simulation with regular delays, intermediate serialization stage,
        # refresh and no L2 cache (masked write must work)
        self.run_test([
            "--finish-after-memtest", "--log-level", "warn",
            "--output-dir", "build/test_ddr5_sim_dq_dqs_ratio_8",
            "--l2-size", "0",
            "--dq-dqs-ratio", "8",
        ])

    def test_ddr5_sim_dq_dqs_ratio_4_with_sub_channels(self):
        # Test simulation with regular delays, intermediate serialization stage,
        # refresh and with L2 cache (masked write doesn't work for x4)
        self.run_test([
            "--finish-after-memtest", "--log-level", "warn",
            "--output-dir", "build/test_ddr5_sim_dq_dqs_ratio_4_with_sub_channels",
            "--l2-size", "32",
            "--dq-dqs-ratio", "4",
            "--with-sub-channels",
        ])

    def test_ddr5_sim_dq_dqs_ratio_8_with_sub_channels(self):
        # Test simulation with regular delays, intermediate serialization stage,
        # refresh and no L2 cache (masked write must work)
        self.run_test([
            "--finish-after-memtest", "--log-level", "warn",
            "--output-dir", "build/test_ddr5_sim_dq_dqs_ratio_8_with_sub_channels",
            "--l2-size", "0",
            "--dq-dqs-ratio", "8",
            "--with-sub-channels",
        ])
