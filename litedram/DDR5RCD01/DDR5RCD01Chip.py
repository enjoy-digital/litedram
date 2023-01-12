#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# RCD
from litedram.DDR5RCD01.DDR5RCD01BCOMSimulationPads import DDR5RCD01BCOMSimulationPads
from litedram.DDR5RCD01.DDR5RCD01CoreEgressSimulationPads import DDR5RCD01CoreEgressSimulationPads
from litedram.DDR5RCD01.DDR5RCD01Core import DDR5RCD01Core
from litedram.DDR5RCD01.I2CSlave import I2CSlave
from litedram.DDR5RCD01.I3CSlave import I3CSlave


class DDR5RCD01Chip(Module):
    """DDR5 RCD01 Chip
    TODO clean up imports
    TODO clean up parameters
    """

    def __init__(self, pads_ingress, pads_sideband, aligned_reset_zero=False, dq_dqs_ratio=8,
                 nranks=1, with_sub_channels=False, dimm_type='RDIMM', sideband_type='i2c', **kwargs):

        self.submodules.pads_ingress = pads_ingress
        self.submodules.pads_sideband = pads_sideband

        pads_egress = DDR5RCD01CoreEgressSimulationPads(databits=4,
                                                        nranks=nranks,
                                                        dq_dqs_ratio=4,
                                                        with_sub_channels=with_sub_channels)
        self.submodules.pads_egress = pads_egress

        # Sideband traffic handler
        if sideband_type == 'i2c':
            iXC_slave = I2CSlave(pads_sideband)
        elif sideband_type == 'i3c':
            iXC_slave = I3CSlave(pads_sideband)
        else:
            raise (NotImplemented, 'Only i2c and i3c are supported options.')
        sideband_2_core = iXC_slave.sideband_2_core

        core = DDR5RCD01Core(pads_ingress, sideband_2_core)
        if dimm_type == 'RDIMM':
            # TODO potentially remove this if
            pass
        if dimm_type == 'LRDIMM':
            # TODO Implement BCOM traffic handler
            pads_bcom = DDR5RCD01BCOMSimulationPads(databits=4,
                                                    nranks=nranks,
                                                    dq_dqs_ratio=4,
                                                    with_sub_channels=with_sub_channels)

            pads_bcom = core.pads_bcom
            # TODO replace print with preffered style of logging
            print('Warning : LRDIMM is not supported')


if __name__ == "__main__":
    raise NotImplementedError("Test of this block is to be done.")
