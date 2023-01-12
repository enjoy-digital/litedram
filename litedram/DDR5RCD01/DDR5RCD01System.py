#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# LiteDRAM : RCD
from litedram.DDR5RCD01.DDR5RCD01Chip import DDR5RCD01Chip
from litedram.DDR5RCD01.DDR5RCD01DataBuffer import DDR5RCD01DataBuffer
from litedram.DDR5RCD01.DDR5RCD01CoreIngressSimulationPads import  DDR5RCD01CoreIngressSimulationPads
from litedram.DDR5RCD01.DDR5RCD01SidebandSimulationPads import  DDR5RCD01SidebandSimulationPads
from litedram.DDR5RCD01.DDR5RCD01DataBufferSimulationPads import DDR5RCD01DataBufferSimulationPads
from litedram.DDR5RCD01.DDR5RCD01Shell import DDR5RCD01Shell

class DDR5RCD01System(Module):
    """The DDR5 RCD01 System
    
    The DDR5 RCD01 System contains:
    - the RCD chip
    - the data buffer chips (LRDIMM and RDIMM)

    1. RDIMM
      - BCOM is unused
      - Data buffer signals are passed through
    2. LRDIMM [to be implemented]
      - TODO enable BCOM support
      - TODO attach a data buffer model

    Implementation structure:
    System:
      -> RCD:
        -> RCD Shell
        -> RCD Chip
          -> RCD Core
      -> Data Buffers:
        -> Data Buffer Shell
        -> Data Buffer Chip
    """
    def __init__(self, pads_dram_data_ingress,\
                       pads_sideband,\
                       pads_rcd_ingress,\
                       rcd_passthrough=True,\
                       sideband_type='i2c',\
                       aligned_reset_zero=False, dq_dqs_ratio=8, nranks=1, with_sub_channels=False, **kwargs):

      self.submodules.pads_dram_data_ingress = pads_dram_data_ingress
      self.submodules.pads_sideband = pads_sideband
      self.submodules.pads_rcd_ingress = pads_rcd_ingress

      # RCD
      if rcd_passthrough:
        RCD = DDR5RCD01Shell( pads_rcd_ingress, pads_sideband)
      else:
        RCD = DDR5RCD01Chip( pads_rcd_ingress, pads_sideband, sideband_type='i3c')
      self.submodules.RCD = RCD
      self.submodules.pads_egress = RCD.pads_egress

      # Data Buffer
      data_buffer = DDR5RCD01DataBuffer( pads_dram_data_ingress, dimm_type='RDIMM')
      self.submodules.data_buffer = data_buffer
      self.submodules.pads_dram_data_egress = data_buffer.pads_egress

if __name__ == "__main__":
  raise NotImplementedError("Test of this block is to be done.")
  pi = DDR5RCD01CoreIngressSimulationPads()
  ps = DDR5RCD01SidebandSimulationPads()
  pdi = DDR5RCD01DataBufferSimulationPads()
  objTB = DDR5RCD01System(pdi,ps,pi)
  
