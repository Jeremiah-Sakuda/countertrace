"""Catalog of modules for model-written checks.

Each module has a reviewed plain-English specification, ports, parameter
settings, and a hand-written golden reference. The golden is trusted fixture
code and is never sent to the model.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from countertrace.catalog import FIXTURES

MODULES = FIXTURES / "modules"
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
SIGNAL = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


class CatalogError(ValueError):
    pass


def width_value(width: int | str, params: dict[str, int]) -> int:
    """A port width is an integer or a parameter name."""
    if isinstance(width, int):
        value = width
    elif isinstance(width, str) and width in params:
        value = params[width]
    else:
        raise CatalogError(f"width {width!r} must be an integer or a parameter name")
    if not 1 <= value <= 64:
        raise CatalogError(f"width {value} is outside 1 to 64")
    return value


def width_decl(width: int | str) -> str:
    """Verilog range for a declaration, written in terms of the parameter when it has one."""
    if isinstance(width, int):
        return "" if width == 1 else f"[{width - 1}:0] "
    return f"[{width}-1:0] "


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    top: str
    clock: str
    reset: str
    params: list[dict[str, int]]
    inputs: dict[str, int | str]
    outputs: dict[str, int | str]
    observe: dict[str, str]
    spec: str
    golden_path: Path
    split: str = "development"
    limits: tuple = ()

    @property
    def golden(self) -> str:
        return self.golden_path.read_text()

    @property
    def primary(self) -> dict[str, int]:
        return self.params[0]

    def ports(self) -> list[str]:
        return [self.clock, *self.inputs, *self.outputs]

    def widths(self, params: dict[str, int] | None = None) -> dict[str, int]:
        params = params or self.primary
        return {name: width_value(w, params) for name, w in {**self.inputs, **self.outputs}.items()}

    @property
    def reference_properties(self) -> dict:
        """Hand-written properties derived from the specification; they validate the golden and are never sent to the model."""
        return json.loads((MODULES / self.id / "reference_properties.json").read_text())

    def public(self) -> dict:
        """What the model and the interface may see: never the golden source."""
        return {"id": self.id, "title": self.title, "top": self.top, "clock": self.clock, "reset": self.reset,
                "params": self.params, "inputs": self.inputs, "outputs": self.outputs, "spec": self.spec, "split": self.split}


def load(module_id: str) -> Module:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,40}", module_id or ""):
        raise CatalogError("invalid module id")
    path = MODULES / module_id / "module.json"
    if not path.is_file():
        raise CatalogError(f"unknown module {module_id}")
    data = json.loads(path.read_text())
    golden = (FIXTURES / data["golden"]).resolve()
    if FIXTURES.resolve() not in golden.parents or not golden.is_file():
        raise CatalogError("golden reference must be a file inside fixtures/")
    module = Module(id=data["id"], title=data["title"], top=data["top"], clock=data["clock"], reset=data["reset"],
                    params=[dict(p) for p in data["params"]], inputs=dict(data["inputs"]), outputs=dict(data["outputs"]),
                    observe=dict(data.get("observe", {})), spec="\n".join(data["spec"]), golden_path=golden,
                    split=data.get("split", "development"), limits=tuple(sorted((data.get("limits") or {}).items())))
    validate(module)
    return module


def validate(module: Module) -> None:
    for name in (module.top, module.clock, module.reset, *module.inputs, *module.outputs):
        if not IDENT.match(name):
            raise CatalogError(f"invalid identifier {name!r}")
    if module.reset not in module.inputs or module.inputs[module.reset] != 1:
        raise CatalogError("reset must be a one-bit input")
    names = [module.clock, *module.inputs, *module.outputs]
    if len(set(names)) != len(names):
        raise CatalogError("port names must be unique")
    if not 1 <= len(module.params) <= 4:
        raise CatalogError("one to four parameter settings are required")
    keys = set(module.params[0])
    for setting in module.params:
        if set(setting) != keys or not all(IDENT.match(k) and isinstance(v, int) and 1 <= v <= 64 for k, v in setting.items()):
            raise CatalogError("every parameter setting must give the same integer parameters")
        module.widths(setting)
    if module.split not in ("development", "heldout"):
        raise CatalogError("split must be development or heldout")
    for key, value in module.limits:
        if key not in ("bmc_depth", "cover_depth", "solver_s") or not isinstance(value, int) or not 1 <= value <= (600 if key == "solver_s" else 64):
            raise CatalogError(f"invalid limit {key}")
    for name in module.observe:
        if name not in module.outputs:
            raise CatalogError(f"observation qualifier for unknown output {name!r}")


def catalog() -> list[Module]:
    return [load(p.parent.name) for p in sorted(MODULES.glob("*/module.json"))]
