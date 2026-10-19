#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Native DDR4 control profiles for local or partner-nibble strobes.

External north/south clock forwarding is not supported by this initial profile.
Clocks, RIU, reset and training sequencing are provided by the caller.
"""

import re

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlProfile:
    site: str
    data: bool
    other_nibble: bool


def control_profiles(sites):
    """Derive controls from a validated ``parse_vivado_map`` result.

    All data pins in a control must use one strobe, in the same byte. Output
    commands may share a data control; their RXTX configuration remains the
    caller's responsibility. A command-only control disables receive gating.
    """
    dq = sorted(i for signal, i in sites if signal == "dq")
    strobes = sorted(i for signal, i in sites if signal == "dqs_p")
    if not strobes or dq != list(range(len(dq))) or strobes != list(range(len(strobes))):
        raise ValueError("Contiguous DQ and DQS resources are required")
    if len(dq) not in (4 * len(strobes), 8 * len(strobes)):
        raise ValueError("Only x4/x8 strobe groups are supported")
    group_width = len(dq) // len(strobes)
    groups = {}
    for (signal, index), site in sites.items():
        if signal in ("dqs_n", "clk_n", "reset_n"):
            continue
        data = signal in ("dq", "dm", "dqs_p")
        if not data and signal not in ("a", "ba", "bg", "cas_n", "ras_n", "we_n",
                "cs_n", "cke", "odt", "act_n", "clk_p"):
            raise ValueError("Unsupported signal in native control")
        source = None
        if data:
            lane = index // group_width if signal == "dq" else index
            if signal == "dm":
                if group_width != 8:
                    raise ValueError("DM with x4 strobes requires explicit mapping")
            source = sites.get(("dqs_p", lane))
            if source is None or (site.bank, site.byte) != (source.bank, source.byte):
                raise ValueError("Data control requires a strobe in the same byte")
        groups.setdefault(site.control_site, []).append((site, data, source))
    result = {}
    for location, entries in groups.items():
        data = any(data for _, data, _ in entries)
        sources = {source.control_site for _, _, source in entries if source is not None}
        if len(sources) > 1:
            raise ValueError("Multiple strobes share one native control")
        other = bool(sources and location not in sources)
        result[location] = ControlProfile(location, data, other)
    return result


def control_parameters(profile, *, family):
    if family not in ("ULTRASCALE", "ULTRASCALE_PLUS"):
        raise ValueError("Unsupported native control family")
    if not re.fullmatch(r"BITSLICE_CONTROL_X\d+Y\d+", profile.site):
        raise ValueError("Invalid native control site")
    if type(profile.data) is not bool or type(profile.other_nibble) is not bool:
        raise ValueError("Control flags must be boolean")
    if profile.other_nibble and not profile.data:
        raise ValueError("Command profile cannot borrow a data strobe")
    gate = '"ENABLE"' if profile.data else '"DISABLE"'
    phase = '"SHIFT_90"' if profile.data else '"SHIFT_0"'
    other = '"TRUE"' if profile.other_nibble else '"FALSE"'
    return dict(CTRL_CLK='"EXTERNAL"', DIV_MODE='"DIV4"',
        EN_CLK_TO_EXT_NORTH='"DISABLE"', EN_CLK_TO_EXT_SOUTH='"DISABLE"',
        EN_DYN_ODLY_MODE='"FALSE"', EN_OTHER_NCLK=other, EN_OTHER_PCLK=other,
        IDLY_VT_TRACK='"TRUE"', INV_RXCLK='"FALSE"', ODLY_VT_TRACK='"TRUE"',
        QDLY_VT_TRACK='"TRUE"', READ_IDLE_COUNT="6'h1F", REFCLK_SRC='"PLLCLK"',
        ROUNDING_FACTOR="16", RXGATE_EXTEND='"FALSE"', RX_CLK_PHASE_N=phase,
        RX_CLK_PHASE_P=phase, RX_GATING=gate, SELF_CALIBRATE='"ENABLE"',
        SERIAL_MODE='"FALSE"', SIM_DEVICE=f'"{family}"', SIM_SPEEDUP='"FAST"',
        SIM_VERSION="2.0", TX_GATING=gate)


CONTROL_PORTS = {
    **{name: ("output", 1) for name in ("CLK_TO_EXT_NORTH", "CLK_TO_EXT_SOUTH",
        "DLY_RDY", "NCLK_NIBBLE_OUT", "PCLK_NIBBLE_OUT", "RIU_VALID", "VTC_RDY")},
    "DYN_DCI": ("output", 7), "RIU_RD_DATA": ("output", 16),
    **{f"{direction}_BIT_CTRL_OUT{i}": ("output", 40)
       for direction in ("RX", "TX") for i in range(7)},
    "TX_BIT_CTRL_OUT_TRI": ("output", 40),
    **{name: ("input", 1) for name in ("CLK_FROM_EXT", "EN_VTC", "NCLK_NIBBLE_IN",
        "PCLK_NIBBLE_IN", "PLL_CLK", "REFCLK", "RIU_CLK", "RIU_NIBBLE_SEL",
        "RIU_WR_EN", "RST")},
    **{name: ("input", 4) for name in ("PHY_RDCS0", "PHY_RDCS1", "PHY_RDEN",
        "PHY_WRCS0", "PHY_WRCS1", "TBYTE_IN")},
    "RIU_ADDR": ("input", 6), "RIU_WR_DATA": ("input", 16),
    **{f"{direction}_BIT_CTRL_IN{i}": ("input", 40)
       for direction in ("RX", "TX") for i in range(7)},
    "TX_BIT_CTRL_IN_TRI": ("input", 40),
}


def emit_control(module_name, profile, *, family):
    """Emit an explicit-port located control wrapper for the initial profile."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", module_name):
        raise ValueError("Invalid Verilog module name")
    parameters = control_parameters(profile, family=family)
    declarations = [f"    {direction} wire " + (f"[{width-1}:0] " if width != 1 else "") + name
                    for name, (direction, width) in CONTROL_PORTS.items()]
    return "\n".join(["`default_nettype none", f"module {module_name} (",
        ",\n".join(declarations), ");",
        f'(* DONT_TOUCH = "TRUE", LOC = "{profile.site}", BEL = "BITSLICE_CONTROL.CONTROL" *)',
        "BITSLICE_CONTROL #(",
        ",\n".join(f"    .{name}({value})" for name, value in parameters.items()),
        ") native_control (",
        ",\n".join(f"    .{name}({name})" for name in CONTROL_PORTS),
        ");", "endmodule", "`default_nettype wire", ""])
