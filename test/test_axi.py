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


# Burst/Beat Helpers -------------------------------------------------------------------------------

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

# Access Helpers -----------------------------------------------------------------------------------

class Access(Burst):
    def __init__(self, addr, data, strb, id, **kwargs):
        Burst.__init__(self, addr, **kwargs)
        self.data = data
        self.strb = strb
        self.id   = id


class Write(Access): pass

class Read(Access): pass

def strb_to_mask(strb, data_width):
    mask = 0
    for i in reversed(range(data_width//8)):
        mask <<= 8
        if (strb >> i) & 0x1:
            mask |= 0xff
    return mask

# Test AXI -----------------------------------------------------------------------------------------

class TestAXI(unittest.TestCase):
    def _test_axi2native(self,
        naccesses=16, simultaneous_writes_reads=False,
        # AXI WRAP burst support of the DUT (the harness only issues INCR/FIXED bursts).
        with_wrap = True,
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
        r_ready_random  = 0,
        # AXI base address of the DRAM
        base_address    = 0
        ):

        def writes_cmd_generator(axi_port, writes):
            prng = random.Random(42)
            for write in writes:
                while prng.randrange(100) < aw_valid_random:
                    yield
                # Send command
                yield axi_port.aw.valid.eq(1)
                yield axi_port.aw.addr.eq(base_address + (write.addr<<2))
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
                for i, (data, strb) in enumerate(zip(write.data, write.strb)):
                    while prng.randrange(100) < w_valid_random:
                        yield
                    # Send data
                    yield axi_port.w.valid.eq(1)
                    if (i == (len(write.data) - 1)):
                        yield axi_port.w.last.eq(1)
                    else:
                        yield axi_port.w.last.eq(0)
                    yield axi_port.w.data.eq(data)
                    yield axi_port.w.strb.eq(strb)
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
            axi_port.writes_done = True

        def reads_cmd_generator(axi_port, reads):
            prng = random.Random(42)
            while not axi_port.reads_enable:
                yield
            for read in reads:
                # AXI does not order reads with writes: wait for write responses before checked reads.
                while (not read.dummy) and (not axi_port.writes_done):
                    yield
                while prng.randrange(100) < ar_valid_random:
                    yield
                # Send command
                yield axi_port.ar.valid.eq(1)
                yield axi_port.ar.addr.eq(base_address + (read.addr<<2))
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
                for i, (data, strb) in enumerate(zip(read.data, read.strb)):
                    # Wait data / response
                    yield axi_port.r.ready.eq(0)
                    yield
                    while (yield axi_port.r.valid) == 0:
                        yield
                    while prng.randrange(100) < r_ready_random:
                        yield
                    yield axi_port.r.ready.eq(1)
                    yield
                    data_ref = data                    & strb_to_mask(strb, axi_port.data_width)
                    data_cur = (yield axi_port.r.data) & strb_to_mask(strb, axi_port.data_width)
                    if data_ref != data_cur:
                        print(f"ref: {data_ref:08x} vs cur: {data_cur:08x}")
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
        axi_port  = LiteDRAMAXIPort(data_width=32, address_width=32, id_width=8)
        dram_port = LiteDRAMNativePort("both", 32, 32)
        dut       = LiteDRAMAXI2Native(axi_port, dram_port, with_read_modify_write=True,
            base_address=base_address, with_wrap=with_wrap)
        mem       = DRAMMemory(32, 1024)

        # Generate writes/reads
        prng   = random.Random(42)
        writes = []
        offset = 1
        for i in range(naccesses):
            _id   = prng.randrange(2**8)        if   id_rand_enable else i
            _len  = prng.randrange(32)          if  len_rand_enable else i
            _data = [prng.randrange(2**32)      if data_rand_enable else    j for j in range(_len + 1)]
            _strb = [prng.randrange(2**(32//8)) if data_rand_enable else 0xff for j in range(_len + 1)]
            writes.append(Write(offset, _data, _strb, _id, type=BURST_INCR, len=_len, size=log2_int(32//8)))
            offset += _len + 1
        # Dummy reads (simultaneous with writes) before the effective reads.
        dummy_reads = [Read(1023, [0], [2**(32//8)-1], 0, type=BURST_FIXED, len=0, size=log2_int(32//8)) for _ in range(32)]
        for read in dummy_reads:
            read.dummy = True
        for write in writes:
            write.dummy = False
        reads = dummy_reads + writes

        # Simulation
        axi_port.writes_done = False
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
        run_simulation(dut, generators, vcd_name="sim.vcd")
        #mem.show_content()
        self.assertEqual(self.writes_id_errors, 0)
        self.assertEqual(self.reads_data_errors, 0)
        self.assertEqual(self.reads_id_errors, 0)
        self.assertEqual(self.reads_last_errors, 0)

    # Test with no randomness
    def test_axi2native_non_pow2_base_address(self):
        # The DRAM does not have to be mapped at a power-of-two address.
        self._test_axi2native(base_address=0x40010000)

    def test_axi2native_writes_then_reads_no_random(self):
        self._test_axi2native(simultaneous_writes_reads=False)

    def test_axi2native_writes_and_reads_no_random(self):
        self._test_axi2native(simultaneous_writes_reads=True)

    # Test without WRAP burst support (INCR/FIXED bursts only).
    def test_axi2native_without_wrap(self):
        self._test_axi2native(simultaneous_writes_reads=False, with_wrap=False)

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

    def test_axi2native_write_data_waits_for_cmd(self):
        axi_port  = LiteDRAMAXIPort(data_width=32, address_width=32, id_width=8)
        dram_port = LiteDRAMNativePort("both", 32, 32)
        dut       = LiteDRAMAXI2Native(axi_port, dram_port)

        self.unreserved_wdata_errors = 0

        def axi_write_generator():
            yield axi_port.aw.valid.eq(1)
            yield axi_port.aw.addr.eq(0)
            yield axi_port.aw.burst.eq(BURST_INCR)
            yield axi_port.aw.len.eq(0)
            yield axi_port.aw.size.eq(log2_int(32//8))
            yield axi_port.aw.id.eq(1)

            yield axi_port.w.valid.eq(1)
            yield axi_port.w.data.eq(0x12345678)
            yield axi_port.w.strb.eq(0xf)
            yield axi_port.w.last.eq(1)
            while (yield axi_port.w.ready) == 0:
                yield
            yield axi_port.w.valid.eq(0)

            for _ in range(8):
                yield

        def native_ready_monitor():
            yield dram_port.cmd.ready.eq(0)
            yield dram_port.wdata.ready.eq(1)
            for _ in range(8):
                if (yield dram_port.wdata.valid):
                    self.unreserved_wdata_errors += 1
                yield

        run_simulation(dut, [axi_write_generator(), native_ready_monitor()])
        self.assertEqual(self.unreserved_wdata_errors, 0)

    def _axi2native_single_writes(self, writes, w_buffer_depth=16, with_read_modify_write=False,
        mem_init=[], w_delay=0, aw_delay=0, b_ready_delay=0, ncycles=1000):
        # Issue single-beat writes with independent AW/W timings and return (B IDs, memory).
        axi_port  = LiteDRAMAXIPort(data_width=32, address_width=32, id_width=8)
        dram_port = LiteDRAMNativePort("both", 32, 32)
        dut       = LiteDRAMAXI2Native(axi_port, dram_port,
            w_buffer_depth         = w_buffer_depth,
            with_read_modify_write = with_read_modify_write)
        mem       = DRAMMemory(32, 1024, init=mem_init)
        b_ids     = []

        def aw_generator():
            for _ in range(aw_delay):
                yield
            for addr, data, strb, _id in writes:
                yield axi_port.aw.valid.eq(1)
                yield axi_port.aw.addr.eq(addr)
                yield axi_port.aw.burst.eq(BURST_INCR)
                yield axi_port.aw.len.eq(0)
                yield axi_port.aw.size.eq(log2_int(32//8))
                yield axi_port.aw.id.eq(_id)
                yield
                while (yield axi_port.aw.ready) == 0:
                    yield
                yield axi_port.aw.valid.eq(0)

        def w_generator():
            for _ in range(w_delay):
                yield
            for addr, data, strb, _id in writes:
                yield axi_port.w.valid.eq(1)
                yield axi_port.w.data.eq(data)
                yield axi_port.w.strb.eq(strb)
                yield axi_port.w.last.eq(1)
                yield
                while (yield axi_port.w.ready) == 0:
                    yield
                yield axi_port.w.valid.eq(0)

        def b_generator():
            yield axi_port.b.ready.eq(0)
            for _ in range(b_ready_delay):
                yield
            yield axi_port.b.ready.eq(1)
            for _ in range(ncycles):
                yield
                if (yield axi_port.b.valid) and (yield axi_port.b.ready):
                    b_ids.append((yield axi_port.b.id))

        generators = [
            aw_generator(),
            w_generator(),
            b_generator(),
            mem.read_handler(dram_port),
            mem.write_handler(dram_port),
        ]
        run_simulation(dut, generators)
        return b_ids, mem

    def test_axi2native_b_backpressure(self):
        # Holding BREADY low across more writes than the response buffer can hold must stall the
        # writes, not drop their responses.
        for depth in [2, 4]:
            for with_read_modify_write in [False, True]:
                with self.subTest(depth=depth, with_read_modify_write=with_read_modify_write):
                    writes = [(4*(16 + i), 0x100 + i, 0xf, i) for i in range(2*depth + 1)]
                    b_ids, mem = self._axi2native_single_writes(writes,
                        w_buffer_depth         = depth,
                        with_read_modify_write = with_read_modify_write,
                        b_ready_delay          = 200)
                    self.assertEqual(b_ids, [_id for _, _, _, _id in writes])
                    for addr, data, _, _ in writes:
                        self.assertEqual(mem.mem[addr//4], data)

    def test_axi2native_b_backpressure_rmw_partial(self):
        # Same with partial writes going through the Read-Modify-Write path.
        writes = [(4*(16 + i), 0x100 + i, 0x1, i) for i in range(5)]
        b_ids, mem = self._axi2native_single_writes(writes,
            w_buffer_depth         = 2,
            with_read_modify_write = True,
            mem_init               = [0xaabbcc00]*32,
            b_ready_delay          = 200)
        self.assertEqual(b_ids, [_id for _, _, _, _id in writes])
        for addr, data, _, _ in writes:
            self.assertEqual(mem.mem[addr//4], 0xaabbcc00 | (data & 0xff))

    def test_axi2native_rmw_w_before_aw(self):
        # A partial W beat arriving before its AW must be merged at the AW address and answered
        # with the AW ID.
        for warmup in [False, True]:
            with self.subTest(warmup=warmup):
                mem_init = [0]*64
                mem_init[0]  = 0xaabbcc11
                mem_init[16] = 0x11223344
                writes = [(0x40, 0x000000dd, 0x1, 7)]
                if warmup:
                    writes = [(0x80, 0x55667788, 0xf, 3)] + writes
                b_ids, mem = self._axi2native_single_writes(writes,
                    with_read_modify_write = True,
                    mem_init               = mem_init,
                    aw_delay               = 40)
                self.assertEqual(b_ids, [_id for _, _, _, _id in writes])
                self.assertEqual(mem.mem[0],  0xaabbcc11)
                self.assertEqual(mem.mem[16], 0x112233dd)
                if warmup:
                    self.assertEqual(mem.mem[32], 0x55667788)

    def test_axi2native_rmw_partial_w_behind_buffered_w(self):
        # A partial W beat queued behind full W beats whose AWs have not been seen yet must not
        # be merged at the address of the first buffered write.
        mem_init = [0]*64
        mem_init[18] = 0x11223344
        writes = [
            (0x40, 0x01010101, 0xf, 1),
            (0x44, 0x02020202, 0xf, 2),
            (0x48, 0x000000dd, 0x1, 3),
        ]
        b_ids, mem = self._axi2native_single_writes(writes,
            with_read_modify_write = True,
            mem_init               = mem_init,
            aw_delay               = 40)
        self.assertEqual(b_ids, [1, 2, 3])
        self.assertEqual(mem.mem[16], 0x01010101)
        self.assertEqual(mem.mem[17], 0x02020202)
        self.assertEqual(mem.mem[18], 0x112233dd)

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
