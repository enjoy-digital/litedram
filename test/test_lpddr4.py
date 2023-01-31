#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import re
import copy
import unittest
from typing import Mapping
from functools import partial
from collections import defaultdict

from migen import *

from litedram.phy.lpddr4.simphy import LPDDR4SimPHY, DoubleRateLPDDR4SimPHY
from litedram.phy.lpddr4 import simsoc
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

dfi_data_to_dq = partial(test.phy_common.dfi_data_to_dq, databits=16, nphases=8, burst=16)
dq_pattern = partial(test.phy_common.dq_pattern, databits=16, nphases=8, burst=16)


class LPDDR4Tests(unittest.TestCase):
    SYS_CLK_FREQ = 100e6
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
        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
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
        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
            dfi_sequence = [
                {3: dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)},
            ],
            pad_checkers = {"sys8x_90_ddr": {
                'clk': latency + '01010101' * 3,
            }},
        )

    def test_lpddr4_cs_multiple_phases(self):
        # Test that CS is serialized on different phases and that overlapping commands are handled
        latency = '00000000' * self.CMD_LATENCY
        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
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
        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
            dfi_sequence = [
                {0: read, 3: read},  # p3 should be ignored
                {0: read, 4: read},
                {6: read},
                {0: read}, # ignored
                {7: read},
                {3: read}, # not ignored
            ],
            pad_checkers = {"sys8x_90": {
                'cs':  latency + '10100000' + '10101010' + '00000010' + '10000000' + '00000001' + '01010100',
                'ca0': latency + '00000000' + '00000000' + '00000000' + '00000000' + '00000000' + '00000000',
                'ca1': latency + '10100000' + '10101010' + '00000010' + '10000000' + '00000001' + '01010100',
                'ca2': latency + '00000000' + '00000000' + '00000000' + '00000000' + '00000000' + '00000000',
                'ca3': latency + '0x000000' + '0x000x00' + '0000000x' + '00000000' + '00000000' + 'x000x000',
                'ca4': latency + '00100000' + '00100010' + '00000000' + '10000000' + '00000000' + '01000100',
                'ca5': latency + '00000000' + '00000000' + '00000000' + '00000000' + '00000000' + '00000000',
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
        mrw        = dict(cs_n=0, cas_n=0, ras_n=0, we_n=0, bank=0b110011, address=0b10101010)  # bank=6-bit address, address=8-bit op code
        zqc_start  = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=0,     address=0b1001111)  # MPC with ZQCAL START operand
        zqc_latch  = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=0,     address=0b1010001)  # MPC with ZQCAL LATCH operand
        mrr        = dict(cs_n=0, cas_n=1, ras_n=1, we_n=0, bank=1,     address=0b101101)  # 6-bit address (bank=1 selects MRR)
        for masked_write in [True, False]:
            with self.subTest(masked_write=masked_write):
                wr_ca3 = '{}x00'.format('0' if not masked_write else '1')
                self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ, masked_write=masked_write),
                    dfi_sequence = [
                        {0: read, 4: write_ap},
                        {0: activate, 4: refresh_ab},
                        {0: precharge, 4: mrw},
                        {0: zqc_start, 4: zqc_latch},
                        {0: mrr},
                    ],
                    pad_checkers = {"sys8x_90": {
                        # note that refresh and precharge have a single command so these go as cmd2
                        # here MRR CAS-2 is sent with C[8:2] also taken from dfi.address, but this should have no influence
                        #                 rd     wr       act    ref      pre    mrw      zqcs   zqcl     mrr
                        'cs':  latency + '1010'+'1010' + '1010'+'0010' + '0010'+'1010' + '0010'+'0010' + '1010'+'0000',
                        'ca0': latency + '0100'+'0100' + '1011'+'0000' + '0001'+'0100' + '0001'+'0001' + '0101'+'0000',
                        'ca1': latency + '1010'+'0110' + '0110'+'0000' + '0001'+'1111' + '0001'+'0000' + '1011'+'0000',
                        'ca2': latency + '0101'+'1100' + '0010'+'0001' + '0000'+'1010' + '0001'+'0000' + '1100'+'0000',
                        'ca3': latency + '0x01'+wr_ca3 + '1110'+'001x' + '000x'+'0001' + '0001'+'0000' + '1101'+'0000',
                        'ca4': latency + '0110'+'0010' + '1010'+'000x' + '001x'+'0110' + '0000'+'0001' + '0010'+'0000',
                        'ca5': latency + '0010'+'0100' + '1001'+'001x' + '000x'+'1101' + '0010'+'0010' + 'x100'+'0000',
                    }},
                )

    def test_lpddr4_command_overlaps(self):
        # Test command overlap protection (can happen only if controller violates timings)
        latency = '00000000' * self.CMD_LATENCY
        read = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)
        dfi_sequence = [
            # p2 always ignored:
            # 1111
            #   1111
            #       1111
            {0: read, 2: read, 6: read},
            {},
            # p2 or both p2 and p4 ignored, depending on extended_overlaps_check
            # 1111
            #   1111
            #     1111
            {0: read, 2: read, 4: read},
        ]
        for extended_check in [False, True]:
            with self.subTest(extended_check=extended_check):
                phy = LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ, extended_overlaps_check=extended_check)
                pads = {
                    False: {'cs': latency + '10100010'+'10000000'+'10100000'},  # last cycle: p2 and p4 ignored
                    True:  {'cs': latency + '10100010'+'10000000'+'10101010'},  # last cycle: only p2 ignored
                }[extended_check]
                self.run_test(phy,
                    dfi_sequence = dfi_sequence,
                    pad_checkers = {"sys8x_90": pads},
                )

    def test_lpddr4_command_pads(self):
        # Test serialization of DFI command pins (cs/cke/odt/reset_n)
        latency = '00000000' * self.CMD_LATENCY
        read = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1)
        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
            dfi_sequence = [
                {
                    0: dict(cke=1, odt=1, reset_n=1, **read),
                    7: dict(cke=0, odt=1, reset_n=1, **read),
                },
                {
                    3: dict(cke=1, odt=0, reset_n=0, **read),
                }
            ],
            pad_checkers = {"sys8x_90": {
                'cs':      latency + '10100001' + '01010100',
                'cke':     latency + '10000000' + '00010000',
                'odt':     latency + '10000001' + '00000000',
                'reset_n': latency + '11111111' + '11101111',
            }},
        )

    def test_lpddr4_dq_out(self):
        # Test serialization of dfi wrdata to DQ pads
        dut = LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
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
        dut = LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
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

        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
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
                    'dqs0': (self.CMD_LATENCY+1)*zero + '01010101'+'00000101' + '01010101'+'01010101' + '00010101'+'01010101' + zero,
                    'dqs1': (self.CMD_LATENCY+1)*zero + '01010101'+'00000101' + '01010101'+'01010101' + '00010101'+'01010101' + zero,
                }
            },
        )

    def test_lpddr4_dmi_no_mask(self):
        # Test proper output on DMI pads. We don't implement masking now, so nothing should be sent to DMI pads
        zero = '00000000' * 2

        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
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
        read_latency = 9  # settings.read_latency
        dfi_sequence = [
            {0: dict(rddata_en=1)},  # command is issued by MC (appears on next cycle)
            *[{p: dict(rddata_valid=0) for p in range(8)} for _ in range(read_latency - 1)],  # nothing is sent during write latency
            {p: dict(rddata_valid=1) for p in range(8)},
            {},
        ]

        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
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

        self.run_test(LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ),
            dfi_sequence = dfi_sequence,
            pad_checkers = {},
            pad_generators = {
                "sys8x_90_ddr": sim_dq,
            },
        )

    def test_lpddr4_cmd_write(self):
        # Test whole WRITE command sequence verifying data on pads and write_latency from MC perspective
        for masked_write in [True, False]:
            with self.subTest(masked_write=masked_write):
                phy = LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ, masked_write=masked_write)
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

                wr_ca3 = "0000{}000".format('0' if not masked_write else '1')
                self.run_test(phy,
                    dfi_sequence = dfi_sequence,
                    pad_checkers = {
                        "sys8x_90": {
                            "cs":  "00000000"*2 + "00001010" + "00000000"*2,
                            "ca0": "00000000"*2 + "00000000" + "00000000"*2,
                            "ca1": "00000000"*2 + "00000010" + "00000000"*2,
                            "ca2": "00000000"*2 + "00001000" + "00000000"*2,
                            "ca3": "00000000"*2 +  wr_ca3    + "00000000"*2,
                            "ca4": "00000000"*2 + "00000010" + "00000000"*2,
                            "ca5": "00000000"*2 + "00000000" + "00000000"*2,
                        },
                        "sys8x_90_ddr": {
                            f'dq{i}': (self.CMD_LATENCY+1)*zero + zero + dq_pattern(i, dfi_data, "wrdata") + zero
                            for i in range(16)
                        },
                        "sys8x_ddr": {
                            "dqs0": (self.CMD_LATENCY+1)*zero + '01010101'+'00000101' + '01010101'+'01010101' + '00010101'+'01010101' + zero,
                        },
                    },
                )

    def test_lpddr4_cmd_read(self):
        # Test whole READ command sequence simulating DRAM response and verifying read_latency from MC perspective
        phy = LPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ)
        zero = '00000000' * 2
        read_latency = phy.settings.read_latency
        rdphase = phy.settings.rdphase.reset.value

        # FIXME: The data will appear 1 cycle before rddata_valid. This is because we have one more cycle
        # of read latency that is needed for bitslips to be usable, and here we're not doing read leveling
        # so the bitslip is configured incorrectly. If we increased cl by 1 in Simulator and did a single
        # bitslip increment before the test, it should work, but this would unnecessarily complicate the test.
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
            dfi_data,
            dfi_data_valid,
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

    def test_lpddr4_double_rate_phy_write(self):
        # Verify that double rate PHY works as normal one with half sys clock more latency
        phy = DoubleRateLPDDR4SimPHY(sys_clk_freq=self.SYS_CLK_FREQ, serdes_reset_cnt=-1)
        zero = '00000000' * 2  # DDR
        half = '0000'  # double rate PHY introduces latency of 4 sys8x clocks
        init_ddr_latency = (self.CMD_LATENCY + 1) * zero + half*2  # half*2 for DDR
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
                    "cs":  half + "00000000"*2 + "00001010" + "00000000"*2,
                    "ca0": half + "00000000"*2 + "00000000" + "00000000"*2,
                    "ca1": half + "00000000"*2 + "00000010" + "00000000"*2,
                    "ca2": half + "00000000"*2 + "00001000" + "00000000"*2,
                    "ca3": half + "00000000"*2 + "00001000" + "00000000"*2,
                    "ca4": half + "00000000"*2 + "00000010" + "00000000"*2,
                    "ca5": half + "00000000"*2 + "00000000" + "00000000"*2,
                },
                "sys8x_90_ddr": {
                    f'dq{i}': init_ddr_latency + zero + dq_pattern(i, dfi_data, "wrdata") + zero
                    for i in range(16)
                },
                "sys8x_ddr": {
                    "dqs0": init_ddr_latency + '01010101'+'00000101' + '01010101'+'01010101' + '00010101'+'01010101' + zero,
                },
            },
        )


class VerilatorLPDDR4Tests(unittest.TestCase):
    # We ignore these 2 warnings, they appear due to the fact that litedram starts
    # in hardware control mode which holds reset_n=1 all the time. PHY will later
    # set reset_n=0 once again and then perform proper init sequence.
    ALLOWED = [
        ("WARN", "tINIT1 violated: RESET deasserted too fast"),
        ("WARN", "tINIT3 violated: CKE set HIGH too fast after RESET being released"),
    ]

    def check_logs(self, logs):
        for match in SimLogger.LOG_PATTERN.finditer(logs):
            if match.group("level") in ["WARN", "ERROR"]:
                allowed = any(
                    lvl == match.group("level") and msg in match.group("msg")
                    for lvl, msg in self.ALLOWED
                )
                self.assertTrue(allowed, msg=match.group(0))

    def run_test(self, args, **kwargs):
        import pexpect

        command = ["python3", simsoc.__file__, *args]
        timeout = 12 * 60  # give more than enough time
        p = pexpect.spawn(" ".join(command), timeout=timeout, **kwargs)

        res = p.expect(["Memtest OK", "Memtest KO"])
        self.assertEqual(res, 0, msg="{}\nGot '{}'".format(p.before.decode(), p.after.decode()))

        self.check_logs(p.before.decode())

    def test_lpddr4_sim_x2rate_no_cache(self):
        # Test simulation with regular delays, intermediate serialization stage,
        # refresh and no L2 cache (masked write must work)
        self.run_test([
            "--finish-after-memtest", "--log-level", "warn",
            "--output-dir", "build/test_lpddr4_sim_x2rate_no_cache",
            "--double-rate-phy",
            "--l2-size", "0",
            "--no-refresh",  # FIXME: LiteDRAM sends refresh commands when only MRW/MRR are allowed
        ])

    def test_lpddr4_sim_fast(self):
        # Fast test of simulation with L2 cache (so no data masking is required)
        self.run_test([
            "--finish-after-memtest", "--log-level", "warn",
            "--output-dir", "build/test_lpddr4_sim_fast",
            "--disable-delay",
            "--no-refresh",
        ])
