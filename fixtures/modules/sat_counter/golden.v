// Golden saturating up/down counter with load, hand-written for Countertrace.
`default_nettype none
module sat_counter #(
    parameter integer WIDTH = 4
) (
    input  wire             clk,
    input  wire             rst,
    input  wire             inc,
    input  wire             dec,
    input  wire             load,
    input  wire [WIDTH-1:0] load_value,
    output reg  [WIDTH-1:0] count,
    output wire             at_max,
    output wire             at_min
);
    assign at_max = (count == {WIDTH{1'b1}});
    assign at_min = (count == {WIDTH{1'b0}});

    always @(posedge clk) begin
        if (rst)
            count <= {WIDTH{1'b0}};
        else if (load)
            count <= load_value;
        else if (inc && !dec && !at_max)
            count <= count + 1'b1;
        else if (dec && !inc && !at_min)
            count <= count - 1'b1;
    end
endmodule
`default_nettype wire
