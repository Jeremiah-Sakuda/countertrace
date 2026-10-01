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

The first build downloads about 700 MB. Later builds reuse the toolchain layer.

## Model configuration

Only the control service reads `.env`; exported variables take precedence. Set `NEBIUS_API_KEY`, `NEBIUS_BASE_URL` (for example the Token Factory OpenAI-compatible base URL shown in your account), `NEBIUS_MODEL_ID`, `COUNTERTRACE_MODEL_INPUT_TOKEN_LIMIT`, and `COUNTERTRACE_MODEL_OUTPUT_TOKEN_LIMIT`. Calls are refused until all are set. A spend limit is enforced only when per-token prices are configured; otherwise cost is reported as unavailable. Usage is appended to `.countertrace/model_usage.jsonl` without the credential.

`countertrace model-check` explains the newest recorded counterexample with one call and stores sanitized metadata in `.countertrace/model_checks/`. This is the remaining October 4 gate item.

## Recorded runs

`countertrace record <run-id> --note "..."` copies a completed run into `recorded/<run-id>/`, marks it recorded, and keeps its original timings and versions. The interface labels these as recorded runs. Re-record after changing the harness, stimulus, or model configuration.

## Documentation workflow

The requirements live in [PRD.md](PRD.md), mirrored from the [Countertrace PRD Page](https://chatgpt.com/space/page_6c532b87187881918d1a6e23def79098). Version 1.1 matches the Page's content on October 1, 2026, apart from the repository's document heading. Synchronization is manual. For a requirements change, read the latest Page, apply the agreed change, export the read-back Markdown to `docs/PRD.md`, and update the version in both. If the Page is unavailable, record the unsynchronized change explicitly. Implementation details belong in repository-only documents such as [ARCHITECTURE.md](ARCHITECTURE.md), [API.md](API.md), and [STATUS.md](STATUS.md).

Update [STATUS.md](STATUS.md) whenever something new has actually run. Distinguish unit tests, simulation, bounded checking, and unbounded proof in pull requests.

## Data boundaries

Run data lives in `.countertrace/` (ignored). `.env`, credentials, uploaded designs, waveforms, logs, and `evaluation/holdout/` are ignored, except curated evidence under `recorded/` and parser fixtures under `tests/data/`. Keep held-out labels and final regressions outside prompt-development context until the evaluation protocol permits release. Only team-owned or appropriately licensed fixtures belong in the public repository.
