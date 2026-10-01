"""Audit check sets are built only from reviewed templates and frozen suite tests."""

import unittest

from countertrace import audit, catalog
from countertrace.scoreboard import ROWS, check_set_from_dict
from countertrace.stimulus import suite


class AuditDefinitionTest(unittest.TestCase):
    def test_bundled_check_sets_validate(self):
        names = set(suite(4)) & set(suite(2))
        for item in audit.list_check_sets():
            with self.subTest(check_set=item["id"]):
                built = check_set_from_dict(item)
                for test in built.tests or []:
                    self.assertIn(test, names)

    def test_weak_set_is_labeled_and_misses_boundaries(self):
        weak = audit.load_check_set("weak-learner-v1")
        self.assertIn("weak", weak["label"].lower())
        watched = audit.monitored(weak)
        for row in ("write_full", "both_full", "both_empty", "read_empty"):
            self.assertFalse(watched[row], row)

    def test_monitored_rows_for_all_edge_checks(self):
        watched = audit.monitored(audit.load_check_set("core-mirror-v1"))
        self.assertEqual(set(watched), set(ROWS))
        self.assertTrue(all(watched[r] == {"empty_flag", "full_flag", "read_data"} for r in ROWS))

    def test_fault_library_applies_and_targets_contract_rows(self):
        from countertrace.contract import REQUIREMENTS

        for fault_id in catalog.faults()["audit_library"]["faults"]:
            fault = catalog.fault(fault_id)
            self.assertNotEqual(catalog.fault_source(fault_id), catalog.base_source(fault["base"]))
            self.assertTrue(fault["class"] == "none" or fault["class"] in REQUIREMENTS, fault_id)

    def test_unknown_check_set(self):
        with self.assertRaises(KeyError):
            audit.load_check_set("missing")


if __name__ == "__main__":
    unittest.main()
