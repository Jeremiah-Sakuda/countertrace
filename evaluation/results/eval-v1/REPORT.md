# Evaluation eval-v1 (October 4, 2026)

One pre-registered run of the frozen suite. All outcomes are reported, including failures. This is the project's first evaluation; it is **not** externally reviewed, and every case, label, and brief was authored by the developer's coding assistant.

## Protocol

Pre-registration is evidenced by same-repository git commits (configuration freeze, then case hash, then results). There is no external timestamp, so the ordering cannot be verified independently of this repository; future freezes should be anchored by pushing a tag before running.

- Configuration frozen first: [freeze-2026-10-04.json](../../freeze-2026-10-04.json) (commit `ee3b5de`): Nemotron 3 Ultra for explanation and repair, Nemotron 3 Super for interpretation, prompt hashes, token caps (16,384 in / 4,096 out; 4,000 for repair), three repair attempts, verifier digest `7d82f4b2482a24f2`, harness and stimulus hashes, scoring rules.
- The independent FIFO ([William Mar, MIT](../../../fixtures/independent/billdmar/)) was held out of prompt development and first read after the freeze. Interface mappings (`c1cd37f`) were added afterwards so it could be admitted; prompts, models, budgets, harness, worker, stimulus, and scoring did not change.
- Cases frozen before running: [cases-frozen-eval-v1.json](../../cases-frozen-eval-v1.json) records SHA-256 `586fa989…a736`, which matches [suite.original.json](suite.original.json). [suite.json](suite.json) only updates the independent FIFO's path to its published location.
- Each configuration ran once. Raw outcomes: [results.json](results.json). Local run IDs are listed per case.

## Results against PRD targets

| Target | PRD bar | Result |
| --- | --- | --- |
| Reliable diagnosis | ≥6 of 8 faulty cases, ≥4 defect classes | **8 / 8**; reset, flags/boundaries, simultaneous, ordering/wraparound; every formal counterexample reproduced in simulation |
| Honest conclusions | No false alarm on 4 controls; no faulty case accepted | **0 / 4** false alarms; 0 faulty cases accepted; 0 unresolved or tool errors on controls |
| Useful repair | ≥5 of 8 within three candidates | **7 / 8** (all cases); 7 / 8 (attempted cases); 6 on the first candidate |
| Model contribution: interpretation | ≥3 of 4 conflicts detected, ≥3 of 4 compatible proceed | **4 / 4** and **4 / 4**, each conflict on the expected topic |
| Model contribution: explanation | Cites actual signals and cycles | 8 / 8 schema-valid; 7 with zero invalid citations, 1 with one invalid citation (`queue`); assistant review scored all 8 at 2/2 on the four rubric items |

Controls: the independent FIFO (depth 4), `fifo_count` (depth 2 and 4), and `fifo_wrapbit` (depth 4). All four were proved for all three core properties. The three Countertrace controls were also development controls.

| Case | Implementation | Category | First finding | Repair |
| --- | --- | --- | --- | --- |
| E1 | independent | reset | empty_flag @0 | passed on attempt 3 (attempts 1–2 hit the output limit) |
| E2 | independent | simultaneous | full_flag @6 | passed on attempt 1 |
| E3 | independent | ordering/wraparound | empty_flag @4 | passed on attempt 1 |
| E4 | independent | flags/boundaries | empty_flag @1 | **failed**: all three attempts hit the output limit before valid JSON |
| E5 | Countertrace | simultaneous | full_flag @4 | passed on attempt 1 |
| E6 | Countertrace | flags/boundaries | empty_flag @1 | passed on attempt 1 |
| E7 | Countertrace | reset | empty_flag @0 | passed on attempt 1 |
| E8 | Countertrace | ordering/wraparound | read_data @3 | passed on attempt 1 |

Every passing repair reverses its seeded fault and passed all ten unchanged obligations, including three unbounded proofs, with an identical frozen check set. The E6 candidate also added `dout <= 0` to reset (allowed by the contract), and all full-file candidates deleted header comments.

## Failures and issues found

1. **Output exhaustion caused every repair failure.** All 12 repair requests that failed schema validation ended with `finish_reason: length` (E1 ×4, E4 ×6, and one each inside E3's and E5's successful attempts). Two explanation requests (E3, E4) also hit the 4,096-token limit and succeeded on retry. The full-file response format is long for the 146-line independent FIFO. E4's miss is entirely this.
2. **Full-file repairs drop comments**, including the independent author's header. Attribution must survive a repair.
3. One explanation cited a non-signal (`queue`); several explanations state internal pointer values inferred from RTL rather than sampled.

After eval-v1, repairs switched to exact-match edits to reduce output size and preserve untouched attribution (see [STATUS](../../../docs/STATUS.md)). Initial validation used development cases; the later [eval-v2](../eval-v2/REPORT.md) separately evaluated that workflow on fresh frozen cases. eval-v1 numbers remain unchanged. Citation validation still cannot establish semantic correctness; invalid citations and partly incorrect explanations remain disclosed in the later report.

## Cost and time

37 model requests: 80,755 input and 107,875 output tokens, about **$0.40** at public list prices ($1/$3 per million for Ultra; Super calls are priced as Ultra, so this overestimates). Account billing is unverified. Interpretation took 7.1–11.4 s per brief on Super.

## Limits

Single run per configuration; small suite; assistant-authored cases and labels; assistant review of explanations; no learner or expert study. Proofs hold only for the stated parameters and assumptions. The audit-specific repair comparison in the PRD was not run because the repair loop does not consume audit findings, so the baseline and product workflows would be identical.
