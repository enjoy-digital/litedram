#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Invalidate calibration permission when synchronized native readiness is lost."""
from migen import If, Module, Signal


class NativeCalibrationGuard(Module):
    """Sticky permission armed only by a new successful calibration event.

    Inputs must already be synchronized into this module's clock domain.
    ``commit`` is a one-cycle pulse after calibration AND controller memtest.
    A stale level or restored PLL readiness cannot automatically re-arm traffic.
    This permission must gate command admission; it cannot repair in-flight
    transactions. The caller must quiesce/reset the controller before retraining.
    ``clear_fault`` affects diagnostics only; it never grants permission.
    """
    def __init__(self):
        self.native_ready = Signal()
        self.retrain = Signal()
        self.commit = Signal()
        self.clear_fault = Signal()
        self.allowed = Signal()
        self.fault = Signal()
        self.calibrated = Signal()
        # Require a new rising edge: a held commit cannot restore permission
        # after readiness drops and later returns.
        previous_commit = Signal()
        self.sync += previous_commit.eq(self.commit)
        self.comb += self.allowed.eq(self.calibrated & self.native_ready & ~self.retrain)
        self.sync += [
            If(~self.native_ready | self.retrain,
                self.calibrated.eq(0)
            ).Elif(self.commit & ~previous_commit,
                self.calibrated.eq(1)
            ),
            If(self.calibrated & ~self.native_ready,
                self.fault.eq(1)
            ).Elif(self.clear_fault,
                self.fault.eq(0)
            )
        ]
