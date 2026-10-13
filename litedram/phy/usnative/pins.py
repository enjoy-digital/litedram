#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Extract native DDR pin inputs from resolved LiteX platform constraints.

This stage does not query the Vivado device database. Byte/nibble sites,
differential partners, bank legality and clock routes require a later stage.
"""

import re
import json
import hashlib

from dataclasses import asdict, dataclass

from litex.build.generic_platform import IOStandard


def device_family(part):
    """Return native SelectIO family eligibility, not part qualification."""
    device = part.lower().split("-", 1)[0]
    if re.fullmatch(r"xc(?:ku|vu)\d+", device):
        return "ULTRASCALE"
    if (re.fullmatch(r"xc(?:au|ku|vu)\d+p", device)
            or re.fullmatch(r"xczu\d+(?:eg|ev|cg|dr)", device)
            or device in {"xcu200", "xcu250", "xcu280"}):
        return "ULTRASCALE_PLUS"
    raise ValueError(f"Unsupported native DDR device: {part}")


@dataclass(frozen=True)
class DDRPin:
    signal: str
    index: int
    package_pin: str
    iostandard: str


@dataclass(frozen=True)
class DDRPinMap:
    part: str
    family: str
    pins: tuple

    def to_dict(self):
        return dict(schema_version=1, part=self.part, family=self.family,
                    pins=[asdict(pin) for pin in self.pins])

    @property
    def fingerprint(self):
        """Stable input hash; a device-query cache must also key tool/schema versions."""
        data = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()


def extract_ddr_pins(platform, pads):
    """Extract one requested DDR4 resource without importing board definitions.

    Uses signal identity, so multiple channels and unrelated requested resources
    cannot be confused. Connector aliases have already been resolved by LiteX.
    Positive/negative pin counts are checked here, physical pairing is not.
    """
    family = device_family(platform.device)
    signals = {}
    for field in pads.layout:
        name = field[0]
        signal = getattr(pads, name)
        if not hasattr(signal, "nbits"):
            raise ValueError(f"Nested DDR pad field is unsupported: {name}")
        signals[name] = signal
    required = {"a", "ba", "bg", "act_n", "dq", "dqs_p", "dqs_n",
                "clk_p", "clk_n", "cke", "odt", "reset_n"}
    missing = required - signals.keys()
    if missing:
        raise ValueError(f"Missing DDR4 signals: {', '.join(sorted(missing))}")
    widths = {name: len(signal) for name, signal in signals.items()}
    if widths["dq"] % 8 or widths["dq"] == 0:
        raise ValueError("DDR data width must be a positive multiple of eight")
    lanes = widths["dq"] // 8
    # x4 DIMMs have two strobes per byte; preserving these pins does not imply
    # that their native topology or calibration is already implemented.
    if widths["dqs_p"] not in (lanes, 2 * lanes) or widths["dqs_n"] != widths["dqs_p"]:
        raise ValueError("DDR DQS width must describe x4 or x8 strobe groups")
    if widths["clk_p"] != widths["clk_n"]:
        raise ValueError("DDR clock pair widths differ")
    if "dm" in widths and widths["dm"] != lanes:
        raise ValueError("DDR mask width must match the byte lane count")

    constraints = platform.constraint_manager.get_sig_constraints()
    pins, used_pins = [], set()
    for name, signal in sorted(signals.items()):
        matches = [row for row in constraints if row[0] is signal]
        if len(matches) != 1:
            raise ValueError(f"Expected one pin constraint for DDR signal {name}")
        _, package_pins, others, _ = matches[0]
        if len(package_pins) != widths[name]:
            raise ValueError(f"Pin count differs from signal width: {name}")
        standards = [c.name for c in others if isinstance(c, IOStandard)]
        if len(standards) != 1:
            raise ValueError(f"Expected one I/O standard for DDR signal {name}")
        for index, pin in enumerate(package_pins):
            pin = pin.upper()
            if not re.fullmatch(r"[A-Z]+[1-9][0-9]*", pin) or pin == "X":
                raise ValueError(f"Unresolved or invalid DDR package pin: {pin}")
            if pin in used_pins:
                raise ValueError(f"Duplicate DDR package pin: {pin}")
            used_pins.add(pin)
            pins.append(DDRPin(name, index, pin, standards[0]))
    return DDRPinMap(platform.device.lower(), family, tuple(pins))
