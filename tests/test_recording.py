"""Recorded repair navigation must work without the owner's private run store."""

from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest import mock

from countertrace import runs, server


class RecordingTest(unittest.TestCase):
    def test_published_simulation_verdicts_agree_with_every_trace_row(self):
        checked = 0
        for path in (Path(__file__).resolve().parents[1] / "recorded").glob("*/run.json"):
            state = json.loads(path.read_text())
            v = state.get("verification")
            if not v:
                continue
            checked += 1
            seen = {c for name, rows in v["traces"].items() if name.startswith("sim:")
                    for row in rows for c in row["mismatches"]}
            for o in v["obligations"]:
                if o["method"] == "simulation":
                    expected = "counterexample" if o["check"] in seen else "simulation_passed"
                    self.assertEqual(o["status"], expected, (state["id"], o["id"]))
            self.assertEqual(state["verdict"], runs.verdict(v))
            for correction in state.get("evidence_corrections", []):
                for name, digest in correction["input_hashes"].items():
                    actual = "sha256:" + hashlib.sha256((path.parent / name).read_bytes()).hexdigest()
                    self.assertEqual(actual, digest)
                self.assertTrue(correction["changes"])
        self.assertGreater(checked, 0)

    def test_repair_links_resolve_in_a_clean_read_only_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = runs.RunStore(root / "private")
            parent = store.create_verification(example_id="showcase-overwrite-when-full")
            child = store.create_verification(example_id="good-count-d4", parent_id=parent["id"])
            checks = store.create_checks("sync_fifo")
            checks.update(state="complete", checks={"demonstration": {"hunt_run_id": parent["id"], "repair_run_id": child["id"]}})
            parent["promoted_checks"] = {"source_run": checks["id"]}
            parent.update(state="complete", explanation={"status": "ok", "result": {"summary": "Explanation"}},
                          repair={"status": "passed", "attempts": [{"candidate_run_id": child["id"]}]})
            child["state"] = "complete"
            store.save(parent)
            store.save(child)
            store.save(checks)
            with mock.patch.object(runs, "ROOT", root), mock.patch.object(server, "RECORDED", root / "recorded"):
                runs.record(store, parent["id"])
                runs.record(store, child["id"])
                runs.record(store, checks["id"])
                with mock.patch.object(server, "RunStore", return_value=runs.RunStore(root / "fresh")):
                    app = server.App()
                recorded_parent = app.load_run("rec-" + parent["id"])
                candidate_id = recorded_parent["repair"]["attempts"][0]["candidate_run_id"]
                recorded_child = app.load_run(candidate_id)
                self.assertEqual(candidate_id, "rec-" + child["id"])
                self.assertEqual(recorded_child["parent_id"], recorded_parent["id"])
                self.assertEqual(recorded_parent["explanation"], parent["explanation"])
                recorded_checks = app.load_run(recorded_parent["promoted_checks"]["source_run"])
                self.assertEqual(recorded_checks["checks"]["demonstration"],
                                 {"hunt_run_id": recorded_parent["id"], "repair_run_id": recorded_child["id"]})
                for recorded_id in (recorded_parent["id"], recorded_child["id"]):
                    with self.assertRaises(PermissionError):
                        app.require_live(recorded_id)
            self.assertEqual(store.load(child["id"])["parent_id"], parent["id"])
            self.assertEqual(store.load(parent["id"])["repair"]["attempts"][0]["candidate_run_id"], child["id"])
