#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Falling-edge RIU launch registers for the native input hold-time boundary."""

from pathlib import Path
from migen import *

class RIUFallingLaunch(Module):
    """Preserve native rising-edge samples, adding half-cycle hold margin.

    Upstream RIUTransaction registers remain on rising edges. Their synchronous
    reset values travel through this stage with the same native sampling epoch.
    No independent reset is introduced at the boundary.
    """
    def __init__(self, transaction, platform):
        self.address = Signal(6)
        self.select  = Signal(len(transaction.native_select))
        self.wdata   = Signal(16)
        self.write   = Signal()
        payload = Cat(transaction.native_address, transaction.native_select,
                    transaction.native_wdata, transaction.native_write)
        launch = Cat(self.address, self.select, self.wdata, self.write)
        self.specials += Instance('usnative_riu_falling_launch', p_WIDTH=len(payload),
            i_clk=ClockSignal('riu'), i_payload=payload, o_launch=launch)
        platform.add_source(str(Path(__file__).resolve().with_name('riu_falling_launch.v')))
