#
# This file is part of LiteDRAM.
#
# Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# 1:4 frequency-ratio RPC DRAM PHY for Lattice's Nexus (CertusPro-NX).
#
# Clocking: a single edge clock (sys4x) with sys = sys4x/4 from ECLKDIV (X4 gearing). CLK and DQS
# are aligned to the edge clock, DB is sent 90 degrees ahead through the DQSBUF write clocks
# (DQSW270), STB/CS# through a static output delay.
#
# On Nexus, a pin is only bidirectional at X4 with the memory primitives (ODDRX4DQ/TSHX4DQ with
# IDDRX4DQ): a generic IDDRX4 can't be packed with an output DDR. So, unlike the Artix7 backend,
# reads are captured with the DQS of the DRAM, through the DQSBUF (as NexusDDRPHY does for DDR3):
# - The DQSBUF READ input opens a gate on DQS: it has to open during the DQS preamble and to last
#   as long as the burst (8 tCK). Its position is set in sys_clk cycles/tCK (CSRs) and in fractions
#   of tCK with the DQSBUF read clock selection, which is what the read leveling scans.
# - The DQSBUF then returns the burst aligned on sys_clk, over two cycles flagged by DATAVALID.
#
# The write shifts and READ position defaults come from a simulation of this PHY with Lattice's
# primitive models and a RPC DRAM model, then from the hardware (CertusPro-NX VVML board).

import math

from migen import *
from migen.fhdl.specials import Tristate
from migen.genlib.cdc import MultiReg

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *
from litedram.phy.nxddrphy import NexusDDRPHYInit
from litedram.phy.rpc.basephy import BasePHY, RPCPads

# Nexus RPC Pads -----------------------------------------------------------------------------------

class NXRPCPads(RPCPads):
    """RPC pads with pseudo-differential CLK/DQS: only clk_p/dqs_p are driven, the complementary
    pins come from the differential IO standard (ex SSTL15D_I)."""
    _layout = [
        ("clk_p",  1),
        ("cs_n",   1),  # One per rank.
        ("dqs_p",  1),  # May be 2 (one per DB byte).
        ("stb",    1),  # One per rank.
        ("db",    16),
    ]

    def map(self, pads):
        RPCPads.map(self, pads)
        self.clk_n = getattr(pads, "clk_n", None)
        self.dqs_n = getattr(pads, "dqs_n", None)

# Nexus RPC PHY Write Shift ------------------------------------------------------------------------

class _NXRPCPHYShift(Module):
    """Delay a serialized word (one bit per UI, LSB first) by `shift` UIs (0 to words*len(i)).

    The output is registered (one more sys_clk cycle for all the shifted signals), so that the
    gearboxes are fed by registers."""
    def __init__(self, i, shift, words=2):
        dw     = len(i)
        self.o = Signal(dw)

        # # #

        # History: oldest word first, current word last.
        r = Signal(words*dw, reset_less=True)
        self.sync += r.eq(Cat(r[dw:], i))
        hist  = Signal((words + 1)*dw)
        self.comb += hist.eq(Cat(r, i))
        cases = {}
        for n in range(min(words*dw + 1, 2**len(shift))):
            cases[n] = self.o.eq(hist[words*dw - n:(words + 1)*dw - n])
        self.sync += Case(shift, cases)

# Lattice Nexus RPC PHY ----------------------------------------------------------------------------

class NXRPCPHY(BasePHY):
    delay_taps = 128      # DELAYA taps.
    delay_tap  = 12.5e-12 # DELAYA tap delay (typical).
    stb_skew   = 450e-12  # STB/CS# arrive this much later than CLK/DQS/DB with the same delay.

    def __init__(self, stb_delay=None, eclk="sys4x", rdqs_dec=64, **kwargs):
        # Write shifts (in UIs), to align STB/CS#, DQS and DB between them (the latencies of the
        # generic, DQS and DQ output primitives differ). On the board STB/CS# need one more UI than
        # in simulation (2).
        self._stb_shift = CSRStorage(4, reset=3, description="STB/CS# write shift (UIs).")
        self._dqs_shift = CSRStorage(4, reset=8, description="DQS write shift (UIs).")
        self._db_shift  = CSRStorage(4, reset=5, description="DB write shift (UIs).")

        # Read: DQS read enable position (in sys_clk cycles after rddata_en, then in tCK), delay
        # (DQSBUF read clock selection) and burst detection.
        self._rd_en_sel     = CSRStorage(4, reset=4, description="DQS read enable position (sys_clk cycles).")
        self._rd_en_phase   = CSRStorage(2, reset=0, description="DQS read enable position (tCK).")
        self._rdly_dq_rst   = CSR()
        self._rdly_dq_inc   = CSR()
        # Write leveling delay of the DQSBUFs (DQS and DB together, against CLK): reset/increment
        # of the delay code, for the DQSBUFs selected by dly_sel.
        self._wlvl_rst      = CSR()
        self._wlvl_inc      = CSR()
        # Write delay of the DQSBUFs (DB against DQS, around the 90 degrees of the DDRDLL):
        # reset/move of the delay code (direction: 0 to increase, 1 to decrease).
        self._wdly_dir      = CSRStorage()
        self._wdly_rst      = CSR()
        self._wdly_move     = CSR()
        # Read delay of the DQSBUFs (DQS against DB, around the 90 degrees of the DDRDLL):
        # reset/move of the delay code (direction: 0 to increase, 1 to decrease).
        self._rdqs_dir      = CSRStorage()
        self._rdqs_rst      = CSR()
        self._rdqs_move     = CSR()
        # STB/CS# output delay: reset (to the static value)/move (direction: 0 to increase, 1 to
        # decrease), steps of about 12.5ps.
        self._stb_dly_dir   = CSRStorage()
        self._stb_dly_rst   = CSR()
        self._stb_dly_move  = CSR()
        self._burstdet_clr  = CSR()
        self._burstdet_seen = CSRStatus(2)
        self._datavalid_cnt = CSRStatus(8, description="DATAVALID cycles (first DQSBUF) since burstdet_clr.")

        kwargs.update(dict(
            write_ser_latency = 1, # ODDRX4.
            read_des_latency  = 7, # Write shift register, IDDRX4DQ, DQSBUF FIFO and DATAVALID capture (with margin).
            phytype           = self.__class__.__name__,
            with_bitslip      = False, # The DQSBUF returns the burst aligned.
        ))

        if not isinstance(kwargs["pads"], RPCPads):
            kwargs["pads"] = NXRPCPads(kwargs["pads"])

        super().__init__(**kwargs)

        self.eclk = eclk

        # Read leveling: the "delay" is the DQSBUF read clock selection and the "bitslip" moves the
        # DQS read enable (READ gate), in tCK: the round trip delay (in tCK) depends on the
        # frequency, so the leveling looks for the READ position that gives the widest window.
        self.settings.delays        = 16
        self.settings.bitslips      = 8
        self.settings.read_leveling = True

        # STB/CS# output delay: 90 degrees (a quarter of tCK) less the skew measured on the
        # CertusPro-NX VVML board (centre of the working window from CLK 200MHz to 450MHz),
        # limited to the delay line. The stb_dly CSRs move it.
        if stb_delay is None:
            stb_delay = round((self.tck/4 - self.stb_skew)/self.delay_tap)
            stb_delay = max(0, min(stb_delay, self.delay_taps - 1))
        assert 0 <= stb_delay < self.delay_taps
        self.stb_delay = stb_delay

        # Init (DDRDLL/DQSBUF/ECLK sequencing).
        self.submodules.init = NexusDDRPHYInit(eclk=eclk)

        # Reset of the IO primitives (gearboxes, DQSBUFs): the one of the initialization sequence,
        # asserted and released while the edge clock is stopped, as the ECLKDIV: all the gearboxes
        # then start on the same edge clock cycle. With the reset of sys (released a few cycles
        # after the edge clock restarts, and routed as a sys_clk signal), each primitive could start
        # on a different edge clock cycle, depending on the frequency and on the routing.
        self.io_rst = io_rst = Signal()
        self.comb += io_rst.eq(self.init.reset)

        # Read delay: the DQSBUF delays the DQS of a read by 90 degrees (DDRDLL code) on top of
        # its own path, which is already about a UI at CLK 400MHz on CertusPro-NX: the data of
        # the next UI was then captured. After the initialization, the read delay code is
        # decreased by `rdqs_dec` steps (about 10ps each), with the DQSBUFs paused.
        self.rdqs_auto      = rdqs_auto      = Signal()
        self.rdqs_auto_move = rdqs_auto_move = Signal()
        if rdqs_dec:
            pause = Signal()
            count = Signal(max=4*rdqs_dec + 32)
            self.specials += MultiReg(self.init.pause, pause, "sys")
            self.submodules.rdqs_fsm = rdqs_fsm = FSM(reset_state="IDLE")
            rdqs_fsm.act("IDLE",
                If(pause, NextState("INIT"))
            )
            rdqs_fsm.act("INIT",
                NextValue(count, 0),
                If(~pause, NextState("DECREASE"))
            )
            rdqs_fsm.act("DECREASE",
                rdqs_auto.eq(1),
                # Pulses of 2 sys_clk cycles, every 4, away from the edges of the pause.
                rdqs_auto_move.eq((count >= 16) & (count < 4*rdqs_dec + 16) & ~count[1]),
                NextValue(count, count + 1),
                If(count == 4*rdqs_dec + 31, NextState("DONE"))
            )
            rdqs_fsm.act("DONE")

        # DQSBUFs (one per DQS, shared with the DB bits it strobes).
        self.dqs_re  = dqs_re = [Signal(4) for _ in range(len(self.pads.dqs_p))] # One bit per tCK.
        self.rd_slip = []
        self.dqsw    = []
        self.dqsw270 = []
        self.dqsr90  = []
        self.rdpntr  = []
        self.wrpntr  = []
        self.dqs_i   = []
        self.datavalid = Signal(len(self.pads.dqs_p))
        for i in range(len(self.pads.dqs_p)):
            dqs_i    = Signal()
            dqsw     = Signal()
            dqsw270  = Signal()
            dqsr90   = Signal()
            rdpntr   = Signal(3)
            wrpntr   = Signal(3)
            rdly     = Signal(4)
            burstdet = Signal()
            rd_slip  = Signal(3)
            self.sync += [
                If(self.get_rst(i, self._rdly_dq_rst.wr_stb), rdly.eq(0)),
                If(self.get_inc(i, self._rdly_dq_inc.wr_stb), rdly.eq(rdly + 1)),
                If(self.get_rst(i, self._rdly_dq_bitslip_rst.wr_stb), rd_slip.eq(0)),
                If(self.get_inc(i, self._rdly_dq_bitslip.wr_stb),     rd_slip.eq(rd_slip + 1)),
            ]
            self.rd_slip.append(rd_slip)
            # Write leveling delay controls (pulses of 2 sys_clk cycles). The delay resets only
            # follow their CSRs, not the rst CSR that the BIOS pulses at each initialization.
            wlvl_rst   = Signal()
            wlvl_inc   = Signal()
            wlvl_rst_d = Signal()
            wlvl_inc_d = Signal()
            self.comb += [
                wlvl_rst.eq(self.get_inc(i, self._wlvl_rst.wr_stb)),
                wlvl_inc.eq(self.get_inc(i, self._wlvl_inc.wr_stb)),
            ]
            self.sync += [
                wlvl_rst_d.eq(wlvl_rst),
                wlvl_inc_d.eq(wlvl_inc),
            ]
            # Write delay controls: the reset loads the default code (LOADN low with a MOVE pulse).
            wdly_rst  = Signal(4)
            wdly_move = Signal(2)
            self.sync += [
                wdly_rst.eq(Cat(self.get_inc(i, self._wdly_rst.wr_stb), wdly_rst)),
                wdly_move.eq(Cat(self.get_inc(i, self._wdly_move.wr_stb), wdly_move)),
            ]
            rdqs_rst  = Signal(4)
            rdqs_move = Signal(2)
            self.sync += [
                rdqs_rst.eq(Cat(self.get_inc(i, self._rdqs_rst.wr_stb), rdqs_rst)),
                rdqs_move.eq(Cat(self.get_inc(i, self._rdqs_move.wr_stb), rdqs_move)),
            ]
            self.specials += Instance("DQSBUF",
                p_SIGN_READ            = "POSITIVE",
                p_S_READ               = "0",
                p_SIGN_WRITE           = "POSITIVE",
                p_S_WRITE              = "0",
                p_ENABLE_FIFO          = "ENABLED",
                p_FORCE_READ           = "ENABLED",
                p_FREE_WHEEL           = "DDR",
                p_MT_EN_READ           = "ENABLED",
                p_MT_EN_WRITE          = "ENABLED",
                p_MT_EN_WRITE_LEVELING = "ENABLED",
                p_READ_ENABLE          = "ENABLED",
                p_RX_CENTERED          = "ENABLED",
                p_MODX                 = "MDDRX4",
                p_UPDATE_QU            = "UP1_AND_UP0_SAME",
                p_WRITE_ENABLE         = "ENABLED",

                # Clocks / Reset.
                i_RST        = self.io_rst,
                i_RSTSMCNT   = self.io_rst,
                i_SCLK       = ClockSignal("sys"),
                i_ECLKIN     = ClockSignal(eclk),
                i_SELCLK     = 0,
                i_DLLCODE    = self.init.delay,
                i_PAUSE      = self.init.pause | self._dly_sel.storage[i] | rdqs_auto,

                # Control (LOADNs asserted to use the DDRDLL code).
                i_RDLOADN    = self.init.loadn & (rdqs_rst == 0),
                i_READMOVE   = self.init.move  | rdqs_rst[1] | rdqs_rst[2] | (rdqs_move != 0) | rdqs_auto_move,
                i_RDDIR      = self._rdqs_dir.storage | rdqs_auto,
                i_WRLOAD_N   = self.init.loadn & (wdly_rst == 0),
                i_WRMOVE     = self.init.move  | wdly_rst[1] | wdly_rst[2] | (wdly_move != 0),
                i_WRDIR      = self._wdly_dir.storage,
                i_WRLVLOAD_N = self.init.loadn & ~(wlvl_rst | wlvl_rst_d),
                i_WRLVMOVE   = self.init.move  |  (wlvl_inc | wlvl_inc_d),
                i_WRLVDIR    = 0,

                # Reads (generate the shifted DQS clock for reads).
                i_READ        = dqs_re[i],
                i_RDCLKSEL    = rdly,
                i_DQSI        = dqs_i,
                o_DQSR90      = dqsr90,
                o_RDPNTR      = rdpntr,
                o_WRPNTR      = wrpntr,
                o_DATAVALID   = self.datavalid[i],
                o_BURSTDETECT = burstdet,

                # Writes.
                o_DQSW270    = dqsw270,
                o_DQSW       = dqsw,
            )
            burstdet_d = Signal()
            self.sync += [
                burstdet_d.eq(burstdet),
                If(self._burstdet_clr.wr_stb,  self._burstdet_seen.status[i].eq(0)),
                If(burstdet & ~burstdet_d, self._burstdet_seen.status[i].eq(1)),
            ]
            self.dqs_i.append(dqs_i)
            self.dqsr90.append(dqsr90)
            self.rdpntr.append(rdpntr)
            self.wrpntr.append(wrpntr)
            self.dqsw.append(dqsw)
            self.dqsw270.append(dqsw270)

    # Helpers --------------------------------------------------------------------------------------

    def write_shift(self, i, shift, words=2):
        shifter = _NXRPCPHYShift(i, shift, words)
        self.submodules += shifter
        return shifter.o

    def write_shift_oe(self, oe, shift):
        # Output enable as a serialized word, held one more cycle so that the shifted data is never
        # cut, then reduced to one tristate bit per tCK.
        oe_d = Signal()
        self.sync += oe_d.eq(oe)
        oe_1ck = Signal(2*self.nphases)
        self.comb += oe_1ck.eq(Replicate(oe | oe_d, 2*self.nphases))
        oe_1ck = self.write_shift(oe_1ck, shift)
        return [~(oe_1ck[2*n] | oe_1ck[2*n + 1]) for n in range(self.nphases)]

    def oddrx4(self, din, dout):
        self.specials += Instance("ODDRX4",
            i_RST  = self.io_rst,
            i_SCLK = ClockSignal("sys"),
            i_ECLK = ClockSignal(self.eclk),
            **{f"i_D{n}": din[n] for n in range(8)},
            o_Q    = dout,
        )

    def delaya(self, din, dout, delay):
        # Output delay, static value by default, moved with the stb_dly CSRs (pulses of 2 sys_clk
        # cycles).
        if not hasattr(self, "stb_dly_rst"):
            self.stb_dly_rst  = Signal(2)
            self.stb_dly_move = Signal(2)
            self.sync += [
                self.stb_dly_rst.eq(Cat(self._stb_dly_rst.wr_stb,   self.stb_dly_rst)),
                self.stb_dly_move.eq(Cat(self._stb_dly_move.wr_stb, self.stb_dly_move)),
            ]
        self.specials += Instance("DELAYA",
            p_DEL_MODE     = "USER_DEFINED",
            p_DEL_VALUE    = str(delay),
            p_COARSE_DELAY = "0NS",
            i_A            = din,
            i_LOAD_N       = self.stb_dly_rst == 0,
            i_MOVE         = self.stb_dly_move != 0,
            i_DIRECTION    = self._stb_dly_dir.storage,
            i_COARSE0      = 0,
            i_COARSE1      = 0,
            i_RANKSELECT   = 0,
            i_RANKENABLE   = 0,
            i_RANK0UPDATE  = 0,
            i_RANK1UPDATE  = 0,
            o_Z            = dout,
        )

    # I/O implementation ---------------------------------------------------------------------------

    def do_clock_serialization(self, clk_1ck_out, clk_p, clk_n):
        # Pseudo-differential output on clk_p (clk_n from the IO standard), no delay supported.
        self.oddrx4(din=clk_1ck_out, dout=clk_p)

    def do_stb_serialization(self, stb_1ck_out, stb):
        # Called for each rank. STB idles high.
        stb_1ck = self.write_shift(~stb_1ck_out, self._stb_shift.storage)
        stb_o   = Signal()
        self.oddrx4(din=~stb_1ck, dout=stb_o)
        self.delaya(din=stb_o, dout=stb, delay=self.stb_delay)

    def do_cs_serialization(self, cs_n_1ck_out, cs_n):
        # Called for each rank. CS# idles high.
        cs_n_1ck = self.write_shift(~cs_n_1ck_out, self._stb_shift.storage)
        cs_n_o   = Signal()
        self.oddrx4(din=~cs_n_1ck, dout=cs_n_o)
        self.delaya(din=cs_n_o, dout=cs_n, delay=self.stb_delay)

    def do_dqs_serialization(self, dqs_1ck_out, dqs_1ck_in, dqs_oe, dqs_p, dqs_n):
        dqs_1ck = self.write_shift(dqs_1ck_out, self._dqs_shift.storage)
        dqs_t   = self.write_shift_oe(dqs_oe,   self._dqs_shift.storage)
        for i in range(len(dqs_p)):
            dqs_o    = Signal()
            dqs_oe_n = Signal()
            self.specials += [
                Instance("ODDRX4DQS",
                    i_RST  = self.io_rst,
                    i_SCLK = ClockSignal("sys"),
                    i_ECLK = ClockSignal(self.eclk),
                    i_DQSW = self.dqsw[i],
                    **{f"i_D{n}": dqs_1ck[n] for n in range(8)},
                    o_Q    = dqs_o,
                ),
                Instance("TSHX4DQS",
                    i_RST  = self.io_rst,
                    i_SCLK = ClockSignal("sys"),
                    i_ECLK = ClockSignal(self.eclk),
                    i_DQSW = self.dqsw[i],
                    **{f"i_T{n}": dqs_t[n] for n in range(4)},
                    o_Q    = dqs_oe_n,
                ),
                # Pseudo-differential IO on dqs_p (dqs_n from the IO standard).
                Tristate(dqs_p[i], dqs_o, ~dqs_oe_n, self.dqs_i[i]),
            ]
        # DQS is not used for reads (debug only on the other backends).
        self.comb += dqs_1ck_in.eq(0)

    def do_db_serialization(self, db_1ck_out, db_1ck_in, db_oe, db):
        # DQS read enable: as long as the burst (8 tCK, 2 sys_clk cycles), from the selected position
        # (in sys_clk cycles then in tCK, plus the position of the read leveling for each DQSBUF).
        taps   = [self.rddata_en[n] if n < len(self.rddata_en.sr) else 0 for n in range(16 + 1)]
        dqs_re = Signal()
        self.sync += dqs_re.eq(Array([taps[n] | taps[n + 1] for n in range(16)])[self._rd_en_sel.storage])
        for i in range(len(self.dqs_re)):
            position = Signal(4)
            self.comb += position.eq(self._rd_en_phase.storage + self.rd_slip[i])
            self.comb += self.dqs_re[i].eq(self.write_shift(Replicate(dqs_re, 4), position, words=3))

        # The read data come over the sys_clk cycles flagged by DATAVALID (2 per WORD, any number
        # of WORDs in a row with Address Streaming) and the deserializer of the BasePHY takes them
        # later, at a fixed latency (dq_read_stb): an elastic buffer per DQSBUF, with its pointers
        # reset when no read is in progress.
        rd_depth = 8
        rd_idle  = Signal()
        rd_wrptr = [Signal(max=rd_depth, name=f"rd_wrptr{n}") for n in range(len(self.datavalid))]
        rd_rdptr = Signal(max=rd_depth)
        self.comb += rd_idle.eq((self.rddata_en.sr == 0) & ~self.dq_read_stb)
        self.sync += [
            If(rd_idle,
                rd_rdptr.eq(0),
            ).Elif(self.dq_read_stb,
                rd_rdptr.eq(rd_rdptr + 1),
            )
        ]
        for n in range(len(self.datavalid)):
            self.sync += [
                If(rd_idle,
                    rd_wrptr[n].eq(0),
                ).Elif(self.datavalid[n],
                    rd_wrptr[n].eq(rd_wrptr[n] + 1),
                )
            ]
        self.sync += [
            If(self._burstdet_clr.wr_stb,
                self._datavalid_cnt.status.eq(0),
            ).Elif(self.datavalid[0] & (self._datavalid_cnt.status != 255),
                self._datavalid_cnt.status.eq(self._datavalid_cnt.status + 1),
            )
        ]

        db_t = self.write_shift_oe(db_oe, self._db_shift.storage)
        for i in range(self.databits):
            byte      = i//8 if len(self.dqsw270) > 1 else 0 # One or two DQS (hardware option).
            db_o      = Signal()
            db_oe_n   = Signal()
            db_i      = Signal()
            db_i_1ck  = Signal(8)
            db_1ck    = self.write_shift(db_1ck_out[i], self._db_shift.storage)

            self.specials += [
                # Write path.
                Instance("ODDRX4DQ",
                    i_RST     = self.io_rst,
                    i_SCLK    = ClockSignal("sys"),
                    i_ECLK    = ClockSignal(self.eclk),
                    i_DQSW270 = self.dqsw270[byte],
                    **{f"i_D{n}": db_1ck[n] for n in range(8)},
                    o_Q       = db_o,
                ),
                Instance("TSHX4DQ",
                    i_RST     = self.io_rst,
                    i_SCLK    = ClockSignal("sys"),
                    i_ECLK    = ClockSignal(self.eclk),
                    i_DQSW270 = self.dqsw270[byte],
                    **{f"i_T{n}": db_t[n] for n in range(4)},
                    o_Q       = db_oe_n,
                ),
                Tristate(db[i], db_o, ~db_oe_n, db_i),

                # Read path.
                Instance("IDDRX4DQ",
                    i_RST     = self.io_rst,
                    i_SCLK    = ClockSignal("sys"),
                    i_ECLK    = ClockSignal(self.eclk),
                    i_DQSR90  = self.dqsr90[byte],
                    **{f"i_RDPNTR{n}": self.rdpntr[byte][n] for n in range(3)},
                    **{f"i_WRPNTR{n}": self.wrpntr[byte][n] for n in range(3)},
                    i_D       = db_i,
                    **{f"o_Q{n}": db_i_1ck[n] for n in range(8)},
                ),
            ]
            # Elastic buffer (see above).
            db_i_buf = Array(Signal(8, name=f"db_i_buf{i}_{n}") for n in range(rd_depth))
            self.sync += If(self._burstdet_clr.wr_stb,
                [db_i_buf[n].eq(0) for n in range(rd_depth)], # Debug: no stale data after a clear.
            ).Elif(self.datavalid[byte],
                db_i_buf[rd_wrptr[byte]].eq(db_i_1ck),
            )
            self.comb += db_1ck_in[i].eq(db_i_buf[rd_rdptr])
