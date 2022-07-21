from migen import *

# Decodes a TMR Record or Endpoint
class TMRRecordMaster(Module):

    def __init__(self, cmd):
        for f in cmd.layout:
            if isinstance(f[1], (int, tuple)):
                if len(f) == 3:
                    sigName, sigSize, sigDir = f
                else:
                    raise TypeError
            else:
                raise TypeError
            if sigDir == DIR_M_TO_S:
                TMROut = TMROutput(getattr(cmd, sigName))
                self.submodules += TMROut
                setattr(self, sigName, TMROut.output)
            else:
                TMRIn = TMRInput(getattr(cmd, sigName))
                self.submodules += TMRIn
                setattr(self, sigName, TMRIn.result)