"""Export the public recorded journey to Vercel's Build Output API, without a backend.

Only Git-tracked curated records and verifier files enter the export. Private runs,
model configuration, .env, and the usage ledger are never loaded. Live actions are
unavailable, not simulated. Run after the web production build.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from countertrace import __version__, audit, bundle, server

ROOT = Path(__file__).resolve().parents[1]
NOTICE = "Recorded evidence demo. Live verification and model calls are available in the local test build."


def tracked_files(root: Path, directory: str) -> list[Path]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", directory],
                            check=True, capture_output=True)
    files = [Path(name.decode()) for name in result.stdout.split(b"\0") if name]
    for path in files:
        if (root / path).is_symlink() or not (root / path).is_file():
            raise ValueError(f"Deployment input must be a regular tracked file: {path}")
        if root.resolve() not in (root / path).resolve().parents:
            raise ValueError(f"Deployment input escapes the repository: {path}")
    return files


def recorded_status() -> dict:
    return {
        "version": __version__,
        "deployment": {"mode": "recorded", "live_available": False, "notice": NOTICE},
        "verifier": {"docker": False, "docker_detail": NOTICE, "image_tag": None,
                     "image_built": False, "network": "not running", "resources": {}, "limits": {}},
        "model": {"configured": False, "reason": NOTICE, "model_id": None, "repair_model_id": None,
                  "fast_model_id": None, "endpoint_host": None, "input_token_limit": None,
                  "output_token_limit": None, "spend": {"calls": 0, "prompt_tokens": 0,
                  "completion_tokens": 0, "estimated_cost_usd": None, "cost_status": "unavailable",
                  "spend_limit_usd": None}},
        "uploads_enabled": False,
        "data_notice": "This deployment serves published examples and recorded evidence only. "
                       "No RTL or model request is submitted from this demo.",
    }


def build(output: Path | None = None) -> dict:
    output = output or ROOT / ".vercel" / "output"
    web = ROOT / "apps" / "web" / "dist"
    if not (web / "index.html").is_file():
        raise ValueError("Build apps/web before exporting the recorded demo.")
    if output.exists():
        shutil.rmtree(output)
    static = output / "static"
    shutil.copytree(web, static)
    data = static / "demo-data"

    def write(endpoint: str, value) -> None:
        target = data / f"{endpoint}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, ensure_ascii=False, indent=1))

    # These catalog methods do not need App's run store, Docker status, or model config.
    app = server.App.__new__(server.App)
    write("status", recorded_status())
    write("profile", app.profile())
    examples = app.examples()
    public_recordings = tracked_files(ROOT, "recorded")
    write("examples", examples)
    for example in examples:
        detail = app.example_detail(example["id"], include_recorded=False)
        interpretation = Path("recorded") / "interpretations" / f"{example['id']}.json"
        if interpretation in public_recordings:
            detail["recorded_interpretation"] = json.loads((ROOT / interpretation).read_text())
        write(f"examples/{example['id']}", detail)
    write("check-sets", audit.list_check_sets())
    write("runs", [])
    write("unavailable", {"error": NOTICE})
    recordings = []
    with tempfile.TemporaryDirectory(prefix="countertrace-public-export-") as tmp:
        snapshot = Path(tmp)
        for directory in ("recorded", "verifier"):
            for relative in tracked_files(ROOT, directory):
                target = snapshot / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)

        class PublicStore:
            def run_dir(self, run_id):
                return snapshot / "recorded" / run_id

            def load(self, run_id):
                return json.loads((self.run_dir(run_id) / "run.json").read_text())

        store = PublicStore()
        for run_file in sorted((snapshot / "recorded").glob("*/run.json")):
            state = json.loads(run_file.read_text())
            run_id = run_file.parent.name
            if state.get("id") != run_id or not state.get("recorded") or state.get("state") != "complete":
                raise ValueError(f"Only completed explicitly recorded runs can be published: {run_id}")
            write(f"runs/{run_id}", state)
            recordings.append({k: state.get(k) for k in (
                "id", "kind", "title", "example_id", "created_at", "finished_at", "recorded", "verdict", "recorded_note")})
            public_run = data / "runs" / run_id
            shutil.copytree(run_file.parent, public_run / "files")
            if state.get("kind") == "verification":
                archive = bundle.export(store, run_id, verifier_root=snapshot / "verifier", output_dir=public_run)
                archive.rename(public_run / "bundle.zip")
    write("recorded", recordings)
    routes = [
        {"src": "/(.*)", "headers": {"X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer"}, "continue": True},
        {"src": "/api/(.*)", "methods": ["POST", "PUT", "PATCH", "DELETE"],
         "dest": "/demo-data/unavailable.json", "status": 405, "headers": {"Allow": "GET, HEAD"}},
        {"src": "/api/runs/(rec-[\\w-]+)/bundle", "methods": ["GET", "HEAD"],
         "dest": "/demo-data/runs/$1/bundle.zip", "headers": {"Content-Type": "application/zip",
         "Content-Disposition": 'attachment; filename="countertrace-evidence.zip"'}},
        {"src": "/api/runs/(rec-[\\w-]+)/files/(.*)", "methods": ["GET", "HEAD"],
         "dest": "/demo-data/runs/$1/files/$2", "headers": {"Content-Type": "text/plain; charset=utf-8"}},
        {"src": "/api/(.*)", "methods": ["GET", "HEAD"], "dest": "/demo-data/$1.json",
         "headers": {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "public, max-age=0, must-revalidate"}},
        {"handle": "filesystem"},
    ]
    (output / "config.json").write_text(json.dumps({"version": 3, "routes": routes}, indent=2))
    result = {"mode": "recorded", "live_available": False, "recordings": len(recordings),
              "examples": len(examples), "output": str(output)}
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    build()
