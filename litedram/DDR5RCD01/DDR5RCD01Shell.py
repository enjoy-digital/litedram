#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# RCD
from litedram.DDR5RCD01.DDR5RCD01BCOMSimulationPads import DDR5RCD01BCOMSimulationPads
from litedram.DDR5RCD01.DDR5RCD01CoreEgressSimulationPads import  DDR5RCD01CoreEgressSimulationPads
from litedram.DDR5RCD01.DDR5RCD01CoreIngressSimulationPads import  DDR5RCD01CoreIngressSimulationPads
from litedram.DDR5RCD01.DDR5RCD01SidebandSimulationPads import  DDR5RCD01SidebandSimulationPads

class DDR5RCD01Shell(Module):
    """The DDR5RCD01Shell
        is a module, which:
          - implements the pin-out exactly as the DDR5RCD01_model
          - connect relevant outputs to inputs. This provides a complete
            pass-through (or bypass) performance.
          - the purpose of this block is to quickly develop testbenches
    """
    def __init__(self, pads_ingress, pads_sideband, \
                is_dual_channel=False, **kwargs):

      self.submodules.pads_sideband = pads_sideband
      self.submodules.pads_ingress = pads_ingress

      pads_egress = DDR5RCD01CoreEgressSimulationPads(dcs_n_w=2, dca_w=14, is_dual_channel=is_dual_channel)
      self.submodules.pads_egress = pads_egress

      pads_bcom = DDR5RCD01BCOMSimulationPads(is_dual_channel=is_dual_channel)
      self.submodules.pads_bcom = pads_bcom

      # Note, dpar is not on the list, must be handled in RCD
      # TODO handler dpar[b:a]
      # Reset output

      # Single channel connection matrix
      # Signals in keys are dual channel
      # Signals in values are single channel

      # Order 'Forward' will result in a connection
      # self.comb += egress.eq(ingress)
      # Order 'Reverse' will result in a connection
      # self.comb += ingress.eq(egress)

      connection_matrix_sc ={
      'dlbd' : ['qlbd','Reverse'],
      'dlbs' : ['qlbs','Reverse'],
      'qrst_n' : ['drst_n','Forward'],
      # Clock outputs
      # Rank 0, Row Top
      'qack_t' :  ['dck_t','Forward'],
      'qack_c' :  ['dck_c','Forward'],
      # Rank 1, Row Top
      'qbck_t' :  ['dck_t','Forward'],
      'qbck_c' :  ['dck_c','Forward'],
      # Rank 0, Row Bottom
      'qcck_t' :  ['dck_t','Forward'],
      'qcck_c' :  ['dck_c','Forward'],
      # Rank 1, Row Top
      'qdck_t' :  ['dck_t','Forward'],
      'qdck_c' : ['dck_c','Forward'],
      # Error
      'derror_in_n' : ['alert_n', 'Reverse'],
      }
      
      # Dual-channel connection matrix
      # Signals in keys AND values are dual-channel
      connection_matrix_dc ={
      # Adress, Chip Select
      # Top Row
      'qacs_a_n' : ['dcs_n','Forward'],
      'qaca_a' :  ['dca_n','Forward'],
      # Bottom Row
      'qacs_b_n' :  ['dcs_n','Forward'],
      'qaca_b' :  ['dca_n','Forward'],
      }  
      
      # Connect matrix_sc
      print('Connection Table SC: Signal is connected to Signal ')

      prefixes = [""] if not is_dual_channel else ["A_", "B_"]
      for prefix in prefixes:
          for key in connection_matrix_sc:
            sig_eg = prefix+key
            sig_in = connection_matrix_sc[key][0]
            # Get attr in egress
            atr_eg = getattr(self.pads_egress, sig_eg)
            # Get attr in ingress
            atr_in = getattr(self.pads_ingress, sig_in)
            # Determine correct direction
            direction = connection_matrix_sc[key][1]
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
            # breakpoint()
      
      # TODO the only difference between the two loops is the added prefix, this could be joined

      # Connect matrix dc
      print('Connection Table DC: Signal is connected to Signal ')
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
              print(direction)
              self.comb += atr_in.eq(atr_eg)
              pass
            else:
                raise('Unsupported option defined in connection matrix. Supported: Forward, Reverse')
            # breakpoint()

if __name__ == "__main__":
  raise NotImplementedError("Test of this block is to be done.")
  pi = DDR5RCD01CoreIngressSimulationPads()
  ps = DDR5RCD01SidebandSimulationPads()
  objTB = DDR5RCD01Shell(pi,ps)
  
