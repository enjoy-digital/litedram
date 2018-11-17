/****************************************************************************************
*
*    File Name:  tb.v
*
* Dependencies:  ddr3.v, ddr3_parameters.vh
*
*  Description:  Micron SDRAM DDR3 (Double Data Rate 3) test bench
*
*         Note: -Set simulator resolution to "ps" accuracy
*               -Set Debug = 0 to disable $display messages
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

module tb;

`ifdef den1024Mb
    `include "1024Mb_ddr3_parameters.vh"
`elsif den2048Mb
    `include "2048Mb_ddr3_parameters.vh"
`elsif den4096Mb
    `include "4096Mb_ddr3_parameters.vh"
`elsif den8192Mb
    `include "8192Mb_ddr3_parameters.vh"
`else
    // NOTE: Intentionally cause a compile fail here to force the users
    //       to select the correct component density before continuing
    ERROR: You must specify component density with +define+den____Mb.
`endif

    // ports
    reg                         rst_n;
    reg                         ck;
    wire                        ck_n = ~ck;
    reg                         cke;
    reg                         cs_n;
    reg                         ras_n;
    reg                         cas_n;
    reg                         we_n;
    reg           [BA_BITS-1:0] ba;
    reg         [ADDR_BITS-1:0] a;
    wire          [DM_BITS-1:0] dm;
    wire          [DQ_BITS-1:0] dq;
    wire          [DQ_BITS-1:0] dq0;
    wire          [DQ_BITS-1:0] dq1;
    wire         [DQS_BITS-1:0] dqs;
    wire         [DQS_BITS-1:0] dqs_n;
    wire         [DQS_BITS-1:0] tdqs_n;
    wire                        odt;
    
    // mode registers
    reg         [ADDR_BITS-1:0] mode_reg0;                                 //Mode Register
    reg         [ADDR_BITS-1:0] mode_reg1;                                 //Extended Mode Register
    reg         [ADDR_BITS-1:0] mode_reg2;                                 //Extended Mode Register 2
    wire                  [3:0] cl       = {mode_reg0[2], mode_reg0[6:4]} + 4;              //CAS Latency
    wire                        bo       = mode_reg0[3];                    //Burst Order
    reg                   [3:0] bl;                                         //Burst Length
    wire                  [3:0] cwl      = mode_reg2[5:3] + 5;              //CAS Write Latency
    wire                  [3:0] al       = (mode_reg1[4:3] === 2'b00) ? 4'h0 : cl - mode_reg1[4:3]; //Additive Latency
    wire                  [4:0] rl       = cl + al;                         //Read Latency
    wire                  [4:0] wl       = cwl + al;                        //Write Latency

    // dq transmit
    reg                         dq_en;
    reg           [DM_BITS-1:0] dm_out;
    reg           [DQ_BITS-1:0] dq_out;
    reg                         dqs_en;
    reg          [DQS_BITS-1:0] dqs_out;
    assign                      dm       = dq_en ? dm_out : {DM_BITS{1'bz}};
    assign                      dq0      = dq_en ? dq_out : {DQ_BITS{1'bz}};
    assign                      dq1      = dq_en ? ~dq_out : {DQ_BITS{1'bz}};
    assign                      dqs      = dqs_en ? dqs_out : {DQS_BITS{1'bz}};
    assign                      dqs_n    = dqs_en ? ~dqs_out : {DQS_BITS{1'bz}};

    // dq receive
    reg           [DM_BITS-1:0] dm_fifo [4*CL_MAX+BL_MAX+2:0];
    reg           [DQ_BITS-1:0] dq_fifo [4*CL_MAX+BL_MAX+2:0];
    wire          [DQ_BITS-1:0] q0, q1, q2, q3;
    reg                         ptr_rst_n;
    reg                   [1:0] burst_cntr;

    // odt
    reg                         odt_out;
    reg     [(AL_MAX+CL_MAX):0] odt_fifo;
    assign                      odt      = odt_out & !odt_fifo[0];

    // timing definition in tCK units
    real                        tck;
    wire                 [11:0] tccd     = TCCD;
    wire                 [11:0] tcke     = max(ceil(TCKE/tck), TCKE_TCK);
    wire                 [11:0] tckesr   = TCKESR_TCK;
    wire                 [11:0] tcksre   = max(ceil(TCKSRE/tck), TCKSRE_TCK);
    wire                 [11:0] tcksrx   = max(ceil(TCKSRX/tck), TCKSRX_TCK);
    wire                 [11:0] tcl_min  = min_cl(tck);
    wire                  [6:2] mr_cl    = (tcl_min - 4)<<2 | (tcl_min/12);
    wire                 [11:0] tcpded   = TCPDED;
    wire                 [11:0] tcwl_min = min_cwl(tck);
    wire                  [5:3] mr_cwl   = tcwl_min - 5;
    wire                 [11:0] tdllk    = TDLLK;
    wire                 [11:0] tfaw     = ceil(TFAW/tck);
    wire                 [11:0] tmod     = max(ceil(TMOD/tck), TMOD_TCK);
    wire                 [11:0] tmrd     = TMRD;
    wire                 [11:0] tras     = ceil(TRAS_MIN/tck);
    wire                 [11:0] trc      = ceil(TRC/tck);
    wire                 [11:0] trcd     = ceil(TRCD/tck);
    wire                 [11:0] trfc     = ceil(TRFC_MIN/tck);
    wire                 [11:0] trp      = ceil(TRP/tck);
    wire                 [11:0] trrd     = max(ceil(TRRD/tck), TRRD_TCK);
    wire                 [11:0] trtp     = max(ceil(TRTP/tck), TRTP_TCK);
    wire                 [11:0] twr      = ceil(TWR/tck);
    wire                 [11:0] twtr     = max(ceil(TWTR/tck), TWTR_TCK);
    wire                 [11:0] txp      = max(ceil(TXP/tck), TXP_TCK);
    wire                 [11:0] txpdll   = max(ceil(TXPDLL/tck), TXPDLL_TCK);
    wire                 [11:0] txpr     = max(ceil(TXPR/tck), TXPR_TCK);
    wire                 [11:0] txs      = max(ceil(TXS/tck), TXS_TCK);
    wire                 [11:0] txsdll   = TXSDLL;
    wire                 [11:0] tzqcs    = TZQCS;
    wire                 [11:0] tzqoper  = TZQOPER;
    wire                 [11:0] wr       = (twr < 8) ? twr : twr + twr%2;
    wire                 [11:9] mr_wr    = (twr < 8) ? (twr - 4) : twr>>1;

`ifdef TRUEBL4
    wire                 [11:0] tccd_dg  = TCCD_DG;
    wire                 [11:0] trrd_dg  = max(ceil(TRRD_DG/tck), TRRD_DG_TCK);
    wire                 [11:0] twtr_dg  = max(ceil(TWTR_DG/tck), TWTR_DG_TCK);
`endif

    initial begin
        $timeformat (-9, 1, " ns", 1);
`ifdef period
        tck <= `period; 
`else
        tck <= ceil(TCK_MIN);
`endif
        ck <= 1'b1;
        odt_fifo <= 0;
    end

    // component instantiation
    ddr3 sdramddr3_0 (
        rst_n,
        ck, 
        ck_n,
        cke, 
        cs_n, 
        ras_n, 
        cas_n, 
        we_n, 
        dm, 
        ba, 
        a, 
        dq0, 
        dqs,
        dqs_n,
        tdqs_n,
        odt
    );

    // clock generator
    always @(posedge ck) begin
      ck <= #(tck/2) 1'b0;
      ck <= #(tck) 1'b1;
    end

    function integer ceil;
        input number;
        real number;
        if (number > $rtoi(number))
            ceil = $rtoi(number) + 1;
        else
            ceil = number;
    endfunction

    function integer max;
        input arg1;
        input arg2;
        integer arg1;
        integer arg2;
        if (arg1 > arg2)
            max = arg1;
        else
            max = arg2;
    endfunction

    task power_up;
        begin
            rst_n   <= 1'b0;
            cke     <= 1'b0;
            cs_n    <= 1'b1;
            odt_out <= 1'b0;
            # (10000); // CKE must be LOW 10ns prior to RST# transitioning HIGH.
            @ (negedge ck) rst_n   = 1'b1;
            # (10000) // After RST# transitions HIGH, wait 500us (minus one clock) with CKE LOW. (wait 10 ns instead of 500 us)
            @ (negedge ck) nop(TXPR/tck + 1); // After CKE is registered HIGH and after tXPR has been satisfied, MRS commands may be issued.
        end
    endtask

    task load_mode;
        input   [BA_BITS-1:0] bank;
        input [ADDR_BITS-1:0] addr;
        begin
            case (bank)
                0: mode_reg0 = addr;
                1: mode_reg1 = addr;
                2: mode_reg2 = addr;
            endcase
            cke   <= 1'b1;
            cs_n  <= 1'b0;
            ras_n <= 1'b0;
            cas_n <= 1'b0;
            we_n  <= 1'b0;
            ba    <= bank;
            a     <= addr;
            @(negedge ck);
        end
    endtask

    task refresh;
        begin
            cke   <= 1'b1;
            cs_n  <= 1'b0;
            ras_n <= 1'b0;
            cas_n <= 1'b0;
            we_n  <= 1'b1;
            @(negedge ck);
        end
    endtask
     
    task precharge;
        input [BA_BITS-1:0] bank;
        input               ap; //precharge all
        begin
            cke   <= 1'b1;
            cs_n  <= 1'b0;
            ras_n <= 1'b0;
            cas_n <= 1'b1;
            we_n  <= 1'b0;
            ba    <= bank;
            a     <= (ap<<10);
            @(negedge ck);
        end
    endtask
     
    task activate;
        input  [BA_BITS-1:0] bank;
        input [ROW_BITS-1:0] row;
        begin
            cke   <= 1'b1;
            cs_n  <= 1'b0;
            ras_n <= 1'b0;
            cas_n <= 1'b1;
            we_n  <= 1'b1;
            ba    <= bank;
            a     <=  row;
            @(negedge ck);
        end
    endtask

    //write task supports burst lengths <= 8
    task write;
        input   [BA_BITS-1:0] bank;
        input  [COL_BITS-1:0] col;
        input                 ap; //Auto Precharge
        input                 bc; //Burst Chop  
        input [8*DM_BITS-1:0] dm;
        input [8*DQ_BITS-1:0] dq;
        reg   [ADDR_BITS-1:0] atemp [2:0];
        integer i;
        begin
            cke   <= 1'b1;
            cs_n  <= 1'b0;
            ras_n <= 1'b1;
            cas_n <= 1'b0;
            we_n  <= 1'b0;
            ba    <= bank;

            atemp[0] = col & 10'h3ff;         //a[ 9: 0] = COL[ 9: 0]
            atemp[1] = ((col>>10) & 1'h1)<<11;//a[   11] = COL[   10]
            atemp[2] = (col>>11)<<13;         //a[ N:13] = COL[ N:11]
            a     <= atemp[0] | atemp[1] | atemp[2] | (ap<<10) | (bc<<12);

            casex ({bc, mode_reg0[1:0]})
                3'bx00, 3'b101:bl=8;
                3'bx1x, 3'b001:bl=4;
            endcase

            dqs_en <= #(wl*tck-tck/2) 1'b1;
            dqs_out <= #(wl*tck-tck/2) {DQS_BITS{1'b1}};
            for (i=0; i<=bl; i=i+1) begin
                dqs_en <= #(wl*tck + i*tck/2) 1'b1;
                if (i%2 == 0) begin
                    dqs_out <= #(wl*tck + i*tck/2) {DQS_BITS{1'b0}};
                end else begin
                    dqs_out <= #(wl*tck + i*tck/2) {DQS_BITS{1'b1}};
                end

                dq_en  <= #(wl*tck + i*tck/2 + tck/4) 1'b1;
                dm_out <= #(wl*tck + i*tck/2 + tck/4) dm>>i*DM_BITS;
                dq_out <= #(wl*tck + i*tck/2 + tck/4) dq>>i*DQ_BITS;
            end
            dqs_en <= #(wl*tck + bl*tck/2 + tck/2) 1'b0;
            dq_en  <= #(wl*tck + bl*tck/2 + tck/4) 1'b0;
            @(negedge ck);  
        end
    endtask

    // read without data verification
    task read;
        input   [BA_BITS-1:0] bank;
        input  [COL_BITS-1:0] col;
        input                 ap; //Auto Precharge
        input                 bc; //Burst Chop  
        reg   [ADDR_BITS-1:0] atemp [2:0];
        integer i;
        begin
            cke   <= 1'b1;
            cs_n  <= 1'b0;
            ras_n <= 1'b1;
            cas_n <= 1'b0;
            we_n  <= 1'b1;
            ba    <= bank;
            atemp[0] = col & 10'h3ff;         //a[ 9: 0] = COL[ 9: 0]
            atemp[1] = ((col>>10) & 1'h1)<<11;//a[   11] = COL[   10]
            atemp[2] = (col>>11)<<13;         //a[ N:13] = COL[ N:11]
            a     <= atemp[0] | atemp[1] | atemp[2] | (ap<<10) | (bc<<12);

            casex ({bc, mode_reg0[1:0]})
                3'bx00, 3'b101:bl=8;
                3'bx1x, 3'b001:bl=4;
            endcase

            for (i=0; i<(bl/2 + 2); i=i+1) begin
                odt_fifo[rl-wl + i] = 1'b1;
            end
            @(negedge ck);
        end
    endtask

    task zq_calibration;
        input long;
        begin
            cke   <= 1'b1;
            cs_n  <= 1'b0;
            ras_n <= 1'b1;
            cas_n <= 1'b1;
            we_n  <= 1'b0;
            ba    <=  0;
            a     <=  long<<10;
            @(negedge ck);
        end
    endtask

    task nop;
        input [31:0] count;
        begin
            cke   <= 1'b1;
            cs_n  <= 1'b0;
            ras_n <= 1'b1;
            cas_n <= 1'b1;
            we_n  <= 1'b1;
            repeat(count) @(negedge ck);
        end
    endtask

    task deselect;
        input [31:0] count;
        begin
            cke   <= 1'b1;
            cs_n  <= 1'b1;
            ras_n <= 1'b1;
            cas_n <= 1'b1;
            we_n  <= 1'b1;
            repeat(count) @(negedge ck);
        end
    endtask

    task power_down;
        input [31:0] count;
        begin
            cke   <= 1'b0;
            cs_n  <= 1'b1;
            ras_n <= 1'b1;
            cas_n <= 1'b1;
            we_n  <= 1'b1;
            repeat(count) @(negedge ck);
        end
    endtask

    task self_refresh;
        input [31:0] count;
        begin
            cke   <= 1'b0;
            cs_n  <= 1'b0;
            ras_n <= 1'b0;
            cas_n <= 1'b0;
            we_n  <= 1'b1;
            cs_n  <= #(tck) 1'b1;
            ras_n <= #(tck) 1'b1;
            cas_n <= #(tck) 1'b1;
            we_n  <= #(tck) 1'b1;
            repeat(count) @(negedge ck);
        end
    endtask

    task pd_change_period;
        input [31:0] new_period;
        begin
            $display ("%m at time %t: INFO: Changing Clock Period to %08.3f ps", $time, new_period);
            power_down (tcksre+1);
            tck <= new_period;
            @(posedge ck);
            @(negedge ck);
            repeat(tcksrx) @(negedge ck);
        end
    endtask

    task sr_change_period;
        input [31:0] new_period;
        begin
            $display ("%m at time %t: INFO: Changing Clock Period to %08.3f ps", $time, new_period);
            self_refresh (tcksre+1);
            tck <= new_period;
            @(posedge ck);
            @(negedge ck);
            repeat(tcksrx) @(negedge ck);
        end
    endtask

    // read with data verification
    task read_verify;
        input   [BA_BITS-1:0] bank;
        input  [COL_BITS-1:0] col;
        input                 ap; //Auto Precharge
        input                 bc; //Burst Chop  
        input [8*DM_BITS-1:0] dm; //Expected Data Mask
        input [8*DQ_BITS-1:0] dq; //Expected Data
        integer i, j;
        begin
            read (bank, col, ap, bc);
            for (i=0; i<bl; i=i+1) begin
                j = (col ^ i)%bl;
                if (!bo) begin 
                    j = (j & -4) + ((col + i) & 3);
                end
                dm_fifo[2*rl + i] = dm>>(i*DM_BITS);
                dq_fifo[2*rl + i] = dq>>(i*DQ_BITS);
            end
        end
    endtask

    // receiver(s) for data_verify process
    dqrx dqrx[DQS_BITS-1:0] (ptr_rst_n, dqs, dq, q0, q1, q2, q3);

    // perform data verification as a result of read_verify task call
    always @(ck) begin:data_verify
        integer i;
        integer j;
        reg [DQ_BITS-1:0] bit_mask;
        reg [DM_BITS-1:0] dm_temp;
        reg [DQ_BITS-1:0] dq_temp;
        
        for (i = !ck; (i < 2/(2.0 - !ck)); i=i+1) begin
            if (dm_fifo[i] === {DM_BITS{1'bx}}) begin
                burst_cntr = 0;
            end else begin

                dm_temp = dm_fifo[i];
                for (j=0; j<DQ_BITS; j=j+1) begin
                    bit_mask[j] = !dm_temp[j/(DQ_BITS/DM_BITS)];
                end

                case (burst_cntr)
                    0: dq_temp =  q0;
                    1: dq_temp =  q1;
                    2: dq_temp =  q2;
                    3: dq_temp =  q3;
                endcase
                //if (((dq_temp & bit_mask) === (dq_fifo[i] & bit_mask)))
                //    $display ("%m at time %t: INFO: Successful read data compare.  Expected = %h, Actual = %h, Mask = %h, i = %d", $time, dq_fifo[i], dq_temp, bit_mask, burst_cntr);
                if ((dq_temp & bit_mask) !== (dq_fifo[i] & bit_mask))
                    $display ("%m at time %t: ERROR: Read data miscompare.  Expected = %h, Actual = %h, Mask = %h, i = %d", $time, dq_fifo[i], dq_temp, bit_mask, burst_cntr);

                burst_cntr = burst_cntr + 1;
            end
        end

        if (!ck) begin
            ptr_rst_n <= (dm_fifo[4] !== {DM_BITS{1'bx}});
            for (i=0; i<=(4*CL_MAX+BL_MAX); i=i+1) begin
                dm_fifo[i] = dm_fifo[i+2];
                dq_fifo[i] = dq_fifo[i+2];
            end
            odt_fifo = odt_fifo>>1;
        end
    end

    // End-of-test triggered in 'subtest.vh'
    task test_done;
        begin
            $display ("%m at time %t: INFO: Simulation is Complete", $time);
            $finish(0);
        end
    endtask

    // Test included from external file
    `include "subtest.vh"

endmodule

module dqrx (
    ptr_rst_n, dqs, dq, q0, q1, q2, q3
);

`ifdef den1024Mb
    `include "1024Mb_ddr3_parameters.vh"
`elsif den2048Mb
    `include "2048Mb_ddr3_parameters.vh"
`elsif den4096Mb
    `include "4096Mb_ddr3_parameters.vh"
`elsif den8192Mb
    `include "8192Mb_ddr3_parameters.vh"
`else
    // NOTE: Intentionally cause a compile fail here to force the users
    //       to select the correct component density before continuing
    ERROR: You must specify component density with +define+den____Mb.
`endif

    input  ptr_rst_n;
    input  dqs;
    input  [DQ_BITS/DQS_BITS-1:0] dq;
    output [DQ_BITS/DQS_BITS-1:0] q0;
    output [DQ_BITS/DQS_BITS-1:0] q1;
    output [DQ_BITS/DQS_BITS-1:0] q2;
    output [DQ_BITS/DQS_BITS-1:0] q3;

    reg [1:0] ptr;
    reg [DQ_BITS/DQS_BITS-1:0] q [3:0];

    reg ptr_rst_dly_n;
    always @(ptr_rst_n) ptr_rst_dly_n <= #(TDQSCK + TDQSQ + 2) ptr_rst_n;

    reg dqs_dly;
    always @(dqs) dqs_dly <= #(TDQSQ + 1) dqs;

    always @(negedge ptr_rst_dly_n or posedge dqs_dly or negedge dqs_dly) begin
        if (!ptr_rst_dly_n) begin
            ptr <= 0;
        end else if (dqs_dly || ptr) begin
            q[ptr] <= dq;
            ptr <= ptr + 1;
        end
    end
    
    assign q0 = q[0];
    assign q1 = q[1];
    assign q2 = q[2];
    assign q3 = q[3];
endmodule
