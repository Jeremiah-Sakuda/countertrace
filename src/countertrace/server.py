"""Local control service: JSON API plus the built web interface.

Standard library only. The service owns run state, model calls, and the
verification queue. It never forwards model credentials to workers. Public
custom uploads stay disabled unless COUNTERTRACE_PUBLIC_UPLOADS_ENABLED=true,
which is intended only for the owner's local test build.
"""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import threading
import time
from urllib.parse import unquote, urlsplit

from countertrace import __version__, catalog, runner
from countertrace.contract import SUPPORTED_DEPTHS, Contract
from countertrace.runs import ROOT, RunStore

WEB_DIST = ROOT / "apps" / "web" / "dist"
RECORDED = ROOT / "recorded"
MAX_BODY = 128 * 1024
MODEL_CALLS_PER_HOUR = int(os.environ.get("COUNTERTRACE_MODEL_CALLS_PER_VISITOR_HOUR", "12"))


def uploads_enabled() -> bool:
    return os.environ.get("COUNTERTRACE_PUBLIC_UPLOADS_ENABLED", "false").strip().lower() == "true"


class App:
    def __init__(self) -> None:
        self.store = RunStore()
        self.model_lock = threading.Lock()
        self.status_cache: tuple[float, dict] | None = None
        self.visitor_runs: dict[str, str] = {}
        self.visitor_calls: dict[str, list[float]] = {}
        self.run_owner: dict[str, str] = {}
        self.visitor_lock = threading.Lock()

    # -- per-visitor limits ---------------------------------------------------
    def claim_run_slot(self, visitor: str) -> None:
        with self.visitor_lock:
            run_id = self.visitor_runs.get(visitor)
            if run_id:
                try:
                    active = self.store.load(run_id).get("state") in ("queued", "running")
                except KeyError:
                    active = False
                if active:
                    raise PermissionError("You already have a run in progress. Wait for it or cancel it first.")

    def note_run(self, visitor: str, run_id: str) -> None:
        with self.visitor_lock:
            self.visitor_runs[visitor] = run_id
            self.run_owner[run_id] = visitor

    def claim_model_call(self, visitor: str, units: int = 1) -> None:
        """Count model requests per visitor per hour. A repair counts as its worst case."""
        with self.visitor_lock:
            now = time.monotonic()
            calls = [t for t in self.visitor_calls.get(visitor, []) if now - t < 3600]
            if len(calls) + units > MODEL_CALLS_PER_HOUR:
                raise PermissionError("Model request limit reached for this hour. Recorded evidence remains available.")
            calls.extend([now] * units)
            self.visitor_calls[visitor] = calls

    def require_owner(self, visitor: str, run_id: str) -> None:
        """Only the visitor who started a run may cancel it (local runs: only from this machine)."""
        with self.visitor_lock:
            owner = self.run_owner.get(run_id)
        local = visitor in ("127.0.0.1", "::1") and os.environ.get("COUNTERTRACE_TRUST_PROXY", "").lower() != "true"
        if owner != visitor and not (owner is None and local):
            raise PermissionError("Only the visitor who started this run can cancel it.")

    def require_live(self, run_id: str) -> None:
        if re.fullmatch(r"[\w-]{1,64}", run_id) and (RECORDED / run_id).is_dir():
            raise PermissionError("Recorded runs are read-only. Start a live run to explain or repair it.")

    # -- read-only endpoints ----------------------------------------------
    def status(self) -> dict:
        if self.status_cache and time.monotonic() - self.status_cache[0] < 10:
            return self.status_cache[1]
        from countertrace import model

        docker_ok, docker_detail = runner.docker_available()
        tag = runner.image_tag()
        built = bool(docker_ok and runner.image_id(tag))
        result = {
            "version": __version__,
            "verifier": {"docker": docker_ok, "docker_detail": docker_detail, "image_tag": tag, "image_built": built,
                         "network": "none", "resources": runner.RESOURCES, "limits": runner.DEFAULT_LIMITS},
            "model": model.public_config(),
            "uploads_enabled": uploads_enabled(),
            "data_notice": "RTL executes only in the local isolated verifier container. When you request "
                           "interpretation, explanation, or repair, the RTL, contract, and relevant diagnostics "
                           "are sent to Nebius Token Factory for NVIDIA Nemotron inference. Do not submit "
                           "confidential designs.",
        }
        self.status_cache = (time.monotonic(), result)
        return result

    def examples(self) -> list[dict]:
        items = []
        for item in catalog.examples()["examples"]:
            fault = catalog.fault(item["source"]["fault"]) if item["source"].get("fault") else None
            items.append({
                **{k: item[k] for k in ("id", "split", "title", "depth", "brief", "expected")},
                "base": item["source"]["base"],
                "fault": {k: fault[k] for k in ("id", "summary", "category", "class", "intended_consequence")} if fault else None,
            })
        return items

    def example_detail(self, example_id: str) -> dict:
        item = catalog.example(example_id)
        contract = Contract(depth=item["depth"])
        summary = next(e for e in self.examples() if e["id"] == example_id)
        recorded = RECORDED / "interpretations" / f"{example_id}.json"
        return {**summary, "source": catalog.example_source(item), "contract": contract.document(),
                "contract_hash": contract.digest(),
                "recorded_interpretation": json.loads(recorded.read_text()) if recorded.is_file() else None}

    def profile(self) -> dict:
        timing = json.loads((catalog.FIXTURES / "timing" / "depth2_prd_sequence.json").read_text())
        return {"supported_depths": list(SUPPORTED_DEPTHS), "contract": Contract(depth=4).document(),
                "timing_example": timing}

    def recorded(self) -> list[dict]:
        items = []
        for path in sorted(RECORDED.glob("*/run.json")):
            state = json.loads(path.read_text())
            items.append({k: state.get(k) for k in ("id", "kind", "title", "example_id", "created_at", "finished_at",
                                                     "recorded", "verdict", "recorded_note")})
        return items

    def load_run(self, run_id: str) -> dict:
        recorded = RECORDED / run_id / "run.json"
        if re.fullmatch(r"[\w-]{1,64}", run_id) and recorded.is_file():
            return json.loads(recorded.read_text())
        return self.store.load(run_id)

    def run_root(self, run_id: str) -> Path:
        recorded = RECORDED / run_id
        if re.fullmatch(r"[\w-]{1,64}", run_id) and recorded.is_dir():
            return recorded
        return self.store.run_dir(run_id)

    # -- actions --------------------------------------------------------------
    def create_run(self, body: dict, visitor: str) -> dict:
        self.claim_run_slot(visitor)
        if body.get("example_id"):
            item = catalog.example(body["example_id"])
            contract_hash = Contract(depth=item["depth"]).digest()
            if body.get("accepted_contract_hash") != contract_hash:
                raise ValueError("Accept the current contract version before running.")
            state = self.store.create_verification(example_id=item["id"])
        elif body.get("source") is not None:
            if not uploads_enabled():
                raise PermissionError("Custom sources are disabled in this build. Use a bundled example.")
            depth = int(body.get("depth", 4))
            if Contract(depth=depth).digest() != body.get("accepted_contract_hash"):
                raise ValueError("Accept the current contract version before running.")
            mapping = None
            if body.get("interface_map"):
                from countertrace.interface_map import validate

                mapping = validate(body["interface_map"])  # MappingError is a ValueError -> 400
            state = self.store.create_verification(source_text=str(body["source"]), depth=depth,
                                                   origin="owner_upload", title=str(body.get("title") or "Custom source")[:80],
                                                   interface_map=mapping)
        else:
            raise ValueError("example_id or source is required")
        self.note_run(visitor, state["id"])
        self.store.start(state["id"])
        return state

    def create_audit(self, body: dict, visitor: str) -> dict:
        self.claim_run_slot(visitor)
        state = self.store.create_audit(check_set=str(body.get("check_set", "weak-learner-v1")),
                                        depth=int(body.get("depth", 4)))
        self.note_run(visitor, state["id"])
        self.store.start(state["id"])
        return state

    def interpret(self, body: dict) -> dict:
        from countertrace import model

        item = catalog.example(body["example_id"]) if body.get("example_id") else None
        brief = str(body.get("brief") or (item or {}).get("brief") or "")[:4000]
        depth = int(body.get("depth") or (item or {}).get("depth") or 4)
        return model.interpret(brief, Contract(depth=depth))

    def explain(self, run_id: str) -> dict:
        from countertrace import model

        state = self.store.load(run_id)
        result = model.explain_run(state, (self.store.run_dir(run_id) / "dut.v").read_text())
        state = self.store.load(run_id)
        state["explanation"] = result
        self.store.save(state)
        return result

    def repair(self, run_id: str) -> dict:
        from countertrace import repair

        return repair.start(self.store, run_id)

    def bundle(self, run_id: str) -> Path:
        from countertrace import bundle

        if re.fullmatch(r"[\w-]{1,64}", run_id) and (RECORDED / run_id).is_dir():
            return bundle.export(RecordedStore(), run_id)
        return bundle.export(self.store, run_id)


class RecordedStore:
    """Read-only access to recorded runs for bundle export."""

    def run_dir(self, run_id: str) -> Path:
        if not re.fullmatch(r"[\w-]{1,64}", run_id):
            raise KeyError(run_id)
        return RECORDED / run_id

    def load(self, run_id: str) -> dict:
        return json.loads((self.run_dir(run_id) / "run.json").read_text())


class Handler(BaseHTTPRequestHandler):
    app: App
    server_version = f"Countertrace/{__version__}"

    def log_message(self, fmt: str, *args) -> None:  # keep logs free of request bodies
        if os.environ.get("COUNTERTRACE_ACCESS_LOG"):
            super().log_message(fmt, *args)

    def send_json(self, value, status: int = 200) -> None:
        data = json.dumps(value, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, path: Path, download: str | None = None) -> None:
        data = path.read_bytes()
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix in (".v", ".sv", ".log", ".trace", ".vcd", ".sby", ".txt"):
            ctype = "text/plain; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')
        self.end_headers()
        self.wfile.write(data)

    def visitor(self) -> str:
        # Behind a trusted reverse proxy set COUNTERTRACE_TRUST_PROXY=true to use X-Forwarded-For.
        if os.environ.get("COUNTERTRACE_TRUST_PROXY", "").lower() == "true":
            forwarded = self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if forwarded:
                return forwarded
        return self.client_address[0]

    def body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("request body too large")
        raw = self.rfile.read(length) if length else b"{}"
        value = json.loads(raw or b"{}")
        if not isinstance(value, dict):
            raise ValueError("expected a JSON object")
        return value

    def handle_errors(self, func) -> None:
        try:
            func()
        except (KeyError, FileNotFoundError):
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except PermissionError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            self.send_json({"error": f"{type(exc).__name__}: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_GET(self) -> None:  # noqa: N802
        self.handle_errors(self.route_get)

    def do_POST(self) -> None:  # noqa: N802
        self.handle_errors(self.route_post)

    def route_get(self) -> None:
        app = self.app
        path = unquote(urlsplit(self.path).path)
        if path == "/api/status":
            return self.send_json(app.status())
        if path == "/api/profile":
            return self.send_json(app.profile())
        if path == "/api/examples":
            return self.send_json(app.examples())
        if m := re.fullmatch(r"/api/examples/([\w-]+)", path):
            return self.send_json(app.example_detail(m.group(1)))
        if path == "/api/check-sets":
            from countertrace import audit

            return self.send_json(audit.list_check_sets())
        if path == "/api/recorded":
            return self.send_json(app.recorded())
        if path == "/api/runs":
            return self.send_json(app.store.list())
        if m := re.fullmatch(r"/api/runs/([\w-]+)", path):
            return self.send_json(app.load_run(m.group(1)))
        if m := re.fullmatch(r"/api/runs/([\w-]+)/bundle", path):
            bundle_path = app.bundle(m.group(1))
            return self.send_file(bundle_path, download=bundle_path.name)
        if m := re.fullmatch(r"/api/runs/([\w-]+)/files/(.+)", path):
            root = app.run_root(m.group(1)).resolve()
            target = (root / m.group(2)).resolve()
            if root not in target.parents or not target.is_file():
                raise KeyError(path)
            return self.send_file(target)
        if path.startswith("/api/"):
            raise KeyError(path)
        return self.serve_static(path)

    def route_post(self) -> None:
        app = self.app
        path = unquote(urlsplit(self.path).path)
        body = self.body()
        visitor = self.visitor()
        if path == "/api/runs":
            return self.send_json(app.create_run(body, visitor), HTTPStatus.CREATED)
        if path == "/api/audits":
            return self.send_json(app.create_audit(body, visitor), HTTPStatus.CREATED)
        if path == "/api/check-sets/propose":
            from countertrace import audit

            app.claim_model_call(visitor)
            return self.send_json(audit.propose(str(body.get("description", ""))[:2000], int(body.get("depth", 4))))
        if path == "/api/interpret":
            app.claim_model_call(visitor)
            return self.send_json(app.interpret(body))
        if m := re.fullmatch(r"/api/runs/([\w-]+)/cancel", path):
            app.require_live(m.group(1))
            app.require_owner(visitor, m.group(1))
            return self.send_json({"cancelled": app.store.cancel(m.group(1))})
        if m := re.fullmatch(r"/api/runs/([\w-]+)/explain", path):
            app.require_live(m.group(1))
            app.claim_model_call(visitor)
            return self.send_json(app.explain(m.group(1)))
        if m := re.fullmatch(r"/api/runs/([\w-]+)/repair", path):
            app.require_live(m.group(1))
            from countertrace import repair

            app.claim_model_call(visitor, units=repair.MAX_ATTEMPTS * 2)  # each attempt may retry once
            return self.send_json(app.repair(m.group(1)))
        if m := re.fullmatch(r"/api/runs/([\w-]+)/candidates", path):
            if not uploads_enabled():
                raise PermissionError("Edited candidates are disabled in this build.")
            from countertrace import repair

            return self.send_json(repair.user_candidate(app.store, m.group(1), str(body.get("source", ""))))
        raise KeyError(path)

    def serve_static(self, path: str) -> None:
        if not WEB_DIST.is_dir():
            return self.send_json({"error": "web interface not built; run `make web`"}, HTTPStatus.NOT_FOUND)
        root = WEB_DIST.resolve()
        target = (root / path.lstrip("/")).resolve()
        if root != target and root not in target.parents:
            raise KeyError(path)
        if not target.is_file():
            target = root / "index.html"  # client-side routes
        self.send_file(target)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    Handler.app = App()
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Countertrace {__version__} serving http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
