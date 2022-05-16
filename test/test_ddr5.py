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
run_simulation = partial(test.phy_common.run_simulation, clocks={
    "sys":          (64, 31),
    "sys2x":        (32, 15),
    "sys8x":        ( 8,  3),
    "sys8x_ddr":    ( 4,  1),
    "sys8x_90":     ( 8,  1),
    "sys8x_90_ddr": ( 4,  3),
})

dfi_data_to_dq = partial(test.phy_common.dfi_data_to_dq, databits=8, nphases=8, burst=16)
dq_pattern = partial(test.phy_common.dq_pattern, databits=8, nphases=8, burst=16)


class DDR5Tests(unittest.TestCase):
    SYS_CLK_FREQ = 50e6

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

    def test_ddr5_cs_n_phase_0(self):
        # Test that CS_n is serialized correctly when sending command on phase 0
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        latency_n = '11111111' * phy.settings.cmd_latency

        self.run_test(dut = phy,
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},  # p0: READ
            ],
            pad_checkers = {"sys8x_90": {
                'cs_n': latency_n + '01111111',
            }},
        )

    def test_ddr5_cs_n_phase_3(self):
        # Test that CS_n is serialized correctly when sending command on phase 3
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        latency_n = '11111111' * phy.settings.cmd_latency

        self.run_test(dut = phy,
            dfi_sequence = [
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=0)},  # p3: WRITE
            ],
            pad_checkers = {"sys8x_90": {
                'cs_n': latency_n + '11101111',
            }},
        )

    def test_ddr5_clk(self):
        # Test clock serialization
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)

        self.run_test(dut = phy,
            dfi_sequence = [
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
            ],
            pad_checkers = {"sys8x_90_ddr": {
                'clk': '01010101' * (phy.settings.cmd_latency + 1),
            }},
        )

    def test_ddr5_cs_n_multiple_phases(self):
        # Test that CS_n is serialized on different phases and that overlapping commands are handled
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        latency_n = '11111111' * phy.settings.cmd_latency

        self.run_test(dut = phy,
            dfi_sequence = [
                {0: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {
                    1: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),
                    2: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),  # should be ignored
                },
                {
                    1: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),
                    5: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1),  # should NOT be ignored
                },
                {7: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
                {0: dict(cs_n=0, cas_n=1, ras_n=0, we_n=0)},  # should be ignored due to command on previous cycle
                {2: dict(cs_n=1, cas_n=0, ras_n=1, we_n=1)},  # ignored due to cs_n=1
            ],
            pad_checkers = {"sys8x_90": {
                'cs_n': latency_n + ''.join([
                    '01111111',  # p0
                    '11101111',  # p3
                    '10111111',  # p1, p2 ignored
                    '10111011',  # p1, p5
                    '11111110',  # p7 (1st part)
                    '11111111',  # (2nd part of the previous command), p0 ignored
                    '11111111',  # p2 ignored
                ])
            }},
        )

    def test_ddr5_empty_command_sequence(self):
        # Test CS_n/CA values for empty dfi commands sequence
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        latency   = '00000000' * phy.settings.cmd_latency
        latency_n = '11111111' * phy.settings.cmd_latency

        self.run_test(dut = phy,
                      dfi_sequence = [],
                      pad_checkers = {"sys8x_90": {
                          'cs_n': latency_n,
                          'ca0':  latency,
                          'ca1':  latency,
                          'ca2':  latency,
                          'ca3':  latency,
                          'ca4':  latency,
                          'ca5':  latency,
                          'ca6':  latency,
                          'ca7':  latency,
                          'ca8':  latency,
                          'ca9':  latency,
                          'ca10': latency,
                          'ca11': latency,
                          'ca12': latency,
                          'ca13': latency,
                      }},
                      )

    def test_ddr5_ca_addressing(self):
        # Test that bank/address for different commands are correctly serialized to CA pads
        phy = DDR5SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        latency   = '00000000' * phy.settings.cmd_latency
        latency_n = '11111111' * phy.settings.cmd_latency

        read          = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b101,    address=0b1100110000)
        write_ap      = dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, bank=0b111,    address=0b10000000000)
        activate      = dict(cs_n=0, cas_n=1, ras_n=0, we_n=1, bank=0b010,    address=0b11110000111100001)
        refresh_ab    = dict(cs_n=0, cas_n=0, ras_n=0, we_n=1, bank=0b100,    address=0)
        precharge_ab  = dict(cs_n=0, cas_n=1, ras_n=0, we_n=0, bank=0b011,    address=0)
        mrw           = dict(cs_n=0, cas_n=0, ras_n=0, we_n=0, bank=0b110011, address=0b10101010)  # bank=6-bit address, address=8-bit op code
        zqc_start     = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=0,        address=0b0000101)  # MPC with ZQCAL START operand
        zqc_latch     = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=0,        address=0b0000100)  # MPC with ZQCAL LATCH operand
        mrr           = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=1,        address=0b101101)  # 6-bit address (bank=1 selects MRR)

        self.run_test(dut = phy,
                      dfi_sequence = [
                          {0: read, 4: write_ap},
                          {0: activate, 4: refresh_ab},
                          {0: precharge_ab, 4: mrw},
                          {0: zqc_start, 4: zqc_latch},
                          {0: mrr},
                      ],
                      pad_checkers = {"sys8x_90": {
                          #                    rd     wr       act    ref      pre    mrw      zqcs   zqcl     mrr
                          'cs_n': latency_n + '0111'+'0111' + '0111'+'0111' + '0111'+'0111' + '0111'+'0111' + '0111'+'1111',
                          'ca0':  latency   + '1000'+'1x00' + '0000'+'1000' + '1000'+'1000' + '1000'+'1000' + '1000'+'0000',
                          'ca1':  latency   + '0000'+'0000' + '0100'+'1000' + '1000'+'0100' + '1000'+'1000' + '0000'+'0000',
                          'ca2':  latency   + '1100'+'1000' + '1100'+'0000' + '0000'+'1000' + '1000'+'1000' + '1x00'+'0000',
                          'ca3':  latency   + '1100'+'1000' + '0100'+'0000' + '1000'+'0100' + '1000'+'1000' + '0x00'+'0000',
                          'ca4':  latency   + '1000'+'0000' + '0100'+'1000' + '0000'+'0000' + '0000'+'0000' + '1x00'+'0000',
                          'ca5':  latency   + '1000'+'1000' + '0000'+'x000' + 'x000'+'1100' + '1000'+'0000' + '1x00'+'0000',
                          'ca6':  latency   + '1100'+'1000' + '0000'+'x000' + 'x000'+'1000' + '0000'+'0000' + '0x00'+'0000',
                          'ca7':  latency   + '0100'+'1000' + '1000'+'x000' + 'x000'+'0100' + '1000'+'1000' + '1x00'+'0000',
                          'ca8':  latency   + '1000'+'1100' + '0000'+'x000' + 'x000'+'0x00' + '0000'+'0000' + '1x00'+'0000',
                          'ca9':  latency   + '0x00'+'0x00' + '0100'+'x000' + 'x000'+'1x00' + '0000'+'0000' + '0x00'+'0000',
                          'ca10': latency   + '0100'+'0100' + '0100'+'0000' + '0000'+'1x00' + '0000'+'0000' + '1x00'+'0000',
                          'ca11': latency   + 'xx00'+'x100' + 'x100'+'x000' + 'x000'+'0x00' + '0000'+'0000' + '0x00'+'0000',
                          'ca12': latency   + 'xx00'+'xx00' + 'x100'+'x000' + 'x000'+'0x00' + '0000'+'0000' + '0x00'+'0000',
                          'ca13': latency   + 'xx00'+'xx00' + 'x000'+'x000' + 'x000'+'xx00' + 'x000'+'x000' + 'xx00'+'0000',
                      }},
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
            pad_checkers = {"sys8x_90_ddr": {
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
            pad_checkers = {"sys8x_90_ddr": {
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
                "sys8x_90_ddr": {
                    'dq0':  (phy.settings.cmd_latency + write_latency) * zero + '10101010'+'10101010' + '00000000'+'00000000' + zero,
                    'dq1':  (phy.settings.cmd_latency + write_latency) * zero + '11111111'+'11111111' + '00000000'+'00000000' + zero,
                },
                "sys8x_ddr": {
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
                "sys8x_90": {
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
                    "ca11":  latency  + "00010000" + zeros,
                    "ca12":  latency  + "00000000" + zeros,
                    "ca13":  latency  + "00000000" + zeros,
                },
                "sys8x_90_ddr": {
                    f'dq{i}': (phy.settings.cmd_latency + write_latency) * zeros + dq_pattern(i, dfi_data, "wrdata") + zeros
                            for i in range(8)
                },
                "sys8x_ddr": {
                    "dqs0": (phy.settings.cmd_latency + write_latency - 1) * xs + 'xxxxxxxx'+'xxxxx001' + '01010101'+'01010101' + '0xxxxxxxx' + xs,
                },
            },
            vcd_name="ddr5_write.vcd"
        )
