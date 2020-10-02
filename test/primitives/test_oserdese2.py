#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import sys

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from litex.soc.integration.builder import *
from litex.soc.cores.clock import *


class Platform(XilinxPlatform):
    def __init__(self):
        XilinxPlatform.__init__(self, "", [("clk", 0, Pins("X"))])


class OSERDESE2Sim(Module):
    def __init__(self, platform):

        # Clocking
        self.clock_domains.cd_sys   = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain()
        self.submodules.pll = pll = S7PLL(speedgrade=-1)
        pll.register_clkin(platform.request("clk"), 100e6)
        pll.create_clkout(self.cd_sys,   100e6)
        pll.create_clkout(self.cd_sys4x, 400e6)

        # OSERDESE2
        i_d  = Signal(8)
        i_t1 = Signal()
        o_tq = Signal()
        o_oq = Signal()
        self.specials += Instance("OSERDESE2",
            p_SERDES_MODE    = "MASTER",
            p_DATA_WIDTH     = 8,
            p_TRISTATE_WIDTH = 1,
            p_DATA_RATE_OQ   = "DDR",
            p_DATA_RATE_TQ   = "BUF",
            i_RST    = ResetSignal(),
            i_CLK    = ClockSignal("sys4x"),
            i_CLKDIV = ClockSignal(),
            **{f"i_D{n+1}": i_d[n] for n in range(8)},
            i_TCE    = 1,
            i_T1     = ~i_t1,
            o_TQ     = o_tq,
            i_OCE    = 1,
            o_OQ     = o_oq,
        )

        # Stimulation
        counter = Signal(16)
        self.sync += [
            counter.eq(counter + 1),
            If(counter == (16 - 1),
                counter.eq(0)
            ),
            If(counter == 0,
                i_d.eq(0xff),
                i_t1.eq(0b0),
            ).Else(
                i_d.eq(0x00),
                i_t1.eq(0b1),
            )
        ]

def generate_top():
    platform = Platform()
    sim = OSERDESE2Sim(platform)
    platform.build(sim, build_dir="./", run=False)


def generate_top_tb():
    f = open("top_tb.v", "w")
    f.write("""
`timescale 1ns/1ps

module top_tb();

reg clk;
initial clk = 1'b1;
always #5 clk = ~clk;

top dut (
    .clk(clk)
);

endmodule""")
    f.close()

def run_sim(gui=False):
    os.system("xvlog glbl.v")
    os.system("xvlog top.v -sv")
    os.system("xvlog top_tb.v -sv")
    os.system("xelab -debug typical top_tb glbl -s top_tb_sim -L unisims_ver -L unimacro_ver -L SIMPRIM_VER -L secureip -L $xsimdir/xil_defaultlib -timescale 1ns/1ps")
    if gui:
        os.system("xsim top_tb_sim -gui")
    else:
        os.system("xsim top_tb_sim -runall")

def main():
    generate_top()
    generate_top_tb()
    run_sim(gui="gui" in sys.argv[1:])


if __name__ == "__main__":
    main()
