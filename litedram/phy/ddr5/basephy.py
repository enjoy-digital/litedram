#
# This file is part of LiteDRAM.
#
# Copyright (c) 2022 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from operator import or_, xor
from functools import reduce

from litedram.phy.sim_utils import SimLogger, log_level_getter

from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

from litedram.phy.utils import (bitpattern, delayed, Serializer, Deserializer, Latency,
    CommandsPipeline)
from litedram.phy.ddr5.commands import DFIPhaseAdapter


class DDR5Output:
    """Unserialized output of DDR5PHY. Has to be serialized by concrete implementation."""
    def __init__(self, nphases, databits, nranks, nstrobes, with_sub_channels=False):
        self.ck_t   = Signal(2*nphases)
        self.ck_c   = Signal(2*nphases)
        self.reset_n = Signal(nphases)
        self.alert_n = Signal(nphases)

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]

        for prefix in prefixes:
            setattr(self, prefix+'cs_n', [Signal(nphases) for _ in range(nranks)])
            setattr(self, prefix+'ca',   [Signal(2*nphases) for _ in range(14)]) # 2*nphases, as phy will run in ddr mode
            setattr(self, prefix+'par',  Signal(2*nphases))

            setattr(self, prefix+'dq_o',  [Signal(2*nphases) for _ in range(databits)])
            setattr(self, prefix+'dq_i',  [Signal(2*nphases) for _ in range(databits)])
            setattr(self, prefix+'dq_oe', Signal())  # no serialization

            setattr(self, prefix+'dm_n_o',  [Signal(2*nphases) for _ in range(nstrobes)])
            setattr(self, prefix+'dm_n_i',  [Signal(2*nphases) for _ in range(nstrobes)])
            setattr(self, prefix+'dm_n_oe', Signal())  # no serialization

            setattr(self, prefix+'dqs_t_o',  [Signal(2*nphases) for _ in range(nstrobes)])
            setattr(self, prefix+'dqs_t_i',  [Signal(2*nphases) for _ in range(nstrobes)])
            setattr(self, prefix+'dqs_t_oe', Signal())  # no serialization
            setattr(self, prefix+'dqs_c_o',  [Signal(2*nphases) for _ in range(nstrobes)])
            setattr(self, prefix+'dqs_c_i',  [Signal(2*nphases) for _ in range(nstrobes)])
            setattr(self, prefix+'dqs_c_oe', Signal())  # no serialization


class DDR5DQSPattern(Module):
    def __init__(self, preamble=None, postamble=None, wlevel_en=0, wlevel_strobe=0, register=False):
        self.preamble  = Signal() if preamble  is None else preamble
        self.postamble = Signal() if postamble is None else postamble
        self.o = Signal(8)

        # # #

        # DQS Pattern transmitted as LSB-first.

        self.comb += [
            self.o.eq(0b01010101),
            If(self.preamble,
                self.o.eq(0b01000000)  # 2tCK write preamble (0100 prefix matters only)
            ),
            If(self.postamble,
                self.o.eq(0b00000000) # 0.5 tCK write postamble (0 prefix matters only)
            ),
            If(wlevel_en,
                self.o.eq(0b00000000),
                If(wlevel_strobe,
                    # use 2 toggles as, according to datasheet, the first one may not be registered
                    self.o.eq(0b00000101)
                )
            )
        ]
        if register:
            o = Signal.like(self.o)
            self.sync += o.eq(self.o)
            self.o = o


class DDR5PHY(Module, AutoCSR):
    """Core of DDR5 PHYs.

    This class implements all the logic required to convert DFI to/from pads.
    It works in a single clock domain. Signals for DRAM pads are stored in
    DDR5Output (self.out). Concrete implementations of DDR5 PHYs derive
    from this class and perform (de-)serialization of DDR5Output to pads.

    DFI commands
    ------------
    Not all DDR5 commands map directly to DFI commands. For this reason ZQC
    is treated specially in that DFI ZQC is translated into DDR5 MPC and has
    different interpretation depending on DFI.address.

    Due to the fact that DDR5 has 256-bit Mode Register space, the DFI MRS
    command encodes both register address *and* value in DFI.address (instead
    of the default in LiteDRAM to split them between DFI.address and DFI.bank).
    The MRS command is used both for Mode Register Write and Mode Register Read.
    The command is selected based on the value of DFI.bank.

    Refer to the documentation in `commands.py` for further information.

    Parameters
    ----------
    pads : object
        Object containing DDR5 pads.
    sys_clk_freq : float
        Frequency of memory controller's clock.
    ser_latency : Latency
        Additional latency introduced due to signal serialization.
    des_latency : Latency
        Additional latency introduced during signal deserialization.
    phytype : str
        Name of the PHY (concrete implementation).
    cmd_delay : int
        Used to force cmd delay during initialization in BIOS.
    masked_write : bool
        Use masked variant of WRITE command.
    extended_overlaps_check : bool
        Include additional command overlap checks. Makes no sense during normal operation
        (when the DRAM controller works correctly), so use `False` to avoid wasting resources.
    """
    def __init__(self, pads, *,
                 sys_clk_freq, ser_latency, des_latency, phytype, with_sub_channels=False,
                 cmd_delay=None, masked_write=False, extended_overlaps_check=False):
        self.pads        = pads
        self.memtype     = memtype     = "DDR5"
        self.nranks      = nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        self.databits    = databits    = len(pads.dq) if hasattr(pads, 'dq') else len(pads.A_dq)
        self.strobes     = strobes     = len(pads.dqs_t) if hasattr(pads, "dqs_t") else len(pads.A_dqs_t)
        self.addressbits = addressbits = 18 # for activate row address
        self.bankbits    = bankbits    = 8  # 5 bankbits, but we use 8 for Mode Register address in MRS
        self.nphases     = nphases     = 4
        self.with_sub_channels         = with_sub_channels
        self.tck         = tck         = 1 / (nphases*sys_clk_freq)
        assert databits % 4 == 0

        # Parameters -------------------------------------------------------------------------------
        def get_cl_cw(memtype, tck):
            f_to_cl_cwl = OrderedDict()
            f_to_cl_cwl[3200e6] = 22
            f_to_cl_cwl[3600e6] = 28
            f_to_cl_cwl[4000e6] = 32
            f_to_cl_cwl[4400e6] = 36
            f_to_cl_cwl[4800e6] = 40
            f_to_cl_cwl[5200e6] = 42
            f_to_cl_cwl[5600e6] = 46
            f_to_cl_cwl[6000e6] = 50
            f_to_cl_cwl[6400e6] = 54
            f_to_cl_cwl[6800e6] = 56
            for f, cl in f_to_cl_cwl.items():
                if tck > 1/f:
                    return cl
            raise ValueError

        # Commands are sent over 2 DRAM clocks (sys4x) and we count cl/cwl from last bit
        cmd_latency     = 2

        cl              = get_cl_cw(memtype, tck)
        cwl = cl - 2
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)
        # For reads we need to account for ser+des+(1 full MC clock delay to accomodate latency from write) to make sure we get the data in-phase with sys clock
        rdphase = get_sys_phase(nphases, cl_sys_latency, cl + cmd_latency +
                                ser_latency.sys4x + des_latency.sys4x)
        # No need to modify wrphase, because ser_latency applies the same to both CA and DQ
        wrphase = get_sys_phase(nphases, cwl_sys_latency, cwl + cmd_latency)

        # When the calculated phase is negative, it means that we need to increase sys latency
        def updated_latency(phase, sys_latency):
            while phase < 0:
                phase += nphases
                sys_latency += 1
            return phase, sys_latency

        wrphase, cwl_sys_latency = updated_latency(wrphase, cwl_sys_latency)
        rdphase, cl_sys_latency = updated_latency(rdphase, cl_sys_latency)

        # Read latency
        read_data_delay = ser_latency.sys4x//4 + cl_sys_latency # DFI cmd -> read data on DQ
        read_des_delay  = des_latency.sys4x//4 # data on DQ -> data on DFI rddata
        read_latency    = read_data_delay + read_des_delay

        # Write latency
        write_latency = cwl_sys_latency

        # Registers --------------------------------------------------------------------------------
        self._rst             = CSRStorage()

        self._wlevel_en     = CSRStorage()
        self._wlevel_strobe = CSR()

        self._dly_sel = CSRStorage(databits)

        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        self._wdly_dq_bitslip_rst = CSR()
        self._wdly_dq_bitslip     = CSR()

        self._rdphase = CSRStorage(log2_int(nphases), reset=rdphase)
        self._wrphase = CSRStorage(log2_int(nphases), reset=wrphase)

        self._ddr_mode           = CSRStorage()

        combined_data_bits = databits if not with_sub_channels else 2*databits

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            phytype       = phytype,
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = 2*combined_data_bits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = self._rdphase.storage,
            wrphase       = self._wrphase.storage,
            cl            = cl,
            cwl           = cwl,
            read_latency  = read_latency,
            write_latency = write_latency,
            cmd_latency   = cmd_latency,
            cmd_delay     = cmd_delay,
            bitslips      = 1,
            strobes       = strobes,
            with_sub_channels = with_sub_channels,
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = Interface(14, 1, nranks, 2*combined_data_bits, nphases=4, with_sub_channels=with_sub_channels)
        self.delayed_dfi = dfi = Interface(14, 1, nranks, 2*combined_data_bits, nphases=4, with_sub_channels=with_sub_channels)
        for phase, phased in zip(self.dfi.phases, self.delayed_dfi.phases):
            for sig_or_rec in phase.layout:
                if len(sig_or_rec) == 3:
                    name, width, direction = sig_or_rec
                    if direction == 2:
                        self.sync += getattr(phased, name).eq(getattr(phase, name))
                else:
                    sub_rec_name = sig_or_rec[0]
                    for name, width, direction in sig_or_rec[1]:
                        if direction == 2:
                            self.sync += getattr(getattr(phased, sub_rec_name), name).eq(
                                         getattr(getattr(phase, sub_rec_name), name))


        # Now prepare the data by converting the sequences on adapters into sequences on the pads.
        # We have to ignore overlapping commands, and module timings have to ensure that there are
        # no overlapping commands anyway.
        self.out = DDR5Output(nphases, databits, nranks, strobes, with_sub_channels)

        # Clocks -----------------------------------------------------------------------------------
        self.comb += self.out.ck_t.eq(bitpattern("-_-_-_-_"))
        self.comb += self.out.ck_c.eq(bitpattern("_-_-_-_-"))

        # Simple commands --------------------------------------------------------------------------
        self.comb += self.out.reset_n.eq(Cat(phase.reset_n for phase in dfi.phases))
        self.comb += [phase.alert_n.eq(self.out.alert_n[i]) for i, phase in enumerate(self.dfi.phases)]

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]

        for prefix in prefixes:
            # DDR5 Commands --------------------------------------------------------------------------

            for rank in range(nranks):
                self.comb += getattr(self.out, prefix + 'cs_n')[rank].eq(Cat([getattr(phase, prefix).cs_n[rank] for phase in dfi.phases]))
            self.comb += getattr(self.out, prefix + 'par').eq(
                Cat([reduce(xor, getattr(phase, prefix).address[7*i:7+7*i])] for phase in dfi.phases for i in range(2)))

            for bit in range(7):
                self.comb += (
                    If(self._ddr_mode.storage,
                        getattr(self.out, prefix+'ca')[bit].eq(
                            Cat([getattr(phase, prefix).address[bit + 7*i] for phase in dfi.phases for i in range (2)]))
                    ).Else(
                        getattr(self.out, prefix+'ca')[bit].eq(
                            Cat([getattr(phase, prefix).address[bit] for phase in dfi.phases for _ in range (2)]))
                    )
                )
            for bit in range(7, 14):
                self.comb += getattr(self.out, prefix+'ca')[bit].eq(
                    Cat([getattr(phase, prefix).address[bit] for phase in dfi.phases for _ in range (2)]))

            # DQ ---------------------------------------------------------------------------------------
            dq_oe = Signal()
            self.comb += getattr(self.out, prefix+'dq_oe').eq(dq_oe)

            delayed_rddata = Array([Signal.like(getattr(dfi.phases[0], prefix).rddata) for _ in range(nphases)])

            for bit in range(self.databits):
                # output
                wrdata = [
                    getattr(dfi.phases[i//2], prefix).wrdata[i%2 * self.databits + bit] for i in range(2, 2*nphases)
                ] + [
                    getattr(self.dfi.phases[0], prefix).wrdata[bit],
                    getattr(self.dfi.phases[0], prefix).wrdata[self.databits + bit]
                ]
                self.comb += getattr(self.out, prefix+'dq_o')[bit].eq(Cat(*wrdata))
                # input
                dq_i_bs = Signal(2*nphases)
                self.comb += dq_i_bs.eq(getattr(self.out, prefix+'dq_i')[bit])
                for i in range(2*(nphases-1), 2*nphases):
                    self.sync += delayed_rddata[i//2][i%2 * self.databits + bit].eq(dq_i_bs[i])

                for i in range(2*(nphases-1)):
                    self.comb += getattr(self.dfi.phases[1+i//2], prefix).rddata[i%2 * self.databits + bit].eq(dq_i_bs[i])

                for i in range(2*(nphases-1), 2*nphases):
                    self.comb += getattr(self.dfi.phases[0], prefix).rddata[i%2 * self.databits + bit].eq(
                        delayed_rddata[i//2][i%2 * self.databits + bit])
            # DQS --------------------------------------------------------------------------------------
            dqs_oe        = Signal()
            dqs_preamble  = Signal()
            dqs_postamble = Signal()
            dqs_pattern   = DDR5DQSPattern(
                preamble      = dqs_preamble,
                postamble     = dqs_postamble,
                wlevel_en     = self._wlevel_en.storage,
                wlevel_strobe = self._wlevel_strobe.re)
            self.submodules += dqs_pattern

            self.comb += [
                getattr(self.out, prefix+'dqs_t_oe').eq(dqs_oe),
                getattr(self.out, prefix+'dqs_c_oe').eq(dqs_oe),
            ]

            dqs_pattern_delayed = Signal.like(dqs_pattern.o)
            self.sync += dqs_pattern_delayed.eq(dqs_pattern.o)

            for byte in range(strobes):
                # output
                self.comb += [
                    getattr(self.out, prefix+'dqs_t_o')[byte].eq(Cat(dqs_pattern_delayed[2:8], dqs_pattern.o[0:2])),
                    getattr(self.out, prefix+'dqs_c_o')[byte].eq(~Cat(dqs_pattern_delayed[2:8], dqs_pattern.o[0:2])),
                ]

            # DMI --------------------------------------------------------------------------------------
            # DMI signal is used for Data Mask or Data Bus Invertion depending on Mode Registers values.
            # With DM and DBI disabled, this signal is a Don't Care.
            # With DM enabled, masking is performed only when the command used is WRITE-MASKED.
            # We don't support DBI, DM support is configured statically with `masked_write`.
            for byte in range(strobes):
                if isinstance(masked_write, Signal) or masked_write:
                    self.comb += getattr(self.out, prefix+'dm_n_oe').eq(getattr(self.out, prefix+'dq_oe'))
                    wrdata_mask = [
                        getattr(dfi.phases[i//2], prefix).wrdata_mask[i%2 * strobes + byte]
                        for i in range(2, 2*nphases)
                    ] + [
                        getattr(self.dfi.phases[0], prefix).wrdata_mask[byte],
                        getattr(self.dfi.phases[0], prefix).wrdata_mask[strobes + byte]
                    ]
                    self.comb += getattr(self.out, prefix+'dm_n_o')[byte].eq(Cat(*wrdata_mask))
                else:
                    self.comb += getattr(self.out, prefix+'dm_n_o')[byte].eq(0)
                    self.comb += getattr(self.out, prefix+'dm_n_oe').eq(0)

            # Read Control Path ------------------------------------------------------------------------
            # Creates a delay line of read commands coming from the DFI interface. The output is used to
            # signal a valid read data to the DFI interface.
            #
            # The read data valid is asserted for 1 sys_clk cycle when the data is available on the DFI
            # interface, the latency is the sum of the OSERDESE2, CAS, ISERDESE2 and Bitslip latencies.
            rddata_en = TappedDelayLine(
                signal = reduce(or_, [getattr(dfi.phases[i], prefix).rddata_en for i in range(nphases)]),
                ntaps  = self.settings.read_latency
            )
            self.submodules += rddata_en

            self.comb += [
                getattr(phase, prefix).rddata_valid.eq(rddata_en.output | self._wlevel_en.storage)
                for phase in self.dfi.phases
            ]

            # Write Control Path -----------------------------------------------------------------------
            wrtap = cwl_sys_latency - 1
            assert wrtap >= 0

            # Create a delay line of write commands coming from the DFI interface. This taps are used to
            # control DQ/DQS tristates.
            wrdata_en = TappedDelayLine(
                signal = reduce(or_, [getattr(dfi.phases[i], prefix).wrdata_en for i in range(nphases)]),
                ntaps  = wrtap + 2
            )
            self.submodules += wrdata_en

            dq_oe_delay_serial = TappedDelayLine(
                signal=wrdata_en.taps[wrtap],
                ntaps=Serializer.LATENCY,
            )

            dq_oe_delay = TappedDelayLine(
                signal=dq_oe_delay_serial.output,
                ntaps=6,
            )

            self.submodules += dq_oe_delay_serial
            self.submodules += ClockDomainsRenamer("sys4x_90_ddr")(dq_oe_delay)
            self.comb += dq_oe.eq(dq_oe_delay.output)
            # Always enabled in write leveling mode, else during transfers
            self.sync += dqs_oe.eq(self._wlevel_en.storage | (dqs_preamble | wrdata_en.taps[wrtap] | dqs_postamble))

            # Write DQS Postamble/Preamble Control Path ------------------------------------------------
            # Generates DQS Preamble 1 cycle before the first write and Postamble 1 cycle after the last
            # write. During writes, DQS tristate is configured as output for at least 3 sys_clk cycles:
            # 1 for Preamble, 1 for the Write and 1 for the Postamble.
            def wrdata_en_tap(i):  # allows to have wrtap == 0
                return wrdata_en.input if i == -1 else wrdata_en.taps[i]
            self.comb += dqs_preamble.eq( wrdata_en_tap(wrtap - 1)  & ~wrdata_en_tap(wrtap - 0))
            self.comb += dqs_postamble.eq(wrdata_en_tap(wrtap + 1)  & ~wrdata_en_tap(wrtap - 0))

    def get_rst(self, byte, rst):
        return (self._dly_sel.storage[byte] & rst) | self._rst.storage

    def get_inc(self, byte, inc):
        return self._dly_sel.storage[byte] & inc
