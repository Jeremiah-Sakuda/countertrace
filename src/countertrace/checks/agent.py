"""The check-writing agent: Nemotron writes properties, the golden gate tests them, repeat.

The model sees the specification, ports, and parameter settings, and after each
round the failing gate stage as plain data: compiler or tool errors with the
compiled line, a counterexample trace for a property the golden violates,
unreachable triggers, or surviving mutants as input sequences with reference
and faulty outputs. It never sees the golden source or mutation sites. The
loop is bounded, and every round is recorded.
"""

from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Callable

from countertrace import model
from countertrace.checks import gate
from countertrace.checks.compile import validate
from countertrace.checks.modules import Module

TASK = "write_checks"
MAX_ROUNDS = 4
SURVIVORS_SHOWN = 3
TRACE_ROWS = 24

SYSTEM = """You write formal properties for a synchronous hardware module from its plain-English specification. You never see its implementation.
Reply with JSON only: {"state": [...], "defs": [...], "memories": [...], "writes": [...], "properties": [...], "notes": "..."}.
- state: auxiliary registers that model the specification, each {"name", "width", "next"}. next is the value after every rising edge; include reset behavior in it (for example "rst ? 0 : ...").
- defs: named combinational helpers, each {"name", "width", "expr"}, usable in other defs, state, writes, and properties.
- memories: auxiliary arrays, each {"name", "width", "depth"}; writes: each {"memory", "when", "index", "value"}, applied at the rising edge.
- properties: each {"id" (snake_case), "when", "then", "why"}. At every rising edge after the first, if "when" holds then "then" must hold. Both are evaluated on the values just before that edge, so outputs reflect earlier edges; $past(x) is the value at the previous edge and $past(x, n) n edges ago.
Expressions use Verilog operators, the module's port and parameter names, your helper names, sized or unsized literals, and $past, $stable, $rose, $fell. Nothing else: no assignments, no other functions, no hierarchical names, no comments. Names are lowercase and must not reuse a port or parameter name.
The checks are proved at every listed parameter setting, so write them in terms of the parameter names, never their current values, and size helpers for the largest setting.
Write properties that every correct implementation satisfies and that catch wrong ones: check every output, including data and ordering where the specification defines them. Every "when" must be reachable. Keep the set small; a precise shadow model with a few comparisons is usually best."""


def output_cap() -> int | None:
    model.config()  # loads the private .env file before reading the task cap
    return model.output_limit(model.config(), TASK)


def describe(module: Module) -> str:
    def width(w):
        return f"{w} bit{'s' if w != 1 else ''}" if isinstance(w, int) else f"{w} bits"
    ports = [f"- {module.clock}: clock input (rising edge)"]
    ports += [f"- {n}: input, {width(w)}" for n, w in module.inputs.items()]
    ports += [f"- {n}: output, {width(w)}" for n, w in module.outputs.items()]
    settings = "; ".join(", ".join(f"{k} = {v}" for k, v in p.items()) for p in module.params)
    return (f"Module {module.top}.\nSpecification:\n{module.spec}\n\nPorts:\n" + "\n".join(ports)
            + f"\n\nParameter settings the checks must hold for: {settings}.")


def _table(rows: list[dict], module: Module, faulty: bool) -> str:
    rows = rows[:TRACE_ROWS]
    head = ["edge", *module.inputs, *module.outputs] + ([f"{n} (faulty)" for n in module.outputs] if faulty else [])
    lines = [" | ".join(head)]
    for i, row in enumerate(rows):
        reference = row.get("outputs_g") or row.get("outputs") or {}
        cells = [str(i), *(str(row["inputs"].get(n)) for n in module.inputs), *(str(reference.get(n)) for n in module.outputs)]
        if faulty:
            cells += [str((row.get("outputs_o") or {}).get(n)) for n in module.outputs]
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def feedback(result: dict, module: Module) -> str:
    stage = result.get("stage")
    where = ""
    if result.get("config"):
        where = " at " + ", ".join(f"{k} = {v}" for k, v in result["config"]["params"].items())
    if stage == "compile":
        return f"Your reply could not be compiled: {result['error']}. Fix it and resubmit the whole set."
    if stage in ("tool", "integrity"):
        return f"The formal tools rejected your properties{where}: {result['error']}. Fix the expression and resubmit the whole set."
    if stage == "golden":
        trace = _table(result["trace"], module, faulty=False) if result.get("trace") else "(no trace available)"
        return (f"A reference implementation that meets the specification violates {', '.join(result.get('failed') or ['your properties'])}{where}. "
                "Those properties are wrong, not the design. Counterexample (values just before each edge):\n"
                f"{trace}\nCorrect or remove them and resubmit the whole set.")
    if stage == "vacuity":
        return (f"The conditions of {', '.join(result['unreached'])} can never occur{where}, so those checks are vacuous. "
                "Fix their when conditions and resubmit the whole set.")
    if stage == "mutants":
        parts = [f"Your properties hold on the reference at every setting and caught {result['killed']} of {result['nonequivalent']} "
                 "faulty variants. These faulty variants passed every property; on each input sequence the reference and the faulty "
                 "outputs differ (values just before each edge):"]
        for s in result["survived"][:SURVIVORS_SHOWN]:
            parts.append(f"Variant {s['mutant']}:\n" + (_table(s["trace"], module, faulty=True) if s.get("trace") else "(no trace available)"))
        if result.get("unresolved"):
            parts.append(f"{result['unresolved']} variants could not be decided within the time limit.")
        parts.append("Add or strengthen properties so these variants fail, keep the ones that work, and resubmit the whole set.")
        return "\n\n".join(parts)
    return "The previous round could not be evaluated. Resubmit the whole set."


def summary(result: dict) -> dict:
    """A compact, model-safe record of one gate result."""
    keep = ("stage", "passed", "error", "status", "failed", "unreached", "config", "total", "killed", "equivalent",
            "invalid", "unresolved", "nonequivalent", "kill_rate")
    out = {k: result[k] for k in keep if k in result}
    if "survived" in result:
        out["survived"] = [s["mutant"] for s in result["survived"]]
    return out


def run_loop(module: Module, workdir: Path, image: dict, cancel: threading.Event | None = None,
             on_round: Callable[[dict], None] | None = None, max_rounds: int = MAX_ROUNDS, model_id: str | None = None) -> dict:
    cap = output_cap()
    if not cap:
        return {"status": "unavailable", "detail": "Set COUNTERTRACE_CHECKS_OUTPUT_TOKEN_LIMIT before writing checks.", "rounds": []}
    base = describe(module)
    user = base
    rounds: list[dict] = []
    for index in range(max_rounds):
        if cancel is not None and cancel.is_set():
            break
        reply = model.guarded(model.structured)(TASK, SYSTEM, user, lambda v: validate(v, module), max_tokens=cap, model_id=model_id)
        record = {"index": index, "calls": reply.get("calls", []), "model_status": reply["status"]}
        if reply["status"] == "schema_error":
            # A reply in the wrong format uses up a round; its validator message goes back like any gate failure.
            error = next((c.get("schema_error") for c in reversed(record["calls"]) if c.get("schema_error")), reply.get("detail"))
            record.update(gate={"stage": "format", "passed": False, "error": error},
                          feedback=f"Your reply did not match the required format: {error}. Reply with the whole set as one JSON object.")
            rounds.append(record)
            if on_round:
                on_round(record)
            user = f"{base}\n\n{record['feedback']}"
            continue
        if reply["status"] != "ok":
            record["detail"] = reply.get("detail")
            rounds.append(record)
            if on_round:
                on_round(record)
            break
        props = reply["result"]
        round_dir = workdir / f"round-{index}"
        result = gate.run_gate(module, props, round_dir, image, cancel)
        record.update(properties=props, gate=summary(result), feedback=None)
        if not (result.get("passed") and not result.get("survived")):
            record["feedback"] = feedback(result, module)
        (round_dir / "round.json").parent.mkdir(parents=True, exist_ok=True)
        (round_dir / "round.json").write_text(json.dumps({**record, "gate_full": result}, indent=1, default=str))
        rounds.append(record)
        if on_round:
            on_round(record)
        if result.get("passed") and not result.get("survived"):
            break
        user = f"{base}\n\nYour previous properties:\n{json.dumps(props)}\n\n{record['feedback']}"
    promoted = [r for r in rounds if (r.get("gate") or {}).get("passed")]
    best = max(promoted, key=lambda r: (r["gate"]["killed"], -r["index"])) if promoted else None
    return {"status": "promoted" if best else "not_promoted", "rounds": rounds, "promoted_round": best["index"] if best else None}
