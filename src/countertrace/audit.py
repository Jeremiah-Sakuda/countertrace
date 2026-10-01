"""Supplemental-check audit against a reviewed fault library.

The mandatory core decides whether each mutant is a valid fault (simulation
scoreboard, with formal proof or counterexample to classify the rest). Only
then is the named supplemental check set scored on the same frozen simulation
traces. The result describes that check set; it is never a design-confidence
score, and the core is never removed from design acceptance.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import threading

from countertrace import catalog, runner
from countertrace.contract import REQUIREMENTS, Contract
from countertrace.formal import parse_failed_assertions, parse_status
from countertrace.scoreboard import (
    ROWS, TraceError, check_set_from_dict, first_finding, normalize, parse_sim_trace,
)
from countertrace.stimulus import render, suite
from countertrace.verify import now

CHECK_SETS = catalog.FIXTURES / "check_sets"


def list_check_sets() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(CHECK_SETS.glob("*.json"))]


def load_check_set(check_set_id: str) -> dict:
    for item in list_check_sets():
        if item["id"] == check_set_id:
            check_set_from_dict(item)  # validate against reviewed templates
            return item
    raise KeyError(check_set_id)


def monitored(check_set: dict) -> dict[str, set[str]]:
    """Map each contract row to the check kinds the set evaluates there."""
    result: dict[str, set[str]] = {row: set() for row in ROWS}
    for check in check_set["checks"]:
        for row in check["rows"] if check["rows"] is not None else ROWS:
            result[row].add(check["check"])
    return result


def execute(store, state: dict, cancel: threading.Event, image: dict) -> None:
    run_dir = store.run_dir(state["id"])
    depth = state["depth"]
    contract = Contract(depth=depth)
    library = catalog.faults()["audit_library"]
    raw_set = load_check_set(state["check_set"])
    check_set = check_set_from_dict(raw_set)
    tests = suite(depth)
    stimulus = {name: render(edges) for name, edges in tests.items()}
    designs = [("base", catalog.base_source(library["base"]), None)]
    for fault_id in library["faults"]:
        designs.append((fault_id, catalog.fault_source(fault_id), catalog.fault(fault_id)))
    audit = {
        "check_set": raw_set, "library_version": library["version"], "base": library["base"], "depth": depth,
        "contract_hash": contract.digest(), "stimulus": list(tests),
        "stages": [{"id": "simulating", "status": "running", "started_at": now()},
                   {"id": "checking_properties", "status": "running", "started_at": now()}],
        "mutants": [], "summary": {}, "requirements": {},
    }
    state["audit"] = audit
    store.save(state)

    def batch(kind: str, specs: dict, stim: dict) -> dict:
        ids = {d[0]: f"m{i:02d}" for i, d in enumerate(designs)}
        prepared = runner.prepare_batch(
            run_dir / "batches" / kind,
            [({"id": ids[name], "top": "fifo", "depth": depth, "width": 8, "seed": 1, **specs}, source)
             for name, source, _ in designs],
            stim)
        record = runner.run_batch(prepared, image, cancel)
        record["ids"] = ids
        record["out"] = prepared.out_dir
        return record

    with ThreadPoolExecutor(max_workers=2) as pool:
        sim_future = pool.submit(batch, "sim", {"sim_tests": list(tests), "formal": []}, stimulus)
        formal_future = pool.submit(batch, "formal", {"sim_tests": [], "formal": ["bmc", "prove"]}, {})
        try:
            sim, formal = sim_future.result(), formal_future.result()
        except runner.Cancelled:
            for stage in audit["stages"]:
                stage.update(status="cancelled", finished_at=now())
            return
    for stage in audit["stages"]:
        stage.update(status="done", finished_at=now())
    for kind, record in (("sim", sim), ("formal", formal)):
        worker = record.get("worker")
        if worker is None or worker.get("harness_hashes") != runner.harness_hashes():
            audit["integrity_error"] = f"{kind} batch failed integrity: {record.get('worker_error', 'harness hash mismatch')}"
            audit["stages"][0 if kind == "sim" else 1]["status"] = "error"
            return
    audit["tool_versions"] = sim["worker"]["tool_versions"]

    watched = monitored(raw_set)
    set_tests = check_set.tests or list(tests)
    unknown = [t for t in set_tests if t not in tests]
    if unknown:
        raise ValueError(f"check set refers to tests outside the frozen suite: {unknown}")
    audit["set_tests"] = set_tests
    results = []
    for name, _, fault in designs:
        did = sim["ids"][name]
        traces, errors = {}, []
        for test, edges in tests.items():
            path = sim["out"] / did / "sim" / f"{test}.trace"
            try:
                traces[test] = normalize(contract, parse_sim_trace(path.read_text(), depth, 8, edges))
            except (OSError, TraceError) as exc:
                errors.append(f"{test}: {exc}")
        core_findings = [f for f in (first_finding(rows, t, "simulation") for t, rows in traces.items()) if f]
        mismatch_rows = sorted({f["requirement_id"] for f in core_findings})  # first observed mismatch per test
        formal_dir = formal["out"] / formal["ids"][name] / "formal"
        formal_status = {}
        for task in ("bmc", "prove"):
            status_file = formal_dir / task / "status"
            formal_status[task] = parse_status(status_file.read_text() if status_file.is_file() else None)
        if formal_status["prove"] == "PASS":
            formal_result = "proved_equivalent"
        elif "FAIL" in formal_status.values():
            formal_result = "counterexample"
        elif formal_status["bmc"] == "PASS":
            formal_result = "bounded_no_difference"
        elif None in formal_status.values() or "ERROR" in formal_status.values():
            formal_result = "error"
        else:
            formal_result = "unresolved"
        core_status = "error" if errors else ("killed" if core_findings else "survived")
        if errors and not core_findings:
            classification = "invalid"
        elif core_findings or formal_result == "counterexample":
            classification = "valid_fault"
        elif formal_result == "proved_equivalent":
            classification = "equivalent"
        else:
            classification = "unresolved"
        entry = {
            "fault_id": name,
            "summary": fault["summary"] if fault else "Known-good base implementation (baseline).",
            "category": fault["category"] if fault else "baseline",
            "class": fault["class"] if fault else None,
            "core": {"status": core_status, "errors": errors[:3],
                     "checks": sorted({c for f in core_findings for c in f["checks_failed"]}),
                     "first": min(({"test": f["test"], "cycle": f["cycle"], "check": f["check"],
                                    "requirement_id": f["requirement_id"]} for f in core_findings),
                                  key=lambda f: f["cycle"], default=None),
                     "mismatch_rows": mismatch_rows},
            "formal": {"status": formal_result, "bmc": formal_status["bmc"], "prove": formal_status["prove"],
                       "failed": parse_failed_assertions((formal_dir / "prove" / "logfile.txt").read_text())
                       if (formal_dir / "prove" / "logfile.txt").is_file() else []},
            "classification": classification if fault else ("baseline_clean" if not core_findings and formal_result == "proved_equivalent" else "baseline_failed"),
        }
        if name == "base":
            exercised = {r["row"] for t in set_tests for r in traces.get(t, [])}
            audit["set_rows_exercised"] = sorted(exercised)
        if fault and classification == "valid_fault" and traces:
            killers = []
            first_cycle = None
            for check in check_set.checks:
                for test in set_tests:
                    cycle = check.evaluate(traces.get(test, []))
                    if cycle is not None:
                        killers.append(check.id)
                        first_cycle = cycle if first_cycle is None else min(first_cycle, cycle)
                        break
            entry["supplemental"] = {"status": "killed" if killers else "survived", "by": killers, "first_cycle": first_cycle}
            # The reviewed library records which contract condition each fault targets.
            target = fault["class"]
            covered = target in audit["set_rows_exercised"] and bool(watched.get(target))
            entry["target_requirement"] = target
            entry["missing_requirements"] = [] if killers or covered else [target]
            if not killers and covered:
                entry["note"] = "The set drives and checks this condition but its tests did not expose the fault."
        else:
            entry["supplemental"] = {"status": "not_applicable", "by": [], "first_cycle": None}
            entry["missing_requirements"] = []
        results.append(entry)

    audit["mutants"] = results
    mutants = [m for m in results if m["fault_id"] != "base"]
    valid = [m for m in mutants if m["classification"] == "valid_fault"]
    audit["baseline"] = results[0]["classification"]
    audit["summary"] = {
        "mutants": len(mutants),
        "valid_faults": len(valid),
        "supplemental_killed": sum(1 for m in valid if m["supplemental"]["status"] == "killed"),
        "supplemental_survived": sum(1 for m in valid if m["supplemental"]["status"] == "survived"),
        "equivalent": sum(1 for m in mutants if m["classification"] == "equivalent"),
        "unresolved": sum(1 for m in mutants if m["classification"] == "unresolved"),
        "invalid": sum(1 for m in mutants if m["classification"] == "invalid"),
        "note": "Kill counts describe the named supplemental check set on the frozen simulation stimulus only. "
                "They are not a design-confidence score.",
    }
    audit["requirements"] = {
        row: {"title": REQUIREMENTS[row]["title"],
              "exercised_by_set": row in audit["set_rows_exercised"],
              "covered_by_set": bool(watched[row]) and row in audit["set_rows_exercised"],
              "checks": sorted(watched[row]),
              "surviving_faults": [m["fault_id"] for m in valid if row in m["missing_requirements"]]}
        for row in ROWS
    }
