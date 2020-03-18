# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import unittest
import random

from migen import *

from litedram.common import *
from litedram.frontend.ecc import *

from litex.gen.sim import *

from test.common import *


class TestECC(unittest.TestCase):
    def ecc_encode_decode_test(self, from_width, to_width, n, pre=None, post=None, **kwargs):
        class DUT(Module):
            def __init__(self):
                self.port_from = LiteDRAMNativePort("both", 24, from_width)
                self.port_to = LiteDRAMNativePort("both", 24, to_width)
                self.submodules.ecc = LiteDRAMNativePortECC(self.port_from, self.port_to, **kwargs)
                self.mem = DRAMMemory(to_width, n)

                self.wdata = [seed_to_data(i, nbits=from_width) for i in range(n)]
                self.rdata = []

        def main_generator(dut):
            if pre is not None:
                yield from pre(dut)

            port = dut.port_from

            # write
            for i in range(n):
                yield port.cmd.valid.eq(1)
                yield port.cmd.we.eq(1)
                yield port.cmd.addr.eq(i)
                yield
                while (yield port.cmd.ready) == 0:
                    yield
                yield port.cmd.valid.eq(0)
                yield
                yield port.wdata.valid.eq(1)
                yield port.wdata.data.eq(dut.wdata[i])
                yield
                while (yield port.wdata.ready) == 0:
                    yield
                yield port.wdata.valid.eq(0)
                yield

            # read
            for i in range(n):
                yield port.cmd.valid.eq(1)
                yield port.cmd.we.eq(0)
                yield port.cmd.addr.eq(i)
                yield
                while (yield port.cmd.ready) == 0:
                    yield
                yield port.cmd.valid.eq(0)
                yield
                while (yield port.rdata.valid) == 0:
                    yield
                dut.rdata.append((yield port.rdata.data))
                yield port.rdata.ready.eq(1)
                yield
                yield port.rdata.ready.eq(0)
                yield

            if post is not None:
                yield from post(dut)

        dut = DUT()
        generators = [
            main_generator(dut),
            dut.mem.write_handler(dut.port_to),
            dut.mem.read_handler(dut.port_to),
        ]
        run_simulation(dut, generators)
        return dut

    def test_ecc_32_7(self):
        # 32 data bits + 6 code bits + parity bit
        dut = self.ecc_encode_decode_test(32*8, 39*8, 2)
        self.assertEqual(dut.wdata, dut.rdata)

    def test_ecc_64_8(self):
        # 64 data bits + 7 code bits + parity bit
        dut = self.ecc_encode_decode_test(64*8, 72*8, 2)
        self.assertEqual(dut.wdata, dut.rdata)

    def test_ecc_sec_errors(self):
        def pre(dut):
            yield from dut.ecc.flip.write(0b00000100)

        def post(dut):
            dut.sec_errors = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors = (yield from dut.ecc.ded_errors.read())

        dut = self.ecc_encode_decode_test(8*8, 13*8, 4, pre, post, with_error_injection=True)
        self.assertEqual(dut.wdata, dut.rdata)
        self.assertEqual(dut.sec_errors, 4)
        self.assertEqual(dut.ded_errors, 0)

    def test_ecc_ded_errors(self):
        def pre(dut):
            yield from dut.ecc.flip.write(0b00001100)

        def post(dut):
            dut.sec_errors = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors = (yield from dut.ecc.ded_errors.read())

        dut = self.ecc_encode_decode_test(8*8, 13*8, 4, pre, post, with_error_injection=True)
        self.assertNotEqual(dut.wdata, dut.rdata)
        self.assertEqual(dut.sec_errors, 0)
        self.assertEqual(dut.ded_errors, 4)

    def test_ecc_decoder_disable(self):
        def pre(dut):
            yield from dut.ecc.flip.write(0b10101100)
            yield from dut.ecc.enable.write(0)

        def post(dut):
            dut.sec_errors = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors = (yield from dut.ecc.ded_errors.read())

        dut = self.ecc_encode_decode_test(8*8, 13*8, 4, pre, post, with_error_injection=True)
        self.assertNotEqual(dut.wdata, dut.rdata)
        self.assertEqual(dut.sec_errors, 0)
        self.assertEqual(dut.ded_errors, 0)

    def test_ecc_clear_sec_errors(self):
        def pre(dut):
            yield from dut.ecc.flip.write(0b00000100)

        def post(dut):
            dut.sec_errors = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors = (yield from dut.ecc.ded_errors.read())

            yield from dut.ecc.clear.write(1)
            yield

            dut.sec_errors_c = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors_c = (yield from dut.ecc.ded_errors.read())

        dut = self.ecc_encode_decode_test(8*8, 13*8, 4, pre, post, with_error_injection=True)
        self.assertEqual(dut.wdata, dut.rdata)
        self.assertNotEqual(dut.sec_errors, 0)
        self.assertEqual(dut.ded_errors, 0)
        self.assertEqual(dut.sec_errors_c, 0)
        self.assertEqual(dut.ded_errors_c, 0)

    def test_ecc_clear_ded_errors(self):
        def pre(dut):
            yield from dut.ecc.flip.write(0b10101100)

        def post(dut):
            dut.sec_errors = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors = (yield from dut.ecc.ded_errors.read())

            yield from dut.ecc.clear.write(1)
            yield

            dut.sec_errors_c = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors_c = (yield from dut.ecc.ded_errors.read())

        dut = self.ecc_encode_decode_test(8*8, 13*8, 4, pre, post, with_error_injection=True)
        self.assertNotEqual(dut.wdata, dut.rdata)
        self.assertEqual(dut.sec_errors, 0)
        self.assertNotEqual(dut.ded_errors, 0)
        self.assertEqual(dut.sec_errors_c, 0)
        self.assertEqual(dut.ded_errors_c, 0)


if __name__ == "__main__":
    unittest.main()
