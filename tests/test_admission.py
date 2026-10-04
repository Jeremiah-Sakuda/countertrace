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
            "din": {"direction": "input", "bits": list(range(8))}, "dout": {"direction": "output", "bits": list(range(8))},
            "full": {"direction": "output", "bits": [6]}, "empty": {"direction": "output", "bits": [7]}}}}}
        self.assertEqual(check_ports_json(good, "fifo", 8), [])
        bad = {"modules": {"fifo": {"ports": {**good["modules"]["$paramod\\fifo\\DEPTH=4"]["ports"],
                                              "dout": {"direction": "output", "bits": [1]}}}}}
        self.assertTrue(check_ports_json(bad, "fifo", 8))
        self.assertTrue(check_ports_json({"modules": {}}, "fifo", 8))


if __name__ == "__main__":
    unittest.main()
