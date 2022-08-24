#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litedram.phy import dfi
from litex.soc.interconnect.csr import *
from litedram.common import *

# PhaseInjector ------------------------------------------------------------------------------------

class PhaseInjector(Module, AutoCSR):
    def __init__(self, phase):
        self._command       = CSRStorage(6, write_from_dev=True)  # cs, we, cas, ras, wren, rden
        self._command_issue = CSR()
        self._address       = CSRStorage(len(phase.address), reset_less=True, write_from_dev=True)
        self._baddress      = CSRStorage(len(phase.bank),    reset_less=True, write_from_dev=True)
        self._wrdata        = CSRStorage(len(phase.wrdata),  reset_less=True, write_from_dev=True)
        self._rddata        = CSRStatus(len(phase.rddata))

        # # #

        self.comb += [
            If(self._command_issue.re,
                phase.cs_n.eq(Replicate(~self._command.storage[0], len(phase.cs_n))),
                phase.we_n.eq(~self._command.storage[1]),
                phase.cas_n.eq(~self._command.storage[2]),
                phase.ras_n.eq(~self._command.storage[3])
            ).Else(
                phase.cs_n.eq(Replicate(1, len(phase.cs_n))),
                phase.we_n.eq(1),
                phase.cas_n.eq(1),
                phase.ras_n.eq(1)
            ),
            phase.address.eq(self._address.storage),
            phase.bank.eq(self._baddress.storage),
            phase.wrdata_en.eq(self._command_issue.re & self._command.storage[4]),
            phase.rddata_en.eq(self._command_issue.re & self._command.storage[5]),
            phase.wrdata.eq(self._wrdata.storage),
            phase.wrdata_mask.eq(0)
        ]
        self.sync += If(phase.rddata_valid, self._rddata.status.eq(phase.rddata))

# DFIInjector --------------------------------------------------------------------------------------

class DFIInjector(Module, AutoCSR):
    def __init__(self, addressbits, bankbits, nranks, databits, nphases=1):
        inti        = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.slave  = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.TMRslave = TMRRecord(self.slave)
        self.master = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)

        self._control = CSRStorage(fields=[
            CSRField("sel",     size=1, values=[
                ("``0b0``", "Software (CPU) control."),
                ("``0b1`",  "Hardware control (default)."),
            ], reset=0b1), # Defaults to HW control.
            CSRField("cke",     size=1),
            CSRField("odt",     size=1),
            CSRField("reset_n", size=1),
        ])

        for n, phase in enumerate(inti.phases):
            setattr(self.submodules, "pi" + str(n), PhaseInjector(phase))

        # # #
        
        connect_TMR(self, self.TMRslave, self.slave, master=False)

        self.comb += If(self._control.fields.sel,
                self.slave.connect(self.master)
            ).Else(
                inti.connect(self.master)
            )
        for i in range(nranks):
            self.comb += [phase.cke[i].eq(self._control.fields.cke) for phase in inti.phases]
            self.comb += [phase.odt[i].eq(self._control.fields.odt) for phase in inti.phases if hasattr(phase, "odt")]
        self.comb += [phase.reset_n.eq(self._control.fields.reset_n) for phase in inti.phases if hasattr(phase, "reset_n")]
   
# TMRDFIInjector -----------------------------------------------------------------------------------

class PhaseInjectorModule(Module):
    def __init__(self, addressbits, bankbits, nranks, databits, nphases, control):
        inti = self.inti = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        
        ###
        
        for n, phase in enumerate(inti.phases):
            setattr(self.submodules, "pi" + str(n), PhaseInjector(phase))
            
        for i in range(nranks):
            self.comb += [phase.cke[i].eq(control.fields.cke) for phase in inti.phases]
            self.comb += [phase.odt[i].eq(control.fields.odt) for phase in inti.phases if hasattr(phase, "odt")]
        self.comb += [phase.reset_n.eq(control.fields.reset_n) for phase in inti.phases if hasattr(phase, "reset_n")]
        
    def connect(self, child):
        for n, phase in enumerate(self.inti.phases):
            pi = getattr(self, "pi"+str(n))
            child_pi = getattr(child, "pi"+str(n))
            
            self.comb += [child.inti.phases[n].rddata_valid.eq(phase.rddata_valid), child.inti.phases[n].rddata.eq(phase.rddata)]
            
            for csr in pi.get_csrs():
                print("Connecting " + csr.name)
                child_csr = [c for c in child_pi.get_csrs() if c.name == csr.name][0]
                print("Found child CSR " + child_csr.name)
                
                if isinstance(csr, CSR):
                    print("Connecting CSR")
                    self.comb += [child_csr.w.eq(csr.w), child_csr.we.eq(csr.we), child_csr.re.eq(csr.re)]
                elif isinstance(csr, CSRStorage):
                    print("Connecting CSRStorage")
                    #self.comb += [child_csr.we.eq(csr.we), child_csr.dat_w.eq(csr.storage)]
                    self.sync += [child_csr.storage.eq(csr.storage)]
                #elif isinstance(csr, CSRStatus):
                #    print("Connecting CSRStatus")
                #    #self.comb += [child_csr.status.eq(csr.status), child_csr.re.eq(csr.re)]
                #    
                #    self.sync += If(phase.rddata_valid, child_csr.status.eq(phase.rddata))
   
class TMRDFIInjector(Module, AutoCSR):
    def __init__(self, addressbits, bankbits, nranks, databits, nphases=1):
        self.slave  = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)
        self.TMRslave = TMRRecord(self.slave)
        self.master = dfi.Interface(addressbits, bankbits, nranks, databits, nphases)

        self._control = CSRStorage(fields=[
            CSRField("sel",     size=1, values=[
                ("``0b0``", "Software (CPU) control."),
                ("``0b1`",  "Hardware control (default)."),
            ], reset=0b1), # Defaults to HW control.
            CSRField("cke",     size=1),
            CSRField("odt",     size=1),
            CSRField("reset_n", size=1),
        ])
        
        self.pi_mod1 = PhaseInjectorModule(addressbits, bankbits, nranks, databits, nphases, self._control)
        self.submodules += self.pi_mod1
        
        self.pi_mod2 = PhaseInjectorModule(addressbits, bankbits, nranks, databits, nphases, self._control)
        self.submodules += self.pi_mod2
        
        self.pi_mod3 = PhaseInjectorModule(addressbits, bankbits, nranks, databits, nphases, self._control)
        self.submodules += self.pi_mod3
        
        self.pi_mod1.connect(self.pi_mod2)
        self.pi_mod1.connect(self.pi_mod3)
        
        for n in range(nphases):
            setattr(self.submodules, "pi" + str(n), getattr(self.pi_mod1, "pi"+str(n)))

        # # #
        
        connect_TMR(self, self.TMRslave, self.slave, master=False)

        self.comb += If(self._control.fields.sel,
                self.slave.connect(self.master)
            ).Else(
                self.pi_mod2.inti.connect(self.master)
            )
