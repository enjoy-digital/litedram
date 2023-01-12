#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# Litedram
from litedram.phy.sim_utils import SimPad, SimulationPads


class DDR5RCD01BCOMSimulationPads(SimulationPads):
    """ DDR5 RCD01 Core Ingress SimulationPads
    """

    def layout(self, is_dual_channel=True):
        # BCOM is only used by LRDIMM
        bcom = [
            ('bcs_n', 1, False),
            ('bcom', 3, False),
            ('brst_n', 1, False),
            ('bck_t', 1, False),
            ('bck_c', 1, False),
        ]
        channels_prefix = [""] if not is_dual_channel else ["A_", "B_"]
        return [SimPad(prefix+name, size, io) for prefix in channels_prefix for name, size, io in bcom]


if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
