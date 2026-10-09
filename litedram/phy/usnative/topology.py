#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Native DDR package topology queried from an open Vivado design.

This validates pin grouping, not clock routing, placement or timing closure.
The caller owns the Vivado process and must check its exit status as well as
parse the completed output. No build is launched implicitly.
"""

import re

from dataclasses import dataclass

from litedram.phy.usnative.pins import device_family


_COLUMNS = ("pin", "bank", "function", "site", "site_type", "mate", "master",
            "byte_position", "nibble_position", "native_site", "control_site", "byte")


def vivado_query(pin_map):
    """Return Tcl defining ``usnative_query output_path`` for an open design.

    Package topology is device data, independent of whether the design uses the
    pins. Values embedded in Tcl are restricted tokens, never arbitrary code.
    """
    if not re.fullmatch(r"[a-z0-9-]+", pin_map.part):
        raise ValueError("Invalid part token")
    if device_family(pin_map.part) != pin_map.family:
        raise ValueError("Part/family mismatch")
    package_pins = [pin.package_pin for pin in pin_map.pins]
    if any(not re.fullmatch(r"[A-Z]+[1-9][0-9]*", pin) for pin in package_pins):
        raise ValueError("Invalid package pin token")
    return r'''proc usnative_query {output_path} {
    set part [string tolower [get_property PART [current_design]]]
    if {$part ne "@PART@"} {error "USNative part mismatch: $part"}
    set out [open $output_path w]
    puts $out [join [list USNATIVE 1 @HASH@ $part [version -short]] "\t"]
    puts $out "@COLUMNS@"
    foreach name {@PINS@} {
        set pin [get_package_pins -quiet $name]
        if {[llength $pin] != 1 || ![get_property IS_BONDED $pin]} {
            close $out
            error "Missing or unbonded package pin: $name"
        }
        set site [get_sites -quiet -of_objects $pin]
        if {[llength $site] != 1} {close $out; error "Ambiguous I/O site: $name"}
        # Follow actual device wires, not a presumed IOB/native coordinate match.
        set tx_nodes [get_nodes -quiet -uphill -of_objects [get_nodes -quiet -of_objects [get_site_pins -quiet $site/OP]]]
        set rx_nodes [get_nodes -quiet -downhill -of_objects [get_nodes -quiet -of_objects [get_site_pins -quiet $site/I]]]
        set tx_sites [get_sites -quiet -of_objects [get_site_pins -quiet -of_objects $tx_nodes]]
        set rx_sites [get_sites -quiet -of_objects [get_site_pins -quiet -of_objects $rx_nodes]]
        set native [filter $tx_sites {SITE_TYPE == BITSLICE_RX_TX}]
        set receive [filter $rx_sites {SITE_TYPE == BITSLICE_RX_TX}]
        set ctrl_nodes [get_nodes -quiet -uphill -of_objects [get_nodes -quiet -of_objects [get_site_pins -quiet $site/DYNAMIC_DCI_TS]]]
        set ctrl_sites [get_sites -quiet -of_objects [get_site_pins -quiet -of_objects $ctrl_nodes]]
        set control [filter $ctrl_sites {SITE_TYPE == BITSLICE_CONTROL}]
        set bytegroup [get_pkgpin_bytegroups -quiet -of_objects $pin]
        if {[llength $native] != 1 || $native ne $receive || [llength $control] != 1 || [llength $bytegroup] != 1} {
            close $out
            error "Missing or ambiguous native connectivity: $name TX=$native RX=$receive CONTROL=$control BYTE=$bytegroup"
        }
        puts $out [join [list $name [get_property BANK $pin] [get_property PIN_FUNC $pin] \
            $site [get_property SITE_TYPE $site] [get_property DIFF_PAIR_PIN $pin] \
            [get_property IS_MASTER $pin] [get_property PKGPIN_BYTEGROUP_INDEX $pin] \
            [get_property PKGPIN_NIBBLE_INDEX $pin] $native $control \
            [get_property INDEX_IN_IOBANK $bytegroup]] "\t"]
    }
    puts $out "END\t@COUNT@"
    close $out
}
'''.replace("@PART@", pin_map.part).replace("@HASH@", pin_map.fingerprint).replace(
        "@COLUMNS@", "\\t".join(_COLUMNS)).replace("@PINS@", " ".join(package_pins)).replace(
        "@COUNT@", str(len(package_pins)))


@dataclass(frozen=True)
class NativePinSite:
    package_pin: str
    bank: int
    byte: int
    nibble: str
    position: int
    iob_site: str
    native_site: str
    control_site: str
    mate: str
    master: bool
    function: str


def parse_vivado_map(pin_map, text, *, vivado_version):
    """Validate completed output and return sites keyed by (signal, index).

    The required version is supplied by the caller, not trusted from a cache.
    An input hash, schema or tool mismatch fails closed. Only HP native DDR
    layouts are currently accepted; other native-capable bank types need their
    own validation before support is advertised.
    """
    lines = text.splitlines()
    if device_family(pin_map.part) != pin_map.family:
        raise ValueError("Part/family mismatch")
    expected_header = ["USNATIVE", "1", pin_map.fingerprint, pin_map.part, vivado_version]
    if not lines or lines[0].split("\t") != expected_header:
        raise ValueError("Native map schema, input, part or Vivado version mismatch")
    if len(lines) < 3 or lines[1].split("\t") != list(_COLUMNS):
        raise ValueError("Invalid native map columns")
    if lines[-1] != f"END\t{len(pin_map.pins)}":
        raise ValueError("Incomplete native map")
    expected = {pin.package_pin: pin for pin in pin_map.pins}
    if len(expected) != len(pin_map.pins):
        raise ValueError("Duplicate input package pins")
    found, sites = set(), {}
    for line in lines[2:-1]:
        fields = line.split("\t")
        if len(fields) != len(_COLUMNS):
            raise ValueError("Invalid native map row")
        row = dict(zip(_COLUMNS, fields))
        name = row["pin"]
        if name not in expected or name in found:
            raise ValueError(f"Unexpected or duplicate mapped pin: {name}")
        found.add(name)
        pin = expected[name]
        match = re.search(r"_T([0-3])([LU])_N(\d+)(?:_|$)", row["function"])
        hp_types = ("HPIOB_M", "HPIOB_S", "HPIOB_SNGL")
        if pin_map.family == "ULTRASCALE":
            hp_types += ("HPIOB",)
        if row["site_type"] not in hp_types or match is None:
            raise ValueError(f"Unsupported native bank/site for {name}")
        byte, nibble, position = match.groups()
        if int(row["byte"]) != int(byte):
            raise ValueError(f"Inconsistent byte group: {name}")
        position = int(position)
        if (position not in (range(6) if nibble == "L" else range(6, 13))
                or int(row["byte_position"]) != position
                or int(row["nibble_position"]) != position - (6 if nibble == "U" else 0)):
            raise ValueError(f"Inconsistent nibble position: {name}")
        bank = int(row["bank"])
        if not row["function"].endswith(f"_{bank}"):
            raise ValueError(f"Inconsistent bank: {name}")
        if row["master"] not in ("0", "1"):
            raise ValueError(f"Invalid differential polarity: {name}")
        if not re.fullmatch(r"IOB_X\d+Y\d+", row["site"]):
            raise ValueError(f"Invalid I/O site: {name}")
        if not re.fullmatch(r"BITSLICE_RX_TX_X\d+Y\d+", row["native_site"]):
            raise ValueError(f"Missing native site: {name}")
        if not re.fullmatch(r"BITSLICE_CONTROL_X\d+Y\d+", row["control_site"]):
            raise ValueError(f"Missing native control site: {name}")
        sites[pin.signal, pin.index] = NativePinSite(
            name, bank, int(byte), nibble, position, row["site"], row["native_site"],
            row["control_site"], row["mate"], row["master"] == "1", row["function"])
    if found != set(expected):
        raise ValueError("Missing mapped pins")
    if len({site.native_site for site in sites.values()}) != len(sites):
        raise ValueError("Duplicate native sites")
    controls = {}
    for site in sites.values():
        group = (site.bank, site.byte, site.nibble)
        if group in controls and controls[group] != site.control_site:
            raise ValueError("Inconsistent nibble control site")
        controls[group] = site.control_site
    if len(set(controls.values())) != len(controls):
        raise ValueError("Control site shared across different nibbles")
    for signal in ("dqs", "clk"):
        for (name, index), positive in sites.items():
            if name != signal + "_p":
                continue
            negative = sites.get((signal + "_n", index))
            if (negative is None or not positive.master or negative.master
                    or positive.mate != negative.package_pin
                    or negative.mate != positive.package_pin
                    or positive.bank != negative.bank):
                raise ValueError(f"Invalid differential pair: {signal}[{index}]")
            if signal == "dqs" and (positive.position not in (0, 6)
                    or not re.search(r"_(?:DBC|QBC)(?:_|$)", positive.function)):
                raise ValueError(f"DQS is not on a native strobe site: {index}")
    dq = sorted((index, site) for (name, index), site in sites.items() if name == "dq")
    strobes = [site for (name, index), site in sites.items() if name == "dqs_p"]
    if not strobes or len(dq) not in (4 * len(strobes), 8 * len(strobes)):
        raise ValueError("Invalid data/strobe grouping")
    group_width = len(dq) // len(strobes)
    for index, data in dq:
        strobe = sites.get(("dqs_p", index // group_width))
        if (strobe is None or (data.bank, data.byte) != (strobe.bank, strobe.byte)
                or group_width == 4 and data.nibble != strobe.nibble):
            raise ValueError(f"DQ[{index}] lies outside its strobe group")
    for (name, index), mask in sites.items():
        if name != "dm":
            continue
        strobe = sites.get(("dqs_p", index * (8 // group_width)))
        if strobe is None or (mask.bank, mask.byte) != (strobe.bank, strobe.byte):
            raise ValueError(f"DM[{index}] lies outside its byte group")
    return sites
