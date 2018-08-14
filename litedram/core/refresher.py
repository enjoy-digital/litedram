from migen import *
from migen.genlib.misc import timeline, WaitTimer

from litex.soc.interconnect import stream

from litedram.core.multiplexer import *


class Refresher(Module):
    def __init__(self, settings):
        # 1st command 1 cycle after assertion of ready
        self.cmd = cmd = stream.Endpoint(cmd_request_rw_layout(settings.geom.addressbits,
                                                               settings.geom.bankbits))

        # # #

        # Refresh sequence generator:
        # PRECHARGE ALL --(tRP)--> AUTO REFRESH --(tRFC)--> done
        seq_start = Signal()
        seq_done = Signal()
        self.sync += [
            cmd.a.eq(2**10),
            cmd.ba.eq(0),
            cmd.cas.eq(0),
            cmd.ras.eq(0),
            cmd.we.eq(0),
            seq_done.eq(0)
        ]
        self.sync += timeline(seq_start, [
            (1, [
                cmd.ras.eq(1),
                cmd.we.eq(1)
            ]),
            (1+settings.timing.tRP, [
                cmd.cas.eq(1),
                cmd.ras.eq(1)
            ]),
            (1+settings.timing.tRP+settings.timing.tRFC, [
                seq_done.eq(1)
            ])
        ])

        # Periodic refresh counter
        self.submodules.timer = WaitTimer(settings.timing.tREFI)
        self.comb += self.timer.wait.eq(settings.with_refresh & ~self.timer.done)

        # Control FSM
        cmd_valid = Signal()
        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            If(self.timer.done,
                cmd_valid.eq(1),
                NextState("WAIT_GRANT")
            )
        )
        fsm.act("WAIT_GRANT",
            cmd_valid.eq(1),
            If(cmd.ready,
                seq_start.eq(1),
                NextState("WAIT_SEQ")
            )
        )
        fsm.act("WAIT_SEQ",
            If(seq_done,
                cmd_valid.eq(0),
                NextState("IDLE")
            )
        )
        self.sync += cmd.valid.eq(cmd_valid)
