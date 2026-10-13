#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Regression coverage for fail-closed paired write masks."""

import unittest

from migen import passive
from litedram.common import LiteDRAMNativePort
from litedram.frontend.paired import PairedPort
from test.test_native_benchmark import simulate


class PairedAbortTest(unittest.TestCase):
    def test_invalid_first_middle_last(self):
        for invalid in range(3):
            with self.subTest(invalid=invalid):
                self.run_case(invalid)

    def test_zero_and_half_word_masks(self):
        for mask in (0, 0xffff, 0xffff0000):
            with self.subTest(mask=mask):
                self.run_case(1, mask)

    def test_invalid_data_can_arrive_before_address(self):
        ports = [LiteDRAMNativePort("write", 10, 128) for _ in range(2)]
        dut = PairedPort(ports, "write", depth=4)

        def main():
            yield dut.port.wdata.valid.eq(1)
            yield dut.port.wdata.we.eq(1)
            for _ in range(10):
                yield
                self.assertEqual((yield dut.error), 0)
                self.assertEqual((yield dut.port.wdata.ready), 0)
                self.assertEqual((yield dut.port.cmd.ready), 1)
            yield dut.port.cmd.valid.eq(1)
            yield
            yield dut.port.cmd.valid.eq(0)
            for _ in range(10):
                if (yield dut.port.wdata.ready):
                    break
                yield
            self.assertEqual((yield dut.port.wdata.ready), 1)
            yield dut.port.wdata.valid.eq(0)
            for _ in range(10):
                yield
            self.assertEqual((yield dut.error), 1)
            self.assertEqual((yield dut.drained), 1)
            for port in ports:
                self.assertEqual((yield port.cmd.valid), 0)
                self.assertEqual((yield port.wdata.valid), 0)

        simulate(dut, main())

    def run_case(self, invalid, mask=1):
        ports = [LiteDRAMNativePort("write", 10, 128) for _ in range(2)]
        dut = PairedPort(ports, "write", depth=8)
        commands = [[], []]
        data = [[], []]

        @passive
        def monitor():
            while True:
                for index, port in enumerate(ports):
                    if (yield port.cmd.valid) and (yield port.cmd.ready):
                        commands[index].append((yield port.cmd.addr))
                    if (yield port.wdata.valid) and (yield port.wdata.ready):
                        data[index].append(((yield port.wdata.we), (yield port.wdata.data)))
                yield

        def main():
            # Accept all addresses before the error. Data remains a separate
            # obligation, even when an accepted address must later be aborted.
            for address in range(3):
                yield dut.port.cmd.addr.eq(address)
                yield dut.port.cmd.valid.eq(1)
                yield
                self.assertEqual((yield dut.port.cmd.ready), 1)
            yield dut.port.cmd.valid.eq(0)
            # Asymmetric downstream progress: group 0 drains; group 1 retains
            # prior good commands and data until after the error is observed.
            yield ports[0].cmd.ready.eq(1)
            yield ports[0].wdata.ready.eq(1)
            for beat in range(3):
                yield dut.port.wdata.data.eq((beat + 1) | ((beat + 101) << 128))
                yield dut.port.wdata.we.eq(mask if beat == invalid else 0xffffffff)
                yield dut.port.wdata.valid.eq(1)
                yield
                for _ in range(40):
                    if (yield dut.port.wdata.ready):
                        break
                    yield
                self.assertEqual((yield dut.port.wdata.ready), 1)
                yield dut.port.wdata.valid.eq(0)
                yield
                if beat == invalid:
                    self.assertEqual((yield dut.error), 1)
                    self.assertEqual((yield dut.port.cmd.ready), 0)
                    if beat < 2 or invalid > 0:
                        self.assertEqual((yield dut.drained), 0)
                    # Pending accepted addresses keep drained low while their
                    # corresponding input data beats have not been provided.
                    for _ in range(9):
                        yield
                    if beat < 2:
                        self.assertEqual((yield dut.drained), 0)
            for _ in range(20):
                yield
            if invalid:
                self.assertEqual((yield dut.drained), 0)
            yield ports[1].wdata.ready.eq(1)
            for _ in range(20):
                yield
            if invalid:
                self.assertEqual((yield dut.drained), 0)
            yield ports[1].cmd.ready.eq(1)
            for _ in range(30):
                yield
            self.assertEqual((yield dut.drained), 1)
            self.assertEqual((yield dut.error), 1)
            self.assertEqual((yield dut.port.cmd.ready), 0)
            self.assertEqual(commands, [[2*i for i in range(invalid)],
                                        [2*i+1 for i in range(invalid)]])
            self.assertEqual(data, [[(0xffff, i+1) for i in range(invalid)],
                                    [(0xffff, i+101) for i in range(invalid)]])

        simulate(dut, [main(), monitor()])
