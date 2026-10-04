# Countertrace

Countertrace helps FPGA learners expose FIFO bugs, understand the exact failing sequence, and validate a proposed RTL repair against unchanged checks.

**Status: working local build with a first frozen evaluation.** On October 4, a pre-registered suite of 4 controls and 8 seeded faults (half derived from an independently authored FIFO held out of prompt development) gave: diagnosis 8/8 across four defect classes with 0/4 false alarms, Nemotron repairs passing unchanged checks in 7/8 cases, and conflict detection 4/4 with 4/4 compatible briefs accepted ([report](evaluation/results/eval-v1/REPORT.md)). A second pre-registered run on fresh, harder cases (multi-line and two-bug defects, a new held-out FIFO) with the current repair agent gave diagnosis 8/8, 0/4 false alarms, repairs 8/8 including three cases where a rejected candidate's counterexample led to an accepted fix, and conflicts 3/4 with 4/4 compatible ([report](evaluation/results/eval-v2/REPORT.md)). The cases and labels were authored by the developer's coding assistant and have not been externally reviewed; no user study or hosted deployment exists yet. See [implementation status](docs/STATUS.md) for exactly what ran.

Built for the [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/), targeting Coding and Agentic Engineering. Submission: October 30, 2026, 1:00 p.m. EDT. Judge access must remain available through December 15.

## What it does

One bounded synchronous FIFO profile (`sync-fifo-v1`: one positive-edge clock, synchronous active-high reset, 8-bit words, depth 2 or 4):

1. **Contract.** Shows the exact behavior the checks enforce, including simultaneous operations, boundaries, and reset, with the PRD's cycle-level sampling convention. Nemotron compares a natural-language brief with the contract and flags conflicts and unsupported requests; it cannot change the contract.
2. **Diagnosis.** Admits the RTL, then runs it in an isolated container: Verilator simulation of directed and seeded tests scored by an independent reference queue, plus SymbiYosys bounded checking, unbounded proof, and reachability covers against an independent formal monitor. The first observed mismatch is shown as a compact cycle table with deterministic related events. Formal counterexamples are normalized to application cycles and replayed in simulation.
3. **Explanation.** Nemotron explains the recorded failure; every cycle, signal, and RTL-line citation is checked against the recorded evidence. The explanation never affects the verdict.
4. **Repair agent.** Nemotron proposes up to three patches as exact-match edits. Each is re-admitted, must keep the interface, and is verified as a separate run against the identical frozen contract, harness, stimulus, and limits.
5. **Audit.** A named supplemental check set is scored against a reviewed fault library. The core decides which mutants are real faults; surviving faults point to the requirement the set never exercises.
6. **Evidence.** Every run exports a report and hashed manifest, and `countertrace replay` re-runs the deterministic checks without a model call.

Results keep their method: "Simulation passed for these runs", "No counterexample within N cycles", "Property proved under these assumptions", "Counterexample found", "Unresolved", "Tool error". There is no overall verified badge or percentage.

## NVIDIA Nemotron on Nebius Token Factory

Every model call is a runtime call from the control service to the Nebius Token Factory OpenAI-compatible API. The model proposes; independent checks decide.

| Task | Model | Role and safeguards |
| --- | --- | --- |
| Brief interpretation, check-set proposals | `nvidia/nemotron-3-super-120b-a12b` | Flags conflicts between a plain-English brief and the fixed contract (cannot change it); proposes supplemental checks only from reviewed templates. Reasoning off by default for these tasks: 1.7–2.9 s per development brief (7.1–11.4 s with reasoning on in eval-v1). |
| Failure explanation | `nvidia/Nemotron-3-Ultra-550b-a55b` | Explains the recorded failing cycles for a learner; every cited cycle, signal, and RTL line is checked against the trace and source. Never changes the verdict. |
| Repair agent | `nvidia/Nemotron-3-Ultra-550b-a55b` | Proposes exact-match RTL edits; each candidate is re-admitted and re-verified (simulation, bounded model checking, unbounded proof, reachability) against the frozen check set, up to three attempts. |

Responses are schema-validated with one bounded retry; input/output token caps are required; per-call usage is logged and an inference-spend threshold stops new calls. Token Factory made the agent loop practical: routing quick calls to Super kept interpretation interactive, while Ultra handled trace reasoning and repairs. Verification runs on CPU in a pinned Docker image; Nebius Serverless Jobs are not used (see [feedback](docs/SUBMISSION.md#feedback-on-nebius-and-nvidia-tools)).

## Related work and what is different

LLM-assisted hardware design and repair is an active area. RTLFixer uses LLM agents with compiler feedback to fix Verilog errors; AutoChip iterates LLM-generated Verilog with compiler and simulation feedback; NVIDIA's VerilogEval and ChipNeMo benchmark and adapt LLMs for hardware design, and FVEval evaluates LLMs on formal-verification tasks; Veri-Sure and recent open-source LLM-driven formal verification studies combine generation or repair with formal checks. Mutation testing of checks (for example YosysHQ MCY) is also established.

Countertrace does not claim a new repair algorithm. Its contribution is the combination aimed at learners:

1. **The checks cannot move.** A repair counts only if a separate run with hash-identical contract, harness, stimulus, limits, and formal tasks resolves every obligation, including unbounded proofs. The model never grades its own fix, and the loop feeds each failed candidate's own counterexample back to the model.
2. **Cycle-level evidence a learner can follow.** Two independent references (a Python reference queue and a SystemVerilog formal monitor) agree on one sampling convention; the first mismatch is shown with deterministic "related events", and model explanations are checked citation by citation against that trace.
3. **Intent before verification.** A plain-English brief is compared with the fixed contract and conflicts are surfaced instead of silently changing the rules.
4. **Auditing the learner's checks, not the design.** Seeded faults score a named check set; the independent core decides which faults are real, and each miss points to the requirement the set never drives.

## Quick start

Requires Python 3.11+, Git, Docker (on macOS, a running colima or Docker Desktop VM that shares your home directory), and Node 20.19+ or 22.12+ for the web interface (Vite 8). Docker must use BuildKit (the default in current Docker) so the image picks the right toolchain architecture. HDL tools are not installed on the host; they run only inside the pinned verifier image.

```sh
make setup        # needs Python 3.11+; creates .venv and a private .env from .env.example
make image        # builds the pinned verifier image (~700 MB tool download, checksum-verified)
make test         # unit tests and negative controls, no Docker
make test-integration
make web          # builds apps/web
make serve        # http://127.0.0.1:8765
```

Command line (after `source .venv/bin/activate`, or prefix commands with `.venv/bin/`):

```sh
countertrace verify --example showcase-overwrite-when-full
countertrace audit --check-set weak-learner-v1
countertrace survey                      # every bundled example, raw outcomes
countertrace bundle <run-id>             # evidence zip
countertrace replay <bundle.zip>         # re-run deterministic checks, compare outcomes
countertrace model-check --run-id <run-id> # explain a local failure and preserve model metadata
countertrace doctor
```

To enable Nemotron, fill `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL_ID` (and optionally `NEBIUS_FAST_MODEL_ID`), and the two token limits in `.env`. Calls are refused until the limits are set. When you request interpretation, explanation, or repair, the RTL, contract, and relevant diagnostics are sent to Nebius Token Factory; do not use confidential designs.

## Trust boundaries

- The model proposes interpretation, explanation, or patches; it never authorizes a result.
- RTL executes only in a container with no network, a read-only root, dropped capabilities, bounded CPU, memory, and processes, and no environment from the host. Model credentials stay in the control service.
- Admission rejects DUT-authored assertions or assumptions, file and process system tasks, directives, `initial` blocks, attributes, extra or renamed ports without a validated interface mapping, asynchronous reset, and other constructs that could bypass the harness or make the engines disagree. The same gate applies to model patches.
- The host parses authoritative artifacts: trace files that must match the driven stimulus, SBY status files, and the elaborated property inventory (exactly 3 assertions, 1 assumption, 12 covers, all in the trusted monitor). Harness hashes are compared on every batch. Timeouts, errors, cancellation, and missing evidence never become a pass.
- Public custom uploads are disabled. The public experience uses bundled examples; `COUNTERTRACE_PUBLIC_UPLOADS_ENABLED=true` is for the owner's local test build.

## Repository layout

```text
src/countertrace/   Contract and reference model, admission, scoreboard, formal parsing,
                    runner, verification pipeline, audit, repair, model client, bundles,
                    run store, HTTP control service, CLI
verifier/           Pinned Dockerfile, in-container worker, trusted harness and formal monitor
apps/web/           React + TypeScript interface (contract, findings, repair/export, audit)
fixtures/           RTL fixtures, fault library, examples, check sets, timing fixtures
recorded/           Curated recorded runs served as labeled recorded evidence
tests/              Unit tests, negative controls, Docker integration tests
docs/               PRD, roadmap, architecture, API, status, reviews
evaluation/         Evaluation protocol; held-out cases stay local until frozen
```

## Documents

- [Product requirements](docs/PRD.md) · [Implementation status](docs/STATUS.md) · [Milestones](docs/ROADMAP.md) · [Evaluation eval-v1](evaluation/results/eval-v1/REPORT.md) · [Submission draft](docs/SUBMISSION.md) · [Release decision](docs/RELEASE_DECISION.md)
- [Architecture](docs/ARCHITECTURE.md) · [Control service API](docs/API.md) · [Development](docs/DEVELOPMENT.md) · [Deployment plan](docs/DEPLOYMENT.md)
- [Model gate](docs/MODEL_GATE.md) · [Evaluation protocol](evaluation/README.md) · [Study protocol](evaluation/STUDY.md) · [Release decision](docs/RELEASE_DECISION.md)
- [Hackathon fit review](docs/reviews/hackathon-fit.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

## License and provenance

[MIT](LICENSE). This is a new implementation begun October 1, 2026. No AKILI code has been copied. Fixtures and the fault library were authored for this project; both Countertrace FIFOs share an author. `fixtures/independent/billdmar/` is an unmodified MIT-licensed FIFO by William Mar (pinned commit `07da90c`), used as the independent evaluation implementation with attribution. Tool and dependency licenses are listed in [third-party notices](THIRD_PARTY_NOTICES.md).
