"""Trusted compiler for model-written properties.

The model returns structured data, never Verilog: state registers, named
helpers, auxiliary memories with writes, and properties of the form "at each
rising edge after the first, if WHEN then THEN". This module validates every
name and expression against a whitelist, lowers $past into named delay
registers, and renders a checker whose only assumption (reset at the first
edge) is owned by this template. Compiled assertions are p_<id>; reachability
covers of each trigger are r_<id>.
"""

from __future__ import annotations

import re

from countertrace.checks.modules import Module, width_decl

MAX_PROPERTIES = 24
MAX_HELPERS = 24
MAX_EXPR = 1200
MAX_PAST_DEPTH = 8
TOKEN = re.compile(r"\s*(\$past|\$stable|\$rose|\$fell|\d+'[bdhBDH][0-9a-fA-F_]+|\d+|[A-Za-z_]\w*"
                   r"|===|!==|==|!=|<=|>=|&&|\|\||<<|>>|[-+*/%&|^~!<>?:()\[\]{},])")
# Words that would let property text escape an expression or add verification semantics.
RESERVED = {
    "assume", "assert", "cover", "restrict", "property", "sequence", "initial", "always", "always_ff", "always_comb",
    "assign", "module", "endmodule", "input", "output", "inout", "wire", "reg", "logic", "begin", "end", "if", "else",
    "case", "endcase", "for", "while", "integer", "parameter", "localparam", "posedge", "negedge", "force", "release",
    "bind", "function", "task", "generate", "genvar", "and", "or", "not", "dut", "past_valid", "unique", "priority",
}
NAME = re.compile(r"^[a-z][a-z0-9_]{0,30}$")
ID = re.compile(r"^[a-z][a-z0-9_]{0,40}$")


class PropertyError(ValueError):
    """The submitted property set cannot be compiled; the message is safe to show the model."""


def _tokens(expr: str) -> list[str]:
    if not isinstance(expr, str) or not expr.strip():
        raise PropertyError("every expression must be a non-empty string")
    if len(expr) > MAX_EXPR:
        raise PropertyError(f"an expression is longer than {MAX_EXPR} characters")
    out, pos = [], 0
    while pos < len(expr):
        match = TOKEN.match(expr, pos)
        if not match:
            if expr[pos:].strip() == "":
                break
            raise PropertyError(f"unsupported text near {expr[pos:pos + 16]!r}")
        out.append(match.group(1))
        pos = match.end()
    return out


def check_expr(expr: str, names: set[str]) -> str:
    """Whitelist: identifiers must be declared names; only $past, $stable, $rose, $fell are allowed."""
    for tok in _tokens(expr):
        if re.fullmatch(r"[A-Za-z_]\w*", tok):
            if tok in RESERVED or tok.startswith("ct_") or tok not in names:
                raise PropertyError(f"unknown or reserved name {tok!r}")
    return expr


def _split_args(text: str, start: int) -> tuple[list[str], int]:
    depth, args, cur = 0, [], ""
    for i in range(start, len(text)):
        c = text[i]
        if c == "(":
            depth += 1
            if depth > 1:
                cur += c
        elif c == ")":
            depth -= 1
            if depth == 0:
                args.append(cur.strip())
                return args, i + 1
            cur += c
        elif c == "," and depth == 1:
            args.append(cur.strip())
            cur = ""
        else:
            cur += c
    raise PropertyError("unbalanced parentheses")


class PastLowering:
    """Rewrite $past(expr[, n]) as named delay registers, so the value can be indexed or sliced."""

    def __init__(self, widths: dict[str, str]):
        """widths maps a plain name to its declaration range, such as "[N-1:0] " or ""."""
        self.widths, self.regs, self.cache = widths, [], {}

    def lower(self, expr: str) -> str:
        out, i = "", 0
        while True:
            j = expr.find("$past", i)
            if j < 0:
                return out + expr[i:]
            k = j + len("$past")
            while k < len(expr) and expr[k].isspace():
                k += 1
            if k >= len(expr) or expr[k] != "(":
                raise PropertyError("$past needs parentheses")
            args, end = _split_args(expr, k)
            if not 1 <= len(args) <= 2 or not args[0]:
                raise PropertyError("$past takes an expression and an optional depth")
            depth = 1
            if len(args) == 2:
                if not args[1].isdigit() or not 1 <= int(args[1]) <= MAX_PAST_DEPTH:
                    raise PropertyError(f"$past depth must be a number from 1 to {MAX_PAST_DEPTH}")
                depth = int(args[1])
            out += expr[i:j] + self._delay(self.lower(args[0]), depth)
            i = end

    def _delay(self, inner: str, depth: int) -> str:
        key = (inner, depth)
        if key not in self.cache:
            width = self.widths.get(inner.strip(), "[63:0] ")
            prev = f"({inner})"
            for _ in range(depth):
                name = f"ct_past{len(self.regs)}"
                self.regs.append((name, width, prev))
                prev = name
            self.cache[key] = prev
        return self.cache[key]


def validate(props: dict, module: Module) -> dict:
    """Shape and naming checks; returns the normalized property set."""
    if not isinstance(props, dict):
        raise PropertyError("the reply must be a JSON object")
    unknown = set(props) - {"state", "defs", "memories", "writes", "properties", "notes"}
    if unknown:
        raise PropertyError(f"unknown fields {sorted(unknown)}")
    taken = {module.clock, *module.inputs, *module.outputs, *module.primary}
    groups = {}
    for group in ("state", "defs", "memories"):
        items = props.get(group, []) or []
        if not isinstance(items, list) or len(items) > MAX_HELPERS:
            raise PropertyError(f"{group} must be a list of at most {MAX_HELPERS} items")
        for item in items:
            name = item.get("name") if isinstance(item, dict) else None
            if not isinstance(name, str) or not NAME.match(name) or name in RESERVED or name.startswith("ct_"):
                raise PropertyError(f"{group} name {name!r} is not allowed (lowercase letters, digits, underscores)")
            if name in taken:
                raise PropertyError(f"{group} name {name!r} collides with a port, parameter, or another helper")
            taken.add(name)
            width = item.get("width")
            # A width is an integer or a parameter name, checked at every parameter setting.
            sizes = [width] if isinstance(width, int) else [p[width] for p in module.params] if isinstance(width, str) and width in module.primary else []
            if isinstance(width, bool) or not sizes or not all(1 <= v <= 64 for v in sizes):
                raise PropertyError(f"{group} {name!r} needs a width from 1 to 64: an integer or a parameter name such as {next(iter(module.primary))}")
            if group == "memories" and (not isinstance(item.get("depth"), int) or not 1 <= item["depth"] <= 64):
                raise PropertyError(f"memory {name!r} needs an integer depth from 1 to 64")
        groups[group] = items
    writes = props.get("writes", []) or []
    if not isinstance(writes, list) or len(writes) > MAX_HELPERS:
        raise PropertyError(f"writes must be a list of at most {MAX_HELPERS} items")
    memories = {m["name"] for m in groups["memories"]}
    for w in writes:
        if not isinstance(w, dict) or w.get("memory") not in memories:
            raise PropertyError("each write must name a declared memory")
    properties = props.get("properties")
    if not isinstance(properties, list) or not 1 <= len(properties) <= MAX_PROPERTIES:
        raise PropertyError(f"properties must be a list of 1 to {MAX_PROPERTIES} items")
    seen = set()
    for q in properties:
        if not isinstance(q, dict) or not all(isinstance(q.get(k), str) for k in ("id", "when", "then")):
            raise PropertyError("each property needs string id, when, and then")
        if not ID.match(q["id"]) or q["id"] in seen:
            raise PropertyError(f"property id {q['id']!r} must be unique snake_case")
        seen.add(q["id"])
    return {"state": groups["state"], "defs": groups["defs"], "memories": groups["memories"], "writes": writes,
            "properties": [{k: q.get(k, "") for k in ("id", "when", "then", "why")} for q in properties]}


def _port_list(module: Module, with_outputs: bool) -> list[str]:
    ports = [f"input wire {module.clock}"] + [f"input wire {width_decl(w)}{n}" for n, w in module.inputs.items()]
    if with_outputs:
        ports += [f"output wire {width_decl(w)}{n}" for n, w in module.outputs.items()]
    return ports


def _param_list(module: Module) -> str:
    return ", ".join(f"parameter integer {k} = {v}" for k, v in module.primary.items())


def compile_checker(props: dict, module: Module) -> str:
    """Render ct_props_top. The DUT is `CT_DUT; every expression has passed the whitelist."""
    props = validate(props, module)
    names = {module.clock, *module.inputs, *module.outputs, *module.primary}
    names |= {i["name"] for g in ("state", "defs", "memories") for i in props[g]}
    widths = {**{n: width_decl(w) for n, w in {**module.inputs, **module.outputs}.items()},
              **{i["name"]: width_decl(i["width"]) for g in ("state", "defs") for i in props[g]}}
    lowering = PastLowering(widths)
    ex = lambda text: lowering.lower(check_expr(text, names))  # noqa: E731
    clk = module.clock
    lines = ["// Generated by Countertrace from model-written properties. Trusted template; do not edit.",
             "`default_nettype none", f"module ct_props_top #({_param_list(module)}) (",
             "    " + ",\n    ".join(_port_list(module, with_outputs=False)), ");"]
    lines += [f"    wire {width_decl(w)}{n};" for n, w in module.outputs.items()]
    conns = ", ".join(f".{n}({n})" for n in module.ports())
    lines.append(f"    `CT_DUT #({', '.join(f'.{k}({k})' for k in module.primary)}) dut ({conns});")
    lines += ["    reg past_valid = 1'b0;",
              f"    // Environment assumption owned by this template: reset at the first edge, inputs only.",
              f"    always @(*) if (!past_valid) assume ({module.reset});"]
    for m in props["memories"]:
        lines.append(f"    reg {width_decl(m['width'])}{m['name']} [0:{m['depth'] - 1}];")
    for s in props["state"]:
        lines.append(f"    reg {width_decl(s['width'])}{s['name']};")
    for d in props["defs"]:
        lines.append(f"    wire {width_decl(d['width'])}{d['name']};")
    body = []
    for d in props["defs"]:
        body.append(f"    assign {d['name']} = {ex(d['expr'])};")
    for s in props["state"]:
        body.append(f"    always @(posedge {clk}) {s['name']} <= {ex(s['next'])};")
    for w in props["writes"]:
        body.append(f"    always @(posedge {clk}) if ({ex(w['when'])}) {w['memory']}[{ex(w['index'])}] <= {ex(w['value'])};")
    body += [f"    always @(posedge {clk}) begin", "        past_valid <= 1'b1;", "        if (past_valid) begin"]
    for q in props["properties"]:
        when = ex(q["when"])
        body.append(f"            if ({when}) p_{q['id']}: assert ({ex(q['then'])});")
        body.append(f"            r_{q['id']}: cover ({when});")
    body += ["        end", "    end"]
    for name, width, source in lowering.regs:
        lines.append(f"    reg {width}{name};")
        body.append(f"    always @(posedge {clk}) {name} <= {source};")
    return "\n".join(lines + body + ["endmodule", "`default_nettype wire"]) + "\n"


def compile_miter(module: Module) -> str:
    """ct_miter compares the golden (module top) with `CT_OTHER on identical inputs.

    Outputs with an observation qualifier are compared only when it holds on the golden.
    """
    lines = ["// Generated by Countertrace. Trusted template; do not edit.", "`default_nettype none",
             f"module ct_miter #({_param_list(module)}) (", "    " + ",\n    ".join(_port_list(module, with_outputs=False)), ");"]
    for suffix in ("g", "o"):
        lines += [f"    wire {width_decl(w)}{n}_{suffix};" for n, w in module.outputs.items()]
    params = ", ".join(f".{k}({k})" for k in module.primary)
    for inst, suffix, mod in (("gold", "g", module.top), ("other", "o", "`CT_OTHER")):
        conns = ", ".join([f".{n}({n})" for n in [module.clock, *module.inputs]] + [f".{n}({n}_{suffix})" for n in module.outputs])
        lines.append(f"    {mod} #({params}) {inst} ({conns});")
    lines += ["    reg past_valid = 1'b0;", f"    always @(*) if (!past_valid) assume ({module.reset});",
              f"    always @(posedge {module.clock}) begin", "        past_valid <= 1'b1;", "        if (past_valid) begin"]
    for name in module.outputs:
        qualifier = module.observe.get(name) or "1'b1"
        for out in module.outputs:
            qualifier = re.sub(rf"\b{out}\b", f"{out}_g", qualifier)
        lines.append(f"            if ({qualifier}) eq_{name}: assert ({name}_g == {name}_o);")
    lines += ["        end", "    end", "endmodule", "`default_nettype wire"]
    return "\n".join(lines) + "\n"


def compile_mutant_wrapper(module: Module) -> str:
    """<top>_mut selects one mutation of <top>_all through `CT_MUTSEL."""
    conns = ", ".join(f".{n}({n})" for n in module.ports())
    return "\n".join([
        "// Generated by Countertrace. Trusted template; do not edit.", "`default_nettype none",
        f"module {module.top}_mut #({_param_list(module)}) (", "    " + ",\n    ".join(_port_list(module, with_outputs=True)), ");",
        f"    {module.top}_all u ({conns}, .mutsel(`CT_MUTSEL));", "endmodule", "`default_nettype wire"]) + "\n"


def expected_inventory(props: dict) -> dict[str, int]:
    n = len(props["properties"])
    return {"assert": n, "cover": n, "assume": 1}
