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
# Severity tasks are accepted for elaboration-time parameter guards. They cannot
# touch files or processes; a runtime $fatal only truncates the trace (a tool
# error), and any property cell outside the trusted monitor fails integrity.
SEVERITY_TASKS = {"$error", "$warning", "$info", "$fatal"}
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
    "iff": "Qualified event controls are not supported; use posedge clk with an if statement.",
    "wait": "wait statements are not synthesizable and are not supported.",
    "edge": "Dual-edge event controls are not supported; use posedge clk.",
    "defparam": "defparam is not supported; use the module's parameters.",
    "inout": "Bidirectional ports are not supported.",
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


class LexError(ValueError):
    pass


def strip_comments(text: str) -> str:
    """Blank comments and string contents in one left-to-right pass, as a compiler reads them.

    Comments, strings, and their delimiters are recognized in source order, so
    `// /*` cannot open a block comment and a `"//"` string cannot hide code.
    Newlines are preserved for line numbers; string delimiters are kept and
    their contents replaced by spaces. Raises LexError on an unterminated
    block comment or string.
    """
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "//":
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif two == "/*":
            j = text.find("*/", i + 2)
            if j < 0:
                raise LexError("Unterminated block comment.")
            chunk = text[i:j + 2]
            out.append("".join("\n" if ch == "\n" else " " for ch in chunk))
            i = j + 2
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == "\n":
                    raise LexError("Unterminated string literal.")
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise LexError("Unterminated string literal.")
            out.append('"' + " " * (j - i - 1) + '"')
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def parse_ports(header: str) -> tuple[dict[str, dict], list[str]]:
    """Parse an ANSI port list, including continuation names (`input wire a, b`)."""
    text = header.strip()
    if text.startswith("#"):
        depth, i = 0, text.index("(")
        for i in range(i, len(text)):
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            if depth == 0:
                break
        text = text[i + 1:]
    start = text.find("(")
    if start < 0:
        return {}, ["The module header has no port list."]
    body = text[start + 1:]
    items, depth, current = [], 0, []
    for ch in body:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            items.append("".join(current))
            current = []
        else:
            current.append(ch)
    items.append("".join(current))
    ports: dict[str, dict] = {}
    problems: list[str] = []
    direction = rng = None
    for item in (i.strip() for i in items):
        if not item:
            continue
        m = re.fullmatch(r"(input|output)\b\s*(?:wire|reg|logic|var)?\s*(?:signed\s*)?(\[[^\]]*\])?\s*([A-Za-z_]\w*)", item)
        if m:
            direction, rng, name = m.group(1), m.group(2), m.group(3)
        elif direction and re.fullmatch(r"[A-Za-z_]\w*", item):
            name = item  # continuation inherits the previous direction and range
        else:
            problems.append(f"Unrecognized port declaration: {item[:60]!r}.")
            continue
        if name in ports:
            problems.append(f"Port {name} is declared twice.")
        ports[name] = {"direction": direction, "range": rng or None}
    return ports, problems


def _statements(body: str):
    """Yield (offset, text) for each ';'-terminated chunk of a module body."""
    start = 0
    for i, ch in enumerate(body):
        if ch == ";":
            yield start, body[start:i]
            start = i + 1


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def admit(source: bytes | str, mapping: dict | None = None) -> Admission:
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

    # One ordered lexical pass: comments are blanked and string contents (only
    # meaningful as severity-task messages) are never scanned as code.
    try:
        code = strip_comments(text)
    except LexError as exc:
        diag(Diagnostic("lexical", str(exc)))
        return result
    if "*/" in code:
        diag(Diagnostic("comment", "Stray end of block comment."))
    for match in PROHIBITED_ATTRIBUTES.finditer(code):
        diag(Diagnostic("attribute", "Attributes such as (* anyconst *) or (* keep *) are not accepted.",
                        line_of(code, match.start())))
    for match in re.finditer(r"`\s*([A-Za-z_]\w*)", code):
        if match.group(1) not in ALLOWED_DIRECTIVES:
            diag(Diagnostic("directive", f"Compiler directive `{match.group(1)} is not accepted.",
                            line_of(code, match.start()),
                            "Use parameters instead of macros; includes and defines are not supported."))
    for match in re.finditer(r"\$[A-Za-z_]\w*", code):
        if match.group() not in ALLOWED_SYSTEM_FUNCTIONS | SEVERITY_TASKS:
            diag(Diagnostic("system_task", f"System task or function {match.group()} is not accepted.",
                            line_of(code, match.start()),
                            "Only $clog2, $signed, $unsigned, $bits, and severity tasks are supported."))
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
        if mapping is not None:
            from countertrace.interface_map import MappingError, expected_ports, validate

            try:
                mapping = validate(mapping)
            except MappingError as exc:
                diag(Diagnostic("mapping", f"Invalid interface mapping: {exc}"))
                mapping = None
        names = mapping["parameters"] if mapping else {"DEPTH": "DEPTH", "WIDTH": "WIDTH"}
        if mapping and result.module != mapping["module"]:
            diag(Diagnostic("mapping", f"The mapping names module {mapping['module']}, but the source declares {result.module}."))
        for canonical, name in names.items():
            if name not in result.parameters:
                diag(Diagnostic("interface", f"Parameter {name} ({canonical}) must be declared in the module header.",
                                alternative="Declare `parameter integer DEPTH = 4, parameter integer WIDTH = 8`."))
        result.ports, port_problems = parse_ports(header)
        for problem in port_problems:
            diag(Diagnostic("interface", problem))
        if mapping:
            expected = expected_ports(mapping)
        else:
            expected = {
                "clk": ("input", None), "rst": ("input", None), "wr_en": ("input", None),
                "rd_en": ("input", None), "din": ("input", "[WIDTH-1:0]"), "dout": ("output", "[WIDTH-1:0]"),
                "full": ("output", None), "empty": ("output", None),
            }
        for name, (direction, rng) in expected.items():
            port = result.ports.get(name)
            if port is None:
                diag(Diagnostic("interface", f"Missing port {name}.",
                                alternative="Ports must be clk, rst, wr_en, rd_en, din, dout, full, empty (ANSI style), "
                                            "or declared in a validated interface mapping."))
                continue
            if port["direction"] != direction:
                diag(Diagnostic("interface", f"Port {name} must be an {direction}."))
            if rng is None and port["range"]:
                diag(Diagnostic("interface", f"Port {name} must be one bit."))
            if rng not in (None, "*") and (port["range"] or "").replace(" ", "") != rng:
                diag(Diagnostic("interface", f"Port {name} must be declared {rng}."))
        extra = sorted(set(result.ports) - set(expected))
        if extra:
            diag(Diagnostic("interface", f"Unexpected ports: {', '.join(extra)}.",
                            alternative="Declare them as unused outputs in an interface mapping, if they are outputs."))
        clock = mapping["ports"]["clk"] if mapping else "clk"
        body = code[(header_end + 2) if header_end >= 0 else len(code):]
        for chunk_start, chunk in _statements(body):
            if re.search(r"(?:^|\bbegin\b|\bend\b)\s*(?:reg|logic|integer|bit|int|byte|shortint|longint)\b[^=;]*=(?!=)", chunk):
                diag(Diagnostic("construct", "Variable declaration initializers act like initial blocks; set values in reset instead.",
                                line_of(code, header_end + 2 + chunk_start)))
        for name, port in result.ports.items():
            redeclared = re.search(rf"\b(?:wire|reg|logic|integer|genvar|tri|supply0|supply1)\b[^;]*?\b{name}\b\s*(?:\[[^\]]*\]\s*)?(?:=|;|,)", body)
            if redeclared and re.search(rf"\b{name}\b", redeclared.group().split("=")[0]):
                diag(Diagnostic("interface", f"Port {name} is redeclared inside the module body.", line_of(code, header_end + 2 + redeclared.start())))
            if port["direction"] == "input":
                driven = re.search(rf"(?:\bassign\s+{name}\b|(?<![.\w]){name}\s*(?:\[[^\]]*\]\s*)?(?:<=|=)(?!=))", body)
                if driven:
                    diag(Diagnostic("interface", f"Input port {name} is assigned inside the module.", line_of(code, header_end + 2 + driven.start())))
        for match in re.finditer(r"@", code):
            rest = code[match.end():]
            if not re.match(rf"\s*(?:\*|\(\s*\*\s*\)|\(\s*posedge\s+{clock}\s*\))", rest):
                diag(Diagnostic("clocking", "Only @(posedge clk) and @* event controls are supported.", line_of(code, match.start())))
        for match in re.finditer(r"#(?!\s*\()", code):
            diag(Diagnostic("construct", "Delays (#) are not supported; timing comes from the clock.", line_of(code, match.start())))
        for match in re.finditer(r"(?<![\w'.])[A-Za-z_]\w*\s*\.\s*[A-Za-z_]\w*", code):
            diag(Diagnostic("construct", "Hierarchical references are not supported.", line_of(code, match.start())))
        clocks = set(re.findall(r"@\s*\(\s*posedge\s+([A-Za-z_]\w*)", code))
        if clocks - {clock}:
            diag(Diagnostic("clocking", f"Only posedge clk is supported; found {sorted(clocks)}.",
                            alternative="Use synchronous active-high reset sampled on posedge clk."))
        if re.search(rf"@\s*\(\s*posedge\s+{clock}\s*(or|,)", code):
            diag(Diagnostic("clocking", "Asynchronous reset or multiple events are not supported."))
        if re.search(r"\b(always_latch)\b", code):
            diag(Diagnostic("clocking", "Latches are not supported."))
    result.accepted = not result.diagnostics
    return result


def check_ports_json(ports_json: dict, module: str, width: int) -> list[Diagnostic]:
    """Validate the Yosys-elaborated interface written by the worker."""
    problems = []
    modules = ports_json.get("modules", {})
    from countertrace.interface_map import elaborated_name_matches

    mod = next((m for name, m in modules.items() if elaborated_name_matches(name, module)), None)
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
