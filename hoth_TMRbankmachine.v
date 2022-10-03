/* Machine-generated using Migen */
module TMRBankMachine(
	input [2:0] TMRreq_valid,
	output [2:0] TMRreq_ready,
	input [2:0] TMRreq_we,
	input [62:0] TMRreq_addr,
	output [2:0] TMRreq_lock,
	output [2:0] TMRreq_wdata_ready,
	output [2:0] TMRreq_rdata_valid,
	output [2:0] TMRcmd_valid,
	input [2:0] TMRcmd_ready,
	output [2:0] TMRcmd_first,
	output [2:0] TMRcmd_last,
	output [41:0] TMRcmd_payload_a,
	output [8:0] TMRcmd_payload_ba,
	output [2:0] TMRcmd_payload_cas,
	output [2:0] TMRcmd_payload_ras,
	output [2:0] TMRcmd_payload_we,
	output [2:0] TMRcmd_payload_is_cmd,
	output [2:0] TMRcmd_payload_is_read,
	output [2:0] TMRcmd_payload_is_write,
	input sys_clk,
	input sys_rst
);

wire req_valid;
wire req_ready;
wire req_we;
wire [20:0] req_addr;
wire req_lock;
reg req_wdata_ready;
reg req_rdata_valid;
reg refresh_req = 1'd0;
reg refresh_gnt;
reg cmd_valid;
wire cmd_ready;
reg cmd_first = 1'd0;
reg cmd_last = 1'd0;
reg [13:0] cmd_payload_a;
wire [2:0] cmd_payload_ba;
reg cmd_payload_cas;
reg cmd_payload_ras;
reg cmd_payload_we;
reg cmd_payload_is_cmd;
reg cmd_payload_is_read;
reg cmd_payload_is_write;
wire tmrinput_control0;
reg auto_precharge;
wire [7:0] log_n;
reg [7:0] log_num;
reg [31:0] log_addr;
reg log_valid = 1'd0;
reg log_ready = 1'd0;
reg log_regular_log_sig = 1'd0;
reg log_activate_log_sig = 1'd0;
reg log_precharge_log_sig = 1'd0;
reg log_autoprecharge_log_sig = 1'd0;
reg log_refresh_log_sig = 1'd0;
wire [47:0] loggingsystem_message;
reg loggingsystem_ready = 1'd0;
wire loggingsystem_request;
reg valid_edge = 1'd0;
reg ready_edge = 1'd0;
wire tmrinput_control1;
wire tmrinput_control2;
wire [20:0] tmrinput_control3;
wire cmd_buffer_lookahead_sink_valid;
wire cmd_buffer_lookahead_sink_ready;
reg cmd_buffer_lookahead_sink_first = 1'd0;
reg cmd_buffer_lookahead_sink_last = 1'd0;
wire cmd_buffer_lookahead_sink_payload_we;
wire [20:0] cmd_buffer_lookahead_sink_payload_addr;
wire cmd_buffer_lookahead_source_valid;
wire cmd_buffer_lookahead_source_ready;
wire cmd_buffer_lookahead_source_first;
wire cmd_buffer_lookahead_source_last;
wire cmd_buffer_lookahead_source_payload_we;
wire [20:0] cmd_buffer_lookahead_source_payload_addr;
wire cmd_buffer_lookahead_syncfifo_we;
wire cmd_buffer_lookahead_syncfifo_writable;
wire cmd_buffer_lookahead_syncfifo_re;
wire cmd_buffer_lookahead_syncfifo_readable;
wire [23:0] cmd_buffer_lookahead_syncfifo_din;
wire [23:0] cmd_buffer_lookahead_syncfifo_dout;
reg [3:0] cmd_buffer_lookahead_level = 4'd0;
reg cmd_buffer_lookahead_replace = 1'd0;
reg [2:0] cmd_buffer_lookahead_produce = 3'd0;
reg [2:0] cmd_buffer_lookahead_consume = 3'd0;
reg [2:0] cmd_buffer_lookahead_wrport_adr;
wire [23:0] cmd_buffer_lookahead_wrport_dat_r;
wire cmd_buffer_lookahead_wrport_we;
wire [23:0] cmd_buffer_lookahead_wrport_dat_w;
wire cmd_buffer_lookahead_do_read;
wire [2:0] cmd_buffer_lookahead_rdport_adr;
wire [23:0] cmd_buffer_lookahead_rdport_dat_r;
wire cmd_buffer_lookahead_fifo_in_payload_we;
wire [20:0] cmd_buffer_lookahead_fifo_in_payload_addr;
wire cmd_buffer_lookahead_fifo_in_first;
wire cmd_buffer_lookahead_fifo_in_last;
wire cmd_buffer_lookahead_fifo_out_payload_we;
wire [20:0] cmd_buffer_lookahead_fifo_out_payload_addr;
wire cmd_buffer_lookahead_fifo_out_first;
wire cmd_buffer_lookahead_fifo_out_last;
wire cmd_buffer_sink_valid;
wire cmd_buffer_sink_ready;
wire cmd_buffer_sink_first;
wire cmd_buffer_sink_last;
wire cmd_buffer_sink_payload_we;
wire [20:0] cmd_buffer_sink_payload_addr;
reg cmd_buffer_source_valid = 1'd0;
wire cmd_buffer_source_ready;
reg cmd_buffer_source_first = 1'd0;
reg cmd_buffer_source_last = 1'd0;
reg cmd_buffer_source_payload_we = 1'd0;
reg [20:0] cmd_buffer_source_payload_addr = 21'd0;
wire cmd_buffer_lookahead2_sink_valid;
wire cmd_buffer_lookahead2_sink_ready;
reg cmd_buffer_lookahead2_sink_first = 1'd0;
reg cmd_buffer_lookahead2_sink_last = 1'd0;
wire cmd_buffer_lookahead2_sink_payload_we;
wire [20:0] cmd_buffer_lookahead2_sink_payload_addr;
wire cmd_buffer_lookahead2_source_valid;
wire cmd_buffer_lookahead2_source_ready;
wire cmd_buffer_lookahead2_source_first;
wire cmd_buffer_lookahead2_source_last;
wire cmd_buffer_lookahead2_source_payload_we;
wire [20:0] cmd_buffer_lookahead2_source_payload_addr;
wire cmd_buffer_lookahead2_syncfifo_we;
wire cmd_buffer_lookahead2_syncfifo_writable;
wire cmd_buffer_lookahead2_syncfifo_re;
wire cmd_buffer_lookahead2_syncfifo_readable;
wire [23:0] cmd_buffer_lookahead2_syncfifo_din;
wire [23:0] cmd_buffer_lookahead2_syncfifo_dout;
reg [3:0] cmd_buffer_lookahead2_level = 4'd0;
reg cmd_buffer_lookahead2_replace = 1'd0;
reg [2:0] cmd_buffer_lookahead2_produce = 3'd0;
reg [2:0] cmd_buffer_lookahead2_consume = 3'd0;
reg [2:0] cmd_buffer_lookahead2_wrport_adr;
wire [23:0] cmd_buffer_lookahead2_wrport_dat_r;
wire cmd_buffer_lookahead2_wrport_we;
wire [23:0] cmd_buffer_lookahead2_wrport_dat_w;
wire cmd_buffer_lookahead2_do_read;
wire [2:0] cmd_buffer_lookahead2_rdport_adr;
wire [23:0] cmd_buffer_lookahead2_rdport_dat_r;
wire cmd_buffer_lookahead2_fifo_in_payload_we;
wire [20:0] cmd_buffer_lookahead2_fifo_in_payload_addr;
wire cmd_buffer_lookahead2_fifo_in_first;
wire cmd_buffer_lookahead2_fifo_in_last;
wire cmd_buffer_lookahead2_fifo_out_payload_we;
wire [20:0] cmd_buffer_lookahead2_fifo_out_payload_addr;
wire cmd_buffer_lookahead2_fifo_out_first;
wire cmd_buffer_lookahead2_fifo_out_last;
wire cmd_buffer2_sink_valid;
wire cmd_buffer2_sink_ready;
wire cmd_buffer2_sink_first;
wire cmd_buffer2_sink_last;
wire cmd_buffer2_sink_payload_we;
wire [20:0] cmd_buffer2_sink_payload_addr;
reg cmd_buffer2_source_valid = 1'd0;
wire cmd_buffer2_source_ready;
reg cmd_buffer2_source_first = 1'd0;
reg cmd_buffer2_source_last = 1'd0;
reg cmd_buffer2_source_payload_we = 1'd0;
reg [20:0] cmd_buffer2_source_payload_addr = 21'd0;
wire cmd_buffer_lookahead3_sink_valid;
wire cmd_buffer_lookahead3_sink_ready;
reg cmd_buffer_lookahead3_sink_first = 1'd0;
reg cmd_buffer_lookahead3_sink_last = 1'd0;
wire cmd_buffer_lookahead3_sink_payload_we;
wire [20:0] cmd_buffer_lookahead3_sink_payload_addr;
wire cmd_buffer_lookahead3_source_valid;
wire cmd_buffer_lookahead3_source_ready;
wire cmd_buffer_lookahead3_source_first;
wire cmd_buffer_lookahead3_source_last;
wire cmd_buffer_lookahead3_source_payload_we;
wire [20:0] cmd_buffer_lookahead3_source_payload_addr;
wire cmd_buffer_lookahead3_syncfifo_we;
wire cmd_buffer_lookahead3_syncfifo_writable;
wire cmd_buffer_lookahead3_syncfifo_re;
wire cmd_buffer_lookahead3_syncfifo_readable;
wire [23:0] cmd_buffer_lookahead3_syncfifo_din;
wire [23:0] cmd_buffer_lookahead3_syncfifo_dout;
reg [3:0] cmd_buffer_lookahead3_level = 4'd0;
reg cmd_buffer_lookahead3_replace = 1'd0;
reg [2:0] cmd_buffer_lookahead3_produce = 3'd0;
reg [2:0] cmd_buffer_lookahead3_consume = 3'd0;
reg [2:0] cmd_buffer_lookahead3_wrport_adr;
wire [23:0] cmd_buffer_lookahead3_wrport_dat_r;
wire cmd_buffer_lookahead3_wrport_we;
wire [23:0] cmd_buffer_lookahead3_wrport_dat_w;
wire cmd_buffer_lookahead3_do_read;
wire [2:0] cmd_buffer_lookahead3_rdport_adr;
wire [23:0] cmd_buffer_lookahead3_rdport_dat_r;
wire cmd_buffer_lookahead3_fifo_in_payload_we;
wire [20:0] cmd_buffer_lookahead3_fifo_in_payload_addr;
wire cmd_buffer_lookahead3_fifo_in_first;
wire cmd_buffer_lookahead3_fifo_in_last;
wire cmd_buffer_lookahead3_fifo_out_payload_we;
wire [20:0] cmd_buffer_lookahead3_fifo_out_payload_addr;
wire cmd_buffer_lookahead3_fifo_out_first;
wire cmd_buffer_lookahead3_fifo_out_last;
wire cmd_buffer3_sink_valid;
wire cmd_buffer3_sink_ready;
wire cmd_buffer3_sink_first;
wire cmd_buffer3_sink_last;
wire cmd_buffer3_sink_payload_we;
wire [20:0] cmd_buffer3_sink_payload_addr;
reg cmd_buffer3_source_valid = 1'd0;
wire cmd_buffer3_source_ready;
reg cmd_buffer3_source_first = 1'd0;
reg cmd_buffer3_source_last = 1'd0;
reg cmd_buffer3_source_payload_we = 1'd0;
reg [20:0] cmd_buffer3_source_payload_addr = 21'd0;
wire tmrinput_control4;
wire [20:0] lookAddrVote_control;
wire [20:0] bufAddrVote_control;
wire [2:0] sig_n;
wire lookValidVote_control;
wire bufValidVote_control;
wire bufWeVote_control;
reg [13:0] row = 14'd0;
reg row_opened = 1'd0;
wire row_hit;
reg row_open;
reg row_close;
reg row_col_n_addr_sel;
wire twtpcon_valid;
(* no_retiming = "true" *) reg twtpcon_ready = 1'd0;
reg [2:0] twtpcon_count = 3'd0;
wire twtpcon2_valid;
(* no_retiming = "true" *) reg twtpcon2_ready = 1'd0;
reg [2:0] twtpcon2_count = 3'd0;
wire twtpcon3_valid;
(* no_retiming = "true" *) reg twtpcon3_ready = 1'd0;
reg [2:0] twtpcon3_count = 3'd0;
wire twtpVote_control;
wire trccon_valid;
(* no_retiming = "true" *) reg trccon_ready = 1'd0;
reg [2:0] trccon_count = 3'd0;
wire trccon2_valid;
(* no_retiming = "true" *) reg trccon2_ready = 1'd0;
reg [2:0] trccon2_count = 3'd0;
wire trccon3_valid;
(* no_retiming = "true" *) reg trccon3_ready = 1'd0;
reg [2:0] trccon3_count = 3'd0;
wire trcVote_control;
wire trascon_valid;
(* no_retiming = "true" *) reg trascon_ready = 1'd0;
reg [2:0] trascon_count = 3'd0;
wire trascon2_valid;
(* no_retiming = "true" *) reg trascon2_ready = 1'd0;
reg [2:0] trascon2_count = 3'd0;
wire trascon3_valid;
(* no_retiming = "true" *) reg trascon3_ready = 1'd0;
reg [2:0] trascon3_count = 3'd0;
wire trasVote_control;
reg [2:0] fsm_state;
reg [2:0] fsm_state_edge = 3'd0;
reg [3:0] state = 4'd0;
reg [3:0] next_state;
wire [2:0] slice_proxy0;
wire [2:0] slice_proxy1;
wire [2:0] slice_proxy2;
wire [2:0] slice_proxy3;
wire [2:0] slice_proxy4;
wire [2:0] slice_proxy5;
wire [62:0] slice_proxy6;
wire [62:0] slice_proxy7;
wire [62:0] slice_proxy8;
wire [62:0] slice_proxy9;
wire [62:0] slice_proxy10;
wire [62:0] slice_proxy11;
wire [62:0] slice_proxy12;
wire [62:0] slice_proxy13;
wire [62:0] slice_proxy14;
wire [62:0] slice_proxy15;
wire [62:0] slice_proxy16;
wire [62:0] slice_proxy17;
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

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign log_n = 1'd0;
assign loggingsystem_message = {log_n, log_num, log_addr};

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	log_num <= 8'd0;
	if (log_valid) begin
		log_num <= 1'd0;
	end else begin
		if (log_ready) begin
			log_num <= 1'd1;
		end else begin
			if (log_regular_log_sig) begin
				log_num <= 2'd2;
			end else begin
				if (log_activate_log_sig) begin
					log_num <= 2'd3;
				end else begin
					if (log_precharge_log_sig) begin
						log_num <= 3'd4;
					end else begin
						if (log_autoprecharge_log_sig) begin
							log_num <= 3'd5;
						end else begin
							if (log_refresh_log_sig) begin
								log_num <= 3'd6;
							end
						end
					end
				end
			end
		end
	end
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end
assign loggingsystem_request = ((((((log_valid | log_ready) | log_regular_log_sig) | log_activate_log_sig) | log_precharge_log_sig) | log_autoprecharge_log_sig) | log_refresh_log_sig);
assign cmd_buffer_lookahead_sink_valid = req_valid;
assign cmd_buffer_lookahead_sink_payload_we = req_we;
assign cmd_buffer_lookahead_sink_payload_addr = req_addr;
assign cmd_buffer_sink_valid = cmd_buffer_lookahead_source_valid;
assign cmd_buffer_lookahead_source_ready = cmd_buffer_sink_ready;
assign cmd_buffer_sink_first = cmd_buffer_lookahead_source_first;
assign cmd_buffer_sink_last = cmd_buffer_lookahead_source_last;
assign cmd_buffer_sink_payload_we = cmd_buffer_lookahead_source_payload_we;
assign cmd_buffer_sink_payload_addr = cmd_buffer_lookahead_source_payload_addr;
assign cmd_buffer_source_ready = (req_wdata_ready | req_rdata_valid);
assign cmd_buffer_lookahead2_sink_valid = req_valid;
assign cmd_buffer_lookahead2_sink_payload_we = req_we;
assign cmd_buffer_lookahead2_sink_payload_addr = req_addr;
assign cmd_buffer2_sink_valid = cmd_buffer_lookahead2_source_valid;
assign cmd_buffer_lookahead2_source_ready = cmd_buffer2_sink_ready;
assign cmd_buffer2_sink_first = cmd_buffer_lookahead2_source_first;
assign cmd_buffer2_sink_last = cmd_buffer_lookahead2_source_last;
assign cmd_buffer2_sink_payload_we = cmd_buffer_lookahead2_source_payload_we;
assign cmd_buffer2_sink_payload_addr = cmd_buffer_lookahead2_source_payload_addr;
assign cmd_buffer2_source_ready = (req_wdata_ready | req_rdata_valid);
assign cmd_buffer_lookahead3_sink_valid = req_valid;
assign cmd_buffer_lookahead3_sink_payload_we = req_we;
assign cmd_buffer_lookahead3_sink_payload_addr = req_addr;
assign cmd_buffer3_sink_valid = cmd_buffer_lookahead3_source_valid;
assign cmd_buffer_lookahead3_source_ready = cmd_buffer3_sink_ready;
assign cmd_buffer3_sink_first = cmd_buffer_lookahead3_source_first;
assign cmd_buffer3_sink_last = cmd_buffer_lookahead3_source_last;
assign cmd_buffer3_sink_payload_we = cmd_buffer_lookahead3_source_payload_we;
assign cmd_buffer3_sink_payload_addr = cmd_buffer_lookahead3_source_payload_addr;
assign cmd_buffer3_source_ready = (req_wdata_ready | req_rdata_valid);
assign req_ready = ((cmd_buffer_lookahead_sink_ready & cmd_buffer_lookahead2_sink_ready) & cmd_buffer_lookahead3_sink_ready);
assign sig_n = 1'd0;

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	log_addr <= 32'd0;
	log_addr[14:12] <= sig_n;
	log_addr[11:5] <= bufAddrVote_control[6:0];
	log_addr[31:15] <= bufAddrVote_control[20:7];
	log_addr[30] <= 1'd1;
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end
assign row_hit = (row == bufAddrVote_control[20:7]);
assign cmd_payload_ba = 1'd0;

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	cmd_payload_a <= 14'd0;
	if (row_col_n_addr_sel) begin
		cmd_payload_a <= bufAddrVote_control[20:7];
	end else begin
		cmd_payload_a <= ((auto_precharge <<< 4'd10) | {bufAddrVote_control[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d_2 <= dummy_s;
// synthesis translate_on
end
assign twtpcon_valid = ((cmd_valid & cmd_ready) & cmd_payload_is_write);
assign twtpcon2_valid = ((cmd_valid & cmd_ready) & cmd_payload_is_write);
assign twtpcon3_valid = ((cmd_valid & cmd_ready) & cmd_payload_is_write);
assign trccon_valid = ((cmd_valid & cmd_ready) & row_open);
assign trccon2_valid = ((cmd_valid & cmd_ready) & row_open);
assign trccon3_valid = ((cmd_valid & cmd_ready) & row_open);
assign trascon_valid = ((cmd_valid & cmd_ready) & row_open);
assign trascon2_valid = ((cmd_valid & cmd_ready) & row_open);
assign trascon3_valid = ((cmd_valid & cmd_ready) & row_open);

// synthesis translate_off
reg dummy_d_3;
// synthesis translate_on
always @(*) begin
	auto_precharge <= 1'd0;
	if ((lookValidVote_control & bufValidVote_control)) begin
		if ((lookAddrVote_control[20:7] != bufAddrVote_control[20:7])) begin
			auto_precharge <= (row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_3 <= dummy_s;
// synthesis translate_on
end
assign TMRcmd_valid = {3{cmd_valid}};
assign TMRcmd_last = {3{cmd_last}};
assign TMRcmd_first = {3{cmd_first}};
assign tmrinput_control0 = (((TMRcmd_ready[0] & TMRcmd_ready[1]) | (TMRcmd_ready[1] & TMRcmd_ready[2])) | (TMRcmd_ready[0] & TMRcmd_ready[2]));
assign cmd_ready = tmrinput_control0;
assign TMRcmd_payload_a = {3{cmd_payload_a}};
assign TMRcmd_payload_ba = {3{cmd_payload_ba}};
assign TMRcmd_payload_cas = {3{cmd_payload_cas}};
assign TMRcmd_payload_ras = {3{cmd_payload_ras}};
assign TMRcmd_payload_we = {3{cmd_payload_we}};
assign TMRcmd_payload_is_cmd = {3{cmd_payload_is_cmd}};
assign TMRcmd_payload_is_read = {3{cmd_payload_is_read}};
assign TMRcmd_payload_is_write = {3{cmd_payload_is_write}};
assign tmrinput_control1 = (((TMRreq_valid[0] & TMRreq_valid[1]) | (TMRreq_valid[1] & TMRreq_valid[2])) | (TMRreq_valid[0] & TMRreq_valid[2]));
assign req_valid = tmrinput_control1;
assign TMRreq_ready = {3{req_ready}};
assign tmrinput_control2 = (((TMRreq_we[0] & TMRreq_we[1]) | (TMRreq_we[1] & TMRreq_we[2])) | (TMRreq_we[0] & TMRreq_we[2]));
assign req_we = tmrinput_control2;
assign tmrinput_control3 = (((TMRreq_addr[20:0] & TMRreq_addr[41:21]) | (TMRreq_addr[41:21] & TMRreq_addr[62:42])) | (TMRreq_addr[20:0] & TMRreq_addr[62:42]));
assign req_addr = tmrinput_control3;
assign TMRreq_lock = {3{req_lock}};
assign TMRreq_wdata_ready = {3{req_wdata_ready}};
assign TMRreq_rdata_valid = {3{req_rdata_valid}};
assign cmd_buffer_lookahead_syncfifo_din = {cmd_buffer_lookahead_fifo_in_last, cmd_buffer_lookahead_fifo_in_first, cmd_buffer_lookahead_fifo_in_payload_addr, cmd_buffer_lookahead_fifo_in_payload_we};
assign {cmd_buffer_lookahead_fifo_out_last, cmd_buffer_lookahead_fifo_out_first, cmd_buffer_lookahead_fifo_out_payload_addr, cmd_buffer_lookahead_fifo_out_payload_we} = cmd_buffer_lookahead_syncfifo_dout;
assign cmd_buffer_lookahead_sink_ready = cmd_buffer_lookahead_syncfifo_writable;
assign cmd_buffer_lookahead_syncfifo_we = cmd_buffer_lookahead_sink_valid;
assign cmd_buffer_lookahead_fifo_in_first = cmd_buffer_lookahead_sink_first;
assign cmd_buffer_lookahead_fifo_in_last = cmd_buffer_lookahead_sink_last;
assign cmd_buffer_lookahead_fifo_in_payload_we = cmd_buffer_lookahead_sink_payload_we;
assign cmd_buffer_lookahead_fifo_in_payload_addr = cmd_buffer_lookahead_sink_payload_addr;
assign cmd_buffer_lookahead_source_valid = cmd_buffer_lookahead_syncfifo_readable;
assign cmd_buffer_lookahead_source_first = cmd_buffer_lookahead_fifo_out_first;
assign cmd_buffer_lookahead_source_last = cmd_buffer_lookahead_fifo_out_last;
assign cmd_buffer_lookahead_source_payload_we = cmd_buffer_lookahead_fifo_out_payload_we;
assign cmd_buffer_lookahead_source_payload_addr = cmd_buffer_lookahead_fifo_out_payload_addr;
assign cmd_buffer_lookahead_syncfifo_re = cmd_buffer_lookahead_source_ready;

// synthesis translate_off
reg dummy_d_4;
// synthesis translate_on
always @(*) begin
	cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (cmd_buffer_lookahead_replace) begin
		cmd_buffer_lookahead_wrport_adr <= (cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		cmd_buffer_lookahead_wrport_adr <= cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_4 <= dummy_s;
// synthesis translate_on
end
assign cmd_buffer_lookahead_wrport_dat_w = cmd_buffer_lookahead_syncfifo_din;
assign cmd_buffer_lookahead_wrport_we = (cmd_buffer_lookahead_syncfifo_we & (cmd_buffer_lookahead_syncfifo_writable | cmd_buffer_lookahead_replace));
assign cmd_buffer_lookahead_do_read = (cmd_buffer_lookahead_syncfifo_readable & cmd_buffer_lookahead_syncfifo_re);
assign cmd_buffer_lookahead_rdport_adr = cmd_buffer_lookahead_consume;
assign cmd_buffer_lookahead_syncfifo_dout = cmd_buffer_lookahead_rdport_dat_r;
assign cmd_buffer_lookahead_syncfifo_writable = (cmd_buffer_lookahead_level != 4'd8);
assign cmd_buffer_lookahead_syncfifo_readable = (cmd_buffer_lookahead_level != 1'd0);
assign cmd_buffer_sink_ready = ((~cmd_buffer_source_valid) | cmd_buffer_source_ready);
assign cmd_buffer_lookahead2_syncfifo_din = {cmd_buffer_lookahead2_fifo_in_last, cmd_buffer_lookahead2_fifo_in_first, cmd_buffer_lookahead2_fifo_in_payload_addr, cmd_buffer_lookahead2_fifo_in_payload_we};
assign {cmd_buffer_lookahead2_fifo_out_last, cmd_buffer_lookahead2_fifo_out_first, cmd_buffer_lookahead2_fifo_out_payload_addr, cmd_buffer_lookahead2_fifo_out_payload_we} = cmd_buffer_lookahead2_syncfifo_dout;
assign cmd_buffer_lookahead2_sink_ready = cmd_buffer_lookahead2_syncfifo_writable;
assign cmd_buffer_lookahead2_syncfifo_we = cmd_buffer_lookahead2_sink_valid;
assign cmd_buffer_lookahead2_fifo_in_first = cmd_buffer_lookahead2_sink_first;
assign cmd_buffer_lookahead2_fifo_in_last = cmd_buffer_lookahead2_sink_last;
assign cmd_buffer_lookahead2_fifo_in_payload_we = cmd_buffer_lookahead2_sink_payload_we;
assign cmd_buffer_lookahead2_fifo_in_payload_addr = cmd_buffer_lookahead2_sink_payload_addr;
assign cmd_buffer_lookahead2_source_valid = cmd_buffer_lookahead2_syncfifo_readable;
assign cmd_buffer_lookahead2_source_first = cmd_buffer_lookahead2_fifo_out_first;
assign cmd_buffer_lookahead2_source_last = cmd_buffer_lookahead2_fifo_out_last;
assign cmd_buffer_lookahead2_source_payload_we = cmd_buffer_lookahead2_fifo_out_payload_we;
assign cmd_buffer_lookahead2_source_payload_addr = cmd_buffer_lookahead2_fifo_out_payload_addr;
assign cmd_buffer_lookahead2_syncfifo_re = cmd_buffer_lookahead2_source_ready;

// synthesis translate_off
reg dummy_d_5;
// synthesis translate_on
always @(*) begin
	cmd_buffer_lookahead2_wrport_adr <= 3'd0;
	if (cmd_buffer_lookahead2_replace) begin
		cmd_buffer_lookahead2_wrport_adr <= (cmd_buffer_lookahead2_produce - 1'd1);
	end else begin
		cmd_buffer_lookahead2_wrport_adr <= cmd_buffer_lookahead2_produce;
	end
// synthesis translate_off
	dummy_d_5 <= dummy_s;
// synthesis translate_on
end
assign cmd_buffer_lookahead2_wrport_dat_w = cmd_buffer_lookahead2_syncfifo_din;
assign cmd_buffer_lookahead2_wrport_we = (cmd_buffer_lookahead2_syncfifo_we & (cmd_buffer_lookahead2_syncfifo_writable | cmd_buffer_lookahead2_replace));
assign cmd_buffer_lookahead2_do_read = (cmd_buffer_lookahead2_syncfifo_readable & cmd_buffer_lookahead2_syncfifo_re);
assign cmd_buffer_lookahead2_rdport_adr = cmd_buffer_lookahead2_consume;
assign cmd_buffer_lookahead2_syncfifo_dout = cmd_buffer_lookahead2_rdport_dat_r;
assign cmd_buffer_lookahead2_syncfifo_writable = (cmd_buffer_lookahead2_level != 4'd8);
assign cmd_buffer_lookahead2_syncfifo_readable = (cmd_buffer_lookahead2_level != 1'd0);
assign cmd_buffer2_sink_ready = ((~cmd_buffer2_source_valid) | cmd_buffer2_source_ready);
assign cmd_buffer_lookahead3_syncfifo_din = {cmd_buffer_lookahead3_fifo_in_last, cmd_buffer_lookahead3_fifo_in_first, cmd_buffer_lookahead3_fifo_in_payload_addr, cmd_buffer_lookahead3_fifo_in_payload_we};
assign {cmd_buffer_lookahead3_fifo_out_last, cmd_buffer_lookahead3_fifo_out_first, cmd_buffer_lookahead3_fifo_out_payload_addr, cmd_buffer_lookahead3_fifo_out_payload_we} = cmd_buffer_lookahead3_syncfifo_dout;
assign cmd_buffer_lookahead3_sink_ready = cmd_buffer_lookahead3_syncfifo_writable;
assign cmd_buffer_lookahead3_syncfifo_we = cmd_buffer_lookahead3_sink_valid;
assign cmd_buffer_lookahead3_fifo_in_first = cmd_buffer_lookahead3_sink_first;
assign cmd_buffer_lookahead3_fifo_in_last = cmd_buffer_lookahead3_sink_last;
assign cmd_buffer_lookahead3_fifo_in_payload_we = cmd_buffer_lookahead3_sink_payload_we;
assign cmd_buffer_lookahead3_fifo_in_payload_addr = cmd_buffer_lookahead3_sink_payload_addr;
assign cmd_buffer_lookahead3_source_valid = cmd_buffer_lookahead3_syncfifo_readable;
assign cmd_buffer_lookahead3_source_first = cmd_buffer_lookahead3_fifo_out_first;
assign cmd_buffer_lookahead3_source_last = cmd_buffer_lookahead3_fifo_out_last;
assign cmd_buffer_lookahead3_source_payload_we = cmd_buffer_lookahead3_fifo_out_payload_we;
assign cmd_buffer_lookahead3_source_payload_addr = cmd_buffer_lookahead3_fifo_out_payload_addr;
assign cmd_buffer_lookahead3_syncfifo_re = cmd_buffer_lookahead3_source_ready;

// synthesis translate_off
reg dummy_d_6;
// synthesis translate_on
always @(*) begin
	cmd_buffer_lookahead3_wrport_adr <= 3'd0;
	if (cmd_buffer_lookahead3_replace) begin
		cmd_buffer_lookahead3_wrport_adr <= (cmd_buffer_lookahead3_produce - 1'd1);
	end else begin
		cmd_buffer_lookahead3_wrport_adr <= cmd_buffer_lookahead3_produce;
	end
// synthesis translate_off
	dummy_d_6 <= dummy_s;
// synthesis translate_on
end
assign cmd_buffer_lookahead3_wrport_dat_w = cmd_buffer_lookahead3_syncfifo_din;
assign cmd_buffer_lookahead3_wrport_we = (cmd_buffer_lookahead3_syncfifo_we & (cmd_buffer_lookahead3_syncfifo_writable | cmd_buffer_lookahead3_replace));
assign cmd_buffer_lookahead3_do_read = (cmd_buffer_lookahead3_syncfifo_readable & cmd_buffer_lookahead3_syncfifo_re);
assign cmd_buffer_lookahead3_rdport_adr = cmd_buffer_lookahead3_consume;
assign cmd_buffer_lookahead3_syncfifo_dout = cmd_buffer_lookahead3_rdport_dat_r;
assign cmd_buffer_lookahead3_syncfifo_writable = (cmd_buffer_lookahead3_level != 4'd8);
assign cmd_buffer_lookahead3_syncfifo_readable = (cmd_buffer_lookahead3_level != 1'd0);
assign cmd_buffer3_sink_ready = ((~cmd_buffer3_source_valid) | cmd_buffer3_source_ready);
assign tmrinput_control4 = (((slice_proxy0[0] & slice_proxy1[1]) | (slice_proxy2[1] & slice_proxy3[2])) | (slice_proxy4[0] & slice_proxy5[2]));
assign req_lock = tmrinput_control4;
assign lookAddrVote_control = (((slice_proxy6[20:0] & slice_proxy7[41:21]) | (slice_proxy8[41:21] & slice_proxy9[62:42])) | (slice_proxy10[20:0] & slice_proxy11[62:42]));
assign bufAddrVote_control = (((slice_proxy12[20:0] & slice_proxy13[41:21]) | (slice_proxy14[41:21] & slice_proxy15[62:42])) | (slice_proxy16[20:0] & slice_proxy17[62:42]));
assign lookValidVote_control = (((slice_proxy18[0] & slice_proxy19[1]) | (slice_proxy20[1] & slice_proxy21[2])) | (slice_proxy22[0] & slice_proxy23[2]));
assign bufValidVote_control = (((slice_proxy24[0] & slice_proxy25[1]) | (slice_proxy26[1] & slice_proxy27[2])) | (slice_proxy28[0] & slice_proxy29[2]));
assign bufWeVote_control = (((slice_proxy30[0] & slice_proxy31[1]) | (slice_proxy32[1] & slice_proxy33[2])) | (slice_proxy34[0] & slice_proxy35[2]));
assign twtpVote_control = (((slice_proxy36[0] & slice_proxy37[1]) | (slice_proxy38[1] & slice_proxy39[2])) | (slice_proxy40[0] & slice_proxy41[2]));
assign trcVote_control = (((slice_proxy42[0] & slice_proxy43[1]) | (slice_proxy44[1] & slice_proxy45[2])) | (slice_proxy46[0] & slice_proxy47[2]));
assign trasVote_control = (((slice_proxy48[0] & slice_proxy49[1]) | (slice_proxy50[1] & slice_proxy51[2])) | (slice_proxy52[0] & slice_proxy53[2]));

// synthesis translate_off
reg dummy_d_7;
// synthesis translate_on
always @(*) begin
	req_wdata_ready <= 1'd0;
	req_rdata_valid <= 1'd0;
	refresh_gnt <= 1'd0;
	cmd_valid <= 1'd0;
	cmd_payload_cas <= 1'd0;
	cmd_payload_ras <= 1'd0;
	cmd_payload_we <= 1'd0;
	cmd_payload_is_cmd <= 1'd0;
	cmd_payload_is_read <= 1'd0;
	cmd_payload_is_write <= 1'd0;
	row_open <= 1'd0;
	row_close <= 1'd0;
	row_col_n_addr_sel <= 1'd0;
	fsm_state <= 3'd0;
	next_state <= 4'd0;
	next_state <= state;
	case (state)
		1'd1: begin
			fsm_state <= 1'd1;
			if ((twtpVote_control & trasVote_control)) begin
				cmd_valid <= 1'd1;
				if (cmd_ready) begin
					next_state <= 3'd5;
				end
				cmd_payload_ras <= 1'd1;
				cmd_payload_we <= 1'd1;
				cmd_payload_is_cmd <= 1'd1;
			end
			row_close <= 1'd1;
		end
		2'd2: begin
			fsm_state <= 2'd2;
			if ((twtpVote_control & trasVote_control)) begin
				next_state <= 3'd5;
			end
			row_close <= 1'd1;
		end
		2'd3: begin
			fsm_state <= 2'd3;
			if (trcVote_control) begin
				row_col_n_addr_sel <= 1'd1;
				row_open <= 1'd1;
				cmd_valid <= 1'd1;
				cmd_payload_is_cmd <= 1'd1;
				if (cmd_ready) begin
					next_state <= 3'd7;
				end
				cmd_payload_ras <= 1'd1;
			end
		end
		3'd4: begin
			fsm_state <= 3'd4;
			if (twtpVote_control) begin
				refresh_gnt <= 1'd1;
			end
			row_close <= 1'd1;
			cmd_payload_is_cmd <= 1'd1;
			if ((~refresh_req)) begin
				next_state <= 1'd0;
			end
		end
		3'd5: begin
			next_state <= 3'd6;
		end
		3'd6: begin
			next_state <= 2'd3;
		end
		3'd7: begin
			next_state <= 4'd8;
		end
		4'd8: begin
			next_state <= 1'd0;
		end
		default: begin
			fsm_state <= 1'd0;
			if (refresh_req) begin
				next_state <= 3'd4;
			end else begin
				if (bufValidVote_control) begin
					if (row_opened) begin
						if (row_hit) begin
							cmd_valid <= 1'd1;
							if (bufWeVote_control) begin
								req_wdata_ready <= cmd_ready;
								cmd_payload_is_write <= 1'd1;
								cmd_payload_we <= 1'd1;
							end else begin
								req_rdata_valid <= cmd_ready;
								cmd_payload_is_read <= 1'd1;
							end
							cmd_payload_cas <= 1'd1;
							if ((cmd_ready & auto_precharge)) begin
								next_state <= 2'd2;
							end
						end else begin
							next_state <= 1'd1;
						end
					end else begin
						next_state <= 2'd3;
					end
				end
			end
		end
	endcase
// synthesis translate_off
	dummy_d_7 <= dummy_s;
// synthesis translate_on
end
assign slice_proxy0 = {(cmd_buffer_lookahead3_source_valid | cmd_buffer3_source_valid), (cmd_buffer_lookahead2_source_valid | cmd_buffer2_source_valid), (cmd_buffer_lookahead_source_valid | cmd_buffer_source_valid)};
assign slice_proxy1 = {(cmd_buffer_lookahead3_source_valid | cmd_buffer3_source_valid), (cmd_buffer_lookahead2_source_valid | cmd_buffer2_source_valid), (cmd_buffer_lookahead_source_valid | cmd_buffer_source_valid)};
assign slice_proxy2 = {(cmd_buffer_lookahead3_source_valid | cmd_buffer3_source_valid), (cmd_buffer_lookahead2_source_valid | cmd_buffer2_source_valid), (cmd_buffer_lookahead_source_valid | cmd_buffer_source_valid)};
assign slice_proxy3 = {(cmd_buffer_lookahead3_source_valid | cmd_buffer3_source_valid), (cmd_buffer_lookahead2_source_valid | cmd_buffer2_source_valid), (cmd_buffer_lookahead_source_valid | cmd_buffer_source_valid)};
assign slice_proxy4 = {(cmd_buffer_lookahead3_source_valid | cmd_buffer3_source_valid), (cmd_buffer_lookahead2_source_valid | cmd_buffer2_source_valid), (cmd_buffer_lookahead_source_valid | cmd_buffer_source_valid)};
assign slice_proxy5 = {(cmd_buffer_lookahead3_source_valid | cmd_buffer3_source_valid), (cmd_buffer_lookahead2_source_valid | cmd_buffer2_source_valid), (cmd_buffer_lookahead_source_valid | cmd_buffer_source_valid)};
assign slice_proxy6 = {cmd_buffer_lookahead3_source_payload_addr, cmd_buffer_lookahead2_source_payload_addr, cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy7 = {cmd_buffer_lookahead3_source_payload_addr, cmd_buffer_lookahead2_source_payload_addr, cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy8 = {cmd_buffer_lookahead3_source_payload_addr, cmd_buffer_lookahead2_source_payload_addr, cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy9 = {cmd_buffer_lookahead3_source_payload_addr, cmd_buffer_lookahead2_source_payload_addr, cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy10 = {cmd_buffer_lookahead3_source_payload_addr, cmd_buffer_lookahead2_source_payload_addr, cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy11 = {cmd_buffer_lookahead3_source_payload_addr, cmd_buffer_lookahead2_source_payload_addr, cmd_buffer_lookahead_source_payload_addr};
assign slice_proxy12 = {cmd_buffer3_source_payload_addr, cmd_buffer2_source_payload_addr, cmd_buffer_source_payload_addr};
assign slice_proxy13 = {cmd_buffer3_source_payload_addr, cmd_buffer2_source_payload_addr, cmd_buffer_source_payload_addr};
assign slice_proxy14 = {cmd_buffer3_source_payload_addr, cmd_buffer2_source_payload_addr, cmd_buffer_source_payload_addr};
assign slice_proxy15 = {cmd_buffer3_source_payload_addr, cmd_buffer2_source_payload_addr, cmd_buffer_source_payload_addr};
assign slice_proxy16 = {cmd_buffer3_source_payload_addr, cmd_buffer2_source_payload_addr, cmd_buffer_source_payload_addr};
assign slice_proxy17 = {cmd_buffer3_source_payload_addr, cmd_buffer2_source_payload_addr, cmd_buffer_source_payload_addr};
assign slice_proxy18 = {cmd_buffer_lookahead3_source_valid, cmd_buffer_lookahead2_source_valid, cmd_buffer_lookahead_source_valid};
assign slice_proxy19 = {cmd_buffer_lookahead3_source_valid, cmd_buffer_lookahead2_source_valid, cmd_buffer_lookahead_source_valid};
assign slice_proxy20 = {cmd_buffer_lookahead3_source_valid, cmd_buffer_lookahead2_source_valid, cmd_buffer_lookahead_source_valid};
assign slice_proxy21 = {cmd_buffer_lookahead3_source_valid, cmd_buffer_lookahead2_source_valid, cmd_buffer_lookahead_source_valid};
assign slice_proxy22 = {cmd_buffer_lookahead3_source_valid, cmd_buffer_lookahead2_source_valid, cmd_buffer_lookahead_source_valid};
assign slice_proxy23 = {cmd_buffer_lookahead3_source_valid, cmd_buffer_lookahead2_source_valid, cmd_buffer_lookahead_source_valid};
assign slice_proxy24 = {cmd_buffer3_source_valid, cmd_buffer2_source_valid, cmd_buffer_source_valid};
assign slice_proxy25 = {cmd_buffer3_source_valid, cmd_buffer2_source_valid, cmd_buffer_source_valid};
assign slice_proxy26 = {cmd_buffer3_source_valid, cmd_buffer2_source_valid, cmd_buffer_source_valid};
assign slice_proxy27 = {cmd_buffer3_source_valid, cmd_buffer2_source_valid, cmd_buffer_source_valid};
assign slice_proxy28 = {cmd_buffer3_source_valid, cmd_buffer2_source_valid, cmd_buffer_source_valid};
assign slice_proxy29 = {cmd_buffer3_source_valid, cmd_buffer2_source_valid, cmd_buffer_source_valid};
assign slice_proxy30 = {cmd_buffer3_source_payload_we, cmd_buffer2_source_payload_we, cmd_buffer_source_payload_we};
assign slice_proxy31 = {cmd_buffer3_source_payload_we, cmd_buffer2_source_payload_we, cmd_buffer_source_payload_we};
assign slice_proxy32 = {cmd_buffer3_source_payload_we, cmd_buffer2_source_payload_we, cmd_buffer_source_payload_we};
assign slice_proxy33 = {cmd_buffer3_source_payload_we, cmd_buffer2_source_payload_we, cmd_buffer_source_payload_we};
assign slice_proxy34 = {cmd_buffer3_source_payload_we, cmd_buffer2_source_payload_we, cmd_buffer_source_payload_we};
assign slice_proxy35 = {cmd_buffer3_source_payload_we, cmd_buffer2_source_payload_we, cmd_buffer_source_payload_we};
assign slice_proxy36 = {twtpcon3_ready, twtpcon2_ready, twtpcon_ready};
assign slice_proxy37 = {twtpcon3_ready, twtpcon2_ready, twtpcon_ready};
assign slice_proxy38 = {twtpcon3_ready, twtpcon2_ready, twtpcon_ready};
assign slice_proxy39 = {twtpcon3_ready, twtpcon2_ready, twtpcon_ready};
assign slice_proxy40 = {twtpcon3_ready, twtpcon2_ready, twtpcon_ready};
assign slice_proxy41 = {twtpcon3_ready, twtpcon2_ready, twtpcon_ready};
assign slice_proxy42 = {trccon3_ready, trccon2_ready, trccon_ready};
assign slice_proxy43 = {trccon3_ready, trccon2_ready, trccon_ready};
assign slice_proxy44 = {trccon3_ready, trccon2_ready, trccon_ready};
assign slice_proxy45 = {trccon3_ready, trccon2_ready, trccon_ready};
assign slice_proxy46 = {trccon3_ready, trccon2_ready, trccon_ready};
assign slice_proxy47 = {trccon3_ready, trccon2_ready, trccon_ready};
assign slice_proxy48 = {trascon3_ready, trascon2_ready, trascon_ready};
assign slice_proxy49 = {trascon3_ready, trascon2_ready, trascon_ready};
assign slice_proxy50 = {trascon3_ready, trascon2_ready, trascon_ready};
assign slice_proxy51 = {trascon3_ready, trascon2_ready, trascon_ready};
assign slice_proxy52 = {trascon3_ready, trascon2_ready, trascon_ready};
assign slice_proxy53 = {trascon3_ready, trascon2_ready, trascon_ready};

always @(posedge sys_clk) begin
	if (loggingsystem_ready) begin
		if (log_valid) begin
			log_valid <= 1'd0;
		end else begin
			if (log_ready) begin
				log_ready <= 1'd0;
			end else begin
				if (log_regular_log_sig) begin
					log_regular_log_sig <= 1'd0;
				end else begin
					if (log_activate_log_sig) begin
						log_activate_log_sig <= 1'd0;
					end else begin
						if (log_precharge_log_sig) begin
							log_precharge_log_sig <= 1'd0;
						end else begin
							if (log_autoprecharge_log_sig) begin
								log_autoprecharge_log_sig <= 1'd0;
							end else begin
								if (log_refresh_log_sig) begin
									log_refresh_log_sig <= 1'd0;
								end
							end
						end
					end
				end
			end
		end
	end
	valid_edge <= cmd_valid;
	ready_edge <= cmd_ready;
	if (((cmd_valid & (~valid_edge)) & (~log_valid))) begin
		log_valid <= 1'd1;
	end
	if (((cmd_ready & (~ready_edge)) & (~log_ready))) begin
		log_ready <= 1'd1;
	end
	if (row_close) begin
		row_opened <= 1'd0;
	end else begin
		if (row_open) begin
			row_opened <= 1'd1;
			row <= bufAddrVote_control[20:7];
		end
	end
	fsm_state_edge <= fsm_state;
	if ((fsm_state != fsm_state_edge)) begin
		if ((fsm_state == 1'd0)) begin
			log_regular_log_sig <= 1'd1;
		end
		if ((fsm_state == 1'd1)) begin
			log_precharge_log_sig <= 1'd1;
		end
		if ((fsm_state == 2'd2)) begin
			log_autoprecharge_log_sig <= 1'd1;
		end
		if ((fsm_state == 2'd3)) begin
			log_activate_log_sig <= 1'd1;
		end
		if ((fsm_state == 3'd4)) begin
			log_refresh_log_sig <= 1'd1;
		end
	end
	if (((cmd_buffer_lookahead_syncfifo_we & cmd_buffer_lookahead_syncfifo_writable) & (~cmd_buffer_lookahead_replace))) begin
		cmd_buffer_lookahead_produce <= (cmd_buffer_lookahead_produce + 1'd1);
	end
	if (cmd_buffer_lookahead_do_read) begin
		cmd_buffer_lookahead_consume <= (cmd_buffer_lookahead_consume + 1'd1);
	end
	if (((cmd_buffer_lookahead_syncfifo_we & cmd_buffer_lookahead_syncfifo_writable) & (~cmd_buffer_lookahead_replace))) begin
		if ((~cmd_buffer_lookahead_do_read)) begin
			cmd_buffer_lookahead_level <= (cmd_buffer_lookahead_level + 1'd1);
		end
	end else begin
		if (cmd_buffer_lookahead_do_read) begin
			cmd_buffer_lookahead_level <= (cmd_buffer_lookahead_level - 1'd1);
		end
	end
	if (((~cmd_buffer_source_valid) | cmd_buffer_source_ready)) begin
		cmd_buffer_source_valid <= cmd_buffer_sink_valid;
		cmd_buffer_source_first <= cmd_buffer_sink_first;
		cmd_buffer_source_last <= cmd_buffer_sink_last;
		cmd_buffer_source_payload_we <= cmd_buffer_sink_payload_we;
		cmd_buffer_source_payload_addr <= cmd_buffer_sink_payload_addr;
	end
	if (((cmd_buffer_lookahead2_syncfifo_we & cmd_buffer_lookahead2_syncfifo_writable) & (~cmd_buffer_lookahead2_replace))) begin
		cmd_buffer_lookahead2_produce <= (cmd_buffer_lookahead2_produce + 1'd1);
	end
	if (cmd_buffer_lookahead2_do_read) begin
		cmd_buffer_lookahead2_consume <= (cmd_buffer_lookahead2_consume + 1'd1);
	end
	if (((cmd_buffer_lookahead2_syncfifo_we & cmd_buffer_lookahead2_syncfifo_writable) & (~cmd_buffer_lookahead2_replace))) begin
		if ((~cmd_buffer_lookahead2_do_read)) begin
			cmd_buffer_lookahead2_level <= (cmd_buffer_lookahead2_level + 1'd1);
		end
	end else begin
		if (cmd_buffer_lookahead2_do_read) begin
			cmd_buffer_lookahead2_level <= (cmd_buffer_lookahead2_level - 1'd1);
		end
	end
	if (((~cmd_buffer2_source_valid) | cmd_buffer2_source_ready)) begin
		cmd_buffer2_source_valid <= cmd_buffer2_sink_valid;
		cmd_buffer2_source_first <= cmd_buffer2_sink_first;
		cmd_buffer2_source_last <= cmd_buffer2_sink_last;
		cmd_buffer2_source_payload_we <= cmd_buffer2_sink_payload_we;
		cmd_buffer2_source_payload_addr <= cmd_buffer2_sink_payload_addr;
	end
	if (((cmd_buffer_lookahead3_syncfifo_we & cmd_buffer_lookahead3_syncfifo_writable) & (~cmd_buffer_lookahead3_replace))) begin
		cmd_buffer_lookahead3_produce <= (cmd_buffer_lookahead3_produce + 1'd1);
	end
	if (cmd_buffer_lookahead3_do_read) begin
		cmd_buffer_lookahead3_consume <= (cmd_buffer_lookahead3_consume + 1'd1);
	end
	if (((cmd_buffer_lookahead3_syncfifo_we & cmd_buffer_lookahead3_syncfifo_writable) & (~cmd_buffer_lookahead3_replace))) begin
		if ((~cmd_buffer_lookahead3_do_read)) begin
			cmd_buffer_lookahead3_level <= (cmd_buffer_lookahead3_level + 1'd1);
		end
	end else begin
		if (cmd_buffer_lookahead3_do_read) begin
			cmd_buffer_lookahead3_level <= (cmd_buffer_lookahead3_level - 1'd1);
		end
	end
	if (((~cmd_buffer3_source_valid) | cmd_buffer3_source_ready)) begin
		cmd_buffer3_source_valid <= cmd_buffer3_sink_valid;
		cmd_buffer3_source_first <= cmd_buffer3_sink_first;
		cmd_buffer3_source_last <= cmd_buffer3_sink_last;
		cmd_buffer3_source_payload_we <= cmd_buffer3_sink_payload_we;
		cmd_buffer3_source_payload_addr <= cmd_buffer3_sink_payload_addr;
	end
	if (twtpcon_valid) begin
		twtpcon_count <= 3'd5;
		if (1'd0) begin
			twtpcon_ready <= 1'd1;
		end else begin
			twtpcon_ready <= 1'd0;
		end
	end else begin
		if ((~twtpcon_ready)) begin
			twtpcon_count <= (twtpcon_count - 1'd1);
			if ((twtpcon_count == 1'd1)) begin
				twtpcon_ready <= 1'd1;
			end
		end
	end
	if (twtpcon2_valid) begin
		twtpcon2_count <= 3'd5;
		if (1'd0) begin
			twtpcon2_ready <= 1'd1;
		end else begin
			twtpcon2_ready <= 1'd0;
		end
	end else begin
		if ((~twtpcon2_ready)) begin
			twtpcon2_count <= (twtpcon2_count - 1'd1);
			if ((twtpcon2_count == 1'd1)) begin
				twtpcon2_ready <= 1'd1;
			end
		end
	end
	if (twtpcon3_valid) begin
		twtpcon3_count <= 3'd5;
		if (1'd0) begin
			twtpcon3_ready <= 1'd1;
		end else begin
			twtpcon3_ready <= 1'd0;
		end
	end else begin
		if ((~twtpcon3_ready)) begin
			twtpcon3_count <= (twtpcon3_count - 1'd1);
			if ((twtpcon3_count == 1'd1)) begin
				twtpcon3_ready <= 1'd1;
			end
		end
	end
	if (trccon_valid) begin
		trccon_count <= 3'd6;
		if (1'd0) begin
			trccon_ready <= 1'd1;
		end else begin
			trccon_ready <= 1'd0;
		end
	end else begin
		if ((~trccon_ready)) begin
			trccon_count <= (trccon_count - 1'd1);
			if ((trccon_count == 1'd1)) begin
				trccon_ready <= 1'd1;
			end
		end
	end
	if (trccon2_valid) begin
		trccon2_count <= 3'd6;
		if (1'd0) begin
			trccon2_ready <= 1'd1;
		end else begin
			trccon2_ready <= 1'd0;
		end
	end else begin
		if ((~trccon2_ready)) begin
			trccon2_count <= (trccon2_count - 1'd1);
			if ((trccon2_count == 1'd1)) begin
				trccon2_ready <= 1'd1;
			end
		end
	end
	if (trccon3_valid) begin
		trccon3_count <= 3'd6;
		if (1'd0) begin
			trccon3_ready <= 1'd1;
		end else begin
			trccon3_ready <= 1'd0;
		end
	end else begin
		if ((~trccon3_ready)) begin
			trccon3_count <= (trccon3_count - 1'd1);
			if ((trccon3_count == 1'd1)) begin
				trccon3_ready <= 1'd1;
			end
		end
	end
	if (trascon_valid) begin
		trascon_count <= 3'd5;
		if (1'd0) begin
			trascon_ready <= 1'd1;
		end else begin
			trascon_ready <= 1'd0;
		end
	end else begin
		if ((~trascon_ready)) begin
			trascon_count <= (trascon_count - 1'd1);
			if ((trascon_count == 1'd1)) begin
				trascon_ready <= 1'd1;
			end
		end
	end
	if (trascon2_valid) begin
		trascon2_count <= 3'd5;
		if (1'd0) begin
			trascon2_ready <= 1'd1;
		end else begin
			trascon2_ready <= 1'd0;
		end
	end else begin
		if ((~trascon2_ready)) begin
			trascon2_count <= (trascon2_count - 1'd1);
			if ((trascon2_count == 1'd1)) begin
				trascon2_ready <= 1'd1;
			end
		end
	end
	if (trascon3_valid) begin
		trascon3_count <= 3'd5;
		if (1'd0) begin
			trascon3_ready <= 1'd1;
		end else begin
			trascon3_ready <= 1'd0;
		end
	end else begin
		if ((~trascon3_ready)) begin
			trascon3_count <= (trascon3_count - 1'd1);
			if ((trascon3_count == 1'd1)) begin
				trascon3_ready <= 1'd1;
			end
		end
	end
	state <= next_state;
	if (sys_rst) begin
		log_valid <= 1'd0;
		log_ready <= 1'd0;
		log_regular_log_sig <= 1'd0;
		log_activate_log_sig <= 1'd0;
		log_precharge_log_sig <= 1'd0;
		log_autoprecharge_log_sig <= 1'd0;
		log_refresh_log_sig <= 1'd0;
		valid_edge <= 1'd0;
		ready_edge <= 1'd0;
		cmd_buffer_lookahead_level <= 4'd0;
		cmd_buffer_lookahead_produce <= 3'd0;
		cmd_buffer_lookahead_consume <= 3'd0;
		cmd_buffer_source_valid <= 1'd0;
		cmd_buffer_source_payload_we <= 1'd0;
		cmd_buffer_source_payload_addr <= 21'd0;
		cmd_buffer_lookahead2_level <= 4'd0;
		cmd_buffer_lookahead2_produce <= 3'd0;
		cmd_buffer_lookahead2_consume <= 3'd0;
		cmd_buffer2_source_valid <= 1'd0;
		cmd_buffer2_source_payload_we <= 1'd0;
		cmd_buffer2_source_payload_addr <= 21'd0;
		cmd_buffer_lookahead3_level <= 4'd0;
		cmd_buffer_lookahead3_produce <= 3'd0;
		cmd_buffer_lookahead3_consume <= 3'd0;
		cmd_buffer3_source_valid <= 1'd0;
		cmd_buffer3_source_payload_we <= 1'd0;
		cmd_buffer3_source_payload_addr <= 21'd0;
		row <= 14'd0;
		row_opened <= 1'd0;
		twtpcon_ready <= 1'd0;
		twtpcon_count <= 3'd0;
		twtpcon2_ready <= 1'd0;
		twtpcon2_count <= 3'd0;
		twtpcon3_ready <= 1'd0;
		twtpcon3_count <= 3'd0;
		trccon_ready <= 1'd0;
		trccon_count <= 3'd0;
		trccon2_ready <= 1'd0;
		trccon2_count <= 3'd0;
		trccon3_ready <= 1'd0;
		trccon3_count <= 3'd0;
		trascon_ready <= 1'd0;
		trascon_count <= 3'd0;
		trascon2_ready <= 1'd0;
		trascon2_count <= 3'd0;
		trascon3_ready <= 1'd0;
		trascon3_count <= 3'd0;
		fsm_state_edge <= 3'd0;
		state <= 4'd0;
	end
end

reg [23:0] storage[0:7];
reg [23:0] memdat;
always @(posedge sys_clk) begin
	if (cmd_buffer_lookahead_wrport_we)
		storage[cmd_buffer_lookahead_wrport_adr] <= cmd_buffer_lookahead_wrport_dat_w;
	memdat <= storage[cmd_buffer_lookahead_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign cmd_buffer_lookahead_wrport_dat_r = memdat;
assign cmd_buffer_lookahead_rdport_dat_r = storage[cmd_buffer_lookahead_rdport_adr];

reg [23:0] storage_1[0:7];
reg [23:0] memdat_1;
always @(posedge sys_clk) begin
	if (cmd_buffer_lookahead2_wrport_we)
		storage_1[cmd_buffer_lookahead2_wrport_adr] <= cmd_buffer_lookahead2_wrport_dat_w;
	memdat_1 <= storage_1[cmd_buffer_lookahead2_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign cmd_buffer_lookahead2_wrport_dat_r = memdat_1;
assign cmd_buffer_lookahead2_rdport_dat_r = storage_1[cmd_buffer_lookahead2_rdport_adr];

reg [23:0] storage_2[0:7];
reg [23:0] memdat_2;
always @(posedge sys_clk) begin
	if (cmd_buffer_lookahead3_wrport_we)
		storage_2[cmd_buffer_lookahead3_wrport_adr] <= cmd_buffer_lookahead3_wrport_dat_w;
	memdat_2 <= storage_2[cmd_buffer_lookahead3_wrport_adr];
end

always @(posedge sys_clk) begin
end

assign cmd_buffer_lookahead3_wrport_dat_r = memdat_2;
assign cmd_buffer_lookahead3_rdport_dat_r = storage_2[cmd_buffer_lookahead3_rdport_adr];

endmodule
