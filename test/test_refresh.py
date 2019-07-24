# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import unittest

from migen import *

from litedram.core.multiplexer import cmd_request_rw_layout
from litedram.core.refresher import RefreshGenerator, RefreshTimer, Refresher


def c2bool(c):
    return {"-": 1, "_": 0}[c]

class TestRefresh(unittest.TestCase):
    def refresh_generator_test(self, trp, trfc, starts, dones, cmds):
        cmd = Record(cmd_request_rw_layout(a=16, ba=3))
        def generator(dut):
            dut.errors = 0
            for start, done, cas, ras in zip(starts, dones, cmds.cas, cmds.ras):
                yield dut.start.eq(c2bool(start))
                yield
                if (yield dut.done) != c2bool(done):
                    dut.errors += 1
                if (yield cmd.cas) != c2bool(cas):
                    dut.errors += 1
                if (yield cmd.ras) != c2bool(ras):
                    dut.errors += 1
        dut = RefreshGenerator(cmd, trp, trfc)
        run_simulation(dut, [generator(dut)])
        self.assertEqual(dut.errors, 0)

    def test_refresh_generator(self):
        trp  = 1
        trfc = 2
        class Obj: pass
        cmds = Obj()
        starts   = "_-______________"
        cmds.cas = "___-____________"
        cmds.ras = "__--____________"
        dones    = "_____-__________"
        self.refresh_generator_test(trp, trfc, starts, dones, cmds)

    def refresh_timer_test(self, trefi):
        def generator(dut):
            dut.errors = 0
            for i in range(16*trefi):
                if i%trefi == (trefi - 1):
                    if (yield dut.refresh.done) != 1:
                        dut.errors += 1
                else:
                    if (yield dut.refresh.done) != 0:
                        dut.errors += 1
                yield

        class DUT(Module):
            def __init__(self, trefi):
                self.submodules.refresh = RefreshTimer(trefi)
                self.comb += self.refresh.wait.eq(~self.refresh.done)

        dut = DUT(trefi)
        run_simulation(dut, [generator(dut)])
        self.assertEqual(dut.errors, 0)

    def test_refresh_timer(self):
        for i in range(1, 32):
            self.refresh_timer_test(i)

    def test_refresher(self):
        class Obj: pass
        settings = Obj()
        settings.with_refresh = True
        settings.timing =Obj()
        settings.timing.tREFI = 64
        settings.timing.tRP   = 1
        settings.timing.tRFC  = 2
        settings.geom = Obj()
        settings.geom.addressbits = 16
        settings.geom.bankbits    = 3
        settings.phy = Obj()
        settings.phy.nranks = 1

        def generator(dut):
            dut.errors = 0
            yield dut.cmd.ready.eq(1)
            for i in range(16):
                while (yield dut.cmd.valid) == 0:
                    yield
                cmd_valid_gap = 0
                while (yield dut.cmd.valid) == 1:
                    cmd_valid_gap += 1
                    yield
                while (yield dut.cmd.valid) == 0:
                    cmd_valid_gap += 1
                    yield
                if cmd_valid_gap != settings.timing.tREFI:
                    dut.errors += 1

        dut = Refresher(settings)
        run_simulation(dut, [generator(dut)])
        self.assertEqual(dut.errors, 0)
