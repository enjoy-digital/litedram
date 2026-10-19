#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Generate an eight-bit native RXTX serializer with variable TIME delays.

This is a primitive building block, not a complete DDR PHY. The caller supplies
the native control buses, clocks, FIFO sequencing, reset/VTC handling and I/O
buffers. Device timing and complete topology must be checked during the build.
"""

import re
import math


# Public RXTX_BITSLICE interface. Outputs remain explicit, including diagnostics.
RXTX_PORTS = {
    "FIFO_EMPTY": ("output", 1), "FIFO_WRCLK_OUT": ("output", 1),
    "O": ("output", 1), "Q": ("output", 8),
    "RX_BIT_CTRL_OUT": ("output", 40), "RX_CNTVALUEOUT": ("output", 9),
    "TX_BIT_CTRL_OUT": ("output", 40), "TX_CNTVALUEOUT": ("output", 9),
    "T_OUT": ("output", 1),
    "D": ("input", 8), "DATAIN": ("input", 1),
    "FIFO_RD_CLK": ("input", 1), "FIFO_RD_EN": ("input", 1),
    "RX_BIT_CTRL_IN": ("input", 40), "RX_CE": ("input", 1),
    "RX_CLK": ("input", 1), "RX_CNTVALUEIN": ("input", 9),
    "RX_EN_VTC": ("input", 1), "RX_INC": ("input", 1),
    "RX_LOAD": ("input", 1), "RX_RST": ("input", 1),
    "RX_RST_DLY": ("input", 1), "T": ("input", 1), "TBYTE_IN": ("input", 1),
    "TX_BIT_CTRL_IN": ("input", 40), "TX_CE": ("input", 1),
    "TX_CLK": ("input", 1), "TX_CNTVALUEIN": ("input", 9),
    "TX_EN_VTC": ("input", 1), "TX_INC": ("input", 1),
    "TX_LOAD": ("input", 1), "TX_RST": ("input", 1), "TX_RST_DLY": ("input", 1),
}


def rxtx_parameters(site, *, role, family, refclk_mhz, pre_emphasis=False):
    """Return Verilog parameter literals for the initial DDR4 4:1 profile.

    ``data`` includes DQ and DM. DQS uses ``strobe``; address/command use
    ``command``; differential CK uses ``clock``. Frequency is the native delay
    reference attribute in MHz, not the CPU clock. No speed-rating waiver is
    implied by accepting a positive frequency here.
    """
    if family not in ("ULTRASCALE", "ULTRASCALE_PLUS"):
        raise ValueError("Unsupported native serializer family")
    if role not in ("data", "strobe", "command", "clock"):
        raise ValueError("Unsupported native serializer role")
    if isinstance(refclk_mhz, bool) or not isinstance(refclk_mhz, (int, float)):
        raise ValueError("Native reference frequency must be numeric")
    if not math.isfinite(refclk_mhz) or refclk_mhz <= 0:
        raise ValueError("Native reference frequency must be finite and positive")
    if not isinstance(pre_emphasis, bool):
        raise ValueError("Pre-emphasis must be boolean")
    if not re.fullmatch(r"BITSLICE_RX_TX_X\d+Y\d+", site.native_site):
        raise ValueError("Invalid native serializer site")
    if role in ("strobe", "clock") and not site.master:
        raise ValueError("Differential output must use its positive site")
    if role == "strobe" and (site.position not in (0, 6)
            or not re.search(r"_(?:DBC|QBC)(?:_|$)", site.function)):
        raise ValueError("DQS requires a native strobe site")
    clock_capable = role == "strobe" or (role != "data" and site.position in (0, 6))
    frequency = f"{refclk_mhz:.6f}"
    parameters = dict(
        ENABLE_PRE_EMPHASIS='"TRUE"' if pre_emphasis else '"FALSE"',
        FIFO_SYNC_MODE='"FALSE"', INIT="1'b1",
        IS_RX_CLK_INVERTED="1'b0", IS_RX_RST_DLY_INVERTED="1'b0",
        IS_RX_RST_INVERTED="1'b0", IS_TX_CLK_INVERTED="1'b0",
        IS_TX_RST_DLY_INVERTED="1'b0", IS_TX_RST_INVERTED="1'b0",
        LOOPBACK='"FALSE"', NATIVE_ODELAY_BYPASS='"FALSE"',
        RX_DATA_TYPE='"DATA_AND_CLOCK"' if clock_capable else '"DATA"',
        RX_DATA_WIDTH="8", RX_DELAY_FORMAT='"TIME"', RX_DELAY_TYPE='"VARIABLE"',
        RX_DELAY_VALUE="0", RX_REFCLK_FREQUENCY=frequency, RX_UPDATE_MODE='"ASYNC"',
        SIM_DEVICE=f'"{family}"', SIM_VERSION="2.0",
        TBYTE_CTL='"T"' if role == "data" else '"TBYTE_IN"',
        TX_DATA_WIDTH="8", TX_DELAY_FORMAT='"TIME"', TX_DELAY_TYPE='"VARIABLE"',
        TX_DELAY_VALUE="0", TX_OUTPUT_PHASE_90='"FALSE"' if role == "data" else '"TRUE"',
        TX_REFCLK_FREQUENCY=frequency, TX_UPDATE_MODE='"ASYNC"',
    )
    return parameters


def emit_rxtx(module_name, site, **configuration):
    """Emit a located RXTX module; no reference netlist or board import is used."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", module_name):
        raise ValueError("Invalid Verilog module name")
    parameters = rxtx_parameters(site, **configuration)
    declarations = []
    for name, (direction, width) in RXTX_PORTS.items():
        vector = f"[{width - 1}:0] " if width != 1 else ""
        declarations.append(f"    {direction} wire {vector}{name}")
    lines = ["`default_nettype none", f"module {module_name} (",
             ",\n".join(declarations), ");",
             f'(* DONT_TOUCH = "TRUE", LOC = "{site.native_site}", '
             'BEL = "BITSLICE_RX_TX.RXTX_BITSLICE" *)', "RXTX_BITSLICE #(",
             ",\n".join(f"    .{name}({value})" for name, value in parameters.items()),
             ") native_slice (",
             ",\n".join(f"    .{name}({name})" for name in RXTX_PORTS),
             ");", "endmodule", "`default_nettype wire", ""]
    return "\n".join(lines)
