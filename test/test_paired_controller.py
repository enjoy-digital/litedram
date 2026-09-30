#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import unittest
from migen import *
from litedram.frontend.paired import PairedPort
from litedram.frontend.native_benchmark import NativeDMABenchmark
from test.test_native_benchmark import simulate

from copy import copy
from litedram.modules import MT40A512M16, _SpeedgradeTimings
from litedram.phy.model import SDRAMPHYModel
from litedram.core.controller import LiteDRAMController, ControllerSettings
from litedram.core.crossbar import LiteDRAMCrossbar
from litedram.common import PhySettings


class SmallMemory(MT40A512M16):
    nrows = 2
    technology_timings = copy(MT40A512M16.technology_timings)
    technology_timings.tCCD = (8, None)
    speedgrade_timings = dict(MT40A512M16.speedgrade_timings)
    speedgrade_timings['2666'] = _SpeedgradeTimings(
        tRP=14.25, tRCD=14.25, tWR=15, tRFC=MT40A512M16.trfc, tFAW=(28, 30), tRAS=33)


class ControllerTest(unittest.TestCase):
    def test_rejects_incompatible_controller_geometry(self):
        module = SmallMemory(1000e6/3, "1:4", speedgrade="2666")
        for changed in ({"dfi_databits": 64}, {"databits": 32}, {"nranks": 2}):
            with self.subTest(changed=changed):
                values = dict(phytype="SDRAMPHYModel", memtype="DDR4", databits=16,
                    dfi_databits=32, nranks=1, nphases=4, rdphase=0, wrphase=1,
                    cl=19, cwl=14, read_latency=11, write_latency=3)
                values.update(changed)
                with self.assertRaisesRegex(ValueError, "Bank-group interleaving requires"):
                    LiteDRAMController(PhySettings(**values), module.geom_settings,
                        module.timing_settings, 1000e6/3,
                        controller_settings=ControllerSettings(with_bank_group_interleaving=True))

    def test_full_path_and_cpu_mapping(self):
        module = SmallMemory((1000e6/3), '1:4', speedgrade='2666')
        # Keep command pins (including A10 precharge-all) despite fewer rows.
        module.geom_settings.addressbits = 17
        settings = PhySettings(phytype='SDRAMPHYModel', memtype='DDR4', databits=16,
                               dfi_databits=32, nranks=1, nphases=4, rdphase=0, wrphase=1,
                               cl=19, cwl=14, cmd_latency=1, read_latency=11, write_latency=3)
        top = Module()
        top.submodules.phy = phy = SDRAMPHYModel(module, settings=settings, clk_freq=(1000e6/3))
        top.submodules.controller = controller = LiteDRAMController(settings,
                                                                    module.geom_settings, module.timing_settings, (
                                                                        1000e6/3),
                                                                    controller_settings=ControllerSettings(with_bank_group_interleaving=True))
        banks = [m for _, m in controller._submodules if hasattr(m, "row_hit")]
        assert len(banks) == 8
        top.comb += controller.dfi.connect(phy.dfi)
        top.submodules.crossbar = crossbar = LiteDRAMCrossbar(controller.interface)
        top.submodules.w = w = PairedPort([crossbar.get_port(mode='write')
                                          for _ in range(2)], 'write')
        top.submodules.r = r = PairedPort([crossbar.get_port(mode='read')
                                          for _ in range(2)], 'read')
        cpu = crossbar.get_port(mode='read')
        top.submodules.dma = dma = NativeDMABenchmark(
            w.port, r.port, capacity=32768, drained=w.drained, databits=16)
        events = {'cas': 0, 'refresh': 0, 'cpu_commands': 0}

        @passive
        def monitor():
            cycle = 0
            last = {}
            while True:
                for bank in banks:
                    self.assertEqual((yield bank.row_hit), (yield bank.row) == ((yield bank.current_address) >> 7))
                for nm in range(len(crossbar.masters)):
                    owners = 0
                    for mask in crossbar.owner_masks:
                        owners += ((yield mask) >> nm) & 1
                    self.assertLessEqual(owners, 1, 'a master is locked by multiple banks')
                if (yield cpu.cmd.valid) and (yield cpu.cmd.ready):
                    events['cpu_commands'] += 1
                for phase in controller.dfi.phases:
                    cas = (yield phase.cas_n) == 0
                    ras = (yield phase.ras_n) == 0
                    if cas and not ras:
                        group = (yield phase.bank) >> 2
                        self.assertGreaterEqual(cycle-last.get(group, -10), 2)
                        last[group] = cycle
                        events['cas'] += 1
                    if cas and ras and (yield phase.we_n):
                        events['refresh'] += 1
                cycle += 1
                yield

        def main():
            yield dma.allowed.eq(1)
            yield dma._base.storage.eq(0)
            yield dma._length.storage.eq(24576)
            for random in (0, 1):
                yield dma._random.storage.eq(random)
                yield dma._start.re.eq(1)
                yield
                yield dma._start.re.eq(0)
                yield
                for _ in range(15000):
                    if (yield dma._done.status):
                        break
                    yield
                self.assertEqual((yield dma._done.status), 1)
                self.assertEqual((yield dma._fault.status), 0)
                self.assertEqual((yield dma._errors.status), 0)
                self.assertEqual((yield r.error), 0)
                print('CONTROLLER_MODEL', random, 'write_cycles', (yield dma._write_cycles.status),
                      'read_cycles', (yield dma._read_cycles.status), flush=True)
                if not random:
                    for word in (0, 1, 2, 3, 254, 255, 256, 257, 1022, 1023, 1024, 1025, 1534, 1535):
                        yield cpu.cmd.addr.eq(word)
                        yield cpu.cmd.valid.eq(1)
                        yield
                        while not (yield cpu.cmd.ready):
                            yield
                        yield cpu.cmd.valid.eq(0)
                        for _ in range(1000):
                            if (yield cpu.rdata.valid):
                                break
                            yield
                        self.assertEqual((yield cpu.rdata.valid), 1)
                        index = word//2
                        expected = sum(index << (31*k) for k in range(9)) & ((1 << 256)-1)
                        expected = (expected >> (128*(word & 1))) & ((1 << 128)-1)
                        self.assertEqual((yield cpu.rdata.data), expected)
                        yield
                    self.assertEqual(events['cpu_commands'], 14)
                    print('CPU_MAPPING_PROBES_PASS', events['cpu_commands'], flush=True)
            self.assertGreater(events['refresh'], 0)
            print('CONTROLLER_MODEL_PASS', events, flush=True)
        simulate(top, [main(), monitor()])
