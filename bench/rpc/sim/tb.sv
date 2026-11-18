// NXRPCPHY (Lattice primitive models) + RPC DRAM model: init, UTR reads, write/read.
//
// Plusargs: +STB/+DQS/+DB (write shifts, UIs), +RD_EN/+RD_PH (READ position: sys_clk cycles, tCK),
// +RDLY (DQSBUF read clock selection), +SLIP (READ position of the read leveling, tCK), +RE_START/+RE_LEN (override READ: start/length in tCK after
// the read command), +TCK4X (edge clock period, ps), +PADS=0/1 (pad activity), +MON=0/1/2 (read
// path monitor).
`timescale 1ps/1ps

module arst_sync(input clk, input arst, output rst);
    reg [1:0] r = 2'b11;
    always @(posedge clk or posedge arst)
        if (arst) r <= 2'b11; else r <= {r[0], 1'b0};
    assign rst = r[1];
endmodule

module tb;
    integer STB = 5, DQS = 4, DB = 1, RD_EN = 3, RDLY = 5, RD_PH = 2, SLIP = 2, MON = 0, RE_START = 0, RE_LEN = 0, TCK4X = 5000, PADS = 1;

    reg clk4x = 0, clk_init = 0, rst = 1;
    always #(TCK4X/2) clk4x = ~clk4x;
    always #20833     clk_init = ~clk_init;

    // DFI.
    reg  [11:0] a[4];
    reg  [1:0]  ba[4];
    reg         cas_n[4], cs_n[4], ras_n[4], we_n[4], rddata_en[4], wrdata_en[4];
    reg  [63:0] wrdata[4];
    reg  [7:0]  wrdata_mask[4];
    wire [63:0] rddata[4];
    wire        rddata_valid[4];
    reg         reset_n = 1, odt = 1, cke = 1;

    reg  [3:0] csr_stb_shift = 0, csr_dqs_shift = 0, csr_db_shift = 0, csr_rd_en_sel = 3;
    reg  [1:0] csr_rd_en_phase = 0;
    reg  [1:0] csr_dly_sel = 0;
    reg        csr_rdly_dq_inc = 0, csr_rdly_dq_rst = 0, csr_burstdet_clr = 0, csr_reset_fsm = 0;
    reg        csr_bitslip = 0, csr_bitslip_rst = 0;
    wire [1:0] csr_burstdet_seen;
    wire       csr_init_done, csr_reset_done;

    wire        rpc_clk_p;
    wire [1:0]  rpc_cs_n, rpc_stb, rpc_dqs_p;
    wire [15:0] rpc_db;

    top dut (
        .clk4x(clk4x), .clk_init(clk_init), .rst(rst),
        .csr_burst_stop(1'b1), .csr_burstdet_clr(csr_burstdet_clr), .csr_burstdet_seen(csr_burstdet_seen),
        .csr_db_shift(csr_db_shift), .csr_dly_sel(csr_dly_sel), .csr_dqs_shift(csr_dqs_shift),
        .csr_init_done(csr_init_done), .csr_rd_en_sel(csr_rd_en_sel), .csr_rd_en_phase(csr_rd_en_phase),
        .csr_rdly_dq_bitslip(csr_bitslip), .csr_rdly_dq_bitslip_rst(csr_bitslip_rst),
        .csr_rdly_dq_inc(csr_rdly_dq_inc), .csr_rdly_dq_rst(csr_rdly_dq_rst),
        .csr_reset_done(csr_reset_done), .csr_reset_fsm(csr_reset_fsm), .csr_rst(1'b0),
        .csr_stb_shift(csr_stb_shift),
        .csr_rdqs_dir(1'b0), .csr_rdqs_move(1'b0), .csr_rdqs_rst(1'b0), .csr_wdly_dir(1'b0), .csr_wdly_move(1'b0),
        .csr_wdly_rst(1'b0), .csr_wlvl_inc(1'b0), .csr_wlvl_rst(1'b0),
`define DFI(p) \
        .dfi_p``p``_act_n(1'b1), .dfi_p``p``_address(a[p]), .dfi_p``p``_bank(ba[p]), .dfi_p``p``_cas_n(cas_n[p]), \
        .dfi_p``p``_cke(cke), .dfi_p``p``_cs_n(cs_n[p]), .dfi_p``p``_odt(odt), .dfi_p``p``_ras_n(ras_n[p]), \
        .dfi_p``p``_rddata(rddata[p]), .dfi_p``p``_rddata_en(rddata_en[p]), .dfi_p``p``_rddata_valid(rddata_valid[p]), \
        .dfi_p``p``_reset_n(reset_n), .dfi_p``p``_we_n(we_n[p]), .dfi_p``p``_wrdata(wrdata[p]), \
        .dfi_p``p``_wrdata_en(wrdata_en[p]), .dfi_p``p``_wrdata_mask(wrdata_mask[p]),
        `DFI(0) `DFI(1) `DFI(2) `DFI(3)
        .rpc_clk_p(rpc_clk_p), .rpc_cs_n(rpc_cs_n), .rpc_db(rpc_db), .rpc_dqs_p(rpc_dqs_p), .rpc_stb(rpc_stb)
    );

    rpc_dram dram (.clk(rpc_clk_p), .cs_n(rpc_cs_n[0]), .stb(rpc_stb[0]), .dqs(rpc_dqs_p), .db(rpc_db));

    GSR GSR_INST (.GSR_N(1'b1), .CLK(1'b0));

    wire sys_clk = dut.sys_clk;

    // Pad activity (relative to the last CLK rising edge).
    realtime t_clk = 0;
    always @(posedge rpc_clk_p) t_clk = $realtime;
    reg pads_en = 0;
    always @(rpc_stb[0])   if (pads_en && PADS) $display("[pads] %0t: STB  -> %b (+%0d ps after CLK rise)", $realtime, rpc_stb[0],   $rtoi($realtime - t_clk));
    always @(rpc_cs_n[0])  if (pads_en && PADS) $display("[pads] %0t: CS#  -> %b (+%0d ps after CLK rise)", $realtime, rpc_cs_n[0],  $rtoi($realtime - t_clk));
    always @(rpc_dqs_p[0]) if (pads_en && PADS) $display("[pads] %0t: DQS  -> %b (+%0d ps after CLK rise)", $realtime, rpc_dqs_p[0], $rtoi($realtime - t_clk));
    always @(rpc_db)       if (pads_en && PADS) $display("[pads] %0t: DB   -> %h (+%0d ps after CLK rise)", $realtime, rpc_db,       $rtoi($realtime - t_clk));

    // Read path monitor.
    reg mon_en = 0;
    always @(negedge sys_clk) if (mon_en && MON)
        $display("[mon] %0t: READ %04b datavalid %b burstdet %b rdpntr %0d wrpntr %0d q0 %08b en %b valid %b", $realtime,
            dut.__main___dqs_re0, dut.__main___datavalid[0], dut.__main___burstdet0, dut.__main___rdpntr0, dut.__main___wrpntr0, dut.convert_db_1ck_in0, rddata_en[3], rddata_valid[0]);
    always @(dram.dqs_oe) if (MON) $display("[mon] %0t: DRAM dqs_oe %b (+%0d ps after CLK rise)", $realtime, dram.dqs_oe, $rtoi($realtime - t_clk));
    always @(dram.db_oe)  if (MON) $display("[mon] %0t: DRAM db_oe  %b (+%0d ps after CLK rise)", $realtime, dram.db_oe,  $rtoi($realtime - t_clk));
    always @(dut.__main___dqsr900) if (mon_en && MON > 1) $display("[mon] %0t: DQSR90 %b", $realtime, dut.__main___dqsr900);

    // Optional READ pulse override: RE_LEN tCK starting RE_START tCK after the read command cycle.
    integer re_t = -1;
    integer n_dqsr90 = 0;
    realtime t_first = 0, t_last = 0, t_cmd = 0;
    reg [3:0] re_word;
    always @(posedge sys_clk) begin
        if (rddata_en[3]) begin re_t = 0; n_dqsr90 = 0; t_cmd = $realtime; end
        else if (re_t >= 0 && re_t < 400) re_t = re_t + 4;
        for (int b = 0; b < 4; b++) re_word[b] = (re_t >= 0) && (re_t + b >= RE_START) && (re_t + b < RE_START + RE_LEN);
        if (RE_LEN > 0) force dut.__main___dqs_re0 = re_word;
    end
    always @(posedge dut.__main___dqsr900) begin
        if (n_dqsr90 == 0) t_first = $realtime;
        t_last = $realtime; n_dqsr90 = n_dqsr90 + 1;
    end

    // IDDRX4DQ outputs while DATAVALID.
    reg [7:0] w[16];
    string dv_s = "";
    always @(negedge sys_clk) if (dut.__main___datavalid[0]) begin
            w[0] = dut.convert_db_1ck_in0;
            w[1] = dut.convert_db_1ck_in1;
            w[2] = dut.convert_db_1ck_in2;
            w[3] = dut.convert_db_1ck_in3;
            w[4] = dut.convert_db_1ck_in4;
            w[5] = dut.convert_db_1ck_in5;
            w[6] = dut.convert_db_1ck_in6;
            w[7] = dut.convert_db_1ck_in7;
            w[8] = dut.convert_db_1ck_in8;
            w[9] = dut.convert_db_1ck_in9;
            w[10] = dut.convert_db_1ck_in10;
            w[11] = dut.convert_db_1ck_in11;
            w[12] = dut.convert_db_1ck_in12;
            w[13] = dut.convert_db_1ck_in13;
            w[14] = dut.convert_db_1ck_in14;
            w[15] = dut.convert_db_1ck_in15;
        for (int k = 0; k < 8; k++) begin
            automatic reg [15:0] x;
            for (int i = 0; i < 16; i++) x[i] = w[i][k];
            dv_s = {dv_s, $sformatf(" %04h", x)};
        end
        dv_s = {dv_s, " |"};
    end

    always @(dut.__main___rdqs_auto) if (MON) $display("[mon] %0t: read delay decrease %b", $realtime, dut.__main___rdqs_auto);

    localparam CS = 1, WE = 2, CAS = 4, RAS = 8, WRDATA = 16, RDDATA = 32;

    task automatic idle();
        for (int p = 0; p < 4; p++) begin
            a[p] = 0; ba[p] = 0; cas_n[p] = 1; cs_n[p] = 1; ras_n[p] = 1; we_n[p] = 1;
            rddata_en[p] = 0; wrdata_en[p] = 0;
        end
    endtask

    task automatic cmd(input int p, input int c, input int address = 0, input int bank = 0);
        @(posedge sys_clk); #100;
        a[p] = address; ba[p] = bank;
        cs_n[p]  = !(c & CS);  we_n[p]  = !(c & WE);
        cas_n[p] = !(c & CAS); ras_n[p] = !(c & RAS);
        rddata_en[p] = (c & RDDATA) != 0; wrdata_en[p] = (c & WRDATA) != 0;
        @(posedge sys_clk); #100;
        idle();
    endtask

    task automatic wait_sys(input int n);
        repeat (n) @(posedge sys_clk);
    endtask

    task automatic pulse(ref reg s);
        @(posedge sys_clk); #100; s = 1; @(posedge sys_clk); #100; s = 0;
    endtask

    task automatic read(input string what, input int address = 0, input int bank = 0);
        mon_en = 1; dv_s = "";
        cmd(3, CAS|CS|RDDATA, address, bank);
        fork begin
            fork
                begin @(posedge rddata_valid[0]); @(negedge sys_clk);
                    $write("[tb] %s: rddata", what);
                    for (int p = 0; p < 4; p++) for (int w = 0; w < 4; w++) $write(" %04h", rddata[p][16*w +: 16]);
                    $write(" burstdet %02b dqsr90 %0d pulses, first +%0d last +%0d ps after cmd\n", csr_burstdet_seen, n_dqsr90, $rtoi(t_first - t_cmd), $rtoi(t_last - t_cmd));
                end
                begin wait_sys(40); $display("[tb] %s: no rddata_valid", what); end
            join_any
            disable fork;
        end join
        wait_sys(8);
        $display("[tb] %s: datavalid data:%s burstdet %02b", what, dv_s, csr_burstdet_seen);
        mon_en = 0;
    endtask

    initial begin
        void'($value$plusargs("STB=%d", STB));     void'($value$plusargs("DQS=%d", DQS));
        void'($value$plusargs("DB=%d", DB));       void'($value$plusargs("RD_EN=%d", RD_EN));
        void'($value$plusargs("RDLY=%d", RDLY)); void'($value$plusargs("SLIP=%d", SLIP));
        void'($value$plusargs("RD_PH=%d", RD_PH)); void'($value$plusargs("MON=%d", MON));
        csr_rd_en_phase = RD_PH;
        void'($value$plusargs("RE_START=%d", RE_START)); void'($value$plusargs("RE_LEN=%d", RE_LEN));
        void'($value$plusargs("TCK4X=%d", TCK4X)); void'($value$plusargs("PADS=%d", PADS));
        csr_stb_shift = STB; csr_dqs_shift = DQS; csr_db_shift = DB; csr_rd_en_sel = RD_EN;
        $display("[tb] STB %0d DQS %0d DB %0d RD_EN %0d RD_PH %0d SLIP %0d RDLY %0d TCK4X %0d", STB, DQS, DB, RD_EN, RD_PH, SLIP, RDLY, TCK4X);
        idle();
        for (int p = 0; p < 4; p++) begin wrdata[p] = 0; wrdata_mask[p] = 0; end
        #200000 rst = 0;
        // DDRDLL lock and DQSBUF init.
        fork
            begin @(posedge dut.dbg_pause); @(negedge dut.dbg_pause); $display("[tb] %0t: PHY init done", $realtime); end
            begin #400000000; $display("[tb] PHY init timeout"); $finish; end
        join_any
        disable fork;
        wait_sys(64);
        // Read delay.
        csr_dly_sel = 2'b11;
        pulse(csr_rdly_dq_rst);
        repeat (RDLY) pulse(csr_rdly_dq_inc);
        pulse(csr_bitslip_rst);
        repeat (SLIP) pulse(csr_bitslip);
        csr_dly_sel = 2'b00;
        wait_sys(16);

        // Init sequence (as the BIOS).
        pulse(csr_reset_fsm);
        wait_sys(64);
        cmd(0, CS);                       wait_sys(8);
        reset_n = 0;                      wait_sys(8);
        pads_en = 1;
        cmd(0, RAS|CS);                   wait_sys(300); // PU RESET (5us).
        pads_en = 0;
        $display("[tb] reset_done %b", csr_reset_done);
        reset_n = 1;                      wait_sys(8);
        cmd(0, RAS|WE|CS, 'h400);         wait_sys(8);   // Precharge all.
        pads_en = 1;
        cmd(0, RAS|CAS|WE|CS, 'h240, 1);  wait_sys(8);   // MRS.
        pads_en = 0;
        reset_n = 0;                      wait_sys(8);
        cmd(0, WE|CS, 'h400);             wait_sys(80);  // ZQ init (1us).
        reset_n = 1;                      wait_sys(8);
        $display("[tb] init_done %b", csr_init_done);

        // UTR reads.
        for (int op = 0; op < 4; op++) begin
            reset_n = 0;                             wait_sys(4);
            cmd(0, RAS|CAS|WE|CS, 1 | (op << 1));    wait_sys(4);
            reset_n = 1;                             wait_sys(4);
            pulse(csr_burstdet_clr);
            pads_en = (op == 0);
            read($sformatf("UTR op %0d", op));
            pads_en = 0;
            reset_n = 0;                             wait_sys(4);
            cmd(0, RAS|CAS|WE|CS, 0 | (op << 1));    wait_sys(4);
            reset_n = 1;                             wait_sys(4);
        end

        // Write/read.
        cmd(0, RAS|CS, 'h123, 1);          wait_sys(8);  // Activate.
        for (int p = 0; p < 4; p++) wrdata[p] = {16'h1000 + 16'(4*p + 3), 16'h1000 + 16'(4*p + 2), 16'h1000 + 16'(4*p + 1), 16'h1000 + 16'(4*p)};
        pads_en = 1;
        cmd(3, CAS|WE|CS|WRDATA, 'h20, 1); wait_sys(24);
        pads_en = 0;
        read("read back", 'h20, 1);
        read("read back", 'h20, 1);
        $display("[tb] done, %0d commands seen by the DRAM", dram.n_cmds);
        $finish;
    end
endmodule
