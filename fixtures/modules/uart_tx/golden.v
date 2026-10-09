// Golden 8N1 UART transmitter, hand-written for Countertrace.
`default_nettype none
module uart_tx #(
    parameter integer CLKS_PER_BIT = 2
) (
    input  wire       clk,
    input  wire       rst,
    input  wire       start,
    input  wire [7:0] data,
    output reg        tx,
    output reg        busy
);
    reg [7:0] shreg;
    reg [3:0] bit_idx;   // 0 start bit, 1 to 8 data bits, 9 stop bit
    reg [7:0] clk_cnt;

    always @(posedge clk) begin
        if (rst) begin
            tx   <= 1'b1;
            busy <= 1'b0;
        end else if (!busy) begin
            if (start) begin
                busy    <= 1'b1;
                shreg   <= data;
                bit_idx <= 4'd0;
                clk_cnt <= 8'd0;
                tx      <= 1'b0;
            end
        end else if (clk_cnt == CLKS_PER_BIT - 1) begin
            clk_cnt <= 8'd0;
            if (bit_idx == 4'd9) begin
                busy <= 1'b0;
                tx   <= 1'b1;
            end else begin
                bit_idx <= bit_idx + 4'd1;
                tx      <= (bit_idx < 4'd8) ? shreg[bit_idx[2:0]] : 1'b1;
            end
        end else begin
            clk_cnt <= clk_cnt + 8'd1;
        end
    end
endmodule
`default_nettype wire
