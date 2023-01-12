#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# LiteDRAM : RCD
from litedram.DDR5RCD01.DDR5RCD01SidebandSimulationPads import DDR5RCD01SidebandSimulationPads


class I2CSlave(Module):
    """ I2C Slave
    TODO Documentation
    """

    def __init__(self, pads_sideband, **kwargs):
        # TODO implementation
        # When implementing change the Sideband Simulation Pads.
        # This is only here to provide some connection.
        sideband_2_core = DDR5RCD01SidebandSimulationPads()
        self.submodules.sideband_2_core = sideband_2_core


if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
