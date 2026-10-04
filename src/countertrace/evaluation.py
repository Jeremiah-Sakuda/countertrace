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
