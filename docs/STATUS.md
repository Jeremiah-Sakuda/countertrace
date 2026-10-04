# Implementation status

Last updated: October 4, 2026. This page records what has actually run. The October 4 section reports the first frozen evaluation (eval-v1), which includes an independently authored FIFO held out of prompt development. Everything else uses **development and showcase fixtures authored for this project**. No user study or external review has happened.

## October 4: repair-loop and quota review

An internal review of commit `088840d` recorded the open findings below.

Verified open findings: the feedback-off ablation retains failure summaries and stale trace attribution; an optional system prefix is omitted from token-cap/reservation estimates; and concurrent requests can bypass the per-visitor active-run check. These findings do not establish a false hardware acceptance. The new submission drafts also need latency, citation-example, platform-role, and evaluation-caveat corrections. Free access to live model features and the public video remain submission gaps; a working test build is allowed, and Nebius Cloud hosting is optional. Learner/external review is a score-strengthening opportunity, not an official hackathon entry requirement; the PRD's separate internal acceptance targets still need consistent treatment in release decisions.

The current UI was inspected in a browser at 1280 × 720. Fresh `make check` (73 tests), the web regression, TypeScript checking, and production build passed. GitHub CI for `088840d` passed all jobs, including Docker integration and two clean-replay jobs. Only review documentation changed; no new paid inference or product fixes were performed in this pass.

## October 4 (final): review fixes

Fixes: repair prompts no longer attribute an old finding to a new candidate; 429 errors fall back a tier; only a run's starter can cancel it; a repair counts as six requests against the hourly quota; covers are labeled environment reachability; variable declaration initializers are rejected; recorded Super interpretations for two examples are visible without a key; claim corrections (feedback causation, bounded label, stale documents); interface fixes (recorded interpretation, neutral unresolved note with a gloss, proved-count hero, page titles, accept feedback, ticking elapsed time, audit exercise that no longer reveals its answer). `make check` passes 73 tests; integration passes 7/7.

## October 4 (latest): admission hardening and repair ablation

- **Admission hardening** after a judge admitted five constructs in real pipeline runs (none produced a false pass; the second engine or a tool error caught each): clock-name shadowing and port redeclaration, hidden continuation ports (`input wire a, b`), delays, non-edge or qualified event controls, `wait`, `edge`, `defparam`, `inout`, hierarchical references, and assignments to inputs are now rejected, and the elaborated DUT ports are checked against an interface mapping. Negative-control tests cover each.
- **Bounded-check label** now states 23 cycles for 24 solver steps.
- **Repair ablation** ([report](../evaluation/results/eval-v2-ablation/REPORT.md)) on the frozen eval-v2 suite: Super 8/8, Nano 6/8, Ultra without counterexample feedback 7/8, failing only the two-bug case that feedback solved.
- **Cost control:** worst-case spend reservation per in-flight call and one fallback to the fast tier on network or 5xx errors, both tested.
- **Interface:** repair timeline with the fed-back counterexample, honest rejected-candidate wording, code ligatures off, ledger and audit-exercise fixes.

## October 4 (later): review fixes and eval-v2

An internal review found an admission bypass, repair-loop gaps, and documentation errors. Fixed and verified:

- **Admission bypass closed.** Code hidden by `// /*` … `// */` passed the old two-regex comment stripper; one ordered lexical pass now handles comments and strings, with regression tests.
- **Repair agent.** A failed candidate's own counterexample and diff drive the next proposal. Replies cut off at the output limit retry with Nemotron 3 reasoning off (`chat_template_kwargs: {"enable_thinking": false}`, verified on Token Factory). Interactive tasks default to reasoning off: Super interpretation 1.7–3.3 s on development briefs.
- **Soundness.** Frozen check sets record the formal tasks that ran; the audit path applies admission, port, and property-inventory checks; the formal stage reports an error when its tasks error.
- **eval-v2** ([report](../evaluation/results/eval-v2/REPORT.md)), pre-registered on fresh cases including a new held-out registered-flags FIFO, multi-line bugs, and two-bug cases: diagnosis 8/8, 0/4 false alarms, **repair 8/8** (5 first candidate; F1, F2, and F6 needed further candidates after rejections; an exploratory reduced-feedback run failed only F6 and passed F1 and F2 first time; it was not a clean control, so it does not show that feedback caused the F6 fix), interpretation 3/4 conflicts and 4/4 compatible, about $0.24. The one interpretation miss led to a new `flags` topic, validated only on development briefs.
- **Recorded iteration.** `rec-20261004-010137-ver-dd43e0` (eval-v2 F6) shows candidate 1 rejected by the unchanged checks and candidate 2 accepted.
- **Interface.** Concrete landing hero with a data-driven showcase tour, probable-origin line derived from the trace, candidate diff and before/after obligations, runs ledger cleanup, audit exercise before the answer, readable screen-reader labels, mobile cycle table (browser-checked at desktop and 375 px; no screen-reader testing).
- **Setup.** Make targets use `.venv` and stop on Python below 3.11; `.env.example` carries the documented endpoint, model IDs, caps, and prices.

## October 4: first frozen evaluation and follow-ups

**Evaluation eval-v1** ([report](../evaluation/results/eval-v1/REPORT.md), [raw results](../evaluation/results/eval-v1/results.json)). The configuration was frozen first (models, prompt hashes, budgets, verifier digest, stimulus, scoring), then the cases (SHA-256 committed before the run). Four controls and eight faulty cases span two Countertrace implementations and one independently authored MIT FIFO by William Mar, admitted through a validated interface mapping and held out of prompt development. One run:

| PRD target | Bar | eval-v1 |
| --- | --- | --- |
| Diagnosis | ≥6/8, ≥4 classes | 8/8, four classes; every formal counterexample replayed in simulation |
| Honest conclusions | 0 false alarms on 4 controls | 0/4; all four controls proved for all three core properties |
| Repair | ≥5/8 within three candidates | 7/8 (6 on the first candidate); the one failure was output exhaustion |
| Interpretation | ≥3/4 conflicts, ≥3/4 compatible | 4/4 and 4/4 on Nemotron 3 Super |
| Explanation citations | Actual signals and cycles | 8/8 schema-valid; 7/8 with only valid citations (E6 cited `queue`); assistant review 2/2 on all rubric items |

All cases, labels, and briefs were authored by the coding assistant after the freeze, and explanation review was by the assistant, so this is not independent validation. 37 requests, about $0.40 at list prices.

**Follow-ups, validated on development cases only (not eval-v1):**

- *Edit-based repair.* All eval-v1 repair failures were `finish_reason: length` on full-file rewrites, and full-file repairs dropped comments including the external author's header. Repairs are now exact-match find/replace edits applied by the host. Five development faults: 5/5 passed on the first candidate with one-line diffs and comments intact.
- *Model routing.* Interpretation and check proposals use Nemotron 3 Super; explanation and repair use Ultra. On six development briefs Ultra, Super, and Nano were each 6/6; Super took 4.7–9 s versus 9.5–72 s on Ultra, and 1.7–2.9 s with reasoning off (1.9–3.3 s after the flags topic; 2.3–3.7 s on eval-v2 briefs) ([raw reports](evidence/2026-10-04-development/)).
- *Explanation prompt.* Now states the exact configuration after one development explanation misstated DEPTH. Three further development faults were explained correctly.
- *Spend control.* Prices ($1/$3 per million, Ultra list) and a $20 inference threshold are configured in the local `.env`; account balance and credit expiry remain unverified.
- *Recorded showcase refreshed.* `rec-20261004-003607-ver-4cc749` holds a one-request Ultra explanation (18 valid citations, reviewed by the assistant against the trace) and a first-candidate one-line repair (`rec-20261004-003622-ver-d88ef8`) that passed all ten unchanged obligations. The October 1/3 showcase pair was retired from `recorded/`; its evidence remains in [the model-gate record](evidence/model-gate-2026-10-03.json).
- *Clean-environment replay.* A CI job on two fresh x64 runners builds the pinned image and replays three recorded bundles; on October 4 all six replays matched with no model call.


## October 4 feasibility gate

| Gate item | State | Evidence |
| --- | --- | --- |
| Deterministic runner distinguishes a known-good control from a witnessed faulty design | Met on development fixtures | Survey below: 3 controls proved, 7 faults with counterexamples |
| Counterexample replayed with the specified cycle convention | Met on development fixtures | Every formal counterexample below was reproduced by the independent simulation scoreboard at the same cycle and check; the depth-2 PRD sequence and a depth-4 wraparound fixture pass as unit tests |
| Useful response from an authenticated Nemotron endpoint | Met on the development showcase, October 3; eval-v1 explanations October 4 | Nemotron 3 Ultra explanation accepted after source/trace review by Codex, with all four rubric items scored 2/2. Six checks and seven requests included failures and prompt tuning; independent human review remains pending. See the evidence below. |
| Verifier image and toolchain pinned | Met | Debian base digest and OSS CAD Suite `2026-09-30` tarball SHA-256 in [verifier/Dockerfile](../verifier/Dockerfile) |

The feasibility gate is met on development evidence. This does not establish evaluation performance or authorize the primary repair release. Independent technical review and learner validation remain outstanding.

## October 3 authenticated model evidence

The account catalog accepted authentication and listed Ultra, Super, Nano, and Lightning Nemotron IDs. Calls used `nvidia/Nemotron-3-Ultra-550b-a55b` at the US Central Token Factory endpoint with configured input/output caps of 16,384/4,096 tokens and a blank system prefix.

Six model checks made seven explanation requests on the existing showcase. Preserve these as development prompt iterations, not a one-shot success rate:

| Check (UTC) | Outcome of source/trace review |
| --- | --- |
| 20:39:52 | Correct cause; rejected unsupported claim that passing checks excluded full conditions. |
| 20:42:13 | Both requests exhausted the old internal 1,800-output-token cap before valid JSON. |
| 20:42:58 | Correct cause; result limits ambiguously grouped unresolved formal checks with witnessed failures. |
| 20:45:21 | Correct cause; the application cut the limits text at 600 characters. |
| 20:47:58 | Rejected an impossible internal `wr_ptr=4` claim for a two-bit pointer. |
| 20:49:10 | Accepted for usefulness: correct overwrite cause, byte values, failing transactions, and method-specific limits; 16 valid citations, zero invalid citations or uncited steps. |

The final check took 5,350 ms and used 2,615 input / 1,858 output tokens. Its numeric internal pointer/address statements are inferred from RTL, not sampled trace observations; the reviewer checked them against reset, pointer width, and the four preceding writes. The added prompt instruction to avoid unobserved internal numeric values was not fully followed. Citation acceptance is therefore not a semantic correctness guarantee. The four 2/2 scores are **Codex assistant review, not independent human or learner evidence**.

The client now supplies actual method/check outcomes, uses the configured output cap, and preserves complete limits text. All six reports, review notes, request metadata, the final prompt/hash, and the repair outcomes are in [the evidence record](evidence/model-gate-2026-10-03.json). Truncated responses retain failure metadata, not full raw generated text.

Across explanation and repair: **9 chat requests, 20,045 input tokens, 20,572 output tokens**. At the [public cookbook prices](https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/nemotron3-ultra-550b-a55b.md) of $1/$3 per million input/output tokens, the estimate is **$0.081761**. Actual account pricing, applied credits, balance, and expiry are unverified. The owner reports claiming credits; no top-up or VM was created.

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

On October 3, Nemotron 3 Ultra repaired showcase run `20261001-193038-ver-de51cd` in **one candidate and two model requests**; the first request exhausted its 4,000-token task cap before returning valid JSON. The candidate changes the write enable from `wr_en` to `wr_en && !full` (and removes two comments). Total repair wall time was 29.464 seconds; the successful candidate verification took 8.92 seconds on the warm local Docker image.

Candidate `20261003-164426-ver-05e188` passed admission and the identical frozen check set with no integrity issues or findings: three simulation passes, three bounded passes, three unbounded proofs (`empty_flag`, `full_flag`, `read_data`), and one reached cover obligation. Claims apply only to DEPTH=4, WIDTH=8 and the recorded contract, assumptions, and toolchain. The independent checker, not the model, assigned `passed_unchanged_checks`.

The earlier integration test still exercises rejected, failing, and passing candidates using a stub. The new result is one real development repair, not the frozen eight-case evaluation; the primary-versus-diagnosis release decision remains open.

## Reproducibility

`countertrace bundle <run>` exports a hashed evidence bundle; `countertrace replay <bundle.zip>` re-ran the showcase bundle on the same machine and matched every obligation status and finding with an identical frozen check set. On October 3, the recorded real repair candidate bundle also replayed on the same machine: all ten obligation statuses matched, with no findings or frozen-input differences and no model call. Both refreshed bundles passed manifest file-hash validation and retain public parent/candidate relationships, original timings, and model-call metadata (stored on the parent). On October 4, clean-environment replays ran on two fresh GitHub-hosted x64 runners (three bundles each, six of six matched); the job repeats on every push.

## Tests

- `make check`: 69 unit tests (54 on October 3) and negative controls, Python/JSON/TOML validation, documentation links, and whitespace checks pass. New regressions preserve long explanation limits and resolve recorded parent/candidate links in a fresh read-only checkout. Automated model tests use mocked endpoints; the live development calls are documented separately above.
- `npm test` in `apps/web`: the real-recording citation rendering regression passes; TypeScript checking and the production build pass.
- `make test-integration`: 7 Docker tests running real RTL (proved control, replayed fault, altered harness hash, cancellation, unsupported syntax, stubbed repair loop, weak-set audit). Rerun after the worker identity fix: all seven passed locally in 59.34 seconds.

## Interface and recorded runs

The web interface builds with no TypeScript errors and was checked in a browser against the local service: contract setup, a live run from acceptance to finding, the showcase finding and cycle table, a clean control, the audit result and learner exercise, bundle download, model-unavailable states, and a 375 px layout. No screen-reader testing has been done. Seven runs are recorded in `recorded/`: the October 4 showcase fault with explanation and its one-line repair candidate, the eval-v2 two-bug case with its rejected and accepted candidates, the known-good control, and the weak-set audit. The original showcase bundle replayed with matching outcomes. Both repair relationships now use public recording IDs; recording a parent does not publish candidates automatically. The first real explanation exposed a frontend/backend citation-shape mismatch that blanked the run page. The interface now treats citation counts as counts and uses exact invalid-citation entries instead of interpreting a cycle range as a list. A regression renders the actual saved model response and mixed valid/invalid citations. Browser checks confirmed the full explanation/limits, source citations, cycle-5 focus, and recorded candidate navigation.

## October 3 UI/UX Pro Max review

A separate UI subagent reviewed the existing React interface against the UI/UX Pro Max skill and the persisted design system. Existing semantic result colors, focus rings, responsive grids, and reduced-motion support were retained. Changes add section shortcuts for long verification pages, native cycle buttons with a pressed state, and larger controls/text inputs on narrow screens. Collapsing a full trace after selecting a late cycle now restores a visible cycle as both the keyboard entry point and displayed queue.

Browser checks passed for section-heading focus; citation-to-cycle focus; Tab, ArrowDown, Home, and End; selecting cycle 11 then collapsing to the cycle-6 window; and opening the recorded candidate by keyboard. No page-level horizontal overflow was observed at widths 375, 768, 1024, and 1440 px, or at 812 × 375 landscape. Measured text/background contrast was at least 5.21:1 for the reviewed primary, muted, and accent pairings. Reduced-motion handling was reviewed in source, without OS-level emulation. These are focused interaction/responsive checks, not a complete accessibility certification; screen-reader testing and learner sessions remain pending. The UI regression, production build, and `make check` passed after the final edit.

## October 3 palette revision

At the owner's request, blue page, header, card, and code backgrounds were replaced with neutral charcoal, with off-white controls and focus indicators. Semantic result colors remain distinct. The persisted design system records this preference. Browser inspection confirmed body/card colors `#151515` / `#1D1D1D` with no page-level horizontal overflow in the preview. Reviewed foreground, muted, action, and result text contrasts on cards range from 6.09:1 to 15.17:1; muted text on muted surfaces is 6.02:1. `make check` (54 tests) and the production web build pass. No verifier or model behavior changed.

## October 3 evidence-notebook redesign

At the owner's request, the interface was rebuilt around an editorial evidence notebook: warm paper and ink, rust actions, a pale sage navigation rail, a custom trace mark, Newsreader headings, DM Sans body text, and monospace evidence. Setup now has numbered review steps and a mobile example selector; recorded runs are case cards; the run overview shows the actual selected finding's cycle and expected/observed signal values. The independent reference queue appears before its cycle table. The audit entry uses the same layout. Runtime details and original provenance remain in labelled disclosures. A UI subagent rebuilt setup and the case library in parallel; the final design system and web README describe the implementation.

Browser checks confirmed exact-contract acceptance enables execution; the mobile selector changes the FIFO and contract; section navigation transfers focus; explanation citations select cycle 5; ArrowDown selects cycle 6; collapsing the full trace after selecting cycle 11 restores cycle 6 as the visible keyboard entry and reference queue; and recorded repair/parent links retain method-specific result labels. Setup, library, and the showcase run had no page-level horizontal overflow at 375, 768, 1024, and 1440 px, or at 812 × 375 landscape. The audit selector exposed a narrow-screen grid sizing issue, which was fixed and rechecked at 375 px; the recorded audit also fits at 375 px, with wide tables in their own scroll regions. Desktop and phone screenshots were visually reviewed. Reviewed primary, muted, action, and semantic-status text pairings have contrast ratios from 5.01:1 to 13.34:1. Screen-reader testing and learner validation remain pending.

`make check` (54 tests), the recorded-explanation UI regression, TypeScript checking, and the production build passed. This change does not alter the verifier or make new model calls; these checks establish interface behavior, not new hardware or model results.

## Not yet done

Independent human review of explanations and evaluation labels; reviewer and learner recruitment; the usability study and audit-transfer question; evaluation on real learner-written bugs (all evaluated bugs so far are seeded); selectable contract policies such as fall-through reads; Nebius Serverless Jobs (all verification runs locally in Docker); hosted deployment and judge access; the release decision; the demonstration video.

## October 1 follow-up preparation

- The model gate now accepts `--run-id` and attaches its explanation result to the local run, so a later recording can contain it. The generic model prefix is blank; Llama-specific reasoning instructions must be explicitly configured for a compatible endpoint. Public-catalog endpoint/model candidates and input/output caps of 16,384/4,096 are in the ignored local `.env`; the API key and account billing remain absent. Report timestamp: `2026-10-02T01:27:57Z` (October 1 EDT), run `20261001-193038-ver-de51cd`, status `unavailable`, no calls. No showcase recording was replaced and no real repair was attempted.
- A MIT-licensed external FIFO candidate attributed to William Mar is quarantined in ignored `evaluation/holdout/`, pinned and hashed without reading its RTL into development context. Contract compatibility and admission are pending; it does not yet count as an independent control. See [candidate review](../evaluation/INDEPENDENT_FIXTURE.md).
- Recruitment drafts and a three-person study protocol are prepared in [STUDY.md](../evaluation/STUDY.md); nobody has been contacted or enrolled. The [release decision record](RELEASE_DECISION.md) retains diagnosis as the commitment, with primary scope pending real repair evidence.
- Caddy 2.11.4 validated the deployment Caddyfile locally in an offline container. No VM, funding, DNS/TLS, systemd deployment, or logged-out public journey has been tested. The [deployment plan](DEPLOYMENT.md) documents a proposed $300 budget before tax; spending approval is pending.
- Inspection of [Linux CI on the preceding implementation](https://github.com/Jeremiah-Sakuda/countertrace/actions/runs/36941347402) found six integration errors during artifact cleanup: files created by the image's UID 10001 were not removable by the host runner. The launcher now selects the service's non-root UID/GID, with a non-root fallback for root callers, while preserving worker isolation. Current Linux results are published in the repository's [Checks workflow](https://github.com/Jeremiah-Sakuda/countertrace/actions/workflows/ci.yml); macOS results alone do not establish Linux ownership behavior.
