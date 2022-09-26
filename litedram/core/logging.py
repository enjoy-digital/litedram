from migen import *
from migen.genlib.fifo import *
from migen.genlib import roundrobin

from litex.soc.interconnect.csr import *

class LoggingSystem(Module, AutoCSR):
    def __init__(self):
        self._log_csr = log_csr = CSRStatus(32, name='log_buffer')
        
        log_fifo = SyncFIFO(32, 10)
        self.submodules += log_fifo
        self.comb += [log_fifo.replace.eq(0)]
        
        # CSR reads from FIFO if message is available
        self.sync += [If(log_csr.we & log_fifo.readable, log_csr.status.eq(log_fifo.dout), log_fifo.re.eq(1))
                        .Else(If(log_csr.we, log_csr.status.eq(0)), log_fifo.re.eq(0))]
                        
        
        # Arbiter (single ascending # port)
        arbiter = roundrobin.RoundRobin(2, roundrobin.SP_CE)
        self.submodules += arbiter
        
        # Request, grant, & ce
        
        # Driver always requesting log
        self.comb += [arbiter.request[0].eq(1), arbiter.request[1].eq(0), arbiter.ce.eq(log_fifo.writable)]
        self.comb += [log_fifo.we.eq(log_fifo.writable)]
        
        num = Signal(32)
        self.comb += [If(arbiter.grant == 0, log_fifo.din.eq(num))]
        self.sync += [If(arbiter.grant == 0, num.eq(num+1))]
        
    #def do_finalize(self):
    #    pass