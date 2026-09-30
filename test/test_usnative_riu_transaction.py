#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""RIU request/response handshake, timeout and reset-cancellation behavior."""

import unittest
from migen import *
from migen.sim import run_simulation, passive
from litedram.phy.usnative.riu_transaction import RIUTransaction

class RIUTest(unittest.TestCase):
    def test_single_control_construction(self):
        self.assertEqual(len(RIUTransaction(1, [0], timeout=4).native_select), 1)
    def test_invalid_configuration(self):
        for controls, indices, timeout in ((0, [], 32), (2, [0], 32),
                                           (2, [0, -1], 32), (1, [0], 3)):
            with self.assertRaises(ValueError):
                RIUTransaction(controls, indices, timeout=timeout)

    def test_transactions(self):
        dut = RIUTransaction(3, [0, 0, 1], timeout=32)
        writes = []
        @passive
        def native():
            value = 0x1234
            while True:
                if (yield dut.native_write):
                    writes.append(((yield dut.native_address), (yield dut.native_wdata), (yield dut.native_select)))
                    value = (yield dut.native_wdata)
                yield dut.native_valid.eq(3)
                yield dut.native_rdata.eq(value | (0xabcd<<16))
                yield
        def driver():
            for _ in range(8):
                yield
            self.assertEqual((yield dut.valid), 0)
            self.assertEqual((yield dut.error), 0)
            yield dut.select.eq(1)
            yield dut.address.eq(0x30)
            yield dut.wdata.eq(0xbeef)
            yield dut.write.eq(1)
            yield dut.request.eq(1)
            yield
            yield dut.request.eq(0)
            yield
            self.assertEqual((yield dut.busy), 1)
            yield dut.wdata.eq(0x9999)
            yield dut.address.eq(7)
            yield dut.select.eq(2)
            for _ in range(4):
                yield
            yield dut.request.eq(1)
            yield
            yield dut.request.eq(0)
            for _ in range(100):
                yield
            self.assertEqual(writes, [(0x30, 0xbeef, 2)])
            self.assertEqual((yield dut.rdata), 0xbeef)
            self.assertEqual((yield dut.valid), 1)
            self.assertEqual((yield dut.error), 1)
            # Next request clears old success and captures the newly selected byte.
            yield dut.write.eq(0)
            yield dut.request.eq(1)
            yield
            yield dut.request.eq(0)
            yield
            self.assertEqual((yield dut.valid), 0)
            for _ in range(100):
                yield
            self.assertEqual((yield dut.rdata), 0xabcd)
            self.assertEqual((yield dut.error), 0)
            # Reset after completed acknowledgment clears old data validity.
            yield dut.reset.eq(1)
            for _ in range(8):
                yield
            self.assertEqual((yield dut.valid), 0)
            yield dut.reset.eq(0)
            for _ in range(8):
                yield
            # Cancel during request: no old response can become valid later.
            yield dut.request.eq(1)
            yield
            yield dut.request.eq(0)
            yield dut.reset.eq(1)
            for _ in range(100):
                yield
            yield dut.reset.eq(0)
            for _ in range(20):
                yield
            self.assertEqual((yield dut.busy), 0)
            self.assertEqual((yield dut.valid), 0)
        run_simulation(dut, {'sys':driver(), 'riu':native()}, clocks={'sys':10, 'riu':20})
    def test_waits_for_native_ready(self):
        dut = RIUTransaction(3, [0, 0, 1], timeout=64)
        def driver():
            yield dut.write.eq(1)
            yield dut.wdata.eq(0xbeef)
            yield dut.request.eq(1)
            yield
            yield dut.request.eq(0)
            for _ in range(30):
                yield
                self.assertEqual((yield dut.native_write), 0)
            self.assertEqual((yield dut.busy), 1)
            yield dut.native_valid.eq(3)
            yield dut.native_rdata.eq(0xbeef)
            high = 0
            for _ in range(100):
                yield
                high += (yield dut.native_write)
            # One RIU pulse is two sys samples at the exact2:1 ratio.
            self.assertEqual(high, 2)
            self.assertEqual((yield dut.valid), 1)
            self.assertEqual((yield dut.rdata), 0xbeef)
        run_simulation(dut, {'sys':driver()}, clocks={'sys':10, 'riu':20})
    def test_timeout_invalid(self):
        dut = RIUTransaction(3, [0, 0, 1], timeout=8)
        def driver():
            yield dut.request.eq(1)
            yield
            yield dut.request.eq(0)
            for _ in range(100):
                yield
            self.assertEqual((yield dut.busy), 0)
            self.assertEqual((yield dut.valid), 0)
            self.assertEqual((yield dut.error), 1)
            yield dut.select.eq(3)
            yield dut.request.eq(1)
            yield
            yield dut.request.eq(0)
            for _ in range(50):
                yield
            self.assertEqual((yield dut.busy), 0)
            self.assertEqual((yield dut.valid), 0)
            self.assertEqual((yield dut.error), 1)
            # A valid request after timeout/rejection must recover normally.
            yield dut.select.eq(0)
            yield dut.native_valid.eq(1)
            yield dut.native_rdata.eq(0x6543)
            yield dut.request.eq(1)
            yield
            yield dut.request.eq(0)
            for _ in range(80):
                yield
            self.assertEqual((yield dut.valid), 1)
            self.assertEqual((yield dut.error), 0)
            self.assertEqual((yield dut.rdata), 0x6543)
        run_simulation(dut, {'sys':driver()}, clocks={'sys':10, 'riu':20})
if __name__=='__main__':
    unittest.main()
