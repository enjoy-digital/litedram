#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Partner-nibble clocks for the local-strobe native DDR4 profile.

The caller supplies validated physical sites. This does not generate PLL,
external forwarding, FIFO clocks, resets or timing constraints.
"""

import re

from dataclasses import dataclass

from litedram.phy.usnative.control import control_profiles


@dataclass(frozen=True)
class NibbleClock:
    name: str
    source_site: str
    source_port: str
    sink_site: str
    sink_port: str
    enabled: bool


@dataclass(frozen=True)
class NibbleClockWiring:
    clocks: tuple
    unused_inputs: tuple

    def declarations(self):
        return "".join(f"wire {clock.name};\n" for clock in self.clocks)

    def connections(self):
        result = {}
        for clock in self.clocks:
            result[clock.source_site, clock.source_port] = clock.name
            result[clock.sink_site, clock.sink_port] = clock.name
        for key in self.unused_inputs:
            result[key] = "1'b0"
        return result


def nibble_clock_wiring(sites, *, family):
    """Connect P/N outputs to the opposite nibble's inputs in each byte.

    Paired controls retain both directions, including disabled receive paths.
    A lone control with local strobe ties unused partner inputs low. Borrowing
    requires a distinct partner in the same physical bank and byte; control
    coordinates are never used to infer adjacency.
    """
    if family not in ("ULTRASCALE", "ULTRASCALE_PLUS"):
        raise ValueError("Unsupported native family")
    profiles = control_profiles(sites)
    locations, physical = {}, {}
    for (signal, _), site in sites.items():
        if signal in ("dqs_n", "clk_n", "reset_n"):
            continue
        if not re.fullmatch(r"BITSLICE_CONTROL_X\d+Y\d+", site.control_site):
            raise ValueError("Invalid control site")
        if site.nibble not in ("L", "U"):
            raise ValueError("Invalid native nibble")
        key = (site.bank, site.byte, site.nibble)
        if locations.setdefault(site.control_site, key) != key:
            raise ValueError("Control spans physical nibbles")
        if physical.setdefault(key, site.control_site) != site.control_site:
            raise ValueError("Multiple controls occupy one physical nibble")
    clocks, unused = [], []
    for control, (bank, byte, nibble) in sorted(locations.items()):
        partner = physical.get((bank, byte, "U" if nibble == "L" else "L"))
        if partner is None and profiles[control].other_nibble:
            raise ValueError("Borrowed strobe requires the opposite nibble")
        for clock in ("PCLK", "NCLK"):
            if partner is None:
                unused.append((control, f"{clock}_NIBBLE_IN"))
            else:
                clocks.append(NibbleClock(
                    f"usnative_{partner.lower()}_{clock.lower()}_partner",
                    partner, f"{clock}_NIBBLE_OUT", control,
                    f"{clock}_NIBBLE_IN", profiles[control].other_nibble))
    return NibbleClockWiring(tuple(clocks), tuple(unused))
