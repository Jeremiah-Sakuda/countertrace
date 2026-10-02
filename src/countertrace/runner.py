"""Launch verification batches in the isolated container.

The control service owns every command line. A batch receives a read-only job
directory (designs, stimulus, job.json) and a writable output directory. The
container has no network, no added capabilities, a read-only root filesystem,
bounded memory, CPUs, and processes, and no environment from the host, so no
model credential can reach it.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "verifier"
HARNESS = VERIFIER / "harness"
IMAGE_REPO = "countertrace-verifier"

DEFAULT_LIMITS = {"compile_s": 60, "sim_s": 30, "solver_s": 120, "bmc_depth": 24, "cover_depth": 24}
BATCH_LIMIT_S = 15 * 60
RESOURCES = {"cpus": "4", "memory": "4g", "pids": "256", "tmpfs": "1g"}


class RunnerError(Exception):
    pass


class Cancelled(Exception):
    pass


def harness_hashes() -> dict[str, str]:
    return {
        path.name: "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(HARNESS.iterdir()) if path.is_file()
    }


def verifier_digest() -> str:
    """Content hash of everything copied into the worker stage of the image."""
    h = hashlib.sha256()
    for path in [VERIFIER / "Dockerfile", VERIFIER / "worker.py", *sorted(HARNESS.iterdir())]:
        h.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()[:16]


def image_tag() -> str:
    return f"{IMAGE_REPO}:{verifier_digest()}"


def docker_available() -> tuple[bool, str]:
    if not shutil.which("docker"):
        return False, "docker CLI not installed"
    try:
        proc = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"docker unavailable: {exc}"
    if proc.returncode != 0:
        return False, "docker daemon unreachable"
    return True, proc.stdout.strip()


def image_id(tag: str) -> str | None:
    proc = subprocess.run(["docker", "image", "inspect", tag, "--format", "{{.Id}}"],
                          capture_output=True, text=True, timeout=20)
    return proc.stdout.strip() if proc.returncode == 0 else None


def ensure_image(build: bool = True) -> dict:
    tag = image_tag()
    ident = image_id(tag)
    if ident is None:
        if not build:
            raise RunnerError(f"verifier image {tag} is not built; run `countertrace build-image`")
        proc = subprocess.run(["docker", "build", "--target", "worker", "-t", tag, str(VERIFIER)],
                              capture_output=True, text=True, timeout=3600)
        if proc.returncode != 0:
            raise RunnerError("verifier image build failed:\n" + proc.stderr[-4000:])
        ident = image_id(tag)
    return {"tag": tag, "image_id": ident, "verifier_digest": verifier_digest()}


@dataclass
class Batch:
    job_dir: Path
    out_dir: Path
    designs: list[dict]
    limits: dict
    job_id: str

    def write(self) -> None:
        job = {
            "schema": "countertrace-job/1",
            "job_id": self.job_id,
            "limits": self.limits,
            "batch_limit_s": BATCH_LIMIT_S,
            "designs": self.designs,
        }
        (self.job_dir / "job.json").write_text(json.dumps(job, indent=2))


def prepare_batch(root: Path, designs: list[tuple[dict, str]], stimulus: dict[str, str],
                  limits: dict | None = None) -> Batch:
    """designs: (spec, source) pairs. spec has id, top, depth, width, sim_tests, formal, seed."""
    job_id = uuid.uuid4().hex[:12]
    job_dir, out_dir = root / "job", root / "out"
    (job_dir / "designs").mkdir(parents=True)
    (job_dir / "stimulus").mkdir()
    out_dir.mkdir(parents=True)
    os.chmod(out_dir, 0o777)  # the worker runs as an unprivileged container user
    for spec, source in designs:
        (job_dir / "designs" / f"{spec['id']}.v").write_text(source)
    for name, text in stimulus.items():
        (job_dir / "stimulus" / f"{name}.txt").write_text(text)
    batch = Batch(job_dir, out_dir, [spec for spec, _ in designs], dict(limits or DEFAULT_LIMITS), job_id)
    batch.write()
    return batch


def worker_identity() -> str:
    """Keep bind-mounted outputs owned by the service, without running as root.

    Linux preserves numeric ownership on bind mounts. The image's default UID
    would leave nested artifacts that the service cannot remove. A root caller
    still uses the image's unprivileged UID instead of granting worker root.
    """
    return f"{os.getuid() or 10001}:{os.getgid() or 10001}"


def run_batch(batch: Batch, image: dict, cancel: threading.Event | None = None,
              timeout_s: int = BATCH_LIMIT_S + 60) -> dict:
    name = f"ct-{batch.job_id}"
    argv = [
        "docker", "run", "--rm", "--name", name,
        "--user", worker_identity(),
        "--network", "none", "--read-only",
        "--tmpfs", f"/tmp:rw,exec,nosuid,size={RESOURCES['tmpfs']}",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", RESOURCES["pids"], "--memory", RESOURCES["memory"], "--cpus", RESOURCES["cpus"],
        "-v", f"{batch.job_dir.resolve()}:/job:ro",
        "-v", f"{batch.out_dir.resolve()}:/out:rw",
        image["tag"],
    ]
    started = time.monotonic()
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            env={"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""),
                                 **({"DOCKER_HOST": os.environ["DOCKER_HOST"]} if "DOCKER_HOST" in os.environ else {})})
    cancelled = timed_out = False
    while proc.poll() is None:
        if cancel is not None and cancel.wait(0.25):
            cancelled = True
        elif time.monotonic() - started > timeout_s:
            timed_out = True
        else:
            continue
        subprocess.run(["docker", "kill", name], capture_output=True, timeout=30)
        break
    output, _ = proc.communicate(timeout=60)
    (batch.out_dir / "container.log").write_text((output or "")[-1024 * 1024:])
    record = {
        "argv": argv,
        "container_returncode": proc.returncode,
        "wall_s": round(time.monotonic() - started, 3),
        "cancelled": cancelled,
        "timed_out": timed_out,
        "image": image,
        "resources": RESOURCES,
        "network": "none",
    }
    if cancelled:
        raise Cancelled()
    result_path = batch.out_dir / "worker_result.json"
    if result_path.is_file():
        record["worker"] = json.loads(result_path.read_text())
    else:
        error = batch.out_dir / "worker_error.txt"
        record["worker_error"] = error.read_text() if error.is_file() else "worker produced no result"
    return record
