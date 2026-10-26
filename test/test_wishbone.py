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

from test.common import DRAMMemory, MemoryTestDataMixin, timeout_generator


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
        run_simulation(dut, generators)
        self.assertEqual(dut.mem.mem, mem_expected)

    def wishbone_burst_readback_test(self, base_address=0):
        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativePort("both", address_width=30, data_width=128)
                self.wb   = wishbone.Interface(adr_width=30, data_width=32)
                self.submodules += LiteDRAMWishbone2Native(
                    wishbone     = self.wb,
                    port         = self.port,
                    base_address = base_address)
                self.mem = DRAMMemory(self.port.data_width, 8)
                self.native_read_cmds  = 0
                self.native_write_cmds = 0

        def wishbone_burst_write(wb, base, values):
            yield wb.cyc.eq(1)
            yield wb.stb.eq(1)
            yield wb.we.eq(1)
            yield wb.sel.eq(2**len(wb.sel) - 1)
            yield wb.bte.eq(0)

            for i, data in enumerate(values):
                last = i == (len(values) - 1)
                yield wb.adr.eq(base + i)
                yield wb.dat_w.eq(data)
                yield wb.cti.eq(
                    wishbone.CTI_BURST_END if last else wishbone.CTI_BURST_INCREMENTING)
                yield
                while (yield wb.ack) == 0:
                    yield

            yield wb.cyc.eq(0)
            yield wb.stb.eq(0)
            yield wb.we.eq(0)
            yield wb.cti.eq(wishbone.CTI_BURST_NONE)
            yield

        def wishbone_burst_read(wb, base, length):
            data = []
            yield wb.cyc.eq(1)
            yield wb.stb.eq(1)
            yield wb.we.eq(0)
            yield wb.sel.eq(2**len(wb.sel) - 1)
            yield wb.bte.eq(0)

            for i in range(length):
                last = i == (length - 1)
                yield wb.adr.eq(base + i)
                yield wb.cti.eq(
                    wishbone.CTI_BURST_END if last else wishbone.CTI_BURST_INCREMENTING)
                yield
                while (yield wb.ack) == 0:
                    yield
                data.append((yield wb.dat_r))

            yield wb.cyc.eq(0)
            yield wb.stb.eq(0)
            yield wb.cti.eq(wishbone.CTI_BURST_NONE)
            yield
            return data

        @passive
        def cmd_monitor(dut):
            while True:
                yield
                if (yield dut.port.cmd.valid) and (yield dut.port.cmd.ready):
                    if (yield dut.port.cmd.we):
                        dut.native_write_cmds += 1
                    else:
                        dut.native_read_cmds += 1

        values   = [0x01234567, 0x89abcdef, 0x0badcafe, 0x55aa33cc]
        readback = []

        wishbone_base = base_address//(32//8)

        def main_generator(dut):
            yield from wishbone_burst_write(dut.wb, wishbone_base, values)
            for _ in range(16):
                yield
            readback[:] = (yield from wishbone_burst_read(dut.wb, wishbone_base, len(values)))

        dut = DUT()
        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
            cmd_monitor(dut),
            timeout_generator(1000),
        ]
        run_simulation(dut, generators)
        self.assertEqual(readback, values)
        self.assertEqual(dut.native_write_cmds, 1)
        self.assertEqual(dut.native_read_cmds, 1)

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

    def wishbone_write_data_hold_test(self, wb, port, abort):
        # Once the write command is accepted, the controller pulls the write data: the bridge must
        # keep it valid, with the data presented along with the command, even if the master drops
        # stb (or aborts the cycle) and changes its data before the handshake, and must then be
        # able to serve the next transactions.
        class DUT(Module):
            def __init__(self):
                self.port = port
                self.wb   = wb
                self.submodules += LiteDRAMWishbone2Native(self.wb, self.port)
                self.mem  = DRAMMemory(port.data_width, 16)

        def main_generator(dut):
            mask = 2**len(dut.wb.dat_w) - 1
            data = 0x0123456789abcdef & mask
            yield dut.wb.cyc.eq(1)
            yield dut.wb.stb.eq(1)
            yield dut.wb.we.eq(1)
            yield dut.wb.sel.eq(2**len(dut.wb.sel) - 1)
            yield dut.wb.adr.eq(1)
            yield dut.wb.dat_w.eq(data)
            yield
            while not ((yield dut.port.cmd.valid) and (yield dut.port.cmd.ready)):
                yield
            # The command is accepted: drop stb (and cyc when aborting) and change the data before
            # the write data handshake.
            yield dut.wb.stb.eq(0)
            yield dut.wb.cyc.eq(0 if abort else 1)
            yield dut.wb.dat_w.eq(~data & mask)
            yield dut.wb.sel.eq(0)
            acks = 0
            for _ in range(32):
                yield
                acks += (yield dut.wb.ack)
            yield dut.wb.cyc.eq(0)
            yield
            # An aborted cycle gets no ack, a held one gets exactly one.
            self.assertEqual(acks, 0 if abort else 1)
            # The bridge is idle again and wrote the latched data (not the changed one).
            self.assertEqual((yield from dut.wb.read(1)), data)
            yield from dut.wb.write(2, ~data & mask)
            self.assertEqual((yield from dut.wb.read(2)), ~data & mask)

        dut = DUT()
        run_simulation(dut, [
            main_generator(dut),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
            timeout_generator(1000),
        ])

    def test_wishbone_write_data_hold_32bit(self):
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_write_data_hold_test(wb, port, abort=False)

    def test_wishbone_write_data_hold_32bit_abort(self):
        wb   = wishbone.Interface(adr_width=30, data_width=32)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_write_data_hold_test(wb, port, abort=True)

    def test_wishbone_write_data_hold_64bit_to_32bit(self):
        # Through the native port DownConverter.
        wb   = wishbone.Interface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_write_data_hold_test(wb, port, abort=False)

    def test_wishbone_write_data_hold_64bit_to_32bit_abort(self):
        wb   = wishbone.Interface(adr_width=30, data_width=64)
        port = LiteDRAMNativePort("both", address_width=30, data_width=32)
        self.wishbone_write_data_hold_test(wb, port, abort=True)

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

    def test_wishbone_incrementing_burst_32bit_to_128bit(self):
        self.wishbone_burst_readback_test()

    def test_wishbone_incrementing_burst_32bit_to_128bit_base_address(self):
        self.wishbone_burst_readback_test(base_address=0x10000000)

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
