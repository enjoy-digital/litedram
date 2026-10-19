#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Logical serializer boundary between the DFI datapath and native core."""

from migen import Instance, Replicate, Signal


def signal_name(signal, index):
    if signal in ('we_n', 'cas_n', 'ras_n'):
        return 'adr', 14 + ('we_n', 'cas_n', 'ras_n').index(signal)
    return {'a': 'adr', 'dm': 'dm_n', 'dqs_p': 'dqs_t', 'clk_p': 'ck_t'}.get(signal, signal), index


def signal_sites(layout):
    """Map board signal names to compact, generated logical tap IDs."""
    result = {}
    for tap, (signal, index) in enumerate(layout.slices):
        name, index = signal_name(signal, index)
        key = f'o_{name}_serial_out[{index}]'
        if key in result:
            raise ValueError('Overlapping DDR command/address aliases')
        result[key] = tap
    return result


def core_ports(layout):
    n, c, lanes = len(layout.slices), len(layout.controls), len(layout.lanes)
    ports = {}

    def add(direction, width, *names):
        for name in names:
            ports[name] = direction, width

    add('input', 1, 'i_div_clk', 'i_en_vtc', 'i_riu_clk', 'i_rst',
        'i_clb2phy_tristate_odelay_rst', 'i_riu_wr_en')
    add('input', len(layout.banks), 'i_pll_clk')
    add('input', n, 'i_fifo_rd_en')
    add('input', 4*c, 'i_phy_rden', 'i_data_tbyte')
    add('input', 16, 'i_riu_wr_data')
    add('input', 6, 'i_riu_addr')
    add('input', c, 'i_riu_nibble_sel')
    add('input', 4, 'i_cmd_tbyte')
    add('output', c, 'o_dly_rdy', 'o_vtc_rdy')
    add('output', layout.databits + lanes, 'o_dyn_dci')
    widths = {}
    for signal, index in layout.slices:
        name, index = signal_name(signal, index)
        widths[name] = max(widths.get(name, 0), index + 1)
    for name, width in widths.items():
        add('output', width, f'o_{name}_serial_out')
        if name in ('dq', 'dm_n', 'dqs_t'):
            add('output', width, f'o_{name}_tristate')
            add('input', width, f'i_{name}_serial_in')
        if name in ('dq', 'dm_n'):
            add('output', 8*width, f'o_{name}_rx_data')
        if name not in ('dqs_t', 'ck_t'):
            add('input', 8*width, f'i_{name}_tx_data')
    return ports


def connect_core(module, core, sites, boundary):
    """Route compact buses; physical coordinates remain private to the core."""
    layout = core.layout
    native = {name: Signal(width, name='core_' + name) for name, (_, width) in core.ports.items()}
    pins   = {name[2:]: value for name, value in boundary.items()}
    inputs = dict(
        pll_clk       = 'i_pll_clk',
        fifo_clk      = 'i_div_clk',
        riu_clk       = 'i_riu_clk',
        slice_reset   = 'i_clb2phy_tristate_odelay_rst',
        control_reset = 'i_rst',
        delay_reset   = 'i_clb2phy_tristate_odelay_rst',
        slice_vtc     = 'i_slice_en_vtc',
        control_vtc   = 'i_en_vtc',
        riu_addr      = 'i_riu_addr',
        riu_wdata     = 'i_riu_wr_data',
        riu_write     = 'i_riu_wr_en',
        riu_select    = 'i_riu_nibble_sel',
        phy_rden      = 'i_phy_rden',
        fifo_rd_en    = 'i_fifo_rd_en',
    )
    for target, source in inputs.items():
        module.comb += native[target].eq(pins[source])
    module.comb += [
        native['data_tristate'].eq(Replicate(pins['i_data_tristate'], len(layout.lanes))),
        pins['o_dly_rdy'].eq(native['dly_ready']),
        pins['o_vtc_rdy'].eq(native['vtc_ready']),
        pins['o_fifo_empty'].eq(native['fifo_empty']),
    ]
    data_controls = {c for lane in layout.lanes for c in lane.controls}
    for c in range(len(layout.controls)):
        module.comb += native['tbyte'][4*c:4*c+4].eq(
            pins['i_data_tbyte'][4*c:4*c+4] if c in data_controls else pins['i_cmd_tbyte'])
    for i, (signal, index) in enumerate(layout.slices):
        name, pad_index = signal_name(signal, index)
        receive = signal in ('dq', 'dm', 'dqs_p')
        data = (0x55 if signal == 'clk_p' else pins['i_dqs_tx_data'][8*index:8*index+8]
                if signal == 'dqs_p' else pins[f'i_{name}_tx_data'][8*pad_index:8*pad_index+8])
        module.comb += [
            native['tx_data'][8*i:8*i+8].eq(data),
            pins[f'o_{name}_serial_out'][pad_index].eq(native['serial_out'][i]),
            native['serial_in'][i].eq(pins[f'i_{name}_serial_in'][pad_index] if receive else 0),
        ]
        if receive:
            module.comb += pins[f'o_{name}_tristate'][pad_index].eq(native['tristate'][i])
        if signal in ('dq', 'dm'):
            module.comb += pins[f'o_{name}_rx_data'][8*pad_index:8*pad_index+8].eq(native['rx_data'][8*i:8*i+8])
            site = sites[signal, index]
            ci   = layout.controls.index(site.control_site)
            slot = site.position if site.nibble == 'L' else site.position - 6
            di   = index if signal == 'dq' else layout.databits + index
            module.comb += pins['o_dyn_dci'][di].eq(native['dyn_dci'][7*ci+slot])
    for side in ('rx', 'tx'):
        module.comb += [
            native[side+'_rst'].eq(pins[f'i_{side}_delay_rst']),
            native[side+'_ce'].eq(pins[f'i_{side}_delay_ce']),
            pins[f'o_{side}_delay_count'].eq(native[side+'_count']),
        ]
    module.specials += Instance('usnative_core', **{
        ('i_' if direction == 'input' else 'o_') + name: native[name]
        for name, (direction, _) in core.ports.items()})
    return native['riu_rdata'], native['riu_valid']
