"""Evidence bundles: a readable report, a manifest, inputs, and raw artifacts.

A bundle lets anyone re-run the deterministic checks without a model call.
Content hashes identify matching inputs and artifacts; they do not establish
authorship or soundness. Replay compares check outcomes, not log bytes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import zipfile

from countertrace import __version__, runner
from countertrace.contract import ASSUMPTIONS, Contract, sha256_json
from countertrace.stimulus import render, suite
from countertrace.verify import STATUS_LABELS, Verification

ROOT = Path(__file__).resolve().parents[2]
BUNDLE_LIMIT = 32 * 1024 * 1024


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def git_commit() -> str | None:
    try:
        proc = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "src", "verifier", "fixtures"],
                               capture_output=True, text=True, timeout=10).stdout.strip()
        return proc.stdout.strip() + ("-dirty" if dirty else "") if proc.returncode == 0 else None
    except OSError:
        return None


def outcome(state: dict) -> dict:
    v = state.get("verification") or {}
    return {
        "obligations": {o["id"]: o["status"] for o in v.get("obligations", [])},
        "findings": [{"source": f["source"], "test": f["test"], "cycle": f["cycle"], "check": f["check"]}
                     for f in v.get("findings", [])],
        "replay": (v.get("replay") or {}).get("status"),
    }


def fmt(value) -> str:
    return "—" if value is None else (f"0x{value:02x}" if isinstance(value, int) and not isinstance(value, bool) else str(value))


def report(state: dict, contract: Contract) -> str:
    v = state.get("verification") or {}
    lines = [f"# Countertrace evidence report — {state.get('title', state['id'])}", ""]
    lines += [f"Run `{state['id']}` · {state.get('created_at')} · state **{state.get('state')}** · "
              f"{'recorded run' if state.get('recorded') else 'live run'}", ""]
    lines += ["## Intended behavior", "",
              f"Contract `{contract.profile}` v{contract.version}, DEPTH={contract.depth}, WIDTH={contract.width} "
              f"(`{contract.digest()}`).", ""]
    for row in contract.document()["requirements"].values():
        lines.append(f"- **{row['title']}.** {row['text']}")
    lines += ["", "Assumptions:", ""] + [f"- {a}" for a in ASSUMPTIONS] + [""]
    lines += ["## Finding", ""]
    findings = v.get("findings", [])
    if not findings:
        lines += ["No counterexample was found by the methods below. This is not a claim of complete correctness.", ""]
    for f in findings:
        lines += [f"- **{f['requirement_title']}** — {f['check_text']}.",
                  f"  First observed mismatch at cycle {f['cycle']} in `{f['test']}` ({f['source']}): expected "
                  f"dout {fmt(f['expected']['dout'])}, empty {f['expected']['empty']}, full {f['expected']['full']}; observed "
                  f"dout {fmt(f['observed']['dout'])}, empty {f['observed']['empty']}, full {f['observed']['full']}."]
        for e in f.get("related_events", []):
            lines.append(f"  - {e['text']}")
        if f.get("replay"):
            lines.append(f"  - Replay: {f['replay']['status']} — {f['replay'].get('detail', '')}")
    lines += ["", "## Method and results", "", "| Method | Check | Result | Detail |", "| --- | --- | --- | --- |"]
    for o in sorted(v.get("obligations", []), key=lambda o: (o["method"], o["check"])):
        detail = str(o.get("detail", "")).replace("|", "\\|")
        lines.append(f"| {o['method']} | {o['check']} | {o.get('label', STATUS_LABELS.get(o['status']))} | {detail} |")
    unresolved = [o for o in v.get("obligations", []) if o["status"] in ("unresolved", "tool_error", "not_checked")]
    lines += ["", f"## Unresolved items ({len(unresolved)})", ""]
    lines += [f"- {o['method']}:{o['check']} — {o.get('detail', '')}" for o in unresolved] or ["- none"]
    for problem in v.get("integrity", []):
        lines.append(f"- Integrity: {problem}")
    explanation = state.get("explanation")
    if explanation and explanation.get("result"):
        r = explanation["result"]
        lines += ["", "## Model explanation (not part of the verdict)", "",
                  f"Model: {', '.join(c.get('model_id') or '?' for c in explanation.get('calls', []))}. "
                  f"Citation check: {explanation.get('citation_check', {}).get('valid')} valid, "
                  f"{len(explanation.get('citation_check', {}).get('invalid', []))} invalid.", "", r["summary"], ""]
        lines += [f"{i}. {s['text']} (cycles {s['cycles']}, signals {s['signals']})" for i, s in enumerate(r["steps"], 1)]
        lines += ["", f"Likely cause: {r['likely_cause']['text']} (lines {r['likely_cause']['lines']})",
                  f"Next action: {r['next_action']}", f"Limits: {r['limits']}"]
    repair = state.get("repair")
    if repair:
        lines += ["", f"## Repair attempts ({repair.get('status')})", ""]
        for a in repair.get("attempts", []):
            lines.append(f"- Attempt {a['index']} ({a.get('origin')}): {a['status']} — {a.get('summary', '')} "
                         f"{'candidate run ' + a['candidate_run_id'] if a.get('candidate_run_id') else ''}")
    lines += ["", "## Limits", "",
              "Simulation passing, no counterexample within N cycles, and an unbounded proof are different claims. "
              "Results apply only to the exact parameters, contract, assumptions, and toolchain recorded in the manifest. "
              "Two-state semantics; no X-propagation, timing, or synthesized-device claim.", ""]
    return "\n".join(lines)


def export(store, run_id: str) -> Path:
    state = store.load(run_id)
    if state.get("kind") != "verification":
        raise ValueError("Bundles are exported for verification runs.")
    run_dir = store.run_dir(run_id)
    contract = Contract(depth=state["depth"])
    files: dict[str, bytes] = {}
    files["inputs/dut.v"] = (run_dir / "dut.v").read_bytes()
    files["inputs/contract.json"] = json.dumps(contract.document(), indent=2).encode()
    driven = sorted((run_dir / "batches").glob("*-sim/job/stimulus/*.txt"))
    if driven:  # exactly what the run drove
        for path in driven:
            files[f"inputs/stimulus/{path.name}"] = path.read_bytes()
    else:
        for name, edges in suite(contract.depth).items():
            files[f"inputs/stimulus/{name}.txt"] = render(edges).encode()
    for path in sorted((ROOT / "verifier").rglob("*")):
        if path.is_file():
            files[f"verifier/{path.relative_to(ROOT / 'verifier')}"] = path.read_bytes()
    truncated = []
    budget = BUNDLE_LIMIT
    for path in sorted((run_dir / "batches").rglob("*")):
        if not path.is_file() or "job/designs" in str(path):
            continue
        data = path.read_bytes()
        name = f"artifacts/{path.relative_to(run_dir)}"
        if len(data) > budget:
            truncated.append(name)
            continue
        budget -= len(data)
        files[name] = data
    v = state.get("verification") or {}
    files["artifacts/normalized_traces.json"] = json.dumps(v.get("traces", {}), indent=1).encode()
    files["report.md"] = report(state, contract).encode()
    files["REPLAY.md"] = (
        "# Replaying this bundle\n\nNo model call is needed. With Docker running and this repository checked out at "
        "the commit in `manifest.json`:\n\n```sh\ncountertrace replay path/to/this-bundle.zip\n```\n\n"
        "Replay builds the verifier image from the pinned Dockerfile, re-runs the same DUT, contract, stimulus, and "
        "formal tasks, and compares obligation statuses and findings with `manifest.json` `outcome`. Identical "
        "timings, model text, and log bytes are not expected.\n").encode()
    batches = v.get("batches", {})
    manifest = {
        "schema": "countertrace-evidence/1",
        "countertrace_version": __version__,
        "git_commit": git_commit(),
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run": {k: state.get(k) for k in ("id", "title", "kind", "example_id", "origin", "parent_id", "created_at",
                                          "started_at", "finished_at", "state", "recorded")},
        "dut": {"path": "inputs/dut.v", "hash": sha256(files["inputs/dut.v"])},
        "contract": {"hash": contract.digest(), "parameters": {"DEPTH": contract.depth, "WIDTH": contract.width},
                     "assumptions": ASSUMPTIONS},
        "frozen_check_set": v.get("frozen"),
        "image": state.get("image"),
        "tool_versions": next((b.get("tool_versions") for b in batches.values() if b.get("tool_versions")), None),
        "commands": {kind: {"container": b.get("argv"), "steps": [{"id": s["id"], "argv": s["argv"], "returncode": s.get("returncode"),
                                                                  "timed_out": s.get("timed_out"), "duration_s": s.get("duration_s")}
                                                                 for s in b.get("steps", [])]}
                     for kind, b in batches.items()},
        "timings": v.get("timings"),
        "model": {
            "explanation_calls": (state.get("explanation") or {}).get("calls"),
            "repair_calls": [c for a in (state.get("repair") or {}).get("attempts", []) for c in (a.get("calls") or [])],
            "cost": "unavailable unless per-token prices are configured",
        },
        "relationships": {"parent_id": state.get("parent_id"),
                          "candidates": [a.get("candidate_run_id") for a in (state.get("repair") or {}).get("attempts", [])
                                         if a.get("candidate_run_id")]},
        "omitted_or_terminated": truncated + [f"{s['id']}: {s['status']}" for s in v.get("stages", [])
                                              if s["status"] in ("cancelled", "skipped", "error")],
        "outcome": outcome(state),
    }
    manifest["files"] = {name: sha256(data) for name, data in sorted(files.items())}
    files["manifest.json"] = json.dumps(manifest, indent=2).encode()
    from countertrace.runs import data_dir

    out = data_dir() / "bundles" / f"countertrace-{run_id}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in sorted(files.items()):
            zf.writestr(name, data)
    return out


def replay(bundle_path: str) -> dict:
    with zipfile.ZipFile(bundle_path) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        for name, digest in manifest["files"].items():
            if sha256(zf.read(name)) != digest:
                return {"matches": False, "error": f"{name} does not match its manifest hash"}
        bundled_harness = {Path(n).name: sha256(zf.read(n)) for n in manifest["files"] if n.startswith("verifier/harness/")}
        source = zf.read("inputs/dut.v").decode()
        contract_doc = json.loads(zf.read("inputs/contract.json"))
    if bundled_harness != runner.harness_hashes():
        return {"matches": False, "error": "The bundled verifier harness differs from this checkout. Check out "
                                           f"commit {manifest.get('git_commit')} and replay again."}
    contract = Contract(depth=contract_doc["parameters"]["DEPTH"], width=contract_doc["parameters"]["WIDTH"])
    if contract.digest() != manifest["contract"]["hash"]:
        return {"matches": False, "error": "Contract hash mismatch."}
    image = runner.ensure_image(build=True)
    frozen = manifest.get("frozen_check_set") or {}
    current = {name: sha256_json(render(edges)) for name, edges in suite(contract.depth).items()}
    if frozen.get("stimulus") != current:
        return {"matches": False, "error": "The recorded stimulus differs from this checkout's frozen suite. Check out "
                                           f"commit {manifest.get('git_commit')} and replay again."}
    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
        v = Verification(Path(tmp), "dut", source, contract, lambda: None, threading.Event(), image,
                         limits=frozen.get("limits"), formal_tasks=tuple(frozen.get("formal_tasks", ("bmc", "prove", "cover"))))
        state = {"verification": v.run()}
    now_outcome = outcome(state)
    recorded = manifest["outcome"]
    differences = []
    for oid, status in recorded["obligations"].items():
        if now_outcome["obligations"].get(oid) != status:
            differences.append(f"{oid}: recorded {status}, replay {now_outcome['obligations'].get(oid)}")
    if recorded["findings"] != now_outcome["findings"]:
        differences.append(f"findings differ: recorded {recorded['findings']}, replay {now_outcome['findings']}")
    if recorded.get("replay") != now_outcome.get("replay"):
        differences.append(f"counterexample replay status: recorded {recorded.get('replay')}, now {now_outcome.get('replay')}")
    if state["verification"]["frozen"] != frozen:
        differences.append("frozen check set differs from the recorded one")
    return {"matches": not differences, "differences": differences, "recorded": recorded, "replayed": now_outcome,
            "frozen_match": state["verification"]["frozen"] == frozen, "image": image}
