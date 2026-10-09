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
    def test_case_semantic_directives_never_reach_execution(self):
        import re
        base = catalog.base_source("fifo_count.v")
        base = base.replace("assign empty", "reg [7:0] prev_din;\n    always @(posedge clk) if (rst) prev_din <= 0; else prev_din <= din;\n    wire trig = do_write && do_read && prev_din == 8'h5A && din == 8'hA5;\n    wire [AW:0] next_count = count + do_write - do_read;\n    assign empty", 1)
        # Overlapping branches once let parallel_case hide the bad count update
        # from formal synthesis while the ordinary procedural case still failed.
        body = "case (1'b1) MARKER\n                trig: count <= 0;\n                do_write || do_read: count <= next_count;\n                default: count <= count;\n            endcase"
        probe = re.sub(r"case \(.*?endcase", lambda _: body, base, count=1, flags=re.S)
        self.assertIn("MARKER", probe)
        for marker in ('/* synopsys parallel_case */', '/* synthesis parallel_case */'):
            state=verify(probe.replace('MARKER',marker),4)
            self.assertEqual(set(statuses(state).values()),{'unsupported'})
            self.assertEqual(state['batches'],{})
        for keyword in ('unique','unique0','priority'):
            state=verify(probe.replace('MARKER','').replace("case (1'b1)",keyword+" case (1'b1)"),4)
            self.assertEqual(set(statuses(state).values()),{'unsupported'})
            self.assertEqual(state['batches'],{})
        plain=verify(probe.replace('MARKER','/* ordinary case */'),4)
        self.assertEqual(plain['integrity'],[])
        self.assertTrue(any(f['source']=='formal' for f in plain['findings']))
        self.assertIn('counterexample',statuses(plain).values())


    def test_elaborated_init_is_rejected_even_if_lexical_gate_is_bypassed(self):
        from countertrace.admission import admit
        source=catalog.base_source("fifo_count.v").replace('reg [AW:0]      count;', "reg [AW:0]      count = 1;")
        admitted=admit(catalog.base_source("fifo_count.v"))
        with mock.patch('countertrace.verify.admit',return_value=admitted):
            state=verify(source,4,formal=('prove',))
        self.assertTrue(any('initialization attribute' in p for p in state['integrity']))
        self.assertFalse(set(statuses(state).values()) & {'proved','simulation_passed','bounded_pass'})

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
        # empty_flag first fails after other checks in these tests. It must
        # still be a counterexample, even though it never owns the headline.
        seen = {c for name, rows in state["traces"].items() if name.startswith("sim:")
                for row in rows for c in row["mismatches"]}
        self.assertEqual(seen, {"empty_flag", "full_flag", "read_data"})
        for check in seen:
            self.assertEqual(statuses(state)[f"simulation:{check}"], "counterexample")

    def test_altered_harness_hash_never_passes(self):
        image_or_skip()
        with mock.patch.object(runner, "harness_hashes", return_value={"ct_formal_top.sv": "sha256:0"}):
            state = verify(catalog.base_source("fifo_count.v"), 2, formal=("prove",))
        self.assertTrue(state["integrity"])
        self.assertNotIn("proved", statuses(state).values())
        self.assertNotIn("simulation_passed", statuses(state).values())

    def test_design_that_drives_its_own_input_never_passes(self):
        """A tied input bit once constrained the formal stimulus and was reported proved.

        Nested braces slip past the lexical gate on purpose; the elaborated netlist must catch it.
        """
        source = catalog.base_source("fifo_count.v").replace(
            "assign empty", "wire spare;\n    assign {{spare}, din[7]} = 2'b00;\n    assign empty")
        state = verify(source, 2)
        self.assertTrue(any("din[7] is tied to a constant" in p for p in state["integrity"]), state["integrity"])
        self.assertNotIn("proved", statuses(state).values())
        self.assertNotIn("bounded_pass", statuses(state).values())
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


class ChecksGateTest(unittest.TestCase):
    """Model-written checks: promotion and negative controls through the real gate."""

    FIFO_PROPS = {
        "state": [
            {"name": "count", "width": 4, "next": "rst ? 4'd0 : count + (wr_en && (count != DEPTH)) - (rd_en && (count != 0))"},
            {"name": "head", "width": 3, "next": "rst ? 3'd0 : (rd_en && (count != 0)) ? ((head + 3'd1) % DEPTH) : head"},
            {"name": "tail", "width": 3, "next": "rst ? 3'd0 : (wr_en && (count != DEPTH)) ? ((tail + 3'd1) % DEPTH) : tail"},
            {"name": "dout_ref", "width": 8, "next": "rst ? 8'd0 : (rd_en && (count != 0)) ? mem[head] : dout_ref"},
            {"name": "has_read", "width": 1, "next": "rst ? 1'd0 : has_read || (rd_en && (count != 0))"},
        ],
        "memories": [{"name": "mem", "width": 8, "depth": 4}],
        "writes": [{"memory": "mem", "when": "wr_en && (count != DEPTH) && !rst", "index": "tail", "value": "din"}],
        "properties": [
            {"id": "full_flag", "when": "1'b1", "then": "full == (count == DEPTH)"},
            {"id": "empty_flag", "when": "1'b1", "then": "empty == (count == 0)"},
            {"id": "dout_matches", "when": "has_read", "then": "dout == dout_ref"},
        ],
    }

    def gate(self, props):
        from countertrace.checks import gate, modules

        image = image_or_skip()
        with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
            return gate.run_gate(modules.load("sync_fifo"), props, Path(tmp), image)

    def test_parameter_generic_shadow_model_is_promoted(self):
        result = self.gate(self.FIFO_PROPS)
        self.assertEqual(result["stage"], "mutants")
        self.assertTrue(result["passed"])
        self.assertEqual(result["unresolved"], 0)
        self.assertEqual(result["killed"], result["nonequivalent"])
        self.assertGreater(result["nonequivalent"], 20)

    def test_wrong_property_is_disproved_on_the_golden_with_a_trace(self):
        result = self.gate({"properties": [{"id": "never_full", "when": "1'b1", "then": "!full"}]})
        self.assertEqual(result["stage"], "golden")
        self.assertFalse(result["passed"])
        self.assertEqual(result["failed"], ["never_full"])
        self.assertTrue(result["trace"])

    def test_hard_coded_parameter_fails_at_the_second_setting(self):
        props = {**self.FIFO_PROPS, "properties": [{"id": "full_flag", "when": "1'b1", "then": "full == (count == 4)"}]}
        result = self.gate(props)
        self.assertEqual((result["stage"], result["config"]["id"]), ("golden", "p1"))

    def test_unreachable_trigger_is_vacuous(self):
        result = self.gate({"properties": [{"id": "never_happens", "when": "full && empty", "then": "1'b0"}]})
        self.assertEqual(result["stage"], "vacuity")
        self.assertEqual(result["unreached"], ["never_happens"])

    def test_trivially_true_properties_are_never_promoted(self):
        result = self.gate({"properties": [{"id": "tautology", "when": "1'b1", "then": "1'b1"}]})
        self.assertEqual(result["stage"], "mutants")
        self.assertEqual(result["killed"], 0)
        self.assertFalse(result["passed"])
