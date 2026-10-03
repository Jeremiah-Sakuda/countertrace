# Countertrace

Countertrace helps FPGA learners expose FIFO bugs, understand the exact failing sequence, and validate a proposed RTL repair against unchanged checks.

**Status: local feasibility demonstrated on development fixtures.** The isolated verifier, independent reference checks, counterexample replay, supplemental-check audit, repair loop, evidence bundles, control service, and web interface run locally. On October 3, authenticated NVIDIA Nemotron 3 Ultra calls produced a useful showcase explanation after prompt iterations and one repair candidate that passed all ten unchanged obligations, including three unbounded property proofs. The explanation received a Codex source/trace review; independent human review is pending. Diagnosis remains the delivery commitment. No benchmark, held-out evaluation, user result, hosted deployment, or external review is claimed. See [implementation status](docs/STATUS.md) for exactly what ran.

Built for the [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/), targeting Coding and Agentic Engineering. Submission: October 30, 2026, 1:00 p.m. EDT. Judge access must remain available through December 15.

## What it does

One bounded synchronous FIFO profile (`sync-fifo-v1`: one positive-edge clock, synchronous active-high reset, 8-bit words, depth 2 or 4):

1. **Contract.** Shows the exact behavior the checks enforce, including simultaneous operations, boundaries, and reset, with the PRD's cycle-level sampling convention. Nemotron compares a natural-language brief with the contract and flags conflicts and unsupported requests; it cannot change the contract.
2. **Diagnosis.** Admits the RTL, then runs it in an isolated container: Verilator simulation of directed and seeded tests scored by an independent reference queue, plus SymbiYosys bounded checking, unbounded proof, and reachability covers against an independent formal monitor. The first observed mismatch is shown as a compact cycle table with deterministic related events. Formal counterexamples are normalized to application cycles and replayed in simulation.
3. **Explanation.** Nemotron explains the recorded failure; every cycle, signal, and RTL-line citation is checked against the recorded evidence. The explanation never affects the verdict.
4. **Repair.** Nemotron proposes up to three patches. Each is re-admitted, must keep the interface, and is verified as a separate run against the identical frozen contract, harness, stimulus, and limits.
5. **Audit.** A named supplemental check set is scored against a reviewed fault library. The core decides which mutants are real faults; surviving faults point to the requirement the set never exercises.
6. **Evidence.** Every run exports a report and hashed manifest, and `countertrace replay` re-runs the deterministic checks without a model call.

Results keep their method: "Simulation passed for these runs", "No counterexample within N cycles", "Property proved under these assumptions", "Counterexample found", "Unresolved", "Tool error". There is no overall verified badge or percentage.

## Quick start

Requires Python 3.11+, Git, Docker (on macOS, a running colima or Docker Desktop VM that shares your home directory), and Node 20+ for the web interface. HDL tools are not installed on the host; they run only inside the pinned verifier image.

```sh
make setup        # .venv, editable install, private .env from .env.example
make image        # builds the pinned verifier image (~700 MB tool download, checksum-verified)
make test         # unit tests and negative controls, no Docker
make test-integration
make web          # builds apps/web
make serve        # http://127.0.0.1:8765
```

Command line:

```sh
countertrace verify --example showcase-overwrite-when-full
countertrace audit --check-set weak-learner-v1
countertrace survey                      # every bundled example, raw outcomes
countertrace bundle <run-id>             # evidence zip
countertrace replay <bundle.zip>         # re-run deterministic checks, compare outcomes
countertrace model-check --run-id <run-id> # explain a local failure and preserve model metadata
countertrace doctor
```

To enable Nemotron, fill `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL_ID`, and the two token limits in `.env`. Calls are refused until the limits are set. When you request interpretation, explanation, or repair, the RTL, contract, and relevant diagnostics are sent to Nebius Token Factory; do not use confidential designs.

## Trust boundaries

- The model proposes interpretation, explanation, or patches; it never authorizes a result.
- RTL executes only in a container with no network, a read-only root, dropped capabilities, bounded CPU, memory, and processes, and no environment from the host. Model credentials stay in the control service.
- Admission rejects DUT-authored assertions or assumptions, system tasks, directives, `initial` blocks, attributes, extra ports, asynchronous reset, and other constructs that could bypass the harness or make the engines disagree. The same gate applies to model patches.
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

- [Product requirements](docs/PRD.md) · [Implementation status](docs/STATUS.md) · [Milestones](docs/ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md) · [Control service API](docs/API.md) · [Development](docs/DEVELOPMENT.md) · [Deployment plan](docs/DEPLOYMENT.md)
- [Model gate](docs/MODEL_GATE.md) · [Evaluation protocol](evaluation/README.md) · [Study protocol](evaluation/STUDY.md) · [Release decision](docs/RELEASE_DECISION.md)
- [Hackathon fit review](docs/reviews/hackathon-fit.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

## License and provenance

[MIT](LICENSE). This is a new implementation begun October 1, 2026. No AKILI code has been copied. Fixtures and the fault library were authored for this project; both known-good FIFOs share an author and are not independent implementations. Tool and dependency licenses are listed in [third-party notices](THIRD_PARTY_NOTICES.md).
