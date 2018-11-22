from litedram.modules import MT41K128M16
from litedram.phy import A7DDRPHY

core_config = {
    # cpu
    "cpu": "vexriscv",
#    "cpu": None,

    # modules / phy
    "sdram_module": MT41K128M16,
    "sdram_module_nb": 1,
    "sdram_module_speedgrade": "800",
    "sdram_rank_nb": 1,
    "sdram_phy": A7DDRPHY,

    # electrical
    "rtt_nom": "60ohm",
    "rtt_wr": "60ohm",
    "ron": "34ohm",

    # freqs
    "input_clk_freq": 100e6,
    "sys_clk_freq": 100e6,
    "iodelay_clk_freq": 300e6,

    # controller
    "cmd_buffer_depth": 8,
    "write_time": 16,
    "read_time": 32,

    # user_ports
    "user_ports_nb": 2,
    "user_ports_type": "native"
}
