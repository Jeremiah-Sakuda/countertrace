"""Trusted parsers: malformed, truncated, or inconsistent evidence never becomes a pass."""

from pathlib import Path
import copy
import json
import tempfile
import threading
import unittest
from unittest import mock

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
    def test_property_verdicts_include_failures_after_the_first_finding(self):
        from countertrace.verify import Verification

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out/dut/sim"
            out.mkdir(parents=True)
            # empty_flag fails first, read_data later; full_flag stays clean.
            (out / "bad.trace").write_text(trace([GOOD[0], "1 0 1 0 b2 0 1 0", "2 0 0 1 c3 a1 1 0"]))
            (out / "good.trace").write_text(trace(GOOD))
            steps = [{"id": f"dut:{step}", "returncode": 0, "timed_out": False} for step in ("compile", "sim:bad", "sim:good")]
            for missing in (False, True):
                v = Verification(root, "dut", "", Contract(depth=2), lambda: None, threading.Event(), {})
                tests = {"bad": EDGES, "good": EDGES, **({"missing": EDGES} if missing else {})}
                with mock.patch.object(v, "batch", return_value={"out_dir": "out", "worker": {"steps": steps}, "container_returncode":0,"timed_out":False,"cancelled":False}):
                    v.sim_batch("fifo", tests)
                obligations = {o["check"]: o for o in v.state["obligations"]}
                self.assertEqual(v.state["findings"][0]["check"], "empty_flag")
                for check in ("empty_flag", "read_data"):
                    self.assertEqual(obligations[check]["status"], "counterexample")
                    self.assertIn(f"Failed in 1 of {len(tests)} tests: bad.", obligations[check]["detail"])
                self.assertEqual(obligations["full_flag"]["status"], "tool_error" if missing else "simulation_passed")

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
    def test_preserved_formal_pass_never_overrides_execution_failure(self):
        from countertrace.verify import Verification
        root=DATA.parents[1]/'recorded/rec-20261001-193044-ver-f15d50'
        worker=json.loads((root/'batches/dut-formal/out/worker_result.json').read_text())
        base={'out_dir':'batches/dut-formal/out','worker':worker,'container_returncode':0,'timed_out':False,'cancelled':False}
        for field, value in [('clean',None),('container_returncode',1),('timed_out',True),('cancelled',True),('container_returncode',None),('step_returncode',1),('step_returncode',None),('step_timed_out',True),('step_timed_out',None)]:
            with self.subTest(field=field,value=value):
                record=copy.deepcopy(base)
                if field.startswith('step_'):
                    for step in record['worker']['steps']:
                        if ':formal:' in step['id']: step[field[5:]]=value
                elif field!='clean': record[field]=value
                v=Verification(root,'dut','',Contract(depth=4),lambda:None,threading.Event(),{})
                with mock.patch.object(v,'batch',return_value=record): v.formal_batch('fifo')
                states={o['status'] for o in v.state['obligations']}
                if field=='clean': self.assertEqual(states,{'proved','bounded_pass'})
                else: self.assertFalse(states & {'proved','bounded_pass'},states)

    def test_legitimate_nonzero_formal_fail_retains_counterexample(self):
        from countertrace.verify import Verification
        root=DATA.parents[1]/'recorded/rec-20261004-010137-ver-dd43e0'
        worker=json.loads((root/'batches/dut-formal/out/worker_result.json').read_text())
        record={'out_dir':'batches/dut-formal/out','worker':worker,'container_returncode':0,'timed_out':False,'cancelled':False}
        v=Verification(root,'dut','',Contract(depth=4),lambda:None,threading.Event(),{})
        with mock.patch.object(v,'batch',return_value=record): v.formal_batch('fifo')
        self.assertIn('counterexample',{o['status'] for o in v.state['obligations']})
        self.assertNotIn('proved',{o['status'] for o in v.state['obligations']})

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
