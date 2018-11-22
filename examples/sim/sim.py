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


_io = [
    ("clk", 0, Pins("X")),
    ("rst", 0, Pins("X")),
]


class Platform(XilinxPlatform):
    def __init__(self):
        XilinxPlatform.__init__(self, "", _io)


class LiteDRAMCoreSim(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()

        # sdram parameters
        sdram_aw = 24
        sdram_dw = 128

        # sdram bist
        sdram_generator_port = LiteDRAMNativePort("both", sdram_aw, sdram_dw, id=0)
        self.submodules.sdram_generator = _LiteDRAMBISTGenerator(sdram_generator_port)

        sdram_checker_port = LiteDRAMNativePort("both", sdram_aw, sdram_dw, id=1)
        self.submodules.sdram_checker = _LiteDRAMBISTChecker(sdram_checker_port)

        # micron model
        ddram_a = Signal(14)
        ddram_ba = Signal(3)
        ddram_ras_n = Signal()
        ddram_cas_n = Signal()
        ddram_we_n = Signal()
        ddram_cs_n = Signal()
        ddram_dm = Signal(2)
        ddram_dq = Signal(16)
        ddram_dqs_p = Signal(2)
        ddram_dqs_n = Signal(2)
        ddram_clk_p = Signal()
        ddram_clk_n = Signal()
        ddram_cke = Signal()
        ddram_odt = Signal()
        ddram_reset_n = Signal()
        self.specials += Instance("ddr3",
            i_rst_n=ddram_reset_n,
            i_ck=ddram_clk_p,
            i_ck_n=ddram_clk_n,
            i_cke=ddram_cke,
            i_cs_n=ddram_cs_n,
            i_ras_n=ddram_ras_n,
            i_cas_n=ddram_cas_n,
            i_we_n=ddram_we_n,
            io_dm_tdqs=ddram_dm,
            i_ba=ddram_ba,
            i_addr=ddram_a,
            io_dq=ddram_dq,
            io_dqs=ddram_dqs_p,
            io_dqs_n=ddram_dqs_n,
            #o_tdqs_n=,
            i_odt=ddram_odt
        )

        # LiteDRAM standalone core instance
        init_done = Signal()
        init_error = Signal()
        self.specials += Instance("litedram_core",
            # clk / reset input
            i_clk=platform.request("clk"),
            i_rst=platform.request("rst"),

            # dram pins
            o_ddram_a=ddram_a,
            o_ddram_ba=ddram_ba,
            o_ddram_ras_n=ddram_ras_n,
            o_ddram_cas_n=ddram_cas_n,
            o_ddram_we_n=ddram_we_n,
            o_ddram_cs_n=ddram_cs_n,
            o_ddram_dm=ddram_dm,
            io_ddram_dq=ddram_dq,
            o_ddram_dqs_p=ddram_dqs_p,
            o_ddram_dqs_n=ddram_dqs_n,
            o_ddram_clk_p=ddram_clk_p,
            o_ddram_clk_n=ddram_clk_n,
            o_ddram_cke=ddram_cke,
            o_ddram_odt=ddram_odt,
            o_ddram_reset_n=ddram_reset_n,

            # dram init
            o_init_done=init_done,
            o_init_error=init_error,

            # user clk /  reset
            o_user_clk=self.cd_sys.clk,
            o_user_rst=self.cd_sys.rst,

            # user port 0
            #  cmd
            i_user_port0_cmd_valid=sdram_generator_port.cmd.valid,
            o_user_port0_cmd_ready=sdram_generator_port.cmd.ready,
            i_user_port0_cmd_we=sdram_generator_port.cmd.we,
            i_user_port0_cmd_addr=sdram_generator_port.cmd.addr,
            #  wdata
            i_user_port0_wdata_valid=sdram_generator_port.wdata.valid,
            o_user_port0_wdata_ready=sdram_generator_port.wdata.ready,
            i_user_port0_wdata_we=sdram_generator_port.wdata.we,
            i_user_port0_wdata_data=sdram_generator_port.wdata.data,
            #  rdata
            o_user_port0_rdata_valid=sdram_generator_port.rdata.valid,
            i_user_port0_rdata_ready=sdram_generator_port.rdata.ready,
            o_user_port0_rdata_data=sdram_generator_port.rdata.data,
            # user port 1
            #  cmd
            i_user_port1_cmd_valid=sdram_checker_port.cmd.valid,
            o_user_port1_cmd_ready=sdram_checker_port.cmd.ready,
            i_user_port1_cmd_we=sdram_checker_port.cmd.we,
            i_user_port1_cmd_addr=sdram_checker_port.cmd.addr,
            #  wdata
            i_user_port1_wdata_valid=sdram_checker_port.wdata.valid,
            o_user_port1_wdata_ready=sdram_checker_port.wdata.ready,
            i_user_port1_wdata_we=sdram_checker_port.wdata.we,
            i_user_port1_wdata_data=sdram_checker_port.wdata.data,
            #  rdata
            o_user_port1_rdata_valid=sdram_checker_port.rdata.valid,
            i_user_port1_rdata_ready=sdram_checker_port.rdata.ready,
            o_user_port1_rdata_data=sdram_checker_port.rdata.data
        )

        # test
        self.comb += [
            self.sdram_generator.base.eq(0x00000000),
            self.sdram_generator.length.eq(0x00000100),
            self.sdram_generator.random.eq(1),

            self.sdram_checker.base.eq(0x00000000),
            self.sdram_checker.length.eq(0x00000100),
            self.sdram_checker.random.eq(1),
        ]

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(init_done,
                NextState("GENERATOR_START")
            )
        )
        fsm.act("GENERATOR_START",
            self.sdram_generator.start.eq(1),
            NextState("GENERATOR_WAIT")

        )
        fsm.act("GENERATOR_WAIT",
            If(self.sdram_generator.done,
                NextState("CHECKER_START")
            )
        )
        fsm.act("CHECKER_START",
            self.sdram_checker.start.eq(1),
            NextState("CHECKER_WAIT")
        )
        fsm.act("CHECKER_WAIT",
            If(self.sdram_checker.done,
                NextState("DONE")
            )
        )
        fsm.act("DONE")


def generate_core():
    os.system("cd .. && python3 litedram_gen.py sim/sim_config.py")

def generate_top():
    platform = Platform()
    soc = LiteDRAMCoreSim(platform)
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


def copy_core():
    os.system("cp ../build/gateware/litedram_core.v ./")
    os.system("cp ../build/gateware/litedram_core.init ./")


def run_sim(gui=False):
    os.system("rm -rf xsim.dir")
    if sys.platform == "win32":
        call_cmd = "call "
    else:
        call_cmd = ""
    os.system(call_cmd + "xvlog glbl.v")
    os.system(call_cmd + "xvlog micron/2048Mb_ddr3_parameters.vh -sv")
    os.system(call_cmd + "xvlog micron/ddr3.v -sv")
    os.system(call_cmd + "xvlog litedram_core.v -sv")
    os.system(call_cmd + "xvlog top.v -sv")
    os.system(call_cmd + "xvlog top_tb.v -sv ")
    os.system(call_cmd + "xvlog  deps/litex/litex/soc/cores/cpu/vexriscv/verilog/VexRiscv.v  -sv ")
    os.system(call_cmd + "xelab -debug typical top_tb glbl -s top_tb_sim -L unisims_ver -L unimacro_ver -L SIMPRIM_VER -L secureip -L $xsimdir/xil_defaultlib -timescale 1ns/1ps")
    if gui:
        os.system(call_cmd + "xsim top_tb_sim -gui")
    else:
        os.system(call_cmd + "xsim top_tb_sim -runall")


def main():
    generate_core()
    generate_top()
    generate_top_tb()
    copy_core()
    run_sim(gui="gui" in sys.argv[1:])


if __name__ == "__main__":
    main()
