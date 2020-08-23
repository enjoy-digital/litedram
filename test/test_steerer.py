#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from litex.soc.interconnect import stream

from litedram.common import *
from litedram.phy import dfi
from litedram.core.multiplexer import _Steerer
from litedram.core.multiplexer import STEER_NOP, STEER_CMD, STEER_REQ, STEER_REFRESH

from test.common import CmdRequestRWDriver


class SteererDUT(Module):
    def __init__(self, nranks, dfi_databits, nphases):
        a, ba         = 13, 3
        nop           = Record(cmd_request_layout(a=a, ba=ba))
        choose_cmd    = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))
        choose_req    = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))
        refresher_cmd = stream.Endpoint(cmd_request_rw_layout(a=a, ba=ba))

        self.commands = [nop, choose_cmd, choose_req, refresher_cmd]
        self.dfi = dfi.Interface(addressbits=a, bankbits=ba, nranks=nranks, databits=dfi_databits,
                                 nphases=nphases)
        self.submodules.steerer = _Steerer(self.commands, self.dfi)

        # NOP is not an endpoint and does not have is_* signals
        self.drivers = [CmdRequestRWDriver(req, i, ep_layout=i != 0, rw_layout=i != 0)
                        for i, req in enumerate(self.commands)]


class TestSteerer(unittest.TestCase):
    def test_nop_not_valid(self):
        # If NOP is selected then there should be no command selected on cas/ras/we.
        def main_generator(dut):
            # NOP on both phases
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
        # Commands should be connected to phases only if they are valid & ready.
        def main_generator(dut):
            # Set possible requests
            yield from dut.drivers[STEER_NOP].nop()
            yield from dut.drivers[STEER_CMD].activate()
            yield from dut.drivers[STEER_REQ].write()
            yield from dut.drivers[STEER_REFRESH].refresh()
            # Set how phases are steered
            yield dut.steerer.sel[0].eq(STEER_CMD)
            yield dut.steerer.sel[1].eq(STEER_NOP)
            yield
            yield

            def check(is_ready):
                # CMD on phase 0 should be STEER_CMD=activate
                p = dut.dfi.phases[0]
                self.assertEqual((yield p.bank),    STEER_CMD)
                self.assertEqual((yield p.address), STEER_CMD)
                if is_ready:
                    self.assertEqual((yield p.cas_n), 1)
                    self.assertEqual((yield p.ras_n), 0)
                    self.assertEqual((yield p.we_n),  1)
                else:  # Not steered
                    self.assertEqual((yield p.cas_n), 1)
                    self.assertEqual((yield p.ras_n), 1)
                    self.assertEqual((yield p.we_n),  1)

                # Nop on phase 1 should be STEER_NOP
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
        # With a single rank the whole `ba` signal is bank address.
        def main_generator(dut):
            yield from dut.drivers[STEER_NOP].nop()
            yield from dut.drivers[STEER_REQ].write()
            yield from dut.drivers[STEER_REFRESH].refresh()
            # All the bits are for bank
            dut.drivers[STEER_CMD].bank = 0b110
            yield from dut.drivers[STEER_CMD].activate()
            yield dut.commands[STEER_CMD].ready.eq(1)
            # Set how phases are steered
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
        # With multiple ranks `ba` signal should be split into bank and chip select.
        def main_generator(dut):
            yield from dut.drivers[STEER_NOP].nop()
            yield from dut.drivers[STEER_REQ].write()
            yield from dut.drivers[STEER_REFRESH].refresh()
            # Set how phases are steered
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
        # When refresh command is on first phase, all ranks should be selected.
        def main_generator(dut):
            yield from dut.drivers[STEER_NOP].nop()
            yield from dut.drivers[STEER_REQ].write()
            yield from dut.drivers[STEER_CMD].activate()
            # Set how phases are steered
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
        # Reset_n should be 1 for all phases at all times.
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
        # CKE should be 1 for all phases and ranks at all times.
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
        # ODT should be 1 for all phases and ranks at all times.
        #  NOTE: only until dynamic ODT is implemented.
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
