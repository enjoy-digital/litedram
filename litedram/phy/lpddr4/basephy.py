from operator import or_
from functools import reduce
from collections import defaultdict

from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

from litedram.phy.lpddr4.utils import bitpattern, delayed, ConstBitSlip, DQSPattern
from litedram.phy.lpddr4.commands import DFIPhaseAdapter


class LPDDR4PHY(Module, AutoCSR):
    def __init__(self, pads, *,
                 sys_clk_freq, write_ser_latency, read_des_latency, phytype,
                 masked_write=True, cmd_delay=None):
        self.pads        = pads
        self.memtype     = memtype     = "LPDDR4"
        self.nranks      = nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        self.databits    = databits    = len(pads.dq)
        self.addressbits = addressbits = 17  # for activate row address
        self.bankbits    = bankbits    = 3
        self.nphases     = nphases     = 8
        self.tck         = tck         = 1 / (nphases*sys_clk_freq)
        assert databits % 8 == 0

        # Parameters -------------------------------------------------------------------------------
        def get_cl_cw(memtype, tck):
            # MT53E256M16D1, No DBI, Set A
            f_to_cl_cwl = OrderedDict()
            f_to_cl_cwl[ 532e6] = ( 6,  4)  # FIXME: with that low cwl, wrtap is 0
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

        # Bitslip introduces latency between from `cycles` up to `cycles + 1`
        bitslip_cycles  = 1
        # Commands are sent over 4 cycles of DRAM clock (sys8x)
        cmd_latency     = 4
        # Commands read from adapters are delayed on ConstBitSlips
        ca_latency      = 1

        cl, cwl         = get_cl_cw(memtype, tck)
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)
        rdphase         = get_sys_phase(nphases, cl_sys_latency,   cl + cmd_latency)
        wrphase         = get_sys_phase(nphases, cwl_sys_latency, cwl + cmd_latency)

        # When the calculated phase is negative, it means that we need to increase sys latency
        def updated_latency(phase):
            delay_update = 0
            while phase < 0:
                phase += nphases
                delay_update += 1
            return phase, delay_update

        wrphase, cwl_sys_delay = updated_latency(wrphase)
        rdphase, cl_sys_delay = updated_latency(rdphase)
        cwl_sys_latency += cwl_sys_delay
        cl_sys_latency += cl_sys_delay

        # Read latency
        read_data_delay = ca_latency + write_ser_latency + cl_sys_latency  # DFI cmd -> read data on DQ
        read_des_delay  = read_des_latency + bitslip_cycles  # data on DQ -> data on DFI rddata
        read_latency    = read_data_delay + read_des_delay

        # Write latency
        write_latency = cwl_sys_latency

        # FIXME: remove
        if __import__("os").environ.get("DEBUG") == '1':
            print('cl', end=' = '); __import__('pprint').pprint(cl)
            print('cwl', end=' = '); __import__('pprint').pprint(cwl)
            print('cl_sys_latency', end=' = '); __import__('pprint').pprint(cl_sys_latency)
            print('cwl_sys_latency', end=' = '); __import__('pprint').pprint(cwl_sys_latency)
            print('rdphase', end=' = '); __import__('pprint').pprint(rdphase)
            print('wrphase', end=' = '); __import__('pprint').pprint(wrphase)
            print('read_data_delay', end=' = '); __import__('pprint').pprint(read_data_delay)
            print('read_des_delay', end=' = '); __import__('pprint').pprint(read_des_delay)
            print('read_latency', end=' = '); __import__('pprint').pprint(read_latency)
            print('write_latency', end=' = '); __import__('pprint').pprint(write_latency)

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
        # Pads: reset_n, CS, CKE, CK, CA[5:0], DMI[1:0], DQ[15:0], DQS[1:0], ODT_CA
        self.ck_clk     = Signal(2*nphases)
        self.ck_cke     = Signal(nphases)
        self.ck_odt     = Signal(nphases)
        self.ck_reset_n = Signal(nphases)
        self.ck_cs      = Signal(nphases)
        self.ck_ca      = [Signal(nphases)   for _ in range(6)]
        self.ck_dmi_o   = [Signal(2*nphases) for _ in range(2)]
        self.ck_dmi_i   = [Signal(2*nphases) for _ in range(2)]
        self.dmi_oe     = Signal()
        self.ck_dq_o    = [Signal(2*nphases) for _ in range(databits)]
        self.ck_dq_i    = [Signal(2*nphases) for _ in range(databits)]
        self.dq_oe      = Signal()
        self.ck_dqs_o   = [Signal(2*nphases) for _ in range(2)]
        self.ck_dqs_i   = [Signal(2*nphases) for _ in range(2)]
        self.dqs_oe     = Signal()

        # Clocks -----------------------------------------------------------------------------------
        self.comb += self.ck_clk.eq(bitpattern("-_-_-_-_" * 2))

        # Simple commands --------------------------------------------------------------------------
        self.comb += [
            self.ck_cke.eq(Cat(delayed(self, phase.cke) for phase in self.dfi.phases)),
            self.ck_odt.eq(Cat(delayed(self, phase.odt) for phase in self.dfi.phases)),
            self.ck_reset_n.eq(Cat(delayed(self, phase.reset_n) for phase in self.dfi.phases)),
        ]

        # LPDDR4 Commands --------------------------------------------------------------------------
        # Each command can span several phases (up to 4), so we must ignore overlapping commands,
        # but in general, module timings should be set in a way that overlapping will never happen.

        # Create a history of valid adapters used for masking overlapping ones.
        # TODO: make optional, as it takes up resources and the controller should ensure no overlaps
        valids = ConstBitSlip(dw=nphases, cycles=1, slp=0)
        self.submodules += valids
        self.comb += valids.i.eq(Cat(a.valid for a in adapters))
        # valids_hist = valids.r
        valids_hist = Signal.like(valids.r)
        # TODO: especially make this part optional
        for i in range(len(valids_hist)):
            was_valid_before = reduce(or_, valids_hist[max(0, i-3):i], 0)
            self.comb += valids_hist[i].eq(valids.r[i] & ~was_valid_before)

        cs_per_adapter = []
        ca_per_adapter = defaultdict(list)
        for phase, adapter in enumerate(adapters):
            # The signals from an adapter can be used if there were no commands on 3 previous cycles
            allowed = ~reduce(or_, valids_hist[nphases+phase - 3:nphases+phase])

            # Use CS and CA of given adapter slipped by `phase` bits
            cs_bs = ConstBitSlip(dw=nphases, cycles=1, slp=phase)
            self.submodules += cs_bs
            self.comb += cs_bs.i.eq(Cat(adapter.cs)),
            cs_mask = Replicate(allowed, len(cs_bs.o))
            cs = cs_bs.o & cs_mask
            cs_per_adapter.append(cs)

            # For CA we need to do the same for each bit
            ca_bits = []
            for bit in range(6):
                ca_bs = ConstBitSlip(dw=nphases, cycles=1, slp=phase)
                self.submodules += ca_bs
                ca_bit_hist = [adapter.ca[i][bit] for i in range(4)]
                self.comb += ca_bs.i.eq(Cat(*ca_bit_hist)),
                ca_mask = Replicate(allowed, len(ca_bs.o))
                ca = ca_bs.o & ca_mask
                ca_per_adapter[bit].append(ca)

        # OR all the masked signals
        self.comb += self.ck_cs.eq(reduce(or_, cs_per_adapter))
        for bit in range(6):
            self.comb += self.ck_ca[bit].eq(reduce(or_, ca_per_adapter[bit]))

        # DQ ---------------------------------------------------------------------------------------
        dq_oe = Signal()
        self.comb += self.dq_oe.eq(delayed(self, dq_oe, cycles=1))

        for bit in range(self.databits):
            # output
            self.submodules += BitSlip(
                dw     = 2*nphases,
                cycles = bitslip_cycles,
                rst    = (self._dly_sel.storage[bit//8] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[bit//8] & self._wdly_dq_bitslip.re,
                i      = Cat(*[self.dfi.phases[i//2].wrdata[i%2 * self.databits + bit] for i in range(2*nphases)]),
                o      = self.ck_dq_o[bit],
            )

            # input
            dq_i_bs = Signal(2*nphases)
            self.submodules += BitSlip(
                dw     = 2*nphases,
                cycles = bitslip_cycles,
                rst    = (self._dly_sel.storage[bit//8] & self._rdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[bit//8] & self._rdly_dq_bitslip.re,
                i      = self.ck_dq_i[bit],
                o      = dq_i_bs,
            )
            for i in range(2*nphases):
                self.comb += self.dfi.phases[i//2].rddata[i%2 * self.databits + bit].eq(dq_i_bs[i])

        # DQS --------------------------------------------------------------------------------------
        dqs_oe        = Signal()
        dqs_preamble  = Signal()
        dqs_postamble = Signal()
        dqs_pattern   = DQSPattern(
            preamble      = dqs_preamble,  # FIXME: are defined the opposite way (common.py) ???
            postamble     = dqs_postamble,
            wlevel_en     = self._wlevel_en.storage,
            wlevel_strobe = self._wlevel_strobe.re)
        self.submodules += dqs_pattern
        self.comb += [
            self.dqs_oe.eq(delayed(self, dqs_oe, cycles=1)),
        ]

        for bit in range(self.databits//8):
            # output
            self.submodules += BitSlip(
                dw     = 2*nphases,
                cycles = bitslip_cycles,
                rst    = (self._dly_sel.storage[bit] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[bit] & self._wdly_dq_bitslip.re,
                i      = dqs_pattern.o,
                o      = self.ck_dqs_o[bit],
            )

        # DMI --------------------------------------------------------------------------------------
        # DMI signal is used for Data Mask or Data Bus Invertion depending on Mode Registers values.
        # With DM and DBI disabled, this signal is a Don't Care.
        # With DM enabled, masking is performed only when the command used is WRITE-MASKED.
        # We don't support DBI, DM support is configured statically with `masked_write`.
        for bit in range(self.databits//8):
            if not masked_write:
                self.comb += self.ck_dmi_o[bit].eq(0)
                self.comb += self.dmi_oe.eq(0)
            else:
                self.comb += self.dmi_oe.eq(self.dq_oe)
                self.submodules += BitSlip(
                    dw     = 2*nphases,
                    cycles = bitslip_cycles,
                    rst    = (self._dly_sel.storage[bit] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                    slp    = self._dly_sel.storage[bit] & self._wdly_dq_bitslip.re,
                    i      = Cat(*[self.dfi.phases[i//2] .wrdata_mask[i%2 * self.databits//8 + bit] for i in range(2*nphases)]),
                    o      = self.ck_dmi_o[bit],
                )

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

        self.comb += [phase.rddata_valid.eq(rddata_en.output | self._wlevel_en.storage) for phase in dfi.phases]

        # Write Control Path -----------------------------------------------------------------------
        wrtap = cwl_sys_latency - 1
        assert wrtap >= 1

        # Create a delay line of write commands coming from the DFI interface. This taps are used to
        # control DQ/DQS tristates.
        wrdata_en = TappedDelayLine(
            signal = reduce(or_, [dfi.phases[i].wrdata_en for i in range(nphases)]),
            ntaps  = wrtap + 2
        )
        self.submodules += wrdata_en

        self.comb += dq_oe.eq(wrdata_en.taps[wrtap])
        self.comb += If(self._wlevel_en.storage, dqs_oe.eq(1)).Else(dqs_oe.eq(dqs_preamble | dq_oe | dqs_postamble))

        # Write DQS Postamble/Preamble Control Path ------------------------------------------------
        # Generates DQS Preamble 1 cycle before the first write and Postamble 1 cycle after the last
        # write. During writes, DQS tristate is configured as output for at least 3 sys_clk cycles:
        # 1 for Preamble, 1 for the Write and 1 for the Postamble.
        self.comb += dqs_preamble.eq( wrdata_en.taps[wrtap - 1]  & ~wrdata_en.taps[wrtap + 0])
        self.comb += dqs_postamble.eq(wrdata_en.taps[wrtap + 1]  & ~wrdata_en.taps[wrtap + 0])
