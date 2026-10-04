"""Control-service access rules: run ownership and model-request quotas."""

import os
import unittest
from unittest import mock

from countertrace import server


class ServerRulesTest(unittest.TestCase):
    def setUp(self):
        self.app = server.App.__new__(server.App)  # avoid creating a run store
        import threading

        self.app.visitor_lock = threading.Lock()
        self.app.visitor_calls, self.app.visitor_runs, self.app.run_owner = {}, {}, {}

    def test_only_the_starting_visitor_can_cancel(self):
        self.app.note_run("10.0.0.1", "run-a")
        self.app.require_owner("10.0.0.1", "run-a")
        with self.assertRaises(PermissionError):
            self.app.require_owner("10.0.0.2", "run-a")

    def test_unowned_runs_cancel_only_from_this_machine(self):
        with mock.patch.dict(os.environ, {"COUNTERTRACE_TRUST_PROXY": ""}):
            self.app.require_owner("127.0.0.1", "cli-run")
            with self.assertRaises(PermissionError):
                self.app.require_owner("10.0.0.3", "cli-run")

    def test_concurrent_claims_from_one_visitor_get_one_slot(self):
        import threading

        self.app.store = mock.Mock()
        results, barrier = [], threading.Barrier(8)

        def claim():
            barrier.wait()
            try:
                self.app.claim_run_slot("v")
                results.append("ok")
            except PermissionError:
                results.append("refused")

        threads = [threading.Thread(target=claim) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(results.count("ok"), 1)

    def test_failed_creation_releases_the_slot(self):
        self.app.store = mock.Mock()
        with self.assertRaises(ValueError):
            self.app.create_run({}, "v")  # neither example_id nor source
        self.app.claim_run_slot("v")  # the slot is free again

    def test_repair_counts_its_worst_case_against_the_quota(self):
        with mock.patch.object(server, "MODEL_CALLS_PER_HOUR", 12):
            self.app.claim_model_call("v", units=6)
            self.app.claim_model_call("v", units=6)
            with self.assertRaises(PermissionError):
                self.app.claim_model_call("v", units=1)


if __name__ == "__main__":
    unittest.main()
