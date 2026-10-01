# Implementation status

Last updated: October 1, 2026. This page records what has actually run. Everything below uses **development and showcase fixtures authored for this project**; none of it is a held-out evaluation, benchmark, user result, or external review.

## October 4 feasibility gate

| Gate item | State | Evidence |
| --- | --- | --- |
| Deterministic runner distinguishes a known-good control from a witnessed faulty design | Met on development fixtures | Survey below: 3 controls proved, 7 faults with counterexamples |
| Counterexample replayed with the specified cycle convention | Met on development fixtures | Every formal counterexample below was reproduced by the independent simulation scoreboard at the same cycle and check; the depth-2 PRD sequence and a depth-4 wraparound fixture pass as unit tests |
| Useful response from an authenticated Nemotron endpoint | **Not met** | The client is implemented and unit-tested against a mocked endpoint only. No Nebius credential is configured on the build machine. Run `countertrace model-check` after configuring `.env`. |
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

- `make test`: 46 unit tests and negative controls (admission rejections, truncated or tampered traces, solver status and cover parsing, property-inventory controls, model schema/limit/citation handling with a mocked endpoint).
- `make test-integration`: 6 Docker tests running real RTL (proved control, replayed fault, altered harness hash, cancellation, unsupported syntax, stubbed repair loop).

## Not yet done

Live Nemotron calls and their measured usefulness; Nebius Serverless Jobs (all verification runs locally in Docker); the frozen evaluation suite with an independently authored, held-out implementation; reviewer and learner recruitment; the usability study; clean-environment replays; hosted deployment and judge access; the demonstration video.
