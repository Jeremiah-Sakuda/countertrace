// Countertrace evaluation fixture: synchronous FIFO with registered full/empty
// flags and no occupancy counter, a common learner style. Authored for
// Countertrace (MIT) on 2026-10-04 for eval-v2. Supported profile: sync-fifo-v1.
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

    reg [WIDTH-1:0] ram [0:DEPTH-1];
    reg [AW-1:0]    wp;
    reg [AW-1:0]    rp;
    reg             full_r;
    reg             empty_r;

    assign full  = full_r;
    assign empty = empty_r;

    wire          push    = wr_en && !full_r;
    wire          pop     = rd_en && !empty_r;
    wire [AW-1:0] wp_next = wp + 1'b1;
    wire [AW-1:0] rp_next = rp + 1'b1;

    always @(posedge clk) begin
        if (rst) begin
            wp      <= 0;
            rp      <= 0;
            full_r  <= 1'b0;
            empty_r <= 1'b1;
        end else begin
            if (push) begin
                ram[wp] <= din;
                wp      <= wp_next;
            end
            if (pop) begin
                dout <= ram[rp];
                rp   <= rp_next;
            end
            case ({push, pop})
                2'b10: begin
                    empty_r <= 1'b0;
                    full_r  <= (wp_next == rp);
                end
                2'b01: begin
                    full_r  <= 1'b0;
                    empty_r <= (rp_next == wp);
                end
                2'b11: begin
                    full_r  <= (wp_next == rp_next);
                    empty_r <= (rp_next == wp_next);
                end
                default: begin
                    full_r  <= full_r;
                    empty_r <= empty_r;
                end
            endcase
        end
    end
endmodule
`default_nettype wire
