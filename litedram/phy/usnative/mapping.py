#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Versioned logical calibration contract; no device database records are exported."""

import json
import hashlib


class NativeMapping:
    """Translate a validated core layout into bounded software resource IDs.

    Slice and control IDs index the generated core's buses, not Vivado site
    coordinates. The configuration identity covers these logical assignments
    and the operating profile so firmware cannot train a different gateware ABI.
    """
    major        = 1
    minor        = 0
    capabilities = 1  # Logical tap/control addressing.

    def __init__(self, layout, *, profile=None):
        self.layout        = layout
        self.tap_count     = len(layout.slices)
        self.control_count = len(layout.controls)
        self.lane_count    = len(layout.lanes)
        if not 1 <= self.tap_count <= 65535 or not 1 <= self.control_count <= 32:
            raise ValueError('Native mapping exceeds ABI resource limits')
        if not 1 <= self.lane_count <= 8:
            raise ValueError('Native mapping supports one to eight x8 lanes')
        if tuple(lane.index for lane in layout.lanes) != tuple(range(self.lane_count)):
            raise ValueError('Native lane IDs must be contiguous')
        if any(len(lane.dq) != 8 or not lane.controls for lane in layout.lanes):
            raise ValueError('Every x8 lane needs eight DQ and control ownership')
        self.dq_taps  = tuple(tap for lane in layout.lanes for tap in lane.dq)
        self.dqs_taps = tuple(lane.strobe for lane in layout.lanes)
        self.dm_taps  = tuple(lane.mask for lane in layout.lanes if lane.mask is not None)
        self.ck_taps  = tuple(i for i, (name, _) in enumerate(layout.slices) if name == 'clk_p')
        if not self.ck_taps:
            raise ValueError('Native mapping requires a clock tap')
        self.data_controls = tuple(sorted({c for lane in layout.lanes for c in lane.controls}))
        self.lane_controls = tuple(tuple(lane.controls) for lane in layout.lanes)
        if len(self.dq_taps) != 8*self.lane_count or len(self.dm_taps) not in (0, self.lane_count):
            raise ValueError('Invalid x8 lane geometry')
        taps = self.dq_taps + self.dqs_taps + self.dm_taps + self.ck_taps
        if len(taps) != len(set(taps)) or any(not 0 <= tap < self.tap_count for tap in taps):
            raise ValueError('Duplicate or out-of-range logical tap')
        if any(not 0 <= c < self.control_count for c in self.data_controls):
            raise ValueError('Invalid logical control group')
        self.riu_indices = [None]*self.control_count
        for i, (_, lower, upper) in enumerate(layout.riu_bytes):
            for control in (lower, upper):
                if control is None:
                    continue
                if not 0 <= control < self.control_count or self.riu_indices[control] is not None:
                    raise ValueError('Invalid or duplicate RIU ownership')
                self.riu_indices[control] = i
        if None in self.riu_indices:
            raise ValueError('Missing RIU ownership')
        self.riu_indices = tuple(self.riu_indices)
        self.profile     = dict(profile or {})
        encoded          = json.dumps(self.logical_descriptor(), sort_keys=True, separators=(',', ':'))
        self.config_id   = int.from_bytes(hashlib.sha256(encoded.encode()).digest()[:4], 'big')

    def logical_descriptor(self):
        """Only logical ABI values; never include sites, banks or package pins."""
        return dict(
            major         = self.major,
            minor         = self.minor,
            capabilities  = self.capabilities,
            tap_count     = self.tap_count,
            control_count = self.control_count,
            lane_count    = self.lane_count,
            dq_taps       = self.dq_taps,
            dqs_taps      = self.dqs_taps,
            dm_taps       = self.dm_taps,
            ck_taps       = self.ck_taps,
            data_controls = self.data_controls,
            lane_controls = self.lane_controls,
            riu_indices   = self.riu_indices,
            profile       = self.profile,
        )

    def c_defines(self):
        values = dict(
            ABI_MAJOR     = self.major,
            ABI_MINOR     = self.minor,
            CONFIG_ID     = self.config_id,
            REQUIRED_CAPS = self.capabilities,
            TAP_COUNT     = self.tap_count,
            CONTROL_COUNT = self.control_count,
            LANE_COUNT    = self.lane_count,
        )
        for name in ('dq_taps', 'dqs_taps', 'dm_taps', 'ck_taps', 'data_controls'):
            entries = getattr(self, name)
            values[name.upper()] = '{' + ', '.join(map(str, entries or (0,))) + '}'
            values[name.upper() + '_COUNT'] = len(entries)
        return values
