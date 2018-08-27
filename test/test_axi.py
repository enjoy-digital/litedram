import unittest
import random

from migen import *

from litedram.common import LiteDRAMNativePort
from litedram.frontend.axi import *

from litex.gen.sim import *


class TestAXI(unittest.TestCase):
    def test_axi2native(self):
        def main_generator(axi_port, dram_port, dut):
            prng = random.Random(42)
            # axi_port always accepting wresps/rdatas
            yield axi_port.b.ready.eq(1)
            yield axi_port.r.ready.eq(1)
            yield
            # test writes
            for i in range(16):
                # write command
                yield axi_port.aw.valid.eq(1)
                yield axi_port.aw.addr.eq(i)
                while (yield dram_port.cmd.ready) == 0:
                    if prng.randrange(100) < 20:
                        yield dram_port.cmd.ready.eq(1)
                    yield
                yield axi_port.aw.valid.eq(0)
                yield dram_port.cmd.ready.eq(0)
                yield
                # write data
                yield axi_port.w.valid.eq(1)
                yield axi_port.w.data.eq(i)
                while (yield dram_port.wdata.ready) == 0:
                    if prng.randrange(100) < 20:
                        yield dram_port.wdata.ready.eq(1)
                    yield
                    if (yield axi_port.w.ready) == 1:
                        yield axi_port.w.valid.eq(0)
                yield axi_port.aw.valid.eq(0)
                yield dram_port.wdata.ready.eq(0)
                yield
            # test reads
            for i in range(16):
                # read command
                yield axi_port.ar.valid.eq(1)
                yield axi_port.ar.addr.eq(i)
                while (yield dram_port.cmd.ready) == 0:
                    if prng.randrange(100) < 20:
                        yield dram_port.cmd.ready.eq(1)
                    yield
                yield axi_port.ar.valid.eq(0)
                yield dram_port.cmd.ready.eq(0)
                yield
                # read data
                yield dram_port.rdata.valid.eq(1)
                yield dram_port.rdata.data.eq(i)
                while (yield dram_port.rdata.valid) == 0:
                    if prng.randrange(100) < 20:
                        yield dram_port.rdata.valid.eq(1)
                    yield
                yield axi_port.ar.valid.eq(0)
                yield dram_port.rdata.valid.eq(0)
                yield
            for i in range(128):
                yield

        axi_port = LiteDRAMAXIPort(32, 32, 32)
        dram_port = LiteDRAMNativePort("both", 32, 32)
        dut = LiteDRAMAXI2Native(axi_port, dram_port)
        run_simulation(dut, main_generator(axi_port, dram_port, dut), vcd_name="axi2native.vcd")


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
                        r += [Beat(self.addr + i*2**(self.size))]
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
            bursts.append(Burst(burst_types["fixed"], prng.randrange(2**32), prng.randrange(256), log2_int(32//8)))
            bursts.append(Burst(burst_types["incr"], prng.randrange(2**32), prng.randrange(256), log2_int(32//8)))
        
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
