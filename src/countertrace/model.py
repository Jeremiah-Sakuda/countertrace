"""NVIDIA Nemotron through Nebius Token Factory (OpenAI-compatible chat API).

The model interprets intent, explains recorded evidence, and proposes DUT
patches. It never authorizes a result: every response is schema-validated,
citations are checked against the recorded trace, and patches are re-admitted
and re-verified against the unchanged check set. Only this control-service
process reads the credential; workers never receive it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import threading
import time
from urllib import error, request
from urllib.parse import urlsplit

from countertrace.contract import ASSUMPTIONS, CHECKS, REQUIREMENTS, Contract

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SIGNALS = ["clk", "rst", "wr_en", "rd_en", "din", "dout", "full", "empty"]
INTERPRET_TOPICS = {
    "reset_kind": "Reset is synchronous and active-high, sampled on the rising clock edge.",
    "reset_priority": REQUIREMENTS["reset"]["text"],
    "reset_recurrence": "Reset may be asserted again at any later edge and must restore the empty state.",
    "write_when_full": REQUIREMENTS["write_full"]["text"],
    "read_when_empty": REQUIREMENTS["read_empty"]["text"],
    "simultaneous_mid": REQUIREMENTS["both_mid"]["text"],
    "simultaneous_empty": REQUIREMENTS["both_empty"]["text"],
    "simultaneous_full": REQUIREMENTS["both_full"]["text"],
    "ordering": "Accepted words leave exactly once and in arrival order, across pointer wraparound.",
    "read_latency": "dout is registered: it holds the removed word after the edge of an accepted read (no fall-through).",
    "depth": "DEPTH words of capacity, for the selected DEPTH.",
    "flags": "full is true exactly when DEPTH words are stored and empty exactly when none are; there are no early-warning or almost-full semantics on these outputs.",
    "width": "8-bit data words.",
}
STATUSES = ("matches", "conflict", "unspecified", "unsupported")


class ModelError(Exception):
    def __init__(self, status: str, message: str, meta: dict | None = None):
        super().__init__(message)
        self.status = status
        self.meta = meta or {}


def load_env_file() -> None:
    """Load .env into this control-service process without overriding exported values."""
    path = ROOT / ".env"
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key.startswith(("NEBIUS_", "COUNTERTRACE_")) and value and not os.environ.get(key):
            os.environ[key] = value


def env_int(name: str) -> int | None:
    value = os.environ.get(name, "").strip()
    return int(value) if value.isdigit() and int(value) > 0 else None


def env_float(name: str) -> float | None:
    try:
        value = float(os.environ.get(name, "").strip())
    except ValueError:
        return None
    return value if value >= 0 else None


def config() -> dict:
    load_env_file()
    return {
        "api_key": os.environ.get("NEBIUS_API_KEY", "").strip(),
        "base_url": os.environ.get("NEBIUS_BASE_URL", "").strip().rstrip("/"),
        "model_id": os.environ.get("NEBIUS_MODEL_ID", "").strip(),
        "repair_model_id": os.environ.get("NEBIUS_REPAIR_MODEL_ID", "").strip(),
        # Optional faster tier for interactive interpretation and check proposals.
        "fast_model_id": os.environ.get("NEBIUS_FAST_MODEL_ID", "").strip(),
        "input_limit": env_int("COUNTERTRACE_MODEL_INPUT_TOKEN_LIMIT"),
        "output_limit": env_int("COUNTERTRACE_MODEL_OUTPUT_TOKEN_LIMIT"),
        "spend_limit": env_float("COUNTERTRACE_DEPLOYMENT_SPEND_LIMIT_USD"),
        "price_in": env_float("COUNTERTRACE_MODEL_PRICE_INPUT_PER_MTOK_USD"),
        "price_out": env_float("COUNTERTRACE_MODEL_PRICE_OUTPUT_PER_MTOK_USD"),
        # Reasoning controls differ across Nemotron generations and providers.
        # A model-specific directive must be selected explicitly for the endpoint.
        "system_prefix": os.environ.get("COUNTERTRACE_MODEL_SYSTEM_PREFIX", ""),
        "timeout": env_int("COUNTERTRACE_MODEL_TIMEOUT_S") or 120,
    }


def unavailable_reason(cfg: dict) -> str | None:
    missing = [n for n, k in (("NEBIUS_API_KEY", "api_key"), ("NEBIUS_BASE_URL", "base_url"),
                              ("NEBIUS_MODEL_ID", "model_id")) if not cfg[k]]
    if missing:
        return f"Model not configured: set {', '.join(missing)}."
    if not cfg["input_limit"] or not cfg["output_limit"]:
        return ("Token limits not configured: set COUNTERTRACE_MODEL_INPUT_TOKEN_LIMIT and "
                "COUNTERTRACE_MODEL_OUTPUT_TOKEN_LIMIT before making model calls.")
    if cfg["spend_limit"] is not None and (cfg["price_in"] is None or cfg["price_out"] is None):
        return ("A spend limit is set but per-token prices are not, so it cannot be enforced. Set "
                "COUNTERTRACE_MODEL_PRICE_INPUT_PER_MTOK_USD and COUNTERTRACE_MODEL_PRICE_OUTPUT_PER_MTOK_USD.")
    if urlsplit(cfg["base_url"]).scheme != "https":
        return "NEBIUS_BASE_URL must be an https URL."
    return None


def public_config() -> dict:
    cfg = config()
    return {
        "configured": unavailable_reason(cfg) is None,
        "reason": unavailable_reason(cfg),
        "model_id": cfg["model_id"] or None,
        "repair_model_id": cfg["repair_model_id"] or cfg["model_id"] or None,
        "fast_model_id": cfg["fast_model_id"] or cfg["model_id"] or None,
        "endpoint_host": urlsplit(cfg["base_url"]).hostname if cfg["base_url"] else None,
        "input_token_limit": cfg["input_limit"],
        "output_token_limit": cfg["output_limit"],
        "spend": spend_summary(cfg),
    }


# -- usage ledger -------------------------------------------------------------
def ledger_path() -> Path:
    from countertrace.runs import data_dir

    path = data_dir() / "model_usage.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def model_prices(cfg: dict) -> dict[str, tuple[float, float]]:
    """Optional per-model prices from COUNTERTRACE_MODEL_PRICES_JSON: {"model": [input, output]} per million."""
    try:
        raw = json.loads(os.environ.get("COUNTERTRACE_MODEL_PRICES_JSON", "") or "{}")
        return {k: (float(v[0]), float(v[1])) for k, v in raw.items()}
    except (ValueError, TypeError, IndexError):
        return {}


def spend_summary(cfg: dict) -> dict:
    total_in = total_out = calls = 0
    cost = 0.0
    priced = cfg["price_in"] is not None and cfg["price_out"] is not None
    per_model = model_prices(cfg)
    defaulted = set()
    path = ledger_path()
    if path.is_file():
        for line in path.read_text().splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            calls += 1
            tokens_in, tokens_out = entry.get("prompt_tokens") or 0, entry.get("completion_tokens") or 0
            total_in += tokens_in
            total_out += tokens_out
            price = per_model.get(entry.get("model_id") or "")
            if price is None:
                defaulted.add(entry.get("model_id") or "unknown")
                price = (cfg["price_in"], cfg["price_out"]) if priced else None
            if price is not None:
                cost += tokens_in / 1e6 * price[0] + tokens_out / 1e6 * price[1]
    estimated = priced or (not defaulted and bool(per_model))
    return {"calls": calls, "prompt_tokens": total_in, "completion_tokens": total_out,
            "estimated_cost_usd": round(cost, 4) if estimated else None,
            "cost_status": "estimated" if estimated else "unavailable",
            "models_at_default_price": sorted(m for m in defaulted if m not in per_model),
            "spend_limit_usd": cfg["spend_limit"]}


def record_usage(meta: dict) -> None:
    entry = {k: meta.get(k) for k in ("task", "model_id", "prompt_tokens", "completion_tokens", "latency_ms",
                                       "status", "at", "thinking", "finish_reason")}
    with ledger_path().open("a") as handle:
        handle.write(json.dumps(entry) + "\n")


# -- transport ----------------------------------------------------------------
def estimate_tokens(text: str) -> int:
    return len(text) // 3 + 1


def strip_reasoning(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    return text.strip()


def extract_json(text: str) -> dict:
    text = strip_reasoning(text)
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.S)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("response is not a JSON object")
    return value


_CONCURRENCY = threading.BoundedSemaphore(int(os.environ.get("COUNTERTRACE_MODEL_CONCURRENCY", "3") or 3))


def thinking_default(task: str) -> bool:
    """Reasoning is on unless the task is listed in COUNTERTRACE_THINKING_OFF_TASKS.

    Default: off for the interactive interpretation and check-proposal tasks
    (6/6 development briefs either way, 1.7-2.9 s instead of 4.7-9 s on Super);
    on for explanation and repair.
    """
    raw = os.environ.get("COUNTERTRACE_THINKING_OFF_TASKS", "interpret,propose_checks")
    off = {t.strip() for t in raw.split(",") if t.strip()}
    return task not in off


_RESERVED = {"usd": 0.0}
_RESERVE_LOCK = threading.Lock()


def full_system(cfg: dict, system: str) -> str:
    """The exact system message sent, used for both size checks and spend reservation."""
    return f"{cfg['system_prefix']}\n\n{system}".strip()


def price_for(cfg: dict, model: str) -> tuple[float, float] | None:
    per_model = model_prices(cfg).get(model)
    if per_model:
        return per_model
    if cfg["price_in"] is not None and cfg["price_out"] is not None:
        return cfg["price_in"], cfg["price_out"]
    return None


def chat(task: str, system: str, user: str, max_tokens: int | None = None, model_id: str | None = None,
         temperature: float = 0.2, thinking: bool | None = None) -> tuple[str, dict]:
    """One model call with a worst-case spend reservation and a one-step tier fallback.

    The reservation covers the estimated input plus the full output cap, so
    concurrent calls cannot jointly overshoot the threshold. On a network or
    5xx failure the call is retried once on COUNTERTRACE_FALLBACK_MODEL_ID
    (default: the fast tier); the fallback is recorded in the call metadata.
    """
    cfg = config()
    model = model_id or cfg["model_id"]
    try:
        return _reserved_call(cfg, task, system, user, max_tokens, model, temperature, thinking)
    except ModelError as exc:
        fallback = os.environ.get("COUNTERTRACE_FALLBACK_MODEL_ID", "").strip() or cfg["fast_model_id"]
        transient = (exc.meta.get("status") == "network_error" or str(exc).startswith("HTTP 5")
                     or str(exc).startswith("HTTP 429"))
        if not (transient and fallback and fallback != model):
            raise
        content, meta = _reserved_call(cfg, task, system, user, max_tokens, fallback, temperature, thinking)
        meta["fallback_from"] = model
        return content, meta


def _reserved_call(cfg, task, system, user, max_tokens, model, temperature, thinking):
    worst = 0.0
    price = price_for(cfg, model)
    if cfg["spend_limit"] is not None and price is not None:
        out_cap = min(max_tokens or cfg["output_limit"] or 0, cfg["output_limit"] or 0)
        worst = estimate_tokens(full_system(cfg, system) + user) / 1e6 * price[0] + out_cap / 1e6 * price[1]
        with _RESERVE_LOCK:
            spent = spend_summary(cfg)["estimated_cost_usd"] or 0.0
            if spent + _RESERVED["usd"] + worst > cfg["spend_limit"]:
                raise ModelError("unavailable", "Deployment spend limit reached (including in-flight reservations).")
            _RESERVED["usd"] += worst
    try:
        with _CONCURRENCY:  # bound simultaneous inference calls across all visitors
            return _chat(task, system, user, max_tokens, model, temperature, thinking)
    finally:
        if worst:
            with _RESERVE_LOCK:
                _RESERVED["usd"] -= worst


def _chat(task: str, system: str, user: str, max_tokens: int | None, model_id: str | None,
          temperature: float, thinking: bool | None) -> tuple[str, dict]:
    cfg = config()
    reason = unavailable_reason(cfg)
    if reason:
        raise ModelError("unavailable", reason)
    spend = spend_summary(cfg)
    if cfg["spend_limit"] is not None and (spend["estimated_cost_usd"] or 0) >= cfg["spend_limit"]:
        raise ModelError("unavailable", "Deployment spend limit reached.")
    prompt_estimate = estimate_tokens(full_system(cfg, system) + user)
    if prompt_estimate > cfg["input_limit"]:
        raise ModelError("input_too_large", f"Estimated {prompt_estimate} input tokens exceeds the configured limit.")
    model = model_id or cfg["model_id"]
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": full_system(cfg, system)},
                     {"role": "user", "content": user}],
        "max_tokens": min(max_tokens or cfg["output_limit"], cfg["output_limit"]),
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    thinking = thinking_default(task) if thinking is None else thinking
    if not thinking:
        # Nemotron 3 chat template switch; Token Factory honors it (verified 2026-10-04).
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    meta = {"task": task, "model_id": model, "endpoint_host": urlsplit(cfg["base_url"]).hostname,
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "attempts": 0, "thinking": thinking}
    last_error = None
    for attempt in range(3):
        meta["attempts"] = attempt + 1
        req = request.Request(
            cfg["base_url"] + "/chat/completions", data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"},
            method="POST",
        )
        started = time.monotonic()
        try:
            with request.urlopen(req, timeout=cfg["timeout"]) as resp:
                body = json.loads(resp.read())
                meta["request_id"] = resp.headers.get("x-request-id")
        except error.HTTPError as exc:
            detail = exc.read()[:500].decode(errors="replace")
            last_error = f"HTTP {exc.code}: {detail}"
            if exc.code == 400 and "chat_template_kwargs" in payload and "chat_template" in detail:
                payload.pop("chat_template_kwargs")  # endpoint without the template switch
                meta["thinking"] = None
                continue
            if exc.code == 400 and "response_format" in payload:
                payload.pop("response_format")  # some deployments reject JSON mode; validation still applies
                continue
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            meta["status"] = "http_error"
            record_usage(meta)
            raise ModelError("error", last_error.replace(cfg["api_key"], "[redacted]"), meta) from None
        except (error.URLError, TimeoutError, OSError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            meta["status"] = "network_error"
            record_usage(meta)
            raise ModelError("error", last_error, meta) from None
        meta["latency_ms"] = round((time.monotonic() - started) * 1000)
        usage = body.get("usage") or {}
        meta.update(prompt_tokens=usage.get("prompt_tokens"), completion_tokens=usage.get("completion_tokens"),
                    model_reported=body.get("model"), status="ok",
                    finish_reason=(body.get("choices") or [{}])[0].get("finish_reason"))
        record_usage(meta)
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        return content, meta
    raise ModelError("error", last_error or "model call failed", meta)


def structured(task: str, system: str, user: str, validate, max_tokens: int | None = None,
               model_id: str | None = None) -> dict:
    """Call the model, parse JSON, validate, and retry once.

    A reply cut off at the output limit is retried with reasoning switched off,
    so the retry spends its budget on the answer rather than repeating the same
    exhausted request. Other schema failures are retried with the validator's error.
    """
    calls = []
    prompt = user
    thinking = None
    for attempt in range(2):
        content, meta = chat(task, system, prompt, max_tokens=max_tokens, model_id=model_id, thinking=thinking)
        calls.append(meta)
        try:
            value = validate(extract_json(content))
            return {"status": "ok", "result": value, "calls": calls}
        except (ValueError, KeyError, TypeError) as exc:
            calls[-1]["schema_error"] = str(exc)[:300]
            if meta.get("finish_reason") == "length":
                thinking = False
                prompt = (f"{user}\n\nYour previous reply ran out of output tokens before the JSON was complete. "
                          "Answer directly with only the JSON object; keep text fields short.")
            else:
                prompt = (f"{user}\n\nYour previous reply was rejected by the schema validator: {exc}. "
                          "Reply again with only the JSON object in the required schema.")
    return {"status": "schema_error", "result": None, "calls": calls,
            "detail": "The model response did not satisfy the schema after one retry."}


def guarded(func):
    def wrapper(*args, **kwargs) -> dict:
        try:
            return func(*args, **kwargs)
        except ModelError as exc:
            return {"status": exc.status, "detail": str(exc), "result": None, "calls": [exc.meta] if exc.meta else []}
    wrapper.__name__ = func.__name__
    return wrapper


# -- task: intent interpretation ------------------------------------------------
INTERPRET_SYSTEM = """You review a hardware designer's natural-language brief for a synchronous FIFO against a fixed contract profile.
For each topic, report what the brief says and whether it matches, conflicts with, leaves unspecified, or requests something the profile does not support.
Do not resolve conflicts yourself and do not change the contract. Unsupported requests include fall-through (first-word) reads, accepting a write when full during a simultaneous read, asynchronous reset, multiple clocks, and parameters other than WIDTH=8 and DEPTH 2 or 4.
Reply with one JSON object only:
{"summary": string, "decisions": [{"topic": string, "brief_says": string or null, "status": "matches"|"conflict"|"unspecified"|"unsupported", "note": string}]}
Include every topic exactly once."""


def validate_interpretation(value: dict) -> dict:
    decisions = value["decisions"]
    if not isinstance(decisions, list):
        raise ValueError("decisions must be a list")
    seen = {}
    for item in decisions:
        topic = item["topic"]
        if topic not in INTERPRET_TOPICS:
            raise ValueError(f"unknown topic {topic!r}")
        if item["status"] not in STATUSES:
            raise ValueError(f"invalid status {item['status']!r}")
        if topic in seen:
            raise ValueError(f"duplicate topic {topic!r}")
        seen[topic] = {"topic": topic, "contract": INTERPRET_TOPICS[topic],
                       "brief_says": None if item.get("brief_says") in (None, "") else str(item["brief_says"])[:400],
                       "status": item["status"], "note": str(item.get("note", ""))[:400]}
    missing = sorted(set(INTERPRET_TOPICS) - set(seen))
    if len(missing) > 3:
        raise ValueError(f"missing topics: {', '.join(missing)}")
    for topic in missing:  # recorded explicitly, never silently accepted
        seen[topic] = {"topic": topic, "contract": INTERPRET_TOPICS[topic], "brief_says": None,
                       "status": "unspecified", "note": "Not addressed by the model; shown as a decision for you."}
    return {"summary": str(value.get("summary", ""))[:800],
            "decisions": [seen[t] for t in INTERPRET_TOPICS], "backend_filled": missing}


@guarded
def interpret(brief: str, contract: Contract) -> dict:
    if not brief.strip():
        return {"status": "error", "detail": "The brief is empty.", "result": None, "calls": []}
    topics = "\n".join(f"- {k}: {v}" for k, v in INTERPRET_TOPICS.items())
    user = (f"Contract profile {contract.profile} v{contract.version}, DEPTH={contract.depth}, WIDTH={contract.width}.\n"
            f"Topics and the contract's fixed behavior:\n{topics}\n\nBrief:\n\"\"\"\n{brief}\n\"\"\"")
    # Configured output cap: reasoning endpoints can exhaust a small task-local limit.
    result = structured("interpret", INTERPRET_SYSTEM, user, validate_interpretation,
                        model_id=config()["fast_model_id"] or None)
    if result["status"] == "ok":
        decisions = result["result"]["decisions"]
        result["blocking"] = [d["topic"] for d in decisions if d["status"] in ("conflict", "unsupported")]
        result["needs_decision"] = [d["topic"] for d in decisions if d["status"] == "unspecified"]
    return result


# -- task: grounded explanation ---------------------------------------------------
EXPLAIN_SYSTEM = """You explain a recorded FIFO verification failure to a student who knows RTL basics.
Use only the evidence provided. The deterministic checker already decided that the design failed; you explain why, you do not re-judge it.
Cite every claim with cycle numbers from the provided table and signal names that exist in the evidence or RTL. Cite RTL line numbers for the likely cause.
The normalized trace samples interface signals and reference-queue state, not internal registers or memory addresses. Explain the RTL logic, but do not assert numeric internal-register values or memory indices that are absent from the sampled trace.
Reply with one JSON object only:
{"summary": string (two sentences max), "steps": [{"text": string, "cycles": [int], "signals": [string]}], "likely_cause": {"text": string, "lines": [int]}, "next_action": string, "limits": string}
"limits" must state what this failure and any passing checks do and do not establish.
A witnessed failure refutes the contract for the tested configuration. Passing simulation checks cover only their named tests; bounded checks cover their stated horizon; an unbounded proof applies only to its named property and assumptions. Reached cover scenarios establish reachability, not correctness. Unresolved obligations are not passes.
Use the supplied run outcomes for these limits. Do not invent which input conditions passing checks covered or claim that all passing checks excluded full/empty conditions. Other outcomes can come from different traces; do not merge them into the trace being explained.
If naming another outcome, identify its exact method/check pair and status. Never group an unresolved formal check with witnessed counterexamples; a simulation failure does not imply that the formal checker found that same failure."""


def numbered(source: str) -> str:
    return "\n".join(f"{i:3d}| {line}" for i, line in enumerate(source.splitlines(), 1))


def trace_table(rows: list[dict], start: int, end: int) -> str:
    fmt = lambda q: "-" if q is None else "[" + ", ".join(f"{x:02x}" for x in q) + "]"
    lines = ["cycle | rst wr_en rd_en din | contract row | accepted | pre-edge queue -> post-edge queue | "
             "expected dout/empty/full | observed dout/empty/full | mismatches"]
    for r in rows[start:end + 1]:
        acc = "reset" if r["accepted"]["reset"] else "+".join(k for k in ("read", "write") if r["accepted"][k]) or "none"
        exp = r["expected"]
        obs = r["observed"]
        exp_d = f"{exp['dout']:02x}" if exp["dout"] is not None else "--"
        lines.append(
            f"{r['cycle']} | {r['rst']} {r['wr_en']} {r['rd_en']} {r['din']:02x} | {r['row']} | {acc} | "
            f"{fmt(r['pre_queue'])} -> {fmt(r['post_queue'])} | {exp_d}/{int(exp['empty'])}/{int(exp['full'])} | "
            f"{obs['dout']:02x}{'' if r['dout_checked'] else '(unchecked)'}/{int(obs['empty'])}/{int(obs['full'])} | "
            f"{','.join(r['mismatches']) or '-'}")
    return "\n".join(lines)


def citation_check(result: dict, rows: list[dict], start: int, end: int, source: str) -> dict:
    allowed_cycles = {r["cycle"] for r in rows[start:end + 1]}
    identifiers = set(re.findall(r"\b[A-Za-z_]\w*\b", source))
    allowed_signals = set(CANONICAL_SIGNALS) | identifiers
    line_count = len(source.splitlines())
    valid = 0
    invalid = []
    uncited = 0
    for i, step in enumerate(result["steps"]):
        if not step["cycles"] and not step["signals"]:
            uncited += 1
        for cycle in step["cycles"]:
            if cycle in allowed_cycles:
                valid += 1
            else:
                invalid.append({"step": i, "kind": "cycle", "value": cycle})
        for signal in step["signals"]:
            base = re.sub(r"\[.*$", "", signal).split(".")[-1]
            if base in allowed_signals:
                valid += 1
            else:
                invalid.append({"step": i, "kind": "signal", "value": signal})
    for line in result["likely_cause"]["lines"]:
        if 1 <= line <= line_count:
            valid += 1
        else:
            invalid.append({"step": None, "kind": "line", "value": line})
    return {"valid": valid, "invalid": invalid, "uncited_steps": uncited,
            "allowed_cycles": [min(allowed_cycles), max(allowed_cycles)] if allowed_cycles else None}


def validate_explanation(value: dict) -> dict:
    steps = []
    for step in value["steps"]:
        steps.append({"text": str(step["text"])[:600],
                      "cycles": [int(c) for c in step.get("cycles", [])][:12],
                      "signals": [str(s)[:40] for s in step.get("signals", [])][:12]})
    if not steps:
        raise ValueError("steps must not be empty")
    cause = value["likely_cause"]
    return {"summary": str(value["summary"])[:600], "steps": steps[:8],
            "likely_cause": {"text": str(cause["text"])[:600], "lines": [int(x) for x in cause.get("lines", [])][:8]},
            "next_action": str(value["next_action"])[:400], "limits": str(value["limits"])}


def primary_finding(state: dict) -> dict | None:
    findings = (state.get("verification") or {}).get("findings") or []
    sims = [f for f in findings if f["source"] == "simulation"]
    return (sims or findings or [None])[0]


@guarded
def explain_run(state: dict, source: str) -> dict:
    finding = primary_finding(state)
    if finding is None:
        return {"status": "not_applicable", "detail": "There is no recorded failure to explain.", "result": None, "calls": []}
    rows = state["verification"]["traces"][finding["trace"]]
    start, end = finding["window"]["start"], finding["window"]["end"]
    related = "\n".join(f"- {e['text']}" for e in finding.get("related_events", [])) or "- none"
    outcomes = [{key: obligation[key] for key in ("id", "method", "status", "detail", "depth", "tests")
                 if key in obligation} for obligation in state["verification"].get("obligations", [])]
    user = (
        f"Configuration under test: DEPTH={state['depth']}, WIDTH=8. State this configuration exactly; "
        f"results apply to no other configuration.\n"
        f"Contract row at the failing edge ({finding['requirement_id']}): {finding['requirement_text']}\n"
        f"Failed check: {finding['check']} — {finding['check_text']}\n"
        f"First observed mismatch: cycle {finding['cycle']} in test {finding['test']} ({finding['source']}).\n"
        f"Expected: {json.dumps(finding['expected'])}  Observed: {json.dumps(finding['observed'])}\n"
        f"Deterministic related events:\n{related}\n\n"
        f"Sampling convention: cycle k is a rising edge; queues are oldest first; dout is checked only after an accepted read.\n"
        f"Cycle table (hex data):\n{trace_table(rows, start, end)}\n\nRTL with line numbers:\n{numbered(source)}\n\n"
        f"Assumptions: {' '.join(ASSUMPTIONS)}\n\n"
        f"Run outcomes for result scope (may refer to other tests and traces):\n{json.dumps(outcomes)}"
    )
    # Use the configured output cap: reasoning-capable endpoints can exhaust a
    # smaller task-local limit before producing their final structured answer.
    result = structured("explain", EXPLAIN_SYSTEM, user, validate_explanation)
    if result["status"] == "ok":
        result["citation_check"] = citation_check(result["result"], rows, start, end, source)
        if result["citation_check"]["invalid"]:
            result["status"] = "ok_with_invalid_citations"
    result["finding"] = {k: finding[k] for k in ("test", "cycle", "check", "requirement_id", "source")}
    return result


# -- task: constrained repair -----------------------------------------------------
REPAIR_SYSTEM = """You repair a synchronous FIFO RTL module so it satisfies a fixed contract.
Change only the module's internal logic. Keep the module name, parameters, port names, directions, and widths exactly the same.
Do not add assertions, assumptions, initial blocks, system tasks, compiler directives, attributes, or extra modules.
Return a minimal patch as exact-match edits. Each "find" must be copied verbatim from the current RTL (including indentation) and must occur exactly once; "replace" is its new text. Keep comments and author headers unchanged. Use as few, short edits as possible.
Reply with one JSON object only:
{"rationale": string, "edits": [{"find": string, "replace": string}]}"""
MAX_REPAIR_EDITS = 8


def apply_edits(source: str, edits: list) -> str:
    """Apply exact-match edits; every target must occur exactly once in the current text."""
    if not isinstance(edits, list) or not 1 <= len(edits) <= MAX_REPAIR_EDITS:
        raise ValueError(f"edits must be a list of 1 to {MAX_REPAIR_EDITS} items")
    for i, edit in enumerate(edits):
        find, replace = edit.get("find"), edit.get("replace")
        if not isinstance(find, str) or not find.strip() or not isinstance(replace, str):
            raise ValueError(f"edit {i} needs a non-empty find string and a replace string")
        count = source.count(find)
        if count != 1:
            raise ValueError(f"edit {i}: find text occurs {count} times in the current RTL; copy exactly one occurrence verbatim")
        source = source.replace(find, replace)
    return source


def validate_repair(value: dict, current: str) -> dict:
    source = apply_edits(current, value["edits"])
    if source == current:
        raise ValueError("the edits do not change the RTL")
    if len(source) > 64 * 1024:
        raise ValueError("the patched RTL exceeds 64 KiB")
    return {"rationale": str(value["rationale"])[:800], "source": source,
            "edits": [{"find": e["find"], "replace": e["replace"]} for e in value["edits"]]}


@guarded
def propose_repair(source: str, finding: dict, rows: list[dict], previous: list[dict],
                   finding_source: str = "current", include_outcomes: bool = True) -> dict:
    cfg = config()
    start, end = finding["window"]["start"], finding["window"]["end"]
    def outcome(a: dict) -> str:
        if include_outcomes:
            return f"{a['status']}. {a.get('summary', '')}"
        return "rejected." if a["status"] != "passed_unchanged_checks" else "passed."

    history = "\n".join(
        f"- Attempt {a['index']}: {outcome(a)}"
        + (f"\n  Diff it applied:\n{a['diff'][:1500]}" if a.get("diff") else "") for a in previous) or "- none"
    contract_text = "\n".join(f"- {r['title']}: {r['text']}" for r in REQUIREMENTS.values())
    if finding_source == "current":
        origin = ("The current RTL below is what failed; the finding and trace are from verifying it"
                  f"{' (a previous candidate)' if previous else ''}.\n")
    else:
        origin = ("The finding and trace below come from an earlier version of the RTL. The current RTL below "
                  "includes later changes that were also rejected; no counterexample from it is provided.\n")
    user = (
        f"Contract requirements:\n{contract_text}\nChecks: {json.dumps(CHECKS)}\n\n"
        + origin +
        f"Failing clause ({finding['requirement_id']}): {finding['requirement_text']}\n"
        f"First mismatch: cycle {finding['cycle']}, check {finding['check']}; expected {json.dumps(finding['expected'])}, "
        f"observed {json.dumps(finding['observed'])}.\n"
        f"Related events:\n" + ("\n".join(f"- {e['text']}" for e in finding.get('related_events', [])) or "- none") + "\n\n"
        f"Reproducible trace window:\n{trace_table(rows, start, end)}\n\nPrevious attempts:\n{history}\n\n"
        f"Current RTL:\n{source}"
    )
    return structured("repair", REPAIR_SYSTEM, user, lambda v: validate_repair(v, source),
                      model_id=cfg["repair_model_id"] or None)


# -- task: supplemental check proposal ----------------------------------------------
CHECKS_SYSTEM = """You propose a small supplemental check set for a synchronous FIFO, the kind a student would add to a testbench.
You may only use the provided check templates, contract rows, and named stimulus tests. You cannot write code.
Choose the tests the checks observe and, for each check, the template, the contract rows where it applies (or null for every edge), and the requirement it targets.
Reply with one JSON object only:
{"label": string, "rationale": string, "tests": [string], "checks": [{"id": string, "check": string, "rows": [string] or null, "requirement": string, "text": string}]}
Use at most 8 checks."""


def validate_check_proposal(value: dict, tests: list[str]) -> dict:
    from countertrace.scoreboard import check_set_from_dict

    chosen = value.get("tests")
    if not isinstance(chosen, list) or not chosen or any(t not in tests for t in chosen):
        raise ValueError(f"tests must be a non-empty subset of {tests}")
    checks = value["checks"]
    if not isinstance(checks, list) or not 1 <= len(checks) <= 8:
        raise ValueError("between 1 and 8 checks are required")
    for i, check in enumerate(checks):
        check["id"] = re.sub(r"[^a-z0-9_]", "_", str(check.get("id") or f"check_{i}").lower())[:40]
        check["text"] = str(check.get("text", ""))[:200]
    data = {"id": "candidate", "label": str(value.get("label", "Model-proposed checks"))[:80],
            "tests": chosen, "checks": checks}
    check_set_from_dict(data)  # reviewed templates and known rows only
    return {**data, "rationale": str(value.get("rationale", ""))[:600]}


@guarded
def propose_check_set(description: str, contract: Contract, tests: list[str]) -> dict:
    from countertrace.scoreboard import ROWS

    rows = "\n".join(f"- {r}: {REQUIREMENTS[r]['title']}. {REQUIREMENTS[r]['text']}" for r in ROWS)
    user = (f"Check templates: {json.dumps(CHECKS)}\nContract rows:\n{rows}\nNamed stimulus tests: {', '.join(tests)}\n\n"
            f"Student's description of what their testbench checks:\n\"\"\"\n{description}\n\"\"\"")
    return structured("propose_checks", CHECKS_SYSTEM, user,
                      lambda v: validate_check_proposal(v, tests), model_id=config()["fast_model_id"] or None)


# -- feasibility check ------------------------------------------------------------
def feasibility_check(run_id: str | None = None) -> dict:
    """Explain a completed local failure, attach the result, and retain a check report.

    Schema correction may require another call. A successful transport/schema
    result still needs human review for explanation usefulness.
    """
    from countertrace.runs import RunStore, data_dir

    store = RunStore()
    candidate = None
    if run_id:
        try:
            candidate = store.load(run_id)
        except KeyError:
            return {"status": "error", "detail": "The requested local run does not exist."}
    else:
        for item in store.list():
            if (item["kind"] == "verification" and item.get("state") == "complete"
                    and not item.get("recorded")
                    and (item.get("verdict") or {}).get("headline") == "counterexample"):
                candidate = store.load(item["id"])
                break
    if candidate is None:
        return {"status": "error", "detail": "Run `countertrace verify --example showcase-overwrite-when-full` first."}
    if (candidate.get("kind") != "verification" or candidate.get("state") != "complete"
            or candidate.get("recorded")
            or (candidate.get("verdict") or {}).get("headline") != "counterexample"):
        return {"status": "error", "detail": "Model checks require a completed, writable local counterexample run."}
    result = explain_run(candidate, (store.run_dir(candidate["id"]) / "dut.v").read_text())
    # Reload to preserve unrelated fields updated during the request. Keep
    # failures visible too, matching the interactive explanation endpoint.
    latest = store.load(candidate["id"])
    latest["explanation"] = result
    store.save(latest)
    record = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "run_id": candidate["id"],
              "status": result["status"], "detail": result.get("detail"), "calls": result.get("calls"),
              "citation_check": result.get("citation_check"), "explanation": result.get("result"),
              "usefulness_review": "pending"}
    out = data_dir() / "model_checks"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{record['checked_at'].replace(':', '')}.json").write_text(json.dumps(record, indent=2))
    return record
