#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

# if_<name> := Interface name
# if_<name>_<block><function>


class If_channel_ibuf(Record):
    """
    This interface is used for the following connections:
    Core input of input buffer
    Output of the input buffer
    Input of the line buffer
    Input of the Control Center
    """

    def __init__(self, dcs_n_w=2, dca_w=7):
        layout = self.description(dcs_n_w, dca_w)
        Record.__init__(self, layout)

    def description(self, dcs_n_w, dca_w):
        return [
            ('dcs_n', dcs_n_w),
            ('dca', dca_w),
            ('dpar', 1),
        ]


class If_channel_obuf_clks(Record):
    """
    Q[D:A]CK_[T,C] Clock Bus
    This interface is used for the following connections:
    Input of the output buffer
    Output of the line buffer
    Core output of output buffer
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            # Clock outputs
            # Rank 0, Row Top
            ('qack_t', 1, False),
            ('qack_c', 1, False),
            # Rank 1, Row Top
            ('qbck_t', 1, False),
            ('qbck_c', 1, False),
            # Rank 0, Row Bottom
            ('qcck_t', 1, False),
            ('qcck_c', 1, False),
            # Rank 1, Row Top
            ('qdck_t', 1, False),
            ('qdck_c', 1, False),
        ]


class If_channel_obuf_csca(Record):
    """
    This interface is used for the following connections:
    Input of the output buffer
    Output of the line buffer
    Core output of output buffer
    """

    def __init__(self, qacs_w=2, qaca_w=14):
        layout = self.description(qacs_w, qaca_w)
        Record.__init__(self, layout)

    def description(self, qacs_w, qaca_w):
        return [
            # Adress, Chip Select
            # Top Row
            ('qacs_a_n', qacs_w, False),
            ('qaca_a', qaca_w, False),
            # Bottom Row
            ('qacs_b_n', qacs_w, False),
            ('qaca_b', qaca_w, False),
        ]


class If_channel_sdram(Record):
    """
    This interface is used for the:
    Signals coming from the sdram to channel
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            # SDRAM raises an error
            ('derror_in_n', 1, False),
        ]


class If_ctrl_ibuf(Record):
    """
    This interface is used for the:
    Configuration of the input buffer
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('en', 1),
        ]


class If_ctrl_lbuf(Record):
    """
    This interface is used for the:
    Configuration of the line buffer
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('sel_latency_add', 3),
            ('deser_sel_lower_upper', 1),
            ('deser_ca_d_en', 1),
            ('deser_ca_q_en', 1),
            ('deser_cs_n_d_en', 1),
            ('deser_cs_n_q_en', 1),

        ]


class If_ctrl_obuf(Record):
    """
    This interface is used for the:
    Configuration of the output buffer
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('oe_qacs_a_n', 1),
            ('o_inv_en_qacs_a_n', 1),
            ('oe_qaca_a', 1),
            ('o_inv_en_qaca_a', 1),
            ('oe_qacs_b_n', 1),
            ('o_inv_en_qacs_b_n', 1),
            ('oe_qaca_b', 1),
            ('o_inv_en_qaca_b', 1),
            ('oe_qack_t', 1),
            ('o_inv_en_qack_t', 1),
            ('oe_qack_c', 1),
            ('o_inv_en_qack_c', 1),
            ('oe_qbck_t', 1),
            ('o_inv_en_qbck_t', 1),
            ('oe_qbck_c', 1),
            ('o_inv_en_qbck_c', 1),
            ('oe_qcck_t', 1),
            ('o_inv_en_qcck_t', 1),
            ('oe_qcck_c', 1),
            ('o_inv_en_qcck_c', 1),
            ('oe_qdck_t', 1),
            ('o_inv_en_qdck_t', 1),
            ('oe_qdck_c', 1),
            ('o_inv_en_qdck_c', 1)
        ]


class If_channel_config_global(Record):
    """
    This interface is used for the:
    Configuration of the B channel global settings
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            # TODO list all RWs that are global, based on the global list in definitions.
            ('Global_RWs', 1),
        ]


class If_channel_config_common(Record):
    """
    This interface is used for the:
    Configuration of the common block settings
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            # TODO add RWs, e.g. PLL control, loopback mode, error mode
            ('Common_RWs', 1),
        ]


class If_common_sdram(Record):
    """
    Channel/common signals
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('qrst_a_n', 1),
            ('qrst_b_n', 1),
        ]


class If_channel_common(Record):
    """
    Channel/common signals
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('error', 1),
            ('dlbd',  1),
            ('dlbs',  1),
        ]


class If_lb(Record):
    """
    Host/RCD loopback interface
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('lbd',    1),
            ('lbs',    1),
        ]


class If_int_lb(Record):
    """
    DFE Tap internal loopback interface
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('dca_lb',    7),
            ('dpar_lb',    1),
        ]


class If_rst_n(Record):
    """
    Global reset
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def if_assert(self):
        yield self.rst_n.eq(0)

    def if_deassert(self):
        yield self.rst_n.eq(1)

    def description(self):
        return [
            ('rst_n',    1),
        ]


class If_error(Record):
    """
    Host/RCD error interface
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('err_n', 1),
        ]


class If_ck(Record):
    """
    Clock interface
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('ck_t', 1),
            ('ck_c', 1),
        ]


class If_ctrl_pll(Record):
    """
    PLL configuration interface
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('en', 1),
            ('bypass', 1),
        ]


class If_ctrl_lb(Record):
    """
    Loopback configuration interface
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('en', 1),
            ('sel_mode', 1),
            ('sel_phase_ab', 1),
            ('sel_int_bit', 3),
        ]


class If_ctrl_err(Record):
    """
    Error configuration interface
    """

    def __init__(self):
        layout = self.description()
        Record.__init__(self, layout)

    def description(self):
        return [
            ('en', 1),
        ]

if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")
