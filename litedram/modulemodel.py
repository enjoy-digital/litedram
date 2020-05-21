import math

from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# RAM module model ---------------------------------------------------------------------------------

class SDRAMModuleModel(Module):

    def __init__(self, platform):
        vname = "ddr3"

        from os import path
        vdir = path.abspath(path.join(path.dirname(__file__), "../thirdparty/micron"))
        platform.verilog_include_paths.append(vdir)
        platform.add_source(path.join(vdir, f"{vname}.v"))

        DM_BITS     =  2
        ADDR_BITS   = 13
        DQ_BITS     = 16
        DQS_BITS    =  2
        BA_BITS     =  3

        self.reset_n = Signal()
        self.clk_p   = Signal()
        self.clk_n   = Signal()
        self.a       = Signal(ADDR_BITS)
        self.ba      = Signal(BA_BITS)
        self.ras_n   = Signal()
        self.cas_n   = Signal()
        self.we_n    = Signal()
        self.cs_n    = Signal()
        self.dm      = Signal(DM_BITS)
        self._dm     = Signal(DM_BITS)
        self.dq      = Signal(DQ_BITS)
        self.dqs     = Signal(DQS_BITS)
        self._dqs_n  = Signal(DQS_BITS)
        self.cke     = Signal()
        self.odt     = Signal()
        self.tdqs_n  = Signal(DQS_BITS)

        self.comb += self._dm.eq(self.dm)
        self.comb += self._dqs_n.eq(~self.dqs)

        self.specials.module = Instance(vname,
            i_rst_n    = self.reset_n,
            i_ck       = self.clk_p,
            i_ck_n     = self.clk_n,
            i_cke      = self.cke,
            i_cs_n     = self.cs_n,
            i_ras_n    = self.ras_n,
            i_cas_n    = self.cas_n,
            i_we_n     = self.we_n,
            io_dm_tdqs = self._dm,
            i_ba       = self.ba,
            i_addr     = self.a,
            io_dq      = self.dq,
            io_dqs     = self.dqs,
            io_dqs_n   = self._dqs_n,
            i_odt      = self.odt,
            o_tdqs_n   = self.tdqs_n
        )
