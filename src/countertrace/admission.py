"""Pre-execution admission for DUT source, model-generated patches included.

Admission is a conservative lexical and structural gate. It rejects anything
outside the supported subset before any tool runs. The authoritative interface
check happens again inside the worker, where Yosys elaborates the module and
the trusted host parses its port list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

MAX_BYTES = 64 * 1024
MAX_NONBLANK_LINES = 500
ALLOWED_SYSTEM_FUNCTIONS = {"$clog2", "$signed", "$unsigned", "$bits"}
ALLOWED_DIRECTIVES = {"default_nettype", "timescale"}

# Keywords that could add verification semantics, bypass the harness, reach the
# host, or make simulation and formal tools see different behavior.
PROHIBITED_KEYWORDS = {
    "assert": "DUT-authored assertions are not accepted; the trusted monitor owns all checks.",
    "assume": "DUT-authored assumptions could constrain the check; they are not accepted.",
    "restrict": "DUT-authored restrictions could constrain the check; they are not accepted.",
    "cover": "DUT-authored cover statements are not accepted.",
    "property": "SVA properties are outside the supported subset.",
    "sequence": "SVA sequences are outside the supported subset.",
    "bind": "bind could attach code to the trusted harness.",
    "import": "Package and DPI imports are not supported.",
    "export": "DPI exports are not supported.",
    "initial": "initial blocks make simulation and formal start states differ; use reset instead.",
    "final": "final blocks are not supported.",
    "fork": "fork/join is not synthesizable and is not supported.",
    "class": "Classes are outside the supported subset.",
    "program": "program blocks are outside the supported subset.",
    "interface": "SystemVerilog interfaces are outside the supported subset.",
    "package": "Packages are outside the supported subset.",
    "negedge": "Only a single positive-edge clock is supported.",
    "force": "force/release is not supported.",
    "release": "force/release is not supported.",
    "deassign": "Procedural continuous assignment is not supported.",
    "specify": "specify blocks are not supported.",
    "primitive": "User-defined primitives are not supported.",
    "config": "Configurations are not supported.",
    "library": "Library declarations are not supported.",
}
PROHIBITED_ATTRIBUTES = re.compile(r"\(\*.*?\*\)", re.S)


@dataclass
class Diagnostic:
    code: str
    message: str
    line: int | None = None
    alternative: str | None = None


@dataclass
class Admission:
    accepted: bool
    module: str | None = None
    parameters: list[str] = field(default_factory=list)
    ports: dict[str, dict] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "module": self.module,
            "parameters": self.parameters,
            "ports": self.ports,
            "diagnostics": [d.__dict__ for d in self.diagnostics],
        }


def strip_comments(text: str) -> str:
    """Remove comments while preserving line numbers; string literals are rejected separately."""
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def admit(source: bytes | str) -> Admission:
    result = Admission(accepted=False)
    diag = result.diagnostics.append
    raw = source.encode() if isinstance(source, str) else source
    if len(raw) > MAX_BYTES:
        diag(Diagnostic("size", f"Source is {len(raw)} bytes; the limit is {MAX_BYTES}."))
        return result
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        diag(Diagnostic("encoding", "Source must be UTF-8."))
        return result
    if "\x00" in text:
        diag(Diagnostic("encoding", "Source contains NUL bytes."))
        return result
    nonblank = sum(1 for line in text.splitlines() if line.strip())
    if nonblank > MAX_NONBLANK_LINES:
        diag(Diagnostic("size", f"Source has {nonblank} nonblank lines; the limit is {MAX_NONBLANK_LINES}."))
        return result

    code = strip_comments(text)
    if re.search(r'"', code):
        diag(Diagnostic("string", "String literals are not used by supported FIFO RTL.", line_of(code, code.index('"'))))
    if "/*" in code or "*/" in code:
        diag(Diagnostic("comment", "Unbalanced block comment."))
    for match in PROHIBITED_ATTRIBUTES.finditer(code):
        diag(Diagnostic("attribute", "Attributes such as (* anyconst *) or (* keep *) are not accepted.",
                        line_of(code, match.start())))
    for match in re.finditer(r"`\s*([A-Za-z_]\w*)", code):
        if match.group(1) not in ALLOWED_DIRECTIVES:
            diag(Diagnostic("directive", f"Compiler directive `{match.group(1)} is not accepted.",
                            line_of(code, match.start()),
                            "Use parameters instead of macros; includes and defines are not supported."))
    for match in re.finditer(r"\$[A-Za-z_]\w*", code):
        if match.group() not in ALLOWED_SYSTEM_FUNCTIONS:
            diag(Diagnostic("system_task", f"System task or function {match.group()} is not accepted.",
                            line_of(code, match.start()),
                            "Only $clog2, $signed, $unsigned, and $bits are supported."))
    for match in re.finditer(r"\b([A-Za-z_]\w*)\b", code):
        word = match.group(1)
        if word in PROHIBITED_KEYWORDS:
            diag(Diagnostic("construct", f"'{word}': {PROHIBITED_KEYWORDS[word]}", line_of(code, match.start())))
    if re.search(r"\bDPI\b", code):
        diag(Diagnostic("construct", "DPI is not supported."))

    modules = list(re.finditer(r"\bmodule\s+([A-Za-z_]\w*)", code))
    if len(modules) != 1:
        diag(Diagnostic("structure", f"Expected exactly one module; found {len(modules)}.",
                        alternative="Submit one top module with no submodules."))
    if len(re.findall(r"\bendmodule\b", code)) != len(modules):
        diag(Diagnostic("structure", "module/endmodule count mismatch."))
    if modules:
        result.module = modules[0].group(1)
        header_end = code.find(");", modules[0].end())
        header = code[modules[0].end(): header_end if header_end >= 0 else len(code)]
        result.parameters = re.findall(r"\bparameter\b(?:\s+(?:integer|int|logic|\[[^\]]*\]))?\s+([A-Za-z_]\w*)", header)
        for name in ("DEPTH", "WIDTH"):
            if name not in result.parameters:
                diag(Diagnostic("interface", f"Parameter {name} must be declared in the module header.",
                                alternative="Declare `parameter integer DEPTH = 4, parameter integer WIDTH = 8`."))
        for direction, rng, name in re.findall(
            r"\b(input|output)\b\s*(?:wire|reg|logic)?\s*(\[[^\]]*\])?\s*([A-Za-z_]\w*)", header
        ):
            result.ports[name] = {"direction": direction, "range": rng or None}
        expected = {
            "clk": ("input", None), "rst": ("input", None), "wr_en": ("input", None),
            "rd_en": ("input", None), "din": ("input", "WIDTH"), "dout": ("output", "WIDTH"),
            "full": ("output", None), "empty": ("output", None),
        }
        for name, (direction, width) in expected.items():
            port = result.ports.get(name)
            if port is None:
                diag(Diagnostic("interface", f"Missing canonical port {name}.",
                                alternative="Ports must be clk, rst, wr_en, rd_en, din, dout, full, empty (ANSI style)."))
                continue
            if port["direction"] != direction:
                diag(Diagnostic("interface", f"Port {name} must be an {direction}."))
            if width is None and port["range"]:
                diag(Diagnostic("interface", f"Port {name} must be one bit."))
            if width == "WIDTH" and (port["range"] or "").replace(" ", "") != "[WIDTH-1:0]":
                diag(Diagnostic("interface", f"Port {name} must be declared [WIDTH-1:0]."))
        extra = sorted(set(result.ports) - set(expected))
        if extra:
            diag(Diagnostic("interface", f"Unexpected ports: {', '.join(extra)}.",
                            alternative="Port-name mapping is not yet supported."))
        clocks = set(re.findall(r"@\s*\(\s*posedge\s+([A-Za-z_]\w*)", code))
        if clocks - {"clk"}:
            diag(Diagnostic("clocking", f"Only posedge clk is supported; found {sorted(clocks)}.",
                            alternative="Use synchronous active-high reset sampled on posedge clk."))
        if re.search(r"@\s*\(\s*posedge\s+clk\s*(or|,)", code):
            diag(Diagnostic("clocking", "Asynchronous reset or multiple events are not supported."))
        if re.search(r"\b(always_latch)\b", code):
            diag(Diagnostic("clocking", "Latches are not supported."))
    result.accepted = not result.diagnostics
    return result


def check_ports_json(ports_json: dict, module: str, width: int) -> list[Diagnostic]:
    """Validate the Yosys-elaborated interface written by the worker."""
    problems = []
    modules = ports_json.get("modules", {})
    mod = next((m for name, m in modules.items() if name == module or name.startswith(f"$paramod\\{module}\\")), None)
    if mod is None:
        return [Diagnostic("elaboration", f"Module {module} was not found after elaboration.")]
    ports = mod.get("ports", {})
    expected = {
        "clk": ("input", 1), "rst": ("input", 1), "wr_en": ("input", 1), "rd_en": ("input", 1),
        "din": ("input", width), "dout": ("output", width), "full": ("output", 1), "empty": ("output", 1),
    }
    if set(ports) != set(expected):
        problems.append(Diagnostic("elaboration", f"Elaborated ports {sorted(ports)} differ from the contract."))
    for name, (direction, bits) in expected.items():
        port = ports.get(name)
        if port and (port.get("direction") != direction or len(port.get("bits", [])) != bits):
            problems.append(Diagnostic("elaboration", f"Elaborated port {name} is not a {bits}-bit {direction}."))
    return problems
