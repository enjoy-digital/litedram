"""LiteDRAM Refresher."""

from migen import *
from migen.genlib.misc import timeline

from litex.soc.interconnect import stream

from litedram.core.multiplexer import *


class RefreshGenerator(Module):
    def __init__(self, cmd, trp, trfc):
        self.start = Signal()
        self.done = Signal()

        # # #

        self.sync += [
            cmd.a.eq(2**10),
            cmd.ba.eq(0),
            cmd.cas.eq(0),
            cmd.ras.eq(0),
            cmd.we.eq(0),
        ]
        self.sync += [
            self.done.eq(0),
            # Wait start
            timeline(self.start, [
                # Precharge all
                (1, [
                    cmd.ras.eq(1),
                    cmd.we.eq(1)
                ]),
                # Wait tRP then Auto Refresh
                (1 + trp, [
                    cmd.cas.eq(1),
                    cmd.ras.eq(1)
                ]),
                # Wait tRFC then done
                (1 + trp + trfc, [
                    self.done.eq(1)
                ])
            ])
        ]



class RefreshTimer(Module):
    def __init__(self, trefi):
        self.wait = wait = Signal()
        self.done = done = Signal()
        self.count = count = Signal(bits_for(trefi), reset=trefi)

        self.load = load = Signal()
        self.load_count = load_count = Signal(bits_for(trefi))

        # # #

        self.comb += done.eq(count == 0)
        self.sync += [
            If(wait,
                If(~done,
                    If(load & (load_count < count),
                        count.eq(load_count)
                    ).Else(
                        count.eq(count - 1)
                    )
                )
            ).Else(
                count.eq(count.reset)
            )
        ]


class Refresher(Module):
    def __init__(self, settings):
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(
            a=settings.geom.addressbits,
            ba=settings.geom.bankbits + log2_int(settings.phy.nranks)))

        # # #

        # Periodic refresh timer
        timer = RefreshTimer(settings.timing.tREFI)
        timer = ResetInserter()(timer)
        self.submodules.timer = timer
        self.comb += self.timer.reset.eq(~settings.with_refresh)
        self.comb += self.timer.wait.eq(~self.timer.done)

        # Refresh sequence generator
        generator = RefreshGenerator(cmd, settings.timing.tRP, settings.timing.tRFC)
        self.submodules.generator = generator

        # Refresh control FSM
        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            If(timer.done,
                NextState("WAIT_GRANT")
            )
        )
        fsm.act("WAIT_GRANT",
            cmd.valid.eq(1),
            If(cmd.ready,
                generator.start.eq(1),
                NextState("WAIT_SEQ")
            )
        )
        fsm.act("WAIT_SEQ",
            If(generator.done,
                cmd.last.eq(1),
                NextState("IDLE")
            ).Else(
                cmd.valid.eq(1)
            )
        )
