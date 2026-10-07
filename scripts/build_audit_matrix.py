"""Build the testbench-lab matrix from the recorded check-quality audit; no execution.

Reparses the preserved raw simulation traces of every audit mutant against the
recorded stimulus, and records, per seeded fault and suite test, where each
check kind first disagrees with the reference. The browser scores any test and
check selection from this matrix. Fails closed unless the reparsed traces
reproduce every recorded core result and the recorded weak-set score.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from countertrace import catalog
from countertrace.contract import REQUIREMENTS, Contract
from countertrace.scoreboard import check_set_from_dict, first_finding, normalize, parse_sim_trace
from countertrace.stimulus import parse, render, suite

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "recorded" / "rec-20261001-193049-aud-7cf847"
OUT = ROOT / "apps" / "web" / "public" / "learning" / "audit.json"
CHECKS = ("empty_flag", "full_flag", "read_data")

# Plain-language descriptions of the frozen suite's directed tests (stimulus.py).
DESCRIPTIONS = {
    "learner_basic": "Fill exactly, drain exactly, wrap once. The usual first testbench: no boundary requests.",
    "fill_drain": "Write one past full, then read one past empty.",
    "write_when_full": "Fill the queue, keep writing while full, then drain it.",
    "simultaneous": "Read and write in the same cycle while empty, at occupancy 1, while full, and mid-queue.",
    "wraparound": "Several fill and drain rounds so both pointers wrap, including simultaneous operations.",
    "recurrent_reset": "Reset in the middle of traffic, including a reset with read and write requested.",
}


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    state = json.loads((RUN / "run.json").read_text())
    audit = state["audit"]
    depth = audit["depth"]
    contract = Contract(depth=depth)
    if audit["contract_hash"] != contract.digest():
        raise ValueError("The recorded audit used a different contract.")
    frozen = suite(depth)
    if audit["stimulus"] != list(frozen):
        raise ValueError("The recorded audit used a different test suite.")
    sim = RUN / "batches" / "sim"
    inputs = {}
    edges = {}
    for test, expected in frozen.items():
        path = sim / "job" / "stimulus" / f"{test}.txt"
        if path.read_text() != render(expected):
            raise ValueError(f"Recorded stimulus differs from the frozen suite: {test}")
        inputs[str(path.relative_to(ROOT))] = sha(path)
        edges[test] = parse(path.read_text())

    mutants = audit["mutants"]
    designs = json.loads((sim / "job" / "job.json").read_text())["designs"]
    if len(designs) != len(mutants):
        raise ValueError("Audit designs and mutants differ in number.")
    traces = {}
    for design, mutant in zip(designs, mutants):
        per_test = {}
        for test in frozen:
            path = sim / "out" / design["id"] / "sim" / f"{test}.trace"
            inputs[str(path.relative_to(ROOT))] = sha(path)
            per_test[test] = normalize(contract, parse_sim_trace(path.read_text(), depth, 8, edges[test]))
        traces[mutant["fault_id"]] = per_test

    # Rows each test drives on the known-good base, for "never exercised" feedback.
    exercised = {test: sorted({r["row"] for r in rows}) for test, rows in traces["base"].items()}

    library = {f["id"]: f for f in json.loads((catalog.FIXTURES / "faults.json").read_text())["faults"]}
    faults, equivalent = [], []
    for mutant in mutants[1:]:
        fid = mutant["fault_id"]
        matrix = {}
        for test, rows in traces[fid].items():
            hits = {}
            for row in rows:
                for check in row["mismatches"]:
                    hits.setdefault(check, {}).setdefault(row["row"], row["cycle"])
            if hits:
                matrix[test] = hits
        killed = bool(matrix)
        if killed != (mutant["core"]["status"] == "killed"):
            raise ValueError(f"Reparsed traces do not reproduce the recorded core result for {fid}.")
        # The recorded core summary keeps each test's first mismatching edge only.
        firsts = [first_finding(rows, test, "simulation") for test, rows in traces[fid].items()]
        firsts = [f for f in firsts if f]
        if killed and (sorted({c for f in firsts for c in f["checks_failed"]}) != mutant["core"]["checks"]
                       or sorted({f["requirement_id"] for f in firsts}) != mutant["core"]["mismatch_rows"]):
            raise ValueError(f"Reparsed traces differ from the recorded core result for {fid}.")
        entry = {"id": fid, "summary": mutant["summary"], "category": mutant["category"],
                 "target": library.get(fid, {}).get("class") or mutant.get("class"), "matrix": matrix}
        if mutant["classification"] == "valid_fault":
            faults.append(entry)
        elif mutant["classification"] == "equivalent":
            equivalent.append({k: entry[k] for k in ("id", "summary")})
        else:
            raise ValueError(f"Unclassified mutant cannot be published: {fid}")

    # The matrix must reproduce the recorded score of the reviewed weak set.
    weak = check_set_from_dict(audit["check_set"])
    for fault, mutant in zip(faults, [m for m in mutants if m["classification"] == "valid_fault"]):
        caught = any(check.evaluate(traces[fault["id"]][t]) is not None for check in weak.checks for t in weak.tests)
        if caught != (mutant["supplemental"]["status"] == "killed"):
            raise ValueError(f"Matrix does not reproduce the recorded weak-set result for {fault['id']}.")

    tests = []
    for test, test_edges in frozen.items():
        seed = test.removeprefix("random_s") if test.startswith("random_s") else None
        tests.append({"id": test, "edges": len(test_edges), "rows": exercised[test],
                      "description": DESCRIPTIONS.get(test) or f"Seeded random traffic (seed {seed}): {len(test_edges)} edges of mixed reads, writes, and occasional resets."})
    return {
        "schema": "countertrace-testbench-lab-v1",
        "source_run": state["id"], "contract_hash": audit["contract_hash"], "depth": depth,
        "checks": list(CHECKS), "rows": {k: v["title"] for k, v in REQUIREMENTS.items()}, "tests": tests, "faults": faults, "equivalent": equivalent,
        "weak_set": {"id": weak.id, "tests": weak.tests, "checks": sorted({c.check for c in weak.checks})},
        "method": "Reparsed the recorded audit's raw simulation traces against its frozen stimulus. "
                  "No new RTL execution. A fault counts as caught when a selected test shows a selected "
                  "check disagreeing with the reference on any edge.",
        "input_hashes": inputs,
    }


def main() -> None:
    result = build()
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({"faults": len(result["faults"]), "tests": len(result["tests"]), "output": str(OUT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
