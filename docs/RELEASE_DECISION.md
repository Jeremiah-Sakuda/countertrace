# Release decision record

**Current commitment: diagnosis (unchanged until the owner decides). Evidence now supports primary.** On October 4 the frozen eval-v1 suite met every measured primary target: repair 7/8 within three candidates (bar 5/8), diagnosis 8/8 across four classes, 0/4 false alarms, interpretation 4/4 and 4/4 ([report](../evaluation/results/eval-v1/REPORT.md)). Caveats: one run, assistant-authored cases and labels, assistant review only, and no learner evidence yet.

**Recommendation (assistant, for the owner to accept or reject):** select the primary release at the October 8 initial decision, keep the eval-v1 caveats in every claim, and confirm on October 14 after independent review of the suite labels and an early learner session. Fall back to diagnosis if a reviewer rejects more than three of the eight labels or if a fresh-case rerun of the edit-based repair falls below 5/8.

Previous summary: An authenticated Ultra explanation and one real unchanged-check showcase repair ran October 3. The explanation was reviewed by Codex, not an independent human. A development success does not satisfy the frozen repair evaluation. This record implements the existing PRD gates; it does not change them.

| Decision | Date | Required evidence | Current result |
| --- | --- | --- | --- |
| Model feasibility | October 4 | Useful authenticated Nemotron explanation of a replayed failure | Met October 3 on development evidence; Codex source/trace review, independent human validation pending |
| Initial profile | October 8 | Complete diagnosis journey, first real unchanged-check repair, measured verification batch, early feedback | Journey, real repairs (7/8 frozen, 5/5 development with edits), and warm batches measured; early feedback pending |
| Final profile | October 14 | Evidence supports the primary repair target and unchanged-check trust rules; otherwise diagnosis | Pending |

The primary repair target is at least 5 of 8 faulty cases repaired within three candidate attempts, with all-case and attempted-repair denominators. A showcase success is insufficient. Freeze cases and evaluation configuration before the evidence used to make this decision; if that evidence is unavailable by October 14, choose diagnosis. Later evaluations must remain separate from development tuning.

Both profiles still require the PRD's diagnosis, explanation, audit, reproducibility, and user-study evidence. External FIFO acquisition is not independent validation. Either profile is blocked by persistent false acceptance or an untrustworthy oracle. Declare proof versus bounded-only scope separately, using actual named obligations and assumptions.

## Fill when deciding

- Decision date and owner: pending.
- Profile (primary / diagnosis): pending final decision; diagnosis is the delivery baseline.
- Evidence manifest: [freeze](../evaluation/freeze-2026-10-04.json), [cases](../evaluation/cases-frozen-eval-v1.json), [results](../evaluation/results/eval-v1/results.json).
- Repair successes / all 8 cases / attempted cases: 7 / 8 / 8 (eval-v1, full-file format). Edit-based format: 5/5 on development cases only.
- Scope of formal claims: development proofs exist; reviewer and release evaluation pending.
- Remaining release blockers and owners: independent evaluation, reviewer/learners, hosted access/funding, clean replays, and final video.

If diagnosis is selected, remove repair controls from the judged journey and repair promises from the README, submission, and video; retain developer experiments clearly labeled. Use a second held-out counterexample and replay for the replacement video segment. Update [STATUS.md](STATUS.md), [DEMO.md](DEMO.md), and the [roadmap](ROADMAP.md) with the actual decision. No release decision or future reminder is scheduled by this document.
