from migen import *

# Decodes a TMR Record or Endpoint
class TMRRecordInput(Module):

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
                    TMRIn = TMRInput(getattr(cmd, sigName))
                    self.submodules += TMRIn
                    sig = TMRIn.result
                else:
                    raise TypeError
            elif isinstance(f[1], list):
                sigName, sigSublayout = f
                sig = TMRRecordInput(sigSublayout, prefix+sigName)
            else:
                raise TypeError
            setattr(self, sigName, sig)