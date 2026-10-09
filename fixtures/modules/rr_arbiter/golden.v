// Golden round-robin arbiter, hand-written for the spike. N requesters, registered one-hot grant.
`default_nettype none
module rr_arbiter #(
    parameter integer N = 4
) (
    input  wire         clk,
    input  wire         rst,
    input  wire [N-1:0] req,
    output reg  [N-1:0] grant
);
    // last: index of the most recent grant; the search starts just after it.
    reg [$clog2(N)-1:0] last;
    integer i;
    reg found;
    reg [$clog2(N)-1:0] pick;
    always @(*) begin
        found = 1'b0;
        pick = last;
        for (i = 1; i <= N; i = i + 1) begin
            if (!found && req[(last + i) % N]) begin
                found = 1'b1;
                pick = (last + i) % N;
            end
        end
    end
    always @(posedge clk) begin
        if (rst) begin
            grant <= {N{1'b0}};
            last  <= N - 1;
        end else if (found) begin
            grant <= {{(N-1){1'b0}}, 1'b1} << pick;
            last  <= pick;
        end else begin
            grant <= {N{1'b0}};
        end
    end
endmodule
`default_nettype wire
