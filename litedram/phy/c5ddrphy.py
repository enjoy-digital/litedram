#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

from functools import reduce
from operator import or_

from migen import Array, Cat, ClockDomain, ClockDomainsRenamer, If, Mux, Replicate, Signal
from migen.genlib.fifo import AsyncFIFO
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import LiteXModule
from litex.soc.interconnect.csr import CSR, CSRField, CSRStatus, CSRStorage

from litedram.common import PhySettings, TappedDelayLine
from litedram.phy.c5ddrphy_native import CycloneVDDR3Lane
from litedram.phy.dfi import Interface


class CycloneVDDRPHY(LiteXModule):
    """Single-rank DDR3 BL8 PHY using the native Cyclone V byte lanes."""

    def __init__(self, pads, ref_clk, rst, cl, cwl, *, on_the_fly=False, max_write_latency=7,
                 oct=None, io_backend=CycloneVDDR3Lane):
        if io_backend is None:
            raise ValueError("Cyclone V DDR3 requires the native byte-lane PHY")
        if oct is not None:
            raise ValueError("Cyclone V DDR3 requires a dedicated RZQ pin for native termination")

        databits = len(pads.dq)
        addressbits = len(pads.a)
        bankbits = len(pads.ba)
        lanes = databits // 8
        if not 1 <= lanes <= 8 or databits % 8 or any(len(getattr(pads, name)) != lanes for name in ("dm", "dqs_p", "dqs_n")):
            raise ValueError("Cyclone V DDR3 requires one DM and differential DQS per byte")
        if len(pads.cs_n) != 1:
            raise ValueError("Cyclone V DDR3 PHY supports one rank")

        if on_the_fly and addressbits < 13:
            raise ValueError("On-the-fly burst selection requires DDR3 address bit A12")
        if not 0 <= max_write_latency < 64:
            raise ValueError("Invalid maximum AFI write latency")

        self.cd_afi = ClockDomain()
        self.cd_sys = ClockDomain()
        self.dfi = Interface(addressbits, bankbits, nranks=1, databits=2*databits, nphases=4)
        # Allow the maximum six-bit AFI read latency, burst assembly and FIFO
        # synchronization before the LiteDRAM crossbar samples the return word.
        # The native backend stages the incoming frame for one sys cycle.
        read_latency = 37
        self.settings = PhySettings(
            phytype="CycloneVDDRPHY", memtype="DDR3", databits=databits,
            dfi_databits=2*databits, nphases=4, rdphase=3, wrphase=3,
            cl=cl, cwl=cwl, read_latency=read_latency, write_latency=0,
            write_leveling=True, read_leveling=True, delays=32, bitslips=1, cmd_delay=0,
        )

        cal_success = Signal()
        cal_failed = Signal()
        reset_n = Signal()
        wlat_raw = Signal(6)
        read_data = Signal(4*databits)
        read_valid = Signal(2)
        self._calibration = CSRStatus(fields=[
            CSRField("success", offset=0, description="The PHY is ready and reports a supported write latency."),
            CSRField("failed",  offset=1, description="The PHY reported a startup failure or an unsupported write latency."),
        ], description="PHY startup status.")
        self._dly_sel = CSRStorage(lanes, description="Select byte lanes for read-delay training.")
        self._rdly_dq_rst = CSR()
        self._rdly_dq_inc = CSR()
        # The hard FIFOs align BL8 frames at a fixed position.
        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip = CSR()
        self._wlevel_en = CSRStorage()
        self._wlevel_strobe = CSR()
        # CK and command/address use the fixed board PLL phase.
        self._cdly_rst = CSR()
        self._cdly_inc = CSR()
        # At 600 MT/s, one write step spans two roughly 36 ps I/O taps.
        self._half_sys8x_taps = CSRStatus(5, reset=12)
        self._wdly_dq_rst = CSR()
        self._wdly_dq_inc = CSR()
        self._wdly_dqs_rst = CSR()
        self._wdly_dqs_inc = CSR()
        self._wdly_dq_bitslip_rst = CSR()
        self._wdly_dq_bitslip = CSR()
        self._read_error = CSRStatus(description="A read missed its fixed DFI return slot.")

        # Both clock domains are derived from the native PHY PLL.
        self.specials += AsyncResetSynchronizer(self.cd_afi, ~reset_n)
        self.sync.afi += self.cd_sys.clk.eq(~self.cd_sys.clk)
        first = self.cd_sys.clk
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~reset_n)
        # Sample PHY readiness and write latency in the AFI domain.
        afi_cal_first = Signal(8, reset_less=True, attr={"no_retiming"})
        afi_cal = Signal.like(afi_cal_first)
        self.sync.afi += [
            afi_cal_first.eq(Cat(cal_success, cal_failed, wlat_raw)),
            afi_cal.eq(afi_cal_first),
        ]
        wlat = afi_cal[2:]
        latency_supported = wlat <= max_write_latency
        calibrated = afi_cal[0] & latency_supported
        status = Cat(calibrated, afi_cal[1] | (afi_cal[0] & ~latency_supported))
        # Launch on the AFI edge that raises sys. The sys register
        # samples the previous snapshot, which had a full sys period.
        snapshot = Signal(2, name="afi_cal_snapshot", reset_less=True, attr={"no_retiming"})
        self.sync.afi += If(~first, snapshot.eq(status))
        sys_cal_first = Signal(2, reset_less=True, attr={"no_retiming"})
        cal_status = Signal.like(sys_cal_first)
        self.sync += [
            sys_cal_first.eq(snapshot),
            cal_status.eq(sys_cal_first),
        ]
        self.calibrated = cal_status[0]
        self.comb += [
            self._calibration.fields.success.eq(cal_status[0]),
            self._calibration.fields.failed.eq(cal_status[1]),
        ]

        phases = self.dfi.phases
        def phase_address(phase):
            if on_the_fly:
                # A12/BC# is high for a BL8 column command. Leave A12
                # intact on ACT, PRE and mode-register writes.
                column = ~phase.cs_n & phase.ras_n & ~phase.cas_n
                return Cat(phase.address[:12], phase.address[12] | column, phase.address[13:])
            return phase.address

        # Capture a full DFI frame at the AFI edge that launches the next
        # sys cycle. The previous sys frame has had a whole sys cycle to
        # settle. The board constraints cover this deliberate clock enable.
        def capture_frame(value, name):
            # Separate the controller's wide data mux from the
            # sys-to-AFI crossing. Stage commands and data together.
            staged = Signal(len(value), name=name.replace("afi_frame_", "sys_frame_", 1), reset_less=True, attr={"no_retiming"})
            self.sync += staged.eq(value)
            frame = Signal(len(value), name=name, reset_less=True)
            self.sync.afi += If(~first, frame.eq(staged))
            return frame

        cmd = {}
        for dfi_name, afi_name, idle in [
            ("address", "addr", 0), ("bank", "ba", 0),
            ("cs_n", "cs_n", 3), ("ras_n", "ras_n", 3),
            ("cas_n", "cas_n", 3), ("we_n", "we_n", 3),
            ("cke", "cke", 3), ("odt", "odt", 0), ("reset_n", "rst_n", 3),
        ]:
            values = [phase_address(p) if dfi_name == "address" else getattr(p, dfi_name) for p in phases]
            frame = capture_frame(Cat(*values), f"afi_frame_{afi_name}")
            width = len(frame)//2
            cmd[afi_name] = Signal(width, reset=idle)
            self.sync.afi += cmd[afi_name].eq(Mux(calibrated, Mux(first, frame[:width], frame[width:]), idle))

        rd_en = reduce(or_, (phase.rddata_en for phase in phases))
        wr_en = reduce(or_, (phase.wrdata_en for phase in phases))
        frame_read = capture_frame(rd_en, "afi_frame_read")
        afi_rd_en = Signal()
        # The phase-3 column command goes out on the second memory clock
        # of its AFI slot. Enable the PHY in that slot and the next one.
        previous_read = Signal()
        self.sync.afi += [
            If(~first, previous_read.eq(frame_read)),
            afi_rd_en.eq(calibrated & Mux(first, previous_read, frame_read)),
        ]

        # Emit the two BL8 data words starting in the column-command slot.
        wr_data = Cat(*(phase.wrdata for phase in phases))
        wr_mask = Cat(*(phase.wrdata_mask for phase in phases))
        half_data = len(wr_data) // 2
        half_mask = len(wr_mask) // 2
        frame_data = capture_frame(wr_data, "afi_frame_write_data")
        frame_mask = capture_frame(wr_mask, "afi_frame_write_mask")
        frame_write = capture_frame(wr_en, "afi_frame_write")
        upper = Signal(half_data + half_mask + 1)
        self.sync.afi += If(~first, upper.eq(Cat(frame_data[half_data:], frame_mask[half_mask:], frame_write)))
        write_word = Signal.like(upper)
        self.comb += write_word.eq(Mux(first, upper,
            Cat(frame_data[:half_data], frame_mask[:half_mask], frame_write)))
        # The reference PHY reports write latency in AFI cycles. Its data
        # valid starts wlat+1 cycles after the column command. DQS needs an
        # additional memory-clock preamble in the preceding AFI word.
        self.write_delay = ClockDomainsRenamer("afi")(TappedDelayLine(write_word, ntaps=max_write_latency + 2))
        taps = Array([write_word, *self.write_delay.taps])
        write_now = Signal.like(write_word)
        write_next = Signal.like(write_word)
        # A register emits the column command, so tap wlat+1 is measured
        # from the AFI slot containing that registered command.
        self.comb += [
            write_now.eq(taps[wlat + 2]),
            write_next.eq(taps[wlat + 1]),
        ]
        write_active = calibrated & write_now[-1]
        dqs_preamble = calibrated & write_next[-1]
        dqs_burst = Cat(Replicate(write_active, lanes), Replicate(write_active | dqs_preamble, lanes))

        # Read valid is asserted for each AFI word, with both memory phases
        # valid for a word-aligned READ. Pair words before crossing to sys.
        first_word = Signal.like(read_data)
        second_word = Signal()
        self.return_fifo = ClockDomainsRenamer({"write": "afi", "read": "sys"})(
            AsyncFIFO(8*databits, 64))
        fifo = self.return_fifo
        self.sync.afi += If(read_valid == 3,
            If(~second_word, first_word.eq(read_data)),
            second_word.eq(~second_word),
        )
        self.comb += [
            fifo.din.eq(Cat(first_word, read_data)),
            fifo.we.eq((read_valid == 3) & second_word & fifo.writable),
        ]
        self.read_delay = TappedDelayLine(rd_en & cal_status[0], ntaps=read_latency)
        expected = self.read_delay.output
        self.sync += If(expected & ~fifo.readable, self._read_error.status.eq(1))
        write_level_feedback = Signal(lanes)
        feedback_bytes = Cat(*(Cat(write_level_feedback[lane], 0, 0, 0, 0, 0, 0, 0)
                               for lane in range(lanes)))
        self.comb += [
            fifo.re.eq(expected & fifo.readable),
            Cat(*(phase.rddata for phase in phases)).eq(
                Mux(self._wlevel_en.storage, Replicate(feedback_bytes, 8), fifo.dout)),
            *[phase.rddata_valid.eq(self._wlevel_en.storage | (expected & fifo.readable)) for phase in phases],
        ]

        io_ports = dict(
            i_write_level_enable=self._wlevel_en.storage,
            i_write_level_strobe=self._wlevel_strobe.wr_stb,
            o_write_level_feedback=write_level_feedback,
            i_write_dq_delay_reset=self._wdly_dq_rst.wr_stb,
            i_write_dq_delay_increment=self._wdly_dq_inc.wr_stb,
            i_write_dqs_delay_reset=self._wdly_dqs_rst.wr_stb,
            i_write_dqs_delay_increment=self._wdly_dqs_inc.wr_stb,
            i_read_delay_select=self._dly_sel.storage,
            i_read_delay_reset=self._rdly_dq_rst.wr_stb,
            i_read_delay_increment=self._rdly_dq_inc.wr_stb,
            i_pll_ref_clk=ref_clk, i_global_reset_n=~rst, i_oct_rzqin=pads.rzq,
            o_afi_clk=self.cd_afi.clk, o_afi_reset_n=reset_n,
            o_cal_success=cal_success, o_cal_fail=cal_failed,
            i_afi_addr=cmd["addr"], i_afi_ba=cmd["ba"],
            i_afi_cs_n=cmd["cs_n"], i_afi_ras_n=cmd["ras_n"],
            i_afi_cas_n=cmd["cas_n"], i_afi_we_n=cmd["we_n"],
            i_afi_cke=cmd["cke"], i_afi_odt=cmd["odt"], i_afi_rst_n=cmd["rst_n"],
            i_afi_wdata=write_now[:half_data], i_afi_dm=write_now[half_data:half_data + half_mask],
            i_afi_wdata_valid=Replicate(write_active, 2*lanes), i_afi_dqs_burst=dqs_burst,
            i_afi_rdata_en=Replicate(afi_rd_en, 2), i_afi_rdata_en_full=Replicate(afi_rd_en, 2),
            o_afi_rdata=read_data, o_afi_rdata_valid=read_valid, o_afi_wlat=wlat_raw,
            o_mem_a=pads.a, o_mem_ba=pads.ba, o_mem_ck=pads.clk_p, o_mem_ck_n=pads.clk_n,
            o_mem_cke=pads.cke, o_mem_cs_n=pads.cs_n, o_mem_dm=pads.dm, o_mem_ras_n=pads.ras_n,
            o_mem_cas_n=pads.cas_n, o_mem_we_n=pads.we_n, o_mem_reset_n=pads.reset_n,
            io_mem_dq=pads.dq, io_mem_dqs=pads.dqs_p, io_mem_dqs_n=pads.dqs_n,
            o_mem_odt=pads.odt,
        )
        self.io_backend = io_backend(**io_ports)
