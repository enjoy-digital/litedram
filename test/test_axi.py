import unittest
import random

from migen import *

from litedram.common import LiteDRAMNativePort
from litedram.frontend.axi import *

from test.common import *

from litex.gen.sim import *


class TestAXI(unittest.TestCase):
    def test_axi2native(self):
        class Access:
            def __init__(self, addr, data, id):
                self.addr = addr
                self.data = data
                self.id = id

        class Write(Access):
            pass

        class Read(Access):
            pass

        def writes_cmd_data_generator(axi_port, writes):
            for write in writes:
                # send command
                yield axi_port.aw.valid.eq(1)
                yield axi_port.aw.addr.eq(write.addr<<2)
                yield axi_port.aw.id.eq(write.id)
                yield
                while (yield axi_port.aw.ready) == 0:
                    yield
                yield axi_port.aw.valid.eq(0)
                yield
                # send data
                yield axi_port.w.valid.eq(1)
                yield axi_port.w.last.eq(1)
                yield axi_port.w.data.eq(write.data)
                yield
                while (yield axi_port.w.ready) == 0:
                    yield
                yield axi_port.w.valid.eq(0)

        def writes_response_generator(axi_port, writes):
            self.writes_id_errors = 0
            yield axi_port.b.ready.eq(1) # always accepting write response
            for write in writes:
              # wait response
                while (yield axi_port.b.valid) == 0:
                    yield
                if (yield axi_port.b.id) != write.id:
                    self.writes_id_errors += 1
                yield

        def reads_cmd_generator(axi_port, reads):
            for read in reads:
                # send command
                yield axi_port.ar.valid.eq(1)
                yield axi_port.ar.addr.eq(read.addr<<2)
                yield axi_port.ar.id.eq(read.id)
                yield
                while (yield axi_port.ar.ready) == 0:
                    yield
                yield axi_port.ar.valid.eq(0)
                yield

        def reads_response_data_generator(axi_port, reads):
            self.reads_data_errors = 0
            self.reads_id_errors = 0
            self.reads_last_errors = 0
            yield axi_port.r.ready.eq(1) # always accepting read response
            for read in reads:
                # wait data / response
                while (yield axi_port.r.valid) == 0:
                    yield
                if (yield axi_port.r.data) != read.data:
                    self.reads_data_errors += 1
                if (yield axi_port.r.id) != read.id:
                    self.reads_id_errors += 1
                if (yield axi_port.r.last) != 1:
                    self.reads_last_errors += 1
                yield

        # dut
        axi_port = LiteDRAMAXIPort(32, 32, 8)
        dram_port = LiteDRAMNativePort("both", 32, 32)
        dut = LiteDRAMAXI2Native(axi_port, dram_port)
        mem = DRAMMemory(32, 128)

        # generate writes/reads
        prng = random.Random(42)
        writes = []
        for i in range(64):
            # incrementing addr, random data &id
            writes.append(Write(i, prng.randrange(2**32), prng.randrange(2**8)))
            # incrementing addr, data & id (debug)
            #writes.append(Write(i, i, i))
        reads = []
        for i in range(64): # dummy reads while content not yet written
            reads.append(Read(64, 0x00000000, 0x00))
        for i in range(64):
            # incrementing addr, written data, random id
            reads.append(Read(i, writes[i].data, prng.randrange(2**8)))
            # incrementing addr, written data, incrementing id (debug)
            #reads.append(Read(i, writes[i].data, i))

        # simulation
        generators = [
            writes_cmd_data_generator(axi_port, writes),
            writes_response_generator(axi_port, writes),
            reads_cmd_generator(axi_port, reads),
            reads_response_data_generator(axi_port, reads),
            mem.read_handler(dram_port),
            mem.write_handler(dram_port)
        ]
        run_simulation(dut, generators, vcd_name="axi2native.vcd")
        #mem.show_content()
        self.assertEqual(self.writes_id_errors, 0)
        self.assertEqual(self.reads_data_errors, 0)
        self.assertEqual(self.reads_id_errors, 0)
        self.assertEqual(self.reads_last_errors, 0)

    def test_burst2beat(self):
        class Beat:
            def __init__(self, addr):
                self.addr = addr

        class Burst:
            def __init__(self, type, addr, len, size):
                self.type = type
                self.addr = addr
                self.len = len
                self.size = size

            def to_beats(self):
                r = []
                for i in range(self.len + 1):
                    if self.type == burst_types["incr"]:
                        offset = i*2**(self.size)
                        r += [Beat(self.addr + offset)]
                    elif self.type == burst_types["wrap"]:
                        offset = (i*2**(self.size))%((2**self.size)*(self.len))
                        r += [Beat(self.addr + offset)]
                    else:
                        r += [Beat(self.addr)]
                return r

        def bursts_generator(ax, bursts, valid_rand=50):
            prng = random.Random(42)
            for burst in bursts:
                yield ax.valid.eq(1)
                yield ax.addr.eq(burst.addr)
                yield ax.burst.eq(burst.type)
                yield ax.len.eq(burst.len)
                yield ax.size.eq(burst.size)
                while (yield ax.ready) == 0:
                    yield
                yield ax.valid.eq(0)
                while prng.randrange(100) < valid_rand:
                    yield
                yield

        @passive
        def beats_checker(ax, beats, ready_rand=50):
            self.errors = 0
            yield ax.ready.eq(0)
            prng = random.Random(42)
            for beat in beats:
                while ((yield ax.valid) and (yield ax.ready)) == 0:
                    if prng.randrange(100) > ready_rand:
                        yield ax.ready.eq(1)
                    else:
                        yield ax.ready.eq(0)
                    yield
                ax_addr = (yield ax.addr)
                if ax_addr != beat.addr:
                    self.errors += 1
                yield

        # dut
        ax_burst = stream.Endpoint(ax_description(32, 32))
        ax_beat = stream.Endpoint(ax_description(32, 32))
        dut =  LiteDRAMAXIBurst2Beat(ax_burst, ax_beat)

        # generate dut input (bursts)
        prng = random.Random(42)
        bursts = []
        for i in range(32):
            bursts.append(Burst(burst_types["fixed"], prng.randrange(2**32), prng.randrange(255), log2_int(32//8)))
            bursts.append(Burst(burst_types["incr"], prng.randrange(2**32), prng.randrange(255), log2_int(32//8)))
        bursts.append(Burst(burst_types["wrap"], 4, 4-1, log2_int(2)))

        # generate expexted dut output (beats for reference)
        beats = []
        for burst in bursts:
            beats += burst.to_beats()

        # simulation
        generators = [
            bursts_generator(ax_burst, bursts),
            beats_checker(ax_beat, beats)
        ]
        run_simulation(dut, generators, vcd_name="burst2beat.vcd")
        self.assertEqual(self.errors, 0)
