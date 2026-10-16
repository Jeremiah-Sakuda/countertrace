# Feedback recovery pilot — October 16, 2026

This is Countertrace evidence. Dira was not modified or evaluated in this session.

## Result

Detailed verifier feedback promoted **3/6** revisions; rejection-only feedback promoted **4/6**. This small conditional recovery pilot does not establish a reliable advantage for detailed feedback.

## Frozen design

Two already-public, previously rejected proposals (FIFO and debouncer), three repeats per module, two arms per repeat. Both historical golden failures were replayed successfully before inference. Both arms receive the same specification and initial properties; the sole prompt difference is detailed gate diagnostics versus a generic rejection notice. Neither receives golden source. Each gets one structured revision, with the shipped schema retry and output-limit reasoning fallback; execution order alternates. The same deterministic gate judges both arms.

Protocol and runner were committed locally as `d10891f` before inference; the protocol identifies the unchanged product base `00c386e` and hashes the new runner separately. This is same-repository provenance, not an external preregistration or timestamp. No prompt, model, fixture or gate edits were made during execution.

Protocol SHA-256: `9c721dc505a91c688aae01f32294070cb15769de94f5841d438326b0448d8f4d`.

## Outcomes

| Module | Repeat | Feedback | Outcome | Gate stage | Model calls | Elapsed seconds |
| --- | ---: | --- | --- | --- | ---: | ---: |
| sync_fifo | 1 | detailed | not_promoted | golden | 2 | 51.47 |
| sync_fifo | 1 | rejection_only | promoted | mutants | 1 | 53.14 |
| debouncer | 1 | rejection_only | not_promoted | golden | 1 | 20.92 |
| debouncer | 1 | detailed | not_promoted | golden | 2 | 50.84 |
| sync_fifo | 2 | rejection_only | promoted | mutants | 1 | 61.62 |
| sync_fifo | 2 | detailed | promoted | mutants | 1 | 48.75 |
| debouncer | 2 | detailed | not_promoted | golden | 1 | 48.64 |
| debouncer | 2 | rejection_only | promoted | mutants | 1 | 21.51 |
| sync_fifo | 3 | detailed | promoted | mutants | 1 | 37.03 |
| sync_fifo | 3 | rejection_only | promoted | mutants | 1 | 32.88 |
| debouncer | 3 | rejection_only | not_promoted | golden | 1 | 28.90 |
| debouncer | 3 | detailed | promoted | mutants | 1 | 46.20 |

## Usage and interpretation

| Feedback | Input tokens | Output tokens | Estimated USD | Output-limit replies |
| --- | ---: | ---: | ---: | ---: |
| detailed | 9,810 | 84,719 | $0.263967 | 3 |
| rejection_only | 6,294 | 56,362 | $0.175380 | 0 |

Total: **14 raw model calls**, **$0.439347 estimated inference** at configured Ultra rates of $1/$3 per million input/output tokens. Tokens are provider-reported; dollars are calculated estimates, not an invoice. Calls missing usage: 0. Local CPU verification has no cloud-compute charge; local power/hardware cost was not measured. The incremental ledger allowance was $1.50. No VM, top-up or billing change was made.

Output-limit replies remain visible and count toward cost. The shipped client can retry with reasoning off; thus this measures the configured recovery workflow, including that behavior. More diagnostic text can also change reasoning length. Repeats are stochastic runs of two fixtures, not six independent designs. The selected starting failures and prior exposure limit generalization. No claim about classroom benefit, fresh-heldout accuracy, or full four-round agent superiority follows from this experiment.

## Synthetic end-to-end check

The predeclared selection chose newly promoted FIFO run `20261016-154408-che-01f04d` (detailed-feedback repeat 2), with no historical fallback. The seeded overflow bug was found and golden replay confirmed it. One real model repair candidate passed **all 11 unchanged obligations**, including four proved obligations; frozen comparison identity matched. The checks, failing-design and repaired-design ZIPs each replayed successfully without inference. This validates the local workflow at WIDTH=8, DEPTH=4; it does not demonstrate public hosting or a learner study.

The advisory model outputs were **not fully correct**. Super first needed a schema retry, then incorrectly labeled the compatible full-write rule as a conflict. Ultra's explanation correctly identified the overwrite cause but cited `mem[0]` twice, which the citation validator flagged as absent from sampled signals. The fixed contract and deterministic gate remained authoritative; these outputs did not approve the repair. Both errors remain in the evidence rather than being replaced by better reruns. Assistant review is not independent human validation.

End-to-end usage: 4 model calls, 5,435 input and 4,805 output tokens; **$0.019850 estimated** at configured prices. Super calls use the default $1/$3 rates in the local ledger. Combined experiment plus end-to-end estimate: **$0.459197** (18 raw calls). The end-to-end allowance was $0.25. Actual invoiced cost and shared account activity are not attributed by this report.

## Evidence and reproduction

- [Protocol and exact starting prompts](protocol.json).
- [Every raw response, retry, usage record, property proposal and gate summary](results.json).
- [Machine-readable aggregate](summary.json).
- [Twelve local comparison ZIP paths and hashes](local-bundles.json); 3,440,324 bytes total, not automatically published.
- [Synthetic end-to-end journey](end-to-end.json).

Existing results are resumable without repeating completed attempts; interrupted attempts are retained. Do not delete the protocol/results to manufacture a new holdout. To perform a new experiment, create a separately named protocol with its own budget and report.

```sh
PYTHONPATH=src .venv/bin/python scripts/compare_check_feedback.py run
PYTHONPATH=src .venv/bin/python scripts/verify_feedback_e2e.py
make check
```

Live commands require configured Nebius access and credits. The end-to-end command refuses an existing report rather than silently rerunning. Exported ZIPs listed in `end-to-end.json` live under ignored `.countertrace/bundles/`; raw local solver artifacts are retained in `.countertrace/runs/`. These local archives are not automatically published. Replay each listed ZIP with `countertrace replay <path>` from the matching source checkout, with Docker and no inference credentials. Use report hashes to verify the archives.
