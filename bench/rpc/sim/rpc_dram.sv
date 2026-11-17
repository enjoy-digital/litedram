// Timing-aware behavioural RPC DRAM model (parallel Request Packets, WORD reads/writes, UTR).
// STB is sampled by CLK, DB by DQS (writes/requests); reads are edge-aligned to CLK + TDQSCK.
`timescale 1ps/1ps

module rpc_dram #(
    parameter integer RL      = 9,    // Read  latency (tCK) from the Request Packet.
    parameter integer WL      = 9,    // Write latency (tCK) from the Request Packet.
    parameter integer TDQSCK  = 300,  // CLK to DQS/DB output (ps).
    parameter integer TSTABLE = 150,  // DB must be stable +/- this around DQS edges (ps).
    parameter integer VERBOSE = 1
) (
    input  wire        clk,
    input  wire        cs_n,
    input  wire        stb,
    inout  wire [1:0]  dqs,
    inout  wire [15:0] db
);
    // Outputs.
    reg        dqs_oe = 0, dqs_o = 0;
    reg        db_oe  = 0;
    reg [15:0] db_o   = 0;
    assign dqs = dqs_oe ? {2{dqs_o}} : 2'bzz;
    assign db  = db_oe  ? db_o       : 16'hzzzz;

    // Clock period.
    realtime t_rise = 0, tck = 5000;
    always @(posedge clk) begin
        if (t_rise != 0) tck = $realtime - t_rise;
        t_rise = $realtime;
    end

    // DQS edge log (when the DRAM does not drive DQS).
    wire [15:0] #(TSTABLE)   db_d1 = db;
    wire [15:0] #(2*TSTABLE) db_d2 = db;
    typedef struct { realtime t; bit rise; logic [15:0] d; bit stable; } edge_t;
    edge_t edges[$];
    always @(dqs[0]) if (!dqs_oe && (dqs[0] === 1'b0 || dqs[0] === 1'b1)) begin
        automatic edge_t e;
        e.t    = $realtime;
        e.rise = dqs[0];
        fork begin
            // Sample at the edge (db_d1 seen TSTABLE later), require stability around it.
            #(TSTABLE);
            e.d      = db_d1;
            e.stable = (db_d2 === db_d1) && (db === db_d1);
            edges.push_back(e);
            if (edges.size() > 256) void'(edges.pop_front());
        end join_none
    end

    // Find a DQS edge near `t` (+/- tCK/4).
    function automatic int find_edge(input realtime t, input bit rise);
        for (int i = edges.size() - 1; i >= 0; i--)
            if (edges[i].rise == rise && (edges[i].t > t - tck/4) && (edges[i].t < t + tck/4))
                return i;
        return -1;
    endfunction

    // State.
    reg [15:0] mem[bit [31:0]];
    reg [11:0] rows[4];
    reg        utr_en = 0;
    reg [1:0]  utr_op = 0;
    reg [3:0]  zout   = 0;
    integer    n_cmds = 0;

    task automatic get_word(input realtime t, input bit rise, input string what,
                            output logic [15:0] d, output bit ok);
        int i;
        // Let late edges (and their stability check) land.
        i  = find_edge(t, rise);
        ok = (i >= 0);
        d  = 16'hxxxx;
        if (!ok) begin
            if (VERBOSE) $display("[dram] %0t: %s: no DQS %s edge near %0t", $realtime, what, rise ? "rising" : "falling", t);
        end else begin
            d = edges[i].d;
            if (VERBOSE) $display("[dram] %0t: %s = %04h (DQS edge %0d ps vs CLK, %s)", $realtime, what, d,
                $rtoi(edges[i].t - t), edges[i].stable ? "stable" : "DB UNSTABLE");
            if (!edges[i].stable) ok = 0;
        end
    endtask

    function automatic [15:0] utr_word(input int k);
        case (utr_op)
            2'd0: utr_word = (k % 2)      ? 16'hffff : 16'h0000; // 0101
            2'd1: utr_word = ((k/2) % 2)  ? 16'h0000 : 16'hffff; // 1100
            2'd2: utr_word = ((k/2) % 2)  ? 16'hffff : 16'h0000; // 0011
            2'd3: utr_word = (k % 2)      ? 16'h0000 : 16'hffff; // 1010
        endcase
    endfunction

    // Main.
    realtime t0, tp;
    logic [15:0] p, n, m0, m1, d;
    bit okp, okn, ok;
    reg [31:0] base;
    reg [31:0] mask;
    logic [15:0] wdata[16];
    bit wok[16];
    initial forever begin
        // Idle: wait for STB low at a CLK rising edge with CS# low.
        @(posedge clk);
        if (stb === 1'b0 && cs_n === 1'b0) begin
            t0 = $realtime;
            tp = t0 + 2*tck;         // Request Packet: rising then falling edge.
            #(2.5*tck + tck/4 + 2*TSTABLE);
            get_word(tp,         1, "request P", p, okp);
            get_word(tp + tck/2, 0, "request N", n, okn);
            n_cmds = n_cmds + 1;
            if (!(okp && okn)) begin
                $display("[dram] %0t: request packet NOT received", $realtime);
            end else begin
                case (p[2:0])
                    3'b000: if (n[0]) $display("[dram] RESET");
                            else begin
                                $display("[dram] RD%s bank %0d col %0d", utr_en ? " (UTR)" : "", p[4:3], {n[15:13], p[15:13]});
                                base = {p[4:3], rows[p[4:3]], n[15:13], p[15:13], 4'd0};
                                if (zout == 0) $display("[dram] Zout open: no read data");
                                else begin
                                    // Preamble 1 tCK before the data, data edge-aligned to CLK.
                                    #(tp + (RL - 1)*tck + TDQSCK - $realtime);
                                    dqs_oe = 1; dqs_o = 0;
                                    #(tck);
                                    for (int k = 0; k < 16; k++) begin
                                        dqs_o = ~k[0];
                                        db_oe = 1;
                                        db_o  = utr_en ? utr_word(k) : (mem.exists(base + k) ? mem[base + k] : 16'hdead);
                                        #(tck/2);
                                    end
                                    db_oe = 0; dqs_o = 0;
                                    #(tck/2);
                                    dqs_oe = 0;
                                end
                            end
                    3'b001: if (n[0]) $display("[dram] ZQC op %0d", p[15:14]);
                            else begin
                                $display("[dram] WR bank %0d col %0d", p[4:3], {n[15:13], p[15:13]});
                                base = {p[4:3], rows[p[4:3]], n[15:13], p[15:13], 4'd0};
                                #(tp + (WL + 8)*tck + tck/4 + 2*TSTABLE - $realtime);
                                get_word(tp + (WL - 2)*tck,         1, "mask 0", m0, ok);
                                get_word(tp + (WL - 2)*tck + tck/2, 0, "mask 1", m1, ok);
                                mask = {m1, m0};
                                for (int k = 0; k < 16; k++) begin
                                    get_word(tp + WL*tck + k*tck/2, ~k[0], $sformatf("data %0d", k), wdata[k], wok[k]);
                                    if (wok[k]) begin
                                        d = mem.exists(base + k) ? mem[base + k] : 16'hdead;
                                        if (!mask[2*k + 0]) d[ 7:0] = wdata[k][ 7:0];
                                        if (!mask[2*k + 1]) d[15:8] = wdata[k][15:8];
                                        mem[base + k] = d;
                                    end
                                end
                            end
                    3'b010: begin
                                zout = p[12:9];
                                $display("[dram] MRS cl %0d nwr %0d zout %0d odt %0d", p[5:3], p[8:6], p[12:9], p[15:13]);
                            end
                    3'b100: $display("[dram] PRE banks %04b", p[9:6]);
                    3'b101: begin
                                rows[p[4:3]] = n[12:1];
                                $display("[dram] ACT bank %0d row %0d", p[4:3], n[12:1]);
                            end
                    3'b110: $display("[dram] REF banks %04b", p[9:6]);
                    3'b111: begin
                                utr_en = p[3]; utr_op = p[5:4];
                                $display("[dram] UTR en %0d op %0d", p[3], p[5:4]);
                            end
                    default: $display("[dram] unknown opcode %0d", p[2:0]);
                endcase
            end
            // Back to idle once STB is high again.
            while (stb !== 1'b1) @(posedge clk);
        end
    end
endmodule
