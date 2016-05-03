from functools import reduce
from operator import or_, and_

from litex.gen import *
from litex.gen.genlib.roundrobin import *

from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import AutoCSR

from litedram.common import *
from litedram.core.perf import Bandwidth


class _CommandChooser(Module):
    def __init__(self, requests):
        self.want_reads = Signal()
        self.want_writes = Signal()
        self.want_cmds = Signal()

        a = len(requests[0].a)
        ba = len(requests[0].ba)
        # cas/ras/we are 0 when valid is inactive
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(a, ba))

        # # #

        n = len(requests)

        valids = Signal(n)
        for i, request in enumerate(requests):
            command = request.is_cmd & self.want_cmds
            read = request.is_read == self.want_reads
            write = request.is_write == self.want_writes
            self.comb += valids[i].eq(request.valid & (command | (read & write)))


        arbiter = RoundRobin(n, SP_CE)
        self.submodules += arbiter
        choices = Array(valids[i] for i in range(n))
        self.comb += [
            arbiter.request.eq(valids),
            cmd.valid.eq(choices[arbiter.grant])
        ]
        
        for name in ["a", "ba", "is_read", "is_write", "is_cmd"]:
            choices = Array(getattr(req, name) for req in requests)
            self.comb += getattr(cmd, name).eq(choices[arbiter.grant])
        
        for name in ["cas", "ras", "we"]:
            # we should only assert those signals when valid is 1
            choices = Array(getattr(req, name) for req in requests)
            self.comb += \
                If(cmd.valid,
                    getattr(cmd, name).eq(choices[arbiter.grant])
                )

        for i, request in enumerate(requests):
            self.comb += \
                If(cmd.valid & cmd.ready & (arbiter.grant == i),
                    request.ready.eq(1)
                )
        self.comb += arbiter.ce.eq(cmd.ready)


class _Steerer(Module):
    def __init__(self, commands, dfi):
        ncmd = len(commands)
        nph = len(dfi.phases)
        self.sel = [Signal(max=ncmd) for i in range(nph)]

        # # #

        def valid_and(cmd, attr):
            if not hasattr(cmd, "valid"):
                return 0
            else:
                return cmd.valid & getattr(cmd, attr)

        for phase, sel in zip(dfi.phases, self.sel):
            self.comb += [
                phase.cke.eq(1),
                phase.cs_n.eq(0)
            ]
            if hasattr(phase, "odt"):
                self.comb += phase.odt.eq(1)
            if hasattr(phase, "reset_n"):
                self.comb += phase.reset_n.eq(1)
            self.sync += [
                phase.address.eq(Array(cmd.a for cmd in commands)[sel]),
                phase.bank.eq(Array(cmd.ba for cmd in commands)[sel]),
                phase.cas_n.eq(~Array(cmd.cas for cmd in commands)[sel]),
                phase.ras_n.eq(~Array(cmd.ras for cmd in commands)[sel]),
                phase.we_n.eq(~Array(cmd.we for cmd in commands)[sel])
            ]
            rddata_ens = Array(valid_and(cmd, "is_read") for cmd in commands)
            wrdata_ens = Array(valid_and(cmd, "is_write") for cmd in commands)
            self.sync += [
                phase.rddata_en.eq(rddata_ens[sel]),
                phase.wrdata_en.eq(wrdata_ens[sel])
            ]


class Multiplexer(Module, AutoCSR):
    def __init__(self,
            settings,
            bank_machines,
            refresher,
            dfi,
            interface,
            with_bandwidth=False):
        assert(settings.phy.nphases == len(dfi.phases))

        # Command choosing
        requests = [bm.cmd for bm in bank_machines]
        self.submodules.choose_cmd = choose_cmd = _CommandChooser(requests)
        self.submodules.choose_req = choose_req = _CommandChooser(requests)
        if settings.phy.nphases == 1:
            self.comb += [
                choose_cmd.want_cmds.eq(1),
                choose_req.want_cmds.eq(1)
            ]

        # Command steering
        nop = Record(cmd_request_layout(settings.geom.addressbits,
                                        settings.geom.bankbits))
        # nop must be 1st
        commands = [nop, choose_cmd.cmd, choose_req.cmd, refresher.cmd]
        (STEER_NOP, STEER_CMD, STEER_REQ, STEER_REFRESH) = range(4)
        steerer = _Steerer(commands, dfi)
        self.submodules += steerer

        # Read/write turnaround
        read_available = Signal()
        write_available = Signal()
        reads = [req.valid & req.is_read for req in requests]
        writes = [req.valid & req.is_write for req in requests]
        self.comb += [
            read_available.eq(reduce(or_, reads)),
            write_available.eq(reduce(or_, writes))
        ]

        def anti_starvation(timeout):
            en = Signal()
            max_time = Signal()
            if timeout:
                t = timeout - 1
                time = Signal(max=t+1)
                self.comb += max_time.eq(time == 0)
                self.sync += If(~en,
                        time.eq(t)
                    ).Elif(~max_time,
                        time.eq(time - 1)
                    )
            else:
                self.comb += max_time.eq(0)
            return en, max_time

        read_time_en, max_read_time = anti_starvation(settings.read_time)
        write_time_en, max_write_time = anti_starvation(settings.write_time)

        # Refresh
        self.comb += [bm.refresh_req.eq(refresher.req) for bm in bank_machines]
        go_to_refresh = Signal()
        bm_refresh_gnts = [bm.refresh_gnt for bm in bank_machines]
        self.comb += go_to_refresh.eq(reduce(and_, bm_refresh_gnts))

        # Datapath
        all_rddata = [p.rddata for p in dfi.phases]
        all_wrdata = [p.wrdata for p in dfi.phases]
        all_wrdata_mask = [p.wrdata_mask for p in dfi.phases]
        self.comb += [
            interface.rdata.eq(Cat(*all_rddata)),
            Cat(*all_wrdata).eq(interface.wdata),
            Cat(*all_wrdata_mask).eq(~interface.wdata_we)
        ]

        def steerer_sel(steerer, r_w_n):
            r = []
            for i in range(settings.phy.nphases):
                s = steerer.sel[i].eq(STEER_NOP)
                if r_w_n == "read":
                    if i == settings.phy.rdphase:
                        s = steerer.sel[i].eq(STEER_REQ)
                    elif i == settings.phy.rdcmdphase:
                        s = steerer.sel[i].eq(STEER_CMD)
                elif r_w_n == "write":
                    if i == settings.phy.wrphase:
                        s = steerer.sel[i].eq(STEER_REQ)
                    elif i == settings.phy.wrcmdphase:
                        s = steerer.sel[i].eq(STEER_CMD)
                else:
                    raise ValueError
                r.append(s)
            return r

        # Control FSM
        self.submodules.fsm = fsm = FSM()
        fsm.act("READ",
            read_time_en.eq(1),
            choose_req.want_reads.eq(1),
            choose_cmd.cmd.ready.eq(1),
            choose_req.cmd.ready.eq(1),
            steerer_sel(steerer, "read"),
            If(write_available,
                # TODO: switch only after several cycles of ~read_available?
                If(~read_available | max_read_time,
                    NextState("RTW")
                )
            ),
            If(go_to_refresh,
                NextState("REFRESH")
            )
        )
        fsm.act("WRITE",
            write_time_en.eq(1),
            choose_req.want_writes.eq(1),
            choose_cmd.cmd.ready.eq(1),
            choose_req.cmd.ready.eq(1),
            steerer_sel(steerer, "write"),
            If(read_available,
                If(~write_available | max_write_time,
                    NextState("WTR")
                )
            ),
            If(go_to_refresh,
                NextState("REFRESH")
            )
        )
        fsm.act("REFRESH",
            steerer.sel[0].eq(STEER_REFRESH),
            refresher.ack.eq(1),
            If(~refresher.req,
                NextState("READ")
            )
        )
        # TODO: reduce this, actual limit is around (cl+1)/nphases
        fsm.delayed_enter("RTW", "WRITE", settings.phy.read_latency-1)
        fsm.delayed_enter("WTR", "READ", settings.timing.tWTR-1)

        if settings.with_bandwidth:
            data_width = settings.phy.dfi_databits*settings.phy.nphases
            self.submodules.bandwidth = Bandwidth(self.choose_req.cmd, data_width)
