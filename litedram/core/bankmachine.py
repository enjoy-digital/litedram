from migen.fhdl.std import *
from migen.genlib.roundrobin import *
from migen.genlib.fsm import FSM, NextState
from migen.genlib.misc import optree
from migen.genlib.fifo import SyncFIFO

from litedram.core.multiplexer import *

class _AddressSlicer:
	def __init__(self, col_a, address_align):
		self.col_a = col_a
		self.address_align = address_align

	def row(self, address):
		split = self.col_a - self.address_align
		if isinstance(address, int):
			return address >> split
		else:
			return address[split:]

	def col(self, address):
		split = self.col_a - self.address_align
		if isinstance(address, int):
			return (address & (2**split - 1)) << self.address_align
		else:
			return Cat(Replicate(0, self.address_align), address[:split])

class LiteDRAMRowTracker(Module):
	def __init__(self, rw):
		self.row = Signal(rw)
		self.open = Signal()
		self.close = Signal()
		###
		self._has_openrow = Signal()
		self._openrow = Signal(rw)
		self.sync += [
			If(self.open,
				self._has_openrow.eq(1),
				self._openrow.eq(self.row)
			).Elif(self.close,
				self._has_openrow.eq(0)
			)
		]

	def row_hit(self, row):
		return self._openrow == row

class LiteDRAMBankMachine(Module):
	def __init__(self, sdram, bankn, cmd_fifo_depth):
		self.refresh = Sink(dram_refresh_description)
		self.write_cmd = Sink(dram_cmd_description(aw))
		self.read_cmd = Sink(dram_cmd_description(aw))

		self.cmd = Source(dram_bank_cmd_description())
		###

		read_write_n = FlipFlop()
		self.comb += read_write_n.d.eq(1)
		self.submodules += FlipFlop()

		# Cmd fifos
		write_cmd_fifo = SyncFIFO(self.write_cmd.description, cmd_fifo_depth)
		read_cmd_fifo = SyncFIFO(self.read_cmd.description, cmd_fifo_depth)
		self.submodules += write_cmd_fifo, read_cmd_fifo
		self.comb += [
			Record.connect(self.write_cmd, write_cmd_fifo.sink),
			Record.connect(self.read_cmd, read_cmd_fifo.sink)
		]

		# Cmd mux
		mux = Multiplexer(dram_cmd_description(32), 2)
		self.submodules += mux
		self.comb += [
			mux.sel.eq(reading),
			Record.connect(write_cmd_fifo.source, mux.sink0),
			Record.connect(read_cmd_fifo.source, mux.sink1)
		]

		slicer = _AddressSlicer(sdram.geom_settings.col_a, address_align)

		# Row tracking
		row_tracker = LiteDRAMRowTracker(sdram.geom_settings.row_a)
		self.submodules += row_tracker

		# Respect write-to-precharge specification
		precharge_ok = Signal()
		t_unsafe_precharge = 2 + timing_settings.tWR - 1
		unsafe_precharge_count = Signal(max=t_unsafe_precharge+1)
		self.comb += precharge_ok.eq(unsafe_precharge_count == 0)
		self.sync += [
			If(self.cmd.stb & self.cmd.ack & self.cmd.is_write,
				unsafe_precharge_count.eq(t_unsafe_precharge)
			).Elif(~precharge_ok,
				unsafe_precharge_count.eq(unsafe_precharge_count-1)
			)
		]

		write_available = Signal()
		write_hit = Signal()
		self.comb += [
			write_available.eq(write_cmd_fifo.source.stb)
			write_hit.eq(tracker.row_hit(slicer.row(write_cmd_fifo.source.adr)))
		]

		read_available = Signal()
		read_hit = Signal()
		self.comb += [
			read_available.eq(read_cmd_fifo.source.stb)
			read_hit.eq(tracker.row_hit(slicer.row(read_cmd_fifo.source.adr)))
		]

		# Control and command generation FSM
		self.submodules.fsm = fsm = FSM(idle_state="WRITE")
		fsm.act("WRITE",
			read_write_n.reset.eq(1),
			If(self.refresh.stb,
				NextState("REFRESH")
			).Else(
				If(~write_available & read_available, # XXX add anti starvation
					NextState("READ")
				).Else(
					If(tracker.hasopenrow,
						If(write_hit,
							self.cmd.stb.eq(1),
							self.cmd.is_read.eq(0),
							self.cmd.is_write.eq(1),
							self.cmd.cas_n.eq(0),
							self.cmd.we_n.eq(0)
							write_cmd_fifo.source.stb.eq(self.cmd.ack)
						).Else(
							NextState("PRECHARGE")
						)
					).Else(
						NextState("ACTIVATE")
					)
				)
			)
		)
		fsm.act("READ",
			read_write_n.ce.eq(1),
			If(self.refresh.stb,
				NextState("REFRESH")
			).Else(
				If(~read_available & write_available, # XXX add anti starvation
					NextState("READ")
				).Else(
					If(tracker.hasopenrow,
						If(write_hit,
							self.cmd.stb.eq(1),
							self.cmd.is_read.eq(1),
							self.cmd.is_write.eq(0),
							self.cmd.cas_n.eq(0),
							self.cmd.we_n.eq(1)
							read_cmd_fifo.source.stb.eq(self.cmd.ack)
						).Else(
							NextState("PRECHARGE")
						)
					).Else(
						NextState("ACTIVATE")
					)
				)
			)
		)
		fsm.act("PRECHARGE",
			# Notes:
			# 1. we are presenting the column address, A10 is always low
			# 2. since we always go to the ACTIVATE state, we do not need
			# to assert tracker.close.
			If(precharge_ok,
				self.cmd.stb.eq(1),
				self.cmd.ras_n.eq(0),
				self.cmd.we_n.eq(0),
				self.cmd.is_cmd.eq(1),
				If(read_write_n,
					self.cmd.adr.eq(slicer.col(read_cmd_fifo.adr))
				).Else(
					self.cmd.adr.eq(slicer.col(write_cmd_fifo.adr))
				),
				If(self.cmd.ack, NextState("TRP")),
			)
		)
		fsm.act("ACTIVATE",
			tracker.open.eq(1),
			self.cmd.stb.eq(1),
			self.cmd.is_cmd.eq(1),
			If(read_write_n,
				self.cmd.adr.eq(slicer.row(read_cmd_fifo.adr))
			).Else(
				self.cmd.adr.eq(slicer.row(write_cmd_fifo.adr))
			),
			If(self.cmd.ack, NextState("TRCD")),
			self.cmd.ras_n.eq(0)
		)
		fsm.act("REFRESH",
			self.refresh.ack.eq(precharge_ok),
			tracker.close.eq(1),
			self.cmd.is_cmd.eq(1),
			If(~self.refresh.stb, NextState("REGULAR"))
		)
		fsm.delayed_enter("TRP", "ACTIVATE", sdram.timing_settings.tRP-1)
		fsm.delayed_enter("TRCD", "REGULAR", sdram.timing_settings.tRCD-1)
