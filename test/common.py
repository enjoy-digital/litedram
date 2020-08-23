#
# This file is part of LiteDRAM.
#
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2016 Tim 'mithro' Ansell <mithro@mithis.com>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import os
import random
import itertools
from functools import partial
from operator import or_

from migen import *


def seed_to_data(seed, random=True, nbits=32):
    if nbits == 32:
        if random:
            return (seed * 0x31415979 + 1) & 0xffffffff
        else:
            return seed
    else:
        assert nbits%32 == 0
        data = 0
        for i in range(nbits//32):
            data = data << 32
            data |= seed_to_data(seed*nbits//32 + i, random, 32)
        return data


@passive
def timeout_generator(ticks):
    # raise exception after given timeout effectively stopping simulation
    # because of @passive, simulation can end even if this generator is still running
    for _ in range(ticks):
        yield
    raise TimeoutError("Timeout after %d ticks" % ticks)


class NativePortDriver:
    """Generates sequences for reading/writing to LiteDRAMNativePort

    The write/read versions with wait_data=False are a cheap way to perform
    burst during which the port is being held locked, but this way all the
    data is being lost (would require separate coroutine to handle data).
    """
    def __init__(self, port):
        self.port = port
        self.wdata = []  # fifo, consumed by handler
        self.rdata = []  # stack, never consumed
        self.rdata_expected = 0

    def generators(self):
        return [self.write_data_handler(), self.read_data_handler()]

    def wait_all(self):
        while self.wdata or len(self.rdata) < self.rdata_expected:
            yield

    @passive
    def write_data_handler(self):
        while True:
            if self.wdata:
                # pop the data only after write has been completed
                data, we = self.wdata[0]
                yield self.port.wdata.valid.eq(1)
                yield self.port.wdata.data.eq(data)
                yield self.port.wdata.we.eq(we)
                yield
                while (yield self.port.wdata.ready) == 0:
                    yield
                yield self.port.wdata.valid.eq(0)
                self.wdata.pop(0)
            yield

    @passive
    def read_data_handler(self, latency=0):
        if latency == 0:
            yield self.port.rdata.ready.eq(1)
            while True:
                while (yield self.port.rdata.valid) == 0:
                    yield
                data = (yield self.port.rdata.data)
                yield
                self.rdata.append(data)
        else:
            while True:
                while (yield self.port.rdata.valid) == 0:
                    yield
                data = (yield self.port.rdata.data)
                yield self.port.rdata.ready.eq(1)
                yield
                self.rdata.append(data)
                yield self.port.rdata.ready.eq(0)
                for _ in range(latency):
                    yield

    def read(self, address, first=0, last=0, wait_data=True):
        yield self.port.cmd.valid.eq(1)
        yield self.port.cmd.first.eq(first)
        yield self.port.cmd.last.eq(last)
        yield self.port.cmd.we.eq(0)
        yield self.port.cmd.addr.eq(address)
        yield
        while (yield self.port.cmd.ready) == 0:
            yield
        self.rdata_expected += 1
        yield self.port.cmd.valid.eq(0)
        if wait_data:
            while len(self.rdata) != self.rdata_expected:
                yield
            return self.rdata[-1]

    def write(self, address, data, we=None, first=0, last=0, wait_data=True, data_with_cmd=False):
        if we is None:
            we = 2**self.port.wdata.we.nbits - 1
        yield self.port.cmd.valid.eq(1)
        yield self.port.cmd.first.eq(first)
        yield self.port.cmd.last.eq(last)
        yield self.port.cmd.we.eq(1)
        yield self.port.cmd.addr.eq(address)
        if data_with_cmd:
            self.wdata.append((data, we))
        yield
        while (yield self.port.cmd.ready) == 0:
            yield
        if not data_with_cmd:
            self.wdata.append((data, we))
        yield self.port.cmd.valid.eq(0)
        if wait_data:
            n_wdata = len(self.wdata)
            while len(self.wdata) != n_wdata - 1:
                yield


class CmdRequestRWDriver:
    """Simple driver for Endpoint(cmd_request_rw_layout())"""
    def __init__(self, req, i=0, ep_layout=True, rw_layout=True):
        self.req = req
        self.rw_layout = rw_layout  # if False, omit is_* signals
        self.ep_layout = ep_layout  # if False, omit endpoint signals (valid, etc.)

        # used to distinguish commands
        self.i = self.bank = self.row = self.col = i

    def request(self, char):
        # convert character to matching command invocation
        return {
            "w": self.write,
            "r": self.read,
            "W": partial(self.write, auto_precharge=True),
            "R": partial(self.read, auto_precharge=True),
            "a": self.activate,
            "p": self.precharge,
            "f": self.refresh,
            "_": self.nop,
        }[char]()

    def activate(self):
        yield from self._drive(valid=1, is_cmd=1, ras=1, a=self.row, ba=self.bank)

    def precharge(self, all_banks=False):
        a = 0 if not all_banks else (1 << 10)
        yield from self._drive(valid=1, is_cmd=1, ras=1, we=1, a=a, ba=self.bank)

    def refresh(self):
        yield from self._drive(valid=1, is_cmd=1, cas=1, ras=1, ba=self.bank)

    def write(self, auto_precharge=False):
        assert not (self.col & (1 << 10))
        col = self.col | (1 << 10) if auto_precharge else self.col
        yield from self._drive(valid=1, is_write=1, cas=1, we=1, a=col, ba=self.bank)

    def read(self, auto_precharge=False):
        assert not (self.col & (1 << 10))
        col = self.col | (1 << 10) if auto_precharge else self.col
        yield from self._drive(valid=1, is_read=1, cas=1, a=col, ba=self.bank)

    def nop(self):
        yield from self._drive()

    def _drive(self, **kwargs):
        signals = ["a", "ba", "cas", "ras", "we"]
        if self.rw_layout:
            signals += ["is_cmd", "is_read", "is_write"]
        if self.ep_layout:
            signals += ["valid", "first", "last"]
        for s in signals:
            yield getattr(self.req, s).eq(kwargs.get(s, 0))
        # drive ba even for nop, to be able to distinguish bank machines anyway
        if "ba" not in kwargs:
            yield self.req.ba.eq(self.bank)


class DRAMMemory:
    def __init__(self, width, depth, init=[]):
        self.width = width
        self.depth = depth
        self.mem = []
        for d in init:
            self.mem.append(d)
        for _ in range(depth-len(init)):
            self.mem.append(0)

        # "W" enables write msgs, "R" - read msgs and "1" both
        self._debug = os.environ.get("DRAM_MEM_DEBUG", "0")

    def show_content(self):
        for addr in range(self.depth):
            print("0x{:08x}: 0x{:0{dwidth}x}".format(addr, self.mem[addr], dwidth=self.width//4))

    def _warn(self, address):
        if address > self.depth * self.width:
            print("! adr > 0x{:08x}".format(
                self.depth * self.width))

    def _write(self, address, data, we):
        mask = reduce(or_, [0xff << (8 * bit) for bit in range(self.width//8)
                            if (we & (1 << bit)) != 0], 0)
        data = data & mask
        self.mem[address%self.depth] = data | (self.mem[address%self.depth] & ~mask)
        if self._debug in ["1", "W"]:
            print("W 0x{:08x}: 0x{:0{dwidth}x}".format(address, self.mem[address%self.depth],
                                                       dwidth=self.width//4))
            self._warn(address)

    def _read(self, address):
        if self._debug in ["1", "R"]:
            print("R 0x{:08x}: 0x{:0{dwidth}x}".format(address, self.mem[address%self.depth],
                                                       dwidth=self.width//4))
            self._warn(address)
        return self.mem[address%self.depth]

    @passive
    def read_handler(self, dram_port, rdata_valid_random=0):
        address = 0
        pending = 0
        prng = random.Random(42)
        yield dram_port.cmd.ready.eq(0)
        while True:
            yield dram_port.rdata.valid.eq(0)
            if pending:
                while prng.randrange(100) < rdata_valid_random:
                    yield
                yield dram_port.rdata.valid.eq(1)
                yield dram_port.rdata.data.eq(self._read(address))
                yield
                yield dram_port.rdata.valid.eq(0)
                yield dram_port.rdata.data.eq(0)
                pending = 0
            elif (yield dram_port.cmd.valid):
                pending = not (yield dram_port.cmd.we)
                address = (yield dram_port.cmd.addr)
                if pending:
                    yield dram_port.cmd.ready.eq(1)
                    yield
                    yield dram_port.cmd.ready.eq(0)
            yield

    @passive
    def write_handler(self, dram_port, wdata_ready_random=0):
        address = 0
        pending = 0
        prng = random.Random(42)
        yield dram_port.cmd.ready.eq(0)
        while True:
            yield dram_port.wdata.ready.eq(0)
            if pending:
                while (yield dram_port.wdata.valid) == 0:
                    yield
                while prng.randrange(100) < wdata_ready_random:
                    yield
                yield dram_port.wdata.ready.eq(1)
                yield
                self._write(address, (yield dram_port.wdata.data), (yield dram_port.wdata.we))
                yield dram_port.wdata.ready.eq(0)
                yield
                pending = 0
                yield
            elif (yield dram_port.cmd.valid):
                pending = (yield dram_port.cmd.we)
                address = (yield dram_port.cmd.addr)
                if pending:
                    yield dram_port.cmd.ready.eq(1)
                    yield
                    yield dram_port.cmd.ready.eq(0)
            yield


class MemoryTestDataMixin:
    @property
    def bist_test_data(self):
        data = {
            "8bit": dict(
                base     = 2,
                end      = 2 + 8,  # (end - base) must be pow of 2
                length   = 5,
                #                       2     3     4     5     6     7=2+5
                expected = [0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x00],
            ),
            "32bit": dict(
                base     = 0x04,
                end      = 0x04 + 8,
                length   = 5 * 4,
                expected = [
                    0x00000000,  # 0x00
                    0x00000000,  # 0x04
                    0x00000001,  # 0x08
                    0x00000002,  # 0x0c
                    0x00000003,  # 0x10
                    0x00000004,  # 0x14
                    0x00000000,  # 0x18
                    0x00000000,  # 0x1c
                ],
            ),
            "64bit": dict(
                base     = 0x10,
                end      = 0x10 + 8,
                length   = 5 * 8,
                expected = [
                    0x0000000000000000,  # 0x00
                    0x0000000000000000,  # 0x08
                    0x0000000000000000,  # 0x10
                    0x0000000000000001,  # 0x18
                    0x0000000000000002,  # 0x20
                    0x0000000000000003,  # 0x28
                    0x0000000000000004,  # 0x30
                    0x0000000000000000,  # 0x38
                ],
            ),
            "32bit_masked": dict(
                base     = 0x04,
                end      = 0x04 + 0x04,  # TODO: fix address masking to be consistent
                length   = 6 * 4,
                expected = [  # due to masking
                    0x00000000,  # 0x00
                    0x00000004,  # 0x04
                    0x00000005,  # 0x08
                    0x00000002,  # 0x0c
                    0x00000003,  # 0x10
                    0x00000000,  # 0x14
                    0x00000000,  # 0x18
                    0x00000000,  # 0x1c
                ],
            ),
        }
        data["32bit_long_sequential"] = dict(
            base     = 16,
            end      = 16 + 128,
            length   = 64,
            expected = [0x00000000] * 128
        )
        expected = data["32bit_long_sequential"]["expected"]
        expected[16//4:(16 + 64)//4] = list(range(64//4))
        return data

    @property
    def pattern_test_data(self):
        data = {
            "8bit": dict(
                pattern=[
                    # address, data
                    (0x00, 0xaa),
                    (0x05, 0xbb),
                    (0x02, 0xcc),
                    (0x07, 0xdd),
                ],
                expected=[
                    # data, address
                    0xaa,  # 0x00
                    0x00,  # 0x01
                    0xcc,  # 0x02
                    0x00,  # 0x03
                    0x00,  # 0x04
                    0xbb,  # 0x05
                    0x00,  # 0x06
                    0xdd,  # 0x07
                ],
            ),
            "32bit": dict(
                pattern=[
                    # address, data
                    (0x00, 0xabadcafe),
                    (0x07, 0xbaadf00d),
                    (0x02, 0xcafefeed),
                    (0x01, 0xdeadc0de),
                ],
                expected=[
                    # data, address
                    0xabadcafe,  # 0x00
                    0xdeadc0de,  # 0x04
                    0xcafefeed,  # 0x08
                    0x00000000,  # 0x0c
                    0x00000000,  # 0x10
                    0x00000000,  # 0x14
                    0x00000000,  # 0x18
                    0xbaadf00d,  # 0x1c
                ],
            ),
            "64bit": dict(
                pattern=[
                    # address, data
                    (0x00, 0x0ddf00dbadc0ffee),
                    (0x05, 0xabadcafebaadf00d),
                    (0x02, 0xcafefeedfeedface),
                    (0x07, 0xdeadc0debaadbeef),
                ],
                expected=[
                    # data, address
                    0x0ddf00dbadc0ffee,  # 0x00
                    0x0000000000000000,  # 0x08
                    0xcafefeedfeedface,  # 0x10
                    0x0000000000000000,  # 0x18
                    0x0000000000000000,  # 0x20
                    0xabadcafebaadf00d,  # 0x28
                    0x0000000000000000,  # 0x30
                    0xdeadc0debaadbeef,  # 0x38
                ],
            ),
            "64bit_to_32bit": dict(
                pattern=[
                    # address, data
                    (0x00, 0x0d15ea5e00facade),
                    (0x05, 0xabadcafe8badf00d),
                    (0x01, 0xcafefeedbaadf00d),
                    (0x02, 0xfee1deaddeadc0de),
                ],
                expected=[
                    # data, word, address
                    0x00facade,  #  0 0x00
                    0x0d15ea5e,  #  1 0x04
                    0xbaadf00d,  #  2 0x08
                    0xcafefeed,  #  3 0x0c
                    0xdeadc0de,  #  4 0x10
                    0xfee1dead,  #  5 0x14
                    0x00000000,  #  6 0x18
                    0x00000000,  #  7 0x1c
                    0x00000000,  #  8 0x20
                    0x00000000,  #  9 0x24
                    0x8badf00d,  # 10 0x28
                    0xabadcafe,  # 11 0x2c
                    0x00000000,  # 12 0x30
                ]
            ),
            "32bit_to_8bit": dict(
                pattern=[
                    # address, data
                    (0x00, 0x00112233),
                    (0x05, 0x44556677),
                    (0x01, 0x8899aabb),
                    (0x02, 0xccddeeff),
                ],
                expected=[
                    # data, address
                    0x33,  # 0x00
                    0x22,  # 0x01
                    0x11,  # 0x02
                    0x00,  # 0x03
                    0xbb,  # 0x04
                    0xaa,  # 0x05
                    0x99,  # 0x06
                    0x88,  # 0x07
                    0xff,  # 0x08
                    0xee,  # 0x09
                    0xdd,  # 0x0a
                    0xcc,  # 0x0b
                    0x00,  # 0x0c
                    0x00,  # 0x0d
                    0x00,  # 0x0e
                    0x00,  # 0x0f
                    0x00,  # 0x10
                    0x00,  # 0x11
                    0x00,  # 0x12
                    0x00,  # 0x13
                    0x77,  # 0x14
                    0x66,  # 0x15
                    0x55,  # 0x16
                    0x44,  # 0x17
                    0x00,  # 0x18
                    0x00,  # 0x19
                ]
            ),
            "8bit_to_32bit": dict(
                pattern=[
                    # address, data
                    (0x00, 0x00),
                    (0x01, 0x11),
                    (0x02, 0x22),
                    (0x03, 0x33),
                    (0x10, 0x44),
                    (0x11, 0x55),
                    (0x12, 0x66),
                    (0x13, 0x77),
                    (0x08, 0x88),
                    (0x09, 0x99),
                    (0x0a, 0xaa),
                    (0x0b, 0xbb),
                    (0x0c, 0xcc),
                    (0x0d, 0xdd),
                    (0x0e, 0xee),
                    (0x0f, 0xff),
                ],
                expected=[
                    # data, address
                    0x33221100,  # 0x00
                    0x00000000,  # 0x04
                    0xbbaa9988,  # 0x08
                    0xffeeddcc,  # 0x0c
                    0x77665544,  # 0x10
                    0x00000000,  # 0x14
                    0x00000000,  # 0x18
                    0x00000000,  # 0x1c
                ]
            ),
            "8bit_to_32bit_not_aligned": dict(
                pattern=[
                    # address, data
                    (0x00, 0x00),
                    (0x05, 0x11),
                    (0x0a, 0x22),
                    (0x0f, 0x33),
                    (0x1e, 0x44),
                    (0x15, 0x55),
                    (0x13, 0x66),
                    (0x18, 0x77),
                ],
                expected=[
                    # data, address
                    0x00000000,  # 0x00
                    0x00001100,  # 0x04
                    0x00220000,  # 0x08
                    0x33000000,  # 0x0c
                    0x66000000,  # 0x10
                    0x00005500,  # 0x14
                    0x00000077,  # 0x18
                    0x00440000,  # 0x1c
                ]
            ),
            "32bit_to_256bit":  dict(
                pattern=[
                    # address, data
                    (0x00, 0x00000000),
                    (0x01, 0x11111111),
                    (0x02, 0x22222222),
                    (0x03, 0x33333333),
                    (0x04, 0x44444444),
                    (0x05, 0x55555555),
                    (0x06, 0x66666666),
                    (0x07, 0x77777777),
                    (0x10, 0x88888888),
                    (0x11, 0x99999999),
                    (0x12, 0xaaaaaaaa),
                    (0x13, 0xbbbbbbbb),
                    (0x14, 0xcccccccc),
                    (0x15, 0xdddddddd),
                    (0x16, 0xeeeeeeee),
                    (0x17, 0xffffffff),
                ],
                expected=[
                    # data, address
                    0x7777777766666666555555554444444433333333222222221111111100000000,  # 0x00
                    0x0000000000000000000000000000000000000000000000000000000000000000,  # 0x20
                    0xffffffffeeeeeeeeddddddddccccccccbbbbbbbbaaaaaaaa9999999988888888,  # 0x40
                    0x0000000000000000000000000000000000000000000000000000000000000000,  # 0x60
                ]
            ),
            "32bit_to_256bit_not_aligned":  dict(
                pattern=[
                    # address, data
                    (0x00, 0x00000000),
                    (0x01, 0x11111111),
                    (0x02, 0x22222222),
                    (0x03, 0x33333333),
                    (0x04, 0x44444444),
                    (0x05, 0x55555555),
                    (0x06, 0x66666666),
                    (0x07, 0x77777777),
                    (0x14, 0x88888888),
                    (0x15, 0x99999999),
                    (0x16, 0xaaaaaaaa),
                    (0x17, 0xbbbbbbbb),
                    (0x18, 0xcccccccc),
                    (0x19, 0xdddddddd),
                    (0x1a, 0xeeeeeeee),
                    (0x1b, 0xffffffff),
                ],
                expected=[
                    # data, address
                    0x7777777766666666555555554444444433333333222222221111111100000000,  # 0x00
                    0x0000000000000000000000000000000000000000000000000000000000000000,  # 0x20
                    0xbbbbbbbbaaaaaaaa999999998888888800000000000000000000000000000000,  # 0x40
                    0x00000000000000000000000000000000ffffffffeeeeeeeeddddddddcccccccc,  # 0x60
                ]
            ),
            "32bit_not_aligned": dict(
                pattern=[
                    # address, data
                    (0x00, 0xabadcafe),
                    (0x07, 0xbaadf00d),
                    (0x02, 0xcafefeed),
                    (0x01, 0xdeadc0de),
                ],
                expected=[
                    # data, address
                    0xabadcafe,  # 0x00
                    0xdeadc0de,  # 0x04
                    0xcafefeed,  # 0x08
                    0x00000000,  # 0x0c
                    0x00000000,  # 0x10
                    0x00000000,  # 0x14
                    0x00000000,  # 0x18
                    0xbaadf00d,  # 0x1c
                ],
            ),
            "32bit_duplicates": dict(
                pattern=[
                    # address, data
                    (0x00, 0xabadcafe),
                    (0x07, 0xbaadf00d),
                    (0x00, 0xcafefeed),
                    (0x07, 0xdeadc0de),
                ],
                expected=[
                    # data, address
                    0xcafefeed,  # 0x00
                    0x00000000,  # 0x04
                    0x00000000,  # 0x08
                    0x00000000,  # 0x0c
                    0x00000000,  # 0x10
                    0x00000000,  # 0x14
                    0x00000000,  # 0x18
                    0xdeadc0de,  # 0x1c
                ],
            ),
            "32bit_sequential": dict(
                pattern=[
                    # address, data
                    (0x02, 0xabadcafe),
                    (0x03, 0xbaadf00d),
                    (0x04, 0xcafefeed),
                    (0x05, 0xdeadc0de),
                ],
                expected=[
                    # data, address
                    0x00000000,  # 0x00
                    0x00000000,  # 0x04
                    0xabadcafe,  # 0x08
                    0xbaadf00d,  # 0x0c
                    0xcafefeed,  # 0x10
                    0xdeadc0de,  # 0x14
                    0x00000000,  # 0x18
                    0x00000000,  # 0x1c
                ],
            ),
            "32bit_long_sequential": dict(pattern=[], expected=[0] * 64),
        }

        # 32bit_long_sequential
        for i in range(32):
            data["32bit_long_sequential"]["pattern"].append((i, 64 + i))
            data["32bit_long_sequential"]["expected"][i] = 64 + i

        def half_width(data, from_width):
            half_mask = 2**(from_width//2) - 1
            chunks = [(val & half_mask, (val >> from_width//2) & half_mask) for val in data]
            return list(itertools.chain.from_iterable(chunks))

        # down conversion
        data["64bit_to_16bit"] = dict(
            pattern  = data["64bit_to_32bit"]["pattern"].copy(),
            expected = half_width(data["64bit_to_32bit"]["expected"], from_width=32),
        )
        data["64bit_to_8bit"] = dict(
            pattern  = data["64bit_to_16bit"]["pattern"].copy(),
            expected = half_width(data["64bit_to_16bit"]["expected"], from_width=16),
        )

        # up conversion
        data["8bit_to_16bit"] = dict(
            pattern  = data["8bit_to_32bit"]["pattern"].copy(),
            expected = half_width(data["8bit_to_32bit"]["expected"], from_width=32),
        )
        data["32bit_to_128bit"] = dict(
            pattern  = data["32bit_to_256bit"]["pattern"].copy(),
            expected = half_width(data["32bit_to_256bit"]["expected"], from_width=256),
        )
        data["32bit_to_64bit"] = dict(
            pattern  = data["32bit_to_128bit"]["pattern"].copy(),
            expected = half_width(data["32bit_to_128bit"]["expected"], from_width=128),
        )

        return data
