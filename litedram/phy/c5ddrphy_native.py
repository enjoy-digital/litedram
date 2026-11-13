#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

from migen import Array, Cat, ClockDomain, ClockDomainsRenamer, FSM, If, Instance, Memory, NextState, NextValue, Mux, Replicate, Signal
from migen.genlib.cdc import BusSynchronizer, MultiReg, PulseSynchronizer
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import LiteXModule
from litex.soc.interconnect.csr import CSR, CSRStatus, CSRStorage

from litedram.common import TappedDelayLine


class CycloneVDDR3Lane(LiteXModule):
    """DDR3 BL8 byte-lane PHY using Quartus ALTDQ_DQS2 I/O blocks.

    The surrounding PHY supplies AFI-shaped commands and the fixed-latency DFI
    return path. LiteDRAM firmware issues the DDR3 initialization sequence.
    """
    def __init__(self, *, with_trace=False, **ports):
        lanes = len(ports["io_mem_dq"]) // 8
        afi_clk = ports["o_afi_clk"]
        locked = Signal()
        mem_clk, mem_phy_clk, dq_clk, dll_clk, cmd_clk, afi_phy_clk = [Signal() for _ in range(6)]
        config_clk = Signal()
        delay = Signal(7)
        series, parallel = Signal(16), Signal(16)
        # DDR3B's fixed write, DQS gate, LFIFO and AFI capture timing.
        default_settings = 0x080d6731
        self._settings = CSRStorage(32, reset=default_settings,
            description="Write latency [2:0], bypass write slot shift [3], DQS gate delay [6:4], LFIFO latency [12:8], "
                        "LFIFO/VFIFO reset [14:13], bit 15 reserved, AFI read capture delay [20:16], trace index [24:21], write trigger [25], Shared read gate extension [26], request-derived read valid [27], bypass pad masking [28], invert DQS slot shift [29], disable dynamic OCT [30], trace ACT [31].")
        self._vfifo_increment = CSR()
        self._dqs_scan = CSRStorage(31, description="Scan payload [24:0], target [28:27] (0 DQS logic, 1 all DQ and DM, 2 all DQS pads, "
            "3 one lane's DQ and DM), lane index [29,26:25] for target 3, command toggle [30].")
        self._read_status = CSRStatus(32, description="Last captured four-byte AFI read word.")
        self._read_count = CSRStatus(16, description="Number of captured AFI read words.")
        if with_trace:
            self._trace_arm = CSR()
            self._trace_word = CSRStatus(32, description="Raw FIFO data at the selected trace cycle.")
            self._trace_flags = CSRStatus(5, description="Request, gate, raw valid, capture, trace complete.")
            self._trace_afi_write = CSRStatus(32, description="Write payload entering the lane.")
            self._trace_pad_write = CSRStatus(32, description="Write payload entering ALTDQ_DQS2.")
            self._trace_io_flags = CSRStatus(14, description="Write command, AFI OE, pad OE, DQS OE, DM, AFI read valid.")
            self._trace_command = CSRStatus(32, description="AFI CS, RAS, CAS, WE, CKE, ODT, banks and active-slot address.")

        # # #

        self.specials += [
            Instance("q_sys_smc_0_mem_if_ddr3_emif_0_pll0",
                i_global_reset_n=ports["i_global_reset_n"], i_pll_ref_clk=ports["i_pll_ref_clk"],
                o_afi_clk=afi_clk, o_pll_locked=locked, o_pll_mem_clk=mem_clk,
                o_pll_mem_phy_clk=mem_phy_clk, o_pll_write_clk=dq_clk,
                o_pll_write_clk_pre_phy_clk=dll_clk, o_pll_addr_cmd_clk=cmd_clk,
                o_afi_phy_clk=afi_phy_clk, o_pll_config_clk=config_clk),
            Instance("altera_mem_if_dll_cyclonev",
                p_DLL_DELAY_CTRL_WIDTH=7, p_DLL_OFFSET_CTRL_WIDTH=6, p_DELAY_BUFFER_MODE="HIGH",
                p_DELAY_CHAIN_LENGTH=Instance.PreformattedParam("8"), p_DLL_INPUT_FREQUENCY_PS_STR="3333 ps",
                i_clk=dll_clk, i_dll_pll_locked=locked, o_dll_delayctrl=delay),
            Instance("altera_mem_if_oct_cyclonev", p_OCT_TERM_CONTROL_WIDTH=16,
                i_oct_rzqin=ports["i_oct_rzqin"], o_seriesterminationcontrol=series,
                o_parallelterminationcontrol=parallel),
        ]

        # The DLL wrapper resets on PLL unlock and does not export DLL lock.
        # At 150 MHz, 2048 AFI clocks allow 4096 cycles of the 300 MHz DLL
        # reference before releasing the PHY and its controller.
        self.cd_dll_init = ClockDomain("dll_init")
        self.comb += self.cd_dll_init.clk.eq(afi_clk)
        self.specials += AsyncResetSynchronizer(self.cd_dll_init, ~locked)
        dll_init_cycles = Signal(12)
        rfifo_release = Signal()
        level_fifo_reset = Signal()
        level_vfifo_rephase = Signal()
        dll_ready = Signal()
        self.sync.dll_init += [
            If(~dll_ready, dll_init_cycles.eq(dll_init_cycles + 1)),
            If(dll_init_cycles == 2056, dll_ready.eq(1)),
            rfifo_release.eq(dll_init_cycles[-1] & ~level_fifo_reset),
        ]
        # Release the hard FIFO eight AFI cycles before allowing DDR
        # commands. Returning DQS is idle until the first read.
        # These primitive FIFO reset inputs are active high despite their names.
        rfifo_reset = ~(locked & ~self.cd_dll_init.rst & rfifo_release)

        scan_ready = Signal()
        scan_ready_afi = Signal()
        self.specials += MultiReg(scan_ready, scan_ready_afi, odomain="dll_init")
        startup_cycles = Signal(max=1026)
        startup_done = Signal()
        start_vfifo = Signal()
        self.sync.dll_init += If(dll_ready & scan_ready_afi,
            If(~startup_done, startup_cycles.eq(startup_cycles + 1)),
            start_vfifo.eq(startup_cycles == 1023),
            If(startup_cycles == 1024, startup_done.eq(1)),
        )

        # Hold the controller and BIOS in reset until the I/O scan and VFIFO
        # startup finish. The PLL/DLL and hard I/O continue running meanwhile.
        reset_n = Signal()
        self.comb += [
            reset_n.eq(locked & ~self.cd_dll_init.rst & dll_ready),
            ports["o_afi_reset_n"].eq(reset_n & startup_done),
            ports["o_cal_success"].eq(reset_n & startup_done),
            ports["o_cal_fail"].eq(0),
        ]
        self.settings_cdc = BusSynchronizer(33, "sys", "afi")
        self.vfifo_increment = PulseSynchronizer("sys", "afi")
        settings = Signal(32)
        self.comb += [
            self.settings_cdc.i.eq(Cat(self._settings.storage, 1)),
            settings.eq(Mux(self.settings_cdc.o[32], self.settings_cdc.o[:32], default_settings)),
            self.vfifo_increment.i.eq(self._vfifo_increment.wr_stb),
            ports["o_afi_wlat"].eq(settings[:3]),
        ]

        # The hard FIFO reset pins assert asynchronously. Synchronize
        # release on the fabric PLL output in phase with the hard PHY clock.
        # Split the release fanout between the two halves of the byte lanes.
        reset_groups = min(2, lanes)
        fifo_resets = []
        for group in range(reset_groups):
            lfifo_reset = ClockDomain(f"lfifo_reset{group}")
            vfifo_reset = ClockDomain(f"vfifo_reset{group}")
            self.clock_domains += [lfifo_reset, vfifo_reset]
            self.comb += [lfifo_reset.clk.eq(mem_clk), vfifo_reset.clk.eq(mem_clk)]
            self.specials += [
                AsyncResetSynchronizer(lfifo_reset, ~reset_n | ~settings[13] | level_fifo_reset),
                AsyncResetSynchronizer(vfifo_reset, ~reset_n | ~scan_ready_afi | ~settings[14] | level_fifo_reset),
            ]
            fifo_resets.append((lfifo_reset.rst, vfifo_reset.rst))

        self.specials += Instance("q_sys_smc_0_mem_if_ddr3_emif_0_p0_addr_cmd_pads",
            p_DEVICE_FAMILY="Cyclone V", p_MEM_ADDRESS_WIDTH=len(ports["o_mem_a"]),
            p_MEM_BANK_WIDTH=len(ports["o_mem_ba"]), p_MEM_CHIP_SELECT_WIDTH=1,
            p_MEM_CLK_EN_WIDTH=1, p_MEM_CK_WIDTH=1, p_MEM_ODT_WIDTH=1, p_MEM_CONTROL_WIDTH=1,
            p_AFI_ADDRESS_WIDTH=len(ports["i_afi_addr"]), p_AFI_BANK_WIDTH=len(ports["i_afi_ba"]),
            p_AFI_CHIP_SELECT_WIDTH=2, p_AFI_CLK_EN_WIDTH=2, p_AFI_ODT_WIDTH=2,
            p_AFI_CONTROL_WIDTH=2, p_DLL_WIDTH=7, p_REGISTER_C2P="true", p_IS_HHP_HPS="false",
            i_reset_n=reset_n, i_reset_n_afi_clk=reset_n, i_pll_afi_clk=afi_clk,
            i_pll_mem_clk=mem_clk, i_pll_mem_phy_clk=mem_phy_clk, i_pll_afi_phy_clk=afi_phy_clk,
            i_pll_write_clk=dq_clk, i_phy_ddio_addr_cmd_clk=cmd_clk, i_dll_delayctrl_in=delay,
            i_enable_mem_clk=1,
            **{f"i_phy_ddio_{name}": ports[f"i_afi_{afi_name}"] for name, afi_name in (
                ("address", "addr"), ("bank", "ba"), ("cs_n", "cs_n"), ("cke", "cke"),
                ("odt", "odt"), ("we_n", "we_n"), ("ras_n", "ras_n"), ("cas_n", "cas_n"),
                ("reset_n", "rst_n"))},
            **{f"o_phy_mem_{name}": ports[f"o_mem_{mem_name}"] for name, mem_name in (
                ("address", "a"), ("bank", "ba"), ("cs_n", "cs_n"), ("cke", "cke"),
                ("odt", "odt"), ("we_n", "we_n"), ("ras_n", "ras_n"), ("cas_n", "cas_n"),
                ("reset_n", "reset_n"), ("ck", "ck"), ("ck_n", "ck_n"))},
        )

        # Program the hard I/O scan chains with a shared native sequencer.
        # A bundled command preserves the scan word across the clock crossing.
        self.cd_scc = ClockDomain("scc")
        self.comb += self.cd_scc.clk.eq(~config_clk)
        self.specials += AsyncResetSynchronizer(self.cd_scc, ~locked)
        self.dqs_scan_cdc = BusSynchronizer(31, "sys", "scc")
        self.comb += self.dqs_scan_cdc.i.eq(self._dqs_scan.storage)
        scan_command = self.dqs_scan_cdc.o
        scan_toggle = Signal()
        scan_word = Signal(30)
        scan_count = Signal(5)
        scan_io = Signal()
        scan_io_target = Signal(2)
        scan_io_lane = Signal(3)
        scan_single_strobe = Signal()
        scan_dqs = Signal()
        scan_update = Signal()
        # Cross the requested tap values as one coherent snapshot. Each lane
        # keeps its own tap, including during the BIOS's bulk reset sweep.
        read_taps = [Signal(5, reset=4) for _ in range(lanes)]
        dq_taps = [Signal(5) for _ in range(lanes)]
        dqs_taps = [Signal(5) for _ in range(lanes)]
        applied_io = [Signal(10, reset=4) for _ in range(lanes)]
        applied_dqs = [Signal(5) for _ in range(lanes)]
        self.training_taps_cdc = BusSynchronizer(15*lanes + 1, "sys", "scc")
        self.comb += self.training_taps_cdc.i.eq(Cat(*(
            Cat(rd, dq, dqs) for rd, dq, dqs in zip(read_taps, dq_taps, dqs_taps)), 1))
        for lane in range(lanes):
            self.sync += If(ports["i_read_delay_select"][lane],
                If(ports["i_read_delay_reset"], read_taps[lane].eq(0))
                .Elif(ports["i_read_delay_increment"], read_taps[lane].eq(read_taps[lane] + 1)),
                If(ports["i_write_dq_delay_reset"], dq_taps[lane].eq(0))
                .Elif(ports["i_write_dq_delay_increment"], dq_taps[lane].eq(dq_taps[lane] + 1)),
                If(ports["i_write_dqs_delay_reset"], dqs_taps[lane].eq(0))
                .Elif(ports["i_write_dqs_delay_increment"], dqs_taps[lane].eq(dqs_taps[lane] + 1)),
            )
        new_taps = self.training_taps_cdc.o

        # Drive the scan inputs on the falling edge, MSB first. Preserve the
        # hard FIFO mode and the fixed DQ output and output-enable delays.
        write_dq_offset = 6
        max_write_tap = 15
        io_scan = (2 << 18) | (write_dq_offset << 10) | (write_dq_offset << 5)
        dqs_scan = 1 << 22
        boot_step = Signal(2)
        self.scan_fsm = scan_fsm = ClockDomainsRenamer("scc")(FSM(reset_state="IO-INIT"))
        scan_fsm.act("IO-INIT",
            NextValue(scan_word, (2 << 18) << 5),
            NextValue(scan_count, 25),
            NextState("IO-SHIFT"),
        )
        scan_fsm.act("IO-SHIFT",
            scan_io.eq(1),
            NextValue(scan_word, scan_word << 1),
            NextValue(scan_count, scan_count - 1),
            If(scan_count == 1, NextState("DQS-INIT")),
        )
        scan_fsm.act("DQS-INIT",
            NextValue(scan_word, dqs_scan | (2 << 23) | (31 << 17)),
            NextValue(scan_count, 30),
            NextState("DQS-SHIFT"),
        )
        scan_fsm.act("DQS-SHIFT",
            scan_dqs.eq(1),
            NextValue(scan_word, scan_word << 1),
            NextValue(scan_count, scan_count - 1),
            If(scan_count == 1, NextState("UPDATE")),
        )
        scan_fsm.act("IO-UPDATE-SHIFT",
            scan_io.eq(1),
            NextValue(scan_word, scan_word << 1),
            NextValue(scan_count, scan_count - 1),
            If(scan_count == 1, NextState("UPDATE")),
        )
        scan_fsm.act("UPDATE",
            scan_update.eq(1),
            If(boot_step == 0,
                NextValue(boot_step, 1),
                NextValue(scan_word, dqs_scan),
                NextValue(scan_count, 30),
                NextState("DQS-SHIFT"),
            ).Elif(boot_step == 1,
                NextValue(boot_step, 2),
                NextValue(scan_word, (io_scan | 4) << 5),
                NextValue(scan_count, 25),
                NextValue(scan_io_target, 1),
                NextState("IO-UPDATE-SHIFT"),
            ).Else(
                NextValue(scan_ready, 1),
                NextState("IDLE"),
            ),
        )
        pending_scan = If(0)
        for lane in range(lanes):
            dq = new_taps[15*lane:15*lane + 10]
            dqs = new_taps[15*lane + 10:15*(lane + 1)]
            # Each write step is two I/O taps. Shift data, mask and OE
            # together and clamp the fixed DQ offset at the pad limit.
            dq_delay = Signal(5)
            dq_with_offset = (dq[5:] << 1) + write_dq_offset
            self.comb += dq_delay.eq(Mux(dq[5:] > max_write_tap, write_dq_offset,
                Mux(dq[5:] > (31 - write_dq_offset)//2, 31, dq_with_offset)))
            pending_scan = If(dq != applied_io[lane],
                NextValue(applied_io[lane], dq),
                NextValue(scan_word, (dq[:5] | (dq_delay << 5) | (dq_delay << 10) | (2 << 18)) << 5),
                NextValue(scan_count, 25),
                NextValue(scan_io_target, 3),
                NextValue(scan_io_lane, lane),
                NextState("IO-UPDATE-SHIFT"),
            ).Elif(dqs != applied_dqs[lane],
                NextValue(applied_dqs[lane], dqs),
                NextValue(scan_word, Mux(dqs > max_write_tap, 0, (dqs << 11) | (dqs << 16))),
                NextValue(scan_count, 25),
                NextValue(scan_io_target, 2),
                NextValue(scan_single_strobe, 1),
                NextValue(scan_io_lane, lane),
                NextState("IO-UPDATE-SHIFT"),
            ).Else(pending_scan)
        scan_fsm.act("IDLE",
            If(scan_command[30] != scan_toggle,
                NextValue(scan_toggle, scan_command[30]),
                NextValue(scan_single_strobe, 0),
                If(scan_command[27:29] == 0,
                    NextValue(scan_word, scan_command[:25]),
                    NextValue(scan_count, 30),
                    NextState("DQS-SHIFT"),
                ).Else(
                    NextValue(scan_word, scan_command[:25] << 5),
                    NextValue(scan_count, 25),
                    NextValue(scan_io_target, scan_command[27:29]),
                    NextValue(scan_io_lane, Cat(scan_command[25:27], scan_command[29])),
                    NextState("IO-UPDATE-SHIFT"),
                ),
            ).Elif(new_taps[-1],
                pending_scan,
            ),
        )

        read_words = [Signal(32) for _ in range(lanes)]
        read_data = Cat(*(word[8*slot:8*(slot + 1)] for slot in range(4) for word in read_words))
        captured_data = Signal.like(read_data)
        lane_valid = Signal(lanes)
        read_valid = lane_valid == (1 << lanes) - 1
        read_gate = Signal()
        read_request = ports["i_afi_rdata_en_full"][0]
        level_read = Signal()
        gate_request = read_request | level_read
        self.gate_delay = ClockDomainsRenamer("afi")(TappedDelayLine(gate_request, ntaps=7))
        gates = [gate_request, *self.gate_delay.taps]
        delayed_gate = Array(gates)[settings[4:7]]
        previous_gate = Signal()
        self.sync.afi += previous_gate.eq(delayed_gate)
        # Feed both hard FIFO inputs from the same pulse, as in the
        # Cyclone V memory IP. Tune LFIFO latency with settings[8:13].
        level_enable = Signal()
        self.specials += MultiReg(ports["i_write_level_enable"], level_enable, odomain="afi")
        self.level_strobe_cdc = PulseSynchronizer("sys", "afi")
        self.comb += self.level_strobe_cdc.i.eq(ports["i_write_level_strobe"])
        level_strobe = self.level_strobe_cdc.o & level_enable

        # The DRAM presents feedback asynchronously on the prime DQ of each
        # byte. Drive repeated copies of the same DQS edge and capture the
        # settled feedback through the ordinary hard input FIFO.
        feedback_wait = Signal(6)
        previous_level_enable = Signal()
        rearm = Signal(5)
        feedback = Signal(lanes)
        feedback_seen = Signal(lanes)
        lane_feedback = Cat(*(Cat(*(captured_data[8*(slot*lanes + lane):8*(slot*lanes + lane + 1)]
                                     for slot in range(4))) != 0 for lane in range(lanes)))
        level_burst = (feedback_wait <= 32) & (feedback_wait > 14)
        supported_taps = Signal(lanes)
        self.level_taps_cdc = BusSynchronizer(lanes, "sys", "afi")
        self.comb += [
            self.level_taps_cdc.i.eq(Cat(*(tap <= max_write_tap for tap in dqs_taps))),
            supported_taps.eq(self.level_taps_cdc.o),
            level_read.eq(level_enable & (feedback_wait <= 30) & (feedback_wait > 18)),
            read_gate.eq(delayed_gate | (settings[26] & previous_gate)),
            level_fifo_reset.eq((feedback_wait > 40) | (rearm > 16)),
            level_vfifo_rephase.eq((feedback_wait == 36) | (rearm == 1)),
        ]
        # Start with the capture FIFOs reset. Allow their release and VFIFO
        # rephasing before driving DQS. Sample the tail of the capture window
        # after the DRAM feedback has settled.
        self.sync.afi += [
            If(level_strobe, feedback_wait.eq(48), feedback_seen.eq(0))
            .Elif(feedback_wait != 0,
                feedback_wait.eq(feedback_wait - 1),
                If((feedback_wait <= 15) & (feedback_wait > 6),
                    feedback_seen.eq(feedback_seen | lane_feedback),
                ),
                If(feedback_wait == 6, feedback.eq(feedback_seen & supported_taps)),
            ),
            previous_level_enable.eq(level_enable),
            If(previous_level_enable & ~level_enable, rearm.eq(24))
            .Elif(rearm != 0, rearm.eq(rearm - 1)),
        ]
        self.specials += MultiReg(feedback, ports["o_write_level_feedback"], odomain="sys")

        # The half-rate output primitive takes two full-rate slots. Move the
        # payload and DQS enable by one slot and keep DQ enabled over the edges.
        def extend(strobe, previous):
            return Cat(strobe[0] | previous[1] | previous[0],
                       strobe[1] | strobe[0] | previous[1])

        # AFI orders bytes by time slot. Each pad instance takes four
        # consecutive bytes from its own lane.
        for lane in range(lanes):
            lfifo_reset, vfifo_reset = fifo_resets[lane*reset_groups//lanes]
            scan_data_pads = scan_io & (scan_io_target != 2) & ((scan_io_target != 3) | (scan_io_lane == lane))
            scan_strobe_pad = scan_io & ((scan_io_target == 0) |
                ((scan_io_target == 2) & (~scan_single_strobe | (scan_io_lane == lane))))
            write_data = Cat(*(ports["i_afi_wdata"][8*(slot*lanes + lane):8*(slot*lanes + lane + 1)]
                               for slot in range(4)))
            write_mask = Cat(*(ports["i_afi_dm"][slot*lanes + lane] for slot in range(4)))
            write_oe = Cat(ports["i_afi_wdata_valid"][lane], ports["i_afi_wdata_valid"][lanes + lane])
            write_dqs = Cat(ports["i_afi_dqs_burst"][lane], ports["i_afi_dqs_burst"][lanes + lane])
            prev_data, prev_mask = Signal(16), Signal(2)
            prev_oe, prev_dqs = Signal(2), Signal(2)
            data, mask, oe, dqs, oct_enable = Signal(32), Signal(4), Signal(2), Signal(2), Signal(2)

            payload_slots = Mux(settings[3], write_oe, Cat(prev_oe[1], write_oe[0]))
            shifted_mask = Mux(settings[3], write_mask, Cat(prev_mask, write_mask[:2]))
            padding_mask = Cat(Replicate(~payload_slots[0], 2), Replicate(~payload_slots[1], 2))
            self.sync.afi += [
                prev_data.eq(write_data[16:]), prev_mask.eq(write_mask[2:]),
                prev_oe.eq(write_oe), prev_dqs.eq(write_dqs),
                data.eq(Mux(settings[3], write_data, Cat(prev_data, write_data[:16]))),
                mask.eq(shifted_mask | Mux(settings[28], 0, padding_mask)),
                oe.eq(extend(write_oe, prev_oe)),
                dqs.eq(Mux(level_enable, 3,
                           Mux(settings[3] ^ settings[29], write_dqs, Cat(prev_dqs[1], write_dqs[0])))),
                # The hard I/O shares dynamic OCT across DQS and DQ.
                # Disable it while the FPGA drives DQS for write leveling.
                oct_enable.eq(Mux(level_enable | settings[30], 0, ~extend(write_dqs, prev_dqs))),
            ]
            self.specials += Instance("altdq_dqs2_acv_cyclonev", name=f"ddr3b_lane{lane}",
                p_PIN_WIDTH=8, p_PIN_TYPE="bidir", p_USE_HALF_RATE_OUTPUT="true",
                p_DIFFERENTIAL_CAPTURE_STROBE="true", p_DIFFERENTIAL_OUTPUT_STROBE="true",
                p_USE_BIDIR_STROBE="true", p_INVERT_CAPTURE_STROBE="true",
                p_USE_OUTPUT_STROBE_RESET="false", p_USE_DQS_ENABLE="true",
                p_USE_DYNAMIC_CONFIG="true", p_USE_HARD_FIFOS="true",
                p_INPUT_FREQ=Instance.PreformattedParam("300.0"), p_INPUT_FREQ_PS="3333 ps",
                p_DQS_PHASE_SHIFT=Instance.PreformattedParam("0"), p_DQS_ENABLE_PHASE_SETTING=3,
                p_USE_TERMINATION_CONTROL="true", p_USE_OCT_ENA_IN_FOR_OCT="true",
                p_DLL_WIDTH=7, p_EXTRA_OUTPUT_WIDTH=1, p_PREAMBLE_TYPE="high",
                p_HR_DDIO_OUT_HAS_THREE_REGS="false",
                i_write_strobe_clock_in=mem_phy_clk, i_reset_n_core_clock_in=reset_n,
                i_core_clock_in=afi_clk, i_fr_clock_in=dq_clk, i_hr_clock_in=afi_phy_clk,
                i_strobe_ena_hr_clock_in=afi_clk, i_parallelterminationcontrol_in=parallel,
                i_seriesterminationcontrol_in=series, i_dll_delayctrl_in=delay,
                io_read_write_data_io=ports["io_mem_dq"][8*lane:8*(lane + 1)], io_strobe_io=ports["io_mem_dqs"][lane],
                io_strobe_n_io=ports["io_mem_dqs_n"][lane], o_extra_write_data_out=ports["o_mem_dm"][lane],
                i_config_data_in=scan_word[-1], i_config_clock_in=config_clk,
                i_config_dqs_ena=scan_dqs,
                i_config_io_ena=Replicate(scan_data_pads, 8),
                i_config_dqs_io_ena=scan_strobe_pad,
                i_config_extra_io_ena=scan_data_pads, i_config_update=scan_update,
                i_extra_write_data_in=mask, i_write_data_in=data,
                i_write_oe_in=Cat(Replicate(oe[0], 8), Replicate(oe[1], 8)),
                i_output_strobe_ena=dqs,
                i_level_enable=level_enable, i_level_strobe=Replicate(level_burst, 2), i_oct_ena_in=oct_enable,
                i_lfifo_rdata_en=ports["i_afi_rdata_en"], i_lfifo_rdata_en_full=Replicate(read_gate, 2),
                i_lfifo_rd_latency=settings[8:13], i_lfifo_reset_n=lfifo_reset,
                o_lfifo_rdata_valid=lane_valid[lane], i_vfifo_qvld=Replicate(read_gate, 2),
                i_vfifo_inc_wr_ptr=Cat(start_vfifo | level_vfifo_rephase | self.vfifo_increment.o, 0), i_vfifo_reset_n=vfifo_reset,
                i_rfifo_reset_n=rfifo_reset, o_read_data_out=read_words[lane],
            )

            if lane == 0:
                trace_lane = (write_data, data, write_oe, oe, dqs, mask)

        # Qualify the read FIFO output with the scheduled two AFI beats of a BL8
        # read. The LFIFO's raw valid output can remain asserted between reads.
        self.capture_delay = ClockDomainsRenamer("afi")(TappedDelayLine(read_request, ntaps=31))
        capture = Array([read_request, *self.capture_delay.taps])[settings[16:21]]
        # The controller-facing valid is derived from the request, while
        # the hard LFIFO schedules the pad FIFO reads independently.
        # Cross the full-rate to half-rate boundary before reducing the
        # per-lane valid bits. Keep the data and its qualifier in lockstep.
        captured_lane0 = Signal.like(read_words[0])
        captured_valid = Signal(lanes, attr={"no_retiming"})
        captured_request = Signal()
        captured_request_mode = Signal()
        last_read = Signal(32)
        read_count = Signal(16)
        capture_valid = captured_request & (captured_request_mode | (captured_valid == (1 << lanes) - 1))
        self.sync.afi += [
            captured_data.eq(read_data),
            captured_lane0.eq(read_words[0]),
            captured_valid.eq(lane_valid),
            captured_request.eq(capture),
            captured_request_mode.eq(settings[27]),
            ports["o_afi_rdata"].eq(captured_data),
            ports["o_afi_rdata_valid"].eq(Replicate(capture_valid, 2)),
            If(capture_valid, last_read.eq(captured_lane0), read_count.eq(read_count + 1)),
        ]
        if not with_trace:
            self.read_status_cdc = BusSynchronizer(48, "afi", "sys")
            self.comb += [
                self.read_status_cdc.i.eq(Cat(last_read, read_count)),
                self._read_status.status.eq(self.read_status_cdc.o[:32]),
                self._read_count.status.eq(self.read_status_cdc.o[32:]),
            ]
            return

        # Capture raw FIFO behavior before valid qualification. The trace holds
        # one 16-cycle window starting at the next read request.
        self.trace_arm_cdc = PulseSynchronizer("sys", "afi")
        self.comb += self.trace_arm_cdc.i.eq(self._trace_arm.wr_stb)
        self.trace_fsm = trace_fsm = ClockDomainsRenamer("afi")(FSM(reset_state="IDLE"))
        trace_index = Signal(4)
        trace = Memory(146, 16)
        trace_write = trace.get_port(write_capable=True, clock_domain="afi")
        trace_read = trace.get_port(clock_domain="afi")
        self.specials += trace, trace_write, trace_read
        write_command = (~ports["i_afi_cs_n"] & ports["i_afi_ras_n"] &
                         ~ports["i_afi_cas_n"] & ~ports["i_afi_we_n"])
        activate_command = (~ports["i_afi_cs_n"] & ~ports["i_afi_ras_n"] &
                            ports["i_afi_cas_n"] & ports["i_afi_we_n"])
        afi_addr = ports["i_afi_addr"]
        addr_width = len(afi_addr) // 2
        active_addr = Mux(~ports["i_afi_cs_n"][1], afi_addr[addr_width:], afi_addr[:addr_width])
        command = Cat(*(ports[f"i_afi_{name}"] for name in ("cs_n", "ras_n", "cas_n", "we_n", "cke", "odt", "ba")),
                      active_addr)
        write_data, data, write_oe, oe, dqs, mask = trace_lane
        trace_sample = Cat(read_words[0], read_request, read_gate, read_valid, capture,
                           write_data, data, write_command, write_oe, oe, dqs, mask,
                           ports["o_afi_rdata_valid"], command)
        trigger = Mux(settings[31], activate_command != 0, Mux(settings[25], write_command != 0, read_request))
        self.comb += [
            trace_write.dat_w.eq(trace_sample),
            trace_read.adr.eq(settings[21:25]),
        ]
        trace_fsm.act("IDLE", If(self.trace_arm_cdc.o, NextState("ARMED")))
        trace_fsm.act("ARMED", If(trigger,
            trace_write.adr.eq(0),
            trace_write.we.eq(1),
            NextValue(trace_index, 1),
            NextState("CAPTURE"),
        ))
        trace_fsm.act("CAPTURE",
            trace_write.adr.eq(trace_index),
            trace_write.we.eq(1),
            NextValue(trace_index, trace_index + 1),
            If(trace_index == 15, NextState("DONE")),
        )
        trace_fsm.act("DONE", If(self.trace_arm_cdc.o, NextState("ARMED")))
        trace_entry = trace_read.dat_r

        self.read_status_cdc = BusSynchronizer(195, "afi", "sys")
        self.comb += [
            self.read_status_cdc.i.eq(Cat(last_read, read_count, trace_entry[:36], trace_fsm.ongoing("DONE"), trace_entry[36:])),
            self._read_status.status.eq(self.read_status_cdc.o[:32]),
            self._read_count.status.eq(self.read_status_cdc.o[32:48]),
            self._trace_word.status.eq(self.read_status_cdc.o[48:80]),
            self._trace_flags.status.eq(self.read_status_cdc.o[80:85]),
            self._trace_afi_write.status.eq(self.read_status_cdc.o[85:117]),
            self._trace_pad_write.status.eq(self.read_status_cdc.o[117:149]),
            self._trace_io_flags.status.eq(self.read_status_cdc.o[149:163]),
            self._trace_command.status.eq(self.read_status_cdc.o[163:195]),
        ]
