"""Evaluation helpers: brief interpretation scoring and suite bookkeeping.

Outcomes are recorded with their denominators and every attempt. Development
results are reported separately from frozen evaluation results.
"""

from __future__ import annotations

import json
from pathlib import Path
import time

from countertrace import model
from countertrace.contract import Contract


def interpret_briefs(path: Path) -> dict:
    data = json.loads(path.read_text())
    results = []
    for brief in data["briefs"]:
        started = time.monotonic()
        result = model.interpret(brief["text"], Contract(depth=brief["depth"]))
        blocking = result.get("blocking") or []
        ok = result["status"] == "ok"
        if not ok:
            outcome = "error"
        elif brief["expected_blocking"]:
            outcome = "conflict_detected" if blocking else "missed_conflict"
        else:
            outcome = "false_block" if blocking else "proceeded"
        results.append({
            "id": brief["id"], "expected_blocking": brief["expected_blocking"],
            "expected_topics": brief.get("expected_topics", []), "status": result["status"],
            "blocking": blocking, "needs_decision": result.get("needs_decision", []),
            "topic_hit": bool(set(blocking) & set(brief.get("expected_topics", []))) if blocking else False,
            "outcome": outcome, "wall_s": round(time.monotonic() - started, 2),
            "calls": [{k: c.get(k) for k in ("model_id", "latency_ms", "prompt_tokens", "completion_tokens", "status", "schema_error")}
                      for c in result.get("calls", [])],
            "decisions": (result.get("result") or {}).get("decisions"),
            "detail": result.get("detail"),
        })
    conflicting = [r for r in results if r["expected_blocking"]]
    compatible = [r for r in results if not r["expected_blocking"]]
    return {
        "set": data["version"], "split": data["split"], "model_id": model.config()["model_id"],
        "prompt_sha256": prompt_hashes()["interpret"],
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "conflicting_detected": f"{sum(r['outcome'] == 'conflict_detected' for r in conflicting)} / {len(conflicting)}",
            "compatible_proceeded": f"{sum(r['outcome'] == 'proceeded' for r in compatible)} / {len(compatible)}",
            "errors": sum(r["outcome"] == "error" for r in results),
        },
        "results": results,
    }


def prompt_hashes() -> dict:
    import hashlib

    return {name: "sha256:" + hashlib.sha256(text.encode()).hexdigest() for name, text in (
        ("interpret", model.INTERPRET_SYSTEM), ("explain", model.EXPLAIN_SYSTEM),
        ("repair", model.REPAIR_SYSTEM), ("propose_checks", model.CHECKS_SYSTEM))}


def _case_source(suite: dict, case: dict) -> tuple[str, dict | None]:
    from countertrace.catalog import ROOT, apply_fault
    from countertrace.interface_map import load

    impl = suite["implementations"][case["impl"]]
    source = (ROOT / impl["path"]).read_text()
    if case.get("edits"):
        source = apply_fault(source, {"id": case["id"], "edits": case["edits"]})
    mapping = load(ROOT / impl["mapping"]) if impl.get("mapping") else None
    return source, mapping


def _calls(result: dict) -> list[dict]:
    return [{k: c.get(k) for k in ("task", "model_id", "latency_ms", "prompt_tokens", "completion_tokens",
                                   "status", "schema_error", "finish_reason")} for c in result.get("calls") or []]


def run_suite(suite_path: Path, out_path: Path, steps=("diagnosis", "explain", "repair", "interpret")) -> dict:
    """Run a frozen suite once, preserving every outcome. Writes results after each case."""
    from countertrace import repair, runs
    from countertrace.verify import now

    suite = json.loads(suite_path.read_text())
    store = runs.RunStore()
    results = {"suite": suite["version"], "started_at": now(), "model_ids": {
        "explain": model.config()["model_id"], "repair": model.config()["repair_model_id"] or model.config()["model_id"],
        "interpret": model.config()["fast_model_id"] or model.config()["model_id"]},
        "prompt_sha256": prompt_hashes(), "cases": [], "briefs": None}

    def save() -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2, default=str))

    for case in suite["cases"]:
        source, mapping = _case_source(suite, case)
        entry = {k: case.get(k) for k in ("id", "impl", "depth", "expected", "category", "class", "summary")}
        entry["held_out"] = suite["implementations"][case["impl"]]["held_out"]
        run = store.create_verification(source_text=source, depth=case["depth"], interface_map=mapping,
                                        origin="evaluation", title=f"{suite['version']} {case['id']}")
        store.execute(run["id"])
        state = store.load(run["id"])
        v = state.get("verification") or {}
        findings = v.get("findings", [])
        formal = next((f for f in findings if f["source"] == "formal"), None)
        entry["diagnosis"] = {
            "run_id": run["id"], "state": state["state"], "headline": (state.get("verdict") or {}).get("headline"),
            "obligations": {o["id"]: o["status"] for o in v.get("obligations", [])},
            "findings": [{k: f[k] for k in ("source", "test", "cycle", "check", "requirement_id")} for f in findings],
            "formal_replay": (formal or {}).get("replay", {}).get("status"),
            "integrity": v.get("integrity", []), "timings": v.get("timings"),
        }
        headline = entry["diagnosis"]["headline"]
        if case["expected"] == "faulty":
            entry["diagnosis"]["outcome"] = "reproduced" if headline == "counterexample" and (
                formal is None or entry["diagnosis"]["formal_replay"] == "reproduced") else (
                "counterexample_replay_mismatch" if headline == "counterexample" else f"not_reproduced:{headline}")
        else:
            entry["diagnosis"]["outcome"] = "false_alarm" if headline == "counterexample" else (
                "no_counterexample" if headline == "no_counterexample" else f"inconclusive:{headline}")
        if case["expected"] == "faulty" and headline == "counterexample" and "explain" in steps:
            res = model.explain_run(state, source)
            latest = store.load(run["id"]); latest["explanation"] = res; store.save(latest)
            entry["explanation"] = {"status": res["status"], "citation_check": res.get("citation_check"),
                                    "finding": res.get("finding"), "result": res.get("result"), "calls": _calls(res),
                                    "review": None}
        if case["expected"] == "faulty" and headline == "counterexample" and "repair" in steps:
            parent = store.load(run["id"])
            parent["repair"] = {"status": "running", "max_attempts": repair.MAX_ATTEMPTS, "attempts": [],
                                "parent_frozen": parent["verification"]["frozen"], "started_at": now()}
            store.save(parent)
            started = time.monotonic()
            repair.run_loop(store, run["id"])
            r = store.load(run["id"])["repair"]
            entry["repair"] = {
                "status": r["status"], "wall_s": round(time.monotonic() - started, 2),
                "attempts": [{k: a.get(k) for k in ("index", "status", "summary", "candidate_run_id", "frozen_match",
                                                     "rationale", "diff", "diagnostics")} | {"calls": _calls(a)}
                             for a in r["attempts"]],
                "attempts_used": len(r["attempts"]),
                "passed_on_attempt": next((a["index"] for a in r["attempts"] if a["status"] == "passed_unchanged_checks"), None),
            }
        results["cases"].append(entry)
        save()
    if "interpret" in steps:
        tmp = out_path.parent / "briefs.json"
        tmp.write_text(json.dumps(suite["briefs"]))
        results["briefs"] = interpret_briefs(tmp)
        tmp.unlink()
    results["finished_at"] = now()
    results["summary"] = summarize(results)
    save()
    return results


def summarize(results: dict) -> dict:
    cases = results["cases"]
    faulty = [c for c in cases if c["expected"] == "faulty"]
    controls = [c for c in cases if c["expected"] == "correct"]
    repaired = [c for c in faulty if (c.get("repair") or {}).get("status") == "passed"]
    attempted = [c for c in faulty if c.get("repair")]
    calls = [call for c in cases for call in ((c.get("explanation") or {}).get("calls") or [])] + \
            [call for c in cases for a in ((c.get("repair") or {}).get("attempts") or []) for call in a["calls"]] + \
            [call for b in ((results.get("briefs") or {}).get("results") or []) for call in b["calls"]]
    return {
        "diagnosis_reproduced": f"{sum(c['diagnosis']['outcome'] == 'reproduced' for c in faulty)} / {len(faulty)}",
        "categories_reproduced": sorted({c['category'] for c in faulty if c['diagnosis']['outcome'] == 'reproduced'}),
        "controls_false_alarms": f"{sum(c['diagnosis']['outcome'] == 'false_alarm' for c in controls)} / {len(controls)}",
        "controls_inconclusive": sum(c['diagnosis']['outcome'].startswith('inconclusive') for c in controls),
        "explanations_ok": f"{sum((c.get('explanation') or {}).get('status') == 'ok' for c in faulty)} / {len(faulty)}",
        "repair_all_cases": f"{len(repaired)} / {len(faulty)}",
        "repair_attempted_cases": f"{len(repaired)} / {len(attempted)}",
        "repair_first_attempt": sum((c.get('repair') or {}).get('passed_on_attempt') == 1 for c in faulty),
        "interpretation": (results.get("briefs") or {}).get("summary"),
        "model_requests": len(calls),
        "prompt_tokens": sum(c.get("prompt_tokens") or 0 for c in calls),
        "completion_tokens": sum(c.get("completion_tokens") or 0 for c in calls),
    }
