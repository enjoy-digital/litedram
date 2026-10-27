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

from litedram.frontend.wishbone import LiteDRAMWishbone2Native, LiteDRAMNative2Wishbone
from litedram.common import LiteDRAMNativePort

from test.common import DRAMMemory, MemoryTestDataMixin, NativePortDriver, timeout_generator
from test.common import seed_to_data


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


# LiteDRAMNative2Wishbone --------------------------------------------------------------------------

class WishboneSlaveModel:
    """Generator-based Wishbone Classic slave (word or byte addressing) with a configurable
    number of wait states before each ack. Keeps its memory (words from base_address) in a dict
    and records every access as (we, adr, sel, dat_w) at the cycle of the ack."""
    def __init__(self, testcase, wb, wait_states=0, init=None, base_address=0):
        self.testcase     = testcase
        self.wb           = wb
        self.wait_states  = wait_states
        self.data_width   = len(wb.dat_w)
        self.base_address = base_address
        self.mem          = {} if init is None else dict(enumerate(init))
        self.accesses     = []

    def word_address(self, adr):
        nbytes = self.data_width//8
        if self.wb.addressing == "byte":
            return (adr - self.base_address)//nbytes
        return adr - self.base_address//nbytes

    def request(self):
        return (
            (yield self.wb.we),
            (yield self.wb.adr),
            (yield self.wb.sel),
            (yield self.wb.dat_w),
        )

    @passive
    def handler(self):
        while True:
            while not ((yield self.wb.cyc) and (yield self.wb.stb)):
                yield
            request = (yield from self.request())
            # Wait states: the master must hold the request until the ack.
            for _ in range(self.wait_states):
                yield
                self.testcase.assertEqual(((yield self.wb.cyc), (yield self.wb.stb)), (1, 1))
                self.testcase.assertEqual((yield from self.request()), request)
            we, adr, sel, dat_w = request
            word = self.word_address(adr)
            if we:
                mask = 0
                for i in range(self.data_width//8):
                    if sel & (1 << i):
                        mask |= 0xff << (8*i)
                self.mem[word] = (dat_w & mask) | (self.mem.get(word, 0) & ~mask)
            else:
                yield self.wb.dat_r.eq(self.mem.get(word, 0))
            yield self.wb.ack.eq(1)
            self.accesses.append(request)
            yield
            # Ack is a single cycle pulse and the master must have released the request.
            yield self.wb.ack.eq(0)
            yield self.wb.dat_r.eq(0)
            yield
            self.testcase.assertEqual(((yield self.wb.cyc), (yield self.wb.stb)), (0, 0))


class TestNative2Wishbone(unittest.TestCase):
    depth = 16

    def native2wishbone_test(self, data_width, main, addressing="word", base_address=0,
                             wait_states=None, init=None):
        """Drive a LiteDRAMNativePort through LiteDRAMNative2Wishbone against a Wishbone slave:
        a wishbone.SRAM (wait_states=None) or a WishboneSlaveModel with wait states."""
        depth    = self.depth
        testcase = self

        class DUT(Module):
            def __init__(self):
                self.port = LiteDRAMNativePort("both", address_width=30, data_width=data_width)
                self.wb   = wishbone.Interface(adr_width=30, data_width=data_width, addressing=addressing)
                if wait_states is None:
                    self.sram = wishbone.SRAM(depth*data_width//8, init=init, bus=self.wb)
                    self.submodules += self.sram
                else:
                    self.slave = WishboneSlaveModel(testcase, self.wb, wait_states, init, base_address)
                self.submodules += LiteDRAMNative2Wishbone(
                    port         = self.port,
                    wishbone     = self.wb,
                    base_address = base_address)
                # Handshakes seen on the Wishbone bus and on the Native port.
                self.acks   = 0
                self.writes = 0
                self.reads  = 0

        @passive
        def monitor(dut):
            while True:
                dut.acks   += (yield dut.wb.cyc) & (yield dut.wb.stb) & (yield dut.wb.ack)
                dut.writes += (yield dut.port.wdata.valid) & (yield dut.port.wdata.ready)
                dut.reads  += (yield dut.port.rdata.valid) & (yield dut.port.rdata.ready)
                yield

        dut    = DUT()
        driver = NativePortDriver(dut.port)
        generators = [
            main(dut, driver),
            *driver.generators(),
            monitor(dut),
            timeout_generator(4000),
        ]
        if wait_states is not None:
            generators.append(dut.slave.handler())
        run_simulation(dut, generators)
        return dut, driver

    @staticmethod
    def byte_mask(we, data_width):
        mask = 0
        for i in range(data_width//8):
            if we & (1 << i):
                mask |= 0xff << (8*i)
        return mask

    def native2wishbone_sram_test(self, data_width):
        depth = self.depth
        mask  = 2**data_width - 1
        init  = [seed_to_data(i, nbits=data_width) for i in range(depth)]
        mem   = list(init)
        count = {"writes": 0, "reads": 0}

        def main(dut, driver):
            # Reads return the initial content.
            for adr in range(depth):
                self.assertEqual((yield from driver.read(adr)), mem[adr], msg=f"read {adr}")
                count["reads"] += 1

            # Full writes (all byte enables) are visible to the next reads.
            for adr in [0, 5, 2, depth - 1]:
                data = seed_to_data(0x100 + adr, nbits=data_width)
                mem[adr] = data
                yield from driver.write(adr, data)
                self.assertEqual((yield from driver.read(adr)), data, msg=f"write {adr}")
                count["writes"] += 1
                count["reads"]  += 1

            # Partial writes: only the enabled bytes are updated (sel = native byte enables).
            for adr, we in [(3, 0b0101), (4, 0b1000), (6, 0b0001), (7, 0b0110)]:
                data  = (~mem[adr]) & mask
                bmask = self.byte_mask(we, data_width)
                yield from driver.write(adr, data, we=we)
                mem[adr] = (data & bmask) | (mem[adr] & ~bmask)
                self.assertEqual((yield from driver.read(adr)), mem[adr], msg=f"partial write {adr}")
                count["writes"] += 1
                count["reads"]  += 1

            # Back-to-back commands: the bridge takes one command at a time and keeps the data
            # order (writes with the data presented along with the command).
            burst = [(8 + i, seed_to_data(0x200 + i, nbits=data_width)) for i in range(4)]
            for adr, data in burst:
                mem[adr] = data
                yield from driver.write(adr, data, wait_data=False, data_with_cmd=True)
                count["writes"] += 1
            n_rdata = len(driver.rdata)
            for adr, _ in burst:
                yield from driver.read(adr, wait_data=False)
                count["reads"] += 1
            yield from driver.wait_all()
            self.assertEqual(driver.rdata[n_rdata:], [data for _, data in burst])

            # The content of the SRAM matches.
            for adr in range(depth):
                self.assertEqual((yield dut.sram.mem[adr]), mem[adr], msg=f"mem {adr}")

        dut, driver = self.native2wishbone_test(data_width, main, init=init)
        # One Wishbone ack per native command, one write data / read data handshake per command.
        self.assertEqual(dut.writes, count["writes"])
        self.assertEqual(dut.reads,  count["reads"])
        self.assertEqual(dut.acks,   count["writes"] + count["reads"])

    def test_native2wishbone_sram_32bit(self):
        # Verify Native -> Wishbone with 32-bit data width against a Wishbone SRAM.
        self.native2wishbone_sram_test(data_width=32)

    def test_native2wishbone_sram_64bit(self):
        # Verify Native -> Wishbone with 64-bit data width against a Wishbone SRAM.
        self.native2wishbone_sram_test(data_width=64)

    def native2wishbone_wait_states_test(self, data_width, wait_states, addressing, base_address):
        depth = self.depth
        init  = [seed_to_data(i, nbits=data_width) for i in range(depth)]
        mem   = list(init)
        full  = 2**(data_width//8) - 1
        if addressing == "byte":
            wb_offset = base_address
            wb_stride = data_width//8
        else:
            wb_offset = base_address//(data_width//8)
            wb_stride = 1
        expected = []

        def main(dut, driver):
            for adr in [0, 3, depth - 1]:
                self.assertEqual((yield from driver.read(adr)), mem[adr])
                expected.append((0, wb_offset + wb_stride*adr, full))
            for adr, we in [(1, full), (2, 0b0011), (depth - 1, 0b0100)]:
                data  = seed_to_data(0x300 + adr, nbits=data_width)
                bmask = self.byte_mask(we, data_width)
                yield from driver.write(adr, data, we=we)
                expected.append((1, wb_offset + wb_stride*adr, we, data))
                mem[adr] = (data & bmask) | (mem[adr] & ~bmask)
                self.assertEqual((yield from driver.read(adr)), mem[adr])
                expected.append((0, wb_offset + wb_stride*adr, full))

        dut, driver = self.native2wishbone_test(data_width, main,
            addressing   = addressing,
            base_address = base_address,
            wait_states  = wait_states,
            init         = init)
        # Each command is seen once by the slave, at the right address, with the right byte
        # enables (all set for reads) and data.
        accesses = [(we, adr, sel, dat_w) if we else (we, adr, sel)
            for (we, adr, sel, dat_w) in dut.slave.accesses]
        self.assertEqual(accesses, expected)
        self.assertEqual(dut.acks, len(expected))
        self.assertEqual(dut.writes, len([e for e in expected if e[0]]))
        self.assertEqual(dut.reads,  len([e for e in expected if not e[0]]))
        for adr in range(depth):
            self.assertEqual(dut.slave.mem.get(adr, 0), mem[adr])

    def test_native2wishbone_wait_states(self):
        # Verify Native -> Wishbone with a slave inserting wait states before each ack.
        for wait_states in [1, 3]:
            with self.subTest(wait_states=wait_states):
                self.native2wishbone_wait_states_test(32, wait_states, "word", base_address=0)

    def test_native2wishbone_base_address(self):
        # Verify Native -> Wishbone with a non-zero base address (word addressing: in words).
        self.native2wishbone_wait_states_test(32, 2, "word", base_address=0x10000000)

    def test_native2wishbone_byte_addressing(self):
        # Verify Native -> Wishbone with a byte-addressed Wishbone bus and a base address.
        for data_width in [32, 64]:
            with self.subTest(data_width=data_width):
                self.native2wishbone_wait_states_test(data_width, 2, "byte", base_address=0x40000000)
