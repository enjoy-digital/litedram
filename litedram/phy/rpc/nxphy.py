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
    """Delay a serialized word (one bit per UI, LSB first) by `shift` UIs (0 to 2*len(i) - 1)."""
    def __init__(self, i, shift):
        dw     = len(i)
        self.o = Signal(dw)

        # # #

        # History: oldest word first, current word last.
        r = Signal(2*dw, reset_less=True)
        self.sync += r.eq(Cat(r[dw:], i))
        hist  = Signal(3*dw)
        self.comb += hist.eq(Cat(r, i))
        cases = {}
        for n in range(2*dw):
            cases[n] = self.o.eq(hist[2*dw - n:3*dw - n])
        self.comb += Case(shift, cases)

# Lattice Nexus RPC PHY ----------------------------------------------------------------------------

class NXRPCPHY(BasePHY):
    delay_taps = 128      # DELAYB taps.
    delay_tap  = 12.5e-12 # DELAYB tap delay (typical).

    def __init__(self, stb_delay=None, eclk="sys4x", **kwargs):
        # Write shifts (in UIs), to align STB/CS#, DQS and DB between them (the latencies of the
        # generic, DQS and DQ output primitives differ).
        self._stb_shift = CSRStorage(4, reset=5, description="STB/CS# write shift (UIs).")
        self._dqs_shift = CSRStorage(4, reset=4, description="DQS write shift (UIs).")
        self._db_shift  = CSRStorage(4, reset=1, description="DB write shift (UIs).")

        # Read: DQS read enable position (in sys_clk cycles after rddata_en, then in tCK), delay
        # (DQSBUF read clock selection) and burst detection.
        self._rd_en_sel     = CSRStorage(4, reset=4, description="DQS read enable position (sys_clk cycles).")
        self._rd_en_phase   = CSRStorage(2, reset=1, description="DQS read enable position (tCK).")
        self._rdly_dq_rst   = CSR()
        self._rdly_dq_inc   = CSR()
        self._burstdet_clr  = CSR()
        self._burstdet_seen = CSRStatus(2)
        self._datavalid_cnt = CSRStatus(8, description="DATAVALID cycles (first DQSBUF) since burstdet_clr.")

        kwargs.update(dict(
            write_ser_latency = 1, # ODDRX4.
            read_des_latency  = 6, # IDDRX4DQ, DQSBUF FIFO and DATAVALID capture (with margin).
            phytype           = self.__class__.__name__,
        ))

        if not isinstance(kwargs["pads"], RPCPads):
            kwargs["pads"] = NXRPCPads(kwargs["pads"])

        super().__init__(**kwargs)

        self.eclk = eclk

        self.settings.delays        = 16 # DQSBUF read clock selections.
        self.settings.read_leveling = True

        # STB/CS# static delay: 90 degrees (a quarter of tCK), limited to the delay line.
        if stb_delay is None:
            stb_delay = min(round(self.tck/4/self.delay_tap), self.delay_taps - 1)
        assert 0 <= stb_delay < self.delay_taps
        self.stb_delay = stb_delay

        # Init (DDRDLL/DQSBUF/ECLK sequencing).
        self.submodules.init = NexusDDRPHYInit(eclk=eclk)

        # DQSBUFs (one per DQS, shared with the DB bits it strobes).
        self.dqs_re  = dqs_re = Signal(4) # One bit per tCK.
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
            self.sync += [
                If(self.get_rst(i, self._rdly_dq_rst.wr_stb), rdly.eq(0)),
                If(self.get_inc(i, self._rdly_dq_inc.wr_stb), rdly.eq(rdly + 1)),
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
                i_RST        = ResetSignal("sys"),
                i_RSTSMCNT   = ResetSignal("sys"),
                i_SCLK       = ClockSignal("sys"),
                i_ECLKIN     = ClockSignal(eclk),
                i_SELCLK     = 0,
                i_DLLCODE    = self.init.delay,
                i_PAUSE      = self.init.pause | self._dly_sel.storage[i],

                # Control (LOADNs asserted to use the DDRDLL code).
                i_RDLOADN    = self.init.loadn,
                i_READMOVE   = self.init.move,
                i_RDDIR      = 0,
                i_WRLOAD_N   = self.init.loadn,
                i_WRMOVE     = self.init.move,
                i_WRDIR      = 0,
                i_WRLVLOAD_N = self.init.loadn,
                i_WRLVMOVE   = self.init.move,
                i_WRLVDIR    = 0,

                # Reads (generate the shifted DQS clock for reads).
                i_READ        = dqs_re,
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

    def write_shift(self, i, shift):
        shifter = _NXRPCPHYShift(i, shift)
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
            i_RST  = ResetSignal("sys"),
            i_SCLK = ClockSignal("sys"),
            i_ECLK = ClockSignal(self.eclk),
            **{f"i_D{n}": din[n] for n in range(8)},
            o_Q    = dout,
        )

    def delayb(self, din, dout, delay):
        self.specials += Instance("DELAYB",
            p_DEL_VALUE    = str(delay),
            p_COARSE_DELAY = "0NS",
            i_A            = din,
            o_Z            = dout,
        )

    # I/O implementation ---------------------------------------------------------------------------

    def do_clock_serialization(self, clk_1ck_out, clk_p, clk_n):
        # Pseudo-differential output on clk_p (clk_n from the IO standard), no delay supported.
        self.oddrx4(din=clk_1ck_out, dout=clk_p)

    def do_stb_serialization(self, stb_1ck_out, stb):
        # STB idles high (also on the STB pins of the unused ranks).
        stb_1ck = self.write_shift(~stb_1ck_out, self._stb_shift.storage)
        for i in range(len(stb)):
            stb_o = Signal()
            self.oddrx4(din=~stb_1ck if i == 0 else Replicate(1, 8), dout=stb_o)
            self.delayb(din=stb_o, dout=stb[i], delay=self.stb_delay)

    def do_cs_serialization(self, cs_n_1ck_out, cs_n):
        # CS# idles high (also on the CS# pins of the unused ranks).
        cs_n_1ck = self.write_shift(~cs_n_1ck_out, self._stb_shift.storage)
        for i in range(len(cs_n)):
            cs_n_o = Signal()
            self.oddrx4(din=~cs_n_1ck if i == 0 else Replicate(1, 8), dout=cs_n_o)
            self.delayb(din=cs_n_o, dout=cs_n[i], delay=self.stb_delay)

    def do_dqs_serialization(self, dqs_1ck_out, dqs_1ck_in, dqs_oe, dqs_p, dqs_n):
        dqs_1ck = self.write_shift(dqs_1ck_out, self._dqs_shift.storage)
        dqs_t   = self.write_shift_oe(dqs_oe,   self._dqs_shift.storage)
        for i in range(len(dqs_p)):
            dqs_o    = Signal()
            dqs_oe_n = Signal()
            self.specials += [
                Instance("ODDRX4DQS",
                    i_RST  = ResetSignal("sys"),
                    i_SCLK = ClockSignal("sys"),
                    i_ECLK = ClockSignal(self.eclk),
                    i_DQSW = self.dqsw[i],
                    **{f"i_D{n}": dqs_1ck[n] for n in range(8)},
                    o_Q    = dqs_o,
                ),
                Instance("TSHX4DQS",
                    i_RST  = ResetSignal("sys"),
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
        # (in sys_clk cycles then in tCK).
        taps   = [self.rddata_en[n] if n < len(self.rddata_en.sr) else 0 for n in range(16 + 1)]
        dqs_re = Signal()
        self.sync += dqs_re.eq(Array([taps[n] | taps[n + 1] for n in range(16)])[self._rd_en_sel.storage])
        self.comb += self.dqs_re.eq(self.write_shift(Replicate(dqs_re, 4), self._rd_en_phase.storage))

        datavalid_d = Signal(len(self.datavalid))
        self.sync += datavalid_d.eq(self.datavalid)
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
                    i_RST     = ResetSignal("sys"),
                    i_SCLK    = ClockSignal("sys"),
                    i_ECLK    = ClockSignal(self.eclk),
                    i_DQSW270 = self.dqsw270[byte],
                    **{f"i_D{n}": db_1ck[n] for n in range(8)},
                    o_Q       = db_o,
                ),
                Instance("TSHX4DQ",
                    i_RST     = ResetSignal("sys"),
                    i_SCLK    = ClockSignal("sys"),
                    i_ECLK    = ClockSignal(self.eclk),
                    i_DQSW270 = self.dqsw270[byte],
                    **{f"i_T{n}": db_t[n] for n in range(4)},
                    o_Q       = db_oe_n,
                ),
                Tristate(db[i], db_o, ~db_oe_n, db_i),

                # Read path.
                Instance("IDDRX4DQ",
                    i_RST     = ResetSignal("sys"),
                    i_SCLK    = ClockSignal("sys"),
                    i_ECLK    = ClockSignal(self.eclk),
                    i_DQSR90  = self.dqsr90[byte],
                    **{f"i_RDPNTR{n}": self.rdpntr[byte][n] for n in range(3)},
                    **{f"i_WRPNTR{n}": self.wrpntr[byte][n] for n in range(3)},
                    i_D       = db_i,
                    **{f"o_Q{n}": db_i_1ck[n] for n in range(8)},
                ),
            ]
            # The burst comes over the two sys_clk cycles flagged by DATAVALID: hold it and present
            # it to the deserializer of the BasePHY (which runs later, at a fixed latency).
            db_i_2ck = Signal(16)
            self.sync += If(self._burstdet_clr.wr_stb,
                db_i_2ck.eq(0), # Debug: no stale data after a clear.
            ).Elif(self.datavalid[byte],
                If(datavalid_d[byte],
                    db_i_2ck[8:].eq(db_i_1ck),
                ).Else(
                    db_i_2ck[:8].eq(db_i_1ck),
                )
            )
            self.comb += If(self.dq_in_cnt,
                db_1ck_in[i].eq(db_i_2ck[8:]),
            ).Else(
                db_1ck_in[i].eq(db_i_2ck[:8]),
            )
