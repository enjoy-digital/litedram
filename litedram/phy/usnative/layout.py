#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Logical lane and calibration indices, independent of native coordinates.

Inputs must first pass the physical and auxiliary map parsers. Indices are
compact software addresses, never suffixes of Vivado site names.
"""

from typing import Optional
from dataclasses import dataclass

from litedram.phy.usnative.bank import control_wiring
from litedram.phy.usnative.clocks import nibble_clock_wiring
from litedram.phy.usnative.control import control_profiles


@dataclass(frozen=True)
class NativeLane:
    """One logical byte lane; DQ, strobe and mask entries index layout.slices."""
    index: int
    bank: int
    byte: int
    dq: tuple
    strobe: int
    mask: Optional[int]
    controls: tuple


@dataclass(frozen=True)
class NativeLayout:
    """Stable compact indices shared by generated wiring and calibration logic."""
    slices: tuple
    controls: tuple
    banks: tuple
    lanes: tuple
    riu_bytes: tuple

    @property
    def databits(self):
        return sum(len(lane.dq) for lane in self.lanes)

    @property
    def native_word_bits(self):
        return 8 * self.databits


def native_layout(sites, auxiliary, *, family):
    """Describe the initial x8 DDR4 profile; reject unimplemented sidebands.

    Reset and differential negative pads are not serializers. Optional parity
    and alert signals must not disappear during generation: until a complete
    policy exists they are explicit errors. x4 support remains a separate step.
    """
    if any(name in ('par', 'parity', 'alert_n') for name, _ in sites):
        raise ValueError('Parity/alert handling is not implemented in the native profile')
    profiles = control_profiles(sites)
    control_wiring(sites, auxiliary, family=family)
    nibble_clock_wiring(sites, family=family)
    strobes = sorted(i for name, i in sites if name == 'dqs_p')
    dq = sorted(i for name, i in sites if name == 'dq')
    if len(dq) != 8 * len(strobes):
        raise ValueError('Native layout currently requires x8 strobe groups')
    masks = sorted(i for name, i in sites if name == 'dm')
    if masks and masks != strobes:
        raise ValueError('A mask is required for every lane when DM is present')
    active = {key: site for key, site in sites.items()
              if key[0] not in ('dqs_n', 'clk_n', 'reset_n')}
    slices = tuple(sorted(active, key=lambda key: (
        active[key].bank, active[key].byte, active[key].position)))
    indices = {key: i for i, key in enumerate(slices)}
    controls = tuple(sorted(profiles, key=lambda control: next(
        (site.bank, site.byte, site.nibble) for site in active.values()
        if site.control_site == control)))
    control_indices = {control: i for i, control in enumerate(controls)}
    lanes = []
    for lane in strobes:
        strobe = sites['dqs_p', lane]
        keys = [('dq', bit) for bit in range(8 * lane, 8 * lane + 8)]
        lane_keys = keys + [('dqs_p', lane)] + ([('dm', lane)] if masks else [])
        lane_controls = tuple(sorted({control_indices[sites[key].control_site]
                                      for key in lane_keys}))
        lanes.append(NativeLane(lane, strobe.bank, strobe.byte,
            tuple(indices[key] for key in keys), indices['dqs_p', lane],
            indices['dm', lane] if masks else None, lane_controls))
    riu = {}
    for control in controls:
        aux = auxiliary[control]
        halves = riu.setdefault(aux.riu, {})
        if aux.riu_input in halves:
            raise ValueError('Multiple controls occupy one RIU half')
        halves[aux.riu_input] = control_indices[control]
    riu_bytes = tuple((site, halves.get('LOW'), halves.get('UPP'))
                      for site, halves in sorted(riu.items()))
    return NativeLayout(slices, controls,
        tuple(sorted({site.bank for site in active.values()})), tuple(lanes), riu_bytes)
