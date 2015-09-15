from migen.fhdl.std import *
from migen.sim.generic import run_simulation

from litedram.common import *
from litedram.module import MT48LC4M16
from litedram.core.bankmachine import LiteDRAMBankMachine

from test.common import *

class TB(Module):
    def __init__(self):
        sdram_module = MT48LC4M16(100)
        self.submodules.bankmachine = LiteDRAMBankMachine(sdram_module, 16)

    def gen_simulation(self, selfp):
        for i in range(100):
            yield

if __name__ == "__main__":
    run_simulation(TB(), ncycles=2048, vcd_name="my.vcd", keep_files=True)
