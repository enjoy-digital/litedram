from litedram.modules import MT41J256M16
from litedram.phy import K7DDRPHY

core_config = {
    # cpu
    "cpu": "picorv32",

    # modules / phy
    "sdram_module": MT41J256M16,
    "sdram_module_nb": 2,
    "sdram_rank_nb": 1,
    "sdram_phy": K7DDRPHY,

    # electrical
    "rtt_nom": "60ohm",
    "rtt_wr": "60ohm",
    "ron": "34ohm",

    # freqs
    "input_clk_freq": 200e6,
    "sys_clk_freq": 125e6,
    "iodelay_clk_freq": 200e6,

    # controller
    "cmd_buffer_depth": 16,
    "write_time": 16,
    "read_time": 32,

    # user_ports
    "user_ports_nb": 1,
    "user_ports_type": "axi",
    "user_ports_id_width": 8
}
