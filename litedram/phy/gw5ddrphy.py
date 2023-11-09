#
# This file is part of LiteDRAM.
#
# Copyright (c) 2019 David Shah <dave@ds0.me>
# Copyright (c) 2019-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2022 Icenowy Zheng <icenowy@aosc.io>
# Copyright (c) 2023 Gwenhael Goavec-Merou <gwenhael@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# 1:2 frequency-ratio DDR3 PHY for Gowin's GW5A
# DDR3: 800 MT/s

from functools import reduce
from operator import or_

import math

from migen import *

from litex.gen import *

from migen.fhdl.specials import Tristate
from migen.genlib.cdc import MultiReg

from litex.gen.genlib.misc import timeline

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# BitSlip ------------------------------------------------------------------------------------------

# FIXME: Use BitSlip from litedram.common.

class BitSlip(Module):
    def __init__(self, dw, rst=None, slp=None, cycles=1):
        self.i = Signal(dw)
        self.o = Signal(dw)
        self.rst = Signal() if rst is None else rst
        self.slp = Signal() if slp is None else slp

        # # #

        value = Signal(max=cycles*dw)
        self.sync += If(self.slp, value.eq(value + 1))
        self.sync += If(self.rst, value.eq(0))

        r = Signal((cycles+1)*dw, reset_less=True)
        self.sync += r.eq(Cat(r[dw:], self.i))
        cases = {}
        for i in range(cycles*dw):
            cases[i] = self.o.eq(r[i:dw+i])
        self.comb += Case(value, cases)

# Gowin GW5A DDR PHY Initialization -----------------------------------------------------------------

class GW5DDRPHYInit(Module):
    def __init__(self):
        self.pause = Signal()
        self.stop  = Signal()
        self.delay = Signal(8)
        self.reset = Signal()

        # # #

        new_lock = Signal()
        update   = Signal()
        stop     = Signal()
        freeze   = Signal()
        pause    = Signal()
        reset    = Signal()

        # DDRDLLA instance -------------------------------------------------------------------------
        _lock = Signal()
        delay = Signal(8)
        self.specials += Instance("DDRDLL",
            p_SCAL_EN  = "false",
            i_RESET    = ResetSignal("init"),
            i_CLKIN    = ClockSignal("sys2x"),
            i_UPDNCNTL = ~update,
            i_STOP     = freeze,
            o_STEP     = delay,
            o_LOCK     = _lock
        )
        lock   = Signal()
        lock_d = Signal()
        self.specials += MultiReg(_lock, lock, "init")
        self.sync.init += lock_d.eq(lock)
        self.comb += new_lock.eq(lock & ~lock_d)

        # DDRDLLA/DDQBUFM/ECLK initialization sequence ---------------------------------------------
        t = 8 # in cycles
        self.sync.init += [
            # Wait DDRDLLA Lock
            timeline(new_lock, [
                ( 1*t, [freeze.eq(1)]), # Freeze DDRDLLA
                ( 2*t, [  stop.eq(1)]), # Stop ECLK domain
                ( 3*t, [ reset.eq(1)]), # Reset ECLK domain
                ( 4*t, [ reset.eq(0)]), # Release ECLK domain reset
                ( 5*t, [  stop.eq(0)]), # Release ECLK domain stop
                ( 6*t, [freeze.eq(0)]), # Release DDRDLLA freeze
                ( 7*t, [ pause.eq(1)]), # Pause DQSBUFM
                ( 8*t, [update.eq(1)]), # Update DDRDLLA
                ( 9*t, [update.eq(0)]), # Release DDRDMMA update
                (10*t, [ pause.eq(0)]), # Release DQSBUFM pause
            ])
        ]

        # ------------------------------------------------------------------------------------------
        self.comb += [
            self.pause.eq(pause),
            self.stop.eq(stop),
            self.delay.eq(delay),
            self.reset.eq(reset),
        ]

# Gowin GW5A DDR PHY -------------------------------------------------------------------------------

class GW5DDRPHY(Module, AutoCSR):
    def __init__(self, pads,
        sys_clk_freq = 100e6,
        cl           = None,
        cwl          = None,
        cmd_delay    = 0,
        clk_polarity = 0,
        dm_remapping = None):
        assert isinstance(cmd_delay, int) and cmd_delay < 128
        pads        = PHYPadsCombiner(pads)
        memtype     = "DDR3"
        tck         = 2/(2*2*sys_clk_freq)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = 2
        if not dm_remapping:
            dm_remapping = {}
        assert databits%8 == 0

        # Init -------------------------------------------------------------------------------------
        self.submodules.init = GW5DDRPHYInit()

        # Parameters -------------------------------------------------------------------------------
        cl  = get_default_cl( memtype, tck) if cl  is None else cl
        cwl = get_default_cwl(memtype, tck) if cwl is None else cwl
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

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
        rdphase = get_sys_phase(nphases, cl_sys_latency, cl)
        wrphase = get_sys_phase(nphases, cwl_sys_latency, cwl)
        self.settings = PhySettings(
            phytype       = "GW5DDRPHY",
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = 4*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = rdphase,
            wrphase       = wrphase,
            cl            = cl,
            cwl           = cwl,
            read_latency  = cl_sys_latency + 9 + 1,
            write_latency = cwl_sys_latency - 1 + 1,
            read_leveling = True,
            bitslips      = 4,
            delays        = 8,
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 4*databits, nphases)

        # # #

        bl8_chunk   = Signal()

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)

            # Clock --------------------------------------------------------------------------------
            clk_pattern = {0: 0b1010, 1: 0b0101}[clk_polarity]
            for i in range(len(pads.clk_p)):
                pad_oddrx2f = Signal()
                pad_clk = Signal()
                self.specials += Instance("OSER4",
                    p_TXCLK_POL = 0b0,
                    i_RESET = ResetSignal("sys"),
                    i_PCLK  = ClockSignal("sys"),
                    i_FCLK  = ClockSignal("sys2x"),
                    **{f"i_TX{n}": 0b0 for n in range(2)},
                    **{f"i_D{n}": (clk_pattern >> n) & 0b1 for n in range(4)},
                    o_Q0    = pad_oddrx2f,
                    o_Q1    = Open()
                )
                self.specials += Instance("IODELAY",
                    p_C_STATIC_DLY = cmd_delay,
                    p_DYN_DLY_EN   = "FALSE",
                    p_ADAPT_EN     = "FALSE",
                    i_SDTAP   = 0,
                    i_DLYSTEP = Constant(0, 8),
                    i_VALUE   = 0,
                    i_DI      = pad_oddrx2f,
                    o_DF      = Open(),
                    o_DO      = pad_clk,
                )
                self.specials += Instance("ELVDS_OBUF",
                    i_I  = pad_clk,
                    o_O  = pads.clk_p[i],
                    o_OB = pads.clk_n[i]
                )

            # Commands -----------------------------------------------------------------------------
            commands = {
                # Pad name: (DFI name,   Pad type (required or optional))
                "reset_n" : ("reset_n", "optional"),
                "cs_n"    : ("cs_n",    "optional"),
                "a"       : ("address", "required"),
                "ba"      : ("bank"   , "required"),
                "ras_n"   : ("ras_n"  , "required"),
                "cas_n"   : ("cas_n"  , "required"),
                "we_n"    : ("we_n"   , "required"),
                "cke"     : ("cke"    , "optional"),
                "odt"     : ("odt"    , "optional"),
            }
            for pad_name, (dfi_name, pad_type) in commands.items():
                pad = getattr(pads, pad_name, None)
                if (pad is None):
                    if (pad_type == "required"):
                        raise ValueError(f"DRAM pad {pad_name} required but not found in pads.")
                    continue
                for i in range(len(pad)):
                    pad_oddrx2f = Signal()
                    self.specials += Instance("OSER4",
                        p_TXCLK_POL = 0b0,
                        i_RESET = ResetSignal("sys"),
                        i_PCLK = ClockSignal("sys"),
                        i_FCLK = ClockSignal("sys2x"),
                        **{f"i_TX{n}": 0b0 for n in range(2)},
                        **{f"i_D{n}": getattr(dfi.phases[n//2], dfi_name)[i] for n in range(4)},
                        o_Q0   = pad_oddrx2f,
                        o_Q1   = Open()
                    )
                    self.specials += Instance("IODELAY",
                        p_C_STATIC_DLY = cmd_delay,
                        p_DYN_DLY_EN   = "FALSE",
                        p_ADAPT_EN     = "FALSE",
                        i_SDTAP   = 0,
                        i_DLYSTEP = Constant(0, 8),
                        i_VALUE   = 0,
                        i_DI      = pad_oddrx2f,
                        o_DF      = Open(),
                        o_DO      = pad[i]
                    )

        # DQS/DM/DQ --------------------------------------------------------------------------------
        dq_oe         = Signal()
        dqs_re        = Signal()
        dqs_oe        = Signal()
        dqs_postamble = Signal()
        dqs_preamble  = Signal()
        for i in range(databits//8):
            # DQS
            dqs_i    = Signal()
            dqsr90   = Signal()
            dqsw270  = Signal()
            dqsw     = Signal()
            rdpntr   = Signal(3)
            wrpntr   = Signal(3)
            rdly     = Signal(3)
            burstdet = Signal()
            self.sync += [
                If(self._dly_sel.storage[i] & self._rdly_dq_rst.re, rdly.eq(0)),
                If(self._dly_sel.storage[i] & self._rdly_dq_inc.re, rdly.eq(rdly + 1))
            ]
            self.specials += Instance("DQS",
                p_DQS_MODE = "X2_DDR3",
                # Clocks / Reset
                i_RESET    = ResetSignal("sys"),
                i_PCLK     = ClockSignal("sys"),
                i_FCLK     = ClockSignal("sys2x"),
                i_DLLSTEP  = self.init.delay,
                i_HOLD     = self.init.pause | self._dly_sel.storage[i],

                # Control
                # Assert LOADNs to use DDRDEL control
                i_RLOADN   = 0,
                i_RMOVE    = 0,
                i_RDIR     = 1,
                i_WLOADN   = 0,
                i_WMOVE    = 0,
                i_WDIR     = 1,
                o_RFLAG    = Open(),
                o_WFLAG    = Open(),

                # Reads (generate shifted DQS clock for reads)
                i_READ     = Replicate(dqs_re, 4),
                i_RCLKSEL  = rdly,
                i_DQSIN    = dqs_i,
                o_DQSR90   = dqsr90,
                o_RPOINT   = rdpntr,
                o_WPOINT   = wrpntr,
                o_RVALID   = self.datavalid[i],
                o_RBURST   = burstdet,

                # Writes (generate shifted ECLK clock for writes)
                i_WSTEP    = Constant(0, 8),
                o_DQSW270  = dqsw270,
                o_DQSW0    = dqsw
            )
            burstdet_d = Signal()
            self.sync += [
                burstdet_d.eq(burstdet),
                If(self._burstdet_clr.re,  self._burstdet_seen.status[i].eq(0)),
                If(burstdet & ~burstdet_d, self._burstdet_seen.status[i].eq(1)),
            ]

            # DQS ----------------------------------------------------------------------------------
            dqs_o     = Signal()
            dqs_o_oen = Signal()
            self.specials += [
                Instance("OSER4_MEM",
                    p_TCLK_SOURCE = "DQSW",
                    p_TXCLK_POL   = 0b1,
                    i_RESET = ResetSignal("sys"),
                    i_PCLK  = ClockSignal("sys"),
                    i_FCLK  = ClockSignal("sys2x"),
                    i_TCLK  = dqsw,
                    i_TX0   = ~(dqs_oe | dqs_postamble),
                    i_TX1   = ~(dqs_oe | dqs_preamble),
                    **{f"i_D{n}": (0b1010 >> n) & 0b1 for n in range(4)},
                    o_Q0    = dqs_o,
                    o_Q1    = dqs_o_oen
                ),
                Instance("ELVDS_IOBUF",
                    i_I    = dqs_o,
                    i_OEN  = dqs_o_oen,
                    o_O    = dqs_i,
                    io_IO  = pads.dqs_p[i],
                    io_IOB = pads.dqs_n[i]
                )
            ]

            # DM -----------------------------------------------------------------------------------
            dm_o_data       = Signal(8)
            dm_o_data_d     = Signal(8)
            dm_o_data_muxed = Signal(4)
            for n in range(8):
                self.comb += dm_o_data[n].eq(dfi.phases[n//4].wrdata_mask[n%4*databits//8+dm_remapping.get(i, i)])
            self.sync += dm_o_data_d.eq(dm_o_data)
            dm_bl8_cases = {}
            dm_bl8_cases[0] = dm_o_data_muxed.eq(dm_o_data[:4])
            dm_bl8_cases[1] = dm_o_data_muxed.eq(dm_o_data_d[4:])
            self.sync += Case(bl8_chunk, dm_bl8_cases)
            self.specials += Instance("OSER4_MEM",
                p_TCLK_SOURCE = "DQSW270",
                p_TXCLK_POL   = 0b0,
                i_RESET = ResetSignal("sys"),
                i_PCLK  = ClockSignal("sys"),
                i_FCLK  = ClockSignal("sys2x"),
                i_TCLK  = dqsw270,
                **{f"i_TX{n}": 0b0 for n in range(2)},
                **{f"i_D{n}": dm_o_data_muxed[n] for n in range(4)},
                o_Q0    = pads.dm[i],
                o_Q1    = Open()
            )

            # DQ -----------------------------------------------------------------------------------
            for j in range(8*i, 8*(i+1)):
                dq_o            = Signal()
                dq_o_oen        = Signal()
                dq_i            = Signal()
                dq_i_data       = Signal(8)
                dq_o_data       = Signal(8)
                dq_o_data_d     = Signal(8)
                dq_o_data_muxed = Signal(4)
                for n in range(8):
                    self.comb += dq_o_data[n].eq(dfi.phases[n//4].wrdata[n%4*databits+j])
                self.sync += dq_o_data_d.eq(dq_o_data)
                dq_bl8_cases = {}
                dq_bl8_cases[0] = dq_o_data_muxed.eq(dq_o_data[:4])
                dq_bl8_cases[1] = dq_o_data_muxed.eq(dq_o_data_d[4:])
                self.sync += Case(bl8_chunk, dq_bl8_cases)
                self.specials += Instance("OSER4_MEM",
                    p_TCLK_SOURCE = "DQSW270",
                    p_TXCLK_POL   = 0b0,
                    i_RESET = ResetSignal("sys"),
                    i_PCLK  = ClockSignal("sys"),
                    i_FCLK  = ClockSignal("sys2x"),
                    i_TCLK  = dqsw270,
                    i_TX0   = ~dq_oe,
                    i_TX1   = ~dq_oe,
                    **{f"i_D{n}": dq_o_data_muxed[n] for n in range(4)},
                    o_Q0    = dq_o,
                    o_Q1    = dq_o_oen,
                )
                dq_i_bitslip = BitSlip(4,
                    rst    = self._dly_sel.storage[i] & self._rdly_dq_bitslip_rst.re,
                    slp    = self._dly_sel.storage[i] & self._rdly_dq_bitslip.re,
                    cycles = 1)
                self.submodules += dq_i_bitslip
                self.specials += Instance("IDES4_MEM",
                    i_RESET = ResetSignal("sys"),
                    i_PCLK  = ClockSignal("sys"),
                    i_FCLK  = ClockSignal("sys2x"),
                    i_ICLK  = dqsr90,
                    i_RADDR = rdpntr,
                    i_WADDR = wrpntr,
                    i_D     = dq_i,
                    i_CALIB = 0,
                    **{f"o_Q{n}": dq_i_bitslip.i[n] for n in range(4)},
                )
                dq_i_bitslip_o_d = Signal(4)
                self.sync += dq_i_bitslip_o_d.eq(dq_i_bitslip.o)
                self.comb += dq_i_data.eq(Cat(dq_i_bitslip_o_d, dq_i_bitslip.o))
                for n in range(8):
                    self.comb += dfi.phases[n//4].rddata[n%4*databits+j].eq(dq_i_data[n])
                self.specials += Instance("IOBUF",
                    i_I   = dq_o,
                    i_OEN = dq_o_oen,
                    o_O   = dq_i,
                    io_IO = pads.dq[j]
                )

        # Read Control Path ------------------------------------------------------------------------
        rdtap = cl_sys_latency - 1 + 1

        # Creates a delay line of read commands coming from the DFI interface. The taps are used to
        # control DQS read (internal read pulse of the DQSBUF) and the output of the delay is used
        # signal a valid read data to the DFI interface.
        #
        # The DQS read must be asserted for 2 sys_clk cycles before the read data is coming back from
        # the DRAM (see 6.2.4 READ Pulse Positioning Optimization of FPGA-TN-02035-1.2)
        #
        # The read data valid is asserted for 1 sys_clk cycle when the data is available on the DFI
        # interface, the latency is the sum of the ODDRX2DQA, CAS, IDDRX2DQA latencies.
        rddata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].rddata_en for i in range(nphases)]),
            ntaps  = self.settings.read_latency
        )
        self.submodules += rddata_en

        self.comb += [phase.rddata_valid.eq(rddata_en.output) for phase in dfi.phases]
        self.comb += dqs_re.eq(rddata_en.taps[rdtap] | rddata_en.taps[rdtap + 1])

        # Write Control Path -----------------------------------------------------------------------
        wrtap = cwl_sys_latency - 1 + 1

        # Create a delay line of write commands coming from the DFI interface. This taps are used to
        # control DQ/DQS tristates and to select write data of the DRAM burst from the DFI interface.
        # The PHY is operating in halfrate mode (so provide 4 datas every sys_clk cycles: 2x for DDR,
        # 2x for halfrate) but DDR3 requires a burst of 8 datas (BL8) for best efficiency. Writes are
        # then performed in 2 sys_clk cycles and data needs to be selected for each cycle.
        wrdata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].wrdata_en for i in range(nphases)]),
            ntaps  = wrtap + 4
        )
        self.submodules += wrdata_en

        self.comb += dq_oe.eq(wrdata_en.taps[wrtap] | wrdata_en.taps[wrtap + 1])
        self.comb += bl8_chunk.eq(wrdata_en.taps[wrtap])
        self.comb += dqs_oe.eq(dq_oe)

        # Write DQS Postamble/Preamble Control Path ------------------------------------------------
        # Generates DQS Preamble 1 cycle before the first write and Postamble 1 cycle after the last
        # write. During writes, DQS tristate is configured as output for at least 4 sys_clk cycles:
        # 1 for Preamble, 2 for the Write and 1 for the Postamble.
        self.comb += dqs_preamble.eq( wrdata_en.taps[wrtap - 1]  & ~wrdata_en.taps[wrtap + 0])
        self.comb += dqs_postamble.eq(wrdata_en.taps[wrtap + 2]  & ~wrdata_en.taps[wrtap + 1])
