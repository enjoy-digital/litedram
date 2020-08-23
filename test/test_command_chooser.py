#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from litex.soc.interconnect import stream

from litedram.common import *
from litedram.core.multiplexer import _CommandChooser

from test.common import CmdRequestRWDriver


class CommandChooserDUT(Module):
    def __init__(self, n_requests, addressbits, bankbits):
        self.requests = [stream.Endpoint(cmd_request_rw_layout(a=addressbits, ba=bankbits))
                         for _ in range(n_requests)]
        self.submodules.chooser = _CommandChooser(self.requests)

        self.drivers = [CmdRequestRWDriver(req, i) for i, req in enumerate(self.requests)]

    def set_requests(self, description):
        assert len(description) == len(self.drivers)
        for driver, char in zip(self.drivers, description):
            yield from driver.request(char)


class TestCommandChooser(unittest.TestCase):
    def test_helper_methods_correct(self):
        # Verify that helper methods return correct values.
        def main_generator(dut):
            possible_cmds     = "_rwap"
            expected_read     = "01000"
            expected_write    = "00100"
            expected_activate = "00010"
            helper_methods = {
                "write": expected_write,
                "read": expected_read,
                "activate": expected_activate,
            }

            # Create a subTest for each method
            for method, expected_values in helper_methods.items():
                with self.subTest(method=method):
                    # Set each available command as the first request and verify
                    # that the helper method returns the correct value. We can
                    # safely use only the first request because no requests are
                    # valid as all the want_* signals are 0.
                    for cmd, expected in zip(possible_cmds, expected_values):
                        yield from dut.set_requests(f"{cmd}___")
                        yield
                        method_value = (yield getattr(dut.chooser, method)())
                        self.assertEqual(method_value, int(expected))

            # Test accept helper
            with self.subTest(method="accept"):
                yield dut.chooser.want_writes.eq(1)
                yield

                yield from dut.set_requests("____")
                yield
                self.assertEqual((yield dut.chooser.accept()), 0)

                # Set write request, this sets request.valid=1
                yield from dut.set_requests("w___")
                yield
                self.assertEqual((yield dut.chooser.accept()), 0)
                self.assertEqual((yield dut.chooser.cmd.valid), 1)

                # Accept() is only on after we set cmd.ready=1
                yield dut.chooser.cmd.ready.eq(1)
                yield
                self.assertEqual((yield dut.chooser.accept()), 1)

        dut = CommandChooserDUT(n_requests=4, bankbits=3, addressbits=13)
        run_simulation(dut, main_generator(dut))

    def test_selects_next_when_request_not_valid(self):
        # Verify that arbiter moves to next request when valid goes inactive.
        def main_generator(dut):
            yield dut.chooser.want_cmds.eq(1)
            yield from dut.set_requests("pppp")
            yield

            # Advance to next request
            def invalidate(i):
                yield dut.requests[i].valid.eq(0)
                yield
                yield dut.requests[i].valid.eq(1)
                yield

            # First request is selected as it is valid and ~ready
            self.assertEqual((yield dut.chooser.cmd.ba), 0)
            yield
            self.assertEqual((yield dut.chooser.cmd.ba), 0)

            # After deactivating `valid`, arbiter should choose next request
            yield from invalidate(0)
            self.assertEqual((yield dut.chooser.cmd.ba), 1)
            yield from invalidate(1)
            self.assertEqual((yield dut.chooser.cmd.ba), 2)
            yield from invalidate(2)
            self.assertEqual((yield dut.chooser.cmd.ba), 3)
            yield from invalidate(3)
            self.assertEqual((yield dut.chooser.cmd.ba), 0)

        dut = CommandChooserDUT(n_requests=4, bankbits=3, addressbits=13)
        run_simulation(dut, main_generator(dut))

    def test_selects_next_when_cmd_ready(self):
        # Verify that next request is chosen when the current one becomes ready.
        def main_generator(dut):
            yield dut.chooser.want_cmds.eq(1)
            yield from dut.set_requests("pppp")
            yield

            # Advance to next request
            def cmd_ready():
                yield dut.chooser.cmd.ready.eq(1)
                yield
                yield dut.chooser.cmd.ready.eq(0)
                yield

            # First request is selected as it is valid and ~ready
            self.assertEqual((yield dut.chooser.cmd.ba), 0)
            yield
            self.assertEqual((yield dut.chooser.cmd.ba), 0)

            # After deactivating valid arbiter should choose next request
            yield from cmd_ready()
            self.assertEqual((yield dut.chooser.cmd.ba), 1)
            yield from cmd_ready()
            self.assertEqual((yield dut.chooser.cmd.ba), 2)
            yield from cmd_ready()
            self.assertEqual((yield dut.chooser.cmd.ba), 3)
            yield from cmd_ready()
            self.assertEqual((yield dut.chooser.cmd.ba), 0)

        dut = CommandChooserDUT(n_requests=4, bankbits=3, addressbits=13)
        run_simulation(dut, main_generator(dut))

    def selection_test(self, requests, expected_order, wants):
        # Set requests to given states and tests whether they are being connected
        # to chooser.cmd in the expected order. Using `ba` value to distinguish
        # requests (as initialised in CommandChooserDUT).
        # "_" means no valid request.
        def main_generator(dut):
            for want in wants:
                yield getattr(dut.chooser, want).eq(1)

            yield from dut.set_requests(requests)
            yield

            for i, expected_index in enumerate(expected_order):
                error_msg = f"requests={requests}, expected_order={expected_order}, i={i}"
                if expected_index == "_":  # not valid - cas/ras/we should be 0
                    cas = (yield dut.chooser.cmd.cas)
                    ras = (yield dut.chooser.cmd.ras)
                    we = (yield dut.chooser.cmd.we)
                    self.assertEqual((cas, ras, we), (0, 0, 0), msg=error_msg)
                else:
                    # Check that ba is as expected
                    selected_request_index = (yield dut.chooser.cmd.ba)
                    self.assertEqual(selected_request_index, int(expected_index), msg=error_msg)

                # Advance to next request
                yield dut.chooser.cmd.ready.eq(1)
                yield
                yield dut.chooser.cmd.ready.eq(0)
                yield

        assert len(requests) == 8
        dut = CommandChooserDUT(n_requests=8, bankbits=3, addressbits=13)
        run_simulation(dut, main_generator(dut))

    @unittest.skip("Issue #174")
    def test_selects_nothing(self):
        # When want_* = 0, chooser should set cas/ras/we = 0, which means not valid request
        requests = "w_rawpwr"
        order    = "____"  # cas/ras/we are never set
        self.selection_test(requests, order, wants=[])

    def test_selects_writes(self):
        requests = "w_rawpwr"
        order    = "0460460"
        self.selection_test(requests, order, wants=["want_writes"])

    def test_selects_reads(self):
        requests = "rp_awrrw"
        order    = "0560560"
        self.selection_test(requests, order, wants=["want_reads"])

    @unittest.skip("Issue #174")
    def test_selects_writes_and_reads(self):
        requests = "rp_awrrw"
        order    = "04567045670"
        self.selection_test(requests, order, wants=["want_reads", "want_writes"])

    @unittest.skip("Issue #174")
    def test_selects_cmds_without_act(self):
        # When want_cmds = 1, but want_activates = 0, activate commands should not be selected
        requests = "pr_aa_pw"
        order    = "06060"
        self.selection_test(requests, order, wants=["want_cmds"])

    def test_selects_cmds_with_act(self):
        # When want_cmds/activates = 1, both activate and precharge should be selected
        requests = "pr_aa_pw"
        order    = "034603460"
        self.selection_test(requests, order, wants=["want_cmds", "want_activates"])

    @unittest.skip("Issue #174")
    def test_selects_nothing_when_want_activates_only(self):
        # When only want_activates = 1, nothing will be selected
        requests = "pr_aa_pw"
        order    = "____"
        self.selection_test(requests, order, wants=["want_activates"])

    def test_selects_cmds_and_writes(self):
        requests = "pr_aa_pw"
        order    = "0670670"
        self.selection_test(requests, order, wants=["want_cmds", "want_writes"])
