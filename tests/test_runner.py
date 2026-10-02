"""Host/container identity boundary; real artifact cleanup is covered in integration tests."""

import unittest
from unittest import mock

from countertrace import runner


class WorkerIdentityTest(unittest.TestCase):
    def test_unprivileged_service_owns_its_outputs(self):
        with mock.patch.object(runner.os, "getuid", return_value=1001), \
                mock.patch.object(runner.os, "getgid", return_value=1002):
            self.assertEqual(runner.worker_identity(), "1001:1002")

    def test_root_identity_is_never_given_to_worker(self):
        for uid, gid, expected in ((0, 0, "10001:10001"), (1001, 0, "1001:10001")):
            with self.subTest(uid=uid, gid=gid), \
                    mock.patch.object(runner.os, "getuid", return_value=uid), \
                    mock.patch.object(runner.os, "getgid", return_value=gid):
                self.assertEqual(runner.worker_identity(), expected)
