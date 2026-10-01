"""Trusted scoring of recorded traces against the independent reference queue.

Both simulation traces and normalized formal counterexamples are scored here,
so the two engines share one cycle convention. A trace that is truncated,
malformed, or disagrees with the stimulus it claims to have driven is a tool
error, never a pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from countertrace.contract import CHECKS, REQUIREMENTS, Contract, Edge, ReferenceFifo

ROWS = [r for r in REQUIREMENTS if r != "wraparound"]


class TraceError(Exception):
    """The recorded evidence is missing, malformed, or inconsistent."""


@dataclass
class Observation:
    cycle: int
    edge: Edge
    dout: int
    empty: bool
    full: bool


def parse_sim_trace(text: str, depth: int, width: int, stimulus: list[Edge]) -> list[Observation]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != f"CTTRACE 1 DEPTH={depth} WIDTH={width}":
        raise TraceError("trace header missing or parameters differ from the job")
    if not lines[-1].startswith("END "):
        raise TraceError("trace is truncated (no END marker)")
    try:
        end = int(lines[-1].split()[1])
    except (IndexError, ValueError) as exc:
        raise TraceError("malformed END marker") from exc
    body = lines[1:-1]
    if end != len(stimulus) or len(body) != len(stimulus):
        raise TraceError(f"trace recorded {len(body)} cycles (END {end}); stimulus has {len(stimulus)}")
    observations = []
    for index, line in enumerate(body):
        parts = line.split()
        if len(parts) != 8:
            raise TraceError(f"malformed trace line {index + 2}")
        try:
            cycle, rst, wr, rd = (int(p) for p in parts[:4])
            din, dout = int(parts[4], 16), int(parts[5], 16)
            empty, full = int(parts[6]), int(parts[7])
        except ValueError as exc:
            raise TraceError(f"non-numeric value on trace line {index + 2}") from exc
        edge = Edge(rst, wr, rd, din)
        if cycle != index or edge != stimulus[index]:
            raise TraceError(f"trace cycle {index} does not match the driven stimulus")
        if empty not in (0, 1) or full not in (0, 1):
            raise TraceError(f"flag value out of range at cycle {index}")
        observations.append(Observation(cycle, edge, dout, bool(empty), bool(full)))
    return observations


def normalize(contract: Contract, observations: list[Observation]) -> list[dict]:
    """Score each observed cycle against the reference; return normalized cycle rows."""
    model = ReferenceFifo(contract)
    rows = []
    for obs in observations:
        step = model.step(obs.edge)
        mismatches = []
        if obs.empty != step.expected_empty:
            mismatches.append("empty_flag")
        if obs.full != step.expected_full:
            mismatches.append("full_flag")
        if step.accepted_read and obs.dout != step.expected_dout:
            mismatches.append("read_data")
        rows.append({
            "cycle": obs.cycle,
            "rst": obs.edge.rst,
            "wr_en": obs.edge.wr_en,
            "rd_en": obs.edge.rd_en,
            "din": obs.edge.din,
            "row": step.row,
            "pre_queue": step.pre_queue,
            "post_queue": step.post_queue,
            "accepted": {"reset": step.reset, "read": step.accepted_read, "write": step.accepted_write},
            "expected": {"dout": step.expected_dout, "empty": step.expected_empty, "full": step.expected_full},
            "observed": {"dout": obs.dout, "empty": obs.empty, "full": obs.full},
            "dout_checked": step.accepted_read,
            "mismatches": mismatches,
            "wraps": step.wraps,
        })
    return rows


def related_events(rows: list[dict], fail_index: int) -> list[dict]:
    """Deterministic pointers to earlier cycles that explain a data mismatch."""
    row = rows[fail_index]
    if "read_data" not in row["mismatches"]:
        return []
    start = max((i for i in range(fail_index + 1) if rows[i]["rst"]), default=0)
    events = []
    expected, observed = row["expected"]["dout"], row["observed"]["dout"]
    for i in range(start, fail_index):
        r = rows[i]
        if r["wr_en"] and not r["rst"] and r["din"] == expected and r["accepted"]["write"]:
            events.append({"cycle": r["cycle"], "kind": "expected_word_accepted",
                           "text": f"The expected word 0x{expected:02x} was accepted at cycle {r['cycle']}."})
        if r["wr_en"] and not r["rst"] and r["din"] == observed:
            accepted = r["accepted"]["write"]
            events.append({
                "cycle": r["cycle"], "kind": "observed_word_offered", "row": r["row"],
                "text": (f"The observed word 0x{observed:02x} was offered at cycle {r['cycle']} "
                         f"({REQUIREMENTS[r['row']]['title'].lower()}); the contract "
                         f"{'accepted' if accepted else 'ignored'} it."),
            })
        if r["accepted"]["read"] and r["expected"]["dout"] == observed:
            events.append({"cycle": r["cycle"], "kind": "observed_word_already_read",
                           "text": f"The observed word 0x{observed:02x} was already read at cycle {r['cycle']}."})
    return events[-6:]


def first_finding(rows: list[dict], test: str, source: str) -> dict | None:
    for index, row in enumerate(rows):
        if row["mismatches"]:
            check = row["mismatches"][0]
            requirement = row["row"]
            return {
                "test": test,
                "source": source,
                "cycle": row["cycle"],
                "check": check,
                "checks_failed": row["mismatches"],
                "check_text": CHECKS[check],
                "requirement_id": requirement,
                "requirement_title": REQUIREMENTS[requirement]["title"],
                "requirement_text": REQUIREMENTS[requirement]["text"],
                "expected": {k: row["expected"][k] for k in ("dout", "empty", "full")},
                "observed": {k: row["observed"][k] for k in ("dout", "empty", "full")},
                "related_events": related_events(rows, index),
                "note": "This is the first observed mismatch. The governing contract row is the condition "
                        "at that edge; an earlier accepted or ignored operation may be the cause.",
            }
    return None


def coverage(rows: list[dict]) -> dict[str, int]:
    counts = {row: 0 for row in ROWS}
    counts.update({"wrap_write": 0, "wrap_read": 0, "recurrent_reset": 0})
    released = False
    for row in rows:
        counts[row["row"]] += 1
        if row["rst"] and released:
            counts["recurrent_reset"] += 1
        released = released or not row["rst"]
        for kind in row["wraps"]:
            counts[f"wrap_{kind}"] += 1
    return counts


def window(rows: list[dict], cycle: int, before: int = 12, after: int = 2) -> dict:
    """A compact window ending shortly after the failing cycle, starting at the last reset if close."""
    resets = [r["cycle"] for r in rows if r["rst"] and r["cycle"] <= cycle]
    start = resets[-1] if resets and cycle - resets[-1] <= before else max(0, cycle - before)
    return {"start": start, "end": min(len(rows) - 1, cycle + after)}


@dataclass
class SupplementalCheck:
    id: str
    check: str
    rows: list[str] | None  # None means every edge
    requirement: str
    text: str

    def evaluate(self, rows: list[dict]) -> int | None:
        """Return the first cycle at which this check fails, or None."""
        for row in rows:
            if self.rows is not None and row["row"] not in self.rows:
                continue
            if self.check in row["mismatches"]:
                return row["cycle"]
        return None


@dataclass
class CheckSet:
    id: str
    label: str
    origin: str
    checks: list[SupplementalCheck] = field(default_factory=list)
    tests: list[str] | None = None  # frozen suite tests this set observes; None means all

    def covered_requirements(self) -> set[str]:
        return {c.requirement for c in self.checks}


def check_set_from_dict(data: dict) -> CheckSet:
    """Build a supplemental set from reviewed templates only; unknown fields are rejected."""
    checks = []
    for item in data.get("checks", []):
        if item.get("check") not in CHECKS:
            raise ValueError(f"unknown check template {item.get('check')!r}")
        rows = item.get("rows")
        if rows is not None and (not isinstance(rows, list) or any(r not in ROWS for r in rows)):
            raise ValueError(f"unknown contract rows in {item.get('id')!r}")
        requirement = item.get("requirement")
        if requirement not in REQUIREMENTS:
            raise ValueError(f"unknown requirement {requirement!r}")
        checks.append(SupplementalCheck(str(item["id"]), item["check"], rows, requirement, str(item.get("text", ""))))
    if not checks:
        raise ValueError("a supplemental check set needs at least one check")
    tests = data.get("tests")
    if tests is not None and (not isinstance(tests, list) or not tests or not all(isinstance(t, str) for t in tests)):
        raise ValueError("tests must be null or a non-empty list of suite test names")
    return CheckSet(str(data["id"]), str(data["label"]), str(data.get("origin", "unspecified")), checks, tests)
