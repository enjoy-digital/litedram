"""LiteDRAM Crossbar."""

from functools import reduce
from operator import or_

from migen import *
from migen.genlib import roundrobin

from litex.soc.interconnect import stream

from litedram.common import *
from litedram.core.controller import *
from litedram.frontend.adaptation import *


class LiteDRAMCrossbar(Module):
    def __init__(self, controller, ):
        self.controller = controller

        self.rca_bits = controller.address_width
        self.nbanks = controller.nbanks
        self.nranks = controller.nranks
        self.cmd_buffer_depth = controller.settings.cmd_buffer_depth
        self.read_latency = controller.settings.phy.read_latency + 1
        self.write_latency = controller.settings.phy.write_latency + 1

        self.bank_bits = log2_int(self.nbanks, False)
        self.rank_bits = log2_int(self.nranks, False)

        self.masters = []

    def get_port(self, mode="both", data_width=None, clock_domain="sys", reverse=False, **kwargs):
        # retro-compatibility # FIXME: remove
        if "cd" in kwargs:
            print("[WARNING] Please update LiteDRAMCrossbar.get_port's \"cd\" parameter to \"clock_domain\"")
            clock_domain = kwargs["cd"]
        if "dw" in kwargs:
            print("[WARNING] Please update LiteDRAMCrossbar.get_port's \"dw\" parameter to \"data_width\"")
            data_width = kwargs["dw"]

        if self.finalized:
            raise FinalizeError

        if data_width is None:
            # use internal data_width when no width adaptation is requested
            data_width = self.controller.data_width

        # crossbar port
        port = LiteDRAMNativePort(
            mode=mode,
            address_width=self.rca_bits + self.bank_bits - self.rank_bits,
            data_width=self.controller.data_width,
            clock_domain="sys",
            id=len(self.masters))
        self.masters.append(port)

        # clock domain crossing
        if clock_domain != "sys":
            new_port = LiteDRAMNativePort(
                mode=mode,
                address_width=port.address_width,
                data_width=port.data_width,
                clock_domain=clock_domain,
                id=port.id)
            self.submodules += LiteDRAMNativePortCDC(new_port, port)
            port = new_port

        # data width convertion
        if data_width != self.controller.data_width:
            if data_width > self.controller.data_width:
                addr_shift = -log2_int(data_width//self.controller.data_width)
            else:
                addr_shift = log2_int(self.controller.data_width//data_width)
            new_port = LiteDRAMNativePort(
                mode=mode,
                address_width=port.address_width + addr_shift,
                data_width=data_width,
                clock_domain=clock_domain,
                id=port.id)
            self.submodules += ClockDomainsRenamer(clock_domain)(
                LiteDRAMNativePortConverter(new_port, port, reverse))
            port = new_port

        return port

    def do_finalize(self):
        controller = self.controller
        nmasters = len(self.masters)

        # address mapping
        cba_shifts = {
            "ROW_BANK_COL": controller.settings.geom.colbits -
                            controller.address_align,
            "ROW_COL_BANK": controller.settings.geom.rowbits +
                            controller.settings.geom.colbits -
                             controller.address_align
        }
        cba_shift = cba_shifts[controller.settings.address_mapping]
        m_ba = [m.get_bank_address(self.bank_bits, cba_shift)for m in self.masters]
        m_rca = [m.get_row_column_address(self.bank_bits, self.rca_bits, cba_shift) for m in self.masters]

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
                locked = Signal()
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
                bank.addr.eq(Array(m_rca)[arbiter.grant]),
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
            self.comb += master.rdata.data.eq(controller.rdata)
