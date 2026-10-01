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


def main() -> None:
    started = time.monotonic()
    try:
        job = json.loads(JOB.joinpath("job.json").read_text())
    except (OSError, ValueError) as exc:
        fail(f"unreadable job: {exc}")
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
