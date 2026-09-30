#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Experimental native DDR4 PHY with the initial XEM8320 calibration profile."""

from pathlib import Path
from operator import or_
from functools import reduce

from migen import *
from migen.genlib.cdc import MultiReg, PulseSynchronizer

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStorage, CSRStatus

from litedram.common import PhySettings, BitSlip, TappedDelayLine, DQSPattern
from litedram.phy.dfi import Interface, DDR4DFIMux
from litedram.phy.usnative.riu_transaction import RIUTransaction
from litedram.phy.usnative.riu_falling_launch import RIUFallingLaunch
from litedram.phy.usnative.tap_status import RegisteredTapStatus

from .core import emit_core
from .adapter import core_ports, signal_sites, connect_core
from .mapping import NativeMapping
from .pins import extract_ddr_pins
from .query import query_device

# Native receive bitslip ---------------------------------------------------------------------------

class NativeRXBitslip(Module):
    """Register and rotate one gated native FIFO word; never join two bursts.

    This retains the old one-cycle unshifted latency and right-rotation
    convention. Native gated capture supplies complete eight-bit words,
    unlike a continuously sampled component-mode deserializer stream.
    """
    def __init__(self, i, rst, slp):
        self.o = Signal(8)
        word, shift = Signal(8), Signal(3)

        # # #

        self.sync += [
            word.eq(i),
            If(rst,
                shift.eq(0)
            ).Elif(slp,
                shift.eq(shift + 1)
            ),
        ]
        self.comb += self.o.eq(Array([word] + [Cat(word[n:], word[:n]) for n in range(1, 8)])[shift])


# Ultrascale native DDR4 PHY -----------------------------------------------------------------------

class USNativeDDRPHY(Module, AutoCSR):
    def __init__(self, pads, platform, pll_clk, pll_locked, pll_enable,
                 *, sys_clk_freq, output_dir, vivado='vivado', with_debug=False, overclock=False,
                 csr_cdc=lambda signal: signal, riu_domain='riu', registered_tx=True,
                 query_cache_dir=None, query_force_refresh=False):
        from litex.build.xilinx.vivado import XilinxVivadoToolchain

        # Profile and native resources -------------------------------------------------------------

        if not isinstance(platform.toolchain, XilinxVivadoToolchain):
            raise ValueError('USNativeDDRPHY requires the Vivado toolchain')
        widths = dict(a=14, we_n=1, cas_n=1, ras_n=1, ba=2, bg=1, act_n=1,
            dq=16, dm=2, dqs_p=2, dqs_n=2, clk_p=1, clk_n=1, cs_n=1,
            cke=1, odt=1, reset_n=1)
        if any(not hasattr(pads, name) or len(getattr(pads, name)) != width
               for name, width in widths.items()):
            raise ValueError('Integrated native PHY requires single-rank x16 DDR4, '
                'two x8 lanes with DM, a14 plus we/cas/ras, ba2 and bg1')
        if not registered_tx or riu_domain != 'riu':
            raise ValueError('Native profile requires registered TX and related sys:riu 2:1 clocks')
        frequency = int(round(sys_clk_freq))
        profiles = {
            300000000: (17, 12, 2, 3, 12, 3, 3),
            333333333: (19, 14, 0, 1, 12, 3, 3),
            366666667: (21, 16, 2, 3, 13, 4, 4),
            400000000: (24, 16, 3, 3, 14, 4, 5),
        }
        if frequency not in profiles:
            raise ValueError('Native profile supports 2400, 2666.667, 2933.333 or 3200 MT/s')
        if frequency > 333333333 and not overclock:
            raise ValueError('Native rates above 2666.667 MT/s require explicit overclock opt-in')
        cl, cwl, rdphase, wrphase, read_latency, write_latency, gate_delay = profiles[frequency]
        # The experimental high-rate profiles retain the maximum accepted
        # native delay-model parameter. Clock constraints retain the actual
        # rate: this is not a timing waiver or a claim of device compliance.
        refclk_mhz     = min(8*sys_clk_freq/1e6, 2666.666667)
        self.overclock = frequency > 333333333
        pin_map        = extract_ddr_pins(platform, pads)
        physical, auxiliary, directory = query_device(pin_map, output_dir, vivado=vivado,
            cache_dir=query_cache_dir, force_refresh=query_force_refresh)
        generated = emit_core('usnative_core', physical, auxiliary, family=pin_map.family,
                              refclk_mhz=refclk_mhz)
        layout = generated.layout
        mapping = NativeMapping(layout, profile=dict(frequency=frequency, cl=cl, cwl=cwl,
            rdphase=rdphase, wrphase=wrphase, read_latency=read_latency,
            write_latency=write_latency, gate_delay=gate_delay, registered_tx=registered_tx,
            family=pin_map.family, with_debug=bool(with_debug)))
        self.mapping = mapping
        sites        = signal_sites(layout)
        ntaps, ncontrols = mapping.tap_count, mapping.control_count
        ready_mask = (1 << ncontrols) - 1
        # One supplied PLL clock is supported by this integrated datapath.
        # Bank-spanning primitive generation remains available independently.
        if len(layout.banks) != 1:
            raise ValueError('Integrated native PHY currently requires one PLL bank')
        lane_by_tap = {tap: lane.index for lane in layout.lanes
            for tap in lane.dq + (lane.strobe,) + (() if lane.mask is None else (lane.mask,))}
        core = Path(output_dir).resolve() / 'usnative_core.v'
        core.parent.mkdir(parents=True, exist_ok=True)
        core.write_text(generated.verilog)
        self.query_directory = directory
        assert riu_domain == 'riu', 'Transactional adapter requires related sys:riu 2:1 clocks'
        # The target supplies an RIU clock at half the selected sys frequency.
        # CSR address/data stay stable around the synchronized write pulse.
        # Related-clock paths remain timed; no asynchronous false paths.
        # Registers --------------------------------------------------------------------------------

        self._abi_version      = CSRStatus(32, reset=(mapping.major << 16) | mapping.minor)
        self._abi_config_id    = CSRStatus(32, reset=mapping.config_id)
        self._abi_capabilities = CSRStatus(32, reset=mapping.capabilities)
        self._rst              = CSRStorage(reset=1)
        self._en_vtc           = CSRStorage(reset=1)
        self._bisc_only        = CSRStorage(reset=0)  # Full standalone calibration on boot.
        self._debug            = CSRStatus(32)
        self._debug_clear      = CSR()
        self._snapshot         = CSR()
        self._snapshot_status  = CSRStatus(32)
        self._elapsed          = CSRStatus(32)
        self._first_dly        = CSRStatus(32)
        self._first_vtc        = CSRStatus(32)
        self._faults           = CSRStatus(3)
        self._training_stage   = CSRStorage(8)
        self._training_error   = CSRStorage(8)
        self._fifo_reads0      = CSRStatus(32)
        self._fifo_reads1      = CSRStatus(32)
        self._ready            = CSRStatus()
        self._dly_rdy          = CSRStatus(ncontrols)
        self._vtc_rdy          = CSRStatus(ncontrols)
        self._fifo_empty       = CSRStatus(ntaps)
        self._wlevel_en        = CSRStorage()
        self._wlevel_strobe    = CSR()
        self._dly_sel          = CSRStorage(2)
        for name in ('cdly_rst', 'cdly_inc', 'rdly_dq_rst', 'rdly_dq_inc',
                     'rdly_dq_bitslip_rst', 'rdly_dq_bitslip',
                     'wdly_dq_rst', 'wdly_dq_inc', 'wdly_dqs_rst', 'wdly_dqs_inc',
                     'wdly_dq_bitslip_rst', 'wdly_dq_bitslip'):
            setattr(self, '_' + name, CSR(name=name))
        self._cdly_value         = CSRStatus(9)
        self._wdly_dqs_inc_count = CSRStatus(9)
        self._rdphase            = CSRStorage(2, reset=rdphase)
        self._wrphase            = CSRStorage(2, reset=wrphase)
        # Read-gate timing is deliberately exposed for native-PHY bring-up.
        self._gate_delay       = CSRStorage(5, reset=gate_delay)
        self._read_latency     = CSRStatus(5)
        self._riu_address      = CSRStorage(6)
        self._riu_nibble       = CSRStorage(max(1, (ncontrols-1).bit_length()))
        self._riu_wdata        = CSRStorage(16)
        self._riu_write        = CSR()
        self._riu_read         = CSR()
        self._riu_busy         = CSRStatus()
        self._riu_error        = CSRStatus()
        self._riu_rdata        = CSRStatus(16)
        self._riu_valid        = CSRStatus()
        self.software_control  = Signal()  # driven from the actual DFI owner
        self._manual_active    = CSRStatus()
        self._gate_override    = CSRStorage(2)
        self._gate_delay0      = CSRStorage(5, reset=gate_delay)
        self._gate_delay1      = CSRStorage(5, reset=gate_delay)
        self._gate_width0      = CSRStorage(4, reset=2)
        self._gate_width1      = CSRStorage(4, reset=2)
        self._tap_select       = CSRStorage(max(1, (ntaps-1).bit_length()))
        self._tap_allowed      = CSRStatus()
        self._tap_status_valid = CSRStatus()
        self._tap_rx_rst       = CSR()
        self._tap_rx_inc       = CSR()
        self._tap_tx_rst       = CSR()
        self._tap_tx_inc       = CSR()
        self._tap_rx_count     = CSRStatus(9)
        self._tap_tx_count     = CSRStatus(9)
        if with_debug:
            self._trace_arm   = CSR()
            self._trace_state = CSRStatus(2)  # pending, running; done separately
            self._trace_done  = CSRStatus()
            self._trace_index = CSRStorage(6)
            for word in range(8):
                setattr(self, '_trace_word'+str(word), CSRStatus(32, name='trace_word'+str(word)))
        self._fifo_lane_mode = CSRStorage()  # software-only independent lane draining
        # Burst-boundary diagnostics. Change only while software owns DFI and
        # no transaction is pending. Settings persist for controller handoff.
        self._tx_dqs_pre  = CSRStorage(8, reset=0x55)
        self._tx_dqs_post = CSRStorage(8, reset=0x55)
        self._tx_dqs_idle = CSRStorage(8, reset=0x55)
        # # #

        # Software control and DFI -----------------------------------------------------------------

        self.comb += self._manual_active.status.eq(self.software_control)
        pulse_names = ('cdly_rst', 'cdly_inc', 'rdly_dq_rst', 'rdly_dq_inc',
            'rdly_dq_bitslip_rst', 'rdly_dq_bitslip', 'wdly_dq_rst', 'wdly_dq_inc',
            'wdly_dqs_rst', 'wdly_dqs_inc', 'wdly_dq_bitslip_rst', 'wdly_dq_bitslip',
            'wlevel_strobe', 'riu_write', 'riu_read')
        pulse                = {name: csr_cdc(getattr(self, '_' + name).wr_stb) for name in pulse_names}
        self.training_pulses = pulse
        self.settings = PhySettings(phytype='USNativeDDRPHY', memtype='DDR4',
            databits=16, dfi_databits=32, nranks=1, nphases=4,
            rdphase=self._rdphase.storage, wrphase=self._wrphase.storage,
            cl=cl, cwl=cwl, cmd_latency=1 + 4*registered_tx,
            read_latency=read_latency, write_latency=write_latency,
            write_leveling=True, write_latency_calibration=True, read_leveling=True,
            delays=512, bitslips=8, with_dm=True)
        self.settings.usnative_mapping = mapping
        self.settings.tccd             = 8
        self.addressbits               = 17
        self.dfi                       = Interface(17, 3, 1, 32, 4)
        dfi                            = Interface(17, 3, 1, 32, 4)
        self.submodules += DDR4DFIMux(self.dfi, dfi)

        # Serializer boundary and delay controls ---------------------------------------------------

        ports               = {name: dict(direction=d, width=w) for name, (d, w) in core_ports(layout).items()}
        signals             = {name: Signal(p['width'], name='native_' + name) for name, p in ports.items()}
        self.native_signals = signals  # simulation/bring-up probes, not extra CSRs
        rx_rst, rx_ce, tx_rst, tx_ce = [Signal(ntaps) for _ in range(4)]
        rx_rst_request, rx_ce_request = Signal(ntaps), Signal(ntaps)
        tx_rst_request, tx_ce_request = Signal(ntaps), Signal(ntaps)
        # RST_DLY is asynchronous at the native primitive. Register the
        # complete selection/decode logic, rather than exposing CSR address
        # transitions to that pin. Selection must remain stable throughout
        # the transfer so a pulse cannot reset or increment another tap.
        # RX_CLK/TX_CLK clock the variable delay controls, not serial data.
        # Hold each selection vector until its pulse crosses to the slower
        # related RIU clock. Firmware separates commands by >=100 CPU cycles;
        # callers must leave >=16 sys cycles between requests of each kind.
        for request, output in zip(
                (rx_rst_request, rx_ce_request, tx_rst_request, tx_ce_request),
                (rx_rst, rx_ce, tx_rst, tx_ce)):
            if riu_domain == 'sys':
                self.sync += output.eq(request)
            else:
                payload  = Signal(ntaps)
                transfer = PulseSynchronizer('sys', riu_domain)
                self.submodules += transfer
                self.comb += transfer.i.eq(request != 0)
                self.sync += If(request != 0, payload.eq(request))
                getattr(self.sync, riu_domain).__iadd__(output.eq(Mux(transfer.o, payload, 0)))
        rx_count, tx_count = Signal(9*ntaps), Signal(9*ntaps)
        self.delay_controls = dict(rx_rst=rx_rst, rx_ce=rx_ce, tx_rst=tx_rst, tx_ce=tx_ce)
        fifo_empty, dqs_data = Signal(ntaps), Signal(16)
        self.fifo_empty_input = fifo_empty
        data_tristate         = Signal(reset=1)
        slice_vtc             = Signal(reset=1)
        self.slice_vtc        = slice_vtc
        kwargs = {('i_' if p['direction'] == 'input' else 'o_') + name: signals[name]
                  for name, p in ports.items()}
        kwargs.update(i_i_delay_clk=ClockSignal(riu_domain), i_i_rx_delay_rst=rx_rst, i_i_rx_delay_ce=rx_ce,
            i_i_tx_delay_rst=tx_rst, i_i_tx_delay_ce=tx_ce,
            o_o_rx_delay_count=rx_count, o_o_tx_delay_count=tx_count,
            o_o_fifo_empty=fifo_empty, i_i_dqs_tx_data=dqs_data,
            i_i_data_tristate=data_tristate, i_i_slice_en_vtc=slice_vtc)
        # Register the final serializer inputs, after CA packing and TX
        # bitslip muxes. Move command, data, strobe, output enables and read
        # gate by the same sys cycle. Their relative wire timing is preserved;
        # received data and rddata_valid arrive one sys cycle later.
        # CK and BISC/reset/RIU sequencing are not transaction pipelines.
        self.tx_launch_inputs, self.tx_launch_outputs = {}, {}
        for name in signals:
            if ((name.endswith('_tx_data') and name != 'i_ck_t_tx_data')
                    or name in ('i_data_tbyte', 'i_cmd_tbyte', 'i_phy_rden')):
                self.tx_launch_inputs[name] = signals[name]
        self.tx_launch_inputs.update(i_dqs_tx_data=dqs_data, i_data_tristate=data_tristate)
        for name, source in self.tx_launch_inputs.items():
            if registered_tx:
                reset = ((1 << len(source)) - 1 if name in
                         ('i_cs_n_tx_data', 'i_act_n_tx_data', 'i_data_tristate') else 0)
                output = Signal(len(source), reset=reset, name='native_launch_' + name)
                output.attr.add('dont_touch')
                self.sync += output.eq(source)
            else:
                output = source
            self.tx_launch_outputs[name] = output
            kwargs['i_' + name] = output
        riu_data, riu_valid = connect_core(self, generated, physical, kwargs)
        platform.add_source(str(core))

        # Control runs in the DFI domain; implementation checks its timing.
        # Reset release is deterministic: clocks off, reset asserted, reset
        # removed, 64 settling cycles, then enable CLKOUTPHY and await BISC.
        count = Signal(8)
        phy_reset, ctrl_reset = Signal(reset=1), Signal(reset=1)
        locked = Signal()
        self.specials += MultiReg(pll_locked, locked)
        self.sync += If(self._rst.storage | ~locked,
            count.eq(0), phy_reset.eq(1), ctrl_reset.eq(1), pll_enable.eq(0)
        ).Else(
            If(count != 255, count.eq(count + 1)),
            If(count == 63, phy_reset.eq(0), ctrl_reset.eq(0)),
            If(count == 127, pll_enable.eq(1)))
        ready       = Signal()
        initialized = Signal()
        dly_ready, vtc_ready = Signal(ncontrols), Signal(ncontrols)
        self.specials += MultiReg(signals['o_dly_rdy'], dly_ready), MultiReg(signals['o_vtc_rdy'], vtc_ready)
        riu_reset, riu_vtc = Signal(reset=1), Signal()
        vtc_request = Signal()
        if riu_domain == 'sys':
            self.comb += riu_reset.eq(ctrl_reset)
            self.sync += riu_vtc.eq(vtc_request)
        else:
            self.sync.riu += [riu_reset.eq(ctrl_reset), riu_vtc.eq(vtc_request)]
        self.submodules.riu_transaction = transaction = RIUTransaction(ncontrols, mapping.riu_indices)
        self.submodules.riu_launch = launch = RIUFallingLaunch(transaction, platform)
        self.comb += [
            transaction.request.eq(pulse['riu_write'] | pulse['riu_read']),
            transaction.write.eq(pulse['riu_write']), transaction.reset.eq(ctrl_reset | ~ready),
            transaction.address.eq(self._riu_address.storage),
            transaction.select.eq(self._riu_nibble.storage),
            transaction.wdata.eq(self._riu_wdata.storage),
            transaction.native_rdata.eq(riu_data), transaction.native_valid.eq(riu_valid),
            self._riu_busy.status.eq(transaction.busy), self._riu_error.status.eq(transaction.error)]
        self.sync += If(self._rst.storage | ~locked, initialized.eq(0)).Elif(
            pll_enable & (dly_ready == ready_mask) & (vtc_ready == ready_mask), initialized.eq(1))
        # Register readiness before high-fanout training/PHY control.
        self.sync += ready.eq(initialized & locked & (dly_ready == ready_mask) & ~self._rst.storage)
        self.comb += [
            self._ready.status.eq(ready), self._dly_rdy.status.eq(dly_ready),
            self._vtc_rdy.status.eq(vtc_ready), self._fifo_empty.status.eq(fifo_empty),
            signals['i_div_clk'].eq(ClockSignal()), signals['i_riu_clk'].eq(ClockSignal(riu_domain)),
            signals['i_pll_clk'].eq(pll_clk), signals['i_rst'].eq(riu_reset),
            signals['i_clb2phy_tristate_odelay_rst'].eq(riu_reset),
            vtc_request.eq(self._en_vtc.storage & pll_enable & (dly_ready == ready_mask)),
            slice_vtc.eq(~initialized | self._en_vtc.storage),
            signals['i_en_vtc'].eq(riu_vtc),
            signals['i_riu_addr'].eq(launch.address),
            signals['i_riu_wr_data'].eq(launch.wdata),
            signals['i_riu_nibble_sel'].eq(launch.select),
            signals['i_riu_wr_en'].eq(launch.write),
            self._riu_rdata.status.eq(transaction.rdata),
            self._riu_valid.status.eq(transaction.valid),
            # UG571: controller TBYTE_IN is active-high output enable;
            # TX_BITSLICE_TRI inverts it into active-high buffer tristate.
            # Keep zero throughout reset, including TX_OUTPUT_PHASE_90 reset.
            signals['i_cmd_tbyte'].eq(Mux(ready, 15, 0)),
            pads.reset_n.eq(dfi.phases[0].reset_n & ready & ~self._bisc_only.storage),
        ]
        # Status remains accessible with native clocks disabled. Snapshot and
        # fault bits survive software PHY reset; only debug_clear clears them.
        elapsed = Signal(32)
        first_dly, first_vtc = Signal(32), Signal(32)
        faults = Signal(3)
        previous_lock, previous_dly, previous_vtc = Signal(), Signal(), Signal()
        status = Cat(locked, pll_enable, phy_reset, ctrl_reset, slice_vtc,
            riu_vtc, initialized, ready, dly_ready, vtc_ready, count)
        self.comb += [self._debug.status.eq(status), self._elapsed.status.eq(elapsed),
            self._first_dly.status.eq(first_dly), self._first_vtc.status.eq(first_vtc),
            self._faults.status.eq(faults)]
        self.sync += [
            previous_lock.eq(locked), previous_dly.eq(dly_ready == ready_mask),
            previous_vtc.eq(vtc_ready == ready_mask),
            If(self._rst.storage, elapsed.eq(0)).Elif(elapsed != 0xffffffff, elapsed.eq(elapsed + 1)),
            If(self._debug_clear.wr_stb,
                first_dly.eq(0), first_vtc.eq(0), faults.eq(0), self._snapshot_status.status.eq(0)
            ).Else(
                If((first_dly == 0) & (dly_ready == ready_mask), first_dly.eq(elapsed)),
                If((first_vtc == 0) & (vtc_ready == ready_mask), first_vtc.eq(elapsed)),
                If(previous_lock & ~locked, faults[0].eq(1)),
                If(previous_dly & (dly_ready != ready_mask) & ~self._rst.storage, faults[1].eq(1)),
                If(previous_vtc & (vtc_ready != ready_mask) & self._en_vtc.storage & ~self._rst.storage, faults[2].eq(1)),
                If(self._snapshot.wr_stb | (previous_lock & ~locked), self._snapshot_status.status.eq(status)))]
        # CK is 01010101, so its rising edges are slots 0,2,4,6. Change CA
        # on the preceding falling edge: p0 at slots 1/2, p1 at 3/4, etc.
        # This deliberately adds one CK of command latency. Slot 0 holds
        # previous-cycle p3; slot 7 carries current-cycle p3 across the boundary.
        ca = {'adr': ('address', 17), 'ba': ('bank', 2), 'bg': ('bank', 1),
              'cs_n': ('cs_n', 1), 'cke': ('cke', 1), 'odt': ('odt', 1), 'act_n': ('act_n', 1)}
        for name, (field, width) in ca.items():
            for bit in range(width):
                values = [(getattr(p, ('we_n', 'cas_n', 'ras_n')[bit-14])[0]
                    if name == 'adr' and bit >= 14 else getattr(p, field)[bit + (2 if name == 'bg' else 0)])
                    for p in dfi.phases]
                previous = Signal(reset=1 if name in ('cs_n', 'act_n') else 0)
                self.sync += previous.eq(values[3])
                self.comb += signals['i_'+name+'_tx_data'][8*bit:8*bit+8].eq(
                    Cat(previous, values[0], values[0], values[1], values[1], values[2], values[2], values[3]))
            pad = Cat(pads.a, pads.we_n, pads.cas_n, pads.ras_n) if name == 'adr' else getattr(pads, name)
            self.comb += pad.eq(signals['o_'+name+'_serial_out'])
        self.specials += Instance('OBUFDS', i_I=signals['o_ck_t_serial_out'], o_O=pads.clk_p, o_OB=pads.clk_n)

        wr = TappedDelayLine(reduce(or_, [p.wrdata_en for p in dfi.phases]), ntaps=6)
        rd = TappedDelayLine(reduce(or_, [p.rddata_en for p in dfi.phases]), ntaps=32)
        self.submodules += wr, rd
        # Profile write latency selects the DFI enable tap. It increases at
        # higher rates to account for the additional controller pipeline.
        oe = wr.taps[write_latency]
        pre, post = wr.taps[write_latency-1] & ~oe, wr.taps[write_latency+1] & ~oe
        dqs_oe = oe | pre | post | self._wlevel_en.storage
        # T_OUT -> IOB.T is a dedicated route. DQ/DM use the native T input
        # with a registered drive window; write leveling releases DQ/DM while
        # DQS continues to use the native TX_BITSLICE_TRI serialized control.
        self.submodules.data_drive_delay = data_drive = TappedDelayLine(oe | pre | post, ntaps=1)
        self.comb += data_tristate.eq(~ready | self._wlevel_en.storage | ~data_drive.output)
        # Match the working USDDRPHY: its normal DQS pattern continues
        # toggling throughout the enable window. Connecting the optional
        # pre/post patterns inserts gaps that can enter the write burst as
        # native output delay/bitslip changes. Keep WL's single pulse.
        self.submodules.dqs_pattern = pattern = DQSPattern(
            wlevel_en=self._wlevel_en.storage, wlevel_strobe=pulse['wlevel_strobe'])
        selected_pattern = Signal(8)
        self.tx_pattern  = selected_pattern
        self.tx_window   = dict(oe=oe, pre=pre, post=post)
        self.comb += selected_pattern.eq(Mux(self._wlevel_en.storage, pattern.o,
            Mux(oe, 0x55, Mux(post, self._tx_dqs_post.storage,
                Mux(pre, self._tx_dqs_pre.storage, self._tx_dqs_idle.storage)))))
        # Register TBYTE at its final driver: an OR across advancing taps
        # can glitch during pre/active/post handoffs. Computing one cycle
        # earlier preserves the ordinary write window exactly.
        dqs_drive      = Signal()
        self.dqs_drive = dqs_drive
        self.sync += dqs_drive.eq(ready & (wr.taps[write_latency-2] | wr.taps[write_latency-1] |
            wr.taps[write_latency] | self._wlevel_en.storage))
        self.comb += signals['i_data_tbyte'].eq(Replicate(dqs_drive, 4*ncontrols))
        # A read request opens the native gate for a burst plus margins. The
        # gate position must be trained; it is not assumed to equal IOSERDES.
        for byte in range(2):
            override = self.software_control & self._gate_override.storage[byte]
            delay    = Mux(override, getattr(self, '_gate_delay'+str(byte)).storage, self._gate_delay.storage)
            # A BL8 burst spans one fabric cycle. Hardware MPR tests show
            # the former two-cycle window admits unwanted trailing edges.
            width     = Mux(override, getattr(self, '_gate_width'+str(byte)).storage, 1)
            gate      = Array(rd.taps)[delay]
            remaining = Signal(4)
            self.sync += If(self._rst.storage, remaining.eq(0)).Elif(gate,
                remaining.eq(Mux(width > 1, Mux(width > 8, 7, width-1), 0))
            ).Elif(remaining != 0, remaining.eq(remaining-1))
            for control in layout.lanes[byte].controls:
                self.comb += signals['i_phy_rden'][4*control:4*control+4].eq(
                    Replicate((gate | (remaining != 0) | self._wlevel_en.storage) & ready, 4))
        for control in set(range(ncontrols)) - set(mapping.data_controls):
            self.comb += signals['i_phy_rden'][4*control:4*control+4].eq(0)
        # Native FIFOs must not be read past empty when DQS stops between
        # bursts. A registered inverted EMPTY can overrun by one word and
        # repeatedly expose old contents. Drain only when every DQ FIFO has
        # a word, aligning the independent DQS domains at this interface.
        lane_available = []
        for byte in range(2):
            empty = reduce(or_, [fifo_empty[sites[f'o_dq_serial_out[{i}]']]
                                for i in range(8*byte, 8*byte+8)])
            lane_available.append(~empty)
        common_available = lane_available[0] & lane_available[1]
        for byte in range(2):
            drain = Signal()
            reads = getattr(self, '_fifo_reads'+str(byte)).status
            self.comb += drain.eq(ready & Mux(self.software_control & self._fifo_lane_mode.storage,
                                             lane_available[byte], common_available))
            self.sync += If(self._debug_clear.wr_stb, reads.eq(0)).Elif(drain, reads.eq(reads+1))
            lane = layout.lanes[byte]
            for tap in lane.dq + (lane.strobe,) + (() if lane.mask is None else (lane.mask,)):
                self.comb += signals['i_fifo_rd_en'][tap].eq(drain & ready)
        for tap in set(range(ntaps)) - set(lane_by_tap):
            self.comb += signals['i_fifo_rd_en'][tap].eq(0)

        for byte in range(2):
            slip = BitSlip(8, i=selected_pattern, rst=self._rst.storage |
                (self._dly_sel.storage[byte] & pulse['wdly_dq_bitslip_rst']),
                slp=self._dly_sel.storage[byte] & pulse['wdly_dq_bitslip'])
            self.submodules += slip
            self.comb += dqs_data[8*byte:8*byte+8].eq(slip.o)
            self.specials += Instance('IOBUFDS', i_I=signals['o_dqs_t_serial_out'][byte],
                i_T=signals['o_dqs_t_tristate'][byte],
                o_O=signals['i_dqs_t_serial_in'][byte], io_IO=pads.dqs_p[byte], io_IOB=pads.dqs_n[byte])
        for name, width, padname in [('dq', 16, 'dq'), ('dm_n', 2, 'dm')]:
            for bit in range(width):
                byte = bit//8 if name == 'dq' else bit
                y    = sites[f'o_{name}_serial_out[{bit}]']
                dyn  = bit if name == 'dq' else 16 + bit
                self.specials += Instance('IOBUF_DCIEN',
                    i_I=signals[f'o_{name}_serial_out'][bit],
                    i_T=signals[f'o_{name}_tristate'][bit],
                    i_IBUFDISABLE=0, i_DCITERMDISABLE=signals['o_dyn_dci'][dyn],
                    o_O=signals[f'i_{name}_serial_in'][bit], io_IO=getattr(pads, padname)[bit])
                data = Cat(*[(dfi.phases[s//2].wrdata[(s%2)*16+bit] if name=='dq'
                    else ~dfi.phases[s//2].wrdata_mask[(s%2)*2+bit]) for s in range(8)])
                tx = BitSlip(8, i=data, rst=self._rst.storage |
                    (self._dly_sel.storage[byte] & pulse['wdly_dq_bitslip_rst']),
                    slp=self._dly_sel.storage[byte] & pulse['wdly_dq_bitslip'])
                self.submodules += tx
                self.comb += signals[f'i_{name}_tx_data'][8*bit:8*bit+8].eq(tx.o)
                if name == 'dq':
                    rx = NativeRXBitslip(i=signals['o_dq_rx_data'][8*bit:8*bit+8],
                        rst=self._rst.storage | (self._dly_sel.storage[byte] & pulse['rdly_dq_bitslip_rst']),
                        slp=self._dly_sel.storage[byte] & pulse['rdly_dq_bitslip'])
                    self.submodules += rx
                    for s in range(8):
                        self.comb += dfi.phases[s//2].rddata[(s%2)*16+bit].eq(rx.o[s])
        tap_valid   = reduce(or_, [self._tap_select.storage == y for y in sites.values()])
        tap_allowed = self.software_control & ready & ~self._en_vtc.storage & tap_valid
        self.comb += self._tap_allowed.status.eq(tap_allowed)
        # Every delay update and selector change invalidates the settled view.
        previous_select = Signal(len(self._tap_select.storage))
        self.sync += previous_select.eq(self._tap_select.storage)
        status_change = ((previous_select != self._tap_select.storage) |
            reduce(or_, rx_rst_request) | reduce(or_, rx_ce_request) |
            reduce(or_, tx_rst_request) | reduce(or_, tx_ce_request))
        status_valid = []
        for kind, source in (('rx', rx_count), ('tx', tx_count)):
            tree = RegisteredTapStatus(ntaps)
            setattr(self.submodules, 'tap_status_' + kind, tree)
            self.comb += [tree.source.eq(source), tree.select.eq(self._tap_select.storage),
                tree.change.eq(status_change), tree.ready.eq(ready & ~ctrl_reset & tap_valid),
                getattr(self, '_tap_' + kind + '_count').status.eq(tree.value)]
            status_valid.append(tree.valid)
        self.comb += self._tap_status_valid.status.eq(status_valid[0] & status_valid[1])
        for name, y in sites.items():
            byte     = lane_by_tap.get(y)
            selected = self._dly_sel.storage[byte] if byte is not None else 0
            is_dqs   = 'dqs_t' in name
            is_data  = '_dq_' in name or '_dm_n_' in name
            manual   = tap_allowed & (self._tap_select.storage == y)
            self.comb += [
                rx_rst_request[y].eq((selected & pulse['rdly_dq_rst'] if is_data else 0) | (manual & self._tap_rx_rst.wr_stb)),
                rx_ce_request[y].eq((selected & pulse['rdly_dq_inc'] if is_data else 0) | (manual & self._tap_rx_inc.wr_stb)),
                tx_rst_request[y].eq((selected & (pulse['wdly_dqs_rst'] if is_dqs else pulse['wdly_dq_rst'])
                    if is_data or is_dqs else pulse['cdly_rst']) | (manual & self._tap_tx_rst.wr_stb)),
                tx_ce_request[y].eq((selected & (pulse['wdly_dqs_inc'] if is_dqs else pulse['wdly_dq_inc'])
                    if is_data or is_dqs else pulse['cdly_inc']) | (manual & self._tap_tx_inc.wr_stb))]
        for y in set(range(ntaps)) - set(sites.values()):
            self.comb += [rx_rst_request[y].eq(0), rx_ce_request[y].eq(0), tx_rst_request[y].eq(0), tx_ce_request[y].eq(0)]
        dqs_counts = [tx_count[9*sites[f'o_dqs_t_serial_out[{b}]']:9*sites[f'o_dqs_t_serial_out[{b}]']+9]
                      for b in range(2)]
        self.comb += self._wdly_dqs_inc_count.status.eq(Mux(self._dly_sel.storage[1], dqs_counts[1], dqs_counts[0]))
        ck = sites['o_ck_t_serial_out[0]']
        self.comb += self._cdly_value.status.eq(tx_count[9*ck:9*ck+9])
        valid = rd.taps[self.settings.read_latency-1]
        for p in dfi.phases:
            self.comb += p.rddata_valid.eq((valid & ready) | self._wlevel_en.storage)
        self.comb += self._read_latency.status.eq(self.settings.read_latency)

        # Capture fabric-side native data/status only: no additional loads on
        # dedicated serial DATAIN or T_OUT routes. First sample follows trigger.
        if with_debug:
            trace      = Memory(256, 64)
            write_port = trace.get_port(write_capable=True)
            read_port  = trace.get_port()
            self.specials += trace, write_port, read_port
            pending, running = Signal(), Signal()
            pointer = Signal(6)
            trigger = rd.input | pulse['wlevel_strobe']
            self.comb += [
                self._trace_state.status.eq(Cat(pending, running)),
                write_port.adr.eq(pointer), write_port.we.eq(running),
                write_port.dat_w.eq(Cat(signals['o_dq_rx_data'], fifo_empty,
                    ready, rd.input, pulse['wlevel_strobe'], self._wlevel_en.storage,
                    data_tristate, dqs_drive, signals['i_phy_rden'], selected_pattern, dqs_data[:8])),
                read_port.adr.eq(self._trace_index.storage)]
            for word in range(8):
                self.comb += getattr(self, '_trace_word'+str(word)).status.eq(read_port.dat_r[32*word:32*word+32])
            self.sync += If(self._trace_arm.wr_stb,
                pending.eq(1), running.eq(0), pointer.eq(0), self._trace_done.status.eq(0)
            ).Elif(pending & trigger,
                pending.eq(0), running.eq(1), pointer.eq(0)
            ).Elif(running,
                If(pointer == 63, running.eq(0), self._trace_done.status.eq(1))
                .Else(pointer.eq(pointer+1)))
