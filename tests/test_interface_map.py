"""Interface mappings are declarative, validated, and never adapter code."""

import unittest

from countertrace import interface_map
from countertrace.admission import admit
from countertrace.catalog import base_source

MAP = {
    "module": "q", "parameters": {"DEPTH": "N", "WIDTH": "W"},
    "ports": {"clk": "ck", "rst": "rst_n", "wr_en": "push", "rd_en": "pop",
              "din": "d", "dout": "q_o", "full": "f", "empty": "e"},
    "reset_active_low": True, "unused_outputs": ["level"],
}
SOURCE = """module q #(parameter int N = 4, parameter int W = 8) (
    input wire ck, input wire rst_n, input wire push, input wire pop,
    input wire [W-1:0] d, output reg [W-1:0] q_o, output wire f, output wire e, output wire [2:0] level);
    if (W < 1) begin : g_chk
        $error("W must be positive: assert this");
    end
    always @(posedge ck) begin end
endmodule
"""


class InterfaceMapTest(unittest.TestCase):
    def test_valid_mapping_admits_and_generates_fixed_wrapper(self):
        result = admit(SOURCE, MAP)
        self.assertTrue(result.accepted, [d.message for d in result.diagnostics])
        text = interface_map.wrapper(MAP)
        self.assertIn(".rst_n(!rst)", text)
        self.assertIn(".level()", text)
        self.assertIn("module ct_map_dut", text)

    def test_rejects_malformed_mappings(self):
        bad = [
            {**MAP, "module": "q; initial $finish"},
            {**MAP, "ports": {**MAP["ports"], "din": "d)(.x"}},
            {**MAP, "ports": {k: v for k, v in MAP["ports"].items() if k != "full"}},
            {**MAP, "ports": {**MAP["ports"], "full": "e"}},
            {**MAP, "unused_outputs": ["d"]},
            {**MAP, "parameters": {"DEPTH": "N"}},
            {**MAP, "adapter": "assign x = y;"},
            {**MAP, "reset_active_low": "yes"},
        ]
        for mapping in bad:
            with self.subTest(mapping=mapping):
                with self.assertRaises(interface_map.MappingError):
                    interface_map.validate(mapping)

    def test_admission_checks_mapped_interface(self):
        self.assertFalse(admit(SOURCE).accepted)  # canonical names are still required without a map
        self.assertFalse(admit(SOURCE.replace("output wire f", "input wire f"), MAP).accepted)
        self.assertFalse(admit(SOURCE.replace(", output wire [2:0] level", ""), MAP).accepted)
        self.assertFalse(admit(base_source("fifo_count.v"), MAP).accepted)

    def test_severity_task_messages_are_not_scanned_as_code(self):
        self.assertFalse(any(d.code == "construct" for d in admit(SOURCE, MAP).diagnostics))
        self.assertFalse(admit(SOURCE.replace("$error", "$fopen"), MAP).accepted)


if __name__ == "__main__":
    unittest.main()
