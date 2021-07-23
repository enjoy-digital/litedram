#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import os
import unittest
from collections import defaultdict

from migen import *

from litex.build.sim import gtkwave as gtkw

from litedram.phy.dfi import Interface as DFIInterface, DFIRateConverter
from litedram.phy.utils import Serializer, Deserializer

from test.phy_common import DFISequencer, dfi_reset_values, run_simulation as _run_simulation


def run_simulation(ratio, *args, **kwargs):
    clkdiv = "sys"
    clk = f"sys{ratio}x"
    kwargs["clocks"] = {
        clkdiv: (4*ratio, 4*ratio/2 - 1),
        clk:    (4, 1),
    }
    _run_simulation(*args, **kwargs)


# To debug the tests pass vcd_name="sim.vcd" to the self.run_test call and use `gtkwave sim.gtkw` to view the trace
class TestPHYRateConverter(unittest.TestCase):
    class Dut(Module):
        def __init__(self, ratio, converter_kwargs=None, **dfi_kwargs):
            self.ratio = ratio
            self.dfi_old = DFIInterface(**dfi_kwargs)
            converter_kwargs = converter_kwargs or {}
            self.submodules.converter = DFIRateConverter(self.dfi_old, clkdiv="sys", clk=f"sys{ratio}x",
                ratio=ratio, serdes_reset_cnt=-1, **converter_kwargs)
            self.dfi = self.converter.dfi

    def dfi_latency(self, ratio, reset_n=True):
        latency_clkdiv = Serializer.LATENCY
        latency_clk = ratio * latency_clkdiv
        nop = {p: (dict(reset_n=0) if reset_n else {}) for p in range(4)}  # reset_n will have wrong value until driven
        return [nop] * latency_clk

    def run_test(self, dut, dfi_sys, dfi_expected, dfi_input=None, **kwargs):
        assert callable(dut), "dut must be a callable that returns new Dut instance"
        dfi = DFISequencer(dfi_sys)

        # Add GTKWave savefile for debugging if we are creating a VCD dumpfile (requires pyvcd installed)
        if kwargs.get("vcd_name", False):
            dumpfile = kwargs["vcd_name"]
            savefile = os.path.splitext(dumpfile)[0] + ".gtkw"
            # Create a separate dut just for the purpose of generaing a savefile
            tmp_dut = dut()
            vns = verilog.convert(tmp_dut).ns

            with gtkw.GTKWSave(vns, savefile=savefile, dumpfile=dumpfile, prefix="") as save:
                save.clocks()
                for grp_dfi, grp_name in [(tmp_dut.dfi, "dfi new"), (tmp_dut.dfi_old, "dfi old")]:
                    with save.gtkw.group(grp_name):
                        # each phase in separate group
                        with save.gtkw.group("dfi phaseX", closed=True):
                            for i, phase in enumerate(grp_dfi.phases):
                                save.add(phase, group_name="dfi p{}".format(i), mappers=[
                                    gtkw.dfi_sorter(phases=False),
                                    gtkw.dfi_in_phase_colorer(),
                                ])
                        # only dfi command signals
                        save.add(grp_dfi, group_name="dfi commands", mappers=[
                            gtkw.regex_filter(gtkw.suffixes2re(["cas_n", "ras_n", "we_n"])),
                            gtkw.dfi_sorter(),
                            gtkw.dfi_per_phase_colorer(),
                        ])
                        # only dfi data signals
                        save.add(grp_dfi, group_name="dfi wrdata", mappers=[
                            gtkw.regex_filter(["wrdata$"]),
                            gtkw.dfi_sorter(),
                            gtkw.dfi_per_phase_colorer(),
                        ])
                        save.add(grp_dfi, group_name="dfi wrdata_mask", mappers=[
                            gtkw.regex_filter(gtkw.suffixes2re(["wrdata_mask"])),
                            gtkw.dfi_sorter(),
                            gtkw.dfi_per_phase_colorer(),
                        ])
                        save.add(grp_dfi, group_name="dfi rddata", mappers=[
                            gtkw.regex_filter(gtkw.suffixes2re(["rddata", "p0.*rddata_valid"])),
                            gtkw.dfi_sorter(),
                            gtkw.dfi_per_phase_colorer(),
                        ])

        def checker(dfi):
            fail = False

            history = defaultdict(list)
            reference = defaultdict(list)

            # first cycle has undefined data until DFISequencer drives the signals
            yield

            for i, dfi_phases in enumerate(dfi_expected):
                for phase in range(len(dfi.phases)):
                    values = dfi_reset_values()
                    values.update(dfi_phases.get(phase, {}))
                    for name, ref in values.items():
                        # if name in ["rddata", "rddata_valid"]:
                        #     continue
                        val = (yield getattr(dfi.phases[phase], name))
                        msg = f"Cycle {i}, dfi.p{phase}.{name} = {val} != {ref}"
                        history[name].append(val)
                        reference[name].append(ref)
                        if not fail and val != ref:
                            fail = (val, ref, msg)
                yield

            def split_cycles(hist):
                s = ""
                for i, val in enumerate(hist):
                    s += str(val)
                    if (i + 1) % len(dfi.phases) == 0:
                        s += " "
                return s

            if fail:
                print()
                for sig in history:
                    if len(getattr(dfi.phases[0], sig)) == 1:
                        print(f"{sig:12}: {split_cycles(history[sig])}")
                        print(" "*14 + f"{split_cycles(reference[sig])}")
                self.assertEqual(*fail)

        dut = dut()
        run_simulation(dut.ratio, dut, generators={
            "sys": [dfi.generator(dut.dfi), dfi.reader(dut.dfi)],
            f"sys{dut.ratio}x": [checker(dut.dfi_old), DFISequencer.input_generator(dut.dfi_old, dfi_input or [])],
        }, **kwargs)
        dfi.assert_ok(self)

    def test_dfi_rate_converter_phase_0(self):
        read       = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b111, address=0b110101)
        dfi_sys = [
            {0: read},
        ]
        dfi_expected = [
            *self.dfi_latency(ratio=2),
            {0: read},
            {},
        ]
        self.run_test(lambda: self.Dut(
            ratio=2,
            addressbits=16,
            bankbits=3,
            nranks=1,
            databits=2*16,
            nphases=4,
        ), dfi_sys, dfi_expected)

    def test_dfi_rate_converter_1_to_2_cmd(self):
        read       = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b111, address=0b110101)
        activate   = dict(cs_n=0, cas_n=1, ras_n=0, we_n=1, bank=0b010, address=0b1110000111100001)
        precharge  = dict(cs_n=0, cas_n=1, ras_n=0, we_n=0, bank=0b111, address=0)
        dfi_sys = [
            {1: activate, 3: read, 6: precharge},
        ]
        dfi_expected = [
            *self.dfi_latency(ratio=2),
            {1: activate, 3: read},
            {2: precharge},
            {}, {},  # 1
        ]
        self.run_test(lambda: self.Dut(
            ratio=2,
            addressbits=16,
            bankbits=3,
            nranks=1,
            databits=2*16,
            nphases=4,
        ), dfi_sys, dfi_expected)

    def test_dfi_rate_converter_1_to_2_write(self):
        write_ap   = dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, bank=0b111, address=0b10000000000, wrdata_en=1)
        data_clkdiv = {
            0: dict(wrdata=0x1111, wrdata_mask=0b00),
            1: dict(wrdata=0x2222, wrdata_mask=0b11),
            2: dict(wrdata=0x3333, wrdata_mask=0b00),
            3: dict(wrdata=0x4444, wrdata_mask=0b11),
            4: dict(wrdata=0x5555, wrdata_mask=0b01),
            5: dict(wrdata=0x6666, wrdata_mask=0b01),
            6: dict(wrdata=0x7777, wrdata_mask=0b10),
            7: dict(wrdata=0x8888, wrdata_mask=0b01),
        }
        data_clk = {
            0: dict(wrdata=0x22221111, wrdata_mask=0b1100),
            1: dict(wrdata=0x44443333, wrdata_mask=0b1100),
            2: dict(wrdata=0x66665555, wrdata_mask=0b0101),
            3: dict(wrdata=0x88887777, wrdata_mask=0b0110),
        }
        dfi_sys = [
            {7: write_ap},
            {},
            data_clkdiv,
        ]
        dfi_expected = [
            *self.dfi_latency(ratio=2),
            {},  # 0
            {3: write_ap},
            {},  # 1
            {},
            data_clk,  # 2 (assuming write latency = 3)
            {},
            {},  # 3
            {},
        ]
        self.run_test(lambda: self.Dut(
            ratio=2,
            addressbits=16,
            bankbits=3,
            nranks=1,
            databits=2*16,
            nphases=4,
        ), dfi_sys, dfi_expected)

    def test_dfi_rate_converter_1_to_2_read(self):
        read = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b111, address=0b110101)
        data_clkdiv = {
            0: dict(rddata=0x1111, rddata_valid=1),
            1: dict(rddata=0x2222),
            2: dict(rddata=0x3333),
            3: dict(rddata=0x4444),
            4: dict(rddata=0x5555),
            5: dict(rddata=0x6666),
            6: dict(rddata=0x7777),
            7: dict(rddata=0x8888),
        }
        data_clk = {
            0: dict(rddata=0x22221111, rddata_valid=1),
            1: dict(rddata=0x44443333),
            2: dict(rddata=0x66665555),
            3: dict(rddata=0x88887777),
        }
        des_latency = [{}] * Deserializer.LATENCY
        dfi_sys = [
            {7: read}, # 0
            {},
            {},  # 2 (data_clk)
            *des_latency,
            data_clkdiv,
        ]
        dfi_expected = [  # sys2x
            *self.dfi_latency(ratio=2),
            {},  # 0
            {3: read},
        ]
        dfi_input = [  # sys2x
            *self.dfi_latency(ratio=2, reset_n=False),
            {}, # 0
            {},  # read
            {}, # 1
            {},
            data_clk,  # 2 (assumig read latency = 3)
        ]
        self.run_test(lambda: self.Dut(
            ratio=2,
            addressbits=16,
            bankbits=3,
            nranks=1,
            databits=2*16,
            nphases=4,
        ), dfi_sys, dfi_expected, dfi_input=dfi_input)

    def test_dfi_rate_converter_1_to_4_cmd(self):
        read       = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b111, address=0b110101)
        activate   = dict(cs_n=0, cas_n=1, ras_n=0, we_n=1, bank=0b010, address=0b1110000111100001)
        precharge  = dict(cs_n=0, cas_n=1, ras_n=0, we_n=0, bank=0b111, address=0)
        dfi_sys = [
            {1: activate, 3: read, 6: precharge},
        ]
        dfi_expected = [
            *self.dfi_latency(ratio=4),
            {1: activate}, # 0
            {1: read},
            {},
            {0: precharge},
            {}, {}, {}, {}, # 1
        ]
        self.run_test(lambda: self.Dut(
            ratio=4,
            addressbits=16,
            bankbits=3,
            nranks=1,
            databits=2*16,
            nphases=2,
        ), dfi_sys, dfi_expected)

    def test_dfi_rate_converter_1_to_4_write(self):
        write_ap   = dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, bank=0b111, address=0b10000000000, wrdata_en=1)
        data_clkdiv = {
            0: dict(wrdata=0x11),
            1: dict(wrdata=0x22),
            2: dict(wrdata=0x33),
            3: dict(wrdata=0x44),
            4: dict(wrdata=0x55),
            5: dict(wrdata=0x66),
            6: dict(wrdata=0x77),
            7: dict(wrdata=0x88),
        }
        data_clk = {
            0: dict(wrdata=0x44332211),
            1: dict(wrdata=0x88776655),
        }
        dfi_sys = [
            {7: write_ap},
            {},
            data_clkdiv,
        ]
        dfi_expected = [
            *self.dfi_latency(ratio=4),
            {}, # 0
            {},
            {},
            {1: write_ap},
            {}, {}, {}, {}, # 1
            data_clk, # 2 (assuming write latency = 5)
            {}, {}, {},
            {}, {}, {}, {}, # 3
        ]
        self.run_test(lambda: self.Dut(
            ratio=4,
            addressbits=16,
            bankbits=3,
            nranks=1,
            databits=2*16,
            nphases=2,
        ), dfi_sys, dfi_expected)

    def test_dfi_rate_converter_1_to_4_read(self):
        read = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b111, address=0b110101)
        data_clkdiv = {
            0: dict(rddata=0x1111, rddata_valid=1),
            1: dict(rddata=0x2222, rddata_valid=1),
            2: dict(rddata=0x3333, rddata_valid=1),
            3: dict(rddata=0x4444, rddata_valid=1),
            4: dict(rddata=0x5555, rddata_valid=1),
            5: dict(rddata=0x6666, rddata_valid=1),
            6: dict(rddata=0x7777, rddata_valid=1),
            7: dict(rddata=0x8888, rddata_valid=1),
        }
        data_clk = {
            0: dict(rddata=0x4444333322221111, rddata_valid=1),
            1: dict(rddata=0x8888777766665555, rddata_valid=1),
        }
        des_latency = [{}] * Deserializer.LATENCY
        dfi_sys = [
            {7: read}, # 0
            {},
            {},  # 2 (data_clk)
            *des_latency,
            data_clkdiv,
        ]
        dfi_expected = [  # sys2x
            *self.dfi_latency(ratio=4),
            {},  # 0
            {},
            {},
            {1: read},
        ]
        dfi_input = [  # sys2x
            *self.dfi_latency(ratio=4, reset_n=False),
            {}, # 0
            {},
            {},
            {},  # read
            {}, {}, {}, {}, # 1
            data_clk,  # 2 (assumig read latency = 5)
        ]
        self.run_test(lambda: self.Dut(
            ratio=4,
            addressbits=16,
            bankbits=3,
            nranks=1,
            databits=2*32,
            nphases=2,
        ), dfi_sys, dfi_expected, dfi_input=dfi_input)

    def test_dfi_rate_converter_1_to_4_write_delayed(self):
        # When write_latency does not aligh with clkdiv boundaries, the write data must be delayed
        write_ap   = dict(cs_n=0, cas_n=0, ras_n=1, we_n=0, bank=0b111, address=0b10000000000, wrdata_en=1)
        data_clkdiv = {
            0: dict(wrdata=0x11),
            1: dict(wrdata=0x22),
            2: dict(wrdata=0x33),
            3: dict(wrdata=0x44),
            4: dict(wrdata=0x55),
            5: dict(wrdata=0x66),
            6: dict(wrdata=0x77),
            7: dict(wrdata=0x88),
        }
        data_clk = {
            0: dict(wrdata=0x44332211),
            1: dict(wrdata=0x88776655),
        }
        for write_latency, sys_latency, write_delay in [(1, 0, 0), (2, 0, 1), (3, 0, 2), (4, 0, 3), (5, 1, 0)]:
            with self.subTest(write_latency=write_latency, sys_latency=sys_latency, write_delay=write_delay):
                sys_latency = [{}] * sys_latency
                write_latency_cycles = [{}] * (write_latency - 1)
                dfi_sys = [
                    {7: write_ap},
                    *sys_latency,
                    data_clkdiv,  # send with sys write_latency=1
                ]
                dfi_expected = [
                    *self.dfi_latency(ratio=4),
                    {}, # 0
                    {},
                    {},
                    {1: write_ap},
                    # 1
                    *write_latency_cycles,
                    data_clk,
                    {}, {}, {}, {},
                ]
                self.run_test(lambda: self.Dut(
                    ratio=4,
                    addressbits=16,
                    bankbits=3,
                    nranks=1,
                    databits=2*16,
                    nphases=2,
                    converter_kwargs=dict(write_delay=write_delay),
                ), dfi_sys, dfi_expected)

    def test_dfi_rate_converter_1_to_4_read_delayed(self):
        # When read_latency does not aligh with clkdiv boundaries, the read data must be delayed
        read = dict(cs_n=0, cas_n=0, ras_n=1, we_n=1, bank=0b111, address=0b110101)
        data_clkdiv = {
            0: dict(rddata=0x1111, rddata_valid=1),  # make sure it rddata_valid on 1 phase is replicated to ratio phases
            1: dict(rddata=0x2222, rddata_valid=1),
            2: dict(rddata=0x3333, rddata_valid=1),
            3: dict(rddata=0x4444, rddata_valid=1),
            4: dict(rddata=0x5555),
            5: dict(rddata=0x6666),
            6: dict(rddata=0x7777),
            7: dict(rddata=0x8888),
        }
        data_clk = {
            0: dict(rddata=0x4444333322221111, rddata_valid=1),
            1: dict(rddata=0x8888777766665555),
        }
        for read_latency, sys_latency, read_delay in [(1, 0, 0), (2, 0, 1), (3, 0, 2), (4, 0, 3), (5, 1, 0)]:
            # read_latency is the PHY's read latency
            # sys_latency is additional latency added at sys clock
            # read_delay is from which cycle at sys4x the data is taken
            with self.subTest(read_latency=read_latency, sys_latency=sys_latency, read_delay=read_delay):
                sys_latency = [{}] * (Deserializer.LATENCY + sys_latency)
                read_latency_cycles = [{}] * (read_latency - 1)
                dfi_sys = [
                    {7: read}, # 0
                    {}, # 1 (read command shows up on dfi_old)
                    *sys_latency,
                    data_clkdiv,
                ]
                dfi_expected = [  # sys2x
                    *self.dfi_latency(ratio=4),
                    {},  # 0
                    {},
                    {},
                    {1: read},
                ]
                dfi_input = [  # sys2x
                    *self.dfi_latency(ratio=4, reset_n=False),
                    {}, # 0
                    {},
                    {},
                    {},  # read
                    # 1
                    *read_latency_cycles,
                    data_clk,
                ]
                self.run_test(lambda: self.Dut(
                    ratio=4,
                    addressbits=16,
                    bankbits=3,
                    nranks=1,
                    databits=2*32,
                    nphases=2,
                    converter_kwargs=dict(read_delay=read_delay),
                ), dfi_sys, dfi_expected, dfi_input=dfi_input)
