# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
# License: BSD

import copy
import random
import unittest
from functools import partial
from collections import namedtuple

from migen import *

from litex.soc.interconnect import stream

from litedram.common import *
from litedram.phy import dfi
from litedram.core.multiplexer import _CommandChooser, _Steerer, Multiplexer
from litedram.core.multiplexer import STEER_NOP, STEER_CMD, STEER_REQ, STEER_REFRESH

# load after "* imports" to avoid using Migen version of vcd.py
from litex.gen.sim import run_simulation

from test.common import timeout_generator


class CmdRequestRWDriver:
    """Simple driver for Endpoint(cmd_request_rw_layout())"""
    def __init__(self, req, i=0, ep_layout=True, rw_layout=True):
        self.req = req
        self.rw_layout = rw_layout  # if False, omit is_* signals
        self.ep_layout = ep_layout  # if False, omit endpoint signals (valid, etc.)

        # used to distinguish commands
        self.i = self.bank = self.row = self.col = i

    def request(self, char):
        # convert character to matching command invocation
        return {
            "w": self.write,
            "r": self.read,
            "W": partial(self.write, auto_precharge=True),
            "R": partial(self.read, auto_precharge=True),
            "a": self.activate,
            "p": self.precharge,
            "f": self.refresh,
            "_": self.nop,
        }[char]()

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

    def _drive(self, **kwargs):
        signals = ["a", "ba", "cas", "ras", "we"]
        if self.rw_layout:
            signals += ["is_cmd", "is_read", "is_write"]
        if self.ep_layout:
            signals += ["valid", "first", "last"]
        for s in signals:
            yield getattr(self.req, s).eq(kwargs.get(s, 0))
        # drive ba even for nop, to be able to distinguish bank machines anyway
        if "ba" not in kwargs:
            yield self.req.ba.eq(self.bank)


def dfi_cmd_to_char(cas_n, ras_n, we_n):
    return {
        (1, 1, 1): "_",
        (0, 1, 0): "w",
        (0, 1, 1): "r",
        (1, 0, 1): "a",
        (1, 0, 0): "p",
        (0, 0, 1): "f",
    }[(cas_n, ras_n, we_n)]

# _CommandChooser ----------------------------------------------------------------------------------

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
        # Verify that arbiter moves to next request when valid goes inactive
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

            # after deactivating `valid`, arbiter should choose next request
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
        # Verify that next request is chosen when the current one becomes ready
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
    def __init__(self, nranks, dfi_databits, nphases):
        a, ba = 13, 3
        nop = Record(cmd_request_layout(a=a, ba=ba))
        choose_cmd = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))
        choose_req = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))
        refresher_cmd = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))

        self.commands = [nop, choose_cmd, choose_req, refresher_cmd]
        self.dfi = dfi.Interface(addressbits=a, bankbits=ba, nranks=nranks, databits=dfi_databits,
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

        dut = SteererDUT(nranks=2, dfi_databits=16, nphases=2)
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

        dut = SteererDUT(nranks=2, dfi_databits=16, nphases=2)
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

        dut = SteererDUT(nranks=1, dfi_databits=16, nphases=2)
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

        dut = SteererDUT(nranks=2, dfi_databits=16, nphases=2)
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

        dut = SteererDUT(nranks=2, dfi_databits=16, nphases=2)
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

        dut = SteererDUT(nranks=2, dfi_databits=16, nphases=4)
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

        dut = SteererDUT(nranks=2, dfi_databits=16, nphases=4)
        run_simulation(dut, main_generator(dut))

    def test_odt_high_all_ranks(self):
        # odt should be 1 for all phases and ranks at all times
        # NOTE: only until dynamic odt is implemented
        def main_generator(dut):
            yield dut.steerer.sel[0].eq(STEER_CMD)
            yield dut.steerer.sel[1].eq(STEER_NOP)
            yield

            self.assertEqual((yield dut.dfi.phases[0].odt), 0b11)
            self.assertEqual((yield dut.dfi.phases[1].odt), 0b11)
            self.assertEqual((yield dut.dfi.phases[2].odt), 0b11)
            self.assertEqual((yield dut.dfi.phases[3].odt), 0b11)

        dut = SteererDUT(nranks=2, dfi_databits=16, nphases=4)
        run_simulation(dut, main_generator(dut))

# Multiplexer --------------------------------------------------------------------------------------

class BankMachineStub:
    def __init__(self, babits, abits):
        self.cmd = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))
        self.refresh_req = Signal()
        self.refresh_gnt = Signal()


class RefresherStub:
    def __init__(self, babits, abits):
        self.cmd = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))


class MultiplexerDUT(Module):
    # define default settings that can be overwritten in specific tests
    # use only these settings that we actually need for Multiplexer
    default_controller_settings = dict(
        read_time=32,
        write_time=16,
        with_bandwidth=False,
    )
    default_phy_settings = dict(
        nphases=2,
        rdphase=0,
        wrphase=1,
        rdcmdphase=1,
        wrcmdphase=0,
        read_latency=5,
        cwl=3,
        # indirectly
        nranks=1,
        databits=16,
        dfi_databits=2*16,
        memtype="DDR2",
    )
    default_geom_settings = dict(
        bankbits=3,
        rowbits=13,
        colbits=10,
    )
    default_timing_settings = dict(
        tWTR=2,
        tFAW=None,
        tCCD=1,
        tRRD=None,
    )

    def __init__(self, controller_settings=None, phy_settings=None, geom_settings=None,
                 timing_settings=None):
        # update settings if provided
        def updated(settings, update):
            copy = settings.copy()
            copy.update(update or {})
            return copy

        controller_settings = updated(self.default_controller_settings, controller_settings)
        phy_settings        = updated(self.default_phy_settings, phy_settings)
        geom_settings       = updated(self.default_geom_settings, geom_settings)
        timing_settings     = updated(self.default_timing_settings, timing_settings)

        # use simpler settigns to include only Multiplexer-specific members
        class SimpleSettings(Settings):
            def __init__(self, **kwargs):
                self.set_attributes(kwargs)

        settings        = SimpleSettings(**controller_settings)
        settings.phy    = SimpleSettings(**phy_settings)
        settings.geom   = SimpleSettings(**geom_settings)
        settings.timing = SimpleSettings(**timing_settings)
        settings.geom.addressbits = max(settings.geom.rowbits, settings.geom.colbits)
        self.settings = settings

        # create interfaces and stubs required to instantiate Multiplexer
        abits  = settings.geom.addressbits
        babits = settings.geom.bankbits
        nbanks = 2**babits
        nranks = settings.phy.nranks
        self.bank_machines = [BankMachineStub(abits=abits, babits=babits)
                              for _ in range(nbanks*nranks)]
        self.refresher = RefresherStub(abits=abits, babits=babits)
        self.dfi = dfi.Interface(addressbits=abits, bankbits=babits, nranks=settings.phy.nranks,
                                 databits=settings.phy.dfi_databits, nphases=settings.phy.nphases)
        address_align = log2_int(burst_lengths[settings.phy.memtype])
        self.interface = LiteDRAMInterface(address_align=address_align, settings=settings)

        # add Multiplexer
        self.submodules.multiplexer = Multiplexer(settings, self.bank_machines, self.refresher,
                                                  self.dfi, self.interface)

        # add helpers for driving bank machines/refresher
        self.bm_drivers = [CmdRequestRWDriver(bm.cmd, i) for i, bm in enumerate(self.bank_machines)]
        self.refresh_driver = CmdRequestRWDriver(self.refresher.cmd, i=1)

    def fsm_state(self):
        # return name of current state of Multiplexer's FSM
        return self.multiplexer.fsm.decoding[(yield self.multiplexer.fsm.state)]


class TestMultiplexer(unittest.TestCase):
    def test_init(self):
        # Verify that instantiation of Multiplexer in MultiplexerDUT is correct
        # This will fail if Multiplexer starts using any new setting from controller.settings
        dut = MultiplexerDUT()

    def test_fsm_start_at_read(self):
        # FSM should start at READ state (assumed in some other tests)
        def main_generator(dut):
            self.assertEqual((yield from dut.fsm_state()), "READ")

        dut = MultiplexerDUT()
        run_simulation(dut, main_generator(dut))

    def test_fsm_read_to_write_latency(self):
        # Verify the timing of READ to WRITE transition
        def main_generator(dut):
            rtw = dut.settings.phy.read_latency
            expected = "r" + (rtw - 1) * ">" + "w"
            states = ""

            # set write_available=1
            yield from dut.bm_drivers[0].write()
            yield

            for _ in range(len(expected)):
                state = (yield from dut.fsm_state())
                # use ">" for all other states, as FSM.delayed_enter uses
                # anonymous states instead of staying in RTW
                states += {
                    "READ": "r",
                    "WRITE": "w",
                }.get(state, ">")
                yield

            self.assertEqual(states, expected)

        dut = MultiplexerDUT()
        run_simulation(dut, main_generator(dut))

    def test_fsm_write_to_read_latency(self):
        # Verify the timing of WRITE to READ transition
        def main_generator(dut):
            write_latency = math.ceil(dut.settings.phy.cwl / dut.settings.phy.nphases)
            wtr = dut.settings.timing.tWTR + write_latency + dut.settings.timing.tCCD or 0

            expected = "w" + (wtr - 1) * ">" + "r"
            states = ""

            # simulate until we are in WRITE
            yield from dut.bm_drivers[0].write()
            while (yield from dut.fsm_state()) != "WRITE":
                yield

            # set read_available=1
            yield from dut.bm_drivers[0].read()
            yield

            for _ in range(len(expected)):
                state = (yield from dut.fsm_state())
                states += {
                    "READ": "r",
                    "WRITE": "w",
                }.get(state, ">")
                yield

            self.assertEqual(states, expected)

        dut = MultiplexerDUT()
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_steer_read_correct_phases(self):
        # Check that correct phases are being used during READ
        def main_generator(dut):
            yield from dut.bm_drivers[2].read()
            yield from dut.bm_drivers[3].activate()

            while not (yield dut.bank_machines[2].cmd.ready):
                yield
            yield

            # fsm starts in READ
            for phase in range(dut.settings.phy.nphases):
                if phase == dut.settings.phy.rdphase:
                    self.assertEqual((yield dut.dfi.phases[phase].bank), 2)
                elif phase == dut.settings.phy.rdcmdphase:
                    self.assertEqual((yield dut.dfi.phases[phase].bank), 3)
                else:
                    self.assertEqual((yield dut.dfi.phases[phase].bank), 0)

        dut = MultiplexerDUT()
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_steer_write_correct_phases(self):
        # Check that correct phases are being used during WRITE
        def main_generator(dut):
            yield from dut.bm_drivers[2].write()
            yield from dut.bm_drivers[3].activate()

            while not (yield dut.bank_machines[2].cmd.ready):
                yield
            yield

            # fsm starts in READ
            for phase in range(dut.settings.phy.nphases):
                if phase == dut.settings.phy.wrphase:
                    self.assertEqual((yield dut.dfi.phases[phase].bank), 2)
                elif phase == dut.settings.phy.wrcmdphase:
                    self.assertEqual((yield dut.dfi.phases[phase].bank), 3)
                else:
                    self.assertEqual((yield dut.dfi.phases[phase].bank), 0)

        dut = MultiplexerDUT()
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_single_phase_cmd_req(self):
        # Verify that, for a single phase, commands are sent sequentially
        def main_generator(dut):
            yield from dut.bm_drivers[2].write()
            yield from dut.bm_drivers[3].activate()
            ready = {2: dut.bank_machines[2].cmd.ready, 3: dut.bank_machines[3].cmd.ready}

            # activate should appear first
            while not ((yield ready[2]) or (yield ready[3])):
                yield
            yield from dut.bm_drivers[3].nop()
            yield
            self.assertEqual((yield dut.dfi.phases[0].bank), 3)

            # than write
            while not (yield ready[2]):
                yield
            yield from dut.bm_drivers[2].nop()
            yield
            self.assertEqual((yield dut.dfi.phases[0].bank), 2)

        dut = MultiplexerDUT(phy_settings=dict(nphases=1))
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_ras_trrd(self):
        # Verify tRRD
        def main_generator(dut):
            yield from dut.bm_drivers[2].activate()
            yield from dut.bm_drivers[3].activate()
            ready = {2: dut.bank_machines[2].cmd.ready, 3: dut.bank_machines[3].cmd.ready}

            # wait for activate
            while not ((yield ready[2]) or (yield ready[3])):
                yield
            # invalidate command that was ready
            if (yield ready[2]):
                yield from dut.bm_drivers[2].nop()
            else:
                yield from dut.bm_drivers[3].nop()
            yield

            # wait for the second activate; start from 1 for the previous cycle
            ras_time = 1
            while not ((yield ready[2]) or (yield ready[3])):
                ras_time += 1
                yield

            self.assertEqual(ras_time, 6)

        dut = MultiplexerDUT(timing_settings=dict(tRRD=6))
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_cas_tccd(self):
        # Verify tCCD
        def main_generator(dut):
            yield from dut.bm_drivers[2].read()
            yield from dut.bm_drivers[3].read()
            ready = {2: dut.bank_machines[2].cmd.ready, 3: dut.bank_machines[3].cmd.ready}

            # wait for activate
            while not ((yield ready[2]) or (yield ready[3])):
                yield
            # invalidate command that was ready
            if (yield ready[2]):
                yield from dut.bm_drivers[2].nop()
            else:
                yield from dut.bm_drivers[3].nop()
            yield

            # wait for the second activate; start from 1 for the previous cycle
            cas_time = 1
            while not ((yield ready[2]) or (yield ready[3])):
                cas_time += 1
                yield

            self.assertEqual(cas_time, 3)

        dut = MultiplexerDUT(timing_settings=dict(tCCD=3))
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_fsm_anti_starvation(self):
        # Check that anti-starvation works according to controller settings
        def main_generator(dut):
            yield from dut.bm_drivers[2].read()
            yield from dut.bm_drivers[3].write()

            # go to WRITE
            # anti starvation does not work for 1st read, as read_time_en already starts as 1
            # READ -> RTW -> WRITE
            while (yield from dut.fsm_state()) != "WRITE":
                yield

            # wait for write anti starvation
            for _ in range(dut.settings.write_time):
                self.assertEqual((yield from dut.fsm_state()), "WRITE")
                yield
            self.assertEqual((yield from dut.fsm_state()), "WTR")

            # WRITE -> WTR -> READ
            while (yield from dut.fsm_state()) != "READ":
                yield

            # wait for read anti starvation
            for _ in range(dut.settings.read_time):
                self.assertEqual((yield from dut.fsm_state()), "READ")
                yield
            self.assertEqual((yield from dut.fsm_state()), "RTW")

        dut = MultiplexerDUT()
        generators = [
            main_generator(dut),
            timeout_generator(100),
        ]
        run_simulation(dut, generators)

    def test_write_datapath(self):
        # Verify that data is transmitted from native interface to DFI
        def main_generator(dut):
            yield from dut.bm_drivers[2].write()
            # 16bits * 2 (DDR) * 1 (phases)
            yield dut.interface.wdata.eq(0xbaadf00d)
            yield dut.interface.wdata_we.eq(0xf)

            while not (yield dut.bank_machines[2].cmd.ready):
                yield
            yield

            self.assertEqual((yield dut.dfi.phases[0].wrdata), 0xbaadf00d)
            self.assertEqual((yield dut.dfi.phases[0].wrdata_en), 1)
            self.assertEqual((yield dut.dfi.phases[0].address), 2)
            self.assertEqual((yield dut.dfi.phases[0].bank), 2)

        dut = MultiplexerDUT(phy_settings=dict(nphases=1))
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_read_datapath(self):
        # Verify that data is transmitted from DFI to native interface
        def main_generator(dut):
            yield from dut.bm_drivers[2].write()
            # 16bits * 2 (DDR) * 1 (phases)
            yield dut.dfi.phases[0].rddata.eq(0xbaadf00d)
            yield dut.dfi.phases[0].rddata_en.eq(1)
            yield

            while not (yield dut.bank_machines[2].cmd.ready):
                yield
            yield

            self.assertEqual((yield dut.interface.rdata), 0xbaadf00d)
            self.assertEqual((yield dut.interface.wdata_we), 0)
            self.assertEqual((yield dut.dfi.phases[0].address), 2)
            self.assertEqual((yield dut.dfi.phases[0].bank), 2)

        dut = MultiplexerDUT(phy_settings=dict(nphases=1))
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_refresh_requires_gnt(self):
        # After refresher command request, multiplexer waits for permission from all bank machines
        def main_generator(dut):
            def assert_dfi_cmd(cas, ras, we):
                p = dut.dfi.phases[0]
                cas_n, ras_n, we_n = (yield p.cas_n), (yield p.ras_n), (yield p.we_n)
                self.assertEqual((cas_n, ras_n, we_n), (1 - cas, 1 - ras, 1 - we))

            for bm in dut.bank_machines:
                self.assertEqual((yield bm.refresh_req), 0)

            yield from dut.refresh_driver.refresh()
            yield

            # bank machines get the request
            for bm in dut.bank_machines:
                self.assertEqual((yield bm.refresh_req), 1)
            # no command yet
            yield from assert_dfi_cmd(cas=0, ras=0, we=0)

            # grant permission for refresh
            prng = random.Random(42)
            delays = [prng.randrange(100) for _ in dut.bank_machines]
            for t in range(max(delays) + 1):
                # grant permission
                for delay, bm in zip(delays, dut.bank_machines):
                    if delay == t:
                        yield bm.refresh_gnt.eq(1)
                yield

                # make sure thare is no command yet
                yield from assert_dfi_cmd(cas=0, ras=0, we=0)
            yield
            yield

            # refresh command
            yield from assert_dfi_cmd(cas=1, ras=1, we=0)

        dut = MultiplexerDUT()
        run_simulation(dut, main_generator(dut))

    def test_requests_from_multiple_bankmachines(self):
        # Check complex communication scenario with requests from multiple bank machines
        # The communication is greatly simplified - data path is completely ignored,
        # no responses from PHY are simulated. Each bank machine performs a sequence of
        # requests, bank machines are ordered randomly and the DFI command data is
        # checked to verify if all the commands have been sent if correct per-bank order.

        # requests sequence on given bank machines
        bm_sequences = {
            0: "awwwwwwp",
            1: "arrrrrrp",
            2: "arwrwrwp",
            3: "arrrwwwp",
            4: "awparpawp",
            5: "awwparrrrp",
        }
        # convert to lists to use .pop()
        bm_sequences = {bm_num: list(seq) for bm_num, seq in bm_sequences.items()}

        def main_generator(bank_machines, drivers):
            # work on a copy
            bm_seq = copy.deepcopy(bm_sequences)

            def non_empty():
                return list(filter(lambda n: len(bm_seq[n]) > 0, bm_seq.keys()))

            # artificially perform the work of LiteDRAMCrossbar by always picking only one request
            prng = random.Random(42)
            while len(non_empty()) > 0:
                # pick random bank machine
                bm_num = prng.choice(non_empty())

                # set given request
                request_char = bm_seq[bm_num].pop(0)
                yield from drivers[bm_num].request(request_char)
                yield

                # wait for ready
                while not (yield bank_machines[bm_num].cmd.ready):
                    yield

                # disable it
                yield from drivers[bm_num].nop()

            for _ in range(16):
                yield

        # gather data on DFI
        DFISnapshot = namedtuple("DFICapture",
                                 ["cmd", "bank", "address", "wrdata_en", "rddata_en"])
        dfi_snapshots = []

        @passive
        def dfi_monitor(dfi):
            while True:
                # capture current state of DFI lines
                phases = []
                for i, p in enumerate(dfi.phases):
                    # transform cas/ras/we to command name
                    cas_n, ras_n, we_n = (yield p.cas_n), (yield p.ras_n), (yield p.we_n)
                    captured = {"cmd": dfi_cmd_to_char(cas_n, ras_n, we_n)}

                    # capture rest of fields
                    for field in DFISnapshot._fields:
                        if field != "cmd":
                            captured[field] = (yield getattr(p, field))

                    phases.append(DFISnapshot(**captured))
                dfi_snapshots.append(phases)
                yield

        dut = MultiplexerDUT()
        generators = [
            main_generator(dut.bank_machines, dut.bm_drivers),
            dfi_monitor(dut.dfi),
            timeout_generator(200),
        ]
        run_simulation(dut, generators)

        # check captured DFI data with the description
        for snap in dfi_snapshots:
            for i, phase_snap in enumerate(snap):
                if phase_snap.cmd == "_":
                    continue

                # distinguish bank machines by the bank number
                bank = phase_snap.bank
                # find next command for the given bank
                cmd = bm_sequences[bank].pop(0)

                # check if the captured data is correct
                self.assertEqual(phase_snap.cmd, cmd)
                if cmd in ["w", "r"]:
                    # addresses are artificially forced to bank numbers in drivers
                    self.assertEqual(phase_snap.address, bank)
                    if cmd == "w":
                        self.assertEqual(phase_snap.wrdata_en, 1)
                    if cmd == "r":
                        self.assertEqual(phase_snap.rddata_en, 1)
