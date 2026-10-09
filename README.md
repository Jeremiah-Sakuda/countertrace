# Countertrace

**Nemotron writes hardware checks. Countertrace checks the checks.** From a plain-English specification and ports, NVIDIA Nemotron generates formal properties without seeing the golden implementation. Countertrace tests those properties before letting them judge a design.

[Open Countertrace](https://countertrace.vercel.app) · [Local build](#quick-start) · [Current evidence](docs/STATUS.md)

1. Pick a catalog module and inspect its specification and parameter settings.
2. Follow each model round through compilation, golden-reference proof, bounded trigger reachability, and mutation testing. Failures and surviving-mutant traces go back to the model.
3. Inspect the promoted properties, exact denominators, feedback, and model usage. Promotion requires at least 90% of analyzable non-equivalent mutants killed and no unresolved or invalid evidence. Mutation testing currently uses the first parameter setting.
4. For the supported FIFO, run those properties on a bundled design. A property failure becomes a confirmed defect only after the same input sequence passes the golden and fails the candidate against the independent reference.
5. Ask Nemotron for a repair. The properties and core checks stay frozen; every candidate gets a new isolated verification run. Download and replay the evidence without inference.

**Scope:** seven catalog modules; the complete bug-hunt/repair path currently supports the 8-bit synchronous FIFO at depths 2 and 4. The seven-module catalog validation used hand-written reference properties; it is not a seven-module model benchmark. Check-writing model results are development observations, with frozen held-out evaluation still pending. See [STATUS](docs/STATUS.md) for individual runs, failures, and timings. The older [FIFO evaluation](evaluation/results/eval-v2/REPORT.md) measures diagnosis and repair under hand-written checks, not the new property-writing agent.

**Deployment:** Vercel serves actual recorded evidence without a login or key. Live model calls and Docker verification run in the configured local build. Project-funded live judge access through December 15 remains pending. The hosted site does not impersonate live inference.

The [repair casebook](https://countertrace.vercel.app/#/repair), three practice labs, testbench exercise, and [facilitator desk](https://countertrace.vercel.app/#/teach) remain an educational use case for instructors and FPGA club mentors. They use recorded execution and learner-owned notes; no learning gains or adoption are claimed.

Built for the [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/), Coding and Agentic Engineering. Submission deadline: October 30, 2026, 1:00 p.m. EDT.

## The verification workbench

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
| Property generation | `nvidia/Nemotron-3-Ultra-550b-a55b` | Writes structured formal properties from the specification and ports, without golden source. The isolated golden gate and bounded feedback loop decide promotion. |
| Learning coaching | Configured Ultra | Responds to learner reasoning using server-selected recorded observations. Advisory only; validates cited edges. Hosted labs use authored hints. |
| Brief interpretation | `nvidia/nemotron-3-super-120b-a12b` | Flags conflicts between a plain-English brief and the fixed contract (cannot change it). Reasoning off by default for these tasks: 1.7 to 3.7 s per brief across development and eval-v2 briefs (7.1 to 11.4 s with reasoning on in eval-v1). |
| Failure explanation | `nvidia/Nemotron-3-Ultra-550b-a55b` | Explains the recorded failing cycles for a learner; every cited cycle, signal, and RTL line is checked against the trace and source. Never changes the verdict. |
| Repair agent | `nvidia/Nemotron-3-Ultra-550b-a55b` | Proposes exact-match RTL edits; each candidate is re-admitted and re-verified (simulation, bounded model checking, unbounded proof, reachability) against the frozen check set, up to three attempts. |

Responses are schema-validated with one bounded retry; input/output token caps are required; per-call usage is logged and an inference-spend threshold stops new calls. Routing quick calls to Super with reasoning off kept interpretation interactive (1.7 to 3.7 s per brief), while Ultra handled trace reasoning and repairs. Verification runs on CPU in a pinned Docker image; Nebius Serverless Jobs are not used (see [feedback](docs/submission/FEEDBACK.md)).

## Related work and what is different

LLM-assisted hardware design and repair is an active area. RTLFixer uses LLM agents with compiler feedback to fix Verilog errors; AutoChip iterates LLM-generated Verilog with compiler and simulation feedback; NVIDIA's VerilogEval and ChipNeMo benchmark and adapt LLMs for hardware design, and FVEval evaluates LLMs on formal-verification tasks; Veri-Sure and recent open-source LLM-driven formal verification studies combine generation or repair with formal checks. Mutation testing of checks (for example YosysHQ MCY) is also established.

Countertrace combines specification-only property generation with an inspectable quality gate: multi-parameter golden proofs, bounded trigger reachability, and equivalence-classified mutation testing. It then keeps the promoted properties frozen during FIFO bug hunting and repair, alongside independent hand-written checks. The golden reference remains a trusted dependency. This is an engineering workflow, not a first-of-kind research claim.

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
countertrace write-checks --module sync_fifo --rounds 4
countertrace verify --example showcase-overwrite-when-full
countertrace audit --check-set weak-learner-v1
countertrace survey                      # every bundled example, raw outcomes
countertrace bundle <run-id>             # evidence zip
countertrace replay <bundle.zip>         # re-run deterministic checks, compare outcomes
countertrace model-check --run-id <run-id> # explain a local failure and preserve model metadata
countertrace doctor
```

To enable Nemotron, fill `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL_ID` (and optionally `NEBIUS_FAST_MODEL_ID`), and the two token limits in `.env`. Calls are refused until the limits are set. Set `COUNTERTRACE_CHECKS_OUTPUT_TOKEN_LIMIT` for property generation. When you request interpretation, explanation, or repair, the RTL, contract, and relevant diagnostics are sent to Nebius Token Factory; do not use confidential designs.

## Trust boundaries

- The model proposes interpretation, explanation, or patches; it never authorizes a result.
- RTL executes only in a container with no network, a read-only root, dropped capabilities, bounded CPU, memory, and processes, and no environment from the host. Model credentials stay in the control service.
- Admission rejects DUT-authored assertions or assumptions, file and process system tasks, directives, `initial` blocks, attributes, extra or renamed ports without a validated interface mapping, asynchronous reset, and other constructs that could bypass the harness or make the engines disagree. The same gate applies to model patches.
- The host parses authoritative artifacts: trace files that must match the driven stimulus, SBY status files, and the elaborated property inventory (for the core FIFO monitor: exactly 3 assertions, 1 assumption, 12 covers; for generated checks: the exact compiled property inventory). The elaborated DUT must leave every input a free net: an input bit tied to a constant, aliased to another input, or driven inside the design fails integrity, so it cannot constrain its own stimulus. Harness hashes are compared on every batch. Timeouts, errors, cancellation, and missing evidence never become a pass.
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

- [Product requirements](docs/PRD.md) · [Implementation status](docs/STATUS.md) · [Milestones](docs/ROADMAP.md) · [Evaluation eval-v1](evaluation/results/eval-v1/REPORT.md) · [eval-v2](evaluation/results/eval-v2/REPORT.md) · [Repair ablation](evaluation/results/eval-v2-ablation/REPORT.md) · [Submission materials](docs/submission/README.md) · [Release decision](docs/RELEASE_DECISION.md)
- [Architecture](docs/ARCHITECTURE.md) · [Control service API](docs/API.md) · [Development](docs/DEVELOPMENT.md) · [Deployment plan](docs/DEPLOYMENT.md)
- [Model gate](docs/MODEL_GATE.md) · [Evaluation protocol](evaluation/README.md) · [Study protocol](evaluation/STUDY.md) · [Release decision](docs/RELEASE_DECISION.md)
- [Hackathon fit review](docs/reviews/hackathon-fit.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

## License and provenance

[MIT](LICENSE). This is a new implementation begun October 1, 2026. No AKILI code has been copied. Fixtures and the fault library were authored for this project; both Countertrace FIFOs share an author. `fixtures/independent/billdmar/` is an unmodified MIT-licensed FIFO by William Mar (pinned commit `07da90c`), used as the independent evaluation implementation with attribution. Tool and dependency licenses are listed in [third-party notices](THIRD_PARTY_NOTICES.md).
