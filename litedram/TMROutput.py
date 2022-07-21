from migen import *

# Creates a TMR Output signal from control_signal
class TMROutput(Module):

    def __init__(self, control_signal):
        self.control = control_signal
        self.output = Cat(control_signal, control_signal, control_signal)