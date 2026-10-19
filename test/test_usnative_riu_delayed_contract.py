#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Behavioral contract fixture, not an encrypted vendor model or hardware test.

UG571: writes update the RIU register later; reads return register contents one
RIU clock later. RIU_VALID indicates write acceptance/completion, not read-data
freshness. Delayed collision length is deliberately arbitrary for stress.
"""

import sys
import unittest

from pathlib import Path

from migen import Module, Signal, If
from migen.sim import run_simulation
from litedram.phy.usnative.riu_transaction import RIUTransaction


class DelayedNative(Module):
    def __init__(self, delay):
        self.submodules.bridge = b = RIUTransaction(2, [0, 0], timeout=64)
        pending = Signal(max=delay+2)
        shadow = Signal(16)
        register = Signal(16, reset=0x1234)
        readback = Signal(16)
        self.comb += [b.native_valid.eq(pending == 0), b.native_rdata.eq(readback)]
        self.sync.riu += [
            If(b.native_write & (b.native_select != 0),
                shadow.eq(b.native_wdata), pending.eq(delay)),
            If(pending != 0,
                If(pending == 1, register.eq(shadow)), pending.eq(pending-1)),
            If((b.native_select != 0) & ~b.native_write,
                readback.eq(register)).Else(readback.eq(0)),
        ]


class DelayedContractTests(unittest.TestCase):
    def exercise(self, delay):
        top = DelayedNative(delay)
        b = top.bridge
        result = {}
        def driver():
            for _ in range(10):
                yield
            yield b.select.eq(0)
            yield b.address.eq(0x30)
            yield b.wdata.eq(0xbeef)
            yield b.write.eq(1)
            yield b.request.eq(1)
            yield
            yield b.request.eq(0)
            for _ in range(200):
                yield
            result.update(valid=(yield b.valid), error=(yield b.error), data=(yield b.rdata))
        run_simulation(top, driver(), clocks={'sys':10, 'riu':20})
        self.assertEqual(result['valid'], 1)
        self.assertEqual(result['error'], 0)
        self.assertEqual(result['data'], 0xbeef,
            f"delay={delay}: completion sampled stale readback {result['data']:#x}")

    def test_normal_two_cycle_write(self):
        self.exercise(2)

    def test_delayed_twelve_cycle_write(self):
        self.exercise(12)


if __name__ == '__main__':
    unittest.main()
