#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Query the dedicated tristate and RIU sites of validated native controls."""

import re

from dataclasses import dataclass


@dataclass(frozen=True)
class AuxiliarySites:
    control: str
    tristate: str
    riu: str
    riu_input: str


def _controls(sites):
    controls = {}
    for site in sites.values():
        if not re.fullmatch(r"BITSLICE_CONTROL_X\d+Y\d+", site.control_site):
            raise ValueError("Invalid control site")
        group = (site.bank, site.byte, site.nibble)
        if site.nibble not in ("L", "U") or controls.get(site.control_site, group) != group:
            raise ValueError("Inconsistent control group")
        controls[site.control_site] = group
    if not controls:
        raise ValueError("Empty native control map")
    return controls


def vivado_auxiliary_query(pin_map, sites):
    """Return Tcl defining ``usnative_auxiliary_query output_path``.

    The caller checks the process exit status and parses the completed export.
    Device nodes, rather than coordinate arithmetic, determine each connection.
    """
    controls = _controls(sites)
    if not re.fullmatch(r"[a-z0-9-]+", pin_map.part):
        raise ValueError("Invalid device part")
    if pin_map.family not in ("ULTRASCALE", "ULTRASCALE_PLUS"):
        raise ValueError("Unsupported native family")
    return r'''proc usnative_aux_target {pin type} {
    set nodes [get_nodes -quiet -of_objects [get_site_pins -quiet $pin]]
    set nodes [concat $nodes [get_nodes -quiet -downhill -of_objects $nodes]]
    set pins [get_site_pins -quiet -of_objects $nodes]
    set sites [get_sites -quiet -of_objects $pins]
    set targets [filter $sites "SITE_TYPE == $type"]
    if {[llength $targets] != 1} {error "Ambiguous auxiliary target for $pin: $targets"}
    return [lindex $targets 0]
}
proc usnative_auxiliary_query {output_path} {
    set part [string tolower [get_property PART [current_design]]]
    if {$part ne "@PART@"} {error "Auxiliary map part mismatch"}
    set out [open $output_path w]
    puts $out "USNATIVE_AUX\t1\t@HASH@\t$part\t[version -short]"
    puts $out "control\ttristate\triu\triu_input"
    foreach control {@CONTROLS@} {
        set tri [usnative_aux_target $control/BS_RESET_TRI BITSLICE_TX]
        for {set bit 0} {$bit < 9} {incr bit} {
            if {[usnative_aux_target $control/TRISTATE_ODELAY_OUT$bit BITSLICE_TX] ne $tri} {
                error "Tristate delay target mismatch: $control bit $bit"
            }
        }
        set riu [usnative_aux_target $control/RIU2CLB_VALID RIU_OR]
        set side ""
        for {set bit 0} {$bit < 16} {incr bit} {
            set pin $control/RIU2CLB_RD_DATA$bit
            if {[usnative_aux_target $pin RIU_OR] ne $riu} {error "RIU target mismatch: $pin"}
            set nodes [get_nodes -quiet -of_objects [get_site_pins $pin]]
            set nodes [concat $nodes [get_nodes -quiet -downhill -of_objects $nodes]]
            set hits {}
            foreach target [get_site_pins -quiet -of_objects $nodes] {
                if {[regexp {^(.*)/RIU_RD_DATA_(LOW|UPP)([0-9]+)$} $target all loc which index]
                    && $loc eq $riu && $index == $bit} {lappend hits $which}
            }
            set hits [lsort -unique $hits]
            if {[llength $hits] != 1} {error "Ambiguous RIU input: $pin $hits"}
            if {$side ne "" && $side ne [lindex $hits 0]} {error "RIU bus side mismatch"}
            set side [lindex $hits 0]
        }
        puts $out "$control\t$tri\t$riu\t$side"
    }
    puts $out "END\t@COUNT@"
    close $out
}'''.replace("@PART@", pin_map.part).replace("@HASH@", pin_map.fingerprint).replace(
        "@CONTROLS@", " ".join(sorted(controls))).replace("@COUNT@", str(len(controls)))


def parse_auxiliary_map(pin_map, sites, text, *, vivado_version):
    """Reject stale/incomplete maps and inconsistent nibble/byte associations."""
    controls = _controls(sites)
    lines = text.splitlines()
    header = ["USNATIVE_AUX", "1", pin_map.fingerprint, pin_map.part, vivado_version]
    if len(lines) < 4 or lines[0].split("\t") != header:
        raise ValueError("Auxiliary map identity mismatch")
    if lines[1] != "control\ttristate\triu\triu_input" or lines[-1] != f"END\t{len(controls)}":
        raise ValueError("Incomplete auxiliary map")
    result, tri_used, riu_groups, byte_riu = {}, set(), {}, {}
    for line in lines[2:-1]:
        fields = line.split("\t")
        if len(fields) != 4:
            raise ValueError("Malformed auxiliary row")
        control, tri, riu, side = fields
        if control not in controls or control in result:
            raise ValueError("Unknown or duplicate auxiliary control")
        bank, byte, nibble = controls[control]
        if not re.fullmatch(r"BITSLICE_TX_X\d+Y\d+", tri) or tri in tri_used:
            raise ValueError("Invalid or shared tristate site")
        if not re.fullmatch(r"RIU_OR_X\d+Y\d+", riu) or side != ("LOW" if nibble == "L" else "UPP"):
            raise ValueError("Invalid RIU site or nibble input")
        group = (bank, byte)
        if riu_groups.get(riu, group) != group or byte_riu.get(group, riu) != riu:
            raise ValueError("RIU site must serve exactly one byte")
        riu_groups[riu], byte_riu[group] = group, riu
        tri_used.add(tri)
        result[control] = AuxiliarySites(control, tri, riu, side)
    if set(result) != set(controls):
        raise ValueError("Missing auxiliary controls")
    return result
