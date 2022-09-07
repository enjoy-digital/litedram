/* Machine-generated using Migen */
module Multiplexer(
	output reg [13:0] p0_address,
	output reg [2:0] p0_bank,
	output reg p0_cas_n,
	output reg p0_cs_n,
	output reg p0_ras_n,
	output reg p0_we_n,
	output p0_cke,
	output p0_odt,
	output p0_reset_n,
	input p0_act_n,
	output [63:0] p0_wrdata,
	output reg p0_wrdata_en,
	output [7:0] p0_wrdata_mask,
	output reg p0_rddata_en,
	input [63:0] p0_rddata,
	input p0_rddata_valid,
	output reg [13:0] p1_address,
	output reg [2:0] p1_bank,
	output reg p1_cas_n,
	output reg p1_cs_n,
	output reg p1_ras_n,
	output reg p1_we_n,
	output p1_cke,
	output p1_odt,
	output p1_reset_n,
	input p1_act_n,
	output [63:0] p1_wrdata,
	output reg p1_wrdata_en,
	output [7:0] p1_wrdata_mask,
	output reg p1_rddata_en,
	input [63:0] p1_rddata,
	input p1_rddata_valid,
	output reg [13:0] p2_address,
	output reg [2:0] p2_bank,
	output reg p2_cas_n,
	output reg p2_cs_n,
	output reg p2_ras_n,
	output reg p2_we_n,
	output p2_cke,
	output p2_odt,
	output p2_reset_n,
	input p2_act_n,
	output [63:0] p2_wrdata,
	output reg p2_wrdata_en,
	output [7:0] p2_wrdata_mask,
	output reg p2_rddata_en,
	input [63:0] p2_rddata,
	input p2_rddata_valid,
	output reg [13:0] p3_address,
	output reg [2:0] p3_bank,
	output reg p3_cas_n,
	output reg p3_cs_n,
	output reg p3_ras_n,
	output reg p3_we_n,
	output p3_cke,
	output p3_odt,
	output p3_reset_n,
	input p3_act_n,
	output [63:0] p3_wrdata,
	output reg p3_wrdata_en,
	output [7:0] p3_wrdata_mask,
	output reg p3_rddata_en,
	input [63:0] p3_rddata,
	input p3_rddata_valid,
	input [2:0] bank0_valid,
	input [2:0] bank0_ready,
	input [2:0] bank0_we,
	input [62:0] bank0_addr,
	input [2:0] bank0_lock,
	input [2:0] bank0_wdata_ready,
	input [2:0] bank0_rdata_valid,
	input [2:0] bank1_valid,
	input [2:0] bank1_ready,
	input [2:0] bank1_we,
	input [62:0] bank1_addr,
	input [2:0] bank1_lock,
	input [2:0] bank1_wdata_ready,
	input [2:0] bank1_rdata_valid,
	input [2:0] bank2_valid,
	input [2:0] bank2_ready,
	input [2:0] bank2_we,
	input [62:0] bank2_addr,
	input [2:0] bank2_lock,
	input [2:0] bank2_wdata_ready,
	input [2:0] bank2_rdata_valid,
	input [2:0] bank3_valid,
	input [2:0] bank3_ready,
	input [2:0] bank3_we,
	input [62:0] bank3_addr,
	input [2:0] bank3_lock,
	input [2:0] bank3_wdata_ready,
	input [2:0] bank3_rdata_valid,
	input [2:0] bank4_valid,
	input [2:0] bank4_ready,
	input [2:0] bank4_we,
	input [62:0] bank4_addr,
	input [2:0] bank4_lock,
	input [2:0] bank4_wdata_ready,
	input [2:0] bank4_rdata_valid,
	input [2:0] bank5_valid,
	input [2:0] bank5_ready,
	input [2:0] bank5_we,
	input [62:0] bank5_addr,
	input [2:0] bank5_lock,
	input [2:0] bank5_wdata_ready,
	input [2:0] bank5_rdata_valid,
	input [2:0] bank6_valid,
	input [2:0] bank6_ready,
	input [2:0] bank6_we,
	input [62:0] bank6_addr,
	input [2:0] bank6_lock,
	input [2:0] bank6_wdata_ready,
	input [2:0] bank6_rdata_valid,
	input [2:0] bank7_valid,
	input [2:0] bank7_ready,
	input [2:0] bank7_we,
	input [62:0] bank7_addr,
	input [2:0] bank7_lock,
	input [2:0] bank7_wdata_ready,
	input [2:0] bank7_rdata_valid,
	input [767:0] wdata,
	input [95:0] wdata_we,
	output [767:0] rdata,
	input sys_clk,
	input sys_rst
);

reg [1:0] mock_multiplexer_rdphase_storage = 2'd1;
reg [1:0] mock_multiplexer_wrphase_storage = 2'd2;
wire bankmachine0_refresh_req;
reg bankmachine0_refresh_gnt = 1'd0;
reg bankmachine0_cmd_valid = 1'd0;
reg bankmachine0_cmd_payload_is_read = 1'd0;
reg bankmachine0_cmd_payload_is_write = 1'd0;
reg [2:0] bankmachine0_TMRcmd_valid = 3'd0;
wire [2:0] bankmachine0_TMRcmd_ready;
reg [2:0] bankmachine0_TMRcmd_first = 3'd0;
reg [2:0] bankmachine0_TMRcmd_last = 3'd0;
reg [41:0] bankmachine0_TMRcmd_payload_a = 42'd0;
reg [8:0] bankmachine0_TMRcmd_payload_ba = 9'd0;
reg [2:0] bankmachine0_TMRcmd_payload_cas = 3'd0;
reg [2:0] bankmachine0_TMRcmd_payload_ras = 3'd0;
reg [2:0] bankmachine0_TMRcmd_payload_we = 3'd0;
reg [2:0] bankmachine0_TMRcmd_payload_is_cmd = 3'd0;
reg [2:0] bankmachine0_TMRcmd_payload_is_read = 3'd0;
reg [2:0] bankmachine0_TMRcmd_payload_is_write = 3'd0;
wire bankmachine1_refresh_req;
reg bankmachine1_refresh_gnt = 1'd0;
reg bankmachine1_cmd_valid = 1'd0;
reg bankmachine1_cmd_payload_is_read = 1'd0;
reg bankmachine1_cmd_payload_is_write = 1'd0;
reg [2:0] bankmachine1_TMRcmd_valid = 3'd0;
wire [2:0] bankmachine1_TMRcmd_ready;
reg [2:0] bankmachine1_TMRcmd_first = 3'd0;
reg [2:0] bankmachine1_TMRcmd_last = 3'd0;
reg [41:0] bankmachine1_TMRcmd_payload_a = 42'd0;
reg [8:0] bankmachine1_TMRcmd_payload_ba = 9'd0;
reg [2:0] bankmachine1_TMRcmd_payload_cas = 3'd0;
reg [2:0] bankmachine1_TMRcmd_payload_ras = 3'd0;
reg [2:0] bankmachine1_TMRcmd_payload_we = 3'd0;
reg [2:0] bankmachine1_TMRcmd_payload_is_cmd = 3'd0;
reg [2:0] bankmachine1_TMRcmd_payload_is_read = 3'd0;
reg [2:0] bankmachine1_TMRcmd_payload_is_write = 3'd0;
wire bankmachine2_refresh_req;
reg bankmachine2_refresh_gnt = 1'd0;
reg bankmachine2_cmd_valid = 1'd0;
reg bankmachine2_cmd_payload_is_read = 1'd0;
reg bankmachine2_cmd_payload_is_write = 1'd0;
reg [2:0] bankmachine2_TMRcmd_valid = 3'd0;
wire [2:0] bankmachine2_TMRcmd_ready;
reg [2:0] bankmachine2_TMRcmd_first = 3'd0;
reg [2:0] bankmachine2_TMRcmd_last = 3'd0;
reg [41:0] bankmachine2_TMRcmd_payload_a = 42'd0;
reg [8:0] bankmachine2_TMRcmd_payload_ba = 9'd0;
reg [2:0] bankmachine2_TMRcmd_payload_cas = 3'd0;
reg [2:0] bankmachine2_TMRcmd_payload_ras = 3'd0;
reg [2:0] bankmachine2_TMRcmd_payload_we = 3'd0;
reg [2:0] bankmachine2_TMRcmd_payload_is_cmd = 3'd0;
reg [2:0] bankmachine2_TMRcmd_payload_is_read = 3'd0;
reg [2:0] bankmachine2_TMRcmd_payload_is_write = 3'd0;
wire bankmachine3_refresh_req;
reg bankmachine3_refresh_gnt = 1'd0;
reg bankmachine3_cmd_valid = 1'd0;
reg bankmachine3_cmd_payload_is_read = 1'd0;
reg bankmachine3_cmd_payload_is_write = 1'd0;
reg [2:0] bankmachine3_TMRcmd_valid = 3'd0;
wire [2:0] bankmachine3_TMRcmd_ready;
reg [2:0] bankmachine3_TMRcmd_first = 3'd0;
reg [2:0] bankmachine3_TMRcmd_last = 3'd0;
reg [41:0] bankmachine3_TMRcmd_payload_a = 42'd0;
reg [8:0] bankmachine3_TMRcmd_payload_ba = 9'd0;
reg [2:0] bankmachine3_TMRcmd_payload_cas = 3'd0;
reg [2:0] bankmachine3_TMRcmd_payload_ras = 3'd0;
reg [2:0] bankmachine3_TMRcmd_payload_we = 3'd0;
reg [2:0] bankmachine3_TMRcmd_payload_is_cmd = 3'd0;
reg [2:0] bankmachine3_TMRcmd_payload_is_read = 3'd0;
reg [2:0] bankmachine3_TMRcmd_payload_is_write = 3'd0;
reg [2:0] mock_multiplexer_TMRcmd_valid = 3'd0;
wire [2:0] mock_multiplexer_TMRcmd_ready;
reg [2:0] mock_multiplexer_TMRcmd_first = 3'd0;
reg [2:0] mock_multiplexer_TMRcmd_last = 3'd0;
reg [41:0] mock_multiplexer_TMRcmd_payload_a = 42'd0;
reg [8:0] mock_multiplexer_TMRcmd_payload_ba = 9'd0;
reg [2:0] mock_multiplexer_TMRcmd_payload_cas = 3'd0;
reg [2:0] mock_multiplexer_TMRcmd_payload_ras = 3'd0;
reg [2:0] mock_multiplexer_TMRcmd_payload_we = 3'd0;
reg [2:0] mock_multiplexer_TMRcmd_payload_is_cmd = 3'd0;
reg [2:0] mock_multiplexer_TMRcmd_payload_is_read = 3'd0;
reg [2:0] mock_multiplexer_TMRcmd_payload_is_write = 3'd0;
wire ras_allowed;
wire cas_allowed;
wire [1:0] rdcmdphase;
wire [1:0] wrcmdphase;
wire endpoint0_valid;
reg endpoint0_ready;
wire endpoint0_first;
wire endpoint0_last;
wire [13:0] endpoint0_payload_a;
wire [2:0] endpoint0_payload_ba;
wire endpoint0_payload_cas;
wire endpoint0_payload_ras;
wire endpoint0_payload_we;
wire endpoint0_payload_is_cmd;
wire endpoint0_payload_is_read;
wire endpoint0_payload_is_write;
wire endpoint1_valid;
reg endpoint1_ready;
wire endpoint1_first;
wire endpoint1_last;
wire [13:0] endpoint1_payload_a;
wire [2:0] endpoint1_payload_ba;
wire endpoint1_payload_cas;
wire endpoint1_payload_ras;
wire endpoint1_payload_we;
wire endpoint1_payload_is_cmd;
wire endpoint1_payload_is_read;
wire endpoint1_payload_is_write;
wire endpoint2_valid;
reg endpoint2_ready;
wire endpoint2_first;
wire endpoint2_last;
wire [13:0] endpoint2_payload_a;
wire [2:0] endpoint2_payload_ba;
wire endpoint2_payload_cas;
wire endpoint2_payload_ras;
wire endpoint2_payload_we;
wire endpoint2_payload_is_cmd;
wire endpoint2_payload_is_read;
wire endpoint2_payload_is_write;
wire endpoint3_valid;
reg endpoint3_ready;
wire endpoint3_first;
wire endpoint3_last;
wire [13:0] endpoint3_payload_a;
wire [2:0] endpoint3_payload_ba;
wire endpoint3_payload_cas;
wire endpoint3_payload_ras;
wire endpoint3_payload_we;
wire endpoint3_payload_is_cmd;
wire endpoint3_payload_is_read;
wire endpoint3_payload_is_write;
wire control0;
wire control1;
wire control2;
wire [13:0] control3;
wire [2:0] control4;
wire control5;
wire control6;
wire control7;
wire control8;
wire control9;
wire control10;
wire control11;
wire control12;
wire control13;
wire [13:0] control14;
wire [2:0] control15;
wire control16;
wire control17;
wire control18;
wire control19;
wire control20;
wire control21;
wire control22;
wire control23;
wire control24;
wire [13:0] control25;
wire [2:0] control26;
wire control27;
wire control28;
wire control29;
wire control30;
wire control31;
wire control32;
wire control33;
wire control34;
wire control35;
wire [13:0] control36;
wire [2:0] control37;
wire control38;
wire control39;
wire control40;
wire control41;
wire control42;
wire control43;
reg choose_cmd_want_reads = 1'd0;
reg choose_cmd_want_writes = 1'd0;
reg choose_cmd_want_cmds = 1'd0;
reg choose_cmd_want_activates;
wire choose_cmd_cmd_valid;
reg choose_cmd_cmd_ready;
wire [13:0] choose_cmd_cmd_payload_a;
wire [2:0] choose_cmd_cmd_payload_ba;
reg choose_cmd_cmd_payload_cas;
reg choose_cmd_cmd_payload_ras;
reg choose_cmd_cmd_payload_we;
wire choose_cmd_cmd_payload_is_cmd;
wire choose_cmd_cmd_payload_is_read;
wire choose_cmd_cmd_payload_is_write;
reg [3:0] choose_cmd_valids;
wire [3:0] choose_cmd_request;
reg [1:0] choose_cmd_grant = 2'd0;
wire choose_cmd_ce;
reg choose_req_want_reads;
reg choose_req_want_writes;
reg choose_req_want_cmds = 1'd0;
reg choose_req_want_activates = 1'd0;
wire choose_req_cmd_valid;
reg choose_req_cmd_ready;
wire [13:0] choose_req_cmd_payload_a;
wire [2:0] choose_req_cmd_payload_ba;
reg choose_req_cmd_payload_cas;
reg choose_req_cmd_payload_ras;
reg choose_req_cmd_payload_we;
wire choose_req_cmd_payload_is_cmd;
wire choose_req_cmd_payload_is_read;
wire choose_req_cmd_payload_is_write;
reg [3:0] choose_req_valids;
wire [3:0] choose_req_request;
reg [1:0] choose_req_grant = 2'd0;
wire choose_req_ce;
wire refreshCmd_valid;
reg refreshCmd_ready;
wire refreshCmd_first;
wire refreshCmd_last;
wire [13:0] refreshCmd_payload_a;
wire [2:0] refreshCmd_payload_ba;
wire refreshCmd_payload_cas;
wire refreshCmd_payload_ras;
wire refreshCmd_payload_we;
wire refreshCmd_payload_is_cmd;
wire refreshCmd_payload_is_read;
wire refreshCmd_payload_is_write;
wire control44;
wire control45;
wire control46;
wire [13:0] control47;
wire [2:0] control48;
wire control49;
wire control50;
wire control51;
wire control52;
wire control53;
wire control54;
reg [13:0] nop_a = 14'd0;
reg [1:0] nop_ba = 2'd0;
reg [1:0] steerer0;
reg [1:0] steerer1;
reg [1:0] steerer2;
reg [1:0] steerer3;
reg steerer4 = 1'd1;
reg steerer5 = 1'd1;
reg steerer6 = 1'd1;
reg steerer7 = 1'd1;
reg steerer8 = 1'd1;
reg steerer9 = 1'd1;
reg steerer10 = 1'd1;
reg steerer11 = 1'd1;
wire trrdcon_valid;
(* no_retiming = "true" *) reg trrdcon_ready = 1'd0;
reg trrdcon_count = 1'd0;
wire tfawcon_valid;
(* no_retiming = "true" *) reg tfawcon_ready = 1'd1;
wire [2:0] tfawcon_count;
reg [4:0] tfawcon_window = 5'd0;
wire tccdcon_valid;
(* no_retiming = "true" *) reg tccdcon_ready = 1'd0;
reg tccdcon_count = 1'd0;
wire twtrcon_valid;
(* no_retiming = "true" *) reg twtrcon_ready = 1'd0;
reg [2:0] twtrcon_count = 3'd0;
wire read_available;
wire write_available;
reg en0;
wire max_time0;
reg [4:0] time0 = 5'd0;
reg en1;
wire max_time1;
reg [3:0] time1 = 4'd0;
wire go_to_refresh;
wire [255:0] control55;
wire [31:0] control56;
reg [3:0] state = 4'd0;
reg [3:0] next_state;
wire [95:0] slice_proxy0;
wire [95:0] slice_proxy1;
wire [95:0] slice_proxy2;
wire [95:0] slice_proxy3;
wire [95:0] slice_proxy4;
wire [95:0] slice_proxy5;
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

assign rdcmdphase = (mock_multiplexer_rdphase_storage - 1'd1);
assign wrcmdphase = (mock_multiplexer_wrphase_storage - 1'd1);
assign trrdcon_valid = ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & ((choose_cmd_cmd_payload_ras & (~choose_cmd_cmd_payload_cas)) & (~choose_cmd_cmd_payload_we)));
assign tfawcon_valid = ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & ((choose_cmd_cmd_payload_ras & (~choose_cmd_cmd_payload_cas)) & (~choose_cmd_cmd_payload_we)));
assign ras_allowed = (trrdcon_ready & tfawcon_ready);
assign tccdcon_valid = ((choose_req_cmd_valid & choose_req_cmd_ready) & (choose_req_cmd_payload_is_write | choose_req_cmd_payload_is_read));
assign cas_allowed = tccdcon_ready;
assign twtrcon_valid = ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_write);
assign read_available = ((((bankmachine0_cmd_valid & bankmachine0_cmd_payload_is_read) | (bankmachine1_cmd_valid & bankmachine1_cmd_payload_is_read)) | (bankmachine2_cmd_valid & bankmachine2_cmd_payload_is_read)) | (bankmachine3_cmd_valid & bankmachine3_cmd_payload_is_read));
assign write_available = ((((bankmachine0_cmd_valid & bankmachine0_cmd_payload_is_write) | (bankmachine1_cmd_valid & bankmachine1_cmd_payload_is_write)) | (bankmachine2_cmd_valid & bankmachine2_cmd_payload_is_write)) | (bankmachine3_cmd_valid & bankmachine3_cmd_payload_is_write));
assign max_time0 = (time0 == 1'd0);
assign max_time1 = (time1 == 1'd0);
assign bankmachine0_refresh_req = refreshCmd_valid;
assign bankmachine1_refresh_req = refreshCmd_valid;
assign bankmachine2_refresh_req = refreshCmd_valid;
assign bankmachine3_refresh_req = refreshCmd_valid;
assign go_to_refresh = (((bankmachine0_refresh_gnt & bankmachine1_refresh_gnt) & bankmachine2_refresh_gnt) & bankmachine3_refresh_gnt);
assign control0 = (((bankmachine0_TMRcmd_valid[0] & bankmachine0_TMRcmd_valid[1]) | (bankmachine0_TMRcmd_valid[1] & bankmachine0_TMRcmd_valid[2])) | (bankmachine0_TMRcmd_valid[0] & bankmachine0_TMRcmd_valid[2]));
assign endpoint0_valid = control0;
assign control1 = (((bankmachine0_TMRcmd_last[0] & bankmachine0_TMRcmd_last[1]) | (bankmachine0_TMRcmd_last[1] & bankmachine0_TMRcmd_last[2])) | (bankmachine0_TMRcmd_last[0] & bankmachine0_TMRcmd_last[2]));
assign endpoint0_last = control1;
assign bankmachine0_TMRcmd_ready = {3{endpoint0_ready}};
assign control2 = (((bankmachine0_TMRcmd_first[0] & bankmachine0_TMRcmd_first[1]) | (bankmachine0_TMRcmd_first[1] & bankmachine0_TMRcmd_first[2])) | (bankmachine0_TMRcmd_first[0] & bankmachine0_TMRcmd_first[2]));
assign endpoint0_first = control2;
assign control3 = (((bankmachine0_TMRcmd_payload_a[13:0] & bankmachine0_TMRcmd_payload_a[27:14]) | (bankmachine0_TMRcmd_payload_a[27:14] & bankmachine0_TMRcmd_payload_a[41:28])) | (bankmachine0_TMRcmd_payload_a[13:0] & bankmachine0_TMRcmd_payload_a[41:28]));
assign endpoint0_payload_a = control3;
assign control4 = (((bankmachine0_TMRcmd_payload_ba[2:0] & bankmachine0_TMRcmd_payload_ba[5:3]) | (bankmachine0_TMRcmd_payload_ba[5:3] & bankmachine0_TMRcmd_payload_ba[8:6])) | (bankmachine0_TMRcmd_payload_ba[2:0] & bankmachine0_TMRcmd_payload_ba[8:6]));
assign endpoint0_payload_ba = control4;
assign control5 = (((bankmachine0_TMRcmd_payload_cas[0] & bankmachine0_TMRcmd_payload_cas[1]) | (bankmachine0_TMRcmd_payload_cas[1] & bankmachine0_TMRcmd_payload_cas[2])) | (bankmachine0_TMRcmd_payload_cas[0] & bankmachine0_TMRcmd_payload_cas[2]));
assign endpoint0_payload_cas = control5;
assign control6 = (((bankmachine0_TMRcmd_payload_ras[0] & bankmachine0_TMRcmd_payload_ras[1]) | (bankmachine0_TMRcmd_payload_ras[1] & bankmachine0_TMRcmd_payload_ras[2])) | (bankmachine0_TMRcmd_payload_ras[0] & bankmachine0_TMRcmd_payload_ras[2]));
assign endpoint0_payload_ras = control6;
assign control7 = (((bankmachine0_TMRcmd_payload_we[0] & bankmachine0_TMRcmd_payload_we[1]) | (bankmachine0_TMRcmd_payload_we[1] & bankmachine0_TMRcmd_payload_we[2])) | (bankmachine0_TMRcmd_payload_we[0] & bankmachine0_TMRcmd_payload_we[2]));
assign endpoint0_payload_we = control7;
assign control8 = (((bankmachine0_TMRcmd_payload_is_cmd[0] & bankmachine0_TMRcmd_payload_is_cmd[1]) | (bankmachine0_TMRcmd_payload_is_cmd[1] & bankmachine0_TMRcmd_payload_is_cmd[2])) | (bankmachine0_TMRcmd_payload_is_cmd[0] & bankmachine0_TMRcmd_payload_is_cmd[2]));
assign endpoint0_payload_is_cmd = control8;
assign control9 = (((bankmachine0_TMRcmd_payload_is_read[0] & bankmachine0_TMRcmd_payload_is_read[1]) | (bankmachine0_TMRcmd_payload_is_read[1] & bankmachine0_TMRcmd_payload_is_read[2])) | (bankmachine0_TMRcmd_payload_is_read[0] & bankmachine0_TMRcmd_payload_is_read[2]));
assign endpoint0_payload_is_read = control9;
assign control10 = (((bankmachine0_TMRcmd_payload_is_write[0] & bankmachine0_TMRcmd_payload_is_write[1]) | (bankmachine0_TMRcmd_payload_is_write[1] & bankmachine0_TMRcmd_payload_is_write[2])) | (bankmachine0_TMRcmd_payload_is_write[0] & bankmachine0_TMRcmd_payload_is_write[2]));
assign endpoint0_payload_is_write = control10;
assign control11 = (((bankmachine1_TMRcmd_valid[0] & bankmachine1_TMRcmd_valid[1]) | (bankmachine1_TMRcmd_valid[1] & bankmachine1_TMRcmd_valid[2])) | (bankmachine1_TMRcmd_valid[0] & bankmachine1_TMRcmd_valid[2]));
assign endpoint1_valid = control11;
assign control12 = (((bankmachine1_TMRcmd_last[0] & bankmachine1_TMRcmd_last[1]) | (bankmachine1_TMRcmd_last[1] & bankmachine1_TMRcmd_last[2])) | (bankmachine1_TMRcmd_last[0] & bankmachine1_TMRcmd_last[2]));
assign endpoint1_last = control12;
assign bankmachine1_TMRcmd_ready = {3{endpoint1_ready}};
assign control13 = (((bankmachine1_TMRcmd_first[0] & bankmachine1_TMRcmd_first[1]) | (bankmachine1_TMRcmd_first[1] & bankmachine1_TMRcmd_first[2])) | (bankmachine1_TMRcmd_first[0] & bankmachine1_TMRcmd_first[2]));
assign endpoint1_first = control13;
assign control14 = (((bankmachine1_TMRcmd_payload_a[13:0] & bankmachine1_TMRcmd_payload_a[27:14]) | (bankmachine1_TMRcmd_payload_a[27:14] & bankmachine1_TMRcmd_payload_a[41:28])) | (bankmachine1_TMRcmd_payload_a[13:0] & bankmachine1_TMRcmd_payload_a[41:28]));
assign endpoint1_payload_a = control14;
assign control15 = (((bankmachine1_TMRcmd_payload_ba[2:0] & bankmachine1_TMRcmd_payload_ba[5:3]) | (bankmachine1_TMRcmd_payload_ba[5:3] & bankmachine1_TMRcmd_payload_ba[8:6])) | (bankmachine1_TMRcmd_payload_ba[2:0] & bankmachine1_TMRcmd_payload_ba[8:6]));
assign endpoint1_payload_ba = control15;
assign control16 = (((bankmachine1_TMRcmd_payload_cas[0] & bankmachine1_TMRcmd_payload_cas[1]) | (bankmachine1_TMRcmd_payload_cas[1] & bankmachine1_TMRcmd_payload_cas[2])) | (bankmachine1_TMRcmd_payload_cas[0] & bankmachine1_TMRcmd_payload_cas[2]));
assign endpoint1_payload_cas = control16;
assign control17 = (((bankmachine1_TMRcmd_payload_ras[0] & bankmachine1_TMRcmd_payload_ras[1]) | (bankmachine1_TMRcmd_payload_ras[1] & bankmachine1_TMRcmd_payload_ras[2])) | (bankmachine1_TMRcmd_payload_ras[0] & bankmachine1_TMRcmd_payload_ras[2]));
assign endpoint1_payload_ras = control17;
assign control18 = (((bankmachine1_TMRcmd_payload_we[0] & bankmachine1_TMRcmd_payload_we[1]) | (bankmachine1_TMRcmd_payload_we[1] & bankmachine1_TMRcmd_payload_we[2])) | (bankmachine1_TMRcmd_payload_we[0] & bankmachine1_TMRcmd_payload_we[2]));
assign endpoint1_payload_we = control18;
assign control19 = (((bankmachine1_TMRcmd_payload_is_cmd[0] & bankmachine1_TMRcmd_payload_is_cmd[1]) | (bankmachine1_TMRcmd_payload_is_cmd[1] & bankmachine1_TMRcmd_payload_is_cmd[2])) | (bankmachine1_TMRcmd_payload_is_cmd[0] & bankmachine1_TMRcmd_payload_is_cmd[2]));
assign endpoint1_payload_is_cmd = control19;
assign control20 = (((bankmachine1_TMRcmd_payload_is_read[0] & bankmachine1_TMRcmd_payload_is_read[1]) | (bankmachine1_TMRcmd_payload_is_read[1] & bankmachine1_TMRcmd_payload_is_read[2])) | (bankmachine1_TMRcmd_payload_is_read[0] & bankmachine1_TMRcmd_payload_is_read[2]));
assign endpoint1_payload_is_read = control20;
assign control21 = (((bankmachine1_TMRcmd_payload_is_write[0] & bankmachine1_TMRcmd_payload_is_write[1]) | (bankmachine1_TMRcmd_payload_is_write[1] & bankmachine1_TMRcmd_payload_is_write[2])) | (bankmachine1_TMRcmd_payload_is_write[0] & bankmachine1_TMRcmd_payload_is_write[2]));
assign endpoint1_payload_is_write = control21;
assign control22 = (((bankmachine2_TMRcmd_valid[0] & bankmachine2_TMRcmd_valid[1]) | (bankmachine2_TMRcmd_valid[1] & bankmachine2_TMRcmd_valid[2])) | (bankmachine2_TMRcmd_valid[0] & bankmachine2_TMRcmd_valid[2]));
assign endpoint2_valid = control22;
assign control23 = (((bankmachine2_TMRcmd_last[0] & bankmachine2_TMRcmd_last[1]) | (bankmachine2_TMRcmd_last[1] & bankmachine2_TMRcmd_last[2])) | (bankmachine2_TMRcmd_last[0] & bankmachine2_TMRcmd_last[2]));
assign endpoint2_last = control23;
assign bankmachine2_TMRcmd_ready = {3{endpoint2_ready}};
assign control24 = (((bankmachine2_TMRcmd_first[0] & bankmachine2_TMRcmd_first[1]) | (bankmachine2_TMRcmd_first[1] & bankmachine2_TMRcmd_first[2])) | (bankmachine2_TMRcmd_first[0] & bankmachine2_TMRcmd_first[2]));
assign endpoint2_first = control24;
assign control25 = (((bankmachine2_TMRcmd_payload_a[13:0] & bankmachine2_TMRcmd_payload_a[27:14]) | (bankmachine2_TMRcmd_payload_a[27:14] & bankmachine2_TMRcmd_payload_a[41:28])) | (bankmachine2_TMRcmd_payload_a[13:0] & bankmachine2_TMRcmd_payload_a[41:28]));
assign endpoint2_payload_a = control25;
assign control26 = (((bankmachine2_TMRcmd_payload_ba[2:0] & bankmachine2_TMRcmd_payload_ba[5:3]) | (bankmachine2_TMRcmd_payload_ba[5:3] & bankmachine2_TMRcmd_payload_ba[8:6])) | (bankmachine2_TMRcmd_payload_ba[2:0] & bankmachine2_TMRcmd_payload_ba[8:6]));
assign endpoint2_payload_ba = control26;
assign control27 = (((bankmachine2_TMRcmd_payload_cas[0] & bankmachine2_TMRcmd_payload_cas[1]) | (bankmachine2_TMRcmd_payload_cas[1] & bankmachine2_TMRcmd_payload_cas[2])) | (bankmachine2_TMRcmd_payload_cas[0] & bankmachine2_TMRcmd_payload_cas[2]));
assign endpoint2_payload_cas = control27;
assign control28 = (((bankmachine2_TMRcmd_payload_ras[0] & bankmachine2_TMRcmd_payload_ras[1]) | (bankmachine2_TMRcmd_payload_ras[1] & bankmachine2_TMRcmd_payload_ras[2])) | (bankmachine2_TMRcmd_payload_ras[0] & bankmachine2_TMRcmd_payload_ras[2]));
assign endpoint2_payload_ras = control28;
assign control29 = (((bankmachine2_TMRcmd_payload_we[0] & bankmachine2_TMRcmd_payload_we[1]) | (bankmachine2_TMRcmd_payload_we[1] & bankmachine2_TMRcmd_payload_we[2])) | (bankmachine2_TMRcmd_payload_we[0] & bankmachine2_TMRcmd_payload_we[2]));
assign endpoint2_payload_we = control29;
assign control30 = (((bankmachine2_TMRcmd_payload_is_cmd[0] & bankmachine2_TMRcmd_payload_is_cmd[1]) | (bankmachine2_TMRcmd_payload_is_cmd[1] & bankmachine2_TMRcmd_payload_is_cmd[2])) | (bankmachine2_TMRcmd_payload_is_cmd[0] & bankmachine2_TMRcmd_payload_is_cmd[2]));
assign endpoint2_payload_is_cmd = control30;
assign control31 = (((bankmachine2_TMRcmd_payload_is_read[0] & bankmachine2_TMRcmd_payload_is_read[1]) | (bankmachine2_TMRcmd_payload_is_read[1] & bankmachine2_TMRcmd_payload_is_read[2])) | (bankmachine2_TMRcmd_payload_is_read[0] & bankmachine2_TMRcmd_payload_is_read[2]));
assign endpoint2_payload_is_read = control31;
assign control32 = (((bankmachine2_TMRcmd_payload_is_write[0] & bankmachine2_TMRcmd_payload_is_write[1]) | (bankmachine2_TMRcmd_payload_is_write[1] & bankmachine2_TMRcmd_payload_is_write[2])) | (bankmachine2_TMRcmd_payload_is_write[0] & bankmachine2_TMRcmd_payload_is_write[2]));
assign endpoint2_payload_is_write = control32;
assign control33 = (((bankmachine3_TMRcmd_valid[0] & bankmachine3_TMRcmd_valid[1]) | (bankmachine3_TMRcmd_valid[1] & bankmachine3_TMRcmd_valid[2])) | (bankmachine3_TMRcmd_valid[0] & bankmachine3_TMRcmd_valid[2]));
assign endpoint3_valid = control33;
assign control34 = (((bankmachine3_TMRcmd_last[0] & bankmachine3_TMRcmd_last[1]) | (bankmachine3_TMRcmd_last[1] & bankmachine3_TMRcmd_last[2])) | (bankmachine3_TMRcmd_last[0] & bankmachine3_TMRcmd_last[2]));
assign endpoint3_last = control34;
assign bankmachine3_TMRcmd_ready = {3{endpoint3_ready}};
assign control35 = (((bankmachine3_TMRcmd_first[0] & bankmachine3_TMRcmd_first[1]) | (bankmachine3_TMRcmd_first[1] & bankmachine3_TMRcmd_first[2])) | (bankmachine3_TMRcmd_first[0] & bankmachine3_TMRcmd_first[2]));
assign endpoint3_first = control35;
assign control36 = (((bankmachine3_TMRcmd_payload_a[13:0] & bankmachine3_TMRcmd_payload_a[27:14]) | (bankmachine3_TMRcmd_payload_a[27:14] & bankmachine3_TMRcmd_payload_a[41:28])) | (bankmachine3_TMRcmd_payload_a[13:0] & bankmachine3_TMRcmd_payload_a[41:28]));
assign endpoint3_payload_a = control36;
assign control37 = (((bankmachine3_TMRcmd_payload_ba[2:0] & bankmachine3_TMRcmd_payload_ba[5:3]) | (bankmachine3_TMRcmd_payload_ba[5:3] & bankmachine3_TMRcmd_payload_ba[8:6])) | (bankmachine3_TMRcmd_payload_ba[2:0] & bankmachine3_TMRcmd_payload_ba[8:6]));
assign endpoint3_payload_ba = control37;
assign control38 = (((bankmachine3_TMRcmd_payload_cas[0] & bankmachine3_TMRcmd_payload_cas[1]) | (bankmachine3_TMRcmd_payload_cas[1] & bankmachine3_TMRcmd_payload_cas[2])) | (bankmachine3_TMRcmd_payload_cas[0] & bankmachine3_TMRcmd_payload_cas[2]));
assign endpoint3_payload_cas = control38;
assign control39 = (((bankmachine3_TMRcmd_payload_ras[0] & bankmachine3_TMRcmd_payload_ras[1]) | (bankmachine3_TMRcmd_payload_ras[1] & bankmachine3_TMRcmd_payload_ras[2])) | (bankmachine3_TMRcmd_payload_ras[0] & bankmachine3_TMRcmd_payload_ras[2]));
assign endpoint3_payload_ras = control39;
assign control40 = (((bankmachine3_TMRcmd_payload_we[0] & bankmachine3_TMRcmd_payload_we[1]) | (bankmachine3_TMRcmd_payload_we[1] & bankmachine3_TMRcmd_payload_we[2])) | (bankmachine3_TMRcmd_payload_we[0] & bankmachine3_TMRcmd_payload_we[2]));
assign endpoint3_payload_we = control40;
assign control41 = (((bankmachine3_TMRcmd_payload_is_cmd[0] & bankmachine3_TMRcmd_payload_is_cmd[1]) | (bankmachine3_TMRcmd_payload_is_cmd[1] & bankmachine3_TMRcmd_payload_is_cmd[2])) | (bankmachine3_TMRcmd_payload_is_cmd[0] & bankmachine3_TMRcmd_payload_is_cmd[2]));
assign endpoint3_payload_is_cmd = control41;
assign control42 = (((bankmachine3_TMRcmd_payload_is_read[0] & bankmachine3_TMRcmd_payload_is_read[1]) | (bankmachine3_TMRcmd_payload_is_read[1] & bankmachine3_TMRcmd_payload_is_read[2])) | (bankmachine3_TMRcmd_payload_is_read[0] & bankmachine3_TMRcmd_payload_is_read[2]));
assign endpoint3_payload_is_read = control42;
assign control43 = (((bankmachine3_TMRcmd_payload_is_write[0] & bankmachine3_TMRcmd_payload_is_write[1]) | (bankmachine3_TMRcmd_payload_is_write[1] & bankmachine3_TMRcmd_payload_is_write[2])) | (bankmachine3_TMRcmd_payload_is_write[0] & bankmachine3_TMRcmd_payload_is_write[2]));
assign endpoint3_payload_is_write = control43;

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	choose_cmd_valids <= 4'd0;
	choose_cmd_valids[0] <= (endpoint0_valid & (((endpoint0_payload_is_cmd & choose_cmd_want_cmds) & ((~((endpoint0_payload_ras & (~endpoint0_payload_cas)) & (~endpoint0_payload_we))) | choose_cmd_want_activates)) | ((endpoint0_payload_is_read == choose_cmd_want_reads) & (endpoint0_payload_is_write == choose_cmd_want_writes))));
	choose_cmd_valids[1] <= (endpoint1_valid & (((endpoint1_payload_is_cmd & choose_cmd_want_cmds) & ((~((endpoint1_payload_ras & (~endpoint1_payload_cas)) & (~endpoint1_payload_we))) | choose_cmd_want_activates)) | ((endpoint1_payload_is_read == choose_cmd_want_reads) & (endpoint1_payload_is_write == choose_cmd_want_writes))));
	choose_cmd_valids[2] <= (endpoint2_valid & (((endpoint2_payload_is_cmd & choose_cmd_want_cmds) & ((~((endpoint2_payload_ras & (~endpoint2_payload_cas)) & (~endpoint2_payload_we))) | choose_cmd_want_activates)) | ((endpoint2_payload_is_read == choose_cmd_want_reads) & (endpoint2_payload_is_write == choose_cmd_want_writes))));
	choose_cmd_valids[3] <= (endpoint3_valid & (((endpoint3_payload_is_cmd & choose_cmd_want_cmds) & ((~((endpoint3_payload_ras & (~endpoint3_payload_cas)) & (~endpoint3_payload_we))) | choose_cmd_want_activates)) | ((endpoint3_payload_is_read == choose_cmd_want_reads) & (endpoint3_payload_is_write == choose_cmd_want_writes))));
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end
assign choose_cmd_request = choose_cmd_valids;
assign choose_cmd_cmd_valid = rhs_array_muxed0;
assign choose_cmd_cmd_payload_a = rhs_array_muxed1;
assign choose_cmd_cmd_payload_ba = rhs_array_muxed2;
assign choose_cmd_cmd_payload_is_read = rhs_array_muxed3;
assign choose_cmd_cmd_payload_is_write = rhs_array_muxed4;
assign choose_cmd_cmd_payload_is_cmd = rhs_array_muxed5;

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	choose_cmd_cmd_payload_cas <= 1'd0;
	if (choose_cmd_cmd_valid) begin
		choose_cmd_cmd_payload_cas <= t_array_muxed0;
	end
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	choose_cmd_cmd_payload_ras <= 1'd0;
	if (choose_cmd_cmd_valid) begin
		choose_cmd_cmd_payload_ras <= t_array_muxed1;
	end
// synthesis translate_off
	dummy_d_2 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_3;
// synthesis translate_on
always @(*) begin
	choose_cmd_cmd_payload_we <= 1'd0;
	if (choose_cmd_cmd_valid) begin
		choose_cmd_cmd_payload_we <= t_array_muxed2;
	end
// synthesis translate_off
	dummy_d_3 <= dummy_s;
// synthesis translate_on
end
assign choose_cmd_ce = (choose_cmd_cmd_ready | (~choose_cmd_cmd_valid));

// synthesis translate_off
reg dummy_d_4;
// synthesis translate_on
always @(*) begin
	choose_req_valids <= 4'd0;
	choose_req_valids[0] <= (endpoint0_valid & (((endpoint0_payload_is_cmd & choose_req_want_cmds) & ((~((endpoint0_payload_ras & (~endpoint0_payload_cas)) & (~endpoint0_payload_we))) | choose_req_want_activates)) | ((endpoint0_payload_is_read == choose_req_want_reads) & (endpoint0_payload_is_write == choose_req_want_writes))));
	choose_req_valids[1] <= (endpoint1_valid & (((endpoint1_payload_is_cmd & choose_req_want_cmds) & ((~((endpoint1_payload_ras & (~endpoint1_payload_cas)) & (~endpoint1_payload_we))) | choose_req_want_activates)) | ((endpoint1_payload_is_read == choose_req_want_reads) & (endpoint1_payload_is_write == choose_req_want_writes))));
	choose_req_valids[2] <= (endpoint2_valid & (((endpoint2_payload_is_cmd & choose_req_want_cmds) & ((~((endpoint2_payload_ras & (~endpoint2_payload_cas)) & (~endpoint2_payload_we))) | choose_req_want_activates)) | ((endpoint2_payload_is_read == choose_req_want_reads) & (endpoint2_payload_is_write == choose_req_want_writes))));
	choose_req_valids[3] <= (endpoint3_valid & (((endpoint3_payload_is_cmd & choose_req_want_cmds) & ((~((endpoint3_payload_ras & (~endpoint3_payload_cas)) & (~endpoint3_payload_we))) | choose_req_want_activates)) | ((endpoint3_payload_is_read == choose_req_want_reads) & (endpoint3_payload_is_write == choose_req_want_writes))));
// synthesis translate_off
	dummy_d_4 <= dummy_s;
// synthesis translate_on
end
assign choose_req_request = choose_req_valids;
assign choose_req_cmd_valid = rhs_array_muxed6;
assign choose_req_cmd_payload_a = rhs_array_muxed7;
assign choose_req_cmd_payload_ba = rhs_array_muxed8;
assign choose_req_cmd_payload_is_read = rhs_array_muxed9;
assign choose_req_cmd_payload_is_write = rhs_array_muxed10;
assign choose_req_cmd_payload_is_cmd = rhs_array_muxed11;

// synthesis translate_off
reg dummy_d_5;
// synthesis translate_on
always @(*) begin
	choose_req_cmd_payload_cas <= 1'd0;
	if (choose_req_cmd_valid) begin
		choose_req_cmd_payload_cas <= t_array_muxed3;
	end
// synthesis translate_off
	dummy_d_5 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_6;
// synthesis translate_on
always @(*) begin
	choose_req_cmd_payload_ras <= 1'd0;
	if (choose_req_cmd_valid) begin
		choose_req_cmd_payload_ras <= t_array_muxed4;
	end
// synthesis translate_off
	dummy_d_6 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_7;
// synthesis translate_on
always @(*) begin
	choose_req_cmd_payload_we <= 1'd0;
	if (choose_req_cmd_valid) begin
		choose_req_cmd_payload_we <= t_array_muxed5;
	end
// synthesis translate_off
	dummy_d_7 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_8;
// synthesis translate_on
always @(*) begin
	endpoint0_ready <= 1'd0;
	if (((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & (choose_cmd_grant == 1'd0))) begin
		endpoint0_ready <= 1'd1;
	end
	if (((choose_req_cmd_valid & choose_req_cmd_ready) & (choose_req_grant == 1'd0))) begin
		endpoint0_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_8 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_9;
// synthesis translate_on
always @(*) begin
	endpoint1_ready <= 1'd0;
	if (((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & (choose_cmd_grant == 1'd1))) begin
		endpoint1_ready <= 1'd1;
	end
	if (((choose_req_cmd_valid & choose_req_cmd_ready) & (choose_req_grant == 1'd1))) begin
		endpoint1_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_9 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_10;
// synthesis translate_on
always @(*) begin
	endpoint2_ready <= 1'd0;
	if (((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & (choose_cmd_grant == 2'd2))) begin
		endpoint2_ready <= 1'd1;
	end
	if (((choose_req_cmd_valid & choose_req_cmd_ready) & (choose_req_grant == 2'd2))) begin
		endpoint2_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_10 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_11;
// synthesis translate_on
always @(*) begin
	endpoint3_ready <= 1'd0;
	if (((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & (choose_cmd_grant == 2'd3))) begin
		endpoint3_ready <= 1'd1;
	end
	if (((choose_req_cmd_valid & choose_req_cmd_ready) & (choose_req_grant == 2'd3))) begin
		endpoint3_ready <= 1'd1;
	end
// synthesis translate_off
	dummy_d_11 <= dummy_s;
// synthesis translate_on
end
assign choose_req_ce = (choose_req_cmd_ready | (~choose_req_cmd_valid));
assign control44 = (((mock_multiplexer_TMRcmd_valid[0] & mock_multiplexer_TMRcmd_valid[1]) | (mock_multiplexer_TMRcmd_valid[1] & mock_multiplexer_TMRcmd_valid[2])) | (mock_multiplexer_TMRcmd_valid[0] & mock_multiplexer_TMRcmd_valid[2]));
assign refreshCmd_valid = control44;
assign control45 = (((mock_multiplexer_TMRcmd_last[0] & mock_multiplexer_TMRcmd_last[1]) | (mock_multiplexer_TMRcmd_last[1] & mock_multiplexer_TMRcmd_last[2])) | (mock_multiplexer_TMRcmd_last[0] & mock_multiplexer_TMRcmd_last[2]));
assign refreshCmd_last = control45;
assign mock_multiplexer_TMRcmd_ready = {3{refreshCmd_ready}};
assign control46 = (((mock_multiplexer_TMRcmd_first[0] & mock_multiplexer_TMRcmd_first[1]) | (mock_multiplexer_TMRcmd_first[1] & mock_multiplexer_TMRcmd_first[2])) | (mock_multiplexer_TMRcmd_first[0] & mock_multiplexer_TMRcmd_first[2]));
assign refreshCmd_first = control46;
assign control47 = (((mock_multiplexer_TMRcmd_payload_a[13:0] & mock_multiplexer_TMRcmd_payload_a[27:14]) | (mock_multiplexer_TMRcmd_payload_a[27:14] & mock_multiplexer_TMRcmd_payload_a[41:28])) | (mock_multiplexer_TMRcmd_payload_a[13:0] & mock_multiplexer_TMRcmd_payload_a[41:28]));
assign refreshCmd_payload_a = control47;
assign control48 = (((mock_multiplexer_TMRcmd_payload_ba[2:0] & mock_multiplexer_TMRcmd_payload_ba[5:3]) | (mock_multiplexer_TMRcmd_payload_ba[5:3] & mock_multiplexer_TMRcmd_payload_ba[8:6])) | (mock_multiplexer_TMRcmd_payload_ba[2:0] & mock_multiplexer_TMRcmd_payload_ba[8:6]));
assign refreshCmd_payload_ba = control48;
assign control49 = (((mock_multiplexer_TMRcmd_payload_cas[0] & mock_multiplexer_TMRcmd_payload_cas[1]) | (mock_multiplexer_TMRcmd_payload_cas[1] & mock_multiplexer_TMRcmd_payload_cas[2])) | (mock_multiplexer_TMRcmd_payload_cas[0] & mock_multiplexer_TMRcmd_payload_cas[2]));
assign refreshCmd_payload_cas = control49;
assign control50 = (((mock_multiplexer_TMRcmd_payload_ras[0] & mock_multiplexer_TMRcmd_payload_ras[1]) | (mock_multiplexer_TMRcmd_payload_ras[1] & mock_multiplexer_TMRcmd_payload_ras[2])) | (mock_multiplexer_TMRcmd_payload_ras[0] & mock_multiplexer_TMRcmd_payload_ras[2]));
assign refreshCmd_payload_ras = control50;
assign control51 = (((mock_multiplexer_TMRcmd_payload_we[0] & mock_multiplexer_TMRcmd_payload_we[1]) | (mock_multiplexer_TMRcmd_payload_we[1] & mock_multiplexer_TMRcmd_payload_we[2])) | (mock_multiplexer_TMRcmd_payload_we[0] & mock_multiplexer_TMRcmd_payload_we[2]));
assign refreshCmd_payload_we = control51;
assign control52 = (((mock_multiplexer_TMRcmd_payload_is_cmd[0] & mock_multiplexer_TMRcmd_payload_is_cmd[1]) | (mock_multiplexer_TMRcmd_payload_is_cmd[1] & mock_multiplexer_TMRcmd_payload_is_cmd[2])) | (mock_multiplexer_TMRcmd_payload_is_cmd[0] & mock_multiplexer_TMRcmd_payload_is_cmd[2]));
assign refreshCmd_payload_is_cmd = control52;
assign control53 = (((mock_multiplexer_TMRcmd_payload_is_read[0] & mock_multiplexer_TMRcmd_payload_is_read[1]) | (mock_multiplexer_TMRcmd_payload_is_read[1] & mock_multiplexer_TMRcmd_payload_is_read[2])) | (mock_multiplexer_TMRcmd_payload_is_read[0] & mock_multiplexer_TMRcmd_payload_is_read[2]));
assign refreshCmd_payload_is_read = control53;
assign control54 = (((mock_multiplexer_TMRcmd_payload_is_write[0] & mock_multiplexer_TMRcmd_payload_is_write[1]) | (mock_multiplexer_TMRcmd_payload_is_write[1] & mock_multiplexer_TMRcmd_payload_is_write[2])) | (mock_multiplexer_TMRcmd_payload_is_write[0] & mock_multiplexer_TMRcmd_payload_is_write[2]));
assign refreshCmd_payload_is_write = control54;
assign p0_reset_n = 1'd1;
assign p0_cke = {1{steerer4}};
assign p0_odt = {1{steerer5}};
assign p1_reset_n = 1'd1;
assign p1_cke = {1{steerer6}};
assign p1_odt = {1{steerer7}};
assign p2_reset_n = 1'd1;
assign p2_cke = {1{steerer8}};
assign p2_odt = {1{steerer9}};
assign p3_reset_n = 1'd1;
assign p3_cke = {1{steerer10}};
assign p3_odt = {1{steerer11}};
assign tfawcon_count = ((((tfawcon_window[0] + tfawcon_window[1]) + tfawcon_window[2]) + tfawcon_window[3]) + tfawcon_window[4]);
assign rdata = {3{{p3_rddata, p2_rddata, p1_rddata, p0_rddata}}};
assign control55 = (((wdata[255:0] & wdata[511:256]) | (wdata[511:256] & wdata[767:512])) | (wdata[255:0] & wdata[767:512]));
assign {p3_wrdata, p2_wrdata, p1_wrdata, p0_wrdata} = control55;
assign control56 = (((slice_proxy0[31:0] & slice_proxy1[63:32]) | (slice_proxy2[63:32] & slice_proxy3[95:64])) | (slice_proxy4[31:0] & slice_proxy5[95:64]));
assign {p3_wrdata_mask, p2_wrdata_mask, p1_wrdata_mask, p0_wrdata_mask} = control56;

// synthesis translate_off
reg dummy_d_12;
// synthesis translate_on
always @(*) begin
	choose_cmd_want_activates <= 1'd0;
	choose_cmd_cmd_ready <= 1'd0;
	choose_req_want_reads <= 1'd0;
	choose_req_want_writes <= 1'd0;
	choose_req_cmd_ready <= 1'd0;
	refreshCmd_ready <= 1'd0;
	steerer0 <= 2'd0;
	steerer1 <= 2'd0;
	steerer2 <= 2'd0;
	steerer3 <= 2'd0;
	en0 <= 1'd0;
	en1 <= 1'd0;
	next_state <= 4'd0;
	next_state <= state;
	case (state)
		1'd1: begin
			en1 <= 1'd1;
			choose_req_want_writes <= 1'd1;
			if (1'd0) begin
				choose_req_cmd_ready <= (cas_allowed & ((~((choose_req_cmd_payload_ras & (~choose_req_cmd_payload_cas)) & (~choose_req_cmd_payload_we))) | ras_allowed));
			end else begin
				choose_cmd_want_activates <= ras_allowed;
				choose_cmd_cmd_ready <= ((~((choose_cmd_cmd_payload_ras & (~choose_cmd_cmd_payload_cas)) & (~choose_cmd_cmd_payload_we))) | ras_allowed);
				choose_req_cmd_ready <= cas_allowed;
			end
			steerer0 <= 1'd0;
			if ((mock_multiplexer_wrphase_storage == 1'd0)) begin
				steerer0 <= 2'd2;
			end
			if ((wrcmdphase == 1'd0)) begin
				steerer0 <= 1'd1;
			end
			steerer1 <= 1'd0;
			if ((mock_multiplexer_wrphase_storage == 1'd1)) begin
				steerer1 <= 2'd2;
			end
			if ((wrcmdphase == 1'd1)) begin
				steerer1 <= 1'd1;
			end
			steerer2 <= 1'd0;
			if ((mock_multiplexer_wrphase_storage == 2'd2)) begin
				steerer2 <= 2'd2;
			end
			if ((wrcmdphase == 2'd2)) begin
				steerer2 <= 1'd1;
			end
			steerer3 <= 1'd0;
			if ((mock_multiplexer_wrphase_storage == 2'd3)) begin
				steerer3 <= 2'd2;
			end
			if ((wrcmdphase == 2'd3)) begin
				steerer3 <= 1'd1;
			end
			if (read_available) begin
				if (((~write_available) | max_time1)) begin
					next_state <= 2'd3;
				end
			end
			if (go_to_refresh) begin
				next_state <= 2'd2;
			end
		end
		2'd2: begin
			steerer0 <= 2'd3;
			refreshCmd_ready <= 1'd1;
			if (refreshCmd_last) begin
				next_state <= 1'd0;
			end
		end
		2'd3: begin
			if (twtrcon_ready) begin
				next_state <= 1'd0;
			end
		end
		3'd4: begin
			next_state <= 3'd5;
		end
		3'd5: begin
			next_state <= 3'd6;
		end
		3'd6: begin
			next_state <= 3'd7;
		end
		3'd7: begin
			next_state <= 4'd8;
		end
		4'd8: begin
			next_state <= 4'd9;
		end
		4'd9: begin
			next_state <= 4'd10;
		end
		4'd10: begin
			next_state <= 1'd1;
		end
		default: begin
			en0 <= 1'd1;
			choose_req_want_reads <= 1'd1;
			if (1'd0) begin
				choose_req_cmd_ready <= (cas_allowed & ((~((choose_req_cmd_payload_ras & (~choose_req_cmd_payload_cas)) & (~choose_req_cmd_payload_we))) | ras_allowed));
			end else begin
				choose_cmd_want_activates <= ras_allowed;
				choose_cmd_cmd_ready <= ((~((choose_cmd_cmd_payload_ras & (~choose_cmd_cmd_payload_cas)) & (~choose_cmd_cmd_payload_we))) | ras_allowed);
				choose_req_cmd_ready <= cas_allowed;
			end
			steerer0 <= 1'd0;
			if ((mock_multiplexer_rdphase_storage == 1'd0)) begin
				steerer0 <= 2'd2;
			end
			if ((rdcmdphase == 1'd0)) begin
				steerer0 <= 1'd1;
			end
			steerer1 <= 1'd0;
			if ((mock_multiplexer_rdphase_storage == 1'd1)) begin
				steerer1 <= 2'd2;
			end
			if ((rdcmdphase == 1'd1)) begin
				steerer1 <= 1'd1;
			end
			steerer2 <= 1'd0;
			if ((mock_multiplexer_rdphase_storage == 2'd2)) begin
				steerer2 <= 2'd2;
			end
			if ((rdcmdphase == 2'd2)) begin
				steerer2 <= 1'd1;
			end
			steerer3 <= 1'd0;
			if ((mock_multiplexer_rdphase_storage == 2'd3)) begin
				steerer3 <= 2'd2;
			end
			if ((rdcmdphase == 2'd3)) begin
				steerer3 <= 1'd1;
			end
			if (write_available) begin
				if (((~read_available) | max_time0)) begin
					next_state <= 3'd4;
				end
			end
			if (go_to_refresh) begin
				next_state <= 2'd2;
			end
		end
	endcase
// synthesis translate_off
	dummy_d_12 <= dummy_s;
// synthesis translate_on
end
assign slice_proxy0 = (~wdata_we);
assign slice_proxy1 = (~wdata_we);
assign slice_proxy2 = (~wdata_we);
assign slice_proxy3 = (~wdata_we);
assign slice_proxy4 = (~wdata_we);
assign slice_proxy5 = (~wdata_we);

// synthesis translate_off
reg dummy_d_13;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed0 <= 1'd0;
	case (choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed0 <= choose_cmd_valids[0];
		end
		1'd1: begin
			rhs_array_muxed0 <= choose_cmd_valids[1];
		end
		2'd2: begin
			rhs_array_muxed0 <= choose_cmd_valids[2];
		end
		default: begin
			rhs_array_muxed0 <= choose_cmd_valids[3];
		end
	endcase
// synthesis translate_off
	dummy_d_13 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_14;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed1 <= 14'd0;
	case (choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed1 <= endpoint0_payload_a;
		end
		1'd1: begin
			rhs_array_muxed1 <= endpoint1_payload_a;
		end
		2'd2: begin
			rhs_array_muxed1 <= endpoint2_payload_a;
		end
		default: begin
			rhs_array_muxed1 <= endpoint3_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_14 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_15;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed2 <= 3'd0;
	case (choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed2 <= endpoint0_payload_ba;
		end
		1'd1: begin
			rhs_array_muxed2 <= endpoint1_payload_ba;
		end
		2'd2: begin
			rhs_array_muxed2 <= endpoint2_payload_ba;
		end
		default: begin
			rhs_array_muxed2 <= endpoint3_payload_ba;
		end
	endcase
// synthesis translate_off
	dummy_d_15 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_16;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed3 <= 1'd0;
	case (choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed3 <= endpoint0_payload_is_read;
		end
		1'd1: begin
			rhs_array_muxed3 <= endpoint1_payload_is_read;
		end
		2'd2: begin
			rhs_array_muxed3 <= endpoint2_payload_is_read;
		end
		default: begin
			rhs_array_muxed3 <= endpoint3_payload_is_read;
		end
	endcase
// synthesis translate_off
	dummy_d_16 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_17;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed4 <= 1'd0;
	case (choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed4 <= endpoint0_payload_is_write;
		end
		1'd1: begin
			rhs_array_muxed4 <= endpoint1_payload_is_write;
		end
		2'd2: begin
			rhs_array_muxed4 <= endpoint2_payload_is_write;
		end
		default: begin
			rhs_array_muxed4 <= endpoint3_payload_is_write;
		end
	endcase
// synthesis translate_off
	dummy_d_17 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_18;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed5 <= 1'd0;
	case (choose_cmd_grant)
		1'd0: begin
			rhs_array_muxed5 <= endpoint0_payload_is_cmd;
		end
		1'd1: begin
			rhs_array_muxed5 <= endpoint1_payload_is_cmd;
		end
		2'd2: begin
			rhs_array_muxed5 <= endpoint2_payload_is_cmd;
		end
		default: begin
			rhs_array_muxed5 <= endpoint3_payload_is_cmd;
		end
	endcase
// synthesis translate_off
	dummy_d_18 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_19;
// synthesis translate_on
always @(*) begin
	t_array_muxed0 <= 1'd0;
	case (choose_cmd_grant)
		1'd0: begin
			t_array_muxed0 <= endpoint0_payload_cas;
		end
		1'd1: begin
			t_array_muxed0 <= endpoint1_payload_cas;
		end
		2'd2: begin
			t_array_muxed0 <= endpoint2_payload_cas;
		end
		default: begin
			t_array_muxed0 <= endpoint3_payload_cas;
		end
	endcase
// synthesis translate_off
	dummy_d_19 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_20;
// synthesis translate_on
always @(*) begin
	t_array_muxed1 <= 1'd0;
	case (choose_cmd_grant)
		1'd0: begin
			t_array_muxed1 <= endpoint0_payload_ras;
		end
		1'd1: begin
			t_array_muxed1 <= endpoint1_payload_ras;
		end
		2'd2: begin
			t_array_muxed1 <= endpoint2_payload_ras;
		end
		default: begin
			t_array_muxed1 <= endpoint3_payload_ras;
		end
	endcase
// synthesis translate_off
	dummy_d_20 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_21;
// synthesis translate_on
always @(*) begin
	t_array_muxed2 <= 1'd0;
	case (choose_cmd_grant)
		1'd0: begin
			t_array_muxed2 <= endpoint0_payload_we;
		end
		1'd1: begin
			t_array_muxed2 <= endpoint1_payload_we;
		end
		2'd2: begin
			t_array_muxed2 <= endpoint2_payload_we;
		end
		default: begin
			t_array_muxed2 <= endpoint3_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_21 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_22;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed6 <= 1'd0;
	case (choose_req_grant)
		1'd0: begin
			rhs_array_muxed6 <= choose_req_valids[0];
		end
		1'd1: begin
			rhs_array_muxed6 <= choose_req_valids[1];
		end
		2'd2: begin
			rhs_array_muxed6 <= choose_req_valids[2];
		end
		default: begin
			rhs_array_muxed6 <= choose_req_valids[3];
		end
	endcase
// synthesis translate_off
	dummy_d_22 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_23;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed7 <= 14'd0;
	case (choose_req_grant)
		1'd0: begin
			rhs_array_muxed7 <= endpoint0_payload_a;
		end
		1'd1: begin
			rhs_array_muxed7 <= endpoint1_payload_a;
		end
		2'd2: begin
			rhs_array_muxed7 <= endpoint2_payload_a;
		end
		default: begin
			rhs_array_muxed7 <= endpoint3_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_23 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_24;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed8 <= 3'd0;
	case (choose_req_grant)
		1'd0: begin
			rhs_array_muxed8 <= endpoint0_payload_ba;
		end
		1'd1: begin
			rhs_array_muxed8 <= endpoint1_payload_ba;
		end
		2'd2: begin
			rhs_array_muxed8 <= endpoint2_payload_ba;
		end
		default: begin
			rhs_array_muxed8 <= endpoint3_payload_ba;
		end
	endcase
// synthesis translate_off
	dummy_d_24 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_25;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed9 <= 1'd0;
	case (choose_req_grant)
		1'd0: begin
			rhs_array_muxed9 <= endpoint0_payload_is_read;
		end
		1'd1: begin
			rhs_array_muxed9 <= endpoint1_payload_is_read;
		end
		2'd2: begin
			rhs_array_muxed9 <= endpoint2_payload_is_read;
		end
		default: begin
			rhs_array_muxed9 <= endpoint3_payload_is_read;
		end
	endcase
// synthesis translate_off
	dummy_d_25 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_26;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed10 <= 1'd0;
	case (choose_req_grant)
		1'd0: begin
			rhs_array_muxed10 <= endpoint0_payload_is_write;
		end
		1'd1: begin
			rhs_array_muxed10 <= endpoint1_payload_is_write;
		end
		2'd2: begin
			rhs_array_muxed10 <= endpoint2_payload_is_write;
		end
		default: begin
			rhs_array_muxed10 <= endpoint3_payload_is_write;
		end
	endcase
// synthesis translate_off
	dummy_d_26 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_27;
// synthesis translate_on
always @(*) begin
	rhs_array_muxed11 <= 1'd0;
	case (choose_req_grant)
		1'd0: begin
			rhs_array_muxed11 <= endpoint0_payload_is_cmd;
		end
		1'd1: begin
			rhs_array_muxed11 <= endpoint1_payload_is_cmd;
		end
		2'd2: begin
			rhs_array_muxed11 <= endpoint2_payload_is_cmd;
		end
		default: begin
			rhs_array_muxed11 <= endpoint3_payload_is_cmd;
		end
	endcase
// synthesis translate_off
	dummy_d_27 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_28;
// synthesis translate_on
always @(*) begin
	t_array_muxed3 <= 1'd0;
	case (choose_req_grant)
		1'd0: begin
			t_array_muxed3 <= endpoint0_payload_cas;
		end
		1'd1: begin
			t_array_muxed3 <= endpoint1_payload_cas;
		end
		2'd2: begin
			t_array_muxed3 <= endpoint2_payload_cas;
		end
		default: begin
			t_array_muxed3 <= endpoint3_payload_cas;
		end
	endcase
// synthesis translate_off
	dummy_d_28 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_29;
// synthesis translate_on
always @(*) begin
	t_array_muxed4 <= 1'd0;
	case (choose_req_grant)
		1'd0: begin
			t_array_muxed4 <= endpoint0_payload_ras;
		end
		1'd1: begin
			t_array_muxed4 <= endpoint1_payload_ras;
		end
		2'd2: begin
			t_array_muxed4 <= endpoint2_payload_ras;
		end
		default: begin
			t_array_muxed4 <= endpoint3_payload_ras;
		end
	endcase
// synthesis translate_off
	dummy_d_29 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_30;
// synthesis translate_on
always @(*) begin
	t_array_muxed5 <= 1'd0;
	case (choose_req_grant)
		1'd0: begin
			t_array_muxed5 <= endpoint0_payload_we;
		end
		1'd1: begin
			t_array_muxed5 <= endpoint1_payload_we;
		end
		2'd2: begin
			t_array_muxed5 <= endpoint2_payload_we;
		end
		default: begin
			t_array_muxed5 <= endpoint3_payload_we;
		end
	endcase
// synthesis translate_off
	dummy_d_30 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_31;
// synthesis translate_on
always @(*) begin
	array_muxed0 <= 3'd0;
	case (steerer0)
		1'd0: begin
			array_muxed0 <= nop_ba[1:0];
		end
		1'd1: begin
			array_muxed0 <= choose_cmd_cmd_payload_ba[2:0];
		end
		2'd2: begin
			array_muxed0 <= choose_req_cmd_payload_ba[2:0];
		end
		default: begin
			array_muxed0 <= refreshCmd_payload_ba[2:0];
		end
	endcase
// synthesis translate_off
	dummy_d_31 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_32;
// synthesis translate_on
always @(*) begin
	array_muxed1 <= 14'd0;
	case (steerer0)
		1'd0: begin
			array_muxed1 <= nop_a;
		end
		1'd1: begin
			array_muxed1 <= choose_cmd_cmd_payload_a;
		end
		2'd2: begin
			array_muxed1 <= choose_req_cmd_payload_a;
		end
		default: begin
			array_muxed1 <= refreshCmd_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_32 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_33;
// synthesis translate_on
always @(*) begin
	array_muxed2 <= 1'd0;
	case (steerer0)
		1'd0: begin
			array_muxed2 <= 1'd0;
		end
		1'd1: begin
			array_muxed2 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_cas);
		end
		2'd2: begin
			array_muxed2 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_cas);
		end
		default: begin
			array_muxed2 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_cas);
		end
	endcase
// synthesis translate_off
	dummy_d_33 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_34;
// synthesis translate_on
always @(*) begin
	array_muxed3 <= 1'd0;
	case (steerer0)
		1'd0: begin
			array_muxed3 <= 1'd0;
		end
		1'd1: begin
			array_muxed3 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_ras);
		end
		2'd2: begin
			array_muxed3 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_ras);
		end
		default: begin
			array_muxed3 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_ras);
		end
	endcase
// synthesis translate_off
	dummy_d_34 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_35;
// synthesis translate_on
always @(*) begin
	array_muxed4 <= 1'd0;
	case (steerer0)
		1'd0: begin
			array_muxed4 <= 1'd0;
		end
		1'd1: begin
			array_muxed4 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_we);
		end
		2'd2: begin
			array_muxed4 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_we);
		end
		default: begin
			array_muxed4 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_we);
		end
	endcase
// synthesis translate_off
	dummy_d_35 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_36;
// synthesis translate_on
always @(*) begin
	array_muxed5 <= 1'd0;
	case (steerer0)
		1'd0: begin
			array_muxed5 <= 1'd0;
		end
		1'd1: begin
			array_muxed5 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_is_read);
		end
		2'd2: begin
			array_muxed5 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_read);
		end
		default: begin
			array_muxed5 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_is_read);
		end
	endcase
// synthesis translate_off
	dummy_d_36 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_37;
// synthesis translate_on
always @(*) begin
	array_muxed6 <= 1'd0;
	case (steerer0)
		1'd0: begin
			array_muxed6 <= 1'd0;
		end
		1'd1: begin
			array_muxed6 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_is_write);
		end
		2'd2: begin
			array_muxed6 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_write);
		end
		default: begin
			array_muxed6 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_is_write);
		end
	endcase
// synthesis translate_off
	dummy_d_37 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_38;
// synthesis translate_on
always @(*) begin
	array_muxed7 <= 3'd0;
	case (steerer1)
		1'd0: begin
			array_muxed7 <= nop_ba[1:0];
		end
		1'd1: begin
			array_muxed7 <= choose_cmd_cmd_payload_ba[2:0];
		end
		2'd2: begin
			array_muxed7 <= choose_req_cmd_payload_ba[2:0];
		end
		default: begin
			array_muxed7 <= refreshCmd_payload_ba[2:0];
		end
	endcase
// synthesis translate_off
	dummy_d_38 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_39;
// synthesis translate_on
always @(*) begin
	array_muxed8 <= 14'd0;
	case (steerer1)
		1'd0: begin
			array_muxed8 <= nop_a;
		end
		1'd1: begin
			array_muxed8 <= choose_cmd_cmd_payload_a;
		end
		2'd2: begin
			array_muxed8 <= choose_req_cmd_payload_a;
		end
		default: begin
			array_muxed8 <= refreshCmd_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_39 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_40;
// synthesis translate_on
always @(*) begin
	array_muxed9 <= 1'd0;
	case (steerer1)
		1'd0: begin
			array_muxed9 <= 1'd0;
		end
		1'd1: begin
			array_muxed9 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_cas);
		end
		2'd2: begin
			array_muxed9 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_cas);
		end
		default: begin
			array_muxed9 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_cas);
		end
	endcase
// synthesis translate_off
	dummy_d_40 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_41;
// synthesis translate_on
always @(*) begin
	array_muxed10 <= 1'd0;
	case (steerer1)
		1'd0: begin
			array_muxed10 <= 1'd0;
		end
		1'd1: begin
			array_muxed10 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_ras);
		end
		2'd2: begin
			array_muxed10 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_ras);
		end
		default: begin
			array_muxed10 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_ras);
		end
	endcase
// synthesis translate_off
	dummy_d_41 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_42;
// synthesis translate_on
always @(*) begin
	array_muxed11 <= 1'd0;
	case (steerer1)
		1'd0: begin
			array_muxed11 <= 1'd0;
		end
		1'd1: begin
			array_muxed11 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_we);
		end
		2'd2: begin
			array_muxed11 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_we);
		end
		default: begin
			array_muxed11 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_we);
		end
	endcase
// synthesis translate_off
	dummy_d_42 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_43;
// synthesis translate_on
always @(*) begin
	array_muxed12 <= 1'd0;
	case (steerer1)
		1'd0: begin
			array_muxed12 <= 1'd0;
		end
		1'd1: begin
			array_muxed12 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_is_read);
		end
		2'd2: begin
			array_muxed12 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_read);
		end
		default: begin
			array_muxed12 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_is_read);
		end
	endcase
// synthesis translate_off
	dummy_d_43 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_44;
// synthesis translate_on
always @(*) begin
	array_muxed13 <= 1'd0;
	case (steerer1)
		1'd0: begin
			array_muxed13 <= 1'd0;
		end
		1'd1: begin
			array_muxed13 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_is_write);
		end
		2'd2: begin
			array_muxed13 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_write);
		end
		default: begin
			array_muxed13 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_is_write);
		end
	endcase
// synthesis translate_off
	dummy_d_44 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_45;
// synthesis translate_on
always @(*) begin
	array_muxed14 <= 3'd0;
	case (steerer2)
		1'd0: begin
			array_muxed14 <= nop_ba[1:0];
		end
		1'd1: begin
			array_muxed14 <= choose_cmd_cmd_payload_ba[2:0];
		end
		2'd2: begin
			array_muxed14 <= choose_req_cmd_payload_ba[2:0];
		end
		default: begin
			array_muxed14 <= refreshCmd_payload_ba[2:0];
		end
	endcase
// synthesis translate_off
	dummy_d_45 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_46;
// synthesis translate_on
always @(*) begin
	array_muxed15 <= 14'd0;
	case (steerer2)
		1'd0: begin
			array_muxed15 <= nop_a;
		end
		1'd1: begin
			array_muxed15 <= choose_cmd_cmd_payload_a;
		end
		2'd2: begin
			array_muxed15 <= choose_req_cmd_payload_a;
		end
		default: begin
			array_muxed15 <= refreshCmd_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_46 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_47;
// synthesis translate_on
always @(*) begin
	array_muxed16 <= 1'd0;
	case (steerer2)
		1'd0: begin
			array_muxed16 <= 1'd0;
		end
		1'd1: begin
			array_muxed16 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_cas);
		end
		2'd2: begin
			array_muxed16 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_cas);
		end
		default: begin
			array_muxed16 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_cas);
		end
	endcase
// synthesis translate_off
	dummy_d_47 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_48;
// synthesis translate_on
always @(*) begin
	array_muxed17 <= 1'd0;
	case (steerer2)
		1'd0: begin
			array_muxed17 <= 1'd0;
		end
		1'd1: begin
			array_muxed17 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_ras);
		end
		2'd2: begin
			array_muxed17 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_ras);
		end
		default: begin
			array_muxed17 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_ras);
		end
	endcase
// synthesis translate_off
	dummy_d_48 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_49;
// synthesis translate_on
always @(*) begin
	array_muxed18 <= 1'd0;
	case (steerer2)
		1'd0: begin
			array_muxed18 <= 1'd0;
		end
		1'd1: begin
			array_muxed18 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_we);
		end
		2'd2: begin
			array_muxed18 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_we);
		end
		default: begin
			array_muxed18 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_we);
		end
	endcase
// synthesis translate_off
	dummy_d_49 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_50;
// synthesis translate_on
always @(*) begin
	array_muxed19 <= 1'd0;
	case (steerer2)
		1'd0: begin
			array_muxed19 <= 1'd0;
		end
		1'd1: begin
			array_muxed19 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_is_read);
		end
		2'd2: begin
			array_muxed19 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_read);
		end
		default: begin
			array_muxed19 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_is_read);
		end
	endcase
// synthesis translate_off
	dummy_d_50 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_51;
// synthesis translate_on
always @(*) begin
	array_muxed20 <= 1'd0;
	case (steerer2)
		1'd0: begin
			array_muxed20 <= 1'd0;
		end
		1'd1: begin
			array_muxed20 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_is_write);
		end
		2'd2: begin
			array_muxed20 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_write);
		end
		default: begin
			array_muxed20 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_is_write);
		end
	endcase
// synthesis translate_off
	dummy_d_51 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_52;
// synthesis translate_on
always @(*) begin
	array_muxed21 <= 3'd0;
	case (steerer3)
		1'd0: begin
			array_muxed21 <= nop_ba[1:0];
		end
		1'd1: begin
			array_muxed21 <= choose_cmd_cmd_payload_ba[2:0];
		end
		2'd2: begin
			array_muxed21 <= choose_req_cmd_payload_ba[2:0];
		end
		default: begin
			array_muxed21 <= refreshCmd_payload_ba[2:0];
		end
	endcase
// synthesis translate_off
	dummy_d_52 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_53;
// synthesis translate_on
always @(*) begin
	array_muxed22 <= 14'd0;
	case (steerer3)
		1'd0: begin
			array_muxed22 <= nop_a;
		end
		1'd1: begin
			array_muxed22 <= choose_cmd_cmd_payload_a;
		end
		2'd2: begin
			array_muxed22 <= choose_req_cmd_payload_a;
		end
		default: begin
			array_muxed22 <= refreshCmd_payload_a;
		end
	endcase
// synthesis translate_off
	dummy_d_53 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_54;
// synthesis translate_on
always @(*) begin
	array_muxed23 <= 1'd0;
	case (steerer3)
		1'd0: begin
			array_muxed23 <= 1'd0;
		end
		1'd1: begin
			array_muxed23 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_cas);
		end
		2'd2: begin
			array_muxed23 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_cas);
		end
		default: begin
			array_muxed23 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_cas);
		end
	endcase
// synthesis translate_off
	dummy_d_54 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_55;
// synthesis translate_on
always @(*) begin
	array_muxed24 <= 1'd0;
	case (steerer3)
		1'd0: begin
			array_muxed24 <= 1'd0;
		end
		1'd1: begin
			array_muxed24 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_ras);
		end
		2'd2: begin
			array_muxed24 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_ras);
		end
		default: begin
			array_muxed24 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_ras);
		end
	endcase
// synthesis translate_off
	dummy_d_55 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_56;
// synthesis translate_on
always @(*) begin
	array_muxed25 <= 1'd0;
	case (steerer3)
		1'd0: begin
			array_muxed25 <= 1'd0;
		end
		1'd1: begin
			array_muxed25 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_we);
		end
		2'd2: begin
			array_muxed25 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_we);
		end
		default: begin
			array_muxed25 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_we);
		end
	endcase
// synthesis translate_off
	dummy_d_56 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_57;
// synthesis translate_on
always @(*) begin
	array_muxed26 <= 1'd0;
	case (steerer3)
		1'd0: begin
			array_muxed26 <= 1'd0;
		end
		1'd1: begin
			array_muxed26 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_is_read);
		end
		2'd2: begin
			array_muxed26 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_read);
		end
		default: begin
			array_muxed26 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_is_read);
		end
	endcase
// synthesis translate_off
	dummy_d_57 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_58;
// synthesis translate_on
always @(*) begin
	array_muxed27 <= 1'd0;
	case (steerer3)
		1'd0: begin
			array_muxed27 <= 1'd0;
		end
		1'd1: begin
			array_muxed27 <= ((choose_cmd_cmd_valid & choose_cmd_cmd_ready) & choose_cmd_cmd_payload_is_write);
		end
		2'd2: begin
			array_muxed27 <= ((choose_req_cmd_valid & choose_req_cmd_ready) & choose_req_cmd_payload_is_write);
		end
		default: begin
			array_muxed27 <= ((refreshCmd_valid & refreshCmd_ready) & refreshCmd_payload_is_write);
		end
	endcase
// synthesis translate_off
	dummy_d_58 <= dummy_s;
// synthesis translate_on
end

always @(posedge sys_clk) begin
	if ((~en0)) begin
		time0 <= 5'd31;
	end else begin
		if ((~max_time0)) begin
			time0 <= (time0 - 1'd1);
		end
	end
	if ((~en1)) begin
		time1 <= 4'd15;
	end else begin
		if ((~max_time1)) begin
			time1 <= (time1 - 1'd1);
		end
	end
	if (choose_cmd_ce) begin
		case (choose_cmd_grant)
			1'd0: begin
				if (choose_cmd_request[1]) begin
					choose_cmd_grant <= 1'd1;
				end else begin
					if (choose_cmd_request[2]) begin
						choose_cmd_grant <= 2'd2;
					end else begin
						if (choose_cmd_request[3]) begin
							choose_cmd_grant <= 2'd3;
						end
					end
				end
			end
			1'd1: begin
				if (choose_cmd_request[2]) begin
					choose_cmd_grant <= 2'd2;
				end else begin
					if (choose_cmd_request[3]) begin
						choose_cmd_grant <= 2'd3;
					end else begin
						if (choose_cmd_request[0]) begin
							choose_cmd_grant <= 1'd0;
						end
					end
				end
			end
			2'd2: begin
				if (choose_cmd_request[3]) begin
					choose_cmd_grant <= 2'd3;
				end else begin
					if (choose_cmd_request[0]) begin
						choose_cmd_grant <= 1'd0;
					end else begin
						if (choose_cmd_request[1]) begin
							choose_cmd_grant <= 1'd1;
						end
					end
				end
			end
			2'd3: begin
				if (choose_cmd_request[0]) begin
					choose_cmd_grant <= 1'd0;
				end else begin
					if (choose_cmd_request[1]) begin
						choose_cmd_grant <= 1'd1;
					end else begin
						if (choose_cmd_request[2]) begin
							choose_cmd_grant <= 2'd2;
						end
					end
				end
			end
		endcase
	end
	if (choose_req_ce) begin
		case (choose_req_grant)
			1'd0: begin
				if (choose_req_request[1]) begin
					choose_req_grant <= 1'd1;
				end else begin
					if (choose_req_request[2]) begin
						choose_req_grant <= 2'd2;
					end else begin
						if (choose_req_request[3]) begin
							choose_req_grant <= 2'd3;
						end
					end
				end
			end
			1'd1: begin
				if (choose_req_request[2]) begin
					choose_req_grant <= 2'd2;
				end else begin
					if (choose_req_request[3]) begin
						choose_req_grant <= 2'd3;
					end else begin
						if (choose_req_request[0]) begin
							choose_req_grant <= 1'd0;
						end
					end
				end
			end
			2'd2: begin
				if (choose_req_request[3]) begin
					choose_req_grant <= 2'd3;
				end else begin
					if (choose_req_request[0]) begin
						choose_req_grant <= 1'd0;
					end else begin
						if (choose_req_request[1]) begin
							choose_req_grant <= 1'd1;
						end
					end
				end
			end
			2'd3: begin
				if (choose_req_request[0]) begin
					choose_req_grant <= 1'd0;
				end else begin
					if (choose_req_request[1]) begin
						choose_req_grant <= 1'd1;
					end else begin
						if (choose_req_request[2]) begin
							choose_req_grant <= 2'd2;
						end
					end
				end
			end
		endcase
	end
	p0_cs_n <= 1'd0;
	p0_bank <= array_muxed0;
	p0_address <= array_muxed1;
	p0_cas_n <= (~array_muxed2);
	p0_ras_n <= (~array_muxed3);
	p0_we_n <= (~array_muxed4);
	p0_rddata_en <= array_muxed5;
	p0_wrdata_en <= array_muxed6;
	p1_cs_n <= 1'd0;
	p1_bank <= array_muxed7;
	p1_address <= array_muxed8;
	p1_cas_n <= (~array_muxed9);
	p1_ras_n <= (~array_muxed10);
	p1_we_n <= (~array_muxed11);
	p1_rddata_en <= array_muxed12;
	p1_wrdata_en <= array_muxed13;
	p2_cs_n <= 1'd0;
	p2_bank <= array_muxed14;
	p2_address <= array_muxed15;
	p2_cas_n <= (~array_muxed16);
	p2_ras_n <= (~array_muxed17);
	p2_we_n <= (~array_muxed18);
	p2_rddata_en <= array_muxed19;
	p2_wrdata_en <= array_muxed20;
	p3_cs_n <= 1'd0;
	p3_bank <= array_muxed21;
	p3_address <= array_muxed22;
	p3_cas_n <= (~array_muxed23);
	p3_ras_n <= (~array_muxed24);
	p3_we_n <= (~array_muxed25);
	p3_rddata_en <= array_muxed26;
	p3_wrdata_en <= array_muxed27;
	if (trrdcon_valid) begin
		trrdcon_count <= 1'd1;
		if (1'd0) begin
			trrdcon_ready <= 1'd1;
		end else begin
			trrdcon_ready <= 1'd0;
		end
	end else begin
		if ((~trrdcon_ready)) begin
			trrdcon_count <= (trrdcon_count - 1'd1);
			if ((trrdcon_count == 1'd1)) begin
				trrdcon_ready <= 1'd1;
			end
		end
	end
	tfawcon_window <= {tfawcon_window, tfawcon_valid};
	if ((tfawcon_count < 3'd4)) begin
		if ((tfawcon_count == 2'd3)) begin
			tfawcon_ready <= (~tfawcon_valid);
		end else begin
			tfawcon_ready <= 1'd1;
		end
	end
	if (tccdcon_valid) begin
		tccdcon_count <= 1'd0;
		if (1'd1) begin
			tccdcon_ready <= 1'd1;
		end else begin
			tccdcon_ready <= 1'd0;
		end
	end else begin
		if ((~tccdcon_ready)) begin
			tccdcon_count <= (tccdcon_count - 1'd1);
			if ((tccdcon_count == 1'd1)) begin
				tccdcon_ready <= 1'd1;
			end
		end
	end
	if (twtrcon_valid) begin
		twtrcon_count <= 3'd4;
		if (1'd0) begin
			twtrcon_ready <= 1'd1;
		end else begin
			twtrcon_ready <= 1'd0;
		end
	end else begin
		if ((~twtrcon_ready)) begin
			twtrcon_count <= (twtrcon_count - 1'd1);
			if ((twtrcon_count == 1'd1)) begin
				twtrcon_ready <= 1'd1;
			end
		end
	end
	state <= next_state;
	if (sys_rst) begin
		p0_address <= 14'd0;
		p0_bank <= 3'd0;
		p0_cas_n <= 1'd1;
		p0_cs_n <= 1'd1;
		p0_ras_n <= 1'd1;
		p0_we_n <= 1'd1;
		p0_wrdata_en <= 1'd0;
		p0_rddata_en <= 1'd0;
		p1_address <= 14'd0;
		p1_bank <= 3'd0;
		p1_cas_n <= 1'd1;
		p1_cs_n <= 1'd1;
		p1_ras_n <= 1'd1;
		p1_we_n <= 1'd1;
		p1_wrdata_en <= 1'd0;
		p1_rddata_en <= 1'd0;
		p2_address <= 14'd0;
		p2_bank <= 3'd0;
		p2_cas_n <= 1'd1;
		p2_cs_n <= 1'd1;
		p2_ras_n <= 1'd1;
		p2_we_n <= 1'd1;
		p2_wrdata_en <= 1'd0;
		p2_rddata_en <= 1'd0;
		p3_address <= 14'd0;
		p3_bank <= 3'd0;
		p3_cas_n <= 1'd1;
		p3_cs_n <= 1'd1;
		p3_ras_n <= 1'd1;
		p3_we_n <= 1'd1;
		p3_wrdata_en <= 1'd0;
		p3_rddata_en <= 1'd0;
		choose_cmd_grant <= 2'd0;
		choose_req_grant <= 2'd0;
		trrdcon_ready <= 1'd0;
		trrdcon_count <= 1'd0;
		tfawcon_ready <= 1'd1;
		tfawcon_window <= 5'd0;
		tccdcon_ready <= 1'd0;
		tccdcon_count <= 1'd0;
		twtrcon_ready <= 1'd0;
		twtrcon_count <= 3'd0;
		time0 <= 5'd0;
		time1 <= 4'd0;
		state <= 4'd0;
	end
end

endmodule
