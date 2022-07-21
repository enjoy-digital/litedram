from migen import *

# Decodes a TMR Record or Endpoint
class TMRRecordInput(Module):

    def __init__(self, cmd):
        for f in cmd.layout:
            if isinstance(f[1], (int, tuple)):
                if len(f) == 3:
                    sigName, sigSize, sigDir = f
                else:
                    sigName, sigSize = f
            else:
                raise TypeError
            TMRIn = TMRInput(getattr(cmd, sigName))
            self.submodules += TMRIn
            setattr(self, sigName, TMRIn.result)