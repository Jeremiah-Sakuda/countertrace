"""End-to-end verifier checks. Skipped unless Docker and the pinned verifier image are available.

Build the image first with `countertrace build-image`.
"""

from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

from countertrace import catalog, runner
from countertrace.contract import Contract
from countertrace.verify import Verification


def image_or_skip() -> dict:
    ok, _ = runner.docker_available()
    if not ok:
        raise unittest.SkipTest("Docker daemon unavailable")
    try:
        return runner.ensure_image(build=False)
    except runner.RunnerError as exc:
        raise unittest.SkipTest(str(exc))


def verify(source: str, depth: int, cancel: threading.Event | None = None, formal=("bmc", "prove", "cover")) -> dict:
    image = image_or_skip()
    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:  # colima shares the home directory
        v = Verification(Path(tmp), "dut", source, Contract(depth=depth), lambda: None,
                         cancel or threading.Event(), image, formal_tasks=formal)
        return v.run()


def statuses(state: dict) -> dict:
    return {o["id"]: o["status"] for o in state["obligations"]}


class IntegrationTest(unittest.TestCase):
    def test_known_good_control_is_proved_and_clean(self):
        state = verify(catalog.base_source("fifo_count.v"), 2)
        self.assertEqual(state["findings"], [])
        self.assertEqual(state["integrity"], [])
        s = statuses(state)
        for check in ("empty_flag", "full_flag", "read_data"):
            self.assertEqual(s[f"simulation:{check}"], "simulation_passed")
            self.assertEqual(s[f"bmc:{check}"], "bounded_pass")
            self.assertEqual(s[f"prove:{check}"], "proved")
        self.assertEqual(s["cover:reachability"], "bounded_pass")

    def test_witnessed_fault_is_found_and_replayed(self):
        state = verify(catalog.fault_source("count-overwrite-when-full"), 4)
        self.assertTrue(state["findings"])
        self.assertNotIn("proved", statuses(state).values())
        formal = [f for f in state["findings"] if f["source"] == "formal"]
        self.assertEqual(formal[0]["replay"]["status"], "reproduced")

    def test_altered_harness_hash_never_passes(self):
        image_or_skip()
        with mock.patch.object(runner, "harness_hashes", return_value={"ct_formal_top.sv": "sha256:0"}):
            state = verify(catalog.base_source("fifo_count.v"), 2, formal=("prove",))
        self.assertTrue(state["integrity"])
        self.assertNotIn("proved", statuses(state).values())
        self.assertNotIn("simulation_passed", statuses(state).values())

    def test_cancellation_never_passes(self):
        cancel = threading.Event()
        cancel.set()
        state = verify(catalog.base_source("fifo_count.v"), 2, cancel=cancel)
        self.assertNotIn("proved", statuses(state).values())
        self.assertNotIn("simulation_passed", statuses(state).values())

    def test_unsupported_source_is_not_executed(self):
        source = catalog.base_source("fifo_count.v").replace("assign empty", "initial count = 0;\n    assign empty")
        state = verify(source, 2)
        self.assertEqual(set(statuses(state).values()), {"unsupported"})
        self.assertEqual(state["batches"], {})


class RepairLoopTest(unittest.TestCase):
    """Loop mechanics with a stubbed model. This is not evidence of model repair quality."""

    def test_candidates_are_readmitted_and_judged_by_unchanged_checks(self):
        image_or_skip()
        from countertrace import model, repair, runs

        with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
            store = runs.RunStore(Path(tmp))
            parent = store.create_verification(example_id="showcase-overwrite-when-full")
            store.execute(parent["id"])
            good = catalog.base_source("fifo_count.v")
            proposals = iter([
                {"status": "ok", "result": {"rationale": "rename", "source": good.replace("module fifo", "module fifo2"), "changed_lines": []}, "calls": []},
                {"status": "ok", "result": {"rationale": "no-op", "source": catalog.fault_source("count-full-exchange"), "changed_lines": []}, "calls": []},
                {"status": "ok", "result": {"rationale": "gate the write on full", "source": good, "changed_lines": [24]}, "calls": []},
            ])
            seen = []

            def propose(source, finding, rows, previous, finding_source="current", include_outcomes=True):
                seen.append((finding["requirement_id"], finding["cycle"], [a["status"] for a in previous], finding_source))
                return next(proposals)

            with mock.patch.object(model, "propose_repair", side_effect=propose):
                store.save({**store.load(parent["id"]), "repair": {"status": "running", "attempts": [],
                                                                   "parent_frozen": store.load(parent["id"])["verification"]["frozen"]}})
                repair.run_loop(store, parent["id"])
            result = store.load(parent["id"])["repair"]
            self.assertEqual([a["status"] for a in result["attempts"]],
                             ["admission_rejected", "failed_checks", "passed_unchanged_checks"])
            self.assertTrue(result["attempts"][2]["frozen_match"])
            self.assertEqual(result["status"], "passed")
            self.assertIn("-    wire do_write = wr_en;", result["attempts"][2]["diff"])
            # Attempt 3 is driven by attempt 2's own counterexample, not the parent's.
            self.assertEqual(result["attempts"][1]["feedback"]["requirement_id"], "both_full")
            self.assertEqual(seen[2][0], "both_full")
            self.assertNotEqual(seen[0][:2], seen[2][:2])
            self.assertEqual(seen[2][2], ["admission_rejected", "failed_checks"])
            self.assertEqual(seen[2][3], "current")  # the finding came from the RTL being repaired



class AuditTest(unittest.TestCase):
    def test_weak_set_misses_boundary_faults_that_the_core_witnesses(self):
        image_or_skip()
        from countertrace import runs

        with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
            store = runs.RunStore(Path(tmp))
            run = store.create_audit(check_set="weak-learner-v1", depth=4)
            store.execute(run["id"])
            audit = store.load(run["id"])["audit"]
        self.assertEqual(audit["baseline"], "baseline_clean")
        by_id = {m["fault_id"]: m for m in audit["mutants"]}
        self.assertEqual(by_id["count-equivalent-compare"]["classification"], "equivalent")
        survivors = {m["fault_id"] for m in audit["mutants"] if m["supplemental"]["status"] == "survived"}
        self.assertEqual(survivors, {"count-overwrite-when-full", "count-full-exchange", "count-empty-bypass"})
        for fault_id in survivors:
            self.assertEqual(by_id[fault_id]["classification"], "valid_fault")
            self.assertEqual(by_id[fault_id]["missing_requirements"], [by_id[fault_id]["target_requirement"]])


if __name__ == "__main__":
    unittest.main()
