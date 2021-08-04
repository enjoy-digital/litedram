#
# This file is part of LiteDRAM.
#
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from operator import or_
from functools import reduce

from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

from litedram.phy.utils import (bitpattern, delayed, DQSPattern, Serializer, Deserializer, Latency,
    CommandsPipeline)
from litedram.phy.lpddr4.commands import DFIPhaseAdapter


class LPDDR4Output:
    """Unserialized output of LPDDR4PHY. Has to be serialized by concrete implementation."""
    def __init__(self, nphases, databits):
        # Pads: RESET_N, CS, CKE, CK, CA[5:0], DMI[1:0], DQ[15:0], DQS[1:0], ODT_CA
        self.clk     = Signal(2*nphases)
        self.cke     = Signal(nphases)
        self.odt     = Signal(nphases)
        self.reset_n = Signal(nphases)
        self.cs      = Signal(nphases)
        self.ca      = [Signal(nphases)   for _ in range(6)]
        self.dmi_o   = [Signal(2*nphases) for _ in range(databits//8)]
        self.dmi_i   = [Signal(2*nphases) for _ in range(databits//8)]
        self.dmi_oe  = Signal()  # no serialization
        self.dq_o    = [Signal(2*nphases) for _ in range(databits)]
        self.dq_i    = [Signal(2*nphases) for _ in range(databits)]
        self.dq_oe   = Signal()  # no serialization
        self.dqs_o   = [Signal(2*nphases) for _ in range(databits//8)]
        self.dqs_i   = [Signal(2*nphases) for _ in range(databits//8)]
        self.dqs_oe  = Signal()  # no serialization


class LPDDR4PHY(Module, AutoCSR):
    """Core of LPDDR4 PHYs.

    This class implements all the logic required to convert DFI to/from pads.
    It works in a single clock domain. Signals for DRAM pads are stored in
    LPDDR4Output (self.out). Concrete implementations of LPDDR4 PHYs derive
    from this class and perform (de-)serialization of LPDDR4Output to pads.

    DFI commands
    ------------
    Not all LPDDR4 commands map directly to DFI commands. For this reason ZQC
    is treated specially in that DFI ZQC is translated into LPDDR4 MPC and has
    different interpretation depending on DFI.address.

    Due to the fact that LPDDR4 has 256-bit Mode Register space, the DFI MRS
    command encodes both register address *and* value in DFI.address (instead
    of the default in LiteDRAM to split them between DFI.address and DFI.bank).
    The MRS command is used both for Mode Register Write and Mode Register Read.
    The command is selected based on the value of DFI.bank.

    Refer to the documentation in `commands.py` for further information.

    Parameters
    ----------
    pads : object
        Object containing LPDDR4 pads.
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
        Use MASKED-WRITE commands if True else use WRITE commands (data masking will not work).
    extended_overlaps_check : bool
        Include additional command overlap checks. Makes no sense during normal operation
        (when the DRAM controller works correctly), so use `False` to avoid wasting resources.
    """
    def __init__(self, pads, *,
                 sys_clk_freq, ser_latency, des_latency, phytype,
                 cmd_delay=None, masked_write=True, extended_overlaps_check=False):
        self.pads        = pads
        self.memtype     = memtype     = "LPDDR4"
        self.nranks      = nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        self.databits    = databits    = len(pads.dq)
        self.addressbits = addressbits = 17  # for activate row address
        self.bankbits    = bankbits    = 6  # 3 bankbits, but we use 6 for Mode Register address in MRS
        self.nphases     = nphases     = 8
        self.tck         = tck         = 1 / (nphases*sys_clk_freq)
        assert databits % 8 == 0

        # Parameters -------------------------------------------------------------------------------
        def get_cl_cw(memtype, tck):
            # MT53E256M16D1, No DBI, Set A
            f_to_cl_cwl = OrderedDict()
            f_to_cl_cwl[ 532e6] = ( 6,  4)
            f_to_cl_cwl[1066e6] = (10,  6)
            f_to_cl_cwl[1600e6] = (14,  8)
            f_to_cl_cwl[2132e6] = (20, 10)
            f_to_cl_cwl[2666e6] = (24, 12)
            f_to_cl_cwl[3200e6] = (28, 14)
            f_to_cl_cwl[3732e6] = (32, 16)
            f_to_cl_cwl[4266e6] = (36, 18)
            for f, (cl, cwl) in f_to_cl_cwl.items():
                if tck >= 2/f:
                    return cl, cwl
            raise ValueError

        # Bitslip introduces latency from 1 up to `cycles + 1`
        # FIXME: (check if True) from tests on hardware it seems we need 1 more cycle
        #   of read_latency, probably to have space for manipulating bitslip values
        bitslip_cycles  = 1
        bitslip_range   = 1
        # Commands are sent over 4 DRAM clocks (sys8x) and we count cl/cwl from last bit
        cmd_latency     = 4
        # Commands read from adapters are delayed on ConstBitSlips
        ca_latency      = 1

        cl, cwl         = get_cl_cw(memtype, tck)
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)
        # For reads we need to account for ser+des latency to make sure we get the data in-phase with sys clock
        rdphase = get_sys_phase(nphases, cl_sys_latency, cl + cmd_latency + ser_latency.sys8x % 8 + des_latency.sys8x % 8)
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
        read_data_delay = ca_latency + ser_latency.sys8x//8 + cl_sys_latency  # DFI cmd -> read data on DQ
        read_des_delay  = des_latency.sys8x//8 + bitslip_cycles+bitslip_range  # data on DQ -> data on DFI rddata
        read_latency    = read_data_delay + read_des_delay

        # Write latency
        write_latency = cwl_sys_latency

        # Registers --------------------------------------------------------------------------------
        self._rst             = CSRStorage()

        self._wlevel_en     = CSRStorage()
        self._wlevel_strobe = CSR()

        self._dly_sel = CSRStorage(databits//8)

        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        self._wdly_dq_bitslip_rst = CSR()
        self._wdly_dq_bitslip     = CSR()

        self._rdphase = CSRStorage(log2_int(nphases), reset=rdphase)
        self._wrphase = CSRStorage(log2_int(nphases), reset=wrphase)

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            phytype       = phytype,
            memtype       = memtype,
            databits      = databits,
            dfi_databits  = 2*databits,
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
            bitslips      = 16,
        )

        # DFI Interface ----------------------------------------------------------------------------
        # Due to the fact that LPDDR4 has 16n prefetch we use 8 phases to be able to read/write a
        # whole burst during a single controller clock cycle. PHY should use sys8x clock.
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases=8)

        # # #

        adapters = [DFIPhaseAdapter(phase, masked_write=masked_write) for phase in self.dfi.phases]
        self.submodules += adapters

        # Now prepare the data by converting the sequences on adapters into sequences on the pads.
        # We have to ignore overlapping commands, and module timings have to ensure that there are
        # no overlapping commands anyway.
        self.out = LPDDR4Output(nphases, databits)

        # Clocks -----------------------------------------------------------------------------------
        self.comb += self.out.clk.eq(bitpattern("-_-_-_-_" * 2))

        # Simple commands --------------------------------------------------------------------------
        self.comb += [
            self.out.cke.eq(Cat(delayed(self, phase.cke) for phase in self.dfi.phases)),
            self.out.odt.eq(Cat(delayed(self, phase.odt) for phase in self.dfi.phases)),
            self.out.reset_n.eq(Cat(delayed(self, phase.reset_n) for phase in self.dfi.phases)),
        ]

        # LPDDR4 Commands --------------------------------------------------------------------------
        # Each LPDDR4 command can span several phases (2 or 4), so in theory the commands could
        # overlap. No overlap should be guaranteed by the controller based on module timings, but
        # we also include an overlaps check in PHY logic.
        self.submodules.commands = CommandsPipeline(adapters,
            cs_ser_width = len(self.out.cs),
            ca_ser_width = len(self.out.ca[0]),
            ca_nbits     = len(self.out.ca),
            cmd_nphases_span = 4,
            extended_overlaps_check = extended_overlaps_check
        )

        self.comb += self.out.cs.eq(self.commands.cs)
        for bit in range(6):
            self.comb += self.out.ca[bit].eq(self.commands.ca[bit])

        # DQ ---------------------------------------------------------------------------------------
        dq_oe = Signal()
        self.comb += self.out.dq_oe.eq(delayed(self, dq_oe, cycles=1))

        for bit in range(self.databits):
            # output
            wrdata = [
                self.dfi.phases[i//2].wrdata[i%2 * self.databits + bit]
                for i in range(2*nphases)
            ]
            self.submodules += BitSlip(
                dw     = 2*nphases,
                cycles = bitslip_cycles,
                rst    = self.get_rst(bit//8, self._wdly_dq_bitslip_rst.re),
                slp    = self.get_inc(bit//8, self._wdly_dq_bitslip.re),
                i      = Cat(*wrdata),
                o      = self.out.dq_o[bit],
            )

            # input
            dq_i_bs = Signal(2*nphases)
            self.submodules += BitSlip(
                dw     = 2*nphases,
                cycles = bitslip_cycles,
                rst    = self.get_rst(bit//8, self._rdly_dq_bitslip_rst.re),
                slp    = self.get_inc(bit//8, self._rdly_dq_bitslip.re),
                i      = self.out.dq_i[bit],
                o      = dq_i_bs,
            )
            for i in range(2*nphases):
                self.comb += self.dfi.phases[i//2].rddata[i%2 * self.databits + bit].eq(dq_i_bs[i])

        # DQS --------------------------------------------------------------------------------------
        dqs_oe        = Signal()
        dqs_preamble  = Signal()
        dqs_postamble = Signal()
        dqs_pattern   = DQSPattern(
            preamble      = dqs_preamble,
            postamble     = dqs_postamble,
            wlevel_en     = self._wlevel_en.storage,
            wlevel_strobe = self._wlevel_strobe.re)
        self.submodules += dqs_pattern
        self.comb += [
            self.out.dqs_oe.eq(delayed(self, dqs_oe, cycles=1)),
        ]

        for byte in range(self.databits//8):
            # output
            self.submodules += BitSlip(
                dw     = 2*nphases,
                cycles = bitslip_cycles,
                rst    = self.get_rst(byte, self._wdly_dq_bitslip_rst.re),
                slp    = self.get_inc(byte, self._wdly_dq_bitslip.re),
                i      = dqs_pattern.o,
                o      = self.out.dqs_o[byte],
            )

        # DMI --------------------------------------------------------------------------------------
        # DMI signal is used for Data Mask or Data Bus Invertion depending on Mode Registers values.
        # With DM and DBI disabled, this signal is a Don't Care.
        # With DM enabled, masking is performed only when the command used is WRITE-MASKED.
        # We don't support DBI, DM support is configured statically with `masked_write`.
        for byte in range(self.databits//8):
            if isinstance(masked_write, Signal) or masked_write:
                self.comb += self.out.dmi_oe.eq(self.out.dq_oe)
                wrdata_mask = [
                    self.dfi.phases[i//2] .wrdata_mask[i%2 * self.databits//8 + byte]
                    for i in range(2*nphases)
                ]
                self.submodules += BitSlip(
                    dw     = 2*nphases,
                    cycles = bitslip_cycles,
                    rst    = self.get_rst(byte, self._wdly_dq_bitslip_rst.re),
                    slp    = self.get_inc(byte, self._wdly_dq_bitslip.re),
                    i      = Cat(*wrdata_mask),
                    o      = self.out.dmi_o[byte],
                )
            else:
                self.comb += self.out.dmi_o[byte].eq(0)
                self.comb += self.out.dmi_oe.eq(0)

        # Read Control Path ------------------------------------------------------------------------
        # Creates a delay line of read commands coming from the DFI interface. The output is used to
        # signal a valid read data to the DFI interface.
        #
        # The read data valid is asserted for 1 sys_clk cycle when the data is available on the DFI
        # interface, the latency is the sum of the OSERDESE2, CAS, ISERDESE2 and Bitslip latencies.
        rddata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].rddata_en for i in range(nphases)]),
            ntaps  = self.settings.read_latency
        )
        self.submodules += rddata_en

        self.comb += [
            phase.rddata_valid.eq(rddata_en.output | self._wlevel_en.storage)
            for phase in dfi.phases
        ]

        # Write Control Path -----------------------------------------------------------------------
        wrtap = cwl_sys_latency - 1
        assert wrtap >= 0

        # Create a delay line of write commands coming from the DFI interface. This taps are used to
        # control DQ/DQS tristates.
        wrdata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].wrdata_en for i in range(nphases)]),
            ntaps  = wrtap + 2
        )
        self.submodules += wrdata_en

        self.comb += dq_oe.eq(wrdata_en.taps[wrtap])
        # Always enabled in write leveling mode, else during transfers
        self.comb += dqs_oe.eq(self._wlevel_en.storage | (dqs_preamble | dq_oe | dqs_postamble))

        # Write DQS Postamble/Preamble Control Path ------------------------------------------------
        # Generates DQS Preamble 1 cycle before the first write and Postamble 1 cycle after the last
        # write. During writes, DQS tristate is configured as output for at least 3 sys_clk cycles:
        # 1 for Preamble, 1 for the Write and 1 for the Postamble.
        def wrdata_en_tap(i):  # allows to have wrtap == 0
            return wrdata_en.input if i == -1 else wrdata_en.taps[i]
        self.comb += dqs_preamble.eq( wrdata_en_tap(wrtap - 1)  & ~wrdata_en_tap(wrtap + 0))
        self.comb += dqs_postamble.eq(wrdata_en_tap(wrtap + 1)  & ~wrdata_en_tap(wrtap + 0))

    def get_rst(self, byte, rst):
        return (self._dly_sel.storage[byte] & rst) | self._rst.storage

    def get_inc(self, byte, inc):
        return self._dly_sel.storage[byte] & inc


class DoubleRateLPDDR4PHY(LPDDR4PHY):
    """LPDDR4PHY wrapper that performs one stage of serialization (16:8)

    Needed for targets that only have hardware serialization blocks up to 8:1.
    """
    def __init__(self, pads, *, ser_latency, des_latency, serdes_reset_cnt=0, **kwargs):
        super().__init__(pads,
            ser_latency = ser_latency + Latency(sys=Serializer.LATENCY),
            des_latency = des_latency + Latency(sys=Deserializer.LATENCY),
            **kwargs)

        self._out = self.out
        self.out = LPDDR4Output(nphases=self.nphases//2, databits=self.databits)

        def ser(i, o):
            assert len(o) == len(i)//2
            self.submodules += Serializer(
                clkdiv    = "sys",
                clk       = "sys2x",
                i_dw      = len(i),
                o_dw      = len(o),
                i         = i,
                o         = o,
                reset_cnt = serdes_reset_cnt,
            )

        def des(i, o):
            assert len(i) == len(o)//2
            self.submodules += Deserializer(
                clkdiv    = "sys",
                clk       = "sys2x",
                i_dw      = len(i),
                o_dw      = len(o),
                i         = i,
                o         = o,
                reset_cnt = serdes_reset_cnt,
            )

        # handle ser/des for both the lists (like dq) and just Signal (like cs)
        def apply(fn, i, o):
            if not isinstance(i, list):
                i, o = [i], [o]
            for i_n, o_n in zip(i, o):
                fn(i=i_n, o=o_n)

        for name in vars(self.out):
            old = getattr(self._out, name)
            new = getattr(self.out, name)
            if name.endswith("_oe"):  # OE signals need to be delayed
                self.comb += new.eq(delayed(self, old, cycles=Serializer.LATENCY))
            elif name.endswith("_i"):  # Deserialize inputs
                apply(des, o=old, i=new)
            else:  # All other signals are outputs
                apply(ser, i=old, o=new)
