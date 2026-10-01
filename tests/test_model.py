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


def reply(content: str, prompt_tokens: int = 100, completion_tokens: int = 50):
    body = {"model": "nvidia/test-nemotron", "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}]}
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

    def test_extract_json_handles_fences_and_reasoning(self):
        self.assertEqual(model.extract_json('<think>x</think>```json\n{"a": 1}\n```'), {"a": 1})
        with self.assertRaises(ValueError):
            model.extract_json("no object here")


if __name__ == "__main__":
    unittest.main()
