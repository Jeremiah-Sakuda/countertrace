"""Re-derive published simulation summaries from preserved raw traces; no execution.

Dry-run by default. --apply writes only curated run.json files, with original
values and a hash/commit reference. Raw evidence and model text stay untouched.
Historical evaluation outputs are never rewritten by this script.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

from countertrace.contract import Contract
from countertrace.model import citation_check, primary_finding
from countertrace.runs import verdict
from countertrace.scoreboard import normalize, parse_sim_trace
from countertrace.stimulus import parse
from countertrace.verify import STATUS_LABELS

ROOT = Path(__file__).resolve().parents[1]
CORRECTION_ID = "simulation-all-edges-and-declared-citations-v1"


def refresh(path: Path) -> dict | None:
    original = path.read_bytes()
    state = json.loads(original)
    if state.get("kind") != "verification" or not state.get("recorded") or state.get("state") != "complete":
        return None
    if any(c["id"] == CORRECTION_ID for c in state.get("evidence_corrections", [])):
        return None
    v = state["verification"]
    contract = Contract(depth=state["depth"])
    batch = v["batches"]["sim"]
    steps = {s["id"]: s for s in batch["steps"]}
    design = v["design_id"]
    out = path.parent / batch["out_dir"]
    job = out.parent / "job"
    rows_by_test = {}
    hashes = {}
    for key, stored in v["traces"].items():
        if not key.startswith("sim:"):
            continue
        name = key.removeprefix("sim:")
        step = steps[f"{design}:sim:{name}"]
        if step.get("returncode") != 0 or step.get("timed_out"):
            raise ValueError(f"Cannot refresh incomplete simulation: {path} {name}")
        stimulus_path = job / "stimulus" / f"{name}.txt"
        trace_path = out / design / "sim" / f"{name}.trace"
        for raw in (stimulus_path, trace_path):
            hashes[str(raw.relative_to(path.parent))] = "sha256:" + hashlib.sha256(raw.read_bytes()).hexdigest()
        edges = parse(stimulus_path.read_text())
        rows = normalize(contract, parse_sim_trace(trace_path.read_text(), contract.depth, contract.width, edges))
        if rows != stored:
            raise ValueError(f"Preserved normalized/raw evidence differs: {path} {name}")
        rows_by_test[name] = rows
    changes = []
    for item in v["obligations"]:
        if item["method"] != "simulation":
            continue
        if item["status"] not in {"simulation_passed", "counterexample"} or set(item["tests"]) != set(rows_by_test):
            raise ValueError(f"Cannot refresh incomplete obligation: {path} {item['id']}")
        failed = sorted(n for n, rows in rows_by_test.items() if any(item["check"] in r["mismatches"] for r in rows))
        if not failed:
            continue
        before = deepcopy(item)
        more = f" and {len(failed) - 4} more" if len(failed) > 4 else ""
        item.update(status="counterexample", label=STATUS_LABELS["counterexample"],
                    detail=f"Failed in {len(failed)} of {len(rows_by_test)} tests: {', '.join(failed[:4])}{more}.")
        if item != before:
            changes.append({"field": f"verification.obligations.{item['id']}", "before": before, "after": deepcopy(item)})
    old_verdict = state["verdict"]
    state["verdict"] = verdict(v)
    if state["verdict"] != old_verdict:
        changes.append({"field": "verdict", "before": old_verdict, "after": state["verdict"]})
    explanation = state.get("explanation")
    if explanation and explanation.get("result"):
        finding = primary_finding(state)
        check = citation_check(explanation["result"], v["traces"][finding["trace"]],
                               finding["window"]["start"], finding["window"]["end"],
                               (path.parent / "dut.v").read_text())
        for field, value in (("citation_check", check), ("status", "ok_with_invalid_citations" if check["invalid"] else "ok")):
            if explanation.get(field) != value:
                changes.append({"field": f"explanation.{field}", "before": explanation.get(field), "after": value})
                explanation[field] = value
        if any(c["field"].startswith("verification.obligations") for c in changes):
            explanation["evidence_notice"] = (
                "This original model response used simulation summaries that were later corrected. "
                "Some claims that a check passed are contradicted by later cycles in the preserved traces. "
                "Use the corrected check results below; the model text has not been regenerated.")
    if not changes:
        return None
    today = datetime.date.today()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    state.setdefault("evidence_corrections", []).append({
        "id": CORRECTION_ID, "date": today.isoformat(), "original_commit": commit,
        "original_run_sha256": "sha256:" + hashlib.sha256(original).hexdigest(),
        "method": "Reparsed preserved raw simulation traces against their recorded stimulus; aggregated all edges. "
                  "Rechecked citations against declarations. No new RTL execution or model call.",
        "input_hashes": hashes, "changes": changes,
    })
    state["recorded_note"] = (state.get("recorded_note", "") + f" Derived simulation summaries corrected {today:%B} {today.day}, {today.year} "
                              "from the preserved traces; see evidence_corrections in run.json. Original timings, raw artifacts, "
                              "and model text are unchanged.").strip()
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    for path in sorted((ROOT / "recorded").glob("*/run.json")):
        updated = refresh(path)
        if updated is not None:
            print(json.dumps({"run": path.parent.name, "changes": len(updated["evidence_corrections"][-1]["changes"]),
                              "applied": args.apply}))
            if args.apply:
                path.write_text(json.dumps(updated, indent=1))


if __name__ == "__main__":
    main()
