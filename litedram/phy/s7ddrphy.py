# This file is Copyright (c) 2015-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# License: BSD

# 1:4, 1:2 frequency-ratio DDR2/DDR3 PHY for Xilinx's Series7
# DDR2: 400, 533, 667, 800 and 1066 MT/s
# DDR3: 800, 1066, 1333 and 1600 MT/s

import math

from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# Xilinx Series7 DDR2/DDR3 PHY ---------------------------------------------------------------------

class S7DDRPHY(Module, AutoCSR):
    def __init__(self, pads, with_odelay,
        memtype          = "DDR3",
        nphases          = 4,
        sys_clk_freq     = 100e6,
        iodelay_clk_freq = 200e6,
        cmd_latency      = 0,
        interface_type   = "NETWORKING"):
        assert not (memtype == "DDR3" and nphases == 2)
        assert interface_type in ["NETWORKING", "MEMORY"]
        assert not (interface_type == "MEMORY" and nphases == 2)
        phytype     = self.__class__.__name__
        pads        = PHYPadsCombiner(pads)
        tck         = 2/(2*nphases*sys_clk_freq)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = nphases
        assert databits%8 == 0

        # Parameters -------------------------------------------------------------------------------
        iodelay_tap_average = {
            200e6: 78e-12,
            300e6: 52e-12,
            400e6: 39e-12, # Only valid for -3 and -2/2E speed grades
        }
        half_sys8x_taps = math.floor(tck/(4*iodelay_tap_average[iodelay_clk_freq]))

        cl, cwl         = get_cl_cw(memtype, tck)
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl             = cwl + cmd_latency
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        # Registers --------------------------------------------------------------------------------
        self._dly_sel         = CSRStorage(databits//8)
        self._half_sys8x_taps = CSRStorage(5, reset=half_sys8x_taps)

        self._wlevel_en     = CSRStorage()
        self._wlevel_strobe = CSR()

        self._cdly_rst = CSR()
        self._cdly_inc = CSR()

        self._dly_sel = CSRStorage(databits//8)

        self._rdly_dq_rst         = CSR()
        self._rdly_dq_inc         = CSR()
        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        if with_odelay:
            self._wdly_dq_rst   = CSR()
            self._wdly_dq_inc   = CSR()
            self._wdly_dqs_rst  = CSR()
            self._wdly_dqs_inc  = CSR()

        # PHY settings -----------------------------------------------------------------------------
        rdcmdphase, rdphase = get_sys_phases(nphases, cl_sys_latency, cl)
        wrcmdphase, wrphase = get_sys_phases(nphases, cwl_sys_latency, cwl)
        iserdese2_latency  = {
            "NETWORKING": 2,
            "MEMORY":     1,
        }
        self.settings = PhySettings(
            phytype       = phytype,
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = 2*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = rdphase,
            wrphase       = wrphase,
            rdcmdphase    = rdcmdphase,
            wrcmdphase    = wrcmdphase,
            cl            = cl,
            cwl           = cwl - cmd_latency,
            read_latency  = 2 + cl_sys_latency + iserdese2_latency[interface_type] + 2,
            write_latency = cwl_sys_latency,
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, 4)

        # # #

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)

            # Clock --------------------------------------------------------------------------------
            ddr_clk = "sys2x" if nphases == 2 else "sys4x"
            for i in range(len(pads.clk_p)):
                sd_clk_se_nodelay = Signal()
                sd_clk_se_delayed = Signal()
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = ResetSignal(),
                    i_CLK    = ClockSignal(ddr_clk),
                    i_CLKDIV = ClockSignal(),
                    i_D1     = 0,
                    i_D2     = 1,
                    i_D3     = 0,
                    i_D4     = 1,
                    i_D5     = 0,
                    i_D6     = 1,
                    i_D7     = 0,
                    i_D8     = 1,
                    o_OQ     = sd_clk_se_nodelay,
                    i_OCE    = 1,
                )
                if with_odelay:
                   self.specials += Instance("ODELAYE2",
                        p_SIGNAL_PATTERN        = "DATA",
                        p_DELAY_SRC             = "ODATAIN",
                        p_CINVCTRL_SEL          = "FALSE",
                        p_HIGH_PERFORMANCE_MODE = "TRUE",
                        p_PIPE_SEL              = "FALSE",
                        p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                        p_ODELAY_TYPE           = "VARIABLE",
                        p_ODELAY_VALUE          = 0,
                        i_C        = ClockSignal(),
                        i_LD       = self._cdly_rst.re,
                        i_LDPIPEEN = 0,
                        i_CE       = self._cdly_inc.re,
                        i_INC      = 1,
                        o_ODATAIN  = sd_clk_se_nodelay,
                        o_DATAOUT  = sd_clk_se_delayed,
                    )
                self.specials += Instance("OBUFDS",
                    i_I  = sd_clk_se_delayed if with_odelay else sd_clk_se_nodelay,
                    o_O  = pads.clk_p[i],
                    o_OB = pads.clk_n[i]
                )

            # Addresses and Commands -------------------------------------------------------------------
            for i in range(addressbits):
                address = Signal()
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = ResetSignal(),
                    i_CLK    = ClockSignal(ddr_clk),
                    i_CLKDIV = ClockSignal(),
                    i_D1     = dfi.phases[0].address[i],
                    i_D2     = dfi.phases[0].address[i],
                    i_D3     = dfi.phases[1].address[i],
                    i_D4     = dfi.phases[1].address[i],
                    i_D5     = dfi.phases[2].address[i],
                    i_D6     = dfi.phases[2].address[i],
                    i_D7     = dfi.phases[3].address[i],
                    i_D8     = dfi.phases[3].address[i],
                    i_OCE    = 1,
                    o_OQ     = address if with_odelay else pads.a[i],
                )
                if with_odelay:
                    self.specials += Instance("ODELAYE2",
                        p_SIGNAL_PATTERN        = "DATA",
                        p_DELAY_SRC             = "ODATAIN",
                        p_CINVCTRL_SEL          = "FALSE",
                        p_HIGH_PERFORMANCE_MODE = "TRUE",
                        p_PIPE_SEL              = "FALSE",
                        p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                        p_ODELAY_TYPE           = "VARIABLE",
                        p_ODELAY_VALUE          = 0,
                        i_C        = ClockSignal(),
                        i_LD       = self._cdly_rst.re,
                        i_LDPIPEEN = 0,
                        i_CE       = self._cdly_inc.re,
                        i_INC      = 1,
                        o_ODATAIN  = address,
                        o_DATAOUT  = pads.a[i],
                    )
            for i in range(bankbits):
                bank = Signal()
                self.specials += Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = ResetSignal(),
                    i_CLK    = ClockSignal(ddr_clk),
                    i_CLKDIV = ClockSignal(),
                    i_D1     = dfi.phases[0].bank[i],
                    i_D2     = dfi.phases[0].bank[i],
                    i_D3     = dfi.phases[1].bank[i],
                    i_D4     = dfi.phases[1].bank[i],
                    i_D5     = dfi.phases[2].bank[i],
                    i_D6     = dfi.phases[2].bank[i],
                    i_D7     = dfi.phases[3].bank[i],
                    i_D8     = dfi.phases[3].bank[i],
                    i_OCE    = 1,
                    o_OQ     = bank if with_odelay else pads.ba[i],
                )
                if with_odelay:
                    self.specials += Instance("ODELAYE2",
                        p_SIGNAL_PATTERN        = "DATA",
                        p_DELAY_SRC             = "ODATAIN",
                        p_CINVCTRL_SEL          = "FALSE",
                        p_HIGH_PERFORMANCE_MODE = "TRUE",
                        p_PIPE_SEL              = "FALSE",
                        p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                        p_ODELAY_TYPE           = "VARIABLE",
                        p_ODELAY_VALUE          = 0,
                        i_C        = ClockSignal(),
                        i_LD       = self._cdly_rst.re,
                        i_LDPIPEEN = 0,
                        i_CE       = self._cdly_inc.re,
                        i_INC      = 1,
                        o_ODATAIN  = bank,
                        o_DATAOUT  = pads.ba[i],
                    )
            controls = ["ras_n", "cas_n", "we_n", "cke", "odt"]
            if hasattr(pads, "reset_n"):
                controls.append("reset_n")
            if hasattr(pads, "cs_n"):
                controls.append("cs_n")
            for name in controls:
                for i in range(len(getattr(pads, name))):
                    cmd = Signal()
                    self.specials += Instance("OSERDESE2",
                        p_SERDES_MODE    = "MASTER",
                        p_DATA_WIDTH     = 2*nphases,
                        p_TRISTATE_WIDTH = 1,
                        p_DATA_RATE_OQ   = "DDR",
                        p_DATA_RATE_TQ   = "BUF",
                        i_RST    = ResetSignal(),
                        i_CLK    = ClockSignal(ddr_clk),
                        i_CLKDIV = ClockSignal(),
                        i_D1     = getattr(dfi.phases[0], name)[i],
                        i_D2     = getattr(dfi.phases[0], name)[i],
                        i_D3     = getattr(dfi.phases[1], name)[i],
                        i_D4     = getattr(dfi.phases[1], name)[i],
                        i_D5     = getattr(dfi.phases[2], name)[i],
                        i_D6     = getattr(dfi.phases[2], name)[i],
                        i_D7     = getattr(dfi.phases[3], name)[i],
                        i_D8     = getattr(dfi.phases[3], name)[i],
                        i_OCE    = 1,
                        o_OQ     = cmd if with_odelay else getattr(pads, name)[i],
                    )
                    if with_odelay:
                        self.specials += Instance("ODELAYE2",
                            p_SIGNAL_PATTERN        = "DATA",
                            p_DELAY_SRC             = "ODATAIN",
                            p_CINVCTRL_SEL          = "FALSE",
                            p_HIGH_PERFORMANCE_MODE = "TRUE",
                            p_PIPE_SEL              = "FALSE",
                            p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                            p_ODELAY_TYPE           = "VARIABLE",
                            p_ODELAY_VALUE          = 0,
                            i_C        = ClockSignal(),
                            i_LD       = self._cdly_rst.re,
                            i_LDPIPEEN = 0,
                            i_CE       = self._cdly_inc.re,
                            i_INC      = 1,
                            o_ODATAIN  = cmd,
                            o_DATAOUT  = getattr(pads, name)[i],
                        )

        # DQS and DM -------------------------------------------------------------------------------
        dqs_oe         = Signal()
        dqs_oe_delayed = Signal() # Tristate control is asynchronous, needs to be delayed.
        dqs_pattern    = DQSPattern(
            wlevel_en     = self._wlevel_en.storage,
            wlevel_strobe = self._wlevel_strobe.re,
            register      = not with_odelay)
        self.submodules += dqs_pattern
        self.sync += dqs_oe_delayed.eq(dqs_pattern.preamble | dqs_oe | dqs_pattern.postamble)
        for i in range(databits//8):
            dm_o_nodelay = Signal()
            self.specials += Instance("OSERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_DATA_WIDTH     = 2*nphases,
                p_TRISTATE_WIDTH = 1,
                p_DATA_RATE_OQ   = "DDR",
                p_DATA_RATE_TQ   = "BUF",
                i_RST    = ResetSignal(),
                i_CLK    = ClockSignal(ddr_clk),
                i_CLKDIV = ClockSignal(),
                i_D1     = dfi.phases[0].wrdata_mask[i],
                i_D2     = dfi.phases[0].wrdata_mask[databits//8+i],
                i_D3     = dfi.phases[1].wrdata_mask[i],
                i_D4     = dfi.phases[1].wrdata_mask[databits//8+i],
                i_D5     = dfi.phases[2].wrdata_mask[i],
                i_D6     = dfi.phases[2].wrdata_mask[databits//8+i],
                i_D7     = dfi.phases[3].wrdata_mask[i],
                i_D8     = dfi.phases[3].wrdata_mask[databits//8+i],
                i_OCE    = 1,
                o_OQ     = dm_o_nodelay if with_odelay else pads.dm[i],
            )
            if with_odelay:
                self.specials += Instance("ODELAYE2",
                    p_SIGNAL_PATTERN        = "DATA",
                    p_DELAY_SRC             = "ODATAIN",
                    p_CINVCTRL_SEL          = "FALSE",
                    p_HIGH_PERFORMANCE_MODE = "TRUE",
                    p_PIPE_SEL              = "FALSE",
                    p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                    p_ODELAY_TYPE           = "VARIABLE",
                    p_ODELAY_VALUE          = 0,
                    i_C        = ClockSignal(),
                    i_LD       = self._dly_sel.storage[i] & self._wdly_dq_rst.re,
                    i_LDPIPEEN = 0,
                    i_CE       = self._dly_sel.storage[i] & self._wdly_dq_inc.re,
                    i_INC      = 1,
                    o_ODATAIN  = dm_o_nodelay,
                    o_DATAOUT  = pads.dm[i],
                )

        dqs_i         = Signal(databits//8)
        dqs_i_delayed = Signal(databits//8)
        for i in range(databits//8):
            dqs_o_no_delay = Signal()
            dqs_o_delayed  = Signal()
            dqs_t          = Signal()
            self.specials += Instance("OSERDESE2",
                p_SERDES_MODE    = "MASTER",
                p_DATA_WIDTH     = 2*nphases,
                p_TRISTATE_WIDTH = 1,
                p_DATA_RATE_OQ   = "DDR",
                p_DATA_RATE_TQ   = "BUF",
                i_RST    = ResetSignal(),
                i_CLK    = ClockSignal(ddr_clk) if with_odelay else ClockSignal(ddr_clk+"_dqs"),
                i_CLKDIV = ClockSignal(),
                i_D1     = dqs_pattern.o[0],
                i_D2     = dqs_pattern.o[1],
                i_D3     = dqs_pattern.o[2],
                i_D4     = dqs_pattern.o[3],
                i_D5     = dqs_pattern.o[4],
                i_D6     = dqs_pattern.o[5],
                i_D7     = dqs_pattern.o[6],
                i_D8     = dqs_pattern.o[7],
                i_OCE    = 1,
                o_OFB    = dqs_o_no_delay if with_odelay else Signal(),
                o_OQ     = Signal() if with_odelay else dqs_o_no_delay,
                i_TCE    = 1,
                i_T1     = ~dqs_oe_delayed,
                o_TQ     = dqs_t,
            )
            if with_odelay:
                self.specials += Instance("ODELAYE2",
                    p_DELAY_SRC             = "ODATAIN",
                    p_SIGNAL_PATTERN        = "DATA",
                    p_CINVCTRL_SEL          = "FALSE",
                    p_HIGH_PERFORMANCE_MODE = "TRUE",
                    p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                    p_PIPE_SEL              = "FALSE",
                    p_ODELAY_TYPE           = "VARIABLE",
                    p_ODELAY_VALUE          = half_sys8x_taps,
                    i_C        = ClockSignal(),
                    i_LD       = self._dly_sel.storage[i] & self._wdly_dqs_rst.re,
                    i_CE       = self._dly_sel.storage[i] & self._wdly_dqs_inc.re,
                    i_LDPIPEEN = 0,
                    i_INC      = 1,
                    o_ODATAIN  = dqs_o_no_delay,
                    o_DATAOUT  = dqs_o_delayed
                )
            self.specials += [
                Instance("IDELAYE2",
                    p_DELAY_SRC             = "IDATAIN",
                    p_SIGNAL_PATTERN        = "DATA",
                    p_CINVCTRL_SEL          = "FALSE",
                    p_HIGH_PERFORMANCE_MODE = "TRUE",
                    p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                    p_PIPE_SEL              = "FALSE",
                    p_IDELAY_TYPE           = "FIXED",
                    p_IDELAY_VALUE          = half_sys8x_taps,
                    i_IDATAIN               = dqs_i[i],
                    o_DATAOUT               = dqs_i_delayed[i]
                )
            ]
            self.specials += Instance("IOBUFDS",
                i_T    = dqs_t,
                i_I    = dqs_o_delayed if with_odelay else dqs_o_no_delay,
                o_O    = dqs_i[i],
                io_IO  = pads.dqs_p[i],
                io_IOB = pads.dqs_n[i],
            )

        # DQ ---------------------------------------------------------------------------------------
        dq_oe         = Signal()
        dq_oe_delayed = Signal() # Tristate control is asynchronous, needs to be delayed.
        self.sync += dq_oe_delayed.eq(dqs_pattern.preamble | dq_oe | dqs_pattern.postamble)
        for i in range(databits):
            dq_o_nodelay = Signal()
            dq_o_delayed = Signal()
            dq_i_nodelay = Signal()
            dq_i_delayed = Signal()
            dq_t         = Signal()
            dq_i_data    = Signal(8)
            self.specials += [
                Instance("OSERDESE2",
                    p_SERDES_MODE    = "MASTER",
                    p_DATA_WIDTH     = 2*nphases,
                    p_TRISTATE_WIDTH = 1,
                    p_DATA_RATE_OQ   = "DDR",
                    p_DATA_RATE_TQ   = "BUF",
                    i_RST    = ResetSignal(),
                    i_CLK    = ClockSignal(ddr_clk),
                    i_CLKDIV = ClockSignal(),
                    i_D1     = dfi.phases[0].wrdata[i],
                    i_D2     = dfi.phases[0].wrdata[databits+i],
                    i_D3     = dfi.phases[1].wrdata[i],
                    i_D4     = dfi.phases[1].wrdata[databits+i],
                    i_D5     = dfi.phases[2].wrdata[i],
                    i_D6     = dfi.phases[2].wrdata[databits+i],
                    i_D7     = dfi.phases[3].wrdata[i],
                    i_D8     = dfi.phases[3].wrdata[databits+i],
                    i_TCE    = 1,
                    i_T1     = ~dq_oe_delayed,
                    o_TQ     = dq_t,
                    i_OCE    = 1,
                    o_OQ     = dq_o_nodelay,
                )
            ]
            if interface_type == "NETWORKING":
                self.specials += [
                    Instance("ISERDESE2",
                        p_SERDES_MODE    = "MASTER",
                        p_INTERFACE_TYPE = "NETWORKING",
                        p_DATA_WIDTH     = 2*nphases,
                        p_DATA_RATE      = "DDR",
                        p_NUM_CE         = 1,
                        p_IOBDELAY       = "IFD",
                        i_RST     = ResetSignal(),
                        i_CLK     = ClockSignal(ddr_clk),
                        i_CLKB    = ~ClockSignal(ddr_clk),
                        i_CLKDIV  = ClockSignal(),
                        i_BITSLIP = 0,
                        i_CE1     = 1,
                        i_DDLY    = dq_i_delayed,
                        o_Q8      = dq_i_data[0],
                        o_Q7      = dq_i_data[1],
                        o_Q6      = dq_i_data[2],
                        o_Q5      = dq_i_data[3],
                        o_Q4      = dq_i_data[4],
                        o_Q3      = dq_i_data[5],
                        o_Q2      = dq_i_data[6],
                        o_Q1      = dq_i_data[7],
                    )
                ]
            elif interface_type == "MEMORY":
                _dq_i_data_sys2x = Signal(4)
                self.specials += [
                    Instance("ISERDESE2",
                        p_SERDES_MODE    = "MASTER",
                        p_INTERFACE_TYPE = "MEMORY",
                        p_DATA_WIDTH     = nphases,
                        p_DATA_RATE      = "DDR",
                        p_NUM_CE         = 1,
                        p_IOBDELAY       = "IFD",
                        i_RST     = ResetSignal(),
                        i_CLK     = dqs_i_delayed[i//8],
                        i_CLKB    = ~dqs_i_delayed[i//8],
                        i_OCLK    = ClockSignal("sys4x"),
                        i_OCLKB   = ~ClockSignal("sys4x"),
                        i_CLKDIV  = ClockSignal("sys2x"),
                        i_BITSLIP = 0,
                        i_CE1     = 1,
                        i_DDLY    = dq_i_delayed,
                        o_Q4      = _dq_i_data_sys2x[0],
                        o_Q3      = _dq_i_data_sys2x[1],
                        o_Q2      = _dq_i_data_sys2x[2],
                        o_Q1      = _dq_i_data_sys2x[3],
                    )
                ]
                self.sync.sys2x += [
                    dq_i_data[:4].eq(dq_i_data[4:]),
                    dq_i_data[4:].eq(_dq_i_data_sys2x),
                ]

            dq_bitslip = BitSlip(8,
                rst = self._dly_sel.storage[i//8] & self._rdly_dq_bitslip_rst.re,
                slp = self._dly_sel.storage[i//8] & self._rdly_dq_bitslip.re)
            self.submodules += dq_bitslip
            self.comb += dq_bitslip.i.eq(dq_i_data)
            self.comb += [
                dfi.phases[0].rddata[i].eq(dq_bitslip.o[0]),
                dfi.phases[1].rddata[i].eq(dq_bitslip.o[2]),
                dfi.phases[2].rddata[i].eq(dq_bitslip.o[4]),
                dfi.phases[3].rddata[i].eq(dq_bitslip.o[6]),
                dfi.phases[0].rddata[databits+i].eq(dq_bitslip.o[1]),
                dfi.phases[1].rddata[databits+i].eq(dq_bitslip.o[3]),
                dfi.phases[2].rddata[databits+i].eq(dq_bitslip.o[5]),
                dfi.phases[3].rddata[databits+i].eq(dq_bitslip.o[7])
            ]

            if with_odelay:
                self.specials += Instance("ODELAYE2",
                    p_SIGNAL_PATTERN        = "DATA",
                    p_DELAY_SRC             = "ODATAIN",
                    p_CINVCTRL_SEL          = "FALSE",
                    p_HIGH_PERFORMANCE_MODE = "TRUE",
                    p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                    p_PIPE_SEL              = "FALSE",
                    p_ODELAY_TYPE           = "VARIABLE",
                    p_ODELAY_VALUE          = 0,
                    i_C        = ClockSignal(),
                    i_LD       = self._dly_sel.storage[i//8] & self._wdly_dq_rst.re,
                    i_LDPIPEEN = 0,
                    i_CE       = self._dly_sel.storage[i//8] & self._wdly_dq_inc.re,
                    i_INC      = 1,
                    o_ODATAIN  = dq_o_nodelay,
                    o_DATAOUT  = dq_o_delayed,
                )
            self.specials += [
                Instance("IDELAYE2",
                    p_SIGNAL_PATTERN        = "DATA",
                    p_DELAY_SRC             = "IDATAIN",
                    p_CINVCTRL_SEL          = "FALSE",
                    p_HIGH_PERFORMANCE_MODE = "TRUE",
                    p_REFCLK_FREQUENCY      = iodelay_clk_freq/1e6,
                    p_PIPE_SEL              = "FALSE",
                    p_IDELAY_TYPE           = "VARIABLE",
                    p_IDELAY_VALUE          = 0,
                    i_C        = ClockSignal(),
                    i_LD       = self._dly_sel.storage[i//8] & self._rdly_dq_rst.re,
                    i_LDPIPEEN = 0,
                    i_CE       = self._dly_sel.storage[i//8] & self._rdly_dq_inc.re,
                    i_INC      = 1,
                    i_IDATAIN  = dq_i_nodelay,
                    o_DATAOUT  = dq_i_delayed
                ),
                Instance("IOBUF",
                    i_I   = dq_o_delayed if with_odelay else dq_o_nodelay,
                    o_O   = dq_i_nodelay,
                    i_T   = dq_t,
                    io_IO = pads.dq[i]
                )
            ]

        # Read Control Path ------------------------------------------------------------------------
        # Creates a shift register of read commands coming from the DFI interface. This shift register
        # is used to indicate to the DFI interface that the read data is valid.
        #
        # The read data valid is asserted for 1 sys_clk cycle when the data is available on the DFI
        # interface, the latency is the sum of the OSERDESE2, CAS, ISERDESE2 and Bitslip latencies.
        rddata_en      = Signal(self.settings.read_latency)
        rddata_en_last = Signal.like(rddata_en)
        self.comb += rddata_en.eq(Cat(dfi.phases[self.settings.rdphase].rddata_en, rddata_en_last))
        self.sync += rddata_en_last.eq(rddata_en)
        self.sync += [phase.rddata_valid.eq(rddata_en[-1] | self._wlevel_en.storage) for phase in dfi.phases]

        # Write Control Path -----------------------------------------------------------------------
        # Creates a shift register of write commands coming from the DFI interface. This shift register
        # is used to control DQ/DQS tristates.
        wrdata_en = Signal(cwl_sys_latency + 2)
        wrdata_en_last = Signal.like(wrdata_en)
        self.comb += wrdata_en.eq(Cat(dfi.phases[self.settings.wrphase].wrdata_en, wrdata_en_last))
        self.sync += wrdata_en_last.eq(wrdata_en)
        self.comb += dq_oe.eq(wrdata_en[cwl_sys_latency])
        self.comb += If(self._wlevel_en.storage, dqs_oe.eq(1)).Else(dqs_oe.eq(dq_oe))

        # Write DQS Postamble/Preamble Control Path ------------------------------------------------
        # Generates DQS Preamble 1 cycle before the first write and Postamble 1 cycle after the last
        # write. During writes, DQS tristate is configured as output for at least 3 sys_clk cycles:
        # 1 for Preamble, 1 for the Write and 1 for the Postamble.
        self.comb += dqs_pattern.preamble.eq( wrdata_en[cwl_sys_latency - 1]  & ~wrdata_en[cwl_sys_latency])
        self.comb += dqs_pattern.postamble.eq(wrdata_en[cwl_sys_latency + 1]  & ~wrdata_en[cwl_sys_latency])

# Xilinx Virtex7 (S7DDRPHY with odelay) ------------------------------------------------------------

class V7DDRPHY(S7DDRPHY):
    def __init__(self, pads, **kwargs):
        S7DDRPHY.__init__(self, pads, with_odelay=True, **kwargs)

# Xilinx Kintex7 (S7DDRPHY with odelay) ------------------------------------------------------------

class K7DDRPHY(S7DDRPHY):
    def __init__(self, pads, **kwargs):
        S7DDRPHY.__init__(self, pads, with_odelay=True, **kwargs)

# Xilinx Artix7 (S7DDRPHY without odelay, sys2/4x_dqs generated in CRG with 90° phase vs sys2/4x) --

class A7DDRPHY(S7DDRPHY):
    def __init__(self, pads, **kwargs):
        S7DDRPHY.__init__(self, pads, with_odelay=False, **kwargs)
