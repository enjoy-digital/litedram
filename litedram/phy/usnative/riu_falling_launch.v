//
// This file is part of LiteDRAM.
//
// SPDX-License-Identifier: BSD-2-Clause

// Upstream rising-edge registers retain the complete RIU/reset contract.
// Capturing their values at the falling edge preserves each native rising-edge
// sample. No separate reset is introduced that could change an in-flight write.
module usnative_riu_falling_launch #(parameter WIDTH=45)(
    input wire clk,
    input wire [WIDTH-1:0] payload,
    output reg [WIDTH-1:0] launch = {WIDTH{1'b0}}
);
    always @(negedge clk) launch <= payload;
endmodule
