#!/usr/bin/python
import inspect
import os
import shutil
import subprocess

from fusesoc.capi2.generator import Generator

from litedram.generate import generate

import litex.soc.cores.cpu.vexriscv
class LitedramGenerator(Generator):
    
    def run(self):
        generate(self.config)
        vexriscv_file = os.path.join(os.path.dirname(inspect.getfile(litex.soc.cores.cpu.vexriscv)), 'verilog', 'VexRiscv.v')
        shutil.copy2(vexriscv_file, os.getcwd())
        self.add_files([
            {'VexRiscv.v'                        : {'file_type' : 'verilogSource'}},
            {'build/gateware/mem_1.init'         : {'file_type' : 'user', 'copyto' : 'mem_1.init'}},
            {'build/gateware/litedram_core.init' : {'file_type' : 'user', 'copyto' : 'litedram_core.init'}},
            {'build/gateware/litedram_core.v'    : {'file_type' : 'verilogSource'}},
        ])

g = LitedramGenerator()
g.run()
g.write()
