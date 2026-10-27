#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from migen import *

from litedram.dfii import DFIInjector


def csr_value(csr, **fields):
    """The value the CPU writes to a CSRStorage to set the given fields (others 0)."""
    value = 0
    for field in csr.fields.fields:
        value |= (fields.pop(field.name, 0) & (2**field.size - 1)) << field.offset
    assert not fields, f"unknown fields {fields}"
    return value


def read(phase, names):
    r = {}
    for name in names:
        r[name] = (yield getattr(phase, name))
    return r


def nop(nranks=1):
    return dict(cs_n=2**nranks - 1, ras_n=1, cas_n=1, we_n=1)


class TestDFIInjector(unittest.TestCase):
    """DFIInjector: the DFI master is driven either by the CSRs (software mode, sel=0) or by the
    slave DFI (hardware mode, sel=1, the reset value) or by ext_dfi (ext_dfi_sel)."""
    addressbits = 13
    bankbits    = 3
    databits    = 32

    cmd_names = ("cs_n", "ras_n", "cas_n", "we_n", "address", "bank", "wrdata_en", "rddata_en")

    def get_dut(self, nranks=1, nphases=2, is_clam_shell=False):
        return DFIInjector(self.addressbits, self.bankbits, nranks, self.databits, nphases,
            is_clam_shell=is_clam_shell)

    def test_csrs(self):
        dut = self.get_dut(nphases=2)
        self.assertEqual([csr.name for csr in dut.get_csrs()], ["control"] + [
            f"pi{n}_{name}" for n in range(2)
            for name in ["command", "command_issue", "address", "baddress", "wrdata", "rddata"]])
        self.assertEqual(len(dut.pi0._address.storage),  self.addressbits)
        self.assertEqual(len(dut.pi0._baddress.storage), self.bankbits)
        self.assertEqual(len(dut.pi0._wrdata.storage),   self.databits)
        self.assertEqual(len(dut.pi0._rddata.status),    self.databits)
        # Hardware control by default.
        self.assertEqual(dut._control.fields.sel.reset.value, 1)

    def test_software_mode_command_issue(self):
        # Each command is driven on the selected phase for the single cycle of command_issue, the
        # other phase and the surrounding cycles are NOPs; address/bank/wrdata are driven as soon
        # as they are written.
        commands = {
            # name     : (command fields,                        expected on the DFI phase)
            "NOP"      : (dict(cs=1),                             dict(cs_n=0, ras_n=1, cas_n=1, we_n=1)),
            "ACTIVATE" : (dict(cs=1, ras=1),                      dict(cs_n=0, ras_n=0, cas_n=1, we_n=1)),
            "PRECHARGE": (dict(cs=1, ras=1, we=1),                dict(cs_n=0, ras_n=0, cas_n=1, we_n=0)),
            "WRITE"    : (dict(cs=1, cas=1, we=1, wren=1),        dict(cs_n=0, ras_n=1, cas_n=0, we_n=0, wrdata_en=1)),
            "READ"     : (dict(cs=1, cas=1, rden=1),              dict(cs_n=0, ras_n=1, cas_n=0, we_n=1, rddata_en=1)),
            "MRS"      : (dict(cs=1, ras=1, cas=1, we=1),         dict(cs_n=0, ras_n=0, cas_n=0, we_n=0)),
        }
        for issue_phase in range(2):
            for name, (fields, expected) in commands.items():
                with self.subTest(phase=issue_phase, command=name):
                    dut = self.get_dut(nphases=2)
                    pi  = getattr(dut, f"pi{issue_phase}")
                    master = dut.master.phases[issue_phase]
                    other  = dut.master.phases[1 - issue_phase]
                    idle   = {**nop(), "address": 0, "bank": 0, "wrdata_en": 0, "rddata_en": 0}

                    def gen():
                        yield from dut._control.write(csr_value(dut._control, sel=0))
                        for phase in dut.master.phases:
                            self.assertEqual((yield from read(phase, self.cmd_names)), idle)
                        yield from pi._address.write(0x1ABC)
                        yield from pi._baddress.write(0b101)
                        yield from pi._wrdata.write(0xDEADBEEF)
                        yield from pi._command.write(csr_value(pi._command, **fields))
                        # Nothing issued yet.
                        programmed = {**idle, "address": 0x1ABC, "bank": 0b101}
                        self.assertEqual((yield from read(master, self.cmd_names)), programmed)
                        self.assertEqual((yield master.wrdata), 0xDEADBEEF)
                        self.assertEqual((yield master.wrdata_mask), 0)
                        self.assertEqual((yield from read(other, self.cmd_names)), idle)
                        # The command is on the DFI during the cycle of the command_issue write.
                        yield from pi._command_issue.write(1)
                        self.assertEqual((yield from read(master, self.cmd_names)), {**programmed, **expected})
                        self.assertEqual((yield from read(other, self.cmd_names)), idle)
                        # And gone the cycle after, address/bank/wrdata are kept.
                        yield
                        self.assertEqual((yield from read(master, self.cmd_names)), programmed)
                        self.assertEqual((yield master.wrdata), 0xDEADBEEF)
                        self.assertEqual((yield from read(other, self.cmd_names)), idle)
                        yield
                        self.assertEqual((yield from read(master, self.cmd_names)), programmed)

                    run_simulation(dut, gen())

    def test_control_fields(self):
        # cke/odt/reset_n drive every rank of every phase in software mode; in hardware mode the
        # slave DFI drives them.
        nranks = 2
        dut    = self.get_dut(nranks=nranks, nphases=4)
        names  = ("cke", "odt", "reset_n")

        def gen():
            for cke, odt, reset_n in [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 1), (0, 1, 1)]:
                yield from dut._control.write(csr_value(dut._control, sel=0, cke=cke, odt=odt, reset_n=reset_n))
                for phase in dut.master.phases:
                    self.assertEqual((yield from read(phase, names)), dict(
                        cke     = cke*(2**nranks - 1),
                        odt     = odt*(2**nranks - 1),
                        reset_n = reset_n))
                    self.assertEqual((yield from read(phase, ("cs_n", "ras_n", "cas_n", "we_n"))), nop(nranks))
            # Hardware mode: control fields are ignored, the slave's values go through.
            yield from dut._control.write(csr_value(dut._control, sel=1, cke=1, odt=1, reset_n=1))
            for phase in dut.master.phases:
                self.assertEqual((yield from read(phase, names)), dict(cke=0, odt=0, reset_n=0))
            for phase in dut.slave.phases:
                yield phase.cke.eq(0b01)
                yield phase.odt.eq(0b10)
                yield phase.reset_n.eq(1)
            yield
            for phase in dut.master.phases:
                self.assertEqual((yield from read(phase, names)), dict(cke=0b01, odt=0b10, reset_n=1))

        run_simulation(dut, gen())

    def test_hardware_mode(self):
        # Slave -> master for the commands and write data, master -> slave for the read data; the
        # CSRs have no effect; ext_dfi takes over with ext_dfi_sel.
        nranks  = 2
        nphases = 2
        dut     = self.get_dut(nranks=nranks, nphases=nphases)
        m2s     = ("address", "bank", "cas_n", "cs_n", "ras_n", "we_n", "cke", "odt", "reset_n", "act_n",
                   "wrdata", "wrdata_en", "wrdata_mask", "rddata_en")
        values  = {p: dict(
            address     = 0x1234 + p,
            bank        = p + 1,
            cas_n       = p,
            cs_n        = 0b10,
            ras_n       = 1 - p,
            we_n        = 0,
            cke         = 0b11,
            odt         = 0b01,
            reset_n     = 1,
            act_n       = 0,
            wrdata      = 0x11223344*(p + 1),
            wrdata_en   = 1,
            wrdata_mask = 0b1010 >> p,
            rddata_en   = 1,
        ) for p in range(nphases)}
        reset_values = dict(address=0, bank=0, cas_n=1, cs_n=0b11, ras_n=1, we_n=1, cke=0, odt=0,
            reset_n=0, act_n=1, wrdata=0, wrdata_en=0, wrdata_mask=0, rddata_en=0)

        def gen():
            self.assertEqual((yield dut._control.fields.sel), 1)
            for p, phase in enumerate(dut.slave.phases):
                for name, value in values[p].items():
                    yield getattr(phase, name).eq(value)
            for p, phase in enumerate(dut.master.phases):
                yield phase.rddata.eq(0xA5A5A5A0 + p)
                yield phase.rddata_valid.eq(1)
            yield
            for p, phase in enumerate(dut.master.phases):
                self.assertEqual((yield from read(phase, m2s)), values[p])
            for p, phase in enumerate(dut.slave.phases):
                self.assertEqual((yield phase.rddata), 0xA5A5A5A0 + p)
                self.assertEqual((yield phase.rddata_valid), 1)
            # CSR writes are ignored.
            yield from dut.pi0._address.write(0x7FF)
            yield from dut.pi0._command.write(csr_value(dut.pi0._command, cs=1, ras=1, cas=1, we=1))
            yield from dut.pi0._command_issue.write(1)
            self.assertEqual((yield from read(dut.master.p0, m2s)), values[0])
            # External DFI.
            yield dut.ext_dfi_sel.eq(1)
            yield dut.ext_dfi.p1.address.eq(0x555)
            yield dut.ext_dfi.p1.cs_n.eq(0b01)
            yield dut.ext_dfi.p1.ras_n.eq(0)
            yield
            self.assertEqual((yield from read(dut.master.p0, m2s)), reset_values)
            self.assertEqual((yield from read(dut.master.p1, m2s)),
                {**reset_values, "address": 0x555, "cs_n": 0b01, "ras_n": 0})
            for p, phase in enumerate(dut.ext_dfi.phases):
                self.assertEqual((yield phase.rddata), 0xA5A5A5A0 + p)
                self.assertEqual((yield phase.rddata_valid), 1)
            yield dut.ext_dfi_sel.eq(0)
            yield
            for p, phase in enumerate(dut.master.phases):
                self.assertEqual((yield from read(phase, m2s)), values[p])

        run_simulation(dut, gen())

    def test_software_mode_read_data_capture(self):
        # rddata is captured on rddata_valid and held for the CPU.
        nphases = 2
        dut     = self.get_dut(nphases=nphases)

        def gen():
            yield from dut._control.write(csr_value(dut._control, sel=0))
            for p, phase in enumerate(dut.master.phases):
                yield phase.rddata.eq(0xCAFE0000 + p)
            yield
            for p in range(nphases):
                self.assertEqual((yield getattr(dut, f"pi{p}")._rddata.status), 0)
            for phase in dut.master.phases:
                yield phase.rddata_valid.eq(1)
            yield
            for phase in dut.master.phases:
                yield phase.rddata_valid.eq(0)
                yield phase.rddata.eq(0)
            yield
            for p in range(nphases):
                self.assertEqual((yield getattr(dut, f"pi{p}")._rddata.status), 0xCAFE0000 + p)
            # Held while rddata changes without rddata_valid.
            for phase in dut.master.phases:
                yield phase.rddata.eq(0xFFFFFFFF)
            yield
            yield
            for p in range(nphases):
                self.assertEqual((yield getattr(dut, f"pi{p}")._rddata.status), 0xCAFE0000 + p)
            # Not captured in hardware mode: the CSR DFI is disconnected from the master.
            yield from dut._control.write(csr_value(dut._control, sel=1))
            for phase in dut.master.phases:
                yield phase.rddata_valid.eq(1)
            yield
            yield
            for p in range(nphases):
                self.assertEqual((yield getattr(dut, f"pi{p}")._rddata.status), 0xCAFE0000 + p)

        run_simulation(dut, gen())

    def test_clam_shell(self):
        # is_clam_shell doubles the master's cs_n: both halves in hardware mode, cs/cs_top/cs_bottom
        # in software mode. Address/bank go through unchanged (the clam-shell address mirroring is
        # done by the BIOS, see litedram.init).
        nranks = 1
        dut    = self.get_dut(nranks=nranks, nphases=2, is_clam_shell=True)
        self.assertEqual(len(dut.slave.p0.cs_n),   nranks)
        self.assertEqual(len(dut.ext_dfi.p0.cs_n), nranks)
        self.assertEqual(len(dut.master.p0.cs_n),  2*nranks)
        self.assertEqual(len(dut.master.p0.cke),   2*nranks)

        def gen():
            # Hardware mode: the controller's cs_n is broadcast to both halves.
            for cs_n in (0, 1):
                for phase in dut.slave.phases:
                    yield phase.cs_n.eq(cs_n)
                yield
                for phase in dut.master.phases:
                    self.assertEqual((yield phase.cs_n), 0b11 if cs_n else 0b00)
            # Software mode.
            yield from dut._control.write(csr_value(dut._control, sel=0))
            yield from dut.pi0._address.write(0x1555)
            yield from dut.pi0._baddress.write(0b010)
            for fields, cs_n in [
                (dict(),                     0b11),
                (dict(cs=1),                 0b00),
                (dict(cs_top=1),             0b10),
                (dict(cs_bottom=1),          0b01),
                (dict(cs=1, cs_top=1),       0b10),
                (dict(cs=1, cs_bottom=1),    0b01),
                (dict(cs_top=1, cs_bottom=1), 0b10),
            ]:
                yield from dut.pi0._command.write(csr_value(dut.pi0._command, ras=1, **fields))
                yield from dut.pi0._command_issue.write(1)
                self.assertEqual((yield dut.master.p0.cs_n), cs_n, fields)
                self.assertEqual((yield dut.master.p0.ras_n), 0)
                self.assertEqual((yield dut.master.p0.address), 0x1555)
                self.assertEqual((yield dut.master.p0.bank), 0b010)
                self.assertEqual((yield dut.master.p1.cs_n), 0b11)
                yield
                self.assertEqual((yield dut.master.p0.cs_n), 0b11)

        run_simulation(dut, gen())


if __name__ == "__main__":
    unittest.main()
