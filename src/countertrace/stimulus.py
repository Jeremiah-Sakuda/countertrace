"""Deterministic, named stimulus for the simulation harness.

Directed tests cover every contract row, recurrent reset, and wraparound. Seeded
random tests add breadth. The stimulus is part of the frozen check set: a repair
comparison reuses exactly these files, and their hashes enter the manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
import random

from countertrace.contract import Edge

STIMULUS_VERSION = "stimulus-v1"
RANDOM_SEEDS = (1, 2, 3, 4, 5, 6, 7, 8)
RANDOM_LENGTH = 160
TIMING = Path(__file__).resolve().parents[2] / "fixtures" / "timing"


class Builder:
    def __init__(self, first_value: int = 0xA1):
        self.edges: list[Edge] = []
        self.value = first_value

    def next_value(self) -> int:
        value = self.value
        self.value = (self.value + 0x11) & 0xFF or 0x11
        return value

    def reset(self, wr: int = 0, rd: int = 0) -> "Builder":
        self.edges.append(Edge(1, wr, rd, self.next_value()))
        return self

    def write(self, n: int = 1) -> "Builder":
        for _ in range(n):
            self.edges.append(Edge(0, 1, 0, self.next_value()))
        return self

    def read(self, n: int = 1) -> "Builder":
        for _ in range(n):
            self.edges.append(Edge(0, 0, 1, self.next_value()))
        return self

    def both(self, n: int = 1) -> "Builder":
        for _ in range(n):
            self.edges.append(Edge(0, 1, 1, self.next_value()))
        return self

    def idle(self, n: int = 1) -> "Builder":
        for _ in range(n):
            self.edges.append(Edge(0, 0, 0, self.next_value()))
        return self


def directed(depth: int) -> dict[str, list[Edge]]:
    tests: dict[str, list[Edge]] = {}
    if depth == 2:
        fixture = json.loads((TIMING / "depth2_prd_sequence.json").read_text())
        symbols = fixture["symbols"]
        tests["prd_sequence"] = [Edge(e["rst"], e["wr_en"], e["rd_en"], symbols[e["din"]]) for e in fixture["edges"]]
    # A typical first testbench: fill exactly, drain exactly, wrap once. No boundary
    # requests, no simultaneous operations, no recurrent reset. Used by weak check sets.
    tests["learner_basic"] = (
        Builder(0xB5).reset().write(depth).read(depth).write(2).read(2).write(depth - 1).read(depth - 1).idle().edges
    )
    tests["fill_drain"] = Builder(0x10).reset().write(depth + 1).read(depth + 1).idle().edges
    tests["write_when_full"] = Builder(0x31).reset().write(depth).write(2).read(depth + 1).edges
    tests["simultaneous"] = (
        Builder(0x52).reset().both().both()          # both while empty, then both at occupancy 1
        .write(depth - 1).both().both()              # both while full (read only), then mid
        .read(depth).both().read().idle().edges
    )
    tests["wraparound"] = (
        Builder(0x73).reset().write(depth - 1).read(depth - 2)
        .write(depth).read(depth).write(depth).both(depth).read(depth + 1).edges
    )
    tests["recurrent_reset"] = (
        Builder(0x94).reset().write(depth - 1).reset().write(1).read(2)
        .write(depth).reset(wr=1, rd=1).read().write(2).read(2).reset().read().edges
    )
    return tests


def seeded(seed: int, depth: int, length: int = RANDOM_LENGTH) -> list[Edge]:
    rng = random.Random(f"countertrace-{STIMULUS_VERSION}-{depth}-{seed}")
    edges = [Edge(1, rng.randint(0, 1), rng.randint(0, 1), rng.randrange(256))]
    # Bias alternates between filling and draining phases so full and empty both occur.
    for i in range(1, length):
        filling = (i // (depth * 3)) % 2 == 0
        wr = rng.random() < (0.75 if filling else 0.35)
        rd = rng.random() < (0.35 if filling else 0.75)
        rst = rng.random() < 0.02
        edges.append(Edge(int(rst), int(wr), int(rd), rng.randrange(256)))
    return edges


def suite(depth: int) -> dict[str, list[Edge]]:
    tests = directed(depth)
    for seed in RANDOM_SEEDS:
        tests[f"random_s{seed}"] = seeded(seed, depth)
    return tests


def render(edges: list[Edge]) -> str:
    return "".join(f"{e.rst} {e.wr_en} {e.rd_en} {e.din:02x}\n" for e in edges)


def parse(text: str) -> list[Edge]:
    edges = []
    for line in text.splitlines():
        if line.strip():
            rst, wr, rd, din = line.split()
            edges.append(Edge(int(rst), int(wr), int(rd), int(din, 16)))
    return edges
