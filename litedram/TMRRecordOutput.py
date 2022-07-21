from migen import *

# Creates a TMR output copy of a Record
class TMRRecordOutput(Module):

    def __init__(self, cmd, name=None):
        self.name = get_obj_var_name(name, "")
        self.layout = cmd.layout
        
        if self.name:
            prefix = self.name + "_"
        else:
            prefix = ""
            
        for f in self.layout:
            if isinstance(f[1], (int, tuple)):
                if len(f) == 2:
                    sigName, sigSize = f
                    TMROut = TMROutput(getattr(cmd, sigName))
                    self.submodules += TMROut
                    sig = TMROut.output
                else:
                    raise TypeError
            elif isinstance(f[1], list):
                sigName, sigSublayout = f
                sig = TMRRecordOutput(sigSublayout, prefix+sigName)
            else:
                raise TypeError
            setattr(self, sigName, sig)