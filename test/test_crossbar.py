#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import random
import unittest
import functools
import itertools
from collections import namedtuple, defaultdict

from migen import *

from litedram.common import *
from litedram.core.crossbar import LiteDRAMCrossbar

from test.common import timeout_generator, NativePortDriver


class ControllerStub:
    """Simplified simulation of LiteDRAMController as seen by LiteDRAMCrossbar

    This is a simplified implementation of LiteDRAMController suitable for
    testing the crossbar. It consisits of bankmachine handlers that try to mimic
    behaviour of real BankMachines. They also simulate data transmission by
    scheduling it to appear on data interface (data_handler sets it).
    """
    W = namedtuple("WriteData", ["bank", "addr", "data", "we"])
    R = namedtuple("ReadData",  ["bank", "addr", "data"])
    WaitingData = namedtuple("WaitingData", ["delay", "data"])

    def __init__(self, controller_interface, write_latency, read_latency, cmd_delay=None):
        self.interface = controller_interface
        self.write_latency = write_latency
        self.read_latency = read_latency
        self.data = []  # data registered on datapath (W/R)
        self._waiting = []  # data waiting to be set on datapath
        # Incremental generator of artificial read data
        self._read_data = self.read_data_counter()
        # Simulated dealy of command processing, by default just constant
        self._cmd_delay = cmd_delay or (lambda: 6)
        # Minimal logic required so that no two banks will become ready at the same moment
        self._multiplexer_lock = None

    @staticmethod
    def read_data_counter():
        return itertools.count(0x10)

    def generators(self):
        bank_handlers = [self.bankmachine_handler(bn) for bn in range(self.interface.nbanks)]
        return [self.data_handler(), *bank_handlers]

    @passive
    def data_handler(self):
        # Responsible for passing data over datapath with requested latency
        while True:
            # Examine requests to find if there is any for that cycle
            available = [w for w in self._waiting if w.delay == 0]
            # Make sure that it is never the case that we have more then 1
            # operation of the same type
            type_counts = defaultdict(int)
            for a in available:
                type_counts[type(a.data)] += 1
            for t, count in type_counts.items():
                assert count == 1, \
                    "%d data operations of type %s at the same time!" % (count, t.__name__)
            for a in available:
                # Remove it from the list and get the data
                current = self._waiting.pop(self._waiting.index(a)).data
                # If this was a write, then fill it with data from this cycle
                if isinstance(current, self.W):
                    current = current._replace(
                        data=(yield self.interface.wdata),
                        we=(yield self.interface.wdata_we),
                    )
                # If this was a read, then assert the data now
                elif isinstance(current, self.R):
                    yield self.interface.rdata.eq(current.data)
                else:
                    raise TypeError(current)
                # Add it to the data that appeared on the datapath
                self.data.append(current)
            # Advance simulation time by 1 cycle
            for i, w in enumerate(self._waiting):
                self._waiting[i] = w._replace(delay=w.delay - 1)
            yield

    @passive
    def bankmachine_handler(self, n):
        # Simplified simulation of a bank machine.
        # Uses a single buffer (no input fifo). Generates random read data.
        bank = getattr(self.interface, "bank%d" % n)
        while True:
            # Wait for a valid bank command
            while not (yield bank.valid):
                # The lock is being held as long as there is a valid command
                # in the buffer or there is a valid command on the interface.
                # As at this point we have nothing in the buffer, we unlock
                # the lock only if the command on the interface is not valid.
                yield bank.lock.eq(0)
                yield
            # Latch the command to the internal buffer
            cmd_addr = (yield bank.addr)
            cmd_we = (yield bank.we)
            # Lock the buffer as soon as command is valid on the interface.
            # We do this 1 cycle after we see the command, but BankMachine
            # also has latency, because cmd_buffer_lookahead.source must
            # become valid.
            yield bank.lock.eq(1)
            yield bank.ready.eq(1)
            yield
            yield bank.ready.eq(0)
            # Simulate that we are processing the command
            for _ in range(self._cmd_delay()):
                yield
            # Avoid situation that can happen due to the lack of multiplexer,
            # where more than one bank would send data at the same moment
            while self._multiplexer_lock is not None:
                yield
            self._multiplexer_lock = n
            yield
            # After READ/WRITE has been issued, this is signalized by using
            # rdata_valid/wdata_ready. The actual data will appear with latency.
            if cmd_we:  # WRITE
                yield bank.wdata_ready.eq(1)
                yield
                yield bank.wdata_ready.eq(0)
                # Send a request to the data_handler, it will check what
                # has been sent from the crossbar port.
                wdata = self.W(bank=n, addr=cmd_addr,
                               data=None, we=None)  # to be filled in callback
                self._waiting.append(self.WaitingData(data=wdata, delay=self.write_latency))
            else:  # READ
                yield bank.rdata_valid.eq(1)
                yield
                yield bank.rdata_valid.eq(0)
                # Send a request with "data from memory" to the data_handler
                rdata = self.R(bank=n, addr=cmd_addr, data=next(self._read_data))
                # Decrease latecy, as data_handler sets data with 1 cycle delay
                self._waiting.append(self.WaitingData(data=rdata, delay=self.read_latency - 1))
            # At this point cmd_buffer.source.ready has been activated and the
            # command in internal buffer has been discarded. The lock will be
            self._multiplexer_lock = None
            # removed in next loop if there is no other command pending.
            yield


class CrossbarDUT(Module):
    default_controller_settings = dict(
        cmd_buffer_depth = 8,
        address_mapping  = "ROW_BANK_COL",
    )
    default_phy_settings = dict(
        cwl           = 2,
        nphases       = 2,
        nranks        = 1,
        memtype       = "DDR2",
        dfi_databits  = 2*16,
        read_latency  = 5,
        write_latency = 1,
    )
    default_geom_settings = dict(
        bankbits = 3,
        rowbits  = 13,
        colbits  = 10,
    )

    def __init__(self, controller_settings=None, phy_settings=None, geom_settings=None):
        # update settings if provided
        def updated(settings, update):
            copy = settings.copy()
            copy.update(update or {})
            return copy

        controller_settings = updated(self.default_controller_settings, controller_settings)
        phy_settings        = updated(self.default_phy_settings, phy_settings)
        geom_settings       = updated(self.default_geom_settings, geom_settings)

        class SimpleSettings(Settings):
            def __init__(self, **kwargs):
                self.set_attributes(kwargs)

        settings        = SimpleSettings(**controller_settings)
        settings.phy    = SimpleSettings(**phy_settings)
        settings.geom   = SimpleSettings(**geom_settings)
        self.settings = settings

        self.address_align = log2_int(burst_lengths[settings.phy.memtype])
        self.interface = LiteDRAMInterface(self.address_align, settings)
        self.submodules.crossbar = LiteDRAMCrossbar(self.interface)

    def addr_port(self, bank, row, col):
        # construct an address the way port master would do it
        assert self.settings.address_mapping == "ROW_BANK_COL"
        aa = self.address_align
        cb = self.settings.geom.colbits
        rb = self.settings.geom.rowbits
        bb = self.settings.geom.bankbits
        col  = (col  & (2**cb - 1)) >> aa
        bank = (bank & (2**bb - 1)) << (cb - aa)
        row  = (row  & (2**rb - 1)) << (cb + bb - aa)
        return row | bank | col

    def addr_iface(self, row, col):
        # construct address the way bankmachine should receive it
        aa = self.address_align
        cb = self.settings.geom.colbits
        rb = self.settings.geom.rowbits
        col = (col & (2**cb - 1)) >> aa
        row = (row & (2**rb - 1)) << (cb - aa)
        return row | col


class TestCrossbar(unittest.TestCase):
    W = ControllerStub.W
    R = ControllerStub.R

    def test_init(self):
        dut = CrossbarDUT()
        dut.crossbar.get_port()
        dut.finalize()

    def crossbar_test(self, dut, generators, timeout=200, **kwargs):
        # Runs simulation with a controller stub (passive generators) and user generators
        if not isinstance(generators, list):
            generators = [generators]
        controller = ControllerStub(dut.interface,
                                    write_latency=dut.settings.phy.write_latency,
                                    read_latency=dut.settings.phy.read_latency,
                                    **kwargs)
        generators += [*controller.generators(), timeout_generator(timeout)]
        run_simulation(dut, generators)
        return controller.data

    def test_available_address_mappings(self):
        # Check that the only supported address mapping is ROW_BANK_COL (if we start supporting new
        # mappings, then update these tests to also test these other mappings).
        def finalize_crossbar(mapping):
            dut = CrossbarDUT(controller_settings=dict(address_mapping=mapping))
            dut.crossbar.get_port()
            dut.crossbar.finalize()

        for mapping in ["ROW_BANK_COL", "BANK_ROW_COL"]:
            if mapping in ["ROW_BANK_COL"]:
                finalize_crossbar(mapping)
            else:
                with self.assertRaises(KeyError):
                    finalize_crossbar(mapping)

    def test_address_mappings(self):
        # Verify that address is translated correctly.
        reads = []

        def producer(dut, driver):
            for t in transfers:
                addr = dut.addr_port(bank=t["bank"], row=t["row"], col=t["col"])
                if t["rw"] == self.W:
                    yield from driver.write(addr, data=t["data"], we=t.get("we", None))
                elif t["rw"] == self.R:
                    data = (yield from driver.read(addr))
                    reads.append(data)
                else:
                    raise TypeError(t["rw"])

        geom_settings = dict(colbits=10, rowbits=13, bankbits=2)
        dut  = CrossbarDUT(geom_settings=geom_settings)
        port = dut.crossbar.get_port()
        driver = NativePortDriver(port)
        transfers = [
            dict(rw=self.W, bank=2, row=0x30, col=0x03, data=0x20),
            dict(rw=self.W, bank=3, row=0x30, col=0x03, data=0x21),
            dict(rw=self.W, bank=2, row=0xab, col=0x03, data=0x22),
            dict(rw=self.W, bank=2, row=0x30, col=0x13, data=0x23),
            dict(rw=self.R, bank=1, row=0x10, col=0x99),
            dict(rw=self.R, bank=0, row=0x10, col=0x99),
            dict(rw=self.R, bank=1, row=0xcd, col=0x99),
            dict(rw=self.R, bank=1, row=0x10, col=0x77),
        ]
        expected = []
        read_data = ControllerStub.read_data_counter()
        for i, t in enumerate(transfers):
            cls = t["rw"]
            addr = dut.addr_iface(row=t["row"], col=t["col"])
            if cls == self.W:
                kwargs = dict(data=t["data"], we=0xff)
            elif cls == self.R:
                kwargs = dict(data=next(read_data))
            expected.append(cls(bank=t["bank"], addr=addr, **kwargs))

        data = self.crossbar_test(dut, [producer(dut, driver)] + driver.generators())
        self.assertEqual(data, expected)

    def test_arbitration(self):
        # Create multiple masters that write to the same bank at the same time and verify that all
        # the requests have been sent correctly.
        def producer(dut, driver, num):
            addr = dut.addr_port(bank=3, row=0x10 + num, col=0x20 + num)
            yield from driver.write(addr, data=0x30 + num)

        dut      = CrossbarDUT()
        ports    = [dut.crossbar.get_port() for _ in range(4)]
        drivers  = [NativePortDriver(port) for port in ports]
        masters  = [producer(dut, driver, i) for i, driver in enumerate(drivers)]
        generators = masters
        for driver in drivers:
            generators.extend(driver.generators())
        data     = self.crossbar_test(dut, generators)
        expected = {
            self.W(bank=3, addr=dut.addr_iface(row=0x10, col=0x20), data=0x30, we=0xff),
            self.W(bank=3, addr=dut.addr_iface(row=0x11, col=0x21), data=0x31, we=0xff),
            self.W(bank=3, addr=dut.addr_iface(row=0x12, col=0x22), data=0x32, we=0xff),
            self.W(bank=3, addr=dut.addr_iface(row=0x13, col=0x23), data=0x33, we=0xff),
        }
        self.assertEqual(set(data), expected)

    def test_lock_write(self):
        # Verify that the locking mechanism works
        # Create a situation when one master A wants to write to banks 0 then 1, but master B is
        # continuously writing to bank 1 (bank is locked) so that master A is blocked. We use
        # wait_data=False because we are only concerned about sending commands fast enough for
        # the lock to be held continuously.
        def master_a(dut, driver):
            adr    = functools.partial(dut.addr_port, row=1, col=1)
            write  = functools.partial(driver.write, wait_data=False)
            yield from write(adr(bank=0), data=0x10)
            yield from write(adr(bank=1), data=0x11)
            yield from write(adr(bank=0), data=0x12, wait_data=True)

        def master_b(dut, driver):
            adr    = functools.partial(dut.addr_port, row=2, col=2)
            write  = functools.partial(driver.write, wait_data=False)
            yield from write(adr(bank=1), data=0x20)
            yield from write(adr(bank=1), data=0x21)
            yield from write(adr(bank=1), data=0x22)
            yield from write(adr(bank=1), data=0x23)
            yield from write(adr(bank=1), data=0x24)

        dut     = CrossbarDUT()
        ports   = [dut.crossbar.get_port() for _ in range(2)]
        drivers = [NativePortDriver(port) for port in ports]
        masters = [master_a(dut, drivers[0]), master_b(dut, drivers[1])]
        data    = self.crossbar_test(dut, masters + drivers[0].generators() + drivers[1].generators())
        expected = [
            self.W(bank=0, addr=dut.addr_iface(row=1, col=1), data=0x10, we=0xff),  # A
            self.W(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x20, we=0xff),  #  B
            self.W(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x21, we=0xff),  #  B
            self.W(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x22, we=0xff),  #  B
            self.W(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x23, we=0xff),  #  B
            self.W(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x24, we=0xff),  #  B
            self.W(bank=1, addr=dut.addr_iface(row=1, col=1), data=0x11, we=0xff),  # A
            self.W(bank=0, addr=dut.addr_iface(row=1, col=1), data=0x12, we=0xff),  # A
        ]
        self.assertEqual(data, expected)

    def test_lock_read(self):
        # Verify that the locking mechanism works.
        def master_a(dut, port):
            driver = NativePortDriver(port)
            adr    = functools.partial(dut.addr_port, row=1, col=1)
            read   = functools.partial(driver.read, wait_data=False)
            yield from read(adr(bank=0))
            yield from read(adr(bank=1))
            yield from read(adr(bank=0))
            # Wait for read data to show up
            for _ in range(16):
                yield

        def master_b(dut, port):
            driver = NativePortDriver(port)
            adr    = functools.partial(dut.addr_port, row=2, col=2)
            read   = functools.partial(driver.read, wait_data=False)
            yield from read(adr(bank=1))
            yield from read(adr(bank=1))
            yield from read(adr(bank=1))
            yield from read(adr(bank=1))
            yield from read(adr(bank=1))

        dut   = CrossbarDUT()
        ports = [dut.crossbar.get_port() for _ in range(2)]
        data  = self.crossbar_test(dut, [master_a(dut, ports[0]), master_b(dut, ports[1])])
        expected = [
            self.R(bank=0, addr=dut.addr_iface(row=1, col=1), data=0x10),  # A
            self.R(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x11),  #  B
            self.R(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x12),  #  B
            self.R(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x13),  #  B
            self.R(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x14),  #  B
            self.R(bank=1, addr=dut.addr_iface(row=2, col=2), data=0x15),  #  B
            self.R(bank=1, addr=dut.addr_iface(row=1, col=1), data=0x16),  # A
            self.R(bank=0, addr=dut.addr_iface(row=1, col=1), data=0x17),  # A
        ]
        self.assertEqual(data, expected)

    def crossbar_stress_test(self, dut, ports, n_banks, n_ops, clocks=None):
        # Runs simulation with multiple masters writing and reading to multiple banks
        controller = ControllerStub(dut.interface,
                                    write_latency=dut.settings.phy.write_latency,
                                    read_latency=dut.settings.phy.read_latency)
        # Store data produced per master
        produced = defaultdict(list)
        prng = random.Random(42)

        def master(dut, driver, num):
            # Choose operation types based on port mode
            ops_choice = {
                "both":  ["w", "r"],
                "write": ["w"],
                "read":  ["r"],
            }[driver.port.mode]

            for i in range(n_ops):
                bank = prng.randrange(n_banks)
                # We will later distinguish data by its row address
                row = num
                col = 0x20 * num + i
                addr = dut.addr_port(bank=bank, row=row, col=col)
                addr_iface = dut.addr_iface(row=row, col=col)
                if prng.choice(ops_choice) == "w":
                    yield from driver.write(addr, data=i)
                    produced[num].append(self.W(bank, addr_iface, data=i, we=0xff))
                else:
                    yield from driver.read(addr)
                    produced[num].append(self.R(bank, addr_iface, data=None))

            yield from driver.wait_all()

        generators = defaultdict(list)
        for i, port in enumerate(ports):
            driver = NativePortDriver(port)
            generators[port.clock_domain].append(master(dut, driver, i))
            generators[port.clock_domain].extend(driver.generators())
        generators["sys"] += controller.generators()
        generators["sys"].append(timeout_generator(80 * n_ops))

        sim_kwargs = {}
        if clocks is not None:
            sim_kwargs["clocks"] = clocks
        run_simulation(dut, generators, **sim_kwargs)

        # Split controller data by master, as this is what we want to compare
        consumed = defaultdict(list)
        for data in controller.data:
            master = data.addr >> (dut.settings.geom.colbits - dut.address_align)
            if isinstance(data, self.R):
                # Master couldn't know the data when it was sending
                data = data._replace(data=None)
            consumed[master].append(data)

        return produced, consumed, controller.data

    def test_stress(self):
        # Test communication in complex scenarios.
        dut = CrossbarDUT()
        ports = [dut.crossbar.get_port() for _ in range(8)]
        produced, consumed, consumed_all = self.crossbar_stress_test(dut, ports, n_banks=4, n_ops=8)
        for master in produced.keys():
            self.assertEqual(consumed[master], produced[master], msg="master = %d" % master)

    def test_stress_single_bank(self):
        # Test communication in complex scenarios
        dut = CrossbarDUT()
        ports = [dut.crossbar.get_port() for _ in range(4)]
        produced, consumed, consumed_all = self.crossbar_stress_test(dut, ports, n_banks=1, n_ops=8)
        for master in produced.keys():
            self.assertEqual(consumed[master], produced[master], msg="master = %d" % master)

    def test_stress_single_master(self):
        # Test communication in complex scenarios.
        dut = CrossbarDUT()
        ports = [dut.crossbar.get_port() for _ in range(1)]
        produced, consumed, consumed_all = self.crossbar_stress_test(dut, ports, n_banks=4, n_ops=8)
        for master in produced.keys():
            self.assertEqual(consumed[master], produced[master], msg="master = %d" % master)

    def test_port_cdc(self):
        # Verify that correct clock domain is being used.
        dut = CrossbarDUT()
        port = dut.crossbar.get_port(clock_domain="other")
        self.assertEqual(port.clock_domain, "other")

    def test_stress_cdc(self):
        # Verify communication when ports are in different clock domains.
        dut = CrossbarDUT()
        clocks = {
            "sys": 10,
            "clk1": (7, 4),
            "clk2": 12,
        }
        master_clocks = ["sys", "clk1", "clk2"]
        ports = [dut.crossbar.get_port(clock_domain=clk) for clk in master_clocks]
        produced, consumed, consumed_all = self.crossbar_stress_test(
            dut, ports, n_banks=4, n_ops=6, clocks=clocks)
        for master in produced.keys():
            self.assertEqual(consumed[master], produced[master], msg="master = %d" % master)

    def test_port_mode(self):
        # Verify that ports in different modes can be requested.
        dut = CrossbarDUT()
        for mode in ["both", "write", "read"]:
            port = dut.crossbar.get_port(mode=mode)
            self.assertEqual(port.mode, mode)

    # NOTE: Stress testing with different data widths would require complicating
    # the logic a lot to support registering data comming in multiple words (in
    # data_handler), address shifting and recreation of packets. Because of this,
    # and because data width converters are tested separately in test_adaptation,
    # here we only test if ports report correct data widths.
    def test_port_data_width_conversion(self):
        # Verify that correct port data widths are being used.
        dut         = CrossbarDUT()
        dw          = dut.interface.data_width
        data_widths = [dw*2, dw, dw//2]
        modes       = ["both", "write", "read"]
        for mode, data_width in itertools.product(modes, data_widths):
            with self.subTest(mode=mode, data_width=data_width):
                port = dut.crossbar.get_port(mode=mode, data_width=data_width)
                self.assertEqual(port.data_width, data_width)
