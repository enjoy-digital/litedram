#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Concurrent CPU-side native traffic and paired DMA controller coverage."""

import json
import random
import unittest

from migen import Module, passive
from litedram.common import PhySettings, LiteDRAMNativePort
from litedram.core.controller import LiteDRAMController, ControllerSettings
from litedram.core.crossbar import LiteDRAMCrossbar
from litedram.frontend.dma import LiteDRAMDMAReader, LiteDRAMDMAWriter
from litedram.frontend.native_benchmark import NativeDMABenchmark
from litedram.frontend.paired import PairedPort
from litedram.phy.model import SDRAMPHYModel
from test.test_native_benchmark import simulate
from test.test_paired_controller import SmallMemory


class ConcurrentTest(unittest.TestCase):
    def test_concurrent(self):
        for seed in (8320, 2667):
            with self.subTest(seed=seed):
                self.run_seed(seed)

    def run_seed(self, seed):
        rng = random.Random(seed)
        frequency = 1000e6/3
        module = SmallMemory(frequency, "1:4", speedgrade="2666")
        module.geom_settings.addressbits = 17
        module.timing_settings.tREFI = 512
        settings = PhySettings(phytype="SDRAMPHYModel", memtype="DDR4", databits=16,
            dfi_databits=32, nranks=1, nphases=4, rdphase=0, wrphase=1,
            cl=19, cwl=14, cmd_latency=1, read_latency=11, write_latency=3)
        top = Module()
        top.submodules.phy = phy = SDRAMPHYModel(module, settings=settings, clk_freq=frequency)
        top.submodules.controller = controller = LiteDRAMController(settings,
            module.geom_settings, module.timing_settings, frequency,
            controller_settings=ControllerSettings(with_bank_group_interleaving=True))
        top.comb += controller.dfi.connect(phy.dfi)
        top.submodules.crossbar = crossbar = LiteDRAMCrossbar(controller.interface)
        top.submodules.writer = writer = PairedPort(
            [crossbar.get_port("write") for _ in range(2)], "write", depth=4)
        top.submodules.reader = reader = PairedPort(
            [crossbar.get_port("read") for _ in range(2)], "read", depth=4)
        top.submodules.dma = dma = NativeDMABenchmark(writer.port, reader.port,
            capacity=32768, fifo_depth=4, drained=writer.drained, databits=16)
        # A CPU-side native master with standard buffering. This exercises the
        # controller arbitration, not a CPU instruction set or Wishbone bridge.
        cpu_write_port = crossbar.get_port("write")
        cpu_read_port = crossbar.get_port("read")
        top.submodules.cpu_writer = cpu_writer = LiteDRAMDMAWriter(cpu_write_port, fifo_depth=4)
        top.submodules.cpu_reader = cpu_reader = LiteDRAMDMAReader(cpu_read_port, fifo_depth=4)
        state = {"cpu_done": False, "dma_active": False}
        counts = dict(seed=seed, cycles=0, cas=0, refresh=0, cpu_writes=0,
            cpu_reads=0, cpu_commands_during_dma=0, direction_changes=0,
            response_stall_cycles=0, max_cpu_command_wait=0)

        @passive
        def monitor():
            last_group = {}
            last_any = -10
            direction = None
            waits = [0, 0]
            while True:
                cycle = counts["cycles"]
                counts["cycles"] += 1
                for index, port in enumerate((cpu_write_port, cpu_read_port)):
                    if (yield port.cmd.valid):
                        if (yield port.cmd.ready):
                            counts["max_cpu_command_wait"] = max(counts["max_cpu_command_wait"], waits[index])
                            waits[index] = 0
                            counts["cpu_commands_during_dma"] += int(state["dma_active"])
                        else:
                            waits[index] += 1
                            self.assertLess(waits[index], 1200, "CPU command starved")
                if (yield cpu_reader.source.valid) and not (yield cpu_reader.source.ready):
                    counts["response_stall_cycles"] += 1
                for owner in range(len(crossbar.masters)):
                    owners = 0
                    for mask in crossbar.owner_masks:
                        owners += ((yield mask) >> owner) & 1
                    self.assertLessEqual(owners, 1)
                for phase in controller.dfi.phases:
                    if not (yield phase.cas_n):
                        if (yield phase.ras_n):
                            group = (yield phase.bank) >> 2
                            self.assertGreaterEqual(cycle-last_group.get(group, -10), 2)
                            self.assertGreaterEqual(cycle-last_any, 1)
                            last_group[group] = last_any = cycle
                            next_direction = (yield phase.we_n)
                            if direction is not None and next_direction != direction:
                                counts["direction_changes"] += 1
                            direction = next_direction
                            counts["cas"] += 1
                        elif (yield phase.we_n):
                            counts["refresh"] += 1
                yield

        def send(endpoint, **values):
            for name, value in values.items():
                yield getattr(endpoint, name).eq(value)
            yield endpoint.valid.eq(1)
            yield
            for _ in range(1200):
                if (yield endpoint.ready):
                    break
                yield
            else:
                self.fail("stream command timeout")
            yield endpoint.valid.eq(0)

        def cpu():
            for burst in range(5):
                for _ in range(rng.randrange(1, 15)):
                    yield
                words = rng.randrange(2, 5)
                addresses = [1024 + burst*128 + i for i in range(words)]
                expected = [rng.getrandbits(128) for _ in addresses]
                for address, data in zip(addresses, expected):
                    yield from send(cpu_writer.sink, address=address, data=data)
                    counts["cpu_writes"] += 1
                # Let all reserved write data reach the controller before reads.
                for _ in range(100):
                    yield
                for address, data in zip(addresses, expected):
                    yield from send(cpu_reader.sink, address=address)
                    for _ in range(1200):
                        if (yield cpu_reader.source.valid):
                            break
                        yield
                    else:
                        self.fail("CPU response timeout")
                    for _ in range(rng.randrange(3, 20)):
                        self.assertEqual((yield cpu_reader.source.data), data)
                        yield
                    yield cpu_reader.source.ready.eq(1)
                    yield
                    self.assertEqual((yield cpu_reader.source.data), data)
                    yield cpu_reader.source.ready.eq(0)
                    counts["cpu_reads"] += 1
            state["cpu_done"] = True

        def main():
            yield dma.allowed.eq(1)
            yield dma._base.storage.eq(32)
            for length in (256, 512, 1024):
                yield dma._length.storage.eq(length)
                yield dma._random.storage.eq(rng.randrange(2))
                state["dma_active"] = True
                yield dma._start.re.eq(1)
                yield
                yield dma._start.re.eq(0)
                yield
                for _ in range(2500):
                    if (yield dma._done.status):
                        break
                    yield
                self.assertEqual((yield dma._done.status), 1)
                self.assertEqual((yield dma._fault.status), 0)
                self.assertEqual((yield dma._errors.status), 0)
                self.assertEqual((yield dma._read_beats.status), length//32)
                self.assertEqual((yield writer.drained), 1)
                self.assertEqual((yield writer.error), 0)
                self.assertEqual((yield reader.error), 0)
                state["dma_active"] = False
                for _ in range(rng.randrange(1, 30)):
                    yield
            for _ in range(3000):
                if state["cpu_done"]:
                    break
                yield
            self.assertTrue(state["cpu_done"])
            self.assertGreater(counts["cpu_commands_during_dma"], 0)
            self.assertGreater(counts["refresh"], 0)
            self.assertGreater(counts["direction_changes"], 3)
            self.assertGreater(counts["response_stall_cycles"], 0)
            print("CONCURRENT_RESULT " + json.dumps(counts, sort_keys=True), flush=True)

        simulate(top, [main(), cpu(), monitor()])

    def test_invalid_mask_does_not_reach_children(self):
        ports = [LiteDRAMNativePort("write", 10, 128) for _ in range(2)]
        top = PairedPort(ports, "write", depth=4)
        seen = [[], []]

        @passive
        def monitor():
            while True:
                for index, port in enumerate(ports):
                    if (yield port.wdata.valid) and (yield port.wdata.ready):
                        seen[index].append(((yield port.wdata.we), (yield port.wdata.data)))
                yield

        def main():
            for port in ports:
                yield port.cmd.ready.eq(1)
                yield port.wdata.ready.eq(1)
            yield top.port.cmd.valid.eq(1)
            yield top.port.cmd.addr.eq(5)
            yield
            while not (yield top.port.cmd.ready):
                yield
            yield top.port.cmd.valid.eq(0)
            yield top.port.wdata.valid.eq(1)
            yield top.port.wdata.we.eq(1)
            yield top.port.wdata.data.eq(0x1234)
            yield
            while not (yield top.port.wdata.ready):
                yield
            yield top.port.wdata.valid.eq(0)
            for _ in range(30):
                yield
            self.assertEqual((yield top.error), 1)
            self.assertEqual(seen, [[], []])
            print("INVALID_MASK_CHILDREN_AFTER_FIX " + repr(seen), flush=True)

        simulate(top, [main(), monitor()])
