from functools import reduce
from operator import or_

from litex.gen import *
from litex.gen.genlib import roundrobin

from litex.soc.interconnect import stream

from litedram.common import *


class LiteDRAMAsyncAdapter(Module):
    # TODO: check cmd/wdata/rdata fifo depths
    def __init__(self, port_from, port_to):
        assert port_from.aw == port_to.aw
        assert port_from.dw == port.to.dw

        aw = port_from.aw
        dw = port_from.dw
        cd_from = port_from.cd
        cd_to = port_to.cd

        # # #

        cmd_fifo = stream.AsyncFIFO([("we", 1), ("adr", aw)], 8)
        cmd_fifo = ClockDomainsRenamer({"write": cd_from,
                                        "read": cd_to})(cmd_fifo)
        self.submodules += cmd_fifo
        self.comb += [
            port_from.cmd.connect(cmd_fifo.sink),
            cmd_fifo.source.connect(port_to.cmd)
        ]

        wdata_fifo = stream.AsyncFIFO([("data", dw), ("we", dw//8)], 8)
        wdata_fifo = ClockDomainsRenamer({"write": cd_from,
                                          "read": cd_to})(wdata_fifo)
        self.submodules += wdata_fifo
        self.comb += [
            port_from.wdata.connect(wdata_fifo.sink),
            wdata_fifo.source.connect(port_to.wdata)
        ]

        rdata_fifo = stream.AsyncFIFO([("data", dw)], 8)
        rdata_fifo = ClockDomainsRenamer({"write": cd_to,
                                          "read": cd_from})(rdata_fifo)
        self.submodules += rdata_fifo
        self.comb += [
            port_to.rdata.connect(rdata_fifo.sink),
            rdata_fifo.source.connect(port_from.rdata)
        ]


class _LiteDRAMDownConverter(Module):
    """LiteDRAM port DownConverter

    This module reduces user port data width to fit controller data width.
    With N = port_from.dw/port_to.dw:
    - Address is adapted (multiplied by N + internal increments)
    - A single write from the user is splitted and generate N writes to the
    controller.
    - Reads generates N reads on the controller and returned datas are regroup
    into a single data presented to the user.
    """
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd
        assert port_from.dw > port_to.dw
        if port_from.dw % port_to.dw:
            raise ValueError("Ratio must be an int")

        # # #

        ratio = port_from.dw//port_to.dw

        counter = Signal(max=ratio)
        counter_reset = Signal()
        counter_ce = Signal()
        self.sync += \
            If(counter_reset,
                counter.eq(0)
            ).Elif(counter_ce,
                counter.eq(counter + 1)
            )

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            counter_reset.eq(1),
            If(port_from.cmd.valid,
                NextState("ADAPT")
            )
        )
        fsm.act("ADAPT",
            port_to.cmd.valid.eq(1),
            port_to.cmd.we.eq(port_from.cmd.we),
            port_to.cmd.adr.eq(port_from.cmd.adr*ratio + counter),
            If(port_to.cmd.ready,
                counter_ce.eq(1),
                If(counter == ratio - 1,
                    port_from.cmd.ready.eq(1)
                    NextState("IDLE")
                )
            )
        )

        wdata_converter = stream.StrideConverter(port_from.wdata.description,
                                                 port_to.wdata.descritpion)
        self.submodules += wdata_converter
        self.comb += [
            port_from.wdata.connect(wdata_converter.sink),
            wdata_converter.source.connect(port_to.wdata)
        ]

        rdata_converter = stream.StrideConverter(port_to.rdata.description,
                                                 port_from.rdata.description)
        self.submodules += rdata_converter
        self.comb += [
            port_to.rdata.connect(rdata_converter.sink),
            rdata_converter.source.connect(port_from.rdata)
        ]


class _LiteDRAMUpConverter(Module):
    """LiteDRAM port UpConverter

    This module increase user port data width to fit controller data width.
    With N = port_to.dw/port_from.dw:
    - Address is adapted (divided by N)
    - N writes and read from user are regrouped in a single one to the controller
    (when possible, ie when consecutive and bursting)
    """
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd
        assert port_from.dw < port_to.dw

        # # #


class LiteDRAMConverter(Module):
    def __init__(self, port_from, port_to):
        assert port_from.cd == port_to.cd

        # # #

        if port_from.dw > port_to.dw:
            converter = _LiteDRAMDownConverter(port_from, port_to)
            self.submodules += converter
        elif port_from.dw < port.to.dw:
            converter = _LiteDRAMUpConverter(port_from, port_to)
            self.submodules += converter


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

    def get_port(self, cd="sys"):
        if self.finalized:
            raise FinalizeError
        port_to = LiteDRAMPort(self.rca_bits + self.bank_bits, self.dw, "sys")
        self.masters.append(port_to)
        if cd != "sys":
            port_from = LiteDRAMPort(self.rca_bits + self.bank_bits, self.dw, cd)
            self.submodules += LiteDRAMAsyncAdapter(port_from, port_to)
            return port_from
        else:
            return port_to

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
            bank_requested = [bs & master.cmd.valid for bs, master in zip(bank_selected, self.masters)]
            self.comb += [
                arbiter.request.eq(Cat(*bank_requested)),
                arbiter.ce.eq(~bank.valid & ~bank.lock)
            ]

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
