# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

core_config = {
    # General ------------------------------------------------------------------
    "cpu":        "vexriscv",  # Type of CPU used for init/calib (vexriscv, lm32)
    "speedgrade": -1,          # FPGA speedgrade
    "memtype":    "DDR2",      # DRAM type

    # PHY ----------------------------------------------------------------------
    "cmd_delay":       0,           # Command additional delay (in taps)
    "cmd_latency":     0,           # Command additional latency
    "sdram_module":   "MT47H64M16", # SDRAM modules of the board or SO-DIMM
    "sdram_module_nb": 2,           # Number of byte groups
    "sdram_rank_nb":   1,           # Number of ranks
    "sdram_phy":      "A7DDRPHY",    # Type of FPGA PHY

    # Frequency ----------------------------------------------------------------
    "input_clk_freq":   100e6, # Input clock frequency
    "sys_clk_freq":     100e6, # System clock frequency (DDR_clk = 4 x sys_clk)
    "iodelay_clk_freq": 200e6, # IODELAYs reference clock frequency

    # Core ---------------------------------------------------------------------
    "cmd_buffer_depth": 16,    # Depth of the command buffer

    # User Ports ---------------------------------------------------------------
    "user_ports_nb":       1,     # Number of user ports
    "user_ports_type":     "axi", # Type of ports (axi, native)
    "user_ports_id_width": 6,    # AXI identifier width

    # CSR Port -----------------------------------------------------------------
    "expose_csr_port": "no", # expose access to CSR (I/O) ports
}
