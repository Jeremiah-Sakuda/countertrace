"""Trusted parsers: malformed, truncated, or inconsistent evidence never becomes a pass."""

from pathlib import Path
import unittest

from countertrace.contract import Contract, Edge
from countertrace.formal import (
    COVER_LABELS, EXPECTED_PROPERTIES, counterexample_observations, parse_covers,
    parse_failed_assertions, parse_status, property_inventory,
)
from countertrace.scoreboard import (
    TraceError, check_set_from_dict, coverage, first_finding, normalize, parse_sim_trace,
)
from countertrace.stimulus import parse, render, suite

DATA = Path(__file__).resolve().parent / "data"
EDGES = [Edge(1, 0, 0, 0xA1), Edge(0, 1, 0, 0xB2), Edge(0, 0, 1, 0xC3)]


def trace(lines, end=3, header="CTTRACE 1 DEPTH=2 WIDTH=8"):
    return "\n".join([header, *lines, f"END {end}"]) + "\n"


GOOD = ["0 1 0 0 a1 0 1 0", "1 0 1 0 b2 0 0 0", "2 0 0 1 c3 b2 1 0"]


class SimTraceTest(unittest.TestCase):
    def test_good_trace_scores_clean(self):
        rows = normalize(Contract(depth=2), parse_sim_trace(trace(GOOD), 2, 8, EDGES))
        self.assertIsNone(first_finding(rows, "t", "simulation"))
        self.assertEqual(rows[2]["expected"]["dout"], 0xB2)

    def test_truncated_trace_is_error(self):
        with self.assertRaises(TraceError):
            parse_sim_trace("CTTRACE 1 DEPTH=2 WIDTH=8\n" + "\n".join(GOOD[:2]) + "\n", 2, 8, EDGES)

    def test_missing_cycles_is_error(self):
        with self.assertRaises(TraceError):
            parse_sim_trace(trace(GOOD[:2], end=2), 2, 8, EDGES)

    def test_parameter_mismatch_is_error(self):
        with self.assertRaises(TraceError):
            parse_sim_trace(trace(GOOD, header="CTTRACE 1 DEPTH=4 WIDTH=8"), 2, 8, EDGES)

    def test_trace_must_match_driven_stimulus(self):
        tampered = [GOOD[0], "1 0 1 0 ff 0 0 0", GOOD[2]]
        with self.assertRaises(TraceError):
            parse_sim_trace(trace(tampered), 2, 8, EDGES)

    def test_wrong_data_is_a_finding_with_requirement(self):
        bad = [GOOD[0], GOOD[1], "2 0 0 1 c3 a1 1 0"]
        rows = normalize(Contract(depth=2), parse_sim_trace(trace(bad), 2, 8, EDGES))
        finding = first_finding(rows, "t", "simulation")
        self.assertEqual((finding["cycle"], finding["check"], finding["requirement_id"]), (2, "read_data", "read_not_empty"))

    def test_uninitialized_dout_is_not_checked(self):
        rows = normalize(Contract(depth=2), parse_sim_trace(trace(GOOD), 2, 8, EDGES))
        self.assertFalse(rows[1]["dout_checked"])
        self.assertEqual(rows[1]["mismatches"], [])


class FormalParsingTest(unittest.TestCase):
    def test_counterexample_normalization_matches_solver_report(self):
        vcd = (DATA / "overwrite_bmc_trace.vcd").read_text()
        edges, observations = counterexample_observations(vcd, 6)
        self.assertEqual(len(edges), 6)
        self.assertEqual(edges[0].rst, 1)
        rows = normalize(Contract(depth=4), observations)
        finding = first_finding(rows, "formal:bmc", "formal")
        # SBY reported ct_full_flag at solver step 6, i.e. application cycle 5.
        self.assertEqual((finding["cycle"], finding["check"], finding["requirement_id"]), (5, "full_flag", "both_full"))

    def test_missing_steps_are_errors(self):
        vcd = (DATA / "overwrite_bmc_trace.vcd").read_text()
        with self.assertRaises(TraceError):
            counterexample_observations(vcd, 50)

    def test_status_parsing(self):
        self.assertEqual(parse_status("PASS 0 3\n"), "PASS")
        self.assertEqual(parse_status("UNKNOWN\n"), "UNKNOWN")
        self.assertIsNone(parse_status(""))
        self.assertIsNone(parse_status("passed probably"))

    def test_failed_assertions_and_covers(self):
        log = ("SBY [ct_bmc] summary:   failed assertion ct_formal_top.ct_read_data at x.sv:1.1-1.2 step 4\n"
               "SBY [c] engine_0: ##   0:00:00  Reached cover statement in step 3 at ct_formal_top: cov_full\n"
               "SBY [c] engine_0: ##   0:00:00  Unreached cover statement at ct_formal_top: cov_wrap_read\n")
        self.assertEqual(parse_failed_assertions(log), [{"assertion": "ct_read_data", "check": "read_data", "step": 4}])
        covers = parse_covers(log)
        self.assertEqual(covers["cov_full"], {"reached": True, "step": 3})
        self.assertFalse(covers["cov_wrap_read"]["reached"])

    def netlist(self, extra_module=None, drop_asserts=False):
        cells = {}
        if not drop_asserts:
            for name in ("ct_empty_flag", "ct_full_flag", "ct_read_data"):
                cells[name] = {"type": "$check", "parameters": {"FLAVOR": "assert"}}
        cells["$assume$1"] = {"type": "$check", "parameters": {"FLAVOR": "assume"}}
        for name in COVER_LABELS:
            cells[name] = {"type": "$check", "parameters": {"FLAVOR": "cover"}}
        modules = {"ct_formal_top": {"cells": cells}}
        if extra_module:
            modules["fifo"] = {"cells": {"sneaky": {"type": "$check", "parameters": {"FLAVOR": extra_module}}}}
        return {"modules": modules}

    def test_property_inventory_accepts_trusted_monitor(self):
        inventory = property_inventory(self.netlist())
        self.assertEqual(inventory["counts"], EXPECTED_PROPERTIES)
        self.assertEqual(inventory["problems"], [])

    def test_negative_controls_zero_assertions_and_dut_assumptions(self):
        self.assertNotEqual(property_inventory(self.netlist(drop_asserts=True))["counts"], EXPECTED_PROPERTIES)
        inventory = property_inventory(self.netlist(extra_module="assume"))
        self.assertNotEqual(inventory["counts"], EXPECTED_PROPERTIES)
        self.assertTrue(inventory["problems"])


class StimulusAndCoverageTest(unittest.TestCase):
    def test_round_trip_and_determinism(self):
        for depth in (2, 4):
            tests = suite(depth)
            self.assertEqual(tests, suite(depth))
            for edges in tests.values():
                self.assertEqual(parse(render(edges)), edges)
                self.assertEqual(edges[0].rst, 1)

    def test_directed_suite_exercises_every_row(self):
        from countertrace.contract import reference_steps
        from countertrace.scoreboard import Observation

        for depth in (2, 4):
            totals = {}
            for edges in suite(depth).values():
                steps = reference_steps(Contract(depth=depth), edges)
                obs = [Observation(s.cycle, s.edge, s.expected_dout or 0, s.expected_empty, s.expected_full) for s in steps]
                for key, value in coverage(normalize(Contract(depth=depth), obs)).items():
                    totals[key] = totals.get(key, 0) + value
            self.assertTrue(all(totals.values()), {k: v for k, v in totals.items() if not v})

    def test_check_set_templates_are_validated(self):
        with self.assertRaises(ValueError):
            check_set_from_dict({"id": "x", "label": "x", "checks": [{"id": "a", "check": "exec", "requirement": "reset"}]})
        with self.assertRaises(ValueError):
            check_set_from_dict({"id": "x", "label": "x", "checks": [{"id": "a", "check": "read_data", "rows": ["nope"], "requirement": "reset"}]})
        with self.assertRaises(ValueError):
            check_set_from_dict({"id": "x", "label": "x", "checks": []})


if __name__ == "__main__":
    unittest.main()
