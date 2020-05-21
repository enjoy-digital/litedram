# This file is Copyright (c) 2012 Sebastien Bourdeauducq <sb@m-labs.hk>
# This file is Copyright (c) 2012-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2020 Antmicro <www.antmicro.com>
# License: BSD

from functools import reduce
from operator import or_

from migen import *
from migen.genlib.record import *
from migen.fhdl.decorators import ClockDomainsRenamer

from litedram.common import *
from litedram.phy.dfi import *


class Serializer(Module):
    def __init__(self, sd, strb, inputs):
        assert(len(inputs) > 0)
        assert(len(s) == len(inputs[0]) for s in inputs)

        data_width = len(inputs)
        signal_width = len(inputs[0])

        if not isinstance(inputs, Array):
            inputs = Array(inputs)

        self.o = Signal(signal_width)
        data_cntr = Signal(log2_int(data_width), reset=strb)
        sd += data_cntr.eq(data_cntr+1)
        self.comb += self.o.eq(inputs[data_cntr])

class Deserializer(Module):
    def __init__(self, sd, strb, input, outputs):
        assert(len(outputs) > 0)
        assert(len(s) == len(outputs[0]) for s in outputs)
        assert(len(outputs[0]) == len(input))

        data_width = len(outputs)
        signal_width = len(outputs[0])

        if not isinstance(outputs, Array):
            outputs = Array(outputs)

        data_cntr = Signal(log2_int(data_width), reset=strb)
        sd += data_cntr.eq(data_cntr+1)
        sd += outputs[data_cntr].eq(input)

class GenericDDR3PHY(Module):
    def __init__(self, pads, memtype, rd_bitslip, wr_bitslip, platform=None):
        pads        = PHYPadsCombiner(pads)
        if memtype not in ["DDR", "LPDDR", "DDR2", "DDR3"]:
            raise NotImplementedError("GenericDDR3PHY only supports DDR, LPDDR, DDR2 and DDR3")
        addressbits = len(pads.a)
        bankbits    = len(pads.ba)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = 2
        assert databits%8 == 0

        # Load verilog models
        if platform is not None:
            from os import path
            this_file_dir = path.dirname(__file__)
            thirdparty_dir = path.abspath(path.join(this_file_dir, "../../thirdparty"))

            platform.verilog_include_paths.append(f"{thirdparty_dir}/xil-models")
            platform.add_source(f"{thirdparty_dir}/xil-models/ISERDES2.v")
            platform.add_source(f"{thirdparty_dir}/xil-models/ODDR2.v")
            platform.add_source(f"{thirdparty_dir}/xil-models/IOBUF.v")
            # platform.verilog_include_paths.append(f"{thirdparty_dir}/pll_sim")
            # platform.add_source(f"{thirdparty_dir}/pll_sim/PLL_sim.v")


        # PHY settings -----------------------------------------------------------------------------
        if memtype == "DDR3":
            self.settings = PhySettings(
                phytype       = "GenericDDR3PHY",
                memtype       = "DDR3",
                databits      = databits,
                dfi_databits  = 2*databits,
                nranks        = nranks,
                nphases       = nphases,
                rdphase       = 0,
                wrphase       = 1,
                rdcmdphase    = 1,
                wrcmdphase    = 0,
                cl            = 6,
                cwl           = 5,
                read_latency  = 6,
                write_latency = 1
            )
        else:
            self.settings = PhySettings(
                phytype       = "GenericDDR3PHY",
                memtype       = memtype,
                databits      = databits,
                dfi_databits  = 2*databits,
                nranks        = nranks,
                nphases       = nphases,
                rdphase       = 0,
                wrphase       = 1,
                rdcmdphase    = 1,
                wrcmdphase    = 0,
                cl            = 3,
                read_latency  = 5,
                write_latency = 0
            )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
        self.clk4x_wr_strb = Signal()
        self.clk4x_rd_strb = Signal()

        # # #

        # Clock ------------------------------------------------------------------------------------
        # sys_clk           : system clk, used for dfi interface
        # sdram_half_clk    : half rate sdram clk
        # sdram_full_wr_clk : full rate sdram write clk
        # sdram_full_rd_clk : full rate sdram read clk
        sd_sys = getattr(self.sync, "sys")
        sd_sdram_half = getattr(self.sync, "sdram_half")
        sd_full_wr = getattr(self.sync, "sdram_full_wr")
        sd_full_rd = getattr(self.sync, "sdram_full_rd")

        sys_clk = ClockSignal("sys")
        sdram_half_clk = ClockSignal("sdram_half")
        sdram_full_wr_clk = ClockSignal("sdram_full_wr")
        sdram_full_rd_clk = ClockSignal("sdram_full_rd")

        # Addresses and Commands -------------------------------------------------------------------

        # select active phase
        #             sys_clk   ----____----____
        #  phase_sel(nphases=2) 0   1   0   1     Half Rate
        phase_sel = Signal(log2_int(nphases))
        phase_half = Signal.like(phase_sel)
        phase_sys = Signal.like(phase_half)

        sd_sys += phase_sys.eq(phase_half)

        sd_sdram_half += [
            If(phase_half == phase_sys,
                phase_sel.eq(0),
            ).Else(
                phase_sel.eq(phase_sel+1)
            ),
            phase_half.eq(phase_half+1),
        ]

        # register dfi cmds on half_rate clk
        r_dfi = Array(Record(phase_cmd_description(addressbits, bankbits, nranks=nranks)) for i in range(nphases))
        for n, phase in enumerate(dfi.phases):
            sd_sdram_half += [
                r_dfi[n].reset_n.eq(phase.reset_n),
                r_dfi[n].odt.eq(phase.odt),
                r_dfi[n].address.eq(phase.address),
                r_dfi[n].bank.eq(phase.bank),
                r_dfi[n].cs_n.eq(phase.cs_n),
                r_dfi[n].cke.eq(phase.cke),
                r_dfi[n].cas_n.eq(phase.cas_n),
                r_dfi[n].ras_n.eq(phase.ras_n),
                r_dfi[n].we_n.eq(phase.we_n)
            ]

        # Iterate on pads groups -------------------------------------------------------------------
        for pads_group in range(len(pads.groups)):
            pads.sel_group(pads_group)

            # output cmds
            sd_sdram_half += [
                pads.a.eq(r_dfi[phase_sel].address),
                pads.ba.eq(r_dfi[phase_sel].bank),
                pads.cke.eq(r_dfi[phase_sel].cke),
                pads.ras_n.eq(r_dfi[phase_sel].ras_n),
                pads.cas_n.eq(r_dfi[phase_sel].cas_n),
                pads.we_n.eq(r_dfi[phase_sel].we_n)
            ]
            # optional pads
            for name in "reset_n", "cs_n", "odt":
              if hasattr(pads, name):
                  sd_sdram_half += getattr(pads, name).eq(getattr(r_dfi[phase_sel], name))

        # Bitslip ----------------------------------------------------------------------------------
        bitslip_cnt = Signal(4)
        bitslip_inc = Signal()

        sd_sys += [
            If(bitslip_cnt == rd_bitslip,
                bitslip_inc.eq(0)
            ).Else(
                bitslip_cnt.eq(bitslip_cnt+1),
                bitslip_inc.eq(1)
            )
        ]

        # DQ/DQS/DM data ---------------------------------------------------------------------------
        sdram_half_clk_n = Signal()
        self.comb += sdram_half_clk_n.eq(~sdram_half_clk)

        postamble = Signal()
        drive_dqs = Signal()
        dqs_t_d0 = Signal()
        dqs_t_d1 = Signal()

        dqs_o = Signal(databits//8)
        dqs_t = Signal(databits//8)

        self.comb += [
            dqs_t_d0.eq(~(drive_dqs | postamble)),
            dqs_t_d1.eq(~drive_dqs),
        ]

        for i in range(databits//8):
            # DQS output
            self.specials += Instance("ODDR2",
                # p_DDR_ALIGNMENT=dqs_ddr_alignment,
                # p_INIT=0,
                # p_SRTYPE="ASYNC",

                i_C0=sdram_half_clk,
                i_C1=sdram_half_clk_n,

                i_CE=1,
                i_D0=0,
                i_D1=1,
                i_R=0,
                i_S=0,

                o_Q=dqs_o[i]
            )

            # DQS tristate cmd
            self.specials += Instance("ODDR2",
                # p_DDR_ALIGNMENT=dqs_ddr_alignment,
                # p_INIT=0,
                # p_SRTYPE="ASYNC",

                i_C0=sdram_half_clk,
                i_C1=sdram_half_clk_n,

                i_CE=1,
                i_D0=dqs_t_d0,
                i_D1=dqs_t_d1,
                i_R=0,
                i_S=0,

                o_Q=dqs_t[i]
            )

            # DQS tristate buffer
            if hasattr(pads, "dqs_n"):
                self.specials += Instance("IOBUFDS",
                    i_T    = dqs_t[i],
                    i_I    = dqs_o[i],
                    io_IO  = pads.dqs[i],
                    io_IOB = pads.dqs_n[i],
                )
            else:
                self.specials += Instance("IOBUF",
                    i_T   = dqs_t[i],
                    i_I   = dqs_o[i],
                    io_IO = pads.dqs[i],
                )

        sd_sdram_half += postamble.eq(drive_dqs)

        d_dfi = [Record(phase_wrdata_description(nphases*databits)+phase_rddata_description(nphases*databits))
            for i in range(2*nphases)]

        for n, phase in enumerate(dfi.phases):
            self.comb += [
                d_dfi[n].wrdata.eq(phase.wrdata),
                d_dfi[n].wrdata_mask.eq(phase.wrdata_mask),
                d_dfi[n].wrdata_en.eq(phase.wrdata_en),
                d_dfi[n].rddata_en.eq(phase.rddata_en),
            ]
            sd_sys += [
                d_dfi[nphases+n].wrdata.eq(phase.wrdata),
                d_dfi[nphases+n].wrdata_mask.eq(phase.wrdata_mask)
            ]


        drive_dq = Signal()
        drive_dq_n = [Signal() for i in range(2)]
        self.comb += drive_dq_n[0].eq(~drive_dq)
        sd_sys += drive_dq_n[1].eq(drive_dq_n[0])

        dq_t = Signal(databits)
        dq_o = Signal(databits)
        dq_i = Signal(databits)

        dq_wrdata = []

        for i in range(2):
            for j in reversed(range(nphases)):
                dq_wrdata.append(d_dfi[i*nphases+j].wrdata[:databits])
                dq_wrdata.append(d_dfi[i*nphases+j].wrdata[databits:])


        self.oserdes_d1 = Signal.like(dq_wrdata[wr_bitslip+3])
        self.oserdes_d2 = Signal.like(dq_wrdata[wr_bitslip+2])
        self.oserdes_d3 = Signal.like(dq_wrdata[wr_bitslip+1])
        self.oserdes_d4 = Signal.like(dq_wrdata[wr_bitslip+0])

        self.comb += self.oserdes_d1.eq(dq_wrdata[wr_bitslip+3])
        self.comb += self.oserdes_d2.eq(dq_wrdata[wr_bitslip+2])
        self.comb += self.oserdes_d3.eq(dq_wrdata[wr_bitslip+1])
        self.comb += self.oserdes_d4.eq(dq_wrdata[wr_bitslip+0])

        self.test_dq = Signal(len(pads.dq))

        self.submodules.dq_serializer = Serializer(sd_full_wr, self.clk4x_wr_strb,
                [self.oserdes_d1, self.oserdes_d2, self.oserdes_d3, self.oserdes_d4])

        self.comb += self.test_dq.eq(self.dq_serializer.o)
        # self.comb += dq_o.eq(self.dq_serializer.o)



        self.iserdes_q1 = Signal.like(d_dfi[0].rddata)
        self.iserdes_q2 = Signal.like(d_dfi[1].rddata)
        # self.iserdes_q3 = Signal.like(d_dfi[1].rddata[:databits])
        # self.iserdes_q4 = Signal.like(d_dfi[1].rddata[databits:])

        self.submodules.dq_deserializer = Deserializer(sd_full_rd, self.clk4x_rd_strb, dq_i,
                [self.iserdes_q1[databits:], self.iserdes_q1[:databits], self.iserdes_q2[databits:], self.iserdes_q2[:databits]])

        for i in range(databits):
            # Data serializer
            self.specials += Instance("OSERDES2",
                p_DATA_WIDTH=4,
                p_DATA_RATE_OQ="SDR",
                p_DATA_RATE_OT="SDR",
                p_SERDES_MODE="NONE",
                p_OUTPUT_MODE="SINGLE_ENDED",

                o_OQ=dq_o[i],
                i_OCE=1,
                i_CLK0=sdram_full_wr_clk,
                i_CLK1=0,
                i_IOCE=self.clk4x_wr_strb,
                i_RST=0,
                i_CLKDIV=sys_clk,

                i_D1=dq_wrdata[wr_bitslip+3][i],
                i_D2=dq_wrdata[wr_bitslip+2][i],
                i_D3=dq_wrdata[wr_bitslip+1][i],
                i_D4=dq_wrdata[wr_bitslip+0][i],

                o_TQ=dq_t[i],
                i_T1=drive_dq_n[(wr_bitslip+3)//4],
                i_T2=drive_dq_n[(wr_bitslip+2)//4],
                i_T3=drive_dq_n[(wr_bitslip+1)//4],
                i_T4=drive_dq_n[(wr_bitslip+0)//4],
                i_TRAIN=0,
                i_TCE=1,
                i_SHIFTIN1=0,
                i_SHIFTIN2=0,
                i_SHIFTIN3=0,
                i_SHIFTIN4=0,
            )

            # Data deserializer
            self.specials += Instance("ISERDES2",
                p_DATA_WIDTH=4,
                p_DATA_RATE="SDR",
                p_BITSLIP_ENABLE="TRUE",
                p_SERDES_MODE="NONE",
                p_INTERFACE_TYPE="RETIMED",

                i_D=dq_i[i],
                i_CE0=1,
                i_CLK0=sdram_full_rd_clk,
                i_CLK1=0,
                i_IOCE=self.clk4x_rd_strb,
                i_RST=ResetSignal(),
                i_CLKDIV=sys_clk,
                i_BITSLIP=bitslip_inc,

                o_Q1=d_dfi[0*nphases+0].rddata[i],
                o_Q2=d_dfi[0*nphases+0].rddata[i+databits],
                o_Q3=d_dfi[0*nphases+1].rddata[i],
                o_Q4=d_dfi[0*nphases+1].rddata[i+databits],
            )

            # Data buffer
            self.specials += Instance("IOBUF",
                i_I=dq_o[i],
                o_O=dq_i[i],
                i_T=dq_t[i],
                io_IO=pads.dq[i]
            )

        dq_wrdata_mask = []
        for i in range(2):
            for j in reversed(range(nphases)):
                dq_wrdata_mask.append(d_dfi[i*nphases+j].wrdata_mask[:databits//8])
                dq_wrdata_mask.append(d_dfi[i*nphases+j].wrdata_mask[databits//8:])

        self.dm_oserdes_d1 = Signal.like(dq_wrdata_mask[wr_bitslip+3])
        self.dm_oserdes_d2 = Signal.like(dq_wrdata_mask[wr_bitslip+2])
        self.dm_oserdes_d3 = Signal.like(dq_wrdata_mask[wr_bitslip+1])
        self.dm_oserdes_d4 = Signal.like(dq_wrdata_mask[wr_bitslip+0])

        self.comb += self.dm_oserdes_d1.eq(dq_wrdata_mask[wr_bitslip+3])
        self.comb += self.dm_oserdes_d2.eq(dq_wrdata_mask[wr_bitslip+2])
        self.comb += self.dm_oserdes_d3.eq(dq_wrdata_mask[wr_bitslip+1])
        self.comb += self.dm_oserdes_d4.eq(dq_wrdata_mask[wr_bitslip+0])

        self.test_dm = Signal(len(pads.dm))

        self.submodules.dm_serializer = Serializer(sd_full_wr, self.clk4x_wr_strb,
                [self.dm_oserdes_d1, self.dm_oserdes_d2, self.dm_oserdes_d3, self.dm_oserdes_d4])

        self.comb += self.test_dm.eq(self.dm_serializer.o)

        # dm = Signal(len(pads.dm))
        # self.comb += [pads.dm[i].eq(dm[i]) for i in range(len(pads.dm))]
        # self.comb += dm.eq(self.dm_serializer.o)

        for i in range(databits//8):
            # Mask serializer
            self.specials += Instance("OSERDES2",
                p_DATA_WIDTH=4,
                p_DATA_RATE_OQ="SDR",
                p_DATA_RATE_OT="SDR",
                p_SERDES_MODE="NONE",
                p_OUTPUT_MODE="SINGLE_ENDED",
                o_OQ=pads.dm[i],
                i_OCE=1,
                i_CLK0=sdram_full_wr_clk,
                i_CLK1=0,
                i_IOCE=self.clk4x_wr_strb,
                i_RST=0,
                i_CLKDIV=sys_clk,
                i_D1=dq_wrdata_mask[wr_bitslip+3][i],
                i_D2=dq_wrdata_mask[wr_bitslip+2][i],
                i_D3=dq_wrdata_mask[wr_bitslip+1][i],
                i_D4=dq_wrdata_mask[wr_bitslip+0][i],
                i_TRAIN=0,
                i_TCE=0,
                i_SHIFTIN1=0,
                i_SHIFTIN2=0,
                i_SHIFTIN3=0,
                i_SHIFTIN4=0,
            )

        # DQ/DQS/DM control ------------------------------------------------------------------------

        # write
        wrdata_en = Signal()
        self.comb += wrdata_en.eq(reduce(or_, [d_dfi[p].wrdata_en for p in range(nphases)]))

        if memtype == "DDR3":
            r_drive_dq = Signal(self.settings.cwl-1)
            sd_sdram_half += r_drive_dq.eq(Cat(wrdata_en, r_drive_dq))
            self.comb += drive_dq.eq(r_drive_dq[self.settings.cwl-2])
        else:
            self.comb += drive_dq.eq(wrdata_en)

        wrdata_en_d = Signal()
        sd_sys += wrdata_en_d.eq(wrdata_en)

        if memtype == "DDR3":
            r_dfi_wrdata_en = Signal(max(self.settings.cwl, self.settings.cl))
        else:
            r_dfi_wrdata_en = Signal(self.settings.cl)
        sd_sdram_half += r_dfi_wrdata_en.eq(Cat(wrdata_en_d, r_dfi_wrdata_en))

        if memtype == "DDR3":
            self.comb += drive_dqs.eq(r_dfi_wrdata_en[self.settings.cwl-1])
        else:
            self.comb += drive_dqs.eq(r_dfi_wrdata_en[1])

        # read
        rddata_en = Signal()
        self.comb += rddata_en.eq(reduce(or_, [d_dfi[p].rddata_en for p in range(nphases)]))

        rddata_sr = Signal(self.settings.read_latency)
        sd_sys += rddata_sr.eq(Cat(rddata_sr[1:self.settings.read_latency], rddata_en))

        for n, phase in enumerate(dfi.phases):
            self.comb += [
                phase.rddata.eq(d_dfi[n].rddata),
                phase.rddata_valid.eq(rddata_sr[0]),
            ]
