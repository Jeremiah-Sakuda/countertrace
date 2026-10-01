// Countertrace trusted simulation harness (sync-fifo-v1).
// Drives one stimulus file through the DUT using the contract sampling
// convention and records post-edge outputs. It makes no pass/fail decision:
// the trusted control service scores the recorded trace against an
// independent reference queue.
`timescale 1ns/1ps
`default_nettype none
module ct_sim_top;
    parameter integer DEPTH = 4;
    parameter integer WIDTH = 8;

    reg              clk   = 1'b0;
    reg              rst   = 1'b0;
    reg              wr_en = 1'b0;
    reg              rd_en = 1'b0;
    reg  [WIDTH-1:0] din   = {WIDTH{1'b0}};
    wire [WIDTH-1:0] dout;
    wire             full;
    wire             empty;

    `CT_DUT #(.DEPTH(DEPTH), .WIDTH(WIDTH)) dut (
        .clk(clk), .rst(rst), .wr_en(wr_en), .rd_en(rd_en),
        .din(din), .dout(dout), .full(full), .empty(empty)
    );

    string  stim_path;
    string  trace_path;
    string  vcd_path;
    integer fi;
    integer fo;
    integer n;
    integer r;
    integer w;
    integer rd;
    integer d;
    integer cycle;

    initial begin
        if (!$value$plusargs("stim=%s", stim_path)) $fatal(1, "missing +stim");
        if (!$value$plusargs("trace=%s", trace_path)) $fatal(1, "missing +trace");
        if ($value$plusargs("vcd=%s", vcd_path)) begin
            $dumpfile(vcd_path);
            $dumpvars(0, ct_sim_top);
        end
        fi = $fopen(stim_path, "r");
        fo = $fopen(trace_path, "w");
        if (fi == 0 || fo == 0) $fatal(1, "cannot open stimulus or trace file");
        $fwrite(fo, "CTTRACE 1 DEPTH=%0d WIDTH=%0d\n", DEPTH, WIDTH);
        cycle = 0;
        forever begin
            n = $fscanf(fi, "%d %d %d %h\n", r, w, rd, d);
            if (n != 4) break;
            // Clock is low: drive inputs and hold them through the rising edge.
            rst   = r[0];
            wr_en = w[0];
            rd_en = rd[0];
            din   = d[WIDTH-1:0];
            #5 clk = 1'b1;
            // Sample after sequential and combinational updates settle.
            #1 $fwrite(fo, "%0d %0d %0d %0d %0h %0h %0d %0d\n",
                       cycle, r, w, rd, din, dout, empty, full);
            #4 clk = 1'b0;
            cycle = cycle + 1;
        end
        $fwrite(fo, "END %0d\n", cycle);
        $fclose(fo);
        $fclose(fi);
        $finish;
    end
endmodule
`default_nettype wire
