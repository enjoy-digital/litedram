#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Registered delay-tap readback with invalidation after selection or tap changes."""

from migen import *

class RegisteredTapStatus(Module):
    """Registered status tree with explicit settling invalidation.

    change must include every selection and delay-control update. 32 sys cycles
    cover the 2:1 destination clock, pulse CDC and pipeline. Native analog delay
    update settling remains subject to hardware qualification.
    """
    def __init__(self, entries):
        if not isinstance(entries, int) or entries < 1:
            raise ValueError('At least one tap-status entry is required')
        self.source = Signal(9*entries)
        self.select = Signal(max=max(2, entries))
        self.change = Signal()
        self.ready  = Signal()
        self.value  = Signal(9)
        self.valid  = Signal()
        local       = Signal(len(self.source))
        sampled     = Signal(len(self.source))
        age         = Signal(6)
        # Capture the wide status bus before reducing it in the sys domain.
        # This uses the documented related clocks, not a general CDC handshake.
        self.sync.riu += local.eq(self.source)
        self.sync += sampled.eq(local)
        # Split selection into registered groups of eight to shorten the mux
        # path. Pad the final group so every low-bit select has a defined value.
        groups = []
        for start in range(0, entries, 8):
            group = Signal(9)
            group.attr.add('dont_touch')
            values = [sampled[9*i:9*i+9] for i in range(start, min(start+8, entries))]
            values += [Constant(0, 9)]*(8-len(values))
            self.sync += group.eq(Array(values)[self.select[:3]])
            groups.append(group)
        # Match the upper selector/range check to the registered group data.
        # This also removes the CSR selector from the final mux's timing path.
        group_index = Signal(max=max(2, len(groups)))
        in_range    = Signal()
        self.sync += [
            group_index.eq(self.select[3:] if len(self.select) > 3 else 0),
            in_range.eq(self.select < entries),
        ]
        self.sync += [self.value.eq(Mux(in_range, Array(groups)[group_index], 0)),
            If(~self.ready | self.change, age.eq(0)).Elif(age<32, age.eq(age+1))]
        # Only fresh, ready samples may be consumed. The digital wait does
        # not establish the physical delay element's analog settling time.
        self.comb += self.valid.eq((age==32) & self.ready & ~self.change)
