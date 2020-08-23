#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import random
import unittest
import itertools
import collections

from migen import *

from litex.soc.interconnect import stream

from litedram.common import *
from litedram.core.bandwidth import Bandwidth

from test.common import timeout_generator, CmdRequestRWDriver


class BandwidthDUT(Module):
    def __init__(self, data_width=8, **kwargs):
        a, ba = 13, 3
        self.cmd = stream.Endpoint(cmd_request_rw_layout(a, ba))
        self.submodules.bandwidth = Bandwidth(self.cmd, data_width, **kwargs)


class CommandDriver:
    def __init__(self, cmd, cmd_options=None):
        self.cmd = cmd
        self.driver = CmdRequestRWDriver(cmd)
        self.cmd_counts = collections.defaultdict(int)

    @passive
    def random_generator(self, random_ready_max=20, commands=None):
        commands = commands or ["read", "write"]
        prng = random.Random(42)

        while True:
            # Generate random command
            command = prng.choice(commands)
            yield from getattr(self.driver, command)()
            yield
            # Wait some times before it becomes ready
            for _ in range(prng.randint(0, random_ready_max)):
                yield
            yield self.cmd.ready.eq(1)
            yield
            self.cmd_counts[command] += 1
            yield self.cmd.ready.eq(0)
            # Disable command
            yield from self.driver.nop()
            yield

    @passive
    def timeline_generator(self, timeline):
        # Timeline: an iterator of tuples (cycle, command)
        sim_cycle = 0
        for cycle, command in timeline:
            assert cycle >= sim_cycle
            while sim_cycle != cycle:
                sim_cycle += 1
                yield
            # Set the command
            yield from getattr(self.driver, command)()
            yield self.cmd.ready.eq(1)
            self.cmd_counts[command] += 1
            # Advance 1 cycle
            yield
            sim_cycle += 1
            # Clear state
            yield self.cmd.ready.eq(0)
            yield from self.driver.nop()


class TestBandwidth(unittest.TestCase):
    def test_can_read_status_data_width(self):
        # Verify that data width can be read from a CSR.
        def test(data_width):
            def main_generator(dut):
                yield
                self.assertEqual((yield dut.bandwidth.data_width.status), data_width)

            dut = BandwidthDUT(data_width=data_width)
            run_simulation(dut, main_generator(dut))

        for data_width in [8, 16, 32, 64]:
            with self.subTest(data_width=data_width):
                test(data_width)

    def test_requires_update_to_copy_the_data(self):
        # Verify that command counts are copied to CSRs only after `update`.
        def main_generator(dut):
            nreads  = (yield from dut.bandwidth.nreads.read())
            nwrites = (yield from dut.bandwidth.nwrites.read())
            self.assertEqual(nreads, 0)
            self.assertEqual(nwrites, 0)

            # Wait enough for the period to end
            for _ in range(2**6):
                yield

            nreads  = (yield from dut.bandwidth.nreads.read())
            nwrites = (yield from dut.bandwidth.nwrites.read())
            self.assertEqual(nreads, 0)
            self.assertEqual(nwrites, 0)

            # Update register values
            yield from dut.bandwidth.update.write(1)

            nreads  = (yield from dut.bandwidth.nreads.read())
            nwrites = (yield from dut.bandwidth.nwrites.read())
            self.assertNotEqual((nreads, nwrites), (0, 0))

        dut = BandwidthDUT(period_bits=6)
        cmd_driver = CommandDriver(dut.cmd)
        generators = [
            main_generator(dut),
            cmd_driver.random_generator(),
        ]
        run_simulation(dut, generators)

    def test_correct_read_write_counts(self):
        # Verify that the number of registered READ/WRITE commands is correct.
        results = {}

        def main_generator(dut):
            # Wait for the first period to end
            for _ in range(2**8):
                yield
            yield from dut.bandwidth.update.write(1)
            yield
            results["nreads"]  = (yield from dut.bandwidth.nreads.read())
            results["nwrites"] = (yield from dut.bandwidth.nwrites.read())

        dut = BandwidthDUT(period_bits=8)
        cmd_driver = CommandDriver(dut.cmd)
        generators = [
            main_generator(dut),
            cmd_driver.random_generator(),
        ]
        run_simulation(dut, generators)

        self.assertEqual(results["nreads"], cmd_driver.cmd_counts["read"])

    def test_counts_read_write_only(self):
        # Verify that only READ and WRITE commands are registered.
        results = {}

        def main_generator(dut):
            # Wait for the first period to end
            for _ in range(2**8):
                yield
            yield from dut.bandwidth.update.write(1)
            yield
            results["nreads"] = (yield from dut.bandwidth.nreads.read())
            results["nwrites"] = (yield from dut.bandwidth.nwrites.read())

        dut = BandwidthDUT(period_bits=8)
        cmd_driver = CommandDriver(dut.cmd)
        commands   = ["read", "write", "activate", "precharge", "refresh"]
        generators = [
            main_generator(dut),
            cmd_driver.random_generator(commands=commands),
        ]
        run_simulation(dut, generators)

        self.assertEqual(results["nreads"], cmd_driver.cmd_counts["read"])

    def test_correct_period_length(self):
        # Verify that period length is correct by measuring time between CSR changes.
        period_bits = 5
        period = 2**period_bits

        n_per_period = {0: 3, 1: 6, 2: 9}
        timeline = {}
        for p, n in n_per_period.items():
            for i in range(n):
                margin = 10
                timeline[period*p + margin + i] = "write"

        def main_generator(dut):
            # Keep the values always up to date
            yield dut.bandwidth.update.re.eq(1)

            # Wait until we have the data from 1st period
            while (yield dut.bandwidth.nwrites.status) != 3:
                yield

            # Count time to next period
            cycles = 0
            while (yield dut.bandwidth.nwrites.status) != 6:
                cycles += 1
                yield

            self.assertEqual(cycles, period)

        dut = BandwidthDUT(period_bits=period_bits)
        cmd_driver = CommandDriver(dut.cmd)
        generators = [
            main_generator(dut),
            cmd_driver.timeline_generator(timeline.items()),
            timeout_generator(period * 3),
        ]
        run_simulation(dut, generators)

    def test_not_missing_commands_on_period_boundary(self):
        # Verify that no data is lost in the cycle when new period starts.
        period_bits = 5
        period = 2**period_bits

        # Start 10 cycles before period ends, end 10 cycles after it ends
        base = period - 10
        nwrites = 20
        timeline = {base + i: "write" for i in range(nwrites)}

        def main_generator(dut):
            # Wait until 1st period ends (+ some margin)
            for _ in range(period + 10):
                yield

            # Read the count from 1st period
            yield from dut.bandwidth.update.write(1)
            yield
            nwrites_registered = (yield from dut.bandwidth.nwrites.read())

            # Wait until 2nd period ends
            for _ in range(period):
                yield

            # Read the count from 1st period
            yield from dut.bandwidth.update.write(1)
            yield
            nwrites_registered += (yield from dut.bandwidth.nwrites.read())

            self.assertEqual(nwrites_registered, nwrites)

        dut = BandwidthDUT(period_bits=period_bits)
        cmd_driver = CommandDriver(dut.cmd)
        generators = [
            main_generator(dut),
            cmd_driver.timeline_generator(timeline.items()),
        ]
        run_simulation(dut, generators)
