"""Repair feedback provenance with simulated outcomes; no model or RTL execution."""

from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from countertrace import catalog, model, repair
from countertrace.runs import RunStore


class RepairFeedbackTest(unittest.TestCase):
    def exercise(self, status, child_has_finding, feedback):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp))
            parent = store.create_verification(example_id="showcase-overwrite-when-full")
            finding = {"source": "simulation", "trace": "original", "test": "fill_drain",
                       "cycle": 6, "check": "read_data", "requirement_id": "write_full"}
            original_rows = [{"cycle": 6, "marker": "original"}]
            parent.update(state="complete", verification={"findings": [finding],
                          "traces": {"original": original_rows}}, repair={"status": "running", "attempts": []})
            store.save(parent)
            candidate = catalog.fault_source("count-full-exchange")
            proposals = []

            def propose(source, current_finding, rows, previous, finding_source, include_outcomes):
                proposals.append(deepcopy((source, current_finding, rows, previous, finding_source, include_outcomes)))
                if len(proposals) == 1:
                    return {"status": "ok", "result": {"source": candidate, "rationale": "stub"}, "calls": []}
                return {"status": "error", "detail": "stub stopped", "calls": []}

            def verify(_store, _parent, source, attempt, _origin):
                child = store.create_verification(source_text=source, depth=4)
                child_finding = {**finding, "trace": "child", "cycle": 4,
                                 "check": "full_flag", "requirement_id": "both_full"}
                child.update(state="failed" if status == "error" else "complete",
                             verification={"findings": [child_finding] if child_has_finding else [],
                                           "traces": {"child": [{"cycle": 4, "marker": "child"}]}})
                store.save(child)
                attempt.update(status=status, candidate_run_id=child["id"], summary="stub outcome")

            with mock.patch.dict(os.environ, {"COUNTERTRACE_REPAIR_FEEDBACK": feedback}), \
                    mock.patch.object(model, "propose_repair", side_effect=propose), \
                    mock.patch.object(repair, "verify_candidate", side_effect=verify):
                repair.run_loop(store, parent["id"])
            self.assertEqual(store.load(parent["id"])["repair"]["status"], "exhausted")
            self.assertEqual(proposals[1][0], candidate)
            return proposals

    def test_advanced_source_without_new_trace_keeps_earlier_provenance(self):
        for status in ("error", "failed_checks"):
            with self.subTest(status=status):
                proposals = self.exercise(status, False, "on")
                for proposal in proposals[1:]:
                    self.assertEqual(proposal[4], "earlier")
                    self.assertEqual(proposal[1]["cycle"], 6)
                    self.assertEqual(proposal[2][0]["marker"], "original")

    def test_feedback_on_advances_source_and_trace_together(self):
        proposals = self.exercise("failed_checks", True, "on")
        self.assertEqual(proposals[1][4:], ("current", True))
        self.assertEqual(proposals[1][1]["cycle"], 4)
        self.assertEqual(proposals[1][2][0]["marker"], "child")

    def test_feedback_off_keeps_original_evidence_and_hides_outcomes(self):
        proposals = self.exercise("failed_checks", True, "off")
        self.assertEqual(proposals[0][4:], ("current", False))
        for proposal in proposals[1:]:
            self.assertEqual(proposal[4:], ("earlier", False))
            self.assertEqual(proposal[1]["cycle"], 6)
            self.assertNotIn("feedback", proposal[3][0])
