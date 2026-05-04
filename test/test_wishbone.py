#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from litex.gen.sim import run_simulation
from litex.soc.interconnect import wishbone

from litedram.frontend.wishbone import LiteDRAMWishbone2Native
from litedram.common import LiteDRAMNativePort

from test.common import DRAMMemory, MemoryTestDataMixin


class TestWishbone(MemoryTestDataMixin, unittest.TestCase):
    def wishbone_readback_test(self, pattern, mem_expected, wishbone, port, base_address=0):
        class DUT(Module):
            def __init__(self):
                self.port = port
                self.wb   = wishbone
                self.submodules += LiteDRAMWishbone2Native(
                    wishbone     = self.wb,
                    port         = self.port,
                    base_address = base_address)
                self.mem = DRAMMemory(port.data_width, len(mem_expected))

        def main_generator(dut):
            for adr, data in pattern:
                yield from dut.wb.write(adr, data)
                data_r = (yield from dut.wb.read(adr))
                self.assertEqual(data_r, data)

        dut = DUT()
        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
        ]
        run_simulation(dut, generators, vcd_name='sim.vcd')
        self.assertEqual(dut.mem.mem, mem_expected)

    def wishbone_burst_read_test(self, length=8, latency=8, wishbone_data_width=32, native_data_width=32):
        ratio          = wishbone_data_width//native_data_width
        native_length  = length*ratio
        native_mask    = 2**native_data_width - 1

        def expected_data(index):
            data = 0
            for n in range(ratio):
                data |= ((index*ratio + n) & native_mask) << (n*native_data_width)
            return data

        class NativeReadMemory(Module):
            def __init__(self, port):
                self.accept_count = Signal(8)
                self.accepted     = [Signal.like(port.cmd.addr) for _ in range(native_length)]

                valid_pipe = Signal(latency)
                data_pipe  = [Signal.like(port.rdata.data) for _ in range(latency)]

                cmd_accept = Signal()
                self.comb += [
                    port.cmd.ready.eq(1),
                    cmd_accept.eq(port.cmd.valid & port.cmd.ready & ~port.cmd.we),
                    port.rdata.valid.eq(valid_pipe[-1]),
                    port.rdata.data.eq(data_pipe[-1]),
                ]

                cases = {}
                for i in range(native_length):
                    cases[i] = self.accepted[i].eq(port.cmd.addr)

                self.sync += [
                    valid_pipe.eq(Cat(cmd_accept, valid_pipe[:-1])),
                    data_pipe[0].eq(port.cmd.addr),
                    If(cmd_accept,
                        Case(self.accept_count, cases),
                        self.accept_count.eq(self.accept_count + 1),
                    )
                ]
                for i in range(1, latency):
                    self.sync += data_pipe[i].eq(data_pipe[i - 1])

        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativePort("both", address_width=30, data_width=native_data_width)
                self.wb   = wishbone.Interface(adr_width=30, data_width=wishbone_data_width, bursting=True)
                self.submodules += LiteDRAMWishbone2Native(
                    wishbone = self.wb,
                    port     = self.port)
                self.submodules.mem = NativeReadMemory(self.port)

        accepted = []

        def main_generator(dut):
            yield dut.wb.cyc.eq(1)
            yield dut.wb.stb.eq(1)
            yield dut.wb.sel.eq(0xf)
            yield dut.wb.adr.eq(0)
            yield dut.wb.cti.eq(wishbone.CTI_BURST_INCREMENTING)

            for _ in range(latency + ratio + 5):
                if (yield dut.wb.ack) or ((yield dut.mem.accept_count) > ratio):
                    break
                yield
            self.assertEqual((yield dut.wb.ack), 0)
            self.assertGreater((yield dut.mem.accept_count), ratio)

            for i in range(length):
                yield dut.wb.adr.eq(i)
                yield dut.wb.cti.eq(
                    wishbone.CTI_BURST_INCREMENTING if i != (length - 1) else wishbone.CTI_BURST_END)
                while (yield dut.wb.ack) == 0:
                    yield
                accepted_now = []
                for signal in dut.mem.accepted:
                    accepted_now.append((yield signal))
                self.assertEqual((yield dut.wb.dat_r), expected_data(i),
                    (i, (yield dut.mem.accept_count), accepted_now))
                yield

            yield dut.wb.cyc.eq(0)
            yield dut.wb.stb.eq(0)
            yield dut.wb.cti.eq(wishbone.CTI_BURST_NONE)
            for signal in dut.mem.accepted:
                accepted.append((yield signal))

        dut = DUT()
        run_simulation(dut, [main_generator(dut)], vcd_name='sim.vcd')
        self.assertEqual(accepted, list(range(native_length)))

    def test_wishbone_32bit_burst_read(self):
        self.wishbone_burst_read_test()

    def test_wishbone_128bit_to_32bit_burst_read(self):
        self.wishbone_burst_read_test(wishbone_data_width=128, native_data_width=32)

    def test_wishbone_burst_read_prefetch_valid_stays_asserted_when_not_ready(self):
        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativePort("both", address_width=30, data_width=32)
                self.wb   = wishbone.Interface(adr_width=30, data_width=32, bursting=True)
                self.submodules += LiteDRAMWishbone2Native(
                    wishbone = self.wb,
                    port     = self.port)

        def main_generator(dut):
            yield dut.wb.cyc.eq(1)
            yield dut.wb.stb.eq(1)
            yield dut.wb.sel.eq(0xf)
            yield dut.wb.adr.eq(0)
            yield dut.wb.cti.eq(wishbone.CTI_BURST_INCREMENTING)
            yield dut.port.cmd.ready.eq(1)
            yield
            self.assertEqual((yield dut.port.cmd.valid), 1)

            yield dut.port.cmd.ready.eq(0)
            yield
            self.assertEqual((yield dut.port.cmd.valid), 1)
            self.assertEqual((yield dut.port.cmd.addr), 1)

        dut = DUT()
        run_simulation(dut, [main_generator(dut)])

    def test_wishbone_8bit(self):
        # Verify Wishbone with 8-bit data width.
        data = self.pattern_test_data["8bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=8)
        port = LiteDRAMNativePort("both", address_width=30, data_width=8)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit(self):
        # Verify Wishbone with 32-bit data width.
        data = self.pattern_test_data["32bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_64bit(self):
        # Verify Wishbone with 64-bit data width.
        data = self.pattern_test_data["64bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=64)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_64bit_to_32bit(self):
        # Verify Wishbone with 64-bit data width down-converted to 32-bit data width.
        data = self.pattern_test_data["64bit_to_32bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit_to_8bit(self):
        # Verify Wishbone with 32-bit data width down-converted to 8-bit data width.
        data = self.pattern_test_data["32bit_to_8bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=8)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_8bit_to_32bit(self):
        # Verify Wishbone with 8-bit data width up-converted to 32-bit data width.
        data = self.pattern_test_data["8bit_to_32bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=8)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit_to_64bit(self):
        # Verify Wishbone with 32-bit data width up-converted to 64-bit data width.
        data = self.pattern_test_data["32bit_to_64bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=64)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit_to_128bit(self):
        # Verify Wishbone with 32-bit data width up-converted to 128-bit data width.
        data = self.pattern_test_data["32bit_to_128bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=128)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit_to_256bit(self):
        # Verify Wishbone with 32-bit data width up-converted to 128-bit data width.
        data = self.pattern_test_data["32bit_to_256bit"]
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=256)
        self.wishbone_readback_test(data["pattern"], data["expected"], wb, port)

    def test_wishbone_32bit_base_address(self):
        # Verify Wishbone with 32-bit data width and non-zero base address.
        data   = self.pattern_test_data["32bit"]
        wb     = wishbone.Interface(adr_width=30, data_width=32)
        port   = LiteDRAMNativePort("both", address_width=30, data_width=32)
        origin = 0x10000000
        # add offset (in data words)
        pattern = [(adr + origin//(32//8), data) for adr, data in data["pattern"]]
        self.wishbone_readback_test(pattern, data["expected"], wb, port, base_address=origin)

    def test_wishbone_64bit_to_32bit_base_address(self):
        # Verify Wishbone with 64-bit data width down-converted to 32-bit data width and non-zero base address.
        data    = self.pattern_test_data["64bit_to_32bit"]
        wb      = wishbone.Interface(adr_width=30, data_width=64)
        port    = LiteDRAMNativePort("both", address_width=30, data_width=32)
        origin  = 0x10000000
        pattern = [(adr + origin//(64//8), data) for adr, data in data["pattern"]]
        self.wishbone_readback_test(pattern, data["expected"], wb, port, base_address=origin)

    def test_wishbone_32bit_to_8bit_base_address(self):
        # Verify Wishbone with 32-bit data width down-converted to 8-bit data width and non-zero base address.
        data    = self.pattern_test_data["32bit_to_8bit"]
        wb      = wishbone.Interface(adr_width=30, data_width=32)
        port    = LiteDRAMNativePort("both", address_width=30, data_width=8)
        origin  = 0x10000000
        pattern = [(adr + origin//(32//8), data) for adr, data in data["pattern"]]
        self.wishbone_readback_test(pattern, data["expected"], wb, port, base_address=origin)
