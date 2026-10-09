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

    def test_every_module_ships_compilable_reference_properties_and_a_split(self):
        splits = {m.split for m in modules.catalog()}
        self.assertEqual(splits, {"development", "heldout"})
        for module in modules.catalog():
            with self.subTest(module=module.id):
                self.assertIn("p_", compile_checker(module.reference_properties, module))

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


class GateEvidenceTest(unittest.TestCase):
    def classify(self, statuses):
        import tempfile
        from pathlib import Path
        from countertrace.checks.gate import classify_mutants
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'mutants').mkdir()
            (root / 'mutants/mutations.ys').write_text('mutation1\nmutation2\n')
            for name, value in statuses.items():
                (root / name).mkdir()
                (root / name / 'status').write_text(value)
            return classify_mutants(root, ARB)

    def test_missing_errors_and_unknowns_never_reduce_the_promotion_denominator(self):
        good = {'mutant_1_props': 'FAIL', 'mutant_1_equiv': 'FAIL'}
        for status in (None, 'ERROR', 'UNKNOWN', 'TIMEOUT'):
            with self.subTest(status=status):
                other = {} if status is None else {'mutant_2_props': 'FAIL', 'mutant_2_equiv': status}
                result = self.classify({**good, **other})
                self.assertFalse(result['passed'])
                self.assertEqual(result['unresolved'], 1)
                self.assertEqual(result['invalid'], 0)

    def test_equivalent_mutant_cannot_count_as_a_kill(self):
        r = self.classify({'mutant_1_props': 'FAIL', 'mutant_1_equiv': 'PASS'})
        self.assertFalse(r['passed'])
        self.assertEqual(r['stage'], 'integrity')

    def test_pass_artifacts_require_complete_successful_process_records(self):
        import tempfile
        from pathlib import Path
        from countertrace.checks.gate import ChecksBatch, GateToolError, validate_steps
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for mode in ('prove', 'cover'):
                (root / f'golden_{mode}_p0').mkdir()
                (root / f'golden_{mode}_p0/status').write_text('PASS')
            batch = ChecksBatch(root, root, 'job', {'stage': 'gate', 'configs': [{'id': 'p0'}]})
            ids = ['checks:inventory:p0', 'checks:golden_prove_p0', 'checks:golden_cover_p0']
            clean = [{'id': i, 'returncode': 0, 'timed_out': False} for i in ids]
            validate_steps(batch, clean)
            for bad in (clean[:-1], clean + [clean[0]], [*clean[:2], {**clean[2], 'returncode': 2}],
                        [*clean[:2], {**clean[2], 'timed_out': True}], [*clean[:2], {**clean[2], 'start_error': 'failed'}]):
                with self.subTest(bad=bad), self.assertRaises(GateToolError):
                    validate_steps(batch, bad)


class PromotedSelectionTest(unittest.TestCase):
    def test_only_completed_promoted_fifo_sets_can_start_a_hunt(self):
        from countertrace.checks.design import selected
        import copy
        state = {'id': 'test', 'kind': 'checks', 'state': 'complete', 'module_id': 'sync_fifo',
                 'checks': {'status': 'promoted', 'promoted_round': 0,
                            'rounds': [{'index': 0, 'properties': props(("1'b1", '!full || !empty')), 'gate': {'passed': True}}]}}
        self.assertEqual(selected(state)['source_run'], 'test')
        for change in ({'state': 'running'}, {'kind': 'verification'}, {'module_id': 'rr_arbiter'},
                       {'checks': {'status': 'not_promoted'}}, {'checks': {'status': 'promoted', 'rounds': []}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                selected({**copy.deepcopy(state), **change})

    def test_check_bundle_replay_rejects_different_frozen_inputs_without_execution(self):
        import io, json, zipfile
        from unittest.mock import patch
        from countertrace.bundle import sha256
        from countertrace.checks.bundle import replay, SCHEMA
        data = json.dumps({'module_id': 'sync_fifo', 'checks': {'rounds': [{'index': 0, 'properties': props(("1'b1", 'empty || full')), 'frozen': {}}]}}).encode()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('checks.json', data)
            z.writestr('manifest.json', json.dumps({'schema': SCHEMA, 'files': {'checks.json': sha256(data)}}))
        with zipfile.ZipFile(buf) as z, patch('countertrace.runner.ensure_image') as docker:
            self.assertFalse(replay(z)['matches'])
            docker.assert_not_called()
