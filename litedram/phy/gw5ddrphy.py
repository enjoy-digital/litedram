#
# This file is part of LiteDRAM.
#
# Copyright (c) 2019 David Shah <dave@ds0.me>
# Copyright (c) 2019-2020 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2022 Icenowy Zheng <icenowy@aosc.io>
# Copyright (c) 2023 Gwenhael Goavec-Merou <gwenhael@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# 1:2 / 1:4 frequency-ratio DDR3 PHY for Gowin's GW5A
# DDR3: 800 MT/s

from functools import reduce
from operator import or_

import math

from migen import *

from litex.gen import *

from migen.fhdl.specials import Tristate
from migen.genlib.cdc import MultiReg, PulseSynchronizer

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
    def __init__(self, clock_domain="sys2x"):
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
            i_CLKIN    = ClockSignal(clock_domain),
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
    """DDR3 PHY using sys, sys2x/sys4x, and init clock domains.

    Quarter-rate mode also requires sys4x_i, the ungated fast PLL output, to
    capture short burst-detection pulses. The gated HCLK cannot clock fabric FFs.
    """
    def __init__(self, pads,
        sys_clk_freq = 100e6,
        cl           = None,
        cwl          = None,
        cmd_delay    = 0,
        clk_polarity = 0,
        dm_remapping = None,
        dll_off      = False,
        nphases      = 2):
        if nphases not in (2, 4):
            raise ValueError("GW5DDRPHY supports 2 or 4 DFI phases.")
        assert isinstance(cmd_delay, int) and cmd_delay < 128
        pads        = PHYPadsCombiner(pads)
        memtype     = "DDR3"
        tck         = 1/(nphases*sys_clk_freq)
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        serdes_bits = 2*nphases
        phase_beats = 8//nphases
        fast_domain = f"sys{nphases}x"
        dll_on_x4   = nphases == 4 and not dll_off
        if not dm_remapping:
            dm_remapping = {}
        assert databits%8 == 0

        # Init -------------------------------------------------------------------------------------
        # Reset the I/O counters with CLKDIV while the fast clock is stopped.
        self.submodules.init = GW5DDRPHYInit(fast_domain)

        pause = Signal()
        self.specials += MultiReg(self.init.pause, pause, "sys")

        # Parameters -------------------------------------------------------------------------------
        if dll_off:
            if cl not in (None, 6) or cwl not in (None, 6):
                raise ValueError("DDR3 DLL-off mode requires CL=6 and CWL=6.")
            cl, cwl = 6, 6
        cl  = get_default_cl( memtype, tck) if cl  is None else cl
        cwl = get_default_cwl(memtype, tck) if cwl is None else cwl
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        # Registers --------------------------------------------------------------------------------
        self._dly_sel = CSRStorage(databits//8)

        self._rdly_dq_rst         = CSR()
        self._rdly_dq_inc         = CSR()
        self._rdly_dq_dir         = CSRStorage(reset=int(dll_on_x4))
        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        if dll_on_x4:
            self._wdly_dq_rst = CSR()
            self._wdly_dq_inc = CSR()
            self._wdly_dq_dir = CSRStorage()

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
            dfi_databits  = phase_beats*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = rdphase,
            wrphase       = wrphase,
            cl            = cl,
            cwl           = cwl,
            read_latency  = cl_sys_latency + (9 if nphases == 2 else 7),
            write_latency = cwl_sys_latency - 1,
            read_leveling = True,
            write_dq_dqs_training = dll_on_x4,
            bitslips      = serdes_bits,
            delays        = 256,
        )
        self.settings.dll_off = dll_off

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, phase_beats*databits, nphases)

        # # #

        bl8_chunk   = Signal()

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)

            # Clock --------------------------------------------------------------------------------
            clk_pattern = {0: 0b10101010, 1: 0b01010101}[clk_polarity]
            for i in range(len(pads.clk_p)):
                pad_oddrx2f = Signal()
                pad_clk = Signal()
                self.specials += Instance(f"OSER{serdes_bits}",
                    p_TXCLK_POL = 0b0,
                    i_RESET = self.init.reset,
                    i_PCLK  = ClockSignal("sys"),
                    i_FCLK  = ClockSignal(fast_domain),
                    **{f"i_TX{n}": 0b0 for n in range(nphases)},
                    **{f"i_D{n}": (clk_pattern >> n) & 0b1 for n in range(serdes_bits)},
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
                    self.specials += Instance(f"OSER{serdes_bits}",
                        p_TXCLK_POL = 0b0,
                        i_RESET = self.init.reset,
                        i_PCLK = ClockSignal("sys"),
                        i_FCLK = ClockSignal(fast_domain),
                        **{f"i_TX{n}": 0b0 for n in range(nphases)},
                        **{f"i_D{n}": getattr(dfi.phases[n//2], dfi_name)[i] for n in range(serdes_bits)},
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

        dqs_read = Replicate(dqs_re, 4)
        if dll_on_x4:
            # DLL-on returns DQS one CK later than DLL-off at the same CL.
            dqs_re_d = Signal()
            self.sync += dqs_re_d.eq(dqs_re)
            dqs_read = Cat(dqs_re_d, Replicate(dqs_re, 3))

        for i in range(databits//8):
            # DQS
            dqs_i    = Signal()
            dqsr90   = Signal()
            dqsw270  = Signal()
            dqsw     = Signal()
            rdpntr   = Signal(3)
            wrpntr   = Signal(3)
            burstdet = Signal()
            wloadn = 0
            if dll_on_x4:
                wloadn = ~(self.init.reset | (self._dly_sel.storage[i] & self._wdly_dq_rst.wr_stb))
            self.specials += Instance("DQS",
                p_DQS_MODE = "X2_DDR3" if nphases == 2 else "X4",
                # Clocks / Reset
                i_RESET    = self.init.reset,
                i_PCLK     = ClockSignal("sys"),
                i_FCLK     = ClockSignal(fast_domain),
                i_DLLSTEP  = self.init.delay,
                i_HOLD     = pause | self._dly_sel.storage[i],

                # Control
                # Calibrate the read delay, keeping the FIFO clock source fixed.
                i_RLOADN   = ~(self._dly_sel.storage[i] & self._rdly_dq_rst.wr_stb),
                i_RMOVE    = self._dly_sel.storage[i] & self._rdly_dq_inc.wr_stb,
                i_RDIR     = self._rdly_dq_dir.storage,
                i_WLOADN   = wloadn,
                i_WMOVE    = self._dly_sel.storage[i] & self._wdly_dq_inc.wr_stb if dll_on_x4 else 0,
                i_WDIR     = self._wdly_dq_dir.storage if dll_on_x4 else 1,
                o_RFLAG    = Open(),
                o_WFLAG    = Open(),

                # Reads (DLL-on X4 uses the opposite read-gate polarity).
                i_READ     = dqs_read,
                i_RCLKSEL  = 2 if dll_on_x4 else 0,
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
            if nphases == 4:
                # RBURST can rise and fall between system clock edges in X4 mode.
                # Capture its edge in the fast domain before crossing to sys.
                # Synchronize before edge detection so both inputs are registered.
                burstdet_sync = PulseSynchronizer(fast_domain + "_i", "sys")
                self.submodules += burstdet_sync
                burstdet_sample = Signal()
                self.specials += MultiReg(burstdet, burstdet_sample, fast_domain + "_i")
                self.sync.sys4x_i += burstdet_d.eq(burstdet_sample)
                self.comb += burstdet_sync.i.eq(burstdet_sample & ~burstdet_d)
                burst_event = burstdet_sync.o
            else:
                self.sync += burstdet_d.eq(burstdet)
                burst_event = burstdet & ~burstdet_d
            self.sync += [
                If(self._burstdet_clr.wr_stb, self._burstdet_seen.status[i].eq(0)),
                If(burst_event,              self._burstdet_seen.status[i].eq(1)),
            ]

            # DQS ----------------------------------------------------------------------------------
            dqs_o     = Signal()
            dqs_o_oen = Signal()
            self.specials += [
                Instance(f"OSER{serdes_bits}_MEM",
                    p_TCLK_SOURCE = "DQSW",
                    p_TXCLK_POL   = 0b1,
                    i_RESET = self.init.reset,
                    i_PCLK  = ClockSignal("sys"),
                    i_FCLK  = ClockSignal(fast_domain),
                    i_TCLK  = dqsw,
                    **{f"i_TX{n}": ~(
                        dqs_oe |
                        (dqs_postamble if n == 0 else 0) |
                        (dqs_preamble if n == nphases - 1 else 0)
                    ) for n in range(nphases)},
                    **{f"i_D{n}": (0b10101010 >> n) & 0b1 for n in range(serdes_bits)},
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
            dm_o_data_muxed = Signal(serdes_bits)
            for n in range(8):
                self.comb += dm_o_data[n].eq(dfi.phases[n//phase_beats].wrdata_mask[n%phase_beats*databits//8+dm_remapping.get(i, i)])
            if nphases == 2:
                self.sync += dm_o_data_d.eq(dm_o_data)
                self.sync += Case(bl8_chunk, {
                    0: dm_o_data_muxed.eq(dm_o_data[:4]),
                    1: dm_o_data_muxed.eq(dm_o_data_d[4:]),
                })
            else:
                self.sync += dm_o_data_muxed.eq(dm_o_data)
            self.specials += Instance(f"OSER{serdes_bits}_MEM",
                p_TCLK_SOURCE = "DQSW270",
                p_TXCLK_POL   = 0b0,
                i_RESET = self.init.reset,
                i_PCLK  = ClockSignal("sys"),
                i_FCLK  = ClockSignal(fast_domain),
                i_TCLK  = dqsw270,
                **{f"i_TX{n}": 0b0 for n in range(nphases)},
                **{f"i_D{n}": dm_o_data_muxed[n] for n in range(serdes_bits)},
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
                dq_o_data_muxed = Signal(serdes_bits)
                for n in range(8):
                    self.comb += dq_o_data[n].eq(dfi.phases[n//phase_beats].wrdata[n%phase_beats*databits+j])
                if nphases == 2:
                    self.sync += dq_o_data_d.eq(dq_o_data)
                    self.sync += Case(bl8_chunk, {
                        0: dq_o_data_muxed.eq(dq_o_data[:4]),
                        1: dq_o_data_muxed.eq(dq_o_data_d[4:]),
                    })
                else:
                    self.sync += dq_o_data_muxed.eq(dq_o_data)
                self.specials += Instance(f"OSER{serdes_bits}_MEM",
                    p_TCLK_SOURCE = "DQSW270",
                    p_TXCLK_POL   = 0b0,
                    i_RESET = self.init.reset,
                    i_PCLK  = ClockSignal("sys"),
                    i_FCLK  = ClockSignal(fast_domain),
                    i_TCLK  = dqsw270,
                    # Enable DQ before the first DQS edge of the write burst.
                    **{f"i_TX{n}": ~(dq_oe | dqs_preamble) for n in range(nphases)},
                    **{f"i_D{n}": dq_o_data_muxed[n] for n in range(serdes_bits)},
                    o_Q0    = dq_o,
                    o_Q1    = dq_o_oen,
                )
                dq_i_bitslip = BitSlip(serdes_bits,
                    rst    = self._dly_sel.storage[i] & self._rdly_dq_bitslip_rst.wr_stb,
                    slp    = self._dly_sel.storage[i] & self._rdly_dq_bitslip.wr_stb,
                    cycles = 1)
                self.submodules += dq_i_bitslip
                self.specials += Instance(f"IDES{serdes_bits}_MEM",
                    i_RESET = self.init.reset,
                    i_PCLK  = ClockSignal("sys"),
                    i_FCLK  = ClockSignal(fast_domain),
                    i_ICLK  = dqsr90,
                    i_RADDR = rdpntr,
                    i_WADDR = wrpntr,
                    i_D     = dq_i,
                    i_CALIB = 0,
                    **{f"o_Q{n}": dq_i_bitslip.i[n] for n in range(serdes_bits)},
                )
                if nphases == 2:
                    dq_i_bitslip_o_d = Signal(4)
                    self.sync += dq_i_bitslip_o_d.eq(dq_i_bitslip.o)
                    self.comb += dq_i_data.eq(Cat(dq_i_bitslip_o_d, dq_i_bitslip.o))
                else:
                    self.comb += dq_i_data.eq(dq_i_bitslip.o)
                for n in range(8):
                    self.comb += dfi.phases[n//phase_beats].rddata[n%phase_beats*databits+j].eq(dq_i_data[n])
                self.specials += Instance("IOBUF",
                    i_I   = dq_o,
                    i_OEN = dq_o_oen,
                    o_O   = dq_i,
                    io_IO = pads.dq[j]
                )

        # Read Control Path ------------------------------------------------------------------------
        rdtap = cl_sys_latency - 1

        # Creates a delay line of read commands coming from the DFI interface. The taps are used to
        # control DQS read (internal read pulse of the DQSBUF) and the output of the delay is used
        # signal a valid read data to the DFI interface.
        #
        # DQS read gates the returning burst. Read data valid marks the cycle in which the
        # complete BL8 burst is available on the DFI interface.
        rddata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].rddata_en for i in range(nphases)]),
            ntaps  = self.settings.read_latency
        )
        self.submodules += rddata_en

        self.comb += [phase.rddata_valid.eq(rddata_en.output) for phase in dfi.phases]
        self.comb += dqs_re.eq(reduce(or_, rddata_en.taps[rdtap:rdtap + 4//nphases]))

        # Write Control Path -----------------------------------------------------------------------
        wrtap = cwl_sys_latency - 1

        # Create a delay line of write commands coming from the DFI interface. This taps are used to
        # control DQ/DQS tristates and to select write data of the DRAM burst from the DFI interface.
        # BL8 occupies two system cycles at 1:2 and one at 1:4. In 1:2 mode the write
        # data mux selects the appropriate half of the burst for each cycle.
        wrdata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].wrdata_en for i in range(nphases)]),
            ntaps  = wrtap + 4
        )
        self.submodules += wrdata_en

        burst_cycles = 4//nphases
        self.comb += dq_oe.eq(reduce(or_, wrdata_en.taps[wrtap:wrtap + burst_cycles]))
        self.comb += bl8_chunk.eq(wrdata_en.taps[wrtap])
        self.comb += dqs_oe.eq(dq_oe)

        # Write DQS Postamble/Preamble Control Path ------------------------------------------------
        # Extend DQS output enable by one memory clock at each end of the burst. The
        # serializer selects the last/first TX slot of the preceding/following system cycle.
        self.comb += dqs_preamble.eq( wrdata_en.taps[wrtap - 1]  & ~wrdata_en.taps[wrtap + 0])
        self.comb += dqs_postamble.eq(wrdata_en.taps[wrtap + burst_cycles] & ~wrdata_en.taps[wrtap + burst_cycles - 1])
