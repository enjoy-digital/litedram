#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.fhdl.tools import list_targets
from migen.sim import run_simulation

from litex.soc.interconnect.csr_bus import CSRBank

from litedram.phy.c5ddrphy import CycloneVDDRPHY


CLOCKS = {"sys": 20, "afi": 10}

# Clock domains of the CRG used by the PHY and its byte lanes, with their period for the simulation
# (the clocks of the hard I/O only reach the wrappers, which are not simulated: slow).
CRG_CLOCKS = {
    "sys"               : 20,
    "afi"               : 10,
    "afi_phy"           : 1000,
    "pll_mem"           : 1000,
    "pll_mem_phy"       : 1000,
    "pll_write"         : 1000,
    "pll_write_pre_phy" : 1000,
    "pll_addr_cmd"      : 1000,
    "pll_config"        : 1000,
}

# Board arguments of the native byte lanes (arbitrary names, timing of the validated board).
LANE_ARGS = dict(
    ip_name          = "ddr3_ip",
    lane_name        = "ddr3_lane",
    mem_clk_freq     = 300e6,
    default_settings = 0x080d6731,
)

def get_pads(lanes=1):
    return Record([
        ("a",       15),
        ("ba",       3),
        ("cs_n",     1),
        ("ras_n",    1),
        ("cas_n",    1),
        ("we_n",     1),
        ("cke",      1),
        ("odt",      1),
        ("reset_n",  1),
        ("clk_p",    1),
        ("clk_n",    1),
        ("dq",       8*lanes),
        ("dm",       lanes),
        ("dqs_p",    lanes),
        ("dqs_n",    lanes),
        ("rzq",      1),
    ])

def get_phy(**kwargs):
    """PHY with its I/O backend replaced by its ports (name without direction: signal)."""
    pads  = get_pads()
    ports = {}

    def io_backend(ip_name, lane_name, mem_clk_freq, default_settings, **signals):
        ports.update({name[2:]: signal for name, signal in signals.items()})
        return Module()

    phy = CycloneVDDRPHY(pads, cl=6, cwl=5, sys_clk_freq=75e6, io_backend=io_backend, **kwargs)
    phy.submodules += CSRBank([phy._calibration, phy._read_error])
    # The simulation drives the clocks and models the native lane outputs.
    return phy, phy.get_fragment(), ports, pads

def get_native_phy(lanes=1, **kwargs):
    """PHY with its native byte lanes, without their wrappers (simulation of the fabric logic)."""
    phy = CycloneVDDRPHY(get_pads(lanes), cl=6, cwl=5, sys_clk_freq=75e6, **{**LANE_ARGS, **kwargs})
    fragment = phy.get_fragment()
    fragment.specials = {s for s in fragment.specials
                         if not isinstance(s, (Instance, AsyncResetSynchronizer))}
    # The internal clock domains of the byte lanes are clocked by the simulation (startup on afi,
    # I/O scan chains on the configuration clock, FIFO resets without logic).
    clocks = {cd.name: {"dll_init": 10, "scc": 20}.get(cd.name, 1000) for cd in fragment.clock_domains}
    return phy, fragment, {**clocks, **CRG_CLOCKS}


class TestCycloneVDDRPHY(unittest.TestCase):
    def test_calibration_status(self):
        phy, fragment, ports, _ = get_phy()
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

        run_simulation(fragment, generator(), clocks=CLOCKS)

    def test_write_leveling_feedback(self):
        phy, fragment, ports, _ = get_phy()
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

        run_simulation(fragment, generator(), clocks=CLOCKS)

    def test_read_burst_and_missing_return(self):
        phy, fragment, ports, _ = get_phy()
        phases  = phy.dfi.phases
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

        run_simulation(fragment, {"sys": system(), "afi": afi_model()}, clocks=CLOCKS)

    def test_write_command_data_alignment(self):
        phy, fragment, ports, _ = get_phy()
        phases   = phy.dfi.phases
        payload  = [0x2713, 0x8945, 0xcdab, 0x01ef]
        commands = []
        words    = []

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

        run_simulation(fragment, {"sys": system(), "afi": afi()}, clocks=CLOCKS)

        self.assertEqual(len(commands), 1)
        command_cycle, address = commands[0]
        self.assertEqual(address, 0x123 << 15)
        self.assertEqual(words, [(command_cycle + 2, 0x89452713),
                                 (command_cycle + 3, 0x01efcdab)])

    def test_termination_ports(self):
        _, _, ports, pads = get_phy()
        self.assertIs(ports["oct_rzqin"], pads.rzq)
        self.assertNotIn("seriesterminationcontrol", ports)
        self.assertNotIn("parallelterminationcontrol", ports)

    def test_clock_domains(self):
        # The clock domains come from the CRG: the PHY creates none of them and holds no PLL.
        phy       = CycloneVDDRPHY(get_pads(lanes=2), cl=6, cwl=5, sys_clk_freq=75e6, **LANE_ARGS)
        fragment  = phy.get_fragment()
        created   = {cd.name for cd in fragment.clock_domains}
        self.assertEqual(created & set(CRG_CLOCKS), set())
        instances = [s for s in fragment.specials if isinstance(s, Instance)]
        self.assertNotIn("ddr3_ip_pll0", {instance.of for instance in instances})
        def clocks(instance):
            return {item.name: item.expr.cd for item in instance.items
                    if isinstance(item, Instance.Input) and isinstance(item.expr, ClockSignal)}
        lane = next(i for i in instances if i.name_override == "ddr3_lane0")
        self.assertEqual(clocks(lane), {
            "write_strobe_clock_in"   : "pll_mem_phy",
            "core_clock_in"           : "afi",
            "fr_clock_in"             : "pll_write",
            "hr_clock_in"             : "afi_phy",
            "strobe_ena_hr_clock_in"  : "afi",
            "config_clock_in"         : "pll_config",
        })
        pads = next(i for i in instances if i.of == "ddr3_ip_p0_addr_cmd_pads")
        self.assertEqual(clocks(pads), {
            "pll_afi_clk"             : "afi",
            "pll_mem_clk"             : "pll_mem",
            "pll_mem_phy_clk"         : "pll_mem_phy",
            "pll_afi_phy_clk"         : "afi_phy",
            "pll_write_clk"           : "pll_write",
            "phy_ddio_addr_cmd_clk"   : "pll_addr_cmd",
        })
        dll = next(i for i in instances if i.of == "altera_mem_if_dll_cyclonev")
        self.assertEqual(clocks(dll), {"clk": "pll_write_pre_phy"})

    def test_native_startup(self):
        # The byte lanes start with the lock of the PLL of the CRG and report the end of their
        # startup (DLL, I/O scan chains, VFIFO) on ready, for the reset of afi and sys.
        phy, fragment, clocks = get_native_phy()

        def generator():
            self.assertEqual((yield phy.ready), 0)
            yield phy.pll_locked.eq(1)
            cycles = 0
            while not (yield phy.ready) and cycles < 4096:
                cycles += 1
                yield
            self.assertEqual((yield phy.ready), 1)
            # DLL (2048 AFI cycles) then VFIFO (1024 AFI cycles) startup.
            self.assertGreater(cycles, 2048 + 1024)
            for _ in range(64):
                yield
            self.assertEqual((yield phy._calibration.fields.success), 1)
            self.assertEqual((yield phy._calibration.fields.failed),  0)
            # Loss of lock.
            yield phy.pll_locked.eq(0)
            yield
            self.assertEqual((yield phy.ready), 0)

        run_simulation(fragment, {"afi": generator()}, clocks=clocks)

    def test_board_arguments(self):
        phy       = CycloneVDDRPHY(get_pads(lanes=2), cl=6, cwl=5, sys_clk_freq=75e6, **LANE_ARGS)
        lane      = phy.io_backend
        instances = [s for s in lane._fragment.specials if isinstance(s, Instance)]
        modules   = {instance.of for instance in instances}
        self.assertIn("ddr3_ip_p0_addr_cmd_pads", modules)
        lanes = {i.name_override: i for i in instances if i.of == "altdq_dqs2_acv_cyclonev"}
        self.assertEqual(sorted(lanes), ["ddr3_lane0", "ddr3_lane1"])
        def parameters(instance):
            return {item.name: getattr(item.value, "value", item.value)
                    for item in instance.items if isinstance(item, Instance.Parameter)}
        self.assertEqual(parameters(lanes["ddr3_lane0"])["INPUT_FREQ"],    "300.0")
        self.assertEqual(parameters(lanes["ddr3_lane0"])["INPUT_FREQ_PS"], "3333 ps")
        dll = next(i for i in instances if i.of == "altera_mem_if_dll_cyclonev")
        self.assertEqual(parameters(dll)["DLL_INPUT_FREQUENCY_PS_STR"], "3333 ps")
        self.assertEqual(lane._settings.storage.reset.value, 0x080d6731)
        self.assertEqual(lane._settings.fields.capture_delay.reset.value, 13)
        # Fixed name of the capture register placed by the target.
        names = {s.name_override for s in list_targets(phy.get_fragment())}
        self.assertIn("ddr3_lane_captured_valid", names)

    def test_board_arguments_required(self):
        for name in ("sys_clk_freq", "ip_name", "lane_name", "default_settings"):
            with self.subTest(name=name):
                args = {"sys_clk_freq": 75e6, **LANE_ARGS, name: None}
                with self.assertRaisesRegex(ValueError, name):
                    CycloneVDDRPHY(get_pads(), cl=6, cwl=5, **args)
        # Bit 15 belongs to no field of the settings register.
        with self.assertRaisesRegex(ValueError, "default_settings"):
            CycloneVDDRPHY(get_pads(), cl=6, cwl=5, sys_clk_freq=75e6,
                **{**LANE_ARGS, "default_settings": 0x080d6731 | (1 << 15)})

    def test_mem_clk_freq(self):
        # The DRAM clock is 4 x sys: derived from sys_clk_freq, checked when it is passed.
        phy = CycloneVDDRPHY(get_pads(), cl=6, cwl=5, sys_clk_freq=75e6,
            **{**LANE_ARGS, "mem_clk_freq": None})
        dll = next(s for s in phy.io_backend._fragment.specials
                   if isinstance(s, Instance) and s.of == "altera_mem_if_dll_cyclonev")
        self.assertEqual(dll.get_io("clk").cd, "pll_write_pre_phy")
        period = next(item.value for item in dll.items
                      if isinstance(item, Instance.Parameter) and item.name == "DLL_INPUT_FREQUENCY_PS_STR")
        self.assertEqual(period, "3333 ps")
        with self.assertRaisesRegex(ValueError, "mem_clk_freq"):
            CycloneVDDRPHY(get_pads(), cl=6, cwl=5, sys_clk_freq=50e6, **LANE_ARGS)
