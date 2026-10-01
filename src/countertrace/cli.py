"""Local diagnostics that neither execute RTL nor call a model endpoint."""

import argparse
import json
import os
import platform
import shutil
import subprocess

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
    return {
        "version": __version__,
        "stage": "workspace_scaffold",
        "python": platform.python_version(),
        "tools_on_path": tools,
        "docker_daemon": docker_status,
        "configuration_present_in_environment": {
            name: bool(os.environ.get(name, "").strip())
            for name in ("NEBIUS_API_KEY", "NEBIUS_BASE_URL", "NEBIUS_MODEL_ID")
        },
        "model_inference": "not_checked",
        "rtl_verification": "not_implemented",
        "note": "Presence is not validation. No model API or RTL execution was attempted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Countertrace workspace tools")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Report local prerequisites without inference")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable diagnostics")
    args = parser.parse_args()
    report = environment_report()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Countertrace {__version__}: workspace scaffold")
        print(f"Python: {report['python']}")
        for name, present in report["tools_on_path"].items():
            print(f"  {name}: {'found' if present else 'missing'}")
        print(f"Docker daemon: {report['docker_daemon']}")
        for name, present in report["configuration_present_in_environment"].items():
            print(f"  {name}: {'present' if present else 'not exported'}")
        print(report["note"])
        print("RTL verification and model integration remain to be implemented.")
    return 0
