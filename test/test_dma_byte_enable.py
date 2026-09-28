#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

import random
import unittest

from migen import *

from litedram.common import LiteDRAMNativeWritePort
from litedram.frontend.axi import LiteDRAMAXIPort
from litedram.frontend.dma import LiteDRAMDMAWriter


class TestDMAByteEnable(unittest.TestCase):
    def test_masks_follow_buffered_data(self):
        for kind in ["native", "axi"]:
            for width in [32, 64, 128]:
                for buffered in [False, True]:
                    for with_csr in [False, True]:
                        with self.subTest(kind=kind, width=width, buffered=buffered, with_csr=with_csr):
                            lanes = width//8
                            if kind == "native":
                                port = LiteDRAMNativeWritePort(address_width=32, data_width=width)
                                cmd, wdata, strobe = port.cmd, port.wdata, port.wdata.we
                            else:
                                port = LiteDRAMAXIPort(address_width=32, data_width=width)
                                cmd, wdata, strobe = port.aw, port.w, port.w.strb
                            dut = LiteDRAMDMAWriter(port, fifo_depth=4, fifo_buffered=buffered,
                                with_csr=with_csr, with_be=True)
                            full = (1 << lanes) - 1
                            masks = [0, full, 1, 1 << (lanes - 1), 0x55 & full, full >> 1]*3
                            words = [int.from_bytes(bytes((n + i) % 256 for i in range(lanes)), "little")
                                for n in range(len(masks))]
                            commands, writes = [], []
                            complete = [False]

                            @passive
                            def command_consumer():
                                prng = random.Random(7)
                                while True:
                                    yield cmd.ready.eq(prng.randrange(3) == 0)
                                    yield
                                    if (yield cmd.valid) and (yield cmd.ready):
                                        commands.append((yield cmd.addr))

                            @passive
                            def data_consumer():
                                prng = random.Random(11)
                                stalled = None
                                while True:
                                    yield wdata.ready.eq(prng.randrange(4) == 0)
                                    yield
                                    valid, ready = (yield wdata.valid), (yield wdata.ready)
                                    item = ((yield wdata.data), (yield strobe))
                                    if stalled is not None:
                                        self.assertTrue(valid)
                                        self.assertEqual(item, stalled)
                                    stalled = item if valid and not ready else None
                                    if valid and ready:
                                        writes.append(item)

                            def producer():
                                if with_csr:
                                    yield dut._base.storage.eq(0)
                                    yield dut._length.storage.eq(len(masks)*lanes)
                                    yield dut._enable.storage.eq(1)
                                for n, (value, mask) in enumerate(zip(words, masks)):
                                    if not with_csr:
                                        yield dut.sink.address.eq(n)
                                    yield dut.sink.data.eq(value)
                                    yield dut.sink.be.eq(mask)
                                    yield dut.sink.valid.eq(1)
                                    yield dut.sink.last.eq(n == len(masks) - 1)
                                    yield
                                    while not (yield dut.sink.ready):
                                        yield
                                    yield dut.sink.valid.eq(0)
                                    yield
                                complete[0] = True

                            def timeout():
                                for _ in range(3000):
                                    if complete[0] and len(writes) == len(words):
                                        return
                                    yield
                                self.fail("Buffered writes did not drain")

                            run_simulation(dut, [passive(producer)(), command_consumer(), data_consumer(), timeout()])
                            self.assertEqual(commands, list(range(len(words))))
                            self.assertEqual(writes, list(zip(words, masks)))
