"""The published testbench-lab matrix must be exactly what the recorded audit's raw traces produce."""

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_audit_matrix", ROOT / "scripts" / "build_audit_matrix.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class AuditMatrixTest(unittest.TestCase):
    def test_published_matrix_matches_a_fresh_reparse(self):
        published = json.loads(builder.OUT.read_text())
        self.assertEqual(published, json.loads(json.dumps(builder.build())))

    def test_matrix_covers_every_valid_fault_and_the_frozen_suite(self):
        data = builder.build()
        self.assertEqual(len(data["faults"]), 6)
        self.assertEqual(len(data["tests"]), 14)
        self.assertTrue(all(fault["matrix"] for fault in data["faults"]))
        self.assertEqual([e["id"] for e in data["equivalent"]], ["count-equivalent-compare"])


if __name__ == "__main__":
    unittest.main()
