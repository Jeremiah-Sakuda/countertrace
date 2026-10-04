"""Admission must reject constructs that bypass the harness or diverge between engines."""

import unittest

from countertrace.admission import admit, check_ports_json
from countertrace.catalog import base_source, example_source, examples


class AdmissionTest(unittest.TestCase):
    def test_bundled_examples_are_admitted(self):
        for item in examples()["examples"]:
            with self.subTest(example=item["id"]):
                result = admit(example_source(item))
                self.assertTrue(result.accepted, [d.message for d in result.diagnostics])
                self.assertEqual(result.module, "fifo")

    def assert_rejected(self, source: str, code: str) -> None:
        result = admit(source)
        self.assertFalse(result.accepted)
        self.assertIn(code, {d.code for d in result.diagnostics}, [d.message for d in result.diagnostics])

    def mutate(self, find: str, replace: str) -> str:
        source = base_source("fifo_count.v")
        self.assertIn(find, source)
        return source.replace(find, replace, 1)

    def test_rejects_system_tasks(self):
        self.assert_rejected(self.mutate("assign empty", "always @(posedge clk) $display(1);\n    assign empty"), "system_task")
        self.assert_rejected(self.mutate("assign empty", "always @(posedge clk) $finish;\n    assign empty"), "system_task")

    def test_rejects_dut_authored_properties(self):
        for stmt in ("assume (rst);", "assert (1);", "cover (1);", "restrict (rst);"):
            with self.subTest(stmt=stmt):
                self.assert_rejected(self.mutate("assign empty", f"always @* {stmt}\n    assign empty"), "construct")

    def test_rejects_initial_blocks_and_attributes(self):
        self.assert_rejected(self.mutate("assign empty", "initial count = 0;\n    assign empty"), "construct")
        self.assert_rejected(self.mutate("reg [AW:0]      count;", "(* anyconst *) reg [AW:0] count;"), "attribute")

    def test_rejects_directives_and_includes(self):
        self.assert_rejected('`include "x.vh"\n' + base_source("fifo_count.v"), "directive")
        self.assert_rejected("`define FOO 1\n" + base_source("fifo_count.v"), "directive")

    def test_rejects_clocking_outside_profile(self):
        self.assert_rejected(self.mutate("always @(posedge clk)", "always @(posedge clk or posedge rst)"), "clocking")
        self.assert_rejected(self.mutate("always @(posedge clk)", "always @(negedge clk)"), "construct")

    def test_rejects_interface_changes(self):
        self.assert_rejected(self.mutate("output wire             empty", "output wire             empty,\n    output wire almost_full"), "interface")
        self.assert_rejected(self.mutate("input  wire [WIDTH-1:0] din", "input  wire [7:0] din"), "interface")
        self.assert_rejected(self.mutate("parameter integer DEPTH = 4,", ""), "interface")

    def test_comment_and_string_tricks_cannot_hide_code(self):
        """Regression: `// /*` ... `// */` once hid live code from a two-pass regex stripper."""
        hidden = {
            "line comment opening a block": '    // /*\n    initial begin $system("id"); end\n    // */',
            "string containing //": '    wire [7:0] s = "//"; initial $finish;',
            "block containing //": "    /* // */ initial $finish;",
            "escaped quote in string": '    wire s = "a\\" // "; initial $finish;',
        }
        for name, body in hidden.items():
            with self.subTest(name):
                self.assert_rejected(self.mutate("assign empty", body.lstrip() + "\n    assign empty"), "system_task")
        self.assert_rejected(self.mutate("assign empty", "/* never closed\n    assign empty"), "lexical")
        self.assert_rejected(self.mutate("assign empty", 'wire s = "abc;\n    assign empty'), "lexical")

    def test_rejects_constructs_found_in_review(self):
        """Each case was admitted before an internal review; none produced a false pass downstream."""
        cases = {
            "clock shadowed in a generate block": (
                "wire clk_inv = ~clk;\n    if (1) begin : g\n        wire clk = clk_inv;\n        always @(posedge clk) begin end\n    end\n    assign empty", "interface"),
            "delay": ("always @(posedge clk) #1 count <= count;\n    assign empty", "construct"),
            "level-sensitive event": ("always @(clk) begin end\n    assign empty", "clocking"),
            "qualified event": ("always @(posedge clk iff wr_en) begin end\n    assign empty", "construct"),
            "dual edge": ("always @(edge clk) begin end\n    assign empty", "construct"),
            "wait": ("always @* begin wait (rst); end\n    assign empty", "construct"),
            "defparam": ("defparam x.DEPTH = 2;\n    assign empty", "construct"),
            "assign to input": ("assign rst = 1'b0;\n    assign empty", "interface"),
            "procedural write to input": ("always @(posedge clk) wr_en <= 1'b0;\n    assign empty", "interface"),
            "upward reference": ("wire peek = ct_formal_top.ref_full;\n    assign empty", "construct"),
        }
        for name, (body, code) in cases.items():
            with self.subTest(name):
                self.assert_rejected(self.mutate("assign empty", body), code)

    def test_rejects_input_drives_and_lexical_holes(self):
        """These were once admitted; the elaborated netlist check is the authority for inputs."""
        cases = {
            "input bit in a continuous concatenation": ("wire spare;\n    assign {spare, din[7]} = 2'b00;\n    assign empty", "interface"),
            "input bit in a procedural concatenation": ("reg spare;\n    always @(*) {spare, din[7]} = 2'b00;\n    assign empty", "interface"),
            "escaped hierarchical reference": ("wire peek = ct_formal_top.\\ref_count ;\n    assign empty", "construct"),
            "typedef initializer": ("typedef logic [1:0] t2;\n    t2 q = 2'b01;\n    assign empty", "construct"),
            "var initializer": ("var logic q = 1'b1;\n    assign empty", "construct"),
            "time initializer": ("time t = 5;\n    assign empty", "construct"),
            "labeled generate initializer": ("if (1) begin : g reg x = 1'b1; end\n    assign empty", "construct"),
            "checker": ("checker c; endchecker\n    assign empty", "construct"),
            "let": ("let f(a) = a;\n    assign empty", "construct"),
            "wired-or net": ("wor w;\n    assign empty", "construct"),
        }
        for name, (body, code) in cases.items():
            with self.subTest(name):
                self.assert_rejected(self.mutate("assign empty", body), code)

    def test_combinational_event_controls_are_not_attributes(self):
        body = "reg a1, a2;\n    always @(*) a1 = wr_en;\n    always @ ( * ) a2 = rd_en;\n    assign empty"
        result = admit(self.mutate("assign empty", body))
        self.assertTrue(result.accepted, [d.message for d in result.diagnostics])
        self.assert_rejected(self.mutate("assign empty", "always @(*) a1 = wr_en;\n    (* keep *) wire k;\n    assign empty"), "attribute")

    def test_variable_declaration_initializers_are_rejected_like_initial(self):
        self.assert_rejected(self.mutate("reg [AW:0]      count;", "reg [AW:0]      count = 0;"), "construct")
        self.assert_rejected(self.mutate("reg [AW:0]      count;", "logic [AW:0]    count = '0;"), "construct")
        # Continuous net declarations and localparams stay legal.
        result = admit(self.mutate("assign empty", "wire never = 1'b0;\n    localparam integer TWO = 2;\n    assign empty"))
        self.assertTrue(result.accepted, [d.message for d in result.diagnostics])

    def test_hidden_continuation_port_is_seen(self):
        source = self.mutate("input  wire             rd_en,", "input  wire             rd_en, bypass,")
        self.assert_rejected(source, "interface")
        result = admit(source)
        self.assertIn("bypass", result.ports)
        self.assertEqual(result.ports["bypass"]["direction"], "input")

    def test_independent_fifo_admitted_only_with_its_mapping(self):
        import json
        from pathlib import Path

        root = Path(__file__).resolve().parents[1] / "fixtures" / "independent" / "billdmar"
        source = (root / "sync_fifo.sv").read_bytes()
        self.assertTrue(admit(source, json.loads((root / "interface_map.json").read_text())).accepted)
        self.assertFalse(admit(source).accepted)

    def test_rejects_multiple_modules(self):
        self.assert_rejected(base_source("fifo_count.v") + "\nmodule other; endmodule\n", "structure")

    def test_size_and_encoding_limits(self):
        self.assert_rejected(b"\xff\xfe" + base_source("fifo_count.v").encode(), "encoding")
        self.assert_rejected("// x\n" * 70000, "size")
        self.assert_rejected("wire a;\n" * 501, "size")

    def test_elaborated_port_check(self):
        good = {"modules": {"$paramod\\fifo\\DEPTH=4": {"ports": {
            "clk": {"direction": "input", "bits": [2]}, "rst": {"direction": "input", "bits": [3]},
            "wr_en": {"direction": "input", "bits": [4]}, "rd_en": {"direction": "input", "bits": [5]},
            "din": {"direction": "input", "bits": list(range(6, 14))}, "dout": {"direction": "output", "bits": list(range(20, 28))},
            "full": {"direction": "output", "bits": [30]}, "empty": {"direction": "output", "bits": [31]}}}}}
        self.assertEqual(check_ports_json(good, "fifo", 8), [])
        bad = {"modules": {"fifo": {"ports": {**good["modules"]["$paramod\\fifo\\DEPTH=4"]["ports"],
                                              "dout": {"direction": "output", "bits": [1]}}}}}
        self.assertTrue(check_ports_json(bad, "fifo", 8))
        self.assertTrue(check_ports_json({"modules": {}}, "fifo", 8))

    def test_elaborated_inputs_must_be_free_nets(self):
        """Input bits tied to constants, aliased to other inputs, or driven by cells are rejected."""
        def netlist(din_bits, cells=None):
            ports = {"clk": {"direction": "input", "bits": [2]}, "rst": {"direction": "input", "bits": [3]},
                     "wr_en": {"direction": "input", "bits": [4]}, "rd_en": {"direction": "input", "bits": [5]},
                     "din": {"direction": "input", "bits": din_bits},
                     "dout": {"direction": "output", "bits": list(range(20, 28))},
                     "full": {"direction": "output", "bits": [30]}, "empty": {"direction": "output", "bits": [31]}}
            return {"modules": {"fifo": {"ports": ports, "cells": cells or {}}}}

        free = list(range(6, 14))
        self.assertEqual(check_ports_json(netlist(free), "fifo", 8), [])
        tied = check_ports_json(netlist(free[:7] + ["0"]), "fifo", 8)
        self.assertEqual([d.message for d in tied], ["Input din[7] is tied to a constant inside the design."])
        aliased = check_ports_json(netlist(free[:7] + [4]), "fifo", 8)
        self.assertTrue(any("connected to input" in d.message for d in aliased))
        cell = {"$and": {"type": "$and", "port_directions": {"A": "input", "B": "input", "Y": "output"},
                         "connections": {"A": [2], "B": [3], "Y": [13]}}}
        driven = check_ports_json(netlist(free, cell), "fifo", 8)
        self.assertEqual([d.message for d in driven], ["Input din[7] is driven inside the design."])


if __name__ == "__main__":
    unittest.main()
