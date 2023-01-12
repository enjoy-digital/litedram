#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# RCD
from litedram.DDR5RCD01.DDR5RCD01DataBufferChip import DDR5RCD01DataBufferChip
from litedram.DDR5RCD01.DDR5RCD01DataBufferShell import DDR5RCD01DataBufferShell

class DDR5RCD01DataBuffer(Module):
    """
    The DDR5RCD01DataBuffer is a wrapper for the DDR5 data bus. It allows to easily
    switch from the RDIMM to the LRDIMM implementation with the dimm_type flag.
    
    Expected behaviour:
    RDIMM - data signals are unchanged and passed through
    LRDIMM - data signals are connected to the DDR5RCD01DataBufferChip object, which
    may be implemented in the future
    """
    def __init__(self, pads_ingress, dimm_type='RDIMM',nranks=1, with_sub_channels=False, **kwargs):        
        self.submodules.pads_ingress = pads_ingress

        if dimm_type not in ['RDIMM','LRDIMM']:
            raise('Unsupported DIMM type. Use RDIMM or LRDIMM')

        if dimm_type == 'RDIMM':
            data_buffer = DDR5RCD01DataBufferShell(pads_ingress)
        if dimm_type == 'LRDIMM':
            # TODO replace print with preffered style of logging
            print('Warning : LRDIMM is not supported')
            data_buffer = DDR5RCD01DataBufferChip(pads_ingress)
        
        self.submodules.data_buffer = data_buffer
        self.submodules.pads_egress = self.data_buffer.pads_egress

if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
