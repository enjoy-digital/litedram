# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
# License: BSD

import unittest

from migen import *

from litex.gen.sim import run_simulation
from litex.soc.interconnect import stream

from litedram.common import *
from litedram.phy import dfi
from litedram.core.multiplexer import _CommandChooser, _Steerer, Multiplexer
from litedram.core.multiplexer import STEER_NOP, STEER_CMD, STEER_REQ, STEER_REFRESH


class CmdRequestRWDriver:
    def __init__(self, req, i=0, ep_layout=True, rw_layout=True):
        self.req = req
        self.rw_layout = rw_layout
        self.ep_layout = ep_layout

        # used to distinguish commands
        self.bank = i
        self.row  = i
        self.col  = i

    def _drive(self, **kwargs):
        signals = ["a", "ba", "cas", "ras", "we",]
        if self.rw_layout:
            signals += ["is_cmd", "is_read", "is_write"]
        if self.ep_layout:
            signals += ["valid", "first", "last"]
        for s in signals:
            yield getattr(self.req, s).eq(kwargs.get(s, 0))
        # drive ba even for nop
        if "ba" not in kwargs:
            yield self.req.ba.eq(self.bank)

    def activate(self):
        yield from self._drive(valid=1, is_cmd=1, ras=1, a=self.row, ba=self.bank)

    def precharge(self, all_banks=False):
        a = 0 if not all_banks else (1 << 10)
        yield from self._drive(valid=1, is_cmd=1, ras=1, we=1, a=a, ba=self.bank)

    def refresh(self):
        yield from self._drive(valid=1, is_cmd=1, cas=1, ras=1, ba=self.bank)

    def write(self, auto_precharge=False):
        assert not (self.col & (1 << 10))
        col = self.col | (1 << 10) if auto_precharge else self.col
        yield from self._drive(valid=1, is_write=1, cas=1, we=1, a=col, ba=self.bank)

    def read(self, auto_precharge=False):
        assert not (self.col & (1 << 10))
        col = self.col | (1 << 10) if auto_precharge else self.col
        yield from self._drive(valid=1, is_read=1, cas=1, a=col, ba=self.bank)

    def nop(self):
        yield from self._drive()

# _CommandChooser ----------------------------------------------------------------------------------

class CommandChooserDUT(Module):
    def __init__(self, n_requests, addressbits, bankbits):
        self.requests = [stream.Endpoint(cmd_request_rw_layout(a=addressbits, ba=bankbits))
                         for _ in range(n_requests)]
        self.submodules.chooser = _CommandChooser(self.requests)

        self.drivers = [CmdRequestRWDriver(req, i) for i, req in enumerate(self.requests)]

    def set_requests(self, description):
        assert len(description) == len(self.drivers)
        for driver, c in zip(self.drivers, description):
            method = {
                "w": driver.write,
                "r": driver.read,
                "a": driver.activate,
                "p": driver.precharge,
                "_": driver.nop,
            }[c]
            yield from method()


class TestCommandChooser(unittest.TestCase):
    def test_helper_methods_correct(self):
        # Verify that helper methods return correct values
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

            # create a subTest for each method
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

            # test accept helper
            with self.subTest(method="accept"):
                yield dut.chooser.want_writes.eq(1)
                yield

                yield from dut.set_requests("____")
                yield
                self.assertEqual((yield dut.chooser.accept()), 0)

                # set write request, this sets request.valid=1
                yield from dut.set_requests("w___")
                yield
                self.assertEqual((yield dut.chooser.accept()), 0)
                self.assertEqual((yield dut.chooser.cmd.valid), 1)

                # accept() is only on after we set cmd.ready=1
                yield dut.chooser.cmd.ready.eq(1)
                yield
                self.assertEqual((yield dut.chooser.accept()), 1)

        dut = CommandChooserDUT(n_requests=4, bankbits=3, addressbits=13)
        run_simulation(dut, main_generator(dut))

    def test_selects_next_when_request_not_valid(self):
        def main_generator(dut):
            yield dut.chooser.want_cmds.eq(1)
            yield from dut.set_requests("pppp")
            yield

            # advance to next request
            def invalidate(i):
                yield dut.requests[i].valid.eq(0)
                yield
                yield dut.requests[i].valid.eq(1)
                yield

            # first request is selected as it is valid and ~ready
            self.assertEqual((yield dut.chooser.cmd.ba), 0)
            yield
            self.assertEqual((yield dut.chooser.cmd.ba), 0)

            # after deactivating valid arbiter should choose next request
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
        def main_generator(dut):
            yield dut.chooser.want_cmds.eq(1)
            yield from dut.set_requests("pppp")
            yield

            # advance to next request
            def cmd_ready():
                yield dut.chooser.cmd.ready.eq(1)
                yield
                yield dut.chooser.cmd.ready.eq(0)
                yield

            # first request is selected as it is valid and ~ready
            self.assertEqual((yield dut.chooser.cmd.ba), 0)
            yield
            self.assertEqual((yield dut.chooser.cmd.ba), 0)

            # after deactivating valid arbiter should choose next request
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
                    # check that ba is as expected
                    selected_request_index = (yield dut.chooser.cmd.ba)
                    self.assertEqual(selected_request_index, int(expected_index), msg=error_msg)

                # advance to next request
                yield dut.chooser.cmd.ready.eq(1)
                yield
                yield dut.chooser.cmd.ready.eq(0)
                yield

        assert len(requests) == 8
        dut = CommandChooserDUT(n_requests=8, bankbits=3, addressbits=13)
        run_simulation(dut, main_generator(dut))

    def test_selects_nothing(self):
        # When want_* = 0, chooser should set cas/ras/we = 0, which means not valid request
        requests = "w_rawpwr"
        order = "____"  # cas/ras/we are never set
        self.selection_test(requests, order, wants=[])

    def test_selects_writes(self):
        requests = "w_rawpwr"
        order = "0460460"
        self.selection_test(requests, order, wants=["want_writes"])

    def test_selects_reads(self):
        requests = "rp_awrrw"
        order = "0560560"
        self.selection_test(requests, order, wants=["want_reads"])

    def test_selects_writes_and_reads(self):
        requests = "rp_awrrw"
        order = "04567045670"
        self.selection_test(requests, order, wants=["want_reads", "want_writes"])

    def test_selects_cmds_without_act(self):
        # When want_cmds = 1, but want_activates = 0, activate commands should not be selected
        requests = "pr_aa_pw"
        order = "06060"
        self.selection_test(requests, order, wants=["want_cmds"])

    def test_selects_cmds_with_act(self):
        # When want_cmds/activates = 1, both activate and precharge should be selected
        requests = "pr_aa_pw"
        order = "034603460"
        self.selection_test(requests, order, wants=["want_cmds", "want_activates"])

    def test_selects_nothing_when_want_activates_only(self):
        # When only want_activates = 1, nothing will be selected
        requests = "pr_aa_pw"
        order = "____"
        self.selection_test(requests, order, wants=["want_activates"])

    def test_selects_cmds_and_writes(self):
        requests = "pr_aa_pw"
        order = "0670670"
        self.selection_test(requests, order, wants=["want_cmds", "want_writes"])

# _Steerer -----------------------------------------------------------------------------------------

class SteererDUT(Module):
    def __init__(self, nranks, databits, nphases):
        a, ba = 13, 3
        nop = Record(cmd_request_layout(a=a, ba=ba))
        choose_cmd = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))
        choose_req = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))
        refresher_cmd = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))

        self.commands = [nop, choose_cmd, choose_req, refresher_cmd]
        self.dfi = dfi.Interface(addressbits=a, bankbits=ba, nranks=nranks, databits=databits,
                                 nphases=nphases)
        self.submodules.steerer = _Steerer(self.commands, self.dfi)

        # nop is not an endpoint and does not have is_* signals
        self.drivers = [CmdRequestRWDriver(req, i, ep_layout=i != 0, rw_layout=i != 0)
                        for i, req in enumerate(self.commands)]

class TestSteerer(unittest.TestCase):
    def test_nop_not_valid(self):
        # If NOP is selected then there should be no command selected on cas/ras/we

        def main_generator(dut):
            # nop on both phases
            yield dut.steerer.sel[0].eq(STEER_NOP)
            yield dut.steerer.sel[1].eq(STEER_NOP)
            yield from dut.drivers[0].nop()
            yield

            for i in range(2):
                cas_n = (yield dut.dfi.phases[i].cas_n)
                ras_n = (yield dut.dfi.phases[i].ras_n)
                we_n  = (yield dut.dfi.phases[i].we_n)
                self.assertEqual((cas_n, ras_n, we_n), (1, 1, 1))

        dut = SteererDUT(nranks=2, databits=16, nphases=2)
        run_simulation(dut, main_generator(dut))

    def test_connect_only_if_valid_and_ready(self):
        # Commands should be connected to phases only if they are valid & ready

        def main_generator(dut):
            # set possible requests
            yield from dut.drivers[STEER_NOP].nop()
            yield from dut.drivers[STEER_CMD].activate()
            yield from dut.drivers[STEER_REQ].write()
            yield from dut.drivers[STEER_REFRESH].refresh()
            # set how phases are steered
            yield dut.steerer.sel[0].eq(STEER_CMD)
            yield dut.steerer.sel[1].eq(STEER_NOP)
            yield
            yield

            def check(is_ready):
                # cmd on phase 0 should be STEER_CMD=activate
                p = dut.dfi.phases[0]
                self.assertEqual((yield p.bank),    STEER_CMD)
                self.assertEqual((yield p.address), STEER_CMD)
                if is_ready:
                    self.assertEqual((yield p.cas_n), 1)
                    self.assertEqual((yield p.ras_n), 0)
                    self.assertEqual((yield p.we_n),  1)
                else:  # not steered
                    self.assertEqual((yield p.cas_n), 1)
                    self.assertEqual((yield p.ras_n), 1)
                    self.assertEqual((yield p.we_n),  1)

                # nop on phase 1 should be STEER_NOP
                p = dut.dfi.phases[1]
                self.assertEqual((yield p.cas_n), 1)
                self.assertEqual((yield p.ras_n), 1)
                self.assertEqual((yield p.we_n),  1)

            yield from check(is_ready=False)
            yield dut.commands[STEER_CMD].ready.eq(1)
            yield
            yield
            yield from check(is_ready=True)

        dut = SteererDUT(nranks=2, databits=16, nphases=2)
        run_simulation(dut, main_generator(dut))

    def test_no_decode_ba_signle_rank(self):
        # With a single rank the whole `ba` signal is bank address

        def main_generator(dut):
            yield from dut.drivers[STEER_NOP].nop()
            yield from dut.drivers[STEER_REQ].write()
            yield from dut.drivers[STEER_REFRESH].refresh()
            # all the bits are for bank
            dut.drivers[STEER_CMD].bank = 0b110
            yield from dut.drivers[STEER_CMD].activate()
            yield dut.commands[STEER_CMD].ready.eq(1)
            # set how phases are steered
            yield dut.steerer.sel[0].eq(STEER_NOP)
            yield dut.steerer.sel[1].eq(STEER_CMD)
            yield
            yield

            p = dut.dfi.phases[1]
            self.assertEqual((yield p.cas_n),   1)
            self.assertEqual((yield p.ras_n),   0)
            self.assertEqual((yield p.we_n),    1)
            self.assertEqual((yield p.address), STEER_CMD)
            self.assertEqual((yield p.bank),    0b110)
            self.assertEqual((yield p.cs_n),    0)

        dut = SteererDUT(nranks=1, databits=16, nphases=2)
        run_simulation(dut, main_generator(dut))

    def test_decode_ba_multiple_ranks(self):
        # With multiple ranks `ba` signal should be split into bank and chip select

        def main_generator(dut):
            yield from dut.drivers[STEER_NOP].nop()
            yield from dut.drivers[STEER_REQ].write()
            yield from dut.drivers[STEER_REFRESH].refresh()
            # set how phases are steered
            yield dut.steerer.sel[0].eq(STEER_NOP)
            yield dut.steerer.sel[1].eq(STEER_CMD)

            variants = [
                # ba, phase.bank, phase.cs_n
                (0b110, 0b10, 0b01),  # rank=1 -> cs=0b10 -> cs_n=0b01
                (0b101, 0b01, 0b01),  # rank=1 -> cs=0b10 -> cs_n=0b01
                (0b001, 0b01, 0b10),  # rank=0 -> cs=0b01 -> cs_n=0b10
            ]
            for ba, phase_bank, phase_cs_n in variants:
                with self.subTest(ba=ba):
                    # 1 bit for rank, 2 bits for bank
                    dut.drivers[STEER_CMD].bank = ba
                    yield from dut.drivers[STEER_CMD].activate()
                    yield dut.commands[STEER_CMD].ready.eq(1)
                    yield
                    yield

                    p = dut.dfi.phases[1]
                    self.assertEqual((yield p.cas_n), 1)
                    self.assertEqual((yield p.ras_n), 0)
                    self.assertEqual((yield p.we_n),  1)
                    self.assertEqual((yield p.bank),  phase_bank)
                    self.assertEqual((yield p.cs_n),  phase_cs_n)


        dut = SteererDUT(nranks=2, databits=16, nphases=2)
        run_simulation(dut, main_generator(dut))

    def test_select_all_ranks_on_refresh(self):
        # When refresh command is on first phase, all ranks should be selected

        def main_generator(dut):
            yield from dut.drivers[STEER_NOP].nop()
            yield from dut.drivers[STEER_REQ].write()
            yield from dut.drivers[STEER_CMD].activate()
            # set how phases are steered
            yield dut.steerer.sel[0].eq(STEER_REFRESH)
            yield dut.steerer.sel[1].eq(STEER_NOP)

            variants = [
                # ba, phase.bank, phase.cs_n (always all enabled)
                (0b110, 0b10, 0b00),
                (0b101, 0b01, 0b00),
                (0b001, 0b01, 0b00),
            ]
            for ba, phase_bank, phase_cs_n in variants:
                with self.subTest(ba=ba):
                    # 1 bit for rank, 2 bits for bank
                    dut.drivers[STEER_REFRESH].bank = ba
                    yield from dut.drivers[STEER_REFRESH].refresh()
                    yield dut.commands[STEER_REFRESH].ready.eq(1)
                    yield
                    yield

                    p = dut.dfi.phases[0]
                    self.assertEqual((yield p.cas_n), 0)
                    self.assertEqual((yield p.ras_n), 0)
                    self.assertEqual((yield p.we_n),  1)
                    self.assertEqual((yield p.bank),  phase_bank)
                    self.assertEqual((yield p.cs_n),  phase_cs_n)

        dut = SteererDUT(nranks=2, databits=16, nphases=2)
        run_simulation(dut, main_generator(dut))

    def test_reset_n_high(self):
        # reset_n should be 1 for all phases at all times

        def main_generator(dut):
            yield dut.steerer.sel[0].eq(STEER_CMD)
            yield dut.steerer.sel[1].eq(STEER_NOP)
            yield

            self.assertEqual((yield dut.dfi.phases[0].reset_n), 1)
            self.assertEqual((yield dut.dfi.phases[1].reset_n), 1)
            self.assertEqual((yield dut.dfi.phases[2].reset_n), 1)
            self.assertEqual((yield dut.dfi.phases[3].reset_n), 1)

        dut = SteererDUT(nranks=2, databits=16, nphases=4)
        run_simulation(dut, main_generator(dut))

    def test_cke_high_all_ranks(self):
        # cke should be 1 for all phases and ranks at all times

        def main_generator(dut):
            yield dut.steerer.sel[0].eq(STEER_CMD)
            yield dut.steerer.sel[1].eq(STEER_NOP)
            yield

            self.assertEqual((yield dut.dfi.phases[0].cke), 0b11)
            self.assertEqual((yield dut.dfi.phases[1].cke), 0b11)
            self.assertEqual((yield dut.dfi.phases[2].cke), 0b11)
            self.assertEqual((yield dut.dfi.phases[3].cke), 0b11)

        dut = SteererDUT(nranks=2, databits=16, nphases=4)
        run_simulation(dut, main_generator(dut))

    def test_odt_high_all_ranks(self):
        # odt should be 1 for all phases and ranks at all times
        # NOTE: until dynamic odt is implemented

        def main_generator(dut):
            yield dut.steerer.sel[0].eq(STEER_CMD)
            yield dut.steerer.sel[1].eq(STEER_NOP)
            yield

            self.assertEqual((yield dut.dfi.phases[0].odt), 0b11)
            self.assertEqual((yield dut.dfi.phases[1].odt), 0b11)
            self.assertEqual((yield dut.dfi.phases[2].odt), 0b11)
            self.assertEqual((yield dut.dfi.phases[3].odt), 0b11)

        dut = SteererDUT(nranks=2, databits=16, nphases=4)
        run_simulation(dut, main_generator(dut))
