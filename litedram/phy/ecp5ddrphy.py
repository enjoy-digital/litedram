# This file is Copyright (c) 2019 David Shah <dave@ds0.me>
# This file is Copyright (c) 2019-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

# 1:2 frequency-ratio DDR3 PHY for Lattice's ECP5
# DDR3: 800 MT/s

import math

from migen import *
from migen.genlib.misc import timeline, BitSlip
from migen.fhdl.specials import Tristate
from migen.genlib.cdc import MultiReg
from migen.genlib.misc import WaitTimer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# Lattice ECP5 DDR PHY Initialization --------------------------------------------------------------

class ECP5DDRPHYInit(Module):
    def __init__(self, eclk_cd):
        self.pause = Signal()
        self.stop  = Signal()
        self.delay = Signal()

        # # #

        new_lock = Signal()
        update   = Signal()
        stop     = Signal()
        freeze   = Signal()
        pause    = Signal()
        reset    = Signal()

        # DDRDLLA instance -------------------------------------------------------------------------
        _lock = Signal()
        delay = Signal()
        self.specials += Instance("DDRDLLA",
            i_CLK      = ClockSignal("sys2x"),
            i_RST      = ResetSignal(),
            i_UDDCNTLN = ~update,
            i_FREEZE   = freeze,
            o_DDRDEL   = delay,
            o_LOCK     = _lock
        )
        lock   = Signal()
        lock_d = Signal()
        self.specials += MultiReg(_lock, lock)
        self.sync += lock_d.eq(lock)
        self.comb += new_lock.eq(lock & ~lock_d)

        # DDRDLLA/DDQBUFM/ECLK initialization sequence ---------------------------------------------
        t = 8 # in cycles
        self.sync.init += [
            # Wait DDRDLLA Lock
            timeline(new_lock, [
                (1*t,  [freeze.eq(1)]), # Freeze DDRDLLA
                (2*t,  [stop.eq(1)]),   # Stop ECLK domain
                (3*t,  [reset.eq(1)]),  # Reset ECLK domain
                (4*t,  [reset.eq(0)]),  # Release ECLK domain reset
                (5*t,  [stop.eq(0)]),   # Release ECLK domain stop
                (6*t,  [freeze.eq(0)]), # Release DDRDLLA freeze
                (7*t,  [pause.eq(1)]),  # Pause DQSBUFM
                (8*t,  [update.eq(1)]), # Update DDRDLLA
                (9*t,  [update.eq(0)]), # Release DDRDMMA update
                (10*t, [pause.eq(0)]),  # Release DQSBUFM pause
            ])
        ]

        # ------------------------------------------------------------------------------------------
        self.comb += [
            self.pause.eq(pause),
            self.stop.eq(stop),
            self.delay.eq(delay),
            ResetSignal(eclk_cd).eq(reset)
        ]

# Lattice ECP5 DDR PHY -----------------------------------------------------------------------------

class ECP5DDRPHY(Module, AutoCSR):
    def __init__(self, pads, sys_clk_freq=100e6):
        memtype     = "DDR3"
        tck         = 2/(2*2*sys_clk_freq)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = 2
        assert databits%8 == 0

        # Init -------------------------------------------------------------------------------------
        self.submodules.init = ClockDomainsRenamer("init")(ECP5DDRPHYInit("sys2x"))

        # Registers --------------------------------------------------------------------------------
        self._dly_sel = CSRStorage(databits//8)

        self._rdly_dq_rst         = CSR()
        self._rdly_dq_inc         = CSR()
        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        self._burstdet_clr  = CSR()
        self._burstdet_seen = CSRStatus(databits//8)

        # Observation
        self.datavalid = Signal(databits//8)

        # PHY settings -----------------------------------------------------------------------------
        cl, cwl         = get_cl_cw(memtype, tck)
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        rdcmdphase, rdphase = get_sys_phases(nphases, cl_sys_latency, cl)
        wrcmdphase, wrphase = get_sys_phases(nphases, cwl_sys_latency, cwl)
        self.settings = PhySettings(
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = 4*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = rdphase,
            wrphase       = wrphase,
            rdcmdphase    = rdcmdphase,
            wrcmdphase    = wrcmdphase,
            cl            = cl,
            cwl           = cwl,
            read_latency  = 2 + cl_sys_latency + 2 + log2_int(4//nphases) + 6,
            write_latency = cwl_sys_latency
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 4*databits, 4)

        # # #

        bl8_sel = Signal()

        # Clock ------------------------------------------------------------------------------------
        for i in range(len(pads.clk_p)):
            sd_clk_se = Signal()
            self.specials += Instance("ODDRX2F",
                i_RST  = ResetSignal("sys2x"),
                i_ECLK = ClockSignal("sys2x"),
                i_SCLK = ClockSignal(),
                i_D0   = 0,
                i_D1   = 1,
                i_D2   = 0,
                i_D3   = 1,
                o_Q    = pads.clk_p[i]
            )

        # Addresses and Commands -------------------------------------------------------------------
        for i in range(addressbits):
            self.specials += Instance("ODDRX2F",
                i_RST  = ResetSignal("sys2x"),
                i_ECLK = ClockSignal("sys2x"),
                i_SCLK = ClockSignal(),
                i_D0   = dfi.phases[0].address[i],
                i_D1   = dfi.phases[0].address[i],
                i_D2   = dfi.phases[1].address[i],
                i_D3   = dfi.phases[1].address[i],
                o_Q    = pads.a[i]
            )
        for i in range(bankbits):
            self.specials += Instance("ODDRX2F",
                i_RST  = ResetSignal("sys2x"),
                i_ECLK = ClockSignal("sys2x"),
                i_SCLK = ClockSignal(),
                i_D0   = dfi.phases[0].bank[i],
                i_D1   = dfi.phases[0].bank[i],
                i_D2   = dfi.phases[1].bank[i],
                i_D3   = dfi.phases[1].bank[i],
                o_Q    = pads.ba[i]
            )
        controls = ["ras_n", "cas_n", "we_n", "cke", "odt"]
        if hasattr(pads, "reset_n"):
            controls.append("reset_n")
        if hasattr(pads, "cs_n"):
            controls.append("cs_n")
        for name in controls:
            for i in range(len(getattr(pads, name))):
                self.specials += Instance("ODDRX2F",
                    i_RST  = ResetSignal("sys2x"),
                    i_ECLK = ClockSignal("sys2x"),
                    i_SCLK = ClockSignal(),
                    i_D0   = getattr(dfi.phases[0], name)[i],
                    i_D1   = getattr(dfi.phases[0], name)[i],
                    i_D2   = getattr(dfi.phases[1], name)[i],
                    i_D3   = getattr(dfi.phases[1], name)[i],
                    o_Q    = getattr(pads, name)[i]
                )

        # DQ ---------------------------------------------------------------------------------------
        oe_dq         = Signal()
        oe_dqs        = Signal()
        dqs_postamble = Signal()
        dqs_preamble  = Signal()
        dqs_read      = Signal()
        for i in range(databits//8):
            # DQSBUFM
            dqs_i   = Signal()
            dqsr90  = Signal()
            dqsw270 = Signal()
            dqsw    = Signal()
            rdpntr  = Signal(3)
            wrpntr  = Signal(3)
            rdly    = Signal(7)
            self.sync += \
                If(self._dly_sel.storage[i],
                    If(self._rdly_dq_rst.re,
                        rdly.eq(0),
                    ).Elif(self._rdly_dq_inc.re,
                        rdly.eq(rdly + 1),
                    )
                )
            datavalid = Signal()
            burstdet  = Signal()
            self.specials += Instance("DQSBUFM",
                p_DQS_LI_DEL_ADJ = "MINUS",
                p_DQS_LI_DEL_VAL = 1,
                p_DQS_LO_DEL_ADJ = "MINUS",
                p_DQS_LO_DEL_VAL = 4,
                # Clocks / Reset
                i_SCLK           = ClockSignal("sys"),
                i_ECLK           = ClockSignal("sys2x"),
                i_RST            = ResetSignal("sys2x"),
                i_DDRDEL         = self.init.delay,
                i_PAUSE          = self.init.pause | self._dly_sel.storage[i],

                # Control
                # Assert LOADNs to use DDRDEL control
                i_RDLOADN        = 0,
                i_RDMOVE         = 0,
                i_RDDIRECTION    = 1,
                i_WRLOADN        = 0,
                i_WRMOVE         = 0,
                i_WRDIRECTION    = 1,

                # Reads (generate shifted DQS clock for reads)
                i_READ0          = dqs_read,
                i_READ1          = dqs_read,
                i_READCLKSEL0    = rdly[0],
                i_READCLKSEL1    = rdly[1],
                i_READCLKSEL2    = rdly[2],
                i_DQSI           = dqs_i,
                o_DQSR90         = dqsr90,
                o_RDPNTR0        = rdpntr[0],
                o_RDPNTR1        = rdpntr[1],
                o_RDPNTR2        = rdpntr[2],
                o_WRPNTR0        = wrpntr[0],
                o_WRPNTR1        = wrpntr[1],
                o_WRPNTR2        = wrpntr[2],
                o_DATAVALID      = self.datavalid[i],
                o_BURSTDET       = burstdet,

                # Writes (generate shifted ECLK clock for writes)
                o_DQSW270        = dqsw270,
                o_DQSW           = dqsw
            )
            burstdet_d = Signal()
            self.sync += [
                burstdet_d.eq(burstdet),
                If(self._burstdet_clr.re,
                    self._burstdet_seen.status[i].eq(0)
                ).Elif(burstdet & ~burstdet_d,
                    self._burstdet_seen.status[i].eq(1)
                )
            ]

            # DQS and DM ---------------------------------------------------------------------------
            dqs_serdes_pattern = Signal(8, reset=0b1010)
            dm_o_data          = Signal(8)
            dm_o_data_d        = Signal(8)
            dm_o_data_muxed    = Signal(4)
            self.comb += dm_o_data.eq(Cat(
                dfi.phases[0].wrdata_mask[0*databits//8+i], dfi.phases[0].wrdata_mask[1*databits//8+i],
                dfi.phases[0].wrdata_mask[2*databits//8+i], dfi.phases[0].wrdata_mask[3*databits//8+i],
                dfi.phases[1].wrdata_mask[0*databits//8+i], dfi.phases[1].wrdata_mask[1*databits//8+i],
                dfi.phases[1].wrdata_mask[2*databits//8+i], dfi.phases[1].wrdata_mask[3*databits//8+i]),
            )
            self.sync += dm_o_data_d.eq(dm_o_data)
            self.sync += \
                If(bl8_sel,
                    dm_o_data_muxed.eq(dm_o_data_d[4:])
                ).Else(
                    dm_o_data_muxed.eq(dm_o_data[:4])
                )
            self.specials += Instance("ODDRX2DQA",
                i_RST     = ResetSignal("sys2x"),
                i_ECLK    = ClockSignal("sys2x"),
                i_SCLK    = ClockSignal(),
                i_DQSW270 = dqsw270,
                i_D0      = dm_o_data_muxed[0],
                i_D1      = dm_o_data_muxed[1],
                i_D2      = dm_o_data_muxed[2],
                i_D3      = dm_o_data_muxed[3],
                o_Q       = pads.dm[i]
            )

            dqs      = Signal()
            dqs_oe_n = Signal()
            self.specials += [
                Instance("ODDRX2DQSB",
                    i_RST  = ResetSignal("sys2x"),
                    i_ECLK = ClockSignal("sys2x"),
                    i_SCLK = ClockSignal(),
                    i_DQSW = dqsw,
                    i_D0   = dqs_serdes_pattern[0],
                    i_D1   = dqs_serdes_pattern[1],
                    i_D2   = dqs_serdes_pattern[2],
                    i_D3   = dqs_serdes_pattern[3],
                    o_Q    = dqs
                ),
                Instance("TSHX2DQSA",
                    i_RST  = ResetSignal("sys2x"),
                    i_ECLK = ClockSignal("sys2x"),
                    i_SCLK = ClockSignal(),
                    i_DQSW = dqsw,
                    i_T0   = ~(oe_dqs|dqs_postamble),
                    i_T1   = ~(oe_dqs|dqs_preamble),
                    o_Q    = dqs_oe_n
                ),
                Tristate(pads.dqs_p[i], dqs, ~dqs_oe_n, dqs_i)
            ]

            for j in range(8*i, 8*(i+1)):
                dq_o            = Signal()
                dq_i            = Signal()
                dq_oe_n         = Signal()
                dq_i_delayed    = Signal()
                dq_i_data       = Signal(4)
                dq_o_data       = Signal(8)
                dq_o_data_d     = Signal(8)
                dq_o_data_muxed = Signal(4)
                self.comb += dq_o_data.eq(Cat(
                    dfi.phases[0].wrdata[0*databits+j], dfi.phases[0].wrdata[1*databits+j],
                    dfi.phases[0].wrdata[2*databits+j], dfi.phases[0].wrdata[3*databits+j],
                    dfi.phases[1].wrdata[0*databits+j], dfi.phases[1].wrdata[1*databits+j],
                    dfi.phases[1].wrdata[2*databits+j], dfi.phases[1].wrdata[3*databits+j])
                )
                self.sync += dq_o_data_d.eq(dq_o_data)
                self.sync += \
                    If(bl8_sel,
                        dq_o_data_muxed.eq(dq_o_data_d[4:])
                    ).Else(
                        dq_o_data_muxed.eq(dq_o_data[:4])
                    )
                self.specials += [
                    Instance("ODDRX2DQA",
                        i_RST     = ResetSignal("sys2x"),
                        i_ECLK    = ClockSignal("sys2x"),
                        i_SCLK    = ClockSignal(),
                        i_DQSW270 = dqsw270,
                        i_D0      = dq_o_data_muxed[0],
                        i_D1      = dq_o_data_muxed[1],
                        i_D2      = dq_o_data_muxed[2],
                        i_D3      = dq_o_data_muxed[3],
                        o_Q       = dq_o
                    ),
                    Instance("DELAYF",
                        p_DEL_MODE  = "DQS_ALIGNED_X2",
                        i_LOADN     = 1,
                        i_MOVE      = 0,
                        i_DIRECTION = 0,
                        i_A         = dq_i,
                        o_Z         = dq_i_delayed
                    ),
                    Instance("IDDRX2DQA",
                        i_RST     = ResetSignal("sys2x"),
                        i_ECLK    = ClockSignal("sys2x"),
                        i_SCLK    = ClockSignal(),
                        i_DQSR90  = dqsr90,
                        i_RDPNTR0 = rdpntr[0],
                        i_RDPNTR1 = rdpntr[1],
                        i_RDPNTR2 = rdpntr[2],
                        i_WRPNTR0 = wrpntr[0],
                        i_WRPNTR1 = wrpntr[1],
                        i_WRPNTR2 = wrpntr[2],
                        i_D       = dq_i_delayed,
                        o_Q0      = dq_i_data[0],
                        o_Q1      = dq_i_data[1],
                        o_Q2      = dq_i_data[2],
                        o_Q3      = dq_i_data[3],
                    )
                ]
                dq_bitslip = BitSlip(4)
                self.comb += dq_bitslip.i.eq(dq_i_data)
                self.sync += \
                    If(self._dly_sel.storage[i],
                        If(self._rdly_dq_bitslip_rst.re,
                            dq_bitslip.value.eq(0)
                        ).Elif(self._rdly_dq_bitslip.re,
                            dq_bitslip.value.eq(dq_bitslip.value + 1)
                        )
                    )
                self.submodules += dq_bitslip
                dq_bitslip_o_d = Signal(4)
                self.sync += dq_bitslip_o_d.eq(dq_bitslip.o)
                self.comb += [
                    dfi.phases[0].rddata[0*databits+j].eq(dq_bitslip_o_d[0]), dfi.phases[0].rddata[1*databits+j].eq(dq_bitslip_o_d[1]),
                    dfi.phases[0].rddata[2*databits+j].eq(dq_bitslip_o_d[2]), dfi.phases[0].rddata[3*databits+j].eq(dq_bitslip_o_d[3]),
                    dfi.phases[1].rddata[0*databits+j].eq(dq_bitslip.o[0]), dfi.phases[1].rddata[1*databits+j].eq(dq_bitslip.o[1]),
                    dfi.phases[1].rddata[2*databits+j].eq(dq_bitslip.o[2]), dfi.phases[1].rddata[3*databits+j].eq(dq_bitslip.o[3]),
                ]
                self.specials += [
                    Instance("TSHX2DQA",
                        i_RST     = ResetSignal("sys2x"),
                        i_ECLK    = ClockSignal("sys2x"),
                        i_SCLK    = ClockSignal(),
                        i_DQSW270 = dqsw270,
                        i_T0      = ~oe_dq,
                        i_T1      = ~oe_dq,
                        o_Q       = dq_oe_n,
                    ),
                    Tristate(pads.dq[j], dq_o, ~dq_oe_n, dq_i)
                ]

        # Flow control -----------------------------------------------------------------------------
        #
        # total read latency:
        #  ODDRX2DQA latency
        #  cl_sys_latency
        #  IDDRX2DQA latency
        rddata_en  = dfi.phases[self.settings.rdphase].rddata_en
        rddata_ens = Array([Signal() for i in range(self.settings.read_latency-1)])
        for i in range(self.settings.read_latency-1):
            n_rddata_en = Signal()
            self.sync += n_rddata_en.eq(rddata_en)
            self.comb += rddata_ens[i].eq(rddata_en)
            rddata_en = n_rddata_en
        self.sync += [phase.rddata_valid.eq(rddata_en)
            for phase in dfi.phases]
        self.comb += dqs_read.eq(rddata_ens[cl_sys_latency+1] | rddata_ens[cl_sys_latency+2])
        oe = Signal()
        last_wrdata_en = Signal(cwl_sys_latency+3)
        wrphase = dfi.phases[self.settings.wrphase]
        self.sync += last_wrdata_en.eq(Cat(wrphase.wrdata_en, last_wrdata_en[:-1]))
        self.comb += oe.eq(
            last_wrdata_en[cwl_sys_latency-1] |
            last_wrdata_en[cwl_sys_latency]   |
            last_wrdata_en[cwl_sys_latency+1] |
            last_wrdata_en[cwl_sys_latency+2])
        self.sync += oe_dqs.eq(oe), oe_dq.eq(oe)
        self.sync += bl8_sel.eq(last_wrdata_en[cwl_sys_latency-1])
        self.sync += dqs_preamble.eq(last_wrdata_en[cwl_sys_latency-2])
        self.sync += dqs_postamble.eq(oe_dqs)
