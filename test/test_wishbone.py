#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import random
import unittest

from migen import *
from litex.gen.sim import run_simulation
from litex.soc.interconnect import wishbone

from litedram.frontend.wishbone import LiteDRAMWishbone2Native, LiteDRAMNative2Wishbone
from litedram.frontend.wishbone import LiteDRAMWishbonePipelined2Native
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


class PipelinedNativePortModel:
    """Native port model with several commands in flight.

    Accepts commands whenever cmd.ready is high (random stalls with cmd_ready_random %) and
    completes them in order `latency` cycles later: a one-cycle wdata.ready pulse for writes, with
    the data sampled on that cycle whatever wdata.valid is (as the controller does), a one-cycle
    rdata.valid pulse for reads.
    """
    def __init__(self, port, mem, latency=4, cmd_ready_random=0):
        self.port             = port
        self.mem              = mem
        self.latency          = latency
        self.cmd_ready_random = cmd_ready_random

    @passive
    def handler(self):
        prng       = random.Random(42)
        pending    = []
        completing = None
        cycle      = 0
        while True:
            # Handshakes of the current cycle.
            if completing is not None:
                self.mem._write(completing, (yield self.port.wdata.data), (yield self.port.wdata.we))
                completing = None
            if (yield self.port.cmd.valid) and (yield self.port.cmd.ready):
                pending.append((cycle + self.latency, (yield self.port.cmd.we), (yield self.port.cmd.addr)))
            # Drive the next cycle.
            yield self.port.wdata.ready.eq(0)
            yield self.port.rdata.valid.eq(0)
            if pending and pending[0][0] <= cycle:
                _, we, addr = pending.pop(0)
                if we:
                    yield self.port.wdata.ready.eq(1)
                    completing = addr
                else:
                    yield self.port.rdata.valid.eq(1)
                    yield self.port.rdata.data.eq(self.mem._read(addr))
            yield self.port.cmd.ready.eq(prng.randrange(100) >= self.cmd_ready_random)
            yield
            cycle += 1


class TestWishbonePipelined(unittest.TestCase):
    def pipelined_master(self, wb, stall, ops, acks, stats, abort_after=None):
        # Wishbone B4 pipelined master: presents the beats of ops [(we, adr, dat_w), ...] back to
        # back (holding a beat while stall is high), collects the acks (dat_r for reads) in acks and
        # the maximum number of transfers in flight in stats. With abort_after, drops cyc once that
        # many beats have been accepted.
        yield wb.cyc.eq(1)
        yield wb.sel.eq(2**len(wb.sel) - 1)
        yield wb.stb.eq(1)
        yield wb.we.eq(ops[0][0])
        yield wb.adr.eq(ops[0][1])
        yield wb.dat_w.eq(ops[0][2])
        yield
        i           = 0
        outstanding = 0
        stats["max_outstanding"] = 0
        for _ in range(2000):
            if (yield wb.ack):
                acks.append((yield wb.dat_r))
                outstanding -= 1
            if i < len(ops) and (yield wb.stb) and not (yield stall):
                i           += 1
                outstanding += 1
                stats["max_outstanding"] = max(stats["max_outstanding"], outstanding)
                if abort_after is not None and i == abort_after:
                    yield wb.stb.eq(0)
                    yield wb.cyc.eq(0)
                    yield
                    return
                if i < len(ops):
                    yield wb.we.eq(ops[i][0])
                    yield wb.adr.eq(ops[i][1])
                    yield wb.dat_w.eq(ops[i][2])
                else:
                    yield wb.stb.eq(0)
            if len(acks) == len(ops):
                break
            yield
        yield wb.cyc.eq(0)
        yield

    def pipelined_dut(self, depth=8):
        class DUT(Module):
            def __init__(self):
                self.wb   = wishbone.Interface(adr_width=30, data_width=32)
                self.port = LiteDRAMNativePort("both", address_width=30, data_width=32)
                self.bridge = LiteDRAMWishbonePipelined2Native(self.wb, self.port, depth=depth)
                self.submodules += self.bridge
                self.mem  = DRAMMemory(32, 32)
        return DUT()

    def pipelined_test(self, latency, cmd_ready_random, depth=8, nops=8):
        dut     = self.pipelined_dut(depth)
        pattern = [seed_to_data(i, nbits=32) for i in range(nops)]
        ops     = [(1, i, pattern[i]) for i in range(nops)] + [(0, i, 0) for i in range(nops)]
        acks, stats = [], {}
        model = PipelinedNativePortModel(dut.port, dut.mem, latency=latency, cmd_ready_random=cmd_ready_random)
        run_simulation(dut, [
            self.pipelined_master(dut.wb, dut.bridge.stall, ops, acks, stats),
            model.handler(),
            timeout_generator(3000),
        ])
        # One ack per transfer, in order, the reads returning the written pattern.
        self.assertEqual(len(acks), 2*nops)
        self.assertEqual(acks[nops:], pattern)
        self.assertEqual(dut.mem.mem[:nops], pattern)
        return stats

    def test_wishbone_pipelined_back_to_back(self):
        # With an immediately ready controller, several transfers are in flight (no wait for ack).
        stats = self.pipelined_test(latency=4, cmd_ready_random=0)
        self.assertGreaterEqual(stats["max_outstanding"], 2)

    def test_wishbone_pipelined_random_stalls(self):
        # Random cmd.ready stalls: stall is honored and the acks stay in order.
        self.pipelined_test(latency=6, cmd_ready_random=50)

    def test_wishbone_pipelined_depth(self):
        # A slow controller: no more than depth transfers in flight, then stall.
        stats = self.pipelined_test(latency=40, cmd_ready_random=0, depth=4, nops=8)
        self.assertEqual(stats["max_outstanding"], 4)

    def test_wishbone_pipelined_sequential_controller(self):
        # The DRAMMemory handlers (one command at a time, cmd.ready after cmd.valid): stall holds
        # the master until the controller takes the command.
        dut     = self.pipelined_dut()
        pattern = [seed_to_data(i, nbits=32) for i in range(8)]
        ops     = [(1, i, pattern[i]) for i in range(8)] + [(0, i, 0) for i in range(8)]
        acks, stats = [], {}
        run_simulation(dut, [
            self.pipelined_master(dut.wb, dut.bridge.stall, ops, acks, stats),
            dut.mem.write_handler(dut.port),
            dut.mem.read_handler(dut.port),
            timeout_generator(3000),
        ])
        self.assertEqual(len(acks), 16)
        self.assertEqual(acks[8:], pattern)

    def test_wishbone_pipelined_abort(self):
        # cyc dropped with 4 writes in flight: no ack for them, the bridge drains them and serves
        # the next transaction (whose read sees the writes, the controller had accepted them).
        dut   = self.pipelined_dut()
        model = PipelinedNativePortModel(dut.port, dut.mem, latency=8)
        pattern = [seed_to_data(i, nbits=32) for i in range(4)]
        acks1, acks2, stats = [], [], {}

        def main_generator():
            yield from self.pipelined_master(dut.wb, dut.bridge.stall, [(1, i, pattern[i]) for i in range(4)], acks1, stats, abort_after=4)
            for _ in range(32):
                acks1.append((yield dut.wb.ack)) if (yield dut.wb.ack) else None
                yield
            yield from self.pipelined_master(dut.wb, dut.bridge.stall, [(1, 4, 0xcafe), (0, 1, 0), (0, 4, 0)], acks2, stats)

        run_simulation(dut, [main_generator(), model.handler(), timeout_generator(3000)])
        self.assertEqual(acks1, [])
        self.assertEqual(acks2, [0, pattern[1], 0xcafe])
