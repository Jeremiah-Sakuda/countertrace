// Golden debouncer, hand-written for Countertrace.
`default_nettype none
module debouncer #(
    parameter integer STABLE = 3
) (
    input  wire clk,
    input  wire rst,
    input  wire noisy,
    output reg  clean,
    output reg  changed
);
    reg [5:0] cnt;   // consecutive edges at which noisy differed from clean

    always @(posedge clk) begin
        if (rst) begin
            clean   <= 1'b0;
            changed <= 1'b0;
            cnt     <= 6'd0;
        end else begin
            changed <= 1'b0;
            if (noisy == clean)
                cnt <= 6'd0;
            else if (cnt == STABLE - 1) begin
                clean   <= noisy;
                changed <= 1'b1;
                cnt     <= 6'd0;
            end else
                cnt <= cnt + 6'd1;
        end
    end
endmodule
`default_nettype wire
