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


class DDR5RCD01CoreIngressSimulationPads(SimulationPads):
    """ DDR5 RCD01 Core Ingress SimulationPads
    """

    def layout(self, dcs_n_w=2, dca_w=7, is_dual_channel=False):
        common = [
            # Clock
            SimPad('dck_t', 1),
            SimPad('dck_c', 1),
            # Reset input (Comes from MC)
            SimPad('drst_n', 1),
            # Loopback
            SimPad('qlbd', 1),
            SimPad('qlbs', 1),
            # Raise errors
            SimPad('alert_n', 1),
        ]

        A_channel = [
            # Address/Command
            ('A_dcs_n', dcs_n_w, False),
            ('A_dca', dca_w, False),
            # Parity
            ('A_dpar', 1, False),
        ]

        ingress_A_channel = [SimPad(name, size, io)
                             for name, size, io in A_channel]

        if is_dual_channel:
            B_channel = [
                # Address/Command
                ('B_dcs_n', dcs_n_w, False),
                ('B_dca', dca_w, False),
                # Parity
                ('B_dpar', 1, False),
            ]
            ingress_B_channel = [SimPad(name, size, io)
                                 for name, size, io in B_channel]
        else:
            ingress_B_channel = []

        if is_dual_channel:
            return common + ingress_A_channel
        else:
            return common + ingress_A_channel + ingress_B_channel


if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
