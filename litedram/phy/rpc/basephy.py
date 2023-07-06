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
        ("cs_n",   1),
        ("dqs_p",  1),  # may be 2 (hardware option; 2-bit DQS strobes DB by bytes: [0:7], [8:15])
        ("dqs_n",  1),  # may be 2
        ("stb",    1),
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
    def __init__(self, pads, sys_clk_freq, write_ser_latency, read_des_latency, phytype):
        # TODO: pads groups for multiple chips
        #  pads = PHYPadsCombiner(pads)
        if not isinstance(pads, RPCPads):
            pads = RPCPads(pads)
        self.pads = pads

        self.memtype     = memtype     = "RPC"
        self.nranks      = nranks      = 1
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
        self.stb_1ck_out  = stb_1ck_out  = Signal(2*nphases)
        self.cs_n_1ck_out = cs_n_1ck_out = Signal(2*nphases)

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
        for phase in dfi_hist[2].phases + dfi_hist[1].phases + dfi_hist[0].phases:
            adapter = DFIAdapter(phase)
            self.submodules += adapter
            dfi_adapters.append(adapter)
            self.comb += [
                # We always send one WORD, which consists of 32 bytes.
                adapter.bc.eq(0),
                # Always use fast refresh (equivalent to auto refresh) instead of low-power refresh
                # (equivalent to self refresh).
                adapter.ref_op.eq(adapter.REF_OP["FST"]),
            ]

        # Serialize commands to DB pins
        for i in range(databits):
            # A list of differential DB values using previous DFI coomand:
            # db_p[p][i], db_n[p][i], db_p[p+1][i], db_n[p+1][i], ...
            bits = [db for a in dfi_adapters[:nphases] for db in [a.db_p[i], a.db_n[i]]]
            self.comb += db_1ck_cmd[i].eq(Cat(*bits))

        # Commands go on the 2nd cycle, so use previous DFI
        self.comb += dq_cmd_en.eq(reduce(or_, [a.cmd_valid for a in dfi_adapters[:nphases]]))

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
            If(self._reset_fsm.re,
                NextState("IDLE")
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
        stb_bits = []

        assert self.settings.rdphase == 3
        read_sent = [Signal(), Signal()]
        self.comb += read_sent[0].eq(dfi_adapters[3].cmd_valid & (dfi_adapters[3].is_cmd("RD") | dfi_adapters[3].is_cmd("WR")))
        self.sync += read_sent[1].eq(read_sent[0])

        for p in range(nphases):
            # Use cmd from current and prev cycle, depending on which phase the command appears on
            preamble = (dfi_adapters[p+2].cmd_valid | dfi_adapters[p+1].cmd_valid) & cmd_valid

            # force 000100xxxxxxxxxx after preamble to generate Burst Stop
            assert self.settings.rdphase == 3
            burst_stop = {
                0: [0, 0],
                1: [0, 1],
                2: [0, 0],
                3: [1, 1],
            }[(p+1)%4]
            read = read_sent[0] if p == 3 else read_sent[1]
            burst_stop_zero = [cmd_valid & read & (bs == 0) & self._burst_stop.storage
                               for bs in burst_stop]

            # We only want to use STB to start parallel commands, serial reset or to send NOPs. NOP
            # is indicated by the first two bits being high (0b11, and other as "don't care"), so
            # we can simply hold STB high all the time and reset is zeros for 8 cycles (1 sysclk).
            # stb_bits += 2 * [~(preamble | stb_reset_seq)]
            stb_bits += [
                ~(preamble | stb_reset_seq | burst_stop_zero[0]),
                ~(preamble | stb_reset_seq | burst_stop_zero[1]),
            ]

        self.comb += stb_1ck_out.eq(Cat(*stb_bits))

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
        cs_lock_cond = reduce(and_, [dfi_hist[0].phases[p].cs_n for p in range(1, nphases)])
        cs_lock_cond = cs_lock_cond & ~dfi_hist[0].p0.cs_n
        self.sync += If(cs_lock_cond, cs_lock.eq(1)).Elif(self._reset_fsm.re, cs_lock.eq(0))

        _any_cmd_valid = reduce(or_, (a.cmd_valid for a in dfi_adapters))
        self.comb += [
            # self.cs_hold.i.eq(cmd_valid & (_any_cmd_valid | cs_burst_hold)),
            # cs.eq(reduce(or_, self.cs_hold.sr)),
            # cs_n_1ck_out.eq(Replicate(~cs, len(cs_n_1ck_out))),
            cs_n_1ck_out.eq(Replicate(~cs_lock, len(cs_n_1ck_out))),
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

            bs = BitSlip(len(rbits_2ck), cycles=bitslip_cycles,
                rst = self.get_rst(i//8, self._rdly_dq_bitslip_rst.re),
                slp = self.get_inc(i//8, self._rdly_dq_bitslip.re),
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
        # data WORD (32 bytes), and the 2nd 32-bits mask the last data WORD. Because we always send
        # 1 WORD of data (BC=0), we don't care about the 2nd mask (can send 1).
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
                Constant(1),                                    # WL-1
                Constant(1),                                    # WL-1
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
            phase_valid = dfi_adapters[p].cmd_valid | dfi_adapters[nphases+p].cmd_valid
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
        self.comb += dq_mask_en.eq(wrdata_en[write_latency])
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
        self.do_stb_serialization(self.stb_1ck_out, self.pads.stb)
        self.do_dqs_serialization(self.dqs_1ck_out, self.dqs_1ck_in, self.dqs_oe,
                                  self.pads.dqs_p, self.pads.dqs_n)
        self.do_db_serialization(self.db_1ck_out, self.db_1ck_in, self.db_oe, self.pads.db)
        self.do_cs_serialization(self.cs_n_1ck_out, self.pads.cs_n)

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
