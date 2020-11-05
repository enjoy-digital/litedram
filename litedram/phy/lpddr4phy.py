import re
from functools import reduce
from operator import or_
from collections import defaultdict

import math

from migen import *

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def bitpattern(s):
    if len(s) > 8:
        return reduce(or_, [bitpattern(si) << (8*i) for i, si in enumerate(_chunks(s, 8))])
    assert len(s) == 8
    s = s.translate(s.maketrans("_-", "01"))
    return int(s[::-1], 2)  # LSB first, so reverse the string

def delayed(mod, sig, cycles=1):
    delay = TappedDelayLine(signal=sig, ntaps=cycles)
    mod.submodules += delay
    return delay.output

class ConstBitSlip(Module):
    def __init__(self, dw, i=None, o=None, slp=None, cycles=1):
        self.i   = Signal(dw, name='i') if i is None else i
        self.o   = Signal(dw, name='o') if o is None else o
        assert cycles >= 1
        assert 0 <= slp <= cycles*dw-1
        slp = (cycles*dw-1) - slp

        # # #

        self.r = r = Signal((cycles+1)*dw, reset_less=True)
        self.sync += r.eq(Cat(r[dw:], self.i))
        cases = {}
        for i in range(cycles*dw):
            cases[i] = self.o.eq(r[i+1:dw+i+1])
        self.comb += Case(slp, cases)

# TODO: rewrite DQSPattern in common.py to support different data widths
class DQSPattern(Module):
    def __init__(self, preamble=None, postamble=None, wlevel_en=0, wlevel_strobe=0, register=False):
        self.preamble  = Signal() if preamble  is None else preamble
        self.postamble = Signal() if postamble is None else postamble
        self.o = Signal(16)

        # # #

        # DQS Pattern transmitted as LSB-first.

        self.comb += [
            self.o.eq(0b0101010101010101),
            If(self.preamble,
                self.o.eq(0b0001010101010101)
            ),
            If(self.postamble,
                self.o.eq(0b0101010101010100)
            ),
            If(wlevel_en,
                self.o.eq(0b0000000000000000),
                If(wlevel_strobe,
                    self.o.eq(0b0000000000000001)
                )
            )
        ]
        if register:
            o = Signal.like(self.o)
            self.sync += o.eq(self.o)
            self.o = o

# LPDDR4PHY ----------------------------------------------------------------------------------------

class LPDDR4PHY(Module, AutoCSR):
    def __init__(self, pads, *,
                 sys_clk_freq, write_ser_latency, read_des_latency, phytype, cmd_delay=None):
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

        self._dly_sel         = CSRStorage(databits//8)

        self._wlevel_en     = CSRStorage()
        self._wlevel_strobe = CSR()

        self._dly_sel = CSRStorage(databits//8)

        self._rdly_dq_bitslip_rst = CSR()
        self._rdly_dq_bitslip     = CSR()

        self._wdly_dq_bitslip_rst = CSR()
        self._wdly_dq_bitslip     = CSR()

        self._rdphase = CSRStorage(int(math.log2(nphases)), reset=rdphase)
        self._wrphase = CSRStorage(int(math.log2(nphases)), reset=wrphase)

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

        adapters = [DFIPhaseAdapter(phase) for phase in self.dfi.phases]
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
                rst    = (self._dly_sel.storage[bit//8] & self._wdly_dq_bitslip_rst.re) | self._rst.storage,
                slp    = self._dly_sel.storage[bit//8] & self._wdly_dq_bitslip.re,
                i      = dqs_pattern.o,
                o      = self.ck_dqs_o[bit],
            )

        # DMI --------------------------------------------------------------------------------------
        # DMI signal is used for Data Mask or Data Bus Invertion depending on Mode Registers values.
        # With DM and DBI disabled, this signal is a Don't Care.
        # With DM enabled, masking is performed only when the command used is WRITE-MASKED.
        # TODO: use WRITE-MASKED for all write commands, and configure Mode Registers for that
        #       during DRAM initialization (we don't want to support DBI).
        for bin in range(self.databits//8):
            self.comb += self.ck_dmi_o[bit].eq(0)

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

class DFIPhaseAdapter(Module):
    # We must perform mapping of DFI commands to the LPDDR4 commands set on CA bus.
    # LPDDR4 "small command" consists of 2 words CA[5:0] sent on the bus in 2 subsequent
    # cycles. First cycle is marked with CS high, second with CS low.
    # Then most "big commands" consist of 2 "small commands" (e.g. ACTIVATE-1, ACTIVATE-2).
    # If a command uses 1 "small command", then it shall go as cmd2 so that all command
    # timings can be counted from the same moment (cycle of cmd2 CS low).
    def __init__(self, dfi_phase):
        # CS/CA values for 4 SDR cycles
        self.cs = Signal(4)
        self.ca = Array([Signal(6) for _ in range(4)])
        self.valid = Signal()

        # # #

        self.submodules.cmd1 = Command(dfi_phase)
        self.submodules.cmd2 = Command(dfi_phase)
        self.comb += [
            self.cs[:2].eq(self.cmd1.cs),
            self.cs[2:].eq(self.cmd2.cs),
            self.ca[0].eq(self.cmd1.ca[0]),
            self.ca[1].eq(self.cmd1.ca[1]),
            self.ca[2].eq(self.cmd2.ca[0]),
            self.ca[3].eq(self.cmd2.ca[1]),
        ]

        dfi_cmd = Signal(3)
        self.comb += dfi_cmd.eq(Cat(~dfi_phase.we_n, ~dfi_phase.ras_n, ~dfi_phase.cas_n)),
        _cmd = {  # cas, ras, we
            "NOP": 0b000,
            "ACT": 0b010,
            "RD":  0b100,
            "WR":  0b101,
            "PRE": 0b011,
            "REF": 0b110,
            "ZQC": 0b001,
            "MRS": 0b111,
        }

        def cmds(cmd1, cmd2, valid=1):
            return self.cmd1.set(cmd1) + self.cmd2.set(cmd2) + [self.valid.eq(valid)]

        self.comb += If(dfi_phase.cs_n == 0,  # require dfi.cs_n
            Case(dfi_cmd, {
                _cmd["ACT"]: cmds("ACTIVATE-1", "ACTIVATE-2"),
                _cmd["RD"]:  cmds("READ-1",     "CAS-2"),
                _cmd["WR"]:  cmds("WRITE-1",    "CAS-2"),  # TODO: masked write
                _cmd["PRE"]: cmds("DESELECT",   "PRECHARGE"),
                _cmd["REF"]: cmds("DESELECT",   "REFRESH"),
                # TODO: ZQC init/short/long? start/latch?
                # _cmd["ZQC"]: [
                #     *cmds("DESELECT", "MPC"),
                #     self.cmd2.mpc.eq(0b1001111),
                # ],
                _cmd["MRS"]: cmds("MRW-1",      "MRW-2"),
                "default":   cmds("DESELECT",   "DESELECT", valid=0),
            })
        )

class Command(Module):
    # String description of 1st and 2nd edge of each command, later parsed to construct
    # the value. CS is assumed to be H for 1st edge and L for 2nd edge.
    TRUTH_TABLE = {
        "MRW-1":        ["L H H L L OP7",       "MA0 MA1 MA2 MA3 MA4 MA5"],
        "MRW-2":        ["L H H L H OP6",       "OP0 OP1 OP2 OP3 OP4 OP5"],
        "MRR-1":        ["L H H H L V",         "MA0 MA1 MA2 MA3 MA4 MA5"],
        "REFRESH":      ["L L L H L AB",        "BA0 BA1 BA2 V V V"],
        "ACTIVATE-1":   ["H L R12 R13 R14 R15", "BA0 BA1 BA2 R16 R10 R11"],
        "ACTIVATE-2":   ["H H R6 R7 R8 R9",     "R0 R1 R2 R3 R4 R5"],
        "WRITE-1":      ["L L H L L BL",        "BA0 BA1 BA2 V C9 AP"],
        "MASK WRITE-1": ["L L H H L BL",        "BA0 BA1 BA2 V C9 AP"],
        "READ-1":       ["L H L L L BL",        "BA0 BA1 BA2 V C9 AP"],
        "CAS-2":        ["L H L L H C8",        "C2 C3 C4 C5 C6 C7"],
        "PRECHARGE":    ["L L L L H AB",        "BA0 BA1 BA2 V V V"],
        "MPC":          ["L L L L L OP6",       "OP0 OP1 OP2 OP3 OP4 OP5"],
        "DESELECT":     ["X X X X X X",         "X X X X X X"],
    }

    for cmd, (subcmd1, subcmd2) in TRUTH_TABLE.items():
        assert len(subcmd1.split()) == 6, (cmd, subcmd1)
        assert len(subcmd2.split()) == 6, (cmd, subcmd2)

    def __init__(self, dfi_phase):
        self.cs = Signal(2)
        self.ca = Array([Signal(6), Signal(6)])  # CS high, CS low
        self.mpc = Signal(7)  # special OP values for multipurpose command
        self.dfi = dfi_phase

    def set(self, cmd):
        ops = []
        for i, description in enumerate(self.TRUTH_TABLE[cmd]):
            for j, bit in enumerate(description.split()):
                ops.append(self.ca[i][j].eq(self.parse_bit(bit, is_mpc=cmd == "MPC")))
        if cmd != "DESELECT":
            ops.append(self.cs[0].eq(1))
        return ops

    def parse_bit(self, bit, is_mpc=False):
        rules = {
            "H":       lambda: 1,  # high
            "L":       lambda: 0,  # low
            "V":       lambda: 0,  # defined logic
            "X":       lambda: 0,  # don't care
            "BL":      lambda: 0,  # on-the-fly burst length, not using
            "AP":      lambda: self.dfi.address[10],  # auto precharge
            "AB":      lambda: self.dfi.address[10],  # all banks
            "BA(\d+)": lambda i: self.dfi.bank[i],
            "R(\d+)":  lambda i: self.dfi.address[i],  # row
            "C(\d+)":  lambda i: self.dfi.address[i],  # column
            "MA(\d+)": lambda i: self.dfi.address[8+i],  # mode register address
            # mode register value, or op code for MPC
            "OP(\d+)": lambda i: self.mpc[i] if is_mpc else self.dfi.address[i],
        }
        for pattern, value in rules.items():
            m = re.match(pattern, bit)
            if m:
                args = [int(g) for g in m.groups()]
                return value(*args)
        raise ValueError(bit)

# SimulationPHY ------------------------------------------------------------------------------------

class LPDDR4SimulationPads(Module):
    def __init__(self, databits=16):
        self.clk_p   = Signal()
        self.clk_n   = Signal()
        self.cke     = Signal()
        self.odt     = Signal()
        self.reset_n = Signal()
        self.cs      = Signal()
        self.ca      = Signal(6)
        # signals for checking actual tristate lines state (PHY reads these)
        self.dq      = Signal(databits)
        self.dqs     = Signal(databits//8)
        self.dmi     = Signal(databits//8)
        # internal tristates i/o that should be driven for simulation
        self.dq_o    = Signal(databits)  # PHY drives these
        self.dq_i    = Signal(databits)  # DRAM chip (simulator) drives these
        self.dq_oe   = Signal()          # PHY drives these
        self.dqs_o   = Signal(databits//8)
        self.dqs_i   = Signal(databits//8)
        self.dqs_oe  = Signal()
        self.dmi_o   = Signal(databits//8)
        self.dmi_i   = Signal(databits//8)
        self.dmi_oe  = Signal()

        self.comb += [
            If(self.dq_oe, self.dq.eq(self.dq_o)).Else(self.dq.eq(self.dq_i)),
            If(self.dqs_oe, self.dqs.eq(self.dqs_o)).Else(self.dqs.eq(self.dqs_i)),
            If(self.dmi_oe, self.dmi.eq(self.dmi_o)).Else(self.dmi.eq(self.dmi_i)),
        ]


class SimulationPHY(LPDDR4PHY):
    def __init__(self, sys_clk_freq=100e6, aligned_reset_zero=False):
        pads = LPDDR4SimulationPads()
        self.submodules += pads
        super().__init__(pads,
                         sys_clk_freq       = sys_clk_freq,
                         write_ser_latency  = Serializer.LATENCY,
                         read_des_latency   = Deserializer.LATENCY,
                         phytype            = "SimulationPHY")

        def add_reset_value(phase, kwargs):
            if aligned_reset_zero and phase == 0:
                kwargs["reset_value"] = 0

        # Serialization
        def serialize(**kwargs):
            name = 'ser_' + kwargs.pop('name', '')
            ser = Serializer(o_dw=1, name=name.strip('_'), **kwargs)
            self.submodules += ser

        def deserialize(**kwargs):
            name = 'des_' + kwargs.pop('name', '')
            des = Deserializer(i_dw=1, name=name.strip('_'), **kwargs)
            self.submodules += des

        def ser_sdr(phase=0, **kwargs):
            clkdiv = {0: "sys8x", 90: "sys8x_90"}[phase]
            # clk = {0: "sys", 90: "sys_11_25"}[phase]
            clk = {0: "sys", 90: "sys"}[phase]
            add_reset_value(phase, kwargs)
            serialize(clk=clk, clkdiv=clkdiv, i_dw=8, **kwargs)

        def ser_ddr(phase=0, **kwargs):
            # for simulation we require sys8x_ddr clock (=sys16x)
            clkdiv = {0: "sys8x_ddr", 90: "sys8x_90_ddr"}[phase]
            # clk = {0: "sys", 90: "sys_11_25"}[phase]
            clk = {0: "sys", 90: "sys"}[phase]
            add_reset_value(phase, kwargs)
            serialize(clk=clk, clkdiv=clkdiv, i_dw=16, **kwargs)

        def des_ddr(phase=0, **kwargs):
            clkdiv = {0: "sys8x_ddr", 90: "sys8x_90_ddr"}[phase]
            clk = {0: "sys", 90: "sys_11_25"}[phase]
            add_reset_value(phase, kwargs)
            deserialize(clk=clk, clkdiv=clkdiv, o_dw=16, **kwargs)

        # Clock is shifted 180 degrees to get rising edge in the middle of SDR signals.
        # To achieve that we send negated clock on clk_p and non-negated on clk_n.
        ser_ddr(i=~self.ck_clk,    o=self.pads.clk_p,   name='clk_p')
        ser_ddr(i=self.ck_clk,     o=self.pads.clk_n,   name='clk_n')

        ser_sdr(i=self.ck_cke,     o=self.pads.cke,     name='cke')
        ser_sdr(i=self.ck_odt,     o=self.pads.odt,     name='odt')
        ser_sdr(i=self.ck_reset_n, o=self.pads.reset_n, name='reset_n')

        # Command/address
        ser_sdr(i=self.ck_cs,      o=self.pads.cs,      name='cs')
        for i in range(6):
            ser_sdr(i=self.ck_ca[i], o=self.pads.ca[i], name=f'ca{i}')

        # Tristate I/O (separate for simulation)
        for i in range(self.databits//8):
            ser_ddr(i=self.ck_dmi_o[i], o=self.pads.dmi_o[i], name=f'dmi_o{i}')
            des_ddr(o=self.ck_dmi_i[i], i=self.pads.dmi[i],   name=f'dmi_i{i}')
            ser_ddr(i=self.ck_dqs_o[i], o=self.pads.dqs_o[i], name=f'dqs_o{i}', phase=90)
            des_ddr(o=self.ck_dqs_i[i], i=self.pads.dqs[i],   name=f'dqs_i{i}', phase=90)
        for i in range(self.databits):
            ser_ddr(i=self.ck_dq_o[i], o=self.pads.dq_o[i], name=f'dq_o{i}')
            des_ddr(o=self.ck_dq_i[i], i=self.pads.dq[i],   name=f'dq_i{i}')
        # Output enable signals
        self.comb += self.pads.dmi_oe.eq(delayed(self, self.dmi_oe, cycles=Serializer.LATENCY))
        self.comb += self.pads.dqs_oe.eq(delayed(self, self.dqs_oe, cycles=Serializer.LATENCY))
        self.comb += self.pads.dq_oe.eq(delayed(self, self.dq_oe, cycles=Serializer.LATENCY))

class Serializer(Module):
    """Serialize given input signal

    It latches the input data on the rising edge of `clk`. Output data counter `cnt` is incremented
    on rising edges of `clkdiv` and it determines current slice of `i` that is presented on `o`.
    `latency` is specified in `clk` cycles.

    NOTE: both `clk` and `clkdiv` should be phase aligned.
    NOTE: `reset_value` is set to `ratio - 1` so that on the first clock edge after reset it is 0
    """
    LATENCY = 1

    def __init__(self, clk, clkdiv, i_dw, o_dw, i=None, o=None, reset=None, reset_value=-1, name=None):
        assert i_dw > o_dw
        assert i_dw % o_dw == 0
        ratio = i_dw // o_dw

        sd_clk = getattr(self.sync, clk)
        sd_clkdiv = getattr(self.sync, clkdiv)

        if i is None: i = Signal(i_dw)
        if o is None: o = Signal(o_dw)
        if reset is None: reset = Signal()

        self.i = i
        self.o = o
        self.reset = reset

        if reset_value < 0:
            reset_value = ratio + reset_value

        cnt = Signal(max=ratio, reset=reset_value, name='{}_cnt'.format(name) if name is not None else None)
        sd_clkdiv += If(reset | cnt == ratio - 1, cnt.eq(0)).Else(cnt.eq(cnt + 1))

        i_d = Signal.like(self.i)
        sd_clk += i_d.eq(self.i)
        i_array = Array([i_d[n*o_dw:(n+1)*o_dw] for n in range(ratio)])
        self.comb += self.o.eq(i_array[cnt])

class Deserializer(Module):
    """Deserialize given input signal

    Latches the input data on the rising edges of `clkdiv` and stores them in the `o_pre` buffer.
    Additional latency cycle is used to ensure that the last input bit is deserialized correctly.

    NOTE: both `clk` and `clkdiv` should be phase aligned.
    NOTE: `reset_value` is set to `ratio - 1` so that on the first clock edge after reset it is 0
    """
    LATENCY = 2

    def __init__(self, clk, clkdiv, i_dw, o_dw, i=None, o=None, reset=None, reset_value=-1, name=None):
        assert i_dw < o_dw
        assert o_dw % i_dw == 0
        ratio = o_dw // i_dw

        sd_clk = getattr(self.sync, clk)
        sd_clkdiv = getattr(self.sync, clkdiv)

        if i is None: i = Signal(i_dw)
        if o is None: o = Signal(o_dw)
        if reset is None: reset = Signal()

        self.i = i
        self.o = o
        self.reset = reset

        if reset_value < 0:
            reset_value = ratio + reset_value

        cnt = Signal(max=ratio, reset=reset_value, name='{}_cnt'.format(name) if name is not None else None)
        sd_clkdiv += If(reset, cnt.eq(0)).Else(cnt.eq(cnt + 1))

        o_pre = Signal.like(self.o)
        o_array = Array([o_pre[n*i_dw:(n+1)*i_dw] for n in range(ratio)])
        sd_clkdiv += o_array[cnt].eq(self.i)
        # we need to ensure that the last bit will be correct if clocks are phase aligned
        o_pre_d = Signal.like(self.o)
        sd_clk += o_pre_d.eq(o_pre)
        sd_clk += self.o.eq(Cat(o_pre_d[:-1], o_pre[-1]))  # would work as self.comb (at least in simulation)
