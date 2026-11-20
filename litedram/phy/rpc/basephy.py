#
# This file is part of LiteDRAM.
#
# Copyright (c) 2020-2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from math import ceil
from operator import and_

from migen import *

from litex.gen.genlib.misc import WaitTimer

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage

from litedram.common import *
from litedram.phy.utils import chunks, bitpattern
from litedram.phy.dfi import Interface as DFIInterface
from litedram.phy.rpc.commands import DFIAdapter


class ShiftRegister(Module):
    def __init__(self, n, i=None):
        if i is None:
            i = Signal()
        assert len(i) == 1

        self.i = i
        self.sr = sr = Signal(n)
        last = Signal.like(sr)

        self.comb += sr.eq(Cat(i, last))
        self.sync += last.eq(sr)

    def __getitem__(self, key):
        return self.sr[key]


class RPCPads:
    _layout = [
        ("clk_p",  1),
        ("clk_n",  1),
        ("cs_n",   1),  # one per rank
        ("dqs_p",  1),  # may be 2 (hardware option; 2-bit DQS strobes DB by bytes: [0:7], [8:15])
        ("dqs_n",  1),  # may be 2
        ("stb",    1),  # one per rank
        ("db",    16),
    ]

    def __init__(self, pads):
        self.map(pads)
        for pad, width in self._layout:
            assert len(getattr(self, pad)) >= width, \
                "Pad {} has width {} < {}".format(pad, len(getattr(self, pad)), width)

    # reimplement if a specific mapping is needed
    def map(self, pads):
        for pad, _ in self._layout:
            setattr(self, pad, getattr(pads, pad))


class BasePHY(Module, AutoCSR):
    def __init__(self, pads, sys_clk_freq, write_ser_latency, read_des_latency, phytype, with_bitslip=True, nranks=1):
        # TODO: pads groups for multiple chips
        #  pads = PHYPadsCombiner(pads)
        if not isinstance(pads, RPCPads):
            pads = RPCPads(pads)
        self.pads = pads

        self.memtype     = memtype     = "RPC"
        # Ranks: DRAMs sharing CLK/DQS/DB, each with its STB and CS#. The first nranks pads are
        # used; the DRAMs of the others only get the reset sequence, then their STB/CS# are held
        # high (a DRAM that was configured before, ex by another design, and is left alone can
        # disturb the bus: after a reset its outputs are open until a MRS).
        assert 1 <= nranks <= min(len(pads.stb), len(pads.cs_n))
        self.nranks      = nranks
        self.databits    = databits    = 16
        self.addressbits = addressbits = 12
        self.bankbits    = bankbits    = 2
        self.nphases     = nphases     = 4
        self.tck         = tck         = 1 / (nphases*sys_clk_freq)

        # CSRs -------------------------------------------------------------------------------------
        bitslip_cycles = 1
        self._rst                 = CSRStorage()
        self._dly_sel             = CSRStorage(databits//8)
        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        self._reset_done = CSRStatus()
        self._init_done  = CSRStatus()
        self._reset_fsm  = CSR()

        self._burst_stop = CSRStorage(reset=1)

        if nranks > 1:
            self._rdrank = CSRStorage(max(1, log2_int(nranks)), description=
                "Rank that answers the reads sent to several ranks (commands from the software): "
                "only one DRAM can drive DQS/DB.")
            self._cs_all = CSRStorage(description=
                "Keep CS# of all the ranks low (debug), instead of only the ranks of the last command.")

        # PHY settings -----------------------------------------------------------------------------
        def get_cl(tck):
            # FIXME: for testing it's easier to use CL=8; read/write will be on phase 3; max sys_clk_freq=100e6
            return 8
            # tck is for DDR frequency
            f_to_cl = OrderedDict()
            f_to_cl[533e6]  =  3
            f_to_cl[800e6]  =  8
            f_to_cl[1200e6] =  8
            f_to_cl[1333e6] = 10
            f_to_cl[1600e6] = 11
            f_to_cl[1866e6] = 13
            for f, cl in f_to_cl.items():
                if tck >= 2/f:
                    return cl
            raise ValueError(tck)

        # RPC always has AL=1 and both read and write latencies are equal: RL=WL=AL+CL
        al = 1
        cwl = cl = get_cl(tck) + al

        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        rdphase = get_sys_phase(nphases, cl_sys_latency, cl)
        wrphase = get_sys_phase(nphases, cwl_sys_latency, cwl)

        # Read latency
        db_cmd_dly   = 2  # (need 1 cycle to insert STB preamble + 1 more to always meet tCSS)
        cmd_ser_dly  = write_ser_latency
        read_mux_dly = 1
        bitslip_dly  = bitslip_cycles
        # Time until first data is available on DB
        read_db_dly = db_cmd_dly + cmd_ser_dly + cl_sys_latency
        # Time until data is deserialized (data present on 1ck signal)
        read_db_des_dly = read_db_dly + read_des_latency
        # Time until data is set on DFI (+1 because all data is present only on 2nd cycle)
        read_dfi_dly = read_mux_dly + bitslip_dly + 1
        # Final latency
        read_latency = read_db_des_dly + read_dfi_dly

        # Write latency for the controller. We must send 1 cycles of data mask before the
        # data, and we serialize data over 2 sysclk cycles due to minimal BL=16, so we
        # are writing in the 2 cycles following the cycle when we obtain data on DFI.
        # Other PHYs can send everything in 1 sysclk. Because of this spcific delay, we
        # have to increate tWR in the RPC SDRModule definition to meet tWR requirements.
        # +1 cycle needed to insert CS before command
        write_latency = cwl_sys_latency + 1

        self.settings = PhySettings(
            phytype       = phytype,
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = 4*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = rdphase,
            wrphase       = wrphase,
            cl            = cl,
            cwl           = cwl,
            read_latency  = read_latency,
            write_latency = write_latency,
            bitslips      = bitslip_cycles*2*2*nphases,
        )

        # DFI Interface ----------------------------------------------------------------------------
        # minimal BL=16, which gives 16*16=256 bits; with 4 phases we need 16/4=4 data widths
        dfi_params = dict(addressbits=addressbits, bankbits=bankbits, nranks=nranks,
                          databits=4*databits, nphases=nphases)

        # Register DFI history (from newest to oldest), as we need to operate on 3 subsequent cycles
        # hist[0] = dfi[N], hist[1] = dfi[N-1], ...
        self.dfi = dfi = DFIInterface(**dfi_params)
        dfi_hist = [dfi, DFIInterface(**dfi_params), DFIInterface(**dfi_params)]
        self.sync += dfi_hist[0].connect(dfi_hist[1], omit={"rddata", "rddata_valid"})
        self.sync += dfi_hist[1].connect(dfi_hist[2], omit={"rddata", "rddata_valid"})

        # Serialization ----------------------------------------------------------------------------
        # We have the following signals that have to be serialized:
        # - CLK (O)  - full-rate clock
        # - CS  (O)  - chip select
        # - STB (O)  - serial commands, serial preamble
        # - DB  (IO) - transmits data in/out, data mask, parallel commands
        # - DQS (IO) - strobe for commands/data/mask on DB pins
        # DQS is edge-aligned to CLK, while DB and STB are center-aligned to CLK (phase = -90).
        # Sending a parallel command (on DB pins):
        #  CLK: ____----____----____----____----____----____
        #  STB: ----------________________------------------
        #  DQS: ....................----____----____........
        #  DB:  ..........................PPPPnnnn..........
        # The signals prepared by BasePHY will all be phase-aligned. The concrete PHY should shift
        # them so that DB/STB/CS are delayed by 90 degrees in relation to CLK/DQS.

        # Signal values (de)serialized during 1 sysclk.
        # These signals must be populated in specific PHY implementations.
        self.clk_1ck_out  = clk_1ck_out  = Signal(2*nphases)
        self.stb_1ck_out  = stb_1ck_out  = [Signal(2*nphases, name=f"stb{r}_1ck_out")  for r in range(nranks)]
        self.cs_n_1ck_out = cs_n_1ck_out = [Signal(2*nphases, name=f"cs_n{r}_1ck_out") for r in range(nranks)]
        # Unused ranks.
        self.stb_park_1ck_out  = stb_park_1ck_out  = Signal(2*nphases, reset=2**(2*nphases) - 1)
        self.cs_n_park_1ck_out = cs_n_park_1ck_out = Signal(2*nphases, reset=2**(2*nphases) - 1)

        self.dqs_1ck_out = dqs_1ck_out = Signal(2*nphases)
        self.dqs_1ck_in  = dqs_1ck_in  = Signal(2*nphases)
        self.dqs_oe      = dqs_oe      = Signal()

        self.db_1ck_out  = db_1ck_out  = [Signal(2*nphases) for _ in range(databits)]
        self.db_1ck_in   = db_1ck_in   = [Signal(2*nphases) for _ in range(databits)]
        self.db_oe       = db_oe       = Signal()

        # Clocks -----------------------------------------------------------------------------------
        self.comb += clk_1ck_out.eq(bitpattern("-_-_-_-_"))

        # DB muxing --------------------------------------------------------------------------------
        # Commands allowed by FSM
        cmd_valid = Signal()

        # Muxed cmd/data/mask
        db_1ck_data = [Signal(2*nphases) for _ in range(databits)]
        db_1ck_mask = [Signal(2*nphases) for _ in range(databits)]
        db_1ck_cmd  = [Signal(2*nphases) for _ in range(databits)]
        dq_data_en  = Signal()
        dq_mask_en  = Signal()
        dq_cmd_en   = Signal()
        dq_read_stb = Signal()

        # Output enable when writing cmd/data/mask
        # Mask is being send during negative half of sysclk
        self.comb += db_oe.eq(cmd_valid & (dq_data_en | dq_mask_en | dq_cmd_en))

        # Mux between cmd/data/mask
        for i in range(databits):
            self.comb += \
                If(dq_data_en,
                    db_1ck_out[i].eq(db_1ck_data[i])
                ).Elif(dq_mask_en,
                    db_1ck_out[i].eq(db_1ck_mask[i])
                ).Else(
                    db_1ck_out[i].eq(db_1ck_cmd[i])
                )

        # Parallel commands ------------------------------------------------------------------------
        # We need to insert 2 full-clk cycles of STB=0 before any command, to mark the beginning of
        # Request Packet. For that reason we use the previous values of DFI commands. To always be
        # able to meet tCSS, we have to add a delay of 1 more sysclk.
        # list from oldest to newest: dfi[N-1][p0], dfi[N-1][p1], ..., dfi[N][p0], dfi[N][p1], ...
        dfi_adapters = []
        # Ranks addressed by each command (cs_n of DFI). A read sent to several ranks (software
        # commands are sent to all the ranks) only goes to the rank of the rdrank CSR: the DRAMs
        # share DQS/DB.
        rank_sel = []
        for phase in dfi_hist[2].phases + dfi_hist[1].phases + dfi_hist[0].phases:
            adapter = DFIAdapter(phase)
            self.submodules += adapter
            dfi_adapters.append(adapter)
            sel = Signal(nranks, reset=2**nranks - 1)
            rank_sel.append(sel)
            if nranks > 1:
                cs = Signal(nranks)
                self.comb += [
                    cs.eq(~phase.cs_n),
                    sel.eq(cs),
                    If(adapter._is_cmd("RD") & ((cs & (cs - 1)) != 0),
                        Case(self._rdrank.storage, {r: sel.eq(1 << r) for r in range(nranks)})
                    )
                ]
            self.comb += [
                # We always send one WORD, which consists of 32 bytes.
                adapter.bc.eq(0),
                # Always use fast refresh (equivalent to auto refresh) instead of low-power refresh
                # (equivalent to self refresh).
                adapter.ref_op.eq(adapter.REF_OP["FST"]),
            ]

        # Address Streaming -------------------------------------------------------------------------
        # A read/write Request Packet is followed by Serial Packets on STB (one per 8 tCK = 2
        # sys_clk, the first one starts with the Request Packet). A Serial Packet can hold the next
        # read/write (any bank/column of an open row): its data then directly follow the data of
        # the previous WORD, without the Request Packet, latency and tBESL of a new burst. The PHY
        # uses this for a read/write that comes exactly 2 sys_clk after a read/write of the same
        # type (the controller only does this with RPC, see the Multiplexer), and stops the burst
        # (Burst Stop Serial Packet) when no such command follows.
        # The 2 sys_clk of command history give the look-ahead: when a command is serialized
        # (dfi_hist[2]), the next one of the stream is already there (dfi_hist[0]).
        assert rdphase == wrphase
        rwphase  = rdphase
        rw_types = ["RD", "WR"]
        rw_new   = {t: dfi_adapters[2*nphases + rwphase].is_cmd(t) for t in rw_types}
        rw_d     = {t: [Signal(name=f"rw_{t.lower()}_d{n}") for n in range(2)] for t in rw_types}
        for t in rw_types:
            self.sync += [rw_d[t][0].eq(rw_new[t]), rw_d[t][1].eq(rw_d[t][0])]
        # A stream stays on its rank (the STB of each rank has its own Serial Packets).
        rw_rank   = rank_sel[2*nphases + rwphase]
        rw_rank_d = [Signal(nranks, name=f"rw_rank_d{n}") for n in range(2)]
        self.sync += [rw_rank_d[0].eq(rw_rank), rw_rank_d[1].eq(rw_rank_d[0])]
        # stream[n]: the read/write of dfi_hist[n] continues a burst (no Request Packet).
        self.stream = stream = [Signal(name=f"stream{n}") for n in range(3)]
        self.comb += stream[0].eq(reduce(or_, [rw_new[t] & rw_d[t][1] for t in rw_types]) & (rw_rank == rw_rank_d[1]))
        self.sync += [stream[1].eq(stream[0]), stream[2].eq(stream[1])]
        # Request Packets: all the commands but the ones of a stream.
        pcmd_valid = []
        for n, adapter in enumerate(dfi_adapters):
            if n%nphases == rwphase:
                pcmd_valid.append(adapter.cmd_valid & ~stream[2 - n//nphases])
            else:
                pcmd_valid.append(adapter.cmd_valid)

        # Serialize commands to DB pins
        for i in range(databits):
            # A list of differential DB values using previous DFI coomand:
            # db_p[p][i], db_n[p][i], db_p[p+1][i], db_n[p+1][i], ...
            bits = [db for a in dfi_adapters[:nphases] for db in [a.db_p[i], a.db_n[i]]]
            self.comb += db_1ck_cmd[i].eq(Cat(*bits))

        # Commands go on the 2nd cycle, so use previous DFI
        self.comb += dq_cmd_en.eq(reduce(or_, pcmd_valid[:nphases]))

        # Power Up Reset ---------------------------------------------------------------------------
        # During Power Up, after stabilizing clocks, Power Up Reset must be done. It consists of a
        # a Parallel Reset followed by two Serial Resets (2x8=16 full-rate cycles = 4 sys cycles).
        # We use an FSM to make sure that we pass only the commands from the controller that are
        # supported in the current state.
        t_reset          = 5e-6
        t_zqcinit        = 1e-6
        serial_reset_len = 4

        stb_reset_seq      = Signal()
        serial_reset_count = Signal(max=serial_reset_len + 1)

        # prolong the cmd_valid for the cmd latency (length of history)
        self.submodules.cmd_valid_sr = ShiftRegister(len(dfi_adapters) // nphases)
        self.comb += cmd_valid.eq(reduce(or_, self.cmd_valid_sr))

        self.submodules.reset_timer = WaitTimer(ceil(t_reset * sys_clk_freq))
        self.submodules.zqcinit_timer = WaitTimer(ceil(t_zqcinit * sys_clk_freq))

        self.submodules.reset_fsm = fsm = FSM()
        fsm.act("IDLE",
            NextValue(serial_reset_count, 0),
            NextValue(self._reset_done.status, 0),
            self.cmd_valid_sr.i.eq(dfi_adapters[2*nphases+0].is_cmd("RESET")),
            If(self.cmd_valid_sr.i,
                NextState("RESET_RECEIVED")
            ),
        )
        fsm.act("RESET_RECEIVED",
            NextState("SERIAL_RESET")
        )
        fsm.act("SERIAL_RESET",
            self.reset_timer.wait.eq(1),
            If(serial_reset_count != serial_reset_len,
               stb_reset_seq.eq(1),
               NextValue(serial_reset_count, serial_reset_count + 1),
            ),
            If(self.reset_timer.done,
                NextValue(self._reset_done.status, 1),
                NextState("RESET_DONE")
            )
        )
        fsm.act("RESET_DONE",
            self.cmd_valid_sr.i.eq(dfi_adapters[2*nphases+0].is_cmd(["PRE", "MRS", "ZQC_INIT"])),
            If(dfi_adapters[2*nphases+0].is_cmd("ZQC_INIT"),
                NextState("ZQC_INIT")
            )
        )
        fsm.act("ZQC_INIT",
            self.zqcinit_timer.wait.eq(1),
            If(self.zqcinit_timer.done,
                NextState("READY")
            )
        )
        fsm.act("READY",
            self._init_done.status.eq(1),
            self.cmd_valid_sr.i.eq(1),
            If(dfi_adapters[2*nphases+0].is_cmd("UTR") & (dfi_adapters[2*nphases+0].utr_en == 1),
                NextState("UTR_MODE")
            ),
            If(self._reset_fsm.wr_stb,
                NextState("IDLE")
            ),
            # A new initialization (ex sdram_init from the BIOS): do the reset sequence again,
            # with CS# released first as after reset_fsm (on hardware, a reset with CS# kept low
            # left the DRAM with rare read/write errors).
            If(dfi_adapters[2*nphases+0].is_cmd("RESET"),
                NextValue(serial_reset_count, 0),
                NextValue(self._reset_done.status, 0),
                NextState("CS_RELEASE")
            )
        )
        cs_release = Signal()
        fsm.act("CS_RELEASE",
            cs_release.eq(1),
            self.reset_timer.wait.eq(1),
            If(self.reset_timer.done,
                NextState("CS_HOLD")
            )
        )
        fsm.act("CS_HOLD",
            self.zqcinit_timer.wait.eq(1),
            If(self.zqcinit_timer.done,
                NextState("RESET_RECEIVED")
            )
        )
        fsm.act("UTR_MODE",
            self._init_done.status.eq(1),
            self.cmd_valid_sr.i.eq(reduce(or_, [dfi_adapters[p].is_cmd(["UTR", "RD"])
                                                for p in [2*nphases, 2*nphases+self.settings.rdphase]])),
            If(dfi_adapters[2*nphases+0].is_cmd("UTR") & (dfi_adapters[2*nphases+0].utr_en == 0),
                NextState("READY")
            )
        )

        # STB --------------------------------------------------------------------------------------
        # Currently not sending any serial commands, but the STB pin must be held low for 2 full
        # rate cycles before writing a parallel command to activate the DRAM.
        stb_bits = [[] for r in range(nranks)]

        # Serial Packet (16 bits, 2 per tCK) that follows each read/write: it starts with the
        # command (on rwphase, the last phase) and ends 2 sys_clk later.
        #   Read/Write : 0 1 BA0 BA1 RD CA4 CA5 CA6 CA7 CA8 CA9 x x x x x  (next command of the stream)
        #   Burst Stop : 0 0 0   1   0  0   x ...                          (no next command)
        assert rwphase == nphases - 1
        cur   = dfi_adapters[0*nphases + rwphase] # Command being serialized.
        nxt   = dfi_adapters[1*nphases + rwphase] # Next command of the stream, 1 sys_clk before it is serialized.
        rw_s  = Signal() # Read/write being serialized.
        rw_s1 = Signal() # 1 sys_clk later.
        rw_s2 = Signal() # 2 sys_clk later.
        self.comb += rw_s.eq(cur.cmd_valid & cur.is_cmd(rw_types) & cmd_valid)
        self.sync += [rw_s1.eq(rw_s), rw_s2.eq(rw_s1)]
        nxt_dfi = dfi_hist[1].phases[rwphase]
        cur_dfi = dfi_hist[2].phases[rwphase]
        serial  = Signal(2*nphases, reset=2**(2*nphases) - 1)
        self.comb += [
            serial.eq(2**(2*nphases) - 1),
            # Bits 0-1, with the command.
            If(rw_s,
                serial[2*rwphase + 0].eq(0),
                serial[2*rwphase + 1].eq(stream[0]),
            ),
            # Bits 2-9.
            If(rw_s1,
                If(stream[1],
                    serial[0].eq(nxt_dfi.bank[0]),
                    serial[1].eq(nxt_dfi.bank[1]),
                    serial[2].eq(nxt.is_cmd("RD")),
                    serial[3].eq(nxt_dfi.address[4]),
                    serial[4].eq(nxt_dfi.address[5]),
                    serial[5].eq(nxt_dfi.address[6]),
                    serial[6].eq(nxt_dfi.address[7]),
                    serial[7].eq(nxt_dfi.address[8]),
                ).Elif(self._burst_stop.storage,
                    serial[0].eq(0),
                    serial[1].eq(1),
                    serial[2].eq(0),
                    serial[3].eq(0),
                ).Else(
                    # Without Burst Stop: NOP (the burst ends with its burst count).
                    serial[0].eq(1),
                    serial[1].eq(1),
                )
            ),
            # Bit 10.
            If(rw_s2 & stream[2],
                serial[0].eq(cur_dfi.address[9]),
            ),
        ]
        # Without Burst Stop, the first bits of the packet are those of a NOP too.
        nop_bits = Signal()
        self.comb += nop_bits.eq(rw_s & ~stream[0] & ~self._burst_stop.storage)
        # Rank of the Serial Packet: the one of its read/write (the STB of the others stays high).
        serial_rank   = Signal(nranks)
        serial_rank_r = Signal(nranks)
        self.sync += If(rw_s, serial_rank_r.eq(rank_sel[rwphase]))
        self.comb += If(rw_s, serial_rank.eq(rank_sel[rwphase])).Else(serial_rank.eq(serial_rank_r))

        for r, p in [(r, p) for r in range(nranks) for p in range(nphases)]:
            # Use cmd from current and prev cycle, depending on which phase the command appears on
            preamble = ((pcmd_valid[p+2] & rank_sel[p+2][r]) | (pcmd_valid[p+1] & rank_sel[p+1][r])) & cmd_valid

            # We use STB to start parallel commands, for the serial reset, for the Serial Packets
            # of the reads/writes and to send NOPs. NOP is indicated by the first two bits being
            # high (0b11, and other as "don't care"), so we can simply hold STB high all the time
            # and reset is zeros for 8 cycles (1 sysclk).
            stb_bits[r] += [
                ~(preamble | stb_reset_seq) & (serial[2*p + 0] | nop_bits | ~serial_rank[r]),
                ~(preamble | stb_reset_seq) & (serial[2*p + 1] | nop_bits | ~serial_rank[r]),
            ]

        self.comb += [stb_1ck_out[r].eq(Cat(*stb_bits[r])) for r in range(nranks)]

        # Unused ranks: STB of the reset sequence only.
        stb_park_bits = []
        for p in range(nphases):
            preamble = reduce(or_, [pcmd_valid[n] & dfi_adapters[n]._is_cmd("RESET") for n in [p+2, p+1]]) & cmd_valid
            stb_park_bits += 2*[~(preamble | stb_reset_seq)]
        self.comb += stb_park_1ck_out.eq(Cat(*stb_park_bits))

        # Chip Select ------------------------------------------------------------------------------
        # RPC has quite high required time of CS# low before sending a command (tCSS), this means
        # that we would need 1 more cmd_latency to support it for all standard frequencies. To meet
        # tCSH we hold CS# low 1 cycle after each command (and for writes until the burst ends).
        tCSS = 10e-9
        tCSH =  5e-9
        # CS# is held for 2 sysclks before any command, and 1 sysclk after any command
        assert 2 * 1/sys_clk_freq >= tCSS, "tCSS not met for commands on phase 0"
        assert 1 * 1/sys_clk_freq >= tCSH, "tCSH not met for commands on phase 3"

        cs         = Signal()
        cs_burst_hold = Signal()
        self.submodules.cs_hold = ShiftRegister(2)

        # FIXME: currently we hold CS low constantly to avoid problems with signal integrity on our board
        # lock CS when DFI sends cs_n=0 only on phase 0 (avoids start condition problems)
        cs_lock = Signal()
        cs_lock_cond = reduce(and_, [dfi_hist[0].phases[p].cs_n == 2**nranks - 1 for p in range(1, nphases)])
        cs_lock_cond = cs_lock_cond & (dfi_hist[0].p0.cs_n == 0)
        self.sync += If(cs_lock_cond, cs_lock.eq(1)).Elif(self._reset_fsm.wr_stb, cs_lock.eq(0))

        _any_cmd_valid = reduce(or_, (a.cmd_valid for a in dfi_adapters))
        self.comb += [
            # self.cs_hold.i.eq(cmd_valid & (_any_cmd_valid | cs_burst_hold)),
            # cs.eq(reduce(or_, self.cs_hold.sr)),
            # cs_n_1ck_out.eq(Replicate(~cs, len(cs_n_1ck_out))),
        ]
        # Ranks (see Multi Rank in the datasheet): CS# is low only on the ranks of the last
        # command (the others do not receive the DB/DQS traffic and do not terminate it). CS# of a
        # new rank goes low when its command is received (2 sys_clk of command history: at least 1
        # sys_clk + 2 tCK before its STB preamble, for tCSS), CS# of a rank that is left goes high
        # 1 sys_clk later (after the Request Packet of a command sent 3 sys_clk earlier, for tCSH;
        # the controller waits for the end of the bursts before a new Request Packet).
        cs_active = Signal(nranks, reset=2**nranks - 1)
        cs_new    = Signal(nranks)
        if nranks > 1:
            self.comb += cs_new.eq(reduce(or_, [
                Replicate(dfi_adapters[2*nphases + p].cmd_valid, nranks) & rank_sel[2*nphases + p]
                for p in range(nphases)]))
            self.sync += If(cs_new != 0, cs_active.eq(cs_new))
        for r in range(nranks):
            cs_rank = (cs_active[r] | cs_new[r] | self._cs_all.storage) if nranks > 1 else 1
            self.comb += cs_n_1ck_out[r].eq(Replicate(~(cs_lock & ~cs_release & cs_rank), 2*nphases))
        # Unused ranks: CS# low for the reset sequence only.
        in_reset = Signal()
        self.comb += [
            in_reset.eq(reduce(or_, [fsm.ongoing(state) for state in ["IDLE", "RESET_RECEIVED", "SERIAL_RESET", "CS_HOLD"]])),
            cs_n_park_1ck_out.eq(Replicate(~(cs_lock & ~cs_release & in_reset), 2*nphases)),
        ]

        # Data IN ----------------------------------------------------------------------------------
        # Synchronize the deserializer because we deserialize over 2 cycles.
        dq_in_cnt = Signal()
        self.sync += If(dq_read_stb, dq_in_cnt.eq(~dq_in_cnt)).Else(dq_in_cnt.eq(0))

        # Deserialize read data
        # sys_clk:    ------------____________------------____________
        # sysx4_clk:  ---___---___---___---___---___---___---___---___
        # DB num:     <0><1><2><3><4><5><6><7><8><9><a><b><c><d><e><f>
        for i in range(databits):
            # BL=16 -> 2ck
            n_1ck = 2*nphases
            rbits_2ck = Signal(2*n_1ck)
            rbits_1ck = Signal(n_1ck)

            self.comb += rbits_1ck.eq(db_1ck_in[i])
            self.sync += Case(dq_in_cnt, {
                0: rbits_2ck[:n_1ck].eq(rbits_1ck),
                1: rbits_2ck[n_1ck:].eq(rbits_1ck),
            })

            # Without bitslip (backends that get the burst already aligned), the bitslip CSRs are
            # free for another use by the backend.
            bs = BitSlip(len(rbits_2ck), cycles=bitslip_cycles,
                rst = self.get_rst(i//8, self._rdly_dq_bitslip_rst.wr_stb) if with_bitslip else 0,
                slp = self.get_inc(i//8, self._rdly_dq_bitslip.wr_stb)     if with_bitslip else 0,
            )
            self.submodules += bs
            self.comb += bs.i.eq(rbits_2ck)

            for p in range(nphases):
                self.comb += [
                    dfi.phases[p].rddata[i+0*databits].eq(bs.o[p*nphases+0]),
                    dfi.phases[p].rddata[i+1*databits].eq(bs.o[p*nphases+1]),
                    dfi.phases[p].rddata[i+2*databits].eq(bs.o[p*nphases+2]),
                    dfi.phases[p].rddata[i+3*databits].eq(bs.o[p*nphases+3]),
                ]

        # Data OUT ---------------------------------------------------------------------------------
        # TODO: add 1 to tWR bacause we need 2 cycles to send data from 1 cycle

        # Before sending the actual data we have to send 2 32-bit data masks (4 DDR cycles). In the
        # mask each 0 bit means "write byte" and 1 means "mask byte". The 1st 32-bits mask the first
        # data WORD (32 bytes), and the 2nd 32-bits mask the last data WORD of the burst. The masks
        # are only sent before the first WORD: the mask of the first WORD is sent twice (it is
        # also the last WORD without stream), so the next WORDs of a stream are either fully
        # written or get the mask of the first one (last WORD). The controller must then only
        # stream writes of full WORDs.
        #
        # Write data
        # DFI valid:  xxxxxxxxxxxxxxxxxx
        # sys_clk:    ------____________------------____________------------____________
        # sysx4_clk:  ---___---___---___---___---___---___---___---___---___---___---___
        # DB num:           <M><M><M><M><0><1><2><3><4><5><6><7><8><9><a><b><c><d><e><f>

        # Synchronize to 2 cycles, reset counting when dq_data_en turns high.
        db_cnt = Signal()
        self.sync += If(dq_data_en, db_cnt.eq(~db_cnt)).Else(db_cnt.eq(0))

        for i in range(databits):
            # Write data ---------------------------------------------------------------------------
            wbits = []
            for p in range(nphases):
                _dfi = dfi_hist[1] if p < nphases//2 else dfi_hist[2]
                wbits += [
                    _dfi.phases[p].wrdata[i+0*databits],
                    _dfi.phases[p].wrdata[i+1*databits],
                    _dfi.phases[p].wrdata[i+2*databits],
                    _dfi.phases[p].wrdata[i+3*databits],
                ]

            # Mux datas from 2 cycles to always serialize single cycle.
            wbits_2ck = [Cat(*wbits[:2*nphases]), Cat(*wbits[2*nphases:])]
            wbits_1ck = Signal(2*nphases)
            self.comb += wbits_1ck.eq(Array(wbits_2ck)[db_cnt])
            self.comb += db_1ck_data[i].eq(Cat(*wbits_1ck))

            # Data mask ----------------------------------------------------------------------------
            mask = [
                Constant(0),                                    # phase 0
                Constant(0),                                    # phase 0
                Constant(0),                                    # phase 1
                Constant(0),                                    # phase 1
                dfi_hist[0].phases[i//8 + 0].wrdata_mask[i%8],  # WL-2
                dfi_hist[0].phases[i//8 + 2].wrdata_mask[i%8],  # WL-2
                dfi_hist[0].phases[i//8 + 0].wrdata_mask[i%8],  # WL-1
                dfi_hist[0].phases[i//8 + 2].wrdata_mask[i%8],  # WL-1
            ]
            self.comb += db_1ck_mask[i].eq(Cat(*mask))

        # DQS --------------------------------------------------------------------------------------
        # Strobe pattern can go over 2 sysclk (do not count while transmitting mask)
        dqs_cnt = Signal()
        self.sync += If(dqs_oe & (~dq_mask_en), dqs_cnt.eq(~dqs_cnt)).Else(dqs_cnt.eq(0))

        pattern_2ck = [Signal(2*nphases), Signal(2*nphases)]
        self.comb += dqs_1ck_out.eq(Array(pattern_2ck)[dqs_cnt])

        # To avoid having to serialize dqs_oe, we serialize predefined pattern on dqs_out
        # All the patterns will be shifted back 90 degrees!
        data_pattern = [bitpattern("-_-_-_-_"), bitpattern("-_-_-_-_")]
        mask_pattern = [bitpattern("__-_-_-_"), bitpattern("-_-_-_-_")]
        phase_patterns = {
            0: [bitpattern("______-_"), bitpattern("-_______")],
            1: [bitpattern("________"), bitpattern("-_-_____")],
            2: [bitpattern("________"), bitpattern("__-_-___")],
            3: [bitpattern("________"), bitpattern("____-_-_")],
        }

        pattern_cases = \
            If(dq_mask_en,
                pattern_2ck[0].eq(mask_pattern[0]),
                pattern_2ck[1].eq(mask_pattern[1]),
            ).Elif(dq_data_en,
                pattern_2ck[0].eq(data_pattern[0]),
                pattern_2ck[1].eq(data_pattern[1]),
            ).Else(
                pattern_2ck[0].eq(0),
                pattern_2ck[1].eq(0),
            )
        any_phase_valid = 0
        for p in range(nphases):
            phase_valid = pcmd_valid[p] | pcmd_valid[nphases+p]
            pattern_cases = \
                If(phase_valid,
                    pattern_2ck[0].eq(phase_patterns[p][0]),
                    pattern_2ck[1].eq(phase_patterns[p][1]),
                ).Else(pattern_cases)
            any_phase_valid = any_phase_valid | phase_valid

        self.comb += pattern_cases
        self.comb += dqs_oe.eq(cmd_valid & (any_phase_valid | dq_mask_en | dq_data_en))

        # Read Control Path ------------------------------------------------------------------------
        # Creates a shift register of read commands coming from the DFI interface. This shift
        # register is used to indicate to the DFI interface that the read data is valid.
        self.submodules.rddata_en = rddata_en = ShiftRegister(self.settings.read_latency)
        self.comb += rddata_en.i.eq(dfi.phases[self.settings.rdphase].rddata_en)
        # -1 because of syncronious assignment
        self.sync += [phase.rddata_valid.eq(rddata_en[-1]) for phase in dfi.phases]
        # Strobe high when data from DRAM is available, before we can send it to DFI.
        self.sync += dq_read_stb.eq(rddata_en[read_db_des_dly-1] | rddata_en[read_db_des_dly-1 + 1])

        # Write Control Path -----------------------------------------------------------------------
        # Creates a shift register of write commands coming from the DFI interface. This shift
        # register is used to control DQ/DQS tristates.
        self.submodules.wrdata_en = wrdata_en = ShiftRegister(self.settings.write_latency + 2 + 1)
        self.comb += wrdata_en.i.eq(dfi.phases[self.settings.wrphase].wrdata_en & cmd_valid)
        # DQS Preamble and data mask are transmitted 1 cycle before data, then 2 cycles of data
        # (not for the next WORDs of a stream: their data directly follow the previous ones)
        self.submodules.wrdata_stream = wrdata_stream = ShiftRegister(self.settings.write_latency + 1)
        self.comb += wrdata_stream.i.eq(stream[0])
        self.comb += dq_mask_en.eq(wrdata_en[write_latency] & ~wrdata_stream[write_latency])
        self.comb += dq_data_en.eq(wrdata_en[write_latency + 1] | wrdata_en[write_latency + 2])
        # Hold CS# low until end of write burst (use a latch as there can only be 1 write at a time)

        cs_wr_hold = Signal()
        self.sync += If(wrdata_en[0], cs_wr_hold.eq(1)).Elif(wrdata_en[-1], cs_wr_hold.eq(0))
        cs_rd_hold = Signal()
        self.sync += If(rddata_en[0], cs_rd_hold.eq(1)).Elif(rddata_en[-1], cs_rd_hold.eq(0))
        self.comb += cs_burst_hold.eq(cs_wr_hold | cs_rd_hold)

        # Additional variables for LiteScope -------------------------------------------------------
        variables = ["dq_data_en", "dq_mask_en", "dq_cmd_en", "dq_read_stb", "dfi_adapters",
                     "dq_in_cnt", "db_cnt", "dqs_cnt", "rddata_en", "wrdata_en"]
        for v in variables:
            setattr(self, v, locals()[v])

    def get_rst(self, byte, rst):
        return (self._dly_sel.storage[byte] & rst) | self._rst.storage

    def get_inc(self, byte, inc):
        return self._dly_sel.storage[byte] & inc

    def do_finalize(self):
        self.do_clock_serialization(self.clk_1ck_out, self.pads.clk_p, self.pads.clk_n)
        # One STB and one CS# per rank (unused ranks: reset sequence only).
        for r in range(len(self.pads.stb)):
            self.do_stb_serialization(self.stb_1ck_out[r] if r < self.nranks else self.stb_park_1ck_out, self.pads.stb[r])
        self.do_dqs_serialization(self.dqs_1ck_out, self.dqs_1ck_in, self.dqs_oe,
                                  self.pads.dqs_p, self.pads.dqs_n)
        self.do_db_serialization(self.db_1ck_out, self.db_1ck_in, self.db_oe, self.pads.db)
        for r in range(len(self.pads.cs_n)):
            self.do_cs_serialization(self.cs_n_1ck_out[r] if r < self.nranks else self.cs_n_park_1ck_out, self.pads.cs_n[r])

    # I/O implementation ---------------------------------------------------------------------------

    def do_clock_serialization(self, clk_1ck_out, clk_p, clk_n):
        raise NotImplementedError("Serialize the full-rate clock with 90 deg phase delay")

    def do_stb_serialization(self, stb_1ck_out, stb):
        raise NotImplementedError("Serialize the STB line")

    def do_dqs_serialization(self, dqs_1ck_out, dqs_1ck_in, dqs_oe, dqs_p, dqs_n):
        raise NotImplementedError("Tristate and (de)serialize DQS with 90 deg phase delay")

    def do_db_serialization(self, db_1ck_out, db_1ck_in, db_oe, db):
        raise NotImplementedError("Tristate and (de)serialize DB")

    def do_cs_serialization(self, cs_n_1ck_out, cs_n):
        raise NotImplementedError("Serialize the chip select line (CS#)")
