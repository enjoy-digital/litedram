#
# This file is part of LiteDRAM.
#
# Copyright (c) 2022 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from operator import or_, and_, xor
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
    """
        Unserialized output of DDR5PHY.
        Has to be serialized by concrete implementation.
    """
    def __init__(self, nphases, databits, nranks, nstrobes, with_sub_channels=False, name=None):
        self.ck_t   = Signal(2*nphases)
        self.ck_c   = Signal(2*nphases)
        self.reset_n = Signal(2*nphases)  # Serializer will work in ddr mode
        self.alert_n = Signal(2*nphases)  # Deserializer will work in ddr mode

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]

        for prefix in prefixes:
            setattr(self, prefix+'cs_n', [Signal(2*nphases, reset=2*nphases-1, name=name and f"{name}_{i}_cs_n") for i in range(nranks)])
            setattr(self, prefix+'ca',   [Signal(2*nphases, name=name and f"{name}_{i}_ca") for i in range(14)]) # 2*nphases, as phy will run in ddr mode
            setattr(self, prefix+'par',  Signal(2*nphases, name=name and name+"par_n"))

            setattr(self, prefix+'dq_o',  [Signal(2*nphases, name=name and f"{name}_{i}_dq_o") for i in range(databits)])
            setattr(self, prefix+'dq_oe', [Signal(2*nphases, name=name and f"{name}_{i}_dq_oe") for i in range(nstrobes)])
            setattr(self, prefix+'dq_i',  [Signal(2*nphases, name=name and f"{name}_{i}_dq_i") for i in range(databits)])

            setattr(self, prefix+'dm_n_o',  [Signal(2*nphases, name=name and f"{name}_{i}_dm_n_o") for i in range(nstrobes)])
            setattr(self, prefix+'dm_n_i',  [Signal(2*nphases, name=name and f"{name}_{i}_dm_i_o") for i in range(nstrobes)])

            setattr(self, prefix+'dqs_t_o',  [Signal(2*nphases, name=name and f"{name}_{i}_dqs_t_o") for i in range(nstrobes)])
            setattr(self, prefix+'dqs_t_i',  [Signal(2*nphases, name=name and f"{name}_{i}_dqs_t_i") for i in range(nstrobes)])
            setattr(self, prefix+'dqs_oe',   [Signal(2*nphases, name=name and f"{name}_{i}_dqs_oe") for i in range(nstrobes)])
            setattr(self, prefix+'dqs_c_o',  [Signal(2*nphases, name=name and f"{name}_{i}_dqs_c_o") for i in range(nstrobes)])
            setattr(self, prefix+'dqs_c_i',  [Signal(2*nphases, name=name and f"{name}_{i}_dqs_c_i") for i in range(nstrobes)])


class DDR5DQOePattern(Module):
    def __init__(self, old_tap: Signal(4), now_tap: Signal(4)):
        self.oe = Signal(8)

        self.comb += [
            self.oe.eq(0),
            Case(old_tap, {
                0b0010 : [
                    Case(now_tap, {
                        0b0000 :
                            self.oe.eq(0b00000011),
                        0b0010 :
                            self.oe.eq(0b11111111),
                        0b0100 :
                            self.oe.eq(0b11110011),
                        0b1000 :
                            self.oe.eq(0b11000011),
                    })
                ],
                0b0100   : [
                    Case(now_tap, {
                        0b0000 :
                            self.oe.eq(0b00001111),
                        0b0100 :
                            self.oe.eq(0b11111111),
                        0b1000 :
                            self.oe.eq(0b11001111),
                    })
                ],
                0b1000   : [
                    Case(now_tap, {
                        0b0000 :
                            self.oe.eq(0b00111111),
                        0b1000 :
                            self.oe.eq(0b11111111),
                    })
                ],
                "default": [
                    Case(now_tap, {
                        0b0001 :
                            self.oe.eq(0b11111111),
                        0b0010 :
                            self.oe.eq(0b11111100),
                        0b0100 :
                            self.oe.eq(0b11110000),
                        0b1000 :
                            self.oe.eq(0b11000000),
                    })
                ],
            })
        ]


class DDR5DQSPattern(Module):
    def __init__(self, old_tap: Signal(4), now_tap: Signal(4), next_tap:Signal(4),
                 wlevel_en: Signal(), wlevel_strobe: Signal()):
        self.o  = Signal(8)
        self.oe = Signal(8)

        # # #

        # DQS Pattern transmitted as LSB-first.
        # Always enabled in write leveling mode, else during transfers
        # Assumptions: read/writes start in phase 0, preamble is 2 cycles and post amble is 0.5 cycle

        self.comb += [
            self.o.eq(0),
            self.oe.eq(0),
            If(wlevel_en,
                self.o.eq(0b00000000),
                self.oe.eq(0b11111111),
                If(wlevel_strobe,
                    # use 2 toggles as, according to datasheet, the first one may not be registered
                    self.o.eq(0b00000101)
                )
            ).Else(
                Case(old_tap, {
                    0b0001   : [
                        Case(now_tap, {
                            0b0000 : [
                                Case(next_tap, {
                                    0b0001   : [
                                        self.o.eq( 0b01000000),
                                        self.oe.eq(0b11110000),
                                    ],
                                    0b0010   : [
                                        self.o.eq( 0b00000000),
                                        self.oe.eq(0b11000000),
                                    ],
                                })
                            ],
                            0b0001 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                            0b0010 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                            0b0100 : [
                                self.o.eq( 0b01010100),
                                self.oe.eq(0b11111111)
                            ],
                            0b1000 : [
                                self.o.eq( 0b01010000),
                                self.oe.eq(0b11111100)
                            ],
                        })
                    ],
                    0b0010   : [
                        Case(now_tap, {
                            0b0000 : [
                                Case(next_tap, {
                                    0b0001   : [
                                        self.o.eq( 0b01000001),
                                        self.oe.eq(0b11110011),
                                    ],
                                    0b0010   : [
                                        self.o.eq( 0b00000001),
                                        self.oe.eq(0b11000011),
                                    ],
                                    "default": [
                                        self.o.eq( 0b00000001),
                                        self.oe.eq(0b00000011),
                                    ],
                                })
                            ],
                            0b0010 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                            0b0100 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                            0b1000 : [
                                self.o.eq( 0b01010001),
                                self.oe.eq(0b11111111)
                            ],
                        })
                    ],
                    0b0100   : [
                        Case(now_tap, {
                            0b0000 : [
                                Case(next_tap, {
                                    0b0001   : [
                                        self.o.eq( 0b01000101),
                                        self.oe.eq(0b11111111),
                                    ],
                                    0b0010   : [
                                        self.o.eq( 0b00000101),
                                        self.oe.eq(0b11001111),
                                    ],
                                    "default": [
                                        self.o.eq( 0b00000101),
                                        self.oe.eq(0b00001111),
                                    ],
                                })
                            ],
                            0b0100 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                            0b1000 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                        })
                    ],
                    0b1000   : [
                        Case(now_tap, {
                            0b0000 : [
                                Case(next_tap, {
                                    0b0001   : [
                                        self.o.eq( 0b01010101),
                                        self.oe.eq(0b11111111),
                                    ],
                                    0b0010   : [
                                        self.o.eq( 0b00010101),
                                        self.oe.eq(0b11111111),
                                    ],
                                    "default": [
                                        self.o.eq( 0b00010101),
                                        self.oe.eq(0b00111111),
                                    ],
                                })
                            ],
                            0b1000 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                        })
                    ],
                    "default": [
                        Case(now_tap, {
                            0b0000 : [
                                If(next_tap == 0b0001,
                                    self.o.eq( 0b01000000),
                                    self.oe.eq(0b11110000),
                                ).Elif(next_tap == 0b0010,
                                    self.o.eq( 0b00000000),
                                    self.oe.eq(0b11000000),
                                )
                            ],
                            0b0001 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                            0b0010 : [
                                self.o.eq( 0b01010101),
                                self.oe.eq(0b11111111)
                            ],
                            0b0100 : [
                                self.o.eq( 0b01010100),
                                self.oe.eq(0b11111111)
                            ],
                            0b1000 : [
                                self.o.eq( 0b01010000),
                                self.oe.eq(0b11111100)
                            ],
                        })
                    ],
                })
            )
        ]


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
    """
    def __init__(self, pads, *,
                 sys_clk_freq, ser_latency, des_latency, phytype, with_sub_channels=False,
                 cmd_delay=None, masked_write=False, extended_overlaps_check=False,
                 with_odelay=False, csr_cdc=None, rd_extra_delay=Latency(sys=0), address_lines=13):

        self.pads        = pads
        self.memtype     = memtype     = "DDR5"
        self.nranks      = nranks      = len(pads.cs_n) if hasattr(pads, "cs_n") else len(pads.A_cs_n) if hasattr(pads, "A_cs_n") else 1
        self.databits    = databits    = len(pads.dq) if hasattr(pads, "dq") else len(pads.A_dq)
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
        # BitSlip adds delay
        rdphase = get_sys_phase(nphases, cl_sys_latency, cl + cmd_latency +
                                ser_latency.sys4x + des_latency.sys4x + 2 * 4 + rd_extra_delay.sys4x)
        # BitSlip applies at least 1 cycle of delay to DQS and DQ lines, make MC think it need to send data earlier
        wrphase = get_sys_phase(nphases, cwl_sys_latency, cwl + cmd_latency - 4)

        # When the calculated phase is negative, it means that we need to increase sys latency
        def updated_latency(phase, sys_latency):
            while phase < 0:
                phase += nphases
                sys_latency += 1
            return phase, sys_latency

        wrphase, cwl_sys_latency = updated_latency(wrphase, cwl_sys_latency)
        rdphase, cl_sys_latency = updated_latency(rdphase, cl_sys_latency)

        # Read latency
        read_latency  = cl_sys_latency

        # Write latency
        write_latency = cwl_sys_latency

        # Registers --------------------------------------------------------------------------------

        def cdc(i):
            if csr_cdc is None:
                return i
            return csr_cdc(i)

        self._rst           = CSRStorage()
        self._rst_cdc       = cdc(self._rst.storage)
        self._rdimm_mode    = CSRStorage()

        self._rdphase = CSRStorage(log2_int(nphases), reset=rdphase)
        self._wrphase = CSRStorage(log2_int(nphases), reset=wrphase)

        prefixes = [""] if not with_sub_channels else ["A_", "B_"]

        self._l = _l = dict()

        dq_dqs_ratio = databits // strobes

        if with_odelay:
            setattr(self, 'ckdly_rst' , CSR(name='ckdly_rst'))
            setattr(self, 'ckdly_inc' , CSR(name='ckdly_inc'))
            _l['ckdly_rst'] = cdc(getattr(self, 'ckdly_rst').re | self._rst.storage)
            _l['ckdly_inc'] = cdc(getattr(self, 'ckdly_inc').re)

        for prefix in prefixes:
            setattr(self, prefix+'wlevel_en', CSRStorage(name=prefix+'wlevel_en'))
            setattr(self, prefix+'wlevel_strobe', CSR(name=prefix+'wlevel_strobe'))

            setattr(self, prefix+'dly_sel', CSRStorage(max(strobes, databits, 14, nranks), name=prefix+'dly_sel'))
            getattr(self, prefix+'dly_sel').storage.attr.add("mr_ff")
            getattr(self, prefix+'dly_sel').storage.attr.add("keep")

            if with_odelay:
                setattr(self, prefix+'csdly_rst' , CSR(name=prefix+'csdly_rst'))
                setattr(self, prefix+'csdly_inc' , CSR(name=prefix+'csdly_inc'))
                setattr(self, prefix+'cadly_rst' , CSR(name=prefix+'cadly_rst'))
                setattr(self, prefix+'cadly_inc' , CSR(name=prefix+'cadly_inc'))
                setattr(self, prefix+'pardly_rst' , CSR(name=prefix+'pardly_rst'))
                setattr(self, prefix+'pardly_inc' , CSR(name=prefix+'pardly_inc'))

            setattr(self, prefix+'rdly_dq_rst', CSR(name=prefix+'rdly_dq_rst'))
            setattr(self, prefix+'rdly_dq_inc', CSR(name=prefix+'rdly_dq_inc'))
            setattr(self, prefix+'rdly_dqs_rst', CSR(name=prefix+'rdly_dqs_rst'))
            setattr(self, prefix+'rdly_dqs_inc', CSR(name=prefix+'rdly_dqs_inc'))
            setattr(self, prefix+'rdly_dq_bitslip_rst', CSR(name=prefix+'rdly_dq_bitslip_rst'))
            setattr(self, prefix+'rdly_dq_bitslip'    , CSR(name=prefix+'rdly_dq_bitslip'))

            if with_odelay:
                setattr(self, prefix+'wdly_dq_rst', CSR(name=prefix+'wdly_dq_rst'))
                setattr(self, prefix+'wdly_dq_inc', CSR(name=prefix+'wdly_dq_inc'))
                setattr(self, prefix+'wdly_dqs_rst', CSR(name=prefix+'wdly_dqs_rst'))
                setattr(self, prefix+'wdly_dqs_inc', CSR(name=prefix+'wdly_dqs_inc'))


            setattr(self, prefix+'wdly_dq_bitslip_rst', CSR(name=prefix+'wdly_dq_bitslip_rst'))
            setattr(self, prefix+'wdly_dq_bitslip'    , CSR(name=prefix+'wdly_dq_bitslip'))
            setattr(self, prefix+'wdly_dqs_bitslip_rst', CSR(name=prefix+'wdly_dqs_bitslip_rst'))
            setattr(self, prefix+'wdly_dqs_bitslip'    , CSR(name=prefix+'wdly_dqs_bitslip'))

            _l[prefix+'rdly_dq_rst']  = cdc(getattr(self, prefix+'rdly_dq_rst').re)
            _l[prefix+'rdly_dq_inc']  = cdc(getattr(self, prefix+'rdly_dq_inc').re)
            _l[prefix+'rdly_dqs_rst']  = cdc(getattr(self, prefix+'rdly_dqs_rst').re)
            _l[prefix+'rdly_dqs_inc']  = cdc(getattr(self, prefix+'rdly_dqs_inc').re)
            _l[prefix+'rdly_dq_bitslip_rst']  = cdc(getattr(self, prefix+'rdly_dq_bitslip_rst').re)
            _l[prefix+'rdly_dq_bitslip']  = cdc(getattr(self, prefix+'rdly_dq_bitslip').re)
            _l[prefix+'wlevel_strobe'] = cdc(getattr(self, prefix+'wlevel_strobe').re)
            if with_odelay:
                _l[prefix+'csdly_rst']    = cdc(getattr(self, prefix+'csdly_rst').re | self._rst.storage)
                _l[prefix+'csdly_inc']    = cdc(getattr(self, prefix+'csdly_inc').re)
                _l[prefix+'cadly_rst']    = cdc(getattr(self, prefix+'cadly_rst').re | self._rst.storage)
                _l[prefix+'cadly_inc']    = cdc(getattr(self, prefix+'cadly_inc').re)
                _l[prefix+'pardly_rst']   = cdc(getattr(self, prefix+'pardly_rst').re | self._rst.storage)
                _l[prefix+'pardly_inc']   = cdc(getattr(self, prefix+'pardly_inc').re)
                _l[prefix+'wdly_dq_rst']  = cdc(getattr(self, prefix+'wdly_dq_rst').re | self._rst.storage)
                _l[prefix+'wdly_dq_inc']  = cdc(getattr(self, prefix+'wdly_dq_inc').re)
                _l[prefix+'wdly_dqs_rst'] = cdc(getattr(self, prefix+'wdly_dqs_rst').re | self._rst.storage)
                _l[prefix+'wdly_dqs_inc'] = cdc(getattr(self, prefix+'wdly_dqs_inc').re)

            _l[prefix+'wdly_dq_bitslip_rst']  = cdc(getattr(self, prefix+'wdly_dq_bitslip_rst').re | self._rst.storage)
            _l[prefix+'wdly_dq_bitslip']  = cdc(getattr(self, prefix+'wdly_dq_bitslip').re)
            _l[prefix+'wdly_dqs_bitslip_rst']  = cdc(getattr(self, prefix+'wdly_dqs_bitslip_rst').re | self._rst.storage)
            _l[prefix+'wdly_dqs_bitslip']  = cdc(getattr(self, prefix+'wdly_dqs_bitslip').re)

        combined_data_bits = databits if not with_sub_channels else 2*databits
        combined_strobes = strobes if not with_sub_channels else 2*strobes

        # PHY settings -----------------------------------------------------------------------------
        self.settings = PhySettings(
            phytype       = phytype,
            memtype       = memtype,
            databits      = combined_data_bits,
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
            bitslips      = 8,
            strobes       = combined_strobes,
            address_lines       = address_lines,
            with_sub_channels   = with_sub_channels,
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(14, 1, nranks, 2*combined_data_bits, nphases=4, with_sub_channels=with_sub_channels)

        # Now prepare the data by converting the sequences on adapters into sequences on the pads.
        # We have to ignore overlapping commands, and module timings have to ensure that there are
        # no overlapping commands anyway.
        self.out = DDR5Output(nphases, databits, nranks, strobes, with_sub_channels, name="basephy")

        # Clocks -----------------------------------------------------------------------------------
        self.comb += self.out.ck_t.eq(bitpattern("-_-_-_-_"))
        self.comb += self.out.ck_c.eq(bitpattern("_-_-_-_-"))

        # Simple commands --------------------------------------------------------------------------
        self.comb += self.out.reset_n.eq(Cat((phase.reset_n, phase.reset_n) for phase in dfi.phases))
        self.comb += [phase.alert_n.eq(self.out.alert_n[i*2] | self.out.alert_n[i*2+1]) for i, phase in enumerate(self.dfi.phases)]

        for prefix in prefixes:
            # DDR5 Commands --------------------------------------------------------------------------

            for rank in range(nranks):
                carry_cs_n = Signal(reset=1)
                self.sync += [
                    If(dfi.phases[-1].mode_2n,
                        carry_cs_n.eq(getattr(dfi.phases[-1], prefix).cs_n[rank])
                    ).Else(
                        carry_cs_n.eq(1)
                    )
                ]

                for j, phase in enumerate(dfi.phases):
                    self.comb += [
                        If(~phase.mode_2n,
                            getattr(self.out, prefix + 'cs_n')[rank][2*j].eq(
                                getattr(phase, prefix).cs_n[rank] & (carry_cs_n if j == 0 else 1)
                            ),
                            getattr(self.out, prefix + 'cs_n')[rank][2*j+1].eq(
                                getattr(phase, prefix).cs_n[rank]
                            ),
                        ).Else(
                            getattr(self.out, prefix + 'cs_n')[rank][2*j].eq(
                                carry_cs_n if j == 0 else getattr(dfi.phases[j-1], prefix).cs_n[rank]
                            ),
                            getattr(self.out, prefix + 'cs_n')[rank][2*j+1].eq(
                                getattr(phase, prefix).cs_n[rank]
                            ),
                        ),
                    ]

            self.comb += getattr(self.out, prefix + 'par').eq(
                Cat([reduce(xor, getattr(phase, prefix).address[7*i:7+7*i])] for phase in dfi.phases for i in range(2)))

            stage_cnt = Signal()
            self.sync += [
                If(~reduce(and_, getattr(phase, prefix).cs_n),
                    stage_cnt.eq(0),
                ).Else(
                    stage_cnt.eq(~stage_cnt),
                )
            ]

            for bit in range(7):
                for j, phase in enumerate(dfi.phases):
                    self.comb += [
                        If(self._rdimm_mode.storage,
                            If(phase.mode_2n,
                                If(~reduce(and_, getattr(phase, prefix).cs_n) | stage_cnt == 0,
                                    getattr(self.out, prefix+'ca')[bit].eq(Replicate(getattr(phase, prefix).address[bit], 2))
                                ).Else(
                                    getattr(self.out, prefix+'ca')[bit].eq(Replicate(getattr(phase, prefix).address[bit + 7], 2))
                                )
                            ).Else(
                                getattr(self.out, prefix+'ca')[bit].eq(
                                    Cat([getattr(phase, prefix).address[bit + 7*i] for phase in dfi.phases for i in range (2)]))
                            ),
                        ).Else(
                            getattr(self.out, prefix+'ca')[bit].eq(
                                Cat([getattr(phase, prefix).address[bit] for phase in dfi.phases for _ in range (2)]))
                        ),
                    ]
            for bit in range(7, 14):
                self.comb += getattr(self.out, prefix+'ca')[bit].eq(
                    Cat([getattr(phase, prefix).address[bit] for phase in dfi.phases for _ in range (2)]))

            # DQS --------------------------------------------------------------------------------------

            # Write Control Path -----------------------------------------------------------------------
            wrtap = cwl_sys_latency - 1
            assert wrtap >= 0

            # Create a delay line of write commands coming from the DFI interface. This taps are used to
            # control DQ/DQS tristates.
            wrdata_en = TappedDelayLine(
                signal = Cat([getattr(dfi.phases[i], prefix).wrdata_en for i in range(nphases-1, -1, -1)]),
                ntaps  = wrtap + 2
            )
            self.submodules += wrdata_en

            # Assumptions: nphases = 4

            old_tap  = Signal(4)
            now_tap  = Signal(4)
            next_tap = Signal(4)

            # wrtap is at least 5
            self.comb += [
                old_tap.eq( Cat(wrdata_en.taps[wrtap + 1][1:], wrdata_en.taps[wrtap    ][0])),
                now_tap.eq( Cat(wrdata_en.taps[wrtap    ][1:], wrdata_en.taps[wrtap - 1][0])),
                next_tap.eq(Cat(wrdata_en.taps[wrtap - 1][1:], wrdata_en.taps[wrtap - 2][0])),
            ]

            dqs_oe        = Signal(2*nphases)
            dqs_pattern   = DDR5DQSPattern(
                old_tap       = old_tap,
                now_tap       = now_tap,
                next_tap      = next_tap,
                wlevel_en     = getattr(self, prefix+'wlevel_en').storage,
                wlevel_strobe = getattr(self, prefix+'wlevel_strobe').re)
            self.submodules += dqs_pattern

            dq_oe        = Signal(2*nphases)
            dq_pattern   = DDR5DQOePattern(old_tap=old_tap, now_tap=now_tap)
            self.submodules += dq_pattern

            for byte in range(strobes):
                # output
                dqs_bitslip    = BitSlip(8,
                    i      = dqs_pattern.o,
                    rst    = self.get_rst(byte, getattr(self, prefix+'wdly_dqs_bitslip_rst').re, prefix),
                    slp    = self.get_inc(byte, getattr(self, prefix+'wdly_dqs_bitslip').re, prefix),
                    cycles = 1)
                self.submodules += dqs_bitslip

                dqs_oe_bitslip    = BitSlip(8,
                    i      = dqs_pattern.oe,
                    rst    = self.get_rst(byte, getattr(self, prefix+'wdly_dqs_bitslip_rst').re, prefix),
                    slp    = self.get_inc(byte, getattr(self, prefix+'wdly_dqs_bitslip').re, prefix),
                    cycles = 1)
                self.submodules += dqs_oe_bitslip

                dq_oe_bitslip    = BitSlip(8,
                    i      = dq_pattern.oe,
                    rst    = self.get_rst(byte, getattr(self, prefix+'wdly_dq_bitslip_rst').re, prefix),
                    slp    = self.get_inc(byte, getattr(self, prefix+'wdly_dq_bitslip').re, prefix),
                    cycles = 1)
                self.submodules += dq_oe_bitslip

                self.comb += [
                    getattr(self.out, prefix+'dqs_t_o')[byte].eq(dqs_bitslip.o),
                    getattr(self.out, prefix+'dqs_c_o')[byte].eq(~dqs_bitslip.o),
                    getattr(self.out, prefix+'dqs_oe')[byte].eq(dqs_oe_bitslip.o),
                    getattr(self.out, prefix+'dq_oe')[byte].eq(dq_oe_bitslip.o),
                ]


            # DMI --------------------------------------------------------------------------------------
            # DMI signal is used for Data Mask or Data Bus Invertion depending on Mode Registers values.
            # With DM and DBI disabled, this signal is a Don't Care.
            # With DM enabled, masking is performed only when the command used is WRITE-MASKED.
            # We don't support DBI, DM support is configured statically with `masked_write`.
            for byte in range(strobes):
                if isinstance(masked_write, Signal) or masked_write:
                    dm_i = [
                        getattr(dfi.phases[i//2], prefix).wrdata_mask[i%2 * strobes + byte]
                        for i in range(2*nphases)
                    ]
                    dm_o_bitslip = BitSlip(8,
                        i      = dm_i,
                        rst    = self.get_rst(byte, getattr(self, prefix+'wdly_dq_bitslip_rst').re, prefix),
                        slp    = self.get_inc(byte, getattr(self, prefix+'wdly_dq_bitslip').re, prefix),
                        cycles = 1)

                    self.submodules += dm_o_bitslip
                    self.comb += getattr(self.out, prefix+'dm_n_o')[byte].eq(Cat(dm_o_bitslip.o))

                else:
                    self.comb += getattr(self.out, prefix+'dm_n_o')[byte].eq(0)

            # DQ ---------------------------------------------------------------------------------------
            delayed_rddata = Array([Signal.like(getattr(dfi.phases[0], prefix).rddata) for _ in range(nphases)])

            for bit in range(self.databits):
                # output
                wrdata = [
                    getattr(dfi.phases[i//2], prefix).wrdata[i%2 * self.databits + bit] for i in range(2*nphases)
                ]
                dq_o_bitslip = BitSlip(8,
                    i      = Cat(*wrdata),
                    rst    = self.get_rst(bit//dq_dqs_ratio, getattr(self, prefix+'wdly_dq_bitslip_rst').re, prefix),
                    slp    = self.get_inc(bit//dq_dqs_ratio, getattr(self, prefix+'wdly_dq_bitslip').re, prefix),
                    cycles = 1)

                self.submodules += dq_o_bitslip
                self.comb += getattr(self.out, prefix+'dq_o')[bit].eq(dq_o_bitslip.o)

                # input
                dq_i_bs = Signal(2*nphases)
                dq_i_bitslip = BitSlip(8,
                    i      = getattr(self.out, prefix+'dq_i')[bit],
                    rst    = self.get_rst(bit//dq_dqs_ratio, getattr(self, prefix+'rdly_dq_bitslip_rst').re, prefix),
                    slp    = self.get_inc(bit//dq_dqs_ratio, getattr(self, prefix+'rdly_dq_bitslip').re, prefix),
                    cycles = 1)
                self.submodules += dq_i_bitslip

                self.comb += dq_i_bs.eq(dq_i_bitslip.o)
                for i in range(2*nphases):
                    self.comb += getattr(self.dfi.phases[i//2], prefix).rddata[i%2 * self.databits + bit].eq(dq_i_bs[i])

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
                getattr(phase, prefix).rddata_valid.eq(rddata_en.output | getattr(self, prefix+'wlevel_en').storage)
                for phase in self.dfi.phases
            ]

    def get_rst(self, byte, rst, prefix="", clk="sys"):
        cd_clk = getattr(self.sync, clk)
        t = Signal()
        cd_clk += t.eq((getattr(self, prefix+'dly_sel').storage[byte] & rst) | self._rst.storage)
        return t

    def get_inc(self, byte, inc, prefix="", clk="sys"):
        cd_clk = getattr(self.sync, clk)
        t = Signal()
        cd_clk += t.eq(getattr(self, prefix+"dly_sel").storage[byte] & inc)
        return t
