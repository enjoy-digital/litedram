#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Explicit ownership of optional DDR4 PAR/ALERT pads.

Only parity-disabled, write-CRC-disabled initialization is implemented. The
caller must validate the actual MR2/MR5 values emitted by its initialization
sequence, and must not enable either feature later through software DFI.
"""

from dataclasses import dataclass

from migen import If, Instance, Module, Signal
from migen.genlib.cdc import MultiReg


@dataclass(frozen=True)
class SidebandPlan:
    native_sites: dict
    parity: tuple
    alert: tuple
    alert_unavailable_during_calibration: bool


def sideband_plan(sites, *, mr2, mr5):
    """Separate PAR/ALERT ownership after checking the supported mode-register settings."""
    for value in (mr2, mr5):
        if type(value) is not int or not 0 <= value < 65536:
            raise ValueError('Mode registers must be unsigned 16-bit integers')
    if mr5 & 7:
        raise ValueError('Native PAR handling requires CA parity disabled in MR5')
    if mr2 & (1 << 12):
        raise ValueError('Native sideband handling requires write CRC disabled in MR2')
    parity = tuple(key for key in sites if key[0] in ('par', 'parity'))
    alert = tuple(key for key in sites if key[0] == 'alert_n')
    if len(parity) > 1 or len(alert) > 1 or any(index != 0 for _, index in parity + alert):
        raise ValueError('Only one PAR and one ALERT pad are supported')
    native = {key: site for key, site in sites.items() if key not in parity + alert}
    unavailable = any(sites[key].position in (0, 6) and any(
        (site.bank, site.byte) == (sites[key].bank, sites[key].byte)
        for (name, _), site in native.items() if name not in ('reset_n', 'clk_n', 'dqs_n'))
        for key in alert)
    return SidebandPlan(native, parity, alert, unavailable)


class NativeSidebands(Module):
    """Static PAR output and synchronized, sticky ALERT diagnostic.

    The caller enables monitoring only after BISC and input synchronization.
    ALERT is sampled as a level; narrow pulses are not guaranteed to be captured.
    An active alert takes priority over clear. This is diagnostic monitoring,
    not parity/CRC error recovery or a substitute for a board pull-up.
    """
    def __init__(self, pads, plan):
        self.clear = Signal()
        self.enable = Signal()
        self.active = Signal()
        self.seen = Signal()
        for name, index in plan.parity:
            self.specials += Instance('OBUF', i_I=0, o_O=getattr(pads, name)[index])
        self.alert_n = Signal(reset=1)
        if plan.alert:
            name, index = plan.alert[0]
            self._raw_alert_n = raw = Signal(reset=1)
            self.specials += Instance('IBUF', i_I=getattr(pads, name)[index], o_O=raw)
            self.specials += MultiReg(raw, self.alert_n, reset=1)
        else:
            self.comb += self.alert_n.eq(1)
        self.comb += self.active.eq(self.enable & ~self.alert_n)
        self.sync += If(self.active, self.seen.eq(1)).Elif(self.clear, self.seen.eq(0))
