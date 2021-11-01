# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *

from litedram.phy.sim_utils import PulseTiming

class TestSimUtils(unittest.TestCase):
    def pulse_timing_test(self, dut, *, trigger, ready, ready_p, generators=None):
        generators = generators or []
        assert len(trigger) == len(ready) == len(ready_p)

        ready_hist = ""
        ready_p_hist = ""

        def generator():
            nonlocal ready_hist, ready_p_hist
            for i in range(len(trigger)):
                yield dut.trigger.eq(int(trigger[i]))
                yield
                ready_hist += str((yield dut.ready))
                ready_p_hist += str((yield dut.ready_p))

        run_simulation(dut, [generator(), *generators])
        self.assertEqual(ready_hist, ready)
        self.assertEqual(ready_p_hist, ready_p)

    def test_pulse_timing_basic(self):
        self.pulse_timing_test(PulseTiming(4),
            trigger = "01000000",
            ready   = "00000111",
            ready_p = "00000100",
        )

    def test_pulse_timing_1(self):
        self.pulse_timing_test(PulseTiming(1),
            trigger = "01000000",
            ready   = "00111111",
            ready_p = "00100000",
        )

    def test_pulse_timing_0(self):
        self.pulse_timing_test(PulseTiming(0),
            trigger = "01000000",
            ready   = "01111111",
            ready_p = "01000000",
        )

    def pulse_timing_signal_test(self, t, **kwargs):
        class Dut(PulseTiming):
            def __init__(self):
                self.t = Signal(3)
                super().__init__(self.t)
        dut = Dut()
        def generator():
            yield
            yield dut.t.eq(t)
            yield
        self.pulse_timing_test(dut, generators=[generator()], **kwargs)

    def test_pulse_timing_signal(self):
        self.pulse_timing_signal_test(
            t       = 4,
            trigger = "00100000000000000",
            ready   = "00000011111111111",
            ready_p = "00000010000000000",
        )

    def test_pulse_timing_signal_1(self):
        self.pulse_timing_signal_test(
            t       = 1,
            trigger = "00100000000000000",
            ready   = "00011111111111111",
            ready_p = "00010000000000000",
        )

    def test_pulse_timing_signal_0(self):
        self.pulse_timing_signal_test(
            t       = 0,
            trigger = "00100000000000000",
            ready   = "00111111111111111",
            ready_p = "00100000000000000",
        )
