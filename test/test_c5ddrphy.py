#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.sim import run_simulation

from litex.soc.interconnect.csr_bus import CSRBank

from litedram.phy.c5ddrphy import CycloneVDDRPHY


class TestCycloneVDDRPHY(unittest.TestCase):
    @staticmethod
    def make_phy():
        pads = Record([
            ("a", 15), ("ba", 3), ("cs_n", 1), ("ras_n", 1), ("cas_n", 1),
            ("we_n", 1), ("cke", 1), ("odt", 1), ("reset_n", 1),
            ("clk_p", 1), ("clk_n", 1), ("dq", 8), ("dm", 1),
            ("dqs_p", 1), ("dqs_n", 1), ("rzq", 1),
        ])
        ports = {}

        def native_backend(**signals):
            ports.update({name[2:]: signal for name, signal in signals.items()})
            return Module()

        phy = CycloneVDDRPHY(pads, Signal(), Signal(), cl=6, cwl=5, io_backend=native_backend)
        phy.submodules += CSRBank([phy._calibration, phy._read_error])
        fragment = phy.get_fragment()
        # The simulation drives the clocks and models the native lane outputs.
        fragment.specials = {s for s in fragment.specials if not isinstance(s, AsyncResetSynchronizer)}
        return phy, fragment, ports, pads

    def test_calibration_status(self):
        phy, fragment, ports, _ = self.make_phy()
        self.assertEqual(phy._calibration.size, 2)

        def generator():
            cases = [
                # PHY readiness, failure, AFI write latency, packed CSR value.
                (0, 0, 0, 0b00),
                (1, 0, 7, 0b01),
                (1, 0, 8, 0b10),
                (0, 1, 0, 0b10),
            ]
            for success, failed, latency, expected in cases:
                yield ports["cal_success"].eq(success)
                yield ports["cal_fail"].eq(failed)
                yield ports["afi_wlat"].eq(latency)
                for _ in range(8):
                    yield
                self.assertEqual((yield phy._calibration.status), expected)
                self.assertEqual((yield phy.calibrated), expected & 1)

        run_simulation(fragment, generator(), clocks={"sys": 20, "afi": 10})

    def test_write_leveling_feedback_uses_dfi_read_data(self):
        phy, fragment, ports, _ = self.make_phy()
        self.assertTrue(phy.settings.write_leveling)

        def generator():
            yield phy._wlevel_en.storage.eq(1)
            yield ports["write_level_feedback"].eq(1)
            yield
            for phase in phy.dfi.phases:
                self.assertEqual((yield phase.rddata_valid), 1)
                self.assertEqual((yield phase.rddata), 0x0101)
            yield ports["write_level_feedback"].eq(0)
            yield
            self.assertEqual((yield phy.dfi.phases[0].rddata), 0)
            yield phy._wlevel_en.storage.eq(0)
            yield
            self.assertEqual((yield phy.dfi.phases[0].rddata_valid), 0)

        run_simulation(fragment, generator(), clocks={"sys": 20, "afi": 10})

    def test_read_burst_and_missing_return(self):
        phy, fragment, ports, _ = self.make_phy()
        phases = phy.dfi.phases
        payload = [0x2713, 0x8945, 0xcdab, 0x01ef]
        self.assertEqual(phy.settings.read_latency, 37)

        def afi_model():
            yield ports["cal_success"].eq(1)
            while not (yield ports["afi_rdata_en"]):
                yield
            for _ in range(6):
                yield
            yield ports["afi_rdata_valid"].eq(3)
            for low, high in zip(payload[::2], payload[1::2]):
                yield ports["afi_rdata"].eq(low | (high << 16))
                yield
            yield ports["afi_rdata_valid"].eq(0)
            yield

        def system():
            for _ in range(8):
                yield
            self.assertEqual((yield phy.calibrated), 1)
            yield phases[3].rddata_en.eq(1)
            yield
            yield phases[3].rddata_en.eq(0)
            for cycle in range(phy.settings.read_latency + 2):
                expected = cycle == phy.settings.read_latency
                for phase, data in zip(phases, payload):
                    self.assertEqual((yield phase.rddata_valid), expected)
                    if expected:
                        self.assertEqual((yield phase.rddata), data)
                yield
            self.assertEqual((yield phy._read_error.status), 0)

            # A second request gets no AFI response and must flag the missed slot.
            yield phases[3].rddata_en.eq(1)
            yield
            yield phases[3].rddata_en.eq(0)
            for _ in range(phy.settings.read_latency + 3):
                self.assertEqual((yield phases[3].rddata_valid), 0)
                yield
            self.assertEqual((yield phy._read_error.status), 1)

        run_simulation(fragment, {"sys": system(), "afi": afi_model()}, clocks={"sys": 20, "afi": 10})

    def test_native_frame_pipeline_delays_write_command_and_data_together(self):
        phy, fragment, ports, _ = self.make_phy()
        phases = phy.dfi.phases
        payload = [0x2713, 0x8945, 0xcdab, 0x01ef]
        commands = []
        words = []

        def afi():
            yield ports["cal_success"].eq(1)
            yield ports["afi_wlat"].eq(1)
            for cycle in range(48):
                if (yield ports["afi_cs_n"]) != 3:
                    commands.append((cycle, (yield ports["afi_addr"])))
                if (yield ports["afi_wdata_valid"]):
                    words.append((cycle, (yield ports["afi_wdata"])))
                yield

        def system():
            for _ in range(10):
                yield
            for phase, value in zip(phases, payload):
                yield phase.wrdata.eq(value)
            yield phases[3].address.eq(0x123)
            yield phases[3].cs_n.eq(0)
            yield phases[3].cas_n.eq(0)
            yield phases[3].we_n.eq(0)
            yield phases[3].wrdata_en.eq(1)
            yield
            yield phases[3].cs_n.eq(1)
            yield phases[3].wrdata_en.eq(0)

        run_simulation(fragment, {"sys": system(), "afi": afi()}, clocks={"sys": 20, "afi": 10})

        self.assertEqual(len(commands), 1)
        command_cycle, address = commands[0]
        self.assertEqual(address, 0x123 << 15)
        self.assertEqual(words, [(command_cycle + 2, 0x89452713),
                                 (command_cycle + 3, 0x01efcdab)])

    def test_termination_ports(self):
        _, _, ports, pads = self.make_phy()
        self.assertIs(ports["oct_rzqin"], pads.rzq)
        self.assertNotIn("seriesterminationcontrol", ports)
        self.assertNotIn("parallelterminationcontrol", ports)
