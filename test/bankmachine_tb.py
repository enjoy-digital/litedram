from migen.fhdl.std import *
from migen.sim.generic import run_simulation

from litedram.common import *
from litedram.modules import MT48LC4M16
from litedram.core.bankmachine import LiteDRAMBankMachine

from test.common import *

class CmdGen(Module):
    def __init__(self, dram_module):
        self.rowbits = rowbits = dram_module.geom_settings.rowbits
        self.colbits = colbits = dram_module.geom_settings.colbits
        self.cmd = Source(dram_cmd_description(rowbits, colbits))
        self.n = 0

    def do_simulation(self, selfp):
        if selfp.cmd.ack:
            if self.n < 100:
                selfp.cmd.stb = 1
                selfp.cmd.row = randn(2**self.rowbits-1)
                selfp.cmd.col = randn(2**self.colbits-1)
                self.n += 1
            else:
                selfp.cmd.stb = 0


class TB(Module):
    def __init__(self):
        dram_module = MT48LC4M16(100*1000000)
        self.submodules.bankmachine = LiteDRAMBankMachine(dram_module, 16)
        self.submodules.write_gen = CmdGen(dram_module)
        self.submodules.read_gen = CmdGen(dram_module)
        self.comb += [
            Record.connect(self.write_gen.cmd, self.bankmachine.write_cmd),
            Record.connect(self.read_gen.cmd, self.bankmachine.read_cmd),
            self.bankmachine.cmd.ack.eq(1)
        ]

        self.nreads = 0
        self.nwrites = 0

    def do_simulation(self, selfp):
    	if selfp.bankmachine.cmd.stb:
    		if selfp.bankmachine.cmd.write:
    			self.nwrites += 1
    			print("nwrites {}/ nreads {}".format(self.nwrites, self.nreads))
    		elif selfp.bankmachine.cmd.read:
    			self.nreads += 1
    			print("nwrites {}/ nreads {}".format(self.nwrites, self.nreads))



if __name__ == "__main__":
    run_simulation(TB(), ncycles=2048, vcd_name="my.vcd", keep_files=True)
