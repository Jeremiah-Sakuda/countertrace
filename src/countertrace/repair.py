"""Bounded repair loop: the model proposes DUT source; the unchanged checks decide.

Every candidate passes admission again, must keep the module interface, and is
verified as a separate child run. A candidate succeeds only if the child run's
frozen check set (contract, harness, stimulus, limits, tasks, property counts)
is identical to the parent's and every obligation resolves without a
counterexample, tool error, or unresolved item. All attempts are preserved.
"""

from __future__ import annotations

import difflib
import os
import threading

from countertrace import model
from countertrace.admission import admit
from countertrace.verify import now

MAX_ATTEMPTS = 3
PASSING = {"simulation_passed", "bounded_pass", "proved"}
_lock = threading.Lock()


def unified_diff(before: str, after: str) -> str:
    return "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                        fromfile="a/dut.v", tofile="b/dut.v"))


def update(store, run_id: str, mutate) -> dict:
    with _lock:
        state = store.load(run_id)
        mutate(state)
        store.save(state)
        return state


def interface_problems(original: str, candidate: str, mapping: dict | None = None) -> list[str]:
    a, b = admit(original, mapping), admit(candidate, mapping)
    problems = [d.message for d in b.diagnostics]
    if a.module != b.module:
        problems.append(f"Module name changed from {a.module} to {b.module}.")
    if sorted(a.parameters) != sorted(b.parameters):
        problems.append("Parameter list changed.")
    if a.ports != b.ports:
        problems.append("Port list changed.")
    return problems


def judge(parent: dict, child: dict) -> tuple[str, str, bool]:
    v = child.get("verification") or {}
    frozen_match = v.get("frozen") == (parent.get("verification") or {}).get("frozen")
    obligations = v.get("obligations", [])
    if child.get("state") != "complete":
        return "error", f"Candidate run ended in state {child.get('state')}: {child.get('error', '')}", frozen_match
    if not frozen_match:
        return "error", "The candidate's check set differs from the parent's; the comparison is invalid.", False
    if v.get("findings"):
        f = v["findings"][0]
        return "failed_checks", (f"Counterexample: {f['check']} at cycle {f['cycle']} ({f['requirement_title']}) "
                                 f"in {f['test']}."), True
    bad = [o for o in obligations if o["status"] not in PASSING]
    if bad or v.get("integrity") or not obligations:
        return "failed_checks", f"{len(bad)} obligation(s) not resolved: " + ", ".join(
            f"{o['method']}:{o['check']}={o['status']}" for o in bad[:4]), True
    proved = sum(1 for o in obligations if o["status"] == "proved")
    return "passed_unchanged_checks", (f"All {len(obligations)} obligations resolved under the unchanged checks "
                                       f"({proved} proved, no counterexample)."), True


def verify_candidate(store, parent: dict, source: str, attempt: dict, origin: str) -> None:
    run_id = parent["id"]
    child = store.create_verification(source_text=source, depth=parent["depth"], parent_id=run_id,
                                      origin=origin, title=f"{parent.get('title', 'Run')} — candidate {attempt['index']}",
                                      formal_tasks=tuple(parent.get("formal_tasks", ("bmc", "prove", "cover"))),
                                      interface_map=parent.get("interface_map"))
    attempt.update(status="verifying", candidate_run_id=child["id"])
    update(store, run_id, lambda s: s["repair"]["attempts"].__setitem__(attempt["index"] - 1, dict(attempt)))
    store.execute(child["id"])
    status, summary, frozen_match = judge(parent, store.load(child["id"]))
    attempt.update(status=status, summary=summary, frozen_match=frozen_match)


def run_loop(store, run_id: str) -> None:
    parent = store.load(run_id)
    original = (store.run_dir(run_id) / "dut.v").read_text()
    finding = model.primary_finding(parent)
    rows = parent["verification"]["traces"][finding["trace"]]
    current = original
    attempts: list[dict] = []
    for index in range(1, MAX_ATTEMPTS + 1):
        attempt = {"index": index, "origin": "model", "status": "proposing", "started_at": now()}
        attempts.append(attempt)
        update(store, run_id, lambda s: s["repair"]["attempts"].append(dict(attempt)))
        proposal = model.propose_repair(current, finding, rows, attempts[:-1])
        attempt["calls"] = proposal.get("calls")
        if proposal["status"] != "ok":
            attempt.update(status="model_error", summary=proposal.get("detail", proposal["status"]))
        else:
            candidate = proposal["result"]["source"]
            attempt.update(rationale=proposal["result"]["rationale"], diff=unified_diff(original, candidate))
            problems = interface_problems(original, candidate, parent.get("interface_map"))
            if problems:
                attempt.update(status="admission_rejected", diagnostics=problems[:8],
                               summary="Rejected before execution: " + problems[0])
            elif candidate.strip() == current.strip():
                attempt.update(status="admission_rejected", summary="The candidate is identical to the current source.")
            else:
                verify_candidate(store, parent, candidate, attempt, "model_repair")
                current = candidate
                # COUNTERTRACE_REPAIR_FEEDBACK=off exists only for ablation studies.
                if attempt["status"] == "failed_checks" and os.environ.get("COUNTERTRACE_REPAIR_FEEDBACK", "on") != "off":
                    # Feed the candidate's own counterexample to the next proposal.
                    child = store.load(attempt["candidate_run_id"])
                    child_finding = model.primary_finding(child)
                    if child_finding:
                        finding = child_finding
                        rows = child["verification"]["traces"][child_finding["trace"]]
                        attempt["feedback"] = {k: child_finding[k] for k in ("test", "cycle", "check", "requirement_id")}
        attempt["finished_at"] = now()
        update(store, run_id, lambda s: s["repair"]["attempts"].__setitem__(index - 1, dict(attempt)))
        if attempt["status"] == "passed_unchanged_checks":
            break
    passed = any(a["status"] == "passed_unchanged_checks" for a in attempts)

    def finish(s: dict) -> None:
        s["repair"].update(status="passed" if passed else "exhausted", finished_at=now())
    update(store, run_id, finish)


def start(store, run_id: str) -> dict:
    parent = store.load(run_id)
    if parent.get("kind") != "verification" or parent.get("state") != "complete":
        raise ValueError("Repair needs a completed verification run.")
    if model.primary_finding(parent) is None:
        raise ValueError("There is no recorded failure to repair.")
    if (parent.get("repair") or {}).get("status") == "running":
        return {"started": False, "repair": parent["repair"]}
    cfg_reason = model.unavailable_reason(model.config())
    base = {"max_attempts": MAX_ATTEMPTS, "parent_frozen": parent["verification"]["frozen"],
            "started_at": now(), "attempts": (parent.get("repair") or {}).get("attempts", [])}
    if cfg_reason:
        repair = {**base, "status": "unavailable", "detail": cfg_reason}
        update(store, run_id, lambda s: s.__setitem__("repair", repair))
        return {"started": False, "repair": repair}
    repair = {**base, "status": "running", "attempts": []}
    update(store, run_id, lambda s: s.__setitem__("repair", repair))

    def target() -> None:
        try:
            run_loop(store, run_id)
        except Exception as exc:  # noqa: BLE001
            update(store, run_id, lambda s: s["repair"].update(status="error", detail=f"{type(exc).__name__}: {exc}",
                                                              finished_at=now()))

    threading.Thread(target=target, daemon=True).start()
    return {"started": True, "repair": repair}


def user_candidate(store, run_id: str, source: str) -> dict:
    """An owner-edited candidate, checked exactly like a model candidate (local test build only)."""
    parent = store.load(run_id)
    if parent.get("kind") != "verification" or parent.get("state") != "complete":
        raise ValueError("Candidates need a completed verification run.")
    original = (store.run_dir(run_id) / "dut.v").read_text()

    def init(s: dict) -> None:
        s.setdefault("repair", {"status": "manual", "max_attempts": MAX_ATTEMPTS, "attempts": [],
                                "parent_frozen": parent["verification"]["frozen"], "started_at": now()})
    state = update(store, run_id, init)
    attempt = {"index": len(state["repair"]["attempts"]) + 1, "origin": "user", "status": "proposing",
               "diff": unified_diff(original, source), "started_at": now()}
    update(store, run_id, lambda s: s["repair"]["attempts"].append(dict(attempt)))
    problems = interface_problems(original, source, parent.get("interface_map"))

    def target() -> None:
        if problems:
            attempt.update(status="admission_rejected", diagnostics=problems[:8],
                           summary="Rejected before execution: " + problems[0])
        else:
            try:
                verify_candidate(store, parent, source, attempt, "user_edit")
            except Exception as exc:  # noqa: BLE001
                attempt.update(status="error", summary=f"{type(exc).__name__}: {exc}")
        attempt["finished_at"] = now()
        update(store, run_id, lambda s: s["repair"]["attempts"].__setitem__(attempt["index"] - 1, dict(attempt)))

    threading.Thread(target=target, daemon=True).start()
    return {"started": True, "attempt": attempt}
