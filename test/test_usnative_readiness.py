#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Calibration permission, readiness loss and explicit re-arming behavior."""

import unittest
from migen.sim import run_simulation
from litedram.phy.usnative.readiness import NativeCalibrationGuard


class TestNativeCalibrationGuard(unittest.TestCase):
    def test_loss_requires_fresh_calibration(self):
        dut = NativeCalibrationGuard()
        def process():
            yield dut.native_ready.eq(1)
            yield
            yield
            self.assertEqual((yield dut.allowed), 0)
            yield dut.commit.eq(1)
            yield
            yield
            self.assertEqual((yield dut.allowed), 1)
            yield dut.native_ready.eq(0)
            yield
            self.assertEqual((yield dut.allowed), 0)
            yield
            self.assertEqual((yield dut.fault), 1)
            yield dut.native_ready.eq(1)
            yield dut.clear_fault.eq(1)
            yield
            yield
            self.assertEqual((yield dut.allowed), 0)
            self.assertEqual((yield dut.fault), 0)
            # A commit held across the fault must never count as a new success.
            yield dut.commit.eq(0)
            yield
            yield dut.commit.eq(1)
            yield
            yield
            self.assertEqual((yield dut.allowed), 1)
        run_simulation(dut, process())

    def test_retrain_and_fault_priorities(self):
        dut = NativeCalibrationGuard()
        def process():
            yield dut.native_ready.eq(1)
            yield dut.commit.eq(1)
            yield dut.retrain.eq(1)
            yield
            yield
            self.assertEqual((yield dut.allowed), 0)
            yield dut.retrain.eq(0)
            yield
            yield
            self.assertEqual((yield dut.allowed), 0)
            yield dut.commit.eq(0)
            yield
            yield dut.commit.eq(1)
            yield
            yield
            self.assertEqual((yield dut.allowed), 1)
            yield dut.clear_fault.eq(1)
            yield dut.native_ready.eq(0)
            yield
            yield
            self.assertEqual((yield dut.fault), 1)
            self.assertEqual((yield dut.calibrated), 0)
        run_simulation(dut, process())
