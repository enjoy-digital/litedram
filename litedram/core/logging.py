from migen import *
from migen.genlib.fifo import *
from migen.genlib import roundrobin

from litex.soc.interconnect.csr import *

class LoggingSystem(Module, AutoCSR):
    def __init__(self):
        self.messages = []
        self.readys = []
        self.requests = []
    
        self._log_csr = log_csr = CSRStatus(32, name='log_buffer')
        
        self.log_fifo = log_fifo = SyncFIFO(32, 10)
        self.submodules += log_fifo
        self.comb += [log_fifo.replace.eq(0)]
        
        # CSR reads from FIFO if message is available
        self.sync += [If(log_csr.we & log_fifo.readable, log_csr.status.eq(log_fifo.dout), log_fifo.re.eq(1))
                        .Else(If(log_csr.we, log_csr.status.eq(0)), log_fifo.re.eq(0))]
        
    def get_log_port(self):
        message = Signal(32)
        ready = Signal()
        request = Signal()
        
        self.messages.append(message)
        self.readys.append(ready)
        self.requests.append(request)
        
        return message, ready, request
        
    def do_finalize(self):
        #Create Arbiter
        arbiter = roundrobin.RoundRobin(len(self.messages), roundrobin.SP_CE)
        self.submodules += arbiter
        
        self.comb += [self.log_fifo.din.eq(Array(self.messages)[arbiter.grant]),         #Map arbiter grant to data in
                        arbiter.ce.eq(self.log_fifo.writable),                           #Arbitrate if fifo is writable
                        self.log_fifo.we.eq(self.log_fifo.writable & reduce(or_, self.requests)),  #Write if writable and request available
                        arbiter.request.eq(Cat(self.requests)),                   #Map requests to arbiter requests
                        Cat(self.readys).eq(arbiter.grant)]                             #Map grants to readys  