# Repair ablation on the frozen eval-v2 suite (October 4, 2026)

Question from an internal review: does the choice of Nemotron tier, or feeding a rejected candidate's counterexample back to the model, actually matter? Each configuration re-ran diagnosis and the bounded repair loop (three candidates) once on the eight faulty eval-v2 cases. Explanation and interpretation were skipped. Prompts, budgets, verifier, and suite are the eval-v2 frozen ones; only the repair model or the feedback switch changed. Raw results: [repair-super.json](repair-super.json), [repair-nano.json](repair-nano.json), [repair-ultra-no-feedback.json](repair-ultra-no-feedback.json); the Ultra-with-feedback row is [eval-v2](../eval-v2/results.json).

| Configuration | Passed unchanged checks | Passed on first candidate | Candidates | Requests | Replies cut off at output limit | Input / output tokens | Median request latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nemotron 3 Ultra, feedback on (eval-v2) | **8/8** | 5 | 12 | 16 | 4 | 25,335 / 38,008 | 6.7 s |
| Nemotron 3 Super, feedback on | **8/8** | 7 | 9 | 11 | 2 | 17,671 / 22,597 | 10.3 s |
| Nemotron 3 Nano, feedback on | 6/8 | 5 | 13 | 20 | 6 | 30,090 / 48,468 | 16.7 s |
| Nemotron 3 Ultra, reduced feedback (see note) | 7/8 | 7 | 10 | 12 | 2 | 18,849 / 27,136 | 6.2 s |

## What this shows

- **The reduced-feedback run is exploratory, not a clean control.** A later internal review found that the "feedback off" switch stopped refreshing the trace but still passed each rejected candidate's summary, which names its failing check and cycle, and it labeled the old trace as if it came from the current RTL. In that run Ultra failed only F6, the two-bug case, repeating the same one-bug fix three times. With full feedback, F6 passed on the second candidate. This is an observation from one case; it does not establish that feedback caused the fix. The switch was corrected on October 4 (the model now learns only that earlier candidates were rejected) and has not been rerun.
- **Super matched Ultra on this suite** at about 60% of Ultra's output tokens. Nano repaired 6/8; it hit the output limit more often, and two of its failures included schema errors.
- **First-candidate counts are within run-to-run variance.** The two Ultra runs differ only in feedback, which cannot affect a first candidate, yet they passed 5 and 7 cases first time. Treat first-candidate differences of one or two cases as noise at n = 8.
- **No configuration produced a false acceptance.** Every passed candidate cleared the identical frozen check set, including three unbounded proofs. Every failure was a rejected or unparseable candidate.

Countertrace keeps Ultra as the frozen default for repair. Super is a measured, cheaper alternative (`NEBIUS_REPAIR_MODEL_ID`). Choosing between them would need repeated runs and more cases.

## Limits

One run per configuration on eight assistant-authored cases. Costs are list-price estimates with every model priced as Ultra. No model was tuned on this suite.
