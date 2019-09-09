dfii_control_sel     = 0x01
dfii_control_cke     = 0x02
dfii_control_odt     = 0x04
dfii_control_reset_n = 0x08

dfii_command_cs     = 0x01
dfii_command_we     = 0x02
dfii_command_cas    = 0x04
dfii_command_ras    = 0x08
dfii_command_wrdata = 0x10
dfii_command_rddata = 0x20

init_sequence = [
    ("Bring CKE high", 0, 0, dfii_control_cke|dfii_control_odt|dfii_control_reset_n, 20000),
    ("Precharge All", 1024, 0, dfii_command_ras|dfii_command_we|dfii_command_cs, 0),
    ("Load Mode Register / Reset DLL, CL=2, BL=1", 288, 0, dfii_command_ras|dfii_command_cas|dfii_command_we|dfii_command_cs, 200),
    ("Precharge All", 1024, 0, dfii_command_ras|dfii_command_we|dfii_command_cs, 0),
    ("Auto Refresh", 0, 0, dfii_command_ras|dfii_command_cas|dfii_command_cs, 4),
    ("Auto Refresh", 0, 0, dfii_command_ras|dfii_command_cas|dfii_command_cs, 4),
    ("Load Mode Register / CL=2, BL=1", 32, 0, dfii_command_ras|dfii_command_cas|dfii_command_we|dfii_command_cs, 200),
]
