/* Machine-generated using Migen */
module top(
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
reg [2:0] TMRreq_valid = 3'd0;
wire [2:0] TMRreq_ready;
reg [2:0] TMRreq_we = 3'd0;
reg [62:0] TMRreq_addr = 63'd0;
wire [2:0] TMRreq_lock;
wire [2:0] TMRreq_wdata_ready;
wire [2:0] TMRreq_rdata_valid;
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
wire [2:0] TMRcmd_valid;
reg [2:0] TMRcmd_ready = 3'd0;
wire [2:0] TMRcmd_first;
wire [2:0] TMRcmd_last;
wire [41:0] TMRcmd_payload_a;
wire [8:0] TMRcmd_payload_ba;
wire [2:0] TMRcmd_payload_cas;
wire [2:0] TMRcmd_payload_ras;
wire [2:0] TMRcmd_payload_we;
wire [2:0] TMRcmd_payload_is_cmd;
wire [2:0] TMRcmd_payload_is_read;
wire [2:0] TMRcmd_payload_is_write;
wire control0;
reg auto_precharge;
wire control1;
wire control2;
wire [20:0] control3;
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
reg [13:0] row = 14'd0;
reg row_opened = 1'd0;
wire row_hit;
reg row_open;
reg row_close;
reg row_col_n_addr_sel;
wire twtpcon_valid;
(* no_retiming = "true" *) reg twtpcon_ready = 1'd0;
reg [2:0] twtpcon_count = 3'd0;
wire trccon_valid;
(* no_retiming = "true" *) reg trccon_ready = 1'd0;
reg [2:0] trccon_count = 3'd0;
wire trascon_valid;
(* no_retiming = "true" *) reg trascon_ready = 1'd0;
reg [2:0] trascon_count = 3'd0;
reg [3:0] state = 4'd0;
reg [3:0] next_state;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign cmd_buffer_lookahead_sink_valid = req_valid;
assign req_ready = cmd_buffer_lookahead_sink_ready;
assign cmd_buffer_lookahead_sink_payload_we = req_we;
assign cmd_buffer_lookahead_sink_payload_addr = req_addr;
assign cmd_buffer_sink_valid = cmd_buffer_lookahead_source_valid;
assign cmd_buffer_lookahead_source_ready = cmd_buffer_sink_ready;
assign cmd_buffer_sink_first = cmd_buffer_lookahead_source_first;
assign cmd_buffer_sink_last = cmd_buffer_lookahead_source_last;
assign cmd_buffer_sink_payload_we = cmd_buffer_lookahead_source_payload_we;
assign cmd_buffer_sink_payload_addr = cmd_buffer_lookahead_source_payload_addr;
assign cmd_buffer_source_ready = (req_wdata_ready | req_rdata_valid);
assign req_lock = (cmd_buffer_lookahead_source_valid | cmd_buffer_source_valid);
assign row_hit = (row == cmd_buffer_source_payload_addr[20:7]);
assign cmd_payload_ba = 1'd0;

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	cmd_payload_a <= 14'd0;
	if (row_col_n_addr_sel) begin
		cmd_payload_a <= cmd_buffer_source_payload_addr[20:7];
	end else begin
		cmd_payload_a <= ((auto_precharge <<< 4'd10) | {cmd_buffer_source_payload_addr[6:0], {3{1'd0}}});
	end
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end
assign twtpcon_valid = ((cmd_valid & cmd_ready) & cmd_payload_is_write);
assign trccon_valid = ((cmd_valid & cmd_ready) & row_open);
assign trascon_valid = ((cmd_valid & cmd_ready) & row_open);

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	auto_precharge <= 1'd0;
	if ((cmd_buffer_lookahead_source_valid & cmd_buffer_source_valid)) begin
		if ((cmd_buffer_lookahead_source_payload_addr[20:7] != cmd_buffer_source_payload_addr[20:7])) begin
			auto_precharge <= (row_close == 1'd0);
		end
	end
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end
assign TMRcmd_valid = {3{cmd_valid}};
assign TMRcmd_last = {3{cmd_last}};
assign TMRcmd_first = {3{cmd_first}};
assign control0 = (((TMRcmd_ready[0] & TMRcmd_ready[1]) | (TMRcmd_ready[1] & TMRcmd_ready[2])) | (TMRcmd_ready[0] & TMRcmd_ready[2]));
assign cmd_ready = control0;
assign TMRcmd_payload_a = {3{cmd_payload_a}};
assign TMRcmd_payload_ba = {3{cmd_payload_ba}};
assign TMRcmd_payload_cas = {3{cmd_payload_cas}};
assign TMRcmd_payload_ras = {3{cmd_payload_ras}};
assign TMRcmd_payload_we = {3{cmd_payload_we}};
assign TMRcmd_payload_is_cmd = {3{cmd_payload_is_cmd}};
assign TMRcmd_payload_is_read = {3{cmd_payload_is_read}};
assign TMRcmd_payload_is_write = {3{cmd_payload_is_write}};
assign control1 = (((TMRreq_valid[0] & TMRreq_valid[1]) | (TMRreq_valid[1] & TMRreq_valid[2])) | (TMRreq_valid[0] & TMRreq_valid[2]));
assign req_valid = control1;
assign TMRreq_ready = {3{req_ready}};
assign control2 = (((TMRreq_we[0] & TMRreq_we[1]) | (TMRreq_we[1] & TMRreq_we[2])) | (TMRreq_we[0] & TMRreq_we[2]));
assign req_we = control2;
assign control3 = (((TMRreq_addr[20:0] & TMRreq_addr[41:21]) | (TMRreq_addr[41:21] & TMRreq_addr[62:42])) | (TMRreq_addr[20:0] & TMRreq_addr[62:42]));
assign req_addr = control3;
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
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	cmd_buffer_lookahead_wrport_adr <= 3'd0;
	if (cmd_buffer_lookahead_replace) begin
		cmd_buffer_lookahead_wrport_adr <= (cmd_buffer_lookahead_produce - 1'd1);
	end else begin
		cmd_buffer_lookahead_wrport_adr <= cmd_buffer_lookahead_produce;
	end
// synthesis translate_off
	dummy_d_2 <= dummy_s;
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

// synthesis translate_off
reg dummy_d_3;
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
	next_state <= 4'd0;
	next_state <= state;
	case (state)
		1'd1: begin
			if ((twtpcon_ready & trascon_ready)) begin
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
			if ((twtpcon_ready & trascon_ready)) begin
				next_state <= 3'd5;
			end
			row_close <= 1'd1;
		end
		2'd3: begin
			if (trccon_ready) begin
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
			if (twtpcon_ready) begin
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
			if (refresh_req) begin
				next_state <= 3'd4;
			end else begin
				if (cmd_buffer_source_valid) begin
					if (row_opened) begin
						if (row_hit) begin
							cmd_valid <= 1'd1;
							if (cmd_buffer_source_payload_we) begin
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
	dummy_d_3 <= dummy_s;
// synthesis translate_on
end

always @(posedge sys_clk) begin
	if (row_close) begin
		row_opened <= 1'd0;
	end else begin
		if (row_open) begin
			row_opened <= 1'd1;
			row <= cmd_buffer_source_payload_addr[20:7];
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
	state <= next_state;
	if (sys_rst) begin
		cmd_buffer_lookahead_level <= 4'd0;
		cmd_buffer_lookahead_produce <= 3'd0;
		cmd_buffer_lookahead_consume <= 3'd0;
		cmd_buffer_source_valid <= 1'd0;
		cmd_buffer_source_payload_we <= 1'd0;
		cmd_buffer_source_payload_addr <= 21'd0;
		row <= 14'd0;
		row_opened <= 1'd0;
		twtpcon_ready <= 1'd0;
		twtpcon_count <= 3'd0;
		trccon_ready <= 1'd0;
		trccon_count <= 3'd0;
		trascon_ready <= 1'd0;
		trascon_count <= 3'd0;
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

endmodule
