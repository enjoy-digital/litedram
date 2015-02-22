from litedram.common import *

class LiteDRAMCore(Module):
	def __init__(self, phy, sdram):
		nbanks = 2**sdram.geom_settings.bank_a
		aw = 0 # XXX
		dw = 0 # XXX
		self.ports = ports = [LiteDRAMPorts(aw, dw) for i in range(nbanks)]

		self.submodules.refresher = refresher = Refresher(sdram)

		banks = []
		for i in range(2**sdram.geom_settings.bank_a):
			bank = BankMachine(phy, sdram, i)
			self.submodules += bank
			self.banks.append(bank)
			self.comb += [
				Record.connect(self.ports[i].write.cmd, bank.write_cmd),
				Record.connect(self.ports[i].read.cmd, bank.read_cmd)
			]

		self.submodules.multiplexer = Multiplexer(phy, sdram, banks, refresher)
