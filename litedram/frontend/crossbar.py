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
        self.req_queue_size = controller.req_queue_size
        self.read_latency = controller.read_latency
        self.write_latency = controller.write_latency

        self.bank_bits = log2_int(self.nbanks, False)

        self.masters = []

    def get_port(self):
        if self.finalized:
            raise FinalizeError
        port = Interface(self.rca_bits + self.bank_bits,
            self.dw, 1, self.req_queue_size, self.read_latency, self.write_latency)
        self.masters.append(port)
        return port

    def do_finalize(self):
        nmasters = len(self.masters)

        m_ba, m_rca = self.split_master_addresses(self.bank_bits,
                                                  self.rca_bits,
                                                  self.cba_shift)

        controller = self.controller
        controller_selected = [1]*nmasters
        master_readys = [0]*nmasters
        master_dat_w_acks = [0]*nmasters
        master_dat_r_acks = [0]*nmasters

        rrs = [roundrobin.RoundRobin(nmasters, roundrobin.SP_CE) for n in range(self.nbanks)]
        self.submodules += rrs
        for nb, rr in enumerate(rrs):
            bank = getattr(controller, "bank"+str(nb))

            # for each master, determine if another bank locks it
            master_locked = []
            for nm, master in enumerate(self.masters):
                locked = 0
                for other_nb, other_rr in enumerate(rrs):
                    if other_nb != nb:
                        other_bank = getattr(controller, "bank"+str(other_nb))
                        locked = locked | (other_bank.lock & (other_rr.grant == nm))
                master_locked.append(locked)

            # arbitrate
            bank_selected = [cs & (ba == nb) & ~locked for cs, ba, locked in zip(controller_selected, m_ba, master_locked)]
            bank_requested = [bs & master.valid for bs, master in zip(bank_selected, self.masters)]
            self.comb += [
                rr.request.eq(Cat(*bank_requested)),
                rr.ce.eq(~bank.valid & ~bank.lock)
            ]

            # route requests
            self.comb += [
                bank.adr.eq(Array(m_rca)[rr.grant]),
                bank.we.eq(Array(self.masters)[rr.grant].we),
                bank.valid.eq(Array(bank_requested)[rr.grant])
            ]
            master_readys = [master_ready | ((rr.grant == nm) & bank_selected[nm] & bank.ready)
                for nm, master_ready in enumerate(master_readys)]
            master_dat_w_acks = [master_dat_w_ack | ((rr.grant == nm) & bank.dat_w_ack)
                for nm, master_dat_w_ack in enumerate(master_dat_w_acks)]
            master_dat_r_acks = [master_dat_r_ack | ((rr.grant == nm) & bank.dat_r_ack)
                for nm, master_dat_r_ack in enumerate(master_dat_r_acks)]

        for nm, master_dat_w_ack in enumerate(master_dat_w_acks):
                for i in range(self.write_latency):
                    new_master_dat_w_ack = Signal()
                    self.sync += new_master_dat_w_ack.eq(master_dat_w_ack)
                    master_dat_w_ack = new_master_dat_w_ack
                master_dat_w_acks[nm] = master_dat_w_ack

        for nm, master_dat_r_ack in enumerate(master_dat_r_acks):
                for i in range(self.read_latency):
                    new_master_dat_r_ack = Signal()
                    self.sync += new_master_dat_r_ack.eq(master_dat_r_ack)
                    master_dat_r_ack = new_master_dat_r_ack
                master_dat_r_acks[nm] = master_dat_r_ack

        self.comb += [master.ready.eq(master_ready) for master, master_ready in zip(self.masters, master_readys)]
        self.comb += [master.dat_w_ack.eq(master_dat_w_ack) for master, master_dat_w_ack in zip(self.masters, master_dat_w_acks)]
        self.comb += [master.dat_r_ack.eq(master_dat_r_ack) for master, master_dat_r_ack in zip(self.masters, master_dat_r_acks)]

        # route data writes
        controller_selected_wl = controller_selected
        for i in range(self.write_latency):
            n_controller_selected_wl = [Signal() for i in range(nmasters)]
            self.sync += [n.eq(o) for n, o in zip(n_controller_selected_wl, controller_selected_wl)]
            controller_selected_wl = n_controller_selected_wl
        dat_w_maskselect = []
        dat_we_maskselect = []
        for master, selected in zip(self.masters, controller_selected_wl):
            o_dat_w = Signal(self.dw)
            o_dat_we = Signal(self.dw//8)
            self.comb += If(selected,
                    o_dat_w.eq(master.dat_w),
                    o_dat_we.eq(master.dat_we)
                )
            dat_w_maskselect.append(o_dat_w)
            dat_we_maskselect.append(o_dat_we)
        self.comb += [
            controller.dat_w.eq(reduce(or_, dat_w_maskselect)),
            controller.dat_we.eq(reduce(or_, dat_we_maskselect))
        ]

        # route data reads
        self.comb += [master.dat_r.eq(self.controller.dat_r) for master in self.masters]

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
                    self.comb += rca.eq(Cat(master.adr[:cba_shift], master.adr[cba_upper:]))
                else:
                    self.comb += rca.eq(master.adr[cba_upper:])
            else:
                self.comb += rca.eq(master.adr[:cba_shift])

            ba = cba

            m_ba.append(ba)
            m_rca.append(rca)
        return m_ba, m_rca
