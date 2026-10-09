"""The golden gate for model-written properties.

Stage 1 (gate): for every parameter setting, the elaborated property inventory
must match the compiled set exactly, every property must be proved on the
golden reference by an unbounded proof, and every trigger must be reached by a
bounded cover. Stage 2 (mutants) runs only after stage 1 passes: the worker
generates mutants of the golden, and each is classified as killed, equivalent,
surviving, invalid, or unresolved. Tool errors, timeouts, and missing artifacts
never count toward promotion. The control service makes every decision here;
the worker only records artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import threading
import uuid

from countertrace import runner
from countertrace.checks.compile import compile_checker, compile_miter, compile_mutant_wrapper, expected_inventory, validate
from countertrace.checks.modules import Module
from countertrace.formal import parse_status, parse_vcd

SCHEMA = "countertrace-checks-job/1"
LIMITS = {"solver_s": 120, "bmc_depth": 20, "cover_depth": 20}
MUTANTS = {"count": 40, "seed": 1}
# Declared before evaluation: promote only with no unresolved mutants and at least this share of
# non-equivalent analyzable mutants killed.
PROMOTION_KILL_RATE = 0.9
BATCH_LIMIT_S = 20 * 60


@dataclass
class ChecksBatch:
    job_dir: Path
    out_dir: Path
    job_id: str
    job: dict = field(default_factory=dict)


def _prepare(root: Path, files: dict[str, str], job: dict) -> ChecksBatch:
    job_id = uuid.uuid4().hex[:12]
    job_dir, out_dir = root / "job", root / "out"
    job_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    os.chmod(out_dir, 0o777)  # the worker runs as an unprivileged container user
    for name, text in files.items():
        (job_dir / name).write_text(text)
    job = {"schema": SCHEMA, "job_id": job_id, "batch_limit_s": BATCH_LIMIT_S, **job}
    (job_dir / "job.json").write_text(json.dumps(job, indent=2))
    return ChecksBatch(job_dir, out_dir, job_id, job)


def _configs(module: Module) -> list[dict]:
    return [{"id": f"p{i}", "params": p} for i, p in enumerate(module.params)]


def _status(out: Path, name: str) -> str | None:
    path = out / name / "status"
    return parse_status(path.read_text()) if path.is_file() else None


def _log(out: Path, name: str) -> str:
    path = out / name / "logfile.txt"
    return path.read_text(errors="replace") if path.is_file() else ""


def inventory(netlist: dict, props: dict) -> list[str]:
    """Every property cell must be a compiled p_/r_ label or the template assumption, in ct_props_top only."""
    expected = expected_inventory(props)
    ids = {q["id"] for q in props["properties"]}
    counts = {"assert": 0, "assume": 0, "cover": 0}
    problems = []
    for module_name, module in netlist.get("modules", {}).items():
        for cell_name, cell in module.get("cells", {}).items():
            if cell.get("type") not in ("$check", "$assert", "$assume", "$cover", "$live", "$fair"):
                continue
            flavor = str(cell.get("parameters", {}).get("FLAVOR") or cell["type"].lstrip("$")).strip()
            counts[flavor] = counts.get(flavor, 0) + 1
            label = cell_name.lstrip("\\")
            if module_name != "ct_props_top":
                problems.append(f"{flavor} property in module {module_name}")
            elif flavor == "assert" and not (label.startswith("p_") and label[2:] in ids):
                problems.append(f"unexpected assertion {label}")
            elif flavor == "cover" and not (label.startswith("r_") and label[2:] in ids):
                problems.append(f"unexpected cover {label}")
    if counts != expected:
        problems.append(f"property counts {counts} differ from the compiled set {expected}")
    return problems


def failed_properties(log: str) -> list[str]:
    return sorted(set(re.findall(r"\bp_([a-z][a-z0-9_]*)", " ".join(l for l in log.splitlines() if "fail" in l.lower()))))


def unreached_triggers(log: str) -> list[str]:
    return sorted(set(re.findall(r"Unreached cover statement at [^:\n]*:\s*r_([a-z][a-z0-9_]*)", log)))


def trace_rows(vcd_text: str, top: str, module: Module, suffixes: tuple[str, ...] = ("",)) -> list[dict]:
    """Input values and outputs at each solver step, as the gate's feedback shows them."""
    values = parse_vcd(vcd_text)
    steps = sorted(next(iter(values.values()), {})) if values else []
    rows = []
    for step in steps:
        row = {"step": step, "inputs": {n: values.get(f"{top}.{n}", {}).get(step) for n in module.inputs}}
        for suffix in suffixes:
            row["outputs" + (f"_{suffix}" if suffix else "")] = {n: values.get(f"{top}.{n}{'_' + suffix if suffix else ''}", {}).get(step) for n in module.outputs}
        rows.append(row)
    return rows


def _first_vcd(out: Path, name: str) -> str | None:
    vcds = sorted((out / name).glob("trace*.vcd"))
    return vcds[0].read_text(errors="replace") if vcds else None


def _run(batch: ChecksBatch, image: dict, cancel: threading.Event | None) -> dict:
    record = runner.run_batch(batch, image, cancel, timeout_s=BATCH_LIMIT_S + 120)  # type: ignore[arg-type]
    worker = record.get("worker") or {}
    if record.get("cancelled") or record.get("timed_out") or record.get("container_returncode") != 0 or worker.get("deadline_reached"):
        raise GateToolError("the verifier batch did not complete")
    if worker.get("harness_hashes") != runner.harness_hashes():
        raise GateToolError("verifier harness hashes differ from the trusted copy")
    return record


class GateToolError(RuntimeError):
    pass


def run_gate(module: Module, props: dict, workdir: Path, image: dict, cancel: threading.Event | None = None,
             limits: dict | None = None, mutants: dict | None = None) -> dict:
    """Run both stages and return a decision-ready, model-safe result. Never raises for model errors."""
    from countertrace.checks.compile import PropertyError

    limits = dict(limits or {**LIMITS, **dict(module.limits)})
    try:
        props = validate(props, module)
        checker = compile_checker(props, module)
    except (PropertyError, KeyError, TypeError) as exc:
        return {"stage": "compile", "passed": False, "error": str(exc)}
    configs = _configs(module)
    result: dict = {"stage": "gate", "passed": False, "configs": configs, "limits": limits}
    try:
        batch = _prepare(workdir / "gate", {"golden.v": module.golden, "props.sv": checker},
                         {"stage": "gate", "top": module.top, "clock": module.clock, "configs": configs, "limits": limits})
        result["gate_run"] = {k: v for k, v in _run(batch, image, cancel).items() if k in ("wall_s", "image")}
        out = batch.out_dir
        for cfg in configs:
            cid = cfg["id"]
            inv_path = out / "inventory" / f"{cid}.json"
            if not inv_path.is_file():
                return {**result, "stage": "tool", "error": _tool_error(out, f"golden_prove_{cid}", checker), "config": cfg}
            problems = inventory(json.loads(inv_path.read_text()), props)
            if problems:
                return {**result, "stage": "integrity", "error": "; ".join(problems[:4]), "config": cfg}
            status = _status(out, f"golden_prove_{cid}")
            if status in (None, "ERROR"):
                return {**result, "stage": "tool", "error": _tool_error(out, f"golden_prove_{cid}", checker), "config": cfg}
            if status != "PASS":
                vcd = _first_vcd(out, f"golden_prove_{cid}")
                return {**result, "stage": "golden", "status": status, "config": cfg,
                        "failed": failed_properties(_log(out, f"golden_prove_{cid}")),
                        "trace": trace_rows(vcd, "ct_props_top", module) if vcd and status == "FAIL" else None}
            cover = _status(out, f"golden_cover_{cid}")
            if cover != "PASS":
                unreached = unreached_triggers(_log(out, f"golden_cover_{cid}"))
                if cover in (None, "ERROR") or not unreached:
                    return {**result, "stage": "tool", "error": f"cover check ended {cover or 'without a status'}", "config": cfg}
                return {**result, "stage": "vacuity", "status": cover, "config": cfg, "unreached": unreached}
        # Stage 2: mutants of the golden at the first parameter setting.
        mutation = dict(mutants or MUTANTS)
        batch = _prepare(workdir / "mutants", {"golden.v": module.golden, "props.sv": checker, "miter.sv": compile_miter(module),
                                               "mutant.sv": compile_mutant_wrapper(module)},
                         {"stage": "mutants", "top": module.top, "clock": module.clock, "configs": configs[:1], "limits": limits, "mutation": mutation})
        result["mutant_run"] = {k: v for k, v in _run(batch, image, cancel).items() if k in ("wall_s", "image")}
    except GateToolError as exc:
        return {**result, "stage": "tool", "error": str(exc)}
    return {**result, **classify_mutants(batch.out_dir, module)}


def _tool_error(out: Path, name: str, checker: str) -> str:
    text = _log(out, name) + "\n" + "\n".join(p.read_text(errors="replace") for p in (out / "logs").glob("*.log"))
    match = re.search(r"props\.sv:(\d+): ERROR: (.*)", text)
    if match:
        lines = checker.splitlines()
        line = lines[int(match.group(1)) - 1].strip() if int(match.group(1)) <= len(lines) else ""
        return f"{match.group(2).strip()} in compiled line: {line}"
    other = re.search(r"ERROR: (.*)", text)
    return other.group(1).strip() if other else "the formal tools could not process the properties"


def classify_mutants(out: Path, module: Module) -> dict:
    mutations_file = out / "mutants" / "mutations.ys"
    if not mutations_file.is_file():
        return {"stage": "tool", "passed": False, "error": "mutants could not be generated"}
    lines = [l for l in mutations_file.read_text().splitlines() if l.strip()]
    killed, equivalent, invalid, unresolved, survived = [], [], [], [], []
    for i in range(1, len(lines) + 1):
        props_status, equiv_status = _status(out, f"mutant_{i}_props"), _status(out, f"mutant_{i}_equiv")
        if equiv_status in (None, "ERROR"):
            invalid.append(i)  # the tools cannot analyze this mutant; reported, never scored
        elif props_status in (None, "ERROR"):
            return {"stage": "tool", "passed": False, "error": f"the property check on mutant {i} ended in a tool error"}
        elif props_status == "FAIL":
            killed.append(i)
        elif equiv_status == "PASS" and props_status == "PASS":
            equivalent.append(i)
        elif equiv_status == "FAIL" and props_status == "PASS":
            vcd = _first_vcd(out, f"mutant_{i}_equiv")
            survived.append({"mutant": i, "trace": trace_rows(vcd, "ct_miter", module, ("g", "o")) if vcd else None})
        else:
            unresolved.append(i)
    analyzable = len(lines) - len(invalid) - len(unresolved)
    nonequivalent = analyzable - len(equivalent)
    return {"stage": "mutants", "total": len(lines), "killed": len(killed), "equivalent": len(equivalent),
            "invalid": len(invalid), "unresolved": len(unresolved), "survived": survived, "nonequivalent": nonequivalent,
            "kill_rate": round(len(killed) / nonequivalent, 4) if nonequivalent else None,
            "passed": nonequivalent > 0 and not unresolved and len(killed) / nonequivalent >= PROMOTION_KILL_RATE}
