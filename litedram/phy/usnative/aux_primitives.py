#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""DDR4 4:1 tristate and RIU primitive building blocks.

Use device-queried sites. The caller supplies control buses, reset/VTC handling
and a mutually exclusive RIU selection. These helpers do not perform training.
"""

import re
import math
from migen import Instance


TRISTATE_PORTS = {
    "BIT_CTRL_OUT": ("output", 40), "CNTVALUEOUT": ("output", 9),
    "TRI_OUT": ("output", 1), "BIT_CTRL_IN": ("input", 40),
    "CE": ("input", 1), "CLK": ("input", 1), "CNTVALUEIN": ("input", 9),
    "EN_VTC": ("input", 1), "INC": ("input", 1), "LOAD": ("input", 1),
    "RST": ("input", 1), "RST_DLY": ("input", 1),
}
RIU_PORTS = {
    "RIU_RD_DATA": ("output", 16), "RIU_RD_VALID": ("output", 1),
    "RIU_RD_DATA_LOW": ("input", 16), "RIU_RD_DATA_UPP": ("input", 16),
    "RIU_RD_VALID_LOW": ("input", 1), "RIU_RD_VALID_UPP": ("input", 1),
}


def _family(family):
    if family not in ("ULTRASCALE", "ULTRASCALE_PLUS"):
        raise ValueError("Unsupported native family")


def tristate_parameters(*, family, refclk_mhz):
    _family(family)
    if isinstance(refclk_mhz, bool) or not isinstance(refclk_mhz, (int, float)):
        raise ValueError("Native reference frequency must be numeric")
    if not math.isfinite(refclk_mhz) or refclk_mhz < 0.000001:
        raise ValueError("Native reference frequency must be positive and representable")
    return dict(DATA_WIDTH="8", DELAY_FORMAT='"TIME"', DELAY_TYPE='"FIXED"',
        DELAY_VALUE="0", INIT="1'b1", IS_CLK_INVERTED="1'b0",
        IS_RST_DLY_INVERTED="1'b0", IS_RST_INVERTED="1'b0",
        NATIVE_ODELAY_BYPASS='"FALSE"', OUTPUT_PHASE_90='"TRUE"',
        REFCLK_FREQUENCY=f"{refclk_mhz:.6f}", SIM_DEVICE=f'"{family}"',
        SIM_VERSION="2.0", UPDATE_MODE='"ASYNC"')


def emit_tristate(module_name, site, *, family, refclk_mhz):
    """Emit a located fixed-TIME-delay tristate wrapper with explicit ports."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", module_name):
        raise ValueError("Invalid Verilog module name")
    if not re.fullmatch(r"BITSLICE_TX_X\d+Y\d+", site):
        raise ValueError("Invalid tristate site")
    parameters = tristate_parameters(family=family, refclk_mhz=refclk_mhz)
    declarations = [f"    {direction} wire " + (f"[{width-1}:0] " if width != 1 else "") + name
                    for name, (direction, width) in TRISTATE_PORTS.items()]
    return "\n".join(["`default_nettype none", f"module {module_name} (",
        ",\n".join(declarations), ");",
        f'(* DONT_TOUCH = "TRUE", LOC = "{site}", BEL = "BITSLICE_TX.TRISTATE_TX_BITSLICE" *)',
        "TX_BITSLICE_TRI #(",
        ",\n".join(f"    .{name}({value})" for name, value in parameters.items()),
        ") native_tristate (",
        ",\n".join(f"    .{name}({name})" for name in TRISTATE_PORTS),
        ");", "endmodule", "`default_nettype wire", ""])


def riu_or(site, *, family, **ports):
    """Instantiate the dedicated byte RIU combiner; require every port/width.

    LOW and UPP correspond to device-queried nibble inputs, not list order.
    The caller handles unused halves and RIU transaction arbitration.
    """
    _family(family)
    if not re.fullmatch(r"RIU_OR_X\d+Y\d+", site):
        raise ValueError("Invalid RIU site")
    if set(ports) != set(RIU_PORTS):
        raise ValueError("All RIU ports must be provided exactly once")
    for name, (_, width) in RIU_PORTS.items():
        if len(ports[name]) != width:
            raise ValueError(f"Incorrect width for {name}")
    kwargs = {("i_" if direction == "input" else "o_") + name: ports[name]
              for name, (direction, _) in RIU_PORTS.items()}
    return Instance("RIU_OR", p_SIM_DEVICE=family, p_SIM_VERSION=2.0,
                    attr={("LOC", site), ("DONT_TOUCH", "TRUE")}, **kwargs)
