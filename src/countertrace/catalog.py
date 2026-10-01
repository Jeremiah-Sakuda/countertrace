"""Bundled examples and the versioned fault library."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"


@lru_cache(maxsize=1)
def faults() -> dict:
    return json.loads((FIXTURES / "faults.json").read_text())


@lru_cache(maxsize=1)
def examples() -> dict:
    return json.loads((FIXTURES / "examples.json").read_text())


def fault(fault_id: str) -> dict:
    for item in faults()["faults"]:
        if item["id"] == fault_id:
            return item
    raise KeyError(fault_id)


def apply_fault(source: str, item: dict) -> str:
    for edit in item["edits"]:
        count = source.count(edit["find"])
        if count != 1:
            raise ValueError(f"fault {item['id']}: edit target matched {count} times")
        source = source.replace(edit["find"], edit["replace"])
    return source


def base_source(name: str) -> str:
    path = (FIXTURES / "rtl" / name).resolve()
    if path.parent != (FIXTURES / "rtl").resolve():
        raise ValueError("invalid fixture path")
    return path.read_text()


def fault_source(fault_id: str) -> str:
    item = fault(fault_id)
    return apply_fault(base_source(item["base"]), item)


def example(example_id: str) -> dict:
    for item in examples()["examples"]:
        if item["id"] == example_id:
            return item
    raise KeyError(example_id)


def example_source(item: dict) -> str:
    src = item["source"]
    return fault_source(src["fault"]) if src.get("fault") else base_source(src["base"])
