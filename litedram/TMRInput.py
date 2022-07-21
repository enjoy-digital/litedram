from migen import *

# Decodes a TMR signal from received
class TMRInput(Module):

    def __init__(self, received):
        self.result = Signal()
        
        ###

        sig_length = int(len(received) / 3)
        
        sig1 = received[0:sig_length]
        sig2 = received[sig_length:sig_length*2]
        sig3 = received[sig_length*2:sig_length*3]
    
        self.comb += self.result.eq((sig1&sig2) | (sig2&sig3) | (sig1&sig3))