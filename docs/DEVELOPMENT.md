# Development setup

## Current stage

The repository is a scaffold. It contains local diagnostics and documentation, not a running verification product. The Python package has no runtime dependencies. A TypeScript interface, control API, toolchain image, and verification worker will be added behind the first feasibility gate.

## Bootstrap

Use Python 3.11+ and Git, with `make` on macOS or Linux:

```sh
make setup
make check
make doctor
.venv/bin/countertrace doctor --json
```

`make setup` installs the editable package inside `.venv`; only the build backend may need to be downloaded. It creates `.env` only if absent. The diagnostic reports whether configuration is exported in the process environment; it deliberately does not source `.env`, contact Nebius, or print credential values. A present key is not an authenticated inference result.

If you prefer not to install anything yet, `PYTHONPATH=src python3 -m countertrace doctor` and `python3 scripts/check_workspace.py` work with the standard library.

The workspace file configures `.venv/bin/python` and tasks for setup, checks, and diagnostics. Node and npm are intended for `apps/web` later; there is no frontend package or development server yet.

## Verification prerequisites

The first milestone must select and pin a Linux worker image with Verilator, Yosys, SymbiYosys, and a solver. The image digest, tool versions, supported language subset, and replay commands belong in each evidence bundle. No image tag or solver version is designated as verified by this scaffold.

The initial machine inspection found Python 3.14.7, Node 22.22.3, npm 10.9.8, Git, and a Docker client. Its Docker daemon was unavailable and Verilator, Yosys, and SymbiYosys were absent from PATH. Re-run `make doctor` for current state. Start your existing container runtime before testing a future verifier image. Do not run untrusted RTL directly on the host as a workaround.

## Configuration

`.env.example` names the future control-service settings. Choose the actual Nebius endpoint and NVIDIA model ID from your account, then measure schema behavior, quotas, and pricing. Do not assume a populated configuration means access works. Configure model input/output token limits and a deployment spending cap before hosting inference.

Only the control service receives the model credential. Verification workers must have no application/model secrets, blocked child-process network access, a read-only verifier, and per-run scratch space. Public custom uploads remain disabled. Generated patches go through the same admission rules as input RTL.

## Documentation workflow

The requirements live in [PRD.md](PRD.md), mirrored from the [Countertrace PRD Page](https://chatgpt.com/space/page_6c532b87187881918d1a6e23def79098). Version 1.1 matches the Page's content on October 1, 2026, apart from the repository's document heading. Synchronization is manual, not automatic.

For a requirements change, read the latest Page, apply the agreed change, export the read-back Markdown to `docs/PRD.md`, and update the version in both. If the Page is unavailable, record the unsynchronized change explicitly; do not silently treat two versions as equivalent. Implementation details may remain in repository-only documentation.

Run `make check` before committing. It validates Python syntax, JSON/TOML, and local Markdown links; CI also installs the package and exercises its entry point on Python 3.11 and 3.14. These are scaffold checks, not hardware tests. Add meaningful behavioral tests alongside the actual verifier rather than placeholder passing tests.

## Data boundaries

Use `.countertrace/` for local run data. `.env`, credentials, uploaded designs, waveform output, logs, and `evaluation/holdout/` are ignored. Keep held-out labels and final regressions outside prompt-development context until the evaluation protocol permits release. Only team-owned or appropriately licensed fixtures belong in the public repository.

Do not commit run credentials, private user study details, or proprietary source. Publish evaluation fixtures and raw outcomes after the freeze and evaluation according to the declared protocol, recording provenance and any exposed holdout cases.
