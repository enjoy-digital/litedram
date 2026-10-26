#
# This file is part of LiteDRAM.
#
# Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
import random

from migen import *

from litedram.common import *
from litedram.frontend.ecc import *

from litex.gen.sim import *
from litex.soc.cores.ecc import *

from test.common import *

# Helpers ------------------------------------------------------------------------------------------

def bits(value, width=32):
    # Convert int to a string representing binary value and reverse it so that we can index bits
    # easily with s[0] being LSB
    return f"{value:0{width}b}"[::-1]

def frombits(bits):
    # Reverse of bits()
    return int(bits[::-1], 2)

def bits_pp(value, width=32):
    # Pretty print binary value, groupped by bytes
    if isinstance(value, str):
        value = frombits(value)
    s = f"{value:0{width}b}"
    byte_chunks = [s[i:i+8] for i in range(0, len(s), 8)]
    return "0b " + " ".join(byte_chunks)

def extract_ecc_data(data_width, codeword_width, codeword_bits):
    extracted = ""
    for i in range(8):
        word = codeword_bits[codeword_width*i:codeword_width*(i+1)]
        # Remove parity bit
        word = word[1:]
        data_pos = compute_data_positions(codeword_width - 1)  # -1 for parity
        # Extract data bits
        word_ex = list(bits(0, 32))
        for j, d in enumerate(data_pos):
            word_ex[j] = word[d-1]
        word_ex = "".join(word_ex)
        extracted += word_ex
    return extracted

# TestECC ------------------------------------------------------------------------------------------

class TestECC(unittest.TestCase):
    def test_eccw_connected(self):
        # Verify LiteDRAMNativePortECCW ECC encoding.
        class DUT(Module):
            def __init__(self):
                eccw = LiteDRAMNativePortECCW(data_width_from=32*8, data_width_to=39*8)
                self.submodules.eccw = eccw

        def main_generator(dut):
            sink_data = seed_to_data(0, nbits=32*8)
            yield dut.eccw.sink.data.eq(sink_data)
            yield
            source_data = (yield dut.eccw.source.data)

            sink_data_bits   = bits(sink_data,   32*8)
            source_data_bits = bits(source_data, 39*8)
            self.assertNotEqual(sink_data_bits, source_data_bits[:len(sink_data_bits)])

            source_extracted = extract_ecc_data(32, 39, source_data_bits)
            # Assert each word separately for more readable assert messages
            for i in range(8):
                word = slice(32*i, 32*(i+1))
                self.assertEqual(bits_pp(source_extracted[word]), bits_pp(sink_data_bits[word]),
                    msg=f"Mismatch at i = {i}")

        dut = DUT()
        run_simulation(dut, main_generator(dut))

    def test_eccw_we_enabled(self):
        # Verify LiteDRAMNativePortECCW always set bytes enable.
        class DUT(Module):
            def __init__(self):
                eccw = LiteDRAMNativePortECCW(data_width_from=32*8, data_width_to=39*8)
                self.submodules.eccw = eccw
                self.comb += eccw.sink.we.eq(2**(32*8)-1)

        def main_generator(dut):
            yield
            source_we = (yield dut.eccw.source.we)

            self.assertEqual(bits_pp(source_we, 39//8), bits_pp(2**len(dut.eccw.source.we) - 1))

        dut = DUT()
        run_simulation(dut, main_generator(dut))

    def test_eccw_we_error(self):
        # Verify LiteDRAMNativePortECCW flags writes whose byte enables do not cover full ECC words.
        class DUT(Module):
            def __init__(self):
                eccw = LiteDRAMNativePortECCW(data_width_from=32*8, data_width_to=39*8)
                self.submodules.eccw = eccw

        def main_generator(dut):
            full_from = 2**(32*8//8) - 1
            full_to   = 2**39 - 1
            yield dut.eccw.sink.valid.eq(1)
            yield dut.eccw.sink.we.eq(full_from)
            yield
            self.assertEqual((yield dut.eccw.we_error), 0)
            self.assertEqual((yield dut.eccw.source.we), full_to)
            # One byte enable cleared in the 3rd word: error flagged, the word is still fully written.
            yield dut.eccw.sink.we.eq(full_from & ~(1 << (2*4 + 1)))
            yield
            self.assertEqual((yield dut.eccw.we_error), 1)
            self.assertEqual((yield dut.eccw.source.we), full_to)
            # All byte enables of the 3rd word cleared: error flagged, that ECC word is not written
            # (its byte enables are bits (2*39)//8 to (3*39)//8 of the 39-bit vector).
            lo, hi = (2*39)//8, (3*39)//8
            yield dut.eccw.sink.we.eq(full_from & ~(0b1111 << (2*4)))
            yield
            self.assertEqual((yield dut.eccw.we_error), 1)
            self.assertEqual((yield dut.eccw.source.we), full_to & ~((2**(hi-lo)-1) << lo))
            # No error without a valid beat.
            yield dut.eccw.sink.valid.eq(0)
            yield
            self.assertEqual((yield dut.eccw.we_error), 0)

        dut = DUT()
        run_simulation(dut, main_generator(dut))

    def test_eccr_connected(self):
        # Verify LiteDRAMNativePortECCR ECC decoding.
        class DUT(Module):
            def __init__(self):
                eccr = LiteDRAMNativePortECCR(data_width_from=32*8, data_width_to=39*8)
                self.submodules.eccr = eccr

        def main_generator(dut):
            sink_data = seed_to_data(0, nbits=(39*8 // 32 + 1) * 32)

            yield dut.eccr.sink.data.eq(sink_data)
            yield
            source_data = (yield dut.eccr.source.data)

            sink_data_bits   = bits(sink_data, 39*8)
            source_data_bits = bits(source_data, 32*8)
            self.assertNotEqual(sink_data_bits[:len(source_data_bits)], source_data_bits)

            sink_extracted = extract_ecc_data(32, 39, sink_data_bits)
            self.assertEqual(bits_pp(sink_extracted), bits_pp(source_data_bits))
            # Assert each word separately for more readable assert messages
            for i in range(8):
                word = slice(32*i, 32*(i+1))
                self.assertEqual(bits_pp(sink_extracted[word]), bits_pp(source_data_bits[word]),
                                 msg=f"Mismatch at i = {i}")

        dut = DUT()
        run_simulation(dut, main_generator(dut))

    def test_eccr_errors_connected_when_sink_valid(self):
        # Verify LiteDRAMNativePortECCR Error detection.
        class DUT(Module):
            def __init__(self):
                eccr = LiteDRAMNativePortECCR(data_width_from=32*8, data_width_to=39*8)
                self.submodules.eccr = eccr

        def main_generator(dut):
            yield dut.eccr.enable.eq(1)
            yield dut.eccr.sink.data.eq(0b10)  # Wrong parity bit
            yield
            # Verify no errors are detected
            self.assertEqual((yield dut.eccr.sec), 0)
            self.assertEqual((yield dut.eccr.ded), 0)
            # Set sink.valid and verify errors parity error is detected
            yield dut.eccr.sink.valid.eq(1)
            yield
            self.assertEqual((yield dut.eccr.sec), 1)
            self.assertEqual((yield dut.eccr.ded), 0)

        dut = DUT()
        run_simulation(dut, main_generator(dut))

    def ecc_encode_decode_test(self, from_width, to_width, n, pre=None, post=None, **kwargs):
        """ECC encoding/decoding generic test."""
        class DUT(Module):
            def __init__(self):
                self.port_from = LiteDRAMNativePort("both", 24, from_width)
                self.port_to   = LiteDRAMNativePort("both", 24, to_width)
                self.submodules.ecc = LiteDRAMNativePortECC(self.port_from, self.port_to, **kwargs)
                self.mem = DRAMMemory(to_width, n)

                self.wdata = [seed_to_data(i, nbits=from_width) for i in range(n)]
                self.rdata = []

        def main_generator(dut):
            if pre is not None:
                yield from pre(dut)

            port = dut.port_from

            # Write
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
                yield port.wdata.we.eq(2**from_width-1)
                yield port.wdata.data.eq(dut.wdata[i])
                yield
                while (yield port.wdata.ready) == 0:
                    yield
                yield port.wdata.valid.eq(0)
                yield

            # Read
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
        # Verify encoding/decoding on 32 data bits + 6 code bits + parity bit.
        dut = self.ecc_encode_decode_test(32*8, 39*8, 2)
        self.assertEqual(dut.wdata, dut.rdata)

    def test_ecc_64_8(self):
        # Verify encoding/decoding on 64 data bits + 7 code bits + parity bit.
        dut = self.ecc_encode_decode_test(64*8, 72*8, 2)
        self.assertEqual(dut.wdata, dut.rdata)

    def test_ecc_sec_errors(self):
        # Verify SEC errors detection/correction with 1-bit flip.
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
        # Verify DED errors detection with 2-bit flip.
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
        # Verify enable control.
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
        # Verify SEC errors clear.
        def pre(dut):
            yield from dut.ecc.flip.write(0b00000100)

        def post(dut):
            # Read errors after test (SEC errors expected)
            dut.sec_errors = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors = (yield from dut.ecc.ded_errors.read())

            # Clear errors counters
            yield from dut.ecc.clear.write(1)
            yield

            # Re-Read errors to verify clear
            dut.sec_errors_c = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors_c = (yield from dut.ecc.ded_errors.read())

        dut = self.ecc_encode_decode_test(8*8, 13*8, 4, pre, post, with_error_injection=True)
        self.assertEqual(dut.wdata, dut.rdata)
        self.assertNotEqual(dut.sec_errors, 0)
        self.assertEqual(dut.ded_errors, 0)
        self.assertEqual(dut.sec_errors_c, 0)
        self.assertEqual(dut.ded_errors_c, 0)

    def test_ecc_clear_ded_errors(self):
        # Verify DED errors clear.
        def pre(dut):
            yield from dut.ecc.flip.write(0b10101100)

        def post(dut):
            # Read errors after test (DED errors expected)
            dut.sec_errors = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors = (yield from dut.ecc.ded_errors.read())

            # Clear errors counters
            yield from dut.ecc.clear.write(1)
            yield

            # Re-Read errors to verify clear
            dut.sec_errors_c = (yield from dut.ecc.sec_errors.read())
            dut.ded_errors_c = (yield from dut.ecc.ded_errors.read())

        dut = self.ecc_encode_decode_test(8*8, 13*8, 4, pre, post, with_error_injection=True)
        self.assertNotEqual(dut.wdata, dut.rdata)
        self.assertEqual(dut.sec_errors, 0)
        self.assertNotEqual(dut.ded_errors, 0)
        self.assertEqual(dut.sec_errors_c, 0)
        self.assertEqual(dut.ded_errors_c, 0)

    # Write byte enables ---------------------------------------------------------------------------

    def ecc_we_dut(self, from_width, to_width, **kwargs):
        """LiteDRAMNativePortECC between two native ports with a DRAMMemory behind port_to and
        a monitor of the byte enables written to it."""
        class DUT(Module):
            def __init__(self):
                self.port_from = LiteDRAMNativePort("both", 24, from_width)
                self.port_to   = LiteDRAMNativePort("both", 24, to_width)
                self.submodules.ecc = LiteDRAMNativePortECC(self.port_from, self.port_to, **kwargs)
                self.mem   = DRAMMemory(to_width, 4)
                self.we_to = [] # port_to byte enables, one entry per write data handshake.

        @passive
        def we_monitor(dut):
            while True:
                if (yield dut.port_to.wdata.valid) and (yield dut.port_to.wdata.ready):
                    dut.we_to.append((yield dut.port_to.wdata.we))
                yield

        dut = DUT()
        dut.generators = [
            we_monitor(dut),
            dut.mem.write_handler(dut.port_to),
            dut.mem.read_handler(dut.port_to),
            timeout_generator(2000),
        ]
        return dut

    @staticmethod
    def ecc_write(port, addr, data, we):
        yield port.cmd.valid.eq(1)
        yield port.cmd.we.eq(1)
        yield port.cmd.addr.eq(addr)
        yield
        while (yield port.cmd.ready) == 0:
            yield
        yield port.cmd.valid.eq(0)
        yield
        yield port.wdata.valid.eq(1)
        yield port.wdata.we.eq(we)
        yield port.wdata.data.eq(data)
        yield
        while (yield port.wdata.ready) == 0:
            yield
        yield port.wdata.valid.eq(0)
        yield port.wdata.we.eq(0)
        # Let the write reach the memory before the next access.
        for _ in range(8):
            yield

    @staticmethod
    def ecc_read(port, addr):
        yield port.cmd.valid.eq(1)
        yield port.cmd.we.eq(0)
        yield port.cmd.addr.eq(addr)
        yield
        while (yield port.cmd.ready) == 0:
            yield
        yield port.cmd.valid.eq(0)
        yield
        while (yield port.rdata.valid) == 0:
            yield
        data = (yield port.rdata.data)
        yield port.rdata.ready.eq(1)
        yield
        yield port.rdata.ready.eq(0)
        yield
        return data

    def test_ecc_we_errors(self):
        # Verify the write byte enable error counter (with_we_error_detection): a write with all
        # byte enables set is not an error, a write with partial byte enables (one byte of an
        # ECC word cleared, or a whole ECC word disabled) is counted once, clear resets it.
        from_width, to_width = 64*8, 72*8
        full = 2**(from_width//8) - 1
        dut  = self.ecc_we_dut(from_width, to_width, with_we_error_detection=True)

        def main_generator(dut):
            port = dut.port_from
            # Full write: no error.
            yield from self.ecc_write(port, 0, seed_to_data(0, nbits=from_width), full)
            self.assertEqual((yield from dut.ecc.we_errors.read()), 0)
            # One byte of ECC word 0 cleared: one error.
            yield from self.ecc_write(port, 1, seed_to_data(1, nbits=from_width), full & ~(1 << 5))
            self.assertEqual((yield from dut.ecc.we_errors.read()), 1)
            # A whole ECC word (word 1) disabled: one more error.
            yield from self.ecc_write(port, 2, seed_to_data(2, nbits=from_width), full & ~(0xff << 8))
            self.assertEqual((yield from dut.ecc.we_errors.read()), 2)
            # Full write: no new error.
            yield from self.ecc_write(port, 3, seed_to_data(3, nbits=from_width), full)
            self.assertEqual((yield from dut.ecc.we_errors.read()), 2)
            # Clear.
            yield from dut.ecc.clear.write(1)
            yield
            self.assertEqual((yield from dut.ecc.we_errors.read()), 0)

        run_simulation(dut, [main_generator(dut)] + dut.generators)
        # All 4 writes (flagged or not) reached the memory.
        self.assertEqual(len(dut.we_to), 4)

    def test_ecc_we_partial_write(self):
        # Verify partial writes through LiteDRAMNativePortECC: any byte enable set within an ECC
        # word writes the full (re-encoded) ECC word, an ECC word with no byte enable set is left
        # untouched (ECC words of 72 bits are 9 bytes of port_to byte enables).
        from_width, to_width = 64*8, 72*8
        words = 8
        full  = 2**(from_width//8) - 1
        dut   = self.ecc_we_dut(from_width, to_width)
        d0, d1, d2 = [seed_to_data(i, nbits=from_width) for i in range(3)]

        def word(data, i):
            return (data >> (64*i)) & (2**64 - 1)

        def main_generator(dut):
            port = dut.port_from
            yield from self.ecc_write(port, 0, d0, full)
            self.assertEqual((yield from self.ecc_read(port, 0)), d0)
            # One byte of ECC word 2: the full ECC word 2 is written.
            yield from self.ecc_write(port, 0, d1, 1 << (2*8 + 3))
            expected = [word(d1, i) if i == 2 else word(d0, i) for i in range(words)]
            self.assertEqual((yield from self.ecc_read(port, 0)), sum(w << (64*i) for i, w in enumerate(expected)))
            # ECC words 0 and 7 fully enabled.
            yield from self.ecc_write(port, 0, d2, 0xff | (0xff << 56))
            expected = [word(d2, i) if i in [0, 7] else w for i, w in enumerate(expected)]
            self.assertEqual((yield from self.ecc_read(port, 0)), sum(w << (64*i) for i, w in enumerate(expected)))

        run_simulation(dut, [main_generator(dut)] + dut.generators)
        self.assertEqual(dut.we_to, [
            2**72 - 1,
            0x1ff << (2*9),
            0x1ff | (0x1ff << (7*9)),
        ])


if __name__ == "__main__":
    unittest.main()
