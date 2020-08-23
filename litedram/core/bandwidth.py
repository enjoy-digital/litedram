#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2016-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2018 John Sully <john@csquare.ca>
# SPDX-License-Identifier: BSD-2-Clause

"""LiteDRAM Bandwidth."""

from migen import *

from litex.soc.interconnect.csr import *

# Bandwidth ----------------------------------------------------------------------------------------

class Bandwidth(Module, AutoCSR):
    """Measures LiteDRAM bandwidth

    This module works by counting the number of read/write commands issued by
    the controller during a fixed time period. To copy the values registered
    during the last finished period, user must write to the `update` register.

    Parameters
    ----------
    cmd : Endpoint(cmd_request_rw_layout)
        Multiplexer endpoint on which all read/write requests are being sent
    data_width : int, in
        Data width that can be read back from CSR
    period_bits : int, in
        Defines length of bandwidth measurement period = 2^period_bits

    Attributes
    ----------
    update : CSR, in
        Copy the values from last finished period to the status registers
    nreads : CSRStatus, out
        Number of READ commands issued during a period
    nwrites : CSRStatus, out
        Number of WRITE commands issued during a period
    data_width : CSRStatus, out
        Can be read to calculate bandwidth in bits/sec as:
            bandwidth = (nreads+nwrites) * data_width / period
    """
    def __init__(self, cmd, data_width, period_bits=24):
        self.update     = CSR()
        self.nreads     = CSRStatus(period_bits + 1)
        self.nwrites    = CSRStatus(period_bits + 1)
        self.data_width = CSRStatus(bits_for(data_width), reset=data_width)

        # # #

        cmd_valid    = Signal()
        cmd_ready    = Signal()
        cmd_is_read  = Signal()
        cmd_is_write = Signal()
        self.sync += [
            cmd_valid.eq(cmd.valid),
            cmd_ready.eq(cmd.ready),
            cmd_is_read.eq(cmd.is_read),
            cmd_is_write.eq(cmd.is_write)
        ]

        counter   = Signal(period_bits)
        period    = Signal()
        nreads    = Signal(period_bits + 1)
        nwrites   = Signal(period_bits + 1)
        nreads_r  = Signal(period_bits + 1)
        nwrites_r = Signal(period_bits + 1)
        self.sync += [
            Cat(counter, period).eq(counter + 1),
            If(period,
                nreads_r.eq(nreads),
                nwrites_r.eq(nwrites),
                nreads.eq(0),
                nwrites.eq(0),
                # don't miss command if there is one on period boundary
                If(cmd_valid & cmd_ready,
                    If(cmd_is_read, nreads.eq(1)),
                    If(cmd_is_write, nwrites.eq(1)),
                )
            ).Elif(cmd_valid & cmd_ready,
                If(cmd_is_read, nreads.eq(nreads + 1)),
                If(cmd_is_write, nwrites.eq(nwrites + 1)),
            ),
            If(self.update.re,
                self.nreads.status.eq(nreads_r),
                self.nwrites.status.eq(nwrites_r)
            )
        ]
