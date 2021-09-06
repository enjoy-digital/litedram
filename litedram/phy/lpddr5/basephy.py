#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import copy
import collections
from operator import or_, and_
from functools import reduce
from typing import Tuple

from migen import *

from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import AutoCSR, CSRStorage, CSR

from litedram.common import BitSlip, get_sys_latency, get_sys_phase, PhySettings, TappedDelayLine
from litedram.phy.dfi import Interface as DFIInterface, DFIRateConverter
from litedram.phy.utils import CommandsPipeline, bitpattern, delayed, HoldValid
from litedram.phy.lpddr5.commands import DFIPhaseAdapter, WCKSyncType


class LPDDR5Output:
    """Unserialized output of LPDDR5PHY. Has to be serialized by concrete implementation."""
    def __init__(self, databits, wck_ck_ratio):
        assert databits % 8 == 0
        self.reset_n = Signal()
        self.ck      = Signal(2)
        self.cs      = Signal()  # CK SDR
        self.ca      = [Signal(2) for _ in range(7)]  # CK DDR
        # WCK DDR
        self.dq_o    = [Signal(2*wck_ck_ratio) for _ in range(databits)]
        self.dq_i    = [Signal(2*wck_ck_ratio) for _ in range(databits)]
        self.dq_oe   = Signal()
        self.wck     = [Signal(2*wck_ck_ratio)   for _ in range(databits//8)]
        self.rdqs_o  = [Signal(2*wck_ck_ratio)   for _ in range(databits//8)]
        self.rdqs_i  = [Signal(2*wck_ck_ratio)   for _ in range(databits//8)]
        self.rdqs_oe = Signal()
        self.dmi_o   = [Signal(2*wck_ck_ratio) for _ in range(databits//8)]
        self.dmi_i   = [Signal(2*wck_ck_ratio) for _ in range(databits//8)]
        self.dmi_oe  = Signal()


def namedtuple(cls):
    # This is a simple workaround the lack of dataclasses module in Python <3.7
    # It will instead take given class and generate a new one that inherits
    # from namedtuple with fields that are retrieved from class annotations.
    assert cls.__base__ is object, "Supports only simple classes with no inheritance"
    # retrieve field names and generate namedtuple class
    fields = [name for name, _type in cls.__annotations__.items()]
    ntuple_cls = collections.namedtuple(cls.__name__, fields)
    # create a new type inheriting from the generated namedtuple
    new_cls = type(cls.__name__, (ntuple_cls, object), cls.__dict__.copy())
    return new_cls


@namedtuple
class FreqRange:
    mr:                 int                  # MR2[3:0] value
    data_rate:          Tuple[int, int]      # (> Mbps, <= Mbps)
    wl:                 Tuple[int, int]      # (Set A, Set B)
    t_wckenl_wr:        Tuple[int, int]      # (Set A, Set B)
    t_wckpre_static:    int
    t_wckpre_toggle_wr: int
    rl:                 Tuple[int, int, int] # (Set 0, Set 1, Set 2)
    t_wckenl_rd:        Tuple[int, int, int] # (Set 0, Set 1, Set 2)
    t_wckpre_toggle_rd: int
    n_rbtp:             int
    n_wr:               int
    n_wr_op:            int                  # MR2[7:4]

    @property
    def ck_freq(self):
        low, high = self.data_rate
        return (round(low / 4), round(high / 4))

    def for_set(self, wl_set, rl_set):
        wl_set = {"A": 0, "B": 1}[wl_set]
        return self._replace(
            wl          = self.wl[wl_set],
            t_wckenl_wr = self.t_wckenl_wr[wl_set],
            rl          = self.rl[rl_set],
            t_wckenl_rd = self.t_wckenl_rd[rl_set],
        )

# Taken from Tables 182, 183, 201 of JEDEC specification for LPDDR5
# WCK:CK 2:1 or 4:1, DVFSC diabled, Read Link ECC off
FREQUENCY_RANGES = {
    2: [
        #         MR       DR            WL                     RL                              nWR
        FreqRange(0b0000, (40,   533),  (4,  4),  (1, 1), 1, 3, ( 6,  6,  6), (0, 0, 0),  6, 0,  5, 0b0000),
        FreqRange(0b0001, (533,  1067), (4,  6),  (0, 2), 2, 3, ( 8,  8,  8), (0, 0, 0),  7, 0, 10, 0b0001),
        FreqRange(0b0010, (1067, 1600), (6,  8),  (1, 3), 2, 4, (10, 10, 12), (1, 1, 3),  8, 0, 14, 0b0010),
        FreqRange(0b0011, (1600, 2133), (8,  10), (2, 4), 3, 4, (12, 14, 14), (2, 4, 4),  8, 0, 19, 0b0011),
        FreqRange(0b0100, (2133, 2750), (8,  14), (1, 7), 4, 4, (16, 16, 18), (3, 3, 5), 10, 2, 24, 0b0100),
        FreqRange(0b0101, (2750, 3200), (10, 16), (3, 9), 4, 4, (18, 20, 20), (5, 7, 7), 10, 2, 28, 0b0101),
    ],
    4: [
        #         MR       DR            WL                      RL                              nWR
        FreqRange(0b0000, (40,   533),  (2,  2),  (0, 0),  1, 2, ( 3,  3,  3), (0, 0, 0),  3, 0,  3, 0b0000),
        FreqRange(0b0001, (533,  1067), (2,  3),  (0, 1),  1, 2, ( 4,  4,  4), (0, 0, 0),  4, 0,  5, 0b0001),
        FreqRange(0b0010, (1067, 1600), (3,  4),  (1, 2),  1, 2, ( 5,  5,  6), (1, 1, 2),  4, 0,  7, 0b0010),
        FreqRange(0b0011, (1600, 2133), (4,  5),  (1, 2),  2, 2, ( 6,  7,  7), (1, 2, 2),  4, 0, 10, 0b0011),
        FreqRange(0b0100, (2133, 2750), (4,  7),  (1, 4),  2, 2, ( 8,  8,  9), (2, 2, 3),  5, 1, 12, 0b0100),
        FreqRange(0b0101, (2750, 3200), (5,  8),  (2, 5),  2, 2, ( 9, 10, 10), (3, 4, 4),  5, 1, 14, 0b0101),
        FreqRange(0b0110, (3200, 3733), (6,  9),  (2, 5),  3, 2, (10, 11, 12), (3, 4, 5),  5, 2, 16, 0b0110),
        FreqRange(0b0111, (3733, 4267), (6,  11), (2, 7),  3, 2, (12, 13, 14), (4, 5, 6),  6, 2, 19, 0b0111),
        FreqRange(0b1000, (4267, 4800), (7,  12), (3, 8),  3, 2, (13, 14, 15), (5, 6, 7),  6, 3, 21, 0b1000),
        FreqRange(0b1001, (4800, 5500), (8,  14), (3, 9),  4, 2, (15, 16, 17), (6, 7, 8),  6, 4, 24, 0b1001),
        FreqRange(0b1010, (5500, 6000), (9,  15), (4, 10), 4, 2, (16, 17, 19), (6, 7, 9),  7, 4, 26, 0b1010),
        FreqRange(0b1011, (6000, 6400), (9,  16), (4, 11), 4, 2, (17, 18, 20), (7, 8, 10), 7, 4, 28, 0b1011),
    ]
}

def get_frange(twck, wck_ck_ratio):
    data_rate = 2 * 1/twck
    for frange in FREQUENCY_RANGES[wck_ck_ratio]:
        dr_min, dr_max = frange.data_rate
        if dr_min < data_rate/1e6 <= dr_max:
            return frange
    raise ValueError

class LPDDR5PHY(Module, AutoCSR):
    """Core logic of LPDDR5 PHY

    Implements LPDDR5 logic translating DFI commands into sequences on LPDDR5 pads, without handling
    data (de-)serialization. To create a PHY for specific devices, derive from this class and add
    serdes blocks between the signals in `self.out` and device pads.

    DFI commands
    ------------
    We don't currently use official DFI specification regarding CA commands being generated by MC
    and sent on DFI.address. Instead, regular cas/ras/we commands are translated to CA values by the
    PHY itself. Some commands use special encoding, refer to `DFIPhaseAdapter` class documentation
    for more information.

    Parameters
    ----------
    pads : object
        Object containing LPDDR5 pads.
    ck_freq : float
        Frequency of commands clock (CK).
    ser_latency : Latency
        Additional latency introduced due to signal serialization.
    des_latency : Latency
        Additional latency introduced during signal deserialization.
    phytype : str
        Name of the PHY (concrete implementation).
    cmd_delay : int
        Used to force cmd delay during initialization in BIOS.
    masked_write : bool
        Use MASKED-WRITE commands if True else use WRITE commands (data masking will not work).
    wck_ck_ratio : 2 or 4
        Specifies the WCK:CK ratio used.
    """
    def __init__(self, pads, *, ck_freq, phytype, ser_latency, des_latency, cmd_delay=None,
            masked_write=True, wck_ck_ratio=2, csr_cdc=None):
        self.pads        = pads
        self.memtype     = memtype     = "LPDDR5"
        self.nranks      = nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        self.databits    = databits    = len(pads.dq)
        self.addressbits = addressbits = 18  # for activate row address
        self.bankbits    = bankbits    = 7  # 4, but 7 bits needed for Mode Register address
        self.nphases     = nphases     = 1
        self.twck        = twck        = 1 / (wck_ck_ratio * ck_freq)
        self.ser_latency = ser_latency
        self.des_latency = des_latency
        assert databits % 8 == 0

        # Parameters -------------------------------------------------------------------------------
        frange = get_frange(twck, wck_ck_ratio).for_set(wl_set="A", rl_set=0)

        # Burst spans several CK cycles
        burst_len = 16
        burst_ck_cycles = burst_len // (2*wck_ck_ratio)

        # Bitslip introduces latency from 1 up to `cycles + 1` (sys)
        bitslip_cycles  = 1
        bitslip_range   = 1
        # Commands are sent over 2 CK and we count cl/cwl from the 2nd CK
        cmd_latency     = 1

        cl, cwl = frange.rl, frange.wl  # measured with respect to CK

        # Read latency
        # DFI cmd -> cmd buf -> PHY serializers -> DRAM -> Read Latency -> DQ data
        # -> PHY deserializers -> Bitslip -> Burst cycles -> StrideConverter -> DFI rddata
        read_data_delay = cmd_latency + ser_latency.sys + cl  # DFI cmd -> read data on DQ
        read_des_delay  = des_latency.sys + bitslip_cycles+bitslip_range + burst_ck_cycles  # DQ -> DFI rddata
        read_latency    = read_data_delay + read_des_delay

        # Write latency
        write_latency = cwl + cmd_latency

        # Registers --------------------------------------------------------------------------------
        self._rst = CSRStorage()

        self._wlevel_en     = CSRStorage()
        self._wlevel_strobe = CSR()

        self._dly_sel = CSRStorage(databits//8)

        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        self._wdly_dq_bitslip_rst = CSR()
        self._wdly_dq_bitslip     = CSR()

        # Add CDC in case of memory controller operating in different clock domain than this PHY.
        csr_cdc = csr_cdc or (lambda i: i)
        wlevel_strobe       = csr_cdc(self._wlevel_strobe.re)
        rdly_dq_bitslip_rst = csr_cdc(self._rdly_dq_bitslip_rst.re)
        rdly_dq_bitslip     = csr_cdc(self._rdly_dq_bitslip.re)
        wdly_dq_bitslip_rst = csr_cdc(self._wdly_dq_bitslip_rst.re)
        wdly_dq_bitslip     = csr_cdc(self._wdly_dq_bitslip.re)

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            phytype       = phytype,
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = burst_len * databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = 0,
            wrphase       = 0,
            cl            = cl,
            cwl           = cwl,
            read_latency  = read_latency,
            write_latency = write_latency,
            cmd_latency   = cmd_latency,
            cmd_delay     = cmd_delay,
            bitslips      = 8,
        )
        self.settings.wck_ck_ratio  = wck_ck_ratio

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = DFIInterface(
            addressbits, bankbits, nranks, self.settings.dfi_databits, nphases)

        # # #

        self.submodules.adapter = DFIPhaseAdapter(dfi.p0, masked_write=masked_write)
        self.out = LPDDR5Output(databits, wck_ck_ratio)

        # CK ---------------------------------------------------------------------------------------
        self.comb += self.out.ck.eq(bitpattern("-_-_-_-_"))

        # Commands ---------------------------------------------------------------------------------
        # Commands are sent with SDR CS and DDR CA[6:0] clocked by CK. DFI command can translate to
        # 1 or 2 LPDDR5 commands. If we need two commands we send them in this and the next cycle,
        # if there is 1 command, we delay it 1 cycle to be consistent with all timing calculations.
        # It is illegal to send 2 DFI commands in 2 following cycles (second will be ignored). This
        # will in practice be limited by timing constraints.
        cmd_buf = stream.PipeValid([("cs", 1), ("ca_p", 7), ("ca_n", 7)])
        self.submodules += cmd_buf
        self.comb += [
            # ignore command if it comes just after the first one
            cmd_buf.sink.valid.eq(self.adapter.valid & ~cmd_buf.source.valid),
            # buffer the the second command
            cmd_buf.sink.cs.eq(self.adapter.cmd2.cs),
            cmd_buf.sink.ca_p.eq(self.adapter.cmd2.ca[0]),
            cmd_buf.sink.ca_n.eq(self.adapter.cmd2.ca[1]),
            # we pop the data in the next cycle
            cmd_buf.source.ready.eq(1),
        ]

        def set_cmd(out, cmd1, cmd2, default=0):
            return If(cmd_buf.source.valid, # cmd2 stored in the previous cycle
                out.eq(cmd2)
            ).Elif(self.adapter.valid, # cmd1 on DFI (note: there is no cmd2 from prev cycle)
                out.eq(cmd1)
            ).Else(
                out.eq(default)
            )

        self.comb += set_cmd(self.out.cs, cmd1=self.adapter.cmd1.cs, cmd2=cmd_buf.source.cs),
        for bit in range(7):
            self.comb += [
                set_cmd(self.out.ca[bit][0], cmd1=self.adapter.cmd1.ca[0][bit], cmd2=cmd_buf.source.ca_p[bit]),
                set_cmd(self.out.ca[bit][1], cmd1=self.adapter.cmd1.ca[1][bit], cmd2=cmd_buf.source.ca_n[bit]),
            ]

        self.comb += self.out.reset_n.eq(self.dfi.p0.reset_n)

        # WCK --------------------------------------------------------------------------------------
        # WCK can be enabled/disabled. When enabling, it has to be synchronized with CK. To do so,
        # CAS (alone or followed by WR/RD) must be issued. Synchronization is done after tCKSENL_x
        # after CAS command (CK rising edge), by keeping WCK static for tWCKPRE_Static, then
        # toggling it for tWCKPRE_Toggle_x. If using WCK:CK=4:1, then the first CK of toggling
        # should be with half WCK frequency.
        # Timings are in relation to WL and RL as:
        # WL = tWCKENL_WR - 1 + tWCKPRE_Static + tWCKPRE_Toggle_WR
        # RL = tWCKENL_RD - 1 + tWCKPRE_Static + tWCKPRE_Toggle_RD  (without Byte Mode, nor Read DBI/Read Data Copy)
        wck_sync_done = Signal()
        wck_sync = TappedDelayLine(
            signal = self.adapter.wck_sync,
            ntaps  = max(1, max(frange.t_wckenl_wr, frange.t_wckenl_rd) + frange.t_wckpre_static),
        )
        self.submodules += wck_sync
        wck_sync_taps = Array([wck_sync.input, *wck_sync.taps])

        wck_pattern = Signal(8)  # for WCK:CK=2:1 we take wck_pattern[::2]
        patterns = {
            "disabled":      "________",
            "static":        "________",
            "toggle":        "--__--__",
            "toggle_4:1":    "-_-_-_-_",
            "postamble":     "--______",
            "postamble_4:1": "-_-_-___",
        }

        assert frange.t_wckpre_static > 0  # The algorithm assumes it's never 0

        wck_fsm = FSM()
        self.submodules += wck_fsm
        wck_fsm.act("DISABLED",
            wck_pattern.eq(bitpattern(patterns["disabled"])),
            If(wck_sync_taps[frange.t_wckenl_wr] == WCKSyncType.WR,
                NextState("STATIC")
            ).Elif(wck_sync_taps[frange.t_wckenl_rd] == WCKSyncType.RD,
                NextState("STATIC")
            )
        )
        wck_fsm.act("STATIC",
            wck_pattern.eq(bitpattern(patterns["static"])),
            If(wck_sync_taps[frange.t_wckenl_wr + frange.t_wckpre_static] == WCKSyncType.WR,
                NextState("TOGGLE")
            ).Elif(wck_sync_taps[frange.t_wckenl_rd + frange.t_wckpre_static] == WCKSyncType.RD,
                NextState("TOGGLE")
            )
        )
        wck_fsm.act("TOGGLE",
            wck_pattern.eq(bitpattern(patterns["toggle"])),
            If(~wck_sync_done,
                NextState("POSTAMBLE")
            ).Elif((wck_ck_ratio == 4),  # go to full speed in the next cycle
                NextState("TOGGLE_4:1")
            ),
        )
        wck_fsm.act("TOGGLE_4:1",
            wck_pattern.eq(bitpattern(patterns["toggle_4:1"])),
            If(~wck_sync_done,
                NextState("POSTAMBLE")
            ),
        )
        wck_fsm.act("POSTAMBLE",
            If((wck_ck_ratio == 4),
                wck_pattern.eq(bitpattern(patterns["postamble_4:1"])),
                NextState("DISABLED")
            ).Else(
                wck_pattern.eq(bitpattern(patterns["toggle"])),
                NextState("POSTAMBLE_2:1")
            )
        )
        wck_fsm.act("POSTAMBLE_2:1",
            wck_pattern.eq(bitpattern(patterns["postamble"])),
            NextState("DISABLED")
        )

        wck_out = {2: wck_pattern[::2], 4: wck_pattern}[wck_ck_ratio]
        assert len(wck_out) == len(self.out.wck[0]), (len(wck_out), len(self.out.wck))

        # WCK2CK leveling --------------------------------------------------------------------------

        # Strobe needs to be high for tWCKTGGL which is 8 tWCK periods
        # NOTE: WCK2CK leveling always happens at 2:1 WCK2CK ratio.
        twcktggl = 4
        wckl_strobe_dly = TappedDelayLine(
            signal = self._wlevel_strobe.re,
            ntaps  = twcktggl
        )
        self.submodules += wckl_strobe_dly

        wckl_strobe_en = Signal()
        self.comb += [
            wckl_strobe_en.eq(reduce(or_, wckl_strobe_dly.taps[0:twcktggl]))
        ]

        wckl_pattern = Signal(8)
        self.comb += [
            wckl_pattern.eq(bitpattern(patterns["disabled"])),
            If(wckl_strobe_en,
                wckl_pattern.eq(bitpattern(patterns["toggle"])),
            )
        ]

        wckl_out = {2: wckl_pattern[::2], 4: wckl_pattern}[wck_ck_ratio]

        wck_pattern_selected = Signal(2*wck_ck_ratio)
        self.comb += [
            If(self._wlevel_en.storage,
                wck_pattern_selected.eq(wckl_out)
            ).Else(
                wck_pattern_selected.eq(wck_out)
            )
        ]

        for byte in range(self.databits//8):
            # output
            self.submodules += BitSlip(
                dw     = 2*wck_ck_ratio,
                cycles = bitslip_cycles,
                rst    = self.get_rst(byte, self._wdly_dq_bitslip_rst.re),
                slp    = self.get_inc(byte, self._wdly_dq_bitslip.re),
                i      = wck_pattern_selected,
                o      = self.out.wck[byte],
            )

        # Write Control Path -----------------------------------------------------------------------
        wrtap = write_latency - 1
        assert wrtap >= 0

        wrdata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].wrdata_en for i in range(nphases)]),
            ntaps  = wrtap + (burst_ck_cycles-1) + 2
        )
        self.submodules += wrdata_en

        dq_oe = Signal()
        self.comb += dq_oe.eq(reduce(or_, wrdata_en.taps[wrtap:wrtap+burst_ck_cycles]))

        # Read Control Path ------------------------------------------------------------------------
        rddata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].rddata_en for i in range(nphases)]),
            ntaps  = self.settings.read_latency + burst_ck_cycles
        )
        self.submodules += rddata_en

        # Data Path --------------------------------------------------------------------------------
        self.comb += self.out.dq_oe.eq(delayed(self, dq_oe))
        self.comb += self.out.dmi_oe.eq(self.out.dq_oe if masked_write else 0)

        wrdata_ck = Signal(self.settings.dfi_databits//burst_ck_cycles)
        wrdata_hold = HoldValid([("data", self.settings.dfi_databits)])
        wrdata_converter = stream.Converter(
            nbits_from = self.settings.dfi_databits,
            nbits_to   = len(wrdata_ck),
        )
        self.submodules += wrdata_hold, wrdata_converter

        self.comb += [
            wrdata_hold.sink.data.eq(self.dfi.p0.wrdata),
            wrdata_hold.sink.valid.eq(wrdata_en.taps[wrtap]),
            wrdata_hold.source.connect(wrdata_converter.sink),
            wrdata_ck.eq(wrdata_converter.source.data),
            wrdata_converter.source.ready.eq(1),
        ]

        if masked_write:
            wrdata_mask_ck = Signal(len(wrdata_ck)//8)
            wrdata_mask_hold = HoldValid([("data", self.settings.dfi_databits//8)])
            wrdata_mask_converter = stream.Converter(
                nbits_from = self.settings.dfi_databits//8,
                nbits_to   = len(wrdata_mask_ck),
            )
            self.submodules += wrdata_mask_hold, wrdata_mask_converter

            self.comb += [
                wrdata_mask_hold.sink.data.eq(self.dfi.p0.wrdata_mask),
                wrdata_mask_hold.sink.valid.eq(wrdata_en.taps[wrtap]),
                wrdata_mask_hold.source.connect(wrdata_mask_converter.sink),
                wrdata_mask_ck.eq(wrdata_mask_converter.source.data),
                wrdata_mask_converter.source.ready.eq(1),
            ]

        rddata_ck = Signal(self.settings.dfi_databits//burst_ck_cycles)
        rddata_converter = stream.Converter(
            nbits_from = len(rddata_ck),
            nbits_to   = self.settings.dfi_databits,
        )
        self.submodules += rddata_converter

        # TODO: check if that -1 is correct, from Migen simulations it seems like it shouldn't
        # be there, but in LPDDR4 the bitslip_range value was needed
        rddata_start = read_latency - burst_ck_cycles - 1
        self.comb += [
            rddata_converter.sink.data.eq(rddata_ck),
            rddata_converter.sink.valid.eq(reduce(or_, rddata_en.taps[rddata_start:rddata_start+burst_ck_cycles])),
            rddata_converter.source.ready.eq(1),
            self.dfi.p0.rddata.eq(rddata_converter.source.data),
            self.dfi.p0.rddata_valid.eq(rddata_converter.source.valid),
        ]

        # -2 is to take into account the serialization time for wck
        read_wck_latency = cmd_latency + cl + burst_ck_cycles - 2
        write_wck_latency = cmd_latency + cwl + burst_ck_cycles - 2

        self.wck_sync_state = Signal(2)
        self.sync += If(self.adapter.wck_sync != 0,
            wck_sync_done.eq(1),
            self.wck_sync_state.eq(self.adapter.wck_sync)
        ).Elif(self.wck_sync_state == WCKSyncType.RD,
            If(reduce(or_, rddata_en.taps[0:read_wck_latency]) == 0,
                wck_sync_done.eq(0),
                self.wck_sync_state.eq(0b00),
            )
        ).Elif(self.wck_sync_state == WCKSyncType.WR,
            If(reduce(or_, wrdata_en.taps[0:write_wck_latency]) == 0,
                wck_sync_done.eq(0),
                self.wck_sync_state.eq(0b00),
            )
        )

        self.comb += self.adapter.wck_sync_done.eq(wck_sync_done)

        for bit in range(self.databits):
            # output
            wrdata = [wrdata_ck[i * self.databits + bit] for i in range(2*wck_ck_ratio)]
            self.submodules += BitSlip(
                dw     = 2*wck_ck_ratio,
                cycles = bitslip_cycles,
                rst    = self.get_rst(bit//8, wdly_dq_bitslip_rst),
                slp    = self.get_inc(bit//8, wdly_dq_bitslip),
                i      = Cat(*wrdata),
                o      = self.out.dq_o[bit],
            )

            if masked_write and bit % 8 == 0:
                byte = bit//8
                wrdata_mask = [wrdata_mask_ck[i * self.databits//8 + byte] for i in range(2*wck_ck_ratio)]
                self.submodules += BitSlip(
                    dw     = 2*wck_ck_ratio,
                    cycles = bitslip_cycles,
                    rst    = self.get_rst(byte, wdly_dq_bitslip_rst),
                    slp    = self.get_inc(byte, wdly_dq_bitslip),
                    i      = Cat(*wrdata_mask),
                    o      = self.out.dmi_o[byte],
                )

            # input
            dq_i_bs = Signal(2*wck_ck_ratio)
            self.submodules += BitSlip(
                dw     = 2*wck_ck_ratio,
                cycles = bitslip_cycles,
                rst    = self.get_rst(bit//8, rdly_dq_bitslip_rst),
                slp    = self.get_inc(bit//8, rdly_dq_bitslip),
                i      = self.out.dq_i[bit],
                o      = dq_i_bs,
            )
            for i in range(2*wck_ck_ratio):
                self.comb += rddata_ck[i * self.databits + bit].eq(dq_i_bs[i])

    def get_rst(self, byte, rst):
        return (self._dly_sel.storage[byte] & rst) | self._rst.storage

    def get_inc(self, byte, inc):
        return self._dly_sel.storage[byte] & inc
