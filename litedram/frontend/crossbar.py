from functools import reduce
from operator import or_

from litex.gen import *
from litex.gen.genlib import roundrobin

from litedram.common import *


class LiteDRAMCrossbar(Module):
    def __init__(self, controller, cba_shift):
        self.controller = controller
        self.cba_shift = cba_shift

        self.rca_bits = controller.aw
        self.dw = controller.dw
        self.nbanks = controller.nbanks
        self.cmd_buffer_depth = controller.settings.cmd_buffer_depth
        self.read_latency = controller.settings.phy.read_latency + 1
        self.write_latency = controller.settings.phy.write_latency + 1

        self.bank_bits = log2_int(self.nbanks, False)

        self.masters = []

    def get_port(self):
        if self.finalized:
            raise FinalizeError
        port = LiteDRAMPort(self.rca_bits + self.bank_bits,
                            self.dw,
                            self.cmd_buffer_depth,
                            self.read_latency,
                            self.write_latency)
        self.masters.append(port)
        return port

    def do_finalize(self):
        nmasters = len(self.masters)

        m_ba, m_rca = self.split_master_addresses(self.bank_bits,
                                                  self.rca_bits,
                                                  self.cba_shift)

        controller = self.controller
        master_readys = [0]*nmasters
        master_wdata_readys = [0]*nmasters
        master_rdata_valids = [0]*nmasters

        arbiters = [roundrobin.RoundRobin(nmasters, roundrobin.SP_CE) for n in range(self.nbanks)]
        self.submodules += arbiters
        for nb, arbiter in enumerate(arbiters):
            bank = getattr(controller, "bank"+str(nb))

            # for each master, determine if another bank locks it
            master_locked = []
            for nm, master in enumerate(self.masters):
                locked = 0
                for other_nb, other_arbiter in enumerate(arbiters):
                    if other_nb != nb:
                        other_bank = getattr(controller, "bank"+str(other_nb))
                        locked = locked | (other_bank.lock & (other_arbiter.grant == nm))
                master_locked.append(locked)

            # arbitrate
            bank_selected = [(ba == nb) & ~locked for ba, locked in zip(m_ba, master_locked)]
            bank_requested = [bs & master.valid for bs, master in zip(bank_selected, self.masters)]
            self.comb += [
                arbiter.request.eq(Cat(*bank_requested)),
                arbiter.ce.eq(~bank.valid & ~bank.lock)
            ]

            # route requests
            self.comb += [
                bank.adr.eq(Array(m_rca)[arbiter.grant]),
                bank.we.eq(Array(self.masters)[arbiter.grant].we),
                bank.valid.eq(Array(bank_requested)[arbiter.grant])
            ]
            master_readys = [master_ready | ((arbiter.grant == nm) & bank_selected[nm] & bank.ready)
                for nm, master_ready in enumerate(master_readys)]
            master_wdata_readys = [master_wdata_ready | ((arbiter.grant == nm) & bank.wdata_ready)
                for nm, master_wdata_ready in enumerate(master_wdata_readys)]
            master_rdata_valids = [master_rdata_valid | ((arbiter.grant == nm) & bank.rdata_valid)
                for nm, master_rdata_valid in enumerate(master_rdata_valids)]

        for nm, master_wdata_ready in enumerate(master_wdata_readys):
                for i in range(self.write_latency):
                    new_master_wdata_ready = Signal()
                    self.sync += new_master_wdata_ready.eq(master_wdata_ready)
                    master_wdata_ready = new_master_wdata_ready
                master_wdata_readys[nm] = master_wdata_ready

        for nm, master_rdata_valid in enumerate(master_rdata_valids):
                for i in range(self.read_latency):
                    new_master_rdata_valid = Signal()
                    self.sync += new_master_rdata_valid.eq(master_rdata_valid)
                    master_rdata_valid = new_master_rdata_valid
                master_rdata_valids[nm] = master_rdata_valid

        for master, master_ready in zip(self.masters, master_readys):
            self.comb += master.ready.eq(master_ready)
        for master, master_wdata_ready in zip(self.masters, master_wdata_readys):
            self.comb += master.wdata_ready.eq(master_wdata_ready)
        for master, master_rdata_valid in zip(self.masters, master_rdata_valids):
            self.comb += master.rdata_valid.eq(master_rdata_valid)

        # route data writes
        wdata_maskselect = []
        wdata_we_maskselect = []
        for master in self.masters:
            wdata_maskselect.append(master.wdata)
            wdata_we_maskselect.append(master.wdata_we)
        self.comb += [
            controller.wdata.eq(reduce(or_, wdata_maskselect)),
            controller.wdata_we.eq(reduce(or_, wdata_we_maskselect))
        ]

        # route data reads
        for master in self.masters:
            self.comb += master.rdata.eq(self.controller.rdata)

    def split_master_addresses(self, bank_bits, rca_bits, cba_shift):
        m_ba = []    # bank address
        m_rca = []    # row and column address
        for master in self.masters:
            cba = Signal(self.bank_bits)
            rca = Signal(self.rca_bits)
            cba_upper = cba_shift + bank_bits
            self.comb += cba.eq(master.adr[cba_shift:cba_upper])
            if cba_shift < self.rca_bits:
                if cba_shift:
                    self.comb += rca.eq(Cat(master.adr[:cba_shift],
                                            master.adr[cba_upper:]))
                else:
                    self.comb += rca.eq(master.adr[cba_upper:])
            else:
                self.comb += rca.eq(master.adr[:cba_shift])

            ba = cba

            m_ba.append(ba)
            m_rca.append(rca)
        return m_ba, m_rca
