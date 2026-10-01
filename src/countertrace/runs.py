"""Durable run records under COUNTERTRACE_DATA_DIR (default .countertrace/)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import threading
import time

from countertrace import catalog, runner
from countertrace.contract import Contract
from countertrace.verify import FORMAL_TASKS, STATUS_LABELS, Verification, now

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_RUN_LIMIT = 1  # one verification at a time; each uses up to two worker batches


def data_dir() -> Path:
    configured = os.environ.get("COUNTERTRACE_DATA_DIR", ".countertrace")
    path = Path(configured)
    return path if path.is_absolute() else ROOT / path


class RunStore:
    def __init__(self, root: Path | None = None):
        self.root = (root or data_dir()) / "runs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.cancels: dict[str, threading.Event] = {}
        self.locks: dict[str, threading.RLock] = {}
        self.active = threading.BoundedSemaphore(ACTIVE_RUN_LIMIT)
        self.guard = threading.Lock()

    # -- persistence -----------------------------------------------------
    def run_dir(self, run_id: str) -> Path:
        if not run_id.replace("-", "").isalnum() or len(run_id) > 40:
            raise KeyError(run_id)
        return self.root / run_id

    def save(self, state: dict) -> None:
        path = self.run_dir(state["id"]) / "run.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=1, default=str))
        tmp.replace(path)

    def load(self, run_id: str) -> dict:
        path = self.run_dir(run_id) / "run.json"
        if not path.is_file():
            raise KeyError(run_id)
        return json.loads(path.read_text())

    def list(self) -> list[dict]:
        items = []
        for path in sorted(self.root.glob("*/run.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                state = json.loads(path.read_text())
            except ValueError:
                continue
            items.append({k: state.get(k) for k in (
                "id", "kind", "example_id", "title", "state", "created_at", "parent_id", "recorded", "verdict")})
        return items

    def new_id(self, kind: str) -> str:
        return f"{time.strftime('%Y%m%d-%H%M%S')}-{kind[:3]}-{secrets.token_hex(3)}"

    # -- creation --------------------------------------------------------
    def create_verification(self, example_id: str | None = None, source_path: str | None = None,
                            source_text: str | None = None, depth: int | None = None,
                            formal_tasks=FORMAL_TASKS, parent_id: str | None = None,
                            origin: str = "bundled_example", title: str | None = None, extra: dict | None = None) -> dict:
        if example_id:
            item = catalog.example(example_id)
            source = catalog.example_source(item)
            depth = item["depth"]
            title = title or item["title"]
        elif source_path or source_text is not None:
            source = Path(source_path).read_text() if source_path else source_text
            if depth is None:
                raise ValueError("depth is required for non-example sources")
            origin = origin if source_text is not None else "local_file"
            title = title or (Path(source_path).name if source_path else "Custom source")
        else:
            raise ValueError("an example or source is required")
        contract = Contract(depth=depth)
        run_id = self.new_id("verification")
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True)
        (run_dir / "dut.v").write_text(source)
        (run_dir / "contract.json").write_text(json.dumps(contract.document(), indent=2))
        state = {
            "id": run_id,
            "kind": "verification",
            "title": title,
            "example_id": example_id,
            "origin": origin,
            "parent_id": parent_id,
            "depth": depth,
            "formal_tasks": list(formal_tasks),
            "state": "queued",
            "created_at": now(),
            "recorded": False,
            **(extra or {}),
        }
        self.save(state)
        return state

    def create_audit(self, check_set: str, depth: int = 4) -> dict:
        from countertrace import audit

        audit.load_check_set(check_set)  # validate early
        run_id = self.new_id("audit")
        self.run_dir(run_id).mkdir(parents=True)
        state = {"id": run_id, "kind": "audit", "title": f"Supplemental-check audit: {check_set}",
                 "check_set": check_set, "depth": depth, "state": "queued", "created_at": now(), "recorded": False}
        self.save(state)
        return state

    # -- execution -------------------------------------------------------
    def cancel(self, run_id: str) -> bool:
        event = self.cancels.get(run_id)
        if event is None:
            return False
        event.set()
        return True

    def start(self, run_id: str) -> threading.Thread:
        thread = threading.Thread(target=self.execute, args=(run_id,), daemon=True)
        thread.start()
        return thread

    def execute(self, run_id: str) -> None:
        state = self.load(run_id)
        cancel = self.cancels.setdefault(run_id, threading.Event())
        lock = self.locks.setdefault(run_id, threading.RLock())
        acquired = False
        try:
            while not (acquired := self.active.acquire(timeout=0.5)):
                if cancel.is_set():
                    break
            if cancel.is_set():
                state["state"] = "cancelled"
                state["finished_at"] = now()
                self.save(state)
                return
            state["state"] = "running"
            state["started_at"] = now()
            self.save(state)
            image = runner.ensure_image(build=False)
            state["image"] = image
            if state["kind"] == "verification":
                self.execute_verification(state, cancel, lock, image)
            elif state["kind"] == "audit":
                from countertrace import audit

                audit.execute(self, state, cancel, image)
            state["state"] = "cancelled" if cancel.is_set() else "complete"
        except Exception as exc:  # noqa: BLE001 - record every failure explicitly
            state["state"] = "failed"
            state["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            if acquired:
                self.active.release()
            state["finished_at"] = now()
            with lock:
                self.save(state)
            self.cancels.pop(run_id, None)

    def execute_verification(self, state: dict, cancel: threading.Event, lock: threading.RLock, image: dict) -> None:
        run_dir = self.run_dir(state["id"])
        contract = Contract(depth=state["depth"])
        source = (run_dir / "dut.v").read_text()

        def emit() -> None:
            with lock:
                state["verification"] = verification.state
                state["verdict"] = verdict(verification.state)
                self.save(state)

        verification = Verification(run_dir, "dut", source, contract, emit, cancel, image,
                                    formal_tasks=tuple(state.get("formal_tasks", FORMAL_TASKS)))
        verification.run()
        emit()


def verdict(v: dict) -> dict:
    """A method-specific summary. Never a single verified/correct label."""
    obligations = v.get("obligations", [])
    statuses = {o["status"] for o in obligations}
    if "unsupported" in statuses:
        headline = "unsupported"
    elif v.get("findings") or "counterexample" in statuses:
        headline = "counterexample"
    elif not obligations:
        headline = "pending"
    elif statuses & {"tool_error"}:
        headline = "tool_error"
    elif statuses & {"unresolved", "not_checked"}:
        headline = "unresolved"
    else:
        headline = "no_counterexample"
    return {
        "headline": headline,
        "counts": {s: sum(1 for o in obligations if o["status"] == s) for s in STATUS_LABELS},
        "unresolved": sum(1 for o in obligations if o["status"] in ("unresolved", "tool_error", "not_checked")),
    }


def render_summary(state: dict) -> str:
    lines = [f"Run {state['id']} [{state['state']}] {state.get('title', '')}"]
    if state.get("error"):
        lines.append(f"  error: {state['error']}")
    v = state.get("verification") or {}
    for stage in v.get("stages", []):
        lines.append(f"  stage {stage['id']:<20} {stage['status']:<9} {stage.get('detail', '')}")
    for o in sorted(v.get("obligations", []), key=lambda o: (o["method"], o["check"])):
        lines.append(f"  {o['method']:<10} {o['check']:<12} {o['status']:<18} {o.get('detail', '')[:90]}")
    for f in v.get("findings", []):
        replay = f.get("replay", {}).get("status", "")
        lines.append(f"  FINDING [{f['source']}:{f['test']}] cycle {f['cycle']} {f['check']} "
                     f"row={f['requirement_id']} expected={f['expected']} observed={f['observed']} {replay}")
    for problem in v.get("integrity", []):
        lines.append(f"  INTEGRITY {problem}")
    if v.get("timings"):
        lines.append(f"  timings: {v['timings']}")
    return "\n".join(lines)
