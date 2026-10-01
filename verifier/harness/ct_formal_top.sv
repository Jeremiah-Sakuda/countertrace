// Countertrace trusted formal monitor (sync-fifo-v1).
// Independent reference queue; authored separately from any DUT or repair.
//
// Step convention: solver step t applies the inputs present at step t to
// rising edge t. Monitor state and DUT outputs at step t are post-edge values
// of edge t-1, so assertions at step t >= 1 check application cycle t-1.
// past_valid guards every check before the first edge has occurred.
`default_nettype none
module ct_formal_top #(
    parameter integer DEPTH = 4,
    parameter integer WIDTH = 8
) (
    input wire             clk,
    input wire             rst,
    input wire             wr_en,
    input wire             rd_en,
    input wire [WIDTH-1:0] din
);
    wire [WIDTH-1:0] dout;
    wire             full;
    wire             empty;

    `CT_DUT #(.DEPTH(DEPTH), .WIDTH(WIDTH)) dut (
        .clk(clk), .rst(rst), .wr_en(wr_en), .rd_en(rd_en),
        .din(din), .dout(dout), .full(full), .empty(empty)
    );

    localparam integer AW = $clog2(DEPTH);

    reg              past_valid = 1'b0;
    reg              released   = 1'b0;
    reg [WIDTH-1:0]  ref_mem [0:DEPTH-1];
    reg [AW-1:0]     ref_head;
    reg [AW:0]       ref_count;
    reg              exp_valid;
    reg [WIDTH-1:0]  exp_dout;
    reg [AW+1:0]     writes_seen;
    reg [AW+1:0]     reads_seen;

    wire          ref_empty = (ref_count == 0);
    wire          ref_full  = (ref_count == DEPTH);
    wire          acc_rd    = !rst && rd_en && !ref_empty;
    wire          acc_wr    = !rst && wr_en && !ref_full;
    wire [AW-1:0] ref_tail  = ref_head + ref_count[AW-1:0];

    // Environment assumption: reset at the first sampled edge. Inputs only.
    always @(*) if (!past_valid) assume (rst);

    always @(posedge clk) begin
        past_valid <= 1'b1;
        if (rst) begin
            ref_head    <= 0;
            ref_count   <= 0;
            exp_valid   <= 1'b0;
            writes_seen <= 0;
            reads_seen  <= 0;
        end else begin
            released  <= 1'b1;
            exp_valid <= acc_rd;
            if (acc_rd) begin
                exp_dout <= ref_mem[ref_head];
                ref_head <= ref_head + 1'b1;
            end
            if (acc_wr)
                ref_mem[ref_tail] <= din;
            ref_count <= ref_count + {{AW{1'b0}}, acc_wr} - {{AW{1'b0}}, acc_rd};
            if (acc_wr && writes_seen != DEPTH) writes_seen <= writes_seen + 1'b1;
            if (acc_rd && reads_seen != DEPTH) reads_seen <= reads_seen + 1'b1;
        end
    end

    // Core checks: flags against reference occupancy; data only after an accepted read.
    always @(*) begin
        if (past_valid) begin
            ct_empty_flag: assert (empty == ref_empty);
            ct_full_flag:  assert (full == ref_full);
            if (exp_valid)
                ct_read_data: assert (dout == exp_dout);
        end
    end

    // Reachability of contract rows at the edge of the current step.
    always @(*) begin
        if (past_valid && !rst) begin
            cov_reset_release:  cover (1'b1);
            cov_write_accepted: cover (acc_wr);
            cov_read_accepted:  cover (acc_rd);
            cov_full:           cover (ref_full);
            cov_write_full:     cover (wr_en && !rd_en && ref_full);
            cov_read_empty:     cover (rd_en && !wr_en && ref_empty);
            cov_both_empty:     cover (wr_en && rd_en && ref_empty);
            cov_both_mid:       cover (wr_en && rd_en && !ref_empty && !ref_full);
            cov_both_full:      cover (wr_en && rd_en && ref_full);
            cov_wrap_write:     cover (acc_wr && writes_seen == DEPTH);
            cov_wrap_read:      cover (acc_rd && reads_seen == DEPTH);
        end
        if (past_valid && released && rst)
            cov_recurrent_reset: cover (1'b1);
    end
endmodule
`default_nettype wire
