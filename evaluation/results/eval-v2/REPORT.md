# Evaluation eval-v2 (October 4, 2026)

**October 4 derived-evidence correction:** the simulation summarizer originally retained only each test's first failure, so some later property failures could be labeled passed. Overall faulty-design detection and repair rejection remained intact. The published recordings now derive each property's summary from all preserved trace rows, with provenance; see [the correction record](../../../recorded/README.md#corrected-derived-summaries). These historical evaluation outputs and model responses have not been rerun or rewritten.

The second pre-registered run, measuring the repair agent as it now ships (exact-match edits, each failed candidate's counterexample fed back to the model, and a reasoning-off retry when a reply hits the output limit) on fresh and harder cases. Like eval-v1, it is a single run of assistant-authored cases with no external review.

## Protocol

Pre-registration is evidenced by same-repository git commits (configuration freeze, then case hash, then results). There is no external timestamp, so the ordering cannot be verified independently of this repository; future freezes should be anchored by pushing a tag before running.

- Configuration frozen first: [freeze-eval-v2.json](../../freeze-eval-v2.json) (code `2ae9a29`, freeze `bde4b48`). Nemotron 3 Ultra for explanation and repair (reasoning on), Nemotron 3 Super for interpretation (reasoning off), prompt hashes, budgets, verifier digest `7d82f4b2482a24f2` (unchanged since eval-v1).
- Commit IDs: on October 4 the repository history was rewritten to remove internal working notes. Commit order and dates, and every evaluation file, were unchanged. The frozen records keep the original IDs: code commit `3d33fe5` is now `2ae9a29` (`2ae9a296bbe85b400a99e1adbee5a6d6b59107d9`), and freeze commit `efda152` is now `bde4b48`.
- Cases frozen next: [cases-frozen-eval-v2.json](../../cases-frozen-eval-v2.json) records SHA-256 `2a3ba86b…09b9`, matching [suite.original.json](suite.original.json). [suite.json](suite.json) only moves the new FIFO to its published path, [fifo_regflags.v](fifo_regflags.v).
- New for v2: a registered-flags FIFO written for this evaluation and never used in prompt development; two multi-line bugs and two cases with two independent bugs; subtler briefs.
- Raw outcomes: [results.json](results.json).
- Timing note: `fifo_regflags.v` was written and verified as a control about 30 seconds before the freeze file, as the freeze note states; its faults, labels, and the briefs were written after it.

## Results

| Target | PRD bar | eval-v2 | eval-v1 |
| --- | --- | --- | --- |
| Diagnosis | ≥6/8, ≥4 classes | **8/8**, four classes | 8/8 |
| False alarms on controls | 0/4 | **0/4** (all four proved) | 0/4 |
| Repair within three candidates | ≥5/8 | **8/8** (5 first candidate, 2 second, 1 third) | 7/8 |
| Conflicting briefs detected | ≥3/4 | **3/4** | 4/4 |
| Compatible briefs proceed | ≥3/4 | **4/4** | 4/4 |
| Explanations with only valid citations | — | 6/8 | 7/8 |

| Case | Shape | First finding | Repair | Notes |
| --- | --- | --- | --- | --- |
| F1 | multi-line flag logic | empty_flag @2 (both_mid) | passed, **attempt 3** | Attempts 1–2 failed the unchanged checks with new counterexamples (cycle 1 read-while-empty, cycle 2); the third rewrote the flag updates as next-state logic. |
| F2 | single line | full_flag @0 (reset) | passed, attempt 2 | Attempt 1 failed with a new counterexample; attempt 2 also added a simultaneous-operation branch, which the proofs accepted. |
| F3 | single line | full_flag @1 | passed, attempt 1 | Also added a redundant simultaneous branch. |
| F4 | single line (short array) | read_data @8 | passed, attempt 1 | Formal tasks ended in an SBY engine error on the out-of-range index and were reported as tool errors, not passes. |
| F5 | **two bugs** | read_data @2 | passed, attempt 1 | One candidate fixed both bugs. |
| F6 | **two bugs** | empty_flag @1 | passed, **attempt 2** | Attempt 1 fixed one bug and failed the checks on the other (cycle 4); the counterexample led attempt 2 to fix both. |
| F7 | multi-line | full_flag @0 | passed, attempt 1 | |
| F8 | single line | read_data @2 | passed, attempt 1 | |

Four repair requests hit the 4,096-token limit with reasoning on. Every one recovered on the reasoning-off retry (146–630 tokens), so none cost an attempt. No explanation request hit the limit. Repair candidates passed every unchanged obligation, including three unbounded proofs each, with identical frozen check sets.

**Interpretation miss.** B1 asked for "full one entry early, when three bytes are stored, and further writes refused." Super let it proceed. The topic list describes capacity ("DEPTH words") but has no topic for what the full flag means, so a model can read the brief as compatible. This is a real gap in the interpretation design, not only the model.

**Explanation review** (coding assistant, not independent): all eight scored 2/2 on the four rubric items (violated requirement, first failing transaction, expected vs observed, limits). For root cause, 6 of 8 were fully correct. F1 added an incorrect claim of a symmetric bug in `full_r`, and F6 described only one of its two bugs. Two explanations cited non-signals (`expected empty`, `queue`), and the citation checker flagged both.

## Cost

32 requests, 52,193 input and 63,370 output tokens: about **$0.24** at Ultra list prices. Super calls are priced as Ultra, so this overestimates; account billing is unverified.

## Limits

One run; assistant-authored implementation, bugs, labels, and briefs; assistant review only; no learner study. Two-bug cases were constructed by combining independent edits, not taken from real learner code. Proofs hold only for the stated parameters and assumptions.
