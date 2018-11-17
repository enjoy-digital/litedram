/****************************************************************************************
*
*    File Name:  ddr3_module.v
*
*  Description:  Micron SDRAM DDR3 (Double Data Rate 3) module model
*
*   Limitation:  - SPD (Serial Presence-Detect) is not modeled
*                - Command/Address parity is not modeled
*
*   Disclaimer   This software code and all associated documentation, comments or other 
*  of Warranty:  information (collectively "Software") is provided "AS IS" without 
*                warranty of any kind. MICRON TECHNOLOGY, INC. ("MTI") EXPRESSLY 
*                DISCLAIMS ALL WARRANTIES EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
*                TO, NONINFRINGEMENT OF THIRD PARTY RIGHTS, AND ANY IMPLIED WARRANTIES 
*                OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE. MTI DOES NOT 
*                WARRANT THAT THE SOFTWARE WILL MEET YOUR REQUIREMENTS, OR THAT THE 
*                OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE. 
*                FURTHERMORE, MTI DOES NOT MAKE ANY REPRESENTATIONS REGARDING THE USE OR 
*                THE RESULTS OF THE USE OF THE SOFTWARE IN TERMS OF ITS CORRECTNESS, 
*                ACCURACY, RELIABILITY, OR OTHERWISE. THE ENTIRE RISK ARISING OUT OF USE 
*                OR PERFORMANCE OF THE SOFTWARE REMAINS WITH YOU. IN NO EVENT SHALL MTI, 
*                ITS AFFILIATED COMPANIES OR THEIR SUPPLIERS BE LIABLE FOR ANY DIRECT, 
*                INDIRECT, CONSEQUENTIAL, INCIDENTAL, OR SPECIAL DAMAGES (INCLUDING, 
*                WITHOUT LIMITATION, DAMAGES FOR LOSS OF PROFITS, BUSINESS INTERRUPTION, 
*                OR LOSS OF INFORMATION) ARISING OUT OF YOUR USE OF OR INABILITY TO USE 
*                THE SOFTWARE, EVEN IF MTI HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH 
*                DAMAGES. Because some jurisdictions prohibit the exclusion or 
*                limitation of liability for consequential or incidental damages, the 
*                above limitation may not apply to you.
*
*                Copyright 2003 Micron Technology, Inc. All rights reserved.
*
****************************************************************************************/
 `timescale 1ps / 1ps

module ddr3_module (
    reset_n,
    ck     ,
    ck_n   ,
    cke    ,
    s_n    , 
    ras_n  ,
    cas_n  ,
    we_n   ,
    ba     ,
    addr   ,
    odt    ,
    dqs    ,
    dqs_n  ,
    dq     ,
`ifdef SODIMM
`else
    cb     ,
`endif
    scl    ,
    sa     ,
    sda
);

`ifdef den1024Mb
    `include "1024Mb_ddr3_parameters.vh"
`elsif den2048Mb
    `include "2048Mb_ddr3_parameters.vh"
`elsif den4096Mb
    `include "4096Mb_ddr3_parameters.vh"
`elsif den8192Mb
    `include "8192Mb_ddr3_parameters.vh"
`endif

    input                  reset_n;
    input            [1:0] cke    ;
    input                  ras_n  ;
    input                  cas_n  ;
    input                  we_n   ;
    input            [2:0] ba     ;
    input           [15:0] addr   ;
    input            [1:0] odt    ;
    inout           [17:0] dqs    ;
    inout           [17:0] dqs_n  ;
    inout           [63:0] dq     ;
    input                  scl    ; // no connect
    inout                  sda    ; // no connect

`ifdef QUAD_RANK
    initial if (DEBUG) $display("%m: Quad Rank");
`elsif DUAL_RANK
    initial if (DEBUG) $display("%m: Dual Rank");
`else
    initial if (DEBUG) $display("%m: Single Rank");
`endif

`ifdef ECC
    initial if (DEBUG) $display("%m: ECC");
    `ifdef SODIMM
    initial begin
        $display("%m ERROR: ECC is not available on SODIMM configurations");
        if (STOP_ON_ERROR) $stop(0);
    end
    `endif
`else
    initial if (DEBUG) $display("%m: non ECC");
`endif

`ifdef RDIMM
    initial if (DEBUG) $display("%m: RDIMM");

    input                  ck     ;
    input                  ck_n   ;
    input            [3:0] s_n    ;
    inout            [7:0] cb     ;
    input            [2:0] sa     ; // no connect

    wire             [1:0] rck    = {2{ck}};
    wire             [1:0] rck_n  = {2{ck_n}};
    reg              [3:0] rs_n   ;
    reg                    rras_n ;
    reg                    rcas_n ;
    reg                    rwe_n  ;
    reg              [2:0] rba    ;
    reg             [15:0] raddr  ;
    reg              [3:0] rcke   ;
    reg              [3:0] rodt   ;

    always @(negedge reset_n or posedge ck) begin
        if (!reset_n) begin
            rs_n   <= #(500) 0;
            rras_n <= #(500) 0;
            rcas_n <= #(500) 0;
            rwe_n  <= #(500) 0;
            rba    <= #(500) 0;
            raddr  <= #(500) 0;
            rcke   <= #(500) 0;
            rodt   <= #(500) 0;
        end else begin
            rs_n   <= #(500) s_n  ;
            rras_n <= #(500) ras_n;
            rcas_n <= #(500) cas_n;
            rwe_n  <= #(500) we_n ;
            rba    <= #(500) ba   ;
            raddr  <= #(500) addr ;
    `ifdef QUAD_RANK
            rcke   <= #(500) {{2{cke[1]}}, {2{cke[0]}}};
            rodt   <= #(500) {{2{odt[1]}}, {2{odt[0]}}};
    `else
            rcke   <= #(500) {2'b00, cke};
            rodt   <= #(500) {2'b00, odt};
    `endif
        end
    end
`else
    input            [1:0] ck     ;
    input            [1:0] ck_n   ;
    input            [1:0] s_n    ;
    `ifdef SODIMM
    initial if (DEBUG) $display("%m: SODIMM");
    input            [1:0] sa     ; // no connect
    wire             [7:0] cb;
    `else
    initial if (DEBUG) $display("%m: UDIMM");
    inout            [7:0] cb     ;
    input            [2:0] sa     ; // no connect
    `endif

    wire             [1:0] rck    = ck   ;
    wire             [1:0] rck_n  = ck_n ;
    wire             [2:0] rba    = ba   ;
    wire            [15:0] raddr  = addr ;

    wire                   rras_n = ras_n;
    wire                   rcas_n = cas_n;
    wire                   rwe_n  = we_n ;
    `ifdef QUAD_RANK
    wire             [3:0] rs_n   = {{2{s_n[1]}}, {2{s_n[0]}}};
    wire             [3:0] rcke   = {{2{cke[1]}}, {2{cke[0]}}};
    wire             [3:0] rodt   = {{2{odt[1]}}, {2{odt[0]}}};
    `else
    wire             [3:0] rs_n   = {2'b00, s_n};
    wire             [3:0] rcke   = {2'b00, cke};
    wire             [3:0] rodt   = {2'b00, odt};
    `endif
`endif
    wire            [15:0] rcb    = {8'b0, cb};
    wire                   zero   = 1'b0;
    wire                   one    = 1'b1;

// all DUAL_RANK UDIMMs have mirrored address
`ifdef QUAD_RANK
    wire            [15:0] maddr  = raddr;
    wire             [2:0] mba    = rba;
`elsif DUAL_RANK
    `ifdef UDIMM
    initial if (DEBUG) $display("%m: ADDRESS MIRROR");
    wire            [15:0] maddr  = {raddr[15:9], raddr[7], raddr[8], raddr[5], raddr[6], raddr[3], raddr[4], raddr[2:0]};
    wire             [2:0] mba    = {rba[2], rba[0], rba[1]};
    `else
    wire            [15:0] maddr  = raddr;
    wire             [2:0] mba    = rba;
    `endif
`else
    wire            [15:0] maddr  = raddr;
    wire             [2:0] mba    = rba;
`endif

  //ddr3       (rst_n  , ck    , ck_n    , cke    , cs_n   , ras_n , cas_n , we_n , dm_tdqs       , ba , addr                , dq             , dqs           , dqs_n          , tdqs_n   , odt    );
`ifdef x4
    initial if (DEBUG) $display("%m: Component Width = x4");
    ddr3 U1R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [ 3: 0], dqs[  0]      , dqs_n[  0]     ,          , rodt[0]);
    ddr3 U2R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [11: 8], dqs[  1]      , dqs_n[  1]     ,          , rodt[0]);
    ddr3 U3R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [19:16], dqs[  2]      , dqs_n[  2]     ,          , rodt[0]);
    ddr3 U4R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [27:24], dqs[  3]      , dqs_n[  3]     ,          , rodt[0]);
    ddr3 U6R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [35:32], dqs[  4]      , dqs_n[  4]     ,          , rodt[0]);
    ddr3 U7R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [43:40], dqs[  5]      , dqs_n[  5]     ,          , rodt[0]);
    ddr3 U8R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [51:48], dqs[  6]      , dqs_n[  6]     ,          , rodt[0]);
    ddr3 U9R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [59:56], dqs[  7]      , dqs_n[  7]     ,          , rodt[0]);
    `ifdef ECC                
    ddr3 U5R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], rcb[ 3: 0], dqs[  8]      , dqs_n[  8]     ,          , rodt[0]);
    `endif
    ddr3 U18R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [ 7: 4], dqs[  9]      , dqs_n[  9]     ,          , rodt[0]);
    ddr3 U17R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [15:12], dqs[ 10]      , dqs_n[ 10]     ,          , rodt[0]);
    ddr3 U16R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [23:20], dqs[ 11]      , dqs_n[ 11]     ,          , rodt[0]);
    ddr3 U15R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [31:28], dqs[ 12]      , dqs_n[ 12]     ,          , rodt[0]);
    ddr3 U13R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [39:36], dqs[ 13]      , dqs_n[ 13]     ,          , rodt[0]);
    ddr3 U12R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [47:44], dqs[ 14]      , dqs_n[ 14]     ,          , rodt[0]);
    ddr3 U11R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [55:52], dqs[ 15]      , dqs_n[ 15]     ,          , rodt[0]);
    ddr3 U10R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [63:60], dqs[ 16]      , dqs_n[ 16]     ,          , rodt[0]);
    `ifdef ECC                
    ddr3 U14R0 (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], rcb[ 7: 4], dqs[ 17]      , dqs_n[ 17]     ,          , rodt[0]);
    `endif
    `ifdef DUAL_RANK
    ddr3 U1R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [ 3: 0], dqs[  0]      , dqs_n[  0]     ,          , rodt[1]);
    ddr3 U2R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [11: 8], dqs[  1]      , dqs_n[  1]     ,          , rodt[1]);
    ddr3 U3R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [19:16], dqs[  2]      , dqs_n[  2]     ,          , rodt[1]);
    ddr3 U4R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [27:24], dqs[  3]      , dqs_n[  3]     ,          , rodt[1]);
    ddr3 U6R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [35:32], dqs[  4]      , dqs_n[  4]     ,          , rodt[1]);
    ddr3 U7R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [43:40], dqs[  5]      , dqs_n[  5]     ,          , rodt[1]);
    ddr3 U8R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [51:48], dqs[  6]      , dqs_n[  6]     ,          , rodt[1]);
    ddr3 U9R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [59:56], dqs[  7]      , dqs_n[  7]     ,          , rodt[1]);
        `ifdef ECC           
    ddr3 U5R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], rcb[ 3: 0], dqs[  8]      , dqs_n[  8]     ,          , rodt[1]);
        `endif
    ddr3 U18R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [ 7: 4], dqs[  9]      , dqs_n[  9]     ,          , rodt[1]);
    ddr3 U17R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [15:12], dqs[ 10]      , dqs_n[ 10]     ,          , rodt[1]);
    ddr3 U16R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [23:20], dqs[ 11]      , dqs_n[ 11]     ,          , rodt[1]);
    ddr3 U15R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [31:28], dqs[ 12]      , dqs_n[ 12]     ,          , rodt[1]);
    ddr3 U13R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [39:36], dqs[ 13]      , dqs_n[ 13]     ,          , rodt[1]);
    ddr3 U12R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [47:44], dqs[ 14]      , dqs_n[ 14]     ,          , rodt[1]);
    ddr3 U11R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [55:52], dqs[ 15]      , dqs_n[ 15]     ,          , rodt[1]);
    ddr3 U10R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], dq [63:60], dqs[ 16]      , dqs_n[ 16]     ,          , rodt[1]);
        `ifdef ECC           
    ddr3 U14R1 (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero          , mba, maddr[ADDR_BITS-1:0], rcb[ 7: 4], dqs[ 17]      , dqs_n[ 17]     ,          , rodt[1]);
        `endif
    `endif
    `ifdef QUAD_RANK
    ddr3 U1R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [ 3: 0], dqs[  0]      , dqs_n[  0]     ,          , rodt[2]);
    ddr3 U2R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [11: 8], dqs[  1]      , dqs_n[  1]     ,          , rodt[2]);
    ddr3 U3R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [19:16], dqs[  2]      , dqs_n[  2]     ,          , rodt[2]);
    ddr3 U4R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [27:24], dqs[  3]      , dqs_n[  3]     ,          , rodt[2]);
    ddr3 U6R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [35:32], dqs[  4]      , dqs_n[  4]     ,          , rodt[2]);
    ddr3 U7R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [43:40], dqs[  5]      , dqs_n[  5]     ,          , rodt[2]);
    ddr3 U8R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [51:48], dqs[  6]      , dqs_n[  6]     ,          , rodt[2]);
    ddr3 U9R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [59:56], dqs[  7]      , dqs_n[  7]     ,          , rodt[2]);
        `ifdef ECC               
    ddr3 U5R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], rcb[ 3: 0], dqs[  8]      , dqs_n[  8]     ,          , rodt[2]);
        `endif
    ddr3 U18R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [ 7: 4], dqs[  9]      , dqs_n[  9]     ,          , rodt[2]);
    ddr3 U17R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [15:12], dqs[ 10]      , dqs_n[ 10]     ,          , rodt[2]);
    ddr3 U16R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [23:20], dqs[ 11]      , dqs_n[ 11]     ,          , rodt[2]);
    ddr3 U15R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [31:28], dqs[ 12]      , dqs_n[ 12]     ,          , rodt[2]);
    ddr3 U13R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [39:36], dqs[ 13]      , dqs_n[ 13]     ,          , rodt[2]);
    ddr3 U12R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [47:44], dqs[ 14]      , dqs_n[ 14]     ,          , rodt[2]);
    ddr3 U11R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [55:52], dqs[ 15]      , dqs_n[ 15]     ,          , rodt[2]);
    ddr3 U10R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [63:60], dqs[ 16]      , dqs_n[ 16]     ,          , rodt[2]);
        `ifdef ECC               
    ddr3 U14R2 (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], rcb[ 7: 4], dqs[ 17]      , dqs_n[ 17]     ,          , rodt[2]);
        `endif
    ddr3 U1R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [ 3: 0], dqs[  0]      , dqs_n[  0]     ,          , rodt[3]);
    ddr3 U2R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [11: 8], dqs[  1]      , dqs_n[  1]     ,          , rodt[3]);
    ddr3 U3R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [19:16], dqs[  2]      , dqs_n[  2]     ,          , rodt[3]);
    ddr3 U4R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [27:24], dqs[  3]      , dqs_n[  3]     ,          , rodt[3]);
    ddr3 U6R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [35:32], dqs[  4]      , dqs_n[  4]     ,          , rodt[3]);
    ddr3 U7R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [43:40], dqs[  5]      , dqs_n[  5]     ,          , rodt[3]);
    ddr3 U8R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [51:48], dqs[  6]      , dqs_n[  6]     ,          , rodt[3]);
    ddr3 U9R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [59:56], dqs[  7]      , dqs_n[  7]     ,          , rodt[3]);
        `ifdef ECC           
    ddr3 U5R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], rcb[ 3: 0], dqs[  8]      , dqs_n[  8]     ,          , rodt[3]);
        `endif
    ddr3 U18R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [ 7: 4], dqs[  9]      , dqs_n[  9]     ,          , rodt[3]);
    ddr3 U17R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [15:12], dqs[ 10]      , dqs_n[ 10]     ,          , rodt[3]);
    ddr3 U16R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [23:20], dqs[ 11]      , dqs_n[ 11]     ,          , rodt[3]);
    ddr3 U15R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [31:28], dqs[ 12]      , dqs_n[ 12]     ,          , rodt[3]);
    ddr3 U13R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [39:36], dqs[ 13]      , dqs_n[ 13]     ,          , rodt[3]);
    ddr3 U12R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [47:44], dqs[ 14]      , dqs_n[ 14]     ,          , rodt[3]);
    ddr3 U11R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [55:52], dqs[ 15]      , dqs_n[ 15]     ,          , rodt[3]);
    ddr3 U10R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], dq [63:60], dqs[ 16]      , dqs_n[ 16]     ,          , rodt[3]);
        `ifdef ECC           
    ddr3 U14R3 (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, zero          , rba, raddr[ADDR_BITS-1:0], rcb[ 7: 4], dqs[ 17]      , dqs_n[ 17]     ,          , rodt[3]);
        `endif
    `endif
`elsif x8
    initial if (DEBUG) $display("%m: Component Width = x8");
    ddr3 U1R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[ 9]       , rba, raddr[ADDR_BITS-1:0], dq [ 7: 0], dqs[  0]      , dqs_n[  0]     , dqs_n[ 9], rodt[0]);
    ddr3 U2R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[10]       , rba, raddr[ADDR_BITS-1:0], dq [15: 8], dqs[  1]      , dqs_n[  1]     , dqs_n[10], rodt[0]);
    ddr3 U3R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[11]       , rba, raddr[ADDR_BITS-1:0], dq [23:16], dqs[  2]      , dqs_n[  2]     , dqs_n[11], rodt[0]);
    ddr3 U4R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[12]       , rba, raddr[ADDR_BITS-1:0], dq [31:24], dqs[  3]      , dqs_n[  3]     , dqs_n[12], rodt[0]);
    ddr3 U6R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[13]       , rba, raddr[ADDR_BITS-1:0], dq [39:32], dqs[  4]      , dqs_n[  4]     , dqs_n[13], rodt[0]);
    ddr3 U7R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[14]       , rba, raddr[ADDR_BITS-1:0], dq [47:40], dqs[  5]      , dqs_n[  5]     , dqs_n[14], rodt[0]);
    ddr3 U8R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[15]       , rba, raddr[ADDR_BITS-1:0], dq [55:48], dqs[  6]      , dqs_n[  6]     , dqs_n[15], rodt[0]);
    ddr3 U9R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[16]       , rba, raddr[ADDR_BITS-1:0], dq [63:56], dqs[  7]      , dqs_n[  7]     , dqs_n[16], rodt[0]);
    `ifdef ECC                 
    ddr3 U5R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[17]       , rba, raddr[ADDR_BITS-1:0], rcb[ 7: 0], dqs[  8]      , dqs_n[  8]     , dqs_n[17], rodt[0]);
    `endif
    `ifdef DUAL_RANK
    ddr3 U1R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[ 9]       , mba, maddr[ADDR_BITS-1:0], dq [ 7: 0], dqs[  0]      , dqs_n[  0]     , dqs_n[ 9], rodt[1]);
    ddr3 U2R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[10]       , mba, maddr[ADDR_BITS-1:0], dq [15: 8], dqs[  1]      , dqs_n[  1]     , dqs_n[10], rodt[1]);
    ddr3 U3R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[11]       , mba, maddr[ADDR_BITS-1:0], dq [23:16], dqs[  2]      , dqs_n[  2]     , dqs_n[11], rodt[1]);
    ddr3 U4R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[12]       , mba, maddr[ADDR_BITS-1:0], dq [31:24], dqs[  3]      , dqs_n[  3]     , dqs_n[12], rodt[1]);
    ddr3 U6R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[13]       , mba, maddr[ADDR_BITS-1:0], dq [39:32], dqs[  4]      , dqs_n[  4]     , dqs_n[13], rodt[1]);
    ddr3 U7R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[14]       , mba, maddr[ADDR_BITS-1:0], dq [47:40], dqs[  5]      , dqs_n[  5]     , dqs_n[14], rodt[1]);
    ddr3 U8R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[15]       , mba, maddr[ADDR_BITS-1:0], dq [55:48], dqs[  6]      , dqs_n[  6]     , dqs_n[15], rodt[1]);
    ddr3 U9R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[16]       , mba, maddr[ADDR_BITS-1:0], dq [63:56], dqs[  7]      , dqs_n[  7]     , dqs_n[16], rodt[1]);
        `ifdef ECC            
    ddr3 U5R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[17]       , mba, maddr[ADDR_BITS-1:0], rcb[ 7: 0], dqs[  8]      , dqs_n[  8]     , dqs_n[17], rodt[1]);
        `endif
    `endif
    `ifdef QUAD_RANK
    ddr3 U1R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[ 9]       , rba, raddr[ADDR_BITS-1:0], dq [ 7: 0], dqs[  0]      , dqs_n[  0]     , dqs_n[ 9], rodt[2]);
    ddr3 U2R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[10]       , rba, raddr[ADDR_BITS-1:0], dq [15: 8], dqs[  1]      , dqs_n[  1]     , dqs_n[10], rodt[2]);
    ddr3 U3R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[11]       , rba, raddr[ADDR_BITS-1:0], dq [23:16], dqs[  2]      , dqs_n[  2]     , dqs_n[11], rodt[2]);
    ddr3 U4R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[12]       , rba, raddr[ADDR_BITS-1:0], dq [31:24], dqs[  3]      , dqs_n[  3]     , dqs_n[12], rodt[2]);
    ddr3 U6R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[13]       , rba, raddr[ADDR_BITS-1:0], dq [39:32], dqs[  4]      , dqs_n[  4]     , dqs_n[13], rodt[2]);
    ddr3 U7R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[14]       , rba, raddr[ADDR_BITS-1:0], dq [47:40], dqs[  5]      , dqs_n[  5]     , dqs_n[14], rodt[2]);
    ddr3 U8R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[15]       , rba, raddr[ADDR_BITS-1:0], dq [55:48], dqs[  6]      , dqs_n[  6]     , dqs_n[15], rodt[2]);
    ddr3 U9R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[16]       , rba, raddr[ADDR_BITS-1:0], dq [63:56], dqs[  7]      , dqs_n[  7]     , dqs_n[16], rodt[2]);
        `ifdef ECC                 
    ddr3 U5R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[17]       , rba, raddr[ADDR_BITS-1:0], rcb[ 7: 0], dqs[  8]      , dqs_n[  8]     , dqs_n[17], rodt[2]);
        `endif
    ddr3 U1R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[ 9]       , rba, raddr[ADDR_BITS-1:0], dq [ 7: 0], dqs[  0]      , dqs_n[  0]     , dqs_n[ 9], rodt[3]);
    ddr3 U2R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[10]       , rba, raddr[ADDR_BITS-1:0], dq [15: 8], dqs[  1]      , dqs_n[  1]     , dqs_n[10], rodt[3]);
    ddr3 U3R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[11]       , rba, raddr[ADDR_BITS-1:0], dq [23:16], dqs[  2]      , dqs_n[  2]     , dqs_n[11], rodt[3]);
    ddr3 U4R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[12]       , rba, raddr[ADDR_BITS-1:0], dq [31:24], dqs[  3]      , dqs_n[  3]     , dqs_n[12], rodt[3]);
    ddr3 U6R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[13]       , rba, raddr[ADDR_BITS-1:0], dq [39:32], dqs[  4]      , dqs_n[  4]     , dqs_n[13], rodt[3]);
    ddr3 U7R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[14]       , rba, raddr[ADDR_BITS-1:0], dq [47:40], dqs[  5]      , dqs_n[  5]     , dqs_n[14], rodt[3]);
    ddr3 U8R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[15]       , rba, raddr[ADDR_BITS-1:0], dq [55:48], dqs[  6]      , dqs_n[  6]     , dqs_n[15], rodt[3]);
    ddr3 U9R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[16]       , rba, raddr[ADDR_BITS-1:0], dq [63:56], dqs[  7]      , dqs_n[  7]     , dqs_n[16], rodt[3]);
        `ifdef ECC            
    ddr3 U5R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[17]       , rba, raddr[ADDR_BITS-1:0], rcb[ 7: 0], dqs[  8]      , dqs_n[  8]     , dqs_n[17], rodt[3]);
        `endif
    `endif
`elsif x16
    initial if (DEBUG) $display("%m: Component Width = x16");
    ddr3 U1R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[10: 9]    , rba, raddr[ADDR_BITS-1:0], dq [15: 0], dqs[1:0]      , dqs_n[1:0]     ,          , rodt[0]);
    ddr3 U2R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[12:11]    , rba, raddr[ADDR_BITS-1:0], dq [31:16], dqs[3:2]      , dqs_n[3:2]     ,          , rodt[0]);
    ddr3 U4R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[14:13]    , rba, raddr[ADDR_BITS-1:0], dq [47:32], dqs[5:4]      , dqs_n[5:4]     ,          , rodt[0]);
    ddr3 U5R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[16:15]    , rba, raddr[ADDR_BITS-1:0], dq [63:48], dqs[7:6]      , dqs_n[7:6]     ,          , rodt[0]);
    `ifdef ECC
    ddr3 U3R0  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, {one, dqs[17]}, rba, raddr[ADDR_BITS-1:0], rcb[15: 0], {zero, dqs[8]}, {one, dqs_n[8]},          , rodt[0]);
    `endif
    `ifdef DUAL_RANK
    ddr3 U1R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[10: 9]    , mba, maddr[ADDR_BITS-1:0], dq [15: 0], dqs[1:0]      , dqs_n[1:0]     ,          , rodt[1]);
    ddr3 U2R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[12:11]    , mba, maddr[ADDR_BITS-1:0], dq [31:16], dqs[3:2]      , dqs_n[3:2]     ,          , rodt[1]);
    ddr3 U4R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[14:13]    , mba, maddr[ADDR_BITS-1:0], dq [47:32], dqs[5:4]      , dqs_n[5:4]     ,          , rodt[1]);
    ddr3 U5R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[16:15]    , mba, maddr[ADDR_BITS-1:0], dq [63:48], dqs[7:6]      , dqs_n[7:6]     ,          , rodt[1]);
        `ifdef ECC
    ddr3 U3R1  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, {one, dqs[17]}, mba, maddr[ADDR_BITS-1:0], rcb[15: 0], {zero, dqs[8]}, {one, dqs_n[8]},          , rodt[1]);
        `endif
    `endif
    `ifdef QUAD_RANK
    ddr3 U1R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[10: 9]    , rba, raddr[ADDR_BITS-1:0], dq [15: 0], dqs[1:0]      , dqs_n[1:0]     ,          , rodt[2]);
    ddr3 U2R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[12:11]    , rba, raddr[ADDR_BITS-1:0], dq [31:16], dqs[3:2]      , dqs_n[3:2]     ,          , rodt[2]);
    ddr3 U4R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[14:13]    , rba, raddr[ADDR_BITS-1:0], dq [47:32], dqs[5:4]      , dqs_n[5:4]     ,          , rodt[2]);
    ddr3 U5R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, dqs[16:15]    , rba, raddr[ADDR_BITS-1:0], dq [63:48], dqs[7:6]      , dqs_n[7:6]     ,          , rodt[2]);
        `ifdef ECC
    ddr3 U3R2  (reset_n, rck[0], rck_n[0], rcke[2], rs_n[2], rras_n, rcas_n, rwe_n, {one, dqs[17]}, rba, raddr[ADDR_BITS-1:0], rcb[15: 0], {zero, dqs[8]}, {one, dqs_n[8]},          , rodt[2]);
        `endif
    ddr3 U1R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[10: 9]    , rba, raddr[ADDR_BITS-1:0], dq [15: 0], dqs[1:0]      , dqs_n[1:0]     ,          , rodt[3]);
    ddr3 U2R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[12:11]    , rba, raddr[ADDR_BITS-1:0], dq [31:16], dqs[3:2]      , dqs_n[3:2]     ,          , rodt[3]);
    ddr3 U4R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[14:13]    , rba, raddr[ADDR_BITS-1:0], dq [47:32], dqs[5:4]      , dqs_n[5:4]     ,          , rodt[3]);
    ddr3 U5R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, dqs[16:15]    , rba, raddr[ADDR_BITS-1:0], dq [63:48], dqs[7:6]      , dqs_n[7:6]     ,          , rodt[3]);
        `ifdef ECC
    ddr3 U3R3  (reset_n, rck[1], rck_n[1], rcke[3], rs_n[3], rras_n, rcas_n, rwe_n, {one, dqs[17]}, rba, raddr[ADDR_BITS-1:0], rcb[15: 0], {zero, dqs[8]}, {one, dqs_n[8]},          , rodt[3]);
        `endif
    `endif
`endif

    // calculate the absolute value of a real number
    function real abs_value;
    input arg;
    real arg;
    begin
        if (arg < 0.0)
            abs_value = -1.0 * arg;
        else
            abs_value = arg;
    end
    endfunction

    function integer ceil;
        input number;
        real number;

        // LMR 4.1.7
        // When either operand of a relational expression is a real operand then the other operand shall be converted
        // to an equivalent real value, and the expression shall be interpreted as a comparison between two real values.
        if (number > $rtoi(number))
            ceil = $rtoi(number) + 1;
        else
            ceil = number;
    endfunction

    function integer floor;
        input number;
        real number;

        // LMR 4.1.7
        // When either operand of a relational expression is a real operand then the other operand shall be converted
        // to an equivalent real value, and the expression shall be interpreted as a comparison between two real values.
        if (number < $rtoi(number))
            floor = $rtoi(number) - 1;
        else
            floor = number;
    endfunction

    function int max( input int a, b );
        max = (a < b) ? b : a;
    endfunction

    function int min( input int a, b );
        min = (a > b) ? b : a;
    endfunction


endmodule
