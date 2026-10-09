# Development

## Prerequisites

Python 3.11+, Git, Docker, and Node 20+ with npm. On macOS, colima's default profile shares only your home directory with containers, so keep the repository (and `COUNTERTRACE_DATA_DIR`) under your home directory. HDL tools are deliberately not installed on the host: RTL runs only inside the verifier image. Do not run RTL directly on the host as a workaround.

## Setup

```sh
make setup             # .venv + editable install + private .env (never overwritten)
make image             # builds countertrace-verifier:<digest> from verifier/
make test              # unit tests and negative controls (no Docker)
make test-integration  # real RTL in the verifier image
make check             # unit tests + workspace checks + whitespace
make web               # npm install + build apps/web/dist
make serve             # control service + built interface on 127.0.0.1:8765
```

The package reads `fixtures/` and `verifier/` from the repository checkout, so use the editable install or `PYTHONPATH=src`.

For interface work, run `make serve` in one terminal and `cd apps/web && npm run dev` in another; Vite proxies `/api` to the service.

## The verifier image

`verifier/Dockerfile` pins the Debian base by digest and the OSS CAD Suite release tarball by SHA-256. The image tag is a content digest of the Dockerfile, worker, and harness, so changing any of them requires `make image`; a run against a stale image fails its harness-hash integrity check rather than producing results. Each run records the image ID and tool versions.

The first build downloads about 700 MB. Later builds reuse the toolchain layer. Build with BuildKit (the default in current Docker and in CI): it sets `TARGETARCH`, which selects the x64 or arm64 toolchain tarball. The legacy builder leaves it unset, and the Dockerfile then assumes arm64, which fails the checksum on x64 hosts.

The launcher runs the worker with the control service's numeric non-root UID/GID so Linux bind-mounted artifacts remain removable by that service. A root UID or GID is replaced with 10001; worker root is never enabled. Run the hosted service as the dedicated `countertrace` user. Network isolation, read-only mounts, dropped capabilities, and resource limits remain in effect.

## Model configuration

The control process reads `.env`; exported variables take precedence. Set `NEBIUS_API_KEY`, `NEBIUS_BASE_URL` (the Token Factory OpenAI-compatible base URL shown in your account), `NEBIUS_MODEL_ID`, `COUNTERTRACE_MODEL_INPUT_TOKEN_LIMIT`, and `COUNTERTRACE_MODEL_OUTPUT_TOKEN_LIMIT`. Calls are refused until all are set. Usage is appended to `.countertrace/model_usage.jsonl` without the credential. The inference ledger includes reservations for concurrent calls: estimated complete input (including the optional system prefix) plus the full output allowance. Configure default input/output prices; `COUNTERTRACE_MODEL_PRICES_JSON` can override them per model. This is an estimate, not a guaranteed maximum bill: tokenization, account prices, and usage missing after transport failures can differ. Compute, storage, and other processes are excluded. Without prices, cost is unavailable. Use account billing controls separately.

`countertrace model-check --run-id <run-id>` explains a completed local counterexample, attaches the result to that run for recording, and stores sanitized metadata in `.countertrace/model_checks/`. Omit `--run-id` to select the newest completed local counterexample. Read-only recorded runs and controls are rejected. HTTP/schema retries are bounded but can make multiple requests. A successful response still needs a source/trace usefulness review; record whether it was performed by a human or an assistant. See [model gate procedure](MODEL_GATE.md). The development gate was demonstrated on October 3 with Codex review; independent human validation remains pending.

## Recorded runs

`countertrace record <run-id> --note "..."` copies a completed run into `recorded/rec-<run-id>/`, marks it recorded, and keeps its original timings and versions. The interface labels these as recorded runs. Re-record after changing the harness, stimulus, or model configuration. Parent and candidate links are rewritten to recording IDs; explicitly record every related run intended for publication. Recording a parent never publishes its private candidates automatically.

For the October 4 summary-parser correction, [the recorded-evidence procedure](../recorded/README.md#corrected-derived-summaries) re-derives only affected summaries from unchanged raw inputs, retaining provenance and original model text. Do not use this procedure to disguise changed execution, prompts, or benchmark outcomes as old evidence.

## Documentation workflow

The requirements live in [PRD.md](PRD.md), mirrored from the [Countertrace PRD Page](https://chatgpt.com/space/page_6c532b87187881918d1a6e23def79098). Version 1.3 matched the Page's content on October 5, 2026, apart from the repository's document heading. Version 1.4 (October 9, 2026: model-written checks with a golden-reference gate as the lead direction) was edited in the repository only because the Page is not reachable from this workspace; copy it to the Page before relying on the Page. Synchronization is manual. For a requirements change, read the latest Page, apply the agreed change, export the read-back Markdown to `docs/PRD.md`, and update the version in both. If the Page is unavailable, record the unsynchronized change explicitly. Implementation details belong in repository-only documents such as [ARCHITECTURE.md](ARCHITECTURE.md), [API.md](API.md), and [STATUS.md](STATUS.md).

Update [STATUS.md](STATUS.md) whenever something new has actually run. Distinguish unit tests, simulation, bounded checking, and unbounded proof in pull requests.

## Data boundaries

Run data lives in `.countertrace/` (ignored). `.env`, credentials, uploaded designs, waveforms, logs, and `evaluation/holdout/` are ignored, except curated evidence under `recorded/` and parser fixtures under `tests/data/`. Keep held-out labels and final regressions outside prompt-development context until the evaluation protocol permits release. Only team-owned or appropriately licensed fixtures belong in the public repository.

## Learning evidence and coaching

`PYTHONPATH=src .venv/bin/python scripts/build_learning_evidence.py` runs all four-action six-edge paths for three depth-2 candidates in the existing isolated verifier. It checks worker completion, every expected step, harness hashes, elaborated ports, property inventory, raw trace completeness, and prefix repeatability before publishing `apps/web/public/learning/library.json` and `evidence.zip`. Rebuilding requires Docker. This is finite simulation, not a formal proof. `tests/test_learning.py` reparses every archived raw trace against the independent Python reference; the web test compares every browser reference state with those results.

The main repair lab uses `#/repair` with locally saved Markdown field notes. The case loader checks all linked records and the frozen comparison before presenting a result. The practice UI uses hash routes `#/learn/overflow`, `#/learn/exchange`, `#/learn/control`, and `#/teach`. The original setup moved to `#/examples`. Practice is saved locally; instructor imports never leave the browser. `POST /api/learn/hint` accepts a lesson, bounded action path, and explanation; the server loads its own evidence and routes advisory Ultra coaching through the existing model budget and two-call rate reservation. Vercel remains recorded-only and rejects API writes.

The generated `apps/web/src/lib/learning-manifest.json` pins the exact replay library bytes. The browser verifies SHA-256 before showing outcomes; the coaching service verifies the same digest before using source or observations. A mismatch is an error, never a pass. Development coaching checks are run with `scripts/check_learning_coaching.py <new-suffix>`; it refuses to overwrite prior evidence and freezes cases, source hash, model ID, and rubric before calls. Results remain assistant-reviewed development observations, not learner outcomes.
