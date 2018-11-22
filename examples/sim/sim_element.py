#!/usr/bin/env python3

import lxbuildenv

# This variable defines all the external programs that this module
# relies on.  lxbuildenv reads this variable in order to ensure
# the build will finish without exiting due to missing third-party
# programs.
LX_DEPENDENCIES = ["riscv", "vivado"]

import sys

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from litex.soc.integration.builder import *

from litedram.common import LiteDRAMNativePort
from litedram.frontend.bist import _LiteDRAMBISTGenerator
from litedram.frontend.bist import _LiteDRAMBISTChecker

from litex.soc.cores.clock import *


sim_config = {
    # freqs
    "input_clk_freq": 100e6,
    "sys_clk_freq": 100e6,
    "iodelay_clk_freq": 300e6,
}


_io = [
    ("clk", 0, Pins("X")),
    ("rst", 0, Pins("X")),
]


class Platform(XilinxPlatform):
    def __init__(self):
        XilinxPlatform.__init__(self, "", _io)


class CRG(Module):
    def __init__(self, platform, core_config):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_iodelay = ClockDomain()
        self.clock_domains.cd_sys2x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys8x = ClockDomain(reset_less=True)

        # # #

        self.submodules.pll = pll = S7MMCM()
        self.comb += pll.reset.eq(platform.request("rst"))
        pll.register_clkin(platform.request("clk"), sim_config["input_clk_freq"])
        pll.create_clkout(self.cd_sys, sim_config["sys_clk_freq"])
        pll.create_clkout(self.cd_sys4x, 4*sim_config["sys_clk_freq"])
        pll.create_clkout(self.cd_sys4x_dqs, 4*sim_config["sys_clk_freq"], phase=90)
        pll.create_clkout(self.cd_iodelay, sim_config["iodelay_clk_freq"])
        pll.create_clkout(self.cd_sys2x, 2*sim_config["sys_clk_freq"])
        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_iodelay)

        self.submodules.pll2 = pll2 = S7MMCM()
        self.comb += pll2.reset.eq(ResetSignal("sys"))
        pll2.register_clkin(self.cd_sys.clk, sim_config["input_clk_freq"])
        pll2.create_clkout(self.cd_sys8x, 8*sim_config["sys_clk_freq"])


vectors = [0, 1, 2, 4,
           8, 0, 3, 0xc,
           0, 6, 0x10, 0x20,
           0x40, 0x80, 0x3c, 0]

class SimpleSim(Module):
    def __init__(self, platform):
        crg = CRG(platform, sim_config)
        iodelay_clk_freq = sim_config["iodelay_clk_freq"]

        self.submodules += crg

        dq_sim = Signal(8)
        count = Signal(3)
        index = Signal(4)

        for k, i in enumerate(vectors):
            self.sync.sys8x += [
                If( (count == 0) & (index == k),
                   dq_sim.eq(i)
                )
            ]
        self.sync.sys8x += [
            count.eq(count + 1),
            If(count == 0,
               index.eq(index + 1),
            ).Else(
               dq_sim[:].eq(Cat(dq_sim[1:], 0)),
            )
        ]

        dq_i_delayed = Signal()
        self.specials += \
            Instance("IDELAYE2",
                     p_DELAY_SRC="IDATAIN", p_SIGNAL_PATTERN="DATA",
                     p_CINVCTRL_SEL="FALSE", p_HIGH_PERFORMANCE_MODE="TRUE", p_REFCLK_FREQUENCY=iodelay_clk_freq / 1e6,
                     p_PIPE_SEL="FALSE", p_IDELAY_TYPE="VARIABLE", p_IDELAY_VALUE=0,

                     i_C=ClockSignal("sys"),
                     i_LD=0,
                     i_CE=0,
                     i_LDPIPEEN=0, i_INC=1,

                     i_IDATAIN=dq_sim[0], o_DATAOUT=dq_i_delayed
                     )

        dq_i_data = Signal(8)
        dq_demux_data = Signal(4)
        self.specials += \
            Instance("ISERDESE2",
                     p_DATA_WIDTH=4, p_DATA_RATE="DDR",
                     p_SERDES_MODE="MASTER", p_INTERFACE_TYPE="MEMORY",
                     p_NUM_CE=1, p_IOBDELAY="IFD",

                     i_DDLY=dq_i_delayed,
                     i_CE1=1,
                     i_RST=ResetSignal("sys"),
                     i_CLK=ClockSignal("sys4x_dqs"), i_CLKB=~ClockSignal("sys4x_dqs"),
                     i_OCLK=ClockSignal("sys4x"), i_OCLKB=~ClockSignal("sys4x"), i_CLKDIV=ClockSignal("sys2x"),
                     i_BITSLIP=0,
                     o_Q4=dq_demux_data[0], o_Q3=dq_demux_data[1],
                     o_Q2=dq_demux_data[2], o_Q1=dq_demux_data[3]
                     )
        self.sync.sys2x += [
            dq_i_data[:4].eq(dq_i_data[4:]),
            dq_i_data[4:].eq(dq_demux_data)
        ]
        final_dq = Signal(8)
        self.sync.sys += final_dq.eq(dq_i_data)


def generate_top():
    platform = Platform()
    soc = SimpleSim(platform)
    platform.build(soc, build_dir="./", run=False)

#    builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
#    vns = builder.build()
#    soc.do_exit(vns)


def generate_top_tb():
    f = open("top_tb.v", "w")
    f.write("""
`timescale 1ns/1ps

module top_tb();

reg clk;
initial clk = 1'b1;
always #5 clk = ~clk;

top dut (
    .clk(clk),
    .rst(0)
);

endmodule""")
    f.close()


def run_sim(gui=False):
    os.system("rm -rf xsim.dir")
    if sys.platform == "win32":
        call_cmd = "call "
    else:
        call_cmd = ""
    os.system(call_cmd + "xvlog glbl.v")
    os.system(call_cmd + "xvlog top.v -sv")
    os.system(call_cmd + "xvlog top_tb.v -sv ")
    os.system(call_cmd + "xelab -debug typical top_tb glbl -s top_tb_sim -L unisims_ver -L unimacro_ver -L SIMPRIM_VER -L secureip -L $xsimdir/xil_defaultlib -timescale 1ns/1ps")
    if gui:
        os.system(call_cmd + "xsim top_tb_sim -gui")
    else:
        os.system(call_cmd + "xsim top_tb_sim -runall")


def main():
    generate_top()
    generate_top_tb()
    run_sim(gui="gui" in sys.argv[1:])


if __name__ == "__main__":
    main()
