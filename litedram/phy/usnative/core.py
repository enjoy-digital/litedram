#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Generate native bank interconnect without a reference netlist.

This is a primitive core, not a calibrated DFI PHY. The caller owns PLLs,
reset sequencing, registered launch, I/O buffers and timing qualification.
"""

import re

from dataclasses import dataclass

from litedram.phy.usnative.aux_primitives import (
    RIU_PORTS, TRISTATE_PORTS, emit_tristate)
from litedram.phy.usnative.bank import control_wiring
from litedram.phy.usnative.clocks import nibble_clock_wiring
from litedram.phy.usnative.control import CONTROL_PORTS, control_profiles, emit_control
from litedram.phy.usnative.layout import native_layout
from litedram.phy.usnative.rxtx import RXTX_PORTS, emit_rxtx


@dataclass(frozen=True)
class NativeCore:
    """Generated Verilog, its top-level port schema and the matching lane layout."""
    verilog: str
    ports: dict
    layout: object


def emit_core(module_name, sites, auxiliary, *, family, refclk_mhz):
    """Generate compact-indexed data, control, FIFO, reset and RIU wiring.

    ``sites`` must have explicit sideband ownership established before this
    call. Reset/negative differential pads remain in the map for validation,
    but do not consume serializers. Each physical bank has a separate PLL_CLK
    input. Data clocks are local/partner nibble only; no external forwarding.
    """
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', module_name):
        raise ValueError('Invalid native core module name')
    layout = native_layout(sites, auxiliary, family=family)
    profiles = control_profiles(sites)
    n, c, b = len(layout.slices), len(layout.controls), len(layout.riu_bytes)
    ports = {}
    def port(name, direction, width=1):
        ports[name] = (direction, width)
    for name, width in (
            ('pll_clk', len(layout.banks)), ('fifo_clk', 1), ('riu_clk', 1),
            ('slice_reset', 1), ('control_reset', 1), ('delay_reset', 1),
            ('slice_vtc', 1), ('control_vtc', 1), ('tx_data', 8*n),
            ('serial_in', n), ('data_tristate', len(layout.lanes)),
            ('fifo_rd_en', n), ('rx_rst', n), ('rx_ce', n),
            ('tx_rst', n), ('tx_ce', n), ('phy_rden', 4*c), ('tbyte', 4*c),
            ('riu_addr', 6), ('riu_wdata', 16), ('riu_write', 1), ('riu_select', c)):
        port(name, 'input', width)
    for name, width in (
            ('rx_data', 8*n), ('serial_out', n), ('tristate', n),
            ('fifo_empty', n), ('rx_count', 9*n), ('tx_count', 9*n),
            ('dly_ready', c), ('vtc_ready', c), ('dyn_dci', 7*c),
            ('riu_rdata', 16*b), ('riu_valid', b)):
        port(name, 'output', width)
    buses = control_wiring(sites, auxiliary, family=family)
    clocks = nibble_clock_wiring(sites, family=family)
    connections = buses.connections()
    connections.update(clocks.connections())
    declarations = [buses.declarations(), clocks.declarations()]
    statements, wrappers = [], []
    def word(name, index, width):
        return f'{name}[{width*index + width-1}:{width*index}]' if width > 1 else f'{name}[{index}]'
    # Merge physical interconnect with caller-facing signals exactly once.
    # Missing inputs are errors; unused outputs get explicit sink wires.
    def instantiate(module, name, site, schema, values):
        merged = {port: value for (location, port), value in connections.items() if location == site}
        overlap = set(merged) & set(values)
        if overlap:
            raise ValueError(f'Duplicate generated connections: {site} {overlap}')
        merged.update(values)
        if set(merged) - set(schema):
            raise ValueError(f'Unknown generated ports: {site}')
        for port, (direction, width) in schema.items():
            if port in merged:
                continue
            if direction == 'input':
                raise ValueError(f'Unconnected native input: {site}/{port}')
            wire = f'unused_{name}_{port.lower()}'
            declarations.append(f'wire [{width-1}:0] {wire};')
            merged[port] = wire
        statements.append(f'{module} {name} (\n' + ',\n'.join(
            f'    .{port}({merged[port]})' for port in schema) + '\n);')
    control_index = {site: i for i, site in enumerate(layout.controls)}
    lane_index = {bit: lane.index for lane in layout.lanes
                  for bit in lane.dq + (lane.strobe,) + (() if lane.mask is None else (lane.mask,))}
    for i, key in enumerate(layout.slices):
        site = sites[key]
        role = ('data' if key[0] in ('dq', 'dm') else 'strobe' if key[0] == 'dqs_p'
                else 'clock' if key[0] == 'clk_p' else 'command')
        module = f'{module_name}_slice_{i}'
        wrappers.append(emit_rxtx(module, site, role=role, family=family, refclk_mhz=refclk_mhz))
        ci = control_index[site.control_site]
        values = dict(D=word('tx_data', i, 8), Q=word('rx_data', i, 8),
            O=word('serial_out', i, 1), DATAIN=word('serial_in', i, 1),
            T_OUT=word('tristate', i, 1), FIFO_EMPTY=word('fifo_empty', i, 1),
            FIFO_RD_CLK='fifo_clk', FIFO_RD_EN=word('fifo_rd_en', i, 1),
            T=word('data_tristate', lane_index[i], 1) if role == 'data' else "1'b0",
            TBYTE_IN=f'tri_{ci}')
        for side in ('RX', 'TX'):
            lower = side.lower()
            values.update({side + '_CLK': 'riu_clk', side + '_CE': word(lower + '_ce', i, 1),
                side + '_INC': "1'b1", side + '_LOAD': "1'b0", side + '_CNTVALUEIN': "9'd0",
                side + '_CNTVALUEOUT': word(lower + '_count', i, 9),
                side + '_EN_VTC': 'slice_vtc', side + '_RST': 'slice_reset',
                side + '_RST_DLY': f'(delay_reset | {word(lower + "_rst", i, 1)})'})
        instantiate(module, f'slice_{i}', site.native_site, RXTX_PORTS, values)
    for i, control in enumerate(layout.controls):
        site = next(s for s in sites.values() if s.control_site == control)
        module = f'{module_name}_control_{i}'
        wrappers.append(emit_control(module, profiles[control], family=family))
        declarations.extend((f'wire tri_{i};', f'wire [15:0] riu_data_{i};', f'wire riu_valid_{i};'))
        instantiate(module, f'control_{i}', control, CONTROL_PORTS, dict(
            CLK_FROM_EXT="1'b1", EN_VTC='control_vtc', PLL_CLK=word('pll_clk', layout.banks.index(site.bank), 1),
            REFCLK="1'b0", RIU_CLK='riu_clk', RIU_ADDR='riu_addr', RIU_WR_DATA='riu_wdata',
            RIU_WR_EN='riu_write', RIU_NIBBLE_SEL=word('riu_select', i, 1), RST='control_reset',
            PHY_RDCS0="4'd0", PHY_RDCS1="4'd0", PHY_WRCS0="4'd0", PHY_WRCS1="4'd0",
            PHY_RDEN=word('phy_rden', i, 4), TBYTE_IN=word('tbyte', i, 4),
            DLY_RDY=word('dly_ready', i, 1), VTC_RDY=word('vtc_ready', i, 1),
            DYN_DCI=word('dyn_dci', i, 7), RIU_RD_DATA=f'riu_data_{i}', RIU_VALID=f'riu_valid_{i}'))
        module = f'{module_name}_tristate_{i}'
        wrappers.append(emit_tristate(module, auxiliary[control].tristate,
                                      family=family, refclk_mhz=refclk_mhz))
        instantiate(module, f'tristate_{i}', auxiliary[control].tristate, TRISTATE_PORTS,
            dict(TRI_OUT=f'tri_{i}', CE="1'b0", CLK='riu_clk', CNTVALUEIN="9'd0", EN_VTC='slice_vtc',
                 INC="1'b0", LOAD="1'b0", RST='slice_reset', RST_DLY='delay_reset'))
    for i, (site, lower, upper) in enumerate(layout.riu_bytes):
        values = dict(RIU_RD_DATA=word('riu_rdata', i, 16), RIU_RD_VALID=word('riu_valid', i, 1))
        for half, ci in (('LOW', lower), ('UPP', upper)):
            values['RIU_RD_DATA_' + half] = "16'd0" if ci is None else f'riu_data_{ci}'
            values['RIU_RD_VALID_' + half] = "1'b0" if ci is None else f'riu_valid_{ci}'
        statements.append(f'(* LOC = "{site}", DONT_TOUCH = "TRUE" *)')
        instantiate(f'RIU_OR #(.SIM_DEVICE("{family}"), .SIM_VERSION(2.0))',
                    f'riu_{i}', site, RIU_PORTS, values)
    header = ',\n'.join(f'    {direction} wire [{width-1}:0] {name}'
                        for name, (direction, width) in ports.items())
    text = '\n'.join(['`default_nettype none', f'module {module_name} (', header, ');',
        *declarations, *statements, 'endmodule', '`default_nettype wire', *wrappers])
    return NativeCore(text, ports, layout)
