"""The fixed synchronous FIFO contract profile and its independent reference model.

This module is trusted, hand-authored code. It never imports DUT source or model
output. The sampling convention follows the PRD: cycle k names a rising edge;
accepted operations are decided from the reference queue immediately before the
edge; reset has priority; flags are checked against post-edge occupancy; `dout`
is compared only after an accepted read.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json

PROFILE_ID = "sync-fifo-v1"
CONTRACT_VERSION = "1.0.0"
SUPPORTED_DEPTHS = (2, 4)
SUPPORTED_WIDTHS = (8,)
CANONICAL_PORTS = {
    "clk": ("input", 1),
    "rst": ("input", 1),
    "wr_en": ("input", 1),
    "rd_en": ("input", 1),
    "din": ("input", "WIDTH"),
    "dout": ("output", "WIDTH"),
    "full": ("output", 1),
    "empty": ("output", 1),
}

# Contract rows: the condition at an edge, decided from pre-edge reference occupancy.
REQUIREMENTS: dict[str, dict[str, str]] = {
    "reset": {
        "title": "Reset asserted at a rising edge",
        "text": "Reset wins over read and write. Occupancy becomes zero; empty is true and full is false after the edge.",
    },
    "write_not_full": {
        "title": "Write requested while not full",
        "text": "Accept one input word.",
    },
    "read_not_empty": {
        "title": "Read requested while not empty",
        "text": "Remove the oldest word. dout holds that word after the edge.",
    },
    "read_empty": {
        "title": "Read requested while empty",
        "text": "Ignore the read. Nothing is consumed and nothing is bypassed.",
    },
    "write_full": {
        "title": "Write requested while full",
        "text": "Ignore the write.",
    },
    "both_mid": {
        "title": "Read and write between empty and full",
        "text": "Accept both. Occupancy stays constant; the old head is read and the new word joins the tail.",
    },
    "both_empty": {
        "title": "Read and write while empty",
        "text": "Accept only the write. The new word is not bypassed to dout.",
    },
    "both_full": {
        "title": "Read and write while full",
        "text": "Accept only the read. The write is ignored even though the read frees a slot.",
    },
    "idle": {
        "title": "No request",
        "text": "Occupancy and stored words are unchanged.",
    },
    "wraparound": {
        "title": "Wraparound",
        "text": "Preserve accepted-word ordering and capacity across pointer wraparound.",
    },
}

# Core checks. Each check compares an observable output with the reference.
CHECKS: dict[str, str] = {
    "empty_flag": "empty equals (reference occupancy == 0) after every edge",
    "full_flag": "full equals (reference occupancy == DEPTH) after every edge",
    "read_data": "dout equals the reference head removed by an accepted read",
}

ASSUMPTIONS = [
    "Reset is asserted at the first sampled edge; no pre-reset state is claimed.",
    "Later reset pulses are legal and are exercised.",
    "Inputs are driven while the clock is low and held stable through the rising edge.",
    "Two-state digital semantics; X-propagation, timing closure, and synthesized behavior are not checked.",
    "No requirement is imposed on dout unless the preceding edge accepted a read.",
    "Results apply only to the exact instantiated DEPTH and WIDTH.",
]


@dataclass(frozen=True)
class Contract:
    depth: int
    width: int = 8
    profile: str = PROFILE_ID
    version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.depth not in SUPPORTED_DEPTHS:
            raise ValueError(f"unsupported depth {self.depth}; supported: {SUPPORTED_DEPTHS}")
        if self.width not in SUPPORTED_WIDTHS:
            raise ValueError(f"unsupported width {self.width}; supported: {SUPPORTED_WIDTHS}")

    def document(self) -> dict:
        """The exact, versioned contract a user accepts."""
        return {
            "profile": self.profile,
            "version": self.version,
            "parameters": {"DEPTH": self.depth, "WIDTH": self.width},
            "ports": {name: {"direction": d, "width": w} for name, (d, w) in CANONICAL_PORTS.items()},
            "requirements": REQUIREMENTS,
            "checks": CHECKS,
            "assumptions": ASSUMPTIONS,
            "sampling": "Cycle k names a rising edge. Accepted operations come from the reference "
            "queue before the edge; reset has priority; flags are checked after the edge; dout "
            "is checked only after an accepted read.",
        }

    def digest(self) -> str:
        return sha256_json(self.document())


def sha256_json(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Edge:
    """Inputs held stable through one rising edge."""

    rst: int
    wr_en: int
    rd_en: int
    din: int


@dataclass
class Step:
    """The reference outcome of one edge."""

    cycle: int
    edge: Edge
    pre_queue: list[int] | None  # None before the first reset (unspecified)
    row: str
    accepted_read: bool
    accepted_write: bool
    reset: bool
    post_queue: list[int]
    expected_dout: int | None
    expected_empty: bool
    expected_full: bool
    wraps: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        data = asdict(self)
        data["edge"] = asdict(self.edge)
        return data


def classify(edge: Edge, occupancy: int | None, depth: int) -> str:
    """Return the contract row that governs an edge."""
    if edge.rst or occupancy is None:
        return "reset"
    empty, full = occupancy == 0, occupancy == depth
    if edge.wr_en and edge.rd_en:
        return "both_empty" if empty else "both_full" if full else "both_mid"
    if edge.wr_en:
        return "write_full" if full else "write_not_full"
    if edge.rd_en:
        return "read_empty" if empty else "read_not_empty"
    return "idle"


class ReferenceFifo:
    """Independent reference queue. State before the first reset is unspecified."""

    def __init__(self, contract: Contract):
        self.contract = contract
        self.queue: list[int] | None = None
        self.cycle = 0
        self.writes_since_reset = 0
        self.reads_since_reset = 0

    def step(self, edge: Edge) -> Step:
        depth = self.contract.depth
        mask = (1 << self.contract.width) - 1
        pre = None if self.queue is None else list(self.queue)
        if pre is None and not edge.rst:
            raise ValueError("reset must be asserted at the first sampled edge")
        row = classify(edge, None if pre is None else len(pre), depth)
        accepted_read = accepted_write = False
        wraps: list[str] = []
        expected_dout = None
        if edge.rst:
            self.queue = []
            self.writes_since_reset = self.reads_since_reset = 0
        else:
            assert self.queue is not None
            accepted_read = bool(edge.rd_en) and len(self.queue) > 0
            accepted_write = bool(edge.wr_en) and len(self.queue) < depth
            if accepted_read:
                expected_dout = self.queue.pop(0)
                if self.reads_since_reset >= depth:
                    wraps.append("read")
                self.reads_since_reset += 1
            if accepted_write:
                self.queue.append(edge.din & mask)
                if self.writes_since_reset >= depth:
                    wraps.append("write")
                self.writes_since_reset += 1
        step = Step(
            cycle=self.cycle,
            edge=edge,
            pre_queue=pre,
            row=row,
            accepted_read=accepted_read,
            accepted_write=accepted_write,
            reset=bool(edge.rst),
            post_queue=list(self.queue),
            expected_dout=expected_dout,
            expected_empty=len(self.queue) == 0,
            expected_full=len(self.queue) == depth,
            wraps=wraps,
        )
        self.cycle += 1
        return step


def reference_steps(contract: Contract, edges: list[Edge]) -> list[Step]:
    model = ReferenceFifo(contract)
    return [model.step(edge) for edge in edges]
