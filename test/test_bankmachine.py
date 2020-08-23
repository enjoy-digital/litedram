#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import math
import unittest

from migen import *

from litedram.common import *
from litedram.core.bankmachine import BankMachine

from test.common import timeout_generator


class BankMachineDUT(Module):
    # Fill only settings needed by BankMachine
    default_controller_settings = dict(
        cmd_buffer_depth    = 8,
        cmd_buffer_buffered = False,
        with_auto_precharge = True,
    )
    default_phy_settings = dict(
        cwl          = 2,
        nphases      = 2,
        nranks       = 1,
        # indirectly
        memtype      = "DDR2",
        dfi_databits = 2*16,
    )
    default_geom_settings = dict(
        bankbits = 3,
        rowbits  = 13,
        colbits  = 10,
    )
    default_timing_settings = dict(
        tRAS = None,
        tRC  = None,
        tCCD = 1,
        tRCD = 2,
        tRP  = 2,
        tWR  = 2,
    )

    def __init__(self, n,
        controller_settings = None,
        phy_settings        = None,
        geom_settings       = None,
        timing_settings     = None):
        # Update settings if provided
        def updated(settings, update):
            copy = settings.copy()
            copy.update(update or {})
            return copy

        controller_settings = updated(self.default_controller_settings, controller_settings)
        phy_settings        = updated(self.default_phy_settings, phy_settings)
        geom_settings       = updated(self.default_geom_settings, geom_settings)
        timing_settings     = updated(self.default_timing_settings, timing_settings)

        class SimpleSettings(Settings):
            def __init__(self, **kwargs):
                self.set_attributes(kwargs)

        settings        = SimpleSettings(**controller_settings)
        settings.phy    = SimpleSettings(**phy_settings)
        settings.geom   = SimpleSettings(**geom_settings)
        settings.timing = SimpleSettings(**timing_settings)
        settings.geom.addressbits = max(settings.geom.rowbits, settings.geom.colbits)
        self.settings = settings

        self.address_align = log2_int(burst_lengths[settings.phy.memtype])
        self.address_width = LiteDRAMInterface(self.address_align, settings).address_width

        bankmachine = BankMachine(n=n,
            address_width = self.address_width,
            address_align = self.address_align,
            nranks        = settings.phy.nranks,
            settings      = settings)
        self.submodules.bankmachine = bankmachine

    def get_cmd(self):
        # cmd_request_rw_layout -> name
        layout = [name for name, _ in cmd_request_rw_layout(
            a  = self.settings.geom.addressbits,
            ba = self.settings.geom.bankbits)]
        request = {}
        for name in layout + ["valid", "ready", "first", "last"]:
            request[name] = (yield getattr(self.bankmachine.cmd, name))
        request["type"] = {
            (0, 0, 0): "nop",
            (1, 0, 1): "write",
            (1, 0, 0): "read",
            (0, 1, 0): "activate",
            (0, 1, 1): "precharge",
            (1, 1, 0): "refresh",
        }[(request["cas"], request["ras"], request["we"])]
        return request

    def req_address(self, row, col):
        col = col & (2**self.settings.geom.colbits - 1)
        row = row & (2**self.settings.geom.rowbits - 1)
        split = self.settings.geom.colbits - self.address_align
        return (row << split) | col


class TestBankMachine(unittest.TestCase):
    def test_init(self):
        BankMachineDUT(1)

    def bankmachine_commands_test(self, dut, requests, generators=None):
        # Perform a test by simulating requests producer and return registered commands
        commands = []

        def producer(dut):
            for req in requests:
                yield dut.bankmachine.req.addr.eq(req["addr"])
                yield dut.bankmachine.req.we.eq(req["we"])
                yield dut.bankmachine.req.valid.eq(1)
                yield
                while not (yield dut.bankmachine.req.ready):
                    yield
                yield dut.bankmachine.req.valid.eq(0)
                for _ in range(req.get("delay", 0)):
                    yield

        def req_consumer(dut):
            for req in requests:
                if req["we"]:
                    signal = dut.bankmachine.req.wdata_ready
                else:
                    signal = dut.bankmachine.req.rdata_valid
                while not (yield signal):
                    yield
                yield

        @passive
        def cmd_consumer(dut):
            while True:
                while not (yield dut.bankmachine.cmd.valid):
                    yield
                yield dut.bankmachine.cmd.ready.eq(1)
                yield
                commands.append((yield from dut.get_cmd()))
                yield dut.bankmachine.cmd.ready.eq(0)
                yield

        all_generators = [
            producer(dut),
            req_consumer(dut),
            cmd_consumer(dut),
            timeout_generator(50 * len(requests)),
        ]
        if generators is not None:
            all_generators += [g(dut) for g in generators]
        run_simulation(dut, all_generators)
        return commands

    def test_opens_correct_row(self):
        # Verify that the correct row is activated before read/write commands.
        dut = BankMachineDUT(3)
        requests = [
            dict(addr=dut.req_address(row=0xf0, col=0x0d), we=0),
            dict(addr=dut.req_address(row=0xd0, col=0x0d), we=1),
        ]
        commands = self.bankmachine_commands_test(dut=dut, requests=requests)
        # Commands: activate, read (auto-precharge), activate, write
        self.assertEqual(commands[0]["type"], "activate")
        self.assertEqual(commands[0]["a"], 0xf0)
        self.assertEqual(commands[2]["type"], "activate")
        self.assertEqual(commands[2]["a"], 0xd0)

    def test_correct_bank_address(self):
        # Verify that `ba` always corresponds to the BankMachine number.
        for bn in [0, 2, 7]:
            with self.subTest(bn=bn):
                dut = BankMachineDUT(bn, geom_settings=dict(bankbits=3))
                requests = [dict(addr=0, we=0)]
                commands = self.bankmachine_commands_test(dut=dut, requests=requests)
                for cmd in commands:
                    self.assertEqual(cmd["ba"], bn)

    def test_read_write_same_row(self):
        # Verify that there is only one activate when working on single row.
        dut = BankMachineDUT(1)
        requests = [
            dict(addr=dut.req_address(row=0xba, col=0xad), we=0),
            dict(addr=dut.req_address(row=0xba, col=0xad), we=1),
            dict(addr=dut.req_address(row=0xba, col=0xbe), we=0),
            dict(addr=dut.req_address(row=0xba, col=0xbe), we=1),
        ]
        commands = self.bankmachine_commands_test(dut=dut, requests=requests)
        commands = [(cmd["type"], cmd["a"]) for cmd in commands]
        expected = [
            ("activate", 0xba),
            ("read",     0xad << dut.address_align),
            ("write",    0xad << dut.address_align),
            ("read",     0xbe << dut.address_align),
            ("write",    0xbe << dut.address_align),
        ]
        self.assertEqual(commands, expected)

    def test_write_different_rows_with_delay(self):
        # Verify that precharge is used when changing row with a delay this is independent form auto-precharge.
        for auto_precharge in [False, True]:
            with self.subTest(auto_precharge=auto_precharge):
                settings = dict(with_auto_precharge=auto_precharge)
                dut      = BankMachineDUT(1, controller_settings=settings)
                requests = [
                    dict(addr=dut.req_address(row=0xba, col=0xad), we=1, delay=8),
                    dict(addr=dut.req_address(row=0xda, col=0xad), we=1),
                ]
                commands = self.bankmachine_commands_test(dut=dut, requests=requests)
                commands = [(cmd["type"], cmd["a"]) for cmd in commands]
                expected = [
                    ("activate",  0xba),
                    ("write",     0xad << dut.address_align),
                    ("precharge", 0xad << dut.address_align),
                    ("activate",  0xda),
                    ("write",     0xad << dut.address_align),
                ]
                self.assertEqual(commands, expected)

    def test_write_different_rows_with_auto_precharge(self):
        # Verify that auto-precharge is used when changing row without delay.
        settings = dict(with_auto_precharge=True)
        dut      = BankMachineDUT(1, controller_settings=settings)
        requests = [
            dict(addr=dut.req_address(row=0xba, col=0xad), we=1),
            dict(addr=dut.req_address(row=0xda, col=0xad), we=1),
        ]
        commands = self.bankmachine_commands_test(dut=dut, requests=requests)
        commands = [(cmd["type"], cmd["a"]) for cmd in commands]
        expected = [
            ("activate",  0xba),
            ("write",    (0xad << dut.address_align) | (1 << 10)),
            ("activate",  0xda),
            ("write",     0xad << dut.address_align),
        ]
        self.assertEqual(commands, expected)

    def test_write_different_rows_without_auto_precharge(self):
        # Verify that auto-precharge is used when changing row without delay.
        settings = dict(with_auto_precharge=False)
        dut = BankMachineDUT(1, controller_settings=settings)
        requests = [
            dict(addr=dut.req_address(row=0xba, col=0xad), we=1),
            dict(addr=dut.req_address(row=0xda, col=0xad), we=1),
        ]
        commands = self.bankmachine_commands_test(dut=dut, requests=requests)
        commands = [(cmd["type"], cmd["a"]) for cmd in commands]
        expected = [
            ("activate",  0xba),
            ("write",     0xad << dut.address_align),
            ("precharge", 0xad << dut.address_align),
            ("activate",  0xda),
            ("write",     0xad << dut.address_align),
        ]
        self.assertEqual(commands, expected)

    def test_burst_no_request_lost(self):
        # Verify that no request is lost in fast bursts of requests regardless of cmd_buffer_depth.
        for cmd_buffer_depth in [8, 1, 0]:
            settings = dict(cmd_buffer_depth=cmd_buffer_depth)
            with self.subTest(**settings):
                dut = BankMachineDUT(1, controller_settings=settings)
                # Long sequence of writes to the same row
                requests = [dict(addr=dut.req_address(row=0xba, col=i), we=1) for i in range(32)]
                expected = ([("activate", 0xba)] +
                            [("write", i << dut.address_align) for i in range(32)])
                commands = self.bankmachine_commands_test(dut=dut, requests=requests)
                commands = [(cmd["type"], cmd["a"]) for cmd in commands]
                self.assertEqual(commands, expected)

    def test_lock_until_requests_finished(self):
        # Verify that lock is being held until all requests in FIFO are processed.
        @passive
        def lock_checker(dut):
            req = dut.bankmachine.req
            self.assertEqual((yield req.lock), 0)

            # Wait until first request becomes locked
            while not (yield req.valid):
                yield

            # Wait until lock should be released (all requests in queue gets processed)
            # here it happens when the final wdata_ready ends
            for _ in range(3):
                while not (yield req.wdata_ready):
                    yield
                    self.assertEqual((yield req.lock), 1)
                yield

            yield
            self.assertEqual((yield req.lock), 0)

        dut = BankMachineDUT(1)
        # Simple sequence with row change
        requests = [
            dict(addr=dut.req_address(row=0x1a, col=0x01), we=1),
            dict(addr=dut.req_address(row=0x1b, col=0x02), we=1),
            dict(addr=dut.req_address(row=0x1c, col=0x04), we=1),
        ]
        self.bankmachine_commands_test(dut=dut, requests=requests, generators=[lock_checker])

    def timing_test(self, from_cmd, to_cmd, time_expected, **dut_kwargs):
        @passive
        def timing_checker(dut):
            def is_cmd(cmd_type, test_ready):
                cmd = (yield from dut.get_cmd())
                ready = cmd["ready"] if test_ready else True
                return cmd["valid"] and ready and cmd["type"] == cmd_type

            # Time between WRITE ends (ready and valid) and PRECHARGE becomes valid
            while not (yield from is_cmd(from_cmd, test_ready=True)):
                yield
            yield  # Wait until cmd deactivates in case the second cmd is the same as first
            time = 1
            while not (yield from is_cmd(to_cmd, test_ready=False)):
                yield
                time += 1

            self.assertEqual(time, time_expected)

        dut = BankMachineDUT(1, **dut_kwargs)
        # Simple sequence with row change
        requests = [
            dict(addr=dut.req_address(row=0xba, col=0xad), we=1),
            dict(addr=dut.req_address(row=0xda, col=0xad), we=1),
        ]
        self.bankmachine_commands_test(dut=dut, requests=requests, generators=[timing_checker])

    def test_timing_write_to_precharge(self):
        controller_settings = dict(with_auto_precharge=False)
        timing_settings = dict(tWR=6, tCCD=4)
        phy_settings = dict(cwl=2, nphases=2)
        write_latency = math.ceil(phy_settings["cwl"] / phy_settings["nphases"])
        precharge_time = write_latency + timing_settings["tWR"] + timing_settings["tCCD"]
        self.timing_test("write", "precharge", precharge_time,
            controller_settings = controller_settings,
            phy_settings        = phy_settings,
            timing_settings     = timing_settings)

    def test_timing_activate_to_activate(self):
        timing_settings = dict(tRC=16)
        self.timing_test("activate", "activate",
            time_expected   = 16,
            timing_settings = timing_settings)

    def test_timing_activate_to_precharge(self):
        timing_settings = dict(tRAS=32)
        self.timing_test("activate", "precharge",
            time_expected   = 32,
            timing_settings = timing_settings)

    def test_refresh(self):
        # Verify that no commands are issued during refresh and after it the row is re-activated.
        @passive
        def refresh_generator(dut):
            # Wait some time for the bankmachine to start
            for _ in range(16):
                yield

            # Request a refresh
            yield dut.bankmachine.refresh_req.eq(1)
            while not (yield dut.bankmachine.refresh_gnt):
                yield

            # Wait when refresh is being performed
            # Make sure no command is issued during refresh
            for _ in range(32):
                self.assertEqual((yield dut.bankmachine.cmd.valid), 0)
                yield

            # Signalize refresh is ready
            yield dut.bankmachine.refresh_req.eq(0)

        dut = BankMachineDUT(1)
        requests = [dict(addr=dut.req_address(row=0xba, col=i), we=1) for i in range(16)]
        commands = self.bankmachine_commands_test(dut=dut, requests=requests,
                                                  generators=[refresh_generator])
        commands = [(cmd["type"], cmd["a"]) for cmd in commands]
        # Refresh will close row, so bankmachine should re-activate it after refresh
        self.assertEqual(commands.count(("activate", 0xba)), 2)
        # Verify that the write commands are correct
        write_commands = [cmd for cmd in commands if cmd[0] == "write"]
        expected_writes = [("write", i << dut.address_align) for i in range(16)]
        self.assertEqual(write_commands, expected_writes)

    def test_output_annotations(self):
        # Verify that all commands are annotated correctly using is_* signals.
        checked = set()

        @passive
        def cmd_checker(dut):
            while True:
                cmd = (yield from dut.get_cmd())
                if cmd["valid"]:
                    if cmd["type"] in ["activate", "precharge"]:
                        self.assertEqual(cmd["is_cmd"],   1)
                        self.assertEqual(cmd["is_write"], 0)
                        self.assertEqual(cmd["is_read"],  0)
                    elif cmd["type"] in ["write"]:
                        self.assertEqual(cmd["is_cmd"],   0)
                        self.assertEqual(cmd["is_write"], 1)
                        self.assertEqual(cmd["is_read"],  0)
                    elif cmd["type"] in ["read"]:
                        self.assertEqual(cmd["is_cmd"],   0)
                        self.assertEqual(cmd["is_write"], 0)
                        self.assertEqual(cmd["is_read"],  1)
                    else:
                        raise ValueError(cmd["type"])
                    checked.add(cmd["type"])
                yield

        dut = BankMachineDUT(1)
        requests = [
            dict(addr=dut.req_address(row=0xba, col=0xad), we=0),
            dict(addr=dut.req_address(row=0xba, col=0xad), we=1),
            dict(addr=dut.req_address(row=0xda, col=0xad), we=0),
            # Wait enough time for regular (not auto) precharge to be used
            dict(addr=dut.req_address(row=0xda, col=0xad), we=1, delay=32),
            dict(addr=dut.req_address(row=0xba, col=0xad), we=0),
            dict(addr=dut.req_address(row=0xba, col=0xad), we=1),
        ]
        self.bankmachine_commands_test(dut=dut, requests=requests, generators=[cmd_checker])
        # Bankmachine does not produce refresh commands
        self.assertEqual(checked, {"activate", "precharge", "write", "read"})
