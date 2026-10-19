#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Native control-bus wiring derived from validated pin and auxiliary maps.

This covers 40-bit RX/TX control buses, not data, clocks, FIFO or RIU wiring.
Unused controller input slots are tied low; unused output slots stay unconnected.
"""

import re

from dataclasses import dataclass

from litedram.phy.usnative.control import control_profiles


@dataclass(frozen=True)
class ControlBus:
    name: str
    source_site: str
    source_port: str
    sink_site: str
    sink_port: str
    width: int = 40


@dataclass(frozen=True)
class ControlWiring:
    buses: tuple
    unused_inputs: tuple

    def declarations(self):
        return "\n".join(f"wire [{bus.width-1}:0] {bus.name};" for bus in self.buses) + "\n"

    def connections(self):
        result = {}
        for bus in self.buses:
            result[bus.source_site, bus.source_port] = bus.name
            result[bus.sink_site, bus.sink_port] = bus.name
        for site, port in self.unused_inputs:
            result[site, port] = "40'd0"
        return result


def control_wiring(sites, auxiliary, *, family):
    """Return explicit native bus endpoints and unused-input tie-offs.

    Lower-nibble positions 0..5 map to controller slots 0..5. Upper-nibble
    positions 6..12 map to slots 0..6. Negative differential partners and DDR
    reset are excluded from serialization. No site-coordinate arithmetic is used.
    """
    if family not in ("ULTRASCALE", "ULTRASCALE_PLUS"):
        raise ValueError("Unsupported native family")
    controls = control_profiles(sites)
    if not set(controls) <= set(auxiliary):
        raise ValueError("Missing auxiliary mapping for a native control")
    buses, occupied, native_used, tri_used = [], set(), set(), set()
    for (signal, _), site in sorted(sites.items()):
        if signal in ("dqs_n", "clk_n", "reset_n"):
            continue
        if not re.fullmatch(r"BITSLICE_RX_TX_X\d+Y\d+", site.native_site):
            raise ValueError("Invalid RXTX site")
        if site.nibble == "L" and 0 <= site.position < 6:
            slot = site.position
        elif site.nibble == "U" and 6 <= site.position < 13:
            slot = site.position - 6
        else:
            raise ValueError("Invalid native nibble position")
        key = (site.control_site, slot)
        if key in occupied or site.native_site in native_used:
            raise ValueError("Multiple serializers occupy one control slot")
        occupied.add(key)
        native_used.add(site.native_site)
        for direction in ("RX", "TX"):
            prefix = f"usnative_{site.control_site.lower()}_{direction.lower()}_{slot}"
            buses.append(ControlBus(prefix + "_to_slice", site.control_site,
                f"{direction}_BIT_CTRL_OUT{slot}", site.native_site, f"{direction}_BIT_CTRL_IN"))
            buses.append(ControlBus(prefix + "_from_slice", site.native_site,
                f"{direction}_BIT_CTRL_OUT", site.control_site, f"{direction}_BIT_CTRL_IN{slot}"))
    unused = []
    for control in sorted(controls):
        if not re.fullmatch(r"BITSLICE_CONTROL_X\d+Y\d+", control):
            raise ValueError("Invalid control site")
        aux = auxiliary[control]
        if aux.control != control or not re.fullmatch(r"BITSLICE_TX_X\d+Y\d+", aux.tristate):
            raise ValueError("Invalid tristate association")
        if aux.tristate in tri_used:
            raise ValueError("Shared tristate association")
        tri_used.add(aux.tristate)
        prefix = f"usnative_{control.lower()}_tri"
        buses.append(ControlBus(prefix + "_to_slice", control, "TX_BIT_CTRL_OUT_TRI",
                                aux.tristate, "BIT_CTRL_IN"))
        buses.append(ControlBus(prefix + "_from_slice", aux.tristate, "BIT_CTRL_OUT",
                                control, "TX_BIT_CTRL_IN_TRI"))
        for slot in range(7):
            if (control, slot) not in occupied:
                unused.extend((control, f"{d}_BIT_CTRL_IN{slot}") for d in ("RX", "TX"))
    buses.sort(key=lambda bus: bus.name)
    return ControlWiring(tuple(buses), tuple(unused))
