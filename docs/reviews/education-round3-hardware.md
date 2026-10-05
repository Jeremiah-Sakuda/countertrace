# Independent simulated panel — education round 3, hardware

Reviewed October 5, 2026, source `6100514022ed8e8afc88f281e652195d7208bd16`. This is an independent simulated hackathon assessment, not sponsor judging or a human learner study. No previous panel reports or scores were consulted. Scope: current source, recorded evidence, requirements, roadmap, and intended video content in `docs/submission/DEMO_SCRIPT.md`. Deployment of this revision was in progress; I did not inspect the hosted deployment or navigate the shared browser.

| Official criterion, equally weighted | Score / 10 | Assessment |
| --- | ---: | --- |
| Technological Implementation | 8.7 | Real isolated RTL execution, two reference implementations, exact property inventories, re-admission of patches, frozen comparisons, reproducible recorded outcomes, and substantive Nemotron use. The education library has a pinned hash and independently checked raw observations. One conservative error-handling gap remains below. |
| Design | 8.5 | Prediction, a small experiment builder, expected/observed outputs, explanation, transfer, and export form a coherent teaching activity. Source distinguishes reference queue contents from sampled DUT signals, unchecked read data from zero, and recorded evidence from live execution. This score reflects source and workflow review, not a new visual or accessibility audit. |
| Potential Impact | 8.0 | A facilitator can share a bounded debugging exercise without installing a simulator, then discuss voluntary practice records. That is a concrete adoption path. Actual learner usefulness, facilitator preparation time, and repeat adoption remain unmeasured. |
| Quality of Idea | 8.6 | Learners construct a revealing counterexample and defend its scope, with a correct control to discourage inventing failures. Combining this with rejected and accepted AI repairs makes the trust lesson tangible. The novelty is the teaching experience and evidence discipline, not a new formal method or repair algorithm. |

**Equal-weight mean: 8.45/10.**

## Remaining software fix

**P2 — Reconcile failed worker metadata before assigning formal success.** In `src/countertrace/verify.py`, `formal_batch` checks whether a formal step exists and timed out, but does not reject its nonzero `returncode`. Container `timed_out` and `container_returncode` also do not invalidate success in this path. Consequently an authoritative-looking saved `PASS` file wins over contradictory execution-failure metadata. This is inconsistent with the stated fail-closed policy.

**Reproduction performed, without changing files or executing RTL:** load `recorded/rec-20261001-193044-ver-f15d50/batches/dut-formal/out/worker_result.json`; change only `dut:formal:prove.returncode` to `1` in memory; construct `Verification` rooted at that recording with depth 4; mock its `batch` return to use the original archived output directory and edited worker metadata, with `container_returncode=1` and `timed_out=True`; invoke `formal_batch('fifo')`. All three prove obligations remain `proved`. This exercises contradictory artifacts through the result parser. It does **not** establish that this combination occurred in a real execution, that any recorded proof is false, or that the hosted learning labs accept fabricated observations.

**Narrow fix:** accept formal `PASS` only when the relevant step completed successfully and the enclosing execution has no timeout/error contradiction. Preserve completed artifacts for inspection but assign `tool_error` or `unresolved` when execution metadata is incompatible with success. Add a focused regression using preserved PASS artifacts plus each conflicting failure field separately. Keep legitimate formal FAIL/counterexample handling intact; an SBY counterexample need not have process exit code zero. No harness, contract, lesson, or model-prompt expansion is needed.

## Evidence and limits

- `make check` passed: 98 Python tests, syntax/data/document-link checks, CLI smoke check, and whitespace validation.
- `npm test` passed all 3 web tests. The learning tests reparse every archived raw observation against the Python reference, verify archive hashes, check all 5,461 prefixes per design, and compare browser reference states with the recorded library. These checks validate stored evidence and implementation; this review did not rerun Docker or establish a new hardware proof.
- The six-edge, four-action, fixed-data replay limit is consistently disclosed. Authored candidates and hints are not misrepresented as model outputs. Coaching remains advisory; its citation validator is not treated as semantic certification.
- The proposed 2:45 video is a strong sequence: a passing ordinary test, a failing boundary test, explicitly live or recorded Nemotron coaching, transfer/export, facilitator review, then a rejected and accepted repair. Its edge-4 example agrees with the evidence. Intended content earns credit; filming quality and finished footage were not assessed.

## External evidence, not software defects

Observed learner and facilitator sessions would strengthen impact: record whether learners independently identify the governing rule, construct useful inputs, and answer transfer questions, including assistance and failed attempts. Independent expert review would strengthen confidence in the monitor and evaluation labels. Neither can be replaced by this panel, and neither calls for a larger HDL scope, accounts, LMS integration, or perfect model semantics. The present absence is already disclosed and is not an instruction to invent results or block the bounded educational release.

Remaining actionable code work from this review: the single P2 result-parser guard above. No defect was found in the reviewed recorded learning evidence path.
