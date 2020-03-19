# This file is Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2016 Tim 'mithro' Ansell <mithro@mithis.com>
# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
# License: BSD

import random

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


class DRAMMemory:
    def __init__(self, width, depth, init=[]):
        self.width = width
        self.depth = depth
        self.mem = []
        for d in init:
            self.mem.append(d)
        for _ in range(depth-len(init)):
            self.mem.append(0)

    def show_content(self):
        for addr in range(self.depth):
            print("0x{:08x}: 0x{:08x}".format(addr, self.mem[addr]))

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
                yield dram_port.rdata.data.eq(self.mem[address%self.depth])
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
                self.mem[address%self.depth] = (yield dram_port.wdata.data) # TODO manage we
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
                base=2,
                end=2 + 8,  # (end - base) must be pow of 2
                length=5,
                #                       2     3     4     5     6     7=2+5
                expected=[0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x00],
            ),
            "32bit": dict(
                base=0x04,
                end=0x04 + 8,
                length=5 * 4,
                expected=[
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
                base=0x10,
                end=0x10 + 8,
                length=5 * 8,
                expected=[
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
                base=0x04,
                end=0x04 + 0x04,  # TODO: fix address masking to be consistent
                length=6 * 4,
                expected=[  # due to masking
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
            base=16,
            end=16 + 128,
            length=64,
            expected=[0x00000000] * 128
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
        for i in range(32):
            data["32bit_long_sequential"]["pattern"].append((i, 64 + i))
            data["32bit_long_sequential"]["expected"][i] = 64 + i
        return data
