"""Recorded repair navigation must work without the owner's private run store."""

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from countertrace import runs, server


class RecordingTest(unittest.TestCase):
    def test_repair_links_resolve_in_a_clean_read_only_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = runs.RunStore(root / "private")
            parent = store.create_verification(example_id="showcase-overwrite-when-full")
            child = store.create_verification(example_id="good-count-d4", parent_id=parent["id"])
            parent.update(state="complete", explanation={"status": "ok", "result": {"summary": "Explanation"}},
                          repair={"status": "passed", "attempts": [{"candidate_run_id": child["id"]}]})
            child["state"] = "complete"
            store.save(parent)
            store.save(child)
            with mock.patch.object(runs, "ROOT", root), mock.patch.object(server, "RECORDED", root / "recorded"):
                runs.record(store, parent["id"])
                runs.record(store, child["id"])
                with mock.patch.object(server, "RunStore", return_value=runs.RunStore(root / "fresh")):
                    app = server.App()
                recorded_parent = app.load_run("rec-" + parent["id"])
                candidate_id = recorded_parent["repair"]["attempts"][0]["candidate_run_id"]
                recorded_child = app.load_run(candidate_id)
                self.assertEqual(candidate_id, "rec-" + child["id"])
                self.assertEqual(recorded_child["parent_id"], recorded_parent["id"])
                self.assertEqual(recorded_parent["explanation"], parent["explanation"])
                for recorded_id in (recorded_parent["id"], recorded_child["id"]):
                    with self.assertRaises(PermissionError):
                        app.require_live(recorded_id)
            self.assertEqual(store.load(child["id"])["parent_id"], parent["id"])
            self.assertEqual(store.load(parent["id"])["repair"]["attempts"][0]["candidate_run_id"], child["id"])
