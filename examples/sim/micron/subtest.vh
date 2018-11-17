/****************************************************************************************
*
*    File Name:  subtest.vh
*
*  Description:  Micron SDRAM DDR3 (Double Data Rate 3)
*                This file is included by tb.v
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

    initial begin : test
        parameter [31:0] REP = DQ_BITS/8.0;

        reg         [BA_BITS-1:0] r_bank;
        reg        [ROW_BITS-1:0] r_row;
        reg        [COL_BITS-1:0] r_col;
        reg  [BL_MAX*DQ_BITS-1:0] r_data;
        integer                   r_i, r_j;


        real original_tck;
        reg [8*DQ_BITS-1:0] d0, d1, d2, d3;
        d0 = {
           {REP{8'h07}}, {REP{8'h06}}, {REP{8'h05}}, {REP{8'h04}},
           {REP{8'h03}}, {REP{8'h02}}, {REP{8'h01}}, {REP{8'h00}}
        };
        d1 = {
           {REP{8'h17}}, {REP{8'h16}}, {REP{8'h15}}, {REP{8'h14}},
           {REP{8'h13}}, {REP{8'h12}}, {REP{8'h11}}, {REP{8'h10}}
        };
        d2 = {
           {REP{8'h27}}, {REP{8'h26}}, {REP{8'h25}}, {REP{8'h24}},
           {REP{8'h23}}, {REP{8'h22}}, {REP{8'h21}}, {REP{8'h20}}
        };
        d3 = {
           {REP{8'h37}}, {REP{8'h36}}, {REP{8'h35}}, {REP{8'h34}},
           {REP{8'h33}}, {REP{8'h32}}, {REP{8'h31}}, {REP{8'h30}}
        };
        
        rst_n   <=  1'b0;
        cke     <=  1'b0;
        cs_n    <=  1'b1;
        ras_n   <=  1'b1;
        cas_n   <=  1'b1;
        we_n    <=  1'b1;
        ba      <=  {BA_BITS{1'bz}};
        a       <=  {ADDR_BITS{1'bz}};
        odt_out <=  1'b0;
        dq_en   <=  1'b0;
        dqs_en  <=  1'b0;
        
        // POWERUP SECTION 
        power_up;

        // INITIALIZE SECTION
        zq_calibration  (1);                            // perform Long ZQ Calibration

        load_mode       (3, 14'b00000000000000);        // Extended Mode Register (3)
        nop             (tmrd-1);
        
        load_mode       (2, {14'b00001000_000_000} | mr_cwl<<3); // Extended Mode Register 2 with DCC Disable
        nop             (tmrd-1);
        
        load_mode       (1, 14'b0000010110);            // Extended Mode Register with DLL Enable, AL=CL-1
        nop             (tmrd-1);
        
        load_mode       (0, {14'b0_0_000_1_0_000_1_0_00} | mr_wr<<9 | mr_cl<<2); // Mode Register with DLL Reset

        nop             (max(TDLLK,TZQINIT));
        odt_out         <= 1;                           // turn on odt
        nop (10);


// Random Act -> Write -> Read -> Precharge
for (r_i = 0; r_i < 2048; r_i = r_i + 1) begin
        r_bank = $urandom_range (8);
        r_row  = $urandom_range (1<<ROW_BITS);
        r_col  = $urandom_range (1<<COL_BITS);
        r_data = {$urandom,$urandom,$urandom,$urandom,$urandom,$urandom,$urandom,$urandom};

        activate        (r_bank, r_row);
        nop (trcd);

        write           (r_bank, r_col, 0, 0, 0, r_data);
        nop (wl + bl/2 + twtr);

        read            (r_bank, r_col, 0, 0);
        nop (rl + bl/2);

        precharge       (r_bank, 0);
        nop (trp);
end

        nop (20);


/*        
        activate        (0, 0);                         // Activate Bank 0, Row 0
        nop             (trcd);
        $display ("READ (BL4) to WRITE (BL4)");
        read            (0, 0, 0, 0);
        nop             (rl + tccd/2 + 1 - wl);
        write           (0, 0, 0, 0, 0, 10);
        $display ("Consecutive WRITE (BL8) to WRITE (BL8)");
        nop             (tccd - 1);
        write           (0, 0, 0, 1, 0, 20);
        nop             (tccd - 1);
        write           (0, 0, 0, 1, 0, 30);
        $display ("Consecutive WRITE (BL4) to WRITE (BL4)");
        nop             (tccd - 1);
        write           (0, 0, 0, 0, 0, 40);
        nop             (tccd - 1);
        write           (0, 0, 0, 0, 0, 50);
        $display ("WRITE (BL4 on the fly) to READ (BL4 on the fly)");
        nop             (cwl + 3 + twtr);
        read_verify     (0, 0, 0, 0, 0, 50);
        nop             (rl + tccd/2 + 1 - wl);
        $display ("READ (BL4) to WRITE (BL8)");
        write           (0, 0, 0, 1, 0, 10);
        nop             (cwl + 3 + twtr);
        $display ("WRITE (BL8) to READ (BL4)");
        read_verify     (0, 0, 1, 0, 0, 10);
        nop             (al + trtp + trp);

        $display ("tRRD Timing");
        activate        (0, 0);
        nop             (trrd - 1);
        activate        (1, 0);
        nop             (trrd - 1);
        activate        (2, 0);
        nop             (trrd - 1);
        activate        (3, 0);
        nop             (trcd - 1);

        $display ("Consecutive Writes");
        write           (0, 0, 0, 1, 0, d0);
        nop             (tccd - 1);
        write           (1, 0, 0, 1, 0, d1);
        nop             (tccd - 1);
        write           (2, 0, 0, 1, 0, d2);
        nop             (tccd - 1);
        write           (3, 0, 0, 1, 0, d3);
        nop             (wl + bl/2 + twtr);

        $display ("Consecutive Reads");
        read_verify     (0, 0, 0, 1, 0, d0);
        nop             (tccd - 1);
        read_verify     (1, 0, 0, 1, 0, d1);
        nop             (tccd - 1);
        read_verify     (2, 0, 0, 1, 0, d2);
        nop             (tccd - 1);
        read_verify     (3, 0, 0, 1, 0, d3);
        nop             (rl + bl/2);

        $display ("Non Consecutive Writes");
        write           (0, 0, 0, 1, 0, d0);
        nop             (tccd);
        write           (1, 0, 0, 1, 0, d1);
        nop             (tccd);
        write           (2, 0, 0, 1, 0, d2);
        nop             (tccd);
        write           (3, 0, 0, 1, 0, d3);
        nop             (wl + bl/2 + twtr);

        $display ("Non Consecutive Reads");
        read_verify     (0, 0, 1, 1, 0, d0);
        nop             (tccd);
        read_verify     (1, 0, 1, 1, 0, d1);
        nop             (tccd);
        read_verify     (2, 0, 1, 1, 0, d2);
        nop             (tccd);
        read_verify     (3, 0, 1, 1, 0, d3);
        nop             (max(rl + bl/2, al + trtp + trp - 1));

        // POWER DOWN SECTION
        odt_out         <= 1'b0;
        odt_out         <= #(50*tck) 1'b1;
        odt_out         <= #((50 + BL_MAX)*tck) 1'b0;
        refresh;
        power_down      (trfc);
        nop             (txp);
        self_refresh    (trfc);
        nop             (txsdll);

        $display ("Power-Down Entry after WRITE /w AP (WRA)");
        load_mode       (0, {14'b0_0_000_0_0_000_1_0_10} | mr_wr<<9 | mr_cl<<2); // Mode Register with Burst Chop

        nop             (tmod-1);
        activate        (0, 0);                         // Activate Bank 0, Row 0
        nop             (trcd-1);
        write           (0, 0, 1, 0, 0, 10);
        nop             (wl + bl/2 + twr-1);
        power_down      (tcke-1);
        nop             (txpdll);


        $display ("refresh to power down re-entry");
        refresh;
        power_down      (tcke-1);
        nop             (trfc-tcke);
        power_down      (tcke-1);
        nop             (txp);

        $display ("Power-Down Exit to Refresh to Power-Down Entry");
        refresh;
        nop             (txpdll-txp-1);
        power_down      (tcke-1);
        nop             (trfc-txp);

        $display ("Change Frequency during Precharge Power-down");
        original_tck    <= tck;
        pd_change_period (TCK_MAX);
        nop             (tcke + 1);

        $display ("Change Frequency during Self Refresh");
        sr_change_period (original_tck);
        nop             (txsdll);

        // multipurpose register section
        // pre-defined pattern
        load_mode       (3, 14'b00000000000100);
        nop             (tmod);
        read            (0, 0, 0, 1);
        nop             (rl + bl/2 + trtp);

        load_mode       (3, 14'b00000000000000);
        nop             (tmod);

        // self refresh with ck off
        cke             <= 1'b0;
        self_refresh    (tcksre);
        assign          ck = 0;
        # (trfc*tck);
        deassign        ck;
        ck              <= 1'b1;
        # ((tcksrx + 0.5)*tck);
        nop             (txsdll + 1);

        // write levelization section
        load_mode       (2, {14'b00000000_000_000} | mr_cwl<<3); // Extended Mode Register 2 with DCC Disable
        nop             (tmrd - 1);
        load_mode       (1, 14'b00000010010110);
        nop             (tmod);
        odt_out         <= 1'b1;
        nop             (TWLDQSEN - tmod);
        dqs_en          <= 1'b1;
        dqs_out         <= {DQS_BITS{1'b0}};
        nop             (TWLMRD - TWLDQSEN);
        dqs_out         <= #(TWLH + 1)         {DQS_BITS{1'b1}};
        dqs_out         <= #(TWLH + tck/2 + 1) {DQS_BITS{1'b0}};
        nop             (16);
        dqs_out         <= #(TWLH + tck/2 + 1) {DQS_BITS{1'b1}};
        dqs_out         <= #(TWLH + tck + 1)   {DQS_BITS{1'b0}};
        odt_out         <= 1'b0;
        nop             (wl - 1);                       // ODTLoff + tAOF
        load_mode       (1, 14'b00000000010110);
        dqs_en          <= 1'b0;
        nop             (tmod);

        power_up;
        nop             (txp);
        // INITIALIZE SECTION
        
        zq_calibration  (1);                            // perform Long ZQ Calibration
        load_mode       (3, 14'b00000000000000);        // Extended Mode Register (3)
        nop             (tmrd - 1);
        
        load_mode       (2, {14'b00001000_000_000} | mr_cwl<<3); // Extended Mode Register 2 with DCC Disable
        nop             (tmrd - 1);
        
        load_mode       (1, 14'b0000010110);            // Extended Mode Register with DLL Enable, AL=CL-1
        nop             (tmrd - 1);
        
        load_mode       (0, {14'b0_0_000_1_0_000_1_0_01} | mr_wr<<9 | mr_cl<<2); // Mode Register with DLL Reset

        nop             (tdllk);

        odt_out         <= 1'b1;
        activate        (0, 0);                         // Activate Bank 0, Row 0
        nop             (trcd);
        read            (0, 1, 1, 1);
        nop             (rl + bl/2 + trtp + trp);

`ifdef TRUEBL4
        // true BL4 section
        odt_out         <= 1'b0;
        nop             (wl - 1);                       // ODTLoff + tAOF
        load_mode       (1, 14'b00000000000110);        // Extended Mode Register with DLL Enable, AL=0
        nop             (tmrd - 1);
        load_mode       (0, {14'b0_0_000_0_0_000_0_0_11} | mr_wr<<9 | mr_cl<<2); // Mode Register with true BL4
        nop             (tmod - 1);
        odt_out         <= 1'b1;

        $display ("tRRD Timing in True BL4 Mode");
        activate        (0, 0);
        nop             (trrd_dg - 1);
        activate        (2, 0);
        nop             (max(trcd - trrd_dg - 1, trcd - tccd_dg - 1));
        $display ("Consecutive True BL4 Writes");
        write           (0, 0, 0, 0, 0, d0);
        nop             (tccd_dg - 1);
        write           (2, 0, 0, 0, 0, d1);
        nop             (tccd_dg - 1);
        write           (0, 0, 0, 0, 0, d2);
        nop             (tccd_dg - 1);
        write           (2, 0, 0, 0, 0, d3);
        nop             (wl + bl/2 + twtr_dg);

        $display ("Consecutive True BL4 Reads");
        read_verify     (0, 0, 0, 0, 0, d2);
        nop             (tccd_dg - 1);
        read_verify     (2, 0, 0, 0, 0, d3);
        nop             (rl + bl/2);

        $display ("Non Consecutive True BL4 Writes");
        write           (0, 0, 0, 0, 0, d0);
        nop             (tccd_dg);
        write           (2, 0, 0, 0, 0, d1);
        nop             (tccd_dg);
        write           (0, 0, 0, 0, 0, d2);
        nop             (tccd_dg);
        write           (2, 0, 0, 0, 0, d3);
        nop             (wl + bl/2 + twtr_dg);

        $display ("Non Consecutive True BL4 Reads");
        read_verify     (0, 0, 0, 0, 0, d2);
        nop             (tccd_dg);
        read_verify     (2, 0, 0, 0, 0, d3);
        nop             (rl + tccd_dg/2 + 2 - wl - 1);

        $display ("True BL4 Write to Read (Same Group)");
        write           (0, 0, 0, 0, 0, d0);
        nop             (wl + bl/2 + twtr - 1);
        read_verify     (0, 0, 0, 0, 0, d0);
        nop             (rl + tccd_dg/2 + 2 - wl - 1);

        $display ("True BL4 Write to Read (Different Group)");
        write           (2, 0, 0, 0, 0, d1);
        nop             (wl + bl/2 + twtr_dg - 1);
        read_verify     (0, 0, 0, 0, 0, d0);
        nop             (rl + bl/2);
`endif
*/

        test_done;
    end
