"""Model-written checks: catalog, trusted compiler, and inventory, without Docker."""

import unittest

from countertrace.checks import modules
from countertrace.checks.compile import PropertyError, compile_checker, compile_miter, compile_mutant_wrapper, validate
from countertrace.checks.gate import failed_properties, inventory, unreached_triggers

FIFO = modules.load("sync_fifo")
ARB = modules.load("rr_arbiter")


def props(*items, **extra):
    return {"properties": [{"id": f"p{i}", "when": w, "then": t} for i, (w, t) in enumerate(items)], **extra}


class CatalogTest(unittest.TestCase):
    def test_catalog_loads_and_never_exposes_the_golden(self):
        ids = [m.id for m in modules.catalog()]
        self.assertIn("sync_fifo", ids)
        self.assertIn("rr_arbiter", ids)
        for module in modules.catalog():
            public = module.public()
            self.assertNotIn("golden", " ".join(public))
            self.assertNotIn(module.golden.strip()[:60], str(public))
            self.assertGreaterEqual(len(module.params), 2, "the gate needs two parameter settings")

    def test_widths_follow_parameters(self):
        self.assertEqual(ARB.widths({"N": 3})["req"], 3)
        self.assertEqual(FIFO.widths({"DEPTH": 2, "WIDTH": 8})["din"], 8)
        with self.assertRaises(modules.CatalogError):
            modules.load("../modules/rr_arbiter")


class CompileTest(unittest.TestCase):
    def assert_rejected(self, p, module=FIFO):
        with self.assertRaises(PropertyError):
            compile_checker(p, module)

    def test_injection_and_escape_attempts_are_rejected(self):
        for when, then in [
            ("1'b1", "1); assume(0"),           # statement terminator
            ("1'b1", "$finish"),                 # system task
            ("1'b1", "$display(full)"),
            ("1'b1", "dut.count == 0"),          # hierarchical reference
            ("1'b1", "full // comment"),
            ("1'b1", "\"text\" == 0"),
            ("`define X", "full"),
            ("1'b1", "assume"),
            ("1'b1", "ct_past0 == 0"),           # reserved generated name
            ("1'b1", "past_valid"),
            ("1'b1", "nonexistent_signal"),
        ]:
            with self.subTest(then=then, when=when):
                self.assert_rejected(props((when, then)))

    def test_names_must_not_collide_or_use_reserved_prefixes(self):
        for state in ({"name": "full", "width": 1, "next": "1'b0"}, {"name": "ct_x", "width": 1, "next": "1'b0"},
                      {"name": "dut", "width": 1, "next": "1'b0"}, {"name": "Bad", "width": 1, "next": "1'b0"},
                      {"name": "wide", "width": 65, "next": "1'b0"}, {"name": "DEPTH", "width": 4, "next": "0"}):
            with self.subTest(state=state):
                self.assert_rejected(props(("1'b1", "!full || !empty"), state=[state]))
        self.assert_rejected({"properties": [{"id": "a", "when": "1", "then": "full"}, {"id": "a", "when": "1", "then": "empty"}]})
        self.assert_rejected({"properties": []})
        self.assert_rejected(props(("1'b1", "full"), extra_field=1))

    def test_helper_widths_may_name_a_parameter(self):
        text = compile_checker(props(("1'b1", "grant == 0 || last != 0"), state=[{"name": "last", "width": "N", "next": "req"}]), ARB)
        self.assertIn("reg [N-1:0] last;", text)
        for width in ("M", "$clog2(N)", 0, 65, True):
            with self.subTest(width=width):
                self.assert_rejected(props(("1'b1", "last == 0"), state=[{"name": "last", "width": width, "next": "req"}]), ARB)

    def test_past_is_lowered_into_named_registers_that_can_be_indexed(self):
        text = compile_checker(props(("|$past(req)", "grant == ($past(req)[0] ? 1 : 0)"), ("$past(req, 2) == 0", "1'b1")), ARB)
        self.assertNotIn("$past", text)
        self.assertIn("ct_past0[0]", text)
        self.assertIn("reg [N-1:0] ct_past0;", text, "delay registers keep the port's parameter width")
        with self.assertRaises(PropertyError):
            compile_checker(props(("$past(req, 9) == 0", "1'b1")), ARB)
        with self.assertRaises(PropertyError):
            compile_checker(props(("$past req", "1'b1")), ARB)

    def test_checker_owns_the_only_assumption_and_labels_every_property(self):
        text = compile_checker(props(("1'b1", "!(full && empty)"), ("$past(rst)", "empty")), FIFO)
        self.assertEqual(text.count("assume ("), 1)
        self.assertEqual(text.count("assert ("), 2)
        self.assertEqual(text.count("cover ("), 2)
        self.assertIn("p_p0: assert", text)
        self.assertIn("r_p1: cover", text)

    def test_miter_qualifies_observed_outputs_on_the_golden(self):
        text = compile_miter(FIFO)
        self.assertIn("if ($past(rd_en && !empty_g && !rst)) eq_dout", text)
        self.assertIn("eq_full: assert (full_g == full_o)", text)
        self.assertIn(".mutsel(`CT_MUTSEL)", compile_mutant_wrapper(FIFO))

    def test_validate_normalizes_without_dropping_properties(self):
        clean = validate(props(("1'b1", "!(full && empty)")), FIFO)
        self.assertEqual(clean["properties"][0]["id"], "p0")
        self.assertEqual(clean["state"], [])


class InventoryTest(unittest.TestCase):
    def netlist(self, cells, module="ct_props_top"):
        return {"modules": {module: {"cells": {name: {"type": "$check", "parameters": {"FLAVOR": flavor}} for name, flavor in cells}}}}

    def test_inventory_must_match_the_compiled_set(self):
        p = validate(props(("1'b1", "!(full && empty)")), FIFO)
        good = [("\\p_p0", "assert"), ("\\r_p0", "cover"), ("$assume$x", "assume")]
        self.assertEqual(inventory(self.netlist(good), p), [])
        self.assertTrue(inventory(self.netlist(good + [("$assume$y", "assume")]), p))
        self.assertTrue(inventory(self.netlist([("\\p_other", "assert"), ("\\r_p0", "cover"), ("$a", "assume")]), p))
        self.assertTrue(inventory(self.netlist(good, module="fifo"), p))

    def test_log_parsers(self):
        self.assertEqual(failed_properties("Assert failed in ct_props_top: p_never_full (props.sv:12)"), ["never_full"])
        # Exact line format from SymbiYosys 0.69 cover mode (smtbmc yices).
        self.assertEqual(unreached_triggers("engine_0: ##   0:00:00  Unreached cover statement at ct_props_top: r_bad_when"), ["bad_when"])


if __name__ == "__main__":
    unittest.main()


class AgentLoopTest(unittest.TestCase):
    """Loop control and feedback with a stubbed model and gate (no Docker, no API key)."""

    def run_loop(self, replies, results, max_rounds=4):
        import tempfile
        from pathlib import Path
        from unittest import mock

        from countertrace.checks import agent

        replies, results, prompts = list(replies), list(results), []

        def structured(task, system, user, validate, max_tokens=None, model_id=None):
            prompts.append(user)
            return replies.pop(0)

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(agent, "output_cap", return_value=16384), \
                mock.patch.object(agent.model, "structured", structured), \
                mock.patch.object(agent.gate, "run_gate", side_effect=lambda *a, **k: results.pop(0)):
            return agent.run_loop(ARB, Path(tmp), {"tag": "test"}, max_rounds=max_rounds), prompts

    ok = {"status": "ok", "result": props(("1'b1", "grant == 0 || |req")), "calls": []}

    def test_feedback_names_the_failure_and_never_includes_the_golden(self):
        golden_fail = {"stage": "golden", "passed": False, "failed": ["subset"], "config": {"id": "p1", "params": {"N": 3}},
                       "trace": [{"step": 0, "inputs": {"rst": 1, "req": 5}, "outputs": {"grant": 0}}]}
        promoted = {"stage": "mutants", "passed": True, "killed": 27, "nonequivalent": 27, "survived": []}
        result, prompts = self.run_loop([self.ok, self.ok], [golden_fail, promoted])
        self.assertEqual((result["status"], result["promoted_round"]), ("promoted", 1))
        self.assertIn("violates subset at N = 3", prompts[1])
        self.assertIn("edge | rst | req | grant", prompts[1])
        golden = ARB.golden
        for line in [l.strip() for l in golden.splitlines() if len(l.strip()) > 20]:
            self.assertNotIn(line, prompts[1])

    def test_format_errors_use_a_round_and_go_back_as_feedback(self):
        bad = {"status": "schema_error", "calls": [{"schema_error": "state 'x' needs a width"}], "detail": "rejected"}
        result, prompts = self.run_loop([bad, bad], [], max_rounds=2)
        self.assertEqual(result["status"], "not_promoted")
        self.assertEqual([r["gate"]["stage"] for r in result["rounds"]], ["format", "format"])
        self.assertIn("state 'x' needs a width", prompts[1])

    def test_survivors_keep_the_loop_going_and_the_best_passing_round_is_promoted(self):
        surviving = {"stage": "mutants", "passed": True, "killed": 25, "nonequivalent": 27, "unresolved": 0,
                     "survived": [{"mutant": 3, "trace": [{"step": 0, "inputs": {"rst": 0, "req": 1}, "outputs_g": {"grant": 1}, "outputs_o": {"grant": 0}}]}]}
        weaker = {**surviving, "killed": 24}
        result, prompts = self.run_loop([self.ok, self.ok], [surviving, weaker], max_rounds=2)
        self.assertEqual((result["status"], result["promoted_round"]), ("promoted", 0))
        self.assertIn("grant (faulty)", prompts[1])

    def test_model_unavailable_stops_without_a_promotion(self):
        result, _ = self.run_loop([{"status": "unavailable", "detail": "no key", "calls": []}], [])
        self.assertEqual(result["status"], "not_promoted")
        self.assertEqual(len(result["rounds"]), 1)
