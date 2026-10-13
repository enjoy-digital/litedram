#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Synthetic ABI/core simulations, not vendor primitive/package qualification.

Twenty-four family/width/topology cases use invented coordinates, never saved
Vivado query results. The analog primitive boundary is driven by the testbench.
"""

import json
import unittest

from dataclasses import replace

from migen import Module, Signal
from migen.sim import run_simulation
from litedram.phy.usnative.adapter import connect_core, core_ports, signal_sites
from litedram.phy.usnative.core import emit_core
from litedram.phy.usnative.fifo import NativeFIFORead
from litedram.phy.usnative.mapping import NativeMapping
from litedram.phy.usnative.riu_transaction import RIUTransaction
from test.test_usnative_layout import layout_fixture


def synthetic_fixture(width, variant):
    """Permute lanes, bank spans and unrelated slice/control/RIU coordinates."""
    original, old_auxiliary = layout_fixture()
    sites, auxiliary = {}, {}
    lanes_per_bank = (1, 2, 4)[variant]
    for lane in range(width // 8):
        bank, byte = 37 + lane // lanes_per_bank, lane % lanes_per_bank
        controls = {old: f'BITSLICE_CONTROL_X{17+variant}Y{300+19*lane+j*5}'
                    for j, old in enumerate(list(old_auxiliary)[:2])}
        for (name, index), site in original.items():
            if index >= (8 if name == 'dq' else 1):
                continue
            logical = (index*(1 if variant == 0 else -1) + variant*3) % 8
            new_index = 8*lane + logical if name == 'dq' else lane
            sites[name, new_index] = replace(site, bank=bank, byte=byte,
                native_site=f'BITSLICE_RX_TX_X{21+variant}Y{1000+31*lane+site.position}',
                control_site=controls[site.control_site])
        for old, new in controls.items():
            aux = old_auxiliary[old]
            ordinal = width//8-lane if variant else lane
            auxiliary[new] = replace(aux, control=new,
                tristate=f'BITSLICE_TX_X{33+variant}Y{700+17*lane+(aux.riu_input == "UPP")}',
                riu=f'RIU_OR_X{41+variant}Y{900+11*ordinal}')
    # A separate command/clock group exercises non-data controls and CK taps.
    control = f'BITSLICE_CONTROL_X{17+variant}Y9000'
    for key, position in ((('clk_p', 0), 0), (('a', 0), 2)):
        sites[key] = replace(original['dq', position], bank=99, byte=0,
            native_site=f'BITSLICE_RX_TX_X{21+variant}Y{9000+position}',
            control_site=control)
    aux = next(iter(old_auxiliary.values()))
    auxiliary[control] = replace(aux, control=control,
        tristate=f'BITSLICE_TX_X{33+variant}Y9000',
        riu=f'RIU_OR_X{41+variant}Y10000', riu_input='LOW')
    return sites, auxiliary


class TestUSNativeMapping(unittest.TestCase):
    def run_case(self, width, family, variant, profile=None):
        sites, auxiliary = synthetic_fixture(width, variant)
        core = emit_core('usnative_core', sites, auxiliary, family=family, refclk_mhz=2400)
        mapping = NativeMapping(core.layout, profile=profile or dict(rate=2400, width=width, family=family))
        self.assertEqual(mapping.lane_count, width//8)
        self.assertEqual(len(mapping.dq_taps), width)
        self.assertEqual(core.verilog.count('RXTX_BITSLICE #('), mapping.tap_count)
        self.assertEqual(core.verilog.count('BITSLICE_CONTROL #('), mapping.control_count)
        self.assertEqual(len(signal_sites(core.layout)), mapping.tap_count)
        descriptor = json.dumps(mapping.logical_descriptor())
        for forbidden in ('BITSLICE', 'RIU_OR', 'package_pin', 'bank', 'site'):
            self.assertNotIn(forbidden, descriptor)
        for bit, tap in enumerate(mapping.dq_taps):
            self.assertEqual(core.layout.slices[tap], ('dq', bit))
        self.simulate_adapter(core, sites, mapping)
        self.simulate_fifo(core.layout)
        self.simulate_riu(mapping)
        return mapping

    def simulate_adapter(self, core, sites, mapping):
        dut = Module()
        signals = {name: Signal(width) for name, (_, width) in core_ports(core.layout).items()}
        n = mapping.tap_count
        extras = dict(i_rx_delay_rst=n, i_rx_delay_ce=n, i_tx_delay_rst=n,
            i_tx_delay_ce=n, o_rx_delay_count=9*n, o_tx_delay_count=9*n,
            o_fifo_empty=n, i_dqs_tx_data=8*mapping.lane_count,
            i_data_tristate=1, i_slice_en_vtc=1)
        signals.update({name: Signal(width) for name, width in extras.items()})
        boundary = {('i_' if name.startswith('i_') else 'o_') + name: signal
                    for name, signal in signals.items()}
        connect_core(dut, core, sites, boundary)
        fragment = dut.get_fragment()
        instance = next(iter(fragment.specials))
        native = {item.name: item.expr for item in instance.items if hasattr(item, 'expr')}
        fragment.specials = set()  # Test fabric routing; no analog primitive model.
        def check():
            tx = sum(((bit*17+7) & 255) << (8*bit) for bit in range(core.layout.databits))
            yield signals['i_dq_tx_data'].eq(tx)
            yield signals['i_fifo_rd_en'].eq((1 << n)-1)
            yield signals['i_riu_nibble_sel'].eq(1 << (mapping.control_count-1))
            yield signals['i_rx_delay_ce'].eq(1 << mapping.dq_taps[-1])
            received = sum(((tap*29+7) & 255) << (8*tap) for tap in range(n))
            yield native['rx_data'].eq(received)
            yield native['fifo_empty'].eq(1 << mapping.dq_taps[-1])
            yield native['serial_out'].eq(sum((tap & 1) << tap for tap in range(n)))
            yield
            yield
            packed = yield native['tx_data']
            rx = yield signals['o_dq_rx_data']
            serial = yield signals['o_dq_serial_out']
            for bit, tap in enumerate(mapping.dq_taps):
                self.assertEqual((packed >> (8*tap)) & 255, (tx >> (8*bit)) & 255)
                self.assertEqual((rx >> (8*bit)) & 255, (received >> (8*tap)) & 255)
                self.assertEqual((serial >> bit) & 1, tap & 1)
            self.assertEqual((packed >> (8*mapping.ck_taps[0])) & 255, 0x55)
            self.assertEqual((yield native['fifo_rd_en']), (1 << n)-1)
            self.assertEqual((yield native['riu_select']), 1 << (mapping.control_count-1))
            self.assertEqual((yield native['rx_ce']), 1 << mapping.dq_taps[-1])
            self.assertEqual((yield signals['o_fifo_empty']), 1 << mapping.dq_taps[-1])
        run_simulation(fragment, check())

    def simulate_fifo(self, layout):
        dut = NativeFIFORead(layout)
        def check():
            yield dut.ready.eq(1)
            yield dut.independent.eq(1)
            for lane in layout.lanes:
                yield dut.empty.eq(1 << lane.dq[-1])
                yield dut.software_control.eq(0)
                yield
                yield
                self.assertEqual((yield dut.read_enable), 0)
                yield dut.software_control.eq(1)
                yield
                yield
                self.assertEqual((yield dut.lane_drain), ((1 << len(layout.lanes))-1) ^ (1 << lane.index))
            yield dut.empty.eq(0)
            yield dut.ready.eq(0)
            yield
            yield
            self.assertEqual((yield dut.read_enable), 0)
        run_simulation(dut, check())

    def simulate_riu(self, mapping):
        dut = RIUTransaction(mapping.control_count, mapping.riu_indices)
        def check():
            count = max(mapping.riu_indices)+1
            yield dut.native_valid.eq((1 << count)-1)
            yield dut.native_rdata.eq(sum((0x1200+i) << (16*i) for i in range(count)))
            for control, byte in enumerate(mapping.riu_indices):
                yield dut.select.eq(control)
                yield dut.address.eq(17)
                yield dut.request.eq(1)
                yield
                yield dut.request.eq(0)
                for _ in range(150):
                    yield
                    if (yield dut.valid) and not (yield dut.busy):
                        break
                else:
                    self.fail('RIU request did not complete')
                self.assertEqual((yield dut.error), 0)
                self.assertEqual((yield dut.rdata), 0x1200+byte)
                yield
        run_simulation(dut, check(), clocks={'sys': 10, 'riu': 20})

    def test_version_identity_and_invalid_geometry(self):
        sites, auxiliary = synthetic_fixture(16, 1)
        core = emit_core('mapping_test', sites, auxiliary, family='ULTRASCALE_PLUS', refclk_mhz=2400)
        mapping = NativeMapping(core.layout, profile=dict(rate=2400))
        self.assertEqual(mapping.major, 1)
        self.assertEqual(mapping.config_id, NativeMapping(core.layout, profile=dict(rate=2400)).config_id)
        self.assertNotEqual(mapping.config_id, NativeMapping(core.layout, profile=dict(rate=2667)).config_id)
        self.assertNotEqual(
            NativeMapping(core.layout, profile=dict(rate=2400, with_debug=False)).config_id,
            NativeMapping(core.layout, profile=dict(rate=2400, with_debug=True)).config_id)
        self.assertEqual(mapping.c_defines()['DQ_TAPS_COUNT'], 16)
        renamed = replace(core.layout,
            controls=tuple(f'BITSLICE_CONTROL_X999Y{i}' for i in range(len(core.layout.controls))),
            banks=tuple(bank+100 for bank in core.layout.banks),
            lanes=tuple(replace(lane, bank=lane.bank+100) for lane in core.layout.lanes),
            riu_bytes=tuple((f'RIU_OR_X999Y{i}', low, high)
                            for i, (_, low, high) in enumerate(core.layout.riu_bytes)))
        self.assertEqual(mapping.config_id, NativeMapping(renamed, profile=dict(rate=2400)).config_id)
        with self.assertRaisesRegex(ValueError, 'clock|CK'):
            NativeMapping(replace(core.layout,
                slices=tuple(('a', 31) if name == 'clk_p' else (name, index)
                             for name, index in core.layout.slices)))
        bad_lane = replace(core.layout.lanes[0], dq=(0,)*8)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            NativeMapping(replace(core.layout, lanes=(bad_lane, core.layout.lanes[1])))
        with self.assertRaisesRegex(ValueError, 'Missing RIU'):
            NativeMapping(replace(core.layout, riu_bytes=()))
        with self.assertRaisesRegex(ValueError, 'contiguous'):
            NativeMapping(replace(core.layout, lanes=(replace(core.layout.lanes[0], index=5), core.layout.lanes[1])))


for _family in ('ULTRASCALE', 'ULTRASCALE_PLUS'):
    for _width in (8, 16, 32, 64):
        for _variant in range(3):
            def _case(self, family=_family, width=_width, variant=_variant):
                self.run_case(width, family, variant)
            setattr(TestUSNativeMapping, f'test_{_family.lower()}_x{_width}_topology{_variant}', _case)
