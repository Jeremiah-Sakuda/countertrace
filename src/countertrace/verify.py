"""Verify one DUT against a frozen contract and check set.

Result statuses follow the PRD's result semantics. Nothing here infers a pass
from a zero exit code, a completed container, or missing evidence.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import time
from typing import Callable

from countertrace import runner
from countertrace.admission import admit, check_ports_json
from countertrace.interface_map import WRAPPER, digest as interface_map_digest, wrapper
from countertrace.contract import CHECKS, Contract, sha256_json
from countertrace.formal import (
    COVER_LABELS, EXPECTED_PROPERTIES, counterexample_observations, parse_covers,
    parse_failed_assertions, parse_status, property_inventory,
)
from countertrace.scoreboard import (
    TraceError, coverage, first_finding, normalize, parse_sim_trace, window,
)
from countertrace.stimulus import STIMULUS_VERSION, parse as parse_stimulus, render, suite

STATUS_LABELS = {
    "simulation_passed": "Simulation passed for these runs",
    "bounded_pass": "No counterexample within N cycles",
    "proved": "Property proved under these assumptions",
    "counterexample": "Counterexample found",
    "unresolved": "Unresolved",
    "tool_error": "Tool error",
    "not_checked": "Not checked",
    "unsupported": "Unsupported",
}
FORMAL_TASKS = ("bmc", "prove", "cover")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def frozen_check_set(contract: Contract, limits: dict, formal_tasks=FORMAL_TASKS) -> dict:
    """Everything that must stay identical across a repair comparison."""
    tests = suite(contract.depth)
    return {
        "contract": contract.digest(),
        "harness": runner.harness_hashes(),
        "verifier_digest": runner.verifier_digest(),
        "stimulus_version": STIMULUS_VERSION,
        "stimulus": {name: sha256_json(render(edges)) for name, edges in tests.items()},
        "limits": limits,
        "formal_tasks": list(formal_tasks),  # the tasks that actually run
        "expected_properties": EXPECTED_PROPERTIES,
    }


class Verification:
    """Runs and records one verification. `emit` persists state after every change."""

    def __init__(self, run_dir: Path, design_id: str, source: str, contract: Contract,
                 emit: Callable[[], None], cancel: threading.Event, image: dict,
                 limits: dict | None = None, formal_tasks=FORMAL_TASKS, simulate: bool = True,
                 interface_map: dict | None = None):
        self.run_dir = run_dir
        self.interface_map = interface_map
        self.design_id = design_id
        self.source = source
        self.contract = contract
        self.emit = emit
        self.cancel = cancel
        self.image = image
        self.limits = dict(limits or runner.DEFAULT_LIMITS)
        self.formal_tasks = tuple(formal_tasks)
        self.simulate = simulate
        self.lock = threading.RLock()
        self.started = time.monotonic()
        self.state: dict = {
            "design_id": design_id,
            "source_hash": sha256_json(source),
            "interface_map": interface_map,
            "interface_map_hash": interface_map_digest(interface_map),
            "contract_hash": contract.digest(),
            "frozen": frozen_check_set(contract, self.limits, self.formal_tasks),
            "stages": [
                {"id": s, "status": "pending"} for s in
                ("validating", "simulating", "checking_properties", "replaying")
            ],
            "admission": None,
            "obligations": [],
            "findings": [],
            "coverage": {},
            "formal_covers": {},
            "traces": {},
            "batches": {},
            "timings": {},
            "integrity": [],
        }

    # -- state helpers -------------------------------------------------
    def stage(self, stage_id: str, status: str, detail: str | None = None) -> None:
        with self.lock:
            for s in self.state["stages"]:
                if s["id"] == stage_id:
                    s["status"] = status
                    if status == "running":
                        s["started_at"] = now()
                    elif status in ("done", "error", "skipped", "cancelled"):
                        s["finished_at"] = now()
                    if detail:
                        s["detail"] = detail
            self.emit()

    def obligation(self, **item) -> None:
        with self.lock:
            item.setdefault("label", STATUS_LABELS[item["status"]])
            self.state["obligations"] = [o for o in self.state["obligations"] if o["id"] != item["id"]]
            self.state["obligations"].append(item)
            self.emit()

    def add_finding(self, finding: dict) -> None:
        with self.lock:
            if "first_finding_s" not in self.state["timings"]:
                self.state["timings"]["first_finding_s"] = round(time.monotonic() - self.started, 2)
            self.state["findings"].append(finding)
            self.emit()

    # -- pipeline ------------------------------------------------------
    def run(self) -> dict:
        self.stage("validating", "running")
        admission = admit(self.source, self.interface_map)
        self.state["admission"] = admission.as_dict()
        if not admission.accepted:
            self.stage("validating", "error", "Admission rejected the source.")
            for check in CHECKS:
                self.obligation(id=f"admission:{check}", check=check, method="admission", status="unsupported",
                                detail="Not executed: the source is outside the admitted profile.")
            for s in ("simulating", "checking_properties", "replaying"):
                self.stage(s, "skipped")
            return self.finish()
        self.stage("validating", "done", f"Module {admission.module}; one file; supported constructs only.")
        top = WRAPPER if self.interface_map else admission.module
        tests = suite(self.contract.depth)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = []
            if self.simulate:
                futures.append(pool.submit(self.sim_batch, top, tests))
            else:
                self.stage("simulating", "skipped")
            if self.formal_tasks:
                futures.append(pool.submit(self.formal_batch, top))
            else:
                self.stage("checking_properties", "skipped")
            for future in futures:
                future.result()
        if self.cancel.is_set():
            return self.finish(cancelled=True)
        self.replay(top)
        return self.finish()

    def finish(self, cancelled: bool = False) -> dict:
        with self.lock:
            if cancelled:
                for s in self.state["stages"]:
                    if s["status"] in ("pending", "running"):
                        s["status"] = "cancelled"
                for check in CHECKS:
                    for method in ("simulation", "bmc", "prove"):
                        oid = f"{method}:{check}"
                        if not any(o["id"] == oid for o in self.state["obligations"]):
                            self.state["obligations"].append({
                                "id": oid, "check": check, "method": method, "status": "unresolved",
                                "label": STATUS_LABELS["unresolved"], "detail": "Cancelled before completion."})
            self.state["timings"]["total_s"] = round(time.monotonic() - self.started, 2)
            self.state["unresolved_count"] = sum(
                1 for o in self.state["obligations"] if o["status"] in ("unresolved", "tool_error", "not_checked"))
            self.emit()
            return self.state

    def job_source(self) -> str:
        """DUT source, plus the trusted wrapper generated from a validated mapping."""
        return self.source + (wrapper(self.interface_map) if self.interface_map else "")

    def batch(self, kind: str, top: str, specs: dict, stimulus: dict[str, str]) -> dict:
        root = self.run_dir / "batches" / f"{self.design_id}-{kind}"
        batch = runner.prepare_batch(root, [({"id": self.design_id, "top": top, "depth": self.contract.depth,
                                               "width": self.contract.width, "seed": 1, **specs}, self.job_source())],
                                     stimulus, self.limits)
        record = runner.run_batch(batch, self.image, self.cancel)
        record["out_dir"] = str(batch.out_dir.relative_to(self.run_dir))
        with self.lock:
            self.state["batches"][kind] = {k: v for k, v in record.items() if k != "worker"}
            if "worker" in record:
                self.state["batches"][kind]["tool_versions"] = record["worker"]["tool_versions"]
                self.state["batches"][kind]["steps"] = record["worker"]["steps"]
        self.check_integrity(kind, record, batch.out_dir)
        return record

    def check_integrity(self, kind: str, record: dict, out: Path) -> None:
        problems = []
        worker = record.get("worker")
        if worker is None:
            problems.append(f"{kind}: {record.get('worker_error', 'no worker result')}")
        else:
            if worker.get("harness_hashes") != runner.harness_hashes():
                problems.append(f"{kind}: verifier harness hashes differ from the trusted copy (stale or altered image)")
            ports_path = out / self.design_id / "ports.json"
            if not ports_path.is_file():
                problems.append(f"{kind}: elaborated interface was not produced")
            else:
                netlist = json.loads(ports_path.read_text())
                if self.interface_map:
                    from countertrace.interface_map import check_dut_ports

                    problems.extend(f"{kind}: {p}" for p in check_dut_ports(netlist, self.interface_map, self.contract.width))
                for d in check_ports_json(netlist,
                                          WRAPPER if self.interface_map else self.state["admission"]["module"],
                                          self.contract.width):
                    problems.append(f"{kind}: {d.message}")
            props = out / self.design_id / "properties.json"
            if not props.is_file():
                problems.append(f"{kind}: elaborated property netlist was not produced")
            else:
                inventory = property_inventory(json.loads(props.read_text()))
                if inventory["counts"] != EXPECTED_PROPERTIES:
                    problems.append(f"{kind}: property counts {inventory['counts']} differ from the expected {EXPECTED_PROPERTIES}")
                problems.extend(f"{kind}: {p}" for p in inventory["problems"])
        with self.lock:
            self.state["integrity"].extend(problems)
            self.state.setdefault("integrity_checked", []).append(kind)

    def integrity_ok(self, kind: str) -> bool:
        return not any(p.startswith(f"{kind}:") for p in self.state["integrity"])

    def sim_batch(self, top: str, tests: dict) -> None:
        self.stage("simulating", "running")
        stimulus = {name: render(edges) for name, edges in tests.items()}
        try:
            record = self.batch("sim", top, {"sim_tests": list(tests), "formal": []}, stimulus)
        except runner.Cancelled:
            self.stage("simulating", "cancelled")
            return
        except Exception as exc:  # noqa: BLE001 - every failure becomes an explicit tool error
            self.sim_error(f"Worker failure: {exc}")
            return
        out = self.run_dir / record["out_dir"] / self.design_id
        if not self.integrity_ok("sim"):
            self.sim_error("Integrity check failed; see integrity notes.")
            return
        steps = {s["id"]: s for s in record["worker"]["steps"]}
        compile_step = steps.get(f"{self.design_id}:compile")
        if not compile_step or compile_step.get("returncode") != 0:
            self.sim_error("Verilator compilation failed or timed out.", log=f"{record['out_dir']}/{self.design_id}/logs/compile.log")
            return
        failures, cycles, errors = [], 0, []
        totals: dict[str, int] = {}
        for name, edges in tests.items():
            step = steps.get(f"{self.design_id}:sim:{name}")
            path = out / "sim" / f"{name}.trace"
            if not step or step.get("timed_out") or step.get("returncode") != 0 or not path.is_file():
                errors.append(f"{name}: simulation did not complete")
                continue
            try:
                observations = parse_sim_trace(path.read_text(), self.contract.depth, self.contract.width, edges)
            except TraceError as exc:
                errors.append(f"{name}: {exc}")
                continue
            rows = normalize(self.contract, observations)
            cycles += len(rows)
            for key, value in coverage(rows).items():
                totals[key] = totals.get(key, 0) + value
            finding = first_finding(rows, name, "simulation")
            with self.lock:
                self.state["traces"][f"sim:{name}"] = rows
            if finding:
                finding["window"] = window(rows, finding["cycle"])
                finding["trace"] = f"sim:{name}"
                finding["vcd"] = f"{record['out_dir']}/{self.design_id}/sim/{name}.vcd"
                failures.append(finding)
        with self.lock:
            self.state["coverage"] = totals
        if failures:
            self.add_finding(min(failures, key=lambda f: (f["cycle"], f["test"])))
        failed_checks = {c for f in failures for c in f["checks_failed"]}
        for check in CHECKS:
            if errors and check not in failed_checks:
                status, detail = "tool_error", "; ".join(errors[:3])
            elif check in failed_checks:
                status = "counterexample"
                tests_failed = sorted({f["test"] for f in failures if check in f["checks_failed"]})
                more = f" and {len(tests_failed) - 4} more" if len(tests_failed) > 4 else ""
                detail = f"Failed in {len(tests_failed)} of {len(tests)} tests: {', '.join(tests_failed[:4])}{more}."
            else:
                status = "simulation_passed"
                detail = f"{len(tests)} named tests ({cycles} cycles, seeds {', '.join(n for n in tests if n.startswith('random'))})."
            self.obligation(id=f"simulation:{check}", check=check, method="simulation", status=status,
                            detail=detail, tests=list(tests), cycles=cycles)
        unreached = sorted(k for k, v in totals.items() if v == 0)
        self.stage("simulating", "error" if errors else "done",
                   f"{len(tests)} tests, {cycles} cycles" + (f"; rows not exercised: {', '.join(unreached)}" if unreached else ""))

    def sim_error(self, message: str, log: str | None = None) -> None:
        for check in CHECKS:
            self.obligation(id=f"simulation:{check}", check=check, method="simulation", status="tool_error",
                            detail=message, log=log)
        self.stage("simulating", "error", message)

    def formal_batch(self, top: str) -> None:
        self.stage("checking_properties", "running")
        try:
            record = self.batch("formal", top, {"sim_tests": [], "formal": list(self.formal_tasks)}, {})
        except runner.Cancelled:
            self.stage("checking_properties", "cancelled")
            return
        except Exception as exc:  # noqa: BLE001
            self.formal_error(f"Worker failure: {exc}")
            return
        if not self.integrity_ok("formal"):
            self.formal_error("Integrity check failed; see integrity notes.")
            return
        out = self.run_dir / record["out_dir"] / self.design_id / "formal"
        rel = f"{record['out_dir']}/{self.design_id}/formal"
        steps = {s["id"]: s for s in record["worker"]["steps"]}
        depth = self.limits["bmc_depth"]
        for task in self.formal_tasks:
            task_dir = out / task
            step = steps.get(f"{self.design_id}:formal:{task}")
            status_text = (task_dir / "status").read_text() if (task_dir / "status").is_file() else None
            status = parse_status(status_text)
            log_path = task_dir / "logfile.txt"
            log = log_path.read_text() if log_path.is_file() else ""
            log_ref = f"{rel}/{task}/logfile.txt"
            if step is None or step.get("timed_out"):
                status = "TIMEOUT" if step else None
            if task == "cover":
                covers = parse_covers(log)
                with self.lock:
                    self.state["formal_covers"] = {label: covers.get(label, {"reached": None, "step": None})
                                                   for label in COVER_LABELS}
                reached = [l for l in COVER_LABELS if covers.get(l, {}).get("reached")]
                if status == "PASS" and len(reached) == len(COVER_LABELS):
                    self.obligation(id="cover:reachability", check="reachability", method="cover", status="bounded_pass",
                                    label=f"All {len(COVER_LABELS)} input scenarios reachable within {self.limits['cover_depth']} solver steps",
                                    detail="Environment reachability: the covers observe the inputs and the reference queue (not the DUT), showing the assumptions do not rule out any contract scenario. They reduce the risk of vacuous checks; they do not prove the specification complete.",
                                    depth=self.limits["cover_depth"], log=log_ref)
                else:
                    missing = [l for l in COVER_LABELS if l not in reached]
                    self.obligation(id="cover:reachability", check="reachability", method="cover",
                                    status="tool_error" if status in (None, "ERROR") else "unresolved",
                                    detail=f"Not reached within {self.limits['cover_depth']} cycles: {', '.join(missing) or 'unknown'}. "
                                           "Bounded non-reachability is not impossibility.",
                                    depth=self.limits["cover_depth"], log=log_ref)
                continue
            failed = parse_failed_assertions(log)
            failed_checks = {f["check"] for f in failed}
            for check in CHECKS:
                oid = f"{task}:{check}"
                common = {"id": oid, "check": check, "method": task, "log": log_ref}
                if status == "FAIL" and check in failed_checks:
                    fstep = min(f["step"] for f in failed if f["check"] == check)
                    self.obligation(**common, status="counterexample", step=fstep,
                                    detail=f"Solver step {fstep} (application cycle {fstep - 1}); trace {rel}/{task}/trace.vcd")
                elif status == "PASS" and task == "bmc":
                    self.obligation(**common, status="bounded_pass", depth=depth,
                                    label=f"No counterexample within {depth - 1} cycles",
                                    cycles_checked=depth - 1,
                                    detail=f"Bounded model check from reset with the contract assumptions: {depth} solver "
                                           f"steps check application cycles 0-{depth - 2} (outputs are checked one step after each edge).")
                elif status == "PASS" and task == "prove":
                    self.obligation(**common, status="proved",
                                    detail=f"Unbounded proof (abc pdr) for DEPTH={self.contract.depth}, WIDTH={self.contract.width} under the listed assumptions.")
                elif status == "FAIL":
                    self.obligation(**common, status="unresolved",
                                    detail="Not established: the solver stopped at another property's counterexample.")
                elif status in ("UNKNOWN", "TIMEOUT"):
                    self.obligation(**common, status="unresolved", detail=f"Solver returned {status}.")
                else:
                    self.obligation(**common, status="tool_error", detail=f"No authoritative status ({status_text or 'missing'}).")
            if status == "FAIL" and failed:
                vcd = task_dir / "trace.vcd"
                with self.lock:
                    self.state.setdefault("formal_failures", {})[task] = {
                        "step": min(f["step"] for f in failed), "assertions": failed,
                        "vcd": f"{rel}/{task}/trace.vcd" if vcd.is_file() else None,
                    }
        errors = [o for o in self.state["obligations"] if o["method"] in self.formal_tasks and o["status"] == "tool_error"]
        self.stage("checking_properties", "error" if errors else "done",
                   f"{len(errors)} formal obligation(s) ended in a tool error; none counts as a pass." if errors else None)

    def formal_error(self, message: str) -> None:
        for task in self.formal_tasks:
            if task == "cover":
                self.obligation(id="cover:reachability", check="reachability", method="cover", status="tool_error", detail=message)
                continue
            for check in CHECKS:
                self.obligation(id=f"{task}:{check}", check=check, method=task, status="tool_error", detail=message)
        self.stage("checking_properties", "error", message)

    def replay(self, top: str) -> None:
        failures = self.state.get("formal_failures", {})
        task = "bmc" if "bmc" in failures else "prove" if "prove" in failures else None
        if task is None or not failures[task].get("vcd"):
            self.stage("replaying", "skipped", "No formal counterexample to replay.")
            return
        self.stage("replaying", "running")
        info = failures[task]
        try:
            edges, observations = counterexample_observations(
                (self.run_dir / info["vcd"]).read_text(), info["step"])
        except (OSError, TraceError) as exc:
            self.stage("replaying", "error", f"Counterexample could not be normalized: {exc}")
            return
        rows = normalize(self.contract, observations)
        formal_finding = first_finding(rows, f"formal:{task}", "formal")
        with self.lock:
            self.state["traces"][f"formal:{task}"] = rows
        replay = {"status": "not_attempted", "task": task, "solver_step": info["step"],
                  "application_cycle": info["step"] - 1}
        if formal_finding is None:
            replay.update(status="mismatch", detail="The normalized solver trace did not violate the reference scoreboard.")
        else:
            formal_finding["window"] = window(rows, formal_finding["cycle"])
            formal_finding["trace"] = f"formal:{task}"
            formal_finding["vcd"] = info["vcd"]
            stim_name = "formal_replay"
            try:
                record = self.batch("replay", top, {"sim_tests": [stim_name], "formal": []}, {stim_name: render(edges)})
                path = self.run_dir / record["out_dir"] / self.design_id / "sim" / f"{stim_name}.trace"
                sim_rows = normalize(self.contract, parse_sim_trace(path.read_text(), self.contract.depth,
                                                                    self.contract.width, parse_stimulus(render(edges))))
                sim_finding = first_finding(sim_rows, stim_name, "simulation")
                with self.lock:
                    self.state["traces"]["replay"] = sim_rows
                if sim_finding and (sim_finding["cycle"], sim_finding["check"]) == (formal_finding["cycle"], formal_finding["check"]):
                    replay.update(status="reproduced", detail=f"Simulation reproduced {sim_finding['check']} at cycle {sim_finding['cycle']}.")
                elif sim_finding:
                    replay.update(status="mismatch", detail=f"Simulation failed differently ({sim_finding['check']} at cycle {sim_finding['cycle']}). Investigate; pre-reset state can differ between engines.")
                else:
                    replay.update(status="not_reproduced", detail="Simulation of the same inputs did not fail. Investigate: the counterexample may depend on pre-reset or uninitialized state, or an output may depend combinationally on current inputs (the contract assumes registered outputs; formal then samples it under the next cycle's inputs).")
            except runner.Cancelled:
                self.stage("replaying", "cancelled")
                return
            except (OSError, TraceError, runner.RunnerError) as exc:
                replay.update(status="error", detail=f"Replay could not run: {exc}")
            formal_finding["replay"] = replay
            self.add_finding(formal_finding)
        with self.lock:
            self.state["replay"] = replay
        self.stage("replaying", "done" if replay["status"] == "reproduced" else "error", replay.get("detail"))
