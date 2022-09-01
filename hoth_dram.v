/* Machine-generated using Migen */
module top(
	output interface_bank0_valid,
	input [23:0] cmd_payload_addr,
	input sys_clk,
	input sys_rst
);

reg [1:0] ddrphy_rdphase_storage = 2'd1;
reg [1:0] ddrphy_wrphase_storage = 2'd2;
wire [15:0] ddrphy_dfi_p0_address;
wire [2:0] ddrphy_dfi_p0_bank;
wire ddrphy_dfi_p0_cas_n;
wire ddrphy_dfi_p0_cs_n;
wire ddrphy_dfi_p0_ras_n;
wire ddrphy_dfi_p0_we_n;
wire ddrphy_dfi_p0_cke;
wire ddrphy_dfi_p0_odt;
wire ddrphy_dfi_p0_reset_n;
wire ddrphy_dfi_p0_act_n;
wire [63:0] ddrphy_dfi_p0_wrdata;
wire ddrphy_dfi_p0_wrdata_en;
wire [7:0] ddrphy_dfi_p0_wrdata_mask;
wire ddrphy_dfi_p0_rddata_en;
reg [63:0] ddrphy_dfi_p0_rddata = 64'd0;
reg ddrphy_dfi_p0_rddata_valid = 1'd0;
wire [15:0] ddrphy_dfi_p1_address;
wire [2:0] ddrphy_dfi_p1_bank;
wire ddrphy_dfi_p1_cas_n;
wire ddrphy_dfi_p1_cs_n;
wire ddrphy_dfi_p1_ras_n;
wire ddrphy_dfi_p1_we_n;
wire ddrphy_dfi_p1_cke;
wire ddrphy_dfi_p1_odt;
wire ddrphy_dfi_p1_reset_n;
wire ddrphy_dfi_p1_act_n;
wire [63:0] ddrphy_dfi_p1_wrdata;
wire ddrphy_dfi_p1_wrdata_en;
wire [7:0] ddrphy_dfi_p1_wrdata_mask;
wire ddrphy_dfi_p1_rddata_en;
reg [63:0] ddrphy_dfi_p1_rddata = 64'd0;
reg ddrphy_dfi_p1_rddata_valid = 1'd0;
wire [15:0] ddrphy_dfi_p2_address;
wire [2:0] ddrphy_dfi_p2_bank;
wire ddrphy_dfi_p2_cas_n;
wire ddrphy_dfi_p2_cs_n;
wire ddrphy_dfi_p2_ras_n;
wire ddrphy_dfi_p2_we_n;
wire ddrphy_dfi_p2_cke;
wire ddrphy_dfi_p2_odt;
wire ddrphy_dfi_p2_reset_n;
wire ddrphy_dfi_p2_act_n;
wire [63:0] ddrphy_dfi_p2_wrdata;
wire ddrphy_dfi_p2_wrdata_en;
wire [7:0] ddrphy_dfi_p2_wrdata_mask;
wire ddrphy_dfi_p2_rddata_en;
reg [63:0] ddrphy_dfi_p2_rddata = 64'd0;
reg ddrphy_dfi_p2_rddata_valid = 1'd0;
wire [15:0] ddrphy_dfi_p3_address;
wire [2:0] ddrphy_dfi_p3_bank;
wire ddrphy_dfi_p3_cas_n;
wire ddrphy_dfi_p3_cs_n;
wire ddrphy_dfi_p3_ras_n;
wire ddrphy_dfi_p3_we_n;
wire ddrphy_dfi_p3_cke;
wire ddrphy_dfi_p3_odt;
wire ddrphy_dfi_p3_reset_n;
wire ddrphy_dfi_p3_act_n;
wire [63:0] ddrphy_dfi_p3_wrdata;
wire ddrphy_dfi_p3_wrdata_en;
wire [7:0] ddrphy_dfi_p3_wrdata_mask;
wire ddrphy_dfi_p3_rddata_en;
reg [63:0] ddrphy_dfi_p3_rddata = 64'd0;
reg ddrphy_dfi_p3_rddata_valid = 1'd0;
wire [13:0] sdram_slave_p0_address;
wire [2:0] sdram_slave_p0_bank;
wire sdram_slave_p0_cas_n;
wire sdram_slave_p0_cs_n;
wire sdram_slave_p0_ras_n;
wire sdram_slave_p0_we_n;
wire sdram_slave_p0_cke;
wire sdram_slave_p0_odt;
wire sdram_slave_p0_reset_n;
wire sdram_slave_p0_act_n;
wire [63:0] sdram_slave_p0_wrdata;
wire sdram_slave_p0_wrdata_en;
wire [7:0] sdram_slave_p0_wrdata_mask;
wire sdram_slave_p0_rddata_en;
reg [63:0] sdram_slave_p0_rddata;
reg sdram_slave_p0_rddata_valid;
wire [13:0] sdram_slave_p1_address;
wire [2:0] sdram_slave_p1_bank;
wire sdram_slave_p1_cas_n;
wire sdram_slave_p1_cs_n;
wire sdram_slave_p1_ras_n;
wire sdram_slave_p1_we_n;
wire sdram_slave_p1_cke;
wire sdram_slave_p1_odt;
wire sdram_slave_p1_reset_n;
wire sdram_slave_p1_act_n;
wire [63:0] sdram_slave_p1_wrdata;
wire sdram_slave_p1_wrdata_en;
wire [7:0] sdram_slave_p1_wrdata_mask;
wire sdram_slave_p1_rddata_en;
reg [63:0] sdram_slave_p1_rddata;
reg sdram_slave_p1_rddata_valid;
wire [13:0] sdram_slave_p2_address;
wire [2:0] sdram_slave_p2_bank;
wire sdram_slave_p2_cas_n;
wire sdram_slave_p2_cs_n;
wire sdram_slave_p2_ras_n;
wire sdram_slave_p2_we_n;
wire sdram_slave_p2_cke;
wire sdram_slave_p2_odt;
wire sdram_slave_p2_reset_n;
wire sdram_slave_p2_act_n;
wire [63:0] sdram_slave_p2_wrdata;
wire sdram_slave_p2_wrdata_en;
wire [7:0] sdram_slave_p2_wrdata_mask;
wire sdram_slave_p2_rddata_en;
reg [63:0] sdram_slave_p2_rddata;
reg sdram_slave_p2_rddata_valid;
wire [13:0] sdram_slave_p3_address;
wire [2:0] sdram_slave_p3_bank;
wire sdram_slave_p3_cas_n;
wire sdram_slave_p3_cs_n;
wire sdram_slave_p3_ras_n;
wire sdram_slave_p3_we_n;
wire sdram_slave_p3_cke;
wire sdram_slave_p3_odt;
wire sdram_slave_p3_reset_n;
wire sdram_slave_p3_act_n;
wire [63:0] sdram_slave_p3_wrdata;
wire sdram_slave_p3_wrdata_en;
wire [7:0] sdram_slave_p3_wrdata_mask;
wire sdram_slave_p3_rddata_en;
reg [63:0] sdram_slave_p3_rddata;
reg sdram_slave_p3_rddata_valid;
wire [41:0] sdram_TMRslave_p0_address;
wire [8:0] sdram_TMRslave_p0_bank;
wire [2:0] sdram_TMRslave_p0_cas_n;
wire [2:0] sdram_TMRslave_p0_cs_n;
wire [2:0] sdram_TMRslave_p0_ras_n;
wire [2:0] sdram_TMRslave_p0_we_n;
wire [2:0] sdram_TMRslave_p0_cke;
wire [2:0] sdram_TMRslave_p0_odt;
wire [2:0] sdram_TMRslave_p0_reset_n;
wire [2:0] sdram_TMRslave_p0_act_n;
wire [191:0] sdram_TMRslave_p0_wrdata;
wire [2:0] sdram_TMRslave_p0_wrdata_en;
wire [23:0] sdram_TMRslave_p0_wrdata_mask;
wire [2:0] sdram_TMRslave_p0_rddata_en;
wire [191:0] sdram_TMRslave_p0_rddata;
wire [2:0] sdram_TMRslave_p0_rddata_valid;
wire [41:0] sdram_TMRslave_p1_address;
wire [8:0] sdram_TMRslave_p1_bank;
wire [2:0] sdram_TMRslave_p1_cas_n;
wire [2:0] sdram_TMRslave_p1_cs_n;
wire [2:0] sdram_TMRslave_p1_ras_n;
wire [2:0] sdram_TMRslave_p1_we_n;
wire [2:0] sdram_TMRslave_p1_cke;
wire [2:0] sdram_TMRslave_p1_odt;
wire [2:0] sdram_TMRslave_p1_reset_n;
wire [2:0] sdram_TMRslave_p1_act_n;
wire [191:0] sdram_TMRslave_p1_wrdata;
wire [2:0] sdram_TMRslave_p1_wrdata_en;
wire [23:0] sdram_TMRslave_p1_wrdata_mask;
wire [2:0] sdram_TMRslave_p1_rddata_en;
wire [191:0] sdram_TMRslave_p1_rddata;
wire [2:0] sdram_TMRslave_p1_rddata_valid;
wire [41:0] sdram_TMRslave_p2_address;
wire [8:0] sdram_TMRslave_p2_bank;
wire [2:0] sdram_TMRslave_p2_cas_n;
wire [2:0] sdram_TMRslave_p2_cs_n;
wire [2:0] sdram_TMRslave_p2_ras_n;
wire [2:0] sdram_TMRslave_p2_we_n;
wire [2:0] sdram_TMRslave_p2_cke;
wire [2:0] sdram_TMRslave_p2_odt;
wire [2:0] sdram_TMRslave_p2_reset_n;
wire [2:0] sdram_TMRslave_p2_act_n;
wire [191:0] sdram_TMRslave_p2_wrdata;
wire [2:0] sdram_TMRslave_p2_wrdata_en;
wire [23:0] sdram_TMRslave_p2_wrdata_mask;
wire [2:0] sdram_TMRslave_p2_rddata_en;
wire [191:0] sdram_TMRslave_p2_rddata;
wire [2:0] sdram_TMRslave_p2_rddata_valid;
wire [41:0] sdram_TMRslave_p3_address;
wire [8:0] sdram_TMRslave_p3_bank;
wire [2:0] sdram_TMRslave_p3_cas_n;
wire [2:0] sdram_TMRslave_p3_cs_n;
wire [2:0] sdram_TMRslave_p3_ras_n;
wire [2:0] sdram_TMRslave_p3_we_n;
wire [2:0] sdram_TMRslave_p3_cke;
wire [2:0] sdram_TMRslave_p3_odt;
wire [2:0] sdram_TMRslave_p3_reset_n;
wire [2:0] sdram_TMRslave_p3_act_n;
wire [191:0] sdram_TMRslave_p3_wrdata;
wire [2:0] sdram_TMRslave_p3_wrdata_en;
wire [23:0] sdram_TMRslave_p3_wrdata_mask;
wire [2:0] sdram_TMRslave_p3_rddata_en;
wire [191:0] sdram_TMRslave_p3_rddata;
wire [2:0] sdram_TMRslave_p3_rddata_valid;
reg [13:0] sdram_master_p0_address;
reg [2:0] sdram_master_p0_bank;
reg sdram_master_p0_cas_n;
reg sdram_master_p0_cs_n;
reg sdram_master_p0_ras_n;
reg sdram_master_p0_we_n;
reg sdram_master_p0_cke;
reg sdram_master_p0_odt;
reg sdram_master_p0_reset_n;
reg sdram_master_p0_act_n;
reg [63:0] sdram_master_p0_wrdata;
reg sdram_master_p0_wrdata_en;
reg [7:0] sdram_master_p0_wrdata_mask;
reg sdram_master_p0_rddata_en;
wire [63:0] sdram_master_p0_rddata;
wire sdram_master_p0_rddata_valid;
reg [13:0] sdram_master_p1_address;
reg [2:0] sdram_master_p1_bank;
reg sdram_master_p1_cas_n;
reg sdram_master_p1_cs_n;
reg sdram_master_p1_ras_n;
reg sdram_master_p1_we_n;
reg sdram_master_p1_cke;
reg sdram_master_p1_odt;
reg sdram_master_p1_reset_n;
reg sdram_master_p1_act_n;
reg [63:0] sdram_master_p1_wrdata;
reg sdram_master_p1_wrdata_en;
reg [7:0] sdram_master_p1_wrdata_mask;
reg sdram_master_p1_rddata_en;
wire [63:0] sdram_master_p1_rddata;
wire sdram_master_p1_rddata_valid;
reg [13:0] sdram_master_p2_address;
reg [2:0] sdram_master_p2_bank;
reg sdram_master_p2_cas_n;
reg sdram_master_p2_cs_n;
reg sdram_master_p2_ras_n;
reg sdram_master_p2_we_n;
reg sdram_master_p2_cke;
reg sdram_master_p2_odt;
reg sdram_master_p2_reset_n;
reg sdram_master_p2_act_n;
reg [63:0] sdram_master_p2_wrdata;
reg sdram_master_p2_wrdata_en;
reg [7:0] sdram_master_p2_wrdata_mask;
reg sdram_master_p2_rddata_en;
wire [63:0] sdram_master_p2_rddata;
wire sdram_master_p2_rddata_valid;
reg [13:0] sdram_master_p3_address;
reg [2:0] sdram_master_p3_bank;
reg sdram_master_p3_cas_n;
reg sdram_master_p3_cs_n;
reg sdram_master_p3_ras_n;
reg sdram_master_p3_we_n;
reg sdram_master_p3_cke;
reg sdram_master_p3_odt;
reg sdram_master_p3_reset_n;
reg sdram_master_p3_act_n;
reg [63:0] sdram_master_p3_wrdata;
reg sdram_master_p3_wrdata_en;
reg [7:0] sdram_master_p3_wrdata_mask;
reg sdram_master_p3_rddata_en;
wire [63:0] sdram_master_p3_rddata;
wire sdram_master_p3_rddata_valid;
wire [13:0] sdram_inti_inti_p0_address;
wire [2:0] sdram_inti_inti_p0_bank;
wire sdram_inti_inti_p0_cas_n;
wire sdram_inti_inti_p0_cs_n;
wire sdram_inti_inti_p0_ras_n;
wire sdram_inti_inti_p0_we_n;
wire sdram_inti_inti_p0_cke;
wire sdram_inti_inti_p0_odt;
wire sdram_inti_inti_p0_reset_n;
wire sdram_inti_inti_p0_act_n;
wire [63:0] sdram_inti_inti_p0_wrdata;
wire sdram_inti_inti_p0_wrdata_en;
wire [7:0] sdram_inti_inti_p0_wrdata_mask;
wire sdram_inti_inti_p0_rddata_en;
reg [63:0] sdram_inti_inti_p0_rddata;
reg sdram_inti_inti_p0_rddata_valid;
wire [13:0] sdram_inti_inti_p1_address;
wire [2:0] sdram_inti_inti_p1_bank;
wire sdram_inti_inti_p1_cas_n;
wire sdram_inti_inti_p1_cs_n;
wire sdram_inti_inti_p1_ras_n;
wire sdram_inti_inti_p1_we_n;
wire sdram_inti_inti_p1_cke;
wire sdram_inti_inti_p1_odt;
wire sdram_inti_inti_p1_reset_n;
wire sdram_inti_inti_p1_act_n;
wire [63:0] sdram_inti_inti_p1_wrdata;
wire sdram_inti_inti_p1_wrdata_en;
wire [7:0] sdram_inti_inti_p1_wrdata_mask;
wire sdram_inti_inti_p1_rddata_en;
reg [63:0] sdram_inti_inti_p1_rddata;
reg sdram_inti_inti_p1_rddata_valid;
wire [13:0] sdram_inti_inti_p2_address;
wire [2:0] sdram_inti_inti_p2_bank;
wire sdram_inti_inti_p2_cas_n;
wire sdram_inti_inti_p2_cs_n;
wire sdram_inti_inti_p2_ras_n;
wire sdram_inti_inti_p2_we_n;
wire sdram_inti_inti_p2_cke;
wire sdram_inti_inti_p2_odt;
wire sdram_inti_inti_p2_reset_n;
wire sdram_inti_inti_p2_act_n;
wire [63:0] sdram_inti_inti_p2_wrdata;
wire sdram_inti_inti_p2_wrdata_en;
wire [7:0] sdram_inti_inti_p2_wrdata_mask;
wire sdram_inti_inti_p2_rddata_en;
reg [63:0] sdram_inti_inti_p2_rddata;
reg sdram_inti_inti_p2_rddata_valid;
wire [13:0] sdram_inti_inti_p3_address;
wire [2:0] sdram_inti_inti_p3_bank;
wire sdram_inti_inti_p3_cas_n;
wire sdram_inti_inti_p3_cs_n;
wire sdram_inti_inti_p3_ras_n;
wire sdram_inti_inti_p3_we_n;
wire sdram_inti_inti_p3_cke;
wire sdram_inti_inti_p3_odt;
wire sdram_inti_inti_p3_reset_n;
wire sdram_inti_inti_p3_act_n;
wire [63:0] sdram_inti_inti_p3_wrdata;
wire sdram_inti_inti_p3_wrdata_en;
wire [7:0] sdram_inti_inti_p3_wrdata_mask;
wire sdram_inti_inti_p3_rddata_en;
reg [63:0] sdram_inti_inti_p3_rddata;
reg sdram_inti_inti_p3_rddata_valid;
reg sdram_sel = 1'd1;
reg sdram_cke = 1'd0;
reg sdram_odt = 1'd0;
reg sdram_reset_n = 1'd0;
wire [13:0] sdram_pi_mod1_inti_p0_address;
wire [2:0] sdram_pi_mod1_inti_p0_bank;
reg sdram_pi_mod1_inti_p0_cas_n;
reg sdram_pi_mod1_inti_p0_cs_n;
reg sdram_pi_mod1_inti_p0_ras_n;
reg sdram_pi_mod1_inti_p0_we_n;
wire sdram_pi_mod1_inti_p0_cke;
wire sdram_pi_mod1_inti_p0_odt;
wire sdram_pi_mod1_inti_p0_reset_n;
reg sdram_pi_mod1_inti_p0_act_n = 1'd1;
wire [63:0] sdram_pi_mod1_inti_p0_wrdata;
wire sdram_pi_mod1_inti_p0_wrdata_en;
wire [7:0] sdram_pi_mod1_inti_p0_wrdata_mask;
wire sdram_pi_mod1_inti_p0_rddata_en;
reg [63:0] sdram_pi_mod1_inti_p0_rddata;
reg sdram_pi_mod1_inti_p0_rddata_valid;
wire [13:0] sdram_pi_mod1_inti_p1_address;
wire [2:0] sdram_pi_mod1_inti_p1_bank;
reg sdram_pi_mod1_inti_p1_cas_n;
reg sdram_pi_mod1_inti_p1_cs_n;
reg sdram_pi_mod1_inti_p1_ras_n;
reg sdram_pi_mod1_inti_p1_we_n;
wire sdram_pi_mod1_inti_p1_cke;
wire sdram_pi_mod1_inti_p1_odt;
wire sdram_pi_mod1_inti_p1_reset_n;
reg sdram_pi_mod1_inti_p1_act_n = 1'd1;
wire [63:0] sdram_pi_mod1_inti_p1_wrdata;
wire sdram_pi_mod1_inti_p1_wrdata_en;
wire [7:0] sdram_pi_mod1_inti_p1_wrdata_mask;
wire sdram_pi_mod1_inti_p1_rddata_en;
reg [63:0] sdram_pi_mod1_inti_p1_rddata;
reg sdram_pi_mod1_inti_p1_rddata_valid;
wire [13:0] sdram_pi_mod1_inti_p2_address;
wire [2:0] sdram_pi_mod1_inti_p2_bank;
reg sdram_pi_mod1_inti_p2_cas_n;
reg sdram_pi_mod1_inti_p2_cs_n;
reg sdram_pi_mod1_inti_p2_ras_n;
reg sdram_pi_mod1_inti_p2_we_n;
wire sdram_pi_mod1_inti_p2_cke;
wire sdram_pi_mod1_inti_p2_odt;
wire sdram_pi_mod1_inti_p2_reset_n;
reg sdram_pi_mod1_inti_p2_act_n = 1'd1;
wire [63:0] sdram_pi_mod1_inti_p2_wrdata;
wire sdram_pi_mod1_inti_p2_wrdata_en;
wire [7:0] sdram_pi_mod1_inti_p2_wrdata_mask;
wire sdram_pi_mod1_inti_p2_rddata_en;
reg [63:0] sdram_pi_mod1_inti_p2_rddata;
reg sdram_pi_mod1_inti_p2_rddata_valid;
wire [13:0] sdram_pi_mod1_inti_p3_address;
wire [2:0] sdram_pi_mod1_inti_p3_bank;
reg sdram_pi_mod1_inti_p3_cas_n;
reg sdram_pi_mod1_inti_p3_cs_n;
reg sdram_pi_mod1_inti_p3_ras_n;
reg sdram_pi_mod1_inti_p3_we_n;
wire sdram_pi_mod1_inti_p3_cke;
wire sdram_pi_mod1_inti_p3_odt;
wire sdram_pi_mod1_inti_p3_reset_n;
reg sdram_pi_mod1_inti_p3_act_n = 1'd1;
wire [63:0] sdram_pi_mod1_inti_p3_wrdata;
wire sdram_pi_mod1_inti_p3_wrdata_en;
wire [7:0] sdram_pi_mod1_inti_p3_wrdata_mask;
wire sdram_pi_mod1_inti_p3_rddata_en;
reg [63:0] sdram_pi_mod1_inti_p3_rddata;
reg sdram_pi_mod1_inti_p3_rddata_valid;
reg [5:0] sdram_pi_mod1_phaseinjector0_command_storage = 6'd0;
reg sdram_pi_mod1_phaseinjector0_command_we;
reg sdram_pi_mod1_phaseinjector0_command_issue_re = 1'd0;
reg sdram_pi_mod1_phaseinjector0_command_issue_we = 1'd0;
reg sdram_pi_mod1_phaseinjector0_command_issue_w = 1'd0;
reg [13:0] sdram_pi_mod1_phaseinjector0_address_storage = 14'd0;
reg sdram_pi_mod1_phaseinjector0_address_we;
reg [2:0] sdram_pi_mod1_phaseinjector0_baddress_storage = 3'd0;
reg sdram_pi_mod1_phaseinjector0_baddress_we;
reg [63:0] sdram_pi_mod1_phaseinjector0_wrdata_storage = 64'd0;
reg sdram_pi_mod1_phaseinjector0_wrdata_we;
reg [63:0] sdram_pi_mod1_phaseinjector0_status = 64'd0;
reg [5:0] sdram_pi_mod1_phaseinjector1_command_storage = 6'd0;
reg sdram_pi_mod1_phaseinjector1_command_we;
reg sdram_pi_mod1_phaseinjector1_command_issue_re = 1'd0;
reg sdram_pi_mod1_phaseinjector1_command_issue_we = 1'd0;
reg sdram_pi_mod1_phaseinjector1_command_issue_w = 1'd0;
reg [13:0] sdram_pi_mod1_phaseinjector1_address_storage = 14'd0;
reg sdram_pi_mod1_phaseinjector1_address_we;
reg [2:0] sdram_pi_mod1_phaseinjector1_baddress_storage = 3'd0;
reg sdram_pi_mod1_phaseinjector1_baddress_we;
reg [63:0] sdram_pi_mod1_phaseinjector1_wrdata_storage = 64'd0;
reg sdram_pi_mod1_phaseinjector1_wrdata_we;
reg [63:0] sdram_pi_mod1_phaseinjector1_status = 64'd0;
reg [5:0] sdram_pi_mod1_phaseinjector2_command_storage = 6'd0;
reg sdram_pi_mod1_phaseinjector2_command_we;
reg sdram_pi_mod1_phaseinjector2_command_issue_re = 1'd0;
reg sdram_pi_mod1_phaseinjector2_command_issue_we = 1'd0;
reg sdram_pi_mod1_phaseinjector2_command_issue_w = 1'd0;
reg [13:0] sdram_pi_mod1_phaseinjector2_address_storage = 14'd0;
reg sdram_pi_mod1_phaseinjector2_address_we;
reg [2:0] sdram_pi_mod1_phaseinjector2_baddress_storage = 3'd0;
reg sdram_pi_mod1_phaseinjector2_baddress_we;
reg [63:0] sdram_pi_mod1_phaseinjector2_wrdata_storage = 64'd0;
reg sdram_pi_mod1_phaseinjector2_wrdata_we;
reg [63:0] sdram_pi_mod1_phaseinjector2_status = 64'd0;
reg [5:0] sdram_pi_mod1_phaseinjector3_command_storage = 6'd0;
reg sdram_pi_mod1_phaseinjector3_command_we;
reg sdram_pi_mod1_phaseinjector3_command_issue_re = 1'd0;
reg sdram_pi_mod1_phaseinjector3_command_issue_we = 1'd0;
reg sdram_pi_mod1_phaseinjector3_command_issue_w = 1'd0;
reg [13:0] sdram_pi_mod1_phaseinjector3_address_storage = 14'd0;
reg sdram_pi_mod1_phaseinjector3_address_we;
reg [2:0] sdram_pi_mod1_phaseinjector3_baddress_storage = 3'd0;
reg sdram_pi_mod1_phaseinjector3_baddress_we;
reg [63:0] sdram_pi_mod1_phaseinjector3_wrdata_storage = 64'd0;
reg sdram_pi_mod1_phaseinjector3_wrdata_we;
reg [63:0] sdram_pi_mod1_phaseinjector3_status = 64'd0;
wire [13:0] sdram_pi_mod2_inti_p0_address;
wire [2:0] sdram_pi_mod2_inti_p0_bank;
reg sdram_pi_mod2_inti_p0_cas_n;
reg sdram_pi_mod2_inti_p0_cs_n;
reg sdram_pi_mod2_inti_p0_ras_n;
reg sdram_pi_mod2_inti_p0_we_n;
wire sdram_pi_mod2_inti_p0_cke;
wire sdram_pi_mod2_inti_p0_odt;
wire sdram_pi_mod2_inti_p0_reset_n;
wire [63:0] sdram_pi_mod2_inti_p0_wrdata;
wire sdram_pi_mod2_inti_p0_wrdata_en;
wire [7:0] sdram_pi_mod2_inti_p0_wrdata_mask;
wire sdram_pi_mod2_inti_p0_rddata_en;
reg [63:0] sdram_pi_mod2_inti_p0_rddata = 64'd0;
reg sdram_pi_mod2_inti_p0_rddata_valid = 1'd0;
wire [13:0] sdram_pi_mod2_inti_p1_address;
wire [2:0] sdram_pi_mod2_inti_p1_bank;
reg sdram_pi_mod2_inti_p1_cas_n;
reg sdram_pi_mod2_inti_p1_cs_n;
reg sdram_pi_mod2_inti_p1_ras_n;
reg sdram_pi_mod2_inti_p1_we_n;
wire sdram_pi_mod2_inti_p1_cke;
wire sdram_pi_mod2_inti_p1_odt;
wire sdram_pi_mod2_inti_p1_reset_n;
wire [63:0] sdram_pi_mod2_inti_p1_wrdata;
wire sdram_pi_mod2_inti_p1_wrdata_en;
wire [7:0] sdram_pi_mod2_inti_p1_wrdata_mask;
wire sdram_pi_mod2_inti_p1_rddata_en;
reg [63:0] sdram_pi_mod2_inti_p1_rddata = 64'd0;
reg sdram_pi_mod2_inti_p1_rddata_valid = 1'd0;
wire [13:0] sdram_pi_mod2_inti_p2_address;
wire [2:0] sdram_pi_mod2_inti_p2_bank;
reg sdram_pi_mod2_inti_p2_cas_n;
reg sdram_pi_mod2_inti_p2_cs_n;
reg sdram_pi_mod2_inti_p2_ras_n;
reg sdram_pi_mod2_inti_p2_we_n;
wire sdram_pi_mod2_inti_p2_cke;
wire sdram_pi_mod2_inti_p2_odt;
wire sdram_pi_mod2_inti_p2_reset_n;
wire [63:0] sdram_pi_mod2_inti_p2_wrdata;
wire sdram_pi_mod2_inti_p2_wrdata_en;
wire [7:0] sdram_pi_mod2_inti_p2_wrdata_mask;
wire sdram_pi_mod2_inti_p2_rddata_en;
reg [63:0] sdram_pi_mod2_inti_p2_rddata = 64'd0;
reg sdram_pi_mod2_inti_p2_rddata_valid = 1'd0;
wire [13:0] sdram_pi_mod2_inti_p3_address;
wire [2:0] sdram_pi_mod2_inti_p3_bank;
reg sdram_pi_mod2_inti_p3_cas_n;
reg sdram_pi_mod2_inti_p3_cs_n;
reg sdram_pi_mod2_inti_p3_ras_n;
reg sdram_pi_mod2_inti_p3_we_n;
wire sdram_pi_mod2_inti_p3_cke;
wire sdram_pi_mod2_inti_p3_odt;
wire sdram_pi_mod2_inti_p3_reset_n;
wire [63:0] sdram_pi_mod2_inti_p3_wrdata;
wire sdram_pi_mod2_inti_p3_wrdata_en;
wire [7:0] sdram_pi_mod2_inti_p3_wrdata_mask;
wire sdram_pi_mod2_inti_p3_rddata_en;
reg [63:0] sdram_pi_mod2_inti_p3_rddata = 64'd0;
reg sdram_pi_mod2_inti_p3_rddata_valid = 1'd0;
wire [5:0] sdram_pi_mod2_phaseinjector0_command_storage;
wire sdram_pi_mod2_phaseinjector0_command_we;
wire [5:0] sdram_pi_mod2_phaseinjector0_command_dat_w;
wire sdram_pi_mod2_phaseinjector0_command_issue_re;
wire sdram_pi_mod2_phaseinjector0_command_issue_we;
wire sdram_pi_mod2_phaseinjector0_command_issue_w;
wire [13:0] sdram_pi_mod2_phaseinjector0_address_storage;
wire sdram_pi_mod2_phaseinjector0_address_we;
wire [13:0] sdram_pi_mod2_phaseinjector0_address_dat_w;
wire [2:0] sdram_pi_mod2_phaseinjector0_baddress_storage;
wire sdram_pi_mod2_phaseinjector0_baddress_we;
wire [2:0] sdram_pi_mod2_phaseinjector0_baddress_dat_w;
wire [63:0] sdram_pi_mod2_phaseinjector0_wrdata_storage;
wire sdram_pi_mod2_phaseinjector0_wrdata_we;
wire [63:0] sdram_pi_mod2_phaseinjector0_wrdata_dat_w;
reg [63:0] sdram_pi_mod2_phaseinjector0_status = 64'd0;
wire [5:0] sdram_pi_mod2_phaseinjector1_command_storage;
wire sdram_pi_mod2_phaseinjector1_command_we;
wire [5:0] sdram_pi_mod2_phaseinjector1_command_dat_w;
wire sdram_pi_mod2_phaseinjector1_command_issue_re;
wire sdram_pi_mod2_phaseinjector1_command_issue_we;
wire sdram_pi_mod2_phaseinjector1_command_issue_w;
wire [13:0] sdram_pi_mod2_phaseinjector1_address_storage;
wire sdram_pi_mod2_phaseinjector1_address_we;
wire [13:0] sdram_pi_mod2_phaseinjector1_address_dat_w;
wire [2:0] sdram_pi_mod2_phaseinjector1_baddress_storage;
wire sdram_pi_mod2_phaseinjector1_baddress_we;
wire [2:0] sdram_pi_mod2_phaseinjector1_baddress_dat_w;
wire [63:0] sdram_pi_mod2_phaseinjector1_wrdata_storage;
wire sdram_pi_mod2_phaseinjector1_wrdata_we;
wire [63:0] sdram_pi_mod2_phaseinjector1_wrdata_dat_w;
reg [63:0] sdram_pi_mod2_phaseinjector1_status = 64'd0;
wire [5:0] sdram_pi_mod2_phaseinjector2_command_storage;
wire sdram_pi_mod2_phaseinjector2_command_we;
wire [5:0] sdram_pi_mod2_phaseinjector2_command_dat_w;
wire sdram_pi_mod2_phaseinjector2_command_issue_re;
wire sdram_pi_mod2_phaseinjector2_command_issue_we;
wire sdram_pi_mod2_phaseinjector2_command_issue_w;
wire [13:0] sdram_pi_mod2_phaseinjector2_address_storage;
wire sdram_pi_mod2_phaseinjector2_address_we;
wire [13:0] sdram_pi_mod2_phaseinjector2_address_dat_w;
wire [2:0] sdram_pi_mod2_phaseinjector2_baddress_storage;
wire sdram_pi_mod2_phaseinjector2_baddress_we;
wire [2:0] sdram_pi_mod2_phaseinjector2_baddress_dat_w;
wire [63:0] sdram_pi_mod2_phaseinjector2_wrdata_storage;
wire sdram_pi_mod2_phaseinjector2_wrdata_we;
wire [63:0] sdram_pi_mod2_phaseinjector2_wrdata_dat_w;
reg [63:0] sdram_pi_mod2_phaseinjector2_status = 64'd0;
wire [5:0] sdram_pi_mod2_phaseinjector3_command_storage;
wire sdram_pi_mod2_phaseinjector3_command_we;
wire [5:0] sdram_pi_mod2_phaseinjector3_command_dat_w;
wire sdram_pi_mod2_phaseinjector3_command_issue_re;
wire sdram_pi_mod2_phaseinjector3_command_issue_we;
wire sdram_pi_mod2_phaseinjector3_command_issue_w;
wire [13:0] sdram_pi_mod2_phaseinjector3_address_storage;
wire sdram_pi_mod2_phaseinjector3_address_we;
wire [13:0] sdram_pi_mod2_phaseinjector3_address_dat_w;
wire [2:0] sdram_pi_mod2_phaseinjector3_baddress_storage;
wire sdram_pi_mod2_phaseinjector3_baddress_we;
wire [2:0] sdram_pi_mod2_phaseinjector3_baddress_dat_w;
wire [63:0] sdram_pi_mod2_phaseinjector3_wrdata_storage;
wire sdram_pi_mod2_phaseinjector3_wrdata_we;
wire [63:0] sdram_pi_mod2_phaseinjector3_wrdata_dat_w;
reg [63:0] sdram_pi_mod2_phaseinjector3_status = 64'd0;
wire [13:0] sdram_pi_mod3_inti_p0_address;
wire [2:0] sdram_pi_mod3_inti_p0_bank;
reg sdram_pi_mod3_inti_p0_cas_n;
reg sdram_pi_mod3_inti_p0_cs_n;
reg sdram_pi_mod3_inti_p0_ras_n;
reg sdram_pi_mod3_inti_p0_we_n;
wire sdram_pi_mod3_inti_p0_cke;
wire sdram_pi_mod3_inti_p0_odt;
wire sdram_pi_mod3_inti_p0_reset_n;
wire [63:0] sdram_pi_mod3_inti_p0_wrdata;
wire sdram_pi_mod3_inti_p0_wrdata_en;
wire [7:0] sdram_pi_mod3_inti_p0_wrdata_mask;
wire sdram_pi_mod3_inti_p0_rddata_en;
reg [63:0] sdram_pi_mod3_inti_p0_rddata = 64'd0;
reg sdram_pi_mod3_inti_p0_rddata_valid = 1'd0;
wire [13:0] sdram_pi_mod3_inti_p1_address;
wire [2:0] sdram_pi_mod3_inti_p1_bank;
reg sdram_pi_mod3_inti_p1_cas_n;
reg sdram_pi_mod3_inti_p1_cs_n;
reg sdram_pi_mod3_inti_p1_ras_n;
reg sdram_pi_mod3_inti_p1_we_n;
wire sdram_pi_mod3_inti_p1_cke;
wire sdram_pi_mod3_inti_p1_odt;
wire sdram_pi_mod3_inti_p1_reset_n;
wire [63:0] sdram_pi_mod3_inti_p1_wrdata;
wire sdram_pi_mod3_inti_p1_wrdata_en;
wire [7:0] sdram_pi_mod3_inti_p1_wrdata_mask;
wire sdram_pi_mod3_inti_p1_rddata_en;
reg [63:0] sdram_pi_mod3_inti_p1_rddata = 64'd0;
reg sdram_pi_mod3_inti_p1_rddata_valid = 1'd0;
wire [13:0] sdram_pi_mod3_inti_p2_address;
wire [2:0] sdram_pi_mod3_inti_p2_bank;
reg sdram_pi_mod3_inti_p2_cas_n;
reg sdram_pi_mod3_inti_p2_cs_n;
reg sdram_pi_mod3_inti_p2_ras_n;
reg sdram_pi_mod3_inti_p2_we_n;
wire sdram_pi_mod3_inti_p2_cke;
wire sdram_pi_mod3_inti_p2_odt;
wire sdram_pi_mod3_inti_p2_reset_n;
wire [63:0] sdram_pi_mod3_inti_p2_wrdata;
wire sdram_pi_mod3_inti_p2_wrdata_en;
wire [7:0] sdram_pi_mod3_inti_p2_wrdata_mask;
wire sdram_pi_mod3_inti_p2_rddata_en;
reg [63:0] sdram_pi_mod3_inti_p2_rddata = 64'd0;
reg sdram_pi_mod3_inti_p2_rddata_valid = 1'd0;
wire [13:0] sdram_pi_mod3_inti_p3_address;
wire [2:0] sdram_pi_mod3_inti_p3_bank;
reg sdram_pi_mod3_inti_p3_cas_n;
reg sdram_pi_mod3_inti_p3_cs_n;
reg sdram_pi_mod3_inti_p3_ras_n;
reg sdram_pi_mod3_inti_p3_we_n;
wire sdram_pi_mod3_inti_p3_cke;
wire sdram_pi_mod3_inti_p3_odt;
wire sdram_pi_mod3_inti_p3_reset_n;
wire [63:0] sdram_pi_mod3_inti_p3_wrdata;
wire sdram_pi_mod3_inti_p3_wrdata_en;
wire [7:0] sdram_pi_mod3_inti_p3_wrdata_mask;
wire sdram_pi_mod3_inti_p3_rddata_en;
reg [63:0] sdram_pi_mod3_inti_p3_rddata = 64'd0;
reg sdram_pi_mod3_inti_p3_rddata_valid = 1'd0;
wire [5:0] sdram_pi_mod3_phaseinjector0_command_storage;
wire sdram_pi_mod3_phaseinjector0_command_we;
wire [5:0] sdram_pi_mod3_phaseinjector0_command_dat_w;
wire sdram_pi_mod3_phaseinjector0_command_issue_re;
wire sdram_pi_mod3_phaseinjector0_command_issue_we;
wire sdram_pi_mod3_phaseinjector0_command_issue_w;
wire [13:0] sdram_pi_mod3_phaseinjector0_address_storage;
wire sdram_pi_mod3_phaseinjector0_address_we;
wire [13:0] sdram_pi_mod3_phaseinjector0_address_dat_w;
wire [2:0] sdram_pi_mod3_phaseinjector0_baddress_storage;
wire sdram_pi_mod3_phaseinjector0_baddress_we;
wire [2:0] sdram_pi_mod3_phaseinjector0_baddress_dat_w;
wire [63:0] sdram_pi_mod3_phaseinjector0_wrdata_storage;
wire sdram_pi_mod3_phaseinjector0_wrdata_we;
wire [63:0] sdram_pi_mod3_phaseinjector0_wrdata_dat_w;
reg [63:0] sdram_pi_mod3_phaseinjector0_status = 64'd0;
wire [5:0] sdram_pi_mod3_phaseinjector1_command_storage;
wire sdram_pi_mod3_phaseinjector1_command_we;
wire [5:0] sdram_pi_mod3_phaseinjector1_command_dat_w;
wire sdram_pi_mod3_phaseinjector1_command_issue_re;
wire sdram_pi_mod3_phaseinjector1_command_issue_we;
wire sdram_pi_mod3_phaseinjector1_command_issue_w;
wire [13:0] sdram_pi_mod3_phaseinjector1_address_storage;
wire sdram_pi_mod3_phaseinjector1_address_we;
wire [13:0] sdram_pi_mod3_phaseinjector1_address_dat_w;
wire [2:0] sdram_pi_mod3_phaseinjector1_baddress_storage;
wire sdram_pi_mod3_phaseinjector1_baddress_we;
wire [2:0] sdram_pi_mod3_phaseinjector1_baddress_dat_w;
wire [63:0] sdram_pi_mod3_phaseinjector1_wrdata_storage;
wire sdram_pi_mod3_phaseinjector1_wrdata_we;
wire [63:0] sdram_pi_mod3_phaseinjector1_wrdata_dat_w;
reg [63:0] sdram_pi_mod3_phaseinjector1_status = 64'd0;
wire [5:0] sdram_pi_mod3_phaseinjector2_command_storage;
wire sdram_pi_mod3_phaseinjector2_command_we;
wire [5:0] sdram_pi_mod3_phaseinjector2_command_dat_w;
wire sdram_pi_mod3_phaseinjector2_command_issue_re;
wire sdram_pi_mod3_phaseinjector2_command_issue_we;
wire sdram_pi_mod3_phaseinjector2_command_issue_w;
wire [13:0] sdram_pi_mod3_phaseinjector2_address_storage;
wire sdram_pi_mod3_phaseinjector2_address_we;
wire [13:0] sdram_pi_mod3_phaseinjector2_address_dat_w;
wire [2:0] sdram_pi_mod3_phaseinjector2_baddress_storage;
wire sdram_pi_mod3_phaseinjector2_baddress_we;
wire [2:0] sdram_pi_mod3_phaseinjector2_baddress_dat_w;
wire [63:0] sdram_pi_mod3_phaseinjector2_wrdata_storage;
wire sdram_pi_mod3_phaseinjector2_wrdata_we;
wire [63:0] sdram_pi_mod3_phaseinjector2_wrdata_dat_w;
reg [63:0] sdram_pi_mod3_phaseinjector2_status = 64'd0;
wire [5:0] sdram_pi_mod3_phaseinjector3_command_storage;
wire sdram_pi_mod3_phaseinjector3_command_we;
wire [5:0] sdram_pi_mod3_phaseinjector3_command_dat_w;
wire sdram_pi_mod3_phaseinjector3_command_issue_re;
wire sdram_pi_mod3_phaseinjector3_command_issue_we;
wire sdram_pi_mod3_phaseinjector3_command_issue_w;
wire [13:0] sdram_pi_mod3_phaseinjector3_address_storage;
wire sdram_pi_mod3_phaseinjector3_address_we;
wire [13:0] sdram_pi_mod3_phaseinjector3_address_dat_w;
wire [2:0] sdram_pi_mod3_phaseinjector3_baddress_storage;
wire sdram_pi_mod3_phaseinjector3_baddress_we;
wire [2:0] sdram_pi_mod3_phaseinjector3_baddress_dat_w;
wire [63:0] sdram_pi_mod3_phaseinjector3_wrdata_storage;
wire sdram_pi_mod3_phaseinjector3_wrdata_we;
wire [63:0] sdram_pi_mod3_phaseinjector3_wrdata_dat_w;
reg [63:0] sdram_pi_mod3_phaseinjector3_status = 64'd0;
wire [13:0] sdram_control0;
wire [2:0] sdram_control1;
wire sdram_control2;
wire sdram_control3;
wire sdram_control4;
wire sdram_control5;
wire sdram_control6;
wire sdram_control7;
wire sdram_control8;
wire sdram_control9;
wire [63:0] sdram_control10;
wire sdram_control11;
wire [7:0] sdram_control12;
wire sdram_control13;
wire [13:0] sdram_control14;
wire [2:0] sdram_control15;
wire sdram_control16;
wire sdram_control17;
wire sdram_control18;
wire sdram_control19;
wire sdram_control20;
wire sdram_control21;
wire sdram_control22;
wire sdram_control23;
wire [63:0] sdram_control24;
wire sdram_control25;
wire [7:0] sdram_control26;
wire sdram_control27;
wire [13:0] sdram_control28;
wire [2:0] sdram_control29;
wire sdram_control30;
wire sdram_control31;
wire sdram_control32;
wire sdram_control33;
wire sdram_control34;
wire sdram_control35;
wire sdram_control36;
wire sdram_control37;
wire [63:0] sdram_control38;
wire sdram_control39;
wire [7:0] sdram_control40;
wire sdram_control41;
wire [13:0] sdram_control42;
wire [2:0] sdram_control43;
wire sdram_control44;
wire sdram_control45;
wire sdram_control46;
wire sdram_control47;
wire sdram_control48;
wire sdram_control49;
wire sdram_control50;
wire sdram_control51;
wire [63:0] sdram_control52;
wire sdram_control53;
wire [7:0] sdram_control54;
wire sdram_control55;
wire [13:0] sdram_control56;
wire [2:0] sdram_control57;
wire sdram_control58;
wire sdram_control59;
wire sdram_control60;
wire sdram_control61;
wire sdram_control62;
wire sdram_control63;
wire sdram_control64;
wire sdram_control65;
wire [63:0] sdram_control66;
wire sdram_control67;
wire [7:0] sdram_control68;
wire sdram_control69;
wire [13:0] sdram_control70;
wire [2:0] sdram_control71;
wire sdram_control72;
wire sdram_control73;
wire sdram_control74;
wire sdram_control75;
wire sdram_control76;
wire sdram_control77;
wire sdram_control78;
wire sdram_control79;
wire [63:0] sdram_control80;
wire sdram_control81;
wire [7:0] sdram_control82;
wire sdram_control83;
wire [13:0] sdram_control84;
wire [2:0] sdram_control85;
wire sdram_control86;
wire sdram_control87;
wire sdram_control88;
wire sdram_control89;
wire sdram_control90;
wire sdram_control91;
wire sdram_control92;
wire sdram_control93;
wire [63:0] sdram_control94;
wire sdram_control95;
wire [7:0] sdram_control96;
wire sdram_control97;
wire [13:0] sdram_control98;
wire [2:0] sdram_control99;
wire sdram_control100;
wire sdram_control101;
wire sdram_control102;
wire sdram_control103;
wire sdram_control104;
wire sdram_control105;
wire sdram_control106;
wire sdram_control107;
wire [63:0] sdram_control108;
wire sdram_control109;
wire [7:0] sdram_control110;
wire sdram_control111;
wire sdram_interface_bank0_ready;
wire sdram_interface_bank0_we;
wire [20:0] sdram_interface_bank0_addr;
wire sdram_interface_bank0_lock;
wire sdram_interface_bank0_wdata_ready;
wire sdram_interface_bank0_rdata_valid;
wire sdram_interface_bank1_valid;
wire sdram_interface_bank1_ready;
wire sdram_interface_bank1_we;
wire [20:0] sdram_interface_bank1_addr;
wire sdram_interface_bank1_lock;
wire sdram_interface_bank1_wdata_ready;
wire sdram_interface_bank1_rdata_valid;
wire sdram_interface_bank2_valid;
wire sdram_interface_bank2_ready;
wire sdram_interface_bank2_we;
wire [20:0] sdram_interface_bank2_addr;
wire sdram_interface_bank2_lock;
wire sdram_interface_bank2_wdata_ready;
wire sdram_interface_bank2_rdata_valid;
wire sdram_interface_bank3_valid;
wire sdram_interface_bank3_ready;
wire sdram_interface_bank3_we;
wire [20:0] sdram_interface_bank3_addr;
wire sdram_interface_bank3_lock;
wire sdram_interface_bank3_wdata_ready;
wire sdram_interface_bank3_rdata_valid;
wire sdram_interface_bank4_valid;
wire sdram_interface_bank4_ready;
wire sdram_interface_bank4_we;
wire [20:0] sdram_interface_bank4_addr;
wire sdram_interface_bank4_lock;
wire sdram_interface_bank4_wdata_ready;
wire sdram_interface_bank4_rdata_valid;
wire sdram_interface_bank5_valid;
wire sdram_interface_bank5_ready;
wire sdram_interface_bank5_we;
wire [20:0] sdram_interface_bank5_addr;
wire sdram_interface_bank5_lock;
wire sdram_interface_bank5_wdata_ready;
wire sdram_interface_bank5_rdata_valid;
wire sdram_interface_bank6_valid;
wire sdram_interface_bank6_ready;
wire sdram_interface_bank6_we;
wire [20:0] sdram_interface_bank6_addr;
wire sdram_interface_bank6_lock;
wire sdram_interface_bank6_wdata_ready;
wire sdram_interface_bank6_rdata_valid;
wire sdram_interface_bank7_valid;
wire sdram_interface_bank7_ready;
wire sdram_interface_bank7_we;
wire [20:0] sdram_interface_bank7_addr;
wire sdram_interface_bank7_lock;
wire sdram_interface_bank7_wdata_ready;
wire sdram_interface_bank7_rdata_valid;
wire [2:0] sdram_TMRinterface_bank0_valid;
wire [2:0] sdram_TMRinterface_bank0_ready;
wire [2:0] sdram_TMRinterface_bank0_we;
wire [62:0] sdram_TMRinterface_bank0_addr;
wire [2:0] sdram_TMRinterface_bank0_lock;
wire [2:0] sdram_TMRinterface_bank0_wdata_ready;
wire [2:0] sdram_TMRinterface_bank0_rdata_valid;
wire [2:0] sdram_TMRinterface_bank1_valid;
wire [2:0] sdram_TMRinterface_bank1_ready;
wire [2:0] sdram_TMRinterface_bank1_we;
wire [62:0] sdram_TMRinterface_bank1_addr;
wire [2:0] sdram_TMRinterface_bank1_lock;
wire [2:0] sdram_TMRinterface_bank1_wdata_ready;
wire [2:0] sdram_TMRinterface_bank1_rdata_valid;
wire [2:0] sdram_TMRinterface_bank2_valid;
wire [2:0] sdram_TMRinterface_bank2_ready;
wire [2:0] sdram_TMRinterface_bank2_we;
wire [62:0] sdram_TMRinterface_bank2_addr;
wire [2:0] sdram_TMRinterface_bank2_lock;
wire [2:0] sdram_TMRinterface_bank2_wdata_ready;
wire [2:0] sdram_TMRinterface_bank2_rdata_valid;
wire [2:0] sdram_TMRinterface_bank3_valid;
wire [2:0] sdram_TMRinterface_bank3_ready;
wire [2:0] sdram_TMRinterface_bank3_we;
wire [62:0] sdram_TMRinterface_bank3_addr;
wire [2:0] sdram_TMRinterface_bank3_lock;
wire [2:0] sdram_TMRinterface_bank3_wdata_ready;
wire [2:0] sdram_TMRinterface_bank3_rdata_valid;
wire [2:0] sdram_TMRinterface_bank4_valid;
wire [2:0] sdram_TMRinterface_bank4_ready;
wire [2:0] sdram_TMRinterface_bank4_we;
wire [62:0] sdram_TMRinterface_bank4_addr;
wire [2:0] sdram_TMRinterface_bank4_lock;
wire [2:0] sdram_TMRinterface_bank4_wdata_ready;
wire [2:0] sdram_TMRinterface_bank4_rdata_valid;
wire [2:0] sdram_TMRinterface_bank5_valid;
wire [2:0] sdram_TMRinterface_bank5_ready;
wire [2:0] sdram_TMRinterface_bank5_we;
wire [62:0] sdram_TMRinterface_bank5_addr;
wire [2:0] sdram_TMRinterface_bank5_lock;
wire [2:0] sdram_TMRinterface_bank5_wdata_ready;
wire [2:0] sdram_TMRinterface_bank5_rdata_valid;
wire [2:0] sdram_TMRinterface_bank6_valid;
wire [2:0] sdram_TMRinterface_bank6_ready;
wire [2:0] sdram_TMRinterface_bank6_we;
wire [62:0] sdram_TMRinterface_bank6_addr;
wire [2:0] sdram_TMRinterface_bank6_lock;
wire [2:0] sdram_TMRinterface_bank6_wdata_ready;
wire [2:0] sdram_TMRinterface_bank6_rdata_valid;
wire [2:0] sdram_TMRinterface_bank7_valid;
wire [2:0] sdram_TMRinterface_bank7_ready;
wire [2:0] sdram_TMRinterface_bank7_we;
wire [62:0] sdram_TMRinterface_bank7_addr;
wire [2:0] sdram_TMRinterface_bank7_lock;
wire [2:0] sdram_TMRinterface_bank7_wdata_ready;
wire [2:0] sdram_TMRinterface_bank7_rdata_valid;
reg [767:0] sdram_TMRinterface_wdata;
reg [95:0] sdram_TMRinterface_wdata_we;
wire [767:0] sdram_TMRinterface_rdata;
reg [13:0] sdram_dfi_p0_address = 14'd0;
reg [2:0] sdram_dfi_p0_bank = 3'd0;
reg sdram_dfi_p0_cas_n = 1'd1;
reg sdram_dfi_p0_cs_n = 1'd1;
reg sdram_dfi_p0_ras_n = 1'd1;
reg sdram_dfi_p0_we_n = 1'd1;
wire sdram_dfi_p0_cke;
wire sdram_dfi_p0_odt;
wire sdram_dfi_p0_reset_n;
reg sdram_dfi_p0_act_n = 1'd1;
wire [63:0] sdram_dfi_p0_wrdata;
reg sdram_dfi_p0_wrdata_en = 1'd0;
wire [7:0] sdram_dfi_p0_wrdata_mask;
reg sdram_dfi_p0_rddata_en = 1'd0;
wire [63:0] sdram_dfi_p0_rddata;
wire sdram_dfi_p0_rddata_valid;
reg [13:0] sdram_dfi_p1_address = 14'd0;
reg [2:0] sdram_dfi_p1_bank = 3'd0;
reg sdram_dfi_p1_cas_n = 1'd1;
reg sdram_dfi_p1_cs_n = 1'd1;
reg sdram_dfi_p1_ras_n = 1'd1;
reg sdram_dfi_p1_we_n = 1'd1;
wire sdram_dfi_p1_cke;
wire sdram_dfi_p1_odt;
wire sdram_dfi_p1_reset_n;
reg sdram_dfi_p1_act_n = 1'd1;
wire [63:0] sdram_dfi_p1_wrdata;
reg sdram_dfi_p1_wrdata_en = 1'd0;
wire [7:0] sdram_dfi_p1_wrdata_mask;
reg sdram_dfi_p1_rddata_en = 1'd0;
wire [63:0] sdram_dfi_p1_rddata;
wire sdram_dfi_p1_rddata_valid;
reg [13:0] sdram_dfi_p2_address = 14'd0;
reg [2:0] sdram_dfi_p2_bank = 3'd0;
reg sdram_dfi_p2_cas_n = 1'd1;
reg sdram_dfi_p2_cs_n = 1'd1;
reg sdram_dfi_p2_ras_n = 1'd1;
reg sdram_dfi_p2_we_n = 1'd1;
wire sdram_dfi_p2_cke;
wire sdram_dfi_p2_odt;
wire sdram_dfi_p2_reset_n;
reg sdram_dfi_p2_act_n = 1'd1;
wire [63:0] sdram_dfi_p2_wrdata;
reg sdram_dfi_p2_wrdata_en = 1'd0;
wire [7:0] sdram_dfi_p2_wrdata_mask;
reg sdram_dfi_p2_rddata_en = 1'd0;
wire [63:0] sdram_dfi_p2_rddata;
wire sdram_dfi_p2_rddata_valid;
reg [13:0] sdram_dfi_p3_address = 14'd0;
reg [2:0] sdram_dfi_p3_bank = 3'd0;
reg sdram_dfi_p3_cas_n = 1'd1;
reg sdram_dfi_p3_cs_n = 1'd1;
reg sdram_dfi_p3_ras_n = 1'd1;
reg sdram_dfi_p3_we_n = 1'd1;
wire sdram_dfi_p3_cke;
wire sdram_dfi_p3_odt;
wire sdram_dfi_p3_reset_n;
reg sdram_dfi_p3_act_n = 1'd1;
wire [63:0] sdram_dfi_p3_wrdata;
reg sdram_dfi_p3_wrdata_en = 1'd0;
wire [7:0] sdram_dfi_p3_wrdata_mask;
reg sdram_dfi_p3_rddata_en = 1'd0;
wire [63:0] sdram_dfi_p3_rddata;
wire sdram_dfi_p3_rddata_valid;
wire [41:0] sdram_TMRdfi_p0_address;
wire [8:0] sdram_TMRdfi_p0_bank;
wire [2:0] sdram_TMRdfi_p0_cas_n;
wire [2:0] sdram_TMRdfi_p0_cs_n;
wire [2:0] sdram_TMRdfi_p0_ras_n;
wire [2:0] sdram_TMRdfi_p0_we_n;
wire [2:0] sdram_TMRdfi_p0_cke;
wire [2:0] sdram_TMRdfi_p0_odt;
wire [2:0] sdram_TMRdfi_p0_reset_n;
wire [2:0] sdram_TMRdfi_p0_act_n;
wire [191:0] sdram_TMRdfi_p0_wrdata;
wire [2:0] sdram_TMRdfi_p0_wrdata_en;
wire [23:0] sdram_TMRdfi_p0_wrdata_mask;
wire [2:0] sdram_TMRdfi_p0_rddata_en;
wire [191:0] sdram_TMRdfi_p0_rddata;
wire [2:0] sdram_TMRdfi_p0_rddata_valid;
wire [41:0] sdram_TMRdfi_p1_address;
wire [8:0] sdram_TMRdfi_p1_bank;
wire [2:0] sdram_TMRdfi_p1_cas_n;
wire [2:0] sdram_TMRdfi_p1_cs_n;
wire [2:0] sdram_TMRdfi_p1_ras_n;
wire [2:0] sdram_TMRdfi_p1_we_n;
wire [2:0] sdram_TMRdfi_p1_cke;
wire [2:0] sdram_TMRdfi_p1_odt;
wire [2:0] sdram_TMRdfi_p1_reset_n;
wire [2:0] sdram_TMRdfi_p1_act_n;
wire [191:0] sdram_TMRdfi_p1_wrdata;
wire [2:0] sdram_TMRdfi_p1_wrdata_en;
wire [23:0] sdram_TMRdfi_p1_wrdata_mask;
wire [2:0] sdram_TMRdfi_p1_rddata_en;
wire [191:0] sdram_TMRdfi_p1_rddata;
wire [2:0] sdram_TMRdfi_p1_rddata_valid;
wire [41:0] sdram_TMRdfi_p2_address;
wire [8:0] sdram_TMRdfi_p2_bank;
wire [2:0] sdram_TMRdfi_p2_cas_n;
wire [2:0] sdram_TMRdfi_p2_cs_n;
wire [2:0] sdram_TMRdfi_p2_ras_n;
wire [2:0] sdram_TMRdfi_p2_we_n;
wire [2:0] sdram_TMRdfi_p2_cke;
wire [2:0] sdram_TMRdfi_p2_odt;
wire [2:0] sdram_TMRdfi_p2_reset_n;
wire [2:0] sdram_TMRdfi_p2_act_n;
wire [191:0] sdram_TMRdfi_p2_wrdata;
wire [2:0] sdram_TMRdfi_p2_wrdata_en;
wire [23:0] sdram_TMRdfi_p2_wrdata_mask;
wire [2:0] sdram_TMRdfi_p2_rddata_en;
wire [191:0] sdram_TMRdfi_p2_rddata;
wire [2:0] sdram_TMRdfi_p2_rddata_valid;
wire [41:0] sdram_TMRdfi_p3_address;
wire [8:0] sdram_TMRdfi_p3_bank;
wire [2:0] sdram_TMRdfi_p3_cas_n;
wire [2:0] sdram_TMRdfi_p3_cs_n;
wire [2:0] sdram_TMRdfi_p3_ras_n;
wire [2:0] sdram_TMRdfi_p3_we_n;
wire [2:0] sdram_TMRdfi_p3_cke;
wire [2:0] sdram_TMRdfi_p3_odt;
wire [2:0] sdram_TMRdfi_p3_reset_n;
wire [2:0] sdram_TMRdfi_p3_act_n;
wire [191:0] sdram_TMRdfi_p3_wrdata;
wire [2:0] sdram_TMRdfi_p3_wrdata_en;
wire [23:0] sdram_TMRdfi_p3_wrdata_mask;
wire [2:0] sdram_TMRdfi_p3_rddata_en;
wire [191:0] sdram_TMRdfi_p3_rddata;
wire [2:0] sdram_TMRdfi_p3_rddata_valid;
wire [63:0] sdram_tmrinput_control0;
wire sdram_tmrinput_control1;
wire [63:0] sdram_tmrinput_control2;
wire sdram_tmrinput_control3;
wire [63:0] sdram_tmrinput_control4;
wire sdram_tmrinput_control5;
wire [63:0] sdram_tmrinput_control6;
wire sdram_tmrinput_control7;
reg sdram_cmd_valid;
wire sdram_cmd_ready;
reg sdram_cmd_first = 1'd0;
reg sdram_cmd_last;
reg [13:0] sdram_cmd_payload_a = 14'd0;
reg [2:0] sdram_cmd_payload_ba = 3'd0;
reg sdram_cmd_payload_cas = 1'd0;
reg sdram_cmd_payload_ras = 1'd0;
reg sdram_cmd_payload_we = 1'd0;
reg sdram_cmd_payload_is_cmd = 1'd0;
reg sdram_cmd_payload_is_read = 1'd0;
reg sdram_cmd_payload_is_write = 1'd0;
wire [2:0] sdram_TMRcmd_valid;
wire [2:0] sdram_TMRcmd_ready;
wire [2:0] sdram_TMRcmd_first;
wire [2:0] sdram_TMRcmd_last;
wire [41:0] sdram_TMRcmd_payload_a;
wire [8:0] sdram_TMRcmd_payload_ba;
wire [2:0] sdram_TMRcmd_payload_cas;
wire [2:0] sdram_TMRcmd_payload_ras;
wire [2:0] sdram_TMRcmd_payload_we;
wire [2:0] sdram_TMRcmd_payload_is_cmd;
wire [2:0] sdram_TMRcmd_payload_is_read;
wire [2:0] sdram_TMRcmd_payload_is_write;
wire sdram_tmrinput_control8;
wire sdram_wants_refresh;
wire sdram_wants_zqcs;
wire sdram_timer_wait;
wire sdram_timer_done0;
wire [9:0] sdram_timer_count0;
wire sdram_timer_done1;
reg [9:0] sdram_timer_count1 = 10'd976;
wire sdram_timer2_wait;
wire sdram_timer2_done0;
wire [9:0] sdram_timer2_count0;
wire sdram_timer2_done1;
reg [9:0] sdram_timer2_count1 = 10'd976;
wire sdram_timer3_wait;
wire sdram_timer3_done0;
wire [9:0] sdram_timer3_count0;
wire sdram_timer3_done1;
reg [9:0] sdram_timer3_count1 = 10'd976;
wire sdram_timerVote_control;
wire sdram_postponer_req_i;
reg sdram_postponer_req_o = 1'd0;
reg sdram_postponer_count = 1'd0;
wire sdram_postponer2_req_i;
reg sdram_postponer2_req_o = 1'd0;
reg sdram_postponer2_count = 1'd0;
wire sdram_postponer3_req_i;
reg sdram_postponer3_req_o = 1'd0;
reg sdram_postponer3_count = 1'd0;
wire sdram_postponeVote_control;
reg sdram_cmd1_ready = 1'd0;
reg [13:0] sdram_cmd1_payload_a = 14'd0;
reg [2:0] sdram_cmd1_payload_ba = 3'd0;
reg sdram_cmd1_payload_cas = 1'd0;
reg sdram_cmd1_payload_ras = 1'd0;
reg sdram_cmd1_payload_we = 1'd0;
reg sdram_sequencer_start0;
wire sdram_sequencer_done0;
wire sdram_sequencer_start1;
reg sdram_sequencer_done1 = 1'd0;
reg [5:0] sdram_sequencer_counter = 6'd0;
reg sdram_sequencer_count = 1'd0;
reg sdram_cmd2_ready = 1'd0;
reg [13:0] sdram_cmd2_payload_a = 14'd0;
reg [2:0] sdram_cmd2_payload_ba = 3'd0;
reg sdram_cmd2_payload_cas = 1'd0;
reg sdram_cmd2_payload_ras = 1'd0;
reg sdram_cmd2_payload_we = 1'd0;
reg sdram_sequencer2_start0;
wire sdram_sequencer2_done0;
wire sdram_sequencer2_start1;
reg sdram_sequencer2_done1 = 1'd0;
reg [5:0] sdram_sequencer2_counter = 6'd0;
reg sdram_sequencer2_count = 1'd0;
reg sdram_cmd3_ready = 1'd0;
reg [13:0] sdram_cmd3_payload_a = 14'd0;
reg [2:0] sdram_cmd3_payload_ba = 3'd0;
reg sdram_cmd3_payload_cas = 1'd0;
reg sdram_cmd3_payload_ras = 1'd0;
reg sdram_cmd3_payload_we = 1'd0;
reg sdram_sequencer3_start0;
wire sdram_sequencer3_done0;
wire sdram_sequencer3_start1;
reg sdram_sequencer3_done1 = 1'd0;
reg [5:0] sdram_sequencer3_counter = 6'd0;
reg sdram_sequencer3_count = 1'd0;
reg sdram_tmrrefresher_control0 = 1'd0;
reg sdram_tmrrefresher_control1 = 1'd0;
reg sdram_tmrrefresher_control2 = 1'd0;
reg [13:0] sdram_tmrrefresher_control3 = 14'd0;
reg [2:0] sdram_tmrrefresher_control4 = 3'd0;
reg sdram_tmrrefresher_control5 = 1'd0;
reg sdram_tmrrefresher_control6 = 1'd0;
reg sdram_tmrrefresher_control7 = 1'd0;
reg sdram_tmrrefresher_control8 = 1'd0;
reg sdram_tmrrefresher_control9 = 1'd0;
reg sdram_tmrrefresher_control10 = 1'd0;
wire sdram_sequenceVote_control;
wire sdram_zqcs_timer_wait;
wire sdram_zqcs_timer_done0;
wire [26:0] sdram_zqcs_timer_count0;
wire sdram_zqcs_timer_done1;
reg [26:0] sdram_zqcs_timer_count1 = 27'd124999999;
reg sdram_zqcs_executer_start;
reg sdram_zqcs_executer_done = 1'd0;
reg [4:0] sdram_zqcs_executer_counter = 5'd0;
wire sdram_tmrbankmachine0_req_valid;
wire sdram_tmrbankmachine0_req_ready;
wire sdram_tmrbankmachine0_req_we;
wire [20:0] sdram_tmrbankmachine0_req_addr;
reg sdram_tmrbankmachine0_req_lock;
reg sdram_tmrbankmachine0_req_wdata_ready;
reg sdram_tmrbankmachine0_req_rdata_valid;
wire [2:0] sdram_tmrbankmachine0_TMRreq_valid;
wire [2:0] sdram_tmrbankmachine0_TMRreq_ready;
wire [2:0] sdram_tmrbankmachine0_TMRreq_we;
wire [62:0] sdram_tmrbankmachine0_TMRreq_addr;
wire [2:0] sdram_tmrbankmachine0_TMRreq_lock;
wire [2:0] sdram_tmrbankmachine0_TMRreq_wdata_ready;
wire [2:0] sdram_tmrbankmachine0_TMRreq_rdata_valid;
wire sdram_tmrbankmachine0_refresh_req;
reg sdram_tmrbankmachine0_refresh_gnt;
reg sdram_tmrbankmachine0_cmd_valid;
wire sdram_tmrbankmachine0_cmd_ready;
reg sdram_tmrbankmachine0_cmd_first = 1'd0;
reg sdram_tmrbankmachine0_cmd_last = 1'd0;
reg [13:0] sdram_tmrbankmachine0_cmd_payload_a;
wire [2:0] sdram_tmrbankmachine0_cmd_payload_ba;
reg sdram_tmrbankmachine0_cmd_payload_cas;
reg sdram_tmrbankmachine0_cmd_payload_ras;
reg sdram_tmrbankmachine0_cmd_payload_we;
reg sdram_tmrbankmachine0_cmd_payload_is_cmd;
reg sdram_tmrbankmachine0_cmd_payload_is_read;
reg sdram_tmrbankmachine0_cmd_payload_is_write;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_valid;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_ready;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_first;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_last;
wire [41:0] sdram_tmrbankmachine0_TMRcmd_payload_a;
wire [8:0] sdram_tmrbankmachine0_TMRcmd_payload_ba;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_payload_cas;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_payload_ras;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_payload_we;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_payload_is_cmd;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_payload_is_read;
wire [2:0] sdram_tmrbankmachine0_TMRcmd_payload_is_write;
wire sdram_tmrbankmachine0_tmrinput_control0;
reg sdram_tmrbankmachine0_auto_precharge;
wire sdram_tmrbankmachine0_tmrinput_control1;
wire sdram_tmrbankmachine0_tmrinput_control2;
wire [20:0] sdram_tmrbankmachine0_tmrinput_control3;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_valid;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_ready;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_first = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_last = 1'd0;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_source_ready;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_source_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_source_last;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_we;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_writable;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_re;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_readable;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_din;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_dout;
reg [3:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_level = 4'd0;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_adr;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_dat_r;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_we;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_dat_w;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_do_read;
wire [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_rdport_adr;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_rdport_dat_r;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_last;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_last;
wire sdram_tmrbankmachine0_cmd_buffer_sink_valid;
wire sdram_tmrbankmachine0_cmd_buffer_sink_ready;
wire sdram_tmrbankmachine0_cmd_buffer_sink_first;
wire sdram_tmrbankmachine0_cmd_buffer_sink_last;
wire sdram_tmrbankmachine0_cmd_buffer_sink_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_sink_payload_addr;
reg sdram_tmrbankmachine0_cmd_buffer_source_valid = 1'd0;
wire sdram_tmrbankmachine0_cmd_buffer_source_ready;
reg sdram_tmrbankmachine0_cmd_buffer_source_first = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer_source_last = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine0_cmd_buffer_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_valid;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_ready;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_first = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_last = 1'd0;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_ready;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_last;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_we;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_writable;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_re;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_readable;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_din;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_dout;
reg [3:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_level = 4'd0;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_adr;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_dat_r;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_we;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_dat_w;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_do_read;
wire [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_rdport_adr;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_rdport_dat_r;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_last;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_last;
wire sdram_tmrbankmachine0_cmd_buffer2_sink_valid;
wire sdram_tmrbankmachine0_cmd_buffer2_sink_ready;
wire sdram_tmrbankmachine0_cmd_buffer2_sink_first;
wire sdram_tmrbankmachine0_cmd_buffer2_sink_last;
wire sdram_tmrbankmachine0_cmd_buffer2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer2_sink_payload_addr;
reg sdram_tmrbankmachine0_cmd_buffer2_source_valid = 1'd0;
wire sdram_tmrbankmachine0_cmd_buffer2_source_ready;
reg sdram_tmrbankmachine0_cmd_buffer2_source_first = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer2_source_last = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_valid;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_ready;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_first = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_last = 1'd0;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_ready;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_last;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_we;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_writable;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_re;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_readable;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_din;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_dout;
reg [3:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_level = 4'd0;
reg sdram_tmrbankmachine0_cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_adr;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_dat_r;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_we;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_dat_w;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_do_read;
wire [2:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_rdport_adr;
wire [23:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_rdport_dat_r;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_last;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_payload_addr;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_first;
wire sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_last;
wire sdram_tmrbankmachine0_cmd_buffer3_sink_valid;
wire sdram_tmrbankmachine0_cmd_buffer3_sink_ready;
wire sdram_tmrbankmachine0_cmd_buffer3_sink_first;
wire sdram_tmrbankmachine0_cmd_buffer3_sink_last;
wire sdram_tmrbankmachine0_cmd_buffer3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine0_cmd_buffer3_sink_payload_addr;
reg sdram_tmrbankmachine0_cmd_buffer3_source_valid = 1'd0;
wire sdram_tmrbankmachine0_cmd_buffer3_source_ready;
reg sdram_tmrbankmachine0_cmd_buffer3_source_first = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer3_source_last = 1'd0;
reg sdram_tmrbankmachine0_cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine0_tmrinput_control4;
wire [20:0] sdram_tmrbankmachine0_lookAddrVote_control;
wire [20:0] sdram_tmrbankmachine0_bufAddrVote_control;
wire sdram_tmrbankmachine0_lookValidVote_control;
wire sdram_tmrbankmachine0_bufValidVote_control;
wire sdram_tmrbankmachine0_bufWeVote_control;
reg [13:0] sdram_tmrbankmachine0_row = 14'd0;
reg sdram_tmrbankmachine0_row_opened = 1'd0;
wire sdram_tmrbankmachine0_row_hit;
reg sdram_tmrbankmachine0_row_open;
reg sdram_tmrbankmachine0_row_close;
reg sdram_tmrbankmachine0_row_col_n_addr_sel;
wire sdram_tmrbankmachine0_twtpcon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_twtpcon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_twtpcon_count = 3'd0;
wire sdram_tmrbankmachine0_twtpcon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_twtpcon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_twtpcon2_count = 3'd0;
wire sdram_tmrbankmachine0_twtpcon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_twtpcon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_twtpcon3_count = 3'd0;
wire sdram_tmrbankmachine0_twtpVote_control;
wire sdram_tmrbankmachine0_trccon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_trccon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_trccon_count = 3'd0;
wire sdram_tmrbankmachine0_trccon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_trccon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_trccon2_count = 3'd0;
wire sdram_tmrbankmachine0_trccon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_trccon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_trccon3_count = 3'd0;
wire sdram_tmrbankmachine0_trcVote_control;
wire sdram_tmrbankmachine0_trascon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_trascon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_trascon_count = 3'd0;
wire sdram_tmrbankmachine0_trascon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_trascon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_trascon2_count = 3'd0;
wire sdram_tmrbankmachine0_trascon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine0_trascon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine0_trascon3_count = 3'd0;
wire sdram_tmrbankmachine0_trasVote_control;
wire sdram_tmrbankmachine1_req_valid;
wire sdram_tmrbankmachine1_req_ready;
wire sdram_tmrbankmachine1_req_we;
wire [20:0] sdram_tmrbankmachine1_req_addr;
reg sdram_tmrbankmachine1_req_lock;
reg sdram_tmrbankmachine1_req_wdata_ready;
reg sdram_tmrbankmachine1_req_rdata_valid;
wire [2:0] sdram_tmrbankmachine1_TMRreq_valid;
wire [2:0] sdram_tmrbankmachine1_TMRreq_ready;
wire [2:0] sdram_tmrbankmachine1_TMRreq_we;
wire [62:0] sdram_tmrbankmachine1_TMRreq_addr;
wire [2:0] sdram_tmrbankmachine1_TMRreq_lock;
wire [2:0] sdram_tmrbankmachine1_TMRreq_wdata_ready;
wire [2:0] sdram_tmrbankmachine1_TMRreq_rdata_valid;
wire sdram_tmrbankmachine1_refresh_req;
reg sdram_tmrbankmachine1_refresh_gnt;
reg sdram_tmrbankmachine1_cmd_valid;
wire sdram_tmrbankmachine1_cmd_ready;
reg sdram_tmrbankmachine1_cmd_first = 1'd0;
reg sdram_tmrbankmachine1_cmd_last = 1'd0;
reg [13:0] sdram_tmrbankmachine1_cmd_payload_a;
wire [2:0] sdram_tmrbankmachine1_cmd_payload_ba;
reg sdram_tmrbankmachine1_cmd_payload_cas;
reg sdram_tmrbankmachine1_cmd_payload_ras;
reg sdram_tmrbankmachine1_cmd_payload_we;
reg sdram_tmrbankmachine1_cmd_payload_is_cmd;
reg sdram_tmrbankmachine1_cmd_payload_is_read;
reg sdram_tmrbankmachine1_cmd_payload_is_write;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_valid;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_ready;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_first;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_last;
wire [41:0] sdram_tmrbankmachine1_TMRcmd_payload_a;
wire [8:0] sdram_tmrbankmachine1_TMRcmd_payload_ba;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_payload_cas;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_payload_ras;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_payload_we;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_payload_is_cmd;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_payload_is_read;
wire [2:0] sdram_tmrbankmachine1_TMRcmd_payload_is_write;
wire sdram_tmrbankmachine1_tmrinput_control0;
reg sdram_tmrbankmachine1_auto_precharge;
wire sdram_tmrbankmachine1_tmrinput_control1;
wire sdram_tmrbankmachine1_tmrinput_control2;
wire [20:0] sdram_tmrbankmachine1_tmrinput_control3;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_valid;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_ready;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_first = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_last = 1'd0;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_source_ready;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_source_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_source_last;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_we;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_writable;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_re;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_readable;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_din;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_dout;
reg [3:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_level = 4'd0;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_adr;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_dat_r;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_we;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_dat_w;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_do_read;
wire [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_rdport_adr;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_rdport_dat_r;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_last;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_last;
wire sdram_tmrbankmachine1_cmd_buffer_sink_valid;
wire sdram_tmrbankmachine1_cmd_buffer_sink_ready;
wire sdram_tmrbankmachine1_cmd_buffer_sink_first;
wire sdram_tmrbankmachine1_cmd_buffer_sink_last;
wire sdram_tmrbankmachine1_cmd_buffer_sink_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_sink_payload_addr;
reg sdram_tmrbankmachine1_cmd_buffer_source_valid = 1'd0;
wire sdram_tmrbankmachine1_cmd_buffer_source_ready;
reg sdram_tmrbankmachine1_cmd_buffer_source_first = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer_source_last = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine1_cmd_buffer_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_valid;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_ready;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_first = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_last = 1'd0;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_ready;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_last;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_we;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_writable;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_re;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_readable;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_din;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_dout;
reg [3:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_level = 4'd0;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_adr;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_dat_r;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_we;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_dat_w;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_do_read;
wire [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_rdport_adr;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_rdport_dat_r;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_last;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_last;
wire sdram_tmrbankmachine1_cmd_buffer2_sink_valid;
wire sdram_tmrbankmachine1_cmd_buffer2_sink_ready;
wire sdram_tmrbankmachine1_cmd_buffer2_sink_first;
wire sdram_tmrbankmachine1_cmd_buffer2_sink_last;
wire sdram_tmrbankmachine1_cmd_buffer2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer2_sink_payload_addr;
reg sdram_tmrbankmachine1_cmd_buffer2_source_valid = 1'd0;
wire sdram_tmrbankmachine1_cmd_buffer2_source_ready;
reg sdram_tmrbankmachine1_cmd_buffer2_source_first = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer2_source_last = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_valid;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_ready;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_first = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_last = 1'd0;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_ready;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_last;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_we;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_writable;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_re;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_readable;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_din;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_dout;
reg [3:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_level = 4'd0;
reg sdram_tmrbankmachine1_cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_adr;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_dat_r;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_we;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_dat_w;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_do_read;
wire [2:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_rdport_adr;
wire [23:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_rdport_dat_r;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_last;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_payload_addr;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_first;
wire sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_last;
wire sdram_tmrbankmachine1_cmd_buffer3_sink_valid;
wire sdram_tmrbankmachine1_cmd_buffer3_sink_ready;
wire sdram_tmrbankmachine1_cmd_buffer3_sink_first;
wire sdram_tmrbankmachine1_cmd_buffer3_sink_last;
wire sdram_tmrbankmachine1_cmd_buffer3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine1_cmd_buffer3_sink_payload_addr;
reg sdram_tmrbankmachine1_cmd_buffer3_source_valid = 1'd0;
wire sdram_tmrbankmachine1_cmd_buffer3_source_ready;
reg sdram_tmrbankmachine1_cmd_buffer3_source_first = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer3_source_last = 1'd0;
reg sdram_tmrbankmachine1_cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine1_tmrinput_control4;
wire [20:0] sdram_tmrbankmachine1_lookAddrVote_control;
wire [20:0] sdram_tmrbankmachine1_bufAddrVote_control;
wire sdram_tmrbankmachine1_lookValidVote_control;
wire sdram_tmrbankmachine1_bufValidVote_control;
wire sdram_tmrbankmachine1_bufWeVote_control;
reg [13:0] sdram_tmrbankmachine1_row = 14'd0;
reg sdram_tmrbankmachine1_row_opened = 1'd0;
wire sdram_tmrbankmachine1_row_hit;
reg sdram_tmrbankmachine1_row_open;
reg sdram_tmrbankmachine1_row_close;
reg sdram_tmrbankmachine1_row_col_n_addr_sel;
wire sdram_tmrbankmachine1_twtpcon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_twtpcon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_twtpcon_count = 3'd0;
wire sdram_tmrbankmachine1_twtpcon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_twtpcon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_twtpcon2_count = 3'd0;
wire sdram_tmrbankmachine1_twtpcon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_twtpcon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_twtpcon3_count = 3'd0;
wire sdram_tmrbankmachine1_twtpVote_control;
wire sdram_tmrbankmachine1_trccon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_trccon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_trccon_count = 3'd0;
wire sdram_tmrbankmachine1_trccon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_trccon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_trccon2_count = 3'd0;
wire sdram_tmrbankmachine1_trccon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_trccon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_trccon3_count = 3'd0;
wire sdram_tmrbankmachine1_trcVote_control;
wire sdram_tmrbankmachine1_trascon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_trascon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_trascon_count = 3'd0;
wire sdram_tmrbankmachine1_trascon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_trascon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_trascon2_count = 3'd0;
wire sdram_tmrbankmachine1_trascon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine1_trascon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine1_trascon3_count = 3'd0;
wire sdram_tmrbankmachine1_trasVote_control;
wire sdram_tmrbankmachine2_req_valid;
wire sdram_tmrbankmachine2_req_ready;
wire sdram_tmrbankmachine2_req_we;
wire [20:0] sdram_tmrbankmachine2_req_addr;
reg sdram_tmrbankmachine2_req_lock;
reg sdram_tmrbankmachine2_req_wdata_ready;
reg sdram_tmrbankmachine2_req_rdata_valid;
wire [2:0] sdram_tmrbankmachine2_TMRreq_valid;
wire [2:0] sdram_tmrbankmachine2_TMRreq_ready;
wire [2:0] sdram_tmrbankmachine2_TMRreq_we;
wire [62:0] sdram_tmrbankmachine2_TMRreq_addr;
wire [2:0] sdram_tmrbankmachine2_TMRreq_lock;
wire [2:0] sdram_tmrbankmachine2_TMRreq_wdata_ready;
wire [2:0] sdram_tmrbankmachine2_TMRreq_rdata_valid;
wire sdram_tmrbankmachine2_refresh_req;
reg sdram_tmrbankmachine2_refresh_gnt;
reg sdram_tmrbankmachine2_cmd_valid;
wire sdram_tmrbankmachine2_cmd_ready;
reg sdram_tmrbankmachine2_cmd_first = 1'd0;
reg sdram_tmrbankmachine2_cmd_last = 1'd0;
reg [13:0] sdram_tmrbankmachine2_cmd_payload_a;
wire [2:0] sdram_tmrbankmachine2_cmd_payload_ba;
reg sdram_tmrbankmachine2_cmd_payload_cas;
reg sdram_tmrbankmachine2_cmd_payload_ras;
reg sdram_tmrbankmachine2_cmd_payload_we;
reg sdram_tmrbankmachine2_cmd_payload_is_cmd;
reg sdram_tmrbankmachine2_cmd_payload_is_read;
reg sdram_tmrbankmachine2_cmd_payload_is_write;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_valid;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_ready;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_first;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_last;
wire [41:0] sdram_tmrbankmachine2_TMRcmd_payload_a;
wire [8:0] sdram_tmrbankmachine2_TMRcmd_payload_ba;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_payload_cas;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_payload_ras;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_payload_we;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_payload_is_cmd;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_payload_is_read;
wire [2:0] sdram_tmrbankmachine2_TMRcmd_payload_is_write;
wire sdram_tmrbankmachine2_tmrinput_control0;
reg sdram_tmrbankmachine2_auto_precharge;
wire sdram_tmrbankmachine2_tmrinput_control1;
wire sdram_tmrbankmachine2_tmrinput_control2;
wire [20:0] sdram_tmrbankmachine2_tmrinput_control3;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_valid;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_ready;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_first = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_last = 1'd0;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_source_ready;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_source_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_source_last;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_we;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_writable;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_re;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_readable;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_din;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_dout;
reg [3:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_level = 4'd0;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_adr;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_dat_r;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_we;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_dat_w;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_do_read;
wire [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_rdport_adr;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_rdport_dat_r;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_last;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_last;
wire sdram_tmrbankmachine2_cmd_buffer_sink_valid;
wire sdram_tmrbankmachine2_cmd_buffer_sink_ready;
wire sdram_tmrbankmachine2_cmd_buffer_sink_first;
wire sdram_tmrbankmachine2_cmd_buffer_sink_last;
wire sdram_tmrbankmachine2_cmd_buffer_sink_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_sink_payload_addr;
reg sdram_tmrbankmachine2_cmd_buffer_source_valid = 1'd0;
wire sdram_tmrbankmachine2_cmd_buffer_source_ready;
reg sdram_tmrbankmachine2_cmd_buffer_source_first = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer_source_last = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine2_cmd_buffer_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_valid;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_ready;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_first = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_last = 1'd0;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_ready;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_last;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_we;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_writable;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_re;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_readable;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_din;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_dout;
reg [3:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_level = 4'd0;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_adr;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_dat_r;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_we;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_dat_w;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_do_read;
wire [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_rdport_adr;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_rdport_dat_r;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_last;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_last;
wire sdram_tmrbankmachine2_cmd_buffer2_sink_valid;
wire sdram_tmrbankmachine2_cmd_buffer2_sink_ready;
wire sdram_tmrbankmachine2_cmd_buffer2_sink_first;
wire sdram_tmrbankmachine2_cmd_buffer2_sink_last;
wire sdram_tmrbankmachine2_cmd_buffer2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer2_sink_payload_addr;
reg sdram_tmrbankmachine2_cmd_buffer2_source_valid = 1'd0;
wire sdram_tmrbankmachine2_cmd_buffer2_source_ready;
reg sdram_tmrbankmachine2_cmd_buffer2_source_first = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer2_source_last = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_valid;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_ready;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_first = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_last = 1'd0;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_ready;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_last;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_we;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_writable;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_re;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_readable;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_din;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_dout;
reg [3:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_level = 4'd0;
reg sdram_tmrbankmachine2_cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_adr;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_dat_r;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_we;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_dat_w;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_do_read;
wire [2:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_rdport_adr;
wire [23:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_rdport_dat_r;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_last;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_payload_addr;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_first;
wire sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_last;
wire sdram_tmrbankmachine2_cmd_buffer3_sink_valid;
wire sdram_tmrbankmachine2_cmd_buffer3_sink_ready;
wire sdram_tmrbankmachine2_cmd_buffer3_sink_first;
wire sdram_tmrbankmachine2_cmd_buffer3_sink_last;
wire sdram_tmrbankmachine2_cmd_buffer3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine2_cmd_buffer3_sink_payload_addr;
reg sdram_tmrbankmachine2_cmd_buffer3_source_valid = 1'd0;
wire sdram_tmrbankmachine2_cmd_buffer3_source_ready;
reg sdram_tmrbankmachine2_cmd_buffer3_source_first = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer3_source_last = 1'd0;
reg sdram_tmrbankmachine2_cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine2_tmrinput_control4;
wire [20:0] sdram_tmrbankmachine2_lookAddrVote_control;
wire [20:0] sdram_tmrbankmachine2_bufAddrVote_control;
wire sdram_tmrbankmachine2_lookValidVote_control;
wire sdram_tmrbankmachine2_bufValidVote_control;
wire sdram_tmrbankmachine2_bufWeVote_control;
reg [13:0] sdram_tmrbankmachine2_row = 14'd0;
reg sdram_tmrbankmachine2_row_opened = 1'd0;
wire sdram_tmrbankmachine2_row_hit;
reg sdram_tmrbankmachine2_row_open;
reg sdram_tmrbankmachine2_row_close;
reg sdram_tmrbankmachine2_row_col_n_addr_sel;
wire sdram_tmrbankmachine2_twtpcon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_twtpcon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_twtpcon_count = 3'd0;
wire sdram_tmrbankmachine2_twtpcon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_twtpcon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_twtpcon2_count = 3'd0;
wire sdram_tmrbankmachine2_twtpcon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_twtpcon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_twtpcon3_count = 3'd0;
wire sdram_tmrbankmachine2_twtpVote_control;
wire sdram_tmrbankmachine2_trccon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_trccon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_trccon_count = 3'd0;
wire sdram_tmrbankmachine2_trccon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_trccon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_trccon2_count = 3'd0;
wire sdram_tmrbankmachine2_trccon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_trccon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_trccon3_count = 3'd0;
wire sdram_tmrbankmachine2_trcVote_control;
wire sdram_tmrbankmachine2_trascon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_trascon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_trascon_count = 3'd0;
wire sdram_tmrbankmachine2_trascon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_trascon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_trascon2_count = 3'd0;
wire sdram_tmrbankmachine2_trascon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine2_trascon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine2_trascon3_count = 3'd0;
wire sdram_tmrbankmachine2_trasVote_control;
wire sdram_tmrbankmachine3_req_valid;
wire sdram_tmrbankmachine3_req_ready;
wire sdram_tmrbankmachine3_req_we;
wire [20:0] sdram_tmrbankmachine3_req_addr;
reg sdram_tmrbankmachine3_req_lock;
reg sdram_tmrbankmachine3_req_wdata_ready;
reg sdram_tmrbankmachine3_req_rdata_valid;
wire [2:0] sdram_tmrbankmachine3_TMRreq_valid;
wire [2:0] sdram_tmrbankmachine3_TMRreq_ready;
wire [2:0] sdram_tmrbankmachine3_TMRreq_we;
wire [62:0] sdram_tmrbankmachine3_TMRreq_addr;
wire [2:0] sdram_tmrbankmachine3_TMRreq_lock;
wire [2:0] sdram_tmrbankmachine3_TMRreq_wdata_ready;
wire [2:0] sdram_tmrbankmachine3_TMRreq_rdata_valid;
wire sdram_tmrbankmachine3_refresh_req;
reg sdram_tmrbankmachine3_refresh_gnt;
reg sdram_tmrbankmachine3_cmd_valid;
wire sdram_tmrbankmachine3_cmd_ready;
reg sdram_tmrbankmachine3_cmd_first = 1'd0;
reg sdram_tmrbankmachine3_cmd_last = 1'd0;
reg [13:0] sdram_tmrbankmachine3_cmd_payload_a;
wire [2:0] sdram_tmrbankmachine3_cmd_payload_ba;
reg sdram_tmrbankmachine3_cmd_payload_cas;
reg sdram_tmrbankmachine3_cmd_payload_ras;
reg sdram_tmrbankmachine3_cmd_payload_we;
reg sdram_tmrbankmachine3_cmd_payload_is_cmd;
reg sdram_tmrbankmachine3_cmd_payload_is_read;
reg sdram_tmrbankmachine3_cmd_payload_is_write;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_valid;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_ready;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_first;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_last;
wire [41:0] sdram_tmrbankmachine3_TMRcmd_payload_a;
wire [8:0] sdram_tmrbankmachine3_TMRcmd_payload_ba;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_payload_cas;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_payload_ras;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_payload_we;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_payload_is_cmd;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_payload_is_read;
wire [2:0] sdram_tmrbankmachine3_TMRcmd_payload_is_write;
wire sdram_tmrbankmachine3_tmrinput_control0;
reg sdram_tmrbankmachine3_auto_precharge;
wire sdram_tmrbankmachine3_tmrinput_control1;
wire sdram_tmrbankmachine3_tmrinput_control2;
wire [20:0] sdram_tmrbankmachine3_tmrinput_control3;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_valid;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_ready;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_first = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_last = 1'd0;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_source_ready;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_source_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_source_last;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_we;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_writable;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_re;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_readable;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_din;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_dout;
reg [3:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_level = 4'd0;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_adr;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_dat_r;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_we;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_dat_w;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_do_read;
wire [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_rdport_adr;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_rdport_dat_r;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_last;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_last;
wire sdram_tmrbankmachine3_cmd_buffer_sink_valid;
wire sdram_tmrbankmachine3_cmd_buffer_sink_ready;
wire sdram_tmrbankmachine3_cmd_buffer_sink_first;
wire sdram_tmrbankmachine3_cmd_buffer_sink_last;
wire sdram_tmrbankmachine3_cmd_buffer_sink_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_sink_payload_addr;
reg sdram_tmrbankmachine3_cmd_buffer_source_valid = 1'd0;
wire sdram_tmrbankmachine3_cmd_buffer_source_ready;
reg sdram_tmrbankmachine3_cmd_buffer_source_first = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer_source_last = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine3_cmd_buffer_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_valid;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_ready;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_first = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_last = 1'd0;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_ready;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_last;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_we;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_writable;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_re;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_readable;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_din;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_dout;
reg [3:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_level = 4'd0;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_adr;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_dat_r;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_we;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_dat_w;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_do_read;
wire [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_rdport_adr;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_rdport_dat_r;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_last;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_last;
wire sdram_tmrbankmachine3_cmd_buffer2_sink_valid;
wire sdram_tmrbankmachine3_cmd_buffer2_sink_ready;
wire sdram_tmrbankmachine3_cmd_buffer2_sink_first;
wire sdram_tmrbankmachine3_cmd_buffer2_sink_last;
wire sdram_tmrbankmachine3_cmd_buffer2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer2_sink_payload_addr;
reg sdram_tmrbankmachine3_cmd_buffer2_source_valid = 1'd0;
wire sdram_tmrbankmachine3_cmd_buffer2_source_ready;
reg sdram_tmrbankmachine3_cmd_buffer2_source_first = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer2_source_last = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_valid;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_ready;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_first = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_last = 1'd0;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_ready;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_last;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_we;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_writable;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_re;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_readable;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_din;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_dout;
reg [3:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_level = 4'd0;
reg sdram_tmrbankmachine3_cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_adr;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_dat_r;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_we;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_dat_w;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_do_read;
wire [2:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_rdport_adr;
wire [23:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_rdport_dat_r;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_last;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_payload_addr;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_first;
wire sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_last;
wire sdram_tmrbankmachine3_cmd_buffer3_sink_valid;
wire sdram_tmrbankmachine3_cmd_buffer3_sink_ready;
wire sdram_tmrbankmachine3_cmd_buffer3_sink_first;
wire sdram_tmrbankmachine3_cmd_buffer3_sink_last;
wire sdram_tmrbankmachine3_cmd_buffer3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine3_cmd_buffer3_sink_payload_addr;
reg sdram_tmrbankmachine3_cmd_buffer3_source_valid = 1'd0;
wire sdram_tmrbankmachine3_cmd_buffer3_source_ready;
reg sdram_tmrbankmachine3_cmd_buffer3_source_first = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer3_source_last = 1'd0;
reg sdram_tmrbankmachine3_cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine3_tmrinput_control4;
wire [20:0] sdram_tmrbankmachine3_lookAddrVote_control;
wire [20:0] sdram_tmrbankmachine3_bufAddrVote_control;
wire sdram_tmrbankmachine3_lookValidVote_control;
wire sdram_tmrbankmachine3_bufValidVote_control;
wire sdram_tmrbankmachine3_bufWeVote_control;
reg [13:0] sdram_tmrbankmachine3_row = 14'd0;
reg sdram_tmrbankmachine3_row_opened = 1'd0;
wire sdram_tmrbankmachine3_row_hit;
reg sdram_tmrbankmachine3_row_open;
reg sdram_tmrbankmachine3_row_close;
reg sdram_tmrbankmachine3_row_col_n_addr_sel;
wire sdram_tmrbankmachine3_twtpcon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_twtpcon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_twtpcon_count = 3'd0;
wire sdram_tmrbankmachine3_twtpcon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_twtpcon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_twtpcon2_count = 3'd0;
wire sdram_tmrbankmachine3_twtpcon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_twtpcon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_twtpcon3_count = 3'd0;
wire sdram_tmrbankmachine3_twtpVote_control;
wire sdram_tmrbankmachine3_trccon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_trccon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_trccon_count = 3'd0;
wire sdram_tmrbankmachine3_trccon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_trccon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_trccon2_count = 3'd0;
wire sdram_tmrbankmachine3_trccon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_trccon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_trccon3_count = 3'd0;
wire sdram_tmrbankmachine3_trcVote_control;
wire sdram_tmrbankmachine3_trascon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_trascon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_trascon_count = 3'd0;
wire sdram_tmrbankmachine3_trascon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_trascon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_trascon2_count = 3'd0;
wire sdram_tmrbankmachine3_trascon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine3_trascon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine3_trascon3_count = 3'd0;
wire sdram_tmrbankmachine3_trasVote_control;
wire sdram_tmrbankmachine4_req_valid;
wire sdram_tmrbankmachine4_req_ready;
wire sdram_tmrbankmachine4_req_we;
wire [20:0] sdram_tmrbankmachine4_req_addr;
reg sdram_tmrbankmachine4_req_lock;
reg sdram_tmrbankmachine4_req_wdata_ready;
reg sdram_tmrbankmachine4_req_rdata_valid;
wire [2:0] sdram_tmrbankmachine4_TMRreq_valid;
wire [2:0] sdram_tmrbankmachine4_TMRreq_ready;
wire [2:0] sdram_tmrbankmachine4_TMRreq_we;
wire [62:0] sdram_tmrbankmachine4_TMRreq_addr;
wire [2:0] sdram_tmrbankmachine4_TMRreq_lock;
wire [2:0] sdram_tmrbankmachine4_TMRreq_wdata_ready;
wire [2:0] sdram_tmrbankmachine4_TMRreq_rdata_valid;
wire sdram_tmrbankmachine4_refresh_req;
reg sdram_tmrbankmachine4_refresh_gnt;
reg sdram_tmrbankmachine4_cmd_valid;
wire sdram_tmrbankmachine4_cmd_ready;
reg sdram_tmrbankmachine4_cmd_first = 1'd0;
reg sdram_tmrbankmachine4_cmd_last = 1'd0;
reg [13:0] sdram_tmrbankmachine4_cmd_payload_a;
wire [2:0] sdram_tmrbankmachine4_cmd_payload_ba;
reg sdram_tmrbankmachine4_cmd_payload_cas;
reg sdram_tmrbankmachine4_cmd_payload_ras;
reg sdram_tmrbankmachine4_cmd_payload_we;
reg sdram_tmrbankmachine4_cmd_payload_is_cmd;
reg sdram_tmrbankmachine4_cmd_payload_is_read;
reg sdram_tmrbankmachine4_cmd_payload_is_write;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_valid;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_ready;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_first;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_last;
wire [41:0] sdram_tmrbankmachine4_TMRcmd_payload_a;
wire [8:0] sdram_tmrbankmachine4_TMRcmd_payload_ba;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_payload_cas;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_payload_ras;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_payload_we;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_payload_is_cmd;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_payload_is_read;
wire [2:0] sdram_tmrbankmachine4_TMRcmd_payload_is_write;
wire sdram_tmrbankmachine4_tmrinput_control0;
reg sdram_tmrbankmachine4_auto_precharge;
wire sdram_tmrbankmachine4_tmrinput_control1;
wire sdram_tmrbankmachine4_tmrinput_control2;
wire [20:0] sdram_tmrbankmachine4_tmrinput_control3;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_valid;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_ready;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_first = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_last = 1'd0;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_source_ready;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_source_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_source_last;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_we;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_writable;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_re;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_readable;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_din;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_dout;
reg [3:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_level = 4'd0;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_adr;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_dat_r;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_we;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_dat_w;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_do_read;
wire [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_rdport_adr;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_rdport_dat_r;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_last;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_last;
wire sdram_tmrbankmachine4_cmd_buffer_sink_valid;
wire sdram_tmrbankmachine4_cmd_buffer_sink_ready;
wire sdram_tmrbankmachine4_cmd_buffer_sink_first;
wire sdram_tmrbankmachine4_cmd_buffer_sink_last;
wire sdram_tmrbankmachine4_cmd_buffer_sink_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_sink_payload_addr;
reg sdram_tmrbankmachine4_cmd_buffer_source_valid = 1'd0;
wire sdram_tmrbankmachine4_cmd_buffer_source_ready;
reg sdram_tmrbankmachine4_cmd_buffer_source_first = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer_source_last = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine4_cmd_buffer_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_valid;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_ready;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_first = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_last = 1'd0;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_ready;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_last;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_we;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_writable;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_re;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_readable;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_din;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_dout;
reg [3:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_level = 4'd0;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_adr;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_dat_r;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_we;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_dat_w;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_do_read;
wire [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_rdport_adr;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_rdport_dat_r;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_last;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_last;
wire sdram_tmrbankmachine4_cmd_buffer2_sink_valid;
wire sdram_tmrbankmachine4_cmd_buffer2_sink_ready;
wire sdram_tmrbankmachine4_cmd_buffer2_sink_first;
wire sdram_tmrbankmachine4_cmd_buffer2_sink_last;
wire sdram_tmrbankmachine4_cmd_buffer2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer2_sink_payload_addr;
reg sdram_tmrbankmachine4_cmd_buffer2_source_valid = 1'd0;
wire sdram_tmrbankmachine4_cmd_buffer2_source_ready;
reg sdram_tmrbankmachine4_cmd_buffer2_source_first = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer2_source_last = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_valid;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_ready;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_first = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_last = 1'd0;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_ready;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_last;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_we;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_writable;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_re;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_readable;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_din;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_dout;
reg [3:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_level = 4'd0;
reg sdram_tmrbankmachine4_cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_adr;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_dat_r;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_we;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_dat_w;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_do_read;
wire [2:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_rdport_adr;
wire [23:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_rdport_dat_r;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_last;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_payload_addr;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_first;
wire sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_last;
wire sdram_tmrbankmachine4_cmd_buffer3_sink_valid;
wire sdram_tmrbankmachine4_cmd_buffer3_sink_ready;
wire sdram_tmrbankmachine4_cmd_buffer3_sink_first;
wire sdram_tmrbankmachine4_cmd_buffer3_sink_last;
wire sdram_tmrbankmachine4_cmd_buffer3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine4_cmd_buffer3_sink_payload_addr;
reg sdram_tmrbankmachine4_cmd_buffer3_source_valid = 1'd0;
wire sdram_tmrbankmachine4_cmd_buffer3_source_ready;
reg sdram_tmrbankmachine4_cmd_buffer3_source_first = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer3_source_last = 1'd0;
reg sdram_tmrbankmachine4_cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine4_tmrinput_control4;
wire [20:0] sdram_tmrbankmachine4_lookAddrVote_control;
wire [20:0] sdram_tmrbankmachine4_bufAddrVote_control;
wire sdram_tmrbankmachine4_lookValidVote_control;
wire sdram_tmrbankmachine4_bufValidVote_control;
wire sdram_tmrbankmachine4_bufWeVote_control;
reg [13:0] sdram_tmrbankmachine4_row = 14'd0;
reg sdram_tmrbankmachine4_row_opened = 1'd0;
wire sdram_tmrbankmachine4_row_hit;
reg sdram_tmrbankmachine4_row_open;
reg sdram_tmrbankmachine4_row_close;
reg sdram_tmrbankmachine4_row_col_n_addr_sel;
wire sdram_tmrbankmachine4_twtpcon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_twtpcon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_twtpcon_count = 3'd0;
wire sdram_tmrbankmachine4_twtpcon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_twtpcon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_twtpcon2_count = 3'd0;
wire sdram_tmrbankmachine4_twtpcon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_twtpcon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_twtpcon3_count = 3'd0;
wire sdram_tmrbankmachine4_twtpVote_control;
wire sdram_tmrbankmachine4_trccon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_trccon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_trccon_count = 3'd0;
wire sdram_tmrbankmachine4_trccon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_trccon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_trccon2_count = 3'd0;
wire sdram_tmrbankmachine4_trccon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_trccon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_trccon3_count = 3'd0;
wire sdram_tmrbankmachine4_trcVote_control;
wire sdram_tmrbankmachine4_trascon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_trascon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_trascon_count = 3'd0;
wire sdram_tmrbankmachine4_trascon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_trascon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_trascon2_count = 3'd0;
wire sdram_tmrbankmachine4_trascon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine4_trascon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine4_trascon3_count = 3'd0;
wire sdram_tmrbankmachine4_trasVote_control;
wire sdram_tmrbankmachine5_req_valid;
wire sdram_tmrbankmachine5_req_ready;
wire sdram_tmrbankmachine5_req_we;
wire [20:0] sdram_tmrbankmachine5_req_addr;
reg sdram_tmrbankmachine5_req_lock;
reg sdram_tmrbankmachine5_req_wdata_ready;
reg sdram_tmrbankmachine5_req_rdata_valid;
wire [2:0] sdram_tmrbankmachine5_TMRreq_valid;
wire [2:0] sdram_tmrbankmachine5_TMRreq_ready;
wire [2:0] sdram_tmrbankmachine5_TMRreq_we;
wire [62:0] sdram_tmrbankmachine5_TMRreq_addr;
wire [2:0] sdram_tmrbankmachine5_TMRreq_lock;
wire [2:0] sdram_tmrbankmachine5_TMRreq_wdata_ready;
wire [2:0] sdram_tmrbankmachine5_TMRreq_rdata_valid;
wire sdram_tmrbankmachine5_refresh_req;
reg sdram_tmrbankmachine5_refresh_gnt;
reg sdram_tmrbankmachine5_cmd_valid;
wire sdram_tmrbankmachine5_cmd_ready;
reg sdram_tmrbankmachine5_cmd_first = 1'd0;
reg sdram_tmrbankmachine5_cmd_last = 1'd0;
reg [13:0] sdram_tmrbankmachine5_cmd_payload_a;
wire [2:0] sdram_tmrbankmachine5_cmd_payload_ba;
reg sdram_tmrbankmachine5_cmd_payload_cas;
reg sdram_tmrbankmachine5_cmd_payload_ras;
reg sdram_tmrbankmachine5_cmd_payload_we;
reg sdram_tmrbankmachine5_cmd_payload_is_cmd;
reg sdram_tmrbankmachine5_cmd_payload_is_read;
reg sdram_tmrbankmachine5_cmd_payload_is_write;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_valid;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_ready;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_first;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_last;
wire [41:0] sdram_tmrbankmachine5_TMRcmd_payload_a;
wire [8:0] sdram_tmrbankmachine5_TMRcmd_payload_ba;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_payload_cas;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_payload_ras;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_payload_we;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_payload_is_cmd;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_payload_is_read;
wire [2:0] sdram_tmrbankmachine5_TMRcmd_payload_is_write;
wire sdram_tmrbankmachine5_tmrinput_control0;
reg sdram_tmrbankmachine5_auto_precharge;
wire sdram_tmrbankmachine5_tmrinput_control1;
wire sdram_tmrbankmachine5_tmrinput_control2;
wire [20:0] sdram_tmrbankmachine5_tmrinput_control3;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_valid;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_ready;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_first = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_last = 1'd0;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_source_ready;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_source_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_source_last;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_we;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_writable;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_re;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_readable;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_din;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_dout;
reg [3:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_level = 4'd0;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_adr;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_dat_r;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_we;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_dat_w;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_do_read;
wire [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_rdport_adr;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_rdport_dat_r;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_last;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_last;
wire sdram_tmrbankmachine5_cmd_buffer_sink_valid;
wire sdram_tmrbankmachine5_cmd_buffer_sink_ready;
wire sdram_tmrbankmachine5_cmd_buffer_sink_first;
wire sdram_tmrbankmachine5_cmd_buffer_sink_last;
wire sdram_tmrbankmachine5_cmd_buffer_sink_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_sink_payload_addr;
reg sdram_tmrbankmachine5_cmd_buffer_source_valid = 1'd0;
wire sdram_tmrbankmachine5_cmd_buffer_source_ready;
reg sdram_tmrbankmachine5_cmd_buffer_source_first = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer_source_last = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine5_cmd_buffer_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_valid;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_ready;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_first = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_last = 1'd0;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_ready;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_last;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_we;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_writable;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_re;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_readable;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_din;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_dout;
reg [3:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_level = 4'd0;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_adr;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_dat_r;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_we;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_dat_w;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_do_read;
wire [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_rdport_adr;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_rdport_dat_r;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_last;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_last;
wire sdram_tmrbankmachine5_cmd_buffer2_sink_valid;
wire sdram_tmrbankmachine5_cmd_buffer2_sink_ready;
wire sdram_tmrbankmachine5_cmd_buffer2_sink_first;
wire sdram_tmrbankmachine5_cmd_buffer2_sink_last;
wire sdram_tmrbankmachine5_cmd_buffer2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer2_sink_payload_addr;
reg sdram_tmrbankmachine5_cmd_buffer2_source_valid = 1'd0;
wire sdram_tmrbankmachine5_cmd_buffer2_source_ready;
reg sdram_tmrbankmachine5_cmd_buffer2_source_first = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer2_source_last = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_valid;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_ready;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_first = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_last = 1'd0;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_ready;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_last;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_we;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_writable;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_re;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_readable;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_din;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_dout;
reg [3:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_level = 4'd0;
reg sdram_tmrbankmachine5_cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_adr;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_dat_r;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_we;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_dat_w;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_do_read;
wire [2:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_rdport_adr;
wire [23:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_rdport_dat_r;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_last;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_payload_addr;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_first;
wire sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_last;
wire sdram_tmrbankmachine5_cmd_buffer3_sink_valid;
wire sdram_tmrbankmachine5_cmd_buffer3_sink_ready;
wire sdram_tmrbankmachine5_cmd_buffer3_sink_first;
wire sdram_tmrbankmachine5_cmd_buffer3_sink_last;
wire sdram_tmrbankmachine5_cmd_buffer3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine5_cmd_buffer3_sink_payload_addr;
reg sdram_tmrbankmachine5_cmd_buffer3_source_valid = 1'd0;
wire sdram_tmrbankmachine5_cmd_buffer3_source_ready;
reg sdram_tmrbankmachine5_cmd_buffer3_source_first = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer3_source_last = 1'd0;
reg sdram_tmrbankmachine5_cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine5_tmrinput_control4;
wire [20:0] sdram_tmrbankmachine5_lookAddrVote_control;
wire [20:0] sdram_tmrbankmachine5_bufAddrVote_control;
wire sdram_tmrbankmachine5_lookValidVote_control;
wire sdram_tmrbankmachine5_bufValidVote_control;
wire sdram_tmrbankmachine5_bufWeVote_control;
reg [13:0] sdram_tmrbankmachine5_row = 14'd0;
reg sdram_tmrbankmachine5_row_opened = 1'd0;
wire sdram_tmrbankmachine5_row_hit;
reg sdram_tmrbankmachine5_row_open;
reg sdram_tmrbankmachine5_row_close;
reg sdram_tmrbankmachine5_row_col_n_addr_sel;
wire sdram_tmrbankmachine5_twtpcon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_twtpcon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_twtpcon_count = 3'd0;
wire sdram_tmrbankmachine5_twtpcon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_twtpcon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_twtpcon2_count = 3'd0;
wire sdram_tmrbankmachine5_twtpcon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_twtpcon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_twtpcon3_count = 3'd0;
wire sdram_tmrbankmachine5_twtpVote_control;
wire sdram_tmrbankmachine5_trccon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_trccon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_trccon_count = 3'd0;
wire sdram_tmrbankmachine5_trccon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_trccon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_trccon2_count = 3'd0;
wire sdram_tmrbankmachine5_trccon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_trccon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_trccon3_count = 3'd0;
wire sdram_tmrbankmachine5_trcVote_control;
wire sdram_tmrbankmachine5_trascon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_trascon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_trascon_count = 3'd0;
wire sdram_tmrbankmachine5_trascon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_trascon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_trascon2_count = 3'd0;
wire sdram_tmrbankmachine5_trascon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine5_trascon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine5_trascon3_count = 3'd0;
wire sdram_tmrbankmachine5_trasVote_control;
wire sdram_tmrbankmachine6_req_valid;
wire sdram_tmrbankmachine6_req_ready;
wire sdram_tmrbankmachine6_req_we;
wire [20:0] sdram_tmrbankmachine6_req_addr;
reg sdram_tmrbankmachine6_req_lock;
reg sdram_tmrbankmachine6_req_wdata_ready;
reg sdram_tmrbankmachine6_req_rdata_valid;
wire [2:0] sdram_tmrbankmachine6_TMRreq_valid;
wire [2:0] sdram_tmrbankmachine6_TMRreq_ready;
wire [2:0] sdram_tmrbankmachine6_TMRreq_we;
wire [62:0] sdram_tmrbankmachine6_TMRreq_addr;
wire [2:0] sdram_tmrbankmachine6_TMRreq_lock;
wire [2:0] sdram_tmrbankmachine6_TMRreq_wdata_ready;
wire [2:0] sdram_tmrbankmachine6_TMRreq_rdata_valid;
wire sdram_tmrbankmachine6_refresh_req;
reg sdram_tmrbankmachine6_refresh_gnt;
reg sdram_tmrbankmachine6_cmd_valid;
wire sdram_tmrbankmachine6_cmd_ready;
reg sdram_tmrbankmachine6_cmd_first = 1'd0;
reg sdram_tmrbankmachine6_cmd_last = 1'd0;
reg [13:0] sdram_tmrbankmachine6_cmd_payload_a;
wire [2:0] sdram_tmrbankmachine6_cmd_payload_ba;
reg sdram_tmrbankmachine6_cmd_payload_cas;
reg sdram_tmrbankmachine6_cmd_payload_ras;
reg sdram_tmrbankmachine6_cmd_payload_we;
reg sdram_tmrbankmachine6_cmd_payload_is_cmd;
reg sdram_tmrbankmachine6_cmd_payload_is_read;
reg sdram_tmrbankmachine6_cmd_payload_is_write;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_valid;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_ready;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_first;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_last;
wire [41:0] sdram_tmrbankmachine6_TMRcmd_payload_a;
wire [8:0] sdram_tmrbankmachine6_TMRcmd_payload_ba;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_payload_cas;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_payload_ras;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_payload_we;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_payload_is_cmd;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_payload_is_read;
wire [2:0] sdram_tmrbankmachine6_TMRcmd_payload_is_write;
wire sdram_tmrbankmachine6_tmrinput_control0;
reg sdram_tmrbankmachine6_auto_precharge;
wire sdram_tmrbankmachine6_tmrinput_control1;
wire sdram_tmrbankmachine6_tmrinput_control2;
wire [20:0] sdram_tmrbankmachine6_tmrinput_control3;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_valid;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_ready;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_first = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_last = 1'd0;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_source_ready;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_source_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_source_last;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_we;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_writable;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_re;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_readable;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_din;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_dout;
reg [3:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_level = 4'd0;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_adr;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_dat_r;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_we;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_dat_w;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_do_read;
wire [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_rdport_adr;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_rdport_dat_r;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_last;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_last;
wire sdram_tmrbankmachine6_cmd_buffer_sink_valid;
wire sdram_tmrbankmachine6_cmd_buffer_sink_ready;
wire sdram_tmrbankmachine6_cmd_buffer_sink_first;
wire sdram_tmrbankmachine6_cmd_buffer_sink_last;
wire sdram_tmrbankmachine6_cmd_buffer_sink_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_sink_payload_addr;
reg sdram_tmrbankmachine6_cmd_buffer_source_valid = 1'd0;
wire sdram_tmrbankmachine6_cmd_buffer_source_ready;
reg sdram_tmrbankmachine6_cmd_buffer_source_first = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer_source_last = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine6_cmd_buffer_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_valid;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_ready;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_first = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_last = 1'd0;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_ready;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_last;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_we;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_writable;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_re;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_readable;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_din;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_dout;
reg [3:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_level = 4'd0;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_adr;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_dat_r;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_we;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_dat_w;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_do_read;
wire [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_rdport_adr;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_rdport_dat_r;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_last;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_last;
wire sdram_tmrbankmachine6_cmd_buffer2_sink_valid;
wire sdram_tmrbankmachine6_cmd_buffer2_sink_ready;
wire sdram_tmrbankmachine6_cmd_buffer2_sink_first;
wire sdram_tmrbankmachine6_cmd_buffer2_sink_last;
wire sdram_tmrbankmachine6_cmd_buffer2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer2_sink_payload_addr;
reg sdram_tmrbankmachine6_cmd_buffer2_source_valid = 1'd0;
wire sdram_tmrbankmachine6_cmd_buffer2_source_ready;
reg sdram_tmrbankmachine6_cmd_buffer2_source_first = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer2_source_last = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_valid;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_ready;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_first = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_last = 1'd0;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_ready;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_last;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_we;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_writable;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_re;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_readable;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_din;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_dout;
reg [3:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_level = 4'd0;
reg sdram_tmrbankmachine6_cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_adr;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_dat_r;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_we;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_dat_w;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_do_read;
wire [2:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_rdport_adr;
wire [23:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_rdport_dat_r;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_last;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_payload_addr;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_first;
wire sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_last;
wire sdram_tmrbankmachine6_cmd_buffer3_sink_valid;
wire sdram_tmrbankmachine6_cmd_buffer3_sink_ready;
wire sdram_tmrbankmachine6_cmd_buffer3_sink_first;
wire sdram_tmrbankmachine6_cmd_buffer3_sink_last;
wire sdram_tmrbankmachine6_cmd_buffer3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine6_cmd_buffer3_sink_payload_addr;
reg sdram_tmrbankmachine6_cmd_buffer3_source_valid = 1'd0;
wire sdram_tmrbankmachine6_cmd_buffer3_source_ready;
reg sdram_tmrbankmachine6_cmd_buffer3_source_first = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer3_source_last = 1'd0;
reg sdram_tmrbankmachine6_cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine6_tmrinput_control4;
wire [20:0] sdram_tmrbankmachine6_lookAddrVote_control;
wire [20:0] sdram_tmrbankmachine6_bufAddrVote_control;
wire sdram_tmrbankmachine6_lookValidVote_control;
wire sdram_tmrbankmachine6_bufValidVote_control;
wire sdram_tmrbankmachine6_bufWeVote_control;
reg [13:0] sdram_tmrbankmachine6_row = 14'd0;
reg sdram_tmrbankmachine6_row_opened = 1'd0;
wire sdram_tmrbankmachine6_row_hit;
reg sdram_tmrbankmachine6_row_open;
reg sdram_tmrbankmachine6_row_close;
reg sdram_tmrbankmachine6_row_col_n_addr_sel;
wire sdram_tmrbankmachine6_twtpcon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_twtpcon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_twtpcon_count = 3'd0;
wire sdram_tmrbankmachine6_twtpcon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_twtpcon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_twtpcon2_count = 3'd0;
wire sdram_tmrbankmachine6_twtpcon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_twtpcon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_twtpcon3_count = 3'd0;
wire sdram_tmrbankmachine6_twtpVote_control;
wire sdram_tmrbankmachine6_trccon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_trccon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_trccon_count = 3'd0;
wire sdram_tmrbankmachine6_trccon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_trccon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_trccon2_count = 3'd0;
wire sdram_tmrbankmachine6_trccon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_trccon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_trccon3_count = 3'd0;
wire sdram_tmrbankmachine6_trcVote_control;
wire sdram_tmrbankmachine6_trascon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_trascon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_trascon_count = 3'd0;
wire sdram_tmrbankmachine6_trascon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_trascon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_trascon2_count = 3'd0;
wire sdram_tmrbankmachine6_trascon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine6_trascon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine6_trascon3_count = 3'd0;
wire sdram_tmrbankmachine6_trasVote_control;
wire sdram_tmrbankmachine7_req_valid;
wire sdram_tmrbankmachine7_req_ready;
wire sdram_tmrbankmachine7_req_we;
wire [20:0] sdram_tmrbankmachine7_req_addr;
reg sdram_tmrbankmachine7_req_lock;
reg sdram_tmrbankmachine7_req_wdata_ready;
reg sdram_tmrbankmachine7_req_rdata_valid;
wire [2:0] sdram_tmrbankmachine7_TMRreq_valid;
wire [2:0] sdram_tmrbankmachine7_TMRreq_ready;
wire [2:0] sdram_tmrbankmachine7_TMRreq_we;
wire [62:0] sdram_tmrbankmachine7_TMRreq_addr;
wire [2:0] sdram_tmrbankmachine7_TMRreq_lock;
wire [2:0] sdram_tmrbankmachine7_TMRreq_wdata_ready;
wire [2:0] sdram_tmrbankmachine7_TMRreq_rdata_valid;
wire sdram_tmrbankmachine7_refresh_req;
reg sdram_tmrbankmachine7_refresh_gnt;
reg sdram_tmrbankmachine7_cmd_valid;
wire sdram_tmrbankmachine7_cmd_ready;
reg sdram_tmrbankmachine7_cmd_first = 1'd0;
reg sdram_tmrbankmachine7_cmd_last = 1'd0;
reg [13:0] sdram_tmrbankmachine7_cmd_payload_a;
wire [2:0] sdram_tmrbankmachine7_cmd_payload_ba;
reg sdram_tmrbankmachine7_cmd_payload_cas;
reg sdram_tmrbankmachine7_cmd_payload_ras;
reg sdram_tmrbankmachine7_cmd_payload_we;
reg sdram_tmrbankmachine7_cmd_payload_is_cmd;
reg sdram_tmrbankmachine7_cmd_payload_is_read;
reg sdram_tmrbankmachine7_cmd_payload_is_write;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_valid;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_ready;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_first;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_last;
wire [41:0] sdram_tmrbankmachine7_TMRcmd_payload_a;
wire [8:0] sdram_tmrbankmachine7_TMRcmd_payload_ba;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_payload_cas;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_payload_ras;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_payload_we;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_payload_is_cmd;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_payload_is_read;
wire [2:0] sdram_tmrbankmachine7_TMRcmd_payload_is_write;
wire sdram_tmrbankmachine7_tmrinput_control0;
reg sdram_tmrbankmachine7_auto_precharge;
wire sdram_tmrbankmachine7_tmrinput_control1;
wire sdram_tmrbankmachine7_tmrinput_control2;
wire [20:0] sdram_tmrbankmachine7_tmrinput_control3;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_valid;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_ready;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_first = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_last = 1'd0;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_source_ready;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_source_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_source_last;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_we;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_writable;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_re;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_readable;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_din;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_dout;
reg [3:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_level = 4'd0;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_adr;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_dat_r;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_we;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_dat_w;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_do_read;
wire [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_rdport_adr;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_rdport_dat_r;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_last;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_last;
wire sdram_tmrbankmachine7_cmd_buffer_sink_valid;
wire sdram_tmrbankmachine7_cmd_buffer_sink_ready;
wire sdram_tmrbankmachine7_cmd_buffer_sink_first;
wire sdram_tmrbankmachine7_cmd_buffer_sink_last;
wire sdram_tmrbankmachine7_cmd_buffer_sink_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_sink_payload_addr;
reg sdram_tmrbankmachine7_cmd_buffer_source_valid = 1'd0;
wire sdram_tmrbankmachine7_cmd_buffer_source_ready;
reg sdram_tmrbankmachine7_cmd_buffer_source_first = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer_source_last = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine7_cmd_buffer_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_valid;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_ready;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_first = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_last = 1'd0;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_ready;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_last;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_we;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_writable;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_re;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_readable;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_din;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_dout;
reg [3:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_level = 4'd0;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_adr;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_dat_r;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_we;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_dat_w;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_do_read;
wire [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_rdport_adr;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_rdport_dat_r;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_last;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_last;
wire sdram_tmrbankmachine7_cmd_buffer2_sink_valid;
wire sdram_tmrbankmachine7_cmd_buffer2_sink_ready;
wire sdram_tmrbankmachine7_cmd_buffer2_sink_first;
wire sdram_tmrbankmachine7_cmd_buffer2_sink_last;
wire sdram_tmrbankmachine7_cmd_buffer2_sink_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer2_sink_payload_addr;
reg sdram_tmrbankmachine7_cmd_buffer2_source_valid = 1'd0;
wire sdram_tmrbankmachine7_cmd_buffer2_source_ready;
reg sdram_tmrbankmachine7_cmd_buffer2_source_first = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer2_source_last = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_valid;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_ready;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_first = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_last = 1'd0;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_ready;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_last;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_we;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_writable;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_re;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_readable;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_din;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_dout;
reg [3:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_level = 4'd0;
reg sdram_tmrbankmachine7_cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_adr;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_dat_r;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_we;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_dat_w;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_do_read;
wire [2:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_rdport_adr;
wire [23:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_rdport_dat_r;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_last;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_payload_addr;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_first;
wire sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_last;
wire sdram_tmrbankmachine7_cmd_buffer3_sink_valid;
wire sdram_tmrbankmachine7_cmd_buffer3_sink_ready;
wire sdram_tmrbankmachine7_cmd_buffer3_sink_first;
wire sdram_tmrbankmachine7_cmd_buffer3_sink_last;
wire sdram_tmrbankmachine7_cmd_buffer3_sink_payload_we;
wire [20:0] sdram_tmrbankmachine7_cmd_buffer3_sink_payload_addr;
reg sdram_tmrbankmachine7_cmd_buffer3_source_valid = 1'd0;
wire sdram_tmrbankmachine7_cmd_buffer3_source_ready;
reg sdram_tmrbankmachine7_cmd_buffer3_source_first = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer3_source_last = 1'd0;
reg sdram_tmrbankmachine7_cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr = 21'd0;
wire sdram_tmrbankmachine7_tmrinput_control4;
wire [20:0] sdram_tmrbankmachine7_lookAddrVote_control;
wire [20:0] sdram_tmrbankmachine7_bufAddrVote_control;
wire sdram_tmrbankmachine7_lookValidVote_control;
wire sdram_tmrbankmachine7_bufValidVote_control;
wire sdram_tmrbankmachine7_bufWeVote_control;
reg [13:0] sdram_tmrbankmachine7_row = 14'd0;
reg sdram_tmrbankmachine7_row_opened = 1'd0;
wire sdram_tmrbankmachine7_row_hit;
reg sdram_tmrbankmachine7_row_open;
reg sdram_tmrbankmachine7_row_close;
reg sdram_tmrbankmachine7_row_col_n_addr_sel;
wire sdram_tmrbankmachine7_twtpcon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_twtpcon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_twtpcon_count = 3'd0;
wire sdram_tmrbankmachine7_twtpcon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_twtpcon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_twtpcon2_count = 3'd0;
wire sdram_tmrbankmachine7_twtpcon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_twtpcon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_twtpcon3_count = 3'd0;
wire sdram_tmrbankmachine7_twtpVote_control;
wire sdram_tmrbankmachine7_trccon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_trccon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_trccon_count = 3'd0;
wire sdram_tmrbankmachine7_trccon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_trccon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_trccon2_count = 3'd0;
wire sdram_tmrbankmachine7_trccon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_trccon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_trccon3_count = 3'd0;
wire sdram_tmrbankmachine7_trcVote_control;
wire sdram_tmrbankmachine7_trascon_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_trascon_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_trascon_count = 3'd0;
wire sdram_tmrbankmachine7_trascon2_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_trascon2_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_trascon2_count = 3'd0;
wire sdram_tmrbankmachine7_trascon3_valid;
(* no_retiming = "true" *) reg sdram_tmrbankmachine7_trascon3_ready = 1'd0;
reg [2:0] sdram_tmrbankmachine7_trascon3_count = 3'd0;
wire sdram_tmrbankmachine7_trasVote_control;
wire sdram_multiplexer_ras_allowed;
wire sdram_multiplexer_cas_allowed;
wire [1:0] sdram_multiplexer_rdcmdphase;
wire [1:0] sdram_multiplexer_wrcmdphase;
wire sdram_multiplexer_endpoint0_valid;
reg sdram_multiplexer_endpoint0_ready;
wire sdram_multiplexer_endpoint0_first;
wire sdram_multiplexer_endpoint0_last;
wire [13:0] sdram_multiplexer_endpoint0_payload_a;
wire [2:0] sdram_multiplexer_endpoint0_payload_ba;
wire sdram_multiplexer_endpoint0_payload_cas;
wire sdram_multiplexer_endpoint0_payload_ras;
wire sdram_multiplexer_endpoint0_payload_we;
wire sdram_multiplexer_endpoint0_payload_is_cmd;
wire sdram_multiplexer_endpoint0_payload_is_read;
wire sdram_multiplexer_endpoint0_payload_is_write;
wire sdram_multiplexer_endpoint1_valid;
reg sdram_multiplexer_endpoint1_ready;
wire sdram_multiplexer_endpoint1_first;
wire sdram_multiplexer_endpoint1_last;
wire [13:0] sdram_multiplexer_endpoint1_payload_a;
wire [2:0] sdram_multiplexer_endpoint1_payload_ba;
wire sdram_multiplexer_endpoint1_payload_cas;
wire sdram_multiplexer_endpoint1_payload_ras;
wire sdram_multiplexer_endpoint1_payload_we;
wire sdram_multiplexer_endpoint1_payload_is_cmd;
wire sdram_multiplexer_endpoint1_payload_is_read;
wire sdram_multiplexer_endpoint1_payload_is_write;
wire sdram_multiplexer_endpoint2_valid;
reg sdram_multiplexer_endpoint2_ready;
wire sdram_multiplexer_endpoint2_first;
wire sdram_multiplexer_endpoint2_last;
wire [13:0] sdram_multiplexer_endpoint2_payload_a;
wire [2:0] sdram_multiplexer_endpoint2_payload_ba;
wire sdram_multiplexer_endpoint2_payload_cas;
wire sdram_multiplexer_endpoint2_payload_ras;
wire sdram_multiplexer_endpoint2_payload_we;
wire sdram_multiplexer_endpoint2_payload_is_cmd;
wire sdram_multiplexer_endpoint2_payload_is_read;
wire sdram_multiplexer_endpoint2_payload_is_write;
wire sdram_multiplexer_endpoint3_valid;
reg sdram_multiplexer_endpoint3_ready;
wire sdram_multiplexer_endpoint3_first;
wire sdram_multiplexer_endpoint3_last;
wire [13:0] sdram_multiplexer_endpoint3_payload_a;
wire [2:0] sdram_multiplexer_endpoint3_payload_ba;
wire sdram_multiplexer_endpoint3_payload_cas;
wire sdram_multiplexer_endpoint3_payload_ras;
wire sdram_multiplexer_endpoint3_payload_we;
wire sdram_multiplexer_endpoint3_payload_is_cmd;
wire sdram_multiplexer_endpoint3_payload_is_read;
wire sdram_multiplexer_endpoint3_payload_is_write;
wire sdram_multiplexer_endpoint4_valid;
reg sdram_multiplexer_endpoint4_ready;
wire sdram_multiplexer_endpoint4_first;
wire sdram_multiplexer_endpoint4_last;
wire [13:0] sdram_multiplexer_endpoint4_payload_a;
wire [2:0] sdram_multiplexer_endpoint4_payload_ba;
wire sdram_multiplexer_endpoint4_payload_cas;
wire sdram_multiplexer_endpoint4_payload_ras;
wire sdram_multiplexer_endpoint4_payload_we;
wire sdram_multiplexer_endpoint4_payload_is_cmd;
wire sdram_multiplexer_endpoint4_payload_is_read;
wire sdram_multiplexer_endpoint4_payload_is_write;
wire sdram_multiplexer_endpoint5_valid;
reg sdram_multiplexer_endpoint5_ready;
wire sdram_multiplexer_endpoint5_first;
wire sdram_multiplexer_endpoint5_last;
wire [13:0] sdram_multiplexer_endpoint5_payload_a;
wire [2:0] sdram_multiplexer_endpoint5_payload_ba;
wire sdram_multiplexer_endpoint5_payload_cas;
wire sdram_multiplexer_endpoint5_payload_ras;
wire sdram_multiplexer_endpoint5_payload_we;
wire sdram_multiplexer_endpoint5_payload_is_cmd;
wire sdram_multiplexer_endpoint5_payload_is_read;
wire sdram_multiplexer_endpoint5_payload_is_write;
wire sdram_multiplexer_endpoint6_valid;
reg sdram_multiplexer_endpoint6_ready;
wire sdram_multiplexer_endpoint6_first;
wire sdram_multiplexer_endpoint6_last;
wire [13:0] sdram_multiplexer_endpoint6_payload_a;
wire [2:0] sdram_multiplexer_endpoint6_payload_ba;
wire sdram_multiplexer_endpoint6_payload_cas;
wire sdram_multiplexer_endpoint6_payload_ras;
wire sdram_multiplexer_endpoint6_payload_we;
wire sdram_multiplexer_endpoint6_payload_is_cmd;
wire sdram_multiplexer_endpoint6_payload_is_read;
wire sdram_multiplexer_endpoint6_payload_is_write;
wire sdram_multiplexer_endpoint7_valid;
reg sdram_multiplexer_endpoint7_ready;
wire sdram_multiplexer_endpoint7_first;
wire sdram_multiplexer_endpoint7_last;
wire [13:0] sdram_multiplexer_endpoint7_payload_a;
wire [2:0] sdram_multiplexer_endpoint7_payload_ba;
wire sdram_multiplexer_endpoint7_payload_cas;
wire sdram_multiplexer_endpoint7_payload_ras;
wire sdram_multiplexer_endpoint7_payload_we;
wire sdram_multiplexer_endpoint7_payload_is_cmd;
wire sdram_multiplexer_endpoint7_payload_is_read;
wire sdram_multiplexer_endpoint7_payload_is_write;
wire sdram_multiplexer_control0;
wire sdram_multiplexer_control1;
wire sdram_multiplexer_control2;
wire [13:0] sdram_multiplexer_control3;
wire [2:0] sdram_multiplexer_control4;
wire sdram_multiplexer_control5;
wire sdram_multiplexer_control6;
wire sdram_multiplexer_control7;
wire sdram_multiplexer_control8;
wire sdram_multiplexer_control9;
wire sdram_multiplexer_control10;
wire sdram_multiplexer_control11;
wire sdram_multiplexer_control12;
wire sdram_multiplexer_control13;
wire [13:0] sdram_multiplexer_control14;
wire [2:0] sdram_multiplexer_control15;
wire sdram_multiplexer_control16;
wire sdram_multiplexer_control17;
wire sdram_multiplexer_control18;
wire sdram_multiplexer_control19;
wire sdram_multiplexer_control20;
wire sdram_multiplexer_control21;
wire sdram_multiplexer_control22;
wire sdram_multiplexer_control23;
wire sdram_multiplexer_control24;
wire [13:0] sdram_multiplexer_control25;
wire [2:0] sdram_multiplexer_control26;
wire sdram_multiplexer_control27;
wire sdram_multiplexer_control28;
wire sdram_multiplexer_control29;
wire sdram_multiplexer_control30;
wire sdram_multiplexer_control31;
wire sdram_multiplexer_control32;
wire sdram_multiplexer_control33;
wire sdram_multiplexer_control34;
wire sdram_multiplexer_control35;
wire [13:0] sdram_multiplexer_control36;
wire [2:0] sdram_multiplexer_control37;
wire sdram_multiplexer_control38;
wire sdram_multiplexer_control39;
wire sdram_multiplexer_control40;
wire sdram_multiplexer_control41;
wire sdram_multiplexer_control42;
wire sdram_multiplexer_control43;
wire sdram_multiplexer_control44;
wire sdram_multiplexer_control45;
wire sdram_multiplexer_control46;
wire [13:0] sdram_multiplexer_control47;
wire [2:0] sdram_multiplexer_control48;
wire sdram_multiplexer_control49;
wire sdram_multiplexer_control50;
wire sdram_multiplexer_control51;
wire sdram_multiplexer_control52;
wire sdram_multiplexer_control53;
wire sdram_multiplexer_control54;
wire sdram_multiplexer_control55;
wire sdram_multiplexer_control56;
wire sdram_multiplexer_control57;
wire [13:0] sdram_multiplexer_control58;
wire [2:0] sdram_multiplexer_control59;
wire sdram_multiplexer_control60;
wire sdram_multiplexer_control61;
wire sdram_multiplexer_control62;
wire sdram_multiplexer_control63;
wire sdram_multiplexer_control64;
wire sdram_multiplexer_control65;
wire sdram_multiplexer_control66;
wire sdram_multiplexer_control67;
wire sdram_multiplexer_control68;
wire [13:0] sdram_multiplexer_control69;
wire [2:0] sdram_multiplexer_control70;
wire sdram_multiplexer_control71;
wire sdram_multiplexer_control72;
wire sdram_multiplexer_control73;
wire sdram_multiplexer_control74;
wire sdram_multiplexer_control75;
wire sdram_multiplexer_control76;
wire sdram_multiplexer_control77;
wire sdram_multiplexer_control78;
wire sdram_multiplexer_control79;
wire [13:0] sdram_multiplexer_control80;
wire [2:0] sdram_multiplexer_control81;
wire sdram_multiplexer_control82;
wire sdram_multiplexer_control83;
wire sdram_multiplexer_control84;
wire sdram_multiplexer_control85;
wire sdram_multiplexer_control86;
wire sdram_multiplexer_control87;
reg sdram_multiplexer_choose_cmd_want_reads = 1'd0;
reg sdram_multiplexer_choose_cmd_want_writes = 1'd0;
reg sdram_multiplexer_choose_cmd_want_cmds = 1'd0;
reg sdram_multiplexer_choose_cmd_want_activates;
wire sdram_multiplexer_choose_cmd_cmd_valid;
reg sdram_multiplexer_choose_cmd_cmd_ready;
wire [13:0] sdram_multiplexer_choose_cmd_cmd_payload_a;
wire [2:0] sdram_multiplexer_choose_cmd_cmd_payload_ba;
reg sdram_multiplexer_choose_cmd_cmd_payload_cas;
reg sdram_multiplexer_choose_cmd_cmd_payload_ras;
reg sdram_multiplexer_choose_cmd_cmd_payload_we;
wire sdram_multiplexer_choose_cmd_cmd_payload_is_cmd;
wire sdram_multiplexer_choose_cmd_cmd_payload_is_read;
wire sdram_multiplexer_choose_cmd_cmd_payload_is_write;
reg [7:0] sdram_multiplexer_choose_cmd_valids;
wire [7:0] sdram_multiplexer_choose_cmd_request;
reg [2:0] sdram_multiplexer_choose_cmd_grant = 3'd0;
wire sdram_multiplexer_choose_cmd_ce;
reg sdram_multiplexer_choose_req_want_reads;
reg sdram_multiplexer_choose_req_want_writes;
reg sdram_multiplexer_choose_req_want_cmds = 1'd0;
reg sdram_multiplexer_choose_req_want_activates = 1'd0;
wire sdram_multiplexer_choose_req_cmd_valid;
reg sdram_multiplexer_choose_req_cmd_ready;
wire [13:0] sdram_multiplexer_choose_req_cmd_payload_a;
wire [2:0] sdram_multiplexer_choose_req_cmd_payload_ba;
reg sdram_multiplexer_choose_req_cmd_payload_cas;
reg sdram_multiplexer_choose_req_cmd_payload_ras;
reg sdram_multiplexer_choose_req_cmd_payload_we;
wire sdram_multiplexer_choose_req_cmd_payload_is_cmd;
wire sdram_multiplexer_choose_req_cmd_payload_is_read;
wire sdram_multiplexer_choose_req_cmd_payload_is_write;
reg [7:0] sdram_multiplexer_choose_req_valids;
wire [7:0] sdram_multiplexer_choose_req_request;
reg [2:0] sdram_multiplexer_choose_req_grant = 3'd0;
wire sdram_multiplexer_choose_req_ce;
wire sdram_multiplexer_refreshCmd_valid;
reg sdram_multiplexer_refreshCmd_ready;
wire sdram_multiplexer_refreshCmd_first;
wire sdram_multiplexer_refreshCmd_last;
wire [13:0] sdram_multiplexer_refreshCmd_payload_a;
wire [2:0] sdram_multiplexer_refreshCmd_payload_ba;
wire sdram_multiplexer_refreshCmd_payload_cas;
wire sdram_multiplexer_refreshCmd_payload_ras;
wire sdram_multiplexer_refreshCmd_payload_we;
wire sdram_multiplexer_refreshCmd_payload_is_cmd;
wire sdram_multiplexer_refreshCmd_payload_is_read;
wire sdram_multiplexer_refreshCmd_payload_is_write;
wire sdram_multiplexer_control88;
wire sdram_multiplexer_control89;
wire sdram_multiplexer_control90;
wire [13:0] sdram_multiplexer_control91;
wire [2:0] sdram_multiplexer_control92;
wire sdram_multiplexer_control93;
wire sdram_multiplexer_control94;
wire sdram_multiplexer_control95;
wire sdram_multiplexer_control96;
wire sdram_multiplexer_control97;
wire sdram_multiplexer_control98;
reg [13:0] sdram_multiplexer_nop_a = 14'd0;
reg [2:0] sdram_multiplexer_nop_ba = 3'd0;
reg [1:0] sdram_multiplexer_steerer0;
reg [1:0] sdram_multiplexer_steerer1;
reg [1:0] sdram_multiplexer_steerer2;
reg [1:0] sdram_multiplexer_steerer3;
reg sdram_multiplexer_steerer4 = 1'd1;
reg sdram_multiplexer_steerer5 = 1'd1;
reg sdram_multiplexer_steerer6 = 1'd1;
reg sdram_multiplexer_steerer7 = 1'd1;
reg sdram_multiplexer_steerer8 = 1'd1;
reg sdram_multiplexer_steerer9 = 1'd1;
reg sdram_multiplexer_steerer10 = 1'd1;
reg sdram_multiplexer_steerer11 = 1'd1;
wire sdram_multiplexer_trrdcon_valid;
(* no_retiming = "true" *) reg sdram_multiplexer_trrdcon_ready = 1'd0;
reg sdram_multiplexer_trrdcon_count = 1'd0;
wire sdram_multiplexer_tfawcon_valid;
(* no_retiming = "true" *) reg sdram_multiplexer_tfawcon_ready = 1'd1;
wire [2:0] sdram_multiplexer_tfawcon_count;
reg [4:0] sdram_multiplexer_tfawcon_window = 5'd0;
wire sdram_multiplexer_tccdcon_valid;
(* no_retiming = "true" *) reg sdram_multiplexer_tccdcon_ready = 1'd0;
reg sdram_multiplexer_tccdcon_count = 1'd0;
wire sdram_multiplexer_twtrcon_valid;
(* no_retiming = "true" *) reg sdram_multiplexer_twtrcon_ready = 1'd0;
reg [2:0] sdram_multiplexer_twtrcon_count = 3'd0;
wire sdram_multiplexer_read_available;
wire sdram_multiplexer_write_available;
reg sdram_multiplexer_en0;
wire sdram_multiplexer_max_time0;
reg [4:0] sdram_multiplexer_time0 = 5'd0;
reg sdram_multiplexer_en1;
wire sdram_multiplexer_max_time1;
reg [3:0] sdram_multiplexer_time1 = 4'd0;
wire sdram_multiplexer_go_to_refresh;
wire [255:0] sdram_multiplexer_control99;
wire [31:0] sdram_multiplexer_control100;
reg port_cmd_valid = 1'd0;
wire port_cmd_ready;
reg port_cmd_payload_we = 1'd0;
wire [2:0] port_TMRcmd_ready;
wire port_wdata_ready;
reg [255:0] port_wdata_payload_data = 256'd0;
reg [31:0] port_wdata_payload_we = 32'd0;
wire [2:0] port_TMRwdata_ready;
wire [767:0] port_TMRwdata_payload_data;
wire [95:0] port_TMRwdata_payload_we;
wire port_rdata_valid;
wire [255:0] port_rdata_payload_data;
wire [2:0] port_TMRrdata_valid;
wire [767:0] port_TMRrdata_payload_data;
reg [1:0] tmrrefresher_state = 2'd0;
reg [1:0] tmrrefresher_next_state;
reg [3:0] tmrbankmachine0_state = 4'd0;
reg [3:0] tmrbankmachine0_next_state;
reg [3:0] tmrbankmachine1_state = 4'd0;
reg [3:0] tmrbankmachine1_next_state;
reg [3:0] tmrbankmachine2_state = 4'd0;
reg [3:0] tmrbankmachine2_next_state;
reg [3:0] tmrbankmachine3_state = 4'd0;
reg [3:0] tmrbankmachine3_next_state;
reg [3:0] tmrbankmachine4_state = 4'd0;
reg [3:0] tmrbankmachine4_next_state;
reg [3:0] tmrbankmachine5_state = 4'd0;
reg [3:0] tmrbankmachine5_next_state;
reg [3:0] tmrbankmachine6_state = 4'd0;
reg [3:0] tmrbankmachine6_next_state;
reg [3:0] tmrbankmachine7_state = 4'd0;
reg [3:0] tmrbankmachine7_next_state;
reg [3:0] multiplexer_state = 4'd0;
reg [3:0] multiplexer_next_state;
wire roundrobin0_request;
wire roundrobin0_grant;
wire roundrobin0_ce;
wire roundrobin1_request;
wire roundrobin1_grant;
wire roundrobin1_ce;
wire roundrobin2_request;
wire roundrobin2_grant;
wire roundrobin2_ce;
wire roundrobin3_request;
wire roundrobin3_grant;
wire roundrobin3_ce;
wire roundrobin4_request;
wire roundrobin4_grant;
wire roundrobin4_ce;
wire roundrobin5_request;
wire roundrobin5_grant;
wire roundrobin5_ce;
wire roundrobin6_request;
wire roundrobin6_grant;
wire roundrobin6_ce;
wire roundrobin7_request;
wire roundrobin7_grant;
wire roundrobin7_ce;
wire control0;
wire control1;
wire control2;
wire control3;
reg locked0 = 1'd0;
wire control4;
wire control5;
wire control6;
wire control7;
reg locked1 = 1'd0;
wire control8;
wire control9;
wire control10;
wire control11;
reg locked2 = 1'd0;
wire control12;
wire control13;
wire control14;
wire control15;
reg locked3 = 1'd0;
wire control16;
wire control17;
wire control18;
wire control19;
reg locked4 = 1'd0;
wire control20;
wire control21;
wire control22;
wire control23;
reg locked5 = 1'd0;
wire control24;
wire control25;
wire control26;
wire control27;
reg locked6 = 1'd0;
wire control28;
wire control29;
wire control30;
wire control31;
reg locked7 = 1'd0;
reg new_master_wdata_ready0 = 1'd0;
reg new_master_wdata_ready1 = 1'd0;
reg new_master_rdata_valid0 = 1'd0;
reg new_master_rdata_valid1 = 1'd0;
reg new_master_rdata_valid2 = 1'd0;
reg new_master_rdata_valid3 = 1'd0;
reg new_master_rdata_valid4 = 1'd0;
reg new_master_rdata_valid5 = 1'd0;
reg new_master_rdata_valid6 = 1'd0;
reg new_master_rdata_valid7 = 1'd0;
reg new_master_rdata_valid8 = 1'd0;
wire control32;
wire control33;
wire control34;
wire [255:0] control35;
wire [41:0] slice_proxy0;
wire [41:0] slice_proxy1;
wire [41:0] slice_proxy2;
wire [41:0] slice_proxy3;
wire [41:0] slice_proxy4;
wire [41:0] slice_proxy5;
wire [8:0] slice_proxy6;
wire [8:0] slice_proxy7;
wire [8:0] slice_proxy8;
wire [8:0] slice_proxy9;
wire [8:0] slice_proxy10;
wire [8:0] slice_proxy11;
wire [2:0] slice_proxy12;
wire [2:0] slice_proxy13;
wire [2:0] slice_proxy14;
wire [2:0] slice_proxy15;
wire [2:0] slice_proxy16;
wire [2:0] slice_proxy17;
wire [2:0] slice_proxy18;
wire [2:0] slice_proxy19;
wire [2:0] slice_proxy20;
wire [2:0] slice_proxy21;
wire [2:0] slice_proxy22;
wire [2:0] slice_proxy23;
wire [2:0] slice_proxy24;
wire [2:0] slice_proxy25;
wire [2:0] slice_proxy26;
wire [2:0] slice_proxy27;
wire [2:0] slice_proxy28;
wire [2:0] slice_proxy29;
wire [2:0] slice_proxy30;
wire [2:0] slice_proxy31;
wire [2:0] slice_proxy32;
wire [2:0] slice_proxy33;
wire [2:0] slice_proxy34;
wire [2:0] slice_proxy35;
wire [2:0] slice_proxy36;
wire [2:0] slice_proxy37;
wire [2:0] slice_proxy38;
wire [2:0] slice_proxy39;
wire [2:0] slice_proxy40;
wire [2:0] slice_proxy41;
wire [2:0] slice_proxy42;
wire [2:0] slice_proxy43;
wire [2:0] slice_proxy44;
wire [2:0] slice_proxy45;
wire [2:0] slice_proxy46;
wire [2:0] slice_proxy47;
wire [2:0] slice_proxy48;
wire [2:0] slice_proxy49;
wire [2:0] slice_proxy50;
wire [2:0] slice_proxy51;
wire [2:0] slice_proxy52;
wire [2:0] slice_proxy53;
wire [2:0] slice_proxy54;
wire [2:0] slice_proxy55;
wire [2:0] slice_proxy56;
wire [2:0] slice_proxy57;
wire [2:0] slice_proxy58;
wire [2:0] slice_proxy59;
wire [191:0] slice_proxy60;
wire [191:0] slice_proxy61;
wire [191:0] slice_proxy62;
wire [191:0] slice_proxy63;
wire [191:0] slice_proxy64;
wire [191:0] slice_proxy65;
wire [2:0] slice_proxy66;
wire [2:0] slice_proxy67;
wire [2:0] slice_proxy68;
wire [2:0] slice_proxy69;
wire [2:0] slice_proxy70;
wire [2:0] slice_proxy71;
wire [23:0] slice_proxy72;
wire [23:0] slice_proxy73;
wire [23:0] slice_proxy74;
wire [23:0] slice_proxy75;
wire [23:0] slice_proxy76;
wire [23:0] slice_proxy77;
wire [2:0] slice_proxy78;
wire [2:0] slice_proxy79;
wire [2:0] slice_proxy80;
wire [2:0] slice_proxy81;
wire [2:0] slice_proxy82;
wire [2:0] slice_proxy83;
wire [41:0] slice_proxy84;
wire [41:0] slice_proxy85;
wire [41:0] slice_proxy86;
wire [41:0] slice_proxy87;
wire [41:0] slice_proxy88;
wire [41:0] slice_proxy89;
wire [8:0] slice_proxy90;
wire [8:0] slice_proxy91;
wire [8:0] slice_proxy92;
wire [8:0] slice_proxy93;
wire [8:0] slice_proxy94;
wire [8:0] slice_proxy95;
wire [2:0] slice_proxy96;
wire [2:0] slice_proxy97;
wire [2:0] slice_proxy98;
wire [2:0] slice_proxy99;
wire [2:0] slice_proxy100;
wire [2:0] slice_proxy101;
wire [2:0] slice_proxy102;
wire [2:0] slice_proxy103;
wire [2:0] slice_proxy104;
wire [2:0] slice_proxy105;
wire [2:0] slice_proxy106;
wire [2:0] slice_proxy107;
wire [2:0] slice_proxy108;
wire [2:0] slice_proxy109;
wire [2:0] slice_proxy110;
wire [2:0] slice_proxy111;
wire [2:0] slice_proxy112;
wire [2:0] slice_proxy113;
wire [2:0] slice_proxy114;
wire [2:0] slice_proxy115;
wire [2:0] slice_proxy116;
wire [2:0] slice_proxy117;
wire [2:0] slice_proxy118;
wire [2:0] slice_proxy119;
wire [2:0] slice_proxy120;
wire [2:0] slice_proxy121;
wire [2:0] slice_proxy122;
wire [2:0] slice_proxy123;
wire [2:0] slice_proxy124;
wire [2:0] slice_proxy125;
wire [2:0] slice_proxy126;
wire [2:0] slice_proxy127;
wire [2:0] slice_proxy128;
wire [2:0] slice_proxy129;
wire [2:0] slice_proxy130;
wire [2:0] slice_proxy131;
wire [2:0] slice_proxy132;
wire [2:0] slice_proxy133;
wire [2:0] slice_proxy134;
wire [2:0] slice_proxy135;
wire [2:0] slice_proxy136;
wire [2:0] slice_proxy137;
wire [2:0] slice_proxy138;
wire [2:0] slice_proxy139;
wire [2:0] slice_proxy140;
wire [2:0] slice_proxy141;
wire [2:0] slice_proxy142;
wire [2:0] slice_proxy143;
wire [191:0] slice_proxy144;
wire [191:0] slice_proxy145;
wire [191:0] slice_proxy146;
wire [191:0] slice_proxy147;
wire [191:0] slice_proxy148;
wire [191:0] slice_proxy149;
wire [2:0] slice_proxy150;
wire [2:0] slice_proxy151;
wire [2:0] slice_proxy152;
wire [2:0] slice_proxy153;
wire [2:0] slice_proxy154;
wire [2:0] slice_proxy155;
wire [23:0] slice_proxy156;
wire [23:0] slice_proxy157;
wire [23:0] slice_proxy158;
wire [23:0] slice_proxy159;
wire [23:0] slice_proxy160;
wire [23:0] slice_proxy161;
wire [2:0] slice_proxy162;
wire [2:0] slice_proxy163;
wire [2:0] slice_proxy164;
wire [2:0] slice_proxy165;
wire [2:0] slice_proxy166;
wire [2:0] slice_proxy167;
wire [41:0] slice_proxy168;
wire [41:0] slice_proxy169;
wire [41:0] slice_proxy170;
wire [41:0] slice_proxy171;
wire [41:0] slice_proxy172;
wire [41:0] slice_proxy173;
wire [8:0] slice_proxy174;
wire [8:0] slice_proxy175;
wire [8:0] slice_proxy176;
wire [8:0] slice_proxy177;
wire [8:0] slice_proxy178;
wire [8:0] slice_proxy179;
wire [2:0] slice_proxy180;
wire [2:0] slice_proxy181;
wire [2:0] slice_proxy182;
wire [2:0] slice_proxy183;
wire [2:0] slice_proxy184;
wire [2:0] slice_proxy185;
wire [2:0] slice_proxy186;
wire [2:0] slice_proxy187;
wire [2:0] slice_proxy188;
wire [2:0] slice_proxy189;
wire [2:0] slice_proxy190;
wire [2:0] slice_proxy191;
wire [2:0] slice_proxy192;
wire [2:0] slice_proxy193;
wire [2:0] slice_proxy194;
wire [2:0] slice_proxy195;
wire [2:0] slice_proxy196;
wire [2:0] slice_proxy197;
wire [2:0] slice_proxy198;
wire [2:0] slice_proxy199;
wire [2:0] slice_proxy200;
wire [2:0] slice_proxy201;
wire [2:0] slice_proxy202;
wire [2:0] slice_proxy203;
wire [2:0] slice_proxy204;
wire [2:0] slice_proxy205;
wire [2:0] slice_proxy206;
wire [2:0] slice_proxy207;
wire [2:0] slice_proxy208;
wire [2:0] slice_proxy209;
wire [2:0] slice_proxy210;
wire [2:0] slice_proxy211;
wire [2:0] slice_proxy212;
wire [2:0] slice_proxy213;
wire [2:0] slice_proxy214;
wire [2:0] slice_proxy215;
wire [2:0] slice_proxy216;
wire [2:0] slice_proxy217;
wire [2:0] slice_proxy218;
wire [2:0] slice_proxy219;
wire [2:0] slice_proxy220;
wire [2:0] slice_proxy221;
wire [2:0] slice_proxy222;
wire [2:0] slice_proxy223;
wire [2:0] slice_proxy224;
wire [2:0] slice_proxy225;
wire [2:0] slice_proxy226;
wire [2:0] slice_proxy227;
wire [191:0] slice_proxy228;
wire [191:0] slice_proxy229;
wire [191:0] slice_proxy230;
wire [191:0] slice_proxy231;
wire [191:0] slice_proxy232;
wire [191:0] slice_proxy233;
wire [2:0] slice_proxy234;
wire [2:0] slice_proxy235;
wire [2:0] slice_proxy236;
wire [2:0] slice_proxy237;
wire [2:0] slice_proxy238;
wire [2:0] slice_proxy239;
wire [23:0] slice_proxy240;
wire [23:0] slice_proxy241;
wire [23:0] slice_proxy242;
wire [23:0] slice_proxy243;
wire [23:0] slice_proxy244;
wire [23:0] slice_proxy245;
wire [2:0] slice_proxy246;
wire [2:0] slice_proxy247;
wire [2:0] slice_proxy248;
wire [2:0] slice_proxy249;
wire [2:0] slice_proxy250;
wire [2:0] slice_proxy251;
wire [41:0] slice_proxy252;
wire [41:0] slice_proxy253;
wire [41:0] slice_proxy254;
wire [41:0] slice_proxy255;
wire [41:0] slice_proxy256;
wire [41:0] slice_proxy257;
wire [8:0] slice_proxy258;
wire [8:0] slice_proxy259;
wire [8:0] slice_proxy260;
wire [8:0] slice_proxy261;
wire [8:0] slice_proxy262;
wire [8:0] slice_proxy263;
wire [2:0] slice_proxy264;
wire [2:0] slice_proxy265;
wire [2:0] slice_proxy266;
wire [2:0] slice_proxy267;
wire [2:0] slice_proxy268;
wire [2:0] slice_proxy269;
wire [2:0] slice_proxy270;
wire [2:0] slice_proxy271;
wire [2:0] slice_proxy272;
wire [2:0] slice_proxy273;
wire [2:0] slice_proxy274;
wire [2:0] slice_proxy275;
wire [2:0] slice_proxy276;
wire [2:0] slice_proxy277;
wire [2:0] slice_proxy278;
wire [2:0] slice_proxy279;
wire [2:0] slice_proxy280;
wire [2:0] slice_proxy281;
wire [2:0] slice_proxy282;
wire [2:0] slice_proxy283;
wire [2:0] slice_proxy284;
wire [2:0] slice_proxy285;
wire [2:0] slice_proxy286;
wire [2:0] slice_proxy287;
wire [2:0] slice_proxy288;
wire [2:0] slice_proxy289;
wire [2:0] slice_proxy290;
wire [2:0] slice_proxy291;
wire [2:0] slice_proxy292;
wire [2:0] slice_proxy293;
wire [2:0] slice_proxy294;
wire [2:0] slice_proxy295;
wire [2:0] slice_proxy296;
wire [2:0] slice_proxy297;
wire [2:0] slice_proxy298;
wire [2:0] slice_proxy299;
wire [2:0] slice_proxy300;
wire [2:0] slice_proxy301;
wire [2:0] slice_proxy302;
wire [2:0] slice_proxy303;
wire [2:0] slice_proxy304;
wire [2:0] slice_proxy305;
wire [2:0] slice_proxy306;
wire [2:0] slice_proxy307;
wire [2:0] slice_proxy308;
wire [2:0] slice_proxy309;
wire [2:0] slice_proxy310;
wire [2:0] slice_proxy311;
wire [191:0] slice_proxy312;
wire [191:0] slice_proxy313;
wire [191:0] slice_proxy314;
wire [191:0] slice_proxy315;
wire [191:0] slice_proxy316;
wire [191:0] slice_proxy317;
wire [2:0] slice_proxy318;
wire [2:0] slice_proxy319;
wire [2:0] slice_proxy320;
wire [2:0] slice_proxy321;
wire [2:0] slice_proxy322;
wire [2:0] slice_proxy323;
wire [23:0] slice_proxy324;
wire [23:0] slice_proxy325;
wire [23:0] slice_proxy326;
wire [23:0] slice_proxy327;
wire [23:0] slice_proxy328;
wire [23:0] slice_proxy329;
wire [2:0] slice_proxy330;
wire [2:0] slice_proxy331;
wire [2:0] slice_proxy332;
wire [2:0] slice_proxy333;
wire [2:0] slice_proxy334;
wire [2:0] slice_proxy335;
wire [2:0] slice_proxy336;
wire [2:0] slice_proxy337;
wire [2:0] slice_proxy338;
wire [2:0] slice_proxy339;
wire [2:0] slice_proxy340;
wire [2:0] slice_proxy341;
wire [2:0] slice_proxy342;
wire [2:0] slice_proxy343;
wire [2:0] slice_proxy344;
wire [2:0] slice_proxy345;
wire [2:0] slice_proxy346;
wire [2:0] slice_proxy347;
wire [2:0] slice_proxy348;
wire [2:0] slice_proxy349;
wire [2:0] slice_proxy350;
wire [2:0] slice_proxy351;
wire [2:0] slice_proxy352;
wire [2:0] slice_proxy353;
wire [2:0] slice_proxy354;
wire [2:0] slice_proxy355;
wire [2:0] slice_proxy356;
wire [2:0] slice_proxy357;
wire [2:0] slice_proxy358;
wire [2:0] slice_proxy359;
wire [62:0] slice_proxy360;
wire [62:0] slice_proxy361;
wire [62:0] slice_proxy362;
wire [62:0] slice_proxy363;
wire [62:0] slice_proxy364;
wire [62:0] slice_proxy365;
wire [62:0] slice_proxy366;
wire [62:0] slice_proxy367;
wire [62:0] slice_proxy368;
wire [62:0] slice_proxy369;
wire [62:0] slice_proxy370;
wire [62:0] slice_proxy371;
wire [2:0] slice_proxy372;
wire [2:0] slice_proxy373;
wire [2:0] slice_proxy374;
wire [2:0] slice_proxy375;
wire [2:0] slice_proxy376;
wire [2:0] slice_proxy377;
wire [2:0] slice_proxy378;
wire [2:0] slice_proxy379;
wire [2:0] slice_proxy380;
wire [2:0] slice_proxy381;
wire [2:0] slice_proxy382;
wire [2:0] slice_proxy383;
wire [2:0] slice_proxy384;
wire [2:0] slice_proxy385;
wire [2:0] slice_proxy386;
wire [2:0] slice_proxy387;
wire [2:0] slice_proxy388;
wire [2:0] slice_proxy389;
wire [2:0] slice_proxy390;
wire [2:0] slice_proxy391;
wire [2:0] slice_proxy392;
wire [2:0] slice_proxy393;
wire [2:0] slice_proxy394;
wire [2:0] slice_proxy395;
wire [2:0] slice_proxy396;
wire [2:0] slice_proxy397;
wire [2:0] slice_proxy398;
wire [2:0] slice_proxy399;
wire [2:0] slice_proxy400;
wire [2:0] slice_proxy401;
wire [2:0] slice_proxy402;
wire [2:0] slice_proxy403;
wire [2:0] slice_proxy404;
wire [2:0] slice_proxy405;
wire [2:0] slice_proxy406;
wire [2:0] slice_proxy407;
wire [2:0] slice_proxy408;
wire [2:0] slice_proxy409;
wire [2:0] slice_proxy410;
wire [2:0] slice_proxy411;
wire [2:0] slice_proxy412;
wire [2:0] slice_proxy413;
wire [62:0] slice_proxy414;
wire [62:0] slice_proxy415;
wire [62:0] slice_proxy416;
wire [62:0] slice_proxy417;
wire [62:0] slice_proxy418;
wire [62:0] slice_proxy419;
wire [62:0] slice_proxy420;
wire [62:0] slice_proxy421;
wire [62:0] slice_proxy422;
wire [62:0] slice_proxy423;
wire [62:0] slice_proxy424;
wire [62:0] slice_proxy425;
wire [2:0] slice_proxy426;
wire [2:0] slice_proxy427;
wire [2:0] slice_proxy428;
wire [2:0] slice_proxy429;
wire [2:0] slice_proxy430;
wire [2:0] slice_proxy431;
wire [2:0] slice_proxy432;
wire [2:0] slice_proxy433;
wire [2:0] slice_proxy434;
wire [2:0] slice_proxy435;
wire [2:0] slice_proxy436;
wire [2:0] slice_proxy437;
wire [2:0] slice_proxy438;
wire [2:0] slice_proxy439;
wire [2:0] slice_proxy440;
wire [2:0] slice_proxy441;
wire [2:0] slice_proxy442;
wire [2:0] slice_proxy443;
wire [2:0] slice_proxy444;
wire [2:0] slice_proxy445;
wire [2:0] slice_proxy446;
wire [2:0] slice_proxy447;
wire [2:0] slice_proxy448;
wire [2:0] slice_proxy449;
wire [2:0] slice_proxy450;
wire [2:0] slice_proxy451;
wire [2:0] slice_proxy452;
wire [2:0] slice_proxy453;
wire [2:0] slice_proxy454;
wire [2:0] slice_proxy455;
wire [2:0] slice_proxy456;
wire [2:0] slice_proxy457;
wire [2:0] slice_proxy458;
wire [2:0] slice_proxy459;
wire [2:0] slice_proxy460;
wire [2:0] slice_proxy461;
wire [2:0] slice_proxy462;
wire [2:0] slice_proxy463;
wire [2:0] slice_proxy464;
wire [2:0] slice_proxy465;
wire [2:0] slice_proxy466;
wire [2:0] slice_proxy467;
wire [62:0] slice_proxy468;
wire [62:0] slice_proxy469;
wire [62:0] slice_proxy470;
wire [62:0] slice_proxy471;
wire [62:0] slice_proxy472;
wire [62:0] slice_proxy473;
wire [62:0] slice_proxy474;
wire [62:0] slice_proxy475;
wire [62:0] slice_proxy476;
wire [62:0] slice_proxy477;
wire [62:0] slice_proxy478;
wire [62:0] slice_proxy479;
wire [2:0] slice_proxy480;
wire [2:0] slice_proxy481;
wire [2:0] slice_proxy482;
wire [2:0] slice_proxy483;
wire [2:0] slice_proxy484;
wire [2:0] slice_proxy485;
wire [2:0] slice_proxy486;
wire [2:0] slice_proxy487;
wire [2:0] slice_proxy488;
wire [2:0] slice_proxy489;
wire [2:0] slice_proxy490;
wire [2:0] slice_proxy491;
wire [2:0] slice_proxy492;
wire [2:0] slice_proxy493;
wire [2:0] slice_proxy494;
wire [2:0] slice_proxy495;
wire [2:0] slice_proxy496;
wire [2:0] slice_proxy497;
wire [2:0] slice_proxy498;
wire [2:0] slice_proxy499;
wire [2:0] slice_proxy500;
wire [2:0] slice_proxy501;
wire [2:0] slice_proxy502;
wire [2:0] slice_proxy503;
wire [2:0] slice_proxy504;
wire [2:0] slice_proxy505;
wire [2:0] slice_proxy506;
wire [2:0] slice_proxy507;
wire [2:0] slice_proxy508;
wire [2:0] slice_proxy509;
wire [2:0] slice_proxy510;
wire [2:0] slice_proxy511;
wire [2:0] slice_proxy512;
wire [2:0] slice_proxy513;
wire [2:0] slice_proxy514;
wire [2:0] slice_proxy515;
wire [2:0] slice_proxy516;
wire [2:0] slice_proxy517;
wire [2:0] slice_proxy518;
wire [2:0] slice_proxy519;
wire [2:0] slice_proxy520;
wire [2:0] slice_proxy521;
wire [62:0] slice_proxy522;
wire [62:0] slice_proxy523;
wire [62:0] slice_proxy524;
wire [62:0] slice_proxy525;
wire [62:0] slice_proxy526;
wire [62:0] slice_proxy527;
wire [62:0] slice_proxy528;
wire [62:0] slice_proxy529;
wire [62:0] slice_proxy530;
wire [62:0] slice_proxy531;
wire [62:0] slice_proxy532;
wire [62:0] slice_proxy533;
wire [2:0] slice_proxy534;
wire [2:0] slice_proxy535;
wire [2:0] slice_proxy536;
wire [2:0] slice_proxy537;
wire [2:0] slice_proxy538;
wire [2:0] slice_proxy539;
wire [2:0] slice_proxy540;
wire [2:0] slice_proxy541;
wire [2:0] slice_proxy542;
wire [2:0] slice_proxy543;
wire [2:0] slice_proxy544;
wire [2:0] slice_proxy545;
wire [2:0] slice_proxy546;
wire [2:0] slice_proxy547;
wire [2:0] slice_proxy548;
wire [2:0] slice_proxy549;
wire [2:0] slice_proxy550;
wire [2:0] slice_proxy551;
wire [2:0] slice_proxy552;
wire [2:0] slice_proxy553;
wire [2:0] slice_proxy554;
wire [2:0] slice_proxy555;
wire [2:0] slice_proxy556;
wire [2:0] slice_proxy557;
wire [2:0] slice_proxy558;
wire [2:0] slice_proxy559;
wire [2:0] slice_proxy560;
wire [2:0] slice_proxy561;
wire [2:0] slice_proxy562;
wire [2:0] slice_proxy563;
wire [2:0] slice_proxy564;
wire [2:0] slice_proxy565;
wire [2:0] slice_proxy566;
wire [2:0] slice_proxy567;
wire [2:0] slice_proxy568;
wire [2:0] slice_proxy569;
wire [2:0] slice_proxy570;
wire [2:0] slice_proxy571;
wire [2:0] slice_proxy572;
wire [2:0] slice_proxy573;
wire [2:0] slice_proxy574;
wire [2:0] slice_proxy575;
wire [62:0] slice_proxy576;
wire [62:0] slice_proxy577;
wire [62:0] slice_proxy578;
wire [62:0] slice_proxy579;
wire [62:0] slice_proxy580;
wire [62:0] slice_proxy581;
wire [62:0] slice_proxy582;
wire [62:0] slice_proxy583;
wire [62:0] slice_proxy584;
wire [62:0] slice_proxy585;
wire [62:0] slice_proxy586;
wire [62:0] slice_proxy587;
wire [2:0] slice_proxy588;
wire [2:0] slice_proxy589;
wire [2:0] slice_proxy590;
wire [2:0] slice_proxy591;
wire [2:0] slice_proxy592;
wire [2:0] slice_proxy593;
wire [2:0] slice_proxy594;
wire [2:0] slice_proxy595;
wire [2:0] slice_proxy596;
wire [2:0] slice_proxy597;
wire [2:0] slice_proxy598;
wire [2:0] slice_proxy599;
wire [2:0] slice_proxy600;
wire [2:0] slice_proxy601;
wire [2:0] slice_proxy602;
wire [2:0] slice_proxy603;
wire [2:0] slice_proxy604;
wire [2:0] slice_proxy605;
wire [2:0] slice_proxy606;
wire [2:0] slice_proxy607;
wire [2:0] slice_proxy608;
wire [2:0] slice_proxy609;
wire [2:0] slice_proxy610;
wire [2:0] slice_proxy611;
wire [2:0] slice_proxy612;
wire [2:0] slice_proxy613;
wire [2:0] slice_proxy614;
wire [2:0] slice_proxy615;
wire [2:0] slice_proxy616;
wire [2:0] slice_proxy617;
wire [2:0] slice_proxy618;
wire [2:0] slice_proxy619;
wire [2:0] slice_proxy620;
wire [2:0] slice_proxy621;
wire [2:0] slice_proxy622;
wire [2:0] slice_proxy623;
wire [2:0] slice_proxy624;
wire [2:0] slice_proxy625;
wire [2:0] slice_proxy626;
wire [2:0] slice_proxy627;
wire [2:0] slice_proxy628;
wire [2:0] slice_proxy629;
wire [62:0] slice_proxy630;
wire [62:0] slice_proxy631;
wire [62:0] slice_proxy632;
wire [62:0] slice_proxy633;
wire [62:0] slice_proxy634;
wire [62:0] slice_proxy635;
wire [62:0] slice_proxy636;
wire [62:0] slice_proxy637;
wire [62:0] slice_proxy638;
wire [62:0] slice_proxy639;
wire [62:0] slice_proxy640;
wire [62:0] slice_proxy641;
wire [2:0] slice_proxy642;
wire [2:0] slice_proxy643;
wire [2:0] slice_proxy644;
wire [2:0] slice_proxy645;
wire [2:0] slice_proxy646;
wire [2:0] slice_proxy647;
wire [2:0] slice_proxy648;
wire [2:0] slice_proxy649;
wire [2:0] slice_proxy650;
wire [2:0] slice_proxy651;
wire [2:0] slice_proxy652;
wire [2:0] slice_proxy653;
wire [2:0] slice_proxy654;
wire [2:0] slice_proxy655;
wire [2:0] slice_proxy656;
wire [2:0] slice_proxy657;
wire [2:0] slice_proxy658;
wire [2:0] slice_proxy659;
wire [2:0] slice_proxy660;
wire [2:0] slice_proxy661;
wire [2:0] slice_proxy662;
wire [2:0] slice_proxy663;
wire [2:0] slice_proxy664;
wire [2:0] slice_proxy665;
wire [2:0] slice_proxy666;
wire [2:0] slice_proxy667;
wire [2:0] slice_proxy668;
wire [2:0] slice_proxy669;
wire [2:0] slice_proxy670;
wire [2:0] slice_proxy671;
wire [2:0] slice_proxy672;
wire [2:0] slice_proxy673;
wire [2:0] slice_proxy674;
wire [2:0] slice_proxy675;
wire [2:0] slice_proxy676;
wire [2:0] slice_proxy677;
wire [2:0] slice_proxy678;
wire [2:0] slice_proxy679;
wire [2:0] slice_proxy680;
wire [2:0] slice_proxy681;
wire [2:0] slice_proxy682;
wire [2:0] slice_proxy683;
wire [62:0] slice_proxy684;
wire [62:0] slice_proxy685;
wire [62:0] slice_proxy686;
wire [62:0] slice_proxy687;
wire [62:0] slice_proxy688;
wire [62:0] slice_proxy689;
wire [62:0] slice_proxy690;
wire [62:0] slice_proxy691;
wire [62:0] slice_proxy692;
wire [62:0] slice_proxy693;
wire [62:0] slice_proxy694;
wire [62:0] slice_proxy695;
wire [2:0] slice_proxy696;
wire [2:0] slice_proxy697;
wire [2:0] slice_proxy698;
wire [2:0] slice_proxy699;
wire [2:0] slice_proxy700;
wire [2:0] slice_proxy701;
wire [2:0] slice_proxy702;
wire [2:0] slice_proxy703;
wire [2:0] slice_proxy704;
wire [2:0] slice_proxy705;
wire [2:0] slice_proxy706;
wire [2:0] slice_proxy707;
wire [2:0] slice_proxy708;
wire [2:0] slice_proxy709;
wire [2:0] slice_proxy710;
wire [2:0] slice_proxy711;
wire [2:0] slice_proxy712;
wire [2:0] slice_proxy713;
wire [2:0] slice_proxy714;
wire [2:0] slice_proxy715;
wire [2:0] slice_proxy716;
wire [2:0] slice_proxy717;
wire [2:0] slice_proxy718;
wire [2:0] slice_proxy719;
wire [2:0] slice_proxy720;
wire [2:0] slice_proxy721;
wire [2:0] slice_proxy722;
wire [2:0] slice_proxy723;
wire [2:0] slice_proxy724;
wire [2:0] slice_proxy725;
wire [2:0] slice_proxy726;
wire [2:0] slice_proxy727;
wire [2:0] slice_proxy728;
wire [2:0] slice_proxy729;
wire [2:0] slice_proxy730;
wire [2:0] slice_proxy731;
wire [2:0] slice_proxy732;
wire [2:0] slice_proxy733;
wire [2:0] slice_proxy734;
wire [2:0] slice_proxy735;
wire [2:0] slice_proxy736;
wire [2:0] slice_proxy737;
wire [62:0] slice_proxy738;
wire [62:0] slice_proxy739;
wire [62:0] slice_proxy740;
wire [62:0] slice_proxy741;
wire [62:0] slice_proxy742;
wire [62:0] slice_proxy743;
wire [62:0] slice_proxy744;
wire [62:0] slice_proxy745;
wire [62:0] slice_proxy746;
wire [62:0] slice_proxy747;
wire [62:0] slice_proxy748;
wire [62:0] slice_proxy749;
wire [2:0] slice_proxy750;
wire [2:0] slice_proxy751;
wire [2:0] slice_proxy752;
wire [2:0] slice_proxy753;
wire [2:0] slice_proxy754;
wire [2:0] slice_proxy755;
wire [2:0] slice_proxy756;
wire [2:0] slice_proxy757;
wire [2:0] slice_proxy758;
wire [2:0] slice_proxy759;
wire [2:0] slice_proxy760;
wire [2:0] slice_proxy761;
wire [2:0] slice_proxy762;
wire [2:0] slice_proxy763;
wire [2:0] slice_proxy764;
wire [2:0] slice_proxy765;
wire [2:0] slice_proxy766;
wire [2:0] slice_proxy767;
wire [2:0] slice_proxy768;
wire [2:0] slice_proxy769;
wire [2:0] slice_proxy770;
wire [2:0] slice_proxy771;
wire [2:0] slice_proxy772;
wire [2:0] slice_proxy773;
wire [2:0] slice_proxy774;
wire [2:0] slice_proxy775;
wire [2:0] slice_proxy776;
wire [2:0] slice_proxy777;
wire [2:0] slice_proxy778;
wire [2:0] slice_proxy779;
wire [2:0] slice_proxy780;
wire [2:0] slice_proxy781;
wire [2:0] slice_proxy782;
wire [2:0] slice_proxy783;
wire [2:0] slice_proxy784;
wire [2:0] slice_proxy785;
wire [95:0] slice_proxy786;
wire [95:0] slice_proxy787;
wire [95:0] slice_proxy788;
wire [95:0] slice_proxy789;
wire [95:0] slice_proxy790;
wire [95:0] slice_proxy791;
reg rhs_array_muxed0;
reg [13:0] rhs_array_muxed1;
reg [2:0] rhs_array_muxed2;
reg rhs_array_muxed3;
reg rhs_array_muxed4;
reg rhs_array_muxed5;
reg t_array_muxed0;
reg t_array_muxed1;
reg t_array_muxed2;
reg rhs_array_muxed6;
reg [13:0] rhs_array_muxed7;
reg [2:0] rhs_array_muxed8;
reg rhs_array_muxed9;
reg rhs_array_muxed10;
reg rhs_array_muxed11;
reg t_array_muxed3;
reg t_array_muxed4;
reg t_array_muxed5;
reg [20:0] rhs_array_muxed12;
reg rhs_array_muxed13;
reg rhs_array_muxed14;
reg [20:0] rhs_array_muxed15;
reg rhs_array_muxed16;
reg rhs_array_muxed17;
reg [20:0] rhs_array_muxed18;
reg rhs_array_muxed19;
reg rhs_array_muxed20;
reg [20:0] rhs_array_muxed21;
reg rhs_array_muxed22;
reg rhs_array_muxed23;
reg [20:0] rhs_array_muxed24;
reg rhs_array_muxed25;
reg rhs_array_muxed26;
reg [20:0] rhs_array_muxed27;
reg rhs_array_muxed28;
reg rhs_array_muxed29;
reg [20:0] rhs_array_muxed30;
reg rhs_array_muxed31;
reg rhs_array_muxed32;
reg [20:0] rhs_array_muxed33;
reg rhs_array_muxed34;
reg rhs_array_muxed35;
reg [2:0] array_muxed0;
reg [13:0] array_muxed1;
reg array_muxed2;
reg array_muxed3;
reg array_muxed4;
reg array_muxed5;
reg array_muxed6;
reg [2:0] array_muxed7;
reg [13:0] array_muxed8;
reg array_muxed9;
reg array_muxed10;
reg array_muxed11;
reg array_muxed12;
reg array_muxed13;
reg [2:0] array_muxed14;
reg [13:0] array_muxed15;
reg array_muxed16;
reg array_muxed17;
reg array_muxed18;
reg array_muxed19;
reg array_muxed20;
reg [2:0] array_muxed21;
reg [13:0] array_muxed22;
reg array_muxed23;
reg array_muxed24;
reg array_muxed25;
reg array_muxed26;
reg array_muxed27;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign ddrphy_dfi_p0_address = sdram_master_p0_address;
assign ddrphy_dfi_p0_bank = sdram_master_p0_bank;
assign ddrphy_dfi_p0_cas_n = sdram_master_p0_cas_n;
assign ddrphy_dfi_p0_cs_n = sdram_master_p0_cs_n;
assign ddrphy_dfi_p0_ras_n = sdram_master_p0_ras_n;
assign ddrphy_dfi_p0_we_n = sdram_master_p0_we_n;
assign ddrphy_dfi_p0_cke = sdram_master_p0_cke;
assign ddrphy_dfi_p0_odt = sdram_master_p0_odt;
assign ddrphy_dfi_p0_reset_n = sdram_master_p0_reset_n;
assign ddrphy_dfi_p0_act_n = sdram_master_p0_act_n;
assign ddrphy_dfi_p0_wrdata = sdram_master_p0_wrdata;
assign ddrphy_dfi_p0_wrdata_en = sdram_master_p0_wrdata_en;
assign ddrphy_dfi_p0_wrdata_mask = sdram_master_p0_wrdata_mask;
assign ddrphy_dfi_p0_rddata_en = sdram_master_p0_rddata_en;
assign sdram_master_p0_rddata = ddrphy_dfi_p0_rddata;
assign sdram_master_p0_rddata_valid = ddrphy_dfi_p0_rddata_valid;
assign ddrphy_dfi_p1_address = sdram_master_p1_address;
assign ddrphy_dfi_p1_bank = sdram_master_p1_bank;
assign ddrphy_dfi_p1_cas_n = sdram_master_p1_cas_n;
assign ddrphy_dfi_p1_cs_n = sdram_master_p1_cs_n;
assign ddrphy_dfi_p1_ras_n = sdram_master_p1_ras_n;
assign ddrphy_dfi_p1_we_n = sdram_master_p1_we_n;
assign ddrphy_dfi_p1_cke = sdram_master_p1_cke;
assign ddrphy_dfi_p1_odt = sdram_master_p1_odt;
assign ddrphy_dfi_p1_reset_n = sdram_master_p1_reset_n;
assign ddrphy_dfi_p1_act_n = sdram_master_p1_act_n;
assign ddrphy_dfi_p1_wrdata = sdram_master_p1_wrdata;
assign ddrphy_dfi_p1_wrdata_en = sdram_master_p1_wrdata_en;
assign ddrphy_dfi_p1_wrdata_mask = sdram_master_p1_wrdata_mask;
assign ddrphy_dfi_p1_rddata_en = sdram_master_p1_rddata_en;
assign sdram_master_p1_rddata = ddrphy_dfi_p1_rddata;
assign sdram_master_p1_rddata_valid = ddrphy_dfi_p1_rddata_valid;
assign ddrphy_dfi_p2_address = sdram_master_p2_address;
assign ddrphy_dfi_p2_bank = sdram_master_p2_bank;
assign ddrphy_dfi_p2_cas_n = sdram_master_p2_cas_n;
assign ddrphy_dfi_p2_cs_n = sdram_master_p2_cs_n;
assign ddrphy_dfi_p2_ras_n = sdram_master_p2_ras_n;
assign ddrphy_dfi_p2_we_n = sdram_master_p2_we_n;
assign ddrphy_dfi_p2_cke = sdram_master_p2_cke;
assign ddrphy_dfi_p2_odt = sdram_master_p2_odt;
assign ddrphy_dfi_p2_reset_n = sdram_master_p2_reset_n;
assign ddrphy_dfi_p2_act_n = sdram_master_p2_act_n;
assign ddrphy_dfi_p2_wrdata = sdram_master_p2_wrdata;
assign ddrphy_dfi_p2_wrdata_en = sdram_master_p2_wrdata_en;
assign ddrphy_dfi_p2_wrdata_mask = sdram_master_p2_wrdata_mask;
assign ddrphy_dfi_p2_rddata_en = sdram_master_p2_rddata_en;
assign sdram_master_p2_rddata = ddrphy_dfi_p2_rddata;
assign sdram_master_p2_rddata_valid = ddrphy_dfi_p2_rddata_valid;
assign ddrphy_dfi_p3_address = sdram_master_p3_address;
assign ddrphy_dfi_p3_bank = sdram_master_p3_bank;
assign ddrphy_dfi_p3_cas_n = sdram_master_p3_cas_n;
assign ddrphy_dfi_p3_cs_n = sdram_master_p3_cs_n;
assign ddrphy_dfi_p3_ras_n = sdram_master_p3_ras_n;
assign ddrphy_dfi_p3_we_n = sdram_master_p3_we_n;
assign ddrphy_dfi_p3_cke = sdram_master_p3_cke;
assign ddrphy_dfi_p3_odt = sdram_master_p3_odt;
assign ddrphy_dfi_p3_reset_n = sdram_master_p3_reset_n;
assign ddrphy_dfi_p3_act_n = sdram_master_p3_act_n;
assign ddrphy_dfi_p3_wrdata = sdram_master_p3_wrdata;
assign ddrphy_dfi_p3_wrdata_en = sdram_master_p3_wrdata_en;
assign ddrphy_dfi_p3_wrdata_mask = sdram_master_p3_wrdata_mask;
assign ddrphy_dfi_p3_rddata_en = sdram_master_p3_rddata_en;
assign sdram_master_p3_rddata = ddrphy_dfi_p3_rddata;
assign sdram_master_p3_rddata_valid = ddrphy_dfi_p3_rddata_valid;
assign sdram_TMRslave_p0_address = sdram_TMRdfi_p0_address;
assign sdram_TMRslave_p0_bank = sdram_TMRdfi_p0_bank;
assign sdram_TMRslave_p0_cas_n = sdram_TMRdfi_p0_cas_n;
assign sdram_TMRslave_p0_cs_n = sdram_TMRdfi_p0_cs_n;
assign sdram_TMRslave_p0_ras_n = sdram_TMRdfi_p0_ras_n;
assign sdram_TMRslave_p0_we_n = sdram_TMRdfi_p0_we_n;
assign sdram_TMRslave_p0_cke = sdram_TMRdfi_p0_cke;
assign sdram_TMRslave_p0_odt = sdram_TMRdfi_p0_odt;
assign sdram_TMRslave_p0_reset_n = sdram_TMRdfi_p0_reset_n;
assign sdram_TMRslave_p0_act_n = sdram_TMRdfi_p0_act_n;
assign sdram_TMRslave_p0_wrdata = sdram_TMRdfi_p0_wrdata;
assign sdram_TMRslave_p0_wrdata_en = sdram_TMRdfi_p0_wrdata_en;
assign sdram_TMRslave_p0_wrdata_mask = sdram_TMRdfi_p0_wrdata_mask;
assign sdram_TMRslave_p0_rddata_en = sdram_TMRdfi_p0_rddata_en;
assign sdram_TMRdfi_p0_rddata = sdram_TMRslave_p0_rddata;
assign sdram_TMRdfi_p0_rddata_valid = sdram_TMRslave_p0_rddata_valid;
assign sdram_TMRslave_p1_address = sdram_TMRdfi_p1_address;
assign sdram_TMRslave_p1_bank = sdram_TMRdfi_p1_bank;
assign sdram_TMRslave_p1_cas_n = sdram_TMRdfi_p1_cas_n;
assign sdram_TMRslave_p1_cs_n = sdram_TMRdfi_p1_cs_n;
assign sdram_TMRslave_p1_ras_n = sdram_TMRdfi_p1_ras_n;
assign sdram_TMRslave_p1_we_n = sdram_TMRdfi_p1_we_n;
assign sdram_TMRslave_p1_cke = sdram_TMRdfi_p1_cke;
assign sdram_TMRslave_p1_odt = sdram_TMRdfi_p1_odt;
assign sdram_TMRslave_p1_reset_n = sdram_TMRdfi_p1_reset_n;
assign sdram_TMRslave_p1_act_n = sdram_TMRdfi_p1_act_n;
assign sdram_TMRslave_p1_wrdata = sdram_TMRdfi_p1_wrdata;
assign sdram_TMRslave_p1_wrdata_en = sdram_TMRdfi_p1_wrdata_en;
assign sdram_TMRslave_p1_wrdata_mask = sdram_TMRdfi_p1_wrdata_mask;
assign sdram_TMRslave_p1_rddata_en = sdram_TMRdfi_p1_rddata_en;
assign sdram_TMRdfi_p1_rddata = sdram_TMRslave_p1_rddata;
assign sdram_TMRdfi_p1_rddata_valid = sdram_TMRslave_p1_rddata_valid;
assign sdram_TMRslave_p2_address = sdram_TMRdfi_p2_address;
assign sdram_TMRslave_p2_bank = sdram_TMRdfi_p2_bank;
assign sdram_TMRslave_p2_cas_n = sdram_TMRdfi_p2_cas_n;
assign sdram_TMRslave_p2_cs_n = sdram_TMRdfi_p2_cs_n;
assign sdram_TMRslave_p2_ras_n = sdram_TMRdfi_p2_ras_n;
assign sdram_TMRslave_p2_we_n = sdram_TMRdfi_p2_we_n;
assign sdram_TMRslave_p2_cke = sdram_TMRdfi_p2_cke;
assign sdram_TMRslave_p2_odt = sdram_TMRdfi_p2_odt;
assign sdram_TMRslave_p2_reset_n = sdram_TMRdfi_p2_reset_n;
assign sdram_TMRslave_p2_act_n = sdram_TMRdfi_p2_act_n;
assign sdram_TMRslave_p2_wrdata = sdram_TMRdfi_p2_wrdata;
assign sdram_TMRslave_p2_wrdata_en = sdram_TMRdfi_p2_wrdata_en;
assign sdram_TMRslave_p2_wrdata_mask = sdram_TMRdfi_p2_wrdata_mask;
assign sdram_TMRslave_p2_rddata_en = sdram_TMRdfi_p2_rddata_en;
assign sdram_TMRdfi_p2_rddata = sdram_TMRslave_p2_rddata;
assign sdram_TMRdfi_p2_rddata_valid = sdram_TMRslave_p2_rddata_valid;
assign sdram_TMRslave_p3_address = sdram_TMRdfi_p3_address;
assign sdram_TMRslave_p3_bank = sdram_TMRdfi_p3_bank;
assign sdram_TMRslave_p3_cas_n = sdram_TMRdfi_p3_cas_n;
assign sdram_TMRslave_p3_cs_n = sdram_TMRdfi_p3_cs_n;
assign sdram_TMRslave_p3_ras_n = sdram_TMRdfi_p3_ras_n;
assign sdram_TMRslave_p3_we_n = sdram_TMRdfi_p3_we_n;
assign sdram_TMRslave_p3_cke = sdram_TMRdfi_p3_cke;
assign sdram_TMRslave_p3_odt = sdram_TMRdfi_p3_odt;
assign sdram_TMRslave_p3_reset_n = sdram_TMRdfi_p3_reset_n;
assign sdram_TMRslave_p3_act_n = sdram_TMRdfi_p3_act_n;
assign sdram_TMRslave_p3_wrdata = sdram_TMRdfi_p3_wrdata;
assign sdram_TMRslave_p3_wrdata_en = sdram_TMRdfi_p3_wrdata_en;
assign sdram_TMRslave_p3_wrdata_mask = sdram_TMRdfi_p3_wrdata_mask;
assign sdram_TMRslave_p3_rddata_en = sdram_TMRdfi_p3_rddata_en;
assign sdram_TMRdfi_p3_rddata = sdram_TMRslave_p3_rddata;
assign sdram_TMRdfi_p3_rddata_valid = sdram_TMRslave_p3_rddata_valid;

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p0_rddata <= 64'd0;
	sdram_pi_mod1_inti_p0_rddata <= sdram_inti_inti_p0_rddata;
	sdram_pi_mod1_inti_p0_rddata <= sdram_inti_inti_p0_rddata;
	sdram_pi_mod1_inti_p0_rddata <= sdram_inti_inti_p0_rddata;
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p0_rddata_valid <= 1'd0;
	sdram_pi_mod1_inti_p0_rddata_valid <= sdram_inti_inti_p0_rddata_valid;
	sdram_pi_mod1_inti_p0_rddata_valid <= sdram_inti_inti_p0_rddata_valid;
	sdram_pi_mod1_inti_p0_rddata_valid <= sdram_inti_inti_p0_rddata_valid;
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p1_rddata <= 64'd0;
	sdram_pi_mod1_inti_p1_rddata <= sdram_inti_inti_p1_rddata;
	sdram_pi_mod1_inti_p1_rddata <= sdram_inti_inti_p1_rddata;
	sdram_pi_mod1_inti_p1_rddata <= sdram_inti_inti_p1_rddata;
// synthesis translate_off
	dummy_d_2 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_3;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p1_rddata_valid <= 1'd0;
	sdram_pi_mod1_inti_p1_rddata_valid <= sdram_inti_inti_p1_rddata_valid;
	sdram_pi_mod1_inti_p1_rddata_valid <= sdram_inti_inti_p1_rddata_valid;
	sdram_pi_mod1_inti_p1_rddata_valid <= sdram_inti_inti_p1_rddata_valid;
// synthesis translate_off
	dummy_d_3 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_4;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p2_rddata <= 64'd0;
	sdram_pi_mod1_inti_p2_rddata <= sdram_inti_inti_p2_rddata;
	sdram_pi_mod1_inti_p2_rddata <= sdram_inti_inti_p2_rddata;
	sdram_pi_mod1_inti_p2_rddata <= sdram_inti_inti_p2_rddata;
// synthesis translate_off
	dummy_d_4 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_5;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p2_rddata_valid <= 1'd0;
	sdram_pi_mod1_inti_p2_rddata_valid <= sdram_inti_inti_p2_rddata_valid;
	sdram_pi_mod1_inti_p2_rddata_valid <= sdram_inti_inti_p2_rddata_valid;
	sdram_pi_mod1_inti_p2_rddata_valid <= sdram_inti_inti_p2_rddata_valid;
// synthesis translate_off
	dummy_d_5 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_6;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p3_rddata <= 64'd0;
	sdram_pi_mod1_inti_p3_rddata <= sdram_inti_inti_p3_rddata;
	sdram_pi_mod1_inti_p3_rddata <= sdram_inti_inti_p3_rddata;
	sdram_pi_mod1_inti_p3_rddata <= sdram_inti_inti_p3_rddata;
// synthesis translate_off
	dummy_d_6 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_7;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p3_rddata_valid <= 1'd0;
	sdram_pi_mod1_inti_p3_rddata_valid <= sdram_inti_inti_p3_rddata_valid;
	sdram_pi_mod1_inti_p3_rddata_valid <= sdram_inti_inti_p3_rddata_valid;
	sdram_pi_mod1_inti_p3_rddata_valid <= sdram_inti_inti_p3_rddata_valid;
// synthesis translate_off
	dummy_d_7 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_8;
// synthesis translate_on
always @(*) begin
	sdram_slave_p0_rddata <= 64'd0;
	sdram_slave_p0_rddata_valid <= 1'd0;
	sdram_slave_p1_rddata <= 64'd0;
	sdram_slave_p1_rddata_valid <= 1'd0;
	sdram_slave_p2_rddata <= 64'd0;
	sdram_slave_p2_rddata_valid <= 1'd0;
	sdram_slave_p3_rddata <= 64'd0;
	sdram_slave_p3_rddata_valid <= 1'd0;
	sdram_master_p0_address <= 14'd0;
	sdram_master_p0_bank <= 3'd0;
	sdram_master_p0_cas_n <= 1'd1;
	sdram_master_p0_cs_n <= 1'd1;
	sdram_master_p0_ras_n <= 1'd1;
	sdram_master_p0_we_n <= 1'd1;
	sdram_master_p0_cke <= 1'd0;
	sdram_master_p0_odt <= 1'd0;
	sdram_master_p0_reset_n <= 1'd0;
	sdram_master_p0_act_n <= 1'd1;
	sdram_master_p0_wrdata <= 64'd0;
	sdram_master_p0_wrdata_en <= 1'd0;
	sdram_master_p0_wrdata_mask <= 8'd0;
	sdram_master_p0_rddata_en <= 1'd0;
	sdram_master_p1_address <= 14'd0;
	sdram_master_p1_bank <= 3'd0;
	sdram_master_p1_cas_n <= 1'd1;
	sdram_master_p1_cs_n <= 1'd1;
	sdram_master_p1_ras_n <= 1'd1;
	sdram_master_p1_we_n <= 1'd1;
	sdram_master_p1_cke <= 1'd0;
	sdram_master_p1_odt <= 1'd0;
	sdram_master_p1_reset_n <= 1'd0;
	sdram_master_p1_act_n <= 1'd1;
	sdram_master_p1_wrdata <= 64'd0;
	sdram_master_p1_wrdata_en <= 1'd0;
	sdram_master_p1_wrdata_mask <= 8'd0;
	sdram_master_p1_rddata_en <= 1'd0;
	sdram_master_p2_address <= 14'd0;
	sdram_master_p2_bank <= 3'd0;
	sdram_master_p2_cas_n <= 1'd1;
	sdram_master_p2_cs_n <= 1'd1;
	sdram_master_p2_ras_n <= 1'd1;
	sdram_master_p2_we_n <= 1'd1;
	sdram_master_p2_cke <= 1'd0;
	sdram_master_p2_odt <= 1'd0;
	sdram_master_p2_reset_n <= 1'd0;
	sdram_master_p2_act_n <= 1'd1;
	sdram_master_p2_wrdata <= 64'd0;
	sdram_master_p2_wrdata_en <= 1'd0;
	sdram_master_p2_wrdata_mask <= 8'd0;
	sdram_master_p2_rddata_en <= 1'd0;
	sdram_master_p3_address <= 14'd0;
	sdram_master_p3_bank <= 3'd0;
	sdram_master_p3_cas_n <= 1'd1;
	sdram_master_p3_cs_n <= 1'd1;
	sdram_master_p3_ras_n <= 1'd1;
	sdram_master_p3_we_n <= 1'd1;
	sdram_master_p3_cke <= 1'd0;
	sdram_master_p3_odt <= 1'd0;
	sdram_master_p3_reset_n <= 1'd0;
	sdram_master_p3_act_n <= 1'd1;
	sdram_master_p3_wrdata <= 64'd0;
	sdram_master_p3_wrdata_en <= 1'd0;
	sdram_master_p3_wrdata_mask <= 8'd0;
	sdram_master_p3_rddata_en <= 1'd0;
	sdram_inti_inti_p0_rddata <= 64'd0;
	sdram_inti_inti_p0_rddata_valid <= 1'd0;
	sdram_inti_inti_p1_rddata <= 64'd0;
	sdram_inti_inti_p1_rddata_valid <= 1'd0;
	sdram_inti_inti_p2_rddata <= 64'd0;
	sdram_inti_inti_p2_rddata_valid <= 1'd0;
	sdram_inti_inti_p3_rddata <= 64'd0;
	sdram_inti_inti_p3_rddata_valid <= 1'd0;
	if (sdram_sel) begin
		sdram_master_p0_address <= sdram_slave_p0_address;
		sdram_master_p0_bank <= sdram_slave_p0_bank;
		sdram_master_p0_cas_n <= sdram_slave_p0_cas_n;
		sdram_master_p0_cs_n <= sdram_slave_p0_cs_n;
		sdram_master_p0_ras_n <= sdram_slave_p0_ras_n;
		sdram_master_p0_we_n <= sdram_slave_p0_we_n;
		sdram_master_p0_cke <= sdram_slave_p0_cke;
		sdram_master_p0_odt <= sdram_slave_p0_odt;
		sdram_master_p0_reset_n <= sdram_slave_p0_reset_n;
		sdram_master_p0_act_n <= sdram_slave_p0_act_n;
		sdram_master_p0_wrdata <= sdram_slave_p0_wrdata;
		sdram_master_p0_wrdata_en <= sdram_slave_p0_wrdata_en;
		sdram_master_p0_wrdata_mask <= sdram_slave_p0_wrdata_mask;
		sdram_master_p0_rddata_en <= sdram_slave_p0_rddata_en;
		sdram_slave_p0_rddata <= sdram_master_p0_rddata;
		sdram_slave_p0_rddata_valid <= sdram_master_p0_rddata_valid;
		sdram_master_p1_address <= sdram_slave_p1_address;
		sdram_master_p1_bank <= sdram_slave_p1_bank;
		sdram_master_p1_cas_n <= sdram_slave_p1_cas_n;
		sdram_master_p1_cs_n <= sdram_slave_p1_cs_n;
		sdram_master_p1_ras_n <= sdram_slave_p1_ras_n;
		sdram_master_p1_we_n <= sdram_slave_p1_we_n;
		sdram_master_p1_cke <= sdram_slave_p1_cke;
		sdram_master_p1_odt <= sdram_slave_p1_odt;
		sdram_master_p1_reset_n <= sdram_slave_p1_reset_n;
		sdram_master_p1_act_n <= sdram_slave_p1_act_n;
		sdram_master_p1_wrdata <= sdram_slave_p1_wrdata;
		sdram_master_p1_wrdata_en <= sdram_slave_p1_wrdata_en;
		sdram_master_p1_wrdata_mask <= sdram_slave_p1_wrdata_mask;
		sdram_master_p1_rddata_en <= sdram_slave_p1_rddata_en;
		sdram_slave_p1_rddata <= sdram_master_p1_rddata;
		sdram_slave_p1_rddata_valid <= sdram_master_p1_rddata_valid;
		sdram_master_p2_address <= sdram_slave_p2_address;
		sdram_master_p2_bank <= sdram_slave_p2_bank;
		sdram_master_p2_cas_n <= sdram_slave_p2_cas_n;
		sdram_master_p2_cs_n <= sdram_slave_p2_cs_n;
		sdram_master_p2_ras_n <= sdram_slave_p2_ras_n;
		sdram_master_p2_we_n <= sdram_slave_p2_we_n;
		sdram_master_p2_cke <= sdram_slave_p2_cke;
		sdram_master_p2_odt <= sdram_slave_p2_odt;
		sdram_master_p2_reset_n <= sdram_slave_p2_reset_n;
		sdram_master_p2_act_n <= sdram_slave_p2_act_n;
		sdram_master_p2_wrdata <= sdram_slave_p2_wrdata;
		sdram_master_p2_wrdata_en <= sdram_slave_p2_wrdata_en;
		sdram_master_p2_wrdata_mask <= sdram_slave_p2_wrdata_mask;
		sdram_master_p2_rddata_en <= sdram_slave_p2_rddata_en;
		sdram_slave_p2_rddata <= sdram_master_p2_rddata;
		sdram_slave_p2_rddata_valid <= sdram_master_p2_rddata_valid;
		sdram_master_p3_address <= sdram_slave_p3_address;
		sdram_master_p3_bank <= sdram_slave_p3_bank;
		sdram_master_p3_cas_n <= sdram_slave_p3_cas_n;
		sdram_master_p3_cs_n <= sdram_slave_p3_cs_n;
		sdram_master_p3_ras_n <= sdram_slave_p3_ras_n;
		sdram_master_p3_we_n <= sdram_slave_p3_we_n;
		sdram_master_p3_cke <= sdram_slave_p3_cke;
		sdram_master_p3_odt <= sdram_slave_p3_odt;
		sdram_master_p3_reset_n <= sdram_slave_p3_reset_n;
		sdram_master_p3_act_n <= sdram_slave_p3_act_n;
		sdram_master_p3_wrdata <= sdram_slave_p3_wrdata;
		sdram_master_p3_wrdata_en <= sdram_slave_p3_wrdata_en;
		sdram_master_p3_wrdata_mask <= sdram_slave_p3_wrdata_mask;
		sdram_master_p3_rddata_en <= sdram_slave_p3_rddata_en;
		sdram_slave_p3_rddata <= sdram_master_p3_rddata;
		sdram_slave_p3_rddata_valid <= sdram_master_p3_rddata_valid;
	end else begin
		sdram_master_p0_address <= sdram_inti_inti_p0_address;
		sdram_master_p0_bank <= sdram_inti_inti_p0_bank;
		sdram_master_p0_cas_n <= sdram_inti_inti_p0_cas_n;
		sdram_master_p0_cs_n <= sdram_inti_inti_p0_cs_n;
		sdram_master_p0_ras_n <= sdram_inti_inti_p0_ras_n;
		sdram_master_p0_we_n <= sdram_inti_inti_p0_we_n;
		sdram_master_p0_cke <= sdram_inti_inti_p0_cke;
		sdram_master_p0_odt <= sdram_inti_inti_p0_odt;
		sdram_master_p0_reset_n <= sdram_inti_inti_p0_reset_n;
		sdram_master_p0_act_n <= sdram_inti_inti_p0_act_n;
		sdram_master_p0_wrdata <= sdram_inti_inti_p0_wrdata;
		sdram_master_p0_wrdata_en <= sdram_inti_inti_p0_wrdata_en;
		sdram_master_p0_wrdata_mask <= sdram_inti_inti_p0_wrdata_mask;
		sdram_master_p0_rddata_en <= sdram_inti_inti_p0_rddata_en;
		sdram_inti_inti_p0_rddata <= sdram_master_p0_rddata;
		sdram_inti_inti_p0_rddata_valid <= sdram_master_p0_rddata_valid;
		sdram_master_p1_address <= sdram_inti_inti_p1_address;
		sdram_master_p1_bank <= sdram_inti_inti_p1_bank;
		sdram_master_p1_cas_n <= sdram_inti_inti_p1_cas_n;
		sdram_master_p1_cs_n <= sdram_inti_inti_p1_cs_n;
		sdram_master_p1_ras_n <= sdram_inti_inti_p1_ras_n;
		sdram_master_p1_we_n <= sdram_inti_inti_p1_we_n;
		sdram_master_p1_cke <= sdram_inti_inti_p1_cke;
		sdram_master_p1_odt <= sdram_inti_inti_p1_odt;
		sdram_master_p1_reset_n <= sdram_inti_inti_p1_reset_n;
		sdram_master_p1_act_n <= sdram_inti_inti_p1_act_n;
		sdram_master_p1_wrdata <= sdram_inti_inti_p1_wrdata;
		sdram_master_p1_wrdata_en <= sdram_inti_inti_p1_wrdata_en;
		sdram_master_p1_wrdata_mask <= sdram_inti_inti_p1_wrdata_mask;
		sdram_master_p1_rddata_en <= sdram_inti_inti_p1_rddata_en;
		sdram_inti_inti_p1_rddata <= sdram_master_p1_rddata;
		sdram_inti_inti_p1_rddata_valid <= sdram_master_p1_rddata_valid;
		sdram_master_p2_address <= sdram_inti_inti_p2_address;
		sdram_master_p2_bank <= sdram_inti_inti_p2_bank;
		sdram_master_p2_cas_n <= sdram_inti_inti_p2_cas_n;
		sdram_master_p2_cs_n <= sdram_inti_inti_p2_cs_n;
		sdram_master_p2_ras_n <= sdram_inti_inti_p2_ras_n;
		sdram_master_p2_we_n <= sdram_inti_inti_p2_we_n;
		sdram_master_p2_cke <= sdram_inti_inti_p2_cke;
		sdram_master_p2_odt <= sdram_inti_inti_p2_odt;
		sdram_master_p2_reset_n <= sdram_inti_inti_p2_reset_n;
		sdram_master_p2_act_n <= sdram_inti_inti_p2_act_n;
		sdram_master_p2_wrdata <= sdram_inti_inti_p2_wrdata;
		sdram_master_p2_wrdata_en <= sdram_inti_inti_p2_wrdata_en;
		sdram_master_p2_wrdata_mask <= sdram_inti_inti_p2_wrdata_mask;
		sdram_master_p2_rddata_en <= sdram_inti_inti_p2_rddata_en;
		sdram_inti_inti_p2_rddata <= sdram_master_p2_rddata;
		sdram_inti_inti_p2_rddata_valid <= sdram_master_p2_rddata_valid;
		sdram_master_p3_address <= sdram_inti_inti_p3_address;
		sdram_master_p3_bank <= sdram_inti_inti_p3_bank;
		sdram_master_p3_cas_n <= sdram_inti_inti_p3_cas_n;
		sdram_master_p3_cs_n <= sdram_inti_inti_p3_cs_n;
		sdram_master_p3_ras_n <= sdram_inti_inti_p3_ras_n;
		sdram_master_p3_we_n <= sdram_inti_inti_p3_we_n;
		sdram_master_p3_cke <= sdram_inti_inti_p3_cke;
		sdram_master_p3_odt <= sdram_inti_inti_p3_odt;
		sdram_master_p3_reset_n <= sdram_inti_inti_p3_reset_n;
		sdram_master_p3_act_n <= sdram_inti_inti_p3_act_n;
		sdram_master_p3_wrdata <= sdram_inti_inti_p3_wrdata;
		sdram_master_p3_wrdata_en <= sdram_inti_inti_p3_wrdata_en;
		sdram_master_p3_wrdata_mask <= sdram_inti_inti_p3_wrdata_mask;
		sdram_master_p3_rddata_en <= sdram_inti_inti_p3_rddata_en;
		sdram_inti_inti_p3_rddata <= sdram_master_p3_rddata;
		sdram_inti_inti_p3_rddata_valid <= sdram_master_p3_rddata_valid;
	end
// synthesis translate_off
	dummy_d_8 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod1_inti_p0_cke = sdram_cke;
assign sdram_pi_mod1_inti_p1_cke = sdram_cke;
assign sdram_pi_mod1_inti_p2_cke = sdram_cke;
assign sdram_pi_mod1_inti_p3_cke = sdram_cke;
assign sdram_pi_mod1_inti_p0_odt = sdram_odt;
assign sdram_pi_mod1_inti_p1_odt = sdram_odt;
assign sdram_pi_mod1_inti_p2_odt = sdram_odt;
assign sdram_pi_mod1_inti_p3_odt = sdram_odt;
assign sdram_pi_mod1_inti_p0_reset_n = sdram_reset_n;
assign sdram_pi_mod1_inti_p1_reset_n = sdram_reset_n;
assign sdram_pi_mod1_inti_p2_reset_n = sdram_reset_n;
assign sdram_pi_mod1_inti_p3_reset_n = sdram_reset_n;
assign sdram_pi_mod2_phaseinjector0_command_we = 1'd1;
assign sdram_pi_mod2_phaseinjector0_command_dat_w = sdram_pi_mod1_phaseinjector0_command_storage;
assign sdram_pi_mod2_phaseinjector0_command_storage = sdram_pi_mod1_phaseinjector0_command_storage;
assign sdram_pi_mod2_phaseinjector0_command_issue_w = sdram_pi_mod1_phaseinjector0_command_issue_w;
assign sdram_pi_mod2_phaseinjector0_command_issue_we = sdram_pi_mod1_phaseinjector0_command_issue_we;
assign sdram_pi_mod2_phaseinjector0_command_issue_re = sdram_pi_mod1_phaseinjector0_command_issue_re;
assign sdram_pi_mod2_phaseinjector0_address_we = 1'd1;
assign sdram_pi_mod2_phaseinjector0_address_dat_w = sdram_pi_mod1_phaseinjector0_address_storage;
assign sdram_pi_mod2_phaseinjector0_address_storage = sdram_pi_mod1_phaseinjector0_address_storage;
assign sdram_pi_mod2_phaseinjector0_baddress_we = 1'd1;
assign sdram_pi_mod2_phaseinjector0_baddress_dat_w = sdram_pi_mod1_phaseinjector0_baddress_storage;
assign sdram_pi_mod2_phaseinjector0_baddress_storage = sdram_pi_mod1_phaseinjector0_baddress_storage;
assign sdram_pi_mod2_phaseinjector0_wrdata_we = 1'd1;
assign sdram_pi_mod2_phaseinjector0_wrdata_dat_w = sdram_pi_mod1_phaseinjector0_wrdata_storage;
assign sdram_pi_mod2_phaseinjector0_wrdata_storage = sdram_pi_mod1_phaseinjector0_wrdata_storage;
assign sdram_pi_mod2_phaseinjector1_command_we = 1'd1;
assign sdram_pi_mod2_phaseinjector1_command_dat_w = sdram_pi_mod1_phaseinjector1_command_storage;
assign sdram_pi_mod2_phaseinjector1_command_storage = sdram_pi_mod1_phaseinjector1_command_storage;
assign sdram_pi_mod2_phaseinjector1_command_issue_w = sdram_pi_mod1_phaseinjector1_command_issue_w;
assign sdram_pi_mod2_phaseinjector1_command_issue_we = sdram_pi_mod1_phaseinjector1_command_issue_we;
assign sdram_pi_mod2_phaseinjector1_command_issue_re = sdram_pi_mod1_phaseinjector1_command_issue_re;
assign sdram_pi_mod2_phaseinjector1_address_we = 1'd1;
assign sdram_pi_mod2_phaseinjector1_address_dat_w = sdram_pi_mod1_phaseinjector1_address_storage;
assign sdram_pi_mod2_phaseinjector1_address_storage = sdram_pi_mod1_phaseinjector1_address_storage;
assign sdram_pi_mod2_phaseinjector1_baddress_we = 1'd1;
assign sdram_pi_mod2_phaseinjector1_baddress_dat_w = sdram_pi_mod1_phaseinjector1_baddress_storage;
assign sdram_pi_mod2_phaseinjector1_baddress_storage = sdram_pi_mod1_phaseinjector1_baddress_storage;
assign sdram_pi_mod2_phaseinjector1_wrdata_we = 1'd1;
assign sdram_pi_mod2_phaseinjector1_wrdata_dat_w = sdram_pi_mod1_phaseinjector1_wrdata_storage;
assign sdram_pi_mod2_phaseinjector1_wrdata_storage = sdram_pi_mod1_phaseinjector1_wrdata_storage;
assign sdram_pi_mod2_phaseinjector2_command_we = 1'd1;
assign sdram_pi_mod2_phaseinjector2_command_dat_w = sdram_pi_mod1_phaseinjector2_command_storage;
assign sdram_pi_mod2_phaseinjector2_command_storage = sdram_pi_mod1_phaseinjector2_command_storage;
assign sdram_pi_mod2_phaseinjector2_command_issue_w = sdram_pi_mod1_phaseinjector2_command_issue_w;
assign sdram_pi_mod2_phaseinjector2_command_issue_we = sdram_pi_mod1_phaseinjector2_command_issue_we;
assign sdram_pi_mod2_phaseinjector2_command_issue_re = sdram_pi_mod1_phaseinjector2_command_issue_re;
assign sdram_pi_mod2_phaseinjector2_address_we = 1'd1;
assign sdram_pi_mod2_phaseinjector2_address_dat_w = sdram_pi_mod1_phaseinjector2_address_storage;
assign sdram_pi_mod2_phaseinjector2_address_storage = sdram_pi_mod1_phaseinjector2_address_storage;
assign sdram_pi_mod2_phaseinjector2_baddress_we = 1'd1;
assign sdram_pi_mod2_phaseinjector2_baddress_dat_w = sdram_pi_mod1_phaseinjector2_baddress_storage;
assign sdram_pi_mod2_phaseinjector2_baddress_storage = sdram_pi_mod1_phaseinjector2_baddress_storage;
assign sdram_pi_mod2_phaseinjector2_wrdata_we = 1'd1;
assign sdram_pi_mod2_phaseinjector2_wrdata_dat_w = sdram_pi_mod1_phaseinjector2_wrdata_storage;
assign sdram_pi_mod2_phaseinjector2_wrdata_storage = sdram_pi_mod1_phaseinjector2_wrdata_storage;
assign sdram_pi_mod2_phaseinjector3_command_we = 1'd1;
assign sdram_pi_mod2_phaseinjector3_command_dat_w = sdram_pi_mod1_phaseinjector3_command_storage;
assign sdram_pi_mod2_phaseinjector3_command_storage = sdram_pi_mod1_phaseinjector3_command_storage;
assign sdram_pi_mod2_phaseinjector3_command_issue_w = sdram_pi_mod1_phaseinjector3_command_issue_w;
assign sdram_pi_mod2_phaseinjector3_command_issue_we = sdram_pi_mod1_phaseinjector3_command_issue_we;
assign sdram_pi_mod2_phaseinjector3_command_issue_re = sdram_pi_mod1_phaseinjector3_command_issue_re;
assign sdram_pi_mod2_phaseinjector3_address_we = 1'd1;
assign sdram_pi_mod2_phaseinjector3_address_dat_w = sdram_pi_mod1_phaseinjector3_address_storage;
assign sdram_pi_mod2_phaseinjector3_address_storage = sdram_pi_mod1_phaseinjector3_address_storage;
assign sdram_pi_mod2_phaseinjector3_baddress_we = 1'd1;
assign sdram_pi_mod2_phaseinjector3_baddress_dat_w = sdram_pi_mod1_phaseinjector3_baddress_storage;
assign sdram_pi_mod2_phaseinjector3_baddress_storage = sdram_pi_mod1_phaseinjector3_baddress_storage;
assign sdram_pi_mod2_phaseinjector3_wrdata_we = 1'd1;
assign sdram_pi_mod2_phaseinjector3_wrdata_dat_w = sdram_pi_mod1_phaseinjector3_wrdata_storage;
assign sdram_pi_mod2_phaseinjector3_wrdata_storage = sdram_pi_mod1_phaseinjector3_wrdata_storage;
assign sdram_pi_mod3_phaseinjector0_command_we = 1'd1;
assign sdram_pi_mod3_phaseinjector0_command_dat_w = sdram_pi_mod1_phaseinjector0_command_storage;

// synthesis translate_off
reg dummy_d_9;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector0_command_we <= 1'd0;
	sdram_pi_mod1_phaseinjector0_command_we <= 1'd0;
	sdram_pi_mod1_phaseinjector0_command_we <= 1'd0;
// synthesis translate_off
	dummy_d_9 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector0_command_storage = sdram_pi_mod1_phaseinjector0_command_storage;
assign sdram_pi_mod3_phaseinjector0_command_issue_w = sdram_pi_mod1_phaseinjector0_command_issue_w;
assign sdram_pi_mod3_phaseinjector0_command_issue_we = sdram_pi_mod1_phaseinjector0_command_issue_we;
assign sdram_pi_mod3_phaseinjector0_command_issue_re = sdram_pi_mod1_phaseinjector0_command_issue_re;
assign sdram_pi_mod3_phaseinjector0_address_we = 1'd1;
assign sdram_pi_mod3_phaseinjector0_address_dat_w = sdram_pi_mod1_phaseinjector0_address_storage;

// synthesis translate_off
reg dummy_d_10;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector0_address_we <= 1'd0;
	sdram_pi_mod1_phaseinjector0_address_we <= 1'd0;
	sdram_pi_mod1_phaseinjector0_address_we <= 1'd0;
// synthesis translate_off
	dummy_d_10 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector0_address_storage = sdram_pi_mod1_phaseinjector0_address_storage;
assign sdram_pi_mod3_phaseinjector0_baddress_we = 1'd1;
assign sdram_pi_mod3_phaseinjector0_baddress_dat_w = sdram_pi_mod1_phaseinjector0_baddress_storage;

// synthesis translate_off
reg dummy_d_11;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector0_baddress_we <= 1'd0;
	sdram_pi_mod1_phaseinjector0_baddress_we <= 1'd0;
	sdram_pi_mod1_phaseinjector0_baddress_we <= 1'd0;
// synthesis translate_off
	dummy_d_11 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector0_baddress_storage = sdram_pi_mod1_phaseinjector0_baddress_storage;
assign sdram_pi_mod3_phaseinjector0_wrdata_we = 1'd1;
assign sdram_pi_mod3_phaseinjector0_wrdata_dat_w = sdram_pi_mod1_phaseinjector0_wrdata_storage;

// synthesis translate_off
reg dummy_d_12;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector0_wrdata_we <= 1'd0;
	sdram_pi_mod1_phaseinjector0_wrdata_we <= 1'd0;
	sdram_pi_mod1_phaseinjector0_wrdata_we <= 1'd0;
// synthesis translate_off
	dummy_d_12 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector0_wrdata_storage = sdram_pi_mod1_phaseinjector0_wrdata_storage;
assign sdram_pi_mod3_phaseinjector1_command_we = 1'd1;
assign sdram_pi_mod3_phaseinjector1_command_dat_w = sdram_pi_mod1_phaseinjector1_command_storage;

// synthesis translate_off
reg dummy_d_13;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector1_command_we <= 1'd0;
	sdram_pi_mod1_phaseinjector1_command_we <= 1'd0;
	sdram_pi_mod1_phaseinjector1_command_we <= 1'd0;
// synthesis translate_off
	dummy_d_13 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector1_command_storage = sdram_pi_mod1_phaseinjector1_command_storage;
assign sdram_pi_mod3_phaseinjector1_command_issue_w = sdram_pi_mod1_phaseinjector1_command_issue_w;
assign sdram_pi_mod3_phaseinjector1_command_issue_we = sdram_pi_mod1_phaseinjector1_command_issue_we;
assign sdram_pi_mod3_phaseinjector1_command_issue_re = sdram_pi_mod1_phaseinjector1_command_issue_re;
assign sdram_pi_mod3_phaseinjector1_address_we = 1'd1;
assign sdram_pi_mod3_phaseinjector1_address_dat_w = sdram_pi_mod1_phaseinjector1_address_storage;

// synthesis translate_off
reg dummy_d_14;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector1_address_we <= 1'd0;
	sdram_pi_mod1_phaseinjector1_address_we <= 1'd0;
	sdram_pi_mod1_phaseinjector1_address_we <= 1'd0;
// synthesis translate_off
	dummy_d_14 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector1_address_storage = sdram_pi_mod1_phaseinjector1_address_storage;
assign sdram_pi_mod3_phaseinjector1_baddress_we = 1'd1;
assign sdram_pi_mod3_phaseinjector1_baddress_dat_w = sdram_pi_mod1_phaseinjector1_baddress_storage;

// synthesis translate_off
reg dummy_d_15;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector1_baddress_we <= 1'd0;
	sdram_pi_mod1_phaseinjector1_baddress_we <= 1'd0;
	sdram_pi_mod1_phaseinjector1_baddress_we <= 1'd0;
// synthesis translate_off
	dummy_d_15 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector1_baddress_storage = sdram_pi_mod1_phaseinjector1_baddress_storage;
assign sdram_pi_mod3_phaseinjector1_wrdata_we = 1'd1;
assign sdram_pi_mod3_phaseinjector1_wrdata_dat_w = sdram_pi_mod1_phaseinjector1_wrdata_storage;

// synthesis translate_off
reg dummy_d_16;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector1_wrdata_we <= 1'd0;
	sdram_pi_mod1_phaseinjector1_wrdata_we <= 1'd0;
	sdram_pi_mod1_phaseinjector1_wrdata_we <= 1'd0;
// synthesis translate_off
	dummy_d_16 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector1_wrdata_storage = sdram_pi_mod1_phaseinjector1_wrdata_storage;
assign sdram_pi_mod3_phaseinjector2_command_we = 1'd1;
assign sdram_pi_mod3_phaseinjector2_command_dat_w = sdram_pi_mod1_phaseinjector2_command_storage;

// synthesis translate_off
reg dummy_d_17;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector2_command_we <= 1'd0;
	sdram_pi_mod1_phaseinjector2_command_we <= 1'd0;
	sdram_pi_mod1_phaseinjector2_command_we <= 1'd0;
// synthesis translate_off
	dummy_d_17 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector2_command_storage = sdram_pi_mod1_phaseinjector2_command_storage;
assign sdram_pi_mod3_phaseinjector2_command_issue_w = sdram_pi_mod1_phaseinjector2_command_issue_w;
assign sdram_pi_mod3_phaseinjector2_command_issue_we = sdram_pi_mod1_phaseinjector2_command_issue_we;
assign sdram_pi_mod3_phaseinjector2_command_issue_re = sdram_pi_mod1_phaseinjector2_command_issue_re;
assign sdram_pi_mod3_phaseinjector2_address_we = 1'd1;
assign sdram_pi_mod3_phaseinjector2_address_dat_w = sdram_pi_mod1_phaseinjector2_address_storage;

// synthesis translate_off
reg dummy_d_18;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector2_address_we <= 1'd0;
	sdram_pi_mod1_phaseinjector2_address_we <= 1'd0;
	sdram_pi_mod1_phaseinjector2_address_we <= 1'd0;
// synthesis translate_off
	dummy_d_18 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector2_address_storage = sdram_pi_mod1_phaseinjector2_address_storage;
assign sdram_pi_mod3_phaseinjector2_baddress_we = 1'd1;
assign sdram_pi_mod3_phaseinjector2_baddress_dat_w = sdram_pi_mod1_phaseinjector2_baddress_storage;

// synthesis translate_off
reg dummy_d_19;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector2_baddress_we <= 1'd0;
	sdram_pi_mod1_phaseinjector2_baddress_we <= 1'd0;
	sdram_pi_mod1_phaseinjector2_baddress_we <= 1'd0;
// synthesis translate_off
	dummy_d_19 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector2_baddress_storage = sdram_pi_mod1_phaseinjector2_baddress_storage;
assign sdram_pi_mod3_phaseinjector2_wrdata_we = 1'd1;
assign sdram_pi_mod3_phaseinjector2_wrdata_dat_w = sdram_pi_mod1_phaseinjector2_wrdata_storage;

// synthesis translate_off
reg dummy_d_20;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector2_wrdata_we <= 1'd0;
	sdram_pi_mod1_phaseinjector2_wrdata_we <= 1'd0;
	sdram_pi_mod1_phaseinjector2_wrdata_we <= 1'd0;
// synthesis translate_off
	dummy_d_20 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector2_wrdata_storage = sdram_pi_mod1_phaseinjector2_wrdata_storage;
assign sdram_pi_mod3_phaseinjector3_command_we = 1'd1;
assign sdram_pi_mod3_phaseinjector3_command_dat_w = sdram_pi_mod1_phaseinjector3_command_storage;

// synthesis translate_off
reg dummy_d_21;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector3_command_we <= 1'd0;
	sdram_pi_mod1_phaseinjector3_command_we <= 1'd0;
	sdram_pi_mod1_phaseinjector3_command_we <= 1'd0;
// synthesis translate_off
	dummy_d_21 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector3_command_storage = sdram_pi_mod1_phaseinjector3_command_storage;
assign sdram_pi_mod3_phaseinjector3_command_issue_w = sdram_pi_mod1_phaseinjector3_command_issue_w;
assign sdram_pi_mod3_phaseinjector3_command_issue_we = sdram_pi_mod1_phaseinjector3_command_issue_we;
assign sdram_pi_mod3_phaseinjector3_command_issue_re = sdram_pi_mod1_phaseinjector3_command_issue_re;
assign sdram_pi_mod3_phaseinjector3_address_we = 1'd1;
assign sdram_pi_mod3_phaseinjector3_address_dat_w = sdram_pi_mod1_phaseinjector3_address_storage;

// synthesis translate_off
reg dummy_d_22;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector3_address_we <= 1'd0;
	sdram_pi_mod1_phaseinjector3_address_we <= 1'd0;
	sdram_pi_mod1_phaseinjector3_address_we <= 1'd0;
// synthesis translate_off
	dummy_d_22 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector3_address_storage = sdram_pi_mod1_phaseinjector3_address_storage;
assign sdram_pi_mod3_phaseinjector3_baddress_we = 1'd1;
assign sdram_pi_mod3_phaseinjector3_baddress_dat_w = sdram_pi_mod1_phaseinjector3_baddress_storage;

// synthesis translate_off
reg dummy_d_23;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector3_baddress_we <= 1'd0;
	sdram_pi_mod1_phaseinjector3_baddress_we <= 1'd0;
	sdram_pi_mod1_phaseinjector3_baddress_we <= 1'd0;
// synthesis translate_off
	dummy_d_23 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector3_baddress_storage = sdram_pi_mod1_phaseinjector3_baddress_storage;
assign sdram_pi_mod3_phaseinjector3_wrdata_we = 1'd1;
assign sdram_pi_mod3_phaseinjector3_wrdata_dat_w = sdram_pi_mod1_phaseinjector3_wrdata_storage;

// synthesis translate_off
reg dummy_d_24;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_phaseinjector3_wrdata_we <= 1'd0;
	sdram_pi_mod1_phaseinjector3_wrdata_we <= 1'd0;
	sdram_pi_mod1_phaseinjector3_wrdata_we <= 1'd0;
// synthesis translate_off
	dummy_d_24 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_phaseinjector3_wrdata_storage = sdram_pi_mod1_phaseinjector3_wrdata_storage;

// synthesis translate_off
reg dummy_d_25;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p0_cas_n <= 1'd1;
	sdram_pi_mod1_inti_p0_cs_n <= 1'd1;
	sdram_pi_mod1_inti_p0_ras_n <= 1'd1;
	sdram_pi_mod1_inti_p0_we_n <= 1'd1;
	if (sdram_pi_mod1_phaseinjector0_command_issue_re) begin
		sdram_pi_mod1_inti_p0_cs_n <= {1{(~sdram_pi_mod1_phaseinjector0_command_storage[0])}};
		sdram_pi_mod1_inti_p0_we_n <= (~sdram_pi_mod1_phaseinjector0_command_storage[1]);
		sdram_pi_mod1_inti_p0_cas_n <= (~sdram_pi_mod1_phaseinjector0_command_storage[2]);
		sdram_pi_mod1_inti_p0_ras_n <= (~sdram_pi_mod1_phaseinjector0_command_storage[3]);
	end else begin
		sdram_pi_mod1_inti_p0_cs_n <= {1{1'd1}};
		sdram_pi_mod1_inti_p0_we_n <= 1'd1;
		sdram_pi_mod1_inti_p0_cas_n <= 1'd1;
		sdram_pi_mod1_inti_p0_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_25 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod1_inti_p0_address = sdram_pi_mod1_phaseinjector0_address_storage;
assign sdram_pi_mod1_inti_p0_bank = sdram_pi_mod1_phaseinjector0_baddress_storage;
assign sdram_pi_mod1_inti_p0_wrdata_en = (sdram_pi_mod1_phaseinjector0_command_issue_re & sdram_pi_mod1_phaseinjector0_command_storage[4]);
assign sdram_pi_mod1_inti_p0_rddata_en = (sdram_pi_mod1_phaseinjector0_command_issue_re & sdram_pi_mod1_phaseinjector0_command_storage[5]);
assign sdram_pi_mod1_inti_p0_wrdata = sdram_pi_mod1_phaseinjector0_wrdata_storage;
assign sdram_pi_mod1_inti_p0_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_26;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p1_cas_n <= 1'd1;
	sdram_pi_mod1_inti_p1_cs_n <= 1'd1;
	sdram_pi_mod1_inti_p1_ras_n <= 1'd1;
	sdram_pi_mod1_inti_p1_we_n <= 1'd1;
	if (sdram_pi_mod1_phaseinjector1_command_issue_re) begin
		sdram_pi_mod1_inti_p1_cs_n <= {1{(~sdram_pi_mod1_phaseinjector1_command_storage[0])}};
		sdram_pi_mod1_inti_p1_we_n <= (~sdram_pi_mod1_phaseinjector1_command_storage[1]);
		sdram_pi_mod1_inti_p1_cas_n <= (~sdram_pi_mod1_phaseinjector1_command_storage[2]);
		sdram_pi_mod1_inti_p1_ras_n <= (~sdram_pi_mod1_phaseinjector1_command_storage[3]);
	end else begin
		sdram_pi_mod1_inti_p1_cs_n <= {1{1'd1}};
		sdram_pi_mod1_inti_p1_we_n <= 1'd1;
		sdram_pi_mod1_inti_p1_cas_n <= 1'd1;
		sdram_pi_mod1_inti_p1_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_26 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod1_inti_p1_address = sdram_pi_mod1_phaseinjector1_address_storage;
assign sdram_pi_mod1_inti_p1_bank = sdram_pi_mod1_phaseinjector1_baddress_storage;
assign sdram_pi_mod1_inti_p1_wrdata_en = (sdram_pi_mod1_phaseinjector1_command_issue_re & sdram_pi_mod1_phaseinjector1_command_storage[4]);
assign sdram_pi_mod1_inti_p1_rddata_en = (sdram_pi_mod1_phaseinjector1_command_issue_re & sdram_pi_mod1_phaseinjector1_command_storage[5]);
assign sdram_pi_mod1_inti_p1_wrdata = sdram_pi_mod1_phaseinjector1_wrdata_storage;
assign sdram_pi_mod1_inti_p1_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_27;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p2_cas_n <= 1'd1;
	sdram_pi_mod1_inti_p2_cs_n <= 1'd1;
	sdram_pi_mod1_inti_p2_ras_n <= 1'd1;
	sdram_pi_mod1_inti_p2_we_n <= 1'd1;
	if (sdram_pi_mod1_phaseinjector2_command_issue_re) begin
		sdram_pi_mod1_inti_p2_cs_n <= {1{(~sdram_pi_mod1_phaseinjector2_command_storage[0])}};
		sdram_pi_mod1_inti_p2_we_n <= (~sdram_pi_mod1_phaseinjector2_command_storage[1]);
		sdram_pi_mod1_inti_p2_cas_n <= (~sdram_pi_mod1_phaseinjector2_command_storage[2]);
		sdram_pi_mod1_inti_p2_ras_n <= (~sdram_pi_mod1_phaseinjector2_command_storage[3]);
	end else begin
		sdram_pi_mod1_inti_p2_cs_n <= {1{1'd1}};
		sdram_pi_mod1_inti_p2_we_n <= 1'd1;
		sdram_pi_mod1_inti_p2_cas_n <= 1'd1;
		sdram_pi_mod1_inti_p2_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_27 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod1_inti_p2_address = sdram_pi_mod1_phaseinjector2_address_storage;
assign sdram_pi_mod1_inti_p2_bank = sdram_pi_mod1_phaseinjector2_baddress_storage;
assign sdram_pi_mod1_inti_p2_wrdata_en = (sdram_pi_mod1_phaseinjector2_command_issue_re & sdram_pi_mod1_phaseinjector2_command_storage[4]);
assign sdram_pi_mod1_inti_p2_rddata_en = (sdram_pi_mod1_phaseinjector2_command_issue_re & sdram_pi_mod1_phaseinjector2_command_storage[5]);
assign sdram_pi_mod1_inti_p2_wrdata = sdram_pi_mod1_phaseinjector2_wrdata_storage;
assign sdram_pi_mod1_inti_p2_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_28;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod1_inti_p3_cas_n <= 1'd1;
	sdram_pi_mod1_inti_p3_cs_n <= 1'd1;
	sdram_pi_mod1_inti_p3_ras_n <= 1'd1;
	sdram_pi_mod1_inti_p3_we_n <= 1'd1;
	if (sdram_pi_mod1_phaseinjector3_command_issue_re) begin
		sdram_pi_mod1_inti_p3_cs_n <= {1{(~sdram_pi_mod1_phaseinjector3_command_storage[0])}};
		sdram_pi_mod1_inti_p3_we_n <= (~sdram_pi_mod1_phaseinjector3_command_storage[1]);
		sdram_pi_mod1_inti_p3_cas_n <= (~sdram_pi_mod1_phaseinjector3_command_storage[2]);
		sdram_pi_mod1_inti_p3_ras_n <= (~sdram_pi_mod1_phaseinjector3_command_storage[3]);
	end else begin
		sdram_pi_mod1_inti_p3_cs_n <= {1{1'd1}};
		sdram_pi_mod1_inti_p3_we_n <= 1'd1;
		sdram_pi_mod1_inti_p3_cas_n <= 1'd1;
		sdram_pi_mod1_inti_p3_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_28 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod1_inti_p3_address = sdram_pi_mod1_phaseinjector3_address_storage;
assign sdram_pi_mod1_inti_p3_bank = sdram_pi_mod1_phaseinjector3_baddress_storage;
assign sdram_pi_mod1_inti_p3_wrdata_en = (sdram_pi_mod1_phaseinjector3_command_issue_re & sdram_pi_mod1_phaseinjector3_command_storage[4]);
assign sdram_pi_mod1_inti_p3_rddata_en = (sdram_pi_mod1_phaseinjector3_command_issue_re & sdram_pi_mod1_phaseinjector3_command_storage[5]);
assign sdram_pi_mod1_inti_p3_wrdata = sdram_pi_mod1_phaseinjector3_wrdata_storage;
assign sdram_pi_mod1_inti_p3_wrdata_mask = 1'd0;
assign sdram_pi_mod2_inti_p0_cke = sdram_cke;
assign sdram_pi_mod2_inti_p1_cke = sdram_cke;
assign sdram_pi_mod2_inti_p2_cke = sdram_cke;
assign sdram_pi_mod2_inti_p3_cke = sdram_cke;
assign sdram_pi_mod2_inti_p0_odt = sdram_odt;
assign sdram_pi_mod2_inti_p1_odt = sdram_odt;
assign sdram_pi_mod2_inti_p2_odt = sdram_odt;
assign sdram_pi_mod2_inti_p3_odt = sdram_odt;
assign sdram_pi_mod2_inti_p0_reset_n = sdram_reset_n;
assign sdram_pi_mod2_inti_p1_reset_n = sdram_reset_n;
assign sdram_pi_mod2_inti_p2_reset_n = sdram_reset_n;
assign sdram_pi_mod2_inti_p3_reset_n = sdram_reset_n;

// synthesis translate_off
reg dummy_d_29;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod2_inti_p0_cas_n <= 1'd1;
	sdram_pi_mod2_inti_p0_cs_n <= 1'd1;
	sdram_pi_mod2_inti_p0_ras_n <= 1'd1;
	sdram_pi_mod2_inti_p0_we_n <= 1'd1;
	if (sdram_pi_mod2_phaseinjector0_command_issue_re) begin
		sdram_pi_mod2_inti_p0_cs_n <= {1{(~sdram_pi_mod2_phaseinjector0_command_storage[0])}};
		sdram_pi_mod2_inti_p0_we_n <= (~sdram_pi_mod2_phaseinjector0_command_storage[1]);
		sdram_pi_mod2_inti_p0_cas_n <= (~sdram_pi_mod2_phaseinjector0_command_storage[2]);
		sdram_pi_mod2_inti_p0_ras_n <= (~sdram_pi_mod2_phaseinjector0_command_storage[3]);
	end else begin
		sdram_pi_mod2_inti_p0_cs_n <= {1{1'd1}};
		sdram_pi_mod2_inti_p0_we_n <= 1'd1;
		sdram_pi_mod2_inti_p0_cas_n <= 1'd1;
		sdram_pi_mod2_inti_p0_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_29 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod2_inti_p0_address = sdram_pi_mod2_phaseinjector0_address_storage;
assign sdram_pi_mod2_inti_p0_bank = sdram_pi_mod2_phaseinjector0_baddress_storage;
assign sdram_pi_mod2_inti_p0_wrdata_en = (sdram_pi_mod2_phaseinjector0_command_issue_re & sdram_pi_mod2_phaseinjector0_command_storage[4]);
assign sdram_pi_mod2_inti_p0_rddata_en = (sdram_pi_mod2_phaseinjector0_command_issue_re & sdram_pi_mod2_phaseinjector0_command_storage[5]);
assign sdram_pi_mod2_inti_p0_wrdata = sdram_pi_mod2_phaseinjector0_wrdata_storage;
assign sdram_pi_mod2_inti_p0_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_30;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod2_inti_p1_cas_n <= 1'd1;
	sdram_pi_mod2_inti_p1_cs_n <= 1'd1;
	sdram_pi_mod2_inti_p1_ras_n <= 1'd1;
	sdram_pi_mod2_inti_p1_we_n <= 1'd1;
	if (sdram_pi_mod2_phaseinjector1_command_issue_re) begin
		sdram_pi_mod2_inti_p1_cs_n <= {1{(~sdram_pi_mod2_phaseinjector1_command_storage[0])}};
		sdram_pi_mod2_inti_p1_we_n <= (~sdram_pi_mod2_phaseinjector1_command_storage[1]);
		sdram_pi_mod2_inti_p1_cas_n <= (~sdram_pi_mod2_phaseinjector1_command_storage[2]);
		sdram_pi_mod2_inti_p1_ras_n <= (~sdram_pi_mod2_phaseinjector1_command_storage[3]);
	end else begin
		sdram_pi_mod2_inti_p1_cs_n <= {1{1'd1}};
		sdram_pi_mod2_inti_p1_we_n <= 1'd1;
		sdram_pi_mod2_inti_p1_cas_n <= 1'd1;
		sdram_pi_mod2_inti_p1_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_30 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod2_inti_p1_address = sdram_pi_mod2_phaseinjector1_address_storage;
assign sdram_pi_mod2_inti_p1_bank = sdram_pi_mod2_phaseinjector1_baddress_storage;
assign sdram_pi_mod2_inti_p1_wrdata_en = (sdram_pi_mod2_phaseinjector1_command_issue_re & sdram_pi_mod2_phaseinjector1_command_storage[4]);
assign sdram_pi_mod2_inti_p1_rddata_en = (sdram_pi_mod2_phaseinjector1_command_issue_re & sdram_pi_mod2_phaseinjector1_command_storage[5]);
assign sdram_pi_mod2_inti_p1_wrdata = sdram_pi_mod2_phaseinjector1_wrdata_storage;
assign sdram_pi_mod2_inti_p1_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_31;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod2_inti_p2_cas_n <= 1'd1;
	sdram_pi_mod2_inti_p2_cs_n <= 1'd1;
	sdram_pi_mod2_inti_p2_ras_n <= 1'd1;
	sdram_pi_mod2_inti_p2_we_n <= 1'd1;
	if (sdram_pi_mod2_phaseinjector2_command_issue_re) begin
		sdram_pi_mod2_inti_p2_cs_n <= {1{(~sdram_pi_mod2_phaseinjector2_command_storage[0])}};
		sdram_pi_mod2_inti_p2_we_n <= (~sdram_pi_mod2_phaseinjector2_command_storage[1]);
		sdram_pi_mod2_inti_p2_cas_n <= (~sdram_pi_mod2_phaseinjector2_command_storage[2]);
		sdram_pi_mod2_inti_p2_ras_n <= (~sdram_pi_mod2_phaseinjector2_command_storage[3]);
	end else begin
		sdram_pi_mod2_inti_p2_cs_n <= {1{1'd1}};
		sdram_pi_mod2_inti_p2_we_n <= 1'd1;
		sdram_pi_mod2_inti_p2_cas_n <= 1'd1;
		sdram_pi_mod2_inti_p2_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_31 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod2_inti_p2_address = sdram_pi_mod2_phaseinjector2_address_storage;
assign sdram_pi_mod2_inti_p2_bank = sdram_pi_mod2_phaseinjector2_baddress_storage;
assign sdram_pi_mod2_inti_p2_wrdata_en = (sdram_pi_mod2_phaseinjector2_command_issue_re & sdram_pi_mod2_phaseinjector2_command_storage[4]);
assign sdram_pi_mod2_inti_p2_rddata_en = (sdram_pi_mod2_phaseinjector2_command_issue_re & sdram_pi_mod2_phaseinjector2_command_storage[5]);
assign sdram_pi_mod2_inti_p2_wrdata = sdram_pi_mod2_phaseinjector2_wrdata_storage;
assign sdram_pi_mod2_inti_p2_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_32;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod2_inti_p3_cas_n <= 1'd1;
	sdram_pi_mod2_inti_p3_cs_n <= 1'd1;
	sdram_pi_mod2_inti_p3_ras_n <= 1'd1;
	sdram_pi_mod2_inti_p3_we_n <= 1'd1;
	if (sdram_pi_mod2_phaseinjector3_command_issue_re) begin
		sdram_pi_mod2_inti_p3_cs_n <= {1{(~sdram_pi_mod2_phaseinjector3_command_storage[0])}};
		sdram_pi_mod2_inti_p3_we_n <= (~sdram_pi_mod2_phaseinjector3_command_storage[1]);
		sdram_pi_mod2_inti_p3_cas_n <= (~sdram_pi_mod2_phaseinjector3_command_storage[2]);
		sdram_pi_mod2_inti_p3_ras_n <= (~sdram_pi_mod2_phaseinjector3_command_storage[3]);
	end else begin
		sdram_pi_mod2_inti_p3_cs_n <= {1{1'd1}};
		sdram_pi_mod2_inti_p3_we_n <= 1'd1;
		sdram_pi_mod2_inti_p3_cas_n <= 1'd1;
		sdram_pi_mod2_inti_p3_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_32 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod2_inti_p3_address = sdram_pi_mod2_phaseinjector3_address_storage;
assign sdram_pi_mod2_inti_p3_bank = sdram_pi_mod2_phaseinjector3_baddress_storage;
assign sdram_pi_mod2_inti_p3_wrdata_en = (sdram_pi_mod2_phaseinjector3_command_issue_re & sdram_pi_mod2_phaseinjector3_command_storage[4]);
assign sdram_pi_mod2_inti_p3_rddata_en = (sdram_pi_mod2_phaseinjector3_command_issue_re & sdram_pi_mod2_phaseinjector3_command_storage[5]);
assign sdram_pi_mod2_inti_p3_wrdata = sdram_pi_mod2_phaseinjector3_wrdata_storage;
assign sdram_pi_mod2_inti_p3_wrdata_mask = 1'd0;
assign sdram_pi_mod3_inti_p0_cke = sdram_cke;
assign sdram_pi_mod3_inti_p1_cke = sdram_cke;
assign sdram_pi_mod3_inti_p2_cke = sdram_cke;
assign sdram_pi_mod3_inti_p3_cke = sdram_cke;
assign sdram_pi_mod3_inti_p0_odt = sdram_odt;
assign sdram_pi_mod3_inti_p1_odt = sdram_odt;
assign sdram_pi_mod3_inti_p2_odt = sdram_odt;
assign sdram_pi_mod3_inti_p3_odt = sdram_odt;
assign sdram_pi_mod3_inti_p0_reset_n = sdram_reset_n;
assign sdram_pi_mod3_inti_p1_reset_n = sdram_reset_n;
assign sdram_pi_mod3_inti_p2_reset_n = sdram_reset_n;
assign sdram_pi_mod3_inti_p3_reset_n = sdram_reset_n;

// synthesis translate_off
reg dummy_d_33;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod3_inti_p0_cas_n <= 1'd1;
	sdram_pi_mod3_inti_p0_cs_n <= 1'd1;
	sdram_pi_mod3_inti_p0_ras_n <= 1'd1;
	sdram_pi_mod3_inti_p0_we_n <= 1'd1;
	if (sdram_pi_mod3_phaseinjector0_command_issue_re) begin
		sdram_pi_mod3_inti_p0_cs_n <= {1{(~sdram_pi_mod3_phaseinjector0_command_storage[0])}};
		sdram_pi_mod3_inti_p0_we_n <= (~sdram_pi_mod3_phaseinjector0_command_storage[1]);
		sdram_pi_mod3_inti_p0_cas_n <= (~sdram_pi_mod3_phaseinjector0_command_storage[2]);
		sdram_pi_mod3_inti_p0_ras_n <= (~sdram_pi_mod3_phaseinjector0_command_storage[3]);
	end else begin
		sdram_pi_mod3_inti_p0_cs_n <= {1{1'd1}};
		sdram_pi_mod3_inti_p0_we_n <= 1'd1;
		sdram_pi_mod3_inti_p0_cas_n <= 1'd1;
		sdram_pi_mod3_inti_p0_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_33 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_inti_p0_address = sdram_pi_mod3_phaseinjector0_address_storage;
assign sdram_pi_mod3_inti_p0_bank = sdram_pi_mod3_phaseinjector0_baddress_storage;
assign sdram_pi_mod3_inti_p0_wrdata_en = (sdram_pi_mod3_phaseinjector0_command_issue_re & sdram_pi_mod3_phaseinjector0_command_storage[4]);
assign sdram_pi_mod3_inti_p0_rddata_en = (sdram_pi_mod3_phaseinjector0_command_issue_re & sdram_pi_mod3_phaseinjector0_command_storage[5]);
assign sdram_pi_mod3_inti_p0_wrdata = sdram_pi_mod3_phaseinjector0_wrdata_storage;
assign sdram_pi_mod3_inti_p0_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_34;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod3_inti_p1_cas_n <= 1'd1;
	sdram_pi_mod3_inti_p1_cs_n <= 1'd1;
	sdram_pi_mod3_inti_p1_ras_n <= 1'd1;
	sdram_pi_mod3_inti_p1_we_n <= 1'd1;
	if (sdram_pi_mod3_phaseinjector1_command_issue_re) begin
		sdram_pi_mod3_inti_p1_cs_n <= {1{(~sdram_pi_mod3_phaseinjector1_command_storage[0])}};
		sdram_pi_mod3_inti_p1_we_n <= (~sdram_pi_mod3_phaseinjector1_command_storage[1]);
		sdram_pi_mod3_inti_p1_cas_n <= (~sdram_pi_mod3_phaseinjector1_command_storage[2]);
		sdram_pi_mod3_inti_p1_ras_n <= (~sdram_pi_mod3_phaseinjector1_command_storage[3]);
	end else begin
		sdram_pi_mod3_inti_p1_cs_n <= {1{1'd1}};
		sdram_pi_mod3_inti_p1_we_n <= 1'd1;
		sdram_pi_mod3_inti_p1_cas_n <= 1'd1;
		sdram_pi_mod3_inti_p1_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_34 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_inti_p1_address = sdram_pi_mod3_phaseinjector1_address_storage;
assign sdram_pi_mod3_inti_p1_bank = sdram_pi_mod3_phaseinjector1_baddress_storage;
assign sdram_pi_mod3_inti_p1_wrdata_en = (sdram_pi_mod3_phaseinjector1_command_issue_re & sdram_pi_mod3_phaseinjector1_command_storage[4]);
assign sdram_pi_mod3_inti_p1_rddata_en = (sdram_pi_mod3_phaseinjector1_command_issue_re & sdram_pi_mod3_phaseinjector1_command_storage[5]);
assign sdram_pi_mod3_inti_p1_wrdata = sdram_pi_mod3_phaseinjector1_wrdata_storage;
assign sdram_pi_mod3_inti_p1_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_35;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod3_inti_p2_cas_n <= 1'd1;
	sdram_pi_mod3_inti_p2_cs_n <= 1'd1;
	sdram_pi_mod3_inti_p2_ras_n <= 1'd1;
	sdram_pi_mod3_inti_p2_we_n <= 1'd1;
	if (sdram_pi_mod3_phaseinjector2_command_issue_re) begin
		sdram_pi_mod3_inti_p2_cs_n <= {1{(~sdram_pi_mod3_phaseinjector2_command_storage[0])}};
		sdram_pi_mod3_inti_p2_we_n <= (~sdram_pi_mod3_phaseinjector2_command_storage[1]);
		sdram_pi_mod3_inti_p2_cas_n <= (~sdram_pi_mod3_phaseinjector2_command_storage[2]);
		sdram_pi_mod3_inti_p2_ras_n <= (~sdram_pi_mod3_phaseinjector2_command_storage[3]);
	end else begin
		sdram_pi_mod3_inti_p2_cs_n <= {1{1'd1}};
		sdram_pi_mod3_inti_p2_we_n <= 1'd1;
		sdram_pi_mod3_inti_p2_cas_n <= 1'd1;
		sdram_pi_mod3_inti_p2_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_35 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_inti_p2_address = sdram_pi_mod3_phaseinjector2_address_storage;
assign sdram_pi_mod3_inti_p2_bank = sdram_pi_mod3_phaseinjector2_baddress_storage;
assign sdram_pi_mod3_inti_p2_wrdata_en = (sdram_pi_mod3_phaseinjector2_command_issue_re & sdram_pi_mod3_phaseinjector2_command_storage[4]);
assign sdram_pi_mod3_inti_p2_rddata_en = (sdram_pi_mod3_phaseinjector2_command_issue_re & sdram_pi_mod3_phaseinjector2_command_storage[5]);
assign sdram_pi_mod3_inti_p2_wrdata = sdram_pi_mod3_phaseinjector2_wrdata_storage;
assign sdram_pi_mod3_inti_p2_wrdata_mask = 1'd0;

// synthesis translate_off
reg dummy_d_36;
// synthesis translate_on
always @(*) begin
	sdram_pi_mod3_inti_p3_cas_n <= 1'd1;
	sdram_pi_mod3_inti_p3_cs_n <= 1'd1;
	sdram_pi_mod3_inti_p3_ras_n <= 1'd1;
	sdram_pi_mod3_inti_p3_we_n <= 1'd1;
	if (sdram_pi_mod3_phaseinjector3_command_issue_re) begin
		sdram_pi_mod3_inti_p3_cs_n <= {1{(~sdram_pi_mod3_phaseinjector3_command_storage[0])}};
		sdram_pi_mod3_inti_p3_we_n <= (~sdram_pi_mod3_phaseinjector3_command_storage[1]);
		sdram_pi_mod3_inti_p3_cas_n <= (~sdram_pi_mod3_phaseinjector3_command_storage[2]);
		sdram_pi_mod3_inti_p3_ras_n <= (~sdram_pi_mod3_phaseinjector3_command_storage[3]);
	end else begin
		sdram_pi_mod3_inti_p3_cs_n <= {1{1'd1}};
		sdram_pi_mod3_inti_p3_we_n <= 1'd1;
		sdram_pi_mod3_inti_p3_cas_n <= 1'd1;
		sdram_pi_mod3_inti_p3_ras_n <= 1'd1;
	end
// synthesis translate_off
	dummy_d_36 <= dummy_s;
// synthesis translate_on
end
assign sdram_pi_mod3_inti_p3_address = sdram_pi_mod3_phaseinjector3_address_storage;
assign sdram_pi_mod3_inti_p3_bank = sdram_pi_mod3_phaseinjector3_baddress_storage;
assign sdram_pi_mod3_inti_p3_wrdata_en = (sdram_pi_mod3_phaseinjector3_command_issue_re & sdram_pi_mod3_phaseinjector3_command_storage[4]);
assign sdram_pi_mod3_inti_p3_rddata_en = (sdram_pi_mod3_phaseinjector3_command_issue_re & sdram_pi_mod3_phaseinjector3_command_storage[5]);
assign sdram_pi_mod3_inti_p3_wrdata = sdram_pi_mod3_phaseinjector3_wrdata_storage;
assign sdram_pi_mod3_inti_p3_wrdata_mask = 1'd0;
assign sdram_control0 = (((sdram_TMRslave_p0_address[13:0] & sdram_TMRslave_p0_address[27:14]) | (sdram_TMRslave_p0_address[27:14] & sdram_TMRslave_p0_address[41:28])) | (sdram_TMRslave_p0_address[13:0] & sdram_TMRslave_p0_address[41:28]));
assign sdram_slave_p0_address = sdram_control0;
assign sdram_control1 = (((sdram_TMRslave_p0_bank[2:0] & sdram_TMRslave_p0_bank[5:3]) | (sdram_TMRslave_p0_bank[5:3] & sdram_TMRslave_p0_bank[8:6])) | (sdram_TMRslave_p0_bank[2:0] & sdram_TMRslave_p0_bank[8:6]));
assign sdram_slave_p0_bank = sdram_control1;
assign sdram_control2 = (((sdram_TMRslave_p0_cas_n[0] & sdram_TMRslave_p0_cas_n[1]) | (sdram_TMRslave_p0_cas_n[1] & sdram_TMRslave_p0_cas_n[2])) | (sdram_TMRslave_p0_cas_n[0] & sdram_TMRslave_p0_cas_n[2]));
assign sdram_slave_p0_cas_n = sdram_control2;
assign sdram_control3 = (((sdram_TMRslave_p0_cs_n[0] & sdram_TMRslave_p0_cs_n[1]) | (sdram_TMRslave_p0_cs_n[1] & sdram_TMRslave_p0_cs_n[2])) | (sdram_TMRslave_p0_cs_n[0] & sdram_TMRslave_p0_cs_n[2]));
assign sdram_slave_p0_cs_n = sdram_control3;
assign sdram_control4 = (((sdram_TMRslave_p0_ras_n[0] & sdram_TMRslave_p0_ras_n[1]) | (sdram_TMRslave_p0_ras_n[1] & sdram_TMRslave_p0_ras_n[2])) | (sdram_TMRslave_p0_ras_n[0] & sdram_TMRslave_p0_ras_n[2]));
assign sdram_slave_p0_ras_n = sdram_control4;
assign sdram_control5 = (((sdram_TMRslave_p0_we_n[0] & sdram_TMRslave_p0_we_n[1]) | (sdram_TMRslave_p0_we_n[1] & sdram_TMRslave_p0_we_n[2])) | (sdram_TMRslave_p0_we_n[0] & sdram_TMRslave_p0_we_n[2]));
assign sdram_slave_p0_we_n = sdram_control5;
assign sdram_control6 = (((sdram_TMRslave_p0_cke[0] & sdram_TMRslave_p0_cke[1]) | (sdram_TMRslave_p0_cke[1] & sdram_TMRslave_p0_cke[2])) | (sdram_TMRslave_p0_cke[0] & sdram_TMRslave_p0_cke[2]));
assign sdram_slave_p0_cke = sdram_control6;
assign sdram_control7 = (((sdram_TMRslave_p0_odt[0] & sdram_TMRslave_p0_odt[1]) | (sdram_TMRslave_p0_odt[1] & sdram_TMRslave_p0_odt[2])) | (sdram_TMRslave_p0_odt[0] & sdram_TMRslave_p0_odt[2]));
assign sdram_slave_p0_odt = sdram_control7;
assign sdram_control8 = (((sdram_TMRslave_p0_reset_n[0] & sdram_TMRslave_p0_reset_n[1]) | (sdram_TMRslave_p0_reset_n[1] & sdram_TMRslave_p0_reset_n[2])) | (sdram_TMRslave_p0_reset_n[0] & sdram_TMRslave_p0_reset_n[2]));
assign sdram_slave_p0_reset_n = sdram_control8;
assign sdram_control9 = (((sdram_TMRslave_p0_act_n[0] & sdram_TMRslave_p0_act_n[1]) | (sdram_TMRslave_p0_act_n[1] & sdram_TMRslave_p0_act_n[2])) | (sdram_TMRslave_p0_act_n[0] & sdram_TMRslave_p0_act_n[2]));
assign sdram_slave_p0_act_n = sdram_control9;
assign sdram_control10 = (((sdram_TMRslave_p0_wrdata[63:0] & sdram_TMRslave_p0_wrdata[127:64]) | (sdram_TMRslave_p0_wrdata[127:64] & sdram_TMRslave_p0_wrdata[191:128])) | (sdram_TMRslave_p0_wrdata[63:0] & sdram_TMRslave_p0_wrdata[191:128]));
assign sdram_slave_p0_wrdata = sdram_control10;
assign sdram_control11 = (((sdram_TMRslave_p0_wrdata_en[0] & sdram_TMRslave_p0_wrdata_en[1]) | (sdram_TMRslave_p0_wrdata_en[1] & sdram_TMRslave_p0_wrdata_en[2])) | (sdram_TMRslave_p0_wrdata_en[0] & sdram_TMRslave_p0_wrdata_en[2]));
assign sdram_slave_p0_wrdata_en = sdram_control11;
assign sdram_control12 = (((sdram_TMRslave_p0_wrdata_mask[7:0] & sdram_TMRslave_p0_wrdata_mask[15:8]) | (sdram_TMRslave_p0_wrdata_mask[15:8] & sdram_TMRslave_p0_wrdata_mask[23:16])) | (sdram_TMRslave_p0_wrdata_mask[7:0] & sdram_TMRslave_p0_wrdata_mask[23:16]));
assign sdram_slave_p0_wrdata_mask = sdram_control12;
assign sdram_control13 = (((sdram_TMRslave_p0_rddata_en[0] & sdram_TMRslave_p0_rddata_en[1]) | (sdram_TMRslave_p0_rddata_en[1] & sdram_TMRslave_p0_rddata_en[2])) | (sdram_TMRslave_p0_rddata_en[0] & sdram_TMRslave_p0_rddata_en[2]));
assign sdram_slave_p0_rddata_en = sdram_control13;
assign sdram_TMRslave_p0_rddata = {3{sdram_slave_p0_rddata}};
assign sdram_TMRslave_p0_rddata_valid = {3{sdram_slave_p0_rddata_valid}};
assign sdram_control14 = (((sdram_TMRslave_p1_address[13:0] & sdram_TMRslave_p1_address[27:14]) | (sdram_TMRslave_p1_address[27:14] & sdram_TMRslave_p1_address[41:28])) | (sdram_TMRslave_p1_address[13:0] & sdram_TMRslave_p1_address[41:28]));
assign sdram_slave_p1_address = sdram_control14;
assign sdram_control15 = (((sdram_TMRslave_p1_bank[2:0] & sdram_TMRslave_p1_bank[5:3]) | (sdram_TMRslave_p1_bank[5:3] & sdram_TMRslave_p1_bank[8:6])) | (sdram_TMRslave_p1_bank[2:0] & sdram_TMRslave_p1_bank[8:6]));
assign sdram_slave_p1_bank = sdram_control15;
assign sdram_control16 = (((sdram_TMRslave_p1_cas_n[0] & sdram_TMRslave_p1_cas_n[1]) | (sdram_TMRslave_p1_cas_n[1] & sdram_TMRslave_p1_cas_n[2])) | (sdram_TMRslave_p1_cas_n[0] & sdram_TMRslave_p1_cas_n[2]));
assign sdram_slave_p1_cas_n = sdram_control16;
assign sdram_control17 = (((sdram_TMRslave_p1_cs_n[0] & sdram_TMRslave_p1_cs_n[1]) | (sdram_TMRslave_p1_cs_n[1] & sdram_TMRslave_p1_cs_n[2])) | (sdram_TMRslave_p1_cs_n[0] & sdram_TMRslave_p1_cs_n[2]));
assign sdram_slave_p1_cs_n = sdram_control17;
assign sdram_control18 = (((sdram_TMRslave_p1_ras_n[0] & sdram_TMRslave_p1_ras_n[1]) | (sdram_TMRslave_p1_ras_n[1] & sdram_TMRslave_p1_ras_n[2])) | (sdram_TMRslave_p1_ras_n[0] & sdram_TMRslave_p1_ras_n[2]));
assign sdram_slave_p1_ras_n = sdram_control18;
assign sdram_control19 = (((sdram_TMRslave_p1_we_n[0] & sdram_TMRslave_p1_we_n[1]) | (sdram_TMRslave_p1_we_n[1] & sdram_TMRslave_p1_we_n[2])) | (sdram_TMRslave_p1_we_n[0] & sdram_TMRslave_p1_we_n[2]));
assign sdram_slave_p1_we_n = sdram_control19;
assign sdram_control20 = (((sdram_TMRslave_p1_cke[0] & sdram_TMRslave_p1_cke[1]) | (sdram_TMRslave_p1_cke[1] & sdram_TMRslave_p1_cke[2])) | (sdram_TMRslave_p1_cke[0] & sdram_TMRslave_p1_cke[2]));
assign sdram_slave_p1_cke = sdram_control20;
assign sdram_control21 = (((sdram_TMRslave_p1_odt[0] & sdram_TMRslave_p1_odt[1]) | (sdram_TMRslave_p1_odt[1] & sdram_TMRslave_p1_odt[2])) | (sdram_TMRslave_p1_odt[0] & sdram_TMRslave_p1_odt[2]));
assign sdram_slave_p1_odt = sdram_control21;
assign sdram_control22 = (((sdram_TMRslave_p1_reset_n[0] & sdram_TMRslave_p1_reset_n[1]) | (sdram_TMRslave_p1_reset_n[1] & sdram_TMRslave_p1_reset_n[2])) | (sdram_TMRslave_p1_reset_n[0] & sdram_TMRslave_p1_reset_n[2]));
assign sdram_slave_p1_reset_n = sdram_control22;
assign sdram_control23 = (((sdram_TMRslave_p1_act_n[0] & sdram_TMRslave_p1_act_n[1]) | (sdram_TMRslave_p1_act_n[1] & sdram_TMRslave_p1_act_n[2])) | (sdram_TMRslave_p1_act_n[0] & sdram_TMRslave_p1_act_n[2]));
assign sdram_slave_p1_act_n = sdram_control23;
assign sdram_control24 = (((sdram_TMRslave_p1_wrdata[63:0] & sdram_TMRslave_p1_wrdata[127:64]) | (sdram_TMRslave_p1_wrdata[127:64] & sdram_TMRslave_p1_wrdata[191:128])) | (sdram_TMRslave_p1_wrdata[63:0] & sdram_TMRslave_p1_wrdata[191:128]));
assign sdram_slave_p1_wrdata = sdram_control24;
assign sdram_control25 = (((sdram_TMRslave_p1_wrdata_en[0] & sdram_TMRslave_p1_wrdata_en[1]) | (sdram_TMRslave_p1_wrdata_en[1] & sdram_TMRslave_p1_wrdata_en[2])) | (sdram_TMRslave_p1_wrdata_en[0] & sdram_TMRslave_p1_wrdata_en[2]));
assign sdram_slave_p1_wrdata_en = sdram_control25;
assign sdram_control26 = (((sdram_TMRslave_p1_wrdata_mask[7:0] & sdram_TMRslave_p1_wrdata_mask[15:8]) | (sdram_TMRslave_p1_wrdata_mask[15:8] & sdram_TMRslave_p1_wrdata_mask[23:16])) | (sdram_TMRslave_p1_wrdata_mask[7:0] & sdram_TMRslave_p1_wrdata_mask[23:16]));
assign sdram_slave_p1_wrdata_mask = sdram_control26;
assign sdram_control27 = (((sdram_TMRslave_p1_rddata_en[0] & sdram_TMRslave_p1_rddata_en[1]) | (sdram_TMRslave_p1_rddata_en[1] & sdram_TMRslave_p1_rddata_en[2])) | (sdram_TMRslave_p1_rddata_en[0] & sdram_TMRslave_p1_rddata_en[2]));
assign sdram_slave_p1_rddata_en = sdram_control27;
assign sdram_TMRslave_p1_rddata = {3{sdram_slave_p1_rddata}};
assign sdram_TMRslave_p1_rddata_valid = {3{sdram_slave_p1_rddata_valid}};
assign sdram_control28 = (((sdram_TMRslave_p2_address[13:0] & sdram_TMRslave_p2_address[27:14]) | (sdram_TMRslave_p2_address[27:14] & sdram_TMRslave_p2_address[41:28])) | (sdram_TMRslave_p2_address[13:0] & sdram_TMRslave_p2_address[41:28]));
assign sdram_slave_p2_address = sdram_control28;
assign sdram_control29 = (((sdram_TMRslave_p2_bank[2:0] & sdram_TMRslave_p2_bank[5:3]) | (sdram_TMRslave_p2_bank[5:3] & sdram_TMRslave_p2_bank[8:6])) | (sdram_TMRslave_p2_bank[2:0] & sdram_TMRslave_p2_bank[8:6]));
assign sdram_slave_p2_bank = sdram_control29;
assign sdram_control30 = (((sdram_TMRslave_p2_cas_n[0] & sdram_TMRslave_p2_cas_n[1]) | (sdram_TMRslave_p2_cas_n[1] & sdram_TMRslave_p2_cas_n[2])) | (sdram_TMRslave_p2_cas_n[0] & sdram_TMRslave_p2_cas_n[2]));
assign sdram_slave_p2_cas_n = sdram_control30;
assign sdram_control31 = (((sdram_TMRslave_p2_cs_n[0] & sdram_TMRslave_p2_cs_n[1]) | (sdram_TMRslave_p2_cs_n[1] & sdram_TMRslave_p2_cs_n[2])) | (sdram_TMRslave_p2_cs_n[0] & sdram_TMRslave_p2_cs_n[2]));
assign sdram_slave_p2_cs_n = sdram_control31;
assign sdram_control32 = (((sdram_TMRslave_p2_ras_n[0] & sdram_TMRslave_p2_ras_n[1]) | (sdram_TMRslave_p2_ras_n[1] & sdram_TMRslave_p2_ras_n[2])) | (sdram_TMRslave_p2_ras_n[0] & sdram_TMRslave_p2_ras_n[2]));
assign sdram_slave_p2_ras_n = sdram_control32;
assign sdram_control33 = (((sdram_TMRslave_p2_we_n[0] & sdram_TMRslave_p2_we_n[1]) | (sdram_TMRslave_p2_we_n[1] & sdram_TMRslave_p2_we_n[2])) | (sdram_TMRslave_p2_we_n[0] & sdram_TMRslave_p2_we_n[2]));
assign sdram_slave_p2_we_n = sdram_control33;
assign sdram_control34 = (((sdram_TMRslave_p2_cke[0] & sdram_TMRslave_p2_cke[1]) | (sdram_TMRslave_p2_cke[1] & sdram_TMRslave_p2_cke[2])) | (sdram_TMRslave_p2_cke[0] & sdram_TMRslave_p2_cke[2]));
assign sdram_slave_p2_cke = sdram_control34;
assign sdram_control35 = (((sdram_TMRslave_p2_odt[0] & sdram_TMRslave_p2_odt[1]) | (sdram_TMRslave_p2_odt[1] & sdram_TMRslave_p2_odt[2])) | (sdram_TMRslave_p2_odt[0] & sdram_TMRslave_p2_odt[2]));
assign sdram_slave_p2_odt = sdram_control35;
assign sdram_control36 = (((sdram_TMRslave_p2_reset_n[0] & sdram_TMRslave_p2_reset_n[1]) | (sdram_TMRslave_p2_reset_n[1] & sdram_TMRslave_p2_reset_n[2])) | (sdram_TMRslave_p2_reset_n[0] & sdram_TMRslave_p2_reset_n[2]));
assign sdram_slave_p2_reset_n = sdram_control36;
assign sdram_control37 = (((sdram_TMRslave_p2_act_n[0] & sdram_TMRslave_p2_act_n[1]) | (sdram_TMRslave_p2_act_n[1] & sdram_TMRslave_p2_act_n[2])) | (sdram_TMRslave_p2_act_n[0] & sdram_TMRslave_p2_act_n[2]));
assign sdram_slave_p2_act_n = sdram_control37;
assign sdram_control38 = (((sdram_TMRslave_p2_wrdata[63:0] & sdram_TMRslave_p2_wrdata[127:64]) | (sdram_TMRslave_p2_wrdata[127:64] & sdram_TMRslave_p2_wrdata[191:128])) | (sdram_TMRslave_p2_wrdata[63:0] & sdram_TMRslave_p2_wrdata[191:128]));
assign sdram_slave_p2_wrdata = sdram_control38;
assign sdram_control39 = (((sdram_TMRslave_p2_wrdata_en[0] & sdram_TMRslave_p2_wrdata_en[1]) | (sdram_TMRslave_p2_wrdata_en[1] & sdram_TMRslave_p2_wrdata_en[2])) | (sdram_TMRslave_p2_wrdata_en[0] & sdram_TMRslave_p2_wrdata_en[2]));
assign sdram_slave_p2_wrdata_en = sdram_control39;
assign sdram_control40 = (((sdram_TMRslave_p2_wrdata_mask[7:0] & sdram_TMRslave_p2_wrdata_mask[15:8]) | (sdram_TMRslave_p2_wrdata_mask[15:8] & sdram_TMRslave_p2_wrdata_mask[23:16])) | (sdram_TMRslave_p2_wrdata_mask[7:0] & sdram_TMRslave_p2_wrdata_mask[23:16]));
assign sdram_slave_p2_wrdata_mask = sdram_control40;
assign sdram_control41 = (((sdram_TMRslave_p2_rddata_en[0] & sdram_TMRslave_p2_rddata_en[1]) | (sdram_TMRslave_p2_rddata_en[1] & sdram_TMRslave_p2_rddata_en[2])) | (sdram_TMRslave_p2_rddata_en[0] & sdram_TMRslave_p2_rddata_en[2]));
assign sdram_slave_p2_rddata_en = sdram_control41;
assign sdram_TMRslave_p2_rddata = {3{sdram_slave_p2_rddata}};
assign sdram_TMRslave_p2_rddata_valid = {3{sdram_slave_p2_rddata_valid}};
assign sdram_control42 = (((sdram_TMRslave_p3_address[13:0] & sdram_TMRslave_p3_address[27:14]) | (sdram_TMRslave_p3_address[27:14] & sdram_TMRslave_p3_address[41:28])) | (sdram_TMRslave_p3_address[13:0] & sdram_TMRslave_p3_address[41:28]));
assign sdram_slave_p3_address = sdram_control42;
assign sdram_control43 = (((sdram_TMRslave_p3_bank[2:0] & sdram_TMRslave_p3_bank[5:3]) | (sdram_TMRslave_p3_bank[5:3] & sdram_TMRslave_p3_bank[8:6])) | (sdram_TMRslave_p3_bank[2:0] & sdram_TMRslave_p3_bank[8:6]));
assign sdram_slave_p3_bank = sdram_control43;
assign sdram_control44 = (((sdram_TMRslave_p3_cas_n[0] & sdram_TMRslave_p3_cas_n[1]) | (sdram_TMRslave_p3_cas_n[1] & sdram_TMRslave_p3_cas_n[2])) | (sdram_TMRslave_p3_cas_n[0] & sdram_TMRslave_p3_cas_n[2]));
assign sdram_slave_p3_cas_n = sdram_control44;
assign sdram_control45 = (((sdram_TMRslave_p3_cs_n[0] & sdram_TMRslave_p3_cs_n[1]) | (sdram_TMRslave_p3_cs_n[1] & sdram_TMRslave_p3_cs_n[2])) | (sdram_TMRslave_p3_cs_n[0] & sdram_TMRslave_p3_cs_n[2]));
assign sdram_slave_p3_cs_n = sdram_control45;
assign sdram_control46 = (((sdram_TMRslave_p3_ras_n[0] & sdram_TMRslave_p3_ras_n[1]) | (sdram_TMRslave_p3_ras_n[1] & sdram_TMRslave_p3_ras_n[2])) | (sdram_TMRslave_p3_ras_n[0] & sdram_TMRslave_p3_ras_n[2]));
assign sdram_slave_p3_ras_n = sdram_control46;
assign sdram_control47 = (((sdram_TMRslave_p3_we_n[0] & sdram_TMRslave_p3_we_n[1]) | (sdram_TMRslave_p3_we_n[1] & sdram_TMRslave_p3_we_n[2])) | (sdram_TMRslave_p3_we_n[0] & sdram_TMRslave_p3_we_n[2]));
assign sdram_slave_p3_we_n = sdram_control47;
assign sdram_control48 = (((sdram_TMRslave_p3_cke[0] & sdram_TMRslave_p3_cke[1]) | (sdram_TMRslave_p3_cke[1] & sdram_TMRslave_p3_cke[2])) | (sdram_TMRslave_p3_cke[0] & sdram_TMRslave_p3_cke[2]));
assign sdram_slave_p3_cke = sdram_control48;
assign sdram_control49 = (((sdram_TMRslave_p3_odt[0] & sdram_TMRslave_p3_odt[1]) | (sdram_TMRslave_p3_odt[1] & sdram_TMRslave_p3_odt[2])) | (sdram_TMRslave_p3_odt[0] & sdram_TMRslave_p3_odt[2]));
assign sdram_slave_p3_odt = sdram_control49;
assign sdram_control50 = (((sdram_TMRslave_p3_reset_n[0] & sdram_TMRslave_p3_reset_n[1]) | (sdram_TMRslave_p3_reset_n[1] & sdram_TMRslave_p3_reset_n[2])) | (sdram_TMRslave_p3_reset_n[0] & sdram_TMRslave_p3_reset_n[2]));
assign sdram_slave_p3_reset_n = sdram_control50;
assign sdram_control51 = (((sdram_TMRslave_p3_act_n[0] & sdram_TMRslave_p3_act_n[1]) | (sdram_TMRslave_p3_act_n[1] & sdram_TMRslave_p3_act_n[2])) | (sdram_TMRslave_p3_act_n[0] & sdram_TMRslave_p3_act_n[2]));
assign sdram_slave_p3_act_n = sdram_control51;
assign sdram_control52 = (((sdram_TMRslave_p3_wrdata[63:0] & sdram_TMRslave_p3_wrdata[127:64]) | (sdram_TMRslave_p3_wrdata[127:64] & sdram_TMRslave_p3_wrdata[191:128])) | (sdram_TMRslave_p3_wrdata[63:0] & sdram_TMRslave_p3_wrdata[191:128]));
assign sdram_slave_p3_wrdata = sdram_control52;
assign sdram_control53 = (((sdram_TMRslave_p3_wrdata_en[0] & sdram_TMRslave_p3_wrdata_en[1]) | (sdram_TMRslave_p3_wrdata_en[1] & sdram_TMRslave_p3_wrdata_en[2])) | (sdram_TMRslave_p3_wrdata_en[0] & sdram_TMRslave_p3_wrdata_en[2]));
assign sdram_slave_p3_wrdata_en = sdram_control53;
assign sdram_control54 = (((sdram_TMRslave_p3_wrdata_mask[7:0] & sdram_TMRslave_p3_wrdata_mask[15:8]) | (sdram_TMRslave_p3_wrdata_mask[15:8] & sdram_TMRslave_p3_wrdata_mask[23:16])) | (sdram_TMRslave_p3_wrdata_mask[7:0] & sdram_TMRslave_p3_wrdata_mask[23:16]));
assign sdram_slave_p3_wrdata_mask = sdram_control54;
assign sdram_control55 = (((sdram_TMRslave_p3_rddata_en[0] & sdram_TMRslave_p3_rddata_en[1]) | (sdram_TMRslave_p3_rddata_en[1] & sdram_TMRslave_p3_rddata_en[2])) | (sdram_TMRslave_p3_rddata_en[0] & sdram_TMRslave_p3_rddata_en[2]));
assign sdram_slave_p3_rddata_en = sdram_control55;
assign sdram_TMRslave_p3_rddata = {3{sdram_slave_p3_rddata}};
assign sdram_TMRslave_p3_rddata_valid = {3{sdram_slave_p3_rddata_valid}};
assign sdram_control56 = (((slice_proxy0[13:0] & slice_proxy1[27:14]) | (slice_proxy2[27:14] & slice_proxy3[41:28])) | (slice_proxy4[13:0] & slice_proxy5[41:28]));
assign sdram_inti_inti_p0_address = sdram_control56;
assign sdram_control57 = (((slice_proxy6[2:0] & slice_proxy7[5:3]) | (slice_proxy8[5:3] & slice_proxy9[8:6])) | (slice_proxy10[2:0] & slice_proxy11[8:6]));
assign sdram_inti_inti_p0_bank = sdram_control57;
assign sdram_control58 = (((slice_proxy12[0] & slice_proxy13[1]) | (slice_proxy14[1] & slice_proxy15[2])) | (slice_proxy16[0] & slice_proxy17[2]));
assign sdram_inti_inti_p0_cas_n = sdram_control58;
assign sdram_control59 = (((slice_proxy18[0] & slice_proxy19[1]) | (slice_proxy20[1] & slice_proxy21[2])) | (slice_proxy22[0] & slice_proxy23[2]));
assign sdram_inti_inti_p0_cs_n = sdram_control59;
assign sdram_control60 = (((slice_proxy24[0] & slice_proxy25[1]) | (slice_proxy26[1] & slice_proxy27[2])) | (slice_proxy28[0] & slice_proxy29[2]));
assign sdram_inti_inti_p0_ras_n = sdram_control60;
assign sdram_control61 = (((slice_proxy30[0] & slice_proxy31[1]) | (slice_proxy32[1] & slice_proxy33[2])) | (slice_proxy34[0] & slice_proxy35[2]));
assign sdram_inti_inti_p0_we_n = sdram_control61;
assign sdram_control62 = (((slice_proxy36[0] & slice_proxy37[1]) | (slice_proxy38[1] & slice_proxy39[2])) | (slice_proxy40[0] & slice_proxy41[2]));
assign sdram_inti_inti_p0_cke = sdram_control62;
assign sdram_control63 = (((slice_proxy42[0] & slice_proxy43[1]) | (slice_proxy44[1] & slice_proxy45[2])) | (slice_proxy46[0] & slice_proxy47[2]));
assign sdram_inti_inti_p0_odt = sdram_control63;
assign sdram_control64 = (((slice_proxy48[0] & slice_proxy49[1]) | (slice_proxy50[1] & slice_proxy51[2])) | (slice_proxy52[0] & slice_proxy53[2]));
assign sdram_inti_inti_p0_reset_n = sdram_control64;
assign sdram_control65 = (((slice_proxy54[0] & slice_proxy55[1]) | (slice_proxy56[1] & slice_proxy57[2])) | (slice_proxy58[0] & slice_proxy59[2]));
assign sdram_inti_inti_p0_act_n = sdram_control65;
assign sdram_control66 = (((slice_proxy60[63:0] & slice_proxy61[127:64]) | (slice_proxy62[127:64] & slice_proxy63[191:128])) | (slice_proxy64[63:0] & slice_proxy65[191:128]));
assign sdram_inti_inti_p0_wrdata = sdram_control66;
assign sdram_control67 = (((slice_proxy66[0] & slice_proxy67[1]) | (slice_proxy68[1] & slice_proxy69[2])) | (slice_proxy70[0] & slice_proxy71[2]));
assign sdram_inti_inti_p0_wrdata_en = sdram_control67;
assign sdram_control68 = (((slice_proxy72[7:0] & slice_proxy73[15:8]) | (slice_proxy74[15:8] & slice_proxy75[23:16])) | (slice_proxy76[7:0] & slice_proxy77[23:16]));
assign sdram_inti_inti_p0_wrdata_mask = sdram_control68;
assign sdram_control69 = (((slice_proxy78[0] & slice_proxy79[1]) | (slice_proxy80[1] & slice_proxy81[2])) | (slice_proxy82[0] & slice_proxy83[2]));
assign sdram_inti_inti_p0_rddata_en = sdram_control69;
assign sdram_control70 = (((slice_proxy84[13:0] & slice_proxy85[27:14]) | (slice_proxy86[27:14] & slice_proxy87[41:28])) | (slice_proxy88[13:0] & slice_proxy89[41:28]));
assign sdram_inti_inti_p1_address = sdram_control70;
assign sdram_control71 = (((slice_proxy90[2:0] & slice_proxy91[5:3]) | (slice_proxy92[5:3] & slice_proxy93[8:6])) | (slice_proxy94[2:0] & slice_proxy95[8:6]));
assign sdram_inti_inti_p1_bank = sdram_control71;
assign sdram_control72 = (((slice_proxy96[0] & slice_proxy97[1]) | (slice_proxy98[1] & slice_proxy99[2])) | (slice_proxy100[0] & slice_proxy101[2]));
assign sdram_inti_inti_p1_cas_n = sdram_control72;
assign sdram_control73 = (((slice_proxy102[0] & slice_proxy103[1]) | (slice_proxy104[1] & slice_proxy105[2])) | (slice_proxy106[0] & slice_proxy107[2]));
assign sdram_inti_inti_p1_cs_n = sdram_control73;
assign sdram_control74 = (((slice_proxy108[0] & slice_proxy109[1]) | (slice_proxy110[1] & slice_proxy111[2])) | (slice_proxy112[0] & slice_proxy113[2]));
assign sdram_inti_inti_p1_ras_n = sdram_control74;
assign sdram_control75 = (((slice_proxy114[0] & slice_proxy115[1]) | (slice_proxy116[1] & slice_proxy117[2])) | (slice_proxy118[0] & slice_proxy119[2]));
assign sdram_inti_inti_p1_we_n = sdram_control75;
assign sdram_control76 = (((slice_proxy120[0] & slice_proxy121[1]) | (slice_proxy122[1] & slice_proxy123[2])) | (slice_proxy124[0] & slice_proxy125[2]));
assign sdram_inti_inti_p1_cke = sdram_control76;
assign sdram_control77 = (((slice_proxy126[0] & slice_proxy127[1]) | (slice_proxy128[1] & slice_proxy129[2])) | (slice_proxy130[0] & slice_proxy131[2]));
assign sdram_inti_inti_p1_odt = sdram_control77;
assign sdram_control78 = (((slice_proxy132[0] & slice_proxy133[1]) | (slice_proxy134[1] & slice_proxy135[2])) | (slice_proxy136[0] & slice_proxy137[2]));
assign sdram_inti_inti_p1_reset_n = sdram_control78;
assign sdram_control79 = (((slice_proxy138[0] & slice_proxy139[1]) | (slice_proxy140[1] & slice_proxy141[2])) | (slice_proxy142[0] & slice_proxy143[2]));
assign sdram_inti_inti_p1_act_n = sdram_control79;
assign sdram_control80 = (((slice_proxy144[63:0] & slice_proxy145[127:64]) | (slice_proxy146[127:64] & slice_proxy147[191:128])) | (slice_proxy148[63:0] & slice_proxy149[191:128]));
assign sdram_inti_inti_p1_wrdata = sdram_control80;
assign sdram_control81 = (((slice_proxy150[0] & slice_proxy151[1]) | (slice_proxy152[1] & slice_proxy153[2])) | (slice_proxy154[0] & slice_proxy155[2]));
assign sdram_inti_inti_p1_wrdata_en = sdram_control81;
assign sdram_control82 = (((slice_proxy156[7:0] & slice_proxy157[15:8]) | (slice_proxy158[15:8] & slice_proxy159[23:16])) | (slice_proxy160[7:0] & slice_proxy161[23:16]));
assign sdram_inti_inti_p1_wrdata_mask = sdram_control82;
assign sdram_control83 = (((slice_proxy162[0] & slice_proxy163[1]) | (slice_proxy164[1] & slice_proxy165[2])) | (slice_proxy166[0] & slice_proxy167[2]));
assign sdram_inti_inti_p1_rddata_en = sdram_control83;
assign sdram_control84 = (((slice_proxy168[13:0] & slice_proxy169[27:14]) | (slice_proxy170[27:14] & slice_proxy171[41:28])) | (slice_proxy172[13:0] & slice_proxy173[41:28]));
assign sdram_inti_inti_p2_address = sdram_control84;
assign sdram_control85 = (((slice_proxy174[2:0] & slice_proxy175[5:3]) | (slice_proxy176[5:3] & slice_proxy177[8:6])) | (slice_proxy178[2:0] & slice_proxy179[8:6]));
assign sdram_inti_inti_p2_bank = sdram_control85;
assign sdram_control86 = (((slice_proxy180[0] & slice_proxy181[1]) | (slice_proxy182[1] & slice_proxy183[2])) | (slice_proxy184[0] & slice_proxy185[2]));
assign sdram_inti_inti_p2_cas_n = sdram_control86;
assign sdram_control87 = (((slice_proxy186[0] & slice_proxy187[1]) | (slice_proxy188[1] & slice_proxy189[2])) | (slice_proxy190[0] & slice_proxy191[2]));
assign sdram_inti_inti_p2_cs_n = sdram_control87;
assign sdram_control88 = (((slice_proxy192[0] & slice_proxy193[1]) | (slice_proxy194[1] & slice_proxy195[2])) | (slice_proxy196[0] & slice_proxy197[2]));
assign sdram_inti_inti_p2_ras_n = sdram_control88;
assign sdram_control89 = (((slice_proxy198[0] & slice_proxy199[1]) | (slice_proxy200[1] & slice_proxy201[2])) | (slice_proxy202[0] & slice_proxy203[2]));
assign sdram_inti_inti_p2_we_n = sdram_control89;
assign sdram_control90 = (((slice_proxy204[0] & slice_proxy205[1]) | (slice_proxy206[1] & slice_proxy207[2])) | (slice_proxy208[0] & slice_proxy209[2]));
assign sdram_inti_inti_p2_cke = sdram_control90;
assign sdram_control91 = (((slice_proxy210[0] & slice_proxy211[1]) | (slice_proxy212[1] & slice_proxy213[2])) | (slice_proxy214[0] & slice_proxy215[2]));
assign sdram_inti_inti_p2_odt = sdram_control91;
assign sdram_control92 = (((slice_proxy216[0] & slice_proxy217[1]) | (slice_proxy218[1] & slice_proxy219[2])) | (slice_proxy220[0] & slice_proxy221[2]));
assign sdram_inti_inti_p2_reset_n = sdram_control92;
assign sdram_control93 = (((slice_proxy222[0] & slice_proxy223[1]) | (slice_proxy224[1] & slice_proxy225[2])) | (slice_proxy226[0] & slice_proxy227[2]));
assign sdram_inti_inti_p2_act_n = sdram_control93;
assign sdram_control94 = (((slice_proxy228[63:0] & slice_proxy229[127:64]) | (slice_proxy230[127:64] & slice_proxy231[191:128])) | (slice_proxy232[63:0] & slice_proxy233[191:128]));
assign sdram_inti_inti_p2_wrdata = sdram_control94;
assign sdram_control95 = (((slice_proxy234[0] & slice_proxy235[1]) | (slice_proxy236[1] & slice_proxy237[2])) | (slice_proxy238[0] & slice_proxy239[2]));
assign sdram_inti_inti_p2_wrdata_en = sdram_control95;
assign sdram_control96 = (((slice_proxy240[7:0] & slice_proxy241[15:8]) | (slice_proxy242[15:8] & slice_proxy243[23:16])) | (slice_proxy244[7:0] & slice_proxy245[23:16]));
assign sdram_inti_inti_p2_wrdata_mask = sdram_control96;
assign sdram_control97 = (((slice_proxy246[0] & slice_proxy247[1]) | (slice_proxy248[1] & slice_proxy249[2])) | (slice_proxy250[0] & slice_proxy251[2]));
assign sdram_inti_inti_p2_rddata_en = sdram_control97;
assign sdram_control98 = (((slice_proxy252[13:0] & slice_proxy253[27:14]) | (slice_proxy254[27:14] & slice_proxy255[41:28])) | (slice_proxy256[13:0] & slice_proxy257[41:28]));
assign sdram_inti_inti_p3_address = sdram_control98;
assign sdram_control99 = (((slice_proxy258[2:0] & slice_proxy259[5:3]) | (slice_proxy260[5:3] & slice_proxy261[8:6])) | (slice_proxy262[2:0] & slice_proxy263[8:6]));
assign sdram_inti_inti_p3_bank = sdram_control99;
assign sdram_control100 = (((slice_proxy264[0] & slice_proxy265[1]) | (slice_proxy266[1] & slice_proxy267[2])) | (slice_proxy268[0] & slice_proxy269[2]));
assign sdram_inti_inti_p3_cas_n = sdram_control100;
assign sdram_control101 = (((slice_proxy270[0] & slice_proxy271[1]) | (slice_proxy272[1] & slice_proxy273[2])) | (slice_proxy274[0] & slice_proxy275[2]));
assign sdram_inti_inti_p3_cs_n = sdram_control101;
assign sdram_control102 = (((slice_proxy276[0] & slice_proxy277[1]) | (slice_proxy278[1] & slice_proxy279[2])) | (slice_proxy280[0] & slice_proxy281[2]));
assign sdram_inti_inti_p3_ras_n = sdram_control102;
assign sdram_control103 = (((slice_proxy282[0] & slice_proxy283[1]) | (slice_proxy284[1] & slice_proxy285[2])) | (slice_proxy286[0] & slice_proxy287[2]));
assign sdram_inti_inti_p3_we_n = sdram_control103;
assign sdram_control104 = (((slice_proxy288[0] & slice_proxy289[1]) | (slice_proxy290[1] & slice_proxy291[2])) | (slice_proxy292[0] & slice_proxy293[2]));
assign sdram_inti_inti_p3_cke = sdram_control104;
assign sdram_control105 = (((slice_proxy294[0] & slice_proxy295[1]) | (slice_proxy296[1] & slice_proxy297[2])) | (slice_proxy298[0] & slice_proxy299[2]));
assign sdram_inti_inti_p3_odt = sdram_control105;
assign sdram_control106 = (((slice_proxy300[0] & slice_proxy301[1]) | (slice_proxy302[1] & slice_proxy303[2])) | (slice_proxy304[0] & slice_proxy305[2]));
assign sdram_inti_inti_p3_reset_n = sdram_control106;
assign sdram_control107 = (((slice_proxy306[0] & slice_proxy307[1]) | (slice_proxy308[1] & slice_proxy309[2])) | (slice_proxy310[0] & slice_proxy311[2]));
assign sdram_inti_inti_p3_act_n = sdram_control107;
assign sdram_control108 = (((slice_proxy312[63:0] & slice_proxy313[127:64]) | (slice_proxy314[127:64] & slice_proxy315[191:128])) | (slice_proxy316[63:0] & slice_proxy317[191:128]));
assign sdram_inti_inti_p3_wrdata = sdram_control108;
assign sdram_control109 = (((slice_proxy318[0] & slice_proxy319[1]) | (slice_proxy320[1] & slice_proxy321[2])) | (slice_proxy322[0] & slice_proxy323[2]));
assign sdram_inti_inti_p3_wrdata_en = sdram_control109;
assign sdram_control110 = (((slice_proxy324[7:0] & slice_proxy325[15:8]) | (slice_proxy326[15:8] & slice_proxy327[23:16])) | (slice_proxy328[7:0] & slice_proxy329[23:16]));
assign sdram_inti_inti_p3_wrdata_mask = sdram_control110;
assign sdram_control111 = (((slice_proxy330[0] & slice_proxy331[1]) | (slice_proxy332[1] & slice_proxy333[2])) | (slice_proxy334[0] & slice_proxy335[2]));
assign sdram_inti_inti_p3_rddata_en = sdram_control111;
assign sdram_tmrbankmachine0_TMRreq_valid = sdram_TMRinterface_bank0_valid;
assign sdram_TMRinterface_bank0_ready = sdram_tmrbankmachine0_TMRreq_ready;
assign sdram_tmrbankmachine0_TMRreq_we = sdram_TMRinterface_bank0_we;
assign sdram_tmrbankmachine0_TMRreq_addr = sdram_TMRinterface_bank0_addr;
assign sdram_TMRinterface_bank0_lock = sdram_tmrbankmachine0_TMRreq_lock;
assign sdram_TMRinterface_bank0_wdata_ready = sdram_tmrbankmachine0_TMRreq_wdata_ready;
assign sdram_TMRinterface_bank0_rdata_valid = sdram_tmrbankmachine0_TMRreq_rdata_valid;
assign sdram_tmrbankmachine1_TMRreq_valid = sdram_TMRinterface_bank1_valid;
assign sdram_TMRinterface_bank1_ready = sdram_tmrbankmachine1_TMRreq_ready;
assign sdram_tmrbankmachine1_TMRreq_we = sdram_TMRinterface_bank1_we;
assign sdram_tmrbankmachine1_TMRreq_addr = sdram_TMRinterface_bank1_addr;
assign sdram_TMRinterface_bank1_lock = sdram_tmrbankmachine1_TMRreq_lock;
assign sdram_TMRinterface_bank1_wdata_ready = sdram_tmrbankmachine1_TMRreq_wdata_ready;
assign sdram_TMRinterface_bank1_rdata_valid = sdram_tmrbankmachine1_TMRreq_rdata_valid;
assign sdram_tmrbankmachine2_TMRreq_valid = sdram_TMRinterface_bank2_valid;
assign sdram_TMRinterface_bank2_ready = sdram_tmrbankmachine2_TMRreq_ready;
assign sdram_tmrbankmachine2_TMRreq_we = sdram_TMRinterface_bank2_we;
assign sdram_tmrbankmachine2_TMRreq_addr = sdram_TMRinterface_bank2_addr;
assign sdram_TMRinterface_bank2_lock = sdram_tmrbankmachine2_TMRreq_lock;
assign sdram_TMRinterface_bank2_wdata_ready = sdram_tmrbankmachine2_TMRreq_wdata_ready;
assign sdram_TMRinterface_bank2_rdata_valid = sdram_tmrbankmachine2_TMRreq_rdata_valid;
assign sdram_tmrbankmachine3_TMRreq_valid = sdram_TMRinterface_bank3_valid;
assign sdram_TMRinterface_bank3_ready = sdram_tmrbankmachine3_TMRreq_ready;
assign sdram_tmrbankmachine3_TMRreq_we = sdram_TMRinterface_bank3_we;
assign sdram_tmrbankmachine3_TMRreq_addr = sdram_TMRinterface_bank3_addr;
assign sdram_TMRinterface_bank3_lock = sdram_tmrbankmachine3_TMRreq_lock;
assign sdram_TMRinterface_bank3_wdata_ready = sdram_tmrbankmachine3_TMRreq_wdata_ready;
assign sdram_TMRinterface_bank3_rdata_valid = sdram_tmrbankmachine3_TMRreq_rdata_valid;
assign sdram_tmrbankmachine4_TMRreq_valid = sdram_TMRinterface_bank4_valid;
assign sdram_TMRinterface_bank4_ready = sdram_tmrbankmachine4_TMRreq_ready;
assign sdram_tmrbankmachine4_TMRreq_we = sdram_TMRinterface_bank4_we;
assign sdram_tmrbankmachine4_TMRreq_addr = sdram_TMRinterface_bank4_addr;
assign sdram_TMRinterface_bank4_lock = sdram_tmrbankmachine4_TMRreq_lock;
assign sdram_TMRinterface_bank4_wdata_ready = sdram_tmrbankmachine4_TMRreq_wdata_ready;
assign sdram_TMRinterface_bank4_rdata_valid = sdram_tmrbankmachine4_TMRreq_rdata_valid;
assign sdram_tmrbankmachine5_TMRreq_valid = sdram_TMRinterface_bank5_valid;
assign sdram_TMRinterface_bank5_ready = sdram_tmrbankmachine5_TMRreq_ready;
assign sdram_tmrbankmachine5_TMRreq_we = sdram_TMRinterface_bank5_we;
assign sdram_tmrbankmachine5_TMRreq_addr = sdram_TMRinterface_bank5_addr;
assign sdram_TMRinterface_bank5_lock = sdram_tmrbankmachine5_TMRreq_lock;
assign sdram_TMRinterface_bank5_wdata_ready = sdram_tmrbankmachine5_TMRreq_wdata_ready;
assign sdram_TMRinterface_bank5_rdata_valid = sdram_tmrbankmachine5_TMRreq_rdata_valid;
assign sdram_tmrbankmachine6_TMRreq_valid = sdram_TMRinterface_bank6_valid;
assign sdram_TMRinterface_bank6_ready = sdram_tmrbankmachine6_TMRreq_ready;
assign sdram_tmrbankmachine6_TMRreq_we = sdram_TMRinterface_bank6_we;
assign sdram_tmrbankmachine6_TMRreq_addr = sdram_TMRinterface_bank6_addr;
assign sdram_TMRinterface_bank6_lock = sdram_tmrbankmachine6_TMRreq_lock;
assign sdram_TMRinterface_bank6_wdata_ready = sdram_tmrbankmachine6_TMRreq_wdata_ready;
assign sdram_TMRinterface_bank6_rdata_valid = sdram_tmrbankmachine6_TMRreq_rdata_valid;
assign sdram_tmrbankmachine7_TMRreq_valid = sdram_TMRinterface_bank7_valid;
assign sdram_TMRinterface_bank7_ready = sdram_tmrbankmachine7_TMRreq_ready;
assign sdram_tmrbankmachine7_TMRreq_we = sdram_TMRinterface_bank7_we;
assign sdram_tmrbankmachine7_TMRreq_addr = sdram_TMRinterface_bank7_addr;
assign sdram_TMRinterface_bank7_lock = sdram_tmrbankmachine7_TMRreq_lock;
assign sdram_TMRinterface_bank7_wdata_ready = sdram_tmrbankmachine7_TMRreq_wdata_ready;
assign sdram_TMRinterface_bank7_rdata_valid = sdram_tmrbankmachine7_TMRreq_rdata_valid;
assign sdram_TMRdfi_p0_address = {3{sdram_dfi_p0_address}};
assign sdram_TMRdfi_p0_bank = {3{sdram_dfi_p0_bank}};
assign sdram_TMRdfi_p0_cas_n = {3{sdram_dfi_p0_cas_n}};
assign sdram_TMRdfi_p0_cs_n = {3{sdram_dfi_p0_cs_n}};
assign sdram_TMRdfi_p0_ras_n = {3{sdram_dfi_p0_ras_n}};
assign sdram_TMRdfi_p0_we_n = {3{sdram_dfi_p0_we_n}};
assign sdram_TMRdfi_p0_cke = {3{sdram_dfi_p0_cke}};
assign sdram_TMRdfi_p0_odt = {3{sdram_dfi_p0_odt}};
assign sdram_TMRdfi_p0_reset_n = {3{sdram_dfi_p0_reset_n}};
assign sdram_TMRdfi_p0_act_n = {3{sdram_dfi_p0_act_n}};
assign sdram_TMRdfi_p0_wrdata = {3{sdram_dfi_p0_wrdata}};
assign sdram_TMRdfi_p0_wrdata_en = {3{sdram_dfi_p0_wrdata_en}};
assign sdram_TMRdfi_p0_wrdata_mask = {3{sdram_dfi_p0_wrdata_mask}};
assign sdram_TMRdfi_p0_rddata_en = {3{sdram_dfi_p0_rddata_en}};
assign sdram_tmrinput_control0 = (((sdram_TMRdfi_p0_rddata[63:0] & sdram_TMRdfi_p0_rddata[127:64]) | (sdram_TMRdfi_p0_rddata[127:64] & sdram_TMRdfi_p0_rddata[191:128])) | (sdram_TMRdfi_p0_rddata[63:0] & sdram_TMRdfi_p0_rddata[191:128]));
assign sdram_dfi_p0_rddata = sdram_tmrinput_control0;
assign sdram_tmrinput_control1 = (((sdram_TMRdfi_p0_rddata_valid[0] & sdram_TMRdfi_p0_rddata_valid[1]) | (sdram_TMRdfi_p0_rddata_valid[1] & sdram_TMRdfi_p0_rddata_valid[2])) | (sdram_TMRdfi_p0_rddata_valid[0] & sdram_TMRdfi_p0_rddata_valid[2]));
assign sdram_dfi_p0_rddata_valid = sdram_tmrinput_control1;
assign sdram_TMRdfi_p1_address = {3{sdram_dfi_p1_address}};
assign sdram_TMRdfi_p1_bank = {3{sdram_dfi_p1_bank}};
assign sdram_TMRdfi_p1_cas_n = {3{sdram_dfi_p1_cas_n}};
assign sdram_TMRdfi_p1_cs_n = {3{sdram_dfi_p1_cs_n}};
assign sdram_TMRdfi_p1_ras_n = {3{sdram_dfi_p1_ras_n}};
assign sdram_TMRdfi_p1_we_n = {3{sdram_dfi_p1_we_n}};
assign sdram_TMRdfi_p1_cke = {3{sdram_dfi_p1_cke}};
assign sdram_TMRdfi_p1_odt = {3{sdram_dfi_p1_odt}};
assign sdram_TMRdfi_p1_reset_n = {3{sdram_dfi_p1_reset_n}};
assign sdram_TMRdfi_p1_act_n = {3{sdram_dfi_p1_act_n}};
assign sdram_TMRdfi_p1_wrdata = {3{sdram_dfi_p1_wrdata}};
assign sdram_TMRdfi_p1_wrdata_en = {3{sdram_dfi_p1_wrdata_en}};
assign sdram_TMRdfi_p1_wrdata_mask = {3{sdram_dfi_p1_wrdata_mask}};
assign sdram_TMRdfi_p1_rddata_en = {3{sdram_dfi_p1_rddata_en}};
assign sdram_tmrinput_control2 = (((sdram_TMRdfi_p1_rddata[63:0] & sdram_TMRdfi_p1_rddata[127:64]) | (sdram_TMRdfi_p1_rddata[127:64] & sdram_TMRdfi_p1_rddata[191:128])) | (sdram_TMRdfi_p1_rddata[63:0] & sdram_TMRdfi_p1_rddata[191:128]));
assign sdram_dfi_p1_rddata = sdram_tmrinput_control2;
assign sdram_tmrinput_control3 = (((sdram_TMRdfi_p1_rddata_valid[0] & sdram_TMRdfi_p1_rddata_valid[1]) | (sdram_TMRdfi_p1_rddata_valid[1] & sdram_TMRdfi_p1_rddata_valid[2])) | (sdram_TMRdfi_p1_rddata_valid[0] & sdram_TMRdfi_p1_rddata_valid[2]));
assign sdram_dfi_p1_rddata_valid = sdram_tmrinput_control3;
assign sdram_TMRdfi_p2_address = {3{sdram_dfi_p2_address}};
assign sdram_TMRdfi_p2_bank = {3{sdram_dfi_p2_bank}};
assign sdram_TMRdfi_p2_cas_n = {3{sdram_dfi_p2_cas_n}};
assign sdram_TMRdfi_p2_cs_n = {3{sdram_dfi_p2_cs_n}};
assign sdram_TMRdfi_p2_ras_n = {3{sdram_dfi_p2_ras_n}};
assign sdram_TMRdfi_p2_we_n = {3{sdram_dfi_p2_we_n}};
assign sdram_TMRdfi_p2_cke = {3{sdram_dfi_p2_cke}};
assign sdram_TMRdfi_p2_odt = {3{sdram_dfi_p2_odt}};
assign sdram_TMRdfi_p2_reset_n = {3{sdram_dfi_p2_reset_n}};
assign sdram_TMRdfi_p2_act_n = {3{sdram_dfi_p2_act_n}};
assign sdram_TMRdfi_p2_wrdata = {3{sdram_dfi_p2_wrdata}};
assign sdram_TMRdfi_p2_wrdata_en = {3{sdram_dfi_p2_wrdata_en}};
assign sdram_TMRdfi_p2_wrdata_mask = {3{sdram_dfi_p2_wrdata_mask}};
assign sdram_TMRdfi_p2_rddata_en = {3{sdram_dfi_p2_rddata_en}};
assign sdram_tmrinput_control4 = (((sdram_TMRdfi_p2_rddata[63:0] & sdram_TMRdfi_p2_rddata[127:64]) | (sdram_TMRdfi_p2_rddata[127:64] & sdram_TMRdfi_p2_rddata[191:128])) | (sdram_TMRdfi_p2_rddata[63:0] & sdram_TMRdfi_p2_rddata[191:128]));
assign sdram_dfi_p2_rddata = sdram_tmrinput_control4;
assign sdram_tmrinput_control5 = (((sdram_TMRdfi_p2_rddata_valid[0] & sdram_TMRdfi_p2_rddata_valid[1]) | (sdram_TMRdfi_p2_rddata_valid[1] & sdram_TMRdfi_p2_rddata_valid[2])) | (sdram_TMRdfi_p2_rddata_valid[0] & sdram_TMRdfi_p2_rddata_valid[2]));
assign sdram_dfi_p2_rddata_valid = sdram_tmrinput_control5;
assign sdram_TMRdfi_p3_address = {3{sdram_dfi_p3_address}};
assign sdram_TMRdfi_p3_bank = {3{sdram_dfi_p3_bank}};
assign sdram_TMRdfi_p3_cas_n = {3{sdram_dfi_p3_cas_n}};
assign sdram_TMRdfi_p3_cs_n = {3{sdram_dfi_p3_cs_n}};
assign sdram_TMRdfi_p3_ras_n = {3{sdram_dfi_p3_ras_n}};
assign sdram_TMRdfi_p3_we_n = {3{sdram_dfi_p3_we_n}};
assign sdram_TMRdfi_p3_cke = {3{sdram_dfi_p3_cke}};
assign sdram_TMRdfi_p3_odt = {3{sdram_dfi_p3_odt}};
assign sdram_TMRdfi_p3_reset_n = {3{sdram_dfi_p3_reset_n}};
assign sdram_TMRdfi_p3_act_n = {3{sdram_dfi_p3_act_n}};
assign sdram_TMRdfi_p3_wrdata = {3{sdram_dfi_p3_wrdata}};
assign sdram_TMRdfi_p3_wrdata_en = {3{sdram_dfi_p3_wrdata_en}};
assign sdram_TMRdfi_p3_wrdata_mask = {3{sdram_dfi_p3_wrdata_mask}};
assign sdram_TMRdfi_p3_rddata_en = {3{sdram_dfi_p3_rddata_en}};
assign sdram_tmrinput_control6 = (((sdram_TMRdfi_p3_rddata[63:0] & sdram_TMRdfi_p3_rddata[127:64]) | (sdram_TMRdfi_p3_rddata[127:64] & sdram_TMRdfi_p3_rddata[191:128])) | (sdram_TMRdfi_p3_rddata[63:0] & sdram_TMRdfi_p3_rddata[191:128]));
assign sdram_dfi_p3_rddata = sdram_tmrinput_control6;
assign sdram_tmrinput_control7 = (((sdram_TMRdfi_p3_rddata_valid[0] & sdram_TMRdfi_p3_rddata_valid[1]) | (sdram_TMRdfi_p3_rddata_valid[1] & sdram_TMRdfi_p3_rddata_valid[2])) | (sdram_TMRdfi_p3_rddata_valid[0] & sdram_TMRdfi_p3_rddata_valid[2]));
assign sdram_dfi_p3_rddata_valid = sdram_tmrinput_control7;
assign sdram_timer_wait = (~sdram_timer_done0);
assign sdram_timer2_wait = (~sdram_timer2_done0);
assign sdram_timer3_wait = (~sdram_timer3_done0);
assign sdram_postponer_req_i = sdram_timerVote_control;
assign sdram_postponer2_req_i = sdram_timerVote_control;
assign sdram_postponer3_req_i = sdram_timerVote_control;
assign sdram_wants_refresh = sdram_postponeVote_control;
assign sdram_wants_zqcs = sdram_zqcs_timer_done0;
assign sdram_zqcs_timer_wait = (~sdram_zqcs_executer_done);
assign sdram_TMRcmd_valid = {3{sdram_cmd_valid}};
assign sdram_TMRcmd_last = {3{sdram_cmd_last}};
assign sdram_TMRcmd_first = {3{sdram_cmd_first}};
assign sdram_tmrinput_control8 = (((sdram_TMRcmd_ready[0] & sdram_TMRcmd_ready[1]) | (sdram_TMRcmd_ready[1] & sdram_TMRcmd_ready[2])) | (sdram_TMRcmd_ready[0] & sdram_TMRcmd_ready[2]));
assign sdram_cmd_ready = sdram_tmrinput_control8;
assign sdram_TMRcmd_payload_a = {3{sdram_cmd_payload_a}};
assign sdram_TMRcmd_payload_ba = {3{sdram_cmd_payload_ba}};
assign sdram_TMRcmd_payload_cas = {3{sdram_cmd_payload_cas}};
assign sdram_TMRcmd_payload_ras = {3{sdram_cmd_payload_ras}};
assign sdram_TMRcmd_payload_we = {3{sdram_cmd_payload_we}};
assign sdram_TMRcmd_payload_is_cmd = {3{sdram_cmd_payload_is_cmd}};
assign sdram_TMRcmd_payload_is_read = {3{sdram_cmd_payload_is_read}};
assign sdram_TMRcmd_payload_is_write = {3{sdram_cmd_payload_is_write}};
assign sdram_timer_done1 = (sdram_timer_count1 == 1'd0);
assign sdram_timer_done0 = sdram_timer_done1;
assign sdram_timer_count0 = sdram_timer_count1;
assign sdram_timer2_done1 = (sdram_timer2_count1 == 1'd0);
assign sdram_timer2_done0 = sdram_timer2_done1;
assign sdram_timer2_count0 = sdram_timer2_count1;
assign sdram_timer3_done1 = (sdram_timer3_count1 == 1'd0);
assign sdram_timer3_done0 = sdram_timer3_done1;
assign sdram_timer3_count0 = sdram_timer3_count1;
assign sdram_timerVote_control = (((slice_proxy336[0] & slice_proxy337[1]) | (slice_proxy338[1] & slice_proxy339[2])) | (slice_proxy340[0] & slice_proxy341[2]));
assign sdram_postponeVote_control = (((slice_proxy342[0] & slice_proxy343[1]) | (slice_proxy344[1] & slice_proxy345[2])) | (slice_proxy346[0] & slice_proxy347[2]));
assign sdram_sequencer_start1 = (sdram_sequencer_start0 | (sdram_sequencer_count != 1'd0));
assign sdram_sequencer_done0 = (sdram_sequencer_done1 & (sdram_sequencer_count == 1'd0));
assign sdram_sequencer2_start1 = (sdram_sequencer2_start0 | (sdram_sequencer2_count != 1'd0));
assign sdram_sequencer2_done0 = (sdram_sequencer2_done1 & (sdram_sequencer2_count == 1'd0));
assign sdram_sequencer3_start1 = (sdram_sequencer3_start0 | (sdram_sequencer3_count != 1'd0));
assign sdram_sequencer3_done0 = (sdram_sequencer3_done1 & (sdram_sequencer3_count == 1'd0));
assign sdram_sequenceVote_control = (((slice_proxy348[0] & slice_proxy349[1]) | (slice_proxy350[1] & slice_proxy351[2])) | (slice_proxy352[0] & slice_proxy353[2]));
assign sdram_zqcs_timer_done1 = (sdram_zqcs_timer_count1 == 1'd0);
assign sdram_zqcs_timer_done0 = sdram_zqcs_timer_done1;
assign sdram_zqcs_timer_count0 = sdram_zqcs_timer_count1;

// synthesis translate_off
reg dummy_d_37;
// synthesis translate_on
always @(*) begin
	sdram_cmd_valid <= 1'd0;
	sdram_cmd_last <= 1'd0;
	sdram_sequencer_start0 <= 1'd0;
	sdram_sequencer2_start0 <= 1'd0;
	sdram_sequencer3_start0 <= 1'd0;
	sdram_zqcs_executer_start <= 1'd0;
	tmrrefresher_next_state <= 2'd0;
	tmrrefresher_next_state <= tmrrefresher_state;
	case (tmrrefresher_state)
		1'd1: begin
			sdram_cmd_valid <= 1'd1;
			if (sdram_cmd_ready) begin
				sdram_sequencer_start0 <= 1'd1;
				sdram_sequencer2_start0 <= 1'd1;
				sdram_sequencer3_start0 <= 1'd1;
				tmrrefresher_next_state <= 2'd2;
			end
		end
		2'd2: begin
			sdram_cmd_valid <= 1'd1;
			if (sdram_sequenceVote_control) begin
				if (sdram_wants_zqcs) begin
					sdram_zqcs_executer_start <= 1'd1;
					tmrrefresher_next_state <= 2'd3;
				end else begin
					sdram_cmd_valid <= 1'd0;
					sdram_cmd_last <= 1'd1;
					tmrrefresher_next_state <= 1'd0;
				end
			end
		end
		2'd3: begin
			sdram_cmd_valid <= 1'd1;
			if (sdram_zqcs_executer_done) begin
				sdram_cmd_valid <= 1'd0;
				sdram_cmd_last <= 1'd1;
				tmrrefresher_next_state <= 1'd0;
			end
		end
		default: begin
			if (1'd1) begin
				if (sdram_wants_refresh) begin
					tmrrefresher_next_state <= 1'd1;
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_37 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_valid = sdram_tmrbankmachine0_req_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_payload_we = sdram_tmrbankmachine0_req_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_payload_addr = sdram_tmrbankmachine0_req_addr;
assign sdram_tmrbankmachine0_cmd_buffer_sink_valid = sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_source_ready = sdram_tmrbankmachine0_cmd_buffer_sink_ready;
assign sdram_tmrbankmachine0_cmd_buffer_sink_first = sdram_tmrbankmachine0_cmd_buffer_lookahead_source_first;
assign sdram_tmrbankmachine0_cmd_buffer_sink_last = sdram_tmrbankmachine0_cmd_buffer_lookahead_source_last;
assign sdram_tmrbankmachine0_cmd_buffer_sink_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer_sink_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer_source_ready = (sdram_tmrbankmachine0_req_wdata_ready | sdram_tmrbankmachine0_req_rdata_valid);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_valid = sdram_tmrbankmachine0_req_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_payload_we = sdram_tmrbankmachine0_req_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_payload_addr = sdram_tmrbankmachine0_req_addr;
assign sdram_tmrbankmachine0_cmd_buffer2_sink_valid = sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_ready = sdram_tmrbankmachine0_cmd_buffer2_sink_ready;
assign sdram_tmrbankmachine0_cmd_buffer2_sink_first = sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_first;
assign sdram_tmrbankmachine0_cmd_buffer2_sink_last = sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_last;
assign sdram_tmrbankmachine0_cmd_buffer2_sink_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer2_sink_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer2_source_ready = (sdram_tmrbankmachine0_req_wdata_ready | sdram_tmrbankmachine0_req_rdata_valid);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_valid = sdram_tmrbankmachine0_req_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_payload_we = sdram_tmrbankmachine0_req_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_payload_addr = sdram_tmrbankmachine0_req_addr;
assign sdram_tmrbankmachine0_cmd_buffer3_sink_valid = sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_ready = sdram_tmrbankmachine0_cmd_buffer3_sink_ready;
assign sdram_tmrbankmachine0_cmd_buffer3_sink_first = sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_first;
assign sdram_tmrbankmachine0_cmd_buffer3_sink_last = sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_last;
assign sdram_tmrbankmachine0_cmd_buffer3_sink_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer3_sink_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer3_source_ready = (sdram_tmrbankmachine0_req_wdata_ready | sdram_tmrbankmachine0_req_rdata_valid);
assign sdram_tmrbankmachine0_req_ready = ((sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_ready & sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_ready) & sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_ready);
assign sdram_tmrbankmachine0_row_hit = (sdram_tmrbankmachine0_row == sdram_tmrbankmachine0_cmd_buffer_source_payload_addr[20:7]);
assign sdram_tmrbankmachine0_cmd_payload_ba = 1'd0;

// synthesis translate_off
reg dummy_d_38;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine0_cmd_payload_a <= 14'd0;
	if (sdram_tmrbankmachine0_row_col_n_addr_sel) begin
		sdram_tmrbankmachine0_cmd_payload_a <= sdram_tmrbankmachine0_cmd_buffer_source_payload_addr[20:7];
	end else begin
		sdram_tmrbankmachine0_cmd_payload_a <= ((sdram_tmrbankmachine0_auto_precharge <<< 4'd10) | {sdram_tmrbankmachine0_cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_38 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine0_twtpcon_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_cmd_payload_is_write);
assign sdram_tmrbankmachine0_twtpcon2_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_cmd_payload_is_write);
assign sdram_tmrbankmachine0_twtpcon3_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_cmd_payload_is_write);
assign sdram_tmrbankmachine0_trccon_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_row_open);
assign sdram_tmrbankmachine0_trccon2_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_row_open);
assign sdram_tmrbankmachine0_trccon3_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_row_open);
assign sdram_tmrbankmachine0_trascon_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_row_open);
assign sdram_tmrbankmachine0_trascon2_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_row_open);
assign sdram_tmrbankmachine0_trascon3_valid = ((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_ready) & sdram_tmrbankmachine0_row_open);

// synthesis translate_off
reg dummy_d_39;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine0_auto_precharge <= 1'd0;
	if ((sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid & sdram_tmrbankmachine0_cmd_buffer_source_valid)) begin
		if ((sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr[20:7] != sdram_tmrbankmachine0_cmd_buffer_source_payload_addr[20:7])) begin
			sdram_tmrbankmachine0_auto_precharge <= (sdram_tmrbankmachine0_row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_39 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine0_TMRcmd_valid = {3{sdram_tmrbankmachine0_cmd_valid}};
assign sdram_tmrbankmachine0_TMRcmd_last = {3{sdram_tmrbankmachine0_cmd_last}};
assign sdram_tmrbankmachine0_TMRcmd_first = {3{sdram_tmrbankmachine0_cmd_first}};
assign sdram_tmrbankmachine0_tmrinput_control0 = (((sdram_tmrbankmachine0_TMRcmd_ready[0] & sdram_tmrbankmachine0_TMRcmd_ready[1]) | (sdram_tmrbankmachine0_TMRcmd_ready[1] & sdram_tmrbankmachine0_TMRcmd_ready[2])) | (sdram_tmrbankmachine0_TMRcmd_ready[0] & sdram_tmrbankmachine0_TMRcmd_ready[2]));
assign sdram_tmrbankmachine0_cmd_ready = sdram_tmrbankmachine0_tmrinput_control0;
assign sdram_tmrbankmachine0_TMRcmd_payload_a = {3{sdram_tmrbankmachine0_cmd_payload_a}};
assign sdram_tmrbankmachine0_TMRcmd_payload_ba = {3{sdram_tmrbankmachine0_cmd_payload_ba}};
assign sdram_tmrbankmachine0_TMRcmd_payload_cas = {3{sdram_tmrbankmachine0_cmd_payload_cas}};
assign sdram_tmrbankmachine0_TMRcmd_payload_ras = {3{sdram_tmrbankmachine0_cmd_payload_ras}};
assign sdram_tmrbankmachine0_TMRcmd_payload_we = {3{sdram_tmrbankmachine0_cmd_payload_we}};
assign sdram_tmrbankmachine0_TMRcmd_payload_is_cmd = {3{sdram_tmrbankmachine0_cmd_payload_is_cmd}};
assign sdram_tmrbankmachine0_TMRcmd_payload_is_read = {3{sdram_tmrbankmachine0_cmd_payload_is_read}};
assign sdram_tmrbankmachine0_TMRcmd_payload_is_write = {3{sdram_tmrbankmachine0_cmd_payload_is_write}};
assign sdram_tmrbankmachine0_tmrinput_control1 = (((sdram_tmrbankmachine0_TMRreq_valid[0] & sdram_tmrbankmachine0_TMRreq_valid[1]) | (sdram_tmrbankmachine0_TMRreq_valid[1] & sdram_tmrbankmachine0_TMRreq_valid[2])) | (sdram_tmrbankmachine0_TMRreq_valid[0] & sdram_tmrbankmachine0_TMRreq_valid[2]));
assign sdram_tmrbankmachine0_req_valid = sdram_tmrbankmachine0_tmrinput_control1;
assign sdram_tmrbankmachine0_TMRreq_ready = {3{sdram_tmrbankmachine0_req_ready}};
assign sdram_tmrbankmachine0_tmrinput_control2 = (((sdram_tmrbankmachine0_TMRreq_we[0] & sdram_tmrbankmachine0_TMRreq_we[1]) | (sdram_tmrbankmachine0_TMRreq_we[1] & sdram_tmrbankmachine0_TMRreq_we[2])) | (sdram_tmrbankmachine0_TMRreq_we[0] & sdram_tmrbankmachine0_TMRreq_we[2]));
assign sdram_tmrbankmachine0_req_we = sdram_tmrbankmachine0_tmrinput_control2;
assign sdram_tmrbankmachine0_tmrinput_control3 = (((sdram_tmrbankmachine0_TMRreq_addr[20:0] & sdram_tmrbankmachine0_TMRreq_addr[41:21]) | (sdram_tmrbankmachine0_TMRreq_addr[41:21] & sdram_tmrbankmachine0_TMRreq_addr[62:42])) | (sdram_tmrbankmachine0_TMRreq_addr[20:0] & sdram_tmrbankmachine0_TMRreq_addr[62:42]));
assign sdram_tmrbankmachine0_req_addr = sdram_tmrbankmachine0_tmrinput_control3;
assign sdram_tmrbankmachine0_TMRreq_lock = {3{sdram_tmrbankmachine0_req_lock}};
assign sdram_tmrbankmachine0_TMRreq_wdata_ready = {3{sdram_tmrbankmachine0_req_wdata_ready}};
assign sdram_tmrbankmachine0_TMRreq_rdata_valid = {3{sdram_tmrbankmachine0_req_rdata_valid}};
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_din = {sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_last, sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_first, sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_payload_we};
assign {sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_last, sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_first, sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_payload_we} = sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_dout;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_ready = sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_writable;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_we = sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_first = sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_first;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_last = sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_last;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_in_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead_sink_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid = sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_readable;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_source_first = sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_first;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_source_last = sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_last;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead_fifo_out_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_re = sdram_tmrbankmachine0_cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_40;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead_replace) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_adr <= (sdram_tmrbankmachine0_cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_adr <= sdram_tmrbankmachine0_cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_40 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_dat_w = sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_din;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_we = (sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_we & (sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_writable | sdram_tmrbankmachine0_cmd_buffer_lookahead_replace));
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_do_read = (sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_readable & sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_re);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_rdport_adr = sdram_tmrbankmachine0_cmd_buffer_lookahead_consume;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_dout = sdram_tmrbankmachine0_cmd_buffer_lookahead_rdport_dat_r;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_writable = (sdram_tmrbankmachine0_cmd_buffer_lookahead_level != 4'd8);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_readable = (sdram_tmrbankmachine0_cmd_buffer_lookahead_level != 1'd0);
assign sdram_tmrbankmachine0_cmd_buffer_sink_ready = ((~sdram_tmrbankmachine0_cmd_buffer_source_valid) | sdram_tmrbankmachine0_cmd_buffer_source_ready);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_din = {sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_last, sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_first, sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_payload_we};
assign {sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_last, sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_first, sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_payload_we} = sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_dout;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_ready = sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_writable;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_we = sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_first = sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_first;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_last = sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_last;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_in_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead2_sink_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid = sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_readable;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_first = sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_first;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_last = sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_last;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead2_fifo_out_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_re = sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_41;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead2_replace) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_adr <= (sdram_tmrbankmachine0_cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_adr <= sdram_tmrbankmachine0_cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_41 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_dat_w = sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_din;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_we = (sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_we & (sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_writable | sdram_tmrbankmachine0_cmd_buffer_lookahead2_replace));
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_do_read = (sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_readable & sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_re);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_rdport_adr = sdram_tmrbankmachine0_cmd_buffer_lookahead2_consume;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_dout = sdram_tmrbankmachine0_cmd_buffer_lookahead2_rdport_dat_r;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_writable = (sdram_tmrbankmachine0_cmd_buffer_lookahead2_level != 4'd8);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_readable = (sdram_tmrbankmachine0_cmd_buffer_lookahead2_level != 1'd0);
assign sdram_tmrbankmachine0_cmd_buffer2_sink_ready = ((~sdram_tmrbankmachine0_cmd_buffer2_source_valid) | sdram_tmrbankmachine0_cmd_buffer2_source_ready);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_din = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_last, sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_first, sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_payload_we};
assign {sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_last, sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_first, sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_payload_we} = sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_dout;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_ready = sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_writable;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_we = sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_valid;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_first = sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_first;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_last = sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_last;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_in_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead3_sink_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid = sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_readable;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_first = sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_first;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_last = sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_last;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_we = sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_payload_we;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr = sdram_tmrbankmachine0_cmd_buffer_lookahead3_fifo_out_payload_addr;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_re = sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_42;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead3_replace) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_adr <= (sdram_tmrbankmachine0_cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_adr <= sdram_tmrbankmachine0_cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_42 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_dat_w = sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_din;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_we = (sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_we & (sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_writable | sdram_tmrbankmachine0_cmd_buffer_lookahead3_replace));
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_do_read = (sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_readable & sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_re);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_rdport_adr = sdram_tmrbankmachine0_cmd_buffer_lookahead3_consume;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_dout = sdram_tmrbankmachine0_cmd_buffer_lookahead3_rdport_dat_r;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_writable = (sdram_tmrbankmachine0_cmd_buffer_lookahead3_level != 4'd8);
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_readable = (sdram_tmrbankmachine0_cmd_buffer_lookahead3_level != 1'd0);
assign sdram_tmrbankmachine0_cmd_buffer3_sink_ready = ((~sdram_tmrbankmachine0_cmd_buffer3_source_valid) | sdram_tmrbankmachine0_cmd_buffer3_source_ready);
assign sdram_tmrbankmachine0_tmrinput_control4 = (((slice_proxy354[0] & slice_proxy355[1]) | (slice_proxy356[1] & slice_proxy357[2])) | (slice_proxy358[0] & slice_proxy359[2]));

// synthesis translate_off
reg dummy_d_43;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine0_req_lock <= 1'd0;
	sdram_tmrbankmachine0_req_lock <= (sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine0_cmd_buffer_source_valid);
	sdram_tmrbankmachine0_req_lock <= sdram_tmrbankmachine0_tmrinput_control4;
// synthesis translate_off
	dummy_d_43 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine0_lookAddrVote_control = (((slice_proxy360[20:0] & slice_proxy361[41:21]) | (slice_proxy362[41:21] & slice_proxy363[62:42])) | (slice_proxy364[20:0] & slice_proxy365[62:42]));
assign sdram_tmrbankmachine0_bufAddrVote_control = (((slice_proxy366[20:0] & slice_proxy367[41:21]) | (slice_proxy368[41:21] & slice_proxy369[62:42])) | (slice_proxy370[20:0] & slice_proxy371[62:42]));
assign sdram_tmrbankmachine0_lookValidVote_control = (((slice_proxy372[0] & slice_proxy373[1]) | (slice_proxy374[1] & slice_proxy375[2])) | (slice_proxy376[0] & slice_proxy377[2]));
assign sdram_tmrbankmachine0_bufValidVote_control = (((slice_proxy378[0] & slice_proxy379[1]) | (slice_proxy380[1] & slice_proxy381[2])) | (slice_proxy382[0] & slice_proxy383[2]));
assign sdram_tmrbankmachine0_bufWeVote_control = (((slice_proxy384[0] & slice_proxy385[1]) | (slice_proxy386[1] & slice_proxy387[2])) | (slice_proxy388[0] & slice_proxy389[2]));
assign sdram_tmrbankmachine0_twtpVote_control = (((slice_proxy390[0] & slice_proxy391[1]) | (slice_proxy392[1] & slice_proxy393[2])) | (slice_proxy394[0] & slice_proxy395[2]));
assign sdram_tmrbankmachine0_trcVote_control = (((slice_proxy396[0] & slice_proxy397[1]) | (slice_proxy398[1] & slice_proxy399[2])) | (slice_proxy400[0] & slice_proxy401[2]));
assign sdram_tmrbankmachine0_trasVote_control = (((slice_proxy402[0] & slice_proxy403[1]) | (slice_proxy404[1] & slice_proxy405[2])) | (slice_proxy406[0] & slice_proxy407[2]));

// synthesis translate_off
reg dummy_d_44;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine0_req_wdata_ready <= 1'd0;
	sdram_tmrbankmachine0_req_rdata_valid <= 1'd0;
	sdram_tmrbankmachine0_refresh_gnt <= 1'd0;
	sdram_tmrbankmachine0_cmd_valid <= 1'd0;
	sdram_tmrbankmachine0_cmd_payload_cas <= 1'd0;
	sdram_tmrbankmachine0_cmd_payload_ras <= 1'd0;
	sdram_tmrbankmachine0_cmd_payload_we <= 1'd0;
	sdram_tmrbankmachine0_cmd_payload_is_cmd <= 1'd0;
	sdram_tmrbankmachine0_cmd_payload_is_read <= 1'd0;
	sdram_tmrbankmachine0_cmd_payload_is_write <= 1'd0;
	sdram_tmrbankmachine0_row_open <= 1'd0;
	sdram_tmrbankmachine0_row_close <= 1'd0;
	sdram_tmrbankmachine0_row_col_n_addr_sel <= 1'd0;
	tmrbankmachine0_next_state <= 4'd0;
	tmrbankmachine0_next_state <= tmrbankmachine0_state;
	case (tmrbankmachine0_state)
		1'd1: begin
			if ((sdram_tmrbankmachine0_twtpVote_control & sdram_tmrbankmachine0_trasVote_control)) begin
				sdram_tmrbankmachine0_cmd_valid <= 1'd1;
				if (sdram_tmrbankmachine0_cmd_ready) begin
					tmrbankmachine0_next_state <= 3'd5;
				end
				sdram_tmrbankmachine0_cmd_payload_ras <= 1'd1;
				sdram_tmrbankmachine0_cmd_payload_we <= 1'd1;
				sdram_tmrbankmachine0_cmd_payload_is_cmd <= 1'd1;
			end
			sdram_tmrbankmachine0_row_close <= 1'd1;
		end
		2'd2: begin
			if ((sdram_tmrbankmachine0_twtpVote_control & sdram_tmrbankmachine0_trasVote_control)) begin
				tmrbankmachine0_next_state <= 3'd5;
			end
			sdram_tmrbankmachine0_row_close <= 1'd1;
		end
		2'd3: begin
			if (sdram_tmrbankmachine0_trcVote_control) begin
				sdram_tmrbankmachine0_row_col_n_addr_sel <= 1'd1;
				sdram_tmrbankmachine0_row_open <= 1'd1;
				sdram_tmrbankmachine0_cmd_valid <= 1'd1;
				sdram_tmrbankmachine0_cmd_payload_is_cmd <= 1'd1;
				if (sdram_tmrbankmachine0_cmd_ready) begin
					tmrbankmachine0_next_state <= 3'd7;
				end
				sdram_tmrbankmachine0_cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			if (sdram_tmrbankmachine0_twtpVote_control) begin
				sdram_tmrbankmachine0_refresh_gnt <= 1'd1;
			end
			sdram_tmrbankmachine0_row_close <= 1'd1;
			sdram_tmrbankmachine0_cmd_payload_is_cmd <= 1'd1;
			if ((~sdram_tmrbankmachine0_refresh_req)) begin
				tmrbankmachine0_next_state <= 1'd0;
			end
		end
		3'd5: begin
			tmrbankmachine0_next_state <= 3'd6;
		end
		3'd6: begin
			tmrbankmachine0_next_state <= 2'd3;
		end
		3'd7: begin
			tmrbankmachine0_next_state <= 4'd8;
		end
		4'd8: begin
			tmrbankmachine0_next_state <= 1'd0;
		end
		default: begin
			if (sdram_tmrbankmachine0_refresh_req) begin
				tmrbankmachine0_next_state <= 3'd4;
			end else begin
				if (sdram_tmrbankmachine0_cmd_buffer_source_valid) begin
					if (sdram_tmrbankmachine0_row_opened) begin
						if (sdram_tmrbankmachine0_row_hit) begin
							sdram_tmrbankmachine0_cmd_valid <= 1'd1;
							if (sdram_tmrbankmachine0_cmd_buffer_source_payload_we) begin
								sdram_tmrbankmachine0_req_wdata_ready <= sdram_tmrbankmachine0_cmd_ready;
								sdram_tmrbankmachine0_cmd_payload_is_write <= 1'd1;
								sdram_tmrbankmachine0_cmd_payload_we <= 1'd1;
							end else begin
								sdram_tmrbankmachine0_req_rdata_valid <= sdram_tmrbankmachine0_cmd_ready;
								sdram_tmrbankmachine0_cmd_payload_is_read <= 1'd1;
							end
							sdram_tmrbankmachine0_cmd_payload_cas <= 1'd1;
							if ((sdram_tmrbankmachine0_cmd_ready & sdram_tmrbankmachine0_auto_precharge)) begin
								tmrbankmachine0_next_state <= 2'd2;
							end
						end else begin
							tmrbankmachine0_next_state <= 1'd1;
						end
					end else begin
						tmrbankmachine0_next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_44 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_valid = sdram_tmrbankmachine1_req_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_payload_we = sdram_tmrbankmachine1_req_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_payload_addr = sdram_tmrbankmachine1_req_addr;
assign sdram_tmrbankmachine1_cmd_buffer_sink_valid = sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_source_ready = sdram_tmrbankmachine1_cmd_buffer_sink_ready;
assign sdram_tmrbankmachine1_cmd_buffer_sink_first = sdram_tmrbankmachine1_cmd_buffer_lookahead_source_first;
assign sdram_tmrbankmachine1_cmd_buffer_sink_last = sdram_tmrbankmachine1_cmd_buffer_lookahead_source_last;
assign sdram_tmrbankmachine1_cmd_buffer_sink_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer_sink_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer_source_ready = (sdram_tmrbankmachine1_req_wdata_ready | sdram_tmrbankmachine1_req_rdata_valid);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_valid = sdram_tmrbankmachine1_req_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_payload_we = sdram_tmrbankmachine1_req_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_payload_addr = sdram_tmrbankmachine1_req_addr;
assign sdram_tmrbankmachine1_cmd_buffer2_sink_valid = sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_ready = sdram_tmrbankmachine1_cmd_buffer2_sink_ready;
assign sdram_tmrbankmachine1_cmd_buffer2_sink_first = sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_first;
assign sdram_tmrbankmachine1_cmd_buffer2_sink_last = sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_last;
assign sdram_tmrbankmachine1_cmd_buffer2_sink_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer2_sink_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer2_source_ready = (sdram_tmrbankmachine1_req_wdata_ready | sdram_tmrbankmachine1_req_rdata_valid);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_valid = sdram_tmrbankmachine1_req_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_payload_we = sdram_tmrbankmachine1_req_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_payload_addr = sdram_tmrbankmachine1_req_addr;
assign sdram_tmrbankmachine1_cmd_buffer3_sink_valid = sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_ready = sdram_tmrbankmachine1_cmd_buffer3_sink_ready;
assign sdram_tmrbankmachine1_cmd_buffer3_sink_first = sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_first;
assign sdram_tmrbankmachine1_cmd_buffer3_sink_last = sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_last;
assign sdram_tmrbankmachine1_cmd_buffer3_sink_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer3_sink_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer3_source_ready = (sdram_tmrbankmachine1_req_wdata_ready | sdram_tmrbankmachine1_req_rdata_valid);
assign sdram_tmrbankmachine1_req_ready = ((sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_ready & sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_ready) & sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_ready);
assign sdram_tmrbankmachine1_row_hit = (sdram_tmrbankmachine1_row == sdram_tmrbankmachine1_cmd_buffer_source_payload_addr[20:7]);
assign sdram_tmrbankmachine1_cmd_payload_ba = 1'd1;

// synthesis translate_off
reg dummy_d_45;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine1_cmd_payload_a <= 14'd0;
	if (sdram_tmrbankmachine1_row_col_n_addr_sel) begin
		sdram_tmrbankmachine1_cmd_payload_a <= sdram_tmrbankmachine1_cmd_buffer_source_payload_addr[20:7];
	end else begin
		sdram_tmrbankmachine1_cmd_payload_a <= ((sdram_tmrbankmachine1_auto_precharge <<< 4'd10) | {sdram_tmrbankmachine1_cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_45 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine1_twtpcon_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_cmd_payload_is_write);
assign sdram_tmrbankmachine1_twtpcon2_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_cmd_payload_is_write);
assign sdram_tmrbankmachine1_twtpcon3_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_cmd_payload_is_write);
assign sdram_tmrbankmachine1_trccon_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_row_open);
assign sdram_tmrbankmachine1_trccon2_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_row_open);
assign sdram_tmrbankmachine1_trccon3_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_row_open);
assign sdram_tmrbankmachine1_trascon_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_row_open);
assign sdram_tmrbankmachine1_trascon2_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_row_open);
assign sdram_tmrbankmachine1_trascon3_valid = ((sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_ready) & sdram_tmrbankmachine1_row_open);

// synthesis translate_off
reg dummy_d_46;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine1_auto_precharge <= 1'd0;
	if ((sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid & sdram_tmrbankmachine1_cmd_buffer_source_valid)) begin
		if ((sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr[20:7] != sdram_tmrbankmachine1_cmd_buffer_source_payload_addr[20:7])) begin
			sdram_tmrbankmachine1_auto_precharge <= (sdram_tmrbankmachine1_row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_46 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine1_TMRcmd_valid = {3{sdram_tmrbankmachine1_cmd_valid}};
assign sdram_tmrbankmachine1_TMRcmd_last = {3{sdram_tmrbankmachine1_cmd_last}};
assign sdram_tmrbankmachine1_TMRcmd_first = {3{sdram_tmrbankmachine1_cmd_first}};
assign sdram_tmrbankmachine1_tmrinput_control0 = (((sdram_tmrbankmachine1_TMRcmd_ready[0] & sdram_tmrbankmachine1_TMRcmd_ready[1]) | (sdram_tmrbankmachine1_TMRcmd_ready[1] & sdram_tmrbankmachine1_TMRcmd_ready[2])) | (sdram_tmrbankmachine1_TMRcmd_ready[0] & sdram_tmrbankmachine1_TMRcmd_ready[2]));
assign sdram_tmrbankmachine1_cmd_ready = sdram_tmrbankmachine1_tmrinput_control0;
assign sdram_tmrbankmachine1_TMRcmd_payload_a = {3{sdram_tmrbankmachine1_cmd_payload_a}};
assign sdram_tmrbankmachine1_TMRcmd_payload_ba = {3{sdram_tmrbankmachine1_cmd_payload_ba}};
assign sdram_tmrbankmachine1_TMRcmd_payload_cas = {3{sdram_tmrbankmachine1_cmd_payload_cas}};
assign sdram_tmrbankmachine1_TMRcmd_payload_ras = {3{sdram_tmrbankmachine1_cmd_payload_ras}};
assign sdram_tmrbankmachine1_TMRcmd_payload_we = {3{sdram_tmrbankmachine1_cmd_payload_we}};
assign sdram_tmrbankmachine1_TMRcmd_payload_is_cmd = {3{sdram_tmrbankmachine1_cmd_payload_is_cmd}};
assign sdram_tmrbankmachine1_TMRcmd_payload_is_read = {3{sdram_tmrbankmachine1_cmd_payload_is_read}};
assign sdram_tmrbankmachine1_TMRcmd_payload_is_write = {3{sdram_tmrbankmachine1_cmd_payload_is_write}};
assign sdram_tmrbankmachine1_tmrinput_control1 = (((sdram_tmrbankmachine1_TMRreq_valid[0] & sdram_tmrbankmachine1_TMRreq_valid[1]) | (sdram_tmrbankmachine1_TMRreq_valid[1] & sdram_tmrbankmachine1_TMRreq_valid[2])) | (sdram_tmrbankmachine1_TMRreq_valid[0] & sdram_tmrbankmachine1_TMRreq_valid[2]));
assign sdram_tmrbankmachine1_req_valid = sdram_tmrbankmachine1_tmrinput_control1;
assign sdram_tmrbankmachine1_TMRreq_ready = {3{sdram_tmrbankmachine1_req_ready}};
assign sdram_tmrbankmachine1_tmrinput_control2 = (((sdram_tmrbankmachine1_TMRreq_we[0] & sdram_tmrbankmachine1_TMRreq_we[1]) | (sdram_tmrbankmachine1_TMRreq_we[1] & sdram_tmrbankmachine1_TMRreq_we[2])) | (sdram_tmrbankmachine1_TMRreq_we[0] & sdram_tmrbankmachine1_TMRreq_we[2]));
assign sdram_tmrbankmachine1_req_we = sdram_tmrbankmachine1_tmrinput_control2;
assign sdram_tmrbankmachine1_tmrinput_control3 = (((sdram_tmrbankmachine1_TMRreq_addr[20:0] & sdram_tmrbankmachine1_TMRreq_addr[41:21]) | (sdram_tmrbankmachine1_TMRreq_addr[41:21] & sdram_tmrbankmachine1_TMRreq_addr[62:42])) | (sdram_tmrbankmachine1_TMRreq_addr[20:0] & sdram_tmrbankmachine1_TMRreq_addr[62:42]));
assign sdram_tmrbankmachine1_req_addr = sdram_tmrbankmachine1_tmrinput_control3;
assign sdram_tmrbankmachine1_TMRreq_lock = {3{sdram_tmrbankmachine1_req_lock}};
assign sdram_tmrbankmachine1_TMRreq_wdata_ready = {3{sdram_tmrbankmachine1_req_wdata_ready}};
assign sdram_tmrbankmachine1_TMRreq_rdata_valid = {3{sdram_tmrbankmachine1_req_rdata_valid}};
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_din = {sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_last, sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_first, sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_payload_we};
assign {sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_last, sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_first, sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_payload_we} = sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_dout;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_ready = sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_writable;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_we = sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_first = sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_first;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_last = sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_last;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_in_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead_sink_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid = sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_readable;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_source_first = sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_first;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_source_last = sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_last;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead_fifo_out_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_re = sdram_tmrbankmachine1_cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_47;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead_replace) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_adr <= (sdram_tmrbankmachine1_cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_adr <= sdram_tmrbankmachine1_cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_47 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_dat_w = sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_din;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_we = (sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_we & (sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_writable | sdram_tmrbankmachine1_cmd_buffer_lookahead_replace));
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_do_read = (sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_readable & sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_re);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_rdport_adr = sdram_tmrbankmachine1_cmd_buffer_lookahead_consume;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_dout = sdram_tmrbankmachine1_cmd_buffer_lookahead_rdport_dat_r;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_writable = (sdram_tmrbankmachine1_cmd_buffer_lookahead_level != 4'd8);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_readable = (sdram_tmrbankmachine1_cmd_buffer_lookahead_level != 1'd0);
assign sdram_tmrbankmachine1_cmd_buffer_sink_ready = ((~sdram_tmrbankmachine1_cmd_buffer_source_valid) | sdram_tmrbankmachine1_cmd_buffer_source_ready);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_din = {sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_last, sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_first, sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_payload_we};
assign {sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_last, sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_first, sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_payload_we} = sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_dout;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_ready = sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_writable;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_we = sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_first = sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_first;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_last = sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_last;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_in_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead2_sink_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid = sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_readable;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_first = sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_first;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_last = sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_last;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead2_fifo_out_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_re = sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_48;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead2_replace) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_adr <= (sdram_tmrbankmachine1_cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_adr <= sdram_tmrbankmachine1_cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_48 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_dat_w = sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_din;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_we = (sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_we & (sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_writable | sdram_tmrbankmachine1_cmd_buffer_lookahead2_replace));
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_do_read = (sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_readable & sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_re);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_rdport_adr = sdram_tmrbankmachine1_cmd_buffer_lookahead2_consume;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_dout = sdram_tmrbankmachine1_cmd_buffer_lookahead2_rdport_dat_r;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_writable = (sdram_tmrbankmachine1_cmd_buffer_lookahead2_level != 4'd8);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_readable = (sdram_tmrbankmachine1_cmd_buffer_lookahead2_level != 1'd0);
assign sdram_tmrbankmachine1_cmd_buffer2_sink_ready = ((~sdram_tmrbankmachine1_cmd_buffer2_source_valid) | sdram_tmrbankmachine1_cmd_buffer2_source_ready);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_din = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_last, sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_first, sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_payload_we};
assign {sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_last, sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_first, sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_payload_we} = sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_dout;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_ready = sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_writable;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_we = sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_valid;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_first = sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_first;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_last = sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_last;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_in_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead3_sink_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid = sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_readable;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_first = sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_first;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_last = sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_last;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_we = sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_payload_we;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr = sdram_tmrbankmachine1_cmd_buffer_lookahead3_fifo_out_payload_addr;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_re = sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_49;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead3_replace) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_adr <= (sdram_tmrbankmachine1_cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_adr <= sdram_tmrbankmachine1_cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_49 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_dat_w = sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_din;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_we = (sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_we & (sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_writable | sdram_tmrbankmachine1_cmd_buffer_lookahead3_replace));
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_do_read = (sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_readable & sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_re);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_rdport_adr = sdram_tmrbankmachine1_cmd_buffer_lookahead3_consume;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_dout = sdram_tmrbankmachine1_cmd_buffer_lookahead3_rdport_dat_r;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_writable = (sdram_tmrbankmachine1_cmd_buffer_lookahead3_level != 4'd8);
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_readable = (sdram_tmrbankmachine1_cmd_buffer_lookahead3_level != 1'd0);
assign sdram_tmrbankmachine1_cmd_buffer3_sink_ready = ((~sdram_tmrbankmachine1_cmd_buffer3_source_valid) | sdram_tmrbankmachine1_cmd_buffer3_source_ready);
assign sdram_tmrbankmachine1_tmrinput_control4 = (((slice_proxy408[0] & slice_proxy409[1]) | (slice_proxy410[1] & slice_proxy411[2])) | (slice_proxy412[0] & slice_proxy413[2]));

// synthesis translate_off
reg dummy_d_50;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine1_req_lock <= 1'd0;
	sdram_tmrbankmachine1_req_lock <= (sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine1_cmd_buffer_source_valid);
	sdram_tmrbankmachine1_req_lock <= sdram_tmrbankmachine1_tmrinput_control4;
// synthesis translate_off
	dummy_d_50 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine1_lookAddrVote_control = (((slice_proxy414[20:0] & slice_proxy415[41:21]) | (slice_proxy416[41:21] & slice_proxy417[62:42])) | (slice_proxy418[20:0] & slice_proxy419[62:42]));
assign sdram_tmrbankmachine1_bufAddrVote_control = (((slice_proxy420[20:0] & slice_proxy421[41:21]) | (slice_proxy422[41:21] & slice_proxy423[62:42])) | (slice_proxy424[20:0] & slice_proxy425[62:42]));
assign sdram_tmrbankmachine1_lookValidVote_control = (((slice_proxy426[0] & slice_proxy427[1]) | (slice_proxy428[1] & slice_proxy429[2])) | (slice_proxy430[0] & slice_proxy431[2]));
assign sdram_tmrbankmachine1_bufValidVote_control = (((slice_proxy432[0] & slice_proxy433[1]) | (slice_proxy434[1] & slice_proxy435[2])) | (slice_proxy436[0] & slice_proxy437[2]));
assign sdram_tmrbankmachine1_bufWeVote_control = (((slice_proxy438[0] & slice_proxy439[1]) | (slice_proxy440[1] & slice_proxy441[2])) | (slice_proxy442[0] & slice_proxy443[2]));
assign sdram_tmrbankmachine1_twtpVote_control = (((slice_proxy444[0] & slice_proxy445[1]) | (slice_proxy446[1] & slice_proxy447[2])) | (slice_proxy448[0] & slice_proxy449[2]));
assign sdram_tmrbankmachine1_trcVote_control = (((slice_proxy450[0] & slice_proxy451[1]) | (slice_proxy452[1] & slice_proxy453[2])) | (slice_proxy454[0] & slice_proxy455[2]));
assign sdram_tmrbankmachine1_trasVote_control = (((slice_proxy456[0] & slice_proxy457[1]) | (slice_proxy458[1] & slice_proxy459[2])) | (slice_proxy460[0] & slice_proxy461[2]));

// synthesis translate_off
reg dummy_d_51;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine1_req_wdata_ready <= 1'd0;
	sdram_tmrbankmachine1_req_rdata_valid <= 1'd0;
	sdram_tmrbankmachine1_refresh_gnt <= 1'd0;
	sdram_tmrbankmachine1_cmd_valid <= 1'd0;
	sdram_tmrbankmachine1_cmd_payload_cas <= 1'd0;
	sdram_tmrbankmachine1_cmd_payload_ras <= 1'd0;
	sdram_tmrbankmachine1_cmd_payload_we <= 1'd0;
	sdram_tmrbankmachine1_cmd_payload_is_cmd <= 1'd0;
	sdram_tmrbankmachine1_cmd_payload_is_read <= 1'd0;
	sdram_tmrbankmachine1_cmd_payload_is_write <= 1'd0;
	sdram_tmrbankmachine1_row_open <= 1'd0;
	sdram_tmrbankmachine1_row_close <= 1'd0;
	sdram_tmrbankmachine1_row_col_n_addr_sel <= 1'd0;
	tmrbankmachine1_next_state <= 4'd0;
	tmrbankmachine1_next_state <= tmrbankmachine1_state;
	case (tmrbankmachine1_state)
		1'd1: begin
			if ((sdram_tmrbankmachine1_twtpVote_control & sdram_tmrbankmachine1_trasVote_control)) begin
				sdram_tmrbankmachine1_cmd_valid <= 1'd1;
				if (sdram_tmrbankmachine1_cmd_ready) begin
					tmrbankmachine1_next_state <= 3'd5;
				end
				sdram_tmrbankmachine1_cmd_payload_ras <= 1'd1;
				sdram_tmrbankmachine1_cmd_payload_we <= 1'd1;
				sdram_tmrbankmachine1_cmd_payload_is_cmd <= 1'd1;
			end
			sdram_tmrbankmachine1_row_close <= 1'd1;
		end
		2'd2: begin
			if ((sdram_tmrbankmachine1_twtpVote_control & sdram_tmrbankmachine1_trasVote_control)) begin
				tmrbankmachine1_next_state <= 3'd5;
			end
			sdram_tmrbankmachine1_row_close <= 1'd1;
		end
		2'd3: begin
			if (sdram_tmrbankmachine1_trcVote_control) begin
				sdram_tmrbankmachine1_row_col_n_addr_sel <= 1'd1;
				sdram_tmrbankmachine1_row_open <= 1'd1;
				sdram_tmrbankmachine1_cmd_valid <= 1'd1;
				sdram_tmrbankmachine1_cmd_payload_is_cmd <= 1'd1;
				if (sdram_tmrbankmachine1_cmd_ready) begin
					tmrbankmachine1_next_state <= 3'd7;
				end
				sdram_tmrbankmachine1_cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			if (sdram_tmrbankmachine1_twtpVote_control) begin
				sdram_tmrbankmachine1_refresh_gnt <= 1'd1;
			end
			sdram_tmrbankmachine1_row_close <= 1'd1;
			sdram_tmrbankmachine1_cmd_payload_is_cmd <= 1'd1;
			if ((~sdram_tmrbankmachine1_refresh_req)) begin
				tmrbankmachine1_next_state <= 1'd0;
			end
		end
		3'd5: begin
			tmrbankmachine1_next_state <= 3'd6;
		end
		3'd6: begin
			tmrbankmachine1_next_state <= 2'd3;
		end
		3'd7: begin
			tmrbankmachine1_next_state <= 4'd8;
		end
		4'd8: begin
			tmrbankmachine1_next_state <= 1'd0;
		end
		default: begin
			if (sdram_tmrbankmachine1_refresh_req) begin
				tmrbankmachine1_next_state <= 3'd4;
			end else begin
				if (sdram_tmrbankmachine1_cmd_buffer_source_valid) begin
					if (sdram_tmrbankmachine1_row_opened) begin
						if (sdram_tmrbankmachine1_row_hit) begin
							sdram_tmrbankmachine1_cmd_valid <= 1'd1;
							if (sdram_tmrbankmachine1_cmd_buffer_source_payload_we) begin
								sdram_tmrbankmachine1_req_wdata_ready <= sdram_tmrbankmachine1_cmd_ready;
								sdram_tmrbankmachine1_cmd_payload_is_write <= 1'd1;
								sdram_tmrbankmachine1_cmd_payload_we <= 1'd1;
							end else begin
								sdram_tmrbankmachine1_req_rdata_valid <= sdram_tmrbankmachine1_cmd_ready;
								sdram_tmrbankmachine1_cmd_payload_is_read <= 1'd1;
							end
							sdram_tmrbankmachine1_cmd_payload_cas <= 1'd1;
							if ((sdram_tmrbankmachine1_cmd_ready & sdram_tmrbankmachine1_auto_precharge)) begin
								tmrbankmachine1_next_state <= 2'd2;
							end
						end else begin
							tmrbankmachine1_next_state <= 1'd1;
						end
					end else begin
						tmrbankmachine1_next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_51 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_valid = sdram_tmrbankmachine2_req_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_payload_we = sdram_tmrbankmachine2_req_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_payload_addr = sdram_tmrbankmachine2_req_addr;
assign sdram_tmrbankmachine2_cmd_buffer_sink_valid = sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_source_ready = sdram_tmrbankmachine2_cmd_buffer_sink_ready;
assign sdram_tmrbankmachine2_cmd_buffer_sink_first = sdram_tmrbankmachine2_cmd_buffer_lookahead_source_first;
assign sdram_tmrbankmachine2_cmd_buffer_sink_last = sdram_tmrbankmachine2_cmd_buffer_lookahead_source_last;
assign sdram_tmrbankmachine2_cmd_buffer_sink_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer_sink_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer_source_ready = (sdram_tmrbankmachine2_req_wdata_ready | sdram_tmrbankmachine2_req_rdata_valid);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_valid = sdram_tmrbankmachine2_req_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_payload_we = sdram_tmrbankmachine2_req_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_payload_addr = sdram_tmrbankmachine2_req_addr;
assign sdram_tmrbankmachine2_cmd_buffer2_sink_valid = sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_ready = sdram_tmrbankmachine2_cmd_buffer2_sink_ready;
assign sdram_tmrbankmachine2_cmd_buffer2_sink_first = sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_first;
assign sdram_tmrbankmachine2_cmd_buffer2_sink_last = sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_last;
assign sdram_tmrbankmachine2_cmd_buffer2_sink_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer2_sink_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer2_source_ready = (sdram_tmrbankmachine2_req_wdata_ready | sdram_tmrbankmachine2_req_rdata_valid);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_valid = sdram_tmrbankmachine2_req_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_payload_we = sdram_tmrbankmachine2_req_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_payload_addr = sdram_tmrbankmachine2_req_addr;
assign sdram_tmrbankmachine2_cmd_buffer3_sink_valid = sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_ready = sdram_tmrbankmachine2_cmd_buffer3_sink_ready;
assign sdram_tmrbankmachine2_cmd_buffer3_sink_first = sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_first;
assign sdram_tmrbankmachine2_cmd_buffer3_sink_last = sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_last;
assign sdram_tmrbankmachine2_cmd_buffer3_sink_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer3_sink_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer3_source_ready = (sdram_tmrbankmachine2_req_wdata_ready | sdram_tmrbankmachine2_req_rdata_valid);
assign sdram_tmrbankmachine2_req_ready = ((sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_ready & sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_ready) & sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_ready);
assign sdram_tmrbankmachine2_row_hit = (sdram_tmrbankmachine2_row == sdram_tmrbankmachine2_cmd_buffer_source_payload_addr[20:7]);
assign sdram_tmrbankmachine2_cmd_payload_ba = 2'd2;

// synthesis translate_off
reg dummy_d_52;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine2_cmd_payload_a <= 14'd0;
	if (sdram_tmrbankmachine2_row_col_n_addr_sel) begin
		sdram_tmrbankmachine2_cmd_payload_a <= sdram_tmrbankmachine2_cmd_buffer_source_payload_addr[20:7];
	end else begin
		sdram_tmrbankmachine2_cmd_payload_a <= ((sdram_tmrbankmachine2_auto_precharge <<< 4'd10) | {sdram_tmrbankmachine2_cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_52 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine2_twtpcon_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_cmd_payload_is_write);
assign sdram_tmrbankmachine2_twtpcon2_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_cmd_payload_is_write);
assign sdram_tmrbankmachine2_twtpcon3_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_cmd_payload_is_write);
assign sdram_tmrbankmachine2_trccon_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_row_open);
assign sdram_tmrbankmachine2_trccon2_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_row_open);
assign sdram_tmrbankmachine2_trccon3_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_row_open);
assign sdram_tmrbankmachine2_trascon_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_row_open);
assign sdram_tmrbankmachine2_trascon2_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_row_open);
assign sdram_tmrbankmachine2_trascon3_valid = ((sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_ready) & sdram_tmrbankmachine2_row_open);

// synthesis translate_off
reg dummy_d_53;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine2_auto_precharge <= 1'd0;
	if ((sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid & sdram_tmrbankmachine2_cmd_buffer_source_valid)) begin
		if ((sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr[20:7] != sdram_tmrbankmachine2_cmd_buffer_source_payload_addr[20:7])) begin
			sdram_tmrbankmachine2_auto_precharge <= (sdram_tmrbankmachine2_row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_53 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine2_TMRcmd_valid = {3{sdram_tmrbankmachine2_cmd_valid}};
assign sdram_tmrbankmachine2_TMRcmd_last = {3{sdram_tmrbankmachine2_cmd_last}};
assign sdram_tmrbankmachine2_TMRcmd_first = {3{sdram_tmrbankmachine2_cmd_first}};
assign sdram_tmrbankmachine2_tmrinput_control0 = (((sdram_tmrbankmachine2_TMRcmd_ready[0] & sdram_tmrbankmachine2_TMRcmd_ready[1]) | (sdram_tmrbankmachine2_TMRcmd_ready[1] & sdram_tmrbankmachine2_TMRcmd_ready[2])) | (sdram_tmrbankmachine2_TMRcmd_ready[0] & sdram_tmrbankmachine2_TMRcmd_ready[2]));
assign sdram_tmrbankmachine2_cmd_ready = sdram_tmrbankmachine2_tmrinput_control0;
assign sdram_tmrbankmachine2_TMRcmd_payload_a = {3{sdram_tmrbankmachine2_cmd_payload_a}};
assign sdram_tmrbankmachine2_TMRcmd_payload_ba = {3{sdram_tmrbankmachine2_cmd_payload_ba}};
assign sdram_tmrbankmachine2_TMRcmd_payload_cas = {3{sdram_tmrbankmachine2_cmd_payload_cas}};
assign sdram_tmrbankmachine2_TMRcmd_payload_ras = {3{sdram_tmrbankmachine2_cmd_payload_ras}};
assign sdram_tmrbankmachine2_TMRcmd_payload_we = {3{sdram_tmrbankmachine2_cmd_payload_we}};
assign sdram_tmrbankmachine2_TMRcmd_payload_is_cmd = {3{sdram_tmrbankmachine2_cmd_payload_is_cmd}};
assign sdram_tmrbankmachine2_TMRcmd_payload_is_read = {3{sdram_tmrbankmachine2_cmd_payload_is_read}};
assign sdram_tmrbankmachine2_TMRcmd_payload_is_write = {3{sdram_tmrbankmachine2_cmd_payload_is_write}};
assign sdram_tmrbankmachine2_tmrinput_control1 = (((sdram_tmrbankmachine2_TMRreq_valid[0] & sdram_tmrbankmachine2_TMRreq_valid[1]) | (sdram_tmrbankmachine2_TMRreq_valid[1] & sdram_tmrbankmachine2_TMRreq_valid[2])) | (sdram_tmrbankmachine2_TMRreq_valid[0] & sdram_tmrbankmachine2_TMRreq_valid[2]));
assign sdram_tmrbankmachine2_req_valid = sdram_tmrbankmachine2_tmrinput_control1;
assign sdram_tmrbankmachine2_TMRreq_ready = {3{sdram_tmrbankmachine2_req_ready}};
assign sdram_tmrbankmachine2_tmrinput_control2 = (((sdram_tmrbankmachine2_TMRreq_we[0] & sdram_tmrbankmachine2_TMRreq_we[1]) | (sdram_tmrbankmachine2_TMRreq_we[1] & sdram_tmrbankmachine2_TMRreq_we[2])) | (sdram_tmrbankmachine2_TMRreq_we[0] & sdram_tmrbankmachine2_TMRreq_we[2]));
assign sdram_tmrbankmachine2_req_we = sdram_tmrbankmachine2_tmrinput_control2;
assign sdram_tmrbankmachine2_tmrinput_control3 = (((sdram_tmrbankmachine2_TMRreq_addr[20:0] & sdram_tmrbankmachine2_TMRreq_addr[41:21]) | (sdram_tmrbankmachine2_TMRreq_addr[41:21] & sdram_tmrbankmachine2_TMRreq_addr[62:42])) | (sdram_tmrbankmachine2_TMRreq_addr[20:0] & sdram_tmrbankmachine2_TMRreq_addr[62:42]));
assign sdram_tmrbankmachine2_req_addr = sdram_tmrbankmachine2_tmrinput_control3;
assign sdram_tmrbankmachine2_TMRreq_lock = {3{sdram_tmrbankmachine2_req_lock}};
assign sdram_tmrbankmachine2_TMRreq_wdata_ready = {3{sdram_tmrbankmachine2_req_wdata_ready}};
assign sdram_tmrbankmachine2_TMRreq_rdata_valid = {3{sdram_tmrbankmachine2_req_rdata_valid}};
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_din = {sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_last, sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_first, sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_payload_we};
assign {sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_last, sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_first, sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_payload_we} = sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_dout;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_ready = sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_writable;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_we = sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_first = sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_first;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_last = sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_last;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_in_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead_sink_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid = sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_readable;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_source_first = sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_first;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_source_last = sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_last;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead_fifo_out_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_re = sdram_tmrbankmachine2_cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_54;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead_replace) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_adr <= (sdram_tmrbankmachine2_cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_adr <= sdram_tmrbankmachine2_cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_54 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_dat_w = sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_din;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_we = (sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_we & (sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_writable | sdram_tmrbankmachine2_cmd_buffer_lookahead_replace));
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_do_read = (sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_readable & sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_re);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_rdport_adr = sdram_tmrbankmachine2_cmd_buffer_lookahead_consume;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_dout = sdram_tmrbankmachine2_cmd_buffer_lookahead_rdport_dat_r;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_writable = (sdram_tmrbankmachine2_cmd_buffer_lookahead_level != 4'd8);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_readable = (sdram_tmrbankmachine2_cmd_buffer_lookahead_level != 1'd0);
assign sdram_tmrbankmachine2_cmd_buffer_sink_ready = ((~sdram_tmrbankmachine2_cmd_buffer_source_valid) | sdram_tmrbankmachine2_cmd_buffer_source_ready);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_din = {sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_last, sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_first, sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_payload_we};
assign {sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_last, sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_first, sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_payload_we} = sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_dout;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_ready = sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_writable;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_we = sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_first = sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_first;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_last = sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_last;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_in_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead2_sink_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid = sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_readable;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_first = sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_first;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_last = sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_last;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead2_fifo_out_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_re = sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_55;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead2_replace) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_adr <= (sdram_tmrbankmachine2_cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_adr <= sdram_tmrbankmachine2_cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_55 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_dat_w = sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_din;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_we = (sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_we & (sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_writable | sdram_tmrbankmachine2_cmd_buffer_lookahead2_replace));
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_do_read = (sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_readable & sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_re);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_rdport_adr = sdram_tmrbankmachine2_cmd_buffer_lookahead2_consume;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_dout = sdram_tmrbankmachine2_cmd_buffer_lookahead2_rdport_dat_r;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_writable = (sdram_tmrbankmachine2_cmd_buffer_lookahead2_level != 4'd8);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_readable = (sdram_tmrbankmachine2_cmd_buffer_lookahead2_level != 1'd0);
assign sdram_tmrbankmachine2_cmd_buffer2_sink_ready = ((~sdram_tmrbankmachine2_cmd_buffer2_source_valid) | sdram_tmrbankmachine2_cmd_buffer2_source_ready);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_din = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_last, sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_first, sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_payload_we};
assign {sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_last, sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_first, sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_payload_we} = sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_dout;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_ready = sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_writable;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_we = sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_valid;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_first = sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_first;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_last = sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_last;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_in_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead3_sink_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid = sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_readable;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_first = sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_first;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_last = sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_last;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_we = sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_payload_we;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr = sdram_tmrbankmachine2_cmd_buffer_lookahead3_fifo_out_payload_addr;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_re = sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_56;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead3_replace) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_adr <= (sdram_tmrbankmachine2_cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_adr <= sdram_tmrbankmachine2_cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_56 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_dat_w = sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_din;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_we = (sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_we & (sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_writable | sdram_tmrbankmachine2_cmd_buffer_lookahead3_replace));
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_do_read = (sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_readable & sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_re);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_rdport_adr = sdram_tmrbankmachine2_cmd_buffer_lookahead3_consume;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_dout = sdram_tmrbankmachine2_cmd_buffer_lookahead3_rdport_dat_r;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_writable = (sdram_tmrbankmachine2_cmd_buffer_lookahead3_level != 4'd8);
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_readable = (sdram_tmrbankmachine2_cmd_buffer_lookahead3_level != 1'd0);
assign sdram_tmrbankmachine2_cmd_buffer3_sink_ready = ((~sdram_tmrbankmachine2_cmd_buffer3_source_valid) | sdram_tmrbankmachine2_cmd_buffer3_source_ready);
assign sdram_tmrbankmachine2_tmrinput_control4 = (((slice_proxy462[0] & slice_proxy463[1]) | (slice_proxy464[1] & slice_proxy465[2])) | (slice_proxy466[0] & slice_proxy467[2]));

// synthesis translate_off
reg dummy_d_57;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine2_req_lock <= 1'd0;
	sdram_tmrbankmachine2_req_lock <= (sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine2_cmd_buffer_source_valid);
	sdram_tmrbankmachine2_req_lock <= sdram_tmrbankmachine2_tmrinput_control4;
// synthesis translate_off
	dummy_d_57 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine2_lookAddrVote_control = (((slice_proxy468[20:0] & slice_proxy469[41:21]) | (slice_proxy470[41:21] & slice_proxy471[62:42])) | (slice_proxy472[20:0] & slice_proxy473[62:42]));
assign sdram_tmrbankmachine2_bufAddrVote_control = (((slice_proxy474[20:0] & slice_proxy475[41:21]) | (slice_proxy476[41:21] & slice_proxy477[62:42])) | (slice_proxy478[20:0] & slice_proxy479[62:42]));
assign sdram_tmrbankmachine2_lookValidVote_control = (((slice_proxy480[0] & slice_proxy481[1]) | (slice_proxy482[1] & slice_proxy483[2])) | (slice_proxy484[0] & slice_proxy485[2]));
assign sdram_tmrbankmachine2_bufValidVote_control = (((slice_proxy486[0] & slice_proxy487[1]) | (slice_proxy488[1] & slice_proxy489[2])) | (slice_proxy490[0] & slice_proxy491[2]));
assign sdram_tmrbankmachine2_bufWeVote_control = (((slice_proxy492[0] & slice_proxy493[1]) | (slice_proxy494[1] & slice_proxy495[2])) | (slice_proxy496[0] & slice_proxy497[2]));
assign sdram_tmrbankmachine2_twtpVote_control = (((slice_proxy498[0] & slice_proxy499[1]) | (slice_proxy500[1] & slice_proxy501[2])) | (slice_proxy502[0] & slice_proxy503[2]));
assign sdram_tmrbankmachine2_trcVote_control = (((slice_proxy504[0] & slice_proxy505[1]) | (slice_proxy506[1] & slice_proxy507[2])) | (slice_proxy508[0] & slice_proxy509[2]));
assign sdram_tmrbankmachine2_trasVote_control = (((slice_proxy510[0] & slice_proxy511[1]) | (slice_proxy512[1] & slice_proxy513[2])) | (slice_proxy514[0] & slice_proxy515[2]));

// synthesis translate_off
reg dummy_d_58;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine2_req_wdata_ready <= 1'd0;
	sdram_tmrbankmachine2_req_rdata_valid <= 1'd0;
	sdram_tmrbankmachine2_refresh_gnt <= 1'd0;
	sdram_tmrbankmachine2_cmd_valid <= 1'd0;
	sdram_tmrbankmachine2_cmd_payload_cas <= 1'd0;
	sdram_tmrbankmachine2_cmd_payload_ras <= 1'd0;
	sdram_tmrbankmachine2_cmd_payload_we <= 1'd0;
	sdram_tmrbankmachine2_cmd_payload_is_cmd <= 1'd0;
	sdram_tmrbankmachine2_cmd_payload_is_read <= 1'd0;
	sdram_tmrbankmachine2_cmd_payload_is_write <= 1'd0;
	sdram_tmrbankmachine2_row_open <= 1'd0;
	sdram_tmrbankmachine2_row_close <= 1'd0;
	sdram_tmrbankmachine2_row_col_n_addr_sel <= 1'd0;
	tmrbankmachine2_next_state <= 4'd0;
	tmrbankmachine2_next_state <= tmrbankmachine2_state;
	case (tmrbankmachine2_state)
		1'd1: begin
			if ((sdram_tmrbankmachine2_twtpVote_control & sdram_tmrbankmachine2_trasVote_control)) begin
				sdram_tmrbankmachine2_cmd_valid <= 1'd1;
				if (sdram_tmrbankmachine2_cmd_ready) begin
					tmrbankmachine2_next_state <= 3'd5;
				end
				sdram_tmrbankmachine2_cmd_payload_ras <= 1'd1;
				sdram_tmrbankmachine2_cmd_payload_we <= 1'd1;
				sdram_tmrbankmachine2_cmd_payload_is_cmd <= 1'd1;
			end
			sdram_tmrbankmachine2_row_close <= 1'd1;
		end
		2'd2: begin
			if ((sdram_tmrbankmachine2_twtpVote_control & sdram_tmrbankmachine2_trasVote_control)) begin
				tmrbankmachine2_next_state <= 3'd5;
			end
			sdram_tmrbankmachine2_row_close <= 1'd1;
		end
		2'd3: begin
			if (sdram_tmrbankmachine2_trcVote_control) begin
				sdram_tmrbankmachine2_row_col_n_addr_sel <= 1'd1;
				sdram_tmrbankmachine2_row_open <= 1'd1;
				sdram_tmrbankmachine2_cmd_valid <= 1'd1;
				sdram_tmrbankmachine2_cmd_payload_is_cmd <= 1'd1;
				if (sdram_tmrbankmachine2_cmd_ready) begin
					tmrbankmachine2_next_state <= 3'd7;
				end
				sdram_tmrbankmachine2_cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			if (sdram_tmrbankmachine2_twtpVote_control) begin
				sdram_tmrbankmachine2_refresh_gnt <= 1'd1;
			end
			sdram_tmrbankmachine2_row_close <= 1'd1;
			sdram_tmrbankmachine2_cmd_payload_is_cmd <= 1'd1;
			if ((~sdram_tmrbankmachine2_refresh_req)) begin
				tmrbankmachine2_next_state <= 1'd0;
			end
		end
		3'd5: begin
			tmrbankmachine2_next_state <= 3'd6;
		end
		3'd6: begin
			tmrbankmachine2_next_state <= 2'd3;
		end
		3'd7: begin
			tmrbankmachine2_next_state <= 4'd8;
		end
		4'd8: begin
			tmrbankmachine2_next_state <= 1'd0;
		end
		default: begin
			if (sdram_tmrbankmachine2_refresh_req) begin
				tmrbankmachine2_next_state <= 3'd4;
			end else begin
				if (sdram_tmrbankmachine2_cmd_buffer_source_valid) begin
					if (sdram_tmrbankmachine2_row_opened) begin
						if (sdram_tmrbankmachine2_row_hit) begin
							sdram_tmrbankmachine2_cmd_valid <= 1'd1;
							if (sdram_tmrbankmachine2_cmd_buffer_source_payload_we) begin
								sdram_tmrbankmachine2_req_wdata_ready <= sdram_tmrbankmachine2_cmd_ready;
								sdram_tmrbankmachine2_cmd_payload_is_write <= 1'd1;
								sdram_tmrbankmachine2_cmd_payload_we <= 1'd1;
							end else begin
								sdram_tmrbankmachine2_req_rdata_valid <= sdram_tmrbankmachine2_cmd_ready;
								sdram_tmrbankmachine2_cmd_payload_is_read <= 1'd1;
							end
							sdram_tmrbankmachine2_cmd_payload_cas <= 1'd1;
							if ((sdram_tmrbankmachine2_cmd_ready & sdram_tmrbankmachine2_auto_precharge)) begin
								tmrbankmachine2_next_state <= 2'd2;
							end
						end else begin
							tmrbankmachine2_next_state <= 1'd1;
						end
					end else begin
						tmrbankmachine2_next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_58 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_valid = sdram_tmrbankmachine3_req_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_payload_we = sdram_tmrbankmachine3_req_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_payload_addr = sdram_tmrbankmachine3_req_addr;
assign sdram_tmrbankmachine3_cmd_buffer_sink_valid = sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_source_ready = sdram_tmrbankmachine3_cmd_buffer_sink_ready;
assign sdram_tmrbankmachine3_cmd_buffer_sink_first = sdram_tmrbankmachine3_cmd_buffer_lookahead_source_first;
assign sdram_tmrbankmachine3_cmd_buffer_sink_last = sdram_tmrbankmachine3_cmd_buffer_lookahead_source_last;
assign sdram_tmrbankmachine3_cmd_buffer_sink_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer_sink_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer_source_ready = (sdram_tmrbankmachine3_req_wdata_ready | sdram_tmrbankmachine3_req_rdata_valid);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_valid = sdram_tmrbankmachine3_req_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_payload_we = sdram_tmrbankmachine3_req_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_payload_addr = sdram_tmrbankmachine3_req_addr;
assign sdram_tmrbankmachine3_cmd_buffer2_sink_valid = sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_ready = sdram_tmrbankmachine3_cmd_buffer2_sink_ready;
assign sdram_tmrbankmachine3_cmd_buffer2_sink_first = sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_first;
assign sdram_tmrbankmachine3_cmd_buffer2_sink_last = sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_last;
assign sdram_tmrbankmachine3_cmd_buffer2_sink_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer2_sink_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer2_source_ready = (sdram_tmrbankmachine3_req_wdata_ready | sdram_tmrbankmachine3_req_rdata_valid);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_valid = sdram_tmrbankmachine3_req_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_payload_we = sdram_tmrbankmachine3_req_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_payload_addr = sdram_tmrbankmachine3_req_addr;
assign sdram_tmrbankmachine3_cmd_buffer3_sink_valid = sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_ready = sdram_tmrbankmachine3_cmd_buffer3_sink_ready;
assign sdram_tmrbankmachine3_cmd_buffer3_sink_first = sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_first;
assign sdram_tmrbankmachine3_cmd_buffer3_sink_last = sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_last;
assign sdram_tmrbankmachine3_cmd_buffer3_sink_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer3_sink_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer3_source_ready = (sdram_tmrbankmachine3_req_wdata_ready | sdram_tmrbankmachine3_req_rdata_valid);
assign sdram_tmrbankmachine3_req_ready = ((sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_ready & sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_ready) & sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_ready);
assign sdram_tmrbankmachine3_row_hit = (sdram_tmrbankmachine3_row == sdram_tmrbankmachine3_cmd_buffer_source_payload_addr[20:7]);
assign sdram_tmrbankmachine3_cmd_payload_ba = 2'd3;

// synthesis translate_off
reg dummy_d_59;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine3_cmd_payload_a <= 14'd0;
	if (sdram_tmrbankmachine3_row_col_n_addr_sel) begin
		sdram_tmrbankmachine3_cmd_payload_a <= sdram_tmrbankmachine3_cmd_buffer_source_payload_addr[20:7];
	end else begin
		sdram_tmrbankmachine3_cmd_payload_a <= ((sdram_tmrbankmachine3_auto_precharge <<< 4'd10) | {sdram_tmrbankmachine3_cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_59 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine3_twtpcon_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_cmd_payload_is_write);
assign sdram_tmrbankmachine3_twtpcon2_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_cmd_payload_is_write);
assign sdram_tmrbankmachine3_twtpcon3_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_cmd_payload_is_write);
assign sdram_tmrbankmachine3_trccon_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_row_open);
assign sdram_tmrbankmachine3_trccon2_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_row_open);
assign sdram_tmrbankmachine3_trccon3_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_row_open);
assign sdram_tmrbankmachine3_trascon_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_row_open);
assign sdram_tmrbankmachine3_trascon2_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_row_open);
assign sdram_tmrbankmachine3_trascon3_valid = ((sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_ready) & sdram_tmrbankmachine3_row_open);

// synthesis translate_off
reg dummy_d_60;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine3_auto_precharge <= 1'd0;
	if ((sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid & sdram_tmrbankmachine3_cmd_buffer_source_valid)) begin
		if ((sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr[20:7] != sdram_tmrbankmachine3_cmd_buffer_source_payload_addr[20:7])) begin
			sdram_tmrbankmachine3_auto_precharge <= (sdram_tmrbankmachine3_row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_60 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine3_TMRcmd_valid = {3{sdram_tmrbankmachine3_cmd_valid}};
assign sdram_tmrbankmachine3_TMRcmd_last = {3{sdram_tmrbankmachine3_cmd_last}};
assign sdram_tmrbankmachine3_TMRcmd_first = {3{sdram_tmrbankmachine3_cmd_first}};
assign sdram_tmrbankmachine3_tmrinput_control0 = (((sdram_tmrbankmachine3_TMRcmd_ready[0] & sdram_tmrbankmachine3_TMRcmd_ready[1]) | (sdram_tmrbankmachine3_TMRcmd_ready[1] & sdram_tmrbankmachine3_TMRcmd_ready[2])) | (sdram_tmrbankmachine3_TMRcmd_ready[0] & sdram_tmrbankmachine3_TMRcmd_ready[2]));
assign sdram_tmrbankmachine3_cmd_ready = sdram_tmrbankmachine3_tmrinput_control0;
assign sdram_tmrbankmachine3_TMRcmd_payload_a = {3{sdram_tmrbankmachine3_cmd_payload_a}};
assign sdram_tmrbankmachine3_TMRcmd_payload_ba = {3{sdram_tmrbankmachine3_cmd_payload_ba}};
assign sdram_tmrbankmachine3_TMRcmd_payload_cas = {3{sdram_tmrbankmachine3_cmd_payload_cas}};
assign sdram_tmrbankmachine3_TMRcmd_payload_ras = {3{sdram_tmrbankmachine3_cmd_payload_ras}};
assign sdram_tmrbankmachine3_TMRcmd_payload_we = {3{sdram_tmrbankmachine3_cmd_payload_we}};
assign sdram_tmrbankmachine3_TMRcmd_payload_is_cmd = {3{sdram_tmrbankmachine3_cmd_payload_is_cmd}};
assign sdram_tmrbankmachine3_TMRcmd_payload_is_read = {3{sdram_tmrbankmachine3_cmd_payload_is_read}};
assign sdram_tmrbankmachine3_TMRcmd_payload_is_write = {3{sdram_tmrbankmachine3_cmd_payload_is_write}};
assign sdram_tmrbankmachine3_tmrinput_control1 = (((sdram_tmrbankmachine3_TMRreq_valid[0] & sdram_tmrbankmachine3_TMRreq_valid[1]) | (sdram_tmrbankmachine3_TMRreq_valid[1] & sdram_tmrbankmachine3_TMRreq_valid[2])) | (sdram_tmrbankmachine3_TMRreq_valid[0] & sdram_tmrbankmachine3_TMRreq_valid[2]));
assign sdram_tmrbankmachine3_req_valid = sdram_tmrbankmachine3_tmrinput_control1;
assign sdram_tmrbankmachine3_TMRreq_ready = {3{sdram_tmrbankmachine3_req_ready}};
assign sdram_tmrbankmachine3_tmrinput_control2 = (((sdram_tmrbankmachine3_TMRreq_we[0] & sdram_tmrbankmachine3_TMRreq_we[1]) | (sdram_tmrbankmachine3_TMRreq_we[1] & sdram_tmrbankmachine3_TMRreq_we[2])) | (sdram_tmrbankmachine3_TMRreq_we[0] & sdram_tmrbankmachine3_TMRreq_we[2]));
assign sdram_tmrbankmachine3_req_we = sdram_tmrbankmachine3_tmrinput_control2;
assign sdram_tmrbankmachine3_tmrinput_control3 = (((sdram_tmrbankmachine3_TMRreq_addr[20:0] & sdram_tmrbankmachine3_TMRreq_addr[41:21]) | (sdram_tmrbankmachine3_TMRreq_addr[41:21] & sdram_tmrbankmachine3_TMRreq_addr[62:42])) | (sdram_tmrbankmachine3_TMRreq_addr[20:0] & sdram_tmrbankmachine3_TMRreq_addr[62:42]));
assign sdram_tmrbankmachine3_req_addr = sdram_tmrbankmachine3_tmrinput_control3;
assign sdram_tmrbankmachine3_TMRreq_lock = {3{sdram_tmrbankmachine3_req_lock}};
assign sdram_tmrbankmachine3_TMRreq_wdata_ready = {3{sdram_tmrbankmachine3_req_wdata_ready}};
assign sdram_tmrbankmachine3_TMRreq_rdata_valid = {3{sdram_tmrbankmachine3_req_rdata_valid}};
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_din = {sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_last, sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_first, sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_payload_we};
assign {sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_last, sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_first, sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_payload_we} = sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_dout;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_ready = sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_writable;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_we = sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_first = sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_first;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_last = sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_last;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_in_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead_sink_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid = sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_readable;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_source_first = sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_first;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_source_last = sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_last;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead_fifo_out_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_re = sdram_tmrbankmachine3_cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_61;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead_replace) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_adr <= (sdram_tmrbankmachine3_cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_adr <= sdram_tmrbankmachine3_cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_61 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_dat_w = sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_din;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_we = (sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_we & (sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_writable | sdram_tmrbankmachine3_cmd_buffer_lookahead_replace));
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_do_read = (sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_readable & sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_re);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_rdport_adr = sdram_tmrbankmachine3_cmd_buffer_lookahead_consume;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_dout = sdram_tmrbankmachine3_cmd_buffer_lookahead_rdport_dat_r;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_writable = (sdram_tmrbankmachine3_cmd_buffer_lookahead_level != 4'd8);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_readable = (sdram_tmrbankmachine3_cmd_buffer_lookahead_level != 1'd0);
assign sdram_tmrbankmachine3_cmd_buffer_sink_ready = ((~sdram_tmrbankmachine3_cmd_buffer_source_valid) | sdram_tmrbankmachine3_cmd_buffer_source_ready);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_din = {sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_last, sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_first, sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_payload_we};
assign {sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_last, sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_first, sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_payload_we} = sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_dout;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_ready = sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_writable;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_we = sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_first = sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_first;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_last = sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_last;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_in_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead2_sink_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid = sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_readable;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_first = sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_first;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_last = sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_last;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead2_fifo_out_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_re = sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_62;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead2_replace) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_adr <= (sdram_tmrbankmachine3_cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_adr <= sdram_tmrbankmachine3_cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_62 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_dat_w = sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_din;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_we = (sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_we & (sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_writable | sdram_tmrbankmachine3_cmd_buffer_lookahead2_replace));
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_do_read = (sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_readable & sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_re);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_rdport_adr = sdram_tmrbankmachine3_cmd_buffer_lookahead2_consume;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_dout = sdram_tmrbankmachine3_cmd_buffer_lookahead2_rdport_dat_r;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_writable = (sdram_tmrbankmachine3_cmd_buffer_lookahead2_level != 4'd8);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_readable = (sdram_tmrbankmachine3_cmd_buffer_lookahead2_level != 1'd0);
assign sdram_tmrbankmachine3_cmd_buffer2_sink_ready = ((~sdram_tmrbankmachine3_cmd_buffer2_source_valid) | sdram_tmrbankmachine3_cmd_buffer2_source_ready);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_din = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_last, sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_first, sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_payload_we};
assign {sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_last, sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_first, sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_payload_we} = sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_dout;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_ready = sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_writable;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_we = sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_valid;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_first = sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_first;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_last = sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_last;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_in_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead3_sink_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid = sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_readable;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_first = sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_first;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_last = sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_last;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_we = sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_payload_we;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr = sdram_tmrbankmachine3_cmd_buffer_lookahead3_fifo_out_payload_addr;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_re = sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_63;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead3_replace) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_adr <= (sdram_tmrbankmachine3_cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_adr <= sdram_tmrbankmachine3_cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_63 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_dat_w = sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_din;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_we = (sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_we & (sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_writable | sdram_tmrbankmachine3_cmd_buffer_lookahead3_replace));
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_do_read = (sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_readable & sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_re);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_rdport_adr = sdram_tmrbankmachine3_cmd_buffer_lookahead3_consume;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_dout = sdram_tmrbankmachine3_cmd_buffer_lookahead3_rdport_dat_r;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_writable = (sdram_tmrbankmachine3_cmd_buffer_lookahead3_level != 4'd8);
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_readable = (sdram_tmrbankmachine3_cmd_buffer_lookahead3_level != 1'd0);
assign sdram_tmrbankmachine3_cmd_buffer3_sink_ready = ((~sdram_tmrbankmachine3_cmd_buffer3_source_valid) | sdram_tmrbankmachine3_cmd_buffer3_source_ready);
assign sdram_tmrbankmachine3_tmrinput_control4 = (((slice_proxy516[0] & slice_proxy517[1]) | (slice_proxy518[1] & slice_proxy519[2])) | (slice_proxy520[0] & slice_proxy521[2]));

// synthesis translate_off
reg dummy_d_64;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine3_req_lock <= 1'd0;
	sdram_tmrbankmachine3_req_lock <= (sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine3_cmd_buffer_source_valid);
	sdram_tmrbankmachine3_req_lock <= sdram_tmrbankmachine3_tmrinput_control4;
// synthesis translate_off
	dummy_d_64 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine3_lookAddrVote_control = (((slice_proxy522[20:0] & slice_proxy523[41:21]) | (slice_proxy524[41:21] & slice_proxy525[62:42])) | (slice_proxy526[20:0] & slice_proxy527[62:42]));
assign sdram_tmrbankmachine3_bufAddrVote_control = (((slice_proxy528[20:0] & slice_proxy529[41:21]) | (slice_proxy530[41:21] & slice_proxy531[62:42])) | (slice_proxy532[20:0] & slice_proxy533[62:42]));
assign sdram_tmrbankmachine3_lookValidVote_control = (((slice_proxy534[0] & slice_proxy535[1]) | (slice_proxy536[1] & slice_proxy537[2])) | (slice_proxy538[0] & slice_proxy539[2]));
assign sdram_tmrbankmachine3_bufValidVote_control = (((slice_proxy540[0] & slice_proxy541[1]) | (slice_proxy542[1] & slice_proxy543[2])) | (slice_proxy544[0] & slice_proxy545[2]));
assign sdram_tmrbankmachine3_bufWeVote_control = (((slice_proxy546[0] & slice_proxy547[1]) | (slice_proxy548[1] & slice_proxy549[2])) | (slice_proxy550[0] & slice_proxy551[2]));
assign sdram_tmrbankmachine3_twtpVote_control = (((slice_proxy552[0] & slice_proxy553[1]) | (slice_proxy554[1] & slice_proxy555[2])) | (slice_proxy556[0] & slice_proxy557[2]));
assign sdram_tmrbankmachine3_trcVote_control = (((slice_proxy558[0] & slice_proxy559[1]) | (slice_proxy560[1] & slice_proxy561[2])) | (slice_proxy562[0] & slice_proxy563[2]));
assign sdram_tmrbankmachine3_trasVote_control = (((slice_proxy564[0] & slice_proxy565[1]) | (slice_proxy566[1] & slice_proxy567[2])) | (slice_proxy568[0] & slice_proxy569[2]));

// synthesis translate_off
reg dummy_d_65;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine3_req_wdata_ready <= 1'd0;
	sdram_tmrbankmachine3_req_rdata_valid <= 1'd0;
	sdram_tmrbankmachine3_refresh_gnt <= 1'd0;
	sdram_tmrbankmachine3_cmd_valid <= 1'd0;
	sdram_tmrbankmachine3_cmd_payload_cas <= 1'd0;
	sdram_tmrbankmachine3_cmd_payload_ras <= 1'd0;
	sdram_tmrbankmachine3_cmd_payload_we <= 1'd0;
	sdram_tmrbankmachine3_cmd_payload_is_cmd <= 1'd0;
	sdram_tmrbankmachine3_cmd_payload_is_read <= 1'd0;
	sdram_tmrbankmachine3_cmd_payload_is_write <= 1'd0;
	sdram_tmrbankmachine3_row_open <= 1'd0;
	sdram_tmrbankmachine3_row_close <= 1'd0;
	sdram_tmrbankmachine3_row_col_n_addr_sel <= 1'd0;
	tmrbankmachine3_next_state <= 4'd0;
	tmrbankmachine3_next_state <= tmrbankmachine3_state;
	case (tmrbankmachine3_state)
		1'd1: begin
			if ((sdram_tmrbankmachine3_twtpVote_control & sdram_tmrbankmachine3_trasVote_control)) begin
				sdram_tmrbankmachine3_cmd_valid <= 1'd1;
				if (sdram_tmrbankmachine3_cmd_ready) begin
					tmrbankmachine3_next_state <= 3'd5;
				end
				sdram_tmrbankmachine3_cmd_payload_ras <= 1'd1;
				sdram_tmrbankmachine3_cmd_payload_we <= 1'd1;
				sdram_tmrbankmachine3_cmd_payload_is_cmd <= 1'd1;
			end
			sdram_tmrbankmachine3_row_close <= 1'd1;
		end
		2'd2: begin
			if ((sdram_tmrbankmachine3_twtpVote_control & sdram_tmrbankmachine3_trasVote_control)) begin
				tmrbankmachine3_next_state <= 3'd5;
			end
			sdram_tmrbankmachine3_row_close <= 1'd1;
		end
		2'd3: begin
			if (sdram_tmrbankmachine3_trcVote_control) begin
				sdram_tmrbankmachine3_row_col_n_addr_sel <= 1'd1;
				sdram_tmrbankmachine3_row_open <= 1'd1;
				sdram_tmrbankmachine3_cmd_valid <= 1'd1;
				sdram_tmrbankmachine3_cmd_payload_is_cmd <= 1'd1;
				if (sdram_tmrbankmachine3_cmd_ready) begin
					tmrbankmachine3_next_state <= 3'd7;
				end
				sdram_tmrbankmachine3_cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			if (sdram_tmrbankmachine3_twtpVote_control) begin
				sdram_tmrbankmachine3_refresh_gnt <= 1'd1;
			end
			sdram_tmrbankmachine3_row_close <= 1'd1;
			sdram_tmrbankmachine3_cmd_payload_is_cmd <= 1'd1;
			if ((~sdram_tmrbankmachine3_refresh_req)) begin
				tmrbankmachine3_next_state <= 1'd0;
			end
		end
		3'd5: begin
			tmrbankmachine3_next_state <= 3'd6;
		end
		3'd6: begin
			tmrbankmachine3_next_state <= 2'd3;
		end
		3'd7: begin
			tmrbankmachine3_next_state <= 4'd8;
		end
		4'd8: begin
			tmrbankmachine3_next_state <= 1'd0;
		end
		default: begin
			if (sdram_tmrbankmachine3_refresh_req) begin
				tmrbankmachine3_next_state <= 3'd4;
			end else begin
				if (sdram_tmrbankmachine3_cmd_buffer_source_valid) begin
					if (sdram_tmrbankmachine3_row_opened) begin
						if (sdram_tmrbankmachine3_row_hit) begin
							sdram_tmrbankmachine3_cmd_valid <= 1'd1;
							if (sdram_tmrbankmachine3_cmd_buffer_source_payload_we) begin
								sdram_tmrbankmachine3_req_wdata_ready <= sdram_tmrbankmachine3_cmd_ready;
								sdram_tmrbankmachine3_cmd_payload_is_write <= 1'd1;
								sdram_tmrbankmachine3_cmd_payload_we <= 1'd1;
							end else begin
								sdram_tmrbankmachine3_req_rdata_valid <= sdram_tmrbankmachine3_cmd_ready;
								sdram_tmrbankmachine3_cmd_payload_is_read <= 1'd1;
							end
							sdram_tmrbankmachine3_cmd_payload_cas <= 1'd1;
							if ((sdram_tmrbankmachine3_cmd_ready & sdram_tmrbankmachine3_auto_precharge)) begin
								tmrbankmachine3_next_state <= 2'd2;
							end
						end else begin
							tmrbankmachine3_next_state <= 1'd1;
						end
					end else begin
						tmrbankmachine3_next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_65 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_valid = sdram_tmrbankmachine4_req_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_payload_we = sdram_tmrbankmachine4_req_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_payload_addr = sdram_tmrbankmachine4_req_addr;
assign sdram_tmrbankmachine4_cmd_buffer_sink_valid = sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_source_ready = sdram_tmrbankmachine4_cmd_buffer_sink_ready;
assign sdram_tmrbankmachine4_cmd_buffer_sink_first = sdram_tmrbankmachine4_cmd_buffer_lookahead_source_first;
assign sdram_tmrbankmachine4_cmd_buffer_sink_last = sdram_tmrbankmachine4_cmd_buffer_lookahead_source_last;
assign sdram_tmrbankmachine4_cmd_buffer_sink_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer_sink_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer_source_ready = (sdram_tmrbankmachine4_req_wdata_ready | sdram_tmrbankmachine4_req_rdata_valid);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_valid = sdram_tmrbankmachine4_req_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_payload_we = sdram_tmrbankmachine4_req_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_payload_addr = sdram_tmrbankmachine4_req_addr;
assign sdram_tmrbankmachine4_cmd_buffer2_sink_valid = sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_ready = sdram_tmrbankmachine4_cmd_buffer2_sink_ready;
assign sdram_tmrbankmachine4_cmd_buffer2_sink_first = sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_first;
assign sdram_tmrbankmachine4_cmd_buffer2_sink_last = sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_last;
assign sdram_tmrbankmachine4_cmd_buffer2_sink_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer2_sink_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer2_source_ready = (sdram_tmrbankmachine4_req_wdata_ready | sdram_tmrbankmachine4_req_rdata_valid);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_valid = sdram_tmrbankmachine4_req_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_payload_we = sdram_tmrbankmachine4_req_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_payload_addr = sdram_tmrbankmachine4_req_addr;
assign sdram_tmrbankmachine4_cmd_buffer3_sink_valid = sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_ready = sdram_tmrbankmachine4_cmd_buffer3_sink_ready;
assign sdram_tmrbankmachine4_cmd_buffer3_sink_first = sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_first;
assign sdram_tmrbankmachine4_cmd_buffer3_sink_last = sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_last;
assign sdram_tmrbankmachine4_cmd_buffer3_sink_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer3_sink_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer3_source_ready = (sdram_tmrbankmachine4_req_wdata_ready | sdram_tmrbankmachine4_req_rdata_valid);
assign sdram_tmrbankmachine4_req_ready = ((sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_ready & sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_ready) & sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_ready);
assign sdram_tmrbankmachine4_row_hit = (sdram_tmrbankmachine4_row == sdram_tmrbankmachine4_cmd_buffer_source_payload_addr[20:7]);
assign sdram_tmrbankmachine4_cmd_payload_ba = 3'd4;

// synthesis translate_off
reg dummy_d_66;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine4_cmd_payload_a <= 14'd0;
	if (sdram_tmrbankmachine4_row_col_n_addr_sel) begin
		sdram_tmrbankmachine4_cmd_payload_a <= sdram_tmrbankmachine4_cmd_buffer_source_payload_addr[20:7];
	end else begin
		sdram_tmrbankmachine4_cmd_payload_a <= ((sdram_tmrbankmachine4_auto_precharge <<< 4'd10) | {sdram_tmrbankmachine4_cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_66 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine4_twtpcon_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_cmd_payload_is_write);
assign sdram_tmrbankmachine4_twtpcon2_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_cmd_payload_is_write);
assign sdram_tmrbankmachine4_twtpcon3_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_cmd_payload_is_write);
assign sdram_tmrbankmachine4_trccon_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_row_open);
assign sdram_tmrbankmachine4_trccon2_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_row_open);
assign sdram_tmrbankmachine4_trccon3_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_row_open);
assign sdram_tmrbankmachine4_trascon_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_row_open);
assign sdram_tmrbankmachine4_trascon2_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_row_open);
assign sdram_tmrbankmachine4_trascon3_valid = ((sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_ready) & sdram_tmrbankmachine4_row_open);

// synthesis translate_off
reg dummy_d_67;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine4_auto_precharge <= 1'd0;
	if ((sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid & sdram_tmrbankmachine4_cmd_buffer_source_valid)) begin
		if ((sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr[20:7] != sdram_tmrbankmachine4_cmd_buffer_source_payload_addr[20:7])) begin
			sdram_tmrbankmachine4_auto_precharge <= (sdram_tmrbankmachine4_row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_67 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine4_TMRcmd_valid = {3{sdram_tmrbankmachine4_cmd_valid}};
assign sdram_tmrbankmachine4_TMRcmd_last = {3{sdram_tmrbankmachine4_cmd_last}};
assign sdram_tmrbankmachine4_TMRcmd_first = {3{sdram_tmrbankmachine4_cmd_first}};
assign sdram_tmrbankmachine4_tmrinput_control0 = (((sdram_tmrbankmachine4_TMRcmd_ready[0] & sdram_tmrbankmachine4_TMRcmd_ready[1]) | (sdram_tmrbankmachine4_TMRcmd_ready[1] & sdram_tmrbankmachine4_TMRcmd_ready[2])) | (sdram_tmrbankmachine4_TMRcmd_ready[0] & sdram_tmrbankmachine4_TMRcmd_ready[2]));
assign sdram_tmrbankmachine4_cmd_ready = sdram_tmrbankmachine4_tmrinput_control0;
assign sdram_tmrbankmachine4_TMRcmd_payload_a = {3{sdram_tmrbankmachine4_cmd_payload_a}};
assign sdram_tmrbankmachine4_TMRcmd_payload_ba = {3{sdram_tmrbankmachine4_cmd_payload_ba}};
assign sdram_tmrbankmachine4_TMRcmd_payload_cas = {3{sdram_tmrbankmachine4_cmd_payload_cas}};
assign sdram_tmrbankmachine4_TMRcmd_payload_ras = {3{sdram_tmrbankmachine4_cmd_payload_ras}};
assign sdram_tmrbankmachine4_TMRcmd_payload_we = {3{sdram_tmrbankmachine4_cmd_payload_we}};
assign sdram_tmrbankmachine4_TMRcmd_payload_is_cmd = {3{sdram_tmrbankmachine4_cmd_payload_is_cmd}};
assign sdram_tmrbankmachine4_TMRcmd_payload_is_read = {3{sdram_tmrbankmachine4_cmd_payload_is_read}};
assign sdram_tmrbankmachine4_TMRcmd_payload_is_write = {3{sdram_tmrbankmachine4_cmd_payload_is_write}};
assign sdram_tmrbankmachine4_tmrinput_control1 = (((sdram_tmrbankmachine4_TMRreq_valid[0] & sdram_tmrbankmachine4_TMRreq_valid[1]) | (sdram_tmrbankmachine4_TMRreq_valid[1] & sdram_tmrbankmachine4_TMRreq_valid[2])) | (sdram_tmrbankmachine4_TMRreq_valid[0] & sdram_tmrbankmachine4_TMRreq_valid[2]));
assign sdram_tmrbankmachine4_req_valid = sdram_tmrbankmachine4_tmrinput_control1;
assign sdram_tmrbankmachine4_TMRreq_ready = {3{sdram_tmrbankmachine4_req_ready}};
assign sdram_tmrbankmachine4_tmrinput_control2 = (((sdram_tmrbankmachine4_TMRreq_we[0] & sdram_tmrbankmachine4_TMRreq_we[1]) | (sdram_tmrbankmachine4_TMRreq_we[1] & sdram_tmrbankmachine4_TMRreq_we[2])) | (sdram_tmrbankmachine4_TMRreq_we[0] & sdram_tmrbankmachine4_TMRreq_we[2]));
assign sdram_tmrbankmachine4_req_we = sdram_tmrbankmachine4_tmrinput_control2;
assign sdram_tmrbankmachine4_tmrinput_control3 = (((sdram_tmrbankmachine4_TMRreq_addr[20:0] & sdram_tmrbankmachine4_TMRreq_addr[41:21]) | (sdram_tmrbankmachine4_TMRreq_addr[41:21] & sdram_tmrbankmachine4_TMRreq_addr[62:42])) | (sdram_tmrbankmachine4_TMRreq_addr[20:0] & sdram_tmrbankmachine4_TMRreq_addr[62:42]));
assign sdram_tmrbankmachine4_req_addr = sdram_tmrbankmachine4_tmrinput_control3;
assign sdram_tmrbankmachine4_TMRreq_lock = {3{sdram_tmrbankmachine4_req_lock}};
assign sdram_tmrbankmachine4_TMRreq_wdata_ready = {3{sdram_tmrbankmachine4_req_wdata_ready}};
assign sdram_tmrbankmachine4_TMRreq_rdata_valid = {3{sdram_tmrbankmachine4_req_rdata_valid}};
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_din = {sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_last, sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_first, sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_payload_we};
assign {sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_last, sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_first, sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_payload_we} = sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_dout;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_ready = sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_writable;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_we = sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_first = sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_first;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_last = sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_last;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_in_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead_sink_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid = sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_readable;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_source_first = sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_first;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_source_last = sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_last;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead_fifo_out_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_re = sdram_tmrbankmachine4_cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_68;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead_replace) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_adr <= (sdram_tmrbankmachine4_cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_adr <= sdram_tmrbankmachine4_cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_68 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_dat_w = sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_din;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_we = (sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_we & (sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_writable | sdram_tmrbankmachine4_cmd_buffer_lookahead_replace));
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_do_read = (sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_readable & sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_re);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_rdport_adr = sdram_tmrbankmachine4_cmd_buffer_lookahead_consume;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_dout = sdram_tmrbankmachine4_cmd_buffer_lookahead_rdport_dat_r;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_writable = (sdram_tmrbankmachine4_cmd_buffer_lookahead_level != 4'd8);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_readable = (sdram_tmrbankmachine4_cmd_buffer_lookahead_level != 1'd0);
assign sdram_tmrbankmachine4_cmd_buffer_sink_ready = ((~sdram_tmrbankmachine4_cmd_buffer_source_valid) | sdram_tmrbankmachine4_cmd_buffer_source_ready);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_din = {sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_last, sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_first, sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_payload_we};
assign {sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_last, sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_first, sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_payload_we} = sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_dout;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_ready = sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_writable;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_we = sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_first = sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_first;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_last = sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_last;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_in_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead2_sink_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid = sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_readable;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_first = sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_first;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_last = sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_last;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead2_fifo_out_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_re = sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_69;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead2_replace) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_adr <= (sdram_tmrbankmachine4_cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_adr <= sdram_tmrbankmachine4_cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_69 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_dat_w = sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_din;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_we = (sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_we & (sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_writable | sdram_tmrbankmachine4_cmd_buffer_lookahead2_replace));
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_do_read = (sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_readable & sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_re);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_rdport_adr = sdram_tmrbankmachine4_cmd_buffer_lookahead2_consume;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_dout = sdram_tmrbankmachine4_cmd_buffer_lookahead2_rdport_dat_r;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_writable = (sdram_tmrbankmachine4_cmd_buffer_lookahead2_level != 4'd8);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_readable = (sdram_tmrbankmachine4_cmd_buffer_lookahead2_level != 1'd0);
assign sdram_tmrbankmachine4_cmd_buffer2_sink_ready = ((~sdram_tmrbankmachine4_cmd_buffer2_source_valid) | sdram_tmrbankmachine4_cmd_buffer2_source_ready);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_din = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_last, sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_first, sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_payload_we};
assign {sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_last, sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_first, sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_payload_we} = sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_dout;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_ready = sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_writable;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_we = sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_valid;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_first = sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_first;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_last = sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_last;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_in_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead3_sink_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid = sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_readable;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_first = sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_first;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_last = sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_last;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_we = sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_payload_we;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr = sdram_tmrbankmachine4_cmd_buffer_lookahead3_fifo_out_payload_addr;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_re = sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_70;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead3_replace) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_adr <= (sdram_tmrbankmachine4_cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_adr <= sdram_tmrbankmachine4_cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_70 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_dat_w = sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_din;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_we = (sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_we & (sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_writable | sdram_tmrbankmachine4_cmd_buffer_lookahead3_replace));
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_do_read = (sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_readable & sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_re);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_rdport_adr = sdram_tmrbankmachine4_cmd_buffer_lookahead3_consume;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_dout = sdram_tmrbankmachine4_cmd_buffer_lookahead3_rdport_dat_r;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_writable = (sdram_tmrbankmachine4_cmd_buffer_lookahead3_level != 4'd8);
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_readable = (sdram_tmrbankmachine4_cmd_buffer_lookahead3_level != 1'd0);
assign sdram_tmrbankmachine4_cmd_buffer3_sink_ready = ((~sdram_tmrbankmachine4_cmd_buffer3_source_valid) | sdram_tmrbankmachine4_cmd_buffer3_source_ready);
assign sdram_tmrbankmachine4_tmrinput_control4 = (((slice_proxy570[0] & slice_proxy571[1]) | (slice_proxy572[1] & slice_proxy573[2])) | (slice_proxy574[0] & slice_proxy575[2]));

// synthesis translate_off
reg dummy_d_71;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine4_req_lock <= 1'd0;
	sdram_tmrbankmachine4_req_lock <= (sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine4_cmd_buffer_source_valid);
	sdram_tmrbankmachine4_req_lock <= sdram_tmrbankmachine4_tmrinput_control4;
// synthesis translate_off
	dummy_d_71 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine4_lookAddrVote_control = (((slice_proxy576[20:0] & slice_proxy577[41:21]) | (slice_proxy578[41:21] & slice_proxy579[62:42])) | (slice_proxy580[20:0] & slice_proxy581[62:42]));
assign sdram_tmrbankmachine4_bufAddrVote_control = (((slice_proxy582[20:0] & slice_proxy583[41:21]) | (slice_proxy584[41:21] & slice_proxy585[62:42])) | (slice_proxy586[20:0] & slice_proxy587[62:42]));
assign sdram_tmrbankmachine4_lookValidVote_control = (((slice_proxy588[0] & slice_proxy589[1]) | (slice_proxy590[1] & slice_proxy591[2])) | (slice_proxy592[0] & slice_proxy593[2]));
assign sdram_tmrbankmachine4_bufValidVote_control = (((slice_proxy594[0] & slice_proxy595[1]) | (slice_proxy596[1] & slice_proxy597[2])) | (slice_proxy598[0] & slice_proxy599[2]));
assign sdram_tmrbankmachine4_bufWeVote_control = (((slice_proxy600[0] & slice_proxy601[1]) | (slice_proxy602[1] & slice_proxy603[2])) | (slice_proxy604[0] & slice_proxy605[2]));
assign sdram_tmrbankmachine4_twtpVote_control = (((slice_proxy606[0] & slice_proxy607[1]) | (slice_proxy608[1] & slice_proxy609[2])) | (slice_proxy610[0] & slice_proxy611[2]));
assign sdram_tmrbankmachine4_trcVote_control = (((slice_proxy612[0] & slice_proxy613[1]) | (slice_proxy614[1] & slice_proxy615[2])) | (slice_proxy616[0] & slice_proxy617[2]));
assign sdram_tmrbankmachine4_trasVote_control = (((slice_proxy618[0] & slice_proxy619[1]) | (slice_proxy620[1] & slice_proxy621[2])) | (slice_proxy622[0] & slice_proxy623[2]));

// synthesis translate_off
reg dummy_d_72;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine4_req_wdata_ready <= 1'd0;
	sdram_tmrbankmachine4_req_rdata_valid <= 1'd0;
	sdram_tmrbankmachine4_refresh_gnt <= 1'd0;
	sdram_tmrbankmachine4_cmd_valid <= 1'd0;
	sdram_tmrbankmachine4_cmd_payload_cas <= 1'd0;
	sdram_tmrbankmachine4_cmd_payload_ras <= 1'd0;
	sdram_tmrbankmachine4_cmd_payload_we <= 1'd0;
	sdram_tmrbankmachine4_cmd_payload_is_cmd <= 1'd0;
	sdram_tmrbankmachine4_cmd_payload_is_read <= 1'd0;
	sdram_tmrbankmachine4_cmd_payload_is_write <= 1'd0;
	sdram_tmrbankmachine4_row_open <= 1'd0;
	sdram_tmrbankmachine4_row_close <= 1'd0;
	sdram_tmrbankmachine4_row_col_n_addr_sel <= 1'd0;
	tmrbankmachine4_next_state <= 4'd0;
	tmrbankmachine4_next_state <= tmrbankmachine4_state;
	case (tmrbankmachine4_state)
		1'd1: begin
			if ((sdram_tmrbankmachine4_twtpVote_control & sdram_tmrbankmachine4_trasVote_control)) begin
				sdram_tmrbankmachine4_cmd_valid <= 1'd1;
				if (sdram_tmrbankmachine4_cmd_ready) begin
					tmrbankmachine4_next_state <= 3'd5;
				end
				sdram_tmrbankmachine4_cmd_payload_ras <= 1'd1;
				sdram_tmrbankmachine4_cmd_payload_we <= 1'd1;
				sdram_tmrbankmachine4_cmd_payload_is_cmd <= 1'd1;
			end
			sdram_tmrbankmachine4_row_close <= 1'd1;
		end
		2'd2: begin
			if ((sdram_tmrbankmachine4_twtpVote_control & sdram_tmrbankmachine4_trasVote_control)) begin
				tmrbankmachine4_next_state <= 3'd5;
			end
			sdram_tmrbankmachine4_row_close <= 1'd1;
		end
		2'd3: begin
			if (sdram_tmrbankmachine4_trcVote_control) begin
				sdram_tmrbankmachine4_row_col_n_addr_sel <= 1'd1;
				sdram_tmrbankmachine4_row_open <= 1'd1;
				sdram_tmrbankmachine4_cmd_valid <= 1'd1;
				sdram_tmrbankmachine4_cmd_payload_is_cmd <= 1'd1;
				if (sdram_tmrbankmachine4_cmd_ready) begin
					tmrbankmachine4_next_state <= 3'd7;
				end
				sdram_tmrbankmachine4_cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			if (sdram_tmrbankmachine4_twtpVote_control) begin
				sdram_tmrbankmachine4_refresh_gnt <= 1'd1;
			end
			sdram_tmrbankmachine4_row_close <= 1'd1;
			sdram_tmrbankmachine4_cmd_payload_is_cmd <= 1'd1;
			if ((~sdram_tmrbankmachine4_refresh_req)) begin
				tmrbankmachine4_next_state <= 1'd0;
			end
		end
		3'd5: begin
			tmrbankmachine4_next_state <= 3'd6;
		end
		3'd6: begin
			tmrbankmachine4_next_state <= 2'd3;
		end
		3'd7: begin
			tmrbankmachine4_next_state <= 4'd8;
		end
		4'd8: begin
			tmrbankmachine4_next_state <= 1'd0;
		end
		default: begin
			if (sdram_tmrbankmachine4_refresh_req) begin
				tmrbankmachine4_next_state <= 3'd4;
			end else begin
				if (sdram_tmrbankmachine4_cmd_buffer_source_valid) begin
					if (sdram_tmrbankmachine4_row_opened) begin
						if (sdram_tmrbankmachine4_row_hit) begin
							sdram_tmrbankmachine4_cmd_valid <= 1'd1;
							if (sdram_tmrbankmachine4_cmd_buffer_source_payload_we) begin
								sdram_tmrbankmachine4_req_wdata_ready <= sdram_tmrbankmachine4_cmd_ready;
								sdram_tmrbankmachine4_cmd_payload_is_write <= 1'd1;
								sdram_tmrbankmachine4_cmd_payload_we <= 1'd1;
							end else begin
								sdram_tmrbankmachine4_req_rdata_valid <= sdram_tmrbankmachine4_cmd_ready;
								sdram_tmrbankmachine4_cmd_payload_is_read <= 1'd1;
							end
							sdram_tmrbankmachine4_cmd_payload_cas <= 1'd1;
							if ((sdram_tmrbankmachine4_cmd_ready & sdram_tmrbankmachine4_auto_precharge)) begin
								tmrbankmachine4_next_state <= 2'd2;
							end
						end else begin
							tmrbankmachine4_next_state <= 1'd1;
						end
					end else begin
						tmrbankmachine4_next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_72 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_valid = sdram_tmrbankmachine5_req_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_payload_we = sdram_tmrbankmachine5_req_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_payload_addr = sdram_tmrbankmachine5_req_addr;
assign sdram_tmrbankmachine5_cmd_buffer_sink_valid = sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_source_ready = sdram_tmrbankmachine5_cmd_buffer_sink_ready;
assign sdram_tmrbankmachine5_cmd_buffer_sink_first = sdram_tmrbankmachine5_cmd_buffer_lookahead_source_first;
assign sdram_tmrbankmachine5_cmd_buffer_sink_last = sdram_tmrbankmachine5_cmd_buffer_lookahead_source_last;
assign sdram_tmrbankmachine5_cmd_buffer_sink_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer_sink_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer_source_ready = (sdram_tmrbankmachine5_req_wdata_ready | sdram_tmrbankmachine5_req_rdata_valid);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_valid = sdram_tmrbankmachine5_req_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_payload_we = sdram_tmrbankmachine5_req_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_payload_addr = sdram_tmrbankmachine5_req_addr;
assign sdram_tmrbankmachine5_cmd_buffer2_sink_valid = sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_ready = sdram_tmrbankmachine5_cmd_buffer2_sink_ready;
assign sdram_tmrbankmachine5_cmd_buffer2_sink_first = sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_first;
assign sdram_tmrbankmachine5_cmd_buffer2_sink_last = sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_last;
assign sdram_tmrbankmachine5_cmd_buffer2_sink_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer2_sink_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer2_source_ready = (sdram_tmrbankmachine5_req_wdata_ready | sdram_tmrbankmachine5_req_rdata_valid);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_valid = sdram_tmrbankmachine5_req_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_payload_we = sdram_tmrbankmachine5_req_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_payload_addr = sdram_tmrbankmachine5_req_addr;
assign sdram_tmrbankmachine5_cmd_buffer3_sink_valid = sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_ready = sdram_tmrbankmachine5_cmd_buffer3_sink_ready;
assign sdram_tmrbankmachine5_cmd_buffer3_sink_first = sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_first;
assign sdram_tmrbankmachine5_cmd_buffer3_sink_last = sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_last;
assign sdram_tmrbankmachine5_cmd_buffer3_sink_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer3_sink_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer3_source_ready = (sdram_tmrbankmachine5_req_wdata_ready | sdram_tmrbankmachine5_req_rdata_valid);
assign sdram_tmrbankmachine5_req_ready = ((sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_ready & sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_ready) & sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_ready);
assign sdram_tmrbankmachine5_row_hit = (sdram_tmrbankmachine5_row == sdram_tmrbankmachine5_cmd_buffer_source_payload_addr[20:7]);
assign sdram_tmrbankmachine5_cmd_payload_ba = 3'd5;

// synthesis translate_off
reg dummy_d_73;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine5_cmd_payload_a <= 14'd0;
	if (sdram_tmrbankmachine5_row_col_n_addr_sel) begin
		sdram_tmrbankmachine5_cmd_payload_a <= sdram_tmrbankmachine5_cmd_buffer_source_payload_addr[20:7];
	end else begin
		sdram_tmrbankmachine5_cmd_payload_a <= ((sdram_tmrbankmachine5_auto_precharge <<< 4'd10) | {sdram_tmrbankmachine5_cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_73 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine5_twtpcon_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_cmd_payload_is_write);
assign sdram_tmrbankmachine5_twtpcon2_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_cmd_payload_is_write);
assign sdram_tmrbankmachine5_twtpcon3_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_cmd_payload_is_write);
assign sdram_tmrbankmachine5_trccon_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_row_open);
assign sdram_tmrbankmachine5_trccon2_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_row_open);
assign sdram_tmrbankmachine5_trccon3_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_row_open);
assign sdram_tmrbankmachine5_trascon_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_row_open);
assign sdram_tmrbankmachine5_trascon2_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_row_open);
assign sdram_tmrbankmachine5_trascon3_valid = ((sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_ready) & sdram_tmrbankmachine5_row_open);

// synthesis translate_off
reg dummy_d_74;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine5_auto_precharge <= 1'd0;
	if ((sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid & sdram_tmrbankmachine5_cmd_buffer_source_valid)) begin
		if ((sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr[20:7] != sdram_tmrbankmachine5_cmd_buffer_source_payload_addr[20:7])) begin
			sdram_tmrbankmachine5_auto_precharge <= (sdram_tmrbankmachine5_row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_74 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine5_TMRcmd_valid = {3{sdram_tmrbankmachine5_cmd_valid}};
assign sdram_tmrbankmachine5_TMRcmd_last = {3{sdram_tmrbankmachine5_cmd_last}};
assign sdram_tmrbankmachine5_TMRcmd_first = {3{sdram_tmrbankmachine5_cmd_first}};
assign sdram_tmrbankmachine5_tmrinput_control0 = (((sdram_tmrbankmachine5_TMRcmd_ready[0] & sdram_tmrbankmachine5_TMRcmd_ready[1]) | (sdram_tmrbankmachine5_TMRcmd_ready[1] & sdram_tmrbankmachine5_TMRcmd_ready[2])) | (sdram_tmrbankmachine5_TMRcmd_ready[0] & sdram_tmrbankmachine5_TMRcmd_ready[2]));
assign sdram_tmrbankmachine5_cmd_ready = sdram_tmrbankmachine5_tmrinput_control0;
assign sdram_tmrbankmachine5_TMRcmd_payload_a = {3{sdram_tmrbankmachine5_cmd_payload_a}};
assign sdram_tmrbankmachine5_TMRcmd_payload_ba = {3{sdram_tmrbankmachine5_cmd_payload_ba}};
assign sdram_tmrbankmachine5_TMRcmd_payload_cas = {3{sdram_tmrbankmachine5_cmd_payload_cas}};
assign sdram_tmrbankmachine5_TMRcmd_payload_ras = {3{sdram_tmrbankmachine5_cmd_payload_ras}};
assign sdram_tmrbankmachine5_TMRcmd_payload_we = {3{sdram_tmrbankmachine5_cmd_payload_we}};
assign sdram_tmrbankmachine5_TMRcmd_payload_is_cmd = {3{sdram_tmrbankmachine5_cmd_payload_is_cmd}};
assign sdram_tmrbankmachine5_TMRcmd_payload_is_read = {3{sdram_tmrbankmachine5_cmd_payload_is_read}};
assign sdram_tmrbankmachine5_TMRcmd_payload_is_write = {3{sdram_tmrbankmachine5_cmd_payload_is_write}};
assign sdram_tmrbankmachine5_tmrinput_control1 = (((sdram_tmrbankmachine5_TMRreq_valid[0] & sdram_tmrbankmachine5_TMRreq_valid[1]) | (sdram_tmrbankmachine5_TMRreq_valid[1] & sdram_tmrbankmachine5_TMRreq_valid[2])) | (sdram_tmrbankmachine5_TMRreq_valid[0] & sdram_tmrbankmachine5_TMRreq_valid[2]));
assign sdram_tmrbankmachine5_req_valid = sdram_tmrbankmachine5_tmrinput_control1;
assign sdram_tmrbankmachine5_TMRreq_ready = {3{sdram_tmrbankmachine5_req_ready}};
assign sdram_tmrbankmachine5_tmrinput_control2 = (((sdram_tmrbankmachine5_TMRreq_we[0] & sdram_tmrbankmachine5_TMRreq_we[1]) | (sdram_tmrbankmachine5_TMRreq_we[1] & sdram_tmrbankmachine5_TMRreq_we[2])) | (sdram_tmrbankmachine5_TMRreq_we[0] & sdram_tmrbankmachine5_TMRreq_we[2]));
assign sdram_tmrbankmachine5_req_we = sdram_tmrbankmachine5_tmrinput_control2;
assign sdram_tmrbankmachine5_tmrinput_control3 = (((sdram_tmrbankmachine5_TMRreq_addr[20:0] & sdram_tmrbankmachine5_TMRreq_addr[41:21]) | (sdram_tmrbankmachine5_TMRreq_addr[41:21] & sdram_tmrbankmachine5_TMRreq_addr[62:42])) | (sdram_tmrbankmachine5_TMRreq_addr[20:0] & sdram_tmrbankmachine5_TMRreq_addr[62:42]));
assign sdram_tmrbankmachine5_req_addr = sdram_tmrbankmachine5_tmrinput_control3;
assign sdram_tmrbankmachine5_TMRreq_lock = {3{sdram_tmrbankmachine5_req_lock}};
assign sdram_tmrbankmachine5_TMRreq_wdata_ready = {3{sdram_tmrbankmachine5_req_wdata_ready}};
assign sdram_tmrbankmachine5_TMRreq_rdata_valid = {3{sdram_tmrbankmachine5_req_rdata_valid}};
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_din = {sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_last, sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_first, sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_payload_we};
assign {sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_last, sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_first, sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_payload_we} = sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_dout;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_ready = sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_writable;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_we = sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_first = sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_first;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_last = sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_last;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_in_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead_sink_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid = sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_readable;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_source_first = sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_first;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_source_last = sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_last;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead_fifo_out_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_re = sdram_tmrbankmachine5_cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_75;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead_replace) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_adr <= (sdram_tmrbankmachine5_cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_adr <= sdram_tmrbankmachine5_cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_75 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_dat_w = sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_din;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_we = (sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_we & (sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_writable | sdram_tmrbankmachine5_cmd_buffer_lookahead_replace));
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_do_read = (sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_readable & sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_re);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_rdport_adr = sdram_tmrbankmachine5_cmd_buffer_lookahead_consume;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_dout = sdram_tmrbankmachine5_cmd_buffer_lookahead_rdport_dat_r;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_writable = (sdram_tmrbankmachine5_cmd_buffer_lookahead_level != 4'd8);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_readable = (sdram_tmrbankmachine5_cmd_buffer_lookahead_level != 1'd0);
assign sdram_tmrbankmachine5_cmd_buffer_sink_ready = ((~sdram_tmrbankmachine5_cmd_buffer_source_valid) | sdram_tmrbankmachine5_cmd_buffer_source_ready);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_din = {sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_last, sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_first, sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_payload_we};
assign {sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_last, sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_first, sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_payload_we} = sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_dout;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_ready = sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_writable;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_we = sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_first = sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_first;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_last = sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_last;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_in_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead2_sink_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid = sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_readable;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_first = sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_first;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_last = sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_last;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead2_fifo_out_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_re = sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_76;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead2_replace) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_adr <= (sdram_tmrbankmachine5_cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_adr <= sdram_tmrbankmachine5_cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_76 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_dat_w = sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_din;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_we = (sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_we & (sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_writable | sdram_tmrbankmachine5_cmd_buffer_lookahead2_replace));
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_do_read = (sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_readable & sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_re);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_rdport_adr = sdram_tmrbankmachine5_cmd_buffer_lookahead2_consume;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_dout = sdram_tmrbankmachine5_cmd_buffer_lookahead2_rdport_dat_r;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_writable = (sdram_tmrbankmachine5_cmd_buffer_lookahead2_level != 4'd8);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_readable = (sdram_tmrbankmachine5_cmd_buffer_lookahead2_level != 1'd0);
assign sdram_tmrbankmachine5_cmd_buffer2_sink_ready = ((~sdram_tmrbankmachine5_cmd_buffer2_source_valid) | sdram_tmrbankmachine5_cmd_buffer2_source_ready);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_din = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_last, sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_first, sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_payload_we};
assign {sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_last, sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_first, sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_payload_we} = sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_dout;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_ready = sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_writable;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_we = sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_valid;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_first = sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_first;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_last = sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_last;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_in_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead3_sink_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid = sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_readable;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_first = sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_first;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_last = sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_last;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_we = sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_payload_we;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr = sdram_tmrbankmachine5_cmd_buffer_lookahead3_fifo_out_payload_addr;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_re = sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_77;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead3_replace) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_adr <= (sdram_tmrbankmachine5_cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_adr <= sdram_tmrbankmachine5_cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_77 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_dat_w = sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_din;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_we = (sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_we & (sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_writable | sdram_tmrbankmachine5_cmd_buffer_lookahead3_replace));
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_do_read = (sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_readable & sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_re);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_rdport_adr = sdram_tmrbankmachine5_cmd_buffer_lookahead3_consume;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_dout = sdram_tmrbankmachine5_cmd_buffer_lookahead3_rdport_dat_r;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_writable = (sdram_tmrbankmachine5_cmd_buffer_lookahead3_level != 4'd8);
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_readable = (sdram_tmrbankmachine5_cmd_buffer_lookahead3_level != 1'd0);
assign sdram_tmrbankmachine5_cmd_buffer3_sink_ready = ((~sdram_tmrbankmachine5_cmd_buffer3_source_valid) | sdram_tmrbankmachine5_cmd_buffer3_source_ready);
assign sdram_tmrbankmachine5_tmrinput_control4 = (((slice_proxy624[0] & slice_proxy625[1]) | (slice_proxy626[1] & slice_proxy627[2])) | (slice_proxy628[0] & slice_proxy629[2]));

// synthesis translate_off
reg dummy_d_78;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine5_req_lock <= 1'd0;
	sdram_tmrbankmachine5_req_lock <= (sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine5_cmd_buffer_source_valid);
	sdram_tmrbankmachine5_req_lock <= sdram_tmrbankmachine5_tmrinput_control4;
// synthesis translate_off
	dummy_d_78 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine5_lookAddrVote_control = (((slice_proxy630[20:0] & slice_proxy631[41:21]) | (slice_proxy632[41:21] & slice_proxy633[62:42])) | (slice_proxy634[20:0] & slice_proxy635[62:42]));
assign sdram_tmrbankmachine5_bufAddrVote_control = (((slice_proxy636[20:0] & slice_proxy637[41:21]) | (slice_proxy638[41:21] & slice_proxy639[62:42])) | (slice_proxy640[20:0] & slice_proxy641[62:42]));
assign sdram_tmrbankmachine5_lookValidVote_control = (((slice_proxy642[0] & slice_proxy643[1]) | (slice_proxy644[1] & slice_proxy645[2])) | (slice_proxy646[0] & slice_proxy647[2]));
assign sdram_tmrbankmachine5_bufValidVote_control = (((slice_proxy648[0] & slice_proxy649[1]) | (slice_proxy650[1] & slice_proxy651[2])) | (slice_proxy652[0] & slice_proxy653[2]));
assign sdram_tmrbankmachine5_bufWeVote_control = (((slice_proxy654[0] & slice_proxy655[1]) | (slice_proxy656[1] & slice_proxy657[2])) | (slice_proxy658[0] & slice_proxy659[2]));
assign sdram_tmrbankmachine5_twtpVote_control = (((slice_proxy660[0] & slice_proxy661[1]) | (slice_proxy662[1] & slice_proxy663[2])) | (slice_proxy664[0] & slice_proxy665[2]));
assign sdram_tmrbankmachine5_trcVote_control = (((slice_proxy666[0] & slice_proxy667[1]) | (slice_proxy668[1] & slice_proxy669[2])) | (slice_proxy670[0] & slice_proxy671[2]));
assign sdram_tmrbankmachine5_trasVote_control = (((slice_proxy672[0] & slice_proxy673[1]) | (slice_proxy674[1] & slice_proxy675[2])) | (slice_proxy676[0] & slice_proxy677[2]));

// synthesis translate_off
reg dummy_d_79;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine5_req_wdata_ready <= 1'd0;
	sdram_tmrbankmachine5_req_rdata_valid <= 1'd0;
	sdram_tmrbankmachine5_refresh_gnt <= 1'd0;
	sdram_tmrbankmachine5_cmd_valid <= 1'd0;
	sdram_tmrbankmachine5_cmd_payload_cas <= 1'd0;
	sdram_tmrbankmachine5_cmd_payload_ras <= 1'd0;
	sdram_tmrbankmachine5_cmd_payload_we <= 1'd0;
	sdram_tmrbankmachine5_cmd_payload_is_cmd <= 1'd0;
	sdram_tmrbankmachine5_cmd_payload_is_read <= 1'd0;
	sdram_tmrbankmachine5_cmd_payload_is_write <= 1'd0;
	sdram_tmrbankmachine5_row_open <= 1'd0;
	sdram_tmrbankmachine5_row_close <= 1'd0;
	sdram_tmrbankmachine5_row_col_n_addr_sel <= 1'd0;
	tmrbankmachine5_next_state <= 4'd0;
	tmrbankmachine5_next_state <= tmrbankmachine5_state;
	case (tmrbankmachine5_state)
		1'd1: begin
			if ((sdram_tmrbankmachine5_twtpVote_control & sdram_tmrbankmachine5_trasVote_control)) begin
				sdram_tmrbankmachine5_cmd_valid <= 1'd1;
				if (sdram_tmrbankmachine5_cmd_ready) begin
					tmrbankmachine5_next_state <= 3'd5;
				end
				sdram_tmrbankmachine5_cmd_payload_ras <= 1'd1;
				sdram_tmrbankmachine5_cmd_payload_we <= 1'd1;
				sdram_tmrbankmachine5_cmd_payload_is_cmd <= 1'd1;
			end
			sdram_tmrbankmachine5_row_close <= 1'd1;
		end
		2'd2: begin
			if ((sdram_tmrbankmachine5_twtpVote_control & sdram_tmrbankmachine5_trasVote_control)) begin
				tmrbankmachine5_next_state <= 3'd5;
			end
			sdram_tmrbankmachine5_row_close <= 1'd1;
		end
		2'd3: begin
			if (sdram_tmrbankmachine5_trcVote_control) begin
				sdram_tmrbankmachine5_row_col_n_addr_sel <= 1'd1;
				sdram_tmrbankmachine5_row_open <= 1'd1;
				sdram_tmrbankmachine5_cmd_valid <= 1'd1;
				sdram_tmrbankmachine5_cmd_payload_is_cmd <= 1'd1;
				if (sdram_tmrbankmachine5_cmd_ready) begin
					tmrbankmachine5_next_state <= 3'd7;
				end
				sdram_tmrbankmachine5_cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			if (sdram_tmrbankmachine5_twtpVote_control) begin
				sdram_tmrbankmachine5_refresh_gnt <= 1'd1;
			end
			sdram_tmrbankmachine5_row_close <= 1'd1;
			sdram_tmrbankmachine5_cmd_payload_is_cmd <= 1'd1;
			if ((~sdram_tmrbankmachine5_refresh_req)) begin
				tmrbankmachine5_next_state <= 1'd0;
			end
		end
		3'd5: begin
			tmrbankmachine5_next_state <= 3'd6;
		end
		3'd6: begin
			tmrbankmachine5_next_state <= 2'd3;
		end
		3'd7: begin
			tmrbankmachine5_next_state <= 4'd8;
		end
		4'd8: begin
			tmrbankmachine5_next_state <= 1'd0;
		end
		default: begin
			if (sdram_tmrbankmachine5_refresh_req) begin
				tmrbankmachine5_next_state <= 3'd4;
			end else begin
				if (sdram_tmrbankmachine5_cmd_buffer_source_valid) begin
					if (sdram_tmrbankmachine5_row_opened) begin
						if (sdram_tmrbankmachine5_row_hit) begin
							sdram_tmrbankmachine5_cmd_valid <= 1'd1;
							if (sdram_tmrbankmachine5_cmd_buffer_source_payload_we) begin
								sdram_tmrbankmachine5_req_wdata_ready <= sdram_tmrbankmachine5_cmd_ready;
								sdram_tmrbankmachine5_cmd_payload_is_write <= 1'd1;
								sdram_tmrbankmachine5_cmd_payload_we <= 1'd1;
							end else begin
								sdram_tmrbankmachine5_req_rdata_valid <= sdram_tmrbankmachine5_cmd_ready;
								sdram_tmrbankmachine5_cmd_payload_is_read <= 1'd1;
							end
							sdram_tmrbankmachine5_cmd_payload_cas <= 1'd1;
							if ((sdram_tmrbankmachine5_cmd_ready & sdram_tmrbankmachine5_auto_precharge)) begin
								tmrbankmachine5_next_state <= 2'd2;
							end
						end else begin
							tmrbankmachine5_next_state <= 1'd1;
						end
					end else begin
						tmrbankmachine5_next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_79 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_valid = sdram_tmrbankmachine6_req_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_payload_we = sdram_tmrbankmachine6_req_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_payload_addr = sdram_tmrbankmachine6_req_addr;
assign sdram_tmrbankmachine6_cmd_buffer_sink_valid = sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_source_ready = sdram_tmrbankmachine6_cmd_buffer_sink_ready;
assign sdram_tmrbankmachine6_cmd_buffer_sink_first = sdram_tmrbankmachine6_cmd_buffer_lookahead_source_first;
assign sdram_tmrbankmachine6_cmd_buffer_sink_last = sdram_tmrbankmachine6_cmd_buffer_lookahead_source_last;
assign sdram_tmrbankmachine6_cmd_buffer_sink_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer_sink_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer_source_ready = (sdram_tmrbankmachine6_req_wdata_ready | sdram_tmrbankmachine6_req_rdata_valid);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_valid = sdram_tmrbankmachine6_req_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_payload_we = sdram_tmrbankmachine6_req_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_payload_addr = sdram_tmrbankmachine6_req_addr;
assign sdram_tmrbankmachine6_cmd_buffer2_sink_valid = sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_ready = sdram_tmrbankmachine6_cmd_buffer2_sink_ready;
assign sdram_tmrbankmachine6_cmd_buffer2_sink_first = sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_first;
assign sdram_tmrbankmachine6_cmd_buffer2_sink_last = sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_last;
assign sdram_tmrbankmachine6_cmd_buffer2_sink_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer2_sink_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer2_source_ready = (sdram_tmrbankmachine6_req_wdata_ready | sdram_tmrbankmachine6_req_rdata_valid);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_valid = sdram_tmrbankmachine6_req_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_payload_we = sdram_tmrbankmachine6_req_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_payload_addr = sdram_tmrbankmachine6_req_addr;
assign sdram_tmrbankmachine6_cmd_buffer3_sink_valid = sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_ready = sdram_tmrbankmachine6_cmd_buffer3_sink_ready;
assign sdram_tmrbankmachine6_cmd_buffer3_sink_first = sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_first;
assign sdram_tmrbankmachine6_cmd_buffer3_sink_last = sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_last;
assign sdram_tmrbankmachine6_cmd_buffer3_sink_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer3_sink_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer3_source_ready = (sdram_tmrbankmachine6_req_wdata_ready | sdram_tmrbankmachine6_req_rdata_valid);
assign sdram_tmrbankmachine6_req_ready = ((sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_ready & sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_ready) & sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_ready);
assign sdram_tmrbankmachine6_row_hit = (sdram_tmrbankmachine6_row == sdram_tmrbankmachine6_cmd_buffer_source_payload_addr[20:7]);
assign sdram_tmrbankmachine6_cmd_payload_ba = 3'd6;

// synthesis translate_off
reg dummy_d_80;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine6_cmd_payload_a <= 14'd0;
	if (sdram_tmrbankmachine6_row_col_n_addr_sel) begin
		sdram_tmrbankmachine6_cmd_payload_a <= sdram_tmrbankmachine6_cmd_buffer_source_payload_addr[20:7];
	end else begin
		sdram_tmrbankmachine6_cmd_payload_a <= ((sdram_tmrbankmachine6_auto_precharge <<< 4'd10) | {sdram_tmrbankmachine6_cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_80 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine6_twtpcon_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_cmd_payload_is_write);
assign sdram_tmrbankmachine6_twtpcon2_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_cmd_payload_is_write);
assign sdram_tmrbankmachine6_twtpcon3_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_cmd_payload_is_write);
assign sdram_tmrbankmachine6_trccon_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_row_open);
assign sdram_tmrbankmachine6_trccon2_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_row_open);
assign sdram_tmrbankmachine6_trccon3_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_row_open);
assign sdram_tmrbankmachine6_trascon_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_row_open);
assign sdram_tmrbankmachine6_trascon2_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_row_open);
assign sdram_tmrbankmachine6_trascon3_valid = ((sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_ready) & sdram_tmrbankmachine6_row_open);

// synthesis translate_off
reg dummy_d_81;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine6_auto_precharge <= 1'd0;
	if ((sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid & sdram_tmrbankmachine6_cmd_buffer_source_valid)) begin
		if ((sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr[20:7] != sdram_tmrbankmachine6_cmd_buffer_source_payload_addr[20:7])) begin
			sdram_tmrbankmachine6_auto_precharge <= (sdram_tmrbankmachine6_row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_81 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine6_TMRcmd_valid = {3{sdram_tmrbankmachine6_cmd_valid}};
assign sdram_tmrbankmachine6_TMRcmd_last = {3{sdram_tmrbankmachine6_cmd_last}};
assign sdram_tmrbankmachine6_TMRcmd_first = {3{sdram_tmrbankmachine6_cmd_first}};
assign sdram_tmrbankmachine6_tmrinput_control0 = (((sdram_tmrbankmachine6_TMRcmd_ready[0] & sdram_tmrbankmachine6_TMRcmd_ready[1]) | (sdram_tmrbankmachine6_TMRcmd_ready[1] & sdram_tmrbankmachine6_TMRcmd_ready[2])) | (sdram_tmrbankmachine6_TMRcmd_ready[0] & sdram_tmrbankmachine6_TMRcmd_ready[2]));
assign sdram_tmrbankmachine6_cmd_ready = sdram_tmrbankmachine6_tmrinput_control0;
assign sdram_tmrbankmachine6_TMRcmd_payload_a = {3{sdram_tmrbankmachine6_cmd_payload_a}};
assign sdram_tmrbankmachine6_TMRcmd_payload_ba = {3{sdram_tmrbankmachine6_cmd_payload_ba}};
assign sdram_tmrbankmachine6_TMRcmd_payload_cas = {3{sdram_tmrbankmachine6_cmd_payload_cas}};
assign sdram_tmrbankmachine6_TMRcmd_payload_ras = {3{sdram_tmrbankmachine6_cmd_payload_ras}};
assign sdram_tmrbankmachine6_TMRcmd_payload_we = {3{sdram_tmrbankmachine6_cmd_payload_we}};
assign sdram_tmrbankmachine6_TMRcmd_payload_is_cmd = {3{sdram_tmrbankmachine6_cmd_payload_is_cmd}};
assign sdram_tmrbankmachine6_TMRcmd_payload_is_read = {3{sdram_tmrbankmachine6_cmd_payload_is_read}};
assign sdram_tmrbankmachine6_TMRcmd_payload_is_write = {3{sdram_tmrbankmachine6_cmd_payload_is_write}};
assign sdram_tmrbankmachine6_tmrinput_control1 = (((sdram_tmrbankmachine6_TMRreq_valid[0] & sdram_tmrbankmachine6_TMRreq_valid[1]) | (sdram_tmrbankmachine6_TMRreq_valid[1] & sdram_tmrbankmachine6_TMRreq_valid[2])) | (sdram_tmrbankmachine6_TMRreq_valid[0] & sdram_tmrbankmachine6_TMRreq_valid[2]));
assign sdram_tmrbankmachine6_req_valid = sdram_tmrbankmachine6_tmrinput_control1;
assign sdram_tmrbankmachine6_TMRreq_ready = {3{sdram_tmrbankmachine6_req_ready}};
assign sdram_tmrbankmachine6_tmrinput_control2 = (((sdram_tmrbankmachine6_TMRreq_we[0] & sdram_tmrbankmachine6_TMRreq_we[1]) | (sdram_tmrbankmachine6_TMRreq_we[1] & sdram_tmrbankmachine6_TMRreq_we[2])) | (sdram_tmrbankmachine6_TMRreq_we[0] & sdram_tmrbankmachine6_TMRreq_we[2]));
assign sdram_tmrbankmachine6_req_we = sdram_tmrbankmachine6_tmrinput_control2;
assign sdram_tmrbankmachine6_tmrinput_control3 = (((sdram_tmrbankmachine6_TMRreq_addr[20:0] & sdram_tmrbankmachine6_TMRreq_addr[41:21]) | (sdram_tmrbankmachine6_TMRreq_addr[41:21] & sdram_tmrbankmachine6_TMRreq_addr[62:42])) | (sdram_tmrbankmachine6_TMRreq_addr[20:0] & sdram_tmrbankmachine6_TMRreq_addr[62:42]));
assign sdram_tmrbankmachine6_req_addr = sdram_tmrbankmachine6_tmrinput_control3;
assign sdram_tmrbankmachine6_TMRreq_lock = {3{sdram_tmrbankmachine6_req_lock}};
assign sdram_tmrbankmachine6_TMRreq_wdata_ready = {3{sdram_tmrbankmachine6_req_wdata_ready}};
assign sdram_tmrbankmachine6_TMRreq_rdata_valid = {3{sdram_tmrbankmachine6_req_rdata_valid}};
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_din = {sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_last, sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_first, sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_payload_we};
assign {sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_last, sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_first, sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_payload_we} = sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_dout;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_ready = sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_writable;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_we = sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_first = sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_first;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_last = sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_last;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_in_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead_sink_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid = sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_readable;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_source_first = sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_first;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_source_last = sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_last;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead_fifo_out_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_re = sdram_tmrbankmachine6_cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_82;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead_replace) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_adr <= (sdram_tmrbankmachine6_cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_adr <= sdram_tmrbankmachine6_cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_82 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_dat_w = sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_din;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_we = (sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_we & (sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_writable | sdram_tmrbankmachine6_cmd_buffer_lookahead_replace));
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_do_read = (sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_readable & sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_re);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_rdport_adr = sdram_tmrbankmachine6_cmd_buffer_lookahead_consume;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_dout = sdram_tmrbankmachine6_cmd_buffer_lookahead_rdport_dat_r;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_writable = (sdram_tmrbankmachine6_cmd_buffer_lookahead_level != 4'd8);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_readable = (sdram_tmrbankmachine6_cmd_buffer_lookahead_level != 1'd0);
assign sdram_tmrbankmachine6_cmd_buffer_sink_ready = ((~sdram_tmrbankmachine6_cmd_buffer_source_valid) | sdram_tmrbankmachine6_cmd_buffer_source_ready);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_din = {sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_last, sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_first, sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_payload_we};
assign {sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_last, sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_first, sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_payload_we} = sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_dout;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_ready = sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_writable;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_we = sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_first = sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_first;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_last = sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_last;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_in_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead2_sink_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid = sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_readable;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_first = sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_first;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_last = sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_last;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead2_fifo_out_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_re = sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_83;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead2_replace) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_adr <= (sdram_tmrbankmachine6_cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_adr <= sdram_tmrbankmachine6_cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_83 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_dat_w = sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_din;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_we = (sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_we & (sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_writable | sdram_tmrbankmachine6_cmd_buffer_lookahead2_replace));
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_do_read = (sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_readable & sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_re);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_rdport_adr = sdram_tmrbankmachine6_cmd_buffer_lookahead2_consume;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_dout = sdram_tmrbankmachine6_cmd_buffer_lookahead2_rdport_dat_r;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_writable = (sdram_tmrbankmachine6_cmd_buffer_lookahead2_level != 4'd8);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_readable = (sdram_tmrbankmachine6_cmd_buffer_lookahead2_level != 1'd0);
assign sdram_tmrbankmachine6_cmd_buffer2_sink_ready = ((~sdram_tmrbankmachine6_cmd_buffer2_source_valid) | sdram_tmrbankmachine6_cmd_buffer2_source_ready);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_din = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_last, sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_first, sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_payload_we};
assign {sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_last, sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_first, sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_payload_we} = sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_dout;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_ready = sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_writable;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_we = sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_valid;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_first = sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_first;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_last = sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_last;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_in_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead3_sink_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid = sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_readable;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_first = sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_first;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_last = sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_last;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_we = sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_payload_we;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr = sdram_tmrbankmachine6_cmd_buffer_lookahead3_fifo_out_payload_addr;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_re = sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_84;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead3_replace) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_adr <= (sdram_tmrbankmachine6_cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_adr <= sdram_tmrbankmachine6_cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_84 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_dat_w = sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_din;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_we = (sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_we & (sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_writable | sdram_tmrbankmachine6_cmd_buffer_lookahead3_replace));
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_do_read = (sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_readable & sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_re);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_rdport_adr = sdram_tmrbankmachine6_cmd_buffer_lookahead3_consume;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_dout = sdram_tmrbankmachine6_cmd_buffer_lookahead3_rdport_dat_r;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_writable = (sdram_tmrbankmachine6_cmd_buffer_lookahead3_level != 4'd8);
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_readable = (sdram_tmrbankmachine6_cmd_buffer_lookahead3_level != 1'd0);
assign sdram_tmrbankmachine6_cmd_buffer3_sink_ready = ((~sdram_tmrbankmachine6_cmd_buffer3_source_valid) | sdram_tmrbankmachine6_cmd_buffer3_source_ready);
assign sdram_tmrbankmachine6_tmrinput_control4 = (((slice_proxy678[0] & slice_proxy679[1]) | (slice_proxy680[1] & slice_proxy681[2])) | (slice_proxy682[0] & slice_proxy683[2]));

// synthesis translate_off
reg dummy_d_85;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine6_req_lock <= 1'd0;
	sdram_tmrbankmachine6_req_lock <= (sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine6_cmd_buffer_source_valid);
	sdram_tmrbankmachine6_req_lock <= sdram_tmrbankmachine6_tmrinput_control4;
// synthesis translate_off
	dummy_d_85 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine6_lookAddrVote_control = (((slice_proxy684[20:0] & slice_proxy685[41:21]) | (slice_proxy686[41:21] & slice_proxy687[62:42])) | (slice_proxy688[20:0] & slice_proxy689[62:42]));
assign sdram_tmrbankmachine6_bufAddrVote_control = (((slice_proxy690[20:0] & slice_proxy691[41:21]) | (slice_proxy692[41:21] & slice_proxy693[62:42])) | (slice_proxy694[20:0] & slice_proxy695[62:42]));
assign sdram_tmrbankmachine6_lookValidVote_control = (((slice_proxy696[0] & slice_proxy697[1]) | (slice_proxy698[1] & slice_proxy699[2])) | (slice_proxy700[0] & slice_proxy701[2]));
assign sdram_tmrbankmachine6_bufValidVote_control = (((slice_proxy702[0] & slice_proxy703[1]) | (slice_proxy704[1] & slice_proxy705[2])) | (slice_proxy706[0] & slice_proxy707[2]));
assign sdram_tmrbankmachine6_bufWeVote_control = (((slice_proxy708[0] & slice_proxy709[1]) | (slice_proxy710[1] & slice_proxy711[2])) | (slice_proxy712[0] & slice_proxy713[2]));
assign sdram_tmrbankmachine6_twtpVote_control = (((slice_proxy714[0] & slice_proxy715[1]) | (slice_proxy716[1] & slice_proxy717[2])) | (slice_proxy718[0] & slice_proxy719[2]));
assign sdram_tmrbankmachine6_trcVote_control = (((slice_proxy720[0] & slice_proxy721[1]) | (slice_proxy722[1] & slice_proxy723[2])) | (slice_proxy724[0] & slice_proxy725[2]));
assign sdram_tmrbankmachine6_trasVote_control = (((slice_proxy726[0] & slice_proxy727[1]) | (slice_proxy728[1] & slice_proxy729[2])) | (slice_proxy730[0] & slice_proxy731[2]));

// synthesis translate_off
reg dummy_d_86;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine6_req_wdata_ready <= 1'd0;
	sdram_tmrbankmachine6_req_rdata_valid <= 1'd0;
	sdram_tmrbankmachine6_refresh_gnt <= 1'd0;
	sdram_tmrbankmachine6_cmd_valid <= 1'd0;
	sdram_tmrbankmachine6_cmd_payload_cas <= 1'd0;
	sdram_tmrbankmachine6_cmd_payload_ras <= 1'd0;
	sdram_tmrbankmachine6_cmd_payload_we <= 1'd0;
	sdram_tmrbankmachine6_cmd_payload_is_cmd <= 1'd0;
	sdram_tmrbankmachine6_cmd_payload_is_read <= 1'd0;
	sdram_tmrbankmachine6_cmd_payload_is_write <= 1'd0;
	sdram_tmrbankmachine6_row_open <= 1'd0;
	sdram_tmrbankmachine6_row_close <= 1'd0;
	sdram_tmrbankmachine6_row_col_n_addr_sel <= 1'd0;
	tmrbankmachine6_next_state <= 4'd0;
	tmrbankmachine6_next_state <= tmrbankmachine6_state;
	case (tmrbankmachine6_state)
		1'd1: begin
			if ((sdram_tmrbankmachine6_twtpVote_control & sdram_tmrbankmachine6_trasVote_control)) begin
				sdram_tmrbankmachine6_cmd_valid <= 1'd1;
				if (sdram_tmrbankmachine6_cmd_ready) begin
					tmrbankmachine6_next_state <= 3'd5;
				end
				sdram_tmrbankmachine6_cmd_payload_ras <= 1'd1;
				sdram_tmrbankmachine6_cmd_payload_we <= 1'd1;
				sdram_tmrbankmachine6_cmd_payload_is_cmd <= 1'd1;
			end
			sdram_tmrbankmachine6_row_close <= 1'd1;
		end
		2'd2: begin
			if ((sdram_tmrbankmachine6_twtpVote_control & sdram_tmrbankmachine6_trasVote_control)) begin
				tmrbankmachine6_next_state <= 3'd5;
			end
			sdram_tmrbankmachine6_row_close <= 1'd1;
		end
		2'd3: begin
			if (sdram_tmrbankmachine6_trcVote_control) begin
				sdram_tmrbankmachine6_row_col_n_addr_sel <= 1'd1;
				sdram_tmrbankmachine6_row_open <= 1'd1;
				sdram_tmrbankmachine6_cmd_valid <= 1'd1;
				sdram_tmrbankmachine6_cmd_payload_is_cmd <= 1'd1;
				if (sdram_tmrbankmachine6_cmd_ready) begin
					tmrbankmachine6_next_state <= 3'd7;
				end
				sdram_tmrbankmachine6_cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			if (sdram_tmrbankmachine6_twtpVote_control) begin
				sdram_tmrbankmachine6_refresh_gnt <= 1'd1;
			end
			sdram_tmrbankmachine6_row_close <= 1'd1;
			sdram_tmrbankmachine6_cmd_payload_is_cmd <= 1'd1;
			if ((~sdram_tmrbankmachine6_refresh_req)) begin
				tmrbankmachine6_next_state <= 1'd0;
			end
		end
		3'd5: begin
			tmrbankmachine6_next_state <= 3'd6;
		end
		3'd6: begin
			tmrbankmachine6_next_state <= 2'd3;
		end
		3'd7: begin
			tmrbankmachine6_next_state <= 4'd8;
		end
		4'd8: begin
			tmrbankmachine6_next_state <= 1'd0;
		end
		default: begin
			if (sdram_tmrbankmachine6_refresh_req) begin
				tmrbankmachine6_next_state <= 3'd4;
			end else begin
				if (sdram_tmrbankmachine6_cmd_buffer_source_valid) begin
					if (sdram_tmrbankmachine6_row_opened) begin
						if (sdram_tmrbankmachine6_row_hit) begin
							sdram_tmrbankmachine6_cmd_valid <= 1'd1;
							if (sdram_tmrbankmachine6_cmd_buffer_source_payload_we) begin
								sdram_tmrbankmachine6_req_wdata_ready <= sdram_tmrbankmachine6_cmd_ready;
								sdram_tmrbankmachine6_cmd_payload_is_write <= 1'd1;
								sdram_tmrbankmachine6_cmd_payload_we <= 1'd1;
							end else begin
								sdram_tmrbankmachine6_req_rdata_valid <= sdram_tmrbankmachine6_cmd_ready;
								sdram_tmrbankmachine6_cmd_payload_is_read <= 1'd1;
							end
							sdram_tmrbankmachine6_cmd_payload_cas <= 1'd1;
							if ((sdram_tmrbankmachine6_cmd_ready & sdram_tmrbankmachine6_auto_precharge)) begin
								tmrbankmachine6_next_state <= 2'd2;
							end
						end else begin
							tmrbankmachine6_next_state <= 1'd1;
						end
					end else begin
						tmrbankmachine6_next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_86 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_valid = sdram_tmrbankmachine7_req_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_payload_we = sdram_tmrbankmachine7_req_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_payload_addr = sdram_tmrbankmachine7_req_addr;
assign sdram_tmrbankmachine7_cmd_buffer_sink_valid = sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_source_ready = sdram_tmrbankmachine7_cmd_buffer_sink_ready;
assign sdram_tmrbankmachine7_cmd_buffer_sink_first = sdram_tmrbankmachine7_cmd_buffer_lookahead_source_first;
assign sdram_tmrbankmachine7_cmd_buffer_sink_last = sdram_tmrbankmachine7_cmd_buffer_lookahead_source_last;
assign sdram_tmrbankmachine7_cmd_buffer_sink_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer_sink_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer_source_ready = (sdram_tmrbankmachine7_req_wdata_ready | sdram_tmrbankmachine7_req_rdata_valid);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_valid = sdram_tmrbankmachine7_req_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_payload_we = sdram_tmrbankmachine7_req_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_payload_addr = sdram_tmrbankmachine7_req_addr;
assign sdram_tmrbankmachine7_cmd_buffer2_sink_valid = sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_ready = sdram_tmrbankmachine7_cmd_buffer2_sink_ready;
assign sdram_tmrbankmachine7_cmd_buffer2_sink_first = sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_first;
assign sdram_tmrbankmachine7_cmd_buffer2_sink_last = sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_last;
assign sdram_tmrbankmachine7_cmd_buffer2_sink_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer2_sink_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer2_source_ready = (sdram_tmrbankmachine7_req_wdata_ready | sdram_tmrbankmachine7_req_rdata_valid);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_valid = sdram_tmrbankmachine7_req_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_payload_we = sdram_tmrbankmachine7_req_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_payload_addr = sdram_tmrbankmachine7_req_addr;
assign sdram_tmrbankmachine7_cmd_buffer3_sink_valid = sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_ready = sdram_tmrbankmachine7_cmd_buffer3_sink_ready;
assign sdram_tmrbankmachine7_cmd_buffer3_sink_first = sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_first;
assign sdram_tmrbankmachine7_cmd_buffer3_sink_last = sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_last;
assign sdram_tmrbankmachine7_cmd_buffer3_sink_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer3_sink_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer3_source_ready = (sdram_tmrbankmachine7_req_wdata_ready | sdram_tmrbankmachine7_req_rdata_valid);
assign sdram_tmrbankmachine7_req_ready = ((sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_ready & sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_ready) & sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_ready);
assign sdram_tmrbankmachine7_row_hit = (sdram_tmrbankmachine7_row == sdram_tmrbankmachine7_cmd_buffer_source_payload_addr[20:7]);
assign sdram_tmrbankmachine7_cmd_payload_ba = 3'd7;

// synthesis translate_off
reg dummy_d_87;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine7_cmd_payload_a <= 14'd0;
	if (sdram_tmrbankmachine7_row_col_n_addr_sel) begin
		sdram_tmrbankmachine7_cmd_payload_a <= sdram_tmrbankmachine7_cmd_buffer_source_payload_addr[20:7];
	end else begin
		sdram_tmrbankmachine7_cmd_payload_a <= ((sdram_tmrbankmachine7_auto_precharge <<< 4'd10) | {sdram_tmrbankmachine7_cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_87 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine7_twtpcon_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_cmd_payload_is_write);
assign sdram_tmrbankmachine7_twtpcon2_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_cmd_payload_is_write);
assign sdram_tmrbankmachine7_twtpcon3_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_cmd_payload_is_write);
assign sdram_tmrbankmachine7_trccon_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_row_open);
assign sdram_tmrbankmachine7_trccon2_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_row_open);
assign sdram_tmrbankmachine7_trccon3_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_row_open);
assign sdram_tmrbankmachine7_trascon_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_row_open);
assign sdram_tmrbankmachine7_trascon2_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_row_open);
assign sdram_tmrbankmachine7_trascon3_valid = ((sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_ready) & sdram_tmrbankmachine7_row_open);

// synthesis translate_off
reg dummy_d_88;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine7_auto_precharge <= 1'd0;
	if ((sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid & sdram_tmrbankmachine7_cmd_buffer_source_valid)) begin
		if ((sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr[20:7] != sdram_tmrbankmachine7_cmd_buffer_source_payload_addr[20:7])) begin
			sdram_tmrbankmachine7_auto_precharge <= (sdram_tmrbankmachine7_row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_88 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine7_TMRcmd_valid = {3{sdram_tmrbankmachine7_cmd_valid}};
assign sdram_tmrbankmachine7_TMRcmd_last = {3{sdram_tmrbankmachine7_cmd_last}};
assign sdram_tmrbankmachine7_TMRcmd_first = {3{sdram_tmrbankmachine7_cmd_first}};
assign sdram_tmrbankmachine7_tmrinput_control0 = (((sdram_tmrbankmachine7_TMRcmd_ready[0] & sdram_tmrbankmachine7_TMRcmd_ready[1]) | (sdram_tmrbankmachine7_TMRcmd_ready[1] & sdram_tmrbankmachine7_TMRcmd_ready[2])) | (sdram_tmrbankmachine7_TMRcmd_ready[0] & sdram_tmrbankmachine7_TMRcmd_ready[2]));
assign sdram_tmrbankmachine7_cmd_ready = sdram_tmrbankmachine7_tmrinput_control0;
assign sdram_tmrbankmachine7_TMRcmd_payload_a = {3{sdram_tmrbankmachine7_cmd_payload_a}};
assign sdram_tmrbankmachine7_TMRcmd_payload_ba = {3{sdram_tmrbankmachine7_cmd_payload_ba}};
assign sdram_tmrbankmachine7_TMRcmd_payload_cas = {3{sdram_tmrbankmachine7_cmd_payload_cas}};
assign sdram_tmrbankmachine7_TMRcmd_payload_ras = {3{sdram_tmrbankmachine7_cmd_payload_ras}};
assign sdram_tmrbankmachine7_TMRcmd_payload_we = {3{sdram_tmrbankmachine7_cmd_payload_we}};
assign sdram_tmrbankmachine7_TMRcmd_payload_is_cmd = {3{sdram_tmrbankmachine7_cmd_payload_is_cmd}};
assign sdram_tmrbankmachine7_TMRcmd_payload_is_read = {3{sdram_tmrbankmachine7_cmd_payload_is_read}};
assign sdram_tmrbankmachine7_TMRcmd_payload_is_write = {3{sdram_tmrbankmachine7_cmd_payload_is_write}};
assign sdram_tmrbankmachine7_tmrinput_control1 = (((sdram_tmrbankmachine7_TMRreq_valid[0] & sdram_tmrbankmachine7_TMRreq_valid[1]) | (sdram_tmrbankmachine7_TMRreq_valid[1] & sdram_tmrbankmachine7_TMRreq_valid[2])) | (sdram_tmrbankmachine7_TMRreq_valid[0] & sdram_tmrbankmachine7_TMRreq_valid[2]));
assign sdram_tmrbankmachine7_req_valid = sdram_tmrbankmachine7_tmrinput_control1;
assign sdram_tmrbankmachine7_TMRreq_ready = {3{sdram_tmrbankmachine7_req_ready}};
assign sdram_tmrbankmachine7_tmrinput_control2 = (((sdram_tmrbankmachine7_TMRreq_we[0] & sdram_tmrbankmachine7_TMRreq_we[1]) | (sdram_tmrbankmachine7_TMRreq_we[1] & sdram_tmrbankmachine7_TMRreq_we[2])) | (sdram_tmrbankmachine7_TMRreq_we[0] & sdram_tmrbankmachine7_TMRreq_we[2]));
assign sdram_tmrbankmachine7_req_we = sdram_tmrbankmachine7_tmrinput_control2;
assign sdram_tmrbankmachine7_tmrinput_control3 = (((sdram_tmrbankmachine7_TMRreq_addr[20:0] & sdram_tmrbankmachine7_TMRreq_addr[41:21]) | (sdram_tmrbankmachine7_TMRreq_addr[41:21] & sdram_tmrbankmachine7_TMRreq_addr[62:42])) | (sdram_tmrbankmachine7_TMRreq_addr[20:0] & sdram_tmrbankmachine7_TMRreq_addr[62:42]));
assign sdram_tmrbankmachine7_req_addr = sdram_tmrbankmachine7_tmrinput_control3;
assign sdram_tmrbankmachine7_TMRreq_lock = {3{sdram_tmrbankmachine7_req_lock}};
assign sdram_tmrbankmachine7_TMRreq_wdata_ready = {3{sdram_tmrbankmachine7_req_wdata_ready}};
assign sdram_tmrbankmachine7_TMRreq_rdata_valid = {3{sdram_tmrbankmachine7_req_rdata_valid}};
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_din = {sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_last, sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_first, sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_payload_we};
assign {sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_last, sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_first, sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_payload_we} = sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_dout;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_ready = sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_writable;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_we = sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_first = sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_first;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_last = sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_last;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_in_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead_sink_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid = sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_readable;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_source_first = sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_first;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_source_last = sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_last;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead_fifo_out_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_re = sdram_tmrbankmachine7_cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_89;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead_replace) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_adr <= (sdram_tmrbankmachine7_cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_adr <= sdram_tmrbankmachine7_cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_89 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_dat_w = sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_din;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_we = (sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_we & (sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_writable | sdram_tmrbankmachine7_cmd_buffer_lookahead_replace));
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_do_read = (sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_readable & sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_re);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_rdport_adr = sdram_tmrbankmachine7_cmd_buffer_lookahead_consume;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_dout = sdram_tmrbankmachine7_cmd_buffer_lookahead_rdport_dat_r;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_writable = (sdram_tmrbankmachine7_cmd_buffer_lookahead_level != 4'd8);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_readable = (sdram_tmrbankmachine7_cmd_buffer_lookahead_level != 1'd0);
assign sdram_tmrbankmachine7_cmd_buffer_sink_ready = ((~sdram_tmrbankmachine7_cmd_buffer_source_valid) | sdram_tmrbankmachine7_cmd_buffer_source_ready);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_din = {sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_last, sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_first, sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_payload_we};
assign {sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_last, sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_first, sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_payload_we} = sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_dout;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_ready = sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_writable;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_we = sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_first = sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_first;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_last = sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_last;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_in_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead2_sink_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid = sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_readable;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_first = sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_first;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_last = sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_last;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead2_fifo_out_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_re = sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_90;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead2_replace) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_adr <= (sdram_tmrbankmachine7_cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_adr <= sdram_tmrbankmachine7_cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_90 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_dat_w = sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_din;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_we = (sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_we & (sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_writable | sdram_tmrbankmachine7_cmd_buffer_lookahead2_replace));
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_do_read = (sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_readable & sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_re);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_rdport_adr = sdram_tmrbankmachine7_cmd_buffer_lookahead2_consume;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_dout = sdram_tmrbankmachine7_cmd_buffer_lookahead2_rdport_dat_r;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_writable = (sdram_tmrbankmachine7_cmd_buffer_lookahead2_level != 4'd8);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_readable = (sdram_tmrbankmachine7_cmd_buffer_lookahead2_level != 1'd0);
assign sdram_tmrbankmachine7_cmd_buffer2_sink_ready = ((~sdram_tmrbankmachine7_cmd_buffer2_source_valid) | sdram_tmrbankmachine7_cmd_buffer2_source_ready);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_din = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_last, sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_first, sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_payload_we};
assign {sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_last, sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_first, sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_payload_we} = sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_dout;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_ready = sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_writable;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_we = sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_valid;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_first = sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_first;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_last = sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_last;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_in_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead3_sink_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid = sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_readable;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_first = sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_first;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_last = sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_last;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_we = sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_payload_we;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr = sdram_tmrbankmachine7_cmd_buffer_lookahead3_fifo_out_payload_addr;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_re = sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_91;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead3_replace) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_adr <= (sdram_tmrbankmachine7_cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_adr <= sdram_tmrbankmachine7_cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_91 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_dat_w = sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_din;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_we = (sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_we & (sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_writable | sdram_tmrbankmachine7_cmd_buffer_lookahead3_replace));
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_do_read = (sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_readable & sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_re);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_rdport_adr = sdram_tmrbankmachine7_cmd_buffer_lookahead3_consume;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_dout = sdram_tmrbankmachine7_cmd_buffer_lookahead3_rdport_dat_r;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_writable = (sdram_tmrbankmachine7_cmd_buffer_lookahead3_level != 4'd8);
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_readable = (sdram_tmrbankmachine7_cmd_buffer_lookahead3_level != 1'd0);
assign sdram_tmrbankmachine7_cmd_buffer3_sink_ready = ((~sdram_tmrbankmachine7_cmd_buffer3_source_valid) | sdram_tmrbankmachine7_cmd_buffer3_source_ready);
assign sdram_tmrbankmachine7_tmrinput_control4 = (((slice_proxy732[0] & slice_proxy733[1]) | (slice_proxy734[1] & slice_proxy735[2])) | (slice_proxy736[0] & slice_proxy737[2]));

// synthesis translate_off
reg dummy_d_92;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine7_req_lock <= 1'd0;
	sdram_tmrbankmachine7_req_lock <= (sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine7_cmd_buffer_source_valid);
	sdram_tmrbankmachine7_req_lock <= sdram_tmrbankmachine7_tmrinput_control4;
// synthesis translate_off
	dummy_d_92 <= dummy_s;
// synthesis translate_on
end
assign sdram_tmrbankmachine7_lookAddrVote_control = (((slice_proxy738[20:0] & slice_proxy739[41:21]) | (slice_proxy740[41:21] & slice_proxy741[62:42])) | (slice_proxy742[20:0] & slice_proxy743[62:42]));
assign sdram_tmrbankmachine7_bufAddrVote_control = (((slice_proxy744[20:0] & slice_proxy745[41:21]) | (slice_proxy746[41:21] & slice_proxy747[62:42])) | (slice_proxy748[20:0] & slice_proxy749[62:42]));
assign sdram_tmrbankmachine7_lookValidVote_control = (((slice_proxy750[0] & slice_proxy751[1]) | (slice_proxy752[1] & slice_proxy753[2])) | (slice_proxy754[0] & slice_proxy755[2]));
assign sdram_tmrbankmachine7_bufValidVote_control = (((slice_proxy756[0] & slice_proxy757[1]) | (slice_proxy758[1] & slice_proxy759[2])) | (slice_proxy760[0] & slice_proxy761[2]));
assign sdram_tmrbankmachine7_bufWeVote_control = (((slice_proxy762[0] & slice_proxy763[1]) | (slice_proxy764[1] & slice_proxy765[2])) | (slice_proxy766[0] & slice_proxy767[2]));
assign sdram_tmrbankmachine7_twtpVote_control = (((slice_proxy768[0] & slice_proxy769[1]) | (slice_proxy770[1] & slice_proxy771[2])) | (slice_proxy772[0] & slice_proxy773[2]));
assign sdram_tmrbankmachine7_trcVote_control = (((slice_proxy774[0] & slice_proxy775[1]) | (slice_proxy776[1] & slice_proxy777[2])) | (slice_proxy778[0] & slice_proxy779[2]));
assign sdram_tmrbankmachine7_trasVote_control = (((slice_proxy780[0] & slice_proxy781[1]) | (slice_proxy782[1] & slice_proxy783[2])) | (slice_proxy784[0] & slice_proxy785[2]));

// synthesis translate_off
reg dummy_d_93;
// synthesis translate_on
always @(*) begin
	sdram_tmrbankmachine7_req_wdata_ready <= 1'd0;
	sdram_tmrbankmachine7_req_rdata_valid <= 1'd0;
	sdram_tmrbankmachine7_refresh_gnt <= 1'd0;
	sdram_tmrbankmachine7_cmd_valid <= 1'd0;
	sdram_tmrbankmachine7_cmd_payload_cas <= 1'd0;
	sdram_tmrbankmachine7_cmd_payload_ras <= 1'd0;
	sdram_tmrbankmachine7_cmd_payload_we <= 1'd0;
	sdram_tmrbankmachine7_cmd_payload_is_cmd <= 1'd0;
	sdram_tmrbankmachine7_cmd_payload_is_read <= 1'd0;
	sdram_tmrbankmachine7_cmd_payload_is_write <= 1'd0;
	sdram_tmrbankmachine7_row_open <= 1'd0;
	sdram_tmrbankmachine7_row_close <= 1'd0;
	sdram_tmrbankmachine7_row_col_n_addr_sel <= 1'd0;
	tmrbankmachine7_next_state <= 4'd0;
	tmrbankmachine7_next_state <= tmrbankmachine7_state;
	case (tmrbankmachine7_state)
		1'd1: begin
			if ((sdram_tmrbankmachine7_twtpVote_control & sdram_tmrbankmachine7_trasVote_control)) begin
				sdram_tmrbankmachine7_cmd_valid <= 1'd1;
				if (sdram_tmrbankmachine7_cmd_ready) begin
					tmrbankmachine7_next_state <= 3'd5;
				end
				sdram_tmrbankmachine7_cmd_payload_ras <= 1'd1;
				sdram_tmrbankmachine7_cmd_payload_we <= 1'd1;
				sdram_tmrbankmachine7_cmd_payload_is_cmd <= 1'd1;
			end
			sdram_tmrbankmachine7_row_close <= 1'd1;
		end
		2'd2: begin
			if ((sdram_tmrbankmachine7_twtpVote_control & sdram_tmrbankmachine7_trasVote_control)) begin
				tmrbankmachine7_next_state <= 3'd5;
			end
			sdram_tmrbankmachine7_row_close <= 1'd1;
		end
		2'd3: begin
			if (sdram_tmrbankmachine7_trcVote_control) begin
				sdram_tmrbankmachine7_row_col_n_addr_sel <= 1'd1;
				sdram_tmrbankmachine7_row_open <= 1'd1;
				sdram_tmrbankmachine7_cmd_valid <= 1'd1;
				sdram_tmrbankmachine7_cmd_payload_is_cmd <= 1'd1;
				if (sdram_tmrbankmachine7_cmd_ready) begin
					tmrbankmachine7_next_state <= 3'd7;
				end
				sdram_tmrbankmachine7_cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			if (sdram_tmrbankmachine7_twtpVote_control) begin
				sdram_tmrbankmachine7_refresh_gnt <= 1'd1;
			end
			sdram_tmrbankmachine7_row_close <= 1'd1;
			sdram_tmrbankmachine7_cmd_payload_is_cmd <= 1'd1;
			if ((~sdram_tmrbankmachine7_refresh_req)) begin
				tmrbankmachine7_next_state <= 1'd0;
			end
		end
		3'd5: begin
			tmrbankmachine7_next_state <= 3'd6;
		end
		3'd6: begin
			tmrbankmachine7_next_state <= 2'd3;
		end
		3'd7: begin
			tmrbankmachine7_next_state <= 4'd8;
		end
		4'd8: begin
			tmrbankmachine7_next_state <= 1'd0;
		end
		default: begin
			if (sdram_tmrbankmachine7_refresh_req) begin
				tmrbankmachine7_next_state <= 3'd4;
			end else begin
				if (sdram_tmrbankmachine7_cmd_buffer_source_valid) begin
					if (sdram_tmrbankmachine7_row_opened) begin
						if (sdram_tmrbankmachine7_row_hit) begin
							sdram_tmrbankmachine7_cmd_valid <= 1'd1;
							if (sdram_tmrbankmachine7_cmd_buffer_source_payload_we) begin
								sdram_tmrbankmachine7_req_wdata_ready <= sdram_tmrbankmachine7_cmd_ready;
								sdram_tmrbankmachine7_cmd_payload_is_write <= 1'd1;
								sdram_tmrbankmachine7_cmd_payload_we <= 1'd1;
							end else begin
								sdram_tmrbankmachine7_req_rdata_valid <= sdram_tmrbankmachine7_cmd_ready;
								sdram_tmrbankmachine7_cmd_payload_is_read <= 1'd1;
							end
							sdram_tmrbankmachine7_cmd_payload_cas <= 1'd1;
							if ((sdram_tmrbankmachine7_cmd_ready & sdram_tmrbankmachine7_auto_precharge)) begin
								tmrbankmachine7_next_state <= 2'd2;
							end
						end else begin
							tmrbankmachine7_next_state <= 1'd1;
						end
					end else begin
						tmrbankmachine7_next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_93 <= dummy_s;
// synthesis translate_on
end
assign sdram_multiplexer_rdcmdphase = (ddrphy_rdphase_storage - 1'd1);
assign sdram_multiplexer_wrcmdphase = (ddrphy_wrphase_storage - 1'd1);
assign sdram_multiplexer_trrdcon_valid = ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & ((sdram_multiplexer_choose_cmd_cmd_payload_ras & (~sdram_multiplexer_choose_cmd_cmd_payload_cas)) & (~sdram_multiplexer_choose_cmd_cmd_payload_we)));
assign sdram_multiplexer_tfawcon_valid = ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & ((sdram_multiplexer_choose_cmd_cmd_payload_ras & (~sdram_multiplexer_choose_cmd_cmd_payload_cas)) & (~sdram_multiplexer_choose_cmd_cmd_payload_we)));
assign sdram_multiplexer_ras_allowed = (sdram_multiplexer_trrdcon_ready & sdram_multiplexer_tfawcon_ready);
assign sdram_multiplexer_tccdcon_valid = ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_cmd_payload_is_write | sdram_multiplexer_choose_req_cmd_payload_is_read));
assign sdram_multiplexer_cas_allowed = sdram_multiplexer_tccdcon_ready;
assign sdram_multiplexer_twtrcon_valid = ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_write);
assign sdram_multiplexer_read_available = ((((((((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_payload_is_read) | (sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_payload_is_read)) | (sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_payload_is_read)) | (sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_payload_is_read)) | (sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_payload_is_read)) | (sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_payload_is_read)) | (sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_payload_is_read)) | (sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_payload_is_read));
assign sdram_multiplexer_write_available = ((((((((sdram_tmrbankmachine0_cmd_valid & sdram_tmrbankmachine0_cmd_payload_is_write) | (sdram_tmrbankmachine1_cmd_valid & sdram_tmrbankmachine1_cmd_payload_is_write)) | (sdram_tmrbankmachine2_cmd_valid & sdram_tmrbankmachine2_cmd_payload_is_write)) | (sdram_tmrbankmachine3_cmd_valid & sdram_tmrbankmachine3_cmd_payload_is_write)) | (sdram_tmrbankmachine4_cmd_valid & sdram_tmrbankmachine4_cmd_payload_is_write)) | (sdram_tmrbankmachine5_cmd_valid & sdram_tmrbankmachine5_cmd_payload_is_write)) | (sdram_tmrbankmachine6_cmd_valid & sdram_tmrbankmachine6_cmd_payload_is_write)) | (sdram_tmrbankmachine7_cmd_valid & sdram_tmrbankmachine7_cmd_payload_is_write));
assign sdram_multiplexer_max_time0 = (sdram_multiplexer_time0 == 1'd0);
assign sdram_multiplexer_max_time1 = (sdram_multiplexer_time1 == 1'd0);
assign sdram_tmrbankmachine0_refresh_req = sdram_multiplexer_refreshCmd_valid;
assign sdram_tmrbankmachine1_refresh_req = sdram_multiplexer_refreshCmd_valid;
assign sdram_tmrbankmachine2_refresh_req = sdram_multiplexer_refreshCmd_valid;
assign sdram_tmrbankmachine3_refresh_req = sdram_multiplexer_refreshCmd_valid;
assign sdram_tmrbankmachine4_refresh_req = sdram_multiplexer_refreshCmd_valid;
assign sdram_tmrbankmachine5_refresh_req = sdram_multiplexer_refreshCmd_valid;
assign sdram_tmrbankmachine6_refresh_req = sdram_multiplexer_refreshCmd_valid;
assign sdram_tmrbankmachine7_refresh_req = sdram_multiplexer_refreshCmd_valid;
assign sdram_multiplexer_go_to_refresh = (((((((sdram_tmrbankmachine0_refresh_gnt & sdram_tmrbankmachine1_refresh_gnt) & sdram_tmrbankmachine2_refresh_gnt) & sdram_tmrbankmachine3_refresh_gnt) & sdram_tmrbankmachine4_refresh_gnt) & sdram_tmrbankmachine5_refresh_gnt) & sdram_tmrbankmachine6_refresh_gnt) & sdram_tmrbankmachine7_refresh_gnt);
assign sdram_multiplexer_control0 = (((sdram_tmrbankmachine0_TMRcmd_valid[0] & sdram_tmrbankmachine0_TMRcmd_valid[1]) | (sdram_tmrbankmachine0_TMRcmd_valid[1] & sdram_tmrbankmachine0_TMRcmd_valid[2])) | (sdram_tmrbankmachine0_TMRcmd_valid[0] & sdram_tmrbankmachine0_TMRcmd_valid[2]));
assign sdram_multiplexer_endpoint0_valid = sdram_multiplexer_control0;
assign sdram_multiplexer_control1 = (((sdram_tmrbankmachine0_TMRcmd_last[0] & sdram_tmrbankmachine0_TMRcmd_last[1]) | (sdram_tmrbankmachine0_TMRcmd_last[1] & sdram_tmrbankmachine0_TMRcmd_last[2])) | (sdram_tmrbankmachine0_TMRcmd_last[0] & sdram_tmrbankmachine0_TMRcmd_last[2]));
assign sdram_multiplexer_endpoint0_last = sdram_multiplexer_control1;
assign sdram_tmrbankmachine0_TMRcmd_ready = {3{sdram_multiplexer_endpoint0_ready}};
assign sdram_multiplexer_control2 = (((sdram_tmrbankmachine0_TMRcmd_first[0] & sdram_tmrbankmachine0_TMRcmd_first[1]) | (sdram_tmrbankmachine0_TMRcmd_first[1] & sdram_tmrbankmachine0_TMRcmd_first[2])) | (sdram_tmrbankmachine0_TMRcmd_first[0] & sdram_tmrbankmachine0_TMRcmd_first[2]));
assign sdram_multiplexer_endpoint0_first = sdram_multiplexer_control2;
assign sdram_multiplexer_control3 = (((sdram_tmrbankmachine0_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine0_TMRcmd_payload_a[27:14]) | (sdram_tmrbankmachine0_TMRcmd_payload_a[27:14] & sdram_tmrbankmachine0_TMRcmd_payload_a[41:28])) | (sdram_tmrbankmachine0_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine0_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_endpoint0_payload_a = sdram_multiplexer_control3;
assign sdram_multiplexer_control4 = (((sdram_tmrbankmachine0_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine0_TMRcmd_payload_ba[5:3]) | (sdram_tmrbankmachine0_TMRcmd_payload_ba[5:3] & sdram_tmrbankmachine0_TMRcmd_payload_ba[8:6])) | (sdram_tmrbankmachine0_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine0_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_endpoint0_payload_ba = sdram_multiplexer_control4;
assign sdram_multiplexer_control5 = (((sdram_tmrbankmachine0_TMRcmd_payload_cas[0] & sdram_tmrbankmachine0_TMRcmd_payload_cas[1]) | (sdram_tmrbankmachine0_TMRcmd_payload_cas[1] & sdram_tmrbankmachine0_TMRcmd_payload_cas[2])) | (sdram_tmrbankmachine0_TMRcmd_payload_cas[0] & sdram_tmrbankmachine0_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_endpoint0_payload_cas = sdram_multiplexer_control5;
assign sdram_multiplexer_control6 = (((sdram_tmrbankmachine0_TMRcmd_payload_ras[0] & sdram_tmrbankmachine0_TMRcmd_payload_ras[1]) | (sdram_tmrbankmachine0_TMRcmd_payload_ras[1] & sdram_tmrbankmachine0_TMRcmd_payload_ras[2])) | (sdram_tmrbankmachine0_TMRcmd_payload_ras[0] & sdram_tmrbankmachine0_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_endpoint0_payload_ras = sdram_multiplexer_control6;
assign sdram_multiplexer_control7 = (((sdram_tmrbankmachine0_TMRcmd_payload_we[0] & sdram_tmrbankmachine0_TMRcmd_payload_we[1]) | (sdram_tmrbankmachine0_TMRcmd_payload_we[1] & sdram_tmrbankmachine0_TMRcmd_payload_we[2])) | (sdram_tmrbankmachine0_TMRcmd_payload_we[0] & sdram_tmrbankmachine0_TMRcmd_payload_we[2]));
assign sdram_multiplexer_endpoint0_payload_we = sdram_multiplexer_control7;
assign sdram_multiplexer_control8 = (((sdram_tmrbankmachine0_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine0_TMRcmd_payload_is_cmd[1]) | (sdram_tmrbankmachine0_TMRcmd_payload_is_cmd[1] & sdram_tmrbankmachine0_TMRcmd_payload_is_cmd[2])) | (sdram_tmrbankmachine0_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine0_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_endpoint0_payload_is_cmd = sdram_multiplexer_control8;
assign sdram_multiplexer_control9 = (((sdram_tmrbankmachine0_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine0_TMRcmd_payload_is_read[1]) | (sdram_tmrbankmachine0_TMRcmd_payload_is_read[1] & sdram_tmrbankmachine0_TMRcmd_payload_is_read[2])) | (sdram_tmrbankmachine0_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine0_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_endpoint0_payload_is_read = sdram_multiplexer_control9;
assign sdram_multiplexer_control10 = (((sdram_tmrbankmachine0_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine0_TMRcmd_payload_is_write[1]) | (sdram_tmrbankmachine0_TMRcmd_payload_is_write[1] & sdram_tmrbankmachine0_TMRcmd_payload_is_write[2])) | (sdram_tmrbankmachine0_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine0_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_endpoint0_payload_is_write = sdram_multiplexer_control10;
assign sdram_multiplexer_control11 = (((sdram_tmrbankmachine1_TMRcmd_valid[0] & sdram_tmrbankmachine1_TMRcmd_valid[1]) | (sdram_tmrbankmachine1_TMRcmd_valid[1] & sdram_tmrbankmachine1_TMRcmd_valid[2])) | (sdram_tmrbankmachine1_TMRcmd_valid[0] & sdram_tmrbankmachine1_TMRcmd_valid[2]));
assign sdram_multiplexer_endpoint1_valid = sdram_multiplexer_control11;
assign sdram_multiplexer_control12 = (((sdram_tmrbankmachine1_TMRcmd_last[0] & sdram_tmrbankmachine1_TMRcmd_last[1]) | (sdram_tmrbankmachine1_TMRcmd_last[1] & sdram_tmrbankmachine1_TMRcmd_last[2])) | (sdram_tmrbankmachine1_TMRcmd_last[0] & sdram_tmrbankmachine1_TMRcmd_last[2]));
assign sdram_multiplexer_endpoint1_last = sdram_multiplexer_control12;
assign sdram_tmrbankmachine1_TMRcmd_ready = {3{sdram_multiplexer_endpoint1_ready}};
assign sdram_multiplexer_control13 = (((sdram_tmrbankmachine1_TMRcmd_first[0] & sdram_tmrbankmachine1_TMRcmd_first[1]) | (sdram_tmrbankmachine1_TMRcmd_first[1] & sdram_tmrbankmachine1_TMRcmd_first[2])) | (sdram_tmrbankmachine1_TMRcmd_first[0] & sdram_tmrbankmachine1_TMRcmd_first[2]));
assign sdram_multiplexer_endpoint1_first = sdram_multiplexer_control13;
assign sdram_multiplexer_control14 = (((sdram_tmrbankmachine1_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine1_TMRcmd_payload_a[27:14]) | (sdram_tmrbankmachine1_TMRcmd_payload_a[27:14] & sdram_tmrbankmachine1_TMRcmd_payload_a[41:28])) | (sdram_tmrbankmachine1_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine1_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_endpoint1_payload_a = sdram_multiplexer_control14;
assign sdram_multiplexer_control15 = (((sdram_tmrbankmachine1_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine1_TMRcmd_payload_ba[5:3]) | (sdram_tmrbankmachine1_TMRcmd_payload_ba[5:3] & sdram_tmrbankmachine1_TMRcmd_payload_ba[8:6])) | (sdram_tmrbankmachine1_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine1_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_endpoint1_payload_ba = sdram_multiplexer_control15;
assign sdram_multiplexer_control16 = (((sdram_tmrbankmachine1_TMRcmd_payload_cas[0] & sdram_tmrbankmachine1_TMRcmd_payload_cas[1]) | (sdram_tmrbankmachine1_TMRcmd_payload_cas[1] & sdram_tmrbankmachine1_TMRcmd_payload_cas[2])) | (sdram_tmrbankmachine1_TMRcmd_payload_cas[0] & sdram_tmrbankmachine1_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_endpoint1_payload_cas = sdram_multiplexer_control16;
assign sdram_multiplexer_control17 = (((sdram_tmrbankmachine1_TMRcmd_payload_ras[0] & sdram_tmrbankmachine1_TMRcmd_payload_ras[1]) | (sdram_tmrbankmachine1_TMRcmd_payload_ras[1] & sdram_tmrbankmachine1_TMRcmd_payload_ras[2])) | (sdram_tmrbankmachine1_TMRcmd_payload_ras[0] & sdram_tmrbankmachine1_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_endpoint1_payload_ras = sdram_multiplexer_control17;
assign sdram_multiplexer_control18 = (((sdram_tmrbankmachine1_TMRcmd_payload_we[0] & sdram_tmrbankmachine1_TMRcmd_payload_we[1]) | (sdram_tmrbankmachine1_TMRcmd_payload_we[1] & sdram_tmrbankmachine1_TMRcmd_payload_we[2])) | (sdram_tmrbankmachine1_TMRcmd_payload_we[0] & sdram_tmrbankmachine1_TMRcmd_payload_we[2]));
assign sdram_multiplexer_endpoint1_payload_we = sdram_multiplexer_control18;
assign sdram_multiplexer_control19 = (((sdram_tmrbankmachine1_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine1_TMRcmd_payload_is_cmd[1]) | (sdram_tmrbankmachine1_TMRcmd_payload_is_cmd[1] & sdram_tmrbankmachine1_TMRcmd_payload_is_cmd[2])) | (sdram_tmrbankmachine1_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine1_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_endpoint1_payload_is_cmd = sdram_multiplexer_control19;
assign sdram_multiplexer_control20 = (((sdram_tmrbankmachine1_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine1_TMRcmd_payload_is_read[1]) | (sdram_tmrbankmachine1_TMRcmd_payload_is_read[1] & sdram_tmrbankmachine1_TMRcmd_payload_is_read[2])) | (sdram_tmrbankmachine1_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine1_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_endpoint1_payload_is_read = sdram_multiplexer_control20;
assign sdram_multiplexer_control21 = (((sdram_tmrbankmachine1_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine1_TMRcmd_payload_is_write[1]) | (sdram_tmrbankmachine1_TMRcmd_payload_is_write[1] & sdram_tmrbankmachine1_TMRcmd_payload_is_write[2])) | (sdram_tmrbankmachine1_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine1_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_endpoint1_payload_is_write = sdram_multiplexer_control21;
assign sdram_multiplexer_control22 = (((sdram_tmrbankmachine2_TMRcmd_valid[0] & sdram_tmrbankmachine2_TMRcmd_valid[1]) | (sdram_tmrbankmachine2_TMRcmd_valid[1] & sdram_tmrbankmachine2_TMRcmd_valid[2])) | (sdram_tmrbankmachine2_TMRcmd_valid[0] & sdram_tmrbankmachine2_TMRcmd_valid[2]));
assign sdram_multiplexer_endpoint2_valid = sdram_multiplexer_control22;
assign sdram_multiplexer_control23 = (((sdram_tmrbankmachine2_TMRcmd_last[0] & sdram_tmrbankmachine2_TMRcmd_last[1]) | (sdram_tmrbankmachine2_TMRcmd_last[1] & sdram_tmrbankmachine2_TMRcmd_last[2])) | (sdram_tmrbankmachine2_TMRcmd_last[0] & sdram_tmrbankmachine2_TMRcmd_last[2]));
assign sdram_multiplexer_endpoint2_last = sdram_multiplexer_control23;
assign sdram_tmrbankmachine2_TMRcmd_ready = {3{sdram_multiplexer_endpoint2_ready}};
assign sdram_multiplexer_control24 = (((sdram_tmrbankmachine2_TMRcmd_first[0] & sdram_tmrbankmachine2_TMRcmd_first[1]) | (sdram_tmrbankmachine2_TMRcmd_first[1] & sdram_tmrbankmachine2_TMRcmd_first[2])) | (sdram_tmrbankmachine2_TMRcmd_first[0] & sdram_tmrbankmachine2_TMRcmd_first[2]));
assign sdram_multiplexer_endpoint2_first = sdram_multiplexer_control24;
assign sdram_multiplexer_control25 = (((sdram_tmrbankmachine2_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine2_TMRcmd_payload_a[27:14]) | (sdram_tmrbankmachine2_TMRcmd_payload_a[27:14] & sdram_tmrbankmachine2_TMRcmd_payload_a[41:28])) | (sdram_tmrbankmachine2_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine2_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_endpoint2_payload_a = sdram_multiplexer_control25;
assign sdram_multiplexer_control26 = (((sdram_tmrbankmachine2_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine2_TMRcmd_payload_ba[5:3]) | (sdram_tmrbankmachine2_TMRcmd_payload_ba[5:3] & sdram_tmrbankmachine2_TMRcmd_payload_ba[8:6])) | (sdram_tmrbankmachine2_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine2_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_endpoint2_payload_ba = sdram_multiplexer_control26;
assign sdram_multiplexer_control27 = (((sdram_tmrbankmachine2_TMRcmd_payload_cas[0] & sdram_tmrbankmachine2_TMRcmd_payload_cas[1]) | (sdram_tmrbankmachine2_TMRcmd_payload_cas[1] & sdram_tmrbankmachine2_TMRcmd_payload_cas[2])) | (sdram_tmrbankmachine2_TMRcmd_payload_cas[0] & sdram_tmrbankmachine2_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_endpoint2_payload_cas = sdram_multiplexer_control27;
assign sdram_multiplexer_control28 = (((sdram_tmrbankmachine2_TMRcmd_payload_ras[0] & sdram_tmrbankmachine2_TMRcmd_payload_ras[1]) | (sdram_tmrbankmachine2_TMRcmd_payload_ras[1] & sdram_tmrbankmachine2_TMRcmd_payload_ras[2])) | (sdram_tmrbankmachine2_TMRcmd_payload_ras[0] & sdram_tmrbankmachine2_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_endpoint2_payload_ras = sdram_multiplexer_control28;
assign sdram_multiplexer_control29 = (((sdram_tmrbankmachine2_TMRcmd_payload_we[0] & sdram_tmrbankmachine2_TMRcmd_payload_we[1]) | (sdram_tmrbankmachine2_TMRcmd_payload_we[1] & sdram_tmrbankmachine2_TMRcmd_payload_we[2])) | (sdram_tmrbankmachine2_TMRcmd_payload_we[0] & sdram_tmrbankmachine2_TMRcmd_payload_we[2]));
assign sdram_multiplexer_endpoint2_payload_we = sdram_multiplexer_control29;
assign sdram_multiplexer_control30 = (((sdram_tmrbankmachine2_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine2_TMRcmd_payload_is_cmd[1]) | (sdram_tmrbankmachine2_TMRcmd_payload_is_cmd[1] & sdram_tmrbankmachine2_TMRcmd_payload_is_cmd[2])) | (sdram_tmrbankmachine2_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine2_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_endpoint2_payload_is_cmd = sdram_multiplexer_control30;
assign sdram_multiplexer_control31 = (((sdram_tmrbankmachine2_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine2_TMRcmd_payload_is_read[1]) | (sdram_tmrbankmachine2_TMRcmd_payload_is_read[1] & sdram_tmrbankmachine2_TMRcmd_payload_is_read[2])) | (sdram_tmrbankmachine2_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine2_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_endpoint2_payload_is_read = sdram_multiplexer_control31;
assign sdram_multiplexer_control32 = (((sdram_tmrbankmachine2_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine2_TMRcmd_payload_is_write[1]) | (sdram_tmrbankmachine2_TMRcmd_payload_is_write[1] & sdram_tmrbankmachine2_TMRcmd_payload_is_write[2])) | (sdram_tmrbankmachine2_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine2_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_endpoint2_payload_is_write = sdram_multiplexer_control32;
assign sdram_multiplexer_control33 = (((sdram_tmrbankmachine3_TMRcmd_valid[0] & sdram_tmrbankmachine3_TMRcmd_valid[1]) | (sdram_tmrbankmachine3_TMRcmd_valid[1] & sdram_tmrbankmachine3_TMRcmd_valid[2])) | (sdram_tmrbankmachine3_TMRcmd_valid[0] & sdram_tmrbankmachine3_TMRcmd_valid[2]));
assign sdram_multiplexer_endpoint3_valid = sdram_multiplexer_control33;
assign sdram_multiplexer_control34 = (((sdram_tmrbankmachine3_TMRcmd_last[0] & sdram_tmrbankmachine3_TMRcmd_last[1]) | (sdram_tmrbankmachine3_TMRcmd_last[1] & sdram_tmrbankmachine3_TMRcmd_last[2])) | (sdram_tmrbankmachine3_TMRcmd_last[0] & sdram_tmrbankmachine3_TMRcmd_last[2]));
assign sdram_multiplexer_endpoint3_last = sdram_multiplexer_control34;
assign sdram_tmrbankmachine3_TMRcmd_ready = {3{sdram_multiplexer_endpoint3_ready}};
assign sdram_multiplexer_control35 = (((sdram_tmrbankmachine3_TMRcmd_first[0] & sdram_tmrbankmachine3_TMRcmd_first[1]) | (sdram_tmrbankmachine3_TMRcmd_first[1] & sdram_tmrbankmachine3_TMRcmd_first[2])) | (sdram_tmrbankmachine3_TMRcmd_first[0] & sdram_tmrbankmachine3_TMRcmd_first[2]));
assign sdram_multiplexer_endpoint3_first = sdram_multiplexer_control35;
assign sdram_multiplexer_control36 = (((sdram_tmrbankmachine3_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine3_TMRcmd_payload_a[27:14]) | (sdram_tmrbankmachine3_TMRcmd_payload_a[27:14] & sdram_tmrbankmachine3_TMRcmd_payload_a[41:28])) | (sdram_tmrbankmachine3_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine3_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_endpoint3_payload_a = sdram_multiplexer_control36;
assign sdram_multiplexer_control37 = (((sdram_tmrbankmachine3_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine3_TMRcmd_payload_ba[5:3]) | (sdram_tmrbankmachine3_TMRcmd_payload_ba[5:3] & sdram_tmrbankmachine3_TMRcmd_payload_ba[8:6])) | (sdram_tmrbankmachine3_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine3_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_endpoint3_payload_ba = sdram_multiplexer_control37;
assign sdram_multiplexer_control38 = (((sdram_tmrbankmachine3_TMRcmd_payload_cas[0] & sdram_tmrbankmachine3_TMRcmd_payload_cas[1]) | (sdram_tmrbankmachine3_TMRcmd_payload_cas[1] & sdram_tmrbankmachine3_TMRcmd_payload_cas[2])) | (sdram_tmrbankmachine3_TMRcmd_payload_cas[0] & sdram_tmrbankmachine3_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_endpoint3_payload_cas = sdram_multiplexer_control38;
assign sdram_multiplexer_control39 = (((sdram_tmrbankmachine3_TMRcmd_payload_ras[0] & sdram_tmrbankmachine3_TMRcmd_payload_ras[1]) | (sdram_tmrbankmachine3_TMRcmd_payload_ras[1] & sdram_tmrbankmachine3_TMRcmd_payload_ras[2])) | (sdram_tmrbankmachine3_TMRcmd_payload_ras[0] & sdram_tmrbankmachine3_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_endpoint3_payload_ras = sdram_multiplexer_control39;
assign sdram_multiplexer_control40 = (((sdram_tmrbankmachine3_TMRcmd_payload_we[0] & sdram_tmrbankmachine3_TMRcmd_payload_we[1]) | (sdram_tmrbankmachine3_TMRcmd_payload_we[1] & sdram_tmrbankmachine3_TMRcmd_payload_we[2])) | (sdram_tmrbankmachine3_TMRcmd_payload_we[0] & sdram_tmrbankmachine3_TMRcmd_payload_we[2]));
assign sdram_multiplexer_endpoint3_payload_we = sdram_multiplexer_control40;
assign sdram_multiplexer_control41 = (((sdram_tmrbankmachine3_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine3_TMRcmd_payload_is_cmd[1]) | (sdram_tmrbankmachine3_TMRcmd_payload_is_cmd[1] & sdram_tmrbankmachine3_TMRcmd_payload_is_cmd[2])) | (sdram_tmrbankmachine3_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine3_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_endpoint3_payload_is_cmd = sdram_multiplexer_control41;
assign sdram_multiplexer_control42 = (((sdram_tmrbankmachine3_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine3_TMRcmd_payload_is_read[1]) | (sdram_tmrbankmachine3_TMRcmd_payload_is_read[1] & sdram_tmrbankmachine3_TMRcmd_payload_is_read[2])) | (sdram_tmrbankmachine3_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine3_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_endpoint3_payload_is_read = sdram_multiplexer_control42;
assign sdram_multiplexer_control43 = (((sdram_tmrbankmachine3_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine3_TMRcmd_payload_is_write[1]) | (sdram_tmrbankmachine3_TMRcmd_payload_is_write[1] & sdram_tmrbankmachine3_TMRcmd_payload_is_write[2])) | (sdram_tmrbankmachine3_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine3_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_endpoint3_payload_is_write = sdram_multiplexer_control43;
assign sdram_multiplexer_control44 = (((sdram_tmrbankmachine4_TMRcmd_valid[0] & sdram_tmrbankmachine4_TMRcmd_valid[1]) | (sdram_tmrbankmachine4_TMRcmd_valid[1] & sdram_tmrbankmachine4_TMRcmd_valid[2])) | (sdram_tmrbankmachine4_TMRcmd_valid[0] & sdram_tmrbankmachine4_TMRcmd_valid[2]));
assign sdram_multiplexer_endpoint4_valid = sdram_multiplexer_control44;
assign sdram_multiplexer_control45 = (((sdram_tmrbankmachine4_TMRcmd_last[0] & sdram_tmrbankmachine4_TMRcmd_last[1]) | (sdram_tmrbankmachine4_TMRcmd_last[1] & sdram_tmrbankmachine4_TMRcmd_last[2])) | (sdram_tmrbankmachine4_TMRcmd_last[0] & sdram_tmrbankmachine4_TMRcmd_last[2]));
assign sdram_multiplexer_endpoint4_last = sdram_multiplexer_control45;
assign sdram_tmrbankmachine4_TMRcmd_ready = {3{sdram_multiplexer_endpoint4_ready}};
assign sdram_multiplexer_control46 = (((sdram_tmrbankmachine4_TMRcmd_first[0] & sdram_tmrbankmachine4_TMRcmd_first[1]) | (sdram_tmrbankmachine4_TMRcmd_first[1] & sdram_tmrbankmachine4_TMRcmd_first[2])) | (sdram_tmrbankmachine4_TMRcmd_first[0] & sdram_tmrbankmachine4_TMRcmd_first[2]));
assign sdram_multiplexer_endpoint4_first = sdram_multiplexer_control46;
assign sdram_multiplexer_control47 = (((sdram_tmrbankmachine4_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine4_TMRcmd_payload_a[27:14]) | (sdram_tmrbankmachine4_TMRcmd_payload_a[27:14] & sdram_tmrbankmachine4_TMRcmd_payload_a[41:28])) | (sdram_tmrbankmachine4_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine4_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_endpoint4_payload_a = sdram_multiplexer_control47;
assign sdram_multiplexer_control48 = (((sdram_tmrbankmachine4_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine4_TMRcmd_payload_ba[5:3]) | (sdram_tmrbankmachine4_TMRcmd_payload_ba[5:3] & sdram_tmrbankmachine4_TMRcmd_payload_ba[8:6])) | (sdram_tmrbankmachine4_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine4_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_endpoint4_payload_ba = sdram_multiplexer_control48;
assign sdram_multiplexer_control49 = (((sdram_tmrbankmachine4_TMRcmd_payload_cas[0] & sdram_tmrbankmachine4_TMRcmd_payload_cas[1]) | (sdram_tmrbankmachine4_TMRcmd_payload_cas[1] & sdram_tmrbankmachine4_TMRcmd_payload_cas[2])) | (sdram_tmrbankmachine4_TMRcmd_payload_cas[0] & sdram_tmrbankmachine4_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_endpoint4_payload_cas = sdram_multiplexer_control49;
assign sdram_multiplexer_control50 = (((sdram_tmrbankmachine4_TMRcmd_payload_ras[0] & sdram_tmrbankmachine4_TMRcmd_payload_ras[1]) | (sdram_tmrbankmachine4_TMRcmd_payload_ras[1] & sdram_tmrbankmachine4_TMRcmd_payload_ras[2])) | (sdram_tmrbankmachine4_TMRcmd_payload_ras[0] & sdram_tmrbankmachine4_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_endpoint4_payload_ras = sdram_multiplexer_control50;
assign sdram_multiplexer_control51 = (((sdram_tmrbankmachine4_TMRcmd_payload_we[0] & sdram_tmrbankmachine4_TMRcmd_payload_we[1]) | (sdram_tmrbankmachine4_TMRcmd_payload_we[1] & sdram_tmrbankmachine4_TMRcmd_payload_we[2])) | (sdram_tmrbankmachine4_TMRcmd_payload_we[0] & sdram_tmrbankmachine4_TMRcmd_payload_we[2]));
assign sdram_multiplexer_endpoint4_payload_we = sdram_multiplexer_control51;
assign sdram_multiplexer_control52 = (((sdram_tmrbankmachine4_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine4_TMRcmd_payload_is_cmd[1]) | (sdram_tmrbankmachine4_TMRcmd_payload_is_cmd[1] & sdram_tmrbankmachine4_TMRcmd_payload_is_cmd[2])) | (sdram_tmrbankmachine4_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine4_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_endpoint4_payload_is_cmd = sdram_multiplexer_control52;
assign sdram_multiplexer_control53 = (((sdram_tmrbankmachine4_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine4_TMRcmd_payload_is_read[1]) | (sdram_tmrbankmachine4_TMRcmd_payload_is_read[1] & sdram_tmrbankmachine4_TMRcmd_payload_is_read[2])) | (sdram_tmrbankmachine4_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine4_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_endpoint4_payload_is_read = sdram_multiplexer_control53;
assign sdram_multiplexer_control54 = (((sdram_tmrbankmachine4_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine4_TMRcmd_payload_is_write[1]) | (sdram_tmrbankmachine4_TMRcmd_payload_is_write[1] & sdram_tmrbankmachine4_TMRcmd_payload_is_write[2])) | (sdram_tmrbankmachine4_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine4_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_endpoint4_payload_is_write = sdram_multiplexer_control54;
assign sdram_multiplexer_control55 = (((sdram_tmrbankmachine5_TMRcmd_valid[0] & sdram_tmrbankmachine5_TMRcmd_valid[1]) | (sdram_tmrbankmachine5_TMRcmd_valid[1] & sdram_tmrbankmachine5_TMRcmd_valid[2])) | (sdram_tmrbankmachine5_TMRcmd_valid[0] & sdram_tmrbankmachine5_TMRcmd_valid[2]));
assign sdram_multiplexer_endpoint5_valid = sdram_multiplexer_control55;
assign sdram_multiplexer_control56 = (((sdram_tmrbankmachine5_TMRcmd_last[0] & sdram_tmrbankmachine5_TMRcmd_last[1]) | (sdram_tmrbankmachine5_TMRcmd_last[1] & sdram_tmrbankmachine5_TMRcmd_last[2])) | (sdram_tmrbankmachine5_TMRcmd_last[0] & sdram_tmrbankmachine5_TMRcmd_last[2]));
assign sdram_multiplexer_endpoint5_last = sdram_multiplexer_control56;
assign sdram_tmrbankmachine5_TMRcmd_ready = {3{sdram_multiplexer_endpoint5_ready}};
assign sdram_multiplexer_control57 = (((sdram_tmrbankmachine5_TMRcmd_first[0] & sdram_tmrbankmachine5_TMRcmd_first[1]) | (sdram_tmrbankmachine5_TMRcmd_first[1] & sdram_tmrbankmachine5_TMRcmd_first[2])) | (sdram_tmrbankmachine5_TMRcmd_first[0] & sdram_tmrbankmachine5_TMRcmd_first[2]));
assign sdram_multiplexer_endpoint5_first = sdram_multiplexer_control57;
assign sdram_multiplexer_control58 = (((sdram_tmrbankmachine5_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine5_TMRcmd_payload_a[27:14]) | (sdram_tmrbankmachine5_TMRcmd_payload_a[27:14] & sdram_tmrbankmachine5_TMRcmd_payload_a[41:28])) | (sdram_tmrbankmachine5_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine5_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_endpoint5_payload_a = sdram_multiplexer_control58;
assign sdram_multiplexer_control59 = (((sdram_tmrbankmachine5_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine5_TMRcmd_payload_ba[5:3]) | (sdram_tmrbankmachine5_TMRcmd_payload_ba[5:3] & sdram_tmrbankmachine5_TMRcmd_payload_ba[8:6])) | (sdram_tmrbankmachine5_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine5_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_endpoint5_payload_ba = sdram_multiplexer_control59;
assign sdram_multiplexer_control60 = (((sdram_tmrbankmachine5_TMRcmd_payload_cas[0] & sdram_tmrbankmachine5_TMRcmd_payload_cas[1]) | (sdram_tmrbankmachine5_TMRcmd_payload_cas[1] & sdram_tmrbankmachine5_TMRcmd_payload_cas[2])) | (sdram_tmrbankmachine5_TMRcmd_payload_cas[0] & sdram_tmrbankmachine5_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_endpoint5_payload_cas = sdram_multiplexer_control60;
assign sdram_multiplexer_control61 = (((sdram_tmrbankmachine5_TMRcmd_payload_ras[0] & sdram_tmrbankmachine5_TMRcmd_payload_ras[1]) | (sdram_tmrbankmachine5_TMRcmd_payload_ras[1] & sdram_tmrbankmachine5_TMRcmd_payload_ras[2])) | (sdram_tmrbankmachine5_TMRcmd_payload_ras[0] & sdram_tmrbankmachine5_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_endpoint5_payload_ras = sdram_multiplexer_control61;
assign sdram_multiplexer_control62 = (((sdram_tmrbankmachine5_TMRcmd_payload_we[0] & sdram_tmrbankmachine5_TMRcmd_payload_we[1]) | (sdram_tmrbankmachine5_TMRcmd_payload_we[1] & sdram_tmrbankmachine5_TMRcmd_payload_we[2])) | (sdram_tmrbankmachine5_TMRcmd_payload_we[0] & sdram_tmrbankmachine5_TMRcmd_payload_we[2]));
assign sdram_multiplexer_endpoint5_payload_we = sdram_multiplexer_control62;
assign sdram_multiplexer_control63 = (((sdram_tmrbankmachine5_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine5_TMRcmd_payload_is_cmd[1]) | (sdram_tmrbankmachine5_TMRcmd_payload_is_cmd[1] & sdram_tmrbankmachine5_TMRcmd_payload_is_cmd[2])) | (sdram_tmrbankmachine5_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine5_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_endpoint5_payload_is_cmd = sdram_multiplexer_control63;
assign sdram_multiplexer_control64 = (((sdram_tmrbankmachine5_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine5_TMRcmd_payload_is_read[1]) | (sdram_tmrbankmachine5_TMRcmd_payload_is_read[1] & sdram_tmrbankmachine5_TMRcmd_payload_is_read[2])) | (sdram_tmrbankmachine5_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine5_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_endpoint5_payload_is_read = sdram_multiplexer_control64;
assign sdram_multiplexer_control65 = (((sdram_tmrbankmachine5_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine5_TMRcmd_payload_is_write[1]) | (sdram_tmrbankmachine5_TMRcmd_payload_is_write[1] & sdram_tmrbankmachine5_TMRcmd_payload_is_write[2])) | (sdram_tmrbankmachine5_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine5_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_endpoint5_payload_is_write = sdram_multiplexer_control65;
assign sdram_multiplexer_control66 = (((sdram_tmrbankmachine6_TMRcmd_valid[0] & sdram_tmrbankmachine6_TMRcmd_valid[1]) | (sdram_tmrbankmachine6_TMRcmd_valid[1] & sdram_tmrbankmachine6_TMRcmd_valid[2])) | (sdram_tmrbankmachine6_TMRcmd_valid[0] & sdram_tmrbankmachine6_TMRcmd_valid[2]));
assign sdram_multiplexer_endpoint6_valid = sdram_multiplexer_control66;
assign sdram_multiplexer_control67 = (((sdram_tmrbankmachine6_TMRcmd_last[0] & sdram_tmrbankmachine6_TMRcmd_last[1]) | (sdram_tmrbankmachine6_TMRcmd_last[1] & sdram_tmrbankmachine6_TMRcmd_last[2])) | (sdram_tmrbankmachine6_TMRcmd_last[0] & sdram_tmrbankmachine6_TMRcmd_last[2]));
assign sdram_multiplexer_endpoint6_last = sdram_multiplexer_control67;
assign sdram_tmrbankmachine6_TMRcmd_ready = {3{sdram_multiplexer_endpoint6_ready}};
assign sdram_multiplexer_control68 = (((sdram_tmrbankmachine6_TMRcmd_first[0] & sdram_tmrbankmachine6_TMRcmd_first[1]) | (sdram_tmrbankmachine6_TMRcmd_first[1] & sdram_tmrbankmachine6_TMRcmd_first[2])) | (sdram_tmrbankmachine6_TMRcmd_first[0] & sdram_tmrbankmachine6_TMRcmd_first[2]));
assign sdram_multiplexer_endpoint6_first = sdram_multiplexer_control68;
assign sdram_multiplexer_control69 = (((sdram_tmrbankmachine6_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine6_TMRcmd_payload_a[27:14]) | (sdram_tmrbankmachine6_TMRcmd_payload_a[27:14] & sdram_tmrbankmachine6_TMRcmd_payload_a[41:28])) | (sdram_tmrbankmachine6_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine6_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_endpoint6_payload_a = sdram_multiplexer_control69;
assign sdram_multiplexer_control70 = (((sdram_tmrbankmachine6_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine6_TMRcmd_payload_ba[5:3]) | (sdram_tmrbankmachine6_TMRcmd_payload_ba[5:3] & sdram_tmrbankmachine6_TMRcmd_payload_ba[8:6])) | (sdram_tmrbankmachine6_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine6_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_endpoint6_payload_ba = sdram_multiplexer_control70;
assign sdram_multiplexer_control71 = (((sdram_tmrbankmachine6_TMRcmd_payload_cas[0] & sdram_tmrbankmachine6_TMRcmd_payload_cas[1]) | (sdram_tmrbankmachine6_TMRcmd_payload_cas[1] & sdram_tmrbankmachine6_TMRcmd_payload_cas[2])) | (sdram_tmrbankmachine6_TMRcmd_payload_cas[0] & sdram_tmrbankmachine6_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_endpoint6_payload_cas = sdram_multiplexer_control71;
assign sdram_multiplexer_control72 = (((sdram_tmrbankmachine6_TMRcmd_payload_ras[0] & sdram_tmrbankmachine6_TMRcmd_payload_ras[1]) | (sdram_tmrbankmachine6_TMRcmd_payload_ras[1] & sdram_tmrbankmachine6_TMRcmd_payload_ras[2])) | (sdram_tmrbankmachine6_TMRcmd_payload_ras[0] & sdram_tmrbankmachine6_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_endpoint6_payload_ras = sdram_multiplexer_control72;
assign sdram_multiplexer_control73 = (((sdram_tmrbankmachine6_TMRcmd_payload_we[0] & sdram_tmrbankmachine6_TMRcmd_payload_we[1]) | (sdram_tmrbankmachine6_TMRcmd_payload_we[1] & sdram_tmrbankmachine6_TMRcmd_payload_we[2])) | (sdram_tmrbankmachine6_TMRcmd_payload_we[0] & sdram_tmrbankmachine6_TMRcmd_payload_we[2]));
assign sdram_multiplexer_endpoint6_payload_we = sdram_multiplexer_control73;
assign sdram_multiplexer_control74 = (((sdram_tmrbankmachine6_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine6_TMRcmd_payload_is_cmd[1]) | (sdram_tmrbankmachine6_TMRcmd_payload_is_cmd[1] & sdram_tmrbankmachine6_TMRcmd_payload_is_cmd[2])) | (sdram_tmrbankmachine6_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine6_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_endpoint6_payload_is_cmd = sdram_multiplexer_control74;
assign sdram_multiplexer_control75 = (((sdram_tmrbankmachine6_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine6_TMRcmd_payload_is_read[1]) | (sdram_tmrbankmachine6_TMRcmd_payload_is_read[1] & sdram_tmrbankmachine6_TMRcmd_payload_is_read[2])) | (sdram_tmrbankmachine6_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine6_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_endpoint6_payload_is_read = sdram_multiplexer_control75;
assign sdram_multiplexer_control76 = (((sdram_tmrbankmachine6_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine6_TMRcmd_payload_is_write[1]) | (sdram_tmrbankmachine6_TMRcmd_payload_is_write[1] & sdram_tmrbankmachine6_TMRcmd_payload_is_write[2])) | (sdram_tmrbankmachine6_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine6_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_endpoint6_payload_is_write = sdram_multiplexer_control76;
assign sdram_multiplexer_control77 = (((sdram_tmrbankmachine7_TMRcmd_valid[0] & sdram_tmrbankmachine7_TMRcmd_valid[1]) | (sdram_tmrbankmachine7_TMRcmd_valid[1] & sdram_tmrbankmachine7_TMRcmd_valid[2])) | (sdram_tmrbankmachine7_TMRcmd_valid[0] & sdram_tmrbankmachine7_TMRcmd_valid[2]));
assign sdram_multiplexer_endpoint7_valid = sdram_multiplexer_control77;
assign sdram_multiplexer_control78 = (((sdram_tmrbankmachine7_TMRcmd_last[0] & sdram_tmrbankmachine7_TMRcmd_last[1]) | (sdram_tmrbankmachine7_TMRcmd_last[1] & sdram_tmrbankmachine7_TMRcmd_last[2])) | (sdram_tmrbankmachine7_TMRcmd_last[0] & sdram_tmrbankmachine7_TMRcmd_last[2]));
assign sdram_multiplexer_endpoint7_last = sdram_multiplexer_control78;
assign sdram_tmrbankmachine7_TMRcmd_ready = {3{sdram_multiplexer_endpoint7_ready}};
assign sdram_multiplexer_control79 = (((sdram_tmrbankmachine7_TMRcmd_first[0] & sdram_tmrbankmachine7_TMRcmd_first[1]) | (sdram_tmrbankmachine7_TMRcmd_first[1] & sdram_tmrbankmachine7_TMRcmd_first[2])) | (sdram_tmrbankmachine7_TMRcmd_first[0] & sdram_tmrbankmachine7_TMRcmd_first[2]));
assign sdram_multiplexer_endpoint7_first = sdram_multiplexer_control79;
assign sdram_multiplexer_control80 = (((sdram_tmrbankmachine7_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine7_TMRcmd_payload_a[27:14]) | (sdram_tmrbankmachine7_TMRcmd_payload_a[27:14] & sdram_tmrbankmachine7_TMRcmd_payload_a[41:28])) | (sdram_tmrbankmachine7_TMRcmd_payload_a[13:0] & sdram_tmrbankmachine7_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_endpoint7_payload_a = sdram_multiplexer_control80;
assign sdram_multiplexer_control81 = (((sdram_tmrbankmachine7_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine7_TMRcmd_payload_ba[5:3]) | (sdram_tmrbankmachine7_TMRcmd_payload_ba[5:3] & sdram_tmrbankmachine7_TMRcmd_payload_ba[8:6])) | (sdram_tmrbankmachine7_TMRcmd_payload_ba[2:0] & sdram_tmrbankmachine7_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_endpoint7_payload_ba = sdram_multiplexer_control81;
assign sdram_multiplexer_control82 = (((sdram_tmrbankmachine7_TMRcmd_payload_cas[0] & sdram_tmrbankmachine7_TMRcmd_payload_cas[1]) | (sdram_tmrbankmachine7_TMRcmd_payload_cas[1] & sdram_tmrbankmachine7_TMRcmd_payload_cas[2])) | (sdram_tmrbankmachine7_TMRcmd_payload_cas[0] & sdram_tmrbankmachine7_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_endpoint7_payload_cas = sdram_multiplexer_control82;
assign sdram_multiplexer_control83 = (((sdram_tmrbankmachine7_TMRcmd_payload_ras[0] & sdram_tmrbankmachine7_TMRcmd_payload_ras[1]) | (sdram_tmrbankmachine7_TMRcmd_payload_ras[1] & sdram_tmrbankmachine7_TMRcmd_payload_ras[2])) | (sdram_tmrbankmachine7_TMRcmd_payload_ras[0] & sdram_tmrbankmachine7_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_endpoint7_payload_ras = sdram_multiplexer_control83;
assign sdram_multiplexer_control84 = (((sdram_tmrbankmachine7_TMRcmd_payload_we[0] & sdram_tmrbankmachine7_TMRcmd_payload_we[1]) | (sdram_tmrbankmachine7_TMRcmd_payload_we[1] & sdram_tmrbankmachine7_TMRcmd_payload_we[2])) | (sdram_tmrbankmachine7_TMRcmd_payload_we[0] & sdram_tmrbankmachine7_TMRcmd_payload_we[2]));
assign sdram_multiplexer_endpoint7_payload_we = sdram_multiplexer_control84;
assign sdram_multiplexer_control85 = (((sdram_tmrbankmachine7_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine7_TMRcmd_payload_is_cmd[1]) | (sdram_tmrbankmachine7_TMRcmd_payload_is_cmd[1] & sdram_tmrbankmachine7_TMRcmd_payload_is_cmd[2])) | (sdram_tmrbankmachine7_TMRcmd_payload_is_cmd[0] & sdram_tmrbankmachine7_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_endpoint7_payload_is_cmd = sdram_multiplexer_control85;
assign sdram_multiplexer_control86 = (((sdram_tmrbankmachine7_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine7_TMRcmd_payload_is_read[1]) | (sdram_tmrbankmachine7_TMRcmd_payload_is_read[1] & sdram_tmrbankmachine7_TMRcmd_payload_is_read[2])) | (sdram_tmrbankmachine7_TMRcmd_payload_is_read[0] & sdram_tmrbankmachine7_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_endpoint7_payload_is_read = sdram_multiplexer_control86;
assign sdram_multiplexer_control87 = (((sdram_tmrbankmachine7_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine7_TMRcmd_payload_is_write[1]) | (sdram_tmrbankmachine7_TMRcmd_payload_is_write[1] & sdram_tmrbankmachine7_TMRcmd_payload_is_write[2])) | (sdram_tmrbankmachine7_TMRcmd_payload_is_write[0] & sdram_tmrbankmachine7_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_endpoint7_payload_is_write = sdram_multiplexer_control87;

// synthesis translate_off
reg dummy_d_94;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_cmd_valids <= 8'd0;
	sdram_multiplexer_choose_cmd_valids[0] <= (sdram_multiplexer_endpoint0_valid & (((sdram_multiplexer_endpoint0_payload_is_cmd & sdram_multiplexer_choose_cmd_want_cmds) & ((~((sdram_multiplexer_endpoint0_payload_ras & (~sdram_multiplexer_endpoint0_payload_cas)) & (~sdram_multiplexer_endpoint0_payload_we))) | sdram_multiplexer_choose_cmd_want_activates)) | ((sdram_multiplexer_endpoint0_payload_is_read == sdram_multiplexer_choose_cmd_want_reads) & (sdram_multiplexer_endpoint0_payload_is_write == sdram_multiplexer_choose_cmd_want_writes))));
	sdram_multiplexer_choose_cmd_valids[1] <= (sdram_multiplexer_endpoint1_valid & (((sdram_multiplexer_endpoint1_payload_is_cmd & sdram_multiplexer_choose_cmd_want_cmds) & ((~((sdram_multiplexer_endpoint1_payload_ras & (~sdram_multiplexer_endpoint1_payload_cas)) & (~sdram_multiplexer_endpoint1_payload_we))) | sdram_multiplexer_choose_cmd_want_activates)) | ((sdram_multiplexer_endpoint1_payload_is_read == sdram_multiplexer_choose_cmd_want_reads) & (sdram_multiplexer_endpoint1_payload_is_write == sdram_multiplexer_choose_cmd_want_writes))));
	sdram_multiplexer_choose_cmd_valids[2] <= (sdram_multiplexer_endpoint2_valid & (((sdram_multiplexer_endpoint2_payload_is_cmd & sdram_multiplexer_choose_cmd_want_cmds) & ((~((sdram_multiplexer_endpoint2_payload_ras & (~sdram_multiplexer_endpoint2_payload_cas)) & (~sdram_multiplexer_endpoint2_payload_we))) | sdram_multiplexer_choose_cmd_want_activates)) | ((sdram_multiplexer_endpoint2_payload_is_read == sdram_multiplexer_choose_cmd_want_reads) & (sdram_multiplexer_endpoint2_payload_is_write == sdram_multiplexer_choose_cmd_want_writes))));
	sdram_multiplexer_choose_cmd_valids[3] <= (sdram_multiplexer_endpoint3_valid & (((sdram_multiplexer_endpoint3_payload_is_cmd & sdram_multiplexer_choose_cmd_want_cmds) & ((~((sdram_multiplexer_endpoint3_payload_ras & (~sdram_multiplexer_endpoint3_payload_cas)) & (~sdram_multiplexer_endpoint3_payload_we))) | sdram_multiplexer_choose_cmd_want_activates)) | ((sdram_multiplexer_endpoint3_payload_is_read == sdram_multiplexer_choose_cmd_want_reads) & (sdram_multiplexer_endpoint3_payload_is_write == sdram_multiplexer_choose_cmd_want_writes))));
	sdram_multiplexer_choose_cmd_valids[4] <= (sdram_multiplexer_endpoint4_valid & (((sdram_multiplexer_endpoint4_payload_is_cmd & sdram_multiplexer_choose_cmd_want_cmds) & ((~((sdram_multiplexer_endpoint4_payload_ras & (~sdram_multiplexer_endpoint4_payload_cas)) & (~sdram_multiplexer_endpoint4_payload_we))) | sdram_multiplexer_choose_cmd_want_activates)) | ((sdram_multiplexer_endpoint4_payload_is_read == sdram_multiplexer_choose_cmd_want_reads) & (sdram_multiplexer_endpoint4_payload_is_write == sdram_multiplexer_choose_cmd_want_writes))));
	sdram_multiplexer_choose_cmd_valids[5] <= (sdram_multiplexer_endpoint5_valid & (((sdram_multiplexer_endpoint5_payload_is_cmd & sdram_multiplexer_choose_cmd_want_cmds) & ((~((sdram_multiplexer_endpoint5_payload_ras & (~sdram_multiplexer_endpoint5_payload_cas)) & (~sdram_multiplexer_endpoint5_payload_we))) | sdram_multiplexer_choose_cmd_want_activates)) | ((sdram_multiplexer_endpoint5_payload_is_read == sdram_multiplexer_choose_cmd_want_reads) & (sdram_multiplexer_endpoint5_payload_is_write == sdram_multiplexer_choose_cmd_want_writes))));
	sdram_multiplexer_choose_cmd_valids[6] <= (sdram_multiplexer_endpoint6_valid & (((sdram_multiplexer_endpoint6_payload_is_cmd & sdram_multiplexer_choose_cmd_want_cmds) & ((~((sdram_multiplexer_endpoint6_payload_ras & (~sdram_multiplexer_endpoint6_payload_cas)) & (~sdram_multiplexer_endpoint6_payload_we))) | sdram_multiplexer_choose_cmd_want_activates)) | ((sdram_multiplexer_endpoint6_payload_is_read == sdram_multiplexer_choose_cmd_want_reads) & (sdram_multiplexer_endpoint6_payload_is_write == sdram_multiplexer_choose_cmd_want_writes))));
	sdram_multiplexer_choose_cmd_valids[7] <= (sdram_multiplexer_endpoint7_valid & (((sdram_multiplexer_endpoint7_payload_is_cmd & sdram_multiplexer_choose_cmd_want_cmds) & ((~((sdram_multiplexer_endpoint7_payload_ras & (~sdram_multiplexer_endpoint7_payload_cas)) & (~sdram_multiplexer_endpoint7_payload_we))) | sdram_multiplexer_choose_cmd_want_activates)) | ((sdram_multiplexer_endpoint7_payload_is_read == sdram_multiplexer_choose_cmd_want_reads) & (sdram_multiplexer_endpoint7_payload_is_write == sdram_multiplexer_choose_cmd_want_writes))));
// synthesis translate_off
	dummy_d_94 <= dummy_s;
// synthesis translate_on
end
assign sdram_multiplexer_choose_cmd_request = sdram_multiplexer_choose_cmd_valids;
assign sdram_multiplexer_choose_cmd_cmd_valid = rhs_array_muxed0;
assign sdram_multiplexer_choose_cmd_cmd_payload_a = rhs_array_muxed1;
assign sdram_multiplexer_choose_cmd_cmd_payload_ba = rhs_array_muxed2;
assign sdram_multiplexer_choose_cmd_cmd_payload_is_read = rhs_array_muxed3;
assign sdram_multiplexer_choose_cmd_cmd_payload_is_write = rhs_array_muxed4;
assign sdram_multiplexer_choose_cmd_cmd_payload_is_cmd = rhs_array_muxed5;

// synthesis translate_off
reg dummy_d_95;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_cmd_cmd_payload_cas <= 1'd0;
	if (sdram_multiplexer_choose_cmd_cmd_valid) begin
		sdram_multiplexer_choose_cmd_cmd_payload_cas <= t_array_muxed0;
	end
// synthesis translate_off
	dummy_d_95 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_96;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_cmd_cmd_payload_ras <= 1'd0;
	if (sdram_multiplexer_choose_cmd_cmd_valid) begin
		sdram_multiplexer_choose_cmd_cmd_payload_ras <= t_array_muxed1;
	end
// synthesis translate_off
	dummy_d_96 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_97;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_cmd_cmd_payload_we <= 1'd0;
	if (sdram_multiplexer_choose_cmd_cmd_valid) begin
		sdram_multiplexer_choose_cmd_cmd_payload_we <= t_array_muxed2;
	end
// synthesis translate_off
	dummy_d_97 <= dummy_s;
// synthesis translate_on
end
assign sdram_multiplexer_choose_cmd_ce = (sdram_multiplexer_choose_cmd_cmd_ready | (~sdram_multiplexer_choose_cmd_cmd_valid));

// synthesis translate_off
reg dummy_d_98;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_req_valids <= 8'd0;
	sdram_multiplexer_choose_req_valids[0] <= (sdram_multiplexer_endpoint0_valid & (((sdram_multiplexer_endpoint0_payload_is_cmd & sdram_multiplexer_choose_req_want_cmds) & ((~((sdram_multiplexer_endpoint0_payload_ras & (~sdram_multiplexer_endpoint0_payload_cas)) & (~sdram_multiplexer_endpoint0_payload_we))) | sdram_multiplexer_choose_req_want_activates)) | ((sdram_multiplexer_endpoint0_payload_is_read == sdram_multiplexer_choose_req_want_reads) & (sdram_multiplexer_endpoint0_payload_is_write == sdram_multiplexer_choose_req_want_writes))));
	sdram_multiplexer_choose_req_valids[1] <= (sdram_multiplexer_endpoint1_valid & (((sdram_multiplexer_endpoint1_payload_is_cmd & sdram_multiplexer_choose_req_want_cmds) & ((~((sdram_multiplexer_endpoint1_payload_ras & (~sdram_multiplexer_endpoint1_payload_cas)) & (~sdram_multiplexer_endpoint1_payload_we))) | sdram_multiplexer_choose_req_want_activates)) | ((sdram_multiplexer_endpoint1_payload_is_read == sdram_multiplexer_choose_req_want_reads) & (sdram_multiplexer_endpoint1_payload_is_write == sdram_multiplexer_choose_req_want_writes))));
	sdram_multiplexer_choose_req_valids[2] <= (sdram_multiplexer_endpoint2_valid & (((sdram_multiplexer_endpoint2_payload_is_cmd & sdram_multiplexer_choose_req_want_cmds) & ((~((sdram_multiplexer_endpoint2_payload_ras & (~sdram_multiplexer_endpoint2_payload_cas)) & (~sdram_multiplexer_endpoint2_payload_we))) | sdram_multiplexer_choose_req_want_activates)) | ((sdram_multiplexer_endpoint2_payload_is_read == sdram_multiplexer_choose_req_want_reads) & (sdram_multiplexer_endpoint2_payload_is_write == sdram_multiplexer_choose_req_want_writes))));
	sdram_multiplexer_choose_req_valids[3] <= (sdram_multiplexer_endpoint3_valid & (((sdram_multiplexer_endpoint3_payload_is_cmd & sdram_multiplexer_choose_req_want_cmds) & ((~((sdram_multiplexer_endpoint3_payload_ras & (~sdram_multiplexer_endpoint3_payload_cas)) & (~sdram_multiplexer_endpoint3_payload_we))) | sdram_multiplexer_choose_req_want_activates)) | ((sdram_multiplexer_endpoint3_payload_is_read == sdram_multiplexer_choose_req_want_reads) & (sdram_multiplexer_endpoint3_payload_is_write == sdram_multiplexer_choose_req_want_writes))));
	sdram_multiplexer_choose_req_valids[4] <= (sdram_multiplexer_endpoint4_valid & (((sdram_multiplexer_endpoint4_payload_is_cmd & sdram_multiplexer_choose_req_want_cmds) & ((~((sdram_multiplexer_endpoint4_payload_ras & (~sdram_multiplexer_endpoint4_payload_cas)) & (~sdram_multiplexer_endpoint4_payload_we))) | sdram_multiplexer_choose_req_want_activates)) | ((sdram_multiplexer_endpoint4_payload_is_read == sdram_multiplexer_choose_req_want_reads) & (sdram_multiplexer_endpoint4_payload_is_write == sdram_multiplexer_choose_req_want_writes))));
	sdram_multiplexer_choose_req_valids[5] <= (sdram_multiplexer_endpoint5_valid & (((sdram_multiplexer_endpoint5_payload_is_cmd & sdram_multiplexer_choose_req_want_cmds) & ((~((sdram_multiplexer_endpoint5_payload_ras & (~sdram_multiplexer_endpoint5_payload_cas)) & (~sdram_multiplexer_endpoint5_payload_we))) | sdram_multiplexer_choose_req_want_activates)) | ((sdram_multiplexer_endpoint5_payload_is_read == sdram_multiplexer_choose_req_want_reads) & (sdram_multiplexer_endpoint5_payload_is_write == sdram_multiplexer_choose_req_want_writes))));
	sdram_multiplexer_choose_req_valids[6] <= (sdram_multiplexer_endpoint6_valid & (((sdram_multiplexer_endpoint6_payload_is_cmd & sdram_multiplexer_choose_req_want_cmds) & ((~((sdram_multiplexer_endpoint6_payload_ras & (~sdram_multiplexer_endpoint6_payload_cas)) & (~sdram_multiplexer_endpoint6_payload_we))) | sdram_multiplexer_choose_req_want_activates)) | ((sdram_multiplexer_endpoint6_payload_is_read == sdram_multiplexer_choose_req_want_reads) & (sdram_multiplexer_endpoint6_payload_is_write == sdram_multiplexer_choose_req_want_writes))));
	sdram_multiplexer_choose_req_valids[7] <= (sdram_multiplexer_endpoint7_valid & (((sdram_multiplexer_endpoint7_payload_is_cmd & sdram_multiplexer_choose_req_want_cmds) & ((~((sdram_multiplexer_endpoint7_payload_ras & (~sdram_multiplexer_endpoint7_payload_cas)) & (~sdram_multiplexer_endpoint7_payload_we))) | sdram_multiplexer_choose_req_want_activates)) | ((sdram_multiplexer_endpoint7_payload_is_read == sdram_multiplexer_choose_req_want_reads) & (sdram_multiplexer_endpoint7_payload_is_write == sdram_multiplexer_choose_req_want_writes))));
// synthesis translate_off
	dummy_d_98 <= dummy_s;
// synthesis translate_on
end
assign sdram_multiplexer_choose_req_request = sdram_multiplexer_choose_req_valids;
assign sdram_multiplexer_choose_req_cmd_valid = rhs_array_muxed6;
assign sdram_multiplexer_choose_req_cmd_payload_a = rhs_array_muxed7;
assign sdram_multiplexer_choose_req_cmd_payload_ba = rhs_array_muxed8;
assign sdram_multiplexer_choose_req_cmd_payload_is_read = rhs_array_muxed9;
assign sdram_multiplexer_choose_req_cmd_payload_is_write = rhs_array_muxed10;
assign sdram_multiplexer_choose_req_cmd_payload_is_cmd = rhs_array_muxed11;

// synthesis translate_off
reg dummy_d_99;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_req_cmd_payload_cas <= 1'd0;
	if (sdram_multiplexer_choose_req_cmd_valid) begin
		sdram_multiplexer_choose_req_cmd_payload_cas <= t_array_muxed3;
	end
// synthesis translate_off
	dummy_d_99 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_100;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_req_cmd_payload_ras <= 1'd0;
	if (sdram_multiplexer_choose_req_cmd_valid) begin
		sdram_multiplexer_choose_req_cmd_payload_ras <= t_array_muxed4;
	end
// synthesis translate_off
	dummy_d_100 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_101;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_req_cmd_payload_we <= 1'd0;
	if (sdram_multiplexer_choose_req_cmd_valid) begin
		sdram_multiplexer_choose_req_cmd_payload_we <= t_array_muxed5;
	end
// synthesis translate_off
	dummy_d_101 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_102;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_endpoint0_ready <= 1'd0;
	if (((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & (sdram_multiplexer_choose_cmd_grant == 1'd0))) begin
		sdram_multiplexer_endpoint0_ready <= 1'd1;
	end
	if (((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_grant == 1'd0))) begin
		sdram_multiplexer_endpoint0_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_102 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_103;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_endpoint1_ready <= 1'd0;
	if (((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & (sdram_multiplexer_choose_cmd_grant == 1'd1))) begin
		sdram_multiplexer_endpoint1_ready <= 1'd1;
	end
	if (((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_grant == 1'd1))) begin
		sdram_multiplexer_endpoint1_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_103 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_104;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_endpoint2_ready <= 1'd0;
	if (((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & (sdram_multiplexer_choose_cmd_grant == 2'd2))) begin
		sdram_multiplexer_endpoint2_ready <= 1'd1;
	end
	if (((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_grant == 2'd2))) begin
		sdram_multiplexer_endpoint2_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_104 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_105;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_endpoint3_ready <= 1'd0;
	if (((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & (sdram_multiplexer_choose_cmd_grant == 2'd3))) begin
		sdram_multiplexer_endpoint3_ready <= 1'd1;
	end
	if (((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_grant == 2'd3))) begin
		sdram_multiplexer_endpoint3_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_105 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_106;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_endpoint4_ready <= 1'd0;
	if (((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & (sdram_multiplexer_choose_cmd_grant == 3'd4))) begin
		sdram_multiplexer_endpoint4_ready <= 1'd1;
	end
	if (((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_grant == 3'd4))) begin
		sdram_multiplexer_endpoint4_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_106 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_107;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_endpoint5_ready <= 1'd0;
	if (((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & (sdram_multiplexer_choose_cmd_grant == 3'd5))) begin
		sdram_multiplexer_endpoint5_ready <= 1'd1;
	end
	if (((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_grant == 3'd5))) begin
		sdram_multiplexer_endpoint5_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_107 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_108;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_endpoint6_ready <= 1'd0;
	if (((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & (sdram_multiplexer_choose_cmd_grant == 3'd6))) begin
		sdram_multiplexer_endpoint6_ready <= 1'd1;
	end
	if (((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_grant == 3'd6))) begin
		sdram_multiplexer_endpoint6_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_108 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_109;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_endpoint7_ready <= 1'd0;
	if (((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & (sdram_multiplexer_choose_cmd_grant == 3'd7))) begin
		sdram_multiplexer_endpoint7_ready <= 1'd1;
	end
	if (((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & (sdram_multiplexer_choose_req_grant == 3'd7))) begin
		sdram_multiplexer_endpoint7_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_109 <= dummy_s;
// synthesis translate_on
end
assign sdram_multiplexer_choose_req_ce = (sdram_multiplexer_choose_req_cmd_ready | (~sdram_multiplexer_choose_req_cmd_valid));
assign sdram_multiplexer_control88 = (((sdram_TMRcmd_valid[0] & sdram_TMRcmd_valid[1]) | (sdram_TMRcmd_valid[1] & sdram_TMRcmd_valid[2])) | (sdram_TMRcmd_valid[0] & sdram_TMRcmd_valid[2]));
assign sdram_multiplexer_refreshCmd_valid = sdram_multiplexer_control88;
assign sdram_multiplexer_control89 = (((sdram_TMRcmd_last[0] & sdram_TMRcmd_last[1]) | (sdram_TMRcmd_last[1] & sdram_TMRcmd_last[2])) | (sdram_TMRcmd_last[0] & sdram_TMRcmd_last[2]));
assign sdram_multiplexer_refreshCmd_last = sdram_multiplexer_control89;
assign sdram_TMRcmd_ready = {3{sdram_multiplexer_refreshCmd_ready}};
assign sdram_multiplexer_control90 = (((sdram_TMRcmd_first[0] & sdram_TMRcmd_first[1]) | (sdram_TMRcmd_first[1] & sdram_TMRcmd_first[2])) | (sdram_TMRcmd_first[0] & sdram_TMRcmd_first[2]));
assign sdram_multiplexer_refreshCmd_first = sdram_multiplexer_control90;
assign sdram_multiplexer_control91 = (((sdram_TMRcmd_payload_a[13:0] & sdram_TMRcmd_payload_a[27:14]) | (sdram_TMRcmd_payload_a[27:14] & sdram_TMRcmd_payload_a[41:28])) | (sdram_TMRcmd_payload_a[13:0] & sdram_TMRcmd_payload_a[41:28]));
assign sdram_multiplexer_refreshCmd_payload_a = sdram_multiplexer_control91;
assign sdram_multiplexer_control92 = (((sdram_TMRcmd_payload_ba[2:0] & sdram_TMRcmd_payload_ba[5:3]) | (sdram_TMRcmd_payload_ba[5:3] & sdram_TMRcmd_payload_ba[8:6])) | (sdram_TMRcmd_payload_ba[2:0] & sdram_TMRcmd_payload_ba[8:6]));
assign sdram_multiplexer_refreshCmd_payload_ba = sdram_multiplexer_control92;
assign sdram_multiplexer_control93 = (((sdram_TMRcmd_payload_cas[0] & sdram_TMRcmd_payload_cas[1]) | (sdram_TMRcmd_payload_cas[1] & sdram_TMRcmd_payload_cas[2])) | (sdram_TMRcmd_payload_cas[0] & sdram_TMRcmd_payload_cas[2]));
assign sdram_multiplexer_refreshCmd_payload_cas = sdram_multiplexer_control93;
assign sdram_multiplexer_control94 = (((sdram_TMRcmd_payload_ras[0] & sdram_TMRcmd_payload_ras[1]) | (sdram_TMRcmd_payload_ras[1] & sdram_TMRcmd_payload_ras[2])) | (sdram_TMRcmd_payload_ras[0] & sdram_TMRcmd_payload_ras[2]));
assign sdram_multiplexer_refreshCmd_payload_ras = sdram_multiplexer_control94;
assign sdram_multiplexer_control95 = (((sdram_TMRcmd_payload_we[0] & sdram_TMRcmd_payload_we[1]) | (sdram_TMRcmd_payload_we[1] & sdram_TMRcmd_payload_we[2])) | (sdram_TMRcmd_payload_we[0] & sdram_TMRcmd_payload_we[2]));
assign sdram_multiplexer_refreshCmd_payload_we = sdram_multiplexer_control95;
assign sdram_multiplexer_control96 = (((sdram_TMRcmd_payload_is_cmd[0] & sdram_TMRcmd_payload_is_cmd[1]) | (sdram_TMRcmd_payload_is_cmd[1] & sdram_TMRcmd_payload_is_cmd[2])) | (sdram_TMRcmd_payload_is_cmd[0] & sdram_TMRcmd_payload_is_cmd[2]));
assign sdram_multiplexer_refreshCmd_payload_is_cmd = sdram_multiplexer_control96;
assign sdram_multiplexer_control97 = (((sdram_TMRcmd_payload_is_read[0] & sdram_TMRcmd_payload_is_read[1]) | (sdram_TMRcmd_payload_is_read[1] & sdram_TMRcmd_payload_is_read[2])) | (sdram_TMRcmd_payload_is_read[0] & sdram_TMRcmd_payload_is_read[2]));
assign sdram_multiplexer_refreshCmd_payload_is_read = sdram_multiplexer_control97;
assign sdram_multiplexer_control98 = (((sdram_TMRcmd_payload_is_write[0] & sdram_TMRcmd_payload_is_write[1]) | (sdram_TMRcmd_payload_is_write[1] & sdram_TMRcmd_payload_is_write[2])) | (sdram_TMRcmd_payload_is_write[0] & sdram_TMRcmd_payload_is_write[2]));
assign sdram_multiplexer_refreshCmd_payload_is_write = sdram_multiplexer_control98;
assign sdram_dfi_p0_reset_n = 1'd1;
assign sdram_dfi_p0_cke = {1{sdram_multiplexer_steerer4}};
assign sdram_dfi_p0_odt = {1{sdram_multiplexer_steerer5}};
assign sdram_dfi_p1_reset_n = 1'd1;
assign sdram_dfi_p1_cke = {1{sdram_multiplexer_steerer6}};
assign sdram_dfi_p1_odt = {1{sdram_multiplexer_steerer7}};
assign sdram_dfi_p2_reset_n = 1'd1;
assign sdram_dfi_p2_cke = {1{sdram_multiplexer_steerer8}};
assign sdram_dfi_p2_odt = {1{sdram_multiplexer_steerer9}};
assign sdram_dfi_p3_reset_n = 1'd1;
assign sdram_dfi_p3_cke = {1{sdram_multiplexer_steerer10}};
assign sdram_dfi_p3_odt = {1{sdram_multiplexer_steerer11}};
assign sdram_multiplexer_tfawcon_count = ((((sdram_multiplexer_tfawcon_window[0] + sdram_multiplexer_tfawcon_window[1]) + sdram_multiplexer_tfawcon_window[2]) + sdram_multiplexer_tfawcon_window[3]) + sdram_multiplexer_tfawcon_window[4]);
assign sdram_TMRinterface_rdata = {3{{sdram_dfi_p3_rddata, sdram_dfi_p2_rddata, sdram_dfi_p1_rddata, sdram_dfi_p0_rddata}}};
assign sdram_multiplexer_control99 = (((sdram_TMRinterface_wdata[255:0] & sdram_TMRinterface_wdata[511:256]) | (sdram_TMRinterface_wdata[511:256] & sdram_TMRinterface_wdata[767:512])) | (sdram_TMRinterface_wdata[255:0] & sdram_TMRinterface_wdata[767:512]));
assign {sdram_dfi_p3_wrdata, sdram_dfi_p2_wrdata, sdram_dfi_p1_wrdata, sdram_dfi_p0_wrdata} = sdram_multiplexer_control99;
assign sdram_multiplexer_control100 = (((slice_proxy786[31:0] & slice_proxy787[63:32]) | (slice_proxy788[63:32] & slice_proxy789[95:64])) | (slice_proxy790[31:0] & slice_proxy791[95:64]));
assign {sdram_dfi_p3_wrdata_mask, sdram_dfi_p2_wrdata_mask, sdram_dfi_p1_wrdata_mask, sdram_dfi_p0_wrdata_mask} = sdram_multiplexer_control100;

// synthesis translate_off
reg dummy_d_110;
// synthesis translate_on
always @(*) begin
	sdram_multiplexer_choose_cmd_want_activates <= 1'd0;
	sdram_multiplexer_choose_cmd_cmd_ready <= 1'd0;
	sdram_multiplexer_choose_req_want_reads <= 1'd0;
	sdram_multiplexer_choose_req_want_writes <= 1'd0;
	sdram_multiplexer_choose_req_cmd_ready <= 1'd0;
	sdram_multiplexer_refreshCmd_ready <= 1'd0;
	sdram_multiplexer_steerer0 <= 2'd0;
	sdram_multiplexer_steerer1 <= 2'd0;
	sdram_multiplexer_steerer2 <= 2'd0;
	sdram_multiplexer_steerer3 <= 2'd0;
	sdram_multiplexer_en0 <= 1'd0;
	sdram_multiplexer_en1 <= 1'd0;
	multiplexer_next_state <= 4'd0;
	multiplexer_next_state <= multiplexer_state;
	case (multiplexer_state)
		1'd1: begin
			sdram_multiplexer_en1 <= 1'd1;
			sdram_multiplexer_choose_req_want_writes <= 1'd1;
			if (1'd0) begin
				sdram_multiplexer_choose_req_cmd_ready <= (sdram_multiplexer_cas_allowed & ((~((sdram_multiplexer_choose_req_cmd_payload_ras & (~sdram_multiplexer_choose_req_cmd_payload_cas)) & (~sdram_multiplexer_choose_req_cmd_payload_we))) | sdram_multiplexer_ras_allowed));
			end else begin
				sdram_multiplexer_choose_cmd_want_activates <= sdram_multiplexer_ras_allowed;
				sdram_multiplexer_choose_cmd_cmd_ready <= ((~((sdram_multiplexer_choose_cmd_cmd_payload_ras & (~sdram_multiplexer_choose_cmd_cmd_payload_cas)) & (~sdram_multiplexer_choose_cmd_cmd_payload_we))) | sdram_multiplexer_ras_allowed);
				sdram_multiplexer_choose_req_cmd_ready <= sdram_multiplexer_cas_allowed;
			end
			sdram_multiplexer_steerer0 <= 1'd0;
			if ((ddrphy_wrphase_storage == 1'd0)) begin
				sdram_multiplexer_steerer0 <= 2'd2;
			end
			if ((sdram_multiplexer_wrcmdphase == 1'd0)) begin
				sdram_multiplexer_steerer0 <= 1'd1;
			end
			sdram_multiplexer_steerer1 <= 1'd0;
			if ((ddrphy_wrphase_storage == 1'd1)) begin
				sdram_multiplexer_steerer1 <= 2'd2;
			end
			if ((sdram_multiplexer_wrcmdphase == 1'd1)) begin
				sdram_multiplexer_steerer1 <= 1'd1;
			end
			sdram_multiplexer_steerer2 <= 1'd0;
			if ((ddrphy_wrphase_storage == 2'd2)) begin
				sdram_multiplexer_steerer2 <= 2'd2;
			end
			if ((sdram_multiplexer_wrcmdphase == 2'd2)) begin
				sdram_multiplexer_steerer2 <= 1'd1;
			end
			sdram_multiplexer_steerer3 <= 1'd0;
			if ((ddrphy_wrphase_storage == 2'd3)) begin
				sdram_multiplexer_steerer3 <= 2'd2;
			end
			if ((sdram_multiplexer_wrcmdphase == 2'd3)) begin
				sdram_multiplexer_steerer3 <= 1'd1;
			end
			if (sdram_multiplexer_read_available) begin
				if (((~sdram_multiplexer_write_available) | sdram_multiplexer_max_time1)) begin
					multiplexer_next_state <= 2'd3;
				end
			end
			if (sdram_multiplexer_go_to_refresh) begin
				multiplexer_next_state <= 2'd2;
			end
		end
		2'd2: begin
			sdram_multiplexer_steerer0 <= 2'd3;
			sdram_multiplexer_refreshCmd_ready <= 1'd1;
			if (sdram_multiplexer_refreshCmd_last) begin
				multiplexer_next_state <= 1'd0;
			end
		end
		2'd3: begin
			if (sdram_multiplexer_twtrcon_ready) begin
				multiplexer_next_state <= 1'd0;
			end
		end
		3'd4: begin
			multiplexer_next_state <= 3'd5;
		end
		3'd5: begin
			multiplexer_next_state <= 3'd6;
		end
		3'd6: begin
			multiplexer_next_state <= 3'd7;
		end
		3'd7: begin
			multiplexer_next_state <= 4'd8;
		end
		4'd8: begin
			multiplexer_next_state <= 4'd9;
		end
		4'd9: begin
			multiplexer_next_state <= 4'd10;
		end
		4'd10: begin
			multiplexer_next_state <= 1'd1;
		end
		default: begin
			sdram_multiplexer_en0 <= 1'd1;
			sdram_multiplexer_choose_req_want_reads <= 1'd1;
			if (1'd0) begin
				sdram_multiplexer_choose_req_cmd_ready <= (sdram_multiplexer_cas_allowed & ((~((sdram_multiplexer_choose_req_cmd_payload_ras & (~sdram_multiplexer_choose_req_cmd_payload_cas)) & (~sdram_multiplexer_choose_req_cmd_payload_we))) | sdram_multiplexer_ras_allowed));
			end else begin
				sdram_multiplexer_choose_cmd_want_activates <= sdram_multiplexer_ras_allowed;
				sdram_multiplexer_choose_cmd_cmd_ready <= ((~((sdram_multiplexer_choose_cmd_cmd_payload_ras & (~sdram_multiplexer_choose_cmd_cmd_payload_cas)) & (~sdram_multiplexer_choose_cmd_cmd_payload_we))) | sdram_multiplexer_ras_allowed);
				sdram_multiplexer_choose_req_cmd_ready <= sdram_multiplexer_cas_allowed;
			end
			sdram_multiplexer_steerer0 <= 1'd0;
			if ((ddrphy_rdphase_storage == 1'd0)) begin
				sdram_multiplexer_steerer0 <= 2'd2;
			end
			if ((sdram_multiplexer_rdcmdphase == 1'd0)) begin
				sdram_multiplexer_steerer0 <= 1'd1;
			end
			sdram_multiplexer_steerer1 <= 1'd0;
			if ((ddrphy_rdphase_storage == 1'd1)) begin
				sdram_multiplexer_steerer1 <= 2'd2;
			end
			if ((sdram_multiplexer_rdcmdphase == 1'd1)) begin
				sdram_multiplexer_steerer1 <= 1'd1;
			end
			sdram_multiplexer_steerer2 <= 1'd0;
			if ((ddrphy_rdphase_storage == 2'd2)) begin
				sdram_multiplexer_steerer2 <= 2'd2;
			end
			if ((sdram_multiplexer_rdcmdphase == 2'd2)) begin
				sdram_multiplexer_steerer2 <= 1'd1;
			end
			sdram_multiplexer_steerer3 <= 1'd0;
			if ((ddrphy_rdphase_storage == 2'd3)) begin
				sdram_multiplexer_steerer3 <= 2'd2;
			end
			if ((sdram_multiplexer_rdcmdphase == 2'd3)) begin
				sdram_multiplexer_steerer3 <= 1'd1;
			end
			if (sdram_multiplexer_write_available) begin
				if (((~sdram_multiplexer_read_available) | sdram_multiplexer_max_time0)) begin
					multiplexer_next_state <= 3'd4;
				end
			end
			if (sdram_multiplexer_go_to_refresh) begin
				multiplexer_next_state <= 2'd2;
			end
		end
	endcase
// synthesis translate_off
	dummy_d_110 <= dummy_s;
// synthesis translate_on
end
assign roundrobin0_request = {(((cmd_payload_addr[9:7] == 1'd0) & (~(((((((locked0 | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid)};
assign roundrobin0_ce = ((~interface_bank0_valid) & (~sdram_interface_bank0_lock));
assign sdram_interface_bank0_addr = rhs_array_muxed12;
assign sdram_interface_bank0_we = rhs_array_muxed13;
assign interface_bank0_valid = rhs_array_muxed14;
assign roundrobin1_request = {(((cmd_payload_addr[9:7] == 1'd1) & (~(((((((locked1 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid)};
assign roundrobin1_ce = ((~sdram_interface_bank1_valid) & (~sdram_interface_bank1_lock));
assign sdram_interface_bank1_addr = rhs_array_muxed15;
assign sdram_interface_bank1_we = rhs_array_muxed16;
assign sdram_interface_bank1_valid = rhs_array_muxed17;
assign roundrobin2_request = {(((cmd_payload_addr[9:7] == 2'd2) & (~(((((((locked2 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid)};
assign roundrobin2_ce = ((~sdram_interface_bank2_valid) & (~sdram_interface_bank2_lock));
assign sdram_interface_bank2_addr = rhs_array_muxed18;
assign sdram_interface_bank2_we = rhs_array_muxed19;
assign sdram_interface_bank2_valid = rhs_array_muxed20;
assign roundrobin3_request = {(((cmd_payload_addr[9:7] == 2'd3) & (~(((((((locked3 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid)};
assign roundrobin3_ce = ((~sdram_interface_bank3_valid) & (~sdram_interface_bank3_lock));
assign sdram_interface_bank3_addr = rhs_array_muxed21;
assign sdram_interface_bank3_we = rhs_array_muxed22;
assign sdram_interface_bank3_valid = rhs_array_muxed23;
assign roundrobin4_request = {(((cmd_payload_addr[9:7] == 3'd4) & (~(((((((locked4 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid)};
assign roundrobin4_ce = ((~sdram_interface_bank4_valid) & (~sdram_interface_bank4_lock));
assign sdram_interface_bank4_addr = rhs_array_muxed24;
assign sdram_interface_bank4_we = rhs_array_muxed25;
assign sdram_interface_bank4_valid = rhs_array_muxed26;
assign roundrobin5_request = {(((cmd_payload_addr[9:7] == 3'd5) & (~(((((((locked5 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid)};
assign roundrobin5_ce = ((~sdram_interface_bank5_valid) & (~sdram_interface_bank5_lock));
assign sdram_interface_bank5_addr = rhs_array_muxed27;
assign sdram_interface_bank5_we = rhs_array_muxed28;
assign sdram_interface_bank5_valid = rhs_array_muxed29;
assign roundrobin6_request = {(((cmd_payload_addr[9:7] == 3'd6) & (~(((((((locked6 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid)};
assign roundrobin6_ce = ((~sdram_interface_bank6_valid) & (~sdram_interface_bank6_lock));
assign sdram_interface_bank6_addr = rhs_array_muxed30;
assign sdram_interface_bank6_we = rhs_array_muxed31;
assign sdram_interface_bank6_valid = rhs_array_muxed32;
assign roundrobin7_request = {(((cmd_payload_addr[9:7] == 3'd7) & (~(((((((locked7 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))))) & port_cmd_valid)};
assign roundrobin7_ce = ((~sdram_interface_bank7_valid) & (~sdram_interface_bank7_lock));
assign sdram_interface_bank7_addr = rhs_array_muxed33;
assign sdram_interface_bank7_we = rhs_array_muxed34;
assign sdram_interface_bank7_valid = rhs_array_muxed35;

// synthesis translate_off
reg dummy_d_111;
// synthesis translate_on
always @(*) begin
	sdram_TMRinterface_wdata <= 768'd0;
	sdram_TMRinterface_wdata_we <= 96'd0;
	case ({new_master_wdata_ready1})
		1'd1: begin
			sdram_TMRinterface_wdata <= port_TMRwdata_payload_data;
			sdram_TMRinterface_wdata_we <= port_TMRwdata_payload_we;
		end
		default: begin
			sdram_TMRinterface_wdata <= 1'd0;
			sdram_TMRinterface_wdata_we <= 1'd0;
		end
	endcase
// synthesis translate_off
	dummy_d_111 <= dummy_s;
// synthesis translate_on
end
assign port_TMRrdata_payload_data = sdram_TMRinterface_rdata;
assign roundrobin0_grant = 1'd0;
assign roundrobin1_grant = 1'd0;
assign roundrobin2_grant = 1'd0;
assign roundrobin3_grant = 1'd0;
assign roundrobin4_grant = 1'd0;
assign roundrobin5_grant = 1'd0;
assign roundrobin6_grant = 1'd0;
assign roundrobin7_grant = 1'd0;
assign sdram_TMRinterface_bank0_valid = {3{interface_bank0_valid}};
assign control0 = (((sdram_TMRinterface_bank0_ready[0] & sdram_TMRinterface_bank0_ready[1]) | (sdram_TMRinterface_bank0_ready[1] & sdram_TMRinterface_bank0_ready[2])) | (sdram_TMRinterface_bank0_ready[0] & sdram_TMRinterface_bank0_ready[2]));
assign sdram_interface_bank0_ready = control0;
assign sdram_TMRinterface_bank0_we = {3{sdram_interface_bank0_we}};
assign sdram_TMRinterface_bank0_addr = {3{sdram_interface_bank0_addr}};
assign control1 = (((sdram_TMRinterface_bank0_lock[0] & sdram_TMRinterface_bank0_lock[1]) | (sdram_TMRinterface_bank0_lock[1] & sdram_TMRinterface_bank0_lock[2])) | (sdram_TMRinterface_bank0_lock[0] & sdram_TMRinterface_bank0_lock[2]));
assign sdram_interface_bank0_lock = control1;
assign control2 = (((sdram_TMRinterface_bank0_wdata_ready[0] & sdram_TMRinterface_bank0_wdata_ready[1]) | (sdram_TMRinterface_bank0_wdata_ready[1] & sdram_TMRinterface_bank0_wdata_ready[2])) | (sdram_TMRinterface_bank0_wdata_ready[0] & sdram_TMRinterface_bank0_wdata_ready[2]));
assign sdram_interface_bank0_wdata_ready = control2;
assign control3 = (((sdram_TMRinterface_bank0_rdata_valid[0] & sdram_TMRinterface_bank0_rdata_valid[1]) | (sdram_TMRinterface_bank0_rdata_valid[1] & sdram_TMRinterface_bank0_rdata_valid[2])) | (sdram_TMRinterface_bank0_rdata_valid[0] & sdram_TMRinterface_bank0_rdata_valid[2]));
assign sdram_interface_bank0_rdata_valid = control3;
assign sdram_TMRinterface_bank1_valid = {3{sdram_interface_bank1_valid}};
assign control4 = (((sdram_TMRinterface_bank1_ready[0] & sdram_TMRinterface_bank1_ready[1]) | (sdram_TMRinterface_bank1_ready[1] & sdram_TMRinterface_bank1_ready[2])) | (sdram_TMRinterface_bank1_ready[0] & sdram_TMRinterface_bank1_ready[2]));
assign sdram_interface_bank1_ready = control4;
assign sdram_TMRinterface_bank1_we = {3{sdram_interface_bank1_we}};
assign sdram_TMRinterface_bank1_addr = {3{sdram_interface_bank1_addr}};
assign control5 = (((sdram_TMRinterface_bank1_lock[0] & sdram_TMRinterface_bank1_lock[1]) | (sdram_TMRinterface_bank1_lock[1] & sdram_TMRinterface_bank1_lock[2])) | (sdram_TMRinterface_bank1_lock[0] & sdram_TMRinterface_bank1_lock[2]));
assign sdram_interface_bank1_lock = control5;
assign control6 = (((sdram_TMRinterface_bank1_wdata_ready[0] & sdram_TMRinterface_bank1_wdata_ready[1]) | (sdram_TMRinterface_bank1_wdata_ready[1] & sdram_TMRinterface_bank1_wdata_ready[2])) | (sdram_TMRinterface_bank1_wdata_ready[0] & sdram_TMRinterface_bank1_wdata_ready[2]));
assign sdram_interface_bank1_wdata_ready = control6;
assign control7 = (((sdram_TMRinterface_bank1_rdata_valid[0] & sdram_TMRinterface_bank1_rdata_valid[1]) | (sdram_TMRinterface_bank1_rdata_valid[1] & sdram_TMRinterface_bank1_rdata_valid[2])) | (sdram_TMRinterface_bank1_rdata_valid[0] & sdram_TMRinterface_bank1_rdata_valid[2]));
assign sdram_interface_bank1_rdata_valid = control7;
assign sdram_TMRinterface_bank2_valid = {3{sdram_interface_bank2_valid}};
assign control8 = (((sdram_TMRinterface_bank2_ready[0] & sdram_TMRinterface_bank2_ready[1]) | (sdram_TMRinterface_bank2_ready[1] & sdram_TMRinterface_bank2_ready[2])) | (sdram_TMRinterface_bank2_ready[0] & sdram_TMRinterface_bank2_ready[2]));
assign sdram_interface_bank2_ready = control8;
assign sdram_TMRinterface_bank2_we = {3{sdram_interface_bank2_we}};
assign sdram_TMRinterface_bank2_addr = {3{sdram_interface_bank2_addr}};
assign control9 = (((sdram_TMRinterface_bank2_lock[0] & sdram_TMRinterface_bank2_lock[1]) | (sdram_TMRinterface_bank2_lock[1] & sdram_TMRinterface_bank2_lock[2])) | (sdram_TMRinterface_bank2_lock[0] & sdram_TMRinterface_bank2_lock[2]));
assign sdram_interface_bank2_lock = control9;
assign control10 = (((sdram_TMRinterface_bank2_wdata_ready[0] & sdram_TMRinterface_bank2_wdata_ready[1]) | (sdram_TMRinterface_bank2_wdata_ready[1] & sdram_TMRinterface_bank2_wdata_ready[2])) | (sdram_TMRinterface_bank2_wdata_ready[0] & sdram_TMRinterface_bank2_wdata_ready[2]));
assign sdram_interface_bank2_wdata_ready = control10;
assign control11 = (((sdram_TMRinterface_bank2_rdata_valid[0] & sdram_TMRinterface_bank2_rdata_valid[1]) | (sdram_TMRinterface_bank2_rdata_valid[1] & sdram_TMRinterface_bank2_rdata_valid[2])) | (sdram_TMRinterface_bank2_rdata_valid[0] & sdram_TMRinterface_bank2_rdata_valid[2]));
assign sdram_interface_bank2_rdata_valid = control11;
assign sdram_TMRinterface_bank3_valid = {3{sdram_interface_bank3_valid}};
assign control12 = (((sdram_TMRinterface_bank3_ready[0] & sdram_TMRinterface_bank3_ready[1]) | (sdram_TMRinterface_bank3_ready[1] & sdram_TMRinterface_bank3_ready[2])) | (sdram_TMRinterface_bank3_ready[0] & sdram_TMRinterface_bank3_ready[2]));
assign sdram_interface_bank3_ready = control12;
assign sdram_TMRinterface_bank3_we = {3{sdram_interface_bank3_we}};
assign sdram_TMRinterface_bank3_addr = {3{sdram_interface_bank3_addr}};
assign control13 = (((sdram_TMRinterface_bank3_lock[0] & sdram_TMRinterface_bank3_lock[1]) | (sdram_TMRinterface_bank3_lock[1] & sdram_TMRinterface_bank3_lock[2])) | (sdram_TMRinterface_bank3_lock[0] & sdram_TMRinterface_bank3_lock[2]));
assign sdram_interface_bank3_lock = control13;
assign control14 = (((sdram_TMRinterface_bank3_wdata_ready[0] & sdram_TMRinterface_bank3_wdata_ready[1]) | (sdram_TMRinterface_bank3_wdata_ready[1] & sdram_TMRinterface_bank3_wdata_ready[2])) | (sdram_TMRinterface_bank3_wdata_ready[0] & sdram_TMRinterface_bank3_wdata_ready[2]));
assign sdram_interface_bank3_wdata_ready = control14;
assign control15 = (((sdram_TMRinterface_bank3_rdata_valid[0] & sdram_TMRinterface_bank3_rdata_valid[1]) | (sdram_TMRinterface_bank3_rdata_valid[1] & sdram_TMRinterface_bank3_rdata_valid[2])) | (sdram_TMRinterface_bank3_rdata_valid[0] & sdram_TMRinterface_bank3_rdata_valid[2]));
assign sdram_interface_bank3_rdata_valid = control15;
assign sdram_TMRinterface_bank4_valid = {3{sdram_interface_bank4_valid}};
assign control16 = (((sdram_TMRinterface_bank4_ready[0] & sdram_TMRinterface_bank4_ready[1]) | (sdram_TMRinterface_bank4_ready[1] & sdram_TMRinterface_bank4_ready[2])) | (sdram_TMRinterface_bank4_ready[0] & sdram_TMRinterface_bank4_ready[2]));
assign sdram_interface_bank4_ready = control16;
assign sdram_TMRinterface_bank4_we = {3{sdram_interface_bank4_we}};
assign sdram_TMRinterface_bank4_addr = {3{sdram_interface_bank4_addr}};
assign control17 = (((sdram_TMRinterface_bank4_lock[0] & sdram_TMRinterface_bank4_lock[1]) | (sdram_TMRinterface_bank4_lock[1] & sdram_TMRinterface_bank4_lock[2])) | (sdram_TMRinterface_bank4_lock[0] & sdram_TMRinterface_bank4_lock[2]));
assign sdram_interface_bank4_lock = control17;
assign control18 = (((sdram_TMRinterface_bank4_wdata_ready[0] & sdram_TMRinterface_bank4_wdata_ready[1]) | (sdram_TMRinterface_bank4_wdata_ready[1] & sdram_TMRinterface_bank4_wdata_ready[2])) | (sdram_TMRinterface_bank4_wdata_ready[0] & sdram_TMRinterface_bank4_wdata_ready[2]));
assign sdram_interface_bank4_wdata_ready = control18;
assign control19 = (((sdram_TMRinterface_bank4_rdata_valid[0] & sdram_TMRinterface_bank4_rdata_valid[1]) | (sdram_TMRinterface_bank4_rdata_valid[1] & sdram_TMRinterface_bank4_rdata_valid[2])) | (sdram_TMRinterface_bank4_rdata_valid[0] & sdram_TMRinterface_bank4_rdata_valid[2]));
assign sdram_interface_bank4_rdata_valid = control19;
assign sdram_TMRinterface_bank5_valid = {3{sdram_interface_bank5_valid}};
assign control20 = (((sdram_TMRinterface_bank5_ready[0] & sdram_TMRinterface_bank5_ready[1]) | (sdram_TMRinterface_bank5_ready[1] & sdram_TMRinterface_bank5_ready[2])) | (sdram_TMRinterface_bank5_ready[0] & sdram_TMRinterface_bank5_ready[2]));
assign sdram_interface_bank5_ready = control20;
assign sdram_TMRinterface_bank5_we = {3{sdram_interface_bank5_we}};
assign sdram_TMRinterface_bank5_addr = {3{sdram_interface_bank5_addr}};
assign control21 = (((sdram_TMRinterface_bank5_lock[0] & sdram_TMRinterface_bank5_lock[1]) | (sdram_TMRinterface_bank5_lock[1] & sdram_TMRinterface_bank5_lock[2])) | (sdram_TMRinterface_bank5_lock[0] & sdram_TMRinterface_bank5_lock[2]));
assign sdram_interface_bank5_lock = control21;
assign control22 = (((sdram_TMRinterface_bank5_wdata_ready[0] & sdram_TMRinterface_bank5_wdata_ready[1]) | (sdram_TMRinterface_bank5_wdata_ready[1] & sdram_TMRinterface_bank5_wdata_ready[2])) | (sdram_TMRinterface_bank5_wdata_ready[0] & sdram_TMRinterface_bank5_wdata_ready[2]));
assign sdram_interface_bank5_wdata_ready = control22;
assign control23 = (((sdram_TMRinterface_bank5_rdata_valid[0] & sdram_TMRinterface_bank5_rdata_valid[1]) | (sdram_TMRinterface_bank5_rdata_valid[1] & sdram_TMRinterface_bank5_rdata_valid[2])) | (sdram_TMRinterface_bank5_rdata_valid[0] & sdram_TMRinterface_bank5_rdata_valid[2]));
assign sdram_interface_bank5_rdata_valid = control23;
assign sdram_TMRinterface_bank6_valid = {3{sdram_interface_bank6_valid}};
assign control24 = (((sdram_TMRinterface_bank6_ready[0] & sdram_TMRinterface_bank6_ready[1]) | (sdram_TMRinterface_bank6_ready[1] & sdram_TMRinterface_bank6_ready[2])) | (sdram_TMRinterface_bank6_ready[0] & sdram_TMRinterface_bank6_ready[2]));
assign sdram_interface_bank6_ready = control24;
assign sdram_TMRinterface_bank6_we = {3{sdram_interface_bank6_we}};
assign sdram_TMRinterface_bank6_addr = {3{sdram_interface_bank6_addr}};
assign control25 = (((sdram_TMRinterface_bank6_lock[0] & sdram_TMRinterface_bank6_lock[1]) | (sdram_TMRinterface_bank6_lock[1] & sdram_TMRinterface_bank6_lock[2])) | (sdram_TMRinterface_bank6_lock[0] & sdram_TMRinterface_bank6_lock[2]));
assign sdram_interface_bank6_lock = control25;
assign control26 = (((sdram_TMRinterface_bank6_wdata_ready[0] & sdram_TMRinterface_bank6_wdata_ready[1]) | (sdram_TMRinterface_bank6_wdata_ready[1] & sdram_TMRinterface_bank6_wdata_ready[2])) | (sdram_TMRinterface_bank6_wdata_ready[0] & sdram_TMRinterface_bank6_wdata_ready[2]));
assign sdram_interface_bank6_wdata_ready = control26;
assign control27 = (((sdram_TMRinterface_bank6_rdata_valid[0] & sdram_TMRinterface_bank6_rdata_valid[1]) | (sdram_TMRinterface_bank6_rdata_valid[1] & sdram_TMRinterface_bank6_rdata_valid[2])) | (sdram_TMRinterface_bank6_rdata_valid[0] & sdram_TMRinterface_bank6_rdata_valid[2]));
assign sdram_interface_bank6_rdata_valid = control27;
assign sdram_TMRinterface_bank7_valid = {3{sdram_interface_bank7_valid}};
assign control28 = (((sdram_TMRinterface_bank7_ready[0] & sdram_TMRinterface_bank7_ready[1]) | (sdram_TMRinterface_bank7_ready[1] & sdram_TMRinterface_bank7_ready[2])) | (sdram_TMRinterface_bank7_ready[0] & sdram_TMRinterface_bank7_ready[2]));
assign sdram_interface_bank7_ready = control28;
assign sdram_TMRinterface_bank7_we = {3{sdram_interface_bank7_we}};
assign sdram_TMRinterface_bank7_addr = {3{sdram_interface_bank7_addr}};
assign control29 = (((sdram_TMRinterface_bank7_lock[0] & sdram_TMRinterface_bank7_lock[1]) | (sdram_TMRinterface_bank7_lock[1] & sdram_TMRinterface_bank7_lock[2])) | (sdram_TMRinterface_bank7_lock[0] & sdram_TMRinterface_bank7_lock[2]));
assign sdram_interface_bank7_lock = control29;
assign control30 = (((sdram_TMRinterface_bank7_wdata_ready[0] & sdram_TMRinterface_bank7_wdata_ready[1]) | (sdram_TMRinterface_bank7_wdata_ready[1] & sdram_TMRinterface_bank7_wdata_ready[2])) | (sdram_TMRinterface_bank7_wdata_ready[0] & sdram_TMRinterface_bank7_wdata_ready[2]));
assign sdram_interface_bank7_wdata_ready = control30;
assign control31 = (((sdram_TMRinterface_bank7_rdata_valid[0] & sdram_TMRinterface_bank7_rdata_valid[1]) | (sdram_TMRinterface_bank7_rdata_valid[1] & sdram_TMRinterface_bank7_rdata_valid[2])) | (sdram_TMRinterface_bank7_rdata_valid[0] & sdram_TMRinterface_bank7_rdata_valid[2]));
assign sdram_interface_bank7_rdata_valid = control31;
assign port_TMRcmd_ready = {3{((((((((1'd0 | (((roundrobin0_grant == 1'd0) & ((cmd_payload_addr[9:7] == 1'd0) & (~(((((((locked0 | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0)))))) & sdram_interface_bank0_ready)) | (((roundrobin1_grant == 1'd0) & ((cmd_payload_addr[9:7] == 1'd1) & (~(((((((locked1 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0)))))) & sdram_interface_bank1_ready)) | (((roundrobin2_grant == 1'd0) & ((cmd_payload_addr[9:7] == 2'd2) & (~(((((((locked2 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0)))))) & sdram_interface_bank2_ready)) | (((roundrobin3_grant == 1'd0) & ((cmd_payload_addr[9:7] == 2'd3) & (~(((((((locked3 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0)))))) & sdram_interface_bank3_ready)) | (((roundrobin4_grant == 1'd0) & ((cmd_payload_addr[9:7] == 3'd4) & (~(((((((locked4 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0)))))) & sdram_interface_bank4_ready)) | (((roundrobin5_grant == 1'd0) & ((cmd_payload_addr[9:7] == 3'd5) & (~(((((((locked5 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0)))))) & sdram_interface_bank5_ready)) | (((roundrobin6_grant == 1'd0) & ((cmd_payload_addr[9:7] == 3'd6) & (~(((((((locked6 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0)))))) & sdram_interface_bank6_ready)) | (((roundrobin7_grant == 1'd0) & ((cmd_payload_addr[9:7] == 3'd7) & (~(((((((locked7 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0)))))) & sdram_interface_bank7_ready))}};
assign control32 = (((port_TMRcmd_ready[0] & port_TMRcmd_ready[1]) | (port_TMRcmd_ready[1] & port_TMRcmd_ready[2])) | (port_TMRcmd_ready[0] & port_TMRcmd_ready[2]));
assign port_cmd_ready = control32;
assign port_TMRwdata_ready = {3{new_master_wdata_ready1}};
assign control33 = (((port_TMRwdata_ready[0] & port_TMRwdata_ready[1]) | (port_TMRwdata_ready[1] & port_TMRwdata_ready[2])) | (port_TMRwdata_ready[0] & port_TMRwdata_ready[2]));
assign port_wdata_ready = control33;
assign port_TMRrdata_valid = {3{new_master_rdata_valid8}};
assign control34 = (((port_TMRrdata_valid[0] & port_TMRrdata_valid[1]) | (port_TMRrdata_valid[1] & port_TMRrdata_valid[2])) | (port_TMRrdata_valid[0] & port_TMRrdata_valid[2]));
assign port_rdata_valid = control34;
assign port_TMRwdata_payload_data = {3{port_wdata_payload_data}};
assign port_TMRwdata_payload_we = {3{port_wdata_payload_we}};
assign control35 = (((port_TMRrdata_payload_data[255:0] & port_TMRrdata_payload_data[511:256]) | (port_TMRrdata_payload_data[511:256] & port_TMRrdata_payload_data[767:512])) | (port_TMRrdata_payload_data[255:0] & port_TMRrdata_payload_data[767:512]));
assign port_rdata_payload_data = control35;
assign slice_proxy0 = {sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address};
assign slice_proxy1 = {sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address};
assign slice_proxy2 = {sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address};
assign slice_proxy3 = {sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address};
assign slice_proxy4 = {sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address};
assign slice_proxy5 = {sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address, sdram_pi_mod1_inti_p0_address};
assign slice_proxy6 = {sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank};
assign slice_proxy7 = {sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank};
assign slice_proxy8 = {sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank};
assign slice_proxy9 = {sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank};
assign slice_proxy10 = {sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank};
assign slice_proxy11 = {sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank, sdram_pi_mod1_inti_p0_bank};
assign slice_proxy12 = {sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n};
assign slice_proxy13 = {sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n};
assign slice_proxy14 = {sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n};
assign slice_proxy15 = {sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n};
assign slice_proxy16 = {sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n};
assign slice_proxy17 = {sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n, sdram_pi_mod1_inti_p0_cas_n};
assign slice_proxy18 = {sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n};
assign slice_proxy19 = {sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n};
assign slice_proxy20 = {sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n};
assign slice_proxy21 = {sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n};
assign slice_proxy22 = {sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n};
assign slice_proxy23 = {sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n, sdram_pi_mod1_inti_p0_cs_n};
assign slice_proxy24 = {sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n};
assign slice_proxy25 = {sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n};
assign slice_proxy26 = {sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n};
assign slice_proxy27 = {sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n};
assign slice_proxy28 = {sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n};
assign slice_proxy29 = {sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n, sdram_pi_mod1_inti_p0_ras_n};
assign slice_proxy30 = {sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n};
assign slice_proxy31 = {sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n};
assign slice_proxy32 = {sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n};
assign slice_proxy33 = {sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n};
assign slice_proxy34 = {sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n};
assign slice_proxy35 = {sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n, sdram_pi_mod1_inti_p0_we_n};
assign slice_proxy36 = {sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke};
assign slice_proxy37 = {sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke};
assign slice_proxy38 = {sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke};
assign slice_proxy39 = {sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke};
assign slice_proxy40 = {sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke};
assign slice_proxy41 = {sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke, sdram_pi_mod1_inti_p0_cke};
assign slice_proxy42 = {sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt};
assign slice_proxy43 = {sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt};
assign slice_proxy44 = {sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt};
assign slice_proxy45 = {sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt};
assign slice_proxy46 = {sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt};
assign slice_proxy47 = {sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt, sdram_pi_mod1_inti_p0_odt};
assign slice_proxy48 = {sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n};
assign slice_proxy49 = {sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n};
assign slice_proxy50 = {sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n};
assign slice_proxy51 = {sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n};
assign slice_proxy52 = {sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n};
assign slice_proxy53 = {sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n, sdram_pi_mod1_inti_p0_reset_n};
assign slice_proxy54 = {sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n};
assign slice_proxy55 = {sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n};
assign slice_proxy56 = {sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n};
assign slice_proxy57 = {sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n};
assign slice_proxy58 = {sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n};
assign slice_proxy59 = {sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n, sdram_pi_mod1_inti_p0_act_n};
assign slice_proxy60 = {sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata};
assign slice_proxy61 = {sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata};
assign slice_proxy62 = {sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata};
assign slice_proxy63 = {sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata};
assign slice_proxy64 = {sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata};
assign slice_proxy65 = {sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata, sdram_pi_mod1_inti_p0_wrdata};
assign slice_proxy66 = {sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en};
assign slice_proxy67 = {sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en};
assign slice_proxy68 = {sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en};
assign slice_proxy69 = {sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en};
assign slice_proxy70 = {sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en};
assign slice_proxy71 = {sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en, sdram_pi_mod1_inti_p0_wrdata_en};
assign slice_proxy72 = {sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask};
assign slice_proxy73 = {sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask};
assign slice_proxy74 = {sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask};
assign slice_proxy75 = {sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask};
assign slice_proxy76 = {sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask};
assign slice_proxy77 = {sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask, sdram_pi_mod1_inti_p0_wrdata_mask};
assign slice_proxy78 = {sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en};
assign slice_proxy79 = {sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en};
assign slice_proxy80 = {sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en};
assign slice_proxy81 = {sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en};
assign slice_proxy82 = {sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en};
assign slice_proxy83 = {sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en, sdram_pi_mod1_inti_p0_rddata_en};
assign slice_proxy84 = {sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address};
assign slice_proxy85 = {sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address};
assign slice_proxy86 = {sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address};
assign slice_proxy87 = {sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address};
assign slice_proxy88 = {sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address};
assign slice_proxy89 = {sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address, sdram_pi_mod1_inti_p1_address};
assign slice_proxy90 = {sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank};
assign slice_proxy91 = {sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank};
assign slice_proxy92 = {sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank};
assign slice_proxy93 = {sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank};
assign slice_proxy94 = {sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank};
assign slice_proxy95 = {sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank, sdram_pi_mod1_inti_p1_bank};
assign slice_proxy96 = {sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n};
assign slice_proxy97 = {sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n};
assign slice_proxy98 = {sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n};
assign slice_proxy99 = {sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n};
assign slice_proxy100 = {sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n};
assign slice_proxy101 = {sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n, sdram_pi_mod1_inti_p1_cas_n};
assign slice_proxy102 = {sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n};
assign slice_proxy103 = {sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n};
assign slice_proxy104 = {sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n};
assign slice_proxy105 = {sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n};
assign slice_proxy106 = {sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n};
assign slice_proxy107 = {sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n, sdram_pi_mod1_inti_p1_cs_n};
assign slice_proxy108 = {sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n};
assign slice_proxy109 = {sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n};
assign slice_proxy110 = {sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n};
assign slice_proxy111 = {sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n};
assign slice_proxy112 = {sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n};
assign slice_proxy113 = {sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n, sdram_pi_mod1_inti_p1_ras_n};
assign slice_proxy114 = {sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n};
assign slice_proxy115 = {sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n};
assign slice_proxy116 = {sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n};
assign slice_proxy117 = {sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n};
assign slice_proxy118 = {sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n};
assign slice_proxy119 = {sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n, sdram_pi_mod1_inti_p1_we_n};
assign slice_proxy120 = {sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke};
assign slice_proxy121 = {sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke};
assign slice_proxy122 = {sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke};
assign slice_proxy123 = {sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke};
assign slice_proxy124 = {sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke};
assign slice_proxy125 = {sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke, sdram_pi_mod1_inti_p1_cke};
assign slice_proxy126 = {sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt};
assign slice_proxy127 = {sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt};
assign slice_proxy128 = {sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt};
assign slice_proxy129 = {sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt};
assign slice_proxy130 = {sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt};
assign slice_proxy131 = {sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt, sdram_pi_mod1_inti_p1_odt};
assign slice_proxy132 = {sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n};
assign slice_proxy133 = {sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n};
assign slice_proxy134 = {sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n};
assign slice_proxy135 = {sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n};
assign slice_proxy136 = {sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n};
assign slice_proxy137 = {sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n, sdram_pi_mod1_inti_p1_reset_n};
assign slice_proxy138 = {sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n};
assign slice_proxy139 = {sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n};
assign slice_proxy140 = {sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n};
assign slice_proxy141 = {sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n};
assign slice_proxy142 = {sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n};
assign slice_proxy143 = {sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n, sdram_pi_mod1_inti_p1_act_n};
assign slice_proxy144 = {sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata};
assign slice_proxy145 = {sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata};
assign slice_proxy146 = {sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata};
assign slice_proxy147 = {sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata};
assign slice_proxy148 = {sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata};
assign slice_proxy149 = {sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata, sdram_pi_mod1_inti_p1_wrdata};
assign slice_proxy150 = {sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en};
assign slice_proxy151 = {sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en};
assign slice_proxy152 = {sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en};
assign slice_proxy153 = {sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en};
assign slice_proxy154 = {sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en};
assign slice_proxy155 = {sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en, sdram_pi_mod1_inti_p1_wrdata_en};
assign slice_proxy156 = {sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask};
assign slice_proxy157 = {sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask};
assign slice_proxy158 = {sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask};
assign slice_proxy159 = {sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask};
assign slice_proxy160 = {sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask};
assign slice_proxy161 = {sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask, sdram_pi_mod1_inti_p1_wrdata_mask};
assign slice_proxy162 = {sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en};
assign slice_proxy163 = {sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en};
assign slice_proxy164 = {sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en};
assign slice_proxy165 = {sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en};
assign slice_proxy166 = {sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en};
assign slice_proxy167 = {sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en, sdram_pi_mod1_inti_p1_rddata_en};
assign slice_proxy168 = {sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address};
assign slice_proxy169 = {sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address};
assign slice_proxy170 = {sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address};
assign slice_proxy171 = {sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address};
assign slice_proxy172 = {sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address};
assign slice_proxy173 = {sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address, sdram_pi_mod1_inti_p2_address};
assign slice_proxy174 = {sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank};
assign slice_proxy175 = {sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank};
assign slice_proxy176 = {sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank};
assign slice_proxy177 = {sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank};
assign slice_proxy178 = {sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank};
assign slice_proxy179 = {sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank, sdram_pi_mod1_inti_p2_bank};
assign slice_proxy180 = {sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n};
assign slice_proxy181 = {sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n};
assign slice_proxy182 = {sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n};
assign slice_proxy183 = {sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n};
assign slice_proxy184 = {sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n};
assign slice_proxy185 = {sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n, sdram_pi_mod1_inti_p2_cas_n};
assign slice_proxy186 = {sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n};
assign slice_proxy187 = {sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n};
assign slice_proxy188 = {sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n};
assign slice_proxy189 = {sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n};
assign slice_proxy190 = {sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n};
assign slice_proxy191 = {sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n, sdram_pi_mod1_inti_p2_cs_n};
assign slice_proxy192 = {sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n};
assign slice_proxy193 = {sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n};
assign slice_proxy194 = {sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n};
assign slice_proxy195 = {sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n};
assign slice_proxy196 = {sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n};
assign slice_proxy197 = {sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n, sdram_pi_mod1_inti_p2_ras_n};
assign slice_proxy198 = {sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n};
assign slice_proxy199 = {sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n};
assign slice_proxy200 = {sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n};
assign slice_proxy201 = {sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n};
assign slice_proxy202 = {sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n};
assign slice_proxy203 = {sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n, sdram_pi_mod1_inti_p2_we_n};
assign slice_proxy204 = {sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke};
assign slice_proxy205 = {sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke};
assign slice_proxy206 = {sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke};
assign slice_proxy207 = {sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke};
assign slice_proxy208 = {sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke};
assign slice_proxy209 = {sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke, sdram_pi_mod1_inti_p2_cke};
assign slice_proxy210 = {sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt};
assign slice_proxy211 = {sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt};
assign slice_proxy212 = {sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt};
assign slice_proxy213 = {sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt};
assign slice_proxy214 = {sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt};
assign slice_proxy215 = {sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt, sdram_pi_mod1_inti_p2_odt};
assign slice_proxy216 = {sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n};
assign slice_proxy217 = {sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n};
assign slice_proxy218 = {sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n};
assign slice_proxy219 = {sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n};
assign slice_proxy220 = {sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n};
assign slice_proxy221 = {sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n, sdram_pi_mod1_inti_p2_reset_n};
assign slice_proxy222 = {sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n};
assign slice_proxy223 = {sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n};
assign slice_proxy224 = {sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n};
assign slice_proxy225 = {sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n};
assign slice_proxy226 = {sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n};
assign slice_proxy227 = {sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n, sdram_pi_mod1_inti_p2_act_n};
assign slice_proxy228 = {sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata};
assign slice_proxy229 = {sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata};
assign slice_proxy230 = {sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata};
assign slice_proxy231 = {sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata};
assign slice_proxy232 = {sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata};
assign slice_proxy233 = {sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata, sdram_pi_mod1_inti_p2_wrdata};
assign slice_proxy234 = {sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en};
assign slice_proxy235 = {sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en};
assign slice_proxy236 = {sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en};
assign slice_proxy237 = {sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en};
assign slice_proxy238 = {sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en};
assign slice_proxy239 = {sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en, sdram_pi_mod1_inti_p2_wrdata_en};
assign slice_proxy240 = {sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask};
assign slice_proxy241 = {sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask};
assign slice_proxy242 = {sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask};
assign slice_proxy243 = {sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask};
assign slice_proxy244 = {sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask};
assign slice_proxy245 = {sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask, sdram_pi_mod1_inti_p2_wrdata_mask};
assign slice_proxy246 = {sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en};
assign slice_proxy247 = {sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en};
assign slice_proxy248 = {sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en};
assign slice_proxy249 = {sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en};
assign slice_proxy250 = {sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en};
assign slice_proxy251 = {sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en, sdram_pi_mod1_inti_p2_rddata_en};
assign slice_proxy252 = {sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address};
assign slice_proxy253 = {sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address};
assign slice_proxy254 = {sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address};
assign slice_proxy255 = {sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address};
assign slice_proxy256 = {sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address};
assign slice_proxy257 = {sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address, sdram_pi_mod1_inti_p3_address};
assign slice_proxy258 = {sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank};
assign slice_proxy259 = {sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank};
assign slice_proxy260 = {sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank};
assign slice_proxy261 = {sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank};
assign slice_proxy262 = {sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank};
assign slice_proxy263 = {sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank, sdram_pi_mod1_inti_p3_bank};
assign slice_proxy264 = {sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n};
assign slice_proxy265 = {sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n};
assign slice_proxy266 = {sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n};
assign slice_proxy267 = {sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n};
assign slice_proxy268 = {sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n};
assign slice_proxy269 = {sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n, sdram_pi_mod1_inti_p3_cas_n};
assign slice_proxy270 = {sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n};
assign slice_proxy271 = {sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n};
assign slice_proxy272 = {sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n};
assign slice_proxy273 = {sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n};
assign slice_proxy274 = {sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n};
assign slice_proxy275 = {sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n, sdram_pi_mod1_inti_p3_cs_n};
assign slice_proxy276 = {sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n};
assign slice_proxy277 = {sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n};
assign slice_proxy278 = {sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n};
assign slice_proxy279 = {sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n};
assign slice_proxy280 = {sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n};
assign slice_proxy281 = {sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n, sdram_pi_mod1_inti_p3_ras_n};
assign slice_proxy282 = {sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n};
assign slice_proxy283 = {sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n};
assign slice_proxy284 = {sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n};
assign slice_proxy285 = {sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n};
assign slice_proxy286 = {sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n};
assign slice_proxy287 = {sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n, sdram_pi_mod1_inti_p3_we_n};
assign slice_proxy288 = {sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke};
assign slice_proxy289 = {sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke};
assign slice_proxy290 = {sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke};
assign slice_proxy291 = {sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke};
assign slice_proxy292 = {sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke};
assign slice_proxy293 = {sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke, sdram_pi_mod1_inti_p3_cke};
assign slice_proxy294 = {sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt};
assign slice_proxy295 = {sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt};
assign slice_proxy296 = {sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt};
assign slice_proxy297 = {sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt};
assign slice_proxy298 = {sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt};
assign slice_proxy299 = {sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt, sdram_pi_mod1_inti_p3_odt};
assign slice_proxy300 = {sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n};
assign slice_proxy301 = {sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n};
assign slice_proxy302 = {sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n};
assign slice_proxy303 = {sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n};
assign slice_proxy304 = {sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n};
assign slice_proxy305 = {sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n, sdram_pi_mod1_inti_p3_reset_n};
assign slice_proxy306 = {sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n};
assign slice_proxy307 = {sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n};
assign slice_proxy308 = {sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n};
assign slice_proxy309 = {sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n};
assign slice_proxy310 = {sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n};
assign slice_proxy311 = {sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n, sdram_pi_mod1_inti_p3_act_n};
assign slice_proxy312 = {sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata};
assign slice_proxy313 = {sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata};
assign slice_proxy314 = {sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata};
assign slice_proxy315 = {sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata};
assign slice_proxy316 = {sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata};
assign slice_proxy317 = {sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata, sdram_pi_mod1_inti_p3_wrdata};
assign slice_proxy318 = {sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en};
assign slice_proxy319 = {sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en};
assign slice_proxy320 = {sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en};
assign slice_proxy321 = {sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en};
assign slice_proxy322 = {sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en};
assign slice_proxy323 = {sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en, sdram_pi_mod1_inti_p3_wrdata_en};
assign slice_proxy324 = {sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask};
assign slice_proxy325 = {sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask};
assign slice_proxy326 = {sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask};
assign slice_proxy327 = {sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask};
assign slice_proxy328 = {sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask};
assign slice_proxy329 = {sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask, sdram_pi_mod1_inti_p3_wrdata_mask};
assign slice_proxy330 = {sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en};
assign slice_proxy331 = {sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en};
assign slice_proxy332 = {sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en};
assign slice_proxy333 = {sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en};
assign slice_proxy334 = {sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en};
assign slice_proxy335 = {sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en, sdram_pi_mod1_inti_p3_rddata_en};
assign slice_proxy336 = {sdram_timer3_done0, sdram_timer2_done0, sdram_timer_done0};
assign slice_proxy337 = {sdram_timer3_done0, sdram_timer2_done0, sdram_timer_done0};
assign slice_proxy338 = {sdram_timer3_done0, sdram_timer2_done0, sdram_timer_done0};
assign slice_proxy339 = {sdram_timer3_done0, sdram_timer2_done0, sdram_timer_done0};
assign slice_proxy340 = {sdram_timer3_done0, sdram_timer2_done0, sdram_timer_done0};
assign slice_proxy341 = {sdram_timer3_done0, sdram_timer2_done0, sdram_timer_done0};
assign slice_proxy342 = {sdram_postponer3_req_o, sdram_postponer2_req_o, sdram_postponer_req_o};
assign slice_proxy343 = {sdram_postponer3_req_o, sdram_postponer2_req_o, sdram_postponer_req_o};
assign slice_proxy344 = {sdram_postponer3_req_o, sdram_postponer2_req_o, sdram_postponer_req_o};
assign slice_proxy345 = {sdram_postponer3_req_o, sdram_postponer2_req_o, sdram_postponer_req_o};
assign slice_proxy346 = {sdram_postponer3_req_o, sdram_postponer2_req_o, sdram_postponer_req_o};
assign slice_proxy347 = {sdram_postponer3_req_o, sdram_postponer2_req_o, sdram_postponer_req_o};
assign slice_proxy348 = {sdram_sequencer3_done0, sdram_sequencer2_done0, sdram_sequencer_done0};
assign slice_proxy349 = {sdram_sequencer3_done0, sdram_sequencer2_done0, sdram_sequencer_done0};
assign slice_proxy350 = {sdram_sequencer3_done0, sdram_sequencer2_done0, sdram_sequencer_done0};
assign slice_proxy351 = {sdram_sequencer3_done0, sdram_sequencer2_done0, sdram_sequencer_done0};
assign slice_proxy352 = {sdram_sequencer3_done0, sdram_sequencer2_done0, sdram_sequencer_done0};
assign slice_proxy353 = {sdram_sequencer3_done0, sdram_sequencer2_done0, sdram_sequencer_done0};
assign slice_proxy354 = {(sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine0_cmd_buffer3_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine0_cmd_buffer2_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine0_cmd_buffer_source_valid)};
assign slice_proxy355 = {(sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine0_cmd_buffer3_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine0_cmd_buffer2_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine0_cmd_buffer_source_valid)};
assign slice_proxy356 = {(sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine0_cmd_buffer3_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine0_cmd_buffer2_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine0_cmd_buffer_source_valid)};
assign slice_proxy357 = {(sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine0_cmd_buffer3_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine0_cmd_buffer2_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine0_cmd_buffer_source_valid)};
assign slice_proxy358 = {(sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine0_cmd_buffer3_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine0_cmd_buffer2_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine0_cmd_buffer_source_valid)};
assign slice_proxy359 = {(sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine0_cmd_buffer3_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine0_cmd_buffer2_source_valid), (sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine0_cmd_buffer_source_valid)};
assign slice_proxy360 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy361 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy362 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy363 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy364 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy365 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy366 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_source_payload_addr};
assign slice_proxy367 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_source_payload_addr};
assign slice_proxy368 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_source_payload_addr};
assign slice_proxy369 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_source_payload_addr};
assign slice_proxy370 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_source_payload_addr};
assign slice_proxy371 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine0_cmd_buffer_source_payload_addr};
assign slice_proxy372 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid};
assign slice_proxy373 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid};
assign slice_proxy374 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid};
assign slice_proxy375 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid};
assign slice_proxy376 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid};
assign slice_proxy377 = {sdram_tmrbankmachine0_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine0_cmd_buffer_lookahead_source_valid};
assign slice_proxy378 = {sdram_tmrbankmachine0_cmd_buffer3_source_valid, sdram_tmrbankmachine0_cmd_buffer2_source_valid, sdram_tmrbankmachine0_cmd_buffer_source_valid};
assign slice_proxy379 = {sdram_tmrbankmachine0_cmd_buffer3_source_valid, sdram_tmrbankmachine0_cmd_buffer2_source_valid, sdram_tmrbankmachine0_cmd_buffer_source_valid};
assign slice_proxy380 = {sdram_tmrbankmachine0_cmd_buffer3_source_valid, sdram_tmrbankmachine0_cmd_buffer2_source_valid, sdram_tmrbankmachine0_cmd_buffer_source_valid};
assign slice_proxy381 = {sdram_tmrbankmachine0_cmd_buffer3_source_valid, sdram_tmrbankmachine0_cmd_buffer2_source_valid, sdram_tmrbankmachine0_cmd_buffer_source_valid};
assign slice_proxy382 = {sdram_tmrbankmachine0_cmd_buffer3_source_valid, sdram_tmrbankmachine0_cmd_buffer2_source_valid, sdram_tmrbankmachine0_cmd_buffer_source_valid};
assign slice_proxy383 = {sdram_tmrbankmachine0_cmd_buffer3_source_valid, sdram_tmrbankmachine0_cmd_buffer2_source_valid, sdram_tmrbankmachine0_cmd_buffer_source_valid};
assign slice_proxy384 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_we, sdram_tmrbankmachine0_cmd_buffer2_source_payload_we, sdram_tmrbankmachine0_cmd_buffer_source_payload_we};
assign slice_proxy385 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_we, sdram_tmrbankmachine0_cmd_buffer2_source_payload_we, sdram_tmrbankmachine0_cmd_buffer_source_payload_we};
assign slice_proxy386 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_we, sdram_tmrbankmachine0_cmd_buffer2_source_payload_we, sdram_tmrbankmachine0_cmd_buffer_source_payload_we};
assign slice_proxy387 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_we, sdram_tmrbankmachine0_cmd_buffer2_source_payload_we, sdram_tmrbankmachine0_cmd_buffer_source_payload_we};
assign slice_proxy388 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_we, sdram_tmrbankmachine0_cmd_buffer2_source_payload_we, sdram_tmrbankmachine0_cmd_buffer_source_payload_we};
assign slice_proxy389 = {sdram_tmrbankmachine0_cmd_buffer3_source_payload_we, sdram_tmrbankmachine0_cmd_buffer2_source_payload_we, sdram_tmrbankmachine0_cmd_buffer_source_payload_we};
assign slice_proxy390 = {sdram_tmrbankmachine0_twtpcon3_ready, sdram_tmrbankmachine0_twtpcon2_ready, sdram_tmrbankmachine0_twtpcon_ready};
assign slice_proxy391 = {sdram_tmrbankmachine0_twtpcon3_ready, sdram_tmrbankmachine0_twtpcon2_ready, sdram_tmrbankmachine0_twtpcon_ready};
assign slice_proxy392 = {sdram_tmrbankmachine0_twtpcon3_ready, sdram_tmrbankmachine0_twtpcon2_ready, sdram_tmrbankmachine0_twtpcon_ready};
assign slice_proxy393 = {sdram_tmrbankmachine0_twtpcon3_ready, sdram_tmrbankmachine0_twtpcon2_ready, sdram_tmrbankmachine0_twtpcon_ready};
assign slice_proxy394 = {sdram_tmrbankmachine0_twtpcon3_ready, sdram_tmrbankmachine0_twtpcon2_ready, sdram_tmrbankmachine0_twtpcon_ready};
assign slice_proxy395 = {sdram_tmrbankmachine0_twtpcon3_ready, sdram_tmrbankmachine0_twtpcon2_ready, sdram_tmrbankmachine0_twtpcon_ready};
assign slice_proxy396 = {sdram_tmrbankmachine0_trccon3_ready, sdram_tmrbankmachine0_trccon2_ready, sdram_tmrbankmachine0_trccon_ready};
assign slice_proxy397 = {sdram_tmrbankmachine0_trccon3_ready, sdram_tmrbankmachine0_trccon2_ready, sdram_tmrbankmachine0_trccon_ready};
assign slice_proxy398 = {sdram_tmrbankmachine0_trccon3_ready, sdram_tmrbankmachine0_trccon2_ready, sdram_tmrbankmachine0_trccon_ready};
assign slice_proxy399 = {sdram_tmrbankmachine0_trccon3_ready, sdram_tmrbankmachine0_trccon2_ready, sdram_tmrbankmachine0_trccon_ready};
assign slice_proxy400 = {sdram_tmrbankmachine0_trccon3_ready, sdram_tmrbankmachine0_trccon2_ready, sdram_tmrbankmachine0_trccon_ready};
assign slice_proxy401 = {sdram_tmrbankmachine0_trccon3_ready, sdram_tmrbankmachine0_trccon2_ready, sdram_tmrbankmachine0_trccon_ready};
assign slice_proxy402 = {sdram_tmrbankmachine0_trascon3_ready, sdram_tmrbankmachine0_trascon2_ready, sdram_tmrbankmachine0_trascon_ready};
assign slice_proxy403 = {sdram_tmrbankmachine0_trascon3_ready, sdram_tmrbankmachine0_trascon2_ready, sdram_tmrbankmachine0_trascon_ready};
assign slice_proxy404 = {sdram_tmrbankmachine0_trascon3_ready, sdram_tmrbankmachine0_trascon2_ready, sdram_tmrbankmachine0_trascon_ready};
assign slice_proxy405 = {sdram_tmrbankmachine0_trascon3_ready, sdram_tmrbankmachine0_trascon2_ready, sdram_tmrbankmachine0_trascon_ready};
assign slice_proxy406 = {sdram_tmrbankmachine0_trascon3_ready, sdram_tmrbankmachine0_trascon2_ready, sdram_tmrbankmachine0_trascon_ready};
assign slice_proxy407 = {sdram_tmrbankmachine0_trascon3_ready, sdram_tmrbankmachine0_trascon2_ready, sdram_tmrbankmachine0_trascon_ready};
assign slice_proxy408 = {(sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine1_cmd_buffer3_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine1_cmd_buffer2_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine1_cmd_buffer_source_valid)};
assign slice_proxy409 = {(sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine1_cmd_buffer3_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine1_cmd_buffer2_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine1_cmd_buffer_source_valid)};
assign slice_proxy410 = {(sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine1_cmd_buffer3_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine1_cmd_buffer2_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine1_cmd_buffer_source_valid)};
assign slice_proxy411 = {(sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine1_cmd_buffer3_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine1_cmd_buffer2_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine1_cmd_buffer_source_valid)};
assign slice_proxy412 = {(sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine1_cmd_buffer3_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine1_cmd_buffer2_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine1_cmd_buffer_source_valid)};
assign slice_proxy413 = {(sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine1_cmd_buffer3_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine1_cmd_buffer2_source_valid), (sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine1_cmd_buffer_source_valid)};
assign slice_proxy414 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy415 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy416 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy417 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy418 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy419 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy420 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_source_payload_addr};
assign slice_proxy421 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_source_payload_addr};
assign slice_proxy422 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_source_payload_addr};
assign slice_proxy423 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_source_payload_addr};
assign slice_proxy424 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_source_payload_addr};
assign slice_proxy425 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine1_cmd_buffer_source_payload_addr};
assign slice_proxy426 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid};
assign slice_proxy427 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid};
assign slice_proxy428 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid};
assign slice_proxy429 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid};
assign slice_proxy430 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid};
assign slice_proxy431 = {sdram_tmrbankmachine1_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine1_cmd_buffer_lookahead_source_valid};
assign slice_proxy432 = {sdram_tmrbankmachine1_cmd_buffer3_source_valid, sdram_tmrbankmachine1_cmd_buffer2_source_valid, sdram_tmrbankmachine1_cmd_buffer_source_valid};
assign slice_proxy433 = {sdram_tmrbankmachine1_cmd_buffer3_source_valid, sdram_tmrbankmachine1_cmd_buffer2_source_valid, sdram_tmrbankmachine1_cmd_buffer_source_valid};
assign slice_proxy434 = {sdram_tmrbankmachine1_cmd_buffer3_source_valid, sdram_tmrbankmachine1_cmd_buffer2_source_valid, sdram_tmrbankmachine1_cmd_buffer_source_valid};
assign slice_proxy435 = {sdram_tmrbankmachine1_cmd_buffer3_source_valid, sdram_tmrbankmachine1_cmd_buffer2_source_valid, sdram_tmrbankmachine1_cmd_buffer_source_valid};
assign slice_proxy436 = {sdram_tmrbankmachine1_cmd_buffer3_source_valid, sdram_tmrbankmachine1_cmd_buffer2_source_valid, sdram_tmrbankmachine1_cmd_buffer_source_valid};
assign slice_proxy437 = {sdram_tmrbankmachine1_cmd_buffer3_source_valid, sdram_tmrbankmachine1_cmd_buffer2_source_valid, sdram_tmrbankmachine1_cmd_buffer_source_valid};
assign slice_proxy438 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_we, sdram_tmrbankmachine1_cmd_buffer2_source_payload_we, sdram_tmrbankmachine1_cmd_buffer_source_payload_we};
assign slice_proxy439 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_we, sdram_tmrbankmachine1_cmd_buffer2_source_payload_we, sdram_tmrbankmachine1_cmd_buffer_source_payload_we};
assign slice_proxy440 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_we, sdram_tmrbankmachine1_cmd_buffer2_source_payload_we, sdram_tmrbankmachine1_cmd_buffer_source_payload_we};
assign slice_proxy441 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_we, sdram_tmrbankmachine1_cmd_buffer2_source_payload_we, sdram_tmrbankmachine1_cmd_buffer_source_payload_we};
assign slice_proxy442 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_we, sdram_tmrbankmachine1_cmd_buffer2_source_payload_we, sdram_tmrbankmachine1_cmd_buffer_source_payload_we};
assign slice_proxy443 = {sdram_tmrbankmachine1_cmd_buffer3_source_payload_we, sdram_tmrbankmachine1_cmd_buffer2_source_payload_we, sdram_tmrbankmachine1_cmd_buffer_source_payload_we};
assign slice_proxy444 = {sdram_tmrbankmachine1_twtpcon3_ready, sdram_tmrbankmachine1_twtpcon2_ready, sdram_tmrbankmachine1_twtpcon_ready};
assign slice_proxy445 = {sdram_tmrbankmachine1_twtpcon3_ready, sdram_tmrbankmachine1_twtpcon2_ready, sdram_tmrbankmachine1_twtpcon_ready};
assign slice_proxy446 = {sdram_tmrbankmachine1_twtpcon3_ready, sdram_tmrbankmachine1_twtpcon2_ready, sdram_tmrbankmachine1_twtpcon_ready};
assign slice_proxy447 = {sdram_tmrbankmachine1_twtpcon3_ready, sdram_tmrbankmachine1_twtpcon2_ready, sdram_tmrbankmachine1_twtpcon_ready};
assign slice_proxy448 = {sdram_tmrbankmachine1_twtpcon3_ready, sdram_tmrbankmachine1_twtpcon2_ready, sdram_tmrbankmachine1_twtpcon_ready};
assign slice_proxy449 = {sdram_tmrbankmachine1_twtpcon3_ready, sdram_tmrbankmachine1_twtpcon2_ready, sdram_tmrbankmachine1_twtpcon_ready};
assign slice_proxy450 = {sdram_tmrbankmachine1_trccon3_ready, sdram_tmrbankmachine1_trccon2_ready, sdram_tmrbankmachine1_trccon_ready};
assign slice_proxy451 = {sdram_tmrbankmachine1_trccon3_ready, sdram_tmrbankmachine1_trccon2_ready, sdram_tmrbankmachine1_trccon_ready};
assign slice_proxy452 = {sdram_tmrbankmachine1_trccon3_ready, sdram_tmrbankmachine1_trccon2_ready, sdram_tmrbankmachine1_trccon_ready};
assign slice_proxy453 = {sdram_tmrbankmachine1_trccon3_ready, sdram_tmrbankmachine1_trccon2_ready, sdram_tmrbankmachine1_trccon_ready};
assign slice_proxy454 = {sdram_tmrbankmachine1_trccon3_ready, sdram_tmrbankmachine1_trccon2_ready, sdram_tmrbankmachine1_trccon_ready};
assign slice_proxy455 = {sdram_tmrbankmachine1_trccon3_ready, sdram_tmrbankmachine1_trccon2_ready, sdram_tmrbankmachine1_trccon_ready};
assign slice_proxy456 = {sdram_tmrbankmachine1_trascon3_ready, sdram_tmrbankmachine1_trascon2_ready, sdram_tmrbankmachine1_trascon_ready};
assign slice_proxy457 = {sdram_tmrbankmachine1_trascon3_ready, sdram_tmrbankmachine1_trascon2_ready, sdram_tmrbankmachine1_trascon_ready};
assign slice_proxy458 = {sdram_tmrbankmachine1_trascon3_ready, sdram_tmrbankmachine1_trascon2_ready, sdram_tmrbankmachine1_trascon_ready};
assign slice_proxy459 = {sdram_tmrbankmachine1_trascon3_ready, sdram_tmrbankmachine1_trascon2_ready, sdram_tmrbankmachine1_trascon_ready};
assign slice_proxy460 = {sdram_tmrbankmachine1_trascon3_ready, sdram_tmrbankmachine1_trascon2_ready, sdram_tmrbankmachine1_trascon_ready};
assign slice_proxy461 = {sdram_tmrbankmachine1_trascon3_ready, sdram_tmrbankmachine1_trascon2_ready, sdram_tmrbankmachine1_trascon_ready};
assign slice_proxy462 = {(sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine2_cmd_buffer3_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine2_cmd_buffer2_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine2_cmd_buffer_source_valid)};
assign slice_proxy463 = {(sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine2_cmd_buffer3_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine2_cmd_buffer2_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine2_cmd_buffer_source_valid)};
assign slice_proxy464 = {(sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine2_cmd_buffer3_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine2_cmd_buffer2_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine2_cmd_buffer_source_valid)};
assign slice_proxy465 = {(sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine2_cmd_buffer3_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine2_cmd_buffer2_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine2_cmd_buffer_source_valid)};
assign slice_proxy466 = {(sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine2_cmd_buffer3_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine2_cmd_buffer2_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine2_cmd_buffer_source_valid)};
assign slice_proxy467 = {(sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine2_cmd_buffer3_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine2_cmd_buffer2_source_valid), (sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine2_cmd_buffer_source_valid)};
assign slice_proxy468 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy469 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy470 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy471 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy472 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy473 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy474 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_source_payload_addr};
assign slice_proxy475 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_source_payload_addr};
assign slice_proxy476 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_source_payload_addr};
assign slice_proxy477 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_source_payload_addr};
assign slice_proxy478 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_source_payload_addr};
assign slice_proxy479 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine2_cmd_buffer_source_payload_addr};
assign slice_proxy480 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid};
assign slice_proxy481 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid};
assign slice_proxy482 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid};
assign slice_proxy483 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid};
assign slice_proxy484 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid};
assign slice_proxy485 = {sdram_tmrbankmachine2_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine2_cmd_buffer_lookahead_source_valid};
assign slice_proxy486 = {sdram_tmrbankmachine2_cmd_buffer3_source_valid, sdram_tmrbankmachine2_cmd_buffer2_source_valid, sdram_tmrbankmachine2_cmd_buffer_source_valid};
assign slice_proxy487 = {sdram_tmrbankmachine2_cmd_buffer3_source_valid, sdram_tmrbankmachine2_cmd_buffer2_source_valid, sdram_tmrbankmachine2_cmd_buffer_source_valid};
assign slice_proxy488 = {sdram_tmrbankmachine2_cmd_buffer3_source_valid, sdram_tmrbankmachine2_cmd_buffer2_source_valid, sdram_tmrbankmachine2_cmd_buffer_source_valid};
assign slice_proxy489 = {sdram_tmrbankmachine2_cmd_buffer3_source_valid, sdram_tmrbankmachine2_cmd_buffer2_source_valid, sdram_tmrbankmachine2_cmd_buffer_source_valid};
assign slice_proxy490 = {sdram_tmrbankmachine2_cmd_buffer3_source_valid, sdram_tmrbankmachine2_cmd_buffer2_source_valid, sdram_tmrbankmachine2_cmd_buffer_source_valid};
assign slice_proxy491 = {sdram_tmrbankmachine2_cmd_buffer3_source_valid, sdram_tmrbankmachine2_cmd_buffer2_source_valid, sdram_tmrbankmachine2_cmd_buffer_source_valid};
assign slice_proxy492 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_we, sdram_tmrbankmachine2_cmd_buffer2_source_payload_we, sdram_tmrbankmachine2_cmd_buffer_source_payload_we};
assign slice_proxy493 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_we, sdram_tmrbankmachine2_cmd_buffer2_source_payload_we, sdram_tmrbankmachine2_cmd_buffer_source_payload_we};
assign slice_proxy494 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_we, sdram_tmrbankmachine2_cmd_buffer2_source_payload_we, sdram_tmrbankmachine2_cmd_buffer_source_payload_we};
assign slice_proxy495 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_we, sdram_tmrbankmachine2_cmd_buffer2_source_payload_we, sdram_tmrbankmachine2_cmd_buffer_source_payload_we};
assign slice_proxy496 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_we, sdram_tmrbankmachine2_cmd_buffer2_source_payload_we, sdram_tmrbankmachine2_cmd_buffer_source_payload_we};
assign slice_proxy497 = {sdram_tmrbankmachine2_cmd_buffer3_source_payload_we, sdram_tmrbankmachine2_cmd_buffer2_source_payload_we, sdram_tmrbankmachine2_cmd_buffer_source_payload_we};
assign slice_proxy498 = {sdram_tmrbankmachine2_twtpcon3_ready, sdram_tmrbankmachine2_twtpcon2_ready, sdram_tmrbankmachine2_twtpcon_ready};
assign slice_proxy499 = {sdram_tmrbankmachine2_twtpcon3_ready, sdram_tmrbankmachine2_twtpcon2_ready, sdram_tmrbankmachine2_twtpcon_ready};
assign slice_proxy500 = {sdram_tmrbankmachine2_twtpcon3_ready, sdram_tmrbankmachine2_twtpcon2_ready, sdram_tmrbankmachine2_twtpcon_ready};
assign slice_proxy501 = {sdram_tmrbankmachine2_twtpcon3_ready, sdram_tmrbankmachine2_twtpcon2_ready, sdram_tmrbankmachine2_twtpcon_ready};
assign slice_proxy502 = {sdram_tmrbankmachine2_twtpcon3_ready, sdram_tmrbankmachine2_twtpcon2_ready, sdram_tmrbankmachine2_twtpcon_ready};
assign slice_proxy503 = {sdram_tmrbankmachine2_twtpcon3_ready, sdram_tmrbankmachine2_twtpcon2_ready, sdram_tmrbankmachine2_twtpcon_ready};
assign slice_proxy504 = {sdram_tmrbankmachine2_trccon3_ready, sdram_tmrbankmachine2_trccon2_ready, sdram_tmrbankmachine2_trccon_ready};
assign slice_proxy505 = {sdram_tmrbankmachine2_trccon3_ready, sdram_tmrbankmachine2_trccon2_ready, sdram_tmrbankmachine2_trccon_ready};
assign slice_proxy506 = {sdram_tmrbankmachine2_trccon3_ready, sdram_tmrbankmachine2_trccon2_ready, sdram_tmrbankmachine2_trccon_ready};
assign slice_proxy507 = {sdram_tmrbankmachine2_trccon3_ready, sdram_tmrbankmachine2_trccon2_ready, sdram_tmrbankmachine2_trccon_ready};
assign slice_proxy508 = {sdram_tmrbankmachine2_trccon3_ready, sdram_tmrbankmachine2_trccon2_ready, sdram_tmrbankmachine2_trccon_ready};
assign slice_proxy509 = {sdram_tmrbankmachine2_trccon3_ready, sdram_tmrbankmachine2_trccon2_ready, sdram_tmrbankmachine2_trccon_ready};
assign slice_proxy510 = {sdram_tmrbankmachine2_trascon3_ready, sdram_tmrbankmachine2_trascon2_ready, sdram_tmrbankmachine2_trascon_ready};
assign slice_proxy511 = {sdram_tmrbankmachine2_trascon3_ready, sdram_tmrbankmachine2_trascon2_ready, sdram_tmrbankmachine2_trascon_ready};
assign slice_proxy512 = {sdram_tmrbankmachine2_trascon3_ready, sdram_tmrbankmachine2_trascon2_ready, sdram_tmrbankmachine2_trascon_ready};
assign slice_proxy513 = {sdram_tmrbankmachine2_trascon3_ready, sdram_tmrbankmachine2_trascon2_ready, sdram_tmrbankmachine2_trascon_ready};
assign slice_proxy514 = {sdram_tmrbankmachine2_trascon3_ready, sdram_tmrbankmachine2_trascon2_ready, sdram_tmrbankmachine2_trascon_ready};
assign slice_proxy515 = {sdram_tmrbankmachine2_trascon3_ready, sdram_tmrbankmachine2_trascon2_ready, sdram_tmrbankmachine2_trascon_ready};
assign slice_proxy516 = {(sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine3_cmd_buffer3_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine3_cmd_buffer2_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine3_cmd_buffer_source_valid)};
assign slice_proxy517 = {(sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine3_cmd_buffer3_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine3_cmd_buffer2_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine3_cmd_buffer_source_valid)};
assign slice_proxy518 = {(sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine3_cmd_buffer3_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine3_cmd_buffer2_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine3_cmd_buffer_source_valid)};
assign slice_proxy519 = {(sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine3_cmd_buffer3_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine3_cmd_buffer2_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine3_cmd_buffer_source_valid)};
assign slice_proxy520 = {(sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine3_cmd_buffer3_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine3_cmd_buffer2_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine3_cmd_buffer_source_valid)};
assign slice_proxy521 = {(sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine3_cmd_buffer3_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine3_cmd_buffer2_source_valid), (sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine3_cmd_buffer_source_valid)};
assign slice_proxy522 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy523 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy524 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy525 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy526 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy527 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy528 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_source_payload_addr};
assign slice_proxy529 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_source_payload_addr};
assign slice_proxy530 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_source_payload_addr};
assign slice_proxy531 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_source_payload_addr};
assign slice_proxy532 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_source_payload_addr};
assign slice_proxy533 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine3_cmd_buffer_source_payload_addr};
assign slice_proxy534 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid};
assign slice_proxy535 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid};
assign slice_proxy536 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid};
assign slice_proxy537 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid};
assign slice_proxy538 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid};
assign slice_proxy539 = {sdram_tmrbankmachine3_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine3_cmd_buffer_lookahead_source_valid};
assign slice_proxy540 = {sdram_tmrbankmachine3_cmd_buffer3_source_valid, sdram_tmrbankmachine3_cmd_buffer2_source_valid, sdram_tmrbankmachine3_cmd_buffer_source_valid};
assign slice_proxy541 = {sdram_tmrbankmachine3_cmd_buffer3_source_valid, sdram_tmrbankmachine3_cmd_buffer2_source_valid, sdram_tmrbankmachine3_cmd_buffer_source_valid};
assign slice_proxy542 = {sdram_tmrbankmachine3_cmd_buffer3_source_valid, sdram_tmrbankmachine3_cmd_buffer2_source_valid, sdram_tmrbankmachine3_cmd_buffer_source_valid};
assign slice_proxy543 = {sdram_tmrbankmachine3_cmd_buffer3_source_valid, sdram_tmrbankmachine3_cmd_buffer2_source_valid, sdram_tmrbankmachine3_cmd_buffer_source_valid};
assign slice_proxy544 = {sdram_tmrbankmachine3_cmd_buffer3_source_valid, sdram_tmrbankmachine3_cmd_buffer2_source_valid, sdram_tmrbankmachine3_cmd_buffer_source_valid};
assign slice_proxy545 = {sdram_tmrbankmachine3_cmd_buffer3_source_valid, sdram_tmrbankmachine3_cmd_buffer2_source_valid, sdram_tmrbankmachine3_cmd_buffer_source_valid};
assign slice_proxy546 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_we, sdram_tmrbankmachine3_cmd_buffer2_source_payload_we, sdram_tmrbankmachine3_cmd_buffer_source_payload_we};
assign slice_proxy547 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_we, sdram_tmrbankmachine3_cmd_buffer2_source_payload_we, sdram_tmrbankmachine3_cmd_buffer_source_payload_we};
assign slice_proxy548 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_we, sdram_tmrbankmachine3_cmd_buffer2_source_payload_we, sdram_tmrbankmachine3_cmd_buffer_source_payload_we};
assign slice_proxy549 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_we, sdram_tmrbankmachine3_cmd_buffer2_source_payload_we, sdram_tmrbankmachine3_cmd_buffer_source_payload_we};
assign slice_proxy550 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_we, sdram_tmrbankmachine3_cmd_buffer2_source_payload_we, sdram_tmrbankmachine3_cmd_buffer_source_payload_we};
assign slice_proxy551 = {sdram_tmrbankmachine3_cmd_buffer3_source_payload_we, sdram_tmrbankmachine3_cmd_buffer2_source_payload_we, sdram_tmrbankmachine3_cmd_buffer_source_payload_we};
assign slice_proxy552 = {sdram_tmrbankmachine3_twtpcon3_ready, sdram_tmrbankmachine3_twtpcon2_ready, sdram_tmrbankmachine3_twtpcon_ready};
assign slice_proxy553 = {sdram_tmrbankmachine3_twtpcon3_ready, sdram_tmrbankmachine3_twtpcon2_ready, sdram_tmrbankmachine3_twtpcon_ready};
assign slice_proxy554 = {sdram_tmrbankmachine3_twtpcon3_ready, sdram_tmrbankmachine3_twtpcon2_ready, sdram_tmrbankmachine3_twtpcon_ready};
assign slice_proxy555 = {sdram_tmrbankmachine3_twtpcon3_ready, sdram_tmrbankmachine3_twtpcon2_ready, sdram_tmrbankmachine3_twtpcon_ready};
assign slice_proxy556 = {sdram_tmrbankmachine3_twtpcon3_ready, sdram_tmrbankmachine3_twtpcon2_ready, sdram_tmrbankmachine3_twtpcon_ready};
assign slice_proxy557 = {sdram_tmrbankmachine3_twtpcon3_ready, sdram_tmrbankmachine3_twtpcon2_ready, sdram_tmrbankmachine3_twtpcon_ready};
assign slice_proxy558 = {sdram_tmrbankmachine3_trccon3_ready, sdram_tmrbankmachine3_trccon2_ready, sdram_tmrbankmachine3_trccon_ready};
assign slice_proxy559 = {sdram_tmrbankmachine3_trccon3_ready, sdram_tmrbankmachine3_trccon2_ready, sdram_tmrbankmachine3_trccon_ready};
assign slice_proxy560 = {sdram_tmrbankmachine3_trccon3_ready, sdram_tmrbankmachine3_trccon2_ready, sdram_tmrbankmachine3_trccon_ready};
assign slice_proxy561 = {sdram_tmrbankmachine3_trccon3_ready, sdram_tmrbankmachine3_trccon2_ready, sdram_tmrbankmachine3_trccon_ready};
assign slice_proxy562 = {sdram_tmrbankmachine3_trccon3_ready, sdram_tmrbankmachine3_trccon2_ready, sdram_tmrbankmachine3_trccon_ready};
assign slice_proxy563 = {sdram_tmrbankmachine3_trccon3_ready, sdram_tmrbankmachine3_trccon2_ready, sdram_tmrbankmachine3_trccon_ready};
assign slice_proxy564 = {sdram_tmrbankmachine3_trascon3_ready, sdram_tmrbankmachine3_trascon2_ready, sdram_tmrbankmachine3_trascon_ready};
assign slice_proxy565 = {sdram_tmrbankmachine3_trascon3_ready, sdram_tmrbankmachine3_trascon2_ready, sdram_tmrbankmachine3_trascon_ready};
assign slice_proxy566 = {sdram_tmrbankmachine3_trascon3_ready, sdram_tmrbankmachine3_trascon2_ready, sdram_tmrbankmachine3_trascon_ready};
assign slice_proxy567 = {sdram_tmrbankmachine3_trascon3_ready, sdram_tmrbankmachine3_trascon2_ready, sdram_tmrbankmachine3_trascon_ready};
assign slice_proxy568 = {sdram_tmrbankmachine3_trascon3_ready, sdram_tmrbankmachine3_trascon2_ready, sdram_tmrbankmachine3_trascon_ready};
assign slice_proxy569 = {sdram_tmrbankmachine3_trascon3_ready, sdram_tmrbankmachine3_trascon2_ready, sdram_tmrbankmachine3_trascon_ready};
assign slice_proxy570 = {(sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine4_cmd_buffer3_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine4_cmd_buffer2_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine4_cmd_buffer_source_valid)};
assign slice_proxy571 = {(sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine4_cmd_buffer3_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine4_cmd_buffer2_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine4_cmd_buffer_source_valid)};
assign slice_proxy572 = {(sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine4_cmd_buffer3_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine4_cmd_buffer2_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine4_cmd_buffer_source_valid)};
assign slice_proxy573 = {(sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine4_cmd_buffer3_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine4_cmd_buffer2_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine4_cmd_buffer_source_valid)};
assign slice_proxy574 = {(sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine4_cmd_buffer3_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine4_cmd_buffer2_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine4_cmd_buffer_source_valid)};
assign slice_proxy575 = {(sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine4_cmd_buffer3_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine4_cmd_buffer2_source_valid), (sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine4_cmd_buffer_source_valid)};
assign slice_proxy576 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy577 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy578 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy579 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy580 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy581 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy582 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_source_payload_addr};
assign slice_proxy583 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_source_payload_addr};
assign slice_proxy584 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_source_payload_addr};
assign slice_proxy585 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_source_payload_addr};
assign slice_proxy586 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_source_payload_addr};
assign slice_proxy587 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine4_cmd_buffer_source_payload_addr};
assign slice_proxy588 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid};
assign slice_proxy589 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid};
assign slice_proxy590 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid};
assign slice_proxy591 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid};
assign slice_proxy592 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid};
assign slice_proxy593 = {sdram_tmrbankmachine4_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine4_cmd_buffer_lookahead_source_valid};
assign slice_proxy594 = {sdram_tmrbankmachine4_cmd_buffer3_source_valid, sdram_tmrbankmachine4_cmd_buffer2_source_valid, sdram_tmrbankmachine4_cmd_buffer_source_valid};
assign slice_proxy595 = {sdram_tmrbankmachine4_cmd_buffer3_source_valid, sdram_tmrbankmachine4_cmd_buffer2_source_valid, sdram_tmrbankmachine4_cmd_buffer_source_valid};
assign slice_proxy596 = {sdram_tmrbankmachine4_cmd_buffer3_source_valid, sdram_tmrbankmachine4_cmd_buffer2_source_valid, sdram_tmrbankmachine4_cmd_buffer_source_valid};
assign slice_proxy597 = {sdram_tmrbankmachine4_cmd_buffer3_source_valid, sdram_tmrbankmachine4_cmd_buffer2_source_valid, sdram_tmrbankmachine4_cmd_buffer_source_valid};
assign slice_proxy598 = {sdram_tmrbankmachine4_cmd_buffer3_source_valid, sdram_tmrbankmachine4_cmd_buffer2_source_valid, sdram_tmrbankmachine4_cmd_buffer_source_valid};
assign slice_proxy599 = {sdram_tmrbankmachine4_cmd_buffer3_source_valid, sdram_tmrbankmachine4_cmd_buffer2_source_valid, sdram_tmrbankmachine4_cmd_buffer_source_valid};
assign slice_proxy600 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_we, sdram_tmrbankmachine4_cmd_buffer2_source_payload_we, sdram_tmrbankmachine4_cmd_buffer_source_payload_we};
assign slice_proxy601 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_we, sdram_tmrbankmachine4_cmd_buffer2_source_payload_we, sdram_tmrbankmachine4_cmd_buffer_source_payload_we};
assign slice_proxy602 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_we, sdram_tmrbankmachine4_cmd_buffer2_source_payload_we, sdram_tmrbankmachine4_cmd_buffer_source_payload_we};
assign slice_proxy603 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_we, sdram_tmrbankmachine4_cmd_buffer2_source_payload_we, sdram_tmrbankmachine4_cmd_buffer_source_payload_we};
assign slice_proxy604 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_we, sdram_tmrbankmachine4_cmd_buffer2_source_payload_we, sdram_tmrbankmachine4_cmd_buffer_source_payload_we};
assign slice_proxy605 = {sdram_tmrbankmachine4_cmd_buffer3_source_payload_we, sdram_tmrbankmachine4_cmd_buffer2_source_payload_we, sdram_tmrbankmachine4_cmd_buffer_source_payload_we};
assign slice_proxy606 = {sdram_tmrbankmachine4_twtpcon3_ready, sdram_tmrbankmachine4_twtpcon2_ready, sdram_tmrbankmachine4_twtpcon_ready};
assign slice_proxy607 = {sdram_tmrbankmachine4_twtpcon3_ready, sdram_tmrbankmachine4_twtpcon2_ready, sdram_tmrbankmachine4_twtpcon_ready};
assign slice_proxy608 = {sdram_tmrbankmachine4_twtpcon3_ready, sdram_tmrbankmachine4_twtpcon2_ready, sdram_tmrbankmachine4_twtpcon_ready};
assign slice_proxy609 = {sdram_tmrbankmachine4_twtpcon3_ready, sdram_tmrbankmachine4_twtpcon2_ready, sdram_tmrbankmachine4_twtpcon_ready};
assign slice_proxy610 = {sdram_tmrbankmachine4_twtpcon3_ready, sdram_tmrbankmachine4_twtpcon2_ready, sdram_tmrbankmachine4_twtpcon_ready};
assign slice_proxy611 = {sdram_tmrbankmachine4_twtpcon3_ready, sdram_tmrbankmachine4_twtpcon2_ready, sdram_tmrbankmachine4_twtpcon_ready};
assign slice_proxy612 = {sdram_tmrbankmachine4_trccon3_ready, sdram_tmrbankmachine4_trccon2_ready, sdram_tmrbankmachine4_trccon_ready};
assign slice_proxy613 = {sdram_tmrbankmachine4_trccon3_ready, sdram_tmrbankmachine4_trccon2_ready, sdram_tmrbankmachine4_trccon_ready};
assign slice_proxy614 = {sdram_tmrbankmachine4_trccon3_ready, sdram_tmrbankmachine4_trccon2_ready, sdram_tmrbankmachine4_trccon_ready};
assign slice_proxy615 = {sdram_tmrbankmachine4_trccon3_ready, sdram_tmrbankmachine4_trccon2_ready, sdram_tmrbankmachine4_trccon_ready};
assign slice_proxy616 = {sdram_tmrbankmachine4_trccon3_ready, sdram_tmrbankmachine4_trccon2_ready, sdram_tmrbankmachine4_trccon_ready};
assign slice_proxy617 = {sdram_tmrbankmachine4_trccon3_ready, sdram_tmrbankmachine4_trccon2_ready, sdram_tmrbankmachine4_trccon_ready};
assign slice_proxy618 = {sdram_tmrbankmachine4_trascon3_ready, sdram_tmrbankmachine4_trascon2_ready, sdram_tmrbankmachine4_trascon_ready};
assign slice_proxy619 = {sdram_tmrbankmachine4_trascon3_ready, sdram_tmrbankmachine4_trascon2_ready, sdram_tmrbankmachine4_trascon_ready};
assign slice_proxy620 = {sdram_tmrbankmachine4_trascon3_ready, sdram_tmrbankmachine4_trascon2_ready, sdram_tmrbankmachine4_trascon_ready};
assign slice_proxy621 = {sdram_tmrbankmachine4_trascon3_ready, sdram_tmrbankmachine4_trascon2_ready, sdram_tmrbankmachine4_trascon_ready};
assign slice_proxy622 = {sdram_tmrbankmachine4_trascon3_ready, sdram_tmrbankmachine4_trascon2_ready, sdram_tmrbankmachine4_trascon_ready};
assign slice_proxy623 = {sdram_tmrbankmachine4_trascon3_ready, sdram_tmrbankmachine4_trascon2_ready, sdram_tmrbankmachine4_trascon_ready};
assign slice_proxy624 = {(sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine5_cmd_buffer3_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine5_cmd_buffer2_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine5_cmd_buffer_source_valid)};
assign slice_proxy625 = {(sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine5_cmd_buffer3_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine5_cmd_buffer2_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine5_cmd_buffer_source_valid)};
assign slice_proxy626 = {(sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine5_cmd_buffer3_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine5_cmd_buffer2_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine5_cmd_buffer_source_valid)};
assign slice_proxy627 = {(sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine5_cmd_buffer3_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine5_cmd_buffer2_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine5_cmd_buffer_source_valid)};
assign slice_proxy628 = {(sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine5_cmd_buffer3_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine5_cmd_buffer2_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine5_cmd_buffer_source_valid)};
assign slice_proxy629 = {(sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine5_cmd_buffer3_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine5_cmd_buffer2_source_valid), (sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine5_cmd_buffer_source_valid)};
assign slice_proxy630 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy631 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy632 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy633 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy634 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy635 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy636 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_source_payload_addr};
assign slice_proxy637 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_source_payload_addr};
assign slice_proxy638 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_source_payload_addr};
assign slice_proxy639 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_source_payload_addr};
assign slice_proxy640 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_source_payload_addr};
assign slice_proxy641 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine5_cmd_buffer_source_payload_addr};
assign slice_proxy642 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid};
assign slice_proxy643 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid};
assign slice_proxy644 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid};
assign slice_proxy645 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid};
assign slice_proxy646 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid};
assign slice_proxy647 = {sdram_tmrbankmachine5_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine5_cmd_buffer_lookahead_source_valid};
assign slice_proxy648 = {sdram_tmrbankmachine5_cmd_buffer3_source_valid, sdram_tmrbankmachine5_cmd_buffer2_source_valid, sdram_tmrbankmachine5_cmd_buffer_source_valid};
assign slice_proxy649 = {sdram_tmrbankmachine5_cmd_buffer3_source_valid, sdram_tmrbankmachine5_cmd_buffer2_source_valid, sdram_tmrbankmachine5_cmd_buffer_source_valid};
assign slice_proxy650 = {sdram_tmrbankmachine5_cmd_buffer3_source_valid, sdram_tmrbankmachine5_cmd_buffer2_source_valid, sdram_tmrbankmachine5_cmd_buffer_source_valid};
assign slice_proxy651 = {sdram_tmrbankmachine5_cmd_buffer3_source_valid, sdram_tmrbankmachine5_cmd_buffer2_source_valid, sdram_tmrbankmachine5_cmd_buffer_source_valid};
assign slice_proxy652 = {sdram_tmrbankmachine5_cmd_buffer3_source_valid, sdram_tmrbankmachine5_cmd_buffer2_source_valid, sdram_tmrbankmachine5_cmd_buffer_source_valid};
assign slice_proxy653 = {sdram_tmrbankmachine5_cmd_buffer3_source_valid, sdram_tmrbankmachine5_cmd_buffer2_source_valid, sdram_tmrbankmachine5_cmd_buffer_source_valid};
assign slice_proxy654 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_we, sdram_tmrbankmachine5_cmd_buffer2_source_payload_we, sdram_tmrbankmachine5_cmd_buffer_source_payload_we};
assign slice_proxy655 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_we, sdram_tmrbankmachine5_cmd_buffer2_source_payload_we, sdram_tmrbankmachine5_cmd_buffer_source_payload_we};
assign slice_proxy656 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_we, sdram_tmrbankmachine5_cmd_buffer2_source_payload_we, sdram_tmrbankmachine5_cmd_buffer_source_payload_we};
assign slice_proxy657 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_we, sdram_tmrbankmachine5_cmd_buffer2_source_payload_we, sdram_tmrbankmachine5_cmd_buffer_source_payload_we};
assign slice_proxy658 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_we, sdram_tmrbankmachine5_cmd_buffer2_source_payload_we, sdram_tmrbankmachine5_cmd_buffer_source_payload_we};
assign slice_proxy659 = {sdram_tmrbankmachine5_cmd_buffer3_source_payload_we, sdram_tmrbankmachine5_cmd_buffer2_source_payload_we, sdram_tmrbankmachine5_cmd_buffer_source_payload_we};
assign slice_proxy660 = {sdram_tmrbankmachine5_twtpcon3_ready, sdram_tmrbankmachine5_twtpcon2_ready, sdram_tmrbankmachine5_twtpcon_ready};
assign slice_proxy661 = {sdram_tmrbankmachine5_twtpcon3_ready, sdram_tmrbankmachine5_twtpcon2_ready, sdram_tmrbankmachine5_twtpcon_ready};
assign slice_proxy662 = {sdram_tmrbankmachine5_twtpcon3_ready, sdram_tmrbankmachine5_twtpcon2_ready, sdram_tmrbankmachine5_twtpcon_ready};
assign slice_proxy663 = {sdram_tmrbankmachine5_twtpcon3_ready, sdram_tmrbankmachine5_twtpcon2_ready, sdram_tmrbankmachine5_twtpcon_ready};
assign slice_proxy664 = {sdram_tmrbankmachine5_twtpcon3_ready, sdram_tmrbankmachine5_twtpcon2_ready, sdram_tmrbankmachine5_twtpcon_ready};
assign slice_proxy665 = {sdram_tmrbankmachine5_twtpcon3_ready, sdram_tmrbankmachine5_twtpcon2_ready, sdram_tmrbankmachine5_twtpcon_ready};
assign slice_proxy666 = {sdram_tmrbankmachine5_trccon3_ready, sdram_tmrbankmachine5_trccon2_ready, sdram_tmrbankmachine5_trccon_ready};
assign slice_proxy667 = {sdram_tmrbankmachine5_trccon3_ready, sdram_tmrbankmachine5_trccon2_ready, sdram_tmrbankmachine5_trccon_ready};
assign slice_proxy668 = {sdram_tmrbankmachine5_trccon3_ready, sdram_tmrbankmachine5_trccon2_ready, sdram_tmrbankmachine5_trccon_ready};
assign slice_proxy669 = {sdram_tmrbankmachine5_trccon3_ready, sdram_tmrbankmachine5_trccon2_ready, sdram_tmrbankmachine5_trccon_ready};
assign slice_proxy670 = {sdram_tmrbankmachine5_trccon3_ready, sdram_tmrbankmachine5_trccon2_ready, sdram_tmrbankmachine5_trccon_ready};
assign slice_proxy671 = {sdram_tmrbankmachine5_trccon3_ready, sdram_tmrbankmachine5_trccon2_ready, sdram_tmrbankmachine5_trccon_ready};
assign slice_proxy672 = {sdram_tmrbankmachine5_trascon3_ready, sdram_tmrbankmachine5_trascon2_ready, sdram_tmrbankmachine5_trascon_ready};
assign slice_proxy673 = {sdram_tmrbankmachine5_trascon3_ready, sdram_tmrbankmachine5_trascon2_ready, sdram_tmrbankmachine5_trascon_ready};
assign slice_proxy674 = {sdram_tmrbankmachine5_trascon3_ready, sdram_tmrbankmachine5_trascon2_ready, sdram_tmrbankmachine5_trascon_ready};
assign slice_proxy675 = {sdram_tmrbankmachine5_trascon3_ready, sdram_tmrbankmachine5_trascon2_ready, sdram_tmrbankmachine5_trascon_ready};
assign slice_proxy676 = {sdram_tmrbankmachine5_trascon3_ready, sdram_tmrbankmachine5_trascon2_ready, sdram_tmrbankmachine5_trascon_ready};
assign slice_proxy677 = {sdram_tmrbankmachine5_trascon3_ready, sdram_tmrbankmachine5_trascon2_ready, sdram_tmrbankmachine5_trascon_ready};
assign slice_proxy678 = {(sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine6_cmd_buffer3_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine6_cmd_buffer2_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine6_cmd_buffer_source_valid)};
assign slice_proxy679 = {(sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine6_cmd_buffer3_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine6_cmd_buffer2_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine6_cmd_buffer_source_valid)};
assign slice_proxy680 = {(sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine6_cmd_buffer3_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine6_cmd_buffer2_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine6_cmd_buffer_source_valid)};
assign slice_proxy681 = {(sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine6_cmd_buffer3_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine6_cmd_buffer2_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine6_cmd_buffer_source_valid)};
assign slice_proxy682 = {(sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine6_cmd_buffer3_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine6_cmd_buffer2_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine6_cmd_buffer_source_valid)};
assign slice_proxy683 = {(sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine6_cmd_buffer3_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine6_cmd_buffer2_source_valid), (sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine6_cmd_buffer_source_valid)};
assign slice_proxy684 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy685 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy686 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy687 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy688 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy689 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy690 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_source_payload_addr};
assign slice_proxy691 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_source_payload_addr};
assign slice_proxy692 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_source_payload_addr};
assign slice_proxy693 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_source_payload_addr};
assign slice_proxy694 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_source_payload_addr};
assign slice_proxy695 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine6_cmd_buffer_source_payload_addr};
assign slice_proxy696 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid};
assign slice_proxy697 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid};
assign slice_proxy698 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid};
assign slice_proxy699 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid};
assign slice_proxy700 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid};
assign slice_proxy701 = {sdram_tmrbankmachine6_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine6_cmd_buffer_lookahead_source_valid};
assign slice_proxy702 = {sdram_tmrbankmachine6_cmd_buffer3_source_valid, sdram_tmrbankmachine6_cmd_buffer2_source_valid, sdram_tmrbankmachine6_cmd_buffer_source_valid};
assign slice_proxy703 = {sdram_tmrbankmachine6_cmd_buffer3_source_valid, sdram_tmrbankmachine6_cmd_buffer2_source_valid, sdram_tmrbankmachine6_cmd_buffer_source_valid};
assign slice_proxy704 = {sdram_tmrbankmachine6_cmd_buffer3_source_valid, sdram_tmrbankmachine6_cmd_buffer2_source_valid, sdram_tmrbankmachine6_cmd_buffer_source_valid};
assign slice_proxy705 = {sdram_tmrbankmachine6_cmd_buffer3_source_valid, sdram_tmrbankmachine6_cmd_buffer2_source_valid, sdram_tmrbankmachine6_cmd_buffer_source_valid};
assign slice_proxy706 = {sdram_tmrbankmachine6_cmd_buffer3_source_valid, sdram_tmrbankmachine6_cmd_buffer2_source_valid, sdram_tmrbankmachine6_cmd_buffer_source_valid};
assign slice_proxy707 = {sdram_tmrbankmachine6_cmd_buffer3_source_valid, sdram_tmrbankmachine6_cmd_buffer2_source_valid, sdram_tmrbankmachine6_cmd_buffer_source_valid};
assign slice_proxy708 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_we, sdram_tmrbankmachine6_cmd_buffer2_source_payload_we, sdram_tmrbankmachine6_cmd_buffer_source_payload_we};
assign slice_proxy709 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_we, sdram_tmrbankmachine6_cmd_buffer2_source_payload_we, sdram_tmrbankmachine6_cmd_buffer_source_payload_we};
assign slice_proxy710 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_we, sdram_tmrbankmachine6_cmd_buffer2_source_payload_we, sdram_tmrbankmachine6_cmd_buffer_source_payload_we};
assign slice_proxy711 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_we, sdram_tmrbankmachine6_cmd_buffer2_source_payload_we, sdram_tmrbankmachine6_cmd_buffer_source_payload_we};
assign slice_proxy712 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_we, sdram_tmrbankmachine6_cmd_buffer2_source_payload_we, sdram_tmrbankmachine6_cmd_buffer_source_payload_we};
assign slice_proxy713 = {sdram_tmrbankmachine6_cmd_buffer3_source_payload_we, sdram_tmrbankmachine6_cmd_buffer2_source_payload_we, sdram_tmrbankmachine6_cmd_buffer_source_payload_we};
assign slice_proxy714 = {sdram_tmrbankmachine6_twtpcon3_ready, sdram_tmrbankmachine6_twtpcon2_ready, sdram_tmrbankmachine6_twtpcon_ready};
assign slice_proxy715 = {sdram_tmrbankmachine6_twtpcon3_ready, sdram_tmrbankmachine6_twtpcon2_ready, sdram_tmrbankmachine6_twtpcon_ready};
assign slice_proxy716 = {sdram_tmrbankmachine6_twtpcon3_ready, sdram_tmrbankmachine6_twtpcon2_ready, sdram_tmrbankmachine6_twtpcon_ready};
assign slice_proxy717 = {sdram_tmrbankmachine6_twtpcon3_ready, sdram_tmrbankmachine6_twtpcon2_ready, sdram_tmrbankmachine6_twtpcon_ready};
assign slice_proxy718 = {sdram_tmrbankmachine6_twtpcon3_ready, sdram_tmrbankmachine6_twtpcon2_ready, sdram_tmrbankmachine6_twtpcon_ready};
assign slice_proxy719 = {sdram_tmrbankmachine6_twtpcon3_ready, sdram_tmrbankmachine6_twtpcon2_ready, sdram_tmrbankmachine6_twtpcon_ready};
assign slice_proxy720 = {sdram_tmrbankmachine6_trccon3_ready, sdram_tmrbankmachine6_trccon2_ready, sdram_tmrbankmachine6_trccon_ready};
assign slice_proxy721 = {sdram_tmrbankmachine6_trccon3_ready, sdram_tmrbankmachine6_trccon2_ready, sdram_tmrbankmachine6_trccon_ready};
assign slice_proxy722 = {sdram_tmrbankmachine6_trccon3_ready, sdram_tmrbankmachine6_trccon2_ready, sdram_tmrbankmachine6_trccon_ready};
assign slice_proxy723 = {sdram_tmrbankmachine6_trccon3_ready, sdram_tmrbankmachine6_trccon2_ready, sdram_tmrbankmachine6_trccon_ready};
assign slice_proxy724 = {sdram_tmrbankmachine6_trccon3_ready, sdram_tmrbankmachine6_trccon2_ready, sdram_tmrbankmachine6_trccon_ready};
assign slice_proxy725 = {sdram_tmrbankmachine6_trccon3_ready, sdram_tmrbankmachine6_trccon2_ready, sdram_tmrbankmachine6_trccon_ready};
assign slice_proxy726 = {sdram_tmrbankmachine6_trascon3_ready, sdram_tmrbankmachine6_trascon2_ready, sdram_tmrbankmachine6_trascon_ready};
assign slice_proxy727 = {sdram_tmrbankmachine6_trascon3_ready, sdram_tmrbankmachine6_trascon2_ready, sdram_tmrbankmachine6_trascon_ready};
assign slice_proxy728 = {sdram_tmrbankmachine6_trascon3_ready, sdram_tmrbankmachine6_trascon2_ready, sdram_tmrbankmachine6_trascon_ready};
assign slice_proxy729 = {sdram_tmrbankmachine6_trascon3_ready, sdram_tmrbankmachine6_trascon2_ready, sdram_tmrbankmachine6_trascon_ready};
assign slice_proxy730 = {sdram_tmrbankmachine6_trascon3_ready, sdram_tmrbankmachine6_trascon2_ready, sdram_tmrbankmachine6_trascon_ready};
assign slice_proxy731 = {sdram_tmrbankmachine6_trascon3_ready, sdram_tmrbankmachine6_trascon2_ready, sdram_tmrbankmachine6_trascon_ready};
assign slice_proxy732 = {(sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine7_cmd_buffer3_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine7_cmd_buffer2_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine7_cmd_buffer_source_valid)};
assign slice_proxy733 = {(sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine7_cmd_buffer3_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine7_cmd_buffer2_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine7_cmd_buffer_source_valid)};
assign slice_proxy734 = {(sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine7_cmd_buffer3_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine7_cmd_buffer2_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine7_cmd_buffer_source_valid)};
assign slice_proxy735 = {(sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine7_cmd_buffer3_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine7_cmd_buffer2_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine7_cmd_buffer_source_valid)};
assign slice_proxy736 = {(sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine7_cmd_buffer3_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine7_cmd_buffer2_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine7_cmd_buffer_source_valid)};
assign slice_proxy737 = {(sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid | sdram_tmrbankmachine7_cmd_buffer3_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid | sdram_tmrbankmachine7_cmd_buffer2_source_valid), (sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid | sdram_tmrbankmachine7_cmd_buffer_source_valid)};
assign slice_proxy738 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy739 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy740 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy741 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy742 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy743 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy744 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_source_payload_addr};
assign slice_proxy745 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_source_payload_addr};
assign slice_proxy746 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_source_payload_addr};
assign slice_proxy747 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_source_payload_addr};
assign slice_proxy748 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_source_payload_addr};
assign slice_proxy749 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr, sdram_tmrbankmachine7_cmd_buffer_source_payload_addr};
assign slice_proxy750 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid};
assign slice_proxy751 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid};
assign slice_proxy752 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid};
assign slice_proxy753 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid};
assign slice_proxy754 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid};
assign slice_proxy755 = {sdram_tmrbankmachine7_cmd_buffer_lookahead3_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead2_source_valid, sdram_tmrbankmachine7_cmd_buffer_lookahead_source_valid};
assign slice_proxy756 = {sdram_tmrbankmachine7_cmd_buffer3_source_valid, sdram_tmrbankmachine7_cmd_buffer2_source_valid, sdram_tmrbankmachine7_cmd_buffer_source_valid};
assign slice_proxy757 = {sdram_tmrbankmachine7_cmd_buffer3_source_valid, sdram_tmrbankmachine7_cmd_buffer2_source_valid, sdram_tmrbankmachine7_cmd_buffer_source_valid};
assign slice_proxy758 = {sdram_tmrbankmachine7_cmd_buffer3_source_valid, sdram_tmrbankmachine7_cmd_buffer2_source_valid, sdram_tmrbankmachine7_cmd_buffer_source_valid};
assign slice_proxy759 = {sdram_tmrbankmachine7_cmd_buffer3_source_valid, sdram_tmrbankmachine7_cmd_buffer2_source_valid, sdram_tmrbankmachine7_cmd_buffer_source_valid};
assign slice_proxy760 = {sdram_tmrbankmachine7_cmd_buffer3_source_valid, sdram_tmrbankmachine7_cmd_buffer2_source_valid, sdram_tmrbankmachine7_cmd_buffer_source_valid};
assign slice_proxy761 = {sdram_tmrbankmachine7_cmd_buffer3_source_valid, sdram_tmrbankmachine7_cmd_buffer2_source_valid, sdram_tmrbankmachine7_cmd_buffer_source_valid};
assign slice_proxy762 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_we, sdram_tmrbankmachine7_cmd_buffer2_source_payload_we, sdram_tmrbankmachine7_cmd_buffer_source_payload_we};
assign slice_proxy763 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_we, sdram_tmrbankmachine7_cmd_buffer2_source_payload_we, sdram_tmrbankmachine7_cmd_buffer_source_payload_we};
assign slice_proxy764 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_we, sdram_tmrbankmachine7_cmd_buffer2_source_payload_we, sdram_tmrbankmachine7_cmd_buffer_source_payload_we};
assign slice_proxy765 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_we, sdram_tmrbankmachine7_cmd_buffer2_source_payload_we, sdram_tmrbankmachine7_cmd_buffer_source_payload_we};
assign slice_proxy766 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_we, sdram_tmrbankmachine7_cmd_buffer2_source_payload_we, sdram_tmrbankmachine7_cmd_buffer_source_payload_we};
assign slice_proxy767 = {sdram_tmrbankmachine7_cmd_buffer3_source_payload_we, sdram_tmrbankmachine7_cmd_buffer2_source_payload_we, sdram_tmrbankmachine7_cmd_buffer_source_payload_we};
assign slice_proxy768 = {sdram_tmrbankmachine7_twtpcon3_ready, sdram_tmrbankmachine7_twtpcon2_ready, sdram_tmrbankmachine7_twtpcon_ready};
assign slice_proxy769 = {sdram_tmrbankmachine7_twtpcon3_ready, sdram_tmrbankmachine7_twtpcon2_ready, sdram_tmrbankmachine7_twtpcon_ready};
assign slice_proxy770 = {sdram_tmrbankmachine7_twtpcon3_ready, sdram_tmrbankmachine7_twtpcon2_ready, sdram_tmrbankmachine7_twtpcon_ready};
assign slice_proxy771 = {sdram_tmrbankmachine7_twtpcon3_ready, sdram_tmrbankmachine7_twtpcon2_ready, sdram_tmrbankmachine7_twtpcon_ready};
assign slice_proxy772 = {sdram_tmrbankmachine7_twtpcon3_ready, sdram_tmrbankmachine7_twtpcon2_ready, sdram_tmrbankmachine7_twtpcon_ready};
assign slice_proxy773 = {sdram_tmrbankmachine7_twtpcon3_ready, sdram_tmrbankmachine7_twtpcon2_ready, sdram_tmrbankmachine7_twtpcon_ready};
assign slice_proxy774 = {sdram_tmrbankmachine7_trccon3_ready, sdram_tmrbankmachine7_trccon2_ready, sdram_tmrbankmachine7_trccon_ready};
assign slice_proxy775 = {sdram_tmrbankmachine7_trccon3_ready, sdram_tmrbankmachine7_trccon2_ready, sdram_tmrbankmachine7_trccon_ready};
assign slice_proxy776 = {sdram_tmrbankmachine7_trccon3_ready, sdram_tmrbankmachine7_trccon2_ready, sdram_tmrbankmachine7_trccon_ready};
assign slice_proxy777 = {sdram_tmrbankmachine7_trccon3_ready, sdram_tmrbankmachine7_trccon2_ready, sdram_tmrbankmachine7_trccon_ready};
assign slice_proxy778 = {sdram_tmrbankmachine7_trccon3_ready, sdram_tmrbankmachine7_trccon2_ready, sdram_tmrbankmachine7_trccon_ready};
assign slice_proxy779 = {sdram_tmrbankmachine7_trccon3_ready, sdram_tmrbankmachine7_trccon2_ready, sdram_tmrbankmachine7_trccon_ready};
assign slice_proxy780 = {sdram_tmrbankmachine7_trascon3_ready, sdram_tmrbankmachine7_trascon2_ready, sdram_tmrbankmachine7_trascon_ready};
assign slice_proxy781 = {sdram_tmrbankmachine7_trascon3_ready, sdram_tmrbankmachine7_trascon2_ready, sdram_tmrbankmachine7_trascon_ready};
assign slice_proxy782 = {sdram_tmrbankmachine7_trascon3_ready, sdram_tmrbankmachine7_trascon2_ready, sdram_tmrbankmachine7_trascon_ready};
assign slice_proxy783 = {sdram_tmrbankmachine7_trascon3_ready, sdram_tmrbankmachine7_trascon2_ready, sdram_tmrbankmachine7_trascon_ready};
assign slice_proxy784 = {sdram_tmrbankmachine7_trascon3_ready, sdram_tmrbankmachine7_trascon2_ready, sdram_tmrbankmachine7_trascon_ready};
assign slice_proxy785 = {sdram_tmrbankmachine7_trascon3_ready, sdram_tmrbankmachine7_trascon2_ready, sdram_tmrbankmachine7_trascon_ready};
assign slice_proxy786 = (~sdram_TMRinterface_wdata_we);
assign slice_proxy787 = (~sdram_TMRinterface_wdata_we);
assign slice_proxy788 = (~sdram_TMRinterface_wdata_we);
assign slice_proxy789 = (~sdram_TMRinterface_wdata_we);
assign slice_proxy790 = (~sdram_TMRinterface_wdata_we);
assign slice_proxy791 = (~sdram_TMRinterface_wdata_we);

// synthesis translate_off
reg dummy_d_112;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed0 <= 1'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed0 <= sdram_multiplexer_choose_cmd_valids[0];
		end
		1'd1: begin
			rhs_array_muxed0 <= sdram_multiplexer_choose_cmd_valids[1];
		end
		2'd2: begin
			rhs_array_muxed0 <= sdram_multiplexer_choose_cmd_valids[2];
		end
		2'd3: begin
			rhs_array_muxed0 <= sdram_multiplexer_choose_cmd_valids[3];
		end
		3'd4: begin
			rhs_array_muxed0 <= sdram_multiplexer_choose_cmd_valids[4];
		end
		3'd5: begin
			rhs_array_muxed0 <= sdram_multiplexer_choose_cmd_valids[5];
		end
		3'd6: begin
			rhs_array_muxed0 <= sdram_multiplexer_choose_cmd_valids[6];
		end
		default: begin
			rhs_array_muxed0 <= sdram_multiplexer_choose_cmd_valids[7];
		end
	endcase
// synthesis translate_off
	dummy_d_112 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_113;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed1 <= 14'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed1 <= sdram_multiplexer_endpoint0_payload_a;
		end
		1'd1: begin
			rhs_array_muxed1 <= sdram_multiplexer_endpoint1_payload_a;
		end
		2'd2: begin
			rhs_array_muxed1 <= sdram_multiplexer_endpoint2_payload_a;
		end
		2'd3: begin
			rhs_array_muxed1 <= sdram_multiplexer_endpoint3_payload_a;
		end
		3'd4: begin
			rhs_array_muxed1 <= sdram_multiplexer_endpoint4_payload_a;
		end
		3'd5: begin
			rhs_array_muxed1 <= sdram_multiplexer_endpoint5_payload_a;
		end
		3'd6: begin
			rhs_array_muxed1 <= sdram_multiplexer_endpoint6_payload_a;
		end
		default: begin
			rhs_array_muxed1 <= sdram_multiplexer_endpoint7_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_113 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_114;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed2 <= 3'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed2 <= sdram_multiplexer_endpoint0_payload_ba;
		end
		1'd1: begin
			rhs_array_muxed2 <= sdram_multiplexer_endpoint1_payload_ba;
		end
		2'd2: begin
			rhs_array_muxed2 <= sdram_multiplexer_endpoint2_payload_ba;
		end
		2'd3: begin
			rhs_array_muxed2 <= sdram_multiplexer_endpoint3_payload_ba;
		end
		3'd4: begin
			rhs_array_muxed2 <= sdram_multiplexer_endpoint4_payload_ba;
		end
		3'd5: begin
			rhs_array_muxed2 <= sdram_multiplexer_endpoint5_payload_ba;
		end
		3'd6: begin
			rhs_array_muxed2 <= sdram_multiplexer_endpoint6_payload_ba;
		end
		default: begin
			rhs_array_muxed2 <= sdram_multiplexer_endpoint7_payload_ba;
		end
	endcase
// synthesis translate_off
	dummy_d_114 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_115;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed3 <= 1'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed3 <= sdram_multiplexer_endpoint0_payload_is_read;
		end
		1'd1: begin
			rhs_array_muxed3 <= sdram_multiplexer_endpoint1_payload_is_read;
		end
		2'd2: begin
			rhs_array_muxed3 <= sdram_multiplexer_endpoint2_payload_is_read;
		end
		2'd3: begin
			rhs_array_muxed3 <= sdram_multiplexer_endpoint3_payload_is_read;
		end
		3'd4: begin
			rhs_array_muxed3 <= sdram_multiplexer_endpoint4_payload_is_read;
		end
		3'd5: begin
			rhs_array_muxed3 <= sdram_multiplexer_endpoint5_payload_is_read;
		end
		3'd6: begin
			rhs_array_muxed3 <= sdram_multiplexer_endpoint6_payload_is_read;
		end
		default: begin
			rhs_array_muxed3 <= sdram_multiplexer_endpoint7_payload_is_read;
		end
	endcase
// synthesis translate_off
	dummy_d_115 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_116;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed4 <= 1'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed4 <= sdram_multiplexer_endpoint0_payload_is_write;
		end
		1'd1: begin
			rhs_array_muxed4 <= sdram_multiplexer_endpoint1_payload_is_write;
		end
		2'd2: begin
			rhs_array_muxed4 <= sdram_multiplexer_endpoint2_payload_is_write;
		end
		2'd3: begin
			rhs_array_muxed4 <= sdram_multiplexer_endpoint3_payload_is_write;
		end
		3'd4: begin
			rhs_array_muxed4 <= sdram_multiplexer_endpoint4_payload_is_write;
		end
		3'd5: begin
			rhs_array_muxed4 <= sdram_multiplexer_endpoint5_payload_is_write;
		end
		3'd6: begin
			rhs_array_muxed4 <= sdram_multiplexer_endpoint6_payload_is_write;
		end
		default: begin
			rhs_array_muxed4 <= sdram_multiplexer_endpoint7_payload_is_write;
		end
	endcase
// synthesis translate_off
	dummy_d_116 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_117;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed5 <= 1'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed5 <= sdram_multiplexer_endpoint0_payload_is_cmd;
		end
		1'd1: begin
			rhs_array_muxed5 <= sdram_multiplexer_endpoint1_payload_is_cmd;
		end
		2'd2: begin
			rhs_array_muxed5 <= sdram_multiplexer_endpoint2_payload_is_cmd;
		end
		2'd3: begin
			rhs_array_muxed5 <= sdram_multiplexer_endpoint3_payload_is_cmd;
		end
		3'd4: begin
			rhs_array_muxed5 <= sdram_multiplexer_endpoint4_payload_is_cmd;
		end
		3'd5: begin
			rhs_array_muxed5 <= sdram_multiplexer_endpoint5_payload_is_cmd;
		end
		3'd6: begin
			rhs_array_muxed5 <= sdram_multiplexer_endpoint6_payload_is_cmd;
		end
		default: begin
			rhs_array_muxed5 <= sdram_multiplexer_endpoint7_payload_is_cmd;
		end
	endcase
// synthesis translate_off
	dummy_d_117 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_118;
// synthesis translate_on
always @(*) begin
	t_array_muxed0 <= 1'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			t_array_muxed0 <= sdram_multiplexer_endpoint0_payload_cas;
		end
		1'd1: begin
			t_array_muxed0 <= sdram_multiplexer_endpoint1_payload_cas;
		end
		2'd2: begin
			t_array_muxed0 <= sdram_multiplexer_endpoint2_payload_cas;
		end
		2'd3: begin
			t_array_muxed0 <= sdram_multiplexer_endpoint3_payload_cas;
		end
		3'd4: begin
			t_array_muxed0 <= sdram_multiplexer_endpoint4_payload_cas;
		end
		3'd5: begin
			t_array_muxed0 <= sdram_multiplexer_endpoint5_payload_cas;
		end
		3'd6: begin
			t_array_muxed0 <= sdram_multiplexer_endpoint6_payload_cas;
		end
		default: begin
			t_array_muxed0 <= sdram_multiplexer_endpoint7_payload_cas;
		end
	endcase
// synthesis translate_off
	dummy_d_118 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_119;
// synthesis translate_on
always @(*) begin
	t_array_muxed1 <= 1'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			t_array_muxed1 <= sdram_multiplexer_endpoint0_payload_ras;
		end
		1'd1: begin
			t_array_muxed1 <= sdram_multiplexer_endpoint1_payload_ras;
		end
		2'd2: begin
			t_array_muxed1 <= sdram_multiplexer_endpoint2_payload_ras;
		end
		2'd3: begin
			t_array_muxed1 <= sdram_multiplexer_endpoint3_payload_ras;
		end
		3'd4: begin
			t_array_muxed1 <= sdram_multiplexer_endpoint4_payload_ras;
		end
		3'd5: begin
			t_array_muxed1 <= sdram_multiplexer_endpoint5_payload_ras;
		end
		3'd6: begin
			t_array_muxed1 <= sdram_multiplexer_endpoint6_payload_ras;
		end
		default: begin
			t_array_muxed1 <= sdram_multiplexer_endpoint7_payload_ras;
		end
	endcase
// synthesis translate_off
	dummy_d_119 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_120;
// synthesis translate_on
always @(*) begin
	t_array_muxed2 <= 1'd0;
	case (sdram_multiplexer_choose_cmd_grant)
		1'd0: begin
			t_array_muxed2 <= sdram_multiplexer_endpoint0_payload_we;
		end
		1'd1: begin
			t_array_muxed2 <= sdram_multiplexer_endpoint1_payload_we;
		end
		2'd2: begin
			t_array_muxed2 <= sdram_multiplexer_endpoint2_payload_we;
		end
		2'd3: begin
			t_array_muxed2 <= sdram_multiplexer_endpoint3_payload_we;
		end
		3'd4: begin
			t_array_muxed2 <= sdram_multiplexer_endpoint4_payload_we;
		end
		3'd5: begin
			t_array_muxed2 <= sdram_multiplexer_endpoint5_payload_we;
		end
		3'd6: begin
			t_array_muxed2 <= sdram_multiplexer_endpoint6_payload_we;
		end
		default: begin
			t_array_muxed2 <= sdram_multiplexer_endpoint7_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_120 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_121;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed6 <= 1'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			rhs_array_muxed6 <= sdram_multiplexer_choose_req_valids[0];
		end
		1'd1: begin
			rhs_array_muxed6 <= sdram_multiplexer_choose_req_valids[1];
		end
		2'd2: begin
			rhs_array_muxed6 <= sdram_multiplexer_choose_req_valids[2];
		end
		2'd3: begin
			rhs_array_muxed6 <= sdram_multiplexer_choose_req_valids[3];
		end
		3'd4: begin
			rhs_array_muxed6 <= sdram_multiplexer_choose_req_valids[4];
		end
		3'd5: begin
			rhs_array_muxed6 <= sdram_multiplexer_choose_req_valids[5];
		end
		3'd6: begin
			rhs_array_muxed6 <= sdram_multiplexer_choose_req_valids[6];
		end
		default: begin
			rhs_array_muxed6 <= sdram_multiplexer_choose_req_valids[7];
		end
	endcase
// synthesis translate_off
	dummy_d_121 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_122;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed7 <= 14'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			rhs_array_muxed7 <= sdram_multiplexer_endpoint0_payload_a;
		end
		1'd1: begin
			rhs_array_muxed7 <= sdram_multiplexer_endpoint1_payload_a;
		end
		2'd2: begin
			rhs_array_muxed7 <= sdram_multiplexer_endpoint2_payload_a;
		end
		2'd3: begin
			rhs_array_muxed7 <= sdram_multiplexer_endpoint3_payload_a;
		end
		3'd4: begin
			rhs_array_muxed7 <= sdram_multiplexer_endpoint4_payload_a;
		end
		3'd5: begin
			rhs_array_muxed7 <= sdram_multiplexer_endpoint5_payload_a;
		end
		3'd6: begin
			rhs_array_muxed7 <= sdram_multiplexer_endpoint6_payload_a;
		end
		default: begin
			rhs_array_muxed7 <= sdram_multiplexer_endpoint7_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_122 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_123;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed8 <= 3'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			rhs_array_muxed8 <= sdram_multiplexer_endpoint0_payload_ba;
		end
		1'd1: begin
			rhs_array_muxed8 <= sdram_multiplexer_endpoint1_payload_ba;
		end
		2'd2: begin
			rhs_array_muxed8 <= sdram_multiplexer_endpoint2_payload_ba;
		end
		2'd3: begin
			rhs_array_muxed8 <= sdram_multiplexer_endpoint3_payload_ba;
		end
		3'd4: begin
			rhs_array_muxed8 <= sdram_multiplexer_endpoint4_payload_ba;
		end
		3'd5: begin
			rhs_array_muxed8 <= sdram_multiplexer_endpoint5_payload_ba;
		end
		3'd6: begin
			rhs_array_muxed8 <= sdram_multiplexer_endpoint6_payload_ba;
		end
		default: begin
			rhs_array_muxed8 <= sdram_multiplexer_endpoint7_payload_ba;
		end
	endcase
// synthesis translate_off
	dummy_d_123 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_124;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed9 <= 1'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			rhs_array_muxed9 <= sdram_multiplexer_endpoint0_payload_is_read;
		end
		1'd1: begin
			rhs_array_muxed9 <= sdram_multiplexer_endpoint1_payload_is_read;
		end
		2'd2: begin
			rhs_array_muxed9 <= sdram_multiplexer_endpoint2_payload_is_read;
		end
		2'd3: begin
			rhs_array_muxed9 <= sdram_multiplexer_endpoint3_payload_is_read;
		end
		3'd4: begin
			rhs_array_muxed9 <= sdram_multiplexer_endpoint4_payload_is_read;
		end
		3'd5: begin
			rhs_array_muxed9 <= sdram_multiplexer_endpoint5_payload_is_read;
		end
		3'd6: begin
			rhs_array_muxed9 <= sdram_multiplexer_endpoint6_payload_is_read;
		end
		default: begin
			rhs_array_muxed9 <= sdram_multiplexer_endpoint7_payload_is_read;
		end
	endcase
// synthesis translate_off
	dummy_d_124 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_125;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed10 <= 1'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			rhs_array_muxed10 <= sdram_multiplexer_endpoint0_payload_is_write;
		end
		1'd1: begin
			rhs_array_muxed10 <= sdram_multiplexer_endpoint1_payload_is_write;
		end
		2'd2: begin
			rhs_array_muxed10 <= sdram_multiplexer_endpoint2_payload_is_write;
		end
		2'd3: begin
			rhs_array_muxed10 <= sdram_multiplexer_endpoint3_payload_is_write;
		end
		3'd4: begin
			rhs_array_muxed10 <= sdram_multiplexer_endpoint4_payload_is_write;
		end
		3'd5: begin
			rhs_array_muxed10 <= sdram_multiplexer_endpoint5_payload_is_write;
		end
		3'd6: begin
			rhs_array_muxed10 <= sdram_multiplexer_endpoint6_payload_is_write;
		end
		default: begin
			rhs_array_muxed10 <= sdram_multiplexer_endpoint7_payload_is_write;
		end
	endcase
// synthesis translate_off
	dummy_d_125 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_126;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed11 <= 1'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			rhs_array_muxed11 <= sdram_multiplexer_endpoint0_payload_is_cmd;
		end
		1'd1: begin
			rhs_array_muxed11 <= sdram_multiplexer_endpoint1_payload_is_cmd;
		end
		2'd2: begin
			rhs_array_muxed11 <= sdram_multiplexer_endpoint2_payload_is_cmd;
		end
		2'd3: begin
			rhs_array_muxed11 <= sdram_multiplexer_endpoint3_payload_is_cmd;
		end
		3'd4: begin
			rhs_array_muxed11 <= sdram_multiplexer_endpoint4_payload_is_cmd;
		end
		3'd5: begin
			rhs_array_muxed11 <= sdram_multiplexer_endpoint5_payload_is_cmd;
		end
		3'd6: begin
			rhs_array_muxed11 <= sdram_multiplexer_endpoint6_payload_is_cmd;
		end
		default: begin
			rhs_array_muxed11 <= sdram_multiplexer_endpoint7_payload_is_cmd;
		end
	endcase
// synthesis translate_off
	dummy_d_126 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_127;
// synthesis translate_on
always @(*) begin
	t_array_muxed3 <= 1'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			t_array_muxed3 <= sdram_multiplexer_endpoint0_payload_cas;
		end
		1'd1: begin
			t_array_muxed3 <= sdram_multiplexer_endpoint1_payload_cas;
		end
		2'd2: begin
			t_array_muxed3 <= sdram_multiplexer_endpoint2_payload_cas;
		end
		2'd3: begin
			t_array_muxed3 <= sdram_multiplexer_endpoint3_payload_cas;
		end
		3'd4: begin
			t_array_muxed3 <= sdram_multiplexer_endpoint4_payload_cas;
		end
		3'd5: begin
			t_array_muxed3 <= sdram_multiplexer_endpoint5_payload_cas;
		end
		3'd6: begin
			t_array_muxed3 <= sdram_multiplexer_endpoint6_payload_cas;
		end
		default: begin
			t_array_muxed3 <= sdram_multiplexer_endpoint7_payload_cas;
		end
	endcase
// synthesis translate_off
	dummy_d_127 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_128;
// synthesis translate_on
always @(*) begin
	t_array_muxed4 <= 1'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			t_array_muxed4 <= sdram_multiplexer_endpoint0_payload_ras;
		end
		1'd1: begin
			t_array_muxed4 <= sdram_multiplexer_endpoint1_payload_ras;
		end
		2'd2: begin
			t_array_muxed4 <= sdram_multiplexer_endpoint2_payload_ras;
		end
		2'd3: begin
			t_array_muxed4 <= sdram_multiplexer_endpoint3_payload_ras;
		end
		3'd4: begin
			t_array_muxed4 <= sdram_multiplexer_endpoint4_payload_ras;
		end
		3'd5: begin
			t_array_muxed4 <= sdram_multiplexer_endpoint5_payload_ras;
		end
		3'd6: begin
			t_array_muxed4 <= sdram_multiplexer_endpoint6_payload_ras;
		end
		default: begin
			t_array_muxed4 <= sdram_multiplexer_endpoint7_payload_ras;
		end
	endcase
// synthesis translate_off
	dummy_d_128 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_129;
// synthesis translate_on
always @(*) begin
	t_array_muxed5 <= 1'd0;
	case (sdram_multiplexer_choose_req_grant)
		1'd0: begin
			t_array_muxed5 <= sdram_multiplexer_endpoint0_payload_we;
		end
		1'd1: begin
			t_array_muxed5 <= sdram_multiplexer_endpoint1_payload_we;
		end
		2'd2: begin
			t_array_muxed5 <= sdram_multiplexer_endpoint2_payload_we;
		end
		2'd3: begin
			t_array_muxed5 <= sdram_multiplexer_endpoint3_payload_we;
		end
		3'd4: begin
			t_array_muxed5 <= sdram_multiplexer_endpoint4_payload_we;
		end
		3'd5: begin
			t_array_muxed5 <= sdram_multiplexer_endpoint5_payload_we;
		end
		3'd6: begin
			t_array_muxed5 <= sdram_multiplexer_endpoint6_payload_we;
		end
		default: begin
			t_array_muxed5 <= sdram_multiplexer_endpoint7_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_129 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_130;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed12 <= 21'd0;
	case (roundrobin0_grant)
		default: begin
			rhs_array_muxed12 <= {cmd_payload_addr[23:10], cmd_payload_addr[6:0]};
		end
	endcase
// synthesis translate_off
	dummy_d_130 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_131;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed13 <= 1'd0;
	case (roundrobin0_grant)
		default: begin
			rhs_array_muxed13 <= port_cmd_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_131 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_132;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed14 <= 1'd0;
	case (roundrobin0_grant)
		default: begin
			rhs_array_muxed14 <= (((cmd_payload_addr[9:7] == 1'd0) & (~(((((((locked0 | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid);
		end
	endcase
// synthesis translate_off
	dummy_d_132 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_133;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed15 <= 21'd0;
	case (roundrobin1_grant)
		default: begin
			rhs_array_muxed15 <= {cmd_payload_addr[23:10], cmd_payload_addr[6:0]};
		end
	endcase
// synthesis translate_off
	dummy_d_133 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_134;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed16 <= 1'd0;
	case (roundrobin1_grant)
		default: begin
			rhs_array_muxed16 <= port_cmd_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_134 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_135;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed17 <= 1'd0;
	case (roundrobin1_grant)
		default: begin
			rhs_array_muxed17 <= (((cmd_payload_addr[9:7] == 1'd1) & (~(((((((locked1 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid);
		end
	endcase
// synthesis translate_off
	dummy_d_135 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_136;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed18 <= 21'd0;
	case (roundrobin2_grant)
		default: begin
			rhs_array_muxed18 <= {cmd_payload_addr[23:10], cmd_payload_addr[6:0]};
		end
	endcase
// synthesis translate_off
	dummy_d_136 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_137;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed19 <= 1'd0;
	case (roundrobin2_grant)
		default: begin
			rhs_array_muxed19 <= port_cmd_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_137 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_138;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed20 <= 1'd0;
	case (roundrobin2_grant)
		default: begin
			rhs_array_muxed20 <= (((cmd_payload_addr[9:7] == 2'd2) & (~(((((((locked2 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid);
		end
	endcase
// synthesis translate_off
	dummy_d_138 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_139;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed21 <= 21'd0;
	case (roundrobin3_grant)
		default: begin
			rhs_array_muxed21 <= {cmd_payload_addr[23:10], cmd_payload_addr[6:0]};
		end
	endcase
// synthesis translate_off
	dummy_d_139 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_140;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed22 <= 1'd0;
	case (roundrobin3_grant)
		default: begin
			rhs_array_muxed22 <= port_cmd_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_140 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_141;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed23 <= 1'd0;
	case (roundrobin3_grant)
		default: begin
			rhs_array_muxed23 <= (((cmd_payload_addr[9:7] == 2'd3) & (~(((((((locked3 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid);
		end
	endcase
// synthesis translate_off
	dummy_d_141 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_142;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed24 <= 21'd0;
	case (roundrobin4_grant)
		default: begin
			rhs_array_muxed24 <= {cmd_payload_addr[23:10], cmd_payload_addr[6:0]};
		end
	endcase
// synthesis translate_off
	dummy_d_142 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_143;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed25 <= 1'd0;
	case (roundrobin4_grant)
		default: begin
			rhs_array_muxed25 <= port_cmd_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_143 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_144;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed26 <= 1'd0;
	case (roundrobin4_grant)
		default: begin
			rhs_array_muxed26 <= (((cmd_payload_addr[9:7] == 3'd4) & (~(((((((locked4 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid);
		end
	endcase
// synthesis translate_off
	dummy_d_144 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_145;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed27 <= 21'd0;
	case (roundrobin5_grant)
		default: begin
			rhs_array_muxed27 <= {cmd_payload_addr[23:10], cmd_payload_addr[6:0]};
		end
	endcase
// synthesis translate_off
	dummy_d_145 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_146;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed28 <= 1'd0;
	case (roundrobin5_grant)
		default: begin
			rhs_array_muxed28 <= port_cmd_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_146 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_147;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed29 <= 1'd0;
	case (roundrobin5_grant)
		default: begin
			rhs_array_muxed29 <= (((cmd_payload_addr[9:7] == 3'd5) & (~(((((((locked5 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid);
		end
	endcase
// synthesis translate_off
	dummy_d_147 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_148;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed30 <= 21'd0;
	case (roundrobin6_grant)
		default: begin
			rhs_array_muxed30 <= {cmd_payload_addr[23:10], cmd_payload_addr[6:0]};
		end
	endcase
// synthesis translate_off
	dummy_d_148 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_149;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed31 <= 1'd0;
	case (roundrobin6_grant)
		default: begin
			rhs_array_muxed31 <= port_cmd_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_149 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_150;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed32 <= 1'd0;
	case (roundrobin6_grant)
		default: begin
			rhs_array_muxed32 <= (((cmd_payload_addr[9:7] == 3'd6) & (~(((((((locked6 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank7_lock & (roundrobin7_grant == 1'd0))))) & port_cmd_valid);
		end
	endcase
// synthesis translate_off
	dummy_d_150 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_151;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed33 <= 21'd0;
	case (roundrobin7_grant)
		default: begin
			rhs_array_muxed33 <= {cmd_payload_addr[23:10], cmd_payload_addr[6:0]};
		end
	endcase
// synthesis translate_off
	dummy_d_151 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_152;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed34 <= 1'd0;
	case (roundrobin7_grant)
		default: begin
			rhs_array_muxed34 <= port_cmd_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_152 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_153;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed35 <= 1'd0;
	case (roundrobin7_grant)
		default: begin
			rhs_array_muxed35 <= (((cmd_payload_addr[9:7] == 3'd7) & (~(((((((locked7 | (sdram_interface_bank0_lock & (roundrobin0_grant == 1'd0))) | (sdram_interface_bank1_lock & (roundrobin1_grant == 1'd0))) | (sdram_interface_bank2_lock & (roundrobin2_grant == 1'd0))) | (sdram_interface_bank3_lock & (roundrobin3_grant == 1'd0))) | (sdram_interface_bank4_lock & (roundrobin4_grant == 1'd0))) | (sdram_interface_bank5_lock & (roundrobin5_grant == 1'd0))) | (sdram_interface_bank6_lock & (roundrobin6_grant == 1'd0))))) & port_cmd_valid);
		end
	endcase
// synthesis translate_off
	dummy_d_153 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_154;
// synthesis translate_on
always @(*) begin
	array_muxed0 <= 3'd0;
	case (sdram_multiplexer_steerer0)
		1'd0: begin
			array_muxed0 <= sdram_multiplexer_nop_ba[2:0];
		end
		1'd1: begin
			array_muxed0 <= sdram_multiplexer_choose_cmd_cmd_payload_ba[2:0];
		end
		2'd2: begin
			array_muxed0 <= sdram_multiplexer_choose_req_cmd_payload_ba[2:0];
		end
		default: begin
			array_muxed0 <= sdram_multiplexer_refreshCmd_payload_ba[2:0];
		end
	endcase
// synthesis translate_off
	dummy_d_154 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_155;
// synthesis translate_on
always @(*) begin
	array_muxed1 <= 14'd0;
	case (sdram_multiplexer_steerer0)
		1'd0: begin
			array_muxed1 <= sdram_multiplexer_nop_a;
		end
		1'd1: begin
			array_muxed1 <= sdram_multiplexer_choose_cmd_cmd_payload_a;
		end
		2'd2: begin
			array_muxed1 <= sdram_multiplexer_choose_req_cmd_payload_a;
		end
		default: begin
			array_muxed1 <= sdram_multiplexer_refreshCmd_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_155 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_156;
// synthesis translate_on
always @(*) begin
	array_muxed2 <= 1'd0;
	case (sdram_multiplexer_steerer0)
		1'd0: begin
			array_muxed2 <= 1'd0;
		end
		1'd1: begin
			array_muxed2 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_cas);
		end
		2'd2: begin
			array_muxed2 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_cas);
		end
		default: begin
			array_muxed2 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_cas);
		end
	endcase
// synthesis translate_off
	dummy_d_156 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_157;
// synthesis translate_on
always @(*) begin
	array_muxed3 <= 1'd0;
	case (sdram_multiplexer_steerer0)
		1'd0: begin
			array_muxed3 <= 1'd0;
		end
		1'd1: begin
			array_muxed3 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_ras);
		end
		2'd2: begin
			array_muxed3 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_ras);
		end
		default: begin
			array_muxed3 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_ras);
		end
	endcase
// synthesis translate_off
	dummy_d_157 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_158;
// synthesis translate_on
always @(*) begin
	array_muxed4 <= 1'd0;
	case (sdram_multiplexer_steerer0)
		1'd0: begin
			array_muxed4 <= 1'd0;
		end
		1'd1: begin
			array_muxed4 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_we);
		end
		2'd2: begin
			array_muxed4 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_we);
		end
		default: begin
			array_muxed4 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_we);
		end
	endcase
// synthesis translate_off
	dummy_d_158 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_159;
// synthesis translate_on
always @(*) begin
	array_muxed5 <= 1'd0;
	case (sdram_multiplexer_steerer0)
		1'd0: begin
			array_muxed5 <= 1'd0;
		end
		1'd1: begin
			array_muxed5 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_is_read);
		end
		2'd2: begin
			array_muxed5 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_read);
		end
		default: begin
			array_muxed5 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_is_read);
		end
	endcase
// synthesis translate_off
	dummy_d_159 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_160;
// synthesis translate_on
always @(*) begin
	array_muxed6 <= 1'd0;
	case (sdram_multiplexer_steerer0)
		1'd0: begin
			array_muxed6 <= 1'd0;
		end
		1'd1: begin
			array_muxed6 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_is_write);
		end
		2'd2: begin
			array_muxed6 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_write);
		end
		default: begin
			array_muxed6 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_is_write);
		end
	endcase
// synthesis translate_off
	dummy_d_160 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_161;
// synthesis translate_on
always @(*) begin
	array_muxed7 <= 3'd0;
	case (sdram_multiplexer_steerer1)
		1'd0: begin
			array_muxed7 <= sdram_multiplexer_nop_ba[2:0];
		end
		1'd1: begin
			array_muxed7 <= sdram_multiplexer_choose_cmd_cmd_payload_ba[2:0];
		end
		2'd2: begin
			array_muxed7 <= sdram_multiplexer_choose_req_cmd_payload_ba[2:0];
		end
		default: begin
			array_muxed7 <= sdram_multiplexer_refreshCmd_payload_ba[2:0];
		end
	endcase
// synthesis translate_off
	dummy_d_161 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_162;
// synthesis translate_on
always @(*) begin
	array_muxed8 <= 14'd0;
	case (sdram_multiplexer_steerer1)
		1'd0: begin
			array_muxed8 <= sdram_multiplexer_nop_a;
		end
		1'd1: begin
			array_muxed8 <= sdram_multiplexer_choose_cmd_cmd_payload_a;
		end
		2'd2: begin
			array_muxed8 <= sdram_multiplexer_choose_req_cmd_payload_a;
		end
		default: begin
			array_muxed8 <= sdram_multiplexer_refreshCmd_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_162 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_163;
// synthesis translate_on
always @(*) begin
	array_muxed9 <= 1'd0;
	case (sdram_multiplexer_steerer1)
		1'd0: begin
			array_muxed9 <= 1'd0;
		end
		1'd1: begin
			array_muxed9 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_cas);
		end
		2'd2: begin
			array_muxed9 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_cas);
		end
		default: begin
			array_muxed9 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_cas);
		end
	endcase
// synthesis translate_off
	dummy_d_163 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_164;
// synthesis translate_on
always @(*) begin
	array_muxed10 <= 1'd0;
	case (sdram_multiplexer_steerer1)
		1'd0: begin
			array_muxed10 <= 1'd0;
		end
		1'd1: begin
			array_muxed10 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_ras);
		end
		2'd2: begin
			array_muxed10 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_ras);
		end
		default: begin
			array_muxed10 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_ras);
		end
	endcase
// synthesis translate_off
	dummy_d_164 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_165;
// synthesis translate_on
always @(*) begin
	array_muxed11 <= 1'd0;
	case (sdram_multiplexer_steerer1)
		1'd0: begin
			array_muxed11 <= 1'd0;
		end
		1'd1: begin
			array_muxed11 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_we);
		end
		2'd2: begin
			array_muxed11 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_we);
		end
		default: begin
			array_muxed11 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_we);
		end
	endcase
// synthesis translate_off
	dummy_d_165 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_166;
// synthesis translate_on
always @(*) begin
	array_muxed12 <= 1'd0;
	case (sdram_multiplexer_steerer1)
		1'd0: begin
			array_muxed12 <= 1'd0;
		end
		1'd1: begin
			array_muxed12 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_is_read);
		end
		2'd2: begin
			array_muxed12 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_read);
		end
		default: begin
			array_muxed12 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_is_read);
		end
	endcase
// synthesis translate_off
	dummy_d_166 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_167;
// synthesis translate_on
always @(*) begin
	array_muxed13 <= 1'd0;
	case (sdram_multiplexer_steerer1)
		1'd0: begin
			array_muxed13 <= 1'd0;
		end
		1'd1: begin
			array_muxed13 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_is_write);
		end
		2'd2: begin
			array_muxed13 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_write);
		end
		default: begin
			array_muxed13 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_is_write);
		end
	endcase
// synthesis translate_off
	dummy_d_167 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_168;
// synthesis translate_on
always @(*) begin
	array_muxed14 <= 3'd0;
	case (sdram_multiplexer_steerer2)
		1'd0: begin
			array_muxed14 <= sdram_multiplexer_nop_ba[2:0];
		end
		1'd1: begin
			array_muxed14 <= sdram_multiplexer_choose_cmd_cmd_payload_ba[2:0];
		end
		2'd2: begin
			array_muxed14 <= sdram_multiplexer_choose_req_cmd_payload_ba[2:0];
		end
		default: begin
			array_muxed14 <= sdram_multiplexer_refreshCmd_payload_ba[2:0];
		end
	endcase
// synthesis translate_off
	dummy_d_168 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_169;
// synthesis translate_on
always @(*) begin
	array_muxed15 <= 14'd0;
	case (sdram_multiplexer_steerer2)
		1'd0: begin
			array_muxed15 <= sdram_multiplexer_nop_a;
		end
		1'd1: begin
			array_muxed15 <= sdram_multiplexer_choose_cmd_cmd_payload_a;
		end
		2'd2: begin
			array_muxed15 <= sdram_multiplexer_choose_req_cmd_payload_a;
		end
		default: begin
			array_muxed15 <= sdram_multiplexer_refreshCmd_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_169 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_170;
// synthesis translate_on
always @(*) begin
	array_muxed16 <= 1'd0;
	case (sdram_multiplexer_steerer2)
		1'd0: begin
			array_muxed16 <= 1'd0;
		end
		1'd1: begin
			array_muxed16 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_cas);
		end
		2'd2: begin
			array_muxed16 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_cas);
		end
		default: begin
			array_muxed16 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_cas);
		end
	endcase
// synthesis translate_off
	dummy_d_170 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_171;
// synthesis translate_on
always @(*) begin
	array_muxed17 <= 1'd0;
	case (sdram_multiplexer_steerer2)
		1'd0: begin
			array_muxed17 <= 1'd0;
		end
		1'd1: begin
			array_muxed17 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_ras);
		end
		2'd2: begin
			array_muxed17 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_ras);
		end
		default: begin
			array_muxed17 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_ras);
		end
	endcase
// synthesis translate_off
	dummy_d_171 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_172;
// synthesis translate_on
always @(*) begin
	array_muxed18 <= 1'd0;
	case (sdram_multiplexer_steerer2)
		1'd0: begin
			array_muxed18 <= 1'd0;
		end
		1'd1: begin
			array_muxed18 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_we);
		end
		2'd2: begin
			array_muxed18 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_we);
		end
		default: begin
			array_muxed18 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_we);
		end
	endcase
// synthesis translate_off
	dummy_d_172 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_173;
// synthesis translate_on
always @(*) begin
	array_muxed19 <= 1'd0;
	case (sdram_multiplexer_steerer2)
		1'd0: begin
			array_muxed19 <= 1'd0;
		end
		1'd1: begin
			array_muxed19 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_is_read);
		end
		2'd2: begin
			array_muxed19 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_read);
		end
		default: begin
			array_muxed19 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_is_read);
		end
	endcase
// synthesis translate_off
	dummy_d_173 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_174;
// synthesis translate_on
always @(*) begin
	array_muxed20 <= 1'd0;
	case (sdram_multiplexer_steerer2)
		1'd0: begin
			array_muxed20 <= 1'd0;
		end
		1'd1: begin
			array_muxed20 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_is_write);
		end
		2'd2: begin
			array_muxed20 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_write);
		end
		default: begin
			array_muxed20 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_is_write);
		end
	endcase
// synthesis translate_off
	dummy_d_174 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_175;
// synthesis translate_on
always @(*) begin
	array_muxed21 <= 3'd0;
	case (sdram_multiplexer_steerer3)
		1'd0: begin
			array_muxed21 <= sdram_multiplexer_nop_ba[2:0];
		end
		1'd1: begin
			array_muxed21 <= sdram_multiplexer_choose_cmd_cmd_payload_ba[2:0];
		end
		2'd2: begin
			array_muxed21 <= sdram_multiplexer_choose_req_cmd_payload_ba[2:0];
		end
		default: begin
			array_muxed21 <= sdram_multiplexer_refreshCmd_payload_ba[2:0];
		end
	endcase
// synthesis translate_off
	dummy_d_175 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_176;
// synthesis translate_on
always @(*) begin
	array_muxed22 <= 14'd0;
	case (sdram_multiplexer_steerer3)
		1'd0: begin
			array_muxed22 <= sdram_multiplexer_nop_a;
		end
		1'd1: begin
			array_muxed22 <= sdram_multiplexer_choose_cmd_cmd_payload_a;
		end
		2'd2: begin
			array_muxed22 <= sdram_multiplexer_choose_req_cmd_payload_a;
		end
		default: begin
			array_muxed22 <= sdram_multiplexer_refreshCmd_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_176 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_177;
// synthesis translate_on
always @(*) begin
	array_muxed23 <= 1'd0;
	case (sdram_multiplexer_steerer3)
		1'd0: begin
			array_muxed23 <= 1'd0;
		end
		1'd1: begin
			array_muxed23 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_cas);
		end
		2'd2: begin
			array_muxed23 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_cas);
		end
		default: begin
			array_muxed23 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_cas);
		end
	endcase
// synthesis translate_off
	dummy_d_177 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_178;
// synthesis translate_on
always @(*) begin
	array_muxed24 <= 1'd0;
	case (sdram_multiplexer_steerer3)
		1'd0: begin
			array_muxed24 <= 1'd0;
		end
		1'd1: begin
			array_muxed24 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_ras);
		end
		2'd2: begin
			array_muxed24 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_ras);
		end
		default: begin
			array_muxed24 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_ras);
		end
	endcase
// synthesis translate_off
	dummy_d_178 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_179;
// synthesis translate_on
always @(*) begin
	array_muxed25 <= 1'd0;
	case (sdram_multiplexer_steerer3)
		1'd0: begin
			array_muxed25 <= 1'd0;
		end
		1'd1: begin
			array_muxed25 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_we);
		end
		2'd2: begin
			array_muxed25 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_we);
		end
		default: begin
			array_muxed25 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_we);
		end
	endcase
// synthesis translate_off
	dummy_d_179 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_180;
// synthesis translate_on
always @(*) begin
	array_muxed26 <= 1'd0;
	case (sdram_multiplexer_steerer3)
		1'd0: begin
			array_muxed26 <= 1'd0;
		end
		1'd1: begin
			array_muxed26 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_is_read);
		end
		2'd2: begin
			array_muxed26 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_read);
		end
		default: begin
			array_muxed26 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_is_read);
		end
	endcase
// synthesis translate_off
	dummy_d_180 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_181;
// synthesis translate_on
always @(*) begin
	array_muxed27 <= 1'd0;
	case (sdram_multiplexer_steerer3)
		1'd0: begin
			array_muxed27 <= 1'd0;
		end
		1'd1: begin
			array_muxed27 <= ((sdram_multiplexer_choose_cmd_cmd_valid & sdram_multiplexer_choose_cmd_cmd_ready) & sdram_multiplexer_choose_cmd_cmd_payload_is_write);
		end
		2'd2: begin
			array_muxed27 <= ((sdram_multiplexer_choose_req_cmd_valid & sdram_multiplexer_choose_req_cmd_ready) & sdram_multiplexer_choose_req_cmd_payload_is_write);
		end
		default: begin
			array_muxed27 <= ((sdram_multiplexer_refreshCmd_valid & sdram_multiplexer_refreshCmd_ready) & sdram_multiplexer_refreshCmd_payload_is_write);
		end
	endcase
// synthesis translate_off
	dummy_d_181 <= dummy_s;
// synthesis translate_on
end

always @(posedge sys_clk) begin
	if (sdram_pi_mod1_inti_p0_rddata_valid) begin
		sdram_pi_mod1_phaseinjector0_status <= sdram_pi_mod1_inti_p0_rddata;
	end
	if (sdram_pi_mod1_inti_p1_rddata_valid) begin
		sdram_pi_mod1_phaseinjector1_status <= sdram_pi_mod1_inti_p1_rddata;
	end
	if (sdram_pi_mod1_inti_p2_rddata_valid) begin
		sdram_pi_mod1_phaseinjector2_status <= sdram_pi_mod1_inti_p2_rddata;
	end
	if (sdram_pi_mod1_inti_p3_rddata_valid) begin
		sdram_pi_mod1_phaseinjector3_status <= sdram_pi_mod1_inti_p3_rddata;
	end
	if (sdram_pi_mod2_inti_p0_rddata_valid) begin
		sdram_pi_mod2_phaseinjector0_status <= sdram_pi_mod2_inti_p0_rddata;
	end
	if (sdram_pi_mod2_inti_p1_rddata_valid) begin
		sdram_pi_mod2_phaseinjector1_status <= sdram_pi_mod2_inti_p1_rddata;
	end
	if (sdram_pi_mod2_inti_p2_rddata_valid) begin
		sdram_pi_mod2_phaseinjector2_status <= sdram_pi_mod2_inti_p2_rddata;
	end
	if (sdram_pi_mod2_inti_p3_rddata_valid) begin
		sdram_pi_mod2_phaseinjector3_status <= sdram_pi_mod2_inti_p3_rddata;
	end
	if (sdram_pi_mod3_inti_p0_rddata_valid) begin
		sdram_pi_mod3_phaseinjector0_status <= sdram_pi_mod3_inti_p0_rddata;
	end
	if (sdram_pi_mod3_inti_p1_rddata_valid) begin
		sdram_pi_mod3_phaseinjector1_status <= sdram_pi_mod3_inti_p1_rddata;
	end
	if (sdram_pi_mod3_inti_p2_rddata_valid) begin
		sdram_pi_mod3_phaseinjector2_status <= sdram_pi_mod3_inti_p2_rddata;
	end
	if (sdram_pi_mod3_inti_p3_rddata_valid) begin
		sdram_pi_mod3_phaseinjector3_status <= sdram_pi_mod3_inti_p3_rddata;
	end
	sdram_cmd_valid <= sdram_tmrrefresher_control0;
	sdram_cmd_last <= sdram_tmrrefresher_control1;
	sdram_cmd_first <= sdram_tmrrefresher_control2;
	sdram_cmd_payload_a <= sdram_tmrrefresher_control3;
	sdram_cmd_payload_ba <= sdram_tmrrefresher_control4;
	sdram_cmd_payload_cas <= sdram_tmrrefresher_control5;
	sdram_cmd_payload_ras <= sdram_tmrrefresher_control6;
	sdram_cmd_payload_we <= sdram_tmrrefresher_control7;
	sdram_cmd_payload_is_cmd <= sdram_tmrrefresher_control8;
	sdram_cmd_payload_is_read <= sdram_tmrrefresher_control9;
	sdram_cmd_payload_is_write <= sdram_tmrrefresher_control10;
	sdram_cmd1_ready <= sdram_cmd_ready;
	sdram_cmd2_ready <= sdram_cmd_ready;
	sdram_cmd3_ready <= sdram_cmd_ready;
	if ((sdram_timer_wait & (~sdram_timer_done0))) begin
		sdram_timer_count1 <= (sdram_timer_count1 - 1'd1);
	end else begin
		sdram_timer_count1 <= 10'd976;
	end
	if ((sdram_timer2_wait & (~sdram_timer2_done0))) begin
		sdram_timer2_count1 <= (sdram_timer2_count1 - 1'd1);
	end else begin
		sdram_timer2_count1 <= 10'd976;
	end
	if ((sdram_timer3_wait & (~sdram_timer3_done0))) begin
		sdram_timer3_count1 <= (sdram_timer3_count1 - 1'd1);
	end else begin
		sdram_timer3_count1 <= 10'd976;
	end
	sdram_postponer_req_o <= 1'd0;
	if (sdram_postponer_req_i) begin
		sdram_postponer_count <= (sdram_postponer_count - 1'd1);
		if ((sdram_postponer_count == 1'd0)) begin
			sdram_postponer_count <= 1'd0;
			sdram_postponer_req_o <= 1'd1;
		end
	end
	sdram_postponer2_req_o <= 1'd0;
	if (sdram_postponer2_req_i) begin
		sdram_postponer2_count <= (sdram_postponer2_count - 1'd1);
		if ((sdram_postponer2_count == 1'd0)) begin
			sdram_postponer2_count <= 1'd0;
			sdram_postponer2_req_o <= 1'd1;
		end
	end
	sdram_postponer3_req_o <= 1'd0;
	if (sdram_postponer3_req_i) begin
		sdram_postponer3_count <= (sdram_postponer3_count - 1'd1);
		if ((sdram_postponer3_count == 1'd0)) begin
			sdram_postponer3_count <= 1'd0;
			sdram_postponer3_req_o <= 1'd1;
		end
	end
	if (sdram_sequencer_start0) begin
		sdram_sequencer_count <= 1'd0;
	end else begin
		if (sdram_sequencer_done1) begin
			if ((sdram_sequencer_count != 1'd0)) begin
				sdram_sequencer_count <= (sdram_sequencer_count - 1'd1);
			end
		end
	end
	sdram_cmd1_payload_a <= 1'd0;
	sdram_cmd1_payload_ba <= 1'd0;
	sdram_cmd1_payload_cas <= 1'd0;
	sdram_cmd1_payload_ras <= 1'd0;
	sdram_cmd1_payload_we <= 1'd0;
	sdram_sequencer_done1 <= 1'd0;
	if ((sdram_sequencer_start1 & (sdram_sequencer_counter == 1'd0))) begin
		sdram_cmd1_payload_a <= 11'd1024;
		sdram_cmd1_payload_ba <= 1'd0;
		sdram_cmd1_payload_cas <= 1'd0;
		sdram_cmd1_payload_ras <= 1'd1;
		sdram_cmd1_payload_we <= 1'd1;
	end
	if ((sdram_sequencer_counter == 2'd3)) begin
		sdram_cmd1_payload_a <= 11'd1024;
		sdram_cmd1_payload_ba <= 1'd0;
		sdram_cmd1_payload_cas <= 1'd1;
		sdram_cmd1_payload_ras <= 1'd1;
		sdram_cmd1_payload_we <= 1'd0;
	end
	if ((sdram_sequencer_counter == 6'd37)) begin
		sdram_cmd1_payload_a <= 1'd0;
		sdram_cmd1_payload_ba <= 1'd0;
		sdram_cmd1_payload_cas <= 1'd0;
		sdram_cmd1_payload_ras <= 1'd0;
		sdram_cmd1_payload_we <= 1'd0;
		sdram_sequencer_done1 <= 1'd1;
	end
	if ((sdram_sequencer_counter == 6'd37)) begin
		sdram_sequencer_counter <= 1'd0;
	end else begin
		if ((sdram_sequencer_counter != 1'd0)) begin
			sdram_sequencer_counter <= (sdram_sequencer_counter + 1'd1);
		end else begin
			if (sdram_sequencer_start1) begin
				sdram_sequencer_counter <= 1'd1;
			end
		end
	end
	if (sdram_sequencer2_start0) begin
		sdram_sequencer2_count <= 1'd0;
	end else begin
		if (sdram_sequencer2_done1) begin
			if ((sdram_sequencer2_count != 1'd0)) begin
				sdram_sequencer2_count <= (sdram_sequencer2_count - 1'd1);
			end
		end
	end
	sdram_cmd2_payload_a <= 1'd0;
	sdram_cmd2_payload_ba <= 1'd0;
	sdram_cmd2_payload_cas <= 1'd0;
	sdram_cmd2_payload_ras <= 1'd0;
	sdram_cmd2_payload_we <= 1'd0;
	sdram_sequencer2_done1 <= 1'd0;
	if ((sdram_sequencer2_start1 & (sdram_sequencer2_counter == 1'd0))) begin
		sdram_cmd2_payload_a <= 11'd1024;
		sdram_cmd2_payload_ba <= 1'd0;
		sdram_cmd2_payload_cas <= 1'd0;
		sdram_cmd2_payload_ras <= 1'd1;
		sdram_cmd2_payload_we <= 1'd1;
	end
	if ((sdram_sequencer2_counter == 2'd3)) begin
		sdram_cmd2_payload_a <= 11'd1024;
		sdram_cmd2_payload_ba <= 1'd0;
		sdram_cmd2_payload_cas <= 1'd1;
		sdram_cmd2_payload_ras <= 1'd1;
		sdram_cmd2_payload_we <= 1'd0;
	end
	if ((sdram_sequencer2_counter == 6'd37)) begin
		sdram_cmd2_payload_a <= 1'd0;
		sdram_cmd2_payload_ba <= 1'd0;
		sdram_cmd2_payload_cas <= 1'd0;
		sdram_cmd2_payload_ras <= 1'd0;
		sdram_cmd2_payload_we <= 1'd0;
		sdram_sequencer2_done1 <= 1'd1;
	end
	if ((sdram_sequencer2_counter == 6'd37)) begin
		sdram_sequencer2_counter <= 1'd0;
	end else begin
		if ((sdram_sequencer2_counter != 1'd0)) begin
			sdram_sequencer2_counter <= (sdram_sequencer2_counter + 1'd1);
		end else begin
			if (sdram_sequencer2_start1) begin
				sdram_sequencer2_counter <= 1'd1;
			end
		end
	end
	if (sdram_sequencer3_start0) begin
		sdram_sequencer3_count <= 1'd0;
	end else begin
		if (sdram_sequencer3_done1) begin
			if ((sdram_sequencer3_count != 1'd0)) begin
				sdram_sequencer3_count <= (sdram_sequencer3_count - 1'd1);
			end
		end
	end
	sdram_cmd3_payload_a <= 1'd0;
	sdram_cmd3_payload_ba <= 1'd0;
	sdram_cmd3_payload_cas <= 1'd0;
	sdram_cmd3_payload_ras <= 1'd0;
	sdram_cmd3_payload_we <= 1'd0;
	sdram_sequencer3_done1 <= 1'd0;
	if ((sdram_sequencer3_start1 & (sdram_sequencer3_counter == 1'd0))) begin
		sdram_cmd3_payload_a <= 11'd1024;
		sdram_cmd3_payload_ba <= 1'd0;
		sdram_cmd3_payload_cas <= 1'd0;
		sdram_cmd3_payload_ras <= 1'd1;
		sdram_cmd3_payload_we <= 1'd1;
	end
	if ((sdram_sequencer3_counter == 2'd3)) begin
		sdram_cmd3_payload_a <= 11'd1024;
		sdram_cmd3_payload_ba <= 1'd0;
		sdram_cmd3_payload_cas <= 1'd1;
		sdram_cmd3_payload_ras <= 1'd1;
		sdram_cmd3_payload_we <= 1'd0;
	end
	if ((sdram_sequencer3_counter == 6'd37)) begin
		sdram_cmd3_payload_a <= 1'd0;
		sdram_cmd3_payload_ba <= 1'd0;
		sdram_cmd3_payload_cas <= 1'd0;
		sdram_cmd3_payload_ras <= 1'd0;
		sdram_cmd3_payload_we <= 1'd0;
		sdram_sequencer3_done1 <= 1'd1;
	end
	if ((sdram_sequencer3_counter == 6'd37)) begin
		sdram_sequencer3_counter <= 1'd0;
	end else begin
		if ((sdram_sequencer3_counter != 1'd0)) begin
			sdram_sequencer3_counter <= (sdram_sequencer3_counter + 1'd1);
		end else begin
			if (sdram_sequencer3_start1) begin
				sdram_sequencer3_counter <= 1'd1;
			end
		end
	end
	if ((sdram_zqcs_timer_wait & (~sdram_zqcs_timer_done0))) begin
		sdram_zqcs_timer_count1 <= (sdram_zqcs_timer_count1 - 1'd1);
	end else begin
		sdram_zqcs_timer_count1 <= 27'd124999999;
	end
	sdram_zqcs_executer_done <= 1'd0;
	if ((sdram_zqcs_executer_start & (sdram_zqcs_executer_counter == 1'd0))) begin
		sdram_cmd_payload_a <= 11'd1024;
		sdram_cmd_payload_ba <= 1'd0;
		sdram_cmd_payload_cas <= 1'd0;
		sdram_cmd_payload_ras <= 1'd1;
		sdram_cmd_payload_we <= 1'd1;
	end
	if ((sdram_zqcs_executer_counter == 2'd3)) begin
		sdram_cmd_payload_a <= 1'd0;
		sdram_cmd_payload_ba <= 1'd0;
		sdram_cmd_payload_cas <= 1'd0;
		sdram_cmd_payload_ras <= 1'd0;
		sdram_cmd_payload_we <= 1'd1;
	end
	if ((sdram_zqcs_executer_counter == 5'd19)) begin
		sdram_cmd_payload_a <= 1'd0;
		sdram_cmd_payload_ba <= 1'd0;
		sdram_cmd_payload_cas <= 1'd0;
		sdram_cmd_payload_ras <= 1'd0;
		sdram_cmd_payload_we <= 1'd0;
		sdram_zqcs_executer_done <= 1'd1;
	end
	if ((sdram_zqcs_executer_counter == 5'd19)) begin
		sdram_zqcs_executer_counter <= 1'd0;
	end else begin
		if ((sdram_zqcs_executer_counter != 1'd0)) begin
			sdram_zqcs_executer_counter <= (sdram_zqcs_executer_counter + 1'd1);
		end else begin
			if (sdram_zqcs_executer_start) begin
				sdram_zqcs_executer_counter <= 1'd1;
			end
		end
	end
	tmrrefresher_state <= tmrrefresher_next_state;
	if (sdram_tmrbankmachine0_row_close) begin
		sdram_tmrbankmachine0_row_opened <= 1'd0;
	end else begin
		if (sdram_tmrbankmachine0_row_open) begin
			sdram_tmrbankmachine0_row_opened <= 1'd1;
			sdram_tmrbankmachine0_row <= sdram_tmrbankmachine0_cmd_buffer_source_payload_addr[20:7];
		end
	end
	if (((sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_we & sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_writable) & (~sdram_tmrbankmachine0_cmd_buffer_lookahead_replace))) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead_produce <= (sdram_tmrbankmachine0_cmd_buffer_lookahead_produce + 1'd1);
	end
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead_do_read) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead_consume <= (sdram_tmrbankmachine0_cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_we & sdram_tmrbankmachine0_cmd_buffer_lookahead_syncfifo0_writable) & (~sdram_tmrbankmachine0_cmd_buffer_lookahead_replace))) begin
		if ((~sdram_tmrbankmachine0_cmd_buffer_lookahead_do_read)) begin
			sdram_tmrbankmachine0_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine0_cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine0_cmd_buffer_lookahead_do_read) begin
			sdram_tmrbankmachine0_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine0_cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine0_cmd_buffer_source_valid) | sdram_tmrbankmachine0_cmd_buffer_source_ready)) begin
		sdram_tmrbankmachine0_cmd_buffer_source_valid <= sdram_tmrbankmachine0_cmd_buffer_sink_valid;
		sdram_tmrbankmachine0_cmd_buffer_source_first <= sdram_tmrbankmachine0_cmd_buffer_sink_first;
		sdram_tmrbankmachine0_cmd_buffer_source_last <= sdram_tmrbankmachine0_cmd_buffer_sink_last;
		sdram_tmrbankmachine0_cmd_buffer_source_payload_we <= sdram_tmrbankmachine0_cmd_buffer_sink_payload_we;
		sdram_tmrbankmachine0_cmd_buffer_source_payload_addr <= sdram_tmrbankmachine0_cmd_buffer_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_we & sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_writable) & (~sdram_tmrbankmachine0_cmd_buffer_lookahead2_replace))) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead2_produce <= (sdram_tmrbankmachine0_cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead2_do_read) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead2_consume <= (sdram_tmrbankmachine0_cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_we & sdram_tmrbankmachine0_cmd_buffer_lookahead2_syncfifo0_writable) & (~sdram_tmrbankmachine0_cmd_buffer_lookahead2_replace))) begin
		if ((~sdram_tmrbankmachine0_cmd_buffer_lookahead2_do_read)) begin
			sdram_tmrbankmachine0_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine0_cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine0_cmd_buffer_lookahead2_do_read) begin
			sdram_tmrbankmachine0_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine0_cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine0_cmd_buffer2_source_valid) | sdram_tmrbankmachine0_cmd_buffer2_source_ready)) begin
		sdram_tmrbankmachine0_cmd_buffer2_source_valid <= sdram_tmrbankmachine0_cmd_buffer2_sink_valid;
		sdram_tmrbankmachine0_cmd_buffer2_source_first <= sdram_tmrbankmachine0_cmd_buffer2_sink_first;
		sdram_tmrbankmachine0_cmd_buffer2_source_last <= sdram_tmrbankmachine0_cmd_buffer2_sink_last;
		sdram_tmrbankmachine0_cmd_buffer2_source_payload_we <= sdram_tmrbankmachine0_cmd_buffer2_sink_payload_we;
		sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr <= sdram_tmrbankmachine0_cmd_buffer2_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_we & sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_writable) & (~sdram_tmrbankmachine0_cmd_buffer_lookahead3_replace))) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead3_produce <= (sdram_tmrbankmachine0_cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead3_do_read) begin
		sdram_tmrbankmachine0_cmd_buffer_lookahead3_consume <= (sdram_tmrbankmachine0_cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_we & sdram_tmrbankmachine0_cmd_buffer_lookahead3_syncfifo0_writable) & (~sdram_tmrbankmachine0_cmd_buffer_lookahead3_replace))) begin
		if ((~sdram_tmrbankmachine0_cmd_buffer_lookahead3_do_read)) begin
			sdram_tmrbankmachine0_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine0_cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine0_cmd_buffer_lookahead3_do_read) begin
			sdram_tmrbankmachine0_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine0_cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine0_cmd_buffer3_source_valid) | sdram_tmrbankmachine0_cmd_buffer3_source_ready)) begin
		sdram_tmrbankmachine0_cmd_buffer3_source_valid <= sdram_tmrbankmachine0_cmd_buffer3_sink_valid;
		sdram_tmrbankmachine0_cmd_buffer3_source_first <= sdram_tmrbankmachine0_cmd_buffer3_sink_first;
		sdram_tmrbankmachine0_cmd_buffer3_source_last <= sdram_tmrbankmachine0_cmd_buffer3_sink_last;
		sdram_tmrbankmachine0_cmd_buffer3_source_payload_we <= sdram_tmrbankmachine0_cmd_buffer3_sink_payload_we;
		sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr <= sdram_tmrbankmachine0_cmd_buffer3_sink_payload_addr;
	end
	if (sdram_tmrbankmachine0_twtpcon_valid) begin
		sdram_tmrbankmachine0_twtpcon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine0_twtpcon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_twtpcon_ready)) begin
			sdram_tmrbankmachine0_twtpcon_count <= (sdram_tmrbankmachine0_twtpcon_count - 1'd1);
			if ((sdram_tmrbankmachine0_twtpcon_count == 1'd1)) begin
				sdram_tmrbankmachine0_twtpcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine0_twtpcon2_valid) begin
		sdram_tmrbankmachine0_twtpcon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine0_twtpcon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_twtpcon2_ready)) begin
			sdram_tmrbankmachine0_twtpcon2_count <= (sdram_tmrbankmachine0_twtpcon2_count - 1'd1);
			if ((sdram_tmrbankmachine0_twtpcon2_count == 1'd1)) begin
				sdram_tmrbankmachine0_twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine0_twtpcon3_valid) begin
		sdram_tmrbankmachine0_twtpcon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine0_twtpcon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_twtpcon3_ready)) begin
			sdram_tmrbankmachine0_twtpcon3_count <= (sdram_tmrbankmachine0_twtpcon3_count - 1'd1);
			if ((sdram_tmrbankmachine0_twtpcon3_count == 1'd1)) begin
				sdram_tmrbankmachine0_twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine0_trccon_valid) begin
		sdram_tmrbankmachine0_trccon_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine0_trccon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_trccon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_trccon_ready)) begin
			sdram_tmrbankmachine0_trccon_count <= (sdram_tmrbankmachine0_trccon_count - 1'd1);
			if ((sdram_tmrbankmachine0_trccon_count == 1'd1)) begin
				sdram_tmrbankmachine0_trccon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine0_trccon2_valid) begin
		sdram_tmrbankmachine0_trccon2_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine0_trccon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_trccon2_ready)) begin
			sdram_tmrbankmachine0_trccon2_count <= (sdram_tmrbankmachine0_trccon2_count - 1'd1);
			if ((sdram_tmrbankmachine0_trccon2_count == 1'd1)) begin
				sdram_tmrbankmachine0_trccon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine0_trccon3_valid) begin
		sdram_tmrbankmachine0_trccon3_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine0_trccon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_trccon3_ready)) begin
			sdram_tmrbankmachine0_trccon3_count <= (sdram_tmrbankmachine0_trccon3_count - 1'd1);
			if ((sdram_tmrbankmachine0_trccon3_count == 1'd1)) begin
				sdram_tmrbankmachine0_trccon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine0_trascon_valid) begin
		sdram_tmrbankmachine0_trascon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine0_trascon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_trascon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_trascon_ready)) begin
			sdram_tmrbankmachine0_trascon_count <= (sdram_tmrbankmachine0_trascon_count - 1'd1);
			if ((sdram_tmrbankmachine0_trascon_count == 1'd1)) begin
				sdram_tmrbankmachine0_trascon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine0_trascon2_valid) begin
		sdram_tmrbankmachine0_trascon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine0_trascon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_trascon2_ready)) begin
			sdram_tmrbankmachine0_trascon2_count <= (sdram_tmrbankmachine0_trascon2_count - 1'd1);
			if ((sdram_tmrbankmachine0_trascon2_count == 1'd1)) begin
				sdram_tmrbankmachine0_trascon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine0_trascon3_valid) begin
		sdram_tmrbankmachine0_trascon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine0_trascon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine0_trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine0_trascon3_ready)) begin
			sdram_tmrbankmachine0_trascon3_count <= (sdram_tmrbankmachine0_trascon3_count - 1'd1);
			if ((sdram_tmrbankmachine0_trascon3_count == 1'd1)) begin
				sdram_tmrbankmachine0_trascon3_ready <= 1'd1;
			end
		end
	end
	tmrbankmachine0_state <= tmrbankmachine0_next_state;
	if (sdram_tmrbankmachine1_row_close) begin
		sdram_tmrbankmachine1_row_opened <= 1'd0;
	end else begin
		if (sdram_tmrbankmachine1_row_open) begin
			sdram_tmrbankmachine1_row_opened <= 1'd1;
			sdram_tmrbankmachine1_row <= sdram_tmrbankmachine1_cmd_buffer_source_payload_addr[20:7];
		end
	end
	if (((sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_we & sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_writable) & (~sdram_tmrbankmachine1_cmd_buffer_lookahead_replace))) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead_produce <= (sdram_tmrbankmachine1_cmd_buffer_lookahead_produce + 1'd1);
	end
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead_do_read) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead_consume <= (sdram_tmrbankmachine1_cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_we & sdram_tmrbankmachine1_cmd_buffer_lookahead_syncfifo1_writable) & (~sdram_tmrbankmachine1_cmd_buffer_lookahead_replace))) begin
		if ((~sdram_tmrbankmachine1_cmd_buffer_lookahead_do_read)) begin
			sdram_tmrbankmachine1_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine1_cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine1_cmd_buffer_lookahead_do_read) begin
			sdram_tmrbankmachine1_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine1_cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine1_cmd_buffer_source_valid) | sdram_tmrbankmachine1_cmd_buffer_source_ready)) begin
		sdram_tmrbankmachine1_cmd_buffer_source_valid <= sdram_tmrbankmachine1_cmd_buffer_sink_valid;
		sdram_tmrbankmachine1_cmd_buffer_source_first <= sdram_tmrbankmachine1_cmd_buffer_sink_first;
		sdram_tmrbankmachine1_cmd_buffer_source_last <= sdram_tmrbankmachine1_cmd_buffer_sink_last;
		sdram_tmrbankmachine1_cmd_buffer_source_payload_we <= sdram_tmrbankmachine1_cmd_buffer_sink_payload_we;
		sdram_tmrbankmachine1_cmd_buffer_source_payload_addr <= sdram_tmrbankmachine1_cmd_buffer_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_we & sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_writable) & (~sdram_tmrbankmachine1_cmd_buffer_lookahead2_replace))) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead2_produce <= (sdram_tmrbankmachine1_cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead2_do_read) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead2_consume <= (sdram_tmrbankmachine1_cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_we & sdram_tmrbankmachine1_cmd_buffer_lookahead2_syncfifo1_writable) & (~sdram_tmrbankmachine1_cmd_buffer_lookahead2_replace))) begin
		if ((~sdram_tmrbankmachine1_cmd_buffer_lookahead2_do_read)) begin
			sdram_tmrbankmachine1_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine1_cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine1_cmd_buffer_lookahead2_do_read) begin
			sdram_tmrbankmachine1_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine1_cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine1_cmd_buffer2_source_valid) | sdram_tmrbankmachine1_cmd_buffer2_source_ready)) begin
		sdram_tmrbankmachine1_cmd_buffer2_source_valid <= sdram_tmrbankmachine1_cmd_buffer2_sink_valid;
		sdram_tmrbankmachine1_cmd_buffer2_source_first <= sdram_tmrbankmachine1_cmd_buffer2_sink_first;
		sdram_tmrbankmachine1_cmd_buffer2_source_last <= sdram_tmrbankmachine1_cmd_buffer2_sink_last;
		sdram_tmrbankmachine1_cmd_buffer2_source_payload_we <= sdram_tmrbankmachine1_cmd_buffer2_sink_payload_we;
		sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr <= sdram_tmrbankmachine1_cmd_buffer2_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_we & sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_writable) & (~sdram_tmrbankmachine1_cmd_buffer_lookahead3_replace))) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead3_produce <= (sdram_tmrbankmachine1_cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead3_do_read) begin
		sdram_tmrbankmachine1_cmd_buffer_lookahead3_consume <= (sdram_tmrbankmachine1_cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_we & sdram_tmrbankmachine1_cmd_buffer_lookahead3_syncfifo1_writable) & (~sdram_tmrbankmachine1_cmd_buffer_lookahead3_replace))) begin
		if ((~sdram_tmrbankmachine1_cmd_buffer_lookahead3_do_read)) begin
			sdram_tmrbankmachine1_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine1_cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine1_cmd_buffer_lookahead3_do_read) begin
			sdram_tmrbankmachine1_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine1_cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine1_cmd_buffer3_source_valid) | sdram_tmrbankmachine1_cmd_buffer3_source_ready)) begin
		sdram_tmrbankmachine1_cmd_buffer3_source_valid <= sdram_tmrbankmachine1_cmd_buffer3_sink_valid;
		sdram_tmrbankmachine1_cmd_buffer3_source_first <= sdram_tmrbankmachine1_cmd_buffer3_sink_first;
		sdram_tmrbankmachine1_cmd_buffer3_source_last <= sdram_tmrbankmachine1_cmd_buffer3_sink_last;
		sdram_tmrbankmachine1_cmd_buffer3_source_payload_we <= sdram_tmrbankmachine1_cmd_buffer3_sink_payload_we;
		sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr <= sdram_tmrbankmachine1_cmd_buffer3_sink_payload_addr;
	end
	if (sdram_tmrbankmachine1_twtpcon_valid) begin
		sdram_tmrbankmachine1_twtpcon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine1_twtpcon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_twtpcon_ready)) begin
			sdram_tmrbankmachine1_twtpcon_count <= (sdram_tmrbankmachine1_twtpcon_count - 1'd1);
			if ((sdram_tmrbankmachine1_twtpcon_count == 1'd1)) begin
				sdram_tmrbankmachine1_twtpcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine1_twtpcon2_valid) begin
		sdram_tmrbankmachine1_twtpcon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine1_twtpcon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_twtpcon2_ready)) begin
			sdram_tmrbankmachine1_twtpcon2_count <= (sdram_tmrbankmachine1_twtpcon2_count - 1'd1);
			if ((sdram_tmrbankmachine1_twtpcon2_count == 1'd1)) begin
				sdram_tmrbankmachine1_twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine1_twtpcon3_valid) begin
		sdram_tmrbankmachine1_twtpcon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine1_twtpcon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_twtpcon3_ready)) begin
			sdram_tmrbankmachine1_twtpcon3_count <= (sdram_tmrbankmachine1_twtpcon3_count - 1'd1);
			if ((sdram_tmrbankmachine1_twtpcon3_count == 1'd1)) begin
				sdram_tmrbankmachine1_twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine1_trccon_valid) begin
		sdram_tmrbankmachine1_trccon_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine1_trccon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_trccon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_trccon_ready)) begin
			sdram_tmrbankmachine1_trccon_count <= (sdram_tmrbankmachine1_trccon_count - 1'd1);
			if ((sdram_tmrbankmachine1_trccon_count == 1'd1)) begin
				sdram_tmrbankmachine1_trccon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine1_trccon2_valid) begin
		sdram_tmrbankmachine1_trccon2_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine1_trccon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_trccon2_ready)) begin
			sdram_tmrbankmachine1_trccon2_count <= (sdram_tmrbankmachine1_trccon2_count - 1'd1);
			if ((sdram_tmrbankmachine1_trccon2_count == 1'd1)) begin
				sdram_tmrbankmachine1_trccon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine1_trccon3_valid) begin
		sdram_tmrbankmachine1_trccon3_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine1_trccon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_trccon3_ready)) begin
			sdram_tmrbankmachine1_trccon3_count <= (sdram_tmrbankmachine1_trccon3_count - 1'd1);
			if ((sdram_tmrbankmachine1_trccon3_count == 1'd1)) begin
				sdram_tmrbankmachine1_trccon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine1_trascon_valid) begin
		sdram_tmrbankmachine1_trascon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine1_trascon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_trascon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_trascon_ready)) begin
			sdram_tmrbankmachine1_trascon_count <= (sdram_tmrbankmachine1_trascon_count - 1'd1);
			if ((sdram_tmrbankmachine1_trascon_count == 1'd1)) begin
				sdram_tmrbankmachine1_trascon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine1_trascon2_valid) begin
		sdram_tmrbankmachine1_trascon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine1_trascon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_trascon2_ready)) begin
			sdram_tmrbankmachine1_trascon2_count <= (sdram_tmrbankmachine1_trascon2_count - 1'd1);
			if ((sdram_tmrbankmachine1_trascon2_count == 1'd1)) begin
				sdram_tmrbankmachine1_trascon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine1_trascon3_valid) begin
		sdram_tmrbankmachine1_trascon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine1_trascon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine1_trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine1_trascon3_ready)) begin
			sdram_tmrbankmachine1_trascon3_count <= (sdram_tmrbankmachine1_trascon3_count - 1'd1);
			if ((sdram_tmrbankmachine1_trascon3_count == 1'd1)) begin
				sdram_tmrbankmachine1_trascon3_ready <= 1'd1;
			end
		end
	end
	tmrbankmachine1_state <= tmrbankmachine1_next_state;
	if (sdram_tmrbankmachine2_row_close) begin
		sdram_tmrbankmachine2_row_opened <= 1'd0;
	end else begin
		if (sdram_tmrbankmachine2_row_open) begin
			sdram_tmrbankmachine2_row_opened <= 1'd1;
			sdram_tmrbankmachine2_row <= sdram_tmrbankmachine2_cmd_buffer_source_payload_addr[20:7];
		end
	end
	if (((sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_we & sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_writable) & (~sdram_tmrbankmachine2_cmd_buffer_lookahead_replace))) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead_produce <= (sdram_tmrbankmachine2_cmd_buffer_lookahead_produce + 1'd1);
	end
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead_do_read) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead_consume <= (sdram_tmrbankmachine2_cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_we & sdram_tmrbankmachine2_cmd_buffer_lookahead_syncfifo2_writable) & (~sdram_tmrbankmachine2_cmd_buffer_lookahead_replace))) begin
		if ((~sdram_tmrbankmachine2_cmd_buffer_lookahead_do_read)) begin
			sdram_tmrbankmachine2_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine2_cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine2_cmd_buffer_lookahead_do_read) begin
			sdram_tmrbankmachine2_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine2_cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine2_cmd_buffer_source_valid) | sdram_tmrbankmachine2_cmd_buffer_source_ready)) begin
		sdram_tmrbankmachine2_cmd_buffer_source_valid <= sdram_tmrbankmachine2_cmd_buffer_sink_valid;
		sdram_tmrbankmachine2_cmd_buffer_source_first <= sdram_tmrbankmachine2_cmd_buffer_sink_first;
		sdram_tmrbankmachine2_cmd_buffer_source_last <= sdram_tmrbankmachine2_cmd_buffer_sink_last;
		sdram_tmrbankmachine2_cmd_buffer_source_payload_we <= sdram_tmrbankmachine2_cmd_buffer_sink_payload_we;
		sdram_tmrbankmachine2_cmd_buffer_source_payload_addr <= sdram_tmrbankmachine2_cmd_buffer_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_we & sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_writable) & (~sdram_tmrbankmachine2_cmd_buffer_lookahead2_replace))) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead2_produce <= (sdram_tmrbankmachine2_cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead2_do_read) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead2_consume <= (sdram_tmrbankmachine2_cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_we & sdram_tmrbankmachine2_cmd_buffer_lookahead2_syncfifo2_writable) & (~sdram_tmrbankmachine2_cmd_buffer_lookahead2_replace))) begin
		if ((~sdram_tmrbankmachine2_cmd_buffer_lookahead2_do_read)) begin
			sdram_tmrbankmachine2_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine2_cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine2_cmd_buffer_lookahead2_do_read) begin
			sdram_tmrbankmachine2_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine2_cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine2_cmd_buffer2_source_valid) | sdram_tmrbankmachine2_cmd_buffer2_source_ready)) begin
		sdram_tmrbankmachine2_cmd_buffer2_source_valid <= sdram_tmrbankmachine2_cmd_buffer2_sink_valid;
		sdram_tmrbankmachine2_cmd_buffer2_source_first <= sdram_tmrbankmachine2_cmd_buffer2_sink_first;
		sdram_tmrbankmachine2_cmd_buffer2_source_last <= sdram_tmrbankmachine2_cmd_buffer2_sink_last;
		sdram_tmrbankmachine2_cmd_buffer2_source_payload_we <= sdram_tmrbankmachine2_cmd_buffer2_sink_payload_we;
		sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr <= sdram_tmrbankmachine2_cmd_buffer2_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_we & sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_writable) & (~sdram_tmrbankmachine2_cmd_buffer_lookahead3_replace))) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead3_produce <= (sdram_tmrbankmachine2_cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead3_do_read) begin
		sdram_tmrbankmachine2_cmd_buffer_lookahead3_consume <= (sdram_tmrbankmachine2_cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_we & sdram_tmrbankmachine2_cmd_buffer_lookahead3_syncfifo2_writable) & (~sdram_tmrbankmachine2_cmd_buffer_lookahead3_replace))) begin
		if ((~sdram_tmrbankmachine2_cmd_buffer_lookahead3_do_read)) begin
			sdram_tmrbankmachine2_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine2_cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine2_cmd_buffer_lookahead3_do_read) begin
			sdram_tmrbankmachine2_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine2_cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine2_cmd_buffer3_source_valid) | sdram_tmrbankmachine2_cmd_buffer3_source_ready)) begin
		sdram_tmrbankmachine2_cmd_buffer3_source_valid <= sdram_tmrbankmachine2_cmd_buffer3_sink_valid;
		sdram_tmrbankmachine2_cmd_buffer3_source_first <= sdram_tmrbankmachine2_cmd_buffer3_sink_first;
		sdram_tmrbankmachine2_cmd_buffer3_source_last <= sdram_tmrbankmachine2_cmd_buffer3_sink_last;
		sdram_tmrbankmachine2_cmd_buffer3_source_payload_we <= sdram_tmrbankmachine2_cmd_buffer3_sink_payload_we;
		sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr <= sdram_tmrbankmachine2_cmd_buffer3_sink_payload_addr;
	end
	if (sdram_tmrbankmachine2_twtpcon_valid) begin
		sdram_tmrbankmachine2_twtpcon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine2_twtpcon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_twtpcon_ready)) begin
			sdram_tmrbankmachine2_twtpcon_count <= (sdram_tmrbankmachine2_twtpcon_count - 1'd1);
			if ((sdram_tmrbankmachine2_twtpcon_count == 1'd1)) begin
				sdram_tmrbankmachine2_twtpcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine2_twtpcon2_valid) begin
		sdram_tmrbankmachine2_twtpcon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine2_twtpcon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_twtpcon2_ready)) begin
			sdram_tmrbankmachine2_twtpcon2_count <= (sdram_tmrbankmachine2_twtpcon2_count - 1'd1);
			if ((sdram_tmrbankmachine2_twtpcon2_count == 1'd1)) begin
				sdram_tmrbankmachine2_twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine2_twtpcon3_valid) begin
		sdram_tmrbankmachine2_twtpcon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine2_twtpcon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_twtpcon3_ready)) begin
			sdram_tmrbankmachine2_twtpcon3_count <= (sdram_tmrbankmachine2_twtpcon3_count - 1'd1);
			if ((sdram_tmrbankmachine2_twtpcon3_count == 1'd1)) begin
				sdram_tmrbankmachine2_twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine2_trccon_valid) begin
		sdram_tmrbankmachine2_trccon_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine2_trccon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_trccon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_trccon_ready)) begin
			sdram_tmrbankmachine2_trccon_count <= (sdram_tmrbankmachine2_trccon_count - 1'd1);
			if ((sdram_tmrbankmachine2_trccon_count == 1'd1)) begin
				sdram_tmrbankmachine2_trccon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine2_trccon2_valid) begin
		sdram_tmrbankmachine2_trccon2_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine2_trccon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_trccon2_ready)) begin
			sdram_tmrbankmachine2_trccon2_count <= (sdram_tmrbankmachine2_trccon2_count - 1'd1);
			if ((sdram_tmrbankmachine2_trccon2_count == 1'd1)) begin
				sdram_tmrbankmachine2_trccon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine2_trccon3_valid) begin
		sdram_tmrbankmachine2_trccon3_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine2_trccon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_trccon3_ready)) begin
			sdram_tmrbankmachine2_trccon3_count <= (sdram_tmrbankmachine2_trccon3_count - 1'd1);
			if ((sdram_tmrbankmachine2_trccon3_count == 1'd1)) begin
				sdram_tmrbankmachine2_trccon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine2_trascon_valid) begin
		sdram_tmrbankmachine2_trascon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine2_trascon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_trascon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_trascon_ready)) begin
			sdram_tmrbankmachine2_trascon_count <= (sdram_tmrbankmachine2_trascon_count - 1'd1);
			if ((sdram_tmrbankmachine2_trascon_count == 1'd1)) begin
				sdram_tmrbankmachine2_trascon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine2_trascon2_valid) begin
		sdram_tmrbankmachine2_trascon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine2_trascon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_trascon2_ready)) begin
			sdram_tmrbankmachine2_trascon2_count <= (sdram_tmrbankmachine2_trascon2_count - 1'd1);
			if ((sdram_tmrbankmachine2_trascon2_count == 1'd1)) begin
				sdram_tmrbankmachine2_trascon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine2_trascon3_valid) begin
		sdram_tmrbankmachine2_trascon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine2_trascon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine2_trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine2_trascon3_ready)) begin
			sdram_tmrbankmachine2_trascon3_count <= (sdram_tmrbankmachine2_trascon3_count - 1'd1);
			if ((sdram_tmrbankmachine2_trascon3_count == 1'd1)) begin
				sdram_tmrbankmachine2_trascon3_ready <= 1'd1;
			end
		end
	end
	tmrbankmachine2_state <= tmrbankmachine2_next_state;
	if (sdram_tmrbankmachine3_row_close) begin
		sdram_tmrbankmachine3_row_opened <= 1'd0;
	end else begin
		if (sdram_tmrbankmachine3_row_open) begin
			sdram_tmrbankmachine3_row_opened <= 1'd1;
			sdram_tmrbankmachine3_row <= sdram_tmrbankmachine3_cmd_buffer_source_payload_addr[20:7];
		end
	end
	if (((sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_we & sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_writable) & (~sdram_tmrbankmachine3_cmd_buffer_lookahead_replace))) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead_produce <= (sdram_tmrbankmachine3_cmd_buffer_lookahead_produce + 1'd1);
	end
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead_do_read) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead_consume <= (sdram_tmrbankmachine3_cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_we & sdram_tmrbankmachine3_cmd_buffer_lookahead_syncfifo3_writable) & (~sdram_tmrbankmachine3_cmd_buffer_lookahead_replace))) begin
		if ((~sdram_tmrbankmachine3_cmd_buffer_lookahead_do_read)) begin
			sdram_tmrbankmachine3_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine3_cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine3_cmd_buffer_lookahead_do_read) begin
			sdram_tmrbankmachine3_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine3_cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine3_cmd_buffer_source_valid) | sdram_tmrbankmachine3_cmd_buffer_source_ready)) begin
		sdram_tmrbankmachine3_cmd_buffer_source_valid <= sdram_tmrbankmachine3_cmd_buffer_sink_valid;
		sdram_tmrbankmachine3_cmd_buffer_source_first <= sdram_tmrbankmachine3_cmd_buffer_sink_first;
		sdram_tmrbankmachine3_cmd_buffer_source_last <= sdram_tmrbankmachine3_cmd_buffer_sink_last;
		sdram_tmrbankmachine3_cmd_buffer_source_payload_we <= sdram_tmrbankmachine3_cmd_buffer_sink_payload_we;
		sdram_tmrbankmachine3_cmd_buffer_source_payload_addr <= sdram_tmrbankmachine3_cmd_buffer_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_we & sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_writable) & (~sdram_tmrbankmachine3_cmd_buffer_lookahead2_replace))) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead2_produce <= (sdram_tmrbankmachine3_cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead2_do_read) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead2_consume <= (sdram_tmrbankmachine3_cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_we & sdram_tmrbankmachine3_cmd_buffer_lookahead2_syncfifo3_writable) & (~sdram_tmrbankmachine3_cmd_buffer_lookahead2_replace))) begin
		if ((~sdram_tmrbankmachine3_cmd_buffer_lookahead2_do_read)) begin
			sdram_tmrbankmachine3_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine3_cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine3_cmd_buffer_lookahead2_do_read) begin
			sdram_tmrbankmachine3_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine3_cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine3_cmd_buffer2_source_valid) | sdram_tmrbankmachine3_cmd_buffer2_source_ready)) begin
		sdram_tmrbankmachine3_cmd_buffer2_source_valid <= sdram_tmrbankmachine3_cmd_buffer2_sink_valid;
		sdram_tmrbankmachine3_cmd_buffer2_source_first <= sdram_tmrbankmachine3_cmd_buffer2_sink_first;
		sdram_tmrbankmachine3_cmd_buffer2_source_last <= sdram_tmrbankmachine3_cmd_buffer2_sink_last;
		sdram_tmrbankmachine3_cmd_buffer2_source_payload_we <= sdram_tmrbankmachine3_cmd_buffer2_sink_payload_we;
		sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr <= sdram_tmrbankmachine3_cmd_buffer2_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_we & sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_writable) & (~sdram_tmrbankmachine3_cmd_buffer_lookahead3_replace))) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead3_produce <= (sdram_tmrbankmachine3_cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead3_do_read) begin
		sdram_tmrbankmachine3_cmd_buffer_lookahead3_consume <= (sdram_tmrbankmachine3_cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_we & sdram_tmrbankmachine3_cmd_buffer_lookahead3_syncfifo3_writable) & (~sdram_tmrbankmachine3_cmd_buffer_lookahead3_replace))) begin
		if ((~sdram_tmrbankmachine3_cmd_buffer_lookahead3_do_read)) begin
			sdram_tmrbankmachine3_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine3_cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine3_cmd_buffer_lookahead3_do_read) begin
			sdram_tmrbankmachine3_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine3_cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine3_cmd_buffer3_source_valid) | sdram_tmrbankmachine3_cmd_buffer3_source_ready)) begin
		sdram_tmrbankmachine3_cmd_buffer3_source_valid <= sdram_tmrbankmachine3_cmd_buffer3_sink_valid;
		sdram_tmrbankmachine3_cmd_buffer3_source_first <= sdram_tmrbankmachine3_cmd_buffer3_sink_first;
		sdram_tmrbankmachine3_cmd_buffer3_source_last <= sdram_tmrbankmachine3_cmd_buffer3_sink_last;
		sdram_tmrbankmachine3_cmd_buffer3_source_payload_we <= sdram_tmrbankmachine3_cmd_buffer3_sink_payload_we;
		sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr <= sdram_tmrbankmachine3_cmd_buffer3_sink_payload_addr;
	end
	if (sdram_tmrbankmachine3_twtpcon_valid) begin
		sdram_tmrbankmachine3_twtpcon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine3_twtpcon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_twtpcon_ready)) begin
			sdram_tmrbankmachine3_twtpcon_count <= (sdram_tmrbankmachine3_twtpcon_count - 1'd1);
			if ((sdram_tmrbankmachine3_twtpcon_count == 1'd1)) begin
				sdram_tmrbankmachine3_twtpcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine3_twtpcon2_valid) begin
		sdram_tmrbankmachine3_twtpcon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine3_twtpcon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_twtpcon2_ready)) begin
			sdram_tmrbankmachine3_twtpcon2_count <= (sdram_tmrbankmachine3_twtpcon2_count - 1'd1);
			if ((sdram_tmrbankmachine3_twtpcon2_count == 1'd1)) begin
				sdram_tmrbankmachine3_twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine3_twtpcon3_valid) begin
		sdram_tmrbankmachine3_twtpcon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine3_twtpcon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_twtpcon3_ready)) begin
			sdram_tmrbankmachine3_twtpcon3_count <= (sdram_tmrbankmachine3_twtpcon3_count - 1'd1);
			if ((sdram_tmrbankmachine3_twtpcon3_count == 1'd1)) begin
				sdram_tmrbankmachine3_twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine3_trccon_valid) begin
		sdram_tmrbankmachine3_trccon_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine3_trccon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_trccon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_trccon_ready)) begin
			sdram_tmrbankmachine3_trccon_count <= (sdram_tmrbankmachine3_trccon_count - 1'd1);
			if ((sdram_tmrbankmachine3_trccon_count == 1'd1)) begin
				sdram_tmrbankmachine3_trccon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine3_trccon2_valid) begin
		sdram_tmrbankmachine3_trccon2_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine3_trccon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_trccon2_ready)) begin
			sdram_tmrbankmachine3_trccon2_count <= (sdram_tmrbankmachine3_trccon2_count - 1'd1);
			if ((sdram_tmrbankmachine3_trccon2_count == 1'd1)) begin
				sdram_tmrbankmachine3_trccon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine3_trccon3_valid) begin
		sdram_tmrbankmachine3_trccon3_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine3_trccon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_trccon3_ready)) begin
			sdram_tmrbankmachine3_trccon3_count <= (sdram_tmrbankmachine3_trccon3_count - 1'd1);
			if ((sdram_tmrbankmachine3_trccon3_count == 1'd1)) begin
				sdram_tmrbankmachine3_trccon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine3_trascon_valid) begin
		sdram_tmrbankmachine3_trascon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine3_trascon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_trascon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_trascon_ready)) begin
			sdram_tmrbankmachine3_trascon_count <= (sdram_tmrbankmachine3_trascon_count - 1'd1);
			if ((sdram_tmrbankmachine3_trascon_count == 1'd1)) begin
				sdram_tmrbankmachine3_trascon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine3_trascon2_valid) begin
		sdram_tmrbankmachine3_trascon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine3_trascon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_trascon2_ready)) begin
			sdram_tmrbankmachine3_trascon2_count <= (sdram_tmrbankmachine3_trascon2_count - 1'd1);
			if ((sdram_tmrbankmachine3_trascon2_count == 1'd1)) begin
				sdram_tmrbankmachine3_trascon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine3_trascon3_valid) begin
		sdram_tmrbankmachine3_trascon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine3_trascon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine3_trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine3_trascon3_ready)) begin
			sdram_tmrbankmachine3_trascon3_count <= (sdram_tmrbankmachine3_trascon3_count - 1'd1);
			if ((sdram_tmrbankmachine3_trascon3_count == 1'd1)) begin
				sdram_tmrbankmachine3_trascon3_ready <= 1'd1;
			end
		end
	end
	tmrbankmachine3_state <= tmrbankmachine3_next_state;
	if (sdram_tmrbankmachine4_row_close) begin
		sdram_tmrbankmachine4_row_opened <= 1'd0;
	end else begin
		if (sdram_tmrbankmachine4_row_open) begin
			sdram_tmrbankmachine4_row_opened <= 1'd1;
			sdram_tmrbankmachine4_row <= sdram_tmrbankmachine4_cmd_buffer_source_payload_addr[20:7];
		end
	end
	if (((sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_we & sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_writable) & (~sdram_tmrbankmachine4_cmd_buffer_lookahead_replace))) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead_produce <= (sdram_tmrbankmachine4_cmd_buffer_lookahead_produce + 1'd1);
	end
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead_do_read) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead_consume <= (sdram_tmrbankmachine4_cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_we & sdram_tmrbankmachine4_cmd_buffer_lookahead_syncfifo4_writable) & (~sdram_tmrbankmachine4_cmd_buffer_lookahead_replace))) begin
		if ((~sdram_tmrbankmachine4_cmd_buffer_lookahead_do_read)) begin
			sdram_tmrbankmachine4_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine4_cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine4_cmd_buffer_lookahead_do_read) begin
			sdram_tmrbankmachine4_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine4_cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine4_cmd_buffer_source_valid) | sdram_tmrbankmachine4_cmd_buffer_source_ready)) begin
		sdram_tmrbankmachine4_cmd_buffer_source_valid <= sdram_tmrbankmachine4_cmd_buffer_sink_valid;
		sdram_tmrbankmachine4_cmd_buffer_source_first <= sdram_tmrbankmachine4_cmd_buffer_sink_first;
		sdram_tmrbankmachine4_cmd_buffer_source_last <= sdram_tmrbankmachine4_cmd_buffer_sink_last;
		sdram_tmrbankmachine4_cmd_buffer_source_payload_we <= sdram_tmrbankmachine4_cmd_buffer_sink_payload_we;
		sdram_tmrbankmachine4_cmd_buffer_source_payload_addr <= sdram_tmrbankmachine4_cmd_buffer_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_we & sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_writable) & (~sdram_tmrbankmachine4_cmd_buffer_lookahead2_replace))) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead2_produce <= (sdram_tmrbankmachine4_cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead2_do_read) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead2_consume <= (sdram_tmrbankmachine4_cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_we & sdram_tmrbankmachine4_cmd_buffer_lookahead2_syncfifo4_writable) & (~sdram_tmrbankmachine4_cmd_buffer_lookahead2_replace))) begin
		if ((~sdram_tmrbankmachine4_cmd_buffer_lookahead2_do_read)) begin
			sdram_tmrbankmachine4_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine4_cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine4_cmd_buffer_lookahead2_do_read) begin
			sdram_tmrbankmachine4_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine4_cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine4_cmd_buffer2_source_valid) | sdram_tmrbankmachine4_cmd_buffer2_source_ready)) begin
		sdram_tmrbankmachine4_cmd_buffer2_source_valid <= sdram_tmrbankmachine4_cmd_buffer2_sink_valid;
		sdram_tmrbankmachine4_cmd_buffer2_source_first <= sdram_tmrbankmachine4_cmd_buffer2_sink_first;
		sdram_tmrbankmachine4_cmd_buffer2_source_last <= sdram_tmrbankmachine4_cmd_buffer2_sink_last;
		sdram_tmrbankmachine4_cmd_buffer2_source_payload_we <= sdram_tmrbankmachine4_cmd_buffer2_sink_payload_we;
		sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr <= sdram_tmrbankmachine4_cmd_buffer2_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_we & sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_writable) & (~sdram_tmrbankmachine4_cmd_buffer_lookahead3_replace))) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead3_produce <= (sdram_tmrbankmachine4_cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead3_do_read) begin
		sdram_tmrbankmachine4_cmd_buffer_lookahead3_consume <= (sdram_tmrbankmachine4_cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_we & sdram_tmrbankmachine4_cmd_buffer_lookahead3_syncfifo4_writable) & (~sdram_tmrbankmachine4_cmd_buffer_lookahead3_replace))) begin
		if ((~sdram_tmrbankmachine4_cmd_buffer_lookahead3_do_read)) begin
			sdram_tmrbankmachine4_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine4_cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine4_cmd_buffer_lookahead3_do_read) begin
			sdram_tmrbankmachine4_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine4_cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine4_cmd_buffer3_source_valid) | sdram_tmrbankmachine4_cmd_buffer3_source_ready)) begin
		sdram_tmrbankmachine4_cmd_buffer3_source_valid <= sdram_tmrbankmachine4_cmd_buffer3_sink_valid;
		sdram_tmrbankmachine4_cmd_buffer3_source_first <= sdram_tmrbankmachine4_cmd_buffer3_sink_first;
		sdram_tmrbankmachine4_cmd_buffer3_source_last <= sdram_tmrbankmachine4_cmd_buffer3_sink_last;
		sdram_tmrbankmachine4_cmd_buffer3_source_payload_we <= sdram_tmrbankmachine4_cmd_buffer3_sink_payload_we;
		sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr <= sdram_tmrbankmachine4_cmd_buffer3_sink_payload_addr;
	end
	if (sdram_tmrbankmachine4_twtpcon_valid) begin
		sdram_tmrbankmachine4_twtpcon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine4_twtpcon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_twtpcon_ready)) begin
			sdram_tmrbankmachine4_twtpcon_count <= (sdram_tmrbankmachine4_twtpcon_count - 1'd1);
			if ((sdram_tmrbankmachine4_twtpcon_count == 1'd1)) begin
				sdram_tmrbankmachine4_twtpcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine4_twtpcon2_valid) begin
		sdram_tmrbankmachine4_twtpcon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine4_twtpcon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_twtpcon2_ready)) begin
			sdram_tmrbankmachine4_twtpcon2_count <= (sdram_tmrbankmachine4_twtpcon2_count - 1'd1);
			if ((sdram_tmrbankmachine4_twtpcon2_count == 1'd1)) begin
				sdram_tmrbankmachine4_twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine4_twtpcon3_valid) begin
		sdram_tmrbankmachine4_twtpcon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine4_twtpcon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_twtpcon3_ready)) begin
			sdram_tmrbankmachine4_twtpcon3_count <= (sdram_tmrbankmachine4_twtpcon3_count - 1'd1);
			if ((sdram_tmrbankmachine4_twtpcon3_count == 1'd1)) begin
				sdram_tmrbankmachine4_twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine4_trccon_valid) begin
		sdram_tmrbankmachine4_trccon_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine4_trccon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_trccon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_trccon_ready)) begin
			sdram_tmrbankmachine4_trccon_count <= (sdram_tmrbankmachine4_trccon_count - 1'd1);
			if ((sdram_tmrbankmachine4_trccon_count == 1'd1)) begin
				sdram_tmrbankmachine4_trccon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine4_trccon2_valid) begin
		sdram_tmrbankmachine4_trccon2_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine4_trccon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_trccon2_ready)) begin
			sdram_tmrbankmachine4_trccon2_count <= (sdram_tmrbankmachine4_trccon2_count - 1'd1);
			if ((sdram_tmrbankmachine4_trccon2_count == 1'd1)) begin
				sdram_tmrbankmachine4_trccon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine4_trccon3_valid) begin
		sdram_tmrbankmachine4_trccon3_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine4_trccon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_trccon3_ready)) begin
			sdram_tmrbankmachine4_trccon3_count <= (sdram_tmrbankmachine4_trccon3_count - 1'd1);
			if ((sdram_tmrbankmachine4_trccon3_count == 1'd1)) begin
				sdram_tmrbankmachine4_trccon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine4_trascon_valid) begin
		sdram_tmrbankmachine4_trascon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine4_trascon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_trascon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_trascon_ready)) begin
			sdram_tmrbankmachine4_trascon_count <= (sdram_tmrbankmachine4_trascon_count - 1'd1);
			if ((sdram_tmrbankmachine4_trascon_count == 1'd1)) begin
				sdram_tmrbankmachine4_trascon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine4_trascon2_valid) begin
		sdram_tmrbankmachine4_trascon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine4_trascon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_trascon2_ready)) begin
			sdram_tmrbankmachine4_trascon2_count <= (sdram_tmrbankmachine4_trascon2_count - 1'd1);
			if ((sdram_tmrbankmachine4_trascon2_count == 1'd1)) begin
				sdram_tmrbankmachine4_trascon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine4_trascon3_valid) begin
		sdram_tmrbankmachine4_trascon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine4_trascon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine4_trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine4_trascon3_ready)) begin
			sdram_tmrbankmachine4_trascon3_count <= (sdram_tmrbankmachine4_trascon3_count - 1'd1);
			if ((sdram_tmrbankmachine4_trascon3_count == 1'd1)) begin
				sdram_tmrbankmachine4_trascon3_ready <= 1'd1;
			end
		end
	end
	tmrbankmachine4_state <= tmrbankmachine4_next_state;
	if (sdram_tmrbankmachine5_row_close) begin
		sdram_tmrbankmachine5_row_opened <= 1'd0;
	end else begin
		if (sdram_tmrbankmachine5_row_open) begin
			sdram_tmrbankmachine5_row_opened <= 1'd1;
			sdram_tmrbankmachine5_row <= sdram_tmrbankmachine5_cmd_buffer_source_payload_addr[20:7];
		end
	end
	if (((sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_we & sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_writable) & (~sdram_tmrbankmachine5_cmd_buffer_lookahead_replace))) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead_produce <= (sdram_tmrbankmachine5_cmd_buffer_lookahead_produce + 1'd1);
	end
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead_do_read) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead_consume <= (sdram_tmrbankmachine5_cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_we & sdram_tmrbankmachine5_cmd_buffer_lookahead_syncfifo5_writable) & (~sdram_tmrbankmachine5_cmd_buffer_lookahead_replace))) begin
		if ((~sdram_tmrbankmachine5_cmd_buffer_lookahead_do_read)) begin
			sdram_tmrbankmachine5_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine5_cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine5_cmd_buffer_lookahead_do_read) begin
			sdram_tmrbankmachine5_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine5_cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine5_cmd_buffer_source_valid) | sdram_tmrbankmachine5_cmd_buffer_source_ready)) begin
		sdram_tmrbankmachine5_cmd_buffer_source_valid <= sdram_tmrbankmachine5_cmd_buffer_sink_valid;
		sdram_tmrbankmachine5_cmd_buffer_source_first <= sdram_tmrbankmachine5_cmd_buffer_sink_first;
		sdram_tmrbankmachine5_cmd_buffer_source_last <= sdram_tmrbankmachine5_cmd_buffer_sink_last;
		sdram_tmrbankmachine5_cmd_buffer_source_payload_we <= sdram_tmrbankmachine5_cmd_buffer_sink_payload_we;
		sdram_tmrbankmachine5_cmd_buffer_source_payload_addr <= sdram_tmrbankmachine5_cmd_buffer_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_we & sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_writable) & (~sdram_tmrbankmachine5_cmd_buffer_lookahead2_replace))) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead2_produce <= (sdram_tmrbankmachine5_cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead2_do_read) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead2_consume <= (sdram_tmrbankmachine5_cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_we & sdram_tmrbankmachine5_cmd_buffer_lookahead2_syncfifo5_writable) & (~sdram_tmrbankmachine5_cmd_buffer_lookahead2_replace))) begin
		if ((~sdram_tmrbankmachine5_cmd_buffer_lookahead2_do_read)) begin
			sdram_tmrbankmachine5_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine5_cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine5_cmd_buffer_lookahead2_do_read) begin
			sdram_tmrbankmachine5_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine5_cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine5_cmd_buffer2_source_valid) | sdram_tmrbankmachine5_cmd_buffer2_source_ready)) begin
		sdram_tmrbankmachine5_cmd_buffer2_source_valid <= sdram_tmrbankmachine5_cmd_buffer2_sink_valid;
		sdram_tmrbankmachine5_cmd_buffer2_source_first <= sdram_tmrbankmachine5_cmd_buffer2_sink_first;
		sdram_tmrbankmachine5_cmd_buffer2_source_last <= sdram_tmrbankmachine5_cmd_buffer2_sink_last;
		sdram_tmrbankmachine5_cmd_buffer2_source_payload_we <= sdram_tmrbankmachine5_cmd_buffer2_sink_payload_we;
		sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr <= sdram_tmrbankmachine5_cmd_buffer2_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_we & sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_writable) & (~sdram_tmrbankmachine5_cmd_buffer_lookahead3_replace))) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead3_produce <= (sdram_tmrbankmachine5_cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead3_do_read) begin
		sdram_tmrbankmachine5_cmd_buffer_lookahead3_consume <= (sdram_tmrbankmachine5_cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_we & sdram_tmrbankmachine5_cmd_buffer_lookahead3_syncfifo5_writable) & (~sdram_tmrbankmachine5_cmd_buffer_lookahead3_replace))) begin
		if ((~sdram_tmrbankmachine5_cmd_buffer_lookahead3_do_read)) begin
			sdram_tmrbankmachine5_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine5_cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine5_cmd_buffer_lookahead3_do_read) begin
			sdram_tmrbankmachine5_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine5_cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine5_cmd_buffer3_source_valid) | sdram_tmrbankmachine5_cmd_buffer3_source_ready)) begin
		sdram_tmrbankmachine5_cmd_buffer3_source_valid <= sdram_tmrbankmachine5_cmd_buffer3_sink_valid;
		sdram_tmrbankmachine5_cmd_buffer3_source_first <= sdram_tmrbankmachine5_cmd_buffer3_sink_first;
		sdram_tmrbankmachine5_cmd_buffer3_source_last <= sdram_tmrbankmachine5_cmd_buffer3_sink_last;
		sdram_tmrbankmachine5_cmd_buffer3_source_payload_we <= sdram_tmrbankmachine5_cmd_buffer3_sink_payload_we;
		sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr <= sdram_tmrbankmachine5_cmd_buffer3_sink_payload_addr;
	end
	if (sdram_tmrbankmachine5_twtpcon_valid) begin
		sdram_tmrbankmachine5_twtpcon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine5_twtpcon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_twtpcon_ready)) begin
			sdram_tmrbankmachine5_twtpcon_count <= (sdram_tmrbankmachine5_twtpcon_count - 1'd1);
			if ((sdram_tmrbankmachine5_twtpcon_count == 1'd1)) begin
				sdram_tmrbankmachine5_twtpcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine5_twtpcon2_valid) begin
		sdram_tmrbankmachine5_twtpcon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine5_twtpcon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_twtpcon2_ready)) begin
			sdram_tmrbankmachine5_twtpcon2_count <= (sdram_tmrbankmachine5_twtpcon2_count - 1'd1);
			if ((sdram_tmrbankmachine5_twtpcon2_count == 1'd1)) begin
				sdram_tmrbankmachine5_twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine5_twtpcon3_valid) begin
		sdram_tmrbankmachine5_twtpcon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine5_twtpcon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_twtpcon3_ready)) begin
			sdram_tmrbankmachine5_twtpcon3_count <= (sdram_tmrbankmachine5_twtpcon3_count - 1'd1);
			if ((sdram_tmrbankmachine5_twtpcon3_count == 1'd1)) begin
				sdram_tmrbankmachine5_twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine5_trccon_valid) begin
		sdram_tmrbankmachine5_trccon_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine5_trccon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_trccon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_trccon_ready)) begin
			sdram_tmrbankmachine5_trccon_count <= (sdram_tmrbankmachine5_trccon_count - 1'd1);
			if ((sdram_tmrbankmachine5_trccon_count == 1'd1)) begin
				sdram_tmrbankmachine5_trccon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine5_trccon2_valid) begin
		sdram_tmrbankmachine5_trccon2_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine5_trccon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_trccon2_ready)) begin
			sdram_tmrbankmachine5_trccon2_count <= (sdram_tmrbankmachine5_trccon2_count - 1'd1);
			if ((sdram_tmrbankmachine5_trccon2_count == 1'd1)) begin
				sdram_tmrbankmachine5_trccon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine5_trccon3_valid) begin
		sdram_tmrbankmachine5_trccon3_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine5_trccon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_trccon3_ready)) begin
			sdram_tmrbankmachine5_trccon3_count <= (sdram_tmrbankmachine5_trccon3_count - 1'd1);
			if ((sdram_tmrbankmachine5_trccon3_count == 1'd1)) begin
				sdram_tmrbankmachine5_trccon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine5_trascon_valid) begin
		sdram_tmrbankmachine5_trascon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine5_trascon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_trascon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_trascon_ready)) begin
			sdram_tmrbankmachine5_trascon_count <= (sdram_tmrbankmachine5_trascon_count - 1'd1);
			if ((sdram_tmrbankmachine5_trascon_count == 1'd1)) begin
				sdram_tmrbankmachine5_trascon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine5_trascon2_valid) begin
		sdram_tmrbankmachine5_trascon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine5_trascon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_trascon2_ready)) begin
			sdram_tmrbankmachine5_trascon2_count <= (sdram_tmrbankmachine5_trascon2_count - 1'd1);
			if ((sdram_tmrbankmachine5_trascon2_count == 1'd1)) begin
				sdram_tmrbankmachine5_trascon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine5_trascon3_valid) begin
		sdram_tmrbankmachine5_trascon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine5_trascon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine5_trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine5_trascon3_ready)) begin
			sdram_tmrbankmachine5_trascon3_count <= (sdram_tmrbankmachine5_trascon3_count - 1'd1);
			if ((sdram_tmrbankmachine5_trascon3_count == 1'd1)) begin
				sdram_tmrbankmachine5_trascon3_ready <= 1'd1;
			end
		end
	end
	tmrbankmachine5_state <= tmrbankmachine5_next_state;
	if (sdram_tmrbankmachine6_row_close) begin
		sdram_tmrbankmachine6_row_opened <= 1'd0;
	end else begin
		if (sdram_tmrbankmachine6_row_open) begin
			sdram_tmrbankmachine6_row_opened <= 1'd1;
			sdram_tmrbankmachine6_row <= sdram_tmrbankmachine6_cmd_buffer_source_payload_addr[20:7];
		end
	end
	if (((sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_we & sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_writable) & (~sdram_tmrbankmachine6_cmd_buffer_lookahead_replace))) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead_produce <= (sdram_tmrbankmachine6_cmd_buffer_lookahead_produce + 1'd1);
	end
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead_do_read) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead_consume <= (sdram_tmrbankmachine6_cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_we & sdram_tmrbankmachine6_cmd_buffer_lookahead_syncfifo6_writable) & (~sdram_tmrbankmachine6_cmd_buffer_lookahead_replace))) begin
		if ((~sdram_tmrbankmachine6_cmd_buffer_lookahead_do_read)) begin
			sdram_tmrbankmachine6_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine6_cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine6_cmd_buffer_lookahead_do_read) begin
			sdram_tmrbankmachine6_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine6_cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine6_cmd_buffer_source_valid) | sdram_tmrbankmachine6_cmd_buffer_source_ready)) begin
		sdram_tmrbankmachine6_cmd_buffer_source_valid <= sdram_tmrbankmachine6_cmd_buffer_sink_valid;
		sdram_tmrbankmachine6_cmd_buffer_source_first <= sdram_tmrbankmachine6_cmd_buffer_sink_first;
		sdram_tmrbankmachine6_cmd_buffer_source_last <= sdram_tmrbankmachine6_cmd_buffer_sink_last;
		sdram_tmrbankmachine6_cmd_buffer_source_payload_we <= sdram_tmrbankmachine6_cmd_buffer_sink_payload_we;
		sdram_tmrbankmachine6_cmd_buffer_source_payload_addr <= sdram_tmrbankmachine6_cmd_buffer_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_we & sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_writable) & (~sdram_tmrbankmachine6_cmd_buffer_lookahead2_replace))) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead2_produce <= (sdram_tmrbankmachine6_cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead2_do_read) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead2_consume <= (sdram_tmrbankmachine6_cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_we & sdram_tmrbankmachine6_cmd_buffer_lookahead2_syncfifo6_writable) & (~sdram_tmrbankmachine6_cmd_buffer_lookahead2_replace))) begin
		if ((~sdram_tmrbankmachine6_cmd_buffer_lookahead2_do_read)) begin
			sdram_tmrbankmachine6_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine6_cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine6_cmd_buffer_lookahead2_do_read) begin
			sdram_tmrbankmachine6_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine6_cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine6_cmd_buffer2_source_valid) | sdram_tmrbankmachine6_cmd_buffer2_source_ready)) begin
		sdram_tmrbankmachine6_cmd_buffer2_source_valid <= sdram_tmrbankmachine6_cmd_buffer2_sink_valid;
		sdram_tmrbankmachine6_cmd_buffer2_source_first <= sdram_tmrbankmachine6_cmd_buffer2_sink_first;
		sdram_tmrbankmachine6_cmd_buffer2_source_last <= sdram_tmrbankmachine6_cmd_buffer2_sink_last;
		sdram_tmrbankmachine6_cmd_buffer2_source_payload_we <= sdram_tmrbankmachine6_cmd_buffer2_sink_payload_we;
		sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr <= sdram_tmrbankmachine6_cmd_buffer2_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_we & sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_writable) & (~sdram_tmrbankmachine6_cmd_buffer_lookahead3_replace))) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead3_produce <= (sdram_tmrbankmachine6_cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead3_do_read) begin
		sdram_tmrbankmachine6_cmd_buffer_lookahead3_consume <= (sdram_tmrbankmachine6_cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_we & sdram_tmrbankmachine6_cmd_buffer_lookahead3_syncfifo6_writable) & (~sdram_tmrbankmachine6_cmd_buffer_lookahead3_replace))) begin
		if ((~sdram_tmrbankmachine6_cmd_buffer_lookahead3_do_read)) begin
			sdram_tmrbankmachine6_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine6_cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine6_cmd_buffer_lookahead3_do_read) begin
			sdram_tmrbankmachine6_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine6_cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine6_cmd_buffer3_source_valid) | sdram_tmrbankmachine6_cmd_buffer3_source_ready)) begin
		sdram_tmrbankmachine6_cmd_buffer3_source_valid <= sdram_tmrbankmachine6_cmd_buffer3_sink_valid;
		sdram_tmrbankmachine6_cmd_buffer3_source_first <= sdram_tmrbankmachine6_cmd_buffer3_sink_first;
		sdram_tmrbankmachine6_cmd_buffer3_source_last <= sdram_tmrbankmachine6_cmd_buffer3_sink_last;
		sdram_tmrbankmachine6_cmd_buffer3_source_payload_we <= sdram_tmrbankmachine6_cmd_buffer3_sink_payload_we;
		sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr <= sdram_tmrbankmachine6_cmd_buffer3_sink_payload_addr;
	end
	if (sdram_tmrbankmachine6_twtpcon_valid) begin
		sdram_tmrbankmachine6_twtpcon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine6_twtpcon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_twtpcon_ready)) begin
			sdram_tmrbankmachine6_twtpcon_count <= (sdram_tmrbankmachine6_twtpcon_count - 1'd1);
			if ((sdram_tmrbankmachine6_twtpcon_count == 1'd1)) begin
				sdram_tmrbankmachine6_twtpcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine6_twtpcon2_valid) begin
		sdram_tmrbankmachine6_twtpcon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine6_twtpcon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_twtpcon2_ready)) begin
			sdram_tmrbankmachine6_twtpcon2_count <= (sdram_tmrbankmachine6_twtpcon2_count - 1'd1);
			if ((sdram_tmrbankmachine6_twtpcon2_count == 1'd1)) begin
				sdram_tmrbankmachine6_twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine6_twtpcon3_valid) begin
		sdram_tmrbankmachine6_twtpcon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine6_twtpcon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_twtpcon3_ready)) begin
			sdram_tmrbankmachine6_twtpcon3_count <= (sdram_tmrbankmachine6_twtpcon3_count - 1'd1);
			if ((sdram_tmrbankmachine6_twtpcon3_count == 1'd1)) begin
				sdram_tmrbankmachine6_twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine6_trccon_valid) begin
		sdram_tmrbankmachine6_trccon_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine6_trccon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_trccon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_trccon_ready)) begin
			sdram_tmrbankmachine6_trccon_count <= (sdram_tmrbankmachine6_trccon_count - 1'd1);
			if ((sdram_tmrbankmachine6_trccon_count == 1'd1)) begin
				sdram_tmrbankmachine6_trccon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine6_trccon2_valid) begin
		sdram_tmrbankmachine6_trccon2_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine6_trccon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_trccon2_ready)) begin
			sdram_tmrbankmachine6_trccon2_count <= (sdram_tmrbankmachine6_trccon2_count - 1'd1);
			if ((sdram_tmrbankmachine6_trccon2_count == 1'd1)) begin
				sdram_tmrbankmachine6_trccon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine6_trccon3_valid) begin
		sdram_tmrbankmachine6_trccon3_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine6_trccon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_trccon3_ready)) begin
			sdram_tmrbankmachine6_trccon3_count <= (sdram_tmrbankmachine6_trccon3_count - 1'd1);
			if ((sdram_tmrbankmachine6_trccon3_count == 1'd1)) begin
				sdram_tmrbankmachine6_trccon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine6_trascon_valid) begin
		sdram_tmrbankmachine6_trascon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine6_trascon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_trascon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_trascon_ready)) begin
			sdram_tmrbankmachine6_trascon_count <= (sdram_tmrbankmachine6_trascon_count - 1'd1);
			if ((sdram_tmrbankmachine6_trascon_count == 1'd1)) begin
				sdram_tmrbankmachine6_trascon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine6_trascon2_valid) begin
		sdram_tmrbankmachine6_trascon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine6_trascon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_trascon2_ready)) begin
			sdram_tmrbankmachine6_trascon2_count <= (sdram_tmrbankmachine6_trascon2_count - 1'd1);
			if ((sdram_tmrbankmachine6_trascon2_count == 1'd1)) begin
				sdram_tmrbankmachine6_trascon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine6_trascon3_valid) begin
		sdram_tmrbankmachine6_trascon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine6_trascon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine6_trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine6_trascon3_ready)) begin
			sdram_tmrbankmachine6_trascon3_count <= (sdram_tmrbankmachine6_trascon3_count - 1'd1);
			if ((sdram_tmrbankmachine6_trascon3_count == 1'd1)) begin
				sdram_tmrbankmachine6_trascon3_ready <= 1'd1;
			end
		end
	end
	tmrbankmachine6_state <= tmrbankmachine6_next_state;
	if (sdram_tmrbankmachine7_row_close) begin
		sdram_tmrbankmachine7_row_opened <= 1'd0;
	end else begin
		if (sdram_tmrbankmachine7_row_open) begin
			sdram_tmrbankmachine7_row_opened <= 1'd1;
			sdram_tmrbankmachine7_row <= sdram_tmrbankmachine7_cmd_buffer_source_payload_addr[20:7];
		end
	end
	if (((sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_we & sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_writable) & (~sdram_tmrbankmachine7_cmd_buffer_lookahead_replace))) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead_produce <= (sdram_tmrbankmachine7_cmd_buffer_lookahead_produce + 1'd1);
	end
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead_do_read) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead_consume <= (sdram_tmrbankmachine7_cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_we & sdram_tmrbankmachine7_cmd_buffer_lookahead_syncfifo7_writable) & (~sdram_tmrbankmachine7_cmd_buffer_lookahead_replace))) begin
		if ((~sdram_tmrbankmachine7_cmd_buffer_lookahead_do_read)) begin
			sdram_tmrbankmachine7_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine7_cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine7_cmd_buffer_lookahead_do_read) begin
			sdram_tmrbankmachine7_cmd_buffer_lookahead_level <= (sdram_tmrbankmachine7_cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine7_cmd_buffer_source_valid) | sdram_tmrbankmachine7_cmd_buffer_source_ready)) begin
		sdram_tmrbankmachine7_cmd_buffer_source_valid <= sdram_tmrbankmachine7_cmd_buffer_sink_valid;
		sdram_tmrbankmachine7_cmd_buffer_source_first <= sdram_tmrbankmachine7_cmd_buffer_sink_first;
		sdram_tmrbankmachine7_cmd_buffer_source_last <= sdram_tmrbankmachine7_cmd_buffer_sink_last;
		sdram_tmrbankmachine7_cmd_buffer_source_payload_we <= sdram_tmrbankmachine7_cmd_buffer_sink_payload_we;
		sdram_tmrbankmachine7_cmd_buffer_source_payload_addr <= sdram_tmrbankmachine7_cmd_buffer_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_we & sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_writable) & (~sdram_tmrbankmachine7_cmd_buffer_lookahead2_replace))) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead2_produce <= (sdram_tmrbankmachine7_cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead2_do_read) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead2_consume <= (sdram_tmrbankmachine7_cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_we & sdram_tmrbankmachine7_cmd_buffer_lookahead2_syncfifo7_writable) & (~sdram_tmrbankmachine7_cmd_buffer_lookahead2_replace))) begin
		if ((~sdram_tmrbankmachine7_cmd_buffer_lookahead2_do_read)) begin
			sdram_tmrbankmachine7_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine7_cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine7_cmd_buffer_lookahead2_do_read) begin
			sdram_tmrbankmachine7_cmd_buffer_lookahead2_level <= (sdram_tmrbankmachine7_cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine7_cmd_buffer2_source_valid) | sdram_tmrbankmachine7_cmd_buffer2_source_ready)) begin
		sdram_tmrbankmachine7_cmd_buffer2_source_valid <= sdram_tmrbankmachine7_cmd_buffer2_sink_valid;
		sdram_tmrbankmachine7_cmd_buffer2_source_first <= sdram_tmrbankmachine7_cmd_buffer2_sink_first;
		sdram_tmrbankmachine7_cmd_buffer2_source_last <= sdram_tmrbankmachine7_cmd_buffer2_sink_last;
		sdram_tmrbankmachine7_cmd_buffer2_source_payload_we <= sdram_tmrbankmachine7_cmd_buffer2_sink_payload_we;
		sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr <= sdram_tmrbankmachine7_cmd_buffer2_sink_payload_addr;
	end
	if (((sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_we & sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_writable) & (~sdram_tmrbankmachine7_cmd_buffer_lookahead3_replace))) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead3_produce <= (sdram_tmrbankmachine7_cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead3_do_read) begin
		sdram_tmrbankmachine7_cmd_buffer_lookahead3_consume <= (sdram_tmrbankmachine7_cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_we & sdram_tmrbankmachine7_cmd_buffer_lookahead3_syncfifo7_writable) & (~sdram_tmrbankmachine7_cmd_buffer_lookahead3_replace))) begin
		if ((~sdram_tmrbankmachine7_cmd_buffer_lookahead3_do_read)) begin
			sdram_tmrbankmachine7_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine7_cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (sdram_tmrbankmachine7_cmd_buffer_lookahead3_do_read) begin
			sdram_tmrbankmachine7_cmd_buffer_lookahead3_level <= (sdram_tmrbankmachine7_cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~sdram_tmrbankmachine7_cmd_buffer3_source_valid) | sdram_tmrbankmachine7_cmd_buffer3_source_ready)) begin
		sdram_tmrbankmachine7_cmd_buffer3_source_valid <= sdram_tmrbankmachine7_cmd_buffer3_sink_valid;
		sdram_tmrbankmachine7_cmd_buffer3_source_first <= sdram_tmrbankmachine7_cmd_buffer3_sink_first;
		sdram_tmrbankmachine7_cmd_buffer3_source_last <= sdram_tmrbankmachine7_cmd_buffer3_sink_last;
		sdram_tmrbankmachine7_cmd_buffer3_source_payload_we <= sdram_tmrbankmachine7_cmd_buffer3_sink_payload_we;
		sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr <= sdram_tmrbankmachine7_cmd_buffer3_sink_payload_addr;
	end
	if (sdram_tmrbankmachine7_twtpcon_valid) begin
		sdram_tmrbankmachine7_twtpcon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine7_twtpcon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_twtpcon_ready)) begin
			sdram_tmrbankmachine7_twtpcon_count <= (sdram_tmrbankmachine7_twtpcon_count - 1'd1);
			if ((sdram_tmrbankmachine7_twtpcon_count == 1'd1)) begin
				sdram_tmrbankmachine7_twtpcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine7_twtpcon2_valid) begin
		sdram_tmrbankmachine7_twtpcon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine7_twtpcon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_twtpcon2_ready)) begin
			sdram_tmrbankmachine7_twtpcon2_count <= (sdram_tmrbankmachine7_twtpcon2_count - 1'd1);
			if ((sdram_tmrbankmachine7_twtpcon2_count == 1'd1)) begin
				sdram_tmrbankmachine7_twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine7_twtpcon3_valid) begin
		sdram_tmrbankmachine7_twtpcon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine7_twtpcon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_twtpcon3_ready)) begin
			sdram_tmrbankmachine7_twtpcon3_count <= (sdram_tmrbankmachine7_twtpcon3_count - 1'd1);
			if ((sdram_tmrbankmachine7_twtpcon3_count == 1'd1)) begin
				sdram_tmrbankmachine7_twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine7_trccon_valid) begin
		sdram_tmrbankmachine7_trccon_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine7_trccon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_trccon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_trccon_ready)) begin
			sdram_tmrbankmachine7_trccon_count <= (sdram_tmrbankmachine7_trccon_count - 1'd1);
			if ((sdram_tmrbankmachine7_trccon_count == 1'd1)) begin
				sdram_tmrbankmachine7_trccon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine7_trccon2_valid) begin
		sdram_tmrbankmachine7_trccon2_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine7_trccon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_trccon2_ready)) begin
			sdram_tmrbankmachine7_trccon2_count <= (sdram_tmrbankmachine7_trccon2_count - 1'd1);
			if ((sdram_tmrbankmachine7_trccon2_count == 1'd1)) begin
				sdram_tmrbankmachine7_trccon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine7_trccon3_valid) begin
		sdram_tmrbankmachine7_trccon3_count <= 3'd6;
		if (1'd0) begin
			sdram_tmrbankmachine7_trccon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_trccon3_ready)) begin
			sdram_tmrbankmachine7_trccon3_count <= (sdram_tmrbankmachine7_trccon3_count - 1'd1);
			if ((sdram_tmrbankmachine7_trccon3_count == 1'd1)) begin
				sdram_tmrbankmachine7_trccon3_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine7_trascon_valid) begin
		sdram_tmrbankmachine7_trascon_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine7_trascon_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_trascon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_trascon_ready)) begin
			sdram_tmrbankmachine7_trascon_count <= (sdram_tmrbankmachine7_trascon_count - 1'd1);
			if ((sdram_tmrbankmachine7_trascon_count == 1'd1)) begin
				sdram_tmrbankmachine7_trascon_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine7_trascon2_valid) begin
		sdram_tmrbankmachine7_trascon2_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine7_trascon2_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_trascon2_ready)) begin
			sdram_tmrbankmachine7_trascon2_count <= (sdram_tmrbankmachine7_trascon2_count - 1'd1);
			if ((sdram_tmrbankmachine7_trascon2_count == 1'd1)) begin
				sdram_tmrbankmachine7_trascon2_ready <= 1'd1;
			end
		end
	end
	if (sdram_tmrbankmachine7_trascon3_valid) begin
		sdram_tmrbankmachine7_trascon3_count <= 3'd5;
		if (1'd0) begin
			sdram_tmrbankmachine7_trascon3_ready <= 1'd1;
		end else begin
			sdram_tmrbankmachine7_trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_tmrbankmachine7_trascon3_ready)) begin
			sdram_tmrbankmachine7_trascon3_count <= (sdram_tmrbankmachine7_trascon3_count - 1'd1);
			if ((sdram_tmrbankmachine7_trascon3_count == 1'd1)) begin
				sdram_tmrbankmachine7_trascon3_ready <= 1'd1;
			end
		end
	end
	tmrbankmachine7_state <= tmrbankmachine7_next_state;
	if ((~sdram_multiplexer_en0)) begin
		sdram_multiplexer_time0 <= 5'd31;
	end else begin
		if ((~sdram_multiplexer_max_time0)) begin
			sdram_multiplexer_time0 <= (sdram_multiplexer_time0 - 1'd1);
		end
	end
	if ((~sdram_multiplexer_en1)) begin
		sdram_multiplexer_time1 <= 4'd15;
	end else begin
		if ((~sdram_multiplexer_max_time1)) begin
			sdram_multiplexer_time1 <= (sdram_multiplexer_time1 - 1'd1);
		end
	end
	if (sdram_multiplexer_choose_cmd_ce) begin
		case (sdram_multiplexer_choose_cmd_grant)
			1'd0: begin
				if (sdram_multiplexer_choose_cmd_request[1]) begin
					sdram_multiplexer_choose_cmd_grant <= 1'd1;
				end else begin
					if (sdram_multiplexer_choose_cmd_request[2]) begin
						sdram_multiplexer_choose_cmd_grant <= 2'd2;
					end else begin
						if (sdram_multiplexer_choose_cmd_request[3]) begin
							sdram_multiplexer_choose_cmd_grant <= 2'd3;
						end else begin
							if (sdram_multiplexer_choose_cmd_request[4]) begin
								sdram_multiplexer_choose_cmd_grant <= 3'd4;
							end else begin
								if (sdram_multiplexer_choose_cmd_request[5]) begin
									sdram_multiplexer_choose_cmd_grant <= 3'd5;
								end else begin
									if (sdram_multiplexer_choose_cmd_request[6]) begin
										sdram_multiplexer_choose_cmd_grant <= 3'd6;
									end else begin
										if (sdram_multiplexer_choose_cmd_request[7]) begin
											sdram_multiplexer_choose_cmd_grant <= 3'd7;
										end
									end
								end
							end
						end
					end
				end
			end
			1'd1: begin
				if (sdram_multiplexer_choose_cmd_request[2]) begin
					sdram_multiplexer_choose_cmd_grant <= 2'd2;
				end else begin
					if (sdram_multiplexer_choose_cmd_request[3]) begin
						sdram_multiplexer_choose_cmd_grant <= 2'd3;
					end else begin
						if (sdram_multiplexer_choose_cmd_request[4]) begin
							sdram_multiplexer_choose_cmd_grant <= 3'd4;
						end else begin
							if (sdram_multiplexer_choose_cmd_request[5]) begin
								sdram_multiplexer_choose_cmd_grant <= 3'd5;
							end else begin
								if (sdram_multiplexer_choose_cmd_request[6]) begin
									sdram_multiplexer_choose_cmd_grant <= 3'd6;
								end else begin
									if (sdram_multiplexer_choose_cmd_request[7]) begin
										sdram_multiplexer_choose_cmd_grant <= 3'd7;
									end else begin
										if (sdram_multiplexer_choose_cmd_request[0]) begin
											sdram_multiplexer_choose_cmd_grant <= 1'd0;
										end
									end
								end
							end
						end
					end
				end
			end
			2'd2: begin
				if (sdram_multiplexer_choose_cmd_request[3]) begin
					sdram_multiplexer_choose_cmd_grant <= 2'd3;
				end else begin
					if (sdram_multiplexer_choose_cmd_request[4]) begin
						sdram_multiplexer_choose_cmd_grant <= 3'd4;
					end else begin
						if (sdram_multiplexer_choose_cmd_request[5]) begin
							sdram_multiplexer_choose_cmd_grant <= 3'd5;
						end else begin
							if (sdram_multiplexer_choose_cmd_request[6]) begin
								sdram_multiplexer_choose_cmd_grant <= 3'd6;
							end else begin
								if (sdram_multiplexer_choose_cmd_request[7]) begin
									sdram_multiplexer_choose_cmd_grant <= 3'd7;
								end else begin
									if (sdram_multiplexer_choose_cmd_request[0]) begin
										sdram_multiplexer_choose_cmd_grant <= 1'd0;
									end else begin
										if (sdram_multiplexer_choose_cmd_request[1]) begin
											sdram_multiplexer_choose_cmd_grant <= 1'd1;
										end
									end
								end
							end
						end
					end
				end
			end
			2'd3: begin
				if (sdram_multiplexer_choose_cmd_request[4]) begin
					sdram_multiplexer_choose_cmd_grant <= 3'd4;
				end else begin
					if (sdram_multiplexer_choose_cmd_request[5]) begin
						sdram_multiplexer_choose_cmd_grant <= 3'd5;
					end else begin
						if (sdram_multiplexer_choose_cmd_request[6]) begin
							sdram_multiplexer_choose_cmd_grant <= 3'd6;
						end else begin
							if (sdram_multiplexer_choose_cmd_request[7]) begin
								sdram_multiplexer_choose_cmd_grant <= 3'd7;
							end else begin
								if (sdram_multiplexer_choose_cmd_request[0]) begin
									sdram_multiplexer_choose_cmd_grant <= 1'd0;
								end else begin
									if (sdram_multiplexer_choose_cmd_request[1]) begin
										sdram_multiplexer_choose_cmd_grant <= 1'd1;
									end else begin
										if (sdram_multiplexer_choose_cmd_request[2]) begin
											sdram_multiplexer_choose_cmd_grant <= 2'd2;
										end
									end
								end
							end
						end
					end
				end
			end
			3'd4: begin
				if (sdram_multiplexer_choose_cmd_request[5]) begin
					sdram_multiplexer_choose_cmd_grant <= 3'd5;
				end else begin
					if (sdram_multiplexer_choose_cmd_request[6]) begin
						sdram_multiplexer_choose_cmd_grant <= 3'd6;
					end else begin
						if (sdram_multiplexer_choose_cmd_request[7]) begin
							sdram_multiplexer_choose_cmd_grant <= 3'd7;
						end else begin
							if (sdram_multiplexer_choose_cmd_request[0]) begin
								sdram_multiplexer_choose_cmd_grant <= 1'd0;
							end else begin
								if (sdram_multiplexer_choose_cmd_request[1]) begin
									sdram_multiplexer_choose_cmd_grant <= 1'd1;
								end else begin
									if (sdram_multiplexer_choose_cmd_request[2]) begin
										sdram_multiplexer_choose_cmd_grant <= 2'd2;
									end else begin
										if (sdram_multiplexer_choose_cmd_request[3]) begin
											sdram_multiplexer_choose_cmd_grant <= 2'd3;
										end
									end
								end
							end
						end
					end
				end
			end
			3'd5: begin
				if (sdram_multiplexer_choose_cmd_request[6]) begin
					sdram_multiplexer_choose_cmd_grant <= 3'd6;
				end else begin
					if (sdram_multiplexer_choose_cmd_request[7]) begin
						sdram_multiplexer_choose_cmd_grant <= 3'd7;
					end else begin
						if (sdram_multiplexer_choose_cmd_request[0]) begin
							sdram_multiplexer_choose_cmd_grant <= 1'd0;
						end else begin
							if (sdram_multiplexer_choose_cmd_request[1]) begin
								sdram_multiplexer_choose_cmd_grant <= 1'd1;
							end else begin
								if (sdram_multiplexer_choose_cmd_request[2]) begin
									sdram_multiplexer_choose_cmd_grant <= 2'd2;
								end else begin
									if (sdram_multiplexer_choose_cmd_request[3]) begin
										sdram_multiplexer_choose_cmd_grant <= 2'd3;
									end else begin
										if (sdram_multiplexer_choose_cmd_request[4]) begin
											sdram_multiplexer_choose_cmd_grant <= 3'd4;
										end
									end
								end
							end
						end
					end
				end
			end
			3'd6: begin
				if (sdram_multiplexer_choose_cmd_request[7]) begin
					sdram_multiplexer_choose_cmd_grant <= 3'd7;
				end else begin
					if (sdram_multiplexer_choose_cmd_request[0]) begin
						sdram_multiplexer_choose_cmd_grant <= 1'd0;
					end else begin
						if (sdram_multiplexer_choose_cmd_request[1]) begin
							sdram_multiplexer_choose_cmd_grant <= 1'd1;
						end else begin
							if (sdram_multiplexer_choose_cmd_request[2]) begin
								sdram_multiplexer_choose_cmd_grant <= 2'd2;
							end else begin
								if (sdram_multiplexer_choose_cmd_request[3]) begin
									sdram_multiplexer_choose_cmd_grant <= 2'd3;
								end else begin
									if (sdram_multiplexer_choose_cmd_request[4]) begin
										sdram_multiplexer_choose_cmd_grant <= 3'd4;
									end else begin
										if (sdram_multiplexer_choose_cmd_request[5]) begin
											sdram_multiplexer_choose_cmd_grant <= 3'd5;
										end
									end
								end
							end
						end
					end
				end
			end
			3'd7: begin
				if (sdram_multiplexer_choose_cmd_request[0]) begin
					sdram_multiplexer_choose_cmd_grant <= 1'd0;
				end else begin
					if (sdram_multiplexer_choose_cmd_request[1]) begin
						sdram_multiplexer_choose_cmd_grant <= 1'd1;
					end else begin
						if (sdram_multiplexer_choose_cmd_request[2]) begin
							sdram_multiplexer_choose_cmd_grant <= 2'd2;
						end else begin
							if (sdram_multiplexer_choose_cmd_request[3]) begin
								sdram_multiplexer_choose_cmd_grant <= 2'd3;
							end else begin
								if (sdram_multiplexer_choose_cmd_request[4]) begin
									sdram_multiplexer_choose_cmd_grant <= 3'd4;
								end else begin
									if (sdram_multiplexer_choose_cmd_request[5]) begin
										sdram_multiplexer_choose_cmd_grant <= 3'd5;
									end else begin
										if (sdram_multiplexer_choose_cmd_request[6]) begin
											sdram_multiplexer_choose_cmd_grant <= 3'd6;
										end
									end
								end
							end
						end
					end
				end
			end
		endcase
	end
	if (sdram_multiplexer_choose_req_ce) begin
		case (sdram_multiplexer_choose_req_grant)
			1'd0: begin
				if (sdram_multiplexer_choose_req_request[1]) begin
					sdram_multiplexer_choose_req_grant <= 1'd1;
				end else begin
					if (sdram_multiplexer_choose_req_request[2]) begin
						sdram_multiplexer_choose_req_grant <= 2'd2;
					end else begin
						if (sdram_multiplexer_choose_req_request[3]) begin
							sdram_multiplexer_choose_req_grant <= 2'd3;
						end else begin
							if (sdram_multiplexer_choose_req_request[4]) begin
								sdram_multiplexer_choose_req_grant <= 3'd4;
							end else begin
								if (sdram_multiplexer_choose_req_request[5]) begin
									sdram_multiplexer_choose_req_grant <= 3'd5;
								end else begin
									if (sdram_multiplexer_choose_req_request[6]) begin
										sdram_multiplexer_choose_req_grant <= 3'd6;
									end else begin
										if (sdram_multiplexer_choose_req_request[7]) begin
											sdram_multiplexer_choose_req_grant <= 3'd7;
										end
									end
								end
							end
						end
					end
				end
			end
			1'd1: begin
				if (sdram_multiplexer_choose_req_request[2]) begin
					sdram_multiplexer_choose_req_grant <= 2'd2;
				end else begin
					if (sdram_multiplexer_choose_req_request[3]) begin
						sdram_multiplexer_choose_req_grant <= 2'd3;
					end else begin
						if (sdram_multiplexer_choose_req_request[4]) begin
							sdram_multiplexer_choose_req_grant <= 3'd4;
						end else begin
							if (sdram_multiplexer_choose_req_request[5]) begin
								sdram_multiplexer_choose_req_grant <= 3'd5;
							end else begin
								if (sdram_multiplexer_choose_req_request[6]) begin
									sdram_multiplexer_choose_req_grant <= 3'd6;
								end else begin
									if (sdram_multiplexer_choose_req_request[7]) begin
										sdram_multiplexer_choose_req_grant <= 3'd7;
									end else begin
										if (sdram_multiplexer_choose_req_request[0]) begin
											sdram_multiplexer_choose_req_grant <= 1'd0;
										end
									end
								end
							end
						end
					end
				end
			end
			2'd2: begin
				if (sdram_multiplexer_choose_req_request[3]) begin
					sdram_multiplexer_choose_req_grant <= 2'd3;
				end else begin
					if (sdram_multiplexer_choose_req_request[4]) begin
						sdram_multiplexer_choose_req_grant <= 3'd4;
					end else begin
						if (sdram_multiplexer_choose_req_request[5]) begin
							sdram_multiplexer_choose_req_grant <= 3'd5;
						end else begin
							if (sdram_multiplexer_choose_req_request[6]) begin
								sdram_multiplexer_choose_req_grant <= 3'd6;
							end else begin
								if (sdram_multiplexer_choose_req_request[7]) begin
									sdram_multiplexer_choose_req_grant <= 3'd7;
								end else begin
									if (sdram_multiplexer_choose_req_request[0]) begin
										sdram_multiplexer_choose_req_grant <= 1'd0;
									end else begin
										if (sdram_multiplexer_choose_req_request[1]) begin
											sdram_multiplexer_choose_req_grant <= 1'd1;
										end
									end
								end
							end
						end
					end
				end
			end
			2'd3: begin
				if (sdram_multiplexer_choose_req_request[4]) begin
					sdram_multiplexer_choose_req_grant <= 3'd4;
				end else begin
					if (sdram_multiplexer_choose_req_request[5]) begin
						sdram_multiplexer_choose_req_grant <= 3'd5;
					end else begin
						if (sdram_multiplexer_choose_req_request[6]) begin
							sdram_multiplexer_choose_req_grant <= 3'd6;
						end else begin
							if (sdram_multiplexer_choose_req_request[7]) begin
								sdram_multiplexer_choose_req_grant <= 3'd7;
							end else begin
								if (sdram_multiplexer_choose_req_request[0]) begin
									sdram_multiplexer_choose_req_grant <= 1'd0;
								end else begin
									if (sdram_multiplexer_choose_req_request[1]) begin
										sdram_multiplexer_choose_req_grant <= 1'd1;
									end else begin
										if (sdram_multiplexer_choose_req_request[2]) begin
											sdram_multiplexer_choose_req_grant <= 2'd2;
										end
									end
								end
							end
						end
					end
				end
			end
			3'd4: begin
				if (sdram_multiplexer_choose_req_request[5]) begin
					sdram_multiplexer_choose_req_grant <= 3'd5;
				end else begin
					if (sdram_multiplexer_choose_req_request[6]) begin
						sdram_multiplexer_choose_req_grant <= 3'd6;
					end else begin
						if (sdram_multiplexer_choose_req_request[7]) begin
							sdram_multiplexer_choose_req_grant <= 3'd7;
						end else begin
							if (sdram_multiplexer_choose_req_request[0]) begin
								sdram_multiplexer_choose_req_grant <= 1'd0;
							end else begin
								if (sdram_multiplexer_choose_req_request[1]) begin
									sdram_multiplexer_choose_req_grant <= 1'd1;
								end else begin
									if (sdram_multiplexer_choose_req_request[2]) begin
										sdram_multiplexer_choose_req_grant <= 2'd2;
									end else begin
										if (sdram_multiplexer_choose_req_request[3]) begin
											sdram_multiplexer_choose_req_grant <= 2'd3;
										end
									end
								end
							end
						end
					end
				end
			end
			3'd5: begin
				if (sdram_multiplexer_choose_req_request[6]) begin
					sdram_multiplexer_choose_req_grant <= 3'd6;
				end else begin
					if (sdram_multiplexer_choose_req_request[7]) begin
						sdram_multiplexer_choose_req_grant <= 3'd7;
					end else begin
						if (sdram_multiplexer_choose_req_request[0]) begin
							sdram_multiplexer_choose_req_grant <= 1'd0;
						end else begin
							if (sdram_multiplexer_choose_req_request[1]) begin
								sdram_multiplexer_choose_req_grant <= 1'd1;
							end else begin
								if (sdram_multiplexer_choose_req_request[2]) begin
									sdram_multiplexer_choose_req_grant <= 2'd2;
								end else begin
									if (sdram_multiplexer_choose_req_request[3]) begin
										sdram_multiplexer_choose_req_grant <= 2'd3;
									end else begin
										if (sdram_multiplexer_choose_req_request[4]) begin
											sdram_multiplexer_choose_req_grant <= 3'd4;
										end
									end
								end
							end
						end
					end
				end
			end
			3'd6: begin
				if (sdram_multiplexer_choose_req_request[7]) begin
					sdram_multiplexer_choose_req_grant <= 3'd7;
				end else begin
					if (sdram_multiplexer_choose_req_request[0]) begin
						sdram_multiplexer_choose_req_grant <= 1'd0;
					end else begin
						if (sdram_multiplexer_choose_req_request[1]) begin
							sdram_multiplexer_choose_req_grant <= 1'd1;
						end else begin
							if (sdram_multiplexer_choose_req_request[2]) begin
								sdram_multiplexer_choose_req_grant <= 2'd2;
							end else begin
								if (sdram_multiplexer_choose_req_request[3]) begin
									sdram_multiplexer_choose_req_grant <= 2'd3;
								end else begin
									if (sdram_multiplexer_choose_req_request[4]) begin
										sdram_multiplexer_choose_req_grant <= 3'd4;
									end else begin
										if (sdram_multiplexer_choose_req_request[5]) begin
											sdram_multiplexer_choose_req_grant <= 3'd5;
										end
									end
								end
							end
						end
					end
				end
			end
			3'd7: begin
				if (sdram_multiplexer_choose_req_request[0]) begin
					sdram_multiplexer_choose_req_grant <= 1'd0;
				end else begin
					if (sdram_multiplexer_choose_req_request[1]) begin
						sdram_multiplexer_choose_req_grant <= 1'd1;
					end else begin
						if (sdram_multiplexer_choose_req_request[2]) begin
							sdram_multiplexer_choose_req_grant <= 2'd2;
						end else begin
							if (sdram_multiplexer_choose_req_request[3]) begin
								sdram_multiplexer_choose_req_grant <= 2'd3;
							end else begin
								if (sdram_multiplexer_choose_req_request[4]) begin
									sdram_multiplexer_choose_req_grant <= 3'd4;
								end else begin
									if (sdram_multiplexer_choose_req_request[5]) begin
										sdram_multiplexer_choose_req_grant <= 3'd5;
									end else begin
										if (sdram_multiplexer_choose_req_request[6]) begin
											sdram_multiplexer_choose_req_grant <= 3'd6;
										end
									end
								end
							end
						end
					end
				end
			end
		endcase
	end
	sdram_dfi_p0_cs_n <= 1'd0;
	sdram_dfi_p0_bank <= array_muxed0;
	sdram_dfi_p0_address <= array_muxed1;
	sdram_dfi_p0_cas_n <= (~array_muxed2);
	sdram_dfi_p0_ras_n <= (~array_muxed3);
	sdram_dfi_p0_we_n <= (~array_muxed4);
	sdram_dfi_p0_rddata_en <= array_muxed5;
	sdram_dfi_p0_wrdata_en <= array_muxed6;
	sdram_dfi_p1_cs_n <= 1'd0;
	sdram_dfi_p1_bank <= array_muxed7;
	sdram_dfi_p1_address <= array_muxed8;
	sdram_dfi_p1_cas_n <= (~array_muxed9);
	sdram_dfi_p1_ras_n <= (~array_muxed10);
	sdram_dfi_p1_we_n <= (~array_muxed11);
	sdram_dfi_p1_rddata_en <= array_muxed12;
	sdram_dfi_p1_wrdata_en <= array_muxed13;
	sdram_dfi_p2_cs_n <= 1'd0;
	sdram_dfi_p2_bank <= array_muxed14;
	sdram_dfi_p2_address <= array_muxed15;
	sdram_dfi_p2_cas_n <= (~array_muxed16);
	sdram_dfi_p2_ras_n <= (~array_muxed17);
	sdram_dfi_p2_we_n <= (~array_muxed18);
	sdram_dfi_p2_rddata_en <= array_muxed19;
	sdram_dfi_p2_wrdata_en <= array_muxed20;
	sdram_dfi_p3_cs_n <= 1'd0;
	sdram_dfi_p3_bank <= array_muxed21;
	sdram_dfi_p3_address <= array_muxed22;
	sdram_dfi_p3_cas_n <= (~array_muxed23);
	sdram_dfi_p3_ras_n <= (~array_muxed24);
	sdram_dfi_p3_we_n <= (~array_muxed25);
	sdram_dfi_p3_rddata_en <= array_muxed26;
	sdram_dfi_p3_wrdata_en <= array_muxed27;
	if (sdram_multiplexer_trrdcon_valid) begin
		sdram_multiplexer_trrdcon_count <= 1'd1;
		if (1'd0) begin
			sdram_multiplexer_trrdcon_ready <= 1'd1;
		end else begin
			sdram_multiplexer_trrdcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_multiplexer_trrdcon_ready)) begin
			sdram_multiplexer_trrdcon_count <= (sdram_multiplexer_trrdcon_count - 1'd1);
			if ((sdram_multiplexer_trrdcon_count == 1'd1)) begin
				sdram_multiplexer_trrdcon_ready <= 1'd1;
			end
		end
	end
	sdram_multiplexer_tfawcon_window <= {sdram_multiplexer_tfawcon_window, sdram_multiplexer_tfawcon_valid};
	if ((sdram_multiplexer_tfawcon_count < 3'd4)) begin
		if ((sdram_multiplexer_tfawcon_count == 2'd3)) begin
			sdram_multiplexer_tfawcon_ready <= (~sdram_multiplexer_tfawcon_valid);
		end else begin
			sdram_multiplexer_tfawcon_ready <= 1'd1;
		end
	end
	if (sdram_multiplexer_tccdcon_valid) begin
		sdram_multiplexer_tccdcon_count <= 1'd0;
		if (1'd1) begin
			sdram_multiplexer_tccdcon_ready <= 1'd1;
		end else begin
			sdram_multiplexer_tccdcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_multiplexer_tccdcon_ready)) begin
			sdram_multiplexer_tccdcon_count <= (sdram_multiplexer_tccdcon_count - 1'd1);
			if ((sdram_multiplexer_tccdcon_count == 1'd1)) begin
				sdram_multiplexer_tccdcon_ready <= 1'd1;
			end
		end
	end
	if (sdram_multiplexer_twtrcon_valid) begin
		sdram_multiplexer_twtrcon_count <= 3'd4;
		if (1'd0) begin
			sdram_multiplexer_twtrcon_ready <= 1'd1;
		end else begin
			sdram_multiplexer_twtrcon_ready <= 1'd0;
		end
	end else begin
		if ((~sdram_multiplexer_twtrcon_ready)) begin
			sdram_multiplexer_twtrcon_count <= (sdram_multiplexer_twtrcon_count - 1'd1);
			if ((sdram_multiplexer_twtrcon_count == 1'd1)) begin
				sdram_multiplexer_twtrcon_ready <= 1'd1;
			end
		end
	end
	multiplexer_state <= multiplexer_next_state;
	new_master_wdata_ready0 <= ((((((((1'd0 | ((roundrobin0_grant == 1'd0) & sdram_interface_bank0_wdata_ready)) | ((roundrobin1_grant == 1'd0) & sdram_interface_bank1_wdata_ready)) | ((roundrobin2_grant == 1'd0) & sdram_interface_bank2_wdata_ready)) | ((roundrobin3_grant == 1'd0) & sdram_interface_bank3_wdata_ready)) | ((roundrobin4_grant == 1'd0) & sdram_interface_bank4_wdata_ready)) | ((roundrobin5_grant == 1'd0) & sdram_interface_bank5_wdata_ready)) | ((roundrobin6_grant == 1'd0) & sdram_interface_bank6_wdata_ready)) | ((roundrobin7_grant == 1'd0) & sdram_interface_bank7_wdata_ready));
	new_master_wdata_ready1 <= new_master_wdata_ready0;
	new_master_rdata_valid0 <= ((((((((1'd0 | ((roundrobin0_grant == 1'd0) & sdram_interface_bank0_rdata_valid)) | ((roundrobin1_grant == 1'd0) & sdram_interface_bank1_rdata_valid)) | ((roundrobin2_grant == 1'd0) & sdram_interface_bank2_rdata_valid)) | ((roundrobin3_grant == 1'd0) & sdram_interface_bank3_rdata_valid)) | ((roundrobin4_grant == 1'd0) & sdram_interface_bank4_rdata_valid)) | ((roundrobin5_grant == 1'd0) & sdram_interface_bank5_rdata_valid)) | ((roundrobin6_grant == 1'd0) & sdram_interface_bank6_rdata_valid)) | ((roundrobin7_grant == 1'd0) & sdram_interface_bank7_rdata_valid));
	new_master_rdata_valid1 <= new_master_rdata_valid0;
	new_master_rdata_valid2 <= new_master_rdata_valid1;
	new_master_rdata_valid3 <= new_master_rdata_valid2;
	new_master_rdata_valid4 <= new_master_rdata_valid3;
	new_master_rdata_valid5 <= new_master_rdata_valid4;
	new_master_rdata_valid6 <= new_master_rdata_valid5;
	new_master_rdata_valid7 <= new_master_rdata_valid6;
	new_master_rdata_valid8 <= new_master_rdata_valid7;
	if (sys_rst) begin
		sdram_pi_mod1_phaseinjector0_status <= 64'd0;
		sdram_pi_mod1_phaseinjector1_status <= 64'd0;
		sdram_pi_mod1_phaseinjector2_status <= 64'd0;
		sdram_pi_mod1_phaseinjector3_status <= 64'd0;
		sdram_pi_mod2_phaseinjector0_status <= 64'd0;
		sdram_pi_mod2_phaseinjector1_status <= 64'd0;
		sdram_pi_mod2_phaseinjector2_status <= 64'd0;
		sdram_pi_mod2_phaseinjector3_status <= 64'd0;
		sdram_pi_mod3_phaseinjector0_status <= 64'd0;
		sdram_pi_mod3_phaseinjector1_status <= 64'd0;
		sdram_pi_mod3_phaseinjector2_status <= 64'd0;
		sdram_pi_mod3_phaseinjector3_status <= 64'd0;
		sdram_dfi_p0_address <= 14'd0;
		sdram_dfi_p0_bank <= 3'd0;
		sdram_dfi_p0_cas_n <= 1'd1;
		sdram_dfi_p0_cs_n <= 1'd1;
		sdram_dfi_p0_ras_n <= 1'd1;
		sdram_dfi_p0_we_n <= 1'd1;
		sdram_dfi_p0_wrdata_en <= 1'd0;
		sdram_dfi_p0_rddata_en <= 1'd0;
		sdram_dfi_p1_address <= 14'd0;
		sdram_dfi_p1_bank <= 3'd0;
		sdram_dfi_p1_cas_n <= 1'd1;
		sdram_dfi_p1_cs_n <= 1'd1;
		sdram_dfi_p1_ras_n <= 1'd1;
		sdram_dfi_p1_we_n <= 1'd1;
		sdram_dfi_p1_wrdata_en <= 1'd0;
		sdram_dfi_p1_rddata_en <= 1'd0;
		sdram_dfi_p2_address <= 14'd0;
		sdram_dfi_p2_bank <= 3'd0;
		sdram_dfi_p2_cas_n <= 1'd1;
		sdram_dfi_p2_cs_n <= 1'd1;
		sdram_dfi_p2_ras_n <= 1'd1;
		sdram_dfi_p2_we_n <= 1'd1;
		sdram_dfi_p2_wrdata_en <= 1'd0;
		sdram_dfi_p2_rddata_en <= 1'd0;
		sdram_dfi_p3_address <= 14'd0;
		sdram_dfi_p3_bank <= 3'd0;
		sdram_dfi_p3_cas_n <= 1'd1;
		sdram_dfi_p3_cs_n <= 1'd1;
		sdram_dfi_p3_ras_n <= 1'd1;
		sdram_dfi_p3_we_n <= 1'd1;
		sdram_dfi_p3_wrdata_en <= 1'd0;
		sdram_dfi_p3_rddata_en <= 1'd0;
		sdram_cmd_valid <= 1'd0;
		sdram_cmd_payload_a <= 14'd0;
		sdram_cmd_payload_ba <= 3'd0;
		sdram_cmd_payload_cas <= 1'd0;
		sdram_cmd_payload_ras <= 1'd0;
		sdram_cmd_payload_we <= 1'd0;
		sdram_cmd_payload_is_cmd <= 1'd0;
		sdram_cmd_payload_is_read <= 1'd0;
		sdram_cmd_payload_is_write <= 1'd0;
		sdram_timer_count1 <= 10'd976;
		sdram_timer2_count1 <= 10'd976;
		sdram_timer3_count1 <= 10'd976;
		sdram_postponer_req_o <= 1'd0;
		sdram_postponer_count <= 1'd0;
		sdram_postponer2_req_o <= 1'd0;
		sdram_postponer2_count <= 1'd0;
		sdram_postponer3_req_o <= 1'd0;
		sdram_postponer3_count <= 1'd0;
		sdram_cmd1_ready <= 1'd0;
		sdram_cmd1_payload_a <= 14'd0;
		sdram_cmd1_payload_ba <= 3'd0;
		sdram_cmd1_payload_cas <= 1'd0;
		sdram_cmd1_payload_ras <= 1'd0;
		sdram_cmd1_payload_we <= 1'd0;
		sdram_sequencer_done1 <= 1'd0;
		sdram_sequencer_counter <= 6'd0;
		sdram_sequencer_count <= 1'd0;
		sdram_cmd2_ready <= 1'd0;
		sdram_cmd2_payload_a <= 14'd0;
		sdram_cmd2_payload_ba <= 3'd0;
		sdram_cmd2_payload_cas <= 1'd0;
		sdram_cmd2_payload_ras <= 1'd0;
		sdram_cmd2_payload_we <= 1'd0;
		sdram_sequencer2_done1 <= 1'd0;
		sdram_sequencer2_counter <= 6'd0;
		sdram_sequencer2_count <= 1'd0;
		sdram_cmd3_ready <= 1'd0;
		sdram_cmd3_payload_a <= 14'd0;
		sdram_cmd3_payload_ba <= 3'd0;
		sdram_cmd3_payload_cas <= 1'd0;
		sdram_cmd3_payload_ras <= 1'd0;
		sdram_cmd3_payload_we <= 1'd0;
		sdram_sequencer3_done1 <= 1'd0;
		sdram_sequencer3_counter <= 6'd0;
		sdram_sequencer3_count <= 1'd0;
		sdram_zqcs_timer_count1 <= 27'd124999999;
		sdram_zqcs_executer_done <= 1'd0;
		sdram_zqcs_executer_counter <= 5'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead_level <= 4'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead_produce <= 3'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead_consume <= 3'd0;
		sdram_tmrbankmachine0_cmd_buffer_source_valid <= 1'd0;
		sdram_tmrbankmachine0_cmd_buffer_source_payload_we <= 1'd0;
		sdram_tmrbankmachine0_cmd_buffer_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead2_level <= 4'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead2_produce <= 3'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead2_consume <= 3'd0;
		sdram_tmrbankmachine0_cmd_buffer2_source_valid <= 1'd0;
		sdram_tmrbankmachine0_cmd_buffer2_source_payload_we <= 1'd0;
		sdram_tmrbankmachine0_cmd_buffer2_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead3_level <= 4'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead3_produce <= 3'd0;
		sdram_tmrbankmachine0_cmd_buffer_lookahead3_consume <= 3'd0;
		sdram_tmrbankmachine0_cmd_buffer3_source_valid <= 1'd0;
		sdram_tmrbankmachine0_cmd_buffer3_source_payload_we <= 1'd0;
		sdram_tmrbankmachine0_cmd_buffer3_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine0_row <= 14'd0;
		sdram_tmrbankmachine0_row_opened <= 1'd0;
		sdram_tmrbankmachine0_twtpcon_ready <= 1'd0;
		sdram_tmrbankmachine0_twtpcon_count <= 3'd0;
		sdram_tmrbankmachine0_twtpcon2_ready <= 1'd0;
		sdram_tmrbankmachine0_twtpcon2_count <= 3'd0;
		sdram_tmrbankmachine0_twtpcon3_ready <= 1'd0;
		sdram_tmrbankmachine0_twtpcon3_count <= 3'd0;
		sdram_tmrbankmachine0_trccon_ready <= 1'd0;
		sdram_tmrbankmachine0_trccon_count <= 3'd0;
		sdram_tmrbankmachine0_trccon2_ready <= 1'd0;
		sdram_tmrbankmachine0_trccon2_count <= 3'd0;
		sdram_tmrbankmachine0_trccon3_ready <= 1'd0;
		sdram_tmrbankmachine0_trccon3_count <= 3'd0;
		sdram_tmrbankmachine0_trascon_ready <= 1'd0;
		sdram_tmrbankmachine0_trascon_count <= 3'd0;
		sdram_tmrbankmachine0_trascon2_ready <= 1'd0;
		sdram_tmrbankmachine0_trascon2_count <= 3'd0;
		sdram_tmrbankmachine0_trascon3_ready <= 1'd0;
		sdram_tmrbankmachine0_trascon3_count <= 3'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead_level <= 4'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead_produce <= 3'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead_consume <= 3'd0;
		sdram_tmrbankmachine1_cmd_buffer_source_valid <= 1'd0;
		sdram_tmrbankmachine1_cmd_buffer_source_payload_we <= 1'd0;
		sdram_tmrbankmachine1_cmd_buffer_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead2_level <= 4'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead2_produce <= 3'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead2_consume <= 3'd0;
		sdram_tmrbankmachine1_cmd_buffer2_source_valid <= 1'd0;
		sdram_tmrbankmachine1_cmd_buffer2_source_payload_we <= 1'd0;
		sdram_tmrbankmachine1_cmd_buffer2_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead3_level <= 4'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead3_produce <= 3'd0;
		sdram_tmrbankmachine1_cmd_buffer_lookahead3_consume <= 3'd0;
		sdram_tmrbankmachine1_cmd_buffer3_source_valid <= 1'd0;
		sdram_tmrbankmachine1_cmd_buffer3_source_payload_we <= 1'd0;
		sdram_tmrbankmachine1_cmd_buffer3_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine1_row <= 14'd0;
		sdram_tmrbankmachine1_row_opened <= 1'd0;
		sdram_tmrbankmachine1_twtpcon_ready <= 1'd0;
		sdram_tmrbankmachine1_twtpcon_count <= 3'd0;
		sdram_tmrbankmachine1_twtpcon2_ready <= 1'd0;
		sdram_tmrbankmachine1_twtpcon2_count <= 3'd0;
		sdram_tmrbankmachine1_twtpcon3_ready <= 1'd0;
		sdram_tmrbankmachine1_twtpcon3_count <= 3'd0;
		sdram_tmrbankmachine1_trccon_ready <= 1'd0;
		sdram_tmrbankmachine1_trccon_count <= 3'd0;
		sdram_tmrbankmachine1_trccon2_ready <= 1'd0;
		sdram_tmrbankmachine1_trccon2_count <= 3'd0;
		sdram_tmrbankmachine1_trccon3_ready <= 1'd0;
		sdram_tmrbankmachine1_trccon3_count <= 3'd0;
		sdram_tmrbankmachine1_trascon_ready <= 1'd0;
		sdram_tmrbankmachine1_trascon_count <= 3'd0;
		sdram_tmrbankmachine1_trascon2_ready <= 1'd0;
		sdram_tmrbankmachine1_trascon2_count <= 3'd0;
		sdram_tmrbankmachine1_trascon3_ready <= 1'd0;
		sdram_tmrbankmachine1_trascon3_count <= 3'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead_level <= 4'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead_produce <= 3'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead_consume <= 3'd0;
		sdram_tmrbankmachine2_cmd_buffer_source_valid <= 1'd0;
		sdram_tmrbankmachine2_cmd_buffer_source_payload_we <= 1'd0;
		sdram_tmrbankmachine2_cmd_buffer_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead2_level <= 4'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead2_produce <= 3'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead2_consume <= 3'd0;
		sdram_tmrbankmachine2_cmd_buffer2_source_valid <= 1'd0;
		sdram_tmrbankmachine2_cmd_buffer2_source_payload_we <= 1'd0;
		sdram_tmrbankmachine2_cmd_buffer2_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead3_level <= 4'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead3_produce <= 3'd0;
		sdram_tmrbankmachine2_cmd_buffer_lookahead3_consume <= 3'd0;
		sdram_tmrbankmachine2_cmd_buffer3_source_valid <= 1'd0;
		sdram_tmrbankmachine2_cmd_buffer3_source_payload_we <= 1'd0;
		sdram_tmrbankmachine2_cmd_buffer3_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine2_row <= 14'd0;
		sdram_tmrbankmachine2_row_opened <= 1'd0;
		sdram_tmrbankmachine2_twtpcon_ready <= 1'd0;
		sdram_tmrbankmachine2_twtpcon_count <= 3'd0;
		sdram_tmrbankmachine2_twtpcon2_ready <= 1'd0;
		sdram_tmrbankmachine2_twtpcon2_count <= 3'd0;
		sdram_tmrbankmachine2_twtpcon3_ready <= 1'd0;
		sdram_tmrbankmachine2_twtpcon3_count <= 3'd0;
		sdram_tmrbankmachine2_trccon_ready <= 1'd0;
		sdram_tmrbankmachine2_trccon_count <= 3'd0;
		sdram_tmrbankmachine2_trccon2_ready <= 1'd0;
		sdram_tmrbankmachine2_trccon2_count <= 3'd0;
		sdram_tmrbankmachine2_trccon3_ready <= 1'd0;
		sdram_tmrbankmachine2_trccon3_count <= 3'd0;
		sdram_tmrbankmachine2_trascon_ready <= 1'd0;
		sdram_tmrbankmachine2_trascon_count <= 3'd0;
		sdram_tmrbankmachine2_trascon2_ready <= 1'd0;
		sdram_tmrbankmachine2_trascon2_count <= 3'd0;
		sdram_tmrbankmachine2_trascon3_ready <= 1'd0;
		sdram_tmrbankmachine2_trascon3_count <= 3'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead_level <= 4'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead_produce <= 3'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead_consume <= 3'd0;
		sdram_tmrbankmachine3_cmd_buffer_source_valid <= 1'd0;
		sdram_tmrbankmachine3_cmd_buffer_source_payload_we <= 1'd0;
		sdram_tmrbankmachine3_cmd_buffer_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead2_level <= 4'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead2_produce <= 3'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead2_consume <= 3'd0;
		sdram_tmrbankmachine3_cmd_buffer2_source_valid <= 1'd0;
		sdram_tmrbankmachine3_cmd_buffer2_source_payload_we <= 1'd0;
		sdram_tmrbankmachine3_cmd_buffer2_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead3_level <= 4'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead3_produce <= 3'd0;
		sdram_tmrbankmachine3_cmd_buffer_lookahead3_consume <= 3'd0;
		sdram_tmrbankmachine3_cmd_buffer3_source_valid <= 1'd0;
		sdram_tmrbankmachine3_cmd_buffer3_source_payload_we <= 1'd0;
		sdram_tmrbankmachine3_cmd_buffer3_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine3_row <= 14'd0;
		sdram_tmrbankmachine3_row_opened <= 1'd0;
		sdram_tmrbankmachine3_twtpcon_ready <= 1'd0;
		sdram_tmrbankmachine3_twtpcon_count <= 3'd0;
		sdram_tmrbankmachine3_twtpcon2_ready <= 1'd0;
		sdram_tmrbankmachine3_twtpcon2_count <= 3'd0;
		sdram_tmrbankmachine3_twtpcon3_ready <= 1'd0;
		sdram_tmrbankmachine3_twtpcon3_count <= 3'd0;
		sdram_tmrbankmachine3_trccon_ready <= 1'd0;
		sdram_tmrbankmachine3_trccon_count <= 3'd0;
		sdram_tmrbankmachine3_trccon2_ready <= 1'd0;
		sdram_tmrbankmachine3_trccon2_count <= 3'd0;
		sdram_tmrbankmachine3_trccon3_ready <= 1'd0;
		sdram_tmrbankmachine3_trccon3_count <= 3'd0;
		sdram_tmrbankmachine3_trascon_ready <= 1'd0;
		sdram_tmrbankmachine3_trascon_count <= 3'd0;
		sdram_tmrbankmachine3_trascon2_ready <= 1'd0;
		sdram_tmrbankmachine3_trascon2_count <= 3'd0;
		sdram_tmrbankmachine3_trascon3_ready <= 1'd0;
		sdram_tmrbankmachine3_trascon3_count <= 3'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead_level <= 4'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead_produce <= 3'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead_consume <= 3'd0;
		sdram_tmrbankmachine4_cmd_buffer_source_valid <= 1'd0;
		sdram_tmrbankmachine4_cmd_buffer_source_payload_we <= 1'd0;
		sdram_tmrbankmachine4_cmd_buffer_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead2_level <= 4'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead2_produce <= 3'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead2_consume <= 3'd0;
		sdram_tmrbankmachine4_cmd_buffer2_source_valid <= 1'd0;
		sdram_tmrbankmachine4_cmd_buffer2_source_payload_we <= 1'd0;
		sdram_tmrbankmachine4_cmd_buffer2_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead3_level <= 4'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead3_produce <= 3'd0;
		sdram_tmrbankmachine4_cmd_buffer_lookahead3_consume <= 3'd0;
		sdram_tmrbankmachine4_cmd_buffer3_source_valid <= 1'd0;
		sdram_tmrbankmachine4_cmd_buffer3_source_payload_we <= 1'd0;
		sdram_tmrbankmachine4_cmd_buffer3_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine4_row <= 14'd0;
		sdram_tmrbankmachine4_row_opened <= 1'd0;
		sdram_tmrbankmachine4_twtpcon_ready <= 1'd0;
		sdram_tmrbankmachine4_twtpcon_count <= 3'd0;
		sdram_tmrbankmachine4_twtpcon2_ready <= 1'd0;
		sdram_tmrbankmachine4_twtpcon2_count <= 3'd0;
		sdram_tmrbankmachine4_twtpcon3_ready <= 1'd0;
		sdram_tmrbankmachine4_twtpcon3_count <= 3'd0;
		sdram_tmrbankmachine4_trccon_ready <= 1'd0;
		sdram_tmrbankmachine4_trccon_count <= 3'd0;
		sdram_tmrbankmachine4_trccon2_ready <= 1'd0;
		sdram_tmrbankmachine4_trccon2_count <= 3'd0;
		sdram_tmrbankmachine4_trccon3_ready <= 1'd0;
		sdram_tmrbankmachine4_trccon3_count <= 3'd0;
		sdram_tmrbankmachine4_trascon_ready <= 1'd0;
		sdram_tmrbankmachine4_trascon_count <= 3'd0;
		sdram_tmrbankmachine4_trascon2_ready <= 1'd0;
		sdram_tmrbankmachine4_trascon2_count <= 3'd0;
		sdram_tmrbankmachine4_trascon3_ready <= 1'd0;
		sdram_tmrbankmachine4_trascon3_count <= 3'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead_level <= 4'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead_produce <= 3'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead_consume <= 3'd0;
		sdram_tmrbankmachine5_cmd_buffer_source_valid <= 1'd0;
		sdram_tmrbankmachine5_cmd_buffer_source_payload_we <= 1'd0;
		sdram_tmrbankmachine5_cmd_buffer_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead2_level <= 4'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead2_produce <= 3'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead2_consume <= 3'd0;
		sdram_tmrbankmachine5_cmd_buffer2_source_valid <= 1'd0;
		sdram_tmrbankmachine5_cmd_buffer2_source_payload_we <= 1'd0;
		sdram_tmrbankmachine5_cmd_buffer2_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead3_level <= 4'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead3_produce <= 3'd0;
		sdram_tmrbankmachine5_cmd_buffer_lookahead3_consume <= 3'd0;
		sdram_tmrbankmachine5_cmd_buffer3_source_valid <= 1'd0;
		sdram_tmrbankmachine5_cmd_buffer3_source_payload_we <= 1'd0;
		sdram_tmrbankmachine5_cmd_buffer3_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine5_row <= 14'd0;
		sdram_tmrbankmachine5_row_opened <= 1'd0;
		sdram_tmrbankmachine5_twtpcon_ready <= 1'd0;
		sdram_tmrbankmachine5_twtpcon_count <= 3'd0;
		sdram_tmrbankmachine5_twtpcon2_ready <= 1'd0;
		sdram_tmrbankmachine5_twtpcon2_count <= 3'd0;
		sdram_tmrbankmachine5_twtpcon3_ready <= 1'd0;
		sdram_tmrbankmachine5_twtpcon3_count <= 3'd0;
		sdram_tmrbankmachine5_trccon_ready <= 1'd0;
		sdram_tmrbankmachine5_trccon_count <= 3'd0;
		sdram_tmrbankmachine5_trccon2_ready <= 1'd0;
		sdram_tmrbankmachine5_trccon2_count <= 3'd0;
		sdram_tmrbankmachine5_trccon3_ready <= 1'd0;
		sdram_tmrbankmachine5_trccon3_count <= 3'd0;
		sdram_tmrbankmachine5_trascon_ready <= 1'd0;
		sdram_tmrbankmachine5_trascon_count <= 3'd0;
		sdram_tmrbankmachine5_trascon2_ready <= 1'd0;
		sdram_tmrbankmachine5_trascon2_count <= 3'd0;
		sdram_tmrbankmachine5_trascon3_ready <= 1'd0;
		sdram_tmrbankmachine5_trascon3_count <= 3'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead_level <= 4'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead_produce <= 3'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead_consume <= 3'd0;
		sdram_tmrbankmachine6_cmd_buffer_source_valid <= 1'd0;
		sdram_tmrbankmachine6_cmd_buffer_source_payload_we <= 1'd0;
		sdram_tmrbankmachine6_cmd_buffer_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead2_level <= 4'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead2_produce <= 3'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead2_consume <= 3'd0;
		sdram_tmrbankmachine6_cmd_buffer2_source_valid <= 1'd0;
		sdram_tmrbankmachine6_cmd_buffer2_source_payload_we <= 1'd0;
		sdram_tmrbankmachine6_cmd_buffer2_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead3_level <= 4'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead3_produce <= 3'd0;
		sdram_tmrbankmachine6_cmd_buffer_lookahead3_consume <= 3'd0;
		sdram_tmrbankmachine6_cmd_buffer3_source_valid <= 1'd0;
		sdram_tmrbankmachine6_cmd_buffer3_source_payload_we <= 1'd0;
		sdram_tmrbankmachine6_cmd_buffer3_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine6_row <= 14'd0;
		sdram_tmrbankmachine6_row_opened <= 1'd0;
		sdram_tmrbankmachine6_twtpcon_ready <= 1'd0;
		sdram_tmrbankmachine6_twtpcon_count <= 3'd0;
		sdram_tmrbankmachine6_twtpcon2_ready <= 1'd0;
		sdram_tmrbankmachine6_twtpcon2_count <= 3'd0;
		sdram_tmrbankmachine6_twtpcon3_ready <= 1'd0;
		sdram_tmrbankmachine6_twtpcon3_count <= 3'd0;
		sdram_tmrbankmachine6_trccon_ready <= 1'd0;
		sdram_tmrbankmachine6_trccon_count <= 3'd0;
		sdram_tmrbankmachine6_trccon2_ready <= 1'd0;
		sdram_tmrbankmachine6_trccon2_count <= 3'd0;
		sdram_tmrbankmachine6_trccon3_ready <= 1'd0;
		sdram_tmrbankmachine6_trccon3_count <= 3'd0;
		sdram_tmrbankmachine6_trascon_ready <= 1'd0;
		sdram_tmrbankmachine6_trascon_count <= 3'd0;
		sdram_tmrbankmachine6_trascon2_ready <= 1'd0;
		sdram_tmrbankmachine6_trascon2_count <= 3'd0;
		sdram_tmrbankmachine6_trascon3_ready <= 1'd0;
		sdram_tmrbankmachine6_trascon3_count <= 3'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead_level <= 4'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead_produce <= 3'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead_consume <= 3'd0;
		sdram_tmrbankmachine7_cmd_buffer_source_valid <= 1'd0;
		sdram_tmrbankmachine7_cmd_buffer_source_payload_we <= 1'd0;
		sdram_tmrbankmachine7_cmd_buffer_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead2_level <= 4'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead2_produce <= 3'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead2_consume <= 3'd0;
		sdram_tmrbankmachine7_cmd_buffer2_source_valid <= 1'd0;
		sdram_tmrbankmachine7_cmd_buffer2_source_payload_we <= 1'd0;
		sdram_tmrbankmachine7_cmd_buffer2_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead3_level <= 4'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead3_produce <= 3'd0;
		sdram_tmrbankmachine7_cmd_buffer_lookahead3_consume <= 3'd0;
		sdram_tmrbankmachine7_cmd_buffer3_source_valid <= 1'd0;
		sdram_tmrbankmachine7_cmd_buffer3_source_payload_we <= 1'd0;
		sdram_tmrbankmachine7_cmd_buffer3_source_payload_addr <= 21'd0;
		sdram_tmrbankmachine7_row <= 14'd0;
		sdram_tmrbankmachine7_row_opened <= 1'd0;
		sdram_tmrbankmachine7_twtpcon_ready <= 1'd0;
		sdram_tmrbankmachine7_twtpcon_count <= 3'd0;
		sdram_tmrbankmachine7_twtpcon2_ready <= 1'd0;
		sdram_tmrbankmachine7_twtpcon2_count <= 3'd0;
		sdram_tmrbankmachine7_twtpcon3_ready <= 1'd0;
		sdram_tmrbankmachine7_twtpcon3_count <= 3'd0;
		sdram_tmrbankmachine7_trccon_ready <= 1'd0;
		sdram_tmrbankmachine7_trccon_count <= 3'd0;
		sdram_tmrbankmachine7_trccon2_ready <= 1'd0;
		sdram_tmrbankmachine7_trccon2_count <= 3'd0;
		sdram_tmrbankmachine7_trccon3_ready <= 1'd0;
		sdram_tmrbankmachine7_trccon3_count <= 3'd0;
		sdram_tmrbankmachine7_trascon_ready <= 1'd0;
		sdram_tmrbankmachine7_trascon_count <= 3'd0;
		sdram_tmrbankmachine7_trascon2_ready <= 1'd0;
		sdram_tmrbankmachine7_trascon2_count <= 3'd0;
		sdram_tmrbankmachine7_trascon3_ready <= 1'd0;
		sdram_tmrbankmachine7_trascon3_count <= 3'd0;
		sdram_multiplexer_choose_cmd_grant <= 3'd0;
		sdram_multiplexer_choose_req_grant <= 3'd0;
		sdram_multiplexer_trrdcon_ready <= 1'd0;
		sdram_multiplexer_trrdcon_count <= 1'd0;
		sdram_multiplexer_tfawcon_ready <= 1'd1;
		sdram_multiplexer_tfawcon_window <= 5'd0;
		sdram_multiplexer_tccdcon_ready <= 1'd0;
		sdram_multiplexer_tccdcon_count <= 1'd0;
		sdram_multiplexer_twtrcon_ready <= 1'd0;
		sdram_multiplexer_twtrcon_count <= 3'd0;
		sdram_multiplexer_time0 <= 5'd0;
		sdram_multiplexer_time1 <= 4'd0;
		tmrrefresher_state <= 2'd0;
		tmrbankmachine0_state <= 4'd0;
		tmrbankmachine1_state <= 4'd0;
		tmrbankmachine2_state <= 4'd0;
		tmrbankmachine3_state <= 4'd0;
		tmrbankmachine4_state <= 4'd0;
		tmrbankmachine5_state <= 4'd0;
		tmrbankmachine6_state <= 4'd0;
		tmrbankmachine7_state <= 4'd0;
		multiplexer_state <= 4'd0;
		new_master_wdata_ready0 <= 1'd0;
		new_master_wdata_ready1 <= 1'd0;
		new_master_rdata_valid0 <= 1'd0;
		new_master_rdata_valid1 <= 1'd0;
		new_master_rdata_valid2 <= 1'd0;
		new_master_rdata_valid3 <= 1'd0;
		new_master_rdata_valid4 <= 1'd0;
		new_master_rdata_valid5 <= 1'd0;
		new_master_rdata_valid6 <= 1'd0;
		new_master_rdata_valid7 <= 1'd0;
		new_master_rdata_valid8 <= 1'd0;
	end
end

reg [23:0] storage[0:7];
reg [23:0] memdat;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_we)
		storage[sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_adr] <= sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_dat_w;
	memdat <= storage[sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine0_cmd_buffer_lookahead_wrport_dat_r = memdat;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead_rdport_dat_r = storage[sdram_tmrbankmachine0_cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_1[0:7];
reg [23:0] memdat_1;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_we)
		storage_1[sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_adr] <= sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_dat_w;
	memdat_1 <= storage_1[sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_wrport_dat_r = memdat_1;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead2_rdport_dat_r = storage_1[sdram_tmrbankmachine0_cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_2[0:7];
reg [23:0] memdat_2;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_we)
		storage_2[sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_adr] <= sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_dat_w;
	memdat_2 <= storage_2[sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_wrport_dat_r = memdat_2;
assign sdram_tmrbankmachine0_cmd_buffer_lookahead3_rdport_dat_r = storage_2[sdram_tmrbankmachine0_cmd_buffer_lookahead3_rdport_adr];

reg [23:0] storage_3[0:7];
reg [23:0] memdat_3;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_we)
		storage_3[sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_adr] <= sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_dat_w;
	memdat_3 <= storage_3[sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine1_cmd_buffer_lookahead_wrport_dat_r = memdat_3;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead_rdport_dat_r = storage_3[sdram_tmrbankmachine1_cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_4[0:7];
reg [23:0] memdat_4;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_we)
		storage_4[sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_adr] <= sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_dat_w;
	memdat_4 <= storage_4[sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_wrport_dat_r = memdat_4;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead2_rdport_dat_r = storage_4[sdram_tmrbankmachine1_cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_5[0:7];
reg [23:0] memdat_5;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_we)
		storage_5[sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_adr] <= sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_dat_w;
	memdat_5 <= storage_5[sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_wrport_dat_r = memdat_5;
assign sdram_tmrbankmachine1_cmd_buffer_lookahead3_rdport_dat_r = storage_5[sdram_tmrbankmachine1_cmd_buffer_lookahead3_rdport_adr];

reg [23:0] storage_6[0:7];
reg [23:0] memdat_6;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_we)
		storage_6[sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_adr] <= sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_dat_w;
	memdat_6 <= storage_6[sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine2_cmd_buffer_lookahead_wrport_dat_r = memdat_6;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead_rdport_dat_r = storage_6[sdram_tmrbankmachine2_cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_7[0:7];
reg [23:0] memdat_7;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_we)
		storage_7[sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_adr] <= sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_dat_w;
	memdat_7 <= storage_7[sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_wrport_dat_r = memdat_7;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead2_rdport_dat_r = storage_7[sdram_tmrbankmachine2_cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_8[0:7];
reg [23:0] memdat_8;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_we)
		storage_8[sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_adr] <= sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_dat_w;
	memdat_8 <= storage_8[sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_wrport_dat_r = memdat_8;
assign sdram_tmrbankmachine2_cmd_buffer_lookahead3_rdport_dat_r = storage_8[sdram_tmrbankmachine2_cmd_buffer_lookahead3_rdport_adr];

reg [23:0] storage_9[0:7];
reg [23:0] memdat_9;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_we)
		storage_9[sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_adr] <= sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_dat_w;
	memdat_9 <= storage_9[sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine3_cmd_buffer_lookahead_wrport_dat_r = memdat_9;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead_rdport_dat_r = storage_9[sdram_tmrbankmachine3_cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_10[0:7];
reg [23:0] memdat_10;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_we)
		storage_10[sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_adr] <= sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_dat_w;
	memdat_10 <= storage_10[sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_wrport_dat_r = memdat_10;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead2_rdport_dat_r = storage_10[sdram_tmrbankmachine3_cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_11[0:7];
reg [23:0] memdat_11;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_we)
		storage_11[sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_adr] <= sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_dat_w;
	memdat_11 <= storage_11[sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_wrport_dat_r = memdat_11;
assign sdram_tmrbankmachine3_cmd_buffer_lookahead3_rdport_dat_r = storage_11[sdram_tmrbankmachine3_cmd_buffer_lookahead3_rdport_adr];

reg [23:0] storage_12[0:7];
reg [23:0] memdat_12;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_we)
		storage_12[sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_adr] <= sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_dat_w;
	memdat_12 <= storage_12[sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine4_cmd_buffer_lookahead_wrport_dat_r = memdat_12;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead_rdport_dat_r = storage_12[sdram_tmrbankmachine4_cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_13[0:7];
reg [23:0] memdat_13;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_we)
		storage_13[sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_adr] <= sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_dat_w;
	memdat_13 <= storage_13[sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_wrport_dat_r = memdat_13;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead2_rdport_dat_r = storage_13[sdram_tmrbankmachine4_cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_14[0:7];
reg [23:0] memdat_14;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_we)
		storage_14[sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_adr] <= sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_dat_w;
	memdat_14 <= storage_14[sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_wrport_dat_r = memdat_14;
assign sdram_tmrbankmachine4_cmd_buffer_lookahead3_rdport_dat_r = storage_14[sdram_tmrbankmachine4_cmd_buffer_lookahead3_rdport_adr];

reg [23:0] storage_15[0:7];
reg [23:0] memdat_15;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_we)
		storage_15[sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_adr] <= sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_dat_w;
	memdat_15 <= storage_15[sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine5_cmd_buffer_lookahead_wrport_dat_r = memdat_15;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead_rdport_dat_r = storage_15[sdram_tmrbankmachine5_cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_16[0:7];
reg [23:0] memdat_16;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_we)
		storage_16[sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_adr] <= sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_dat_w;
	memdat_16 <= storage_16[sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_wrport_dat_r = memdat_16;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead2_rdport_dat_r = storage_16[sdram_tmrbankmachine5_cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_17[0:7];
reg [23:0] memdat_17;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_we)
		storage_17[sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_adr] <= sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_dat_w;
	memdat_17 <= storage_17[sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_wrport_dat_r = memdat_17;
assign sdram_tmrbankmachine5_cmd_buffer_lookahead3_rdport_dat_r = storage_17[sdram_tmrbankmachine5_cmd_buffer_lookahead3_rdport_adr];

reg [23:0] storage_18[0:7];
reg [23:0] memdat_18;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_we)
		storage_18[sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_adr] <= sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_dat_w;
	memdat_18 <= storage_18[sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine6_cmd_buffer_lookahead_wrport_dat_r = memdat_18;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead_rdport_dat_r = storage_18[sdram_tmrbankmachine6_cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_19[0:7];
reg [23:0] memdat_19;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_we)
		storage_19[sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_adr] <= sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_dat_w;
	memdat_19 <= storage_19[sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_wrport_dat_r = memdat_19;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead2_rdport_dat_r = storage_19[sdram_tmrbankmachine6_cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_20[0:7];
reg [23:0] memdat_20;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_we)
		storage_20[sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_adr] <= sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_dat_w;
	memdat_20 <= storage_20[sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_wrport_dat_r = memdat_20;
assign sdram_tmrbankmachine6_cmd_buffer_lookahead3_rdport_dat_r = storage_20[sdram_tmrbankmachine6_cmd_buffer_lookahead3_rdport_adr];

reg [23:0] storage_21[0:7];
reg [23:0] memdat_21;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_we)
		storage_21[sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_adr] <= sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_dat_w;
	memdat_21 <= storage_21[sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine7_cmd_buffer_lookahead_wrport_dat_r = memdat_21;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead_rdport_dat_r = storage_21[sdram_tmrbankmachine7_cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_22[0:7];
reg [23:0] memdat_22;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_we)
		storage_22[sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_adr] <= sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_dat_w;
	memdat_22 <= storage_22[sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_wrport_dat_r = memdat_22;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead2_rdport_dat_r = storage_22[sdram_tmrbankmachine7_cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_23[0:7];
reg [23:0] memdat_23;
always @(posedge sys_clk) begin
	if (sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_we)
		storage_23[sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_adr] <= sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_dat_w;
	memdat_23 <= storage_23[sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_wrport_dat_r = memdat_23;
assign sdram_tmrbankmachine7_cmd_buffer_lookahead3_rdport_dat_r = storage_23[sdram_tmrbankmachine7_cmd_buffer_lookahead3_rdport_adr];

endmodule
