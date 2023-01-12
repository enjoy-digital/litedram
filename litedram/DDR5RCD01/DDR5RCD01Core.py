#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

# Python
import logging
# migen
from operator import xor
from migen import *
from migen.fhdl import verilog
# RCD
from litedram.DDR5RCD01.RCD_utils import *
from litedram.DDR5RCD01.RCD_definitions import *
from litedram.DDR5RCD01.RCD_interfaces import *
# Simulation Pads
from litedram.DDR5RCD01.DDR5RCD01CoreEgressSimulationPads import DDR5RCD01CoreEgressSimulationPads
from litedram.DDR5RCD01.DDR5RCD01CoreIngressSimulationPads import DDR5RCD01CoreIngressSimulationPads
# Submodules
from litedram.DDR5RCD01.DDR5RCD01Channel import DDR5RCD01Channel
from litedram.DDR5RCD01.DDR5RCD01Common import DDR5RCD01Common


class DDR5RCD01Core(Module):
    """DDR5 RCD01 Core
    TODO Documentation
    Primary function of the Core is to buffer the Command/Address (CA) bus, chip selects and clock
    between the host controller and the DRAMs
    In the LRDIMM use case, a BCOM bus is created to communicate with the data buffers.

    The Core consists of 2 independent channels and some common logic, e.g.: clocking.

    The term "Definintion X.Y.Z" refers to the X.Y.Z section of the JEDEC Standard DDR5 Registering
    Clock Driver Definition (DDR5RCD01).

    """

    def __init__(self, pads_ingress, pads_sideband, aligned_reset_zero=False, dq_dqs_ratio=8,
                 nranks=1, is_dual_channel=False, **kwargs):
        self.submodules.pads_ingress = pads_ingress
        self.submodules.pads_sideband = pads_sideband

        pads_egress = DDR5RCD01CoreEgressSimulationPads(
            is_dual_channel=is_dual_channel)

        self.submodules.pads_egress = pads_egress
        # Internal implementation
        # TODO Integrate simulation pads and interfaces
        if_sdram_A_rst_n = If_rst_n()
        self.comb += if_sdram_A_rst_n.rst_n.eq(self.pads_egress.A_qrst_n)

        # Host <-> common
        if_host_ck = If_ck()
        self.comb += if_host_ck.ck_t.eq(self.pads_ingress.dck_t)
        self.comb += if_host_ck.ck_c.eq(self.pads_ingress.dck_c)
        if_host_rst_n = If_rst_n()
        self.comb += if_host_rst_n.rst_n.eq(self.pads_ingress.drst_n)
        if_host_err = If_error()
        self.comb += if_host_err.err_n.eq(self.pads_ingress.alert_n)
        if_host_lb = If_lb()
        self.comb += if_host_lb.lbd.eq(self.pads_ingress.qlbd)
        self.comb += if_host_lb.lbs.eq(self.pads_ingress.qlbd)
        # Host <-> channel A
        if_ibuf_A = If_channel_ibuf()
        self.comb += if_ibuf_A.dca.eq(self.pads_ingress.A_dca)
        self.comb += if_ibuf_A.dcs_n.eq(self.pads_ingress.A_dcs_n)
        self.comb += if_ibuf_A.dpar.eq(self.pads_ingress.A_dpar)
        # Channel A <-> SDRAM
        if_obuf_csca_A = If_channel_obuf_csca()
        self.comb += if_obuf_csca_A.qacs_a_n.eq(self.pads_egress.A_qacs_a_n)
        self.comb += if_obuf_csca_A.qaca_a.eq(self.pads_egress.A_qaca_a)
        self.comb += if_obuf_csca_A.qacs_b_n.eq(self.pads_egress.A_qacs_b_n)
        self.comb += if_obuf_csca_A.qaca_b.eq(self.pads_egress.A_qaca_b)
        if_obuf_clks_A = If_channel_obuf_clks()
        self.comb += if_obuf_clks_A.qack_t.eq(self.pads_egress.A_qack_t)
        self.comb += if_obuf_clks_A.qack_c.eq(self.pads_egress.A_qack_c)
        self.comb += if_obuf_clks_A.qbck_t.eq(self.pads_egress.A_qbck_t)
        self.comb += if_obuf_clks_A.qbck_c.eq(self.pads_egress.A_qbck_c)
        self.comb += if_obuf_clks_A.qcck_t.eq(self.pads_egress.A_qcck_t)
        self.comb += if_obuf_clks_A.qcck_c.eq(self.pads_egress.A_qcck_c)
        self.comb += if_obuf_clks_A.qdck_t.eq(self.pads_egress.A_qdck_t)
        self.comb += if_obuf_clks_A.qdck_c.eq(self.pads_egress.A_qdck_c)

        if_sdram_A = If_error()
        self.comb += if_sdram_A.err_n.eq(self.pads_egress.A_derror_in_n)

        if_sdram_B_rst_n = If_rst_n()
        self.comb += if_sdram_B_rst_n.rst_n.eq(self.pads_egress.B_qrst_n)

        # Host <-> channel B
        if_ibuf_B = If_channel_ibuf()
        # Channel B <-> SDRAM
        if_obuf_csca_B = If_channel_obuf_csca()
        if_obuf_clks_B = If_channel_obuf_clks()
        if_sdram_B = If_error()

        # Channel A
        if_channel_A_ck = If_ck()
        if_channel_A_rst_n = If_rst_n()
        if_channel_A_err = If_error()
        if_channel_A_lb = If_int_lb()

        # Global config to common
        if_ctrl_pll = If_ctrl_pll()
        if_ctrl_err = If_ctrl_err()
        if_ctrl_lb = If_ctrl_lb()

        # Global config to channel B
        if_ctrl_global = If_channel_config_global()
        is_channel_A = True
        channel_A = DDR5RCD01Channel(
            if_channel_A_ck, if_channel_A_rst_n,
            if_ibuf_A,  # Host interfaces
            if_obuf_csca_A, if_obuf_clks_A, if_sdram_A,  # SDRAM interfaces
            if_channel_A_err, if_channel_A_lb,  # Common
            if_ctrl_global,  # A<->B config
            is_channel_A,
            if_ctrl_pll, if_ctrl_lb, if_ctrl_err,  # Optional args! Only channel A
        )
        self.submodules += channel_A

        # Channel B
        if_channel_B_ck = If_ck()
        if_channel_B_rst_n = If_rst_n()
        if_channel_B_err = If_error()
        if_channel_B_lb = If_int_lb()

        if is_dual_channel:
            is_channel_B = not is_channel_A
            channel_B = DDR5RCD01Channel(if_channel_B_ck, if_channel_B_rst_n,
                                         if_ibuf_B,  # Host interfaces
                                         if_obuf_csca_B, if_obuf_clks_B, if_sdram_B,  # SDRAM interfaces
                                         if_channel_B_err, if_channel_B_lb,  # Common
                                         if_ctrl_global,  # A<->B config
                                         is_channel_B,
                                         )
            self.submodules += channel_B

        # Common part

        if_sdram_A_lb = If_lb()
        if_sdram_B_lb = If_lb()
        if_rcd_lb = If_lb()

        common = DDR5RCD01Common(if_host_ck, if_host_rst_n,  # Distribute clock and reset
                                 if_channel_A_ck, if_channel_A_rst_n,
                                 if_channel_B_ck, if_channel_B_rst_n,
                                 if_sdram_A_rst_n, if_sdram_B_rst_n,
                                 # Error
                                 if_host_err,
                                 if_channel_A_err,
                                 if_channel_B_err,
                                 # Loopback
                                 if_host_lb,
                                 if_rcd_lb,
                                 if_sdram_A_lb,
                                 if_sdram_B_lb,
                                 if_channel_A_lb,
                                 if_channel_B_lb,
                                 # Control interfaces
                                 if_ctrl_pll, if_ctrl_lb, if_ctrl_err,
                                 )
        self.submodules += common

        # TODO feed egress from interfaces


class TestBed(Module):
    def __init__(self):
        is_dual_channel = True
        self.pi = DDR5RCD01CoreIngressSimulationPads(
            is_dual_channel=is_dual_channel)
        self.po = DDR5RCD01CoreEgressSimulationPads(
            is_dual_channel=is_dual_channel)
        self.submodules.dut = DDR5RCD01Core(
            self.pi, self.po, is_dual_channel=is_dual_channel)

        self.clock_domains.dck_t = ClockDomain(name="dck_t")
        self.clock_domains.dck_c = ClockDomain(name="dck_c")

        self.sync += self.dck_t.clk.eq(~self.dck_t.clk)
        self.comb += self.dck_c.clk.eq(~self.dck_t.clk)
        self.comb += self.pi.dck_t.eq(self.dck_t.clk)
        self.comb += self.pi.dck_c.eq(self.dck_c.clk)
        # print(verilog.convert(self.dut))


def seq_cmds(tb):
    # TODO all commands are passed as if they were 2UIs long. To be fixed.
    # Single UI command
    yield from n_ui_dram_command(tb, nums=[0x01, 0x02])
    # 2 UI commands
    yield from n_ui_dram_command(tb, nums=[0x01, 0x02, 0x03, 0x04])
    yield from n_ui_dram_command(tb, nums=[0x0A, 0x0B, 0x0C, 0x0D], non_target_termination=True)
    yield from n_ui_dram_command(tb, nums=[0xDE, 0xAD, 0xBA, 0xBE], non_target_termination=True)
    yield from n_ui_dram_command(tb, nums=[0xC0, 0xDE, 0xF0, 0x0D])


def n_ui_dram_command(tb, nums, non_target_termination=False):
    """
    This function drives the interface with as in:
        "JEDEC 82-511 Figure 7
        One UI DRAM Command Timing Diagram"
    
    Nums can be any length to incroporate two, or more, UI commands
    
    The non target termination parameter extends the DCS assertion to the 2nd UI
    """
    SEQ_INACTIVE = [~0, 0]
    yield from drive_init(tb)
    yield from set_parity(tb)

    sequence = [SEQ_INACTIVE]
    for id, num in enumerate(nums):
        if non_target_termination:
            if id in [0,1,2,3]:
                sequence.append([0b00, num])
            else:
                sequence.append([0b11, num])
        else:
            if id in [0, 1]:
                sequence.append([0b00, num])
            else:
                sequence.append([0b11, num])

    sequence.append(SEQ_INACTIVE)

    for seq_cs, seq_ca in sequence:
        logging.debug(str(seq_cs) + " " + str(seq_ca))
        yield from drive_cs_ca(seq_cs, seq_ca)
    for i in range(3):
        yield


def drive_init(tb):
    yield tb.pi.drst_n.eq(1)
    yield from drive_cs_ca(~0, 0)


def drive_cs_ca(cs, ca):
    yield tb.pi.A_dcs_n.eq(cs)
    yield tb.pi.A_dca.eq(ca)
    yield


def set_parity(tb):
    yield tb.pi.A_dpar.eq(reduce(xor, [tb.pi.A_dca[bit] for bit in range(len(tb.pi.A_dca))]))


def run_test(tb):
    logging.debug('Write test')
    # yield from one_ui_dram_command(tb)
    INIT_CYCLES = CW_DA_REGS_NUM + 5
    yield from drive_init(tb)
    for i in range(INIT_CYCLES):
        yield
    yield from seq_cmds(tb)
    for i in range(5):
        yield

    logging.debug('Yield from write test.')


if __name__ == "__main__":
    eT = EngTest(level=logging.INFO)
    logging.info("<- Module called")
    tb = TestBed()
    logging.info("<- Module ready. Simulating with migen...")
    run_simulation(tb, run_test(tb), vcd_name=eT.wave_file_name)
    logging.info("<- Simulation done")
    logging.info(str(eT))
