from collections import namedtuple

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.flow.actor import *


@ResetInserter()
@CEInserter()
class FlipFlop(Module):
    def __init__(self, *args, **kwargs):
        self.d = Signal(*args, **kwargs)
        self.q = Signal(*args, **kwargs)
        self.sync += self.q.eq(self.d)


@ResetInserter()
@CEInserter()
class Counter(Module):
    def __init__(self, *args, increment=1, **kwargs):
        self.value = Signal(*args, **kwargs)
        self.width = flen(self.value)
        self.sync += self.value.eq(self.value+increment)


def dram_refresh_description():
    payload_layout = [("dummy", 1)]
    return EndpointDescription(payload_layout)

def dram_cmd_description(rowbits, colbits):
    payload_layout = [("row", rowbits), ("col", colbits)]
    return EndpointDescription(payload_layout)

def dram_write_data_description(dw):
    payload_layout = [
        ("data", dw)
        ("be", dw//8)
    ]
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

def dram_bank_cmd_description(addressbits):
    payload_layout = [
        ("adr", addressbits),
        ("cas_n", 1),
        ("ras_n", 1),
        ("we_n", 1),
        ("is_cmd", 1),
        ("is_read", 1),
        ("is_write", 1)
    ]
    return EndpointDescription(payload_layout)

