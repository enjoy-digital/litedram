from migen.fhdl.std import *
from migen.genlib.roundrobin import *
from migen.genlib.misc import optree
from migen.genlib.fsm import FSM, NextState
from migen.bank.description import AutoCSR

from litedram.common import *

class _LiteDRAMCommandChooser(Module):
	def __init__(self, bank_cmds):
		self.want_reads = Signal()
		self.want_writes = Signal()
		self.want_cmds = Signal()
		a = flen(bank_cmds[0].a)
		ba = flen(banks_cmds[0]ba)
		self.cmd = Source(dram_bank_cmd_description)
		###

		nbank = len(bank_cmds)

		rr = RoundRobin(nbank, SP_CE)
		mux = Multiplexer(dram_bank_cmd_description(a, ba), nbank)
		self.submodules += rr, mux
		for i, bank_cmd in enumerate(bank_cmds):
			self.comb += [
				rr.request[i].eq(
					bank_cmd.stb &
					(	(bank_cmd.is_cmd & self.want_cmds) |
				 		(bank_cmd.is_read & self.want_reads) |
				 		(bank_cmd.is_write & self.want_writes)
					)
				),
				getattr(mux, "sink"+str(i)).eq(bank_cmd)
			]
		self.comb += rr.ce.eq(self.cmd.stb & self.cmd.ack)

class _LiteDRAMSteerer(Module):
	def __init__(self, cmds, dfi):
		ncmd = len(cmds)
		nph = len(dfi.phases)
		self.sel = [Signal(max=ncmd) for i in range(nph)]

		###

		def stb_and(cmd, attr):
			return cmd.stb & getattr(cmd, attr)

		for phase, sel in zip(dfi.phases, self.sel):
			self.comb += [
				phase.cke.eq(1),
				phase.cs_n.eq(0)
			]
			if hasattr(phase, "odt"):
				self.comb += phase.odt.eq(1)
			if hasattr(phase, "reset_n"):
				self.comb += phase.reset_n.eq(1)
			self.sync += [
				phase.address.eq(Array(cmd.a for cmd in cmds)[sel]),
				phase.bank.eq(Array(cmd.ba for cmd in cmds)[sel]),
				phase.cas_n.eq(Array(cmd.cas_n for cmd in cmds)[sel]),
				phase.ras_n.eq(Array(cmd.ras_n for cmd in cmds)[sel]),
				phase.we_n.eq(Array(cmd.we_n for cmd in cmds)[sel]),
				phase.rddata_en.eq(Array(stb_and(cmd, "is_read") for cmd in cmds)[sel]),
				phase.wrdata_en.eq(Array(stb_and(cmd, "is_write") for cmd in cmds)[sel])
			]

class LiteDRAMMultiplexer(Module, AutoCSR):
	def __init__(self, phy, sdram, banks, dfi):
		if phy.nphases != len(dfi.phases):
			raise ValueError

		# Command choosing
		bank_cmds = [bank.cmd for bank in banks]
		choose_cmd = _LiteDRAMCommandChooser(bank_cmds)
		choose_req = _LiteDRAMCommandChooser(bank_cmds)
		self.comb += [
			choose_cmd.want_reads.eq(0),
			choose_cmd.want_writes.eq(0)
		]
		if phy_settings.nphases == 1:
			self.comb += [
				choose_cmd.want_cmds.eq(1),
				choose_req.want_cmds.eq(1)
			]
		self.submodules += choose_cmd, choose_req

		# Command steering
		nop = Source(dram_bank_cmd_description(a, aw))
		commands = [nop, choose_cmd.cmd, choose_req.cmd, refresher.cmd] # nop must be 1st
		(STEER_NOP, STEER_CMD, STEER_REQ, STEER_REFRESH) = range(4)
		steerer = _LiteDRAMSteerer(commands, dfi)
		self.submodules += steerer

		# Read/write turnaround
		read_available = Signal()
		write_available = Signal()
		self.comb += [
			read_available.eq(optree("|", [cmd.stb & cmd.is_read for cmd in bank_cmds])),
			write_available.eq(optree("|", [cmd.stb & cmd.is_write for cmd in bank_cmds]))
		]

		def anti_starvation(timeout):
			en = Signal()
			max_time = Signal()
			if timeout:
				t = timeout - 1
				time = Signal(max=t+1)
				self.comb += max_time.eq(time == 0)
				self.sync += If(~en,
						time.eq(t)
					).Elif(~max_time,
						time.eq(time - 1)
					)
			else:
				self.comb += max_time.eq(0)
			return en, max_time
		read_time_en, max_read_time = anti_starvation(sdram.timing_settings.read_time)
		write_time_en, max_write_time = anti_starvation(sdram.timing_settings.write_time)

		# Refresh
		self.comb += [bank.refresh.stb.eq(refresher.req) for bank in banks]
		go_to_refresh = Signal()
		self.comb += go_to_refresh.eq(optree("&", [bank.refresh.ack for bank in banks]))

		# Datapath
		all_rddata = [p.rddata for p in dfi.phases]
		all_wrdata = [p.wrdata for p in dfi.phases]
		all_wrdata_mask = [p.wrdata_mask for p in dfi.phases]
		self.comb += [
			lasmic.dat_r.eq(Cat(*all_rddata)),
			Cat(*all_wrdata).eq(lasmic.dat_w),
			Cat(*all_wrdata_mask).eq(~lasmic.dat_we)
		]

		# Control FSM
		self.submodules.fsm = fsm = FSM()

		def steerer_sel(steerer, phy, r_w_n):
			r = []
			for i in range(phy.nphases):
				s = steerer.sel[i].eq(STEER_NOP)
				if r_w_n == "read":
					if i == phy.rdphase:
						s = steerer.sel[i].eq(STEER_REQ)
					elif i == phy.rdcmdphase:
						s = steerer.sel[i].eq(STEER_CMD)
				elif r_w_n == "write":
					if i == phy.wrphase:
						s = steerer.sel[i].eq(STEER_REQ)
					elif i == phy.wrcmdphase:
						s = steerer.sel[i].eq(STEER_CMD)
				else:
					raise ValueError
				r.append(s)
			return r

		fsm.act("READ",
			read_time_en.eq(1),
			choose_req.want_reads.eq(1),
			choose_cmd.cmd.ack.eq(1),
			choose_req.cmd.ack.eq(1),
			steerer_sel(steerer, phy, "read"),
			If(write_available,
				# TODO: switch only after several cycles of ~read_available?
				If(~read_available | max_read_time, NextState("RTW"))
			),
			If(go_to_refresh, NextState("REFRESH"))
		)
		fsm.act("WRITE",
			write_time_en.eq(1),
			choose_req.want_writes.eq(1),
			choose_cmd.cmd.ack.eq(1),
			choose_req.cmd.ack.eq(1),
			steerer_sel(steerer, phy_settings, "write"),
			If(read_available,
				If(~write_available | max_write_time, NextState("WTR"))
			),
			If(go_to_refresh, NextState("REFRESH"))
		)
		fsm.act("REFRESH",
			steerer.sel[0].eq(STEER_REFRESH),
			refresher.ack.eq(1),
			If(~refresher.stb, NextState("READ"))
		)
		fsm.delayed_enter("RTW", "WRITE", phy_settings.read_latency-1) # FIXME: reduce this, actual limit is around (cl+1)/nphases
		fsm.delayed_enter("WTR", "READ", timing_settings.tWTR-1)
