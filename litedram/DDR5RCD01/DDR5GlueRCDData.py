#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# migen
from migen import *
# RCD
from litedram.DDR5RCD01.DDR5RCD01CoreIngressSimulationPads import DDR5RCD01CoreIngressSimulationPads
from litedram.DDR5RCD01.DDR5RCD01DataBufferSimulationPads import DDR5RCD01DataBufferSimulationPads


class DDR5GlueRCDData(Module):
    """ Glue logic between DDR5 Sim Pads and RCD Sim Pads
    TODO Documentation
    """

    def __init__(self, pads_ddr5, with_sub_channels=False, **kwargs):
        # TODO implementation
        # For signals in pads_ddr5
        # Split signals into Core and Data Pads

        # Connect simPHY to RCD
        self.pi = DDR5RCD01CoreIngressSimulationPads()

        connection_matrix_sc = {
            'dck_t': ['ck_t', 'Forward'],
            'dck_c': ['ck_c', 'Forward'],
            'drst_n': ['reset_n', 'Forward'],
            'alert_n': ['alert_n', 'Reverse'],
        }
        for key in connection_matrix_sc:
            sig_eg = key
            sig_in = connection_matrix_sc[key][0]
            # Get attr in egress
            atr_eg = getattr(self.pi, sig_eg)
            # Get attr in ingress
            atr_in = getattr(pads_ddr5, sig_in)
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
                raise (
                    'Unsupported option defined in connection matrix. Supported: Forward, Reverse')

        # TODO check polarity of CA
        prefixes = [""] if not with_sub_channels else ["A_", "B_"]
        connection_matrix_dc = {
            'dcs_n': ['cs_n', 'Forward'],
            'dca': ['ca', 'Forward'],
            'dpar': ['par', 'Forward'],
        }

        for prefix in prefixes:
            for key in connection_matrix_dc:
                sig_eg = prefix+key
                sig_in = prefix+connection_matrix_dc[key][0]
                # Get attr in egress
                atr_eg = getattr(self.pi, sig_eg)
                # Get attr in ingress
                atr_in = getattr(pads_ddr5, sig_in)
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
                    raise (
                        'Unsupported option defined in connection matrix. Supported: Forward, Reverse')

        # TODO confirm that dm_n and cb are the same signal
        self.pdi = DDR5RCD01DataBufferSimulationPads()
        connection_matrix_db = {
            'dq': ['dq', 'Forward'],
            'cb': ['dm_n', 'Forward'],
            'dqs_t': ['dqs_t', 'Forward'],
            'dqs_c': ['dqs_c', 'Forward'],
        }
        for prefix in prefixes:
            for key in connection_matrix_db:
                sig_eg = prefix+key
                sig_in = prefix+connection_matrix_db[key][0]
                # Get attr in egress
                atr_eg = getattr(self.pdi, sig_eg)
                # Get attr in ingress
                atr_in = getattr(pads_ddr5, sig_in)
                # Determine correct direction
                direction = connection_matrix_db[key][1]
                if direction == 'Forward':
                    print('Connect : ' + sig_in + ' to ' + sig_eg)
                    self.comb += atr_eg.eq(atr_in)
                    pass
                elif direction == 'Reverse':
                    print('Connect : ' + sig_eg + ' to ' + sig_in)
                    self.comb += atr_in.eq(atr_eg)
                    pass
                else:
                    raise (
                        'Unsupported option defined in connection matrix. Supported: Forward, Reverse')


if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
