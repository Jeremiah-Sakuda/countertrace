"""Trusted parsing of SymbiYosys artifacts and counterexample normalization.

Solver step t applies the inputs present at step t to rising edge t; DUT
outputs and monitor state at step t are post-edge values of edge t-1. The
normalizer therefore pairs inputs at step k with outputs at step k+1 to form
application cycle k. This mapping is tested with the shared timing fixtures.
"""

from __future__ import annotations

import re

from countertrace.contract import Edge
from countertrace.scoreboard import Observation, TraceError

EXPECTED_PROPERTIES = {"assert": 3, "assume": 1, "cover": 12}
ASSERTION_TO_CHECK = {"ct_empty_flag": "empty_flag", "ct_full_flag": "full_flag", "ct_read_data": "read_data"}
COVER_LABELS = [
    "cov_reset_release", "cov_write_accepted", "cov_read_accepted", "cov_full", "cov_write_full",
    "cov_read_empty", "cov_both_empty", "cov_both_mid", "cov_both_full", "cov_wrap_write",
    "cov_wrap_read", "cov_recurrent_reset",
]


EXPECTED_LABELS = {"assert": set(ASSERTION_TO_CHECK), "cover": set(COVER_LABELS)}


def property_inventory(netlist: dict) -> dict:
    """Count formal property cells by flavor from the elaborated netlist (Yosys JSON).

    Every property must live in the trusted monitor and carry an expected label;
    a DUT cannot contribute assertions, assumptions, or covers.
    """
    counts = {"assert": 0, "assume": 0, "cover": 0}
    problems = []
    for module_name, module in netlist.get("modules", {}).items():
        for cell_name, cell in module.get("cells", {}).items():
            if cell.get("type") not in ("$check", "$assert", "$assume", "$cover", "$live", "$fair"):
                continue
            flavor = cell.get("parameters", {}).get("FLAVOR") or cell["type"].lstrip("$")
            flavor = str(flavor).strip()
            counts[flavor] = counts.get(flavor, 0) + 1
            if module_name != "ct_formal_top":
                problems.append(f"{flavor} property in module {module_name}")
            elif flavor in EXPECTED_LABELS and cell_name not in EXPECTED_LABELS[flavor]:
                problems.append(f"unexpected {flavor} property {cell_name}")
    return {"counts": counts, "problems": problems}


def parse_status(text: str | None) -> str | None:
    if not text:
        return None
    token = text.split()[0].upper()
    return token if token in {"PASS", "FAIL", "UNKNOWN", "ERROR", "TIMEOUT"} else None


def parse_failed_assertions(log: str) -> list[dict]:
    found = []
    for name, step in re.findall(r"failed assertion ct_formal_top\.(\w+) at \S+ step (\d+)", log):
        found.append({"assertion": name, "check": ASSERTION_TO_CHECK.get(name), "step": int(step)})
    return found


def parse_covers(log: str) -> dict[str, dict]:
    covers: dict[str, dict] = {}
    for step, name in re.findall(r"Reached cover statement in step (\d+) at ct_formal_top: (\w+)", log):
        covers[name] = {"reached": True, "step": int(step)}
    for name in re.findall(r"Unreached cover statement at ct_formal_top: (\w+)", log):
        covers.setdefault(name, {"reached": False, "step": None})
    return covers


def parse_vcd(text: str) -> dict[str, dict[int, int]]:
    """Return {hierarchical signal name: {smt_step: value}} for scalar/vector wires."""
    ids: dict[str, str] = {}
    scope: list[str] = []
    header, _, body = text.partition("$enddefinitions")
    for line in header.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "$scope":
            scope.append(parts[2])
        elif parts[0] == "$upscope":
            scope.pop()
        elif parts[0] == "$var" and len(parts) >= 5:
            ids[parts[3]] = ".".join(scope + [parts[4]])
    current: dict[str, int] = {}
    values: dict[str, dict[int, int]] = {name: {} for name in ids.values()}
    step = None

    def flush() -> None:
        if step is not None:
            for ident, value in current.items():
                if ident in ids:
                    values[ids[ident]][step] = value

    for line in body.splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("$"):
            continue
        if line.startswith("#"):
            continue
        if line[0] == "b":
            bits, ident = line[1:].split()
            value = int(bits.replace("x", "0").replace("z", "0"), 2)
        elif line[0] in "01xz":
            value, ident = (1 if line[0] == "1" else 0), line[1:]
        else:
            continue
        if ids.get(ident) == "smt_step":
            flush()
            step = value
        current[ident] = value
    flush()
    return values


def counterexample_observations(vcd_text: str, fail_step: int) -> tuple[list[Edge], list[Observation]]:
    """Normalize a solver counterexample to application cycles 0..fail_step-1."""
    values = parse_vcd(vcd_text)
    top = "ct_formal_top"
    needed = ["rst", "wr_en", "rd_en", "din", "dout", "empty", "full"]
    for name in needed:
        if f"{top}.{name}" not in values:
            raise TraceError(f"counterexample is missing signal {name}")
    sig = {name: values[f"{top}.{name}"] for name in needed}
    edges, observations = [], []
    for k in range(fail_step):
        try:
            edge = Edge(sig["rst"][k], sig["wr_en"][k], sig["rd_en"][k], sig["din"][k])
            obs = Observation(k, edge, sig["dout"][k + 1], bool(sig["empty"][k + 1]), bool(sig["full"][k + 1]))
        except KeyError as exc:
            raise TraceError(f"counterexample is missing step {exc}") from exc
        edges.append(edge)
        observations.append(obs)
    return edges, observations
