#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
import random

from migen import *

from litedram.common import *
from litedram.frontend.axi import *

from test.common import *

from litex.gen.sim import *


class Burst:
    def __init__(self, addr, type=BURST_FIXED, len=0, size=0):
        self.addr = addr
        self.type = type
        self.len  = len
        self.size = size

    def to_beats(self):
        r = []
        for i in range(self.len + 1):
            if self.type == BURST_INCR:
                offset = i*2**(self.size)
                r += [Beat(self.addr + offset)]
            elif self.type == BURST_WRAP:
                offset = (i*2**(self.size))%((2**self.size)*(self.len))
                r += [Beat(self.addr + offset)]
            else:
                r += [Beat(self.addr)]
        return r


class Beat:
    def __init__(self, addr):
        self.addr = addr


class Access(Burst):
    def __init__(self, addr, data, id, **kwargs):
        Burst.__init__(self, addr, **kwargs)
        self.data = data
        self.id   = id


class Write(Access):
    pass


class Read(Access):
    pass


class TestAXI(unittest.TestCase):
    def _test_axi2native(self,
        naccesses=16, simultaneous_writes_reads=False,
        # Random: 0: min (no random), 100: max.
        # Burst randomness
        id_rand_enable   = False,
        len_rand_enable  = False,
        data_rand_enable = False,
        # Flow valid randomness
        aw_valid_random = 0,
        w_valid_random  = 0,
        ar_valid_random = 0,
        r_valid_random  = 0,
        # Flow ready randomness
        w_ready_random  = 0,
        b_ready_random  = 0,
        r_ready_random  = 0
        ):

        def writes_cmd_generator(axi_port, writes):
            prng = random.Random(42)
            for write in writes:
                while prng.randrange(100) < aw_valid_random:
                    yield
                # Send command
                yield axi_port.aw.valid.eq(1)
                yield axi_port.aw.addr.eq(write.addr<<2)
                yield axi_port.aw.burst.eq(write.type)
                yield axi_port.aw.len.eq(write.len)
                yield axi_port.aw.size.eq(write.size)
                yield axi_port.aw.id.eq(write.id)
                yield
                while (yield axi_port.aw.ready) == 0:
                    yield
                yield axi_port.aw.valid.eq(0)

        def writes_data_generator(axi_port, writes):
            prng = random.Random(42)
            for write in writes:
                for i, data in enumerate(write.data):
                    while prng.randrange(100) < w_valid_random:
                        yield
                    # Send data
                    yield axi_port.w.valid.eq(1)
                    if (i == (len(write.data) - 1)):
                        yield axi_port.w.last.eq(1)
                    else:
                        yield axi_port.w.last.eq(0)
                    yield axi_port.w.data.eq(data)
                    yield axi_port.w.strb.eq(2**axi_port.w.strb.nbits - 1)
                    yield
                    while (yield axi_port.w.ready) == 0:
                        yield
                    yield axi_port.w.valid.eq(0)
            axi_port.reads_enable = True

        def writes_response_generator(axi_port, writes):
            prng = random.Random(42)
            self.writes_id_errors = 0
            for write in writes:
                # Wait response
                yield axi_port.b.ready.eq(0)
                yield
                while (yield axi_port.b.valid) == 0:
                    yield
                while prng.randrange(100) < b_ready_random:
                    yield
                yield axi_port.b.ready.eq(1)
                yield
                if (yield axi_port.b.id) != write.id:
                    self.writes_id_errors += 1

        def reads_cmd_generator(axi_port, reads):
            prng = random.Random(42)
            while not axi_port.reads_enable:
                yield
            for read in reads:
                while prng.randrange(100) < ar_valid_random:
                    yield
                # Send command
                yield axi_port.ar.valid.eq(1)
                yield axi_port.ar.addr.eq(read.addr<<2)
                yield axi_port.ar.burst.eq(read.type)
                yield axi_port.ar.len.eq(read.len)
                yield axi_port.ar.size.eq(read.size)
                yield axi_port.ar.id.eq(read.id)
                yield
                while (yield axi_port.ar.ready) == 0:
                    yield
                yield axi_port.ar.valid.eq(0)

        def reads_response_data_generator(axi_port, reads):
            prng = random.Random(42)
            self.reads_data_errors = 0
            self.reads_id_errors   = 0
            self.reads_last_errors = 0
            while not axi_port.reads_enable:
                yield
            for read in reads:
                for i, data in enumerate(read.data):
                    # Wait data / response
                    yield axi_port.r.ready.eq(0)
                    yield
                    while (yield axi_port.r.valid) == 0:
                        yield
                    while prng.randrange(100) < r_ready_random:
                        yield
                    yield axi_port.r.ready.eq(1)
                    yield
                    if (yield axi_port.r.data) != data:
                        self.reads_data_errors += 1
                    if (yield axi_port.r.id) != read.id:
                        self.reads_id_errors += 1
                    if i == (len(read.data) - 1):
                        if (yield axi_port.r.last) != 1:
                            self.reads_last_errors += 1
                    else:
                        if (yield axi_port.r.last) != 0:
                            self.reads_last_errors += 1

        # DUT
        axi_port  = LiteDRAMAXIPort(32, 32, 8)
        dram_port = LiteDRAMNativePort("both", 32, 32)
        dut       = LiteDRAMAXI2Native(axi_port, dram_port)
        mem       = DRAMMemory(32, 1024)

        # Generate writes/reads
        prng   = random.Random(42)
        writes = []
        offset = 1
        for i in range(naccesses):
            _id   = prng.randrange(2**8) if id_rand_enable else i
            _len  = prng.randrange(32) if len_rand_enable else i
            _data = [prng.randrange(2**32) if data_rand_enable else j for j in range(_len + 1)]
            writes.append(Write(offset, _data, _id, type=BURST_INCR, len=_len, size=log2_int(32//8)))
            offset += _len + 1
        # Dummy reads to ensure datas have been written before the effective reads start.
        dummy_reads = [Read(1023, [0], 0, type=BURST_FIXED, len=0, size=log2_int(32//8)) for _ in range(32)]
        reads = dummy_reads + writes

        # Simulation
        if simultaneous_writes_reads:
            axi_port.reads_enable = True
        else:
            axi_port.reads_enable = False # Will be set by writes_data_generator
        generators = [
            writes_cmd_generator(axi_port, writes),
            writes_data_generator(axi_port, writes),
            writes_response_generator(axi_port, writes),
            reads_cmd_generator(axi_port, reads),
            reads_response_data_generator(axi_port, reads),
            mem.read_handler(dram_port, rdata_valid_random=r_valid_random),
            mem.write_handler(dram_port, wdata_ready_random=w_ready_random)
        ]
        run_simulation(dut, generators)
        #mem.show_content()
        self.assertEqual(self.writes_id_errors, 0)
        self.assertEqual(self.reads_data_errors, 0)
        self.assertEqual(self.reads_id_errors, 0)
        self.assertEqual(self.reads_last_errors, 0)

    # Test with no randomness
    def test_axi2native_writes_then_reads_no_random(self):
        self._test_axi2native(simultaneous_writes_reads=False)

    def test_axi2native_writes_and_reads_no_random(self):
        self._test_axi2native(simultaneous_writes_reads=True)

    # Test randomness one parameter at a time
    def test_axi2native_writes_then_reads_random_bursts(self):
        self._test_axi2native(
            simultaneous_writes_reads = False,
            id_rand_enable   = True,
            len_rand_enable  = True,
            data_rand_enable = True)

    def test_axi2native_writes_and_reads_random_bursts(self):
        self._test_axi2native(
            simultaneous_writes_reads = True,
            id_rand_enable   = True,
            len_rand_enable  = True,
            data_rand_enable = True)

    def test_axi2native_random_w_ready(self):
        self._test_axi2native(w_ready_random=90)

    def test_axi2native_random_b_ready(self):
        self._test_axi2native(b_ready_random=90)

    def test_axi2native_random_r_ready(self):
        self._test_axi2native(r_ready_random=90)

    def test_axi2native_random_aw_valid(self):
        self._test_axi2native(aw_valid_random=90)

    def test_axi2native_random_w_valid(self):
        self._test_axi2native(w_valid_random=90)

    def test_axi2native_random_ar_valid(self):
        self._test_axi2native(ar_valid_random=90)

    def test_axi2native_random_r_valid(self):
        self._test_axi2native(r_valid_random=90)

    # Now let's stress things a bit... :)
    def test_axi2native_random_all(self):
        self._test_axi2native(
            simultaneous_writes_reads=True,
            id_rand_enable  = True,
            len_rand_enable = True,
            aw_valid_random = 50,
            w_ready_random  = 50,
            b_ready_random  = 50,
            w_valid_random  = 50,
            ar_valid_random = 90,
            r_valid_random  = 90,
            r_ready_random  = 90
        )
