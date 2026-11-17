#!/usr/bin/env python3
# Generate a bare NXRPCPHY top (clocking + PHY, DFI and CSR controls as ports) for a vendor-model
# simulation (QuestaSim with the Lattice primitive models).

import sys

from migen import *

from litex.gen import *
from litex.gen.fhdl.verilog import convert
from litex.soc.interconnect.csr import CSR, CSRStorage, CSRStatus

from litedram.phy.rpc.nxphy import NXRPCPHY

class Top(LiteXModule):
    def __init__(self, sys_clk_freq=50e6):
        self.clk4x    = Signal()
        self.clk_init = Signal()
        self.rst      = Signal()
        self.ios      = {self.clk4x, self.clk_init, self.rst}

        self.cd_init    = ClockDomain()
        self.cd_sys     = ClockDomain()
        self.cd_sys4x   = ClockDomain()
        self.cd_sys4x_i = ClockDomain()

        pads = Record([("clk_p", 1), ("cs_n", 2), ("stb", 2), ("dqs_p", 2), ("db", 16)], name="rpc")
        self.ios |= set(pads.flatten())

        self.phy = phy = NXRPCPHY(pads=pads, sys_clk_freq=sys_clk_freq)

        self.comb += [
            self.cd_sys4x_i.clk.eq(self.clk4x),
            self.cd_init.clk.eq(self.clk_init),
        ]
        self.specials += [
            Instance("ECLKSYNC",
                p_STOP_EN = "ENABLE",
                i_ECLKIN  = self.cd_sys4x_i.clk,
                i_STOP    = phy.init.stop,
                o_ECLKOUT = self.cd_sys4x.clk),
            Instance("ECLKDIV",
                p_ECLK_DIV = "4",
                i_SLIP     = 0,
                i_ECLKIN   = self.cd_sys4x.clk,
                i_DIVRST   = phy.init.reset,
                o_DIVOUT   = self.cd_sys.clk),
            Instance("arst_sync", i_clk=self.cd_init.clk, i_arst=self.rst, o_rst=self.cd_init.rst),
            Instance("arst_sync", i_clk=self.cd_sys.clk,  i_arst=self.rst | phy.init.reset, o_rst=self.cd_sys.rst),
        ]

        # DFI as ports.
        self.ios |= set(phy.dfi.flatten())

        # CSRs as ports.
        for name, csr in sorted(vars(phy).items()):
            if not name.startswith("_"):
                continue
            if isinstance(csr, CSRStorage):
                port = Signal(len(csr.storage), name="csr" + name, reset=csr.storage.reset.value)
                self.comb += csr.storage.eq(port)
            elif isinstance(csr, CSRStatus):
                port = Signal(len(csr.status), name="csr" + name)
                self.comb += port.eq(csr.status)
            elif isinstance(csr, CSR):
                port = Signal(name="csr" + name)
                self.comb += csr.wr_stb.eq(port)
            else:
                continue
            self.ios.add(port)

        # Debug.
        dbg = {
            "dbg_dqs_re"    : phy.dqs_re,
            "dbg_datavalid" : phy.datavalid,
            "dbg_pause"     : phy.init.pause,
            "dbg_stop"      : phy.init.stop,
            "dbg_dqsr90"    : Cat(*phy.dqsr90),
            "dbg_dqsw"      : Cat(*phy.dqsw),
            "dbg_dqsw270"   : Cat(*phy.dqsw270),
        }
        for name, sig in dbg.items():
            port = Signal(len(sig), name=name)
            self.comb += port.eq(sig)
            self.ios.add(port)

if __name__ == "__main__":
    top = Top()
    convert(top, ios=top.ios, name="top").write(sys.argv[1] if len(sys.argv) > 1 else "top.v")
