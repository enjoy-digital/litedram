from migen.fhdl.std import *
from migen.genlib.record import *
from migen.flow.actor import *

def dram_write_cmd_description(aw):
	payload_layout = [("adr", aw)]
	return EndpointDescription(payload_layout)

def dram_write_data_description(dw):
	payload_layout = [
		("data", dw)
		("be", dw//8)
	]
	return EndpointDescription(payload_layout)

def dram_read_cmd_description(aw):
	payload_layout = [("adr", aw)]
	return EndpointDescription(payload_layout)

def dram_read_data_description(aw):
	payload_layout = [("data", aw)]
	return EndpointDescription(payload_layout)

class LiteDRAMWritePort:
	def __init__(self, aw, dw):
		self.cmd = Sink(dram_write_cmd_description(aw, dw))
		self.data = Sink(dram_write_cmd_description(aw, dw))

	def connect(self, other):
		return [
			Record.connect(self.cmd, other.cmd),
			Record.connect(self.data, other.data)
		]

class LiteDRAMReadPort:
	def __init__(self, aw, dw):
		self.cmd = Sink(dram_read_cmd_description(aw, dw))
		self.data = Source(dram_read_cmd_description(aw, dw))

	def connect(self, other):
		return [
			Record.connect(self.cmd, other.cmd),
			Record.connect(other.data, self.data)
		]

class LiteDRAMPort:
	def __init__(self, dw):
		self.write = LiteDRAMWritePort(dw)
		self.read = LiteDRAMReadPort(dw)

	def connect(self, other):
		self.write.connect(other)
		self.read.connect(other)

def dram_bank_cmd_description(a, ba):
	payload_layout = [
		("a", a),
		("ba", ba),
		("cas_n", 1),
		("ras_n", 1),
		("we_n", 1),
		("is_cmd", 1),
		("is_read", 1),
		("is_write", 1)
	]
	return EndpointDescription(payload_layout)

