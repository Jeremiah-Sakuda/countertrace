"""Countertrace command line: diagnostics, verification, audit, model checks, and the local server."""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

from countertrace import __version__


def environment_report() -> dict:
    """Report prerequisites without exposing credentials or claiming readiness."""
    tools = {
        name: shutil.which(name) is not None
        for name in ("git", "node", "npm", "docker", "verilator", "yosys", "sby", "z3")
    }
    docker_status = "not_installed"
    if tools["docker"]:
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            docker_status = "reachable" if result.returncode == 0 else "unavailable"
        except (OSError, subprocess.TimeoutExpired):
            docker_status = "unavailable"
    verifier_image = "unknown"
    if docker_status == "reachable":
        from countertrace import runner

        verifier_image = runner.image_tag() if runner.image_id(runner.image_tag()) else "not_built"
    return {
        "version": __version__,
        "python": platform.python_version(),
        "tools_on_path": tools,
        "docker_daemon": docker_status,
        "verifier_image": verifier_image,
        "configuration_present_in_environment": {
            name: bool(os.environ.get(name, "").strip())
            for name in ("NEBIUS_API_KEY", "NEBIUS_BASE_URL", "NEBIUS_MODEL_ID")
        },
        "model_inference": "not_checked",
        "note": "Presence is not validation. HDL tools run only inside the verifier image, so "
                "missing host tools are expected. No model API or RTL execution was attempted.",
    }


def cmd_doctor(args) -> int:
    report = environment_report()
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    print(f"Countertrace {__version__}")
    print(f"Python: {report['python']}")
    for name, present in report["tools_on_path"].items():
        print(f"  {name}: {'found' if present else 'missing'}")
    print(f"Docker daemon: {report['docker_daemon']}")
    print(f"Verifier image: {report['verifier_image']}")
    for name, present in report["configuration_present_in_environment"].items():
        print(f"  {name}: {'present' if present else 'not exported'}")
    print(report["note"])
    return 0


def cmd_build_image(args) -> int:
    from countertrace import runner

    info = runner.ensure_image(build=True)
    print(json.dumps(info, indent=2))
    return 0


def cmd_verify(args) -> int:
    from countertrace import runs

    store = runs.RunStore()
    run = store.create_verification(example_id=args.example, source_path=args.file, depth=args.depth,
                                    formal_tasks=tuple(args.formal.split(",")) if args.formal else ())
    store.execute(run["id"])
    state = store.load(run["id"])
    print(runs.render_summary(state))
    print(f"\nRun directory: {store.run_dir(run['id'])}")
    return 0


def cmd_survey(args) -> int:
    """Run every bundled example and print raw outcomes. Development data, not a held-out evaluation."""
    import time

    from countertrace import catalog, runs

    store = runs.RunStore()
    rows = []
    for item in catalog.examples()["examples"]:
        run = store.create_verification(example_id=item["id"])
        store.execute(run["id"])
        state = store.load(run["id"])
        v = state.get("verification") or {}
        statuses = {o["id"]: o["status"] for o in v.get("obligations", [])}
        findings = v.get("findings", [])
        sim = next((f for f in findings if f["source"] == "simulation"), None)
        formal = next((f for f in findings if f["source"] == "formal"), None)
        rows.append({
            "example": item["id"], "split": item["split"], "depth": item["depth"], "expected": item["expected"],
            "run_id": run["id"], "state": state["state"], "headline": (state.get("verdict") or {}).get("headline"),
            "prove": sorted({s for k, s in statuses.items() if k.startswith("prove:")}),
            "cover": statuses.get("cover:reachability"),
            "sim_finding": f"{sim['check']}@{sim['cycle']} ({sim['test']})" if sim else None,
            "formal_finding": f"{formal['check']}@{formal['cycle']}" if formal else None,
            "replay": (formal or {}).get("replay", {}).get("status"),
            "first_finding_s": (v.get("timings") or {}).get("first_finding_s"),
            "total_s": (v.get("timings") or {}).get("total_s"),
        })
    print("| Example | Split | Depth | Author intent | Headline | Proof | Reachability | Simulation finding | Formal finding | Replay | First finding (s) | Total (s) |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['example']} | {r['split']} | {r['depth']} | {r['expected']} | {r['headline']} | {', '.join(r['prove'])} | "
              f"{r['cover']} | {r['sim_finding'] or '—'} | {r['formal_finding'] or '—'} | {r['replay'] or '—'} | "
              f"{r['first_finding_s'] or '—'} | {r['total_s']} |")
    out = runs.data_dir() / "reports"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"survey-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(rows, indent=2))
    print(f"\nRaw outcomes: {path}")
    return 0


def cmd_audit(args) -> int:
    from countertrace import runs

    store = runs.RunStore()
    run = store.create_audit(check_set=args.check_set, depth=args.depth)
    store.execute(run["id"])
    state = store.load(run["id"])
    print(json.dumps(state.get("audit", {}).get("summary", {}), indent=2))
    print(f"\nRun directory: {store.run_dir(run['id'])}")
    return 0


def cmd_model_check(args) -> int:
    from countertrace import model

    result = model.feasibility_check(args.run_id)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ok" else 1


def cmd_serve(args) -> int:
    from countertrace import server

    server.serve(args.host, args.port)
    return 0


def cmd_bundle(args) -> int:
    from countertrace import bundle, runs

    store = runs.RunStore()
    path = bundle.export(store, args.run_id)
    print(path)
    return 0


def cmd_record(args) -> int:
    from countertrace import runs

    path = runs.record(runs.RunStore(), args.run_id, args.note)
    print(path)
    return 0


def cmd_replay(args) -> int:
    from countertrace import bundle

    result = bundle.replay(args.bundle)
    print(json.dumps(result, indent=2))
    return 0 if result.get("matches") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Countertrace FIFO verification workbench")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="Report local prerequisites without inference")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable diagnostics")
    doctor.set_defaults(func=cmd_doctor)

    build = commands.add_parser("build-image", help="Build the pinned verifier image")
    build.set_defaults(func=cmd_build_image)

    verify = commands.add_parser("verify", help="Verify a bundled example or an owner-controlled file")
    source = verify.add_mutually_exclusive_group(required=True)
    source.add_argument("--example", help="Bundled example id")
    source.add_argument("--file", help="Local RTL file (local test build only)")
    verify.add_argument("--depth", type=int, choices=(2, 4), help="DEPTH for --file runs")
    verify.add_argument("--formal", default="bmc,prove,cover", help="Comma-separated SBY tasks, or empty")
    verify.set_defaults(func=cmd_verify)

    survey = commands.add_parser("survey", help="Run every bundled example and print raw outcomes")
    survey.set_defaults(func=cmd_survey)

    audit = commands.add_parser("audit", help="Run the supplemental-check audit against the fault library")
    audit.add_argument("--check-set", default="weak-learner-v1")
    audit.add_argument("--depth", type=int, choices=(2, 4), default=4)
    audit.set_defaults(func=cmd_audit)

    model_check = commands.add_parser("model-check", help="Explain a local failure with Nemotron and preserve the result")
    model_check.add_argument("--run-id", help="Completed local counterexample run (defaults to the newest)")
    model_check.set_defaults(func=cmd_model_check)

    serve = commands.add_parser("serve", help="Run the local control service and web interface")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(func=cmd_serve)

    export = commands.add_parser("bundle", help="Export a run's evidence bundle")
    export.add_argument("run_id")
    export.set_defaults(func=cmd_bundle)

    record = commands.add_parser("record", help="Freeze a completed run into recorded/ for the public journey")
    record.add_argument("run_id")
    record.add_argument("--note", default="", help="Context shown with the recorded run")
    record.set_defaults(func=cmd_record)

    replay = commands.add_parser("replay", help="Re-run deterministic checks from an evidence bundle")
    replay.add_argument("bundle")
    replay.set_defaults(func=cmd_replay)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
