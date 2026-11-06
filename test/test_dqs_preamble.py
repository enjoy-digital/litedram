#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.fhdl.specials import Instance

from litex.gen.sim import run_simulation

from litedram.core import LiteDRAMCore
from litedram.modules import MT40A256M16, MT41K128M16
from litedram.phy.s7ddrphy import A7DDRPHY, K7DDRPHY
from litedram.phy.usddrphy import USPDDRPHY

TOGGLE    = 0b01010101
PREAMBLE  = 0b00010101
POSTAMBLE = 0b01010100


def get_pads(memtype):
    layout = [("a", 15 if memtype == "DDR4" else 14), ("ba", 2 if memtype == "DDR4" else 3), ("ras_n", 1), ("cas_n", 1),
        ("we_n", 1), ("cs_n", 1), ("clk_p", 1), ("clk_n", 1), ("cke", 1), ("odt", 1), ("reset_n", 1),
        ("dq", 16), ("dm", 2), ("dqs_p", 2), ("dqs_n", 2)]
    if memtype == "DDR4":
        layout += [("bg", 1), ("act_n", 1)]
    return Record(layout)


def item(instance, name):
    for it in instance.items:
        if it.name == name:
            return it.expr


def serializer_data(serializer):
    if serializer.of == "OSERDESE2":
        return Cat(*[item(serializer, f"D{n + 1}") for n in range(8)])
    return item(serializer, "D")


class DUT(Module):
    # Controller and PHY, with the write data only driven during the wdata.ready cycle.
    def __init__(self, phy_cls, memtype, module_cls, sys_clk_freq, **kwargs):
        self.phy = phy_cls(get_pads(memtype), memtype=memtype, sys_clk_freq=sys_clk_freq,
            iodelay_clk_freq=200e6 if phy_cls is not USPDDRPHY else 400e6, **kwargs)
        self.submodules += self.phy
        module = module_cls(sys_clk_freq, "1:4")
        self.submodules.core = LiteDRAMCore(self.phy, module.geom_settings, module.timing_settings, sys_clk_freq)
        self.port = self.core.crossbar.get_port()
        self.comb += self.port.wdata.data.eq(Replicate(self.port.wdata.ready, self.port.data_width))

        # Serializers data inputs of the first DQ and DQS, found through their IO buffers.
        instances   = [s for s in self.phy._fragment.specials if isinstance(s, Instance)]
        serializers = [i for i in instances if i.of in ["OSERDESE2", "OSERDESE3"]]
        self.dq_d = self.dqs_d = None
        for buf in [i for i in instances if i.of.startswith("IOBUF")]:
            for serializer in serializers:
                tq = item(serializer, "TQ" if serializer.of == "OSERDESE2" else "T_OUT")
                if tq is not None and tq is item(buf, "T"):
                    if "DS" in buf.of:
                        self.dqs_d = self.dqs_d if self.dqs_d is not None else serializer_data(serializer)
                    else:
                        self.dq_d  = self.dq_d  if self.dq_d  is not None else serializer_data(serializer)
        # The vendor primitives can't be simulated, only their inputs are looked at.
        self.phy._fragment.specials = {s for s in self.phy._fragment.specials if not isinstance(s, Instance)}


class TestDQSPreamble(unittest.TestCase):
    def capture(self, nwrites, **kwargs):
        dut = DUT(**kwargs)
        log = []

        def writes():
            for _ in range(40):
                yield
            yield dut.port.cmd.we.eq(1)
            yield dut.port.wdata.we.eq(2**(dut.port.data_width//8) - 1)
            for n in range(nwrites):
                yield dut.port.cmd.valid.eq(1)
                yield dut.port.cmd.addr.eq(n)
                yield
                while not (yield dut.port.cmd.ready):
                    yield
            yield dut.port.cmd.valid.eq(0)

        def monitor():
            for _ in range(120):
                log.append(((yield dut.dq_d), (yield dut.dqs_d)))
                yield

        run_simulation(dut, [writes(), monitor()], clocks={
            "sys": 10, "sys4x": 2.5, "sys4x_dqs": 2.5, "sys4x_io": 2.5, "ic": 10, "iodelay": 5})
        return log

    def check(self, nwrites, **kwargs):
        log   = self.capture(nwrites, with_dqs_preamble=True, **kwargs)
        beats = [i for i, (dq, _) in enumerate(log) if dq]
        self.assertEqual(len(beats), nwrites)
        self.assertEqual(beats, list(range(beats[0], beats[0] + nwrites))) # Back to back.
        self.assertEqual(log[beats[0] - 2][1],  TOGGLE)
        self.assertEqual(log[beats[0] - 1][1],  PREAMBLE)
        for beat in beats:
            self.assertEqual(log[beat][1], TOGGLE)
        self.assertEqual(log[beats[-1] + 1][1], POSTAMBLE)
        self.assertEqual(log[beats[-1] + 2][1], TOGGLE)

    def test_a7_ddr3(self):
        for nwrites in [1, 3]:
            with self.subTest(nwrites=nwrites):
                self.check(nwrites, phy_cls=A7DDRPHY, memtype="DDR3", module_cls=MT41K128M16, sys_clk_freq=100e6)

    def test_k7_ddr3(self):
        for nwrites in [1, 3]:
            with self.subTest(nwrites=nwrites):
                self.check(nwrites, phy_cls=K7DDRPHY, memtype="DDR3", module_cls=MT41K128M16, sys_clk_freq=125e6)

    def test_usp_ddr4(self):
        for nwrites in [1, 3]:
            with self.subTest(nwrites=nwrites):
                self.check(nwrites, phy_cls=USPDDRPHY, memtype="DDR4", module_cls=MT40A256M16, sys_clk_freq=125e6)

    def test_disabled_by_default(self):
        log = self.capture(1, phy_cls=A7DDRPHY, memtype="DDR3", module_cls=MT41K128M16, sys_clk_freq=100e6)
        self.assertEqual({dqs for _, dqs in log[10:]}, {TOGGLE})

    def test_requires_1_4(self):
        with self.assertRaises(AssertionError):
            A7DDRPHY(get_pads("DDR2"), memtype="DDR2", nphases=2, sys_clk_freq=100e6, with_dqs_preamble=True)


if __name__ == "__main__":
    unittest.main()
