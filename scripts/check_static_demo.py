"""Unauthenticated checks of the recorded deployment; never starts a paid/live run."""

import argparse
import hashlib
import io
import json
from urllib import error, request
from urllib.parse import urlsplit
import zipfile


def check(base: str) -> dict:
    base = base.rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Use an HTTPS site URL without credentials, query, or fragment.")

    def fetch(path: str, method="GET"):
        req = request.Request(base + path, method=method, data=b"{}" if method == "POST" else None)
        try:
            with request.urlopen(req, timeout=30) as response:
                return response.status, response.headers, response.read()
        except error.HTTPError as exc:
            with exc:
                return exc.code, exc.headers, exc.read()

    def get_json(path: str):
        status, headers, body = fetch(path)
        assert status == 200, (path, status)
        assert "application/json" in headers.get("Content-Type", ""), path
        return json.loads(body)

    status = get_json("/api/status")
    assert status["deployment"]["live_available"] is False
    assert status["model"]["configured"] is False
    assert status["uploads_enabled"] is False
    assert get_json("/api/runs") == []
    recordings = get_json("/api/recorded")
    examples = get_json("/api/examples")
    assert recordings and examples
    modules = get_json("/api/modules")
    assert modules
    for module in modules:
        detail = get_json(f"/api/modules/{module['id']}")
        assert detail["id"] == module["id"] and detail["spec"]
    for example in examples:
        detail = get_json(f"/api/examples/{example['id']}")
        assert detail["id"] == example["id"] and detail["source"] and detail["contract_hash"]
    bundles = 0
    for item in recordings:
        state = get_json(f"/api/runs/{item['id']}")
        assert state["recorded"] and state["state"] == "complete"
        if state["kind"] not in ("verification", "checks"):
            continue
        code, headers, data = fetch(f"/api/runs/{item['id']}/bundle")
        assert code == 200 and "application/zip" in headers.get("Content-Type", "")
        assert "attachment" in headers.get("Content-Disposition", "")
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            for name, digest in manifest["files"].items():
                assert "sha256:" + hashlib.sha256(archive.read(name)).hexdigest() == digest, name
        bundles += 1
    for path in ("/.env", "/.env.local", "/.countertrace/model_usage.jsonl", "/api/runs/not-a-public-run"):
        assert fetch(path)[0] == 404, path
    code, _, body = fetch("/api/runs", "POST")
    assert code == 405 and "Recorded evidence" in json.loads(body)["error"]
    return {"url": base, "authentication": "none", "recordings": len(recordings),
            "examples": len(examples), "bundles_hash_checked": bundles,
            "live_actions": "unavailable (405)", "private_paths": "404"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    args = parser.parse_args()
    print(json.dumps(check(args.url), indent=2))
