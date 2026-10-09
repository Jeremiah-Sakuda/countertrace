"""Countertrace verifier worker. Runs inside the isolated container only.

Reads a strictly validated job description from /job/job.json, executes the
trusted harness against each design with fixed command lines, and writes raw
artifacts plus a step log to /out. It makes no pass/fail decision: the trusted
control service parses the artifacts. Job inputs cannot supply commands, flags,
paths outside /job, or harness files.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

JOB = Path("/job")
OUT = Path("/out")
HARNESS = Path("/opt/countertrace/harness")
WORK = Path("/tmp/work")
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
LOG_LIMIT = 1024 * 1024
ALLOWED_TASKS = ("bmc", "prove", "cover")


def fail(message: str) -> None:
    OUT.joinpath("worker_error.txt").write_text(message + "\n")
    print(message, file=sys.stderr)
    raise SystemExit(2)


def capped(text: str) -> tuple[str, bool]:
    data = text.encode(errors="replace")
    if len(data) <= LOG_LIMIT:
        return text, False
    return data[-LOG_LIMIT:].decode(errors="replace"), True


def run(step_id: str, argv: list[str], cwd: Path, timeout: int, log: Path, steps: list) -> dict:
    started = time.monotonic()
    record = {"id": step_id, "argv": argv, "timeout_s": timeout}
    try:
        proc = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False,
            env={"PATH": os.environ["PATH"], "HOME": "/tmp", "LANG": "C.UTF-8"},
        )
        output = proc.stdout + proc.stderr
        record.update(returncode=proc.returncode, timed_out=False)
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        record.update(returncode=None, timed_out=True)
    except OSError as exc:
        output = f"failed to start: {exc}"
        record.update(returncode=None, timed_out=False, start_error=str(exc))
    text, truncated = capped(output)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(text)
    record.update(duration_s=round(time.monotonic() - started, 3), log=str(log.relative_to(OUT)), log_truncated=truncated)
    steps.append(record)
    return record


def tool_versions() -> dict:
    versions = {}
    for name, argv in {
        "verilator": ["verilator", "--version"],
        "yosys": ["yosys", "-V"],
        "python": ["python3", "--version"],
    }.items():
        try:
            versions[name] = subprocess.run(argv, capture_output=True, text=True, timeout=20).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            versions[name] = "unavailable"
    release = Path("/opt/oss-cad-suite/COUNTERTRACE_RELEASE")
    versions["oss_cad_suite"] = release.read_text().strip() if release.exists() else "unknown"
    return versions


def harness_hashes() -> dict:
    return {
        path.name: "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(HARNESS.iterdir()) if path.is_file()
    }


def validate(job: dict) -> None:
    if job.get("schema") != "countertrace-job/1":
        fail("unsupported job schema")
    limits = job.get("limits", {})
    for key, bound in (("compile_s", 300), ("sim_s", 120), ("solver_s", 600), ("bmc_depth", 64), ("cover_depth", 64)):
        if not isinstance(limits.get(key), int) or not 1 <= limits[key] <= bound:
            fail(f"invalid limit {key}")
    designs = job.get("designs")
    if not isinstance(designs, list) or not 1 <= len(designs) <= 16:
        fail("invalid design list")
    for design in designs:
        if not ID.match(str(design.get("id", ""))):
            fail("invalid design id")
        if not IDENT.match(str(design.get("top", ""))):
            fail("invalid top module name")
        if design.get("depth") not in (2, 4) or design.get("width") != 8:
            fail("unsupported parameters")
        if not JOB.joinpath("designs", design["id"] + ".v").is_file():
            fail("missing design source")
        tests = design.get("sim_tests", [])
        if not isinstance(tests, list) or len(tests) > 64 or not all(ID.match(str(t)) for t in tests):
            fail("invalid simulation test list")
        for test in tests:
            if not JOB.joinpath("stimulus", test + ".txt").is_file():
                fail(f"missing stimulus {test}")
        formal = design.get("formal", [])
        if not isinstance(formal, list) or not all(t in ALLOWED_TASKS for t in formal):
            fail("invalid formal task list")
        if not isinstance(design.get("seed", 1), int):
            fail("invalid seed")


def run_design(design: dict, limits: dict, steps: list, deadline: float) -> None:
    did, top = design["id"], design["top"]
    depth, width = design["depth"], design["width"]
    work = WORK / did
    out = OUT / did
    work.mkdir(parents=True)
    out.mkdir(parents=True)
    shutil.copy(JOB / "designs" / f"{did}.v", work / "dut.v")
    for name in ("ct_sim_top.sv", "ct_formal_top.sv"):
        shutil.copy(HARNESS / name, work / name)

    # Elaborate the DUT alone and export its interface for the trusted parser.
    run(
        f"{did}:ports",
        ["yosys", "-q", "-p",
         f"read_verilog -sv dut.v; hierarchy -top {top} -chparam DEPTH {depth} -chparam WIDTH {width}; "
         f"proc; write_json {out}/ports.json"],
        work, limits["compile_s"], out / "logs" / "ports.log", steps,
    )
    # Count properties in the elaborated monitor + DUT; the host compares with the expected count.
    run(
        f"{did}:properties",
        ["yosys", "-p",
         f"read -formal -D CT_DUT={top} dut.v; read -formal -D CT_DUT={top} ct_formal_top.sv; "
         f"chparam -set DEPTH {depth} -set WIDTH {width} ct_formal_top; prep -top ct_formal_top; "
         f"write_json {out}/properties.json"],
        work, limits["compile_s"], out / "logs" / "properties.log", steps,
    )

    tests = design.get("sim_tests", [])
    if tests and time.monotonic() < deadline:
        compiled = run(
            f"{did}:compile",
            ["verilator", "--binary", "--timing", "--trace", "-Wno-fatal", "-Wno-lint", "-Wno-style",
             "--x-assign", "unique", "--x-initial", "unique", f"-DCT_DUT={top}",
             f"-GDEPTH={depth}", f"-GWIDTH={width}", "--top-module", "ct_sim_top",
             "--Mdir", str(work / "obj"), "-j", "2", "ct_sim_top.sv", "dut.v"],
            work, limits["compile_s"], out / "logs" / "compile.log", steps,
        )
        binary = work / "obj" / "Vct_sim_top"
        if compiled.get("returncode") == 0 and binary.exists():
            (out / "sim").mkdir()
            for test in tests:
                if time.monotonic() >= deadline:
                    break
                run(
                    f"{did}:sim:{test}",
                    [str(binary), f"+stim={JOB}/stimulus/{test}.txt", f"+trace={out}/sim/{test}.trace",
                     f"+vcd={out}/sim/{test}.vcd", "+verilator+rand+reset+2",
                     f"+verilator+seed+{design.get('seed', 1)}"],
                    work, limits["sim_s"], out / "logs" / f"sim_{test}.log", steps,
                )

    formal = design.get("formal", [])
    if formal and time.monotonic() < deadline:
        template = (HARNESS / "ct.sby.in").read_text()
        sby = (template.replace("@BMC_DEPTH@", str(limits["bmc_depth"]))
               .replace("@COVER_DEPTH@", str(limits["cover_depth"]))
               .replace("@TIMEOUT@", str(limits["solver_s"]))
               .replace("@TOP@", top).replace("@DEPTH@", str(depth)).replace("@WIDTH@", str(width)))
        (work / "ct.sby").write_text(sby)
        shutil.copy(work / "ct.sby", out / "ct.sby")
        for task in formal:
            if time.monotonic() >= deadline:
                break
            run(
                f"{did}:formal:{task}", ["sby", "-f", "ct.sby", task],
                work, limits["solver_s"] + 30, out / "logs" / f"sby_{task}.log", steps,
            )
            task_dir = work / f"ct_{task}"
            dest = out / "formal" / task
            dest.mkdir(parents=True)
            if task_dir.is_dir():
                for name in ("status", "PASS", "FAIL", "UNKNOWN", "ERROR", "TIMEOUT", "logfile.txt"):
                    if (task_dir / name).is_file():
                        shutil.copy(task_dir / name, dest / name)
                engine = task_dir / "engine_0"
                if engine.is_dir():
                    for vcd in sorted(engine.glob("trace*.vcd"))[:32]:
                        if vcd.stat().st_size <= 8 * 1024 * 1024:
                            shutil.copy(vcd, dest / vcd.name)


# -- model-written checks ---------------------------------------------------------
# The control service compiles the checker, miter, and mutant wrapper from trusted
# templates; this worker renders every tool script itself and generates mutants
# from a count and seed. Job data never supplies commands.
CHECKS_SCHEMA = "countertrace-checks-job/1"
MUTATE_LINE = re.compile(
    r"^mutate -mode (const0|const1|inv|cnot0|cnot1) -module [A-Za-z_][A-Za-z0-9_]* -cell [^\s;]+ -port [A-Za-z]+ -portbit \d+"
    r"( -ctrlbit \d+)?( -wire [^\s;]+ -wirebit \d+)?( -src [^\s;]+)*$")


def validate_checks(job: dict) -> None:
    if job.get("stage") not in ("gate", "mutants"):
        fail("invalid checks stage")
    if not IDENT.match(str(job.get("top", ""))):
        fail("invalid top module name")
    limits = job.get("limits", {})
    for key, bound in (("solver_s", 600), ("bmc_depth", 64), ("cover_depth", 64)):
        if not isinstance(limits.get(key), int) or not 1 <= limits[key] <= bound:
            fail(f"invalid limit {key}")
    configs = job.get("configs")
    if not isinstance(configs, list) or not 1 <= len(configs) <= 4:
        fail("invalid parameter settings")
    for cfg in configs:
        params = cfg.get("params")
        if not ID.match(str(cfg.get("id", ""))) or not isinstance(params, dict) or not params:
            fail("invalid parameter setting")
        if not all(IDENT.match(k) and isinstance(v, int) and 1 <= v <= 64 for k, v in params.items()):
            fail("invalid parameter value")
    needed = ["golden.v", "props.sv"]
    if job["stage"] == "mutants":
        mutation = job.get("mutation", {})
        if not isinstance(mutation.get("count"), int) or not 1 <= mutation["count"] <= 64:
            fail("invalid mutant count")
        if not isinstance(mutation.get("seed"), int) or not 0 <= mutation["seed"] <= 1_000_000:
            fail("invalid mutant seed")
        needed += ["miter.sv", "mutant.sv"]
    for name in needed:
        if not JOB.joinpath(name).is_file():
            fail(f"missing {name}")


def write_sby(path: Path, mode: str, limits: dict, files: list[str], script: list[str]) -> None:
    engine = {"prove": "abc pdr", "bmc": "abc bmc3", "bmc_smt": "smtbmc yices", "cover": "smtbmc yices"}[mode]
    mode = "bmc" if mode == "bmc_smt" else mode
    depth = limits["cover_depth"] if mode == "cover" else limits["bmc_depth"]
    path.write_text("\n".join(["[options]", f"mode {mode}", f"depth {depth}", f"timeout {limits['solver_s']}",
                               "[engines]", engine, "[script]", *script, "[files]", *files]) + "\n")


def keep_sby_artifacts(task_dir: Path, dest: Path, traces: bool) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("status", "logfile.txt"):
        if (task_dir / name).is_file():
            shutil.copy(task_dir / name, dest / name)
    if traces:
        for vcd in sorted(task_dir.glob("engine_*/trace*.vcd"))[:2]:
            if vcd.stat().st_size <= 4 * 1024 * 1024:
                shutil.copy(vcd, dest / vcd.name)


def chparams(params: dict, module: str) -> str:
    return "chparam " + " ".join(f"-set {k} {v}" for k, v in params.items()) + f" {module}"


def run_sby(name: str, work: Path, mode: str, limits: dict, files: list[str], script: list[str], steps: list, traces: bool) -> None:
    write_sby(work / f"{name}.sby", mode, limits, files, script)
    run(f"checks:{name}", ["sby", "-f", f"{name}.sby"], work, limits["solver_s"] + 30, OUT / "logs" / f"{name}.log", steps)
    log = work / name / "logfile.txt"
    # abc bmc3 refuses a check without state (for example constant properties); only then use smtbmc.
    if mode == "bmc" and log.is_file() and "Does not work for combinational networks" in log.read_text(errors="replace"):
        write_sby(work / f"{name}.sby", "bmc_smt", limits, files, script)
        run(f"checks:{name}:smtbmc", ["sby", "-f", f"{name}.sby"], work, limits["solver_s"] + 30, OUT / "logs" / f"{name}_smtbmc.log", steps)
    keep_sby_artifacts(work / name, OUT / name, traces)


def run_checks(job: dict, steps: list, deadline: float) -> None:
    from concurrent.futures import ThreadPoolExecutor

    top, limits, configs = job["top"], job["limits"], job["configs"]
    work = WORK / "checks"
    work.mkdir(parents=True)
    for name in ("golden.v", "props.sv", "miter.sv", "mutant.sv"):
        if JOB.joinpath(name).is_file():
            shutil.copy(JOB / name, work / name)
    dut = f"-D CT_DUT={top}"
    if job["stage"] == "gate":
        for cfg in configs:
            cid, params = cfg["id"], cfg["params"]
            (OUT / "inventory").mkdir(exist_ok=True)
            run(f"checks:inventory:{cid}", ["yosys", "-q", "-p",
                f"read -formal {dut} golden.v; read -formal {dut} props.sv; {chparams(params, 'ct_props_top')}; "
                f"prep -top ct_props_top; write_json {OUT}/inventory/{cid}.json"],
                work, limits["solver_s"], OUT / "logs" / f"inventory_{cid}.log", steps)
            script = [f"read -formal {dut} golden.v", f"read -formal {dut} props.sv", chparams(params, "ct_props_top"), "prep -top ct_props_top"]
            for mode in ("prove", "cover"):
                if time.monotonic() < deadline:
                    run_sby(f"golden_{mode}_{cid}", work, mode, limits, ["golden.v", "props.sv"], script, steps, traces=True)
        return
    # Mutants: generated here from the golden at the first parameter setting.
    params = configs[0]["params"]
    elaborate = f"read_verilog -sv golden.v; hierarchy -top {top} " + " ".join(f"-chparam {k} {v}" for k, v in params.items()) + "; proc; opt_clean"
    mutation = job["mutation"]
    run("checks:mutate-list", ["yosys", "-q", "-p", f"{elaborate}; mutate -list {mutation['count']} -seed {mutation['seed']} -o mutations.ys -s mutation_sources.txt"],
        work, limits["solver_s"], OUT / "logs" / "mutate_list.log", steps)
    (OUT / "mutants").mkdir(exist_ok=True)
    lines = [l for l in (work / "mutations.ys").read_text().splitlines() if l.strip()] if (work / "mutations.ys").is_file() else []
    if not lines or any(not MUTATE_LINE.match(l) for l in lines):
        OUT.joinpath("mutants", "mutations_rejected.txt").write_text("\n".join(lines) + "\n")
        return
    shutil.copy(work / "mutations.ys", OUT / "mutants" / "mutations.ys")
    if (work / "mutation_sources.txt").is_file():
        shutil.copy(work / "mutation_sources.txt", OUT / "mutants" / "mutation_sources.txt")
    (work / "all_mut.ys").write_text("\n".join([*elaborate.split("; "), *[f"{l} -ctrl mutsel 8 {i + 1}" for i, l in enumerate(lines)],
                                               "opt_clean", f"rename {top} {top}_all", "write_verilog -noattr all_mut.v"]) + "\n")
    built = run("checks:mutate-build", ["yosys", "-q", "-s", "all_mut.ys"], work, limits["solver_s"], OUT / "logs" / "mutate_build.log", steps)
    if built.get("returncode") != 0:
        return
    mut = f"-D CT_DUT={top}_mut"
    def one(i: int) -> None:
        if time.monotonic() >= deadline:
            return
        sel = f"-D CT_MUTSEL=8'd{i}"
        files = ["all_mut.v", "mutant.sv", "props.sv"]
        run_sby(f"mutant_{i}_props", work, "bmc", limits, files,
                ["read -formal all_mut.v", f"read -formal {sel} mutant.sv", f"read -formal {mut} props.sv",
                 chparams(params, "ct_props_top"), "prep -top ct_props_top"], steps, traces=False)
        run_sby(f"mutant_{i}_equiv", work, "prove", limits, ["golden.v", *files[:2], "miter.sv"],
                ["read -formal golden.v", "read -formal all_mut.v", f"read -formal {sel} mutant.sv",
                 f"read -formal -D CT_OTHER={top}_mut miter.sv", chparams(params, "ct_miter"), "prep -top ct_miter"], steps, traces=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(one, range(1, len(lines) + 1)))


def main() -> None:
    started = time.monotonic()
    try:
        job = json.loads(JOB.joinpath("job.json").read_text())
    except (OSError, ValueError) as exc:
        fail(f"unreadable job: {exc}")
    if job.get("schema") == CHECKS_SCHEMA:
        validate_checks(job)
        steps: list = []
        deadline = started + min(int(job.get("batch_limit_s", 900)), 1800)
        WORK.mkdir(parents=True, exist_ok=True)
        (OUT / "logs").mkdir(exist_ok=True)
        run_checks(job, steps, deadline)
        OUT.joinpath("worker_result.json").write_text(json.dumps({
            "schema": "countertrace-worker-result/1", "job_id": job.get("job_id"), "tool_versions": tool_versions(),
            "harness_hashes": harness_hashes(), "steps": steps, "deadline_reached": time.monotonic() >= deadline,
            "duration_s": round(time.monotonic() - started, 3)}, indent=2))
        return
    validate(job)
    steps: list = []
    deadline = started + job.get("batch_limit_s", 900)
    WORK.mkdir(parents=True, exist_ok=True)
    for design in job["designs"]:
        run_design(design, job["limits"], steps, deadline)
    result = {
        "schema": "countertrace-worker-result/1",
        "job_id": job.get("job_id"),
        "tool_versions": tool_versions(),
        "harness_hashes": harness_hashes(),
        "steps": steps,
        "deadline_reached": time.monotonic() >= deadline,
        "duration_s": round(time.monotonic() - started, 3),
    }
    OUT.joinpath("worker_result.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
