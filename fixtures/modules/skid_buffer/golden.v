// Golden two-entry skid buffer, hand-written for Countertrace. Registered ready and valid.
`default_nettype none
module skid_buffer #(
    parameter integer WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst,
    input  wire             in_valid,
    input  wire [WIDTH-1:0] in_data,
    output wire             in_ready,
    output wire             out_valid,
    output wire [WIDTH-1:0] out_data,
    input  wire             out_ready
);
    reg             main_valid, skid_valid;
    reg [WIDTH-1:0] main_data, skid_data;

    assign in_ready  = !skid_valid;
    assign out_valid = main_valid;
    assign out_data  = main_data;

    wire accept  = in_valid && in_ready;
    wire deliver = main_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            main_valid <= 1'b0;
            skid_valid <= 1'b0;
        end else if (skid_valid) begin
            // Input is stalled; the skid word moves up once the head is delivered.
            if (deliver) begin
                main_data  <= skid_data;
                skid_valid <= 1'b0;
            end
        end else if (!main_valid || deliver) begin
            main_valid <= accept;
            if (accept)
                main_data <= in_data;
        end else if (accept) begin
            skid_data  <= in_data;
            skid_valid <= 1'b1;
        end
    end
endmodule
`default_nettype wire
