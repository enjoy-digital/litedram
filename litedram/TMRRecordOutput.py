from migen import *

# Creates a TMR output copy of a Record
class TMRRecordOutput(Module):

    def __init__(self, cmd):
        for f in cmd.layout:
            if isinstance(f[1], (int, tuple)):
                if len(f) == 3:
                    sigName, sigSize, sigDir = f
                else:
                    sigName, sigSize = f
            else:
                raise TypeError
            TMROut = TMROutput(getattr(cmd, sigName))
            self.submodules += TMRIn
            setattr(self, sigName, TMROut.output)