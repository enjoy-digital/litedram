from migen import *
from migen.genlib.fifo import *

from litex.soc.interconnect.csr import *

class LoggingSystem(Module):
    def __init__(self):
        self._log_csr = log_csr = CSRStatus(32, name='log_buffer')
        
        log_fifo = SyncFIFO(32, 10)
        self.submodules += log_fifo
        
        # CSR reads from FIFO if message is available
        self.sync += [If(log_csr.we & log_fifo.readable, log_csr.status.eq(log_fifo.dout), log_fifo.re.eq(1))
                        .Else(If(log_csr.we, log_csr.status.eq(0)), log_fifo.re.eq(0))]
                        
        # Put ascending numbers in FIFO
        num = Signal(32)
        self.comb += [log_fifo.din.eq(num), log_fifo.replace.eq(0), log_fifo.we.eq(log_fifo.writable)]
        self.sync += [If(log_fifo.we, num.eq(num+1))]
        
    def do_finalize(self):
        pass