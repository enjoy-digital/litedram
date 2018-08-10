from functools import reduce
from operator import or_

from migen import *
from migen.genlib import roundrobin

from litex.soc.interconnect import stream

from litedram.common import *
from litedram.frontend.adaptation import LiteDRAMPortCDC, LiteDRAMPortConverter


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

    def get_port(self, mode="both", dw=None, cd="sys", reverse=False, reorder=False):
        if self.finalized:
            raise FinalizeError
        if dw is None:
            dw = self.dw

        # crossbar port
        port = LiteDRAMPort(mode, self.rca_bits + self.bank_bits, self.dw, "sys", len(self.masters), reorder)
        self.masters.append(port)

        # clock domain crossing
        if cd != "sys":
            new_port = LiteDRAMPort(mode, port.aw, port.dw, cd, port.id, reorder)
            self.submodules += LiteDRAMPortCDC(new_port, port)
            port = new_port

        # data width convertion
        if dw != self.dw:
            if dw > self.dw:
                adr_shift = -log2_int(dw//self.dw)
            else:
                adr_shift = log2_int(self.dw//dw)
            new_port = LiteDRAMPort(mode, port.aw + adr_shift, dw, cd, port.id, reorder)
            self.submodules += ClockDomainsRenamer(cd)(LiteDRAMPortConverter(new_port, port, reverse))
            port = new_port

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

        rbank = Signal(max=self.nbanks)
        wbank = Signal(max=self.nbanks)
        for nb, arbiter in enumerate(arbiters):
            bank = getattr(controller, "bank"+str(nb))

            # for each master, determine if another bank locks it
            master_locked = []
            for nm, master in enumerate(self.masters):
                locked = 0
                if not master.reorder:
                    for other_nb, other_arbiter in enumerate(arbiters):
                        if other_nb != nb:
                            other_bank = getattr(controller, "bank"+str(other_nb))
                            locked = locked | (other_bank.lock & (other_arbiter.grant == nm))
                master_locked.append(locked)

            # arbitrate
            bank_selected = [(ba == nb) & ~locked for ba, locked in zip(m_ba, master_locked)]
            bank_requested = [bs & master.cmd.valid for bs, master in zip(bank_selected, self.masters)]
            self.comb += [
                arbiter.request.eq(Cat(*bank_requested)),
                arbiter.ce.eq(~bank.valid & ~bank.lock)
            ]

            # Get rdata source bank
            self.sync += If((arbiter.grant == nm) & bank.rdata_valid, rbank.eq(nb))

            # Get wdata source bank
            self.sync += \
                If((arbiter.grant == nm) & bank.wdata_ready,
                    wbank.eq(nb)
                )

            # route requests
            self.comb += [
                bank.adr.eq(Array(m_rca)[arbiter.grant]),
                bank.we.eq(Array(self.masters)[arbiter.grant].cmd.we),
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

        # Delay bank output to match rvalid
        for i in range(self.read_latency-1):
            new_master_rbank = Signal(max=self.nbanks)
            self.sync += new_master_rbank.eq(rbank)
            rbank = new_master_rbank
        # Delay wbank output to match wready
        for i in range(self.write_latency-1):
            new_master_wbank = Signal(max=self.nbanks)
            self.sync += new_master_wbank.eq(wbank)
            wbank = new_master_wbank

        for master, master_ready in zip(self.masters, master_readys):
            self.comb += master.cmd.ready.eq(master_ready)
        for master, master_wdata_ready in zip(self.masters, master_wdata_readys):
            self.comb += master.wdata.ready.eq(master_wdata_ready)
        for master, master_rdata_valid in zip(self.masters, master_rdata_valids):
            self.comb += master.rdata.valid.eq(master_rdata_valid)

        # route data writes
        wdata_cases = {}
        for nm, master in enumerate(self.masters):
            wdata_cases[2**nm] = [
                controller.wdata.eq(master.wdata.data),
                controller.wdata_we.eq(master.wdata.we)
            ]
        wdata_cases["default"] = [
            controller.wdata.eq(0),
            controller.wdata_we.eq(0)
        ]
        self.comb += Case(Cat(*master_wdata_readys), wdata_cases)

        # route data reads
        for master in self.masters:
            self.comb += master.rdata.data.eq(self.controller.rdata)
            if hasattr(master.rdata, "bank"):
                self.comb += master.rdata.bank.eq(rbank)
                self.comb += master.wdata.bank.eq(wbank)

    def split_master_addresses(self, bank_bits, rca_bits, cba_shift):
        m_ba = []    # bank address
        m_rca = []    # row and column address
        for master in self.masters:
            cba = Signal(self.bank_bits)
            rca = Signal(self.rca_bits)
            cba_upper = cba_shift + bank_bits
            self.comb += cba.eq(master.cmd.adr[cba_shift:cba_upper])
            if cba_shift < self.rca_bits:
                if cba_shift:
                    self.comb += rca.eq(Cat(master.cmd.adr[:cba_shift],
                                            master.cmd.adr[cba_upper:]))
                else:
                    self.comb += rca.eq(master.cmd.adr[cba_upper:])
            else:
                self.comb += rca.eq(master.cmd.adr[:cba_shift])

            ba = cba

            m_ba.append(ba)
            m_rca.append(rca)
        return m_ba, m_rca
