# Implementation status

Last updated: October 1, 2026. This page records what has actually run. Everything below uses **development and showcase fixtures authored for this project**; none of it is a held-out evaluation, benchmark, user result, or external review.

## October 4 feasibility gate

| Gate item | State | Evidence |
| --- | --- | --- |
| Deterministic runner distinguishes a known-good control from a witnessed faulty design | Met on development fixtures | Survey below: 3 controls proved, 7 faults with counterexamples |
| Counterexample replayed with the specified cycle convention | Met on development fixtures | Every formal counterexample below was reproduced by the independent simulation scoreboard at the same cycle and check; the depth-2 PRD sequence and a depth-4 wraparound fixture pass as unit tests |
| Useful response from an authenticated Nemotron endpoint | **Not met** | An explicit showcase model check returned `unavailable` with zero calls because `NEBIUS_API_KEY` is missing. The owner is not signed in to Nebius. Account model availability, prices, schema behavior, and usefulness remain unverified. |
| Verifier image and toolchain pinned | Met | Debian base digest and OSS CAD Suite `2026-09-30` tarball SHA-256 in [verifier/Dockerfile](../verifier/Dockerfile) |

The gate is therefore **not yet passed**: the model response is outstanding.

## Environment of the recorded results

- Machine: Apple M3 Pro, macOS 26.6.2, Docker 29.5.2 in a colima VM (aarch64, 4 vCPU, 8 GiB).
- Verifier image `countertrace-verifier:7d82f4b2482a24f2`, image ID `sha256:a121730b676386b0ee65267070e85db6e1ee7e04885ee2efcba3e6d51ee5a017`.
- Verilator 5.053 (rev v5.052-258-ga419e9157), Yosys 0.69+158, SymbiYosys from OSS CAD Suite 2026-09-30. Engines: `abc bmc3` (bounded, depth 24), `abc pdr` (unbounded), `smtbmc yices` (cover, depth 24).
- Container limits: no network, read-only root, all capabilities dropped, 4 CPUs, 4 GiB, 256 processes. Warm image; times are wall-clock on one machine and are not latency promises.

## Bundled example survey

Command: `countertrace survey` (October 1, 2026). Each example runs 15 (depth 2) or 14 (depth 4) named simulation tests, 7 or 6 directed and 8 seeded, plus bounded, unbounded, and cover tasks in two concurrent worker batches.

| Example | Split | Depth | Author intent | Headline | Proof | Reachability | Simulation finding | Formal finding | Replay | First finding (s) | Total (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| showcase-overwrite-when-full | showcase | 4 | faulty | counterexample | counterexample, unresolved | bounded_pass | read_data@6 (fill_drain) | full_flag@5 | reproduced | 3.57 | 6.91 |
| good-count-d4 | showcase | 4 | correct | no_counterexample | proved | bounded_pass | — | — | — | — | 4.88 |
| good-count-d2 | development | 2 | correct | no_counterexample | proved | bounded_pass | — | — | — | — | 3.33 |
| good-wrapbit-d4 | development | 4 | correct | no_counterexample | proved | bounded_pass | — | — | — | — | 11.46 |
| dev-full-exchange | development | 4 | faulty | counterexample | counterexample, unresolved | bounded_pass | full_flag@6 (random_s8) | full_flag@5 | reproduced | 3.31 | 6.38 |
| dev-empty-bypass | development | 2 | faulty | counterexample | counterexample, unresolved | bounded_pass | empty_flag@1 (prd_sequence) | empty_flag@1 | reproduced | 3.31 | 6.63 |
| dev-reset-keeps-wrptr | development | 4 | faulty | counterexample | counterexample, unresolved | bounded_pass | read_data@2 (random_s1) | read_data@2 | reproduced | 3.31 | 6.64 |
| dev-wrapbit-full-early | development | 4 | faulty | counterexample | counterexample, unresolved | bounded_pass | full_flag@3 (fill_drain) | full_flag@3 | reproduced | 3.31 | 6.64 |
| dev-wrapbit-read-wrap-lost | development | 4 | faulty | counterexample | counterexample, unresolved | bounded_pass | empty_flag@8 (learner_basic) | empty_flag@5 | reproduced | 3.31 | 6.63 |
| dev-wrapbit-duplicate | development | 4 | faulty | counterexample | counterexample, unresolved | bounded_pass | read_data@3 (random_s3) | empty_flag@3 | reproduced | 3.57 | 6.9 |

"Proof: counterexample, unresolved" means the solver found a counterexample for one core property and stopped; the other properties are reported unresolved, not passed. Both known-good implementations were written by the same author, so they are not independent implementations in the PRD's sense.

## Supplemental-check audit

Command: `countertrace audit --check-set weak-learner-v1` against fault library `audit-v1` (7 mutants of `fifo_count.v`, depth 4).

| Check set | Valid faults (core) | Killed by set | Survived | Equivalent (proved) | Unresolved | Invalid |
| --- | --- | --- | --- | --- | --- | --- |
| weak-learner-v1 (deliberately weak) | 6 | 3 | 3 | 1 | 0 | 0 |
| core-mirror-v1 (comparison) | 6 | 6 | 0 | 1 | 0 | 0 |

Survivors of the weak set and the requirement each targets, which the set never drives: `count-overwrite-when-full` (write while full), `count-full-exchange` (read and write while full), `count-empty-bypass` (read and write while empty). The mandatory core witnessed all six valid faults. `count-equivalent-compare` was proved equivalent under the contract for DEPTH=4 and is reported separately. These counts describe the named check sets only.

## Repair

The bounded repair loop, re-admission, interface checks, and frozen-check-set comparison are implemented and exercised by an integration test that **stubs the model** with fixed candidates (rejected interface change → failing candidate → correct candidate). No model-generated repair has been attempted. The primary-versus-diagnosis release decision remains open.

## Reproducibility

`countertrace bundle <run>` exports a hashed evidence bundle; `countertrace replay <bundle.zip>` re-ran the showcase bundle on the same machine and matched every obligation status and finding with an identical frozen check set. Clean-environment replays (three bundles, twice each) have not been performed.

## Tests

- `make check`: 52 unit tests and negative controls, Python/JSON/TOML validation, documentation links, and whitespace checks pass. New tests cover opt-in model directives, attaching a model-check explanation to a local run for recording, rejection of controls/read-only recordings/missing runs, and the worker's non-root UID/GID selection. Model tests still use mocked endpoints.
- `make test-integration`: 7 Docker tests running real RTL (proved control, replayed fault, altered harness hash, cancellation, unsupported syntax, stubbed repair loop, weak-set audit). Rerun after the worker identity fix: all seven passed locally in 59.34 seconds.

## Interface and recorded runs

The web interface builds with no TypeScript errors and was checked in a browser against the local service: contract setup, a live run from acceptance to finding, the showcase finding and cycle table, a clean control, the audit result and learner exercise, bundle download, model-unavailable states, and a 375 px layout. No screen-reader testing has been done. Three runs are recorded in `recorded/` (showcase fault, known-good control, weak-set audit); the recorded showcase bundle replayed with matching outcomes.

## Not yet done

Live Nemotron calls and their measured usefulness; Nebius Serverless Jobs (all verification runs locally in Docker); the frozen evaluation suite with an independently authored, held-out implementation; reviewer and learner recruitment; the usability study; clean-environment replays; hosted deployment and judge access; the demonstration video.

## October 1 follow-up preparation

- The model gate now accepts `--run-id` and attaches its explanation result to the local run, so a later recording can contain it. The generic model prefix is blank; Llama-specific reasoning instructions must be explicitly configured for a compatible endpoint. Public-catalog endpoint/model candidates and input/output caps of 16,384/4,096 are in the ignored local `.env`; the API key and account billing remain absent. Report timestamp: `2026-10-02T01:27:57Z` (October 1 EDT), run `20261001-193038-ver-de51cd`, status `unavailable`, no calls. No showcase recording was replaced and no real repair was attempted.
- A MIT-licensed external FIFO candidate attributed to William Mar is quarantined in ignored `evaluation/holdout/`, pinned and hashed without reading its RTL into development context. Contract compatibility and admission are pending; it does not yet count as an independent control. See [candidate review](../evaluation/INDEPENDENT_FIXTURE.md).
- Recruitment drafts and a three-person study protocol are prepared in [STUDY.md](../evaluation/STUDY.md); nobody has been contacted or enrolled. The [release decision record](RELEASE_DECISION.md) retains diagnosis as the commitment, with primary scope pending real repair evidence.
- Caddy 2.11.4 validated the deployment Caddyfile locally in an offline container. No VM, funding, DNS/TLS, systemd deployment, or logged-out public journey has been tested. The [deployment plan](DEPLOYMENT.md) documents a proposed $300 budget before tax; spending approval is pending.
- Inspection of [Linux CI on the preceding implementation](https://github.com/Jeremiah-Sakuda/countertrace/actions/runs/36941347402) found six integration errors during artifact cleanup: files created by the image's UID 10001 were not removable by the host runner. The launcher now selects the service's non-root UID/GID, with a non-root fallback for root callers, while preserving worker isolation. Current Linux results are published in the repository's [Checks workflow](https://github.com/Jeremiah-Sakuda/countertrace/actions/workflows/ci.yml); macOS results alone do not establish Linux ownership behavior.
