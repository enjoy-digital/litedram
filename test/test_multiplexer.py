#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import copy
import random
import unittest
from collections import namedtuple

from migen import *

from litex.soc.interconnect import stream

from litedram.common import *
from litedram.phy import dfi
from litedram.core.multiplexer import Multiplexer

# load after "* imports" to avoid using Migen version of vcd.py
from litex.gen.sim import run_simulation

from test.common import timeout_generator, CmdRequestRWDriver


def dfi_cmd_to_char(cas_n, ras_n, we_n):
    return {
        (1, 1, 1): "_",
        (0, 1, 0): "w",
        (0, 1, 1): "r",
        (1, 0, 1): "a",
        (1, 0, 0): "p",
        (0, 0, 1): "f",
    }[(cas_n, ras_n, we_n)]


class BankMachineStub:
    def __init__(self, babits, abits):
        self.cmd = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))
        self.refresh_req = Signal()
        self.refresh_gnt = Signal()


class RefresherStub:
    def __init__(self, babits, abits):
        self.cmd = stream.Endpoint(cmd_request_rw_layout(a=abits, ba=babits))


class MultiplexerDUT(Module):
    # Define default settings that can be overwritten in specific tests use only these settings
    # that we actually need for Multiplexer.
    default_controller_settings = dict(
        read_time      = 32,
        write_time     = 16,
        with_bandwidth = False,
    )
    default_phy_settings = dict(
        nphases      = 2,
        rdphase      = 0,
        wrphase      = 1,
        rdcmdphase   = 1,
        wrcmdphase   = 0,
        read_latency = 5,
        cwl          = 3,
        # Indirectly
        nranks       = 1,
        databits     = 16,
        dfi_databits = 2*16,
        memtype      = "DDR2",
    )
    default_geom_settings = dict(
        bankbits = 3,
        rowbits  = 13,
        colbits  = 10,
    )
    default_timing_settings = dict(
        tWTR = 2,
        tFAW = None,
        tCCD = 1,
        tRRD = None,
    )

    def __init__(self,
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

        # Use simpler settigns to include only Multiplexer-specific members
        class SimpleSettings(Settings):
            def __init__(self, **kwargs):
                self.set_attributes(kwargs)

        settings        = SimpleSettings(**controller_settings)
        settings.phy    = SimpleSettings(**phy_settings)
        settings.geom   = SimpleSettings(**geom_settings)
        settings.timing = SimpleSettings(**timing_settings)
        settings.geom.addressbits = max(settings.geom.rowbits, settings.geom.colbits)
        self.settings = settings

        # Create interfaces and stubs required to instantiate Multiplexer
        abits  = settings.geom.addressbits
        babits = settings.geom.bankbits
        nbanks = 2**babits
        nranks = settings.phy.nranks
        self.bank_machines = [BankMachineStub(abits=abits, babits=babits)
                              for _ in range(nbanks*nranks)]
        self.refresher = RefresherStub(abits=abits, babits=babits)
        self.dfi = dfi.Interface(
            addressbits = abits,
            bankbits    = babits,
            nranks      = settings.phy.nranks,
            databits    = settings.phy.dfi_databits,
            nphases     = settings.phy.nphases)
        address_align = log2_int(burst_lengths[settings.phy.memtype])
        self.interface = LiteDRAMInterface(address_align=address_align, settings=settings)

        # Add Multiplexer
        self.submodules.multiplexer = Multiplexer(settings, self.bank_machines, self.refresher,
            self.dfi, self.interface)

        # Add helpers for driving bank machines/refresher
        self.bm_drivers = [CmdRequestRWDriver(bm.cmd, i) for i, bm in enumerate(self.bank_machines)]
        self.refresh_driver = CmdRequestRWDriver(self.refresher.cmd, i=1)

    def fsm_state(self):
        # Return name of current state of Multiplexer's FSM
        return self.multiplexer.fsm.decoding[(yield self.multiplexer.fsm.state)]


class TestMultiplexer(unittest.TestCase):
    def test_init(self):
        # Verify that instantiation of Multiplexer in MultiplexerDUT is correct. This will fail if
        # Multiplexer starts using any new setting from controller.settings.
        MultiplexerDUT()

    def test_fsm_start_at_read(self):
        # FSM should start at READ state (assumed in some other tests).
        def main_generator(dut):
            self.assertEqual((yield from dut.fsm_state()), "READ")

        dut = MultiplexerDUT()
        run_simulation(dut, main_generator(dut))

    def test_fsm_read_to_write_latency(self):
        # Verify the timing of READ to WRITE transition.
        def main_generator(dut):
            rtw = dut.settings.phy.read_latency
            expected = "r" + (rtw - 1) * ">" + "w"
            states = ""

            # Set write_available=1
            yield from dut.bm_drivers[0].write()
            yield

            for _ in range(len(expected)):
                state = (yield from dut.fsm_state())
                # Use ">" for all other states, as FSM.delayed_enter uses anonymous states instead
                # of staying in RTW
                states += {
                    "READ": "r",
                    "WRITE": "w",
                }.get(state, ">")
                yield

            self.assertEqual(states, expected)

        dut = MultiplexerDUT()
        run_simulation(dut, main_generator(dut))

    def test_fsm_write_to_read_latency(self):
        # Verify the timing of WRITE to READ transition.
        def main_generator(dut):
            write_latency = math.ceil(dut.settings.phy.cwl / dut.settings.phy.nphases)
            wtr = dut.settings.timing.tWTR + write_latency + dut.settings.timing.tCCD or 0

            expected = "w" + (wtr - 1) * ">" + "r"
            states   = ""

            # Simulate until we are in WRITE
            yield from dut.bm_drivers[0].write()
            while (yield from dut.fsm_state()) != "WRITE":
                yield

            # Set read_available=1
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
        # Check that correct phases are being used during READ.
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

        dut        = MultiplexerDUT()
        generators = [
            main_generator(dut),
            timeout_generator(50),
        ]
        run_simulation(dut, generators)

    def test_steer_write_correct_phases(self):
        # Check that correct phases are being used during WRITE.
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
        # Verify that, for a single phase, commands are sent sequentially.
        def main_generator(dut):
            yield from dut.bm_drivers[2].write()
            yield from dut.bm_drivers[3].activate()
            ready = {2: dut.bank_machines[2].cmd.ready, 3: dut.bank_machines[3].cmd.ready}

            # Activate should appear first
            while not ((yield ready[2]) or (yield ready[3])):
                yield
            yield from dut.bm_drivers[3].nop()
            yield
            self.assertEqual((yield dut.dfi.phases[0].bank), 3)

            # Then write
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
        # Verify tRRD.
        def main_generator(dut):
            yield from dut.bm_drivers[2].activate()
            yield from dut.bm_drivers[3].activate()
            ready = {2: dut.bank_machines[2].cmd.ready, 3: dut.bank_machines[3].cmd.ready}

            # Wait for activate
            while not ((yield ready[2]) or (yield ready[3])):
                yield
            # Invalidate command that was ready
            if (yield ready[2]):
                yield from dut.bm_drivers[2].nop()
            else:
                yield from dut.bm_drivers[3].nop()
            yield

            # Wait for the second activate; start from 1 for the previous cycle
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
        # Verify tCCD.
        def main_generator(dut):
            yield from dut.bm_drivers[2].read()
            yield from dut.bm_drivers[3].read()
            ready = {2: dut.bank_machines[2].cmd.ready, 3: dut.bank_machines[3].cmd.ready}

            # Wait for activate
            while not ((yield ready[2]) or (yield ready[3])):
                yield
            # Invalidate command that was ready
            if (yield ready[2]):
                yield from dut.bm_drivers[2].nop()
            else:
                yield from dut.bm_drivers[3].nop()
            yield

            # Wait for the second activate; start from 1 for the previous cycle
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
        # Check that anti-starvation works according to controller settings.
        def main_generator(dut):
            yield from dut.bm_drivers[2].read()
            yield from dut.bm_drivers[3].write()

            # Go to WRITE
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

            # Wait for read anti starvation
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
        # Verify that data is transmitted from native interface to DFI.
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
        # Verify that data is transmitted from DFI to native interface.
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
        # After refresher command request, multiplexer waits for permission from all bank machines.
        def main_generator(dut):
            def assert_dfi_cmd(cas, ras, we):
                p = dut.dfi.phases[0]
                cas_n, ras_n, we_n = (yield p.cas_n), (yield p.ras_n), (yield p.we_n)
                self.assertEqual((cas_n, ras_n, we_n), (1 - cas, 1 - ras, 1 - we))

            for bm in dut.bank_machines:
                self.assertEqual((yield bm.refresh_req), 0)

            yield from dut.refresh_driver.refresh()
            yield

            # Bank machines get the request
            for bm in dut.bank_machines:
                self.assertEqual((yield bm.refresh_req), 1)
            # No command yet
            yield from assert_dfi_cmd(cas=0, ras=0, we=0)

            # Grant permission for refresh
            prng = random.Random(42)
            delays = [prng.randrange(100) for _ in dut.bank_machines]
            for t in range(max(delays) + 1):
                # Grant permission
                for delay, bm in zip(delays, dut.bank_machines):
                    if delay == t:
                        yield bm.refresh_gnt.eq(1)
                yield

                # Make sure thare is no command yet
                yield from assert_dfi_cmd(cas=0, ras=0, we=0)
            yield
            yield

            # Refresh command
            yield from assert_dfi_cmd(cas=1, ras=1, we=0)

        dut = MultiplexerDUT()
        run_simulation(dut, main_generator(dut))

    def test_requests_from_multiple_bankmachines(self):
        # Check complex communication scenario with requests from multiple bank machines
        # The communication is greatly simplified - data path is completely ignored, no responses
        # from PHY are simulated. Each bank machine performs a sequence of requests, bank machines
        # are ordered randomly and the DFI command data is checked to verify if all the commands
        # have been sent if correct per-bank order.

        # Tequests sequence on given bank machines
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

            # Artificially perform the work of LiteDRAMCrossbar by always picking only one request
            prng = random.Random(42)
            while len(non_empty()) > 0:
                # Pick random bank machine
                bm_num = prng.choice(non_empty())

                # Set given request
                request_char = bm_seq[bm_num].pop(0)
                yield from drivers[bm_num].request(request_char)
                yield

                # Wait for ready
                while not (yield bank_machines[bm_num].cmd.ready):
                    yield

                # Disable it
                yield from drivers[bm_num].nop()

            for _ in range(16):
                yield

        # Gather data on DFI
        DFISnapshot = namedtuple("DFICapture",
                                 ["cmd", "bank", "address", "wrdata_en", "rddata_en"])
        dfi_snapshots = []

        @passive
        def dfi_monitor(dfi):
            while True:
                # Capture current state of DFI lines
                phases = []
                for i, p in enumerate(dfi.phases):
                    # Transform cas/ras/we to command name
                    cas_n, ras_n, we_n = (yield p.cas_n), (yield p.ras_n), (yield p.we_n)
                    captured = {"cmd": dfi_cmd_to_char(cas_n, ras_n, we_n)}

                    # Capture rest of fields
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

        # Check captured DFI data with the description
        for snap in dfi_snapshots:
            for i, phase_snap in enumerate(snap):
                if phase_snap.cmd == "_":
                    continue

                # Distinguish bank machines by the bank number
                bank = phase_snap.bank
                # Find next command for the given bank
                cmd = bm_sequences[bank].pop(0)

                # Check if the captured data is correct
                self.assertEqual(phase_snap.cmd, cmd)
                if cmd in ["w", "r"]:
                    # Addresses are artificially forced to bank numbers in drivers
                    self.assertEqual(phase_snap.address, bank)
                    if cmd == "w":
                        self.assertEqual(phase_snap.wrdata_en, 1)
                    if cmd == "r":
                        self.assertEqual(phase_snap.rddata_en, 1)
