// Countertrace fixture: known-good synchronous FIFO, extra-wrap-bit pointer style
// with no occupancy register. Authored for Countertrace (MIT) separately from
// fifo_count.v, by the same author. Supported profile: sync-fifo-v1.
`default_nettype none
module fifo #(
    parameter integer DEPTH = 4,
    parameter integer WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst,
    input  wire             wr_en,
    input  wire             rd_en,
    input  wire [WIDTH-1:0] din,
    output reg  [WIDTH-1:0] dout,
    output wire             full,
    output wire             empty
);
    localparam integer AW = $clog2(DEPTH);

    reg [WIDTH-1:0] storage [0:DEPTH-1];
    reg [AW:0]      head;   // read pointer with wrap bit
    reg [AW:0]      tail;   // write pointer with wrap bit

    assign empty = (head[AW-1:0] == tail[AW-1:0]);
    assign full  = (head[AW] != tail[AW]) && (head[AW-1:0] == tail[AW-1:0]);

    wire take = rd_en && !empty;
    wire put  = wr_en && !full;

    always @(posedge clk) begin
        if (rst)
            tail <= 0;
        else if (put) begin
            storage[tail[AW-1:0]] <= din;
            tail <= tail + 1'b1;
        end
    end

    always @(posedge clk) begin
        if (rst)
            head <= 0;
        else if (take) begin
            dout <= storage[head[AW-1:0]];
            head <= head + 1'b1;
        end
    end
endmodule
`default_nettype wire
