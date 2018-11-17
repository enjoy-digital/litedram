/****************************************************************************************
*
*    File Name:  ddr3_dimm.v
*
*  Description:  Micron SDRAM DDR3 (Double Data Rate 3) 240 pin dual in-line memory module (DIMM)
*
*   Limitation:  - SPD (Serial Presence-Detect) is not modeled
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

module ddr3_dimm (
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
    cb     ,
    scl    ,
    sa     ,
    sda
);

`include "ddr3_parameters.vh"

    input                  reset_n;
    input            [1:0] ck     ;
    input            [1:0] ck_n   ;
    input            [1:0] cke    ;
    input            [1:0] s_n    ;
    input                  ras_n  ;
    input                  cas_n  ;
    input                  we_n   ;
    input            [2:0] ba     ;
    input           [15:0] addr   ;
    input            [1:0] odt    ;
    inout           [17:0] dqs    ;
    inout           [17:0] dqs_n  ;
    inout           [63:0] dq     ;
    inout            [7:0] cb     ;
    input                  scl    ; // no connect
    input            [2:0] sa     ; // no connect
    inout                  sda    ; // no connect
`ifdef DUAL_RANK
    initial if (DEBUG) $display("%m: Dual Rank");
`else
    initial if (DEBUG) $display("%m: Single Rank");
`endif
`ifdef ECC
    initial if (DEBUG) $display("%m: ECC");
`else
    initial if (DEBUG) $display("%m: non ECC");
`endif
`ifdef RDIMM
    initial if (DEBUG) $display("%m: Registered DIMM");
    wire             [1:0] rck    = {2{ck[0]}};
    wire             [1:0] rck_n  = {2{ck_n[0]}};
    reg              [1:0] rcke   ;
    reg              [1:0] rs_n   ;
    reg                    rras_n ;
    reg                    rcas_n ;
    reg                    rwe_n  ;
    reg              [2:0] rba    ;
    reg             [15:0] raddr  ;
    reg              [1:0] rodt   ;

    always @(negedge reset_n or posedge ck[0]) begin
        if (!reset_n) begin
	        rcke   <= #(500) 0;   
	        rs_n   <= #(500) 0;   
	        rras_n <= #(500) 0;
	        rcas_n <= #(500) 0;   
            rwe_n  <= #(500) 0;
	        rba    <= #(500) 0;   
	        raddr  <= #(500) 0;   
            rodt   <= #(500) 0;
        end else begin
	        rcke   <= #(500) cke  ;   
            rs_n   <= #(500) s_n  ;
	        rras_n <= #(500) ras_n;   
	        rcas_n <= #(500) cas_n;   
	        rwe_n  <= #(500) we_n ;
	        rba    <= #(500) ba   ;   
	        raddr  <= #(500) addr ;   
            rodt   <= #(500) odt  ;
        end
    end
`else
    initial if (DEBUG) $display("%m: Unbuffered DIMM");
    wire             [1:0] rck    = ck   ;
    wire             [1:0] rck_n  = ck_n ;
    wire             [1:0] rs_n   = s_n  ;
    wire             [2:0] rba    = ba   ;
    wire            [15:0] raddr  = addr ;
    wire             [1:0] rcke   = cke  ;
    wire                   rras_n = ras_n;
    wire                   rcas_n = cas_n;
    wire                   rwe_n  = we_n ;
    wire             [1:0] rodt   = odt  ;
`endif

    wire                   zero   = 1'b0;
    wire                   one    = 1'b1;

  //ddr3      (rst_n  , ck    , ck_n    , cke    , cs_n   , ras_n , cas_n , we_n , dm_tdqs   , ba , addr                , dq       , dqs     , dqs_n     , tdqs_n   , odt    );
`ifdef x4
    initial if (DEBUG) $display("%m: Component Width = x4");
    ddr3 U1   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[ 3: 0], dqs[  0], dqs_n[  0],          , rodt[0]);
    ddr3 U2   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[11: 8], dqs[  1], dqs_n[  1],          , rodt[0]);
    ddr3 U3   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[19:16], dqs[  2], dqs_n[  2],          , rodt[0]);
    ddr3 U4   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[27:24], dqs[  3], dqs_n[  3],          , rodt[0]);
    ddr3 U6   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[35:32], dqs[  4], dqs_n[  4],          , rodt[0]);  
    ddr3 U7   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[43:40], dqs[  5], dqs_n[  5],          , rodt[0]);  
    ddr3 U8   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[51:48], dqs[  6], dqs_n[  6],          , rodt[0]);  
    ddr3 U9   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[59:56], dqs[  7], dqs_n[  7],          , rodt[0]);  
    `ifdef ECC               
    ddr3 U5   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], cb[ 3: 0], dqs[  8], dqs_n[  8],          , rodt[0]);  
    `endif
    ddr3 U18  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[ 7: 4], dqs[  9], dqs_n[  9],          , rodt[0]);
    ddr3 U17  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[15:12], dqs[ 10], dqs_n[ 10],          , rodt[0]);
    ddr3 U16  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[23:20], dqs[ 11], dqs_n[ 11],          , rodt[0]);
    ddr3 U15  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[31:28], dqs[ 12], dqs_n[ 12],          , rodt[0]);
    ddr3 U13  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[39:36], dqs[ 13], dqs_n[ 13],          , rodt[0]);  
    ddr3 U12  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[47:44], dqs[ 14], dqs_n[ 14],          , rodt[0]);  
    ddr3 U11  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[55:52], dqs[ 15], dqs_n[ 15],          , rodt[0]);  
    ddr3 U10  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[63:60], dqs[ 16], dqs_n[ 16],          , rodt[0]);  
    `ifdef ECC               
    ddr3 U14  (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], cb[ 7: 4], dqs[ 17], dqs_n[ 17],          , rodt[0]);  
    `endif
    `ifdef DUAL_RANK
    ddr3 U1t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[ 3: 0], dqs[  0], dqs_n[  0],          , rodt[1]);
    ddr3 U2t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[11: 8], dqs[  1], dqs_n[  1],          , rodt[1]);
    ddr3 U3t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[19:16], dqs[  2], dqs_n[  2],          , rodt[1]);
    ddr3 U4t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[27:24], dqs[  3], dqs_n[  3],          , rodt[1]);
    ddr3 U6t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[35:32], dqs[  4], dqs_n[  4],          , rodt[1]);  
    ddr3 U7t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[43:40], dqs[  5], dqs_n[  5],          , rodt[1]);  
    ddr3 U8t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[51:48], dqs[  6], dqs_n[  6],          , rodt[1]);  
    ddr3 U9t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[59:56], dqs[  7], dqs_n[  7],          , rodt[1]);  
        `ifdef ECC           
    ddr3 U5t  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], cb[ 3: 0], dqs[  8], dqs_n[  8],          , rodt[1]);  
        `endif
    ddr3 U18t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[ 7: 4], dqs[  9], dqs_n[  9],          , rodt[1]);
    ddr3 U17t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[15:12], dqs[ 10], dqs_n[ 10],          , rodt[1]);
    ddr3 U16t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[23:20], dqs[ 11], dqs_n[ 11],          , rodt[1]);
    ddr3 U15t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[31:28], dqs[ 12], dqs_n[ 12],          , rodt[1]);
    ddr3 U13t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[39:36], dqs[ 13], dqs_n[ 13],          , rodt[1]);  
    ddr3 U12t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[47:44], dqs[ 14], dqs_n[ 14],          , rodt[1]);  
    ddr3 U11t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[55:52], dqs[ 15], dqs_n[ 15],          , rodt[1]);  
    ddr3 U10t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], dq[63:60], dqs[ 16], dqs_n[ 16],          , rodt[1]);  
        `ifdef ECC           
    ddr3 U14t (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, zero      , rba, raddr[ADDR_BITS-1:0], cb[ 7: 4], dqs[ 17], dqs_n[ 17],          , rodt[1]);  
        `endif
    `endif
`else `ifdef x8
    initial if (DEBUG) $display("%m: Component Width = x8");
    ddr3 U1   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[ 9]   , rba, raddr[ADDR_BITS-1:0], dq[ 7: 0], dqs[  0], dqs_n[  0], dqs_n[ 9], rodt[0]);
    ddr3 U2   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[10]   , rba, raddr[ADDR_BITS-1:0], dq[15: 8], dqs[  1], dqs_n[  1], dqs_n[10], rodt[0]);
    ddr3 U3   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[11]   , rba, raddr[ADDR_BITS-1:0], dq[23:16], dqs[  2], dqs_n[  2], dqs_n[11], rodt[0]);
    ddr3 U4   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[12]   , rba, raddr[ADDR_BITS-1:0], dq[31:24], dqs[  3], dqs_n[  3], dqs_n[12], rodt[0]);
    ddr3 U6   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[13]   , rba, raddr[ADDR_BITS-1:0], dq[39:32], dqs[  4], dqs_n[  4], dqs_n[13], rodt[0]);  
    ddr3 U7   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[14]   , rba, raddr[ADDR_BITS-1:0], dq[47:40], dqs[  5], dqs_n[  5], dqs_n[14], rodt[0]);  
    ddr3 U8   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[15]   , rba, raddr[ADDR_BITS-1:0], dq[55:48], dqs[  6], dqs_n[  6], dqs_n[15], rodt[0]);  
    ddr3 U9   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[16]   , rba, raddr[ADDR_BITS-1:0], dq[63:56], dqs[  7], dqs_n[  7], dqs_n[16], rodt[0]);  
    `ifdef ECC                
    ddr3 U5   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[17]   , rba, raddr[ADDR_BITS-1:0], cb[ 7: 0], dqs[  8], dqs_n[  8], dqs_n[17], rodt[0]);  
    `endif
    `ifdef DUAL_RANK
    ddr3 U18  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[ 9]   , rba, raddr[ADDR_BITS-1:0], dq[ 7: 0], dqs[  0], dqs_n[  0], dqs_n[ 9], rodt[1]);
    ddr3 U17  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[10]   , rba, raddr[ADDR_BITS-1:0], dq[15: 8], dqs[  1], dqs_n[  1], dqs_n[10], rodt[1]);
    ddr3 U16  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[11]   , rba, raddr[ADDR_BITS-1:0], dq[23:16], dqs[  2], dqs_n[  2], dqs_n[11], rodt[1]);
    ddr3 U15  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[12]   , rba, raddr[ADDR_BITS-1:0], dq[31:24], dqs[  3], dqs_n[  3], dqs_n[12], rodt[1]);
    ddr3 U13  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[13]   , rba, raddr[ADDR_BITS-1:0], dq[39:32], dqs[  4], dqs_n[  4], dqs_n[13], rodt[1]);  
    ddr3 U12  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[14]   , rba, raddr[ADDR_BITS-1:0], dq[47:40], dqs[  5], dqs_n[  5], dqs_n[14], rodt[1]);  
    ddr3 U11  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[15]   , rba, raddr[ADDR_BITS-1:0], dq[55:48], dqs[  6], dqs_n[  6], dqs_n[15], rodt[1]);  
    ddr3 U10  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[16]   , rba, raddr[ADDR_BITS-1:0], dq[63:56], dqs[  7], dqs_n[  7], dqs_n[16], rodt[1]);  
        `ifdef ECC            
    ddr3 U14  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[17]   , rba, raddr[ADDR_BITS-1:0], cb[ 7: 0], dqs[  8], dqs_n[  8], dqs_n[17], rodt[1]);  
        `endif
    `endif
`else `ifdef x16
    initial if (DEBUG) $display("%m: Component Width = x16");
    ddr3 U1   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[10: 9], rba, raddr[ADDR_BITS-1:0], dq[15: 0], dqs[1:0], dqs_n[1:0],          , rodt[0]);
    ddr3 U2   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[12:11], rba, raddr[ADDR_BITS-1:0], dq[31:16], dqs[3:2], dqs_n[3:2],          , rodt[0]);
    ddr3 U4   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[14:13], rba, raddr[ADDR_BITS-1:0], dq[47:32], dqs[5:4], dqs_n[5:4],          , rodt[0]);  
    ddr3 U5   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, dqs[16:15], rba, raddr[ADDR_BITS-1:0], dq[63:48], dqs[7:6], dqs_n[7:6],          , rodt[0]);  
    `ifdef ECC
    ddr3 U3   (reset_n, rck[0], rck_n[0], rcke[0], rs_n[0], rras_n, rcas_n, rwe_n, {one, dqs[17]}, rba, raddr[ADDR_BITS-1:0], {{8{zero}}, cb}, {zero, dqs[8]}, {one, dqs_n[8]},, rodt[0]);  
    `endif
    `ifdef DUAL_RANK
    ddr3 U10  (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[10: 9], rba, raddr[ADDR_BITS-1:0], dq[15: 0], dqs[1:0], dqs_n[1:0],          , rodt[1]);
    ddr3 U9   (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[12:11], rba, raddr[ADDR_BITS-1:0], dq[31:16], dqs[3:2], dqs_n[3:2],          , rodt[1]);
    ddr3 U7   (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[14:13], rba, raddr[ADDR_BITS-1:0], dq[47:32], dqs[5:4], dqs_n[5:4],          , rodt[1]);  
    ddr3 U6   (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, dqs[16:15], rba, raddr[ADDR_BITS-1:0], dq[63:48], dqs[7:6], dqs_n[7:6],          , rodt[1]);  
        `ifdef ECC
    ddr3 U8   (reset_n, rck[1], rck_n[1], rcke[1], rs_n[1], rras_n, rcas_n, rwe_n, {one, dqs[17]}, rba, raddr[ADDR_BITS-1:0], {{8{zero}}, cb}, {zero, dqs[8]}, {one, dqs_n[8]},, rodt[1]);  
        `endif
    `endif
`endif `endif `endif

endmodule
