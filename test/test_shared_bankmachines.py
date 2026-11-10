#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Shared bank machines (ControllerSettings.nbankmachines): data integrity of the full controller
(bank machines, multiplexer, refresher, crossbar) on the SDRAM PHY model, with several ports doing
random reads/writes, and resources/settings checks."""

import os
import random
import unittest

from migen import *

from litedram import modules
from litedram.common import burst_lengths
from litedram.phy.model import SDRAMPHYModel
from litedram.core.controller import LiteDRAMController, ControllerSettings
from litedram.core.crossbar import LiteDRAMCrossbar
from litedram.core.bankmachine import BankMachine


# Reduced geometry; the timings are the module's. The controller sees 2048 rows (A10 in the DFI
# address for auto-precharge/precharge-all), the PHY model only 16 (small memories, fast simulation:
# it stores the activated row in 4 bits, the test only uses rows < 16) with the same address width.
class _SDR(modules.MT48LC16M16):  nrows, ncols = 2048, 64
class _DDR2(modules.MT47H64M16):  nrows, ncols = 2048, 64
class _DDR3(modules.MT41K128M16): nrows, ncols = 2048, 64
class _DDR4(modules.MT40A512M16): nrows, ncols = 2048, 64


FULL      = bool(int(os.environ.get("LITEDRAM_TEST_FULL", "0")))
NACCESSES = 120 if FULL else 40


class SharedBankMachinesDUT(Module):
    def __init__(self, module_cls, rate, clk_freq, nports, controller_settings):
        module = module_cls(clk_freq, rate)
        module.timing_settings.tREFI = 200 # Several refreshes during the test.
        model_module = type("_Model", (module_cls,), {"nrows": 16})(clk_freq, rate)
        model_module.geom_settings.addressbits = module.geom_settings.addressbits # A10.
        self.submodules.model = model = SDRAMPHYModel(model_module, data_width=16, clk_freq=clk_freq)
        self.submodules.controller = controller = LiteDRAMController(
            phy_settings        = model.settings,
            geom_settings       = module.geom_settings,
            timing_settings     = module.timing_settings,
            clk_freq            = clk_freq,
            controller_settings = controller_settings)
        self.comb += controller.dfi.connect(model.dfi)
        self.submodules.crossbar = crossbar = LiteDRAMCrossbar(controller.interface)
        self.ports = [crossbar.get_port() for i in range(nports)]
        self.colbits  = module.geom_settings.colbits - log2_int(burst_lengths[module.memtype])
        self.bankbits = module.geom_settings.bankbits
        self.nrows    = model_module.nrows


def port_traffic(dut, port, prng, naccesses, addresses, stats):
    """Random reads/writes of a port on its own addresses, with a scoreboard: the native port
    executes the commands of a port in order, so a read returns the last data written before it."""
    memory   = {}
    wdatas   = []
    expected = []
    done     = {"cmds": False}

    def cmds():
        for n in range(naccesses):
            addr = prng.choice(addresses)
            # Bursts on the same row and bank switches: mostly the same row/bank as the previous
            # access, sometimes another bank (or row).
            we   = (addr not in memory) or (prng.randrange(2) == 0)
            yield port.cmd.valid.eq(1)
            yield port.cmd.we.eq(we)
            yield port.cmd.addr.eq(addr)
            yield
            while not (yield port.cmd.ready):
                yield
            yield port.cmd.valid.eq(0)
            if we:
                data = prng.randrange(2**port.data_width)
                memory[addr] = data
                wdatas.append(data)
                stats["writes"] += 1
            else:
                expected.append((addr, memory[addr]))
                stats["reads"] += 1
            for _ in range(prng.choice([0, 0, 0, 1, 4])):
                yield
        done["cmds"] = True

    @passive
    def wdata():
        yield port.wdata.we.eq(2**len(port.wdata.we) - 1)
        while True:
            if wdatas:
                yield port.wdata.valid.eq(1)
                yield port.wdata.data.eq(wdatas[0])
                yield
                while not (yield port.wdata.ready):
                    yield
                wdatas.pop(0)
                yield port.wdata.valid.eq(0)
            else:
                yield

    @passive
    def rdata():
        yield port.rdata.ready.eq(1)
        while True:
            yield
            if (yield port.rdata.valid):
                if not expected: # Read data without a read command on this port.
                    stats["errors"] += 1
                    continue
                addr, data = expected.pop(0)
                if (yield port.rdata.data) != data:
                    stats["errors"] += 1

    def wait():
        # Bounded: a hang (e.g. read data routed to another port) fails instead of never ending.
        for _ in range(200*naccesses):
            if done["cmds"] and not expected and not wdatas:
                return
            yield
        stats["timeouts"] += 1

    return [cmds(), wdata(), rdata(), wait()]


@passive
def dfi_protocol_monitor(dfi, nbanks, stats):
    """Bank states on the DFI commands: ACTIVATE on a closed bank, READ/WRITE on an open bank (A10:
    auto-precharge), PRECHARGE (A10: all banks), REFRESH with all the banks closed. Catches commands
    sent to the wrong bank (e.g. the PRECHARGE of a shared bank machine), that the timings checker
    and the PHY model do not see."""
    opened = [False]*nbanks
    while True:
        yield
        for phase in dfi.phases:
            if (yield phase.cs_n):
                continue
            ras = not (yield phase.ras_n)
            cas = not (yield phase.cas_n)
            we  = not (yield phase.we_n)
            bank = (yield phase.bank)
            a10  = ((yield phase.address) >> 10) & 1
            if ras and not cas and not we:   # ACTIVATE.
                if opened[bank]:
                    stats["protocol"] += 1
                opened[bank] = True
            elif ras and not cas and we:     # PRECHARGE.
                if a10:
                    opened = [False]*nbanks
                else:
                    opened[bank] = False
            elif not ras and cas:            # READ/WRITE.
                if not opened[bank]:
                    stats["protocol"] += 1
                if a10:
                    opened[bank] = False
            elif ras and cas and not we:     # REFRESH.
                if any(opened):
                    stats["protocol"] += 1
                stats["refreshes"] += 1


class TestSharedBankMachines(unittest.TestCase):
    def data_test(self, module_cls, rate, clk_freq, nbankmachines, nports=2, naccesses=120, seed=0,
                  **settings_kwargs):
        cs   = ControllerSettings(nbankmachines=nbankmachines, **settings_kwargs)
        dut  = SharedBankMachinesDUT(module_cls, rate, clk_freq, nports, cs)
        prng = random.Random(seed)
        stats = {"writes": 0, "reads": 0, "errors": 0, "protocol": 0, "refreshes": 0, "timeouts": 0}
        # Few rows/columns per bank (row hits and misses), all the banks, interleaved between the
        # ports (port i uses the addresses with column % nports == i: same rows and banks).
        rows  = [prng.randrange(dut.nrows) for i in range(3)]
        gens  = []
        for i, port in enumerate(dut.ports):
            addresses = [(row << (dut.bankbits + dut.colbits)) | (bank << dut.colbits) | col
                for row in rows for bank in range(2**dut.bankbits) for col in range(i, 2*nports, nports)]
            gens += port_traffic(dut, port, random.Random(seed + 1 + i), naccesses, addresses, stats)
        gens.append(dfi_protocol_monitor(dut.controller.dfi, 2**dut.bankbits, stats))
        run_simulation(dut, gens)
        self.assertEqual(stats["timeouts"], 0)
        self.assertEqual(stats["errors"], 0)
        self.assertEqual(stats["protocol"], 0)
        self.assertGreater(stats["refreshes"], 0)
        self.assertGreater(stats["reads"], nports*naccesses//8)
        return dut

    def check_bankmachines(self, dut, nbankmachines):
        bms = [m for name, m in dut.controller._submodules if isinstance(m, BankMachine)]
        self.assertEqual(len(bms), nbankmachines)

    # Data integrity -------------------------------------------------------------------------------
    # The full matrix (all the nbankmachines values, more traffic) is slow in simulation: run it with
    # LITEDRAM_TEST_FULL=1.

    def test_sdr_1to1(self):
        for nbankmachines in ([None, 2, 1] if FULL else [1]):
            with self.subTest(nbankmachines=nbankmachines):
                self.data_test(_SDR, "1:1", 50e6, nbankmachines, naccesses=NACCESSES)

    def test_ddr2_1to2(self):
        for nbankmachines in ([2, 1] if FULL else []):
            with self.subTest(nbankmachines=nbankmachines):
                self.data_test(_DDR2, "1:2", 100e6, nbankmachines, naccesses=NACCESSES)

    def test_ddr3_1to4(self):
        for nbankmachines in ([None, 4, 2, 1] if FULL else [2]):
            with self.subTest(nbankmachines=nbankmachines):
                dut = self.data_test(_DDR3, "1:4", 100e6, nbankmachines, nports=3, naccesses=NACCESSES)
                self.check_bankmachines(dut, nbankmachines or 8)

    def test_ddr3_1to4_without_auto_precharge(self):
        for nbankmachines in ([2, 1] if FULL else [1]):
            with self.subTest(nbankmachines=nbankmachines):
                self.data_test(_DDR3, "1:4", 100e6, nbankmachines, with_auto_precharge=False,
                    naccesses=NACCESSES)

    def test_ddr3_1to4_cmd_buffer(self):
        for depth, buffered in ([(1, False), (2, True)] if FULL else []):
            with self.subTest(depth=depth, buffered=buffered):
                self.data_test(_DDR3, "1:4", 100e6, 2, cmd_buffer_depth=depth,
                    cmd_buffer_buffered=buffered, naccesses=NACCESSES)

    def test_ddr4_1to4(self):
        for nbankmachines in ([4, 1] if FULL else [4]):
            with self.subTest(nbankmachines=nbankmachines):
                self.data_test(_DDR4, "1:4", 200e6, nbankmachines, naccesses=NACCESSES)

    # Settings -------------------------------------------------------------------------------------

    def test_invalid_nbankmachines(self):
        for nbankmachines in [3, 16]:
            with self.subTest(nbankmachines=nbankmachines):
                with self.assertRaises(ValueError):
                    SharedBankMachinesDUT(_DDR3, "1:4", 100e6, 1, ControllerSettings(nbankmachines=nbankmachines))

    def test_default_one_bankmachine_per_bank(self):
        for nbankmachines in [None, 8]:
            with self.subTest(nbankmachines=nbankmachines):
                dut = SharedBankMachinesDUT(_DDR3, "1:4", 100e6, 1, ControllerSettings(nbankmachines=nbankmachines))
                self.check_bankmachines(dut, 8)
