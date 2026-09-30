#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Retimed comparator: same single enabled register stage, parallel chunks."""
from migen import Module, Signal, If


class MismatchRegisters(Module):
    def __init__(self, width, chunk_width=32):
        if width < 1 or chunk_width < 1:
            raise ValueError('Widths must be positive')
        self.a      = Signal(width)
        self.b      = Signal(width)
        self.enable = Signal()
        self.o      = Signal()
        partial     = Signal((width+chunk_width-1)//chunk_width, name='mismatch_partial')
        for index, start in enumerate(range(0, width, chunk_width)):
            end = min(start+chunk_width, width)
            self.sync += If(self.enable, partial[index].eq(self.a[start:end]!=self.b[start:end]))
        self.comb += self.o.eq(partial!=0)
