#
# This file is part of LiteDRAM.
#
# Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *

from litedram.core.multiplexer import cmd_request_rw_layout
from litedram.core.refresher import RefreshSequencer, RefreshTimer, Refresher


def c2bool(c):
    return {"-": 1, "_": 0}[c]

class TestRefresh(unittest.TestCase):
    def refresh_sequencer_test(self, trp, trfc, starts, dones, cmds):
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
        dut = RefreshSequencer(cmd, trp, trfc)
        run_simulation(dut, [generator(dut)])
        self.assertEqual(dut.errors, 0)

    def test_refresh_sequencer(self):
        trp  = 1
        trfc = 2
        class Obj: pass
        cmds = Obj()
        starts   = "_-______________"
        cmds.cas = "___-____________"
        cmds.ras = "__--____________"
        dones    = "_____-__________"
        self.refresh_sequencer_test(trp, trfc, starts, dones, cmds)

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
        for trefi in range(1, 32):
            with self.subTest(trefi=trefi):
                self.refresh_timer_test(trefi)

    def refresher_test(self, postponing):
        class Obj: pass
        settings = Obj()
        settings.with_refresh = True
        settings.refresh_zqcs_freq = 1e0
        settings.timing = Obj()
        settings.timing.tREFI = 128
        settings.timing.tRP   = 1
        settings.timing.tRFC  = 2
        settings.timing.tZQCS = 64
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
                if cmd_valid_gap != postponing*settings.timing.tREFI:
                    print(cmd_valid_gap)
                    dut.errors += 1

        dut = Refresher(settings, clk_freq=100e6, postponing=postponing)
        run_simulation(dut, [generator(dut)])
        self.assertEqual(dut.errors, 0)

    def test_refresher(self):
        for postponing in [1, 2, 4, 8]:
            with self.subTest(postponing=postponing):
                self.refresher_test(postponing)


    def test_registered_refresh_and_zqcs_command_equivalence(self):
        from types import SimpleNamespace
        from litedram.core.controller import ControllerSettings
        from migen import Module
        import random

        self.assertFalse(ControllerSettings().with_registered_refresh_timers)
        for postponing in (1, 2, 4, 8):
            for zqcs in (None, 4):
                with self.subTest(postponing=postponing, zqcs=zqcs):
                    top = Module()
                    def settings(registered):
                        s = ControllerSettings(with_registered_refresh_timers=registered)
                        s.geom = SimpleNamespace(addressbits=12, bankbits=3)
                        s.phy = SimpleNamespace(nranks=1)
                        s.timing = SimpleNamespace(tREFI=101, tRP=3, tRFC=7, tZQCS=zqcs)
                        return s
                    # Keep ZQCS due on each refresh to exercise its entire sequence.
                    top.submodules.reference = reference = Refresher(settings(False),
                        clk_freq=1000, zqcs_freq=1000, postponing=postponing)
                    top.submodules.registered = registered = Refresher(settings(True),
                        clk_freq=1000, zqcs_freq=1000, postponing=postponing)

                    def compare():
                        rng = random.Random(3200)
                        refreshes = calibrations = 0
                        for cycle in range(2500):
                            ready = rng.randrange(4) != 0
                            yield reference.cmd.ready.eq(ready)
                            yield registered.cmd.ready.eq(ready)
                            yield
                            for field in ("valid", "last", "a", "ba", "cas", "ras", "we"):
                                self.assertEqual((yield getattr(reference.cmd, field)),
                                    (yield getattr(registered.cmd, field)), (cycle, field))
                            self.assertEqual((yield reference.timer.done), (yield registered.timer.done))
                            if (yield reference.cmd.cas) and (yield reference.cmd.ras):
                                refreshes += 1
                            if (yield reference.cmd.we) and not (yield reference.cmd.ras):
                                calibrations += 1
                        self.assertGreater(refreshes, 0)
                        if zqcs is not None:
                            self.assertGreater(calibrations, 0)
                    run_simulation(top, compare())
