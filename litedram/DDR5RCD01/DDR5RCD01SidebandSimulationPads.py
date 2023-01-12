#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# LiteDRAM
from litedram.phy.sim_utils import SimPad, SimulationPads


class DDR5RCD01SidebandSimulationPads(SimulationPads):
    """ DDR5 RCD01 Sideband SimulationPads
    TODO Documentation
    TODO layout parameters fix
    """

    def layout(self):
        sideband = [
            SimPad('sda', 1),
            SimPad('scl', 1),
        ]
        return sideband


if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
