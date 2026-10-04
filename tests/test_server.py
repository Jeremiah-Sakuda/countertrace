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

    def test_repair_counts_its_worst_case_against_the_quota(self):
        with mock.patch.object(server, "MODEL_CALLS_PER_HOUR", 12):
            self.app.claim_model_call("v", units=6)
            self.app.claim_model_call("v", units=6)
            with self.assertRaises(PermissionError):
                self.app.claim_model_call("v", units=1)


if __name__ == "__main__":
    unittest.main()
