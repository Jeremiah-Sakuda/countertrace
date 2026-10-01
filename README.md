# Countertrace

Countertrace helps FPGA learners expose FIFO bugs, understand the exact failing sequence, and validate a proposed RTL repair against unchanged checks.

**Status: workspace scaffold.** The PRD and development tooling are ready. RTL verification, Nemotron inference, repair, and the web application are not implemented yet. No benchmark, proof, or user-study result is claimed.

Built for the [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/), targeting Coding and Agentic Engineering. Submission: October 30, 2026, 1:00 p.m. EDT. Judge access must remain available through December 15.

## Start here

- [Product requirements](docs/PRD.md) — scope, contract, acceptance targets, and judging requirements.
- [Development setup](docs/DEVELOPMENT.md) — local commands and toolchain status.
- [Milestones](docs/ROADMAP.md) — the October 4 feasibility gate and subsequent decisions.
- [Architecture](docs/ARCHITECTURE.md) — model, control service, and verifier boundaries.
- [Hackathon fit review](docs/reviews/hackathon-fit.md) — adopted review findings.

## Local setup

Requires Python 3.11 or newer and Git. The scaffold has no runtime package dependencies. Installation may download the Python build backend.

```sh
make setup
make check
make doctor
```

`make setup` creates `.venv` and a private, ignored `.env` from `.env.example` without replacing an existing file. `make doctor` reports local prerequisites; it does not make a model call, run a hardware check, or validate account access. Missing future verification tools are reported honestly and do not prevent working on the scaffold.

For a dependency-free check before installation:

```sh
PYTHONPATH=src python3 -m countertrace doctor --json
python3 scripts/check_workspace.py
```

Open `Countertrace.code-workspace` in a compatible editor for the Python interpreter and workspace tasks. There is no web development server yet.

## Planned workflow

Existing RTL and intended behavior → reviewed contract → independent checks → counterexample → proposed patch → unchanged checks → reproducible evidence.

The initial profile is one synchronous FIFO with 8-bit data and depth 2 or 4. Existing user testbenches, arbitrary SystemVerilog, multiple clocks, and commercial sign-off are outside the MVP. The audit evaluates named supplemental checks, not an uploaded test suite.

NVIDIA Nemotron inference through Nebius Token Factory is planned for intent interpretation, trace explanation, and optional repair. Verilator and a pinned Yosys/SymbiYosys solver flow will supply independent evidence. CPU execution on Nebius Serverless Jobs is preferred after latency and account access are measured. No sponsor service has been exercised by this scaffold.

## Repository layout

```text
src/countertrace/       Python package and local environment diagnostic
apps/web/              TypeScript interface boundary (implementation pending)
verifier/              Trusted harness and pinned worker boundary (pending)
fixtures/              Development, showcase, and timing fixtures
evaluation/            Evaluation protocol; held-out cases remain local until frozen
docs/                  PRD, architecture, roadmap, and review decisions
scripts/               Workspace validation
.github/workflows/     Scaffold checks and installation smoke test
```

## First milestone

By October 4, distinguish a witnessed faulty FIFO from a known-good control, replay its counterexample with the specified cycle convention, and obtain a useful response from an authenticated Nemotron endpoint. Preserve commands, versions, evidence, and timings. The environment diagnostic is not this milestone.

## License and provenance

[MIT](LICENSE). This is a new implementation begun October 1, 2026. No AKILI code has been copied. Attribute third-party fixtures and tool licenses before adding them; the MIT license does not replace dependency licenses. See [third-party notices](THIRD_PARTY_NOTICES.md).
