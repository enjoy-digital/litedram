#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# LiteDRAM
from litedram.phy.sim_utils import SimPad, SimulationPads
# LiteDRAM : RCD

class DDR5RCD01DataBufferSimulationPads(SimulationPads):
    """ The DDR5RCD01DataBufferSimulationPads shall provide SimulationPads 
    for the DDR5 Data Signals: dq,cb,dqs.
    Note, the pads are the same for ingress and egress traffic.
    """
    def layout(self, databits=8, nranks=1, dq_dqs_ratio=8, with_sub_channels=False):
        per_channel = [
            ('dq',32,True),
            ('cb',8,False),
            ('dqs_t',8,True),
            ('dqs_c',8,True),
        ]
        channels_prefix = [""] if not with_sub_channels else ["A_", "B_"]
        return [SimPad(prefix+name, size, io) for prefix in channels_prefix for name, size, io in per_channel]

if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
