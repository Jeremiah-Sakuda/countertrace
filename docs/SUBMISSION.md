# Devpost submission draft

Draft text for the Devpost form. Every number is backed by a committed record: [eval-v1 results](../evaluation/results/eval-v1/results.json), [development evidence](evidence/2026-10-04-development/), and [STATUS](STATUS.md). Replace nothing with unmeasured claims.

## Project name and tagline

**Countertrace** — find the exact cycle where your FIFO breaks, see why, and check a fix against checks that cannot move.

## Track

Coding and Agentic Engineering. Countertrace is a developer tool built around an agent that reads hardware code, runs it in a simulator and a formal verifier, and writes and re-tests RTL repairs, with Nemotron on Nebius Token Factory proposing and explaining, and independent checks deciding.

## Text description

### The problem

Students and junior FPGA developers write small queues (FIFOs) that pass their own tests and then fail in hardware, usually at a boundary: a write while full, a read while empty, a read and write in the same cycle, a second reset, or pointer wraparound. Their testbenches rarely drive those cases, and when something fails, a waveform does not say which requirement broke or why. AI coding assistants make this worse in one specific way: they will happily "fix" the code and declare success without any independent check.

### What Countertrace does

1. **Contract.** You pick a FIFO and read the exact, versioned behavior it will be held to, including simultaneous operations and reset, at the cycle level. Nemotron 3 Super reads your plain-English description and flags where it conflicts with the contract (for example, "overwrite the oldest byte when full") instead of silently changing the rules.
2. **Diagnosis.** The RTL runs in an isolated container (no network, no credentials): Verilator simulation of 14–15 directed and seeded tests scored by an independent reference queue, plus SymbiYosys bounded model checking, unbounded proof (PDR), and reachability covers against an independent formal monitor. Countertrace shows the first failing cycle as a table — inputs, what the contract accepts, the expected queue, and what the design actually output — plus deterministic evidence such as "the word you lost was accepted at cycle 1; the word you got was offered at cycle 5 while full and should have been ignored." Formal counterexamples are replayed in simulation to confirm both engines agree.
3. **Explanation.** Nemotron 3 Ultra explains the recorded failure for a learner. Every cycle, signal, and RTL line it cites is checked against the recorded trace and source; invalid citations are flagged. The explanation never changes the verdict.
4. **Repair agent.** Nemotron 3 Ultra proposes up to three RTL patches. Each one is re-admitted (no assertions, assumptions, system tasks, or interface changes), runs as a new verification against the identical frozen contract, harness, stimulus, and limits, and passes only if every obligation resolves — including unbounded proofs — with matching hashes. The model can never mark its own fix as correct.
5. **Check-quality audit.** Countertrace seeds reviewed bugs into a correct FIFO and shows which ones a named set of learner-style checks misses, and which requirement each miss points to. The independent core still catches every real bug.
6. **Evidence.** Every run exports a hashed bundle; `countertrace replay` re-runs the deterministic checks with no model call.

Results keep their method: "Simulation passed for these runs", "No counterexample within 24 cycles", "Property proved under these assumptions", "Counterexample found", "Unresolved". There is no overall "verified" badge.

### Results so far

First frozen evaluation (October 4, 2026, one run; [report](../evaluation/results/eval-v1/REPORT.md)). The model configuration and prompts were frozen before the cases were written, and the case file's hash was committed before the run. Half of the eight bugs were seeded into an independently authored, MIT-licensed FIFO that was never used while developing prompts.

| Measure | Result |
| --- | --- |
| Bugs found (simulation and formal, counterexamples replayed) | 8 / 8, across reset, boundaries, simultaneous operations, ordering/wraparound |
| False alarms on correct designs | 0 / 4 (all four proved for every core property) |
| Nemotron repairs that passed the unchanged checks | 7 / 8, six on the first candidate |
| Conflicting briefs flagged / compatible briefs accepted | 4 / 4 and 4 / 4 |
| Explanations with only valid citations | 7 / 8 (one cited a non-signal) |
| Model cost for the whole evaluation | about $0.40 at list prices (37 requests) |

The one failed repair ran out of output tokens rewriting a whole file. Repairs are now exact-match edits, a failed candidate's own counterexample is fed back to the model, and replies cut off at the output limit retry with reasoning off.

A second pre-registered evaluation ([eval-v2](../evaluation/results/eval-v2/REPORT.md)) tested that agent on fresh, harder cases: a new FIFO never used in prompt development, multi-line bugs, and designs with two independent bugs.

| Measure | eval-v2 |
| --- | --- |
| Bugs found / false alarms | 8 / 8 and 0 / 4 |
| Repairs that passed the unchanged checks | 8 / 8 (5 first candidate; 3 needed a second or third after a rejected candidate's counterexample was fed back) |
| Conflicting / compatible briefs | 3 / 4 and 4 / 4 (the miss, "assert full one entry early", led to a new flag-meaning topic) |
| Model cost | about $0.24 (32 requests) |

In one two-bug case the first candidate fixed one bug and was rejected by the unchanged checks; the counterexample it produced led the next candidate to fix both. That run is included as a recorded example. The evaluation cases were written by the developer's coding assistant and have not yet been reviewed independently.

### Related work and what is different

LLM-assisted hardware design and repair is an active area. RTLFixer uses LLM agents with compiler feedback to fix Verilog errors; AutoChip iterates LLM-generated Verilog with compiler and simulation feedback; NVIDIA's VerilogEval and ChipNeMo benchmark and adapt LLMs for hardware design, and FVEval evaluates LLMs on formal-verification tasks; Veri-Sure and recent open-source LLM-driven formal verification studies combine generation or repair with formal checks. Mutation testing of checks (for example YosysHQ MCY) is also established.

Countertrace does not claim a new repair algorithm. Its contribution is the combination aimed at learners:

1. **The checks cannot move.** A repair counts only if a separate run with hash-identical contract, harness, stimulus, limits, and formal tasks resolves every obligation, including unbounded proofs. The model never grades its own fix, and the loop feeds each failed candidate's own counterexample back to the model.
2. **Cycle-level evidence a learner can follow.** Two independent references (a Python reference queue and a SystemVerilog formal monitor) agree on one sampling convention; the first mismatch is shown with deterministic "related events", and model explanations are checked citation by citation against that trace.
3. **Intent before verification.** A plain-English brief is compared with the fixed contract and conflicts are surfaced instead of silently changing the rules.
4. **Auditing the learner's checks, not the design.** Seeded faults score a named check set; the independent core decides which faults are real, and each miss points to the requirement the set never drives.

### How NVIDIA Nemotron and Nebius Token Factory are used

All model calls are runtime calls to the Nebius Token Factory OpenAI-compatible API from the control service:

| Task | Model | Why this tier |
| --- | --- | --- |
| Brief interpretation, check-set proposals | `nvidia/nemotron-3-super-120b-a12b` | Interactive, reasoning off: 1.7–2.9 s per development brief (Ultra with reasoning took up to 72 s; all tiers were 6/6 on these briefs) |
| Failure explanation | `nvidia/Nemotron-3-Ultra-550b-a55b` | Needs careful reasoning over trace tables and RTL |
| Repair proposals | `nvidia/Nemotron-3-Ultra-550b-a55b` | Must reason about a failing transaction and keep the interface intact |

Every response is schema-validated with one bounded retry, input and output token caps are required before any call, usage is recorded per call, and an inference-spend threshold stops new calls. Verification never runs on the model's say-so.

### How it was built

New implementation started October 1, 2026 (no prior code). Python control service (standard library only), React + TypeScript interface, a pinned Docker verifier image (Debian digest + OSS CAD Suite 2026-09-30 by SHA-256: Verilator 5.053, Yosys 0.69, SymbiYosys, ABC, Yices), and hand-authored reference monitors. Unit tests, negative controls (altered harness, cancellation, unsupported syntax, zero properties), Docker integration tests, and clean-runner bundle replays run in GitHub Actions.

### Limits

One synchronous FIFO profile (8-bit, depth 2 or 4). Bundled examples only in the public build; arbitrary uploads are a local-only option. Two-state semantics; no timing, X-propagation, or silicon claims. Proofs hold only for the stated parameters and assumptions. Evaluation cases and labels were authored by the developer's coding assistant and have not been externally reviewed; no user study has been run yet.

## Testing instructions

**Hosted demo:** pending (a Nebius VM is planned; see [DEPLOYMENT.md](DEPLOYMENT.md)). Until it exists, judges can run the full test build locally:

1. Install Python 3.11+, Git, Docker, and Node 20+. On macOS, run Docker in a VM that shares your home directory (colima or Docker Desktop).
2. `git clone https://github.com/Jeremiah-Sakuda/countertrace && cd countertrace && make setup && make image && make web`
3. `make serve`, then open http://127.0.0.1:8765.
4. Open **Runs** → the recorded showcase ("Queue that overwrites when full"): the first failing cycle, Nemotron's explanation with clickable cycle citations, and the accepted one-line repair. No API key is needed to inspect recorded evidence.
5. Open **Contract setup**, pick an example, accept the contract, and run it live (about 10–25 s on a laptop). Try the known-good control for comparison.
6. Open **Check-quality audit** and run `weak-learner-v1` to see which seeded bugs a typical learner check set misses.
7. Live Nemotron calls need your own Token Factory key in `.env`; the hosted demo will not require one.
8. `countertrace replay <bundle.zip>` re-runs any exported evidence bundle without a model call.

## Feedback on Nebius and NVIDIA tools

Observed during development on October 3–4, 2026:

1. **Reasoning tokens exhaust structured-output budgets.** Nemotron 3 Ultra spent the entire `max_tokens` budget before emitting the required JSON on several requests (development: two explanation requests at 1,800 tokens, one repair at 4,000, one explanation at 4,096; evaluation: 12 repair requests at 4,000 and 2 explanation requests at 4,096). We found that `chat_template_kwargs: {"enable_thinking": false}` works on Token Factory for Nemotron 3 and now retry cut-off replies that way, but it is not documented in the catalog or cookbook. Suggestion: document the switch and a per-request reasoning budget, and make `finish_reason` distinguish reasoning exhaustion. The Llama-Nemotron "detailed thinking off" convention does not carry over.
2. **Latency variance on Ultra.** Two brief-interpretation requests of about 500 input and 1,700–1,800 output tokens took 66 s and 72 s; four similar requests minutes later took 9.5–16 s. Nemotron 3 Super handled the same task in 4.7–9 s with identical results on our development briefs, and 1.7–2.9 s with reasoning off. Suggestion: publish expected latency ranges per model and surface queueing time in response headers.
3. **Inconsistent model ID casing.** The catalog lists `nvidia/Nemotron-3-Ultra-550b-a55b`, `nvidia/nemotron-3-super-120b-a12b`, and `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. Consistent naming would prevent configuration errors.
4. **Pricing and credits are hard to see programmatically.** We estimated spend from cookbook list prices ($1/$3 per million tokens for Ultra) because the API exposes no price or remaining-credit information, and we could not confirm how hackathon credits apply. A balance/usage endpoint would let applications enforce real budgets.
5. **Serverless Jobs fit for interactive verification (documentation only).** The documented multi-minute startup and one-hour minimum timeout make per-run Jobs a poor fit for a 120-second interactive target, so verification runs on a CPU host with Docker. A warm-pool or sub-minute job mode would make Jobs usable for interactive agent loops. We did not run Jobs, so this is based on the documentation.
6. **Instruction following.** Nemotron 3 Ultra followed the citation format well (7 of 8 evaluation explanations had only valid citations; one cited `queue` as a signal) but did not fully follow an instruction to avoid stating unobserved internal register values.

## Video

Not yet recorded. See [DEMO.md](DEMO.md).
