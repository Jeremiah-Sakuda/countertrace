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


if __name__ == "__main__":
    unittest.main()
