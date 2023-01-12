#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# LiteDRAM : RCD
from litedram.DDR5RCD01.DDR5RCD01DataBufferSimulationPads import DDR5RCD01DataBufferSimulationPads

class DDR5RCD01DataBufferShell(Module):
    """
    DRAM Data bus pass-through
    """
    def __init__(self, pads_ingress, nranks=1, with_sub_channels=False, **kwargs):        
        self.submodules.pads_ingress = pads_ingress

        pads_egress = DDR5RCD01DataBufferSimulationPads(databits=4,
                                    nranks=nranks,
                                    dq_dqs_ratio=4,
                                    with_sub_channels=with_sub_channels)
        self.submodules.pads_egress = pads_egress

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]
        
        # self.comb += (self.pads_egress.dq).eq(self.pads_ingress.dq)
        # self.comb += (self.pads_egress.cb).eq(self.pads_ingress.cb)
        # self.comb += (self.pads_egress.dqs_t).eq(self.pads_ingress.dqs_t)
        # self.comb += (self.pads_egress.dqs_c).eq(self.pads_ingress.dqs_c)
        connection_matrix_dc = {
                'dq' : ['dq','Forward'],
                'cb' : ['cb','Forward'],
                'dqs_t' : ['dqs_t','Forward'],
                'dqs_c' : ['dqs_c','Forward'],
            }

        for prefix in prefixes:
            for key in connection_matrix_dc:
                sig_eg = prefix+key
                sig_in = prefix+connection_matrix_dc[key][0]
                # Get attr in egress
                atr_eg = getattr(self.pads_egress, sig_eg)
                # Get attr in ingress
                atr_in = getattr(self.pads_ingress, sig_in)
                # Determine correct direction
                direction = connection_matrix_dc[key][1]
                if direction == 'Forward':
                    print('Connect : ' + sig_in + ' to ' + sig_eg)
                    self.comb += atr_eg.eq(atr_in)
                    pass
                elif direction == 'Reverse':
                    print('Connect : ' + sig_eg + ' to ' + sig_in)
                    self.comb += atr_in.eq(atr_eg)
                    pass
                else:
                    raise('Unsupported option defined in connection matrix. Supported: Forward, Reverse')

if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
