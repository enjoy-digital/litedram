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

class DDR5RCD01CoreEgressSimulationPads(SimulationPads):
    """ DDR5 RCD01 Core Egress SimulationPads
    """

    def layout(self, dcs_n_w=2, dca_w=14, is_dual_channel=False):
        A_channel = [
            # Loopback sources
            ('A_dlbd', 1, False),
            ('A_dlbs', 1, False),
            # SDRAM raises an error
            ('A_derror_in_n', 1, False),
            # Reset
            ('A_qrst_n', 1, False),
            # Adress, Chip Select
            # Top Row
            ('A_qacs_a_n', dcs_n_w, False),
            ('A_qaca_a', dca_w, False),
            # Bottom Row
            ('A_qacs_b_n', dcs_n_w, False),
            ('A_qaca_b', dca_w, False),
            # Clock outputs
            # Rank 0, Row Top
            ('A_qack_t', 1, False),
            ('A_qack_c', 1, False),
            # Rank 1, Row Top
            ('A_qbck_t', 1, False),
            ('A_qbck_c', 1, False),
            # Rank 0, Row Bottom
            ('A_qcck_t', 1, False),
            ('A_qcck_c', 1, False),
            # Rank 1, Row Top
            ('A_qdck_t', 1, False),
            ('A_qdck_c', 1, False),
        ]
        ingress_A_channel = [SimPad(name, size, io)
                             for name, size, io in A_channel]

        if is_dual_channel:
            B_channel = [
                # Loopback sources
                ('B_dlbd', 1, False),
                ('B_dlbs', 1, False),
                # SDRAM raises an error
                ('B_derror_in_n', 1, False),
                # Reset
                ('B_qrst_n', 1, False),
                # Adress, Chip Select
                # Top Row
                ('B_qacs_a_n', dcs_n_w, False),
                ('B_qaca_a', dca_w, False),
                # Bottom Row
                ('B_qacs_b_n', dcs_n_w, False),
                ('B_qaca_b', dca_w, False),
                # Clock outputs
                # Rank 0, Row Top
                ('B_qack_t', 1, False),
                ('B_qack_c', 1, False),
                # Rank 1, Row Top
                ('B_qbck_t', 1, False),
                ('B_qbck_c', 1, False),
                # Rank 0, Row Bottom
                ('B_qcck_t', 1, False),
                ('B_qcck_c', 1, False),
                # Rank 1, Row Top
                ('B_qdck_t', 1, False),
                ('B_qdck_c', 1, False),
            ]
            ingress_B_channel = [SimPad(name, size, io)
                                 for name, size, io in B_channel]

        if is_dual_channel:
            return ingress_A_channel+ingress_B_channel
        else:
            return ingress_A_channel


if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
