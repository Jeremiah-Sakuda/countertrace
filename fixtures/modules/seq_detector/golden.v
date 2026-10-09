// Golden overlapping 4-bit pattern detector, hand-written for Countertrace.
`default_nettype none
module seq_detector #(
    parameter integer PATTERN = 11
) (
    input  wire clk,
    input  wire rst,
    input  wire bit_in,
    output reg  match
);
    reg [3:0] hist;   // last sampled bits, newest in bit 0
    reg [2:0] seen;   // bits sampled since reset, saturating at 4

    wire [3:0] next_hist = {hist[2:0], bit_in};

    always @(posedge clk) begin
        if (rst) begin
            hist  <= 4'd0;
            seen  <= 3'd0;
            match <= 1'b0;
        end else begin
            hist  <= next_hist;
            if (seen != 3'd4)
                seen <= seen + 3'd1;
            match <= (seen >= 3'd3) && (next_hist == (PATTERN & 15));
        end
    end
endmodule
`default_nettype wire
