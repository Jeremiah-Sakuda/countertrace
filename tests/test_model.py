"""Model client behavior with a mocked endpoint. No network access is used."""

import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from countertrace import model
from countertrace.contract import Contract

CONFIG = {
    "NEBIUS_API_KEY": "test-key-not-real",
    "NEBIUS_BASE_URL": "https://example.invalid/v1",
    "NEBIUS_MODEL_ID": "nvidia/test-nemotron",
    "COUNTERTRACE_MODEL_INPUT_TOKEN_LIMIT": "20000",
    "COUNTERTRACE_MODEL_OUTPUT_TOKEN_LIMIT": "2000",
}


class FakeResponse(io.BytesIO):
    headers = {"x-request-id": "req-1"}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def reply(content: str, prompt_tokens: int = 100, completion_tokens: int = 50, finish_reason: str = "stop"):
    body = {"model": "nvidia/test-nemotron", "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
            "choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}
    return FakeResponse(json.dumps(body).encode())


class ModelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"COUNTERTRACE_DATA_DIR": self.tmp.name}, clear=False)
        self.env.start()
        for key in list(CONFIG) + ["COUNTERTRACE_DEPLOYMENT_SPEND_LIMIT_USD"]:
            os.environ.pop(key, None)
        self.no_dotenv = mock.patch.object(model, "load_env_file", lambda: None)
        self.no_dotenv.start()

    def tearDown(self):
        self.no_dotenv.stop()
        self.env.stop()
        self.tmp.cleanup()

    def test_unconfigured_model_is_unavailable_not_invented(self):
        result = model.interpret("A FIFO.", Contract(depth=4))
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["result"])

    def test_token_limits_are_required(self):
        with mock.patch.dict(os.environ, {k: v for k, v in CONFIG.items() if "TOKEN_LIMIT" not in k}):
            self.assertIn("Token limits", model.public_config()["reason"])

    def test_model_specific_prefix_is_opt_in(self):
        with mock.patch.dict(os.environ, {**CONFIG, "COUNTERTRACE_DATA_DIR": self.tmp.name}, clear=True), \
                mock.patch.object(model.request, "urlopen", side_effect=lambda *a, **k: reply('{}')) as call:
            model.chat("test", "Return JSON.", "Test input")
            sent = json.loads(call.call_args[0][0].data)
            self.assertEqual(sent["messages"][0]["content"], "Return JSON.")
            os.environ["COUNTERTRACE_MODEL_SYSTEM_PREFIX"] = "explicit endpoint directive"
            model.chat("test", "Return JSON.", "Test input")
            sent = json.loads(call.call_args[0][0].data)
            self.assertTrue(sent["messages"][0]["content"].startswith("explicit endpoint directive\n\n"))

    def test_model_check_persists_explanation_for_recording(self):
        from countertrace.runs import RunStore

        store = RunStore()
        state = store.create_verification(example_id="showcase-overwrite-when-full")
        state.update(state="complete", verdict={"headline": "counterexample"})
        store.save(state)
        explanation = {"status": "ok", "result": {"summary": "A witnessed failure."},
                       "calls": [], "citation_check": {"valid": 1, "invalid": []}}
        with mock.patch.object(model, "explain_run", return_value=explanation) as explain:
            report = model.feasibility_check(state["id"])
        self.assertEqual(report["run_id"], state["id"])
        self.assertEqual(report["usefulness_review"], "pending")
        self.assertEqual(store.load(state["id"])["explanation"], explanation)
        explain.assert_called_once()

    def test_model_check_rejects_non_failure_or_recorded_run_without_call(self):
        from countertrace.runs import RunStore

        store = RunStore()
        state = store.create_verification(example_id="good-count-d4")
        state.update(state="complete", verdict={"headline": "no_counterexample"})
        store.save(state)
        with mock.patch.object(model, "explain_run") as explain:
            self.assertEqual(model.feasibility_check(state["id"])["status"], "error")
            state.update(verdict={"headline": "counterexample"}, recorded=True)
            store.save(state)
            self.assertEqual(model.feasibility_check(state["id"])["status"], "error")
            self.assertEqual(model.feasibility_check("absent-run")["status"], "error")
            explain.assert_not_called()

    def test_interpretation_validated_and_conflicts_flagged(self):
        decisions = [{"topic": t, "brief_says": None, "status": "matches", "note": ""} for t in model.INTERPRET_TOPICS]
        decisions[3] = {"topic": "write_when_full", "brief_says": "accept writes when full", "status": "conflict", "note": "x"}
        content = "<think>reasoning</think>" + json.dumps({"summary": "ok", "decisions": decisions})
        with mock.patch.dict(os.environ, CONFIG), mock.patch.object(model.request, "urlopen", return_value=reply(content)) as call:
            result = model.interpret("Accept writes when full.", Contract(depth=4))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["blocking"], ["write_when_full"])
        sent = json.loads(call.call_args[0][0].data)
        self.assertLessEqual(sent["max_tokens"], 2000)
        ledger = (Path(self.tmp.name) / "model_usage.jsonl").read_text()
        self.assertNotIn("test-key-not-real", ledger)

    def test_interpretation_routes_to_fast_model(self):
        decisions = [{"topic": t, "brief_says": None, "status": "matches", "note": ""} for t in model.INTERPRET_TOPICS]
        with mock.patch.dict(os.environ, {**CONFIG, "NEBIUS_FAST_MODEL_ID": "nvidia/fast"}), \
                mock.patch.object(model.request, "urlopen", return_value=reply(json.dumps({"summary": "", "decisions": decisions}))) as call:
            model.interpret("A FIFO.", Contract(depth=4))
        self.assertEqual(json.loads(call.call_args[0][0].data)["model"], "nvidia/fast")

    def test_schema_failure_retries_then_reports(self):
        with mock.patch.dict(os.environ, CONFIG), \
                mock.patch.object(model.request, "urlopen", side_effect=[reply("not json"), reply('{"summary": 1}')]):
            result = model.interpret("A FIFO.", Contract(depth=4))
        self.assertEqual(result["status"], "schema_error")
        self.assertEqual(len(result["calls"]), 2)

    def test_input_limit_enforced(self):
        with mock.patch.dict(os.environ, {**CONFIG, "COUNTERTRACE_MODEL_INPUT_TOKEN_LIMIT": "10"}):
            result = model.interpret("A FIFO.", Contract(depth=4))
        self.assertEqual(result["status"], "input_too_large")

    def test_spend_limit_requires_prices(self):
        with mock.patch.dict(os.environ, {**CONFIG, "COUNTERTRACE_DEPLOYMENT_SPEND_LIMIT_USD": "5"}):
            self.assertFalse(model.public_config()["configured"])

    def test_citations_checked_against_recorded_window(self):
        rows = [{"cycle": c} for c in range(10)]
        result = {"steps": [{"text": "a", "cycles": [3, 42], "signals": ["full", "made_up_signal"]},
                            {"text": "b", "cycles": [], "signals": []}],
                  "likely_cause": {"text": "x", "lines": [2, 999]}}
        check = model.citation_check(result, rows, 2, 6, "module fifo;\nwire do_write;\nendmodule\n")
        kinds = {(i["kind"], i["value"]) for i in check["invalid"]}
        self.assertEqual(kinds, {("cycle", 42), ("signal", "made_up_signal"), ("line", 999)})
        self.assertEqual(check["uncited_steps"], 1)

    def test_check_proposals_limited_to_reviewed_templates(self):
        good = {"label": "x", "tests": ["fill_drain"], "checks": [
            {"id": "Full Flag!", "check": "full_flag", "rows": ["write_full"], "requirement": "write_full", "text": "t"}]}
        self.assertEqual(model.validate_check_proposal(good, ["fill_drain"])["checks"][0]["id"], "full_flag_")
        for bad in (
            {**good, "tests": ["made_up"]},
            {**good, "checks": [{"id": "a", "check": "python_eval", "rows": None, "requirement": "reset"}]},
            {**good, "checks": [{"id": "a", "check": "read_data", "rows": ["sometimes"], "requirement": "reset"}]},
        ):
            with self.assertRaises(ValueError):
                model.validate_check_proposal(bad, ["fill_drain"])

    def test_repair_edits_are_exact_and_unique(self):
        rtl = "// Author: Someone\nmodule m;\n    wire a = b;\n    wire c = b;\nendmodule\n"
        patched = model.validate_repair({"rationale": "r", "edits": [{"find": "wire a = b;", "replace": "wire a = !b;"}]}, rtl)
        self.assertIn("// Author: Someone", patched["source"])
        self.assertIn("wire a = !b;", patched["source"])
        for edits in ([{"find": "= b;", "replace": "= 1;"}],          # ambiguous
                      [{"find": "wire z = q;", "replace": "x"}],       # absent
                      [{"find": "", "replace": "x"}],                  # empty
                      [],                                              # no edits
                      [{"find": "wire a = b;", "replace": "wire a = b;"}]):  # no change
            with self.assertRaises(ValueError):
                model.validate_repair({"rationale": "r", "edits": edits}, rtl)

    def test_length_cutoff_retries_with_reasoning_off(self):
        decisions = [{"topic": t, "brief_says": None, "status": "matches", "note": ""} for t in model.INTERPRET_TOPICS]
        good = json.dumps({"summary": "", "decisions": decisions})
        with mock.patch.dict(os.environ, CONFIG), mock.patch.object(
                model.request, "urlopen", side_effect=[reply('{"summ', finish_reason="length"), reply(good)]) as call:
            result = model.interpret("A FIFO.", Contract(depth=4))
        self.assertEqual(result["status"], "ok")
        first, second = (json.loads(c[0][0].data) for c in call.call_args_list)
        self.assertNotIn("chat_template_kwargs", first)
        self.assertEqual(second["chat_template_kwargs"], {"enable_thinking": False})
        self.assertIn("ran out of output tokens", second["messages"][1]["content"])
        self.assertEqual([c["thinking"] for c in result["calls"]], [True, False])

    def test_thinking_can_be_disabled_per_task(self):
        decisions = [{"topic": t, "brief_says": None, "status": "matches", "note": ""} for t in model.INTERPRET_TOPICS]
        with mock.patch.dict(os.environ, {**CONFIG, "COUNTERTRACE_THINKING_OFF_TASKS": "interpret"}), \
                mock.patch.object(model.request, "urlopen", return_value=reply(json.dumps({"summary": "", "decisions": decisions}))) as call:
            model.interpret("A FIFO.", Contract(depth=4))
        self.assertEqual(json.loads(call.call_args[0][0].data)["chat_template_kwargs"], {"enable_thinking": False})

    def test_per_model_prices_and_default_flagging(self):
        ledger = Path(self.tmp.name) / "model_usage.jsonl"
        ledger.write_text(json.dumps({"model_id": "big", "prompt_tokens": 1_000_000, "completion_tokens": 0}) + "\n"
                          + json.dumps({"model_id": "small", "prompt_tokens": 1_000_000, "completion_tokens": 0}) + "\n")
        env = {**CONFIG, "COUNTERTRACE_MODEL_PRICE_INPUT_PER_MTOK_USD": "1", "COUNTERTRACE_MODEL_PRICE_OUTPUT_PER_MTOK_USD": "3",
               "COUNTERTRACE_MODEL_PRICES_JSON": '{"small": [0.25, 0.5]}'}
        with mock.patch.dict(os.environ, env):
            spend = model.spend_summary(model.config())
        self.assertEqual(spend["estimated_cost_usd"], 1.25)
        self.assertEqual(spend["models_at_default_price"], ["big"])

    def test_extract_json_handles_fences_and_reasoning(self):
        self.assertEqual(model.extract_json('<think>x</think>```json\n{"a": 1}\n```'), {"a": 1})
        with self.assertRaises(ValueError):
            model.extract_json("no object here")

    def test_explanation_preserves_long_result_limits(self):
        limits = ("Passing simulations cover named tests only. " * 16
                  + "Reached cover scenarios establish reachability, not correctness.")
        explanation = {"summary": "A write while full corrupts the queue.",
                       "steps": [{"text": "Mismatch.", "cycles": [6], "signals": ["dout"]}],
                       "likely_cause": {"text": "Missing full gate.", "lines": [25]},
                       "next_action": "Gate writes.", "limits": limits}
        self.assertGreater(len(limits), 600)
        self.assertEqual(model.validate_explanation(explanation)["limits"], limits)


if __name__ == "__main__":
    unittest.main()
