//
// This file is part of LiteDRAM.
//
// SPDX-License-Identifier: BSD-2-Clause

// Behavioral RIU backend and edge-sampling testbench; not a vendor primitive model.
`timescale 1ns/1ps
module backend(input clk,input reset,input [25:0] p,input enable,input [7:0] delay,
output [1:0] valid,output [31:0] rdata);
reg [7:0] pending=0;
reg [15:0] shadow=0,mem=16'h1234,rd=0;
wire [2:0] sel=p[8:6];
assign valid=(enable && pending==0)?2'b11:0;
assign rdata={rd,rd};
always @(posedge clk) begin
  if(reset) begin pending<=0;mem<=16'h1234;rd<=0;end
  else begin
    rd<=mem;
    if(pending!=0) begin pending<=pending-1;if(pending==1)mem<=shadow;end
    if(p[25] && sel!=0) begin
      if(valid==0)$fatal(1,"write while unavailable");
      pending<=delay;shadow<=p[24:9];
    end
  end
end
endmodule
module tb;
reg sys_clk=0,riu_clk=0;
always #5 sys_clk=~sys_clk;
always #10 riu_clk=~riu_clk;
reg sys_rst=1,riu_rst=1,request=0,write=0,reset=0;
reg [5:0] address=0;
reg [1:0] select=0;
reg [15:0] wdata=0;
reg enable=0;
reg [7:0] delay=2;
wire [25:0] pa,pb,launch;
wire ba,bb,va,vb,ea,eb;
wire [15:0] ra,rb;
wire [31:0] da,db;
wire [1:0] na,nb;
bridge original(.sys_clk(sys_clk),.riu_clk(riu_clk),.sys_rst(sys_rst),.riu_rst(riu_rst),
.request(request),.write(write),.reset(reset),.address(address),.select(select),.wdata(wdata),
.busy(ba),.valid(va),.error(ea),.rdata(ra),.native_address(pa[5:0]),.native_select(pa[8:6]),
.native_wdata(pa[24:9]),.native_write(pa[25]),.native_rdata(da),.native_valid(na));
bridge staged(.sys_clk(sys_clk),.riu_clk(riu_clk),.sys_rst(sys_rst),.riu_rst(riu_rst),
.request(request),.write(write),.reset(reset),.address(address),.select(select),.wdata(wdata),
.busy(bb),.valid(vb),.error(eb),.rdata(rb),.native_address(pb[5:0]),.native_select(pb[8:6]),
.native_wdata(pb[24:9]),.native_write(pb[25]),.native_rdata(db),.native_valid(nb));
usnative_riu_falling_launch #(.WIDTH(26)) boundary(riu_clk,pb,launch);
backend a(riu_clk,riu_rst,pa,enable,delay,na,da);
backend b(riu_clk,riu_rst,launch,enable,delay,nb,db);
integer samples=0;
always @(posedge riu_clk) begin
  if(pa!==launch)$fatal(1,"native rising-edge contract differs t=%0t a=%h b=%h",$time,pa,launch);
  samples=samples+1;
  #1;if(da!==db || na!==nb)$fatal(1,"backend response differs");
end
always @(negedge sys_clk) begin
  if({ba,va,ea,ra}!=={bb,vb,eb,rb})$fatal(1,"CSR behavior differs");
end
task issue;
 input wr;input [15:0] data;
 begin
 @(negedge sys_clk);write=wr;wdata=data;request=1;
 @(negedge sys_clk);request=0;
 end
endtask
task finish;
 integer i;
 begin
 i=0;while(ba && i<400)begin @(negedge sys_clk);i=i+1;end
 if(i==400)$fatal(1,"request stuck");
 repeat(3)@(negedge sys_clk);
 end
endtask
integer k;
initial begin
 #37;sys_rst=0;riu_rst=0;
 // Initially unavailable: payload must wait; completion then succeeds.
 issue(1,16'hbeef);
 repeat(25)@(negedge sys_clk);
 enable=1;finish;
 if(!va || ea || ra!==16'hbeef)$fatal(1,"normal response wrong");
 delay=12;issue(1,16'h5678);finish;
 if(!va || ea || ra!==16'h5678)$fatal(1,"delayed response wrong");
 issue(0,0);finish;
 if(!va || ra!==16'h5678)$fatal(1,"fresh read wrong");
 // Soft cancellation during preissue and during native write.
 enable=0;issue(1,16'hcccc);#7;reset=1;
 repeat(80)@(negedge sys_clk);reset=0;enable=1;
 repeat(20)@(negedge sys_clk);if(va)$fatal(1,"stale valid after cancel");
 issue(1,16'hdddd);repeat(15)@(negedge sys_clk);reset=1;
 repeat(80)@(negedge sys_clk);reset=0;
 // Hard reset transitions at offsets around both RIU edges.
 for(k=1;k<20;k=k+3) begin
 issue(1,k);#(k);sys_rst=1;riu_rst=1;
 #43;sys_rst=0;riu_rst=0;
 repeat(30)@(negedge sys_clk);
 end
 delay=2;issue(1,16'h9876);finish;
 if(!va || ea || ra!==16'h9876)$fatal(1,"reset recovery wrong");
 $display("PASS native edge samples=%0d",samples);$finish;
end
initial begin #100000;$fatal(1,"test timed out");end
endmodule
