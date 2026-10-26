#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *
from migen.fhdl import verilog

from litex.build.io import SDRInput, SDROutput, SDRTristate

from litedram.phy.gensdrphy import GENSDRPHY, HalfRateGENSDRPHY


class SDRIOModel(Module):
    """Simulation stand-in for LiteX's SDRInput/SDROutput specials: a register on their clock.

    Like the vendor implementations it takes the clock domain from the special's ClockSignal, which
    ClockDomainsRenamer renames (the generic fallback, InferredSDRIO, uses the clk_domain name the
    special cached at construction, see test_half_rate_verilog_pads_clock).
    """
    def __init__(self, t):
        sd  = getattr(self.sync, t.clk.cd)
        sd += t.o.eq(t.i)

    @staticmethod
    def lower(t):
        return SDRIOModel(t)


def sdr_tristate_model(dq_o=None, dq_oe=None):
    """Simulation stand-in for LiteX's SDRTristate special.

    The generic lowering (InferredSDRTristate) ends in a Tristate special that Migen's simulator
    cannot run (and registers oe in a derived clock domain the simulator never ticks), so the
    SDRTristate is modelled directly: o/oe/i registered on its clock, like the IO registers of the
    generic fallback. The test drives the pad (`io`) as the DRAM would and reads what the PHY
    drives from dq_o/dq_oe (indexed by the pad bit).
    """
    class Model(Module):
        def __init__(self, t):
            o  = Signal(len(t.o))
            oe = Signal(len(t.oe))
            sd = getattr(self.sync, t.clk.cd)
            sd += [o.eq(t.o), oe.eq(t.oe)]
            if t.i is not None:
                sd += t.i.eq(t.io)
            if dq_o is not None:
                dq_o[t.io.start]  = o
                dq_oe[t.io.start] = oe

        @staticmethod
        def lower(t):
            return Model(t)

    return Model


class TestGENSDRPHY(unittest.TestCase):
    databits = 16

    @staticmethod
    def get_pads(with_dm=True, with_cs_n=True, with_cke=True):
        layout = [
            ("a",     13),
            ("ba",     2),
            ("ras_n",  1),
            ("cas_n",  1),
            ("we_n",   1),
            ("dq",    16),
        ]
        if with_dm:
            layout.append(("dm", 2))
        if with_cs_n:
            layout.append(("cs_n", 1))
        if with_cke:
            layout.append(("cke", 1))
        return Record(layout)

    def test_settings(self):
        for cls, nphases in [(GENSDRPHY, 1), (HalfRateGENSDRPHY, 2)]:
            for sys_clk_freq, cl, expected_cl in [
                (100e6, None, 2), # Default CL from the SDR frequency table.
                ( 50e6, None, 2),
                (100e6,    2, 2),
                (100e6,    3, 3),
            ]:
                for with_dm in [True, False]:
                    with self.subTest(cls=cls.__name__, sys_clk_freq=sys_clk_freq, cl=cl, with_dm=with_dm):
                        phy = cls(self.get_pads(with_dm=with_dm), sys_clk_freq=sys_clk_freq, cl=cl)
                        s   = phy.settings
                        self.assertEqual(s.phytype,      cls.__name__)
                        self.assertEqual(s.memtype,      "SDR")
                        self.assertEqual(s.databits,     self.databits)
                        self.assertEqual(s.dfi_databits, self.databits)
                        self.assertEqual(s.nranks,       1)
                        self.assertEqual(s.nphases,      nphases)
                        self.assertEqual(s.rdphase,      0)
                        self.assertEqual(s.wrphase,      0)
                        self.assertEqual(s.cl,           expected_cl)
                        self.assertEqual(s.write_latency, 0)
                        self.assertEqual(s.with_dm,      with_dm)
                        if cls is GENSDRPHY:
                            self.assertEqual(s.read_latency, expected_cl + 1)
                        else:
                            self.assertEqual(s.read_latency, (expected_cl + 1)//2 + 1)
                        self.assertEqual(len(phy.dfi.phases), nphases)
                        self.assertEqual(len(phy.dfi.p0.wrdata), self.databits)
        # No default CL above the SDR table.
        with self.assertRaises(ValueError):
            GENSDRPHY(self.get_pads(), sys_clk_freq=200e6)

    def test_pads(self):
        # a/ba/ras_n/cas_n/we_n/dq are required, dm/cs_n/cke optional.
        for with_cs_n, with_cke in [(True, True), (False, True), (True, False), (False, False)]:
            with self.subTest(with_cs_n=with_cs_n, with_cke=with_cke):
                phy = GENSDRPHY(self.get_pads(with_cs_n=with_cs_n, with_cke=with_cke), sys_clk_freq=100e6)
                self.assertEqual(phy.settings.nranks, 1)
        for missing, error in [("a", AttributeError), ("ba", AttributeError), ("ras_n", ValueError),
                               ("cas_n", ValueError), ("we_n", ValueError)]:
            with self.subTest(missing=missing):
                pads = self.get_pads()
                delattr(pads, missing)
                with self.assertRaises(error):
                    GENSDRPHY(pads, sys_clk_freq=100e6)

    def test_verilog(self):
        for cls in [GENSDRPHY, HalfRateGENSDRPHY]:
            with self.subTest(cls=cls.__name__):
                pads = self.get_pads()
                phy  = cls(pads, sys_clk_freq=100e6)
                v    = str(verilog.convert(phy, ios=set(pads.flatten())))
                for pad in ["a", "ba", "ras_n", "cas_n", "we_n", "cs_n", "cke", "dm"]:
                    width = len(getattr(pads, pad))
                    self.assertIn(f"output reg {f'[{width - 1}:0] ' if width > 1 else ''}{pad}", v)
                self.assertIn("inout [15:0] dq", v)

    def test_write_read(self):
        # One WRITE then one READ through the pad registers: commands/data reach the pads one cycle
        # after the DFI; the DRAM registers the command from the pads and returns the read data CL
        # cycles later; the PHY registers it and flags rddata_valid: read_latency = CL + 1.
        for cl in [2, 3]:
            with self.subTest(cl=cl):
                pads  = self.get_pads()
                phy   = GENSDRPHY(pads, sys_clk_freq=100e6, cl=cl)
                p0    = phy.dfi.p0
                dq_o  = [None]*self.databits
                dq_oe = [None]*self.databits
                self.assertEqual(phy.settings.read_latency, cl + 1)

                def pads_state():
                    r = {}
                    for name in ["cs_n", "ras_n", "cas_n", "we_n", "a", "ba", "cke", "dm"]:
                        r[name] = (yield getattr(pads, name))
                    r["dq_o"]  = (yield Cat(*dq_o))
                    r["dq_oe"] = (yield Cat(*dq_oe))
                    return r

                def command(cs_n=1, ras_n=1, cas_n=1, we_n=1, address=0, bank=0):
                    yield p0.cs_n.eq(cs_n)
                    yield p0.ras_n.eq(ras_n)
                    yield p0.cas_n.eq(cas_n)
                    yield p0.we_n.eq(we_n)
                    yield p0.address.eq(address)
                    yield p0.bank.eq(bank)

                idle = dict(cs_n=1, ras_n=1, cas_n=1, we_n=1, a=0, ba=0, cke=0, dm=0, dq_o=0, dq_oe=0)

                def gen():
                    yield p0.cke.eq(1)
                    yield
                    yield
                    self.assertEqual((yield from pads_state()), {**idle, "cke": 1})

                    # WRITE column 0x5A of bank 1, low byte masked.
                    yield from command(cs_n=0, ras_n=1, cas_n=0, we_n=0, address=0x5A, bank=1)
                    yield p0.wrdata.eq(0xBEEF)
                    yield p0.wrdata_mask.eq(0b01)
                    yield p0.wrdata_en.eq(1)
                    yield
                    yield from command()
                    yield p0.wrdata_en.eq(0)
                    # Not on the pads yet.
                    self.assertEqual((yield from pads_state()), {**idle, "cke": 1})
                    yield
                    self.assertEqual((yield from pads_state()), dict(cs_n=0, ras_n=1, cas_n=0, we_n=0,
                        a=0x5A, ba=1, cke=1, dm=0b01, dq_o=0xBEEF, dq_oe=0xFFFF))
                    yield
                    # DQ released, DM only with the data.
                    state = (yield from pads_state())
                    self.assertEqual((state["dq_oe"], state["dm"]), (0, 0))
                    self.assertEqual({k: v for k, v in state.items() if k not in ["dq_o", "dq_oe", "dm"]},
                        {k: v for k, v in idle.items() if k not in ["dq_o", "dq_oe", "dm"]} | {"cke": 1})

                    # READ column 0x5A of bank 1.
                    yield from command(cs_n=0, ras_n=1, cas_n=0, we_n=1, address=0x5A, bank=1)
                    yield p0.rddata_en.eq(1)
                    yield                                               # DFI cycle 0.
                    yield from command()
                    yield p0.rddata_en.eq(0)
                    # Cycle 1: command on the pads, registered by the DRAM at the end of it; the DRAM
                    # drives DQ CL cycles later (cycle CL+1), the PHY registers DQ (cycle CL+2).
                    data = 0x1234
                    for cycle in range(1, cl + 6):
                        yield pads.dq.eq(data if cycle == cl + 1 else 0)
                        yield
                        if cycle == 1:
                            state = (yield from pads_state())
                            self.assertEqual({k: state[k] for k in ["cs_n", "ras_n", "cas_n", "we_n", "a", "ba", "dq_oe"]},
                                dict(cs_n=0, ras_n=1, cas_n=0, we_n=1, a=0x5A, ba=1, dq_oe=0))
                        if cycle == cl + 2:
                            self.assertEqual((yield p0.rddata_valid), 1, cycle)
                            self.assertEqual((yield p0.rddata), data)
                        else:
                            self.assertEqual((yield p0.rddata_valid), 0, cycle)

                run_simulation(phy, gen(), special_overrides={SDRTristate: sdr_tristate_model(dq_o, dq_oe)})
                self.assertTrue(all(o is not None for o in dq_o + dq_oe))

    def test_half_rate_commands(self):
        # HalfRateGENSDRPHY: the two DFI phases of a sys cycle go out on the two sys2x halves,
        # phase 0 first.
        pads = self.get_pads()
        phy  = HalfRateGENSDRPHY(pads, sys_clk_freq=50e6)
        self.assertEqual(phy.settings.nphases, 2)
        log  = []

        def command(phase, cs_n=1, ras_n=1, cas_n=1, we_n=1, address=0, bank=0):
            yield phase.cs_n.eq(cs_n)
            yield phase.ras_n.eq(ras_n)
            yield phase.cas_n.eq(cas_n)
            yield phase.we_n.eq(we_n)
            yield phase.address.eq(address)
            yield phase.bank.eq(bank)

        def gen():
            # Let the phase detection settle.
            for _ in range(4):
                yield
            # ACTIVATE on phase 0, READ on phase 1 of the same sys cycle.
            yield from command(phy.dfi.p0, cs_n=0, ras_n=0, cas_n=1, we_n=1, address=0x1ABC, bank=2)
            yield from command(phy.dfi.p1, cs_n=0, ras_n=1, cas_n=0, we_n=1, address=0x5A,   bank=2)
            yield
            yield from command(phy.dfi.p0)
            yield from command(phy.dfi.p1)
            for _ in range(4):
                yield

        def monitor():
            # sys2x: one sample per SDRAM clock, from the first clock the pad registers have seen.
            yield
            for _ in range(2*10):
                sample = []
                for name in ["cs_n", "ras_n", "cas_n", "we_n", "a", "ba"]:
                    sample.append((yield getattr(pads, name)))
                log.append(tuple(sample))
                yield

        # The SDR IOs of the full-rate PHY are in sys2x (renamed): modelled from their ClockSignal.
        run_simulation(phy, {"sys": [gen()], "sys2x": [monitor()]}, clocks={"sys": 8, "sys2x": (4, 2)},
            special_overrides={
                SDROutput:   SDRIOModel,
                SDRInput:    SDRIOModel,
                SDRTristate: sdr_tristate_model(),
            })
        activate = (0, 0, 1, 1, 0x1ABC, 2)
        read     = (0, 1, 0, 1, 0x5A,   2)
        nop      = (1, 1, 1, 1, 0,      0)
        self.assertIn(activate, log, log)
        i = log.index(activate)
        self.assertEqual(log[i:i + 2], [activate, read], log)
        self.assertEqual(set(log[:i] + log[i + 2:]), {nop}, log)

    @unittest.expectedFailure
    def test_half_rate_verilog_pads_clock(self):
        # With the generic SDR IO lowering (no vendor override), the full-rate PHY's pad registers
        # must follow its renaming to sys2x. They do not: LiteX's SDRIO special caches clk_domain
        # ("sys") at construction, ClockDomainsRenamer only renames its ClockSignal, and
        # InferredSDRIO is built from the cached name, so the command/address/DM registers (and the
        # DQ output/input registers) end up in sys while the DQ output enable (InferredSDRIO
        # without a name, derived from the renamed ClockSignal) is in sys2x.
        pads = self.get_pads()
        phy  = HalfRateGENSDRPHY(pads, sys_clk_freq=50e6)
        v    = str(verilog.convert(phy, ios=set(pads.flatten())))
        blocks = {}
        for block in v.split("always @(")[1:]:
            clk = block.split(")")[0]
            for pad in ["a", "ba", "ras_n", "cas_n", "we_n", "cs_n", "cke", "dm"]:
                if f"\n\tpads_{pad} <= " in block or f"\n\tpads_{pad}[" in block:
                    blocks.setdefault(pad, set()).add(clk)
        self.assertEqual(blocks, {pad: {"posedge sys2x_clk"} for pad in
            ["a", "ba", "ras_n", "cas_n", "we_n", "cs_n", "cke", "dm"]})


if __name__ == "__main__":
    unittest.main()
